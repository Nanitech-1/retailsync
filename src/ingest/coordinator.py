"""Ingestion Coordinator: Executes multi-source ingestion into staging tables."""

import logging
from typing import Dict
from sqlalchemy import Engine

from src.load.db import get_engine
from src.ingest.olist_loader import ingest_olist_datasets
from src.ingest.api_loader import ingest_api_products
from src.ingest.supplier_loader import ingest_supplier_products

logger = logging.getLogger(__name__)


def run_ingestion(engine: Engine = None) -> Dict[str, int]:
    """Runs ingestion for all three sources and returns row counts.

    Args:
        engine: Database engine. If None, acquires using get_engine().

    Returns:
        Dictionary mapping table name to row count ingested.
    """
    if engine is None:
        engine = get_engine()

    counts: Dict[str, int] = {}
    logger.info("=== Phase 2: Starting Multi-Source Ingestion ===")

    # 1. Ingest Olist CSV datasets
    logger.info("1/3 Ingesting Olist CSV datasets...")
    olist_counts = ingest_olist_datasets(engine)
    counts.update(olist_counts)

    # 2. Ingest Live REST API
    logger.info("2/3 Ingesting Live REST API (DummyJSON)...")
    try:
        api_count = ingest_api_products(engine)
        counts["stg_api_products"] = api_count
    except Exception as exc:
        logger.error(f"Failed to ingest API products: {exc}", exc_info=True)
        counts["stg_api_products"] = 0

    # 3. Ingest Messy Supplier CSV
    logger.info("3/3 Ingesting Supplier CSV dataset...")
    supplier_count = ingest_supplier_products(engine)
    counts["stg_supplier_products"] = supplier_count

    total_rows = sum(counts.values())
    logger.info(f"=== Multi-Source Ingestion Complete: {total_rows} total rows across {len(counts)} tables ===")
    return counts
