"""Loader for messy supplier CSV data into staging."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import Engine, text

from src.config import settings
from scripts.generate_supplier_csv import generate_supplier_data

logger = logging.getLogger(__name__)


def ingest_supplier_products(
    engine: Engine,
    csv_path: Optional[Path] = None,
) -> int:
    """Reads the supplier CSV and ingests rows into stg_supplier_products.

    Args:
        engine: Database engine.
        csv_path: Optional custom path to supplier_products.csv.

    Returns:
        Number of rows ingested into staging.
    """
    file_path = csv_path or (settings.data_raw_dir / "supplier_products.csv")

    if not file_path.exists():
        logger.warning(f"Supplier CSV not found at {file_path}. Generating synthetic dataset...")
        generate_supplier_data(file_path, num_rows=2000)

    logger.info(f"Loading supplier CSV from {file_path}...")
    # Load as strings to preserve raw values exactly as received
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)

    now = datetime.now(timezone.utc)
    df["_source"] = "supplier_csv"
    df["_ingested_at"] = now

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM stg_supplier_products"))

    df.to_sql("stg_supplier_products", engine, if_exists="append", index=False)
    logger.info(f"Successfully ingested {len(df)} rows into stg_supplier_products.")
    return len(df)
