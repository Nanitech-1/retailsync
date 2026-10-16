"""Ingestion module for live REST API (DummyJSON products).

Implements pagination, timeout handling, retries with exponential backoff (tenacity),
and error handling for HTTP 429 / 5xx rate limits and server errors.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import pandas as pd
import requests
from sqlalchemy import Engine, text
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)

from src.config import settings

logger = logging.getLogger(__name__)


def is_transient_error(exception: BaseException) -> bool:
    """Returns True if exception is a network failure or 429/5xx HTTP status."""
    if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(exception, requests.HTTPError):
        status = exception.response.status_code if exception.response else 0
        return status == 429 or status >= 500
    return False


@retry(
    retry=retry_if_exception(is_transient_error),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def fetch_api_page(
    base_url: str,
    skip: int,
    limit: int = 50,
    timeout: int = 10,
    session: Optional[requests.Session] = None,
) -> Dict:
    """Fetches a single page of products from the REST API with retry logic.

    Args:
        base_url: Base endpoint URL.
        skip: Pagination offset.
        limit: Number of records per page.
        timeout: Request timeout in seconds.
        session: Optional persistent requests.Session.

    Returns:
        JSON response dict containing 'products', 'total', 'skip', 'limit'.
    """
    http = session or requests
    params = {"skip": skip, "limit": limit}
    response = http.get(base_url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_all_products(
    base_url: Optional[str] = None,
    limit_per_page: int = 50,
) -> List[Dict]:
    """Iterates through paginated API results until all products are retrieved.

    Args:
        base_url: Optional endpoint URL (defaults to settings.api_base_url).
        limit_per_page: Page size.

    Returns:
        List of product dictionaries.
    """
    url = base_url or settings.api_base_url
    logger.info(f"Starting API ingestion from {url}...")

    all_products: List[Dict] = []
    skip = 0
    total = None

    with requests.Session() as session:
        while total is None or skip < total:
            data = fetch_api_page(url, skip=skip, limit=limit_per_page, session=session)
            products = data.get("products", [])
            if not products:
                break

            total = data.get("total", len(products))
            all_products.extend(products)
            skip += len(products)
            logger.info(f"Fetched {len(all_products)} / {total} products from API.")

    return all_products


def ingest_api_products(
    engine: Engine,
    base_url: Optional[str] = None,
) -> int:
    """Fetches live products from REST API and loads them into stg_api_products.

    Args:
        engine: Database engine.
        base_url: Optional endpoint override.

    Returns:
        Number of rows ingested into staging.
    """
    products = fetch_all_products(base_url=base_url)
    if not products:
        logger.warning("No products fetched from API.")
        return 0

    # Flatten and map fields
    rows = []
    now = datetime.now(timezone.utc)
    for p in products:
        rows.append({
            "api_id": str(p.get("id")),
            "title": str(p.get("title", "")),
            "description": str(p.get("description", "")),
            "price": str(p.get("price", "")),
            "discount_percentage": str(p.get("discountPercentage", "")),
            "rating": str(p.get("rating", "")),
            "stock": str(p.get("stock", "")),
            "brand": str(p.get("brand", "")),
            "category": str(p.get("category", "")),
            "thumbnail": str(p.get("thumbnail", "")),
            "_source": "dummyjson_api",
            "_ingested_at": now,
        })

    df = pd.DataFrame(rows)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM stg_api_products"))

    df.to_sql("stg_api_products", engine, if_exists="append", index=False)
    logger.info(f"Successfully ingested {len(df)} rows into stg_api_products.")
    return len(df)
