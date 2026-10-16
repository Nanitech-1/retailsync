"""Ingestion package exports."""

from src.ingest.coordinator import run_ingestion
from src.ingest.olist_loader import ingest_olist_datasets
from src.ingest.api_loader import ingest_api_products
from src.ingest.supplier_loader import ingest_supplier_products

__all__ = [
    "run_ingestion",
    "ingest_olist_datasets",
    "ingest_api_products",
    "ingest_supplier_products",
]
