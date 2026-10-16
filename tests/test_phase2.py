"""Tests for Phase 2: Multi-Source Ingestion into Staging."""

from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
import requests
from sqlalchemy import text

from src.load.db import get_engine, init_schema
from src.ingest.api_loader import is_transient_error, fetch_api_page, ingest_api_products
from src.ingest.supplier_loader import ingest_supplier_products
from src.ingest.olist_loader import ingest_olist_datasets
from scripts.generate_supplier_csv import generate_supplier_data


@pytest.fixture
def test_db():
    """Initializes and returns a fresh SQLite test database engine."""
    engine = get_engine(force_sqlite=True)
    init_schema(engine=engine)
    return engine


def test_generate_supplier_csv_anomalies(tmp_path: Path):
    """Verifies that generate_supplier_csv injects deliberate data anomalies."""
    test_csv = tmp_path / "supplier_test.csv"
    generate_supplier_data(test_csv, num_rows=200)

    df = pd.read_csv(test_csv, dtype=str, keep_default_na=False)
    assert len(df) == 200
    assert "supplier_sku" in df.columns
    assert "raw_price" in df.columns

    # Verify duplicate SKUs exist
    assert df["supplier_sku"].duplicated().any()

    # Verify invalid or negative prices exist
    prices = df["raw_price"].tolist()
    has_negative_or_na = any(p == "" or p == "N/A" or (p.replace(".", "", 1).lstrip("-").isdigit() and float(p) < 0) for p in prices)
    assert has_negative_or_na


def test_api_loader_transient_error_detection():
    """Verifies transient error identification for tenacity retries."""
    timeout_err = requests.Timeout()
    assert is_transient_error(timeout_err) is True

    conn_err = requests.ConnectionError()
    assert is_transient_error(conn_err) is True

    resp_429 = MagicMock()
    resp_429.status_code = 429
    assert is_transient_error(requests.HTTPError(response=resp_429)) is True

    resp_500 = MagicMock()
    resp_500.status_code = 500
    assert is_transient_error(requests.HTTPError(response=resp_500)) is True

    resp_404 = MagicMock()
    resp_404.status_code = 404
    assert is_transient_error(requests.HTTPError(response=resp_404)) is False


def test_api_loader_mocked_fetch(test_db):
    """Tests API loader staging with mocked response."""
    mock_payload = {
        "products": [
            {
                "id": 1,
                "title": "Smartphone Test",
                "description": "A high-end phone",
                "price": 599.99,
                "discountPercentage": 10.5,
                "rating": 4.5,
                "stock": 35,
                "brand": "TechCorp",
                "category": "smartphones",
                "thumbnail": "https://example.com/thumb.jpg",
            }
        ],
        "total": 1,
        "skip": 0,
        "limit": 50,
    }

    with patch("src.ingest.api_loader.fetch_api_page", return_value=mock_payload):
        count = ingest_api_products(test_db, base_url="https://fake.url/products")
        assert count == 1

        with test_db.connect() as conn:
            row = conn.execute(text("SELECT title, _source FROM stg_api_products WHERE api_id = '1'")).fetchone()
            assert row is not None
            assert row[0] == "Smartphone Test"
            assert row[1] == "dummyjson_api"


def test_supplier_loader_ingestion(test_db, tmp_path: Path):
    """Tests ingestion of supplier products into staging."""
    test_csv = tmp_path / "supplier_test.csv"
    generate_supplier_data(test_csv, num_rows=100)

    count = ingest_supplier_products(test_db, csv_path=test_csv)
    assert count == 100

    with test_db.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*), _source FROM stg_supplier_products GROUP BY _source")).fetchone()
        assert res[0] == 100
        assert res[1] == "supplier_csv"


def test_olist_loader_ingestion(test_db, tmp_path: Path):
    """Tests ingestion of Olist CSVs into staging tables."""
    results = ingest_olist_datasets(test_db, olist_dir=tmp_path / "olist")
    assert len(results) >= 5
    assert "stg_olist_orders" in results
    assert "stg_olist_order_items" in results
    assert results["stg_olist_orders"] > 0
