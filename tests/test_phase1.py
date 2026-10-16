"""Tests for Phase 1: Environment, Configuration, Logging, and Database Schema."""

import pytest
from sqlalchemy import inspect, text

from src.config import settings
from src.load.db import get_engine, init_schema
from src.monitor.run_logger import setup_logger


def test_config_loads_defaults():
    """Validates that settings and configurations load properly."""
    assert settings.db.user == "retailsync_user"
    assert settings.db.port == 5432
    assert "retailsync_dw" in settings.db.database_url
    assert settings.llm.model == "gemini-1.5-flash"
    assert settings.data_raw_dir.exists()


def test_logger_injects_run_id(caplog):
    """Validates that structured logger injects run_id into log records."""
    test_run_id = "TEST-RUN-12345"
    logger = setup_logger(name="test_logger", run_id=test_run_id, log_to_file=False)

    with caplog.at_level("INFO"):
        logger.info("Verifying logger output with run_id")

    assert any(record.run_id == test_run_id for record in caplog.records)


def test_database_schema_initialization():
    """Validates that init_schema creates all required tables and views."""
    engine = get_engine(force_sqlite=True)
    init_schema(engine=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    views = inspector.get_view_names()

    # Core required tables
    required_tables = [
        "stg_olist_orders",
        "stg_olist_order_items",
        "stg_olist_customers",
        "stg_olist_products",
        "stg_olist_payments",
        "stg_olist_sellers",
        "stg_olist_category_translation",
        "stg_api_products",
        "stg_supplier_products",
        "rejected_records",
        "dim_customers",
        "dim_products",
        "dim_sellers",
        "dim_date",
        "fact_orders",
        "llm_cache",
        "pipeline_runs",
    ]

    for table in required_tables:
        assert table in tables, f"Expected table '{table}' not found in database."

    # Core required views
    required_views = [
        "v_revenue_by_category_monthly",
        "v_top_products_by_category",
        "v_repeat_customer_rate",
        "v_delivery_delay_by_seller",
        "v_supplier_vs_api_price_comparison",
    ]

    for view in required_views:
        assert view in views, f"Expected view '{view}' not found in database."


def test_db_connection_query():
    """Validates basic query execution on the engine."""
    engine = get_engine(force_sqlite=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS val")).scalar()
        assert result == 1
