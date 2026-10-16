"""Loader for Olist Brazilian E-Commerce CSV dataset into staging tables."""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from sqlalchemy import Engine, text

from src.config import settings

logger = logging.getLogger(__name__)

# Mapping from common file patterns to target staging tables
OLIST_TABLE_MAPPING = {
    "orders": "stg_olist_orders",
    "order_items": "stg_olist_order_items",
    "customers": "stg_olist_customers",
    "products": "stg_olist_products",
    "payments": "stg_olist_payments",
    "sellers": "stg_olist_sellers",
    "translation": "stg_olist_category_translation",
}


def generate_sample_olist_files(olist_dir: Path) -> None:
    """Generates realistic sample Olist CSV files if not already present.

    Ensures the pipeline can run end-to-end out-of-the-box before full manual
    download from Kaggle.
    """
    olist_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating sample Olist CSV files in {olist_dir}...")

    # 1. Category Translation
    translations = [
        {"product_category_name": "beleza_saude", "product_category_name_english": "health_beauty"},
        {"product_category_name": "informatica_acessorios", "product_category_name_english": "computers_accessories"},
        {"product_category_name": "cama_mesa_banho", "product_category_name_english": "bed_bath_table"},
        {"product_category_name": "esporte_lazer", "product_category_name_english": "sports_leisure"},
        {"product_category_name": "moveis_decoracao", "product_category_name_english": "furniture_decor"},
    ]
    pd.DataFrame(translations).to_csv(olist_dir / "product_category_name_translation.csv", index=False)

    # 2. Customers
    customers = [
        {
            "customer_id": f"cust_{i:04d}",
            "customer_unique_id": f"uniq_{i % 80:04d}",  # repeat customers for repeat rate view!
            "customer_zip_code_prefix": f"{10000 + i}",
            "customer_city": "sao paulo" if i % 2 == 0 else "rio de janeiro",
            "customer_state": "SP" if i % 2 == 0 else "RJ",
        }
        for i in range(1, 101)
    ]
    pd.DataFrame(customers).to_csv(olist_dir / "olist_customers_dataset.csv", index=False)

    # 3. Sellers
    sellers = [
        {
            "seller_id": f"seller_{i:03d}",
            "seller_zip_code_prefix": f"{20000 + i}",
            "seller_city": "curitiba" if i % 2 == 0 else "belo horizonte",
            "seller_state": "PR" if i % 2 == 0 else "MG",
        }
        for i in range(1, 11)
    ]
    pd.DataFrame(sellers).to_csv(olist_dir / "olist_sellers_dataset.csv", index=False)

    # 4. Products
    products = [
        {
            "product_id": f"prod_{i:04d}",
            "product_category_name": translations[i % len(translations)]["product_category_name"],
            "product_name_lenght": "50",
            "product_description_lenght": "250",
            "product_photos_qty": "2",
            "product_weight_g": str(500 + i * 20),
            "product_length_cm": "20",
            "product_height_cm": "15",
            "product_width_cm": "10",
        }
        for i in range(1, 51)
    ]
    pd.DataFrame(products).to_csv(olist_dir / "olist_products_dataset.csv", index=False)

    # 5. Orders & Order Items
    base_time = datetime(2024, 1, 10, 10, 0, 0)
    orders = []
    items = []
    payments = []

    for i in range(1, 151):
        order_id = f"order_{i:04d}"
        cust_id = f"cust_{((i - 1) % 100) + 1:04d}"
        purchase_dt = base_time + timedelta(days=i * 2, hours=i % 12)
        approved_dt = purchase_dt + timedelta(hours=1)
        carrier_dt = purchase_dt + timedelta(days=2)
        estimated_dt = purchase_dt + timedelta(days=10)

        # Some orders delivered late for v_delivery_delay_by_seller
        delivered_dt = purchase_dt + (timedelta(days=14) if i % 4 == 0 else timedelta(days=7))

        orders.append({
            "order_id": order_id,
            "customer_id": cust_id,
            "order_status": "delivered",
            "order_purchase_timestamp": purchase_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "order_approved_at": approved_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "order_delivered_carrier_date": carrier_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "order_delivered_customer_date": delivered_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "order_estimated_delivery_date": estimated_dt.strftime("%Y-%m-%d %H:%M:%S"),
        })

        # Order Items
        items.append({
            "order_id": order_id,
            "order_item_id": "1",
            "product_id": f"prod_{((i - 1) % 50) + 1:04d}",
            "seller_id": f"seller_{((i - 1) % 10) + 1:03d}",
            "shipping_limit_date": (purchase_dt + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "price": str(round(49.99 + (i % 20) * 10, 2)),
            "freight_value": "15.00",
        })

        # Payments
        payments.append({
            "order_id": order_id,
            "payment_sequential": "1",
            "payment_type": "credit_card" if i % 2 == 0 else "boleto",
            "payment_installments": "1",
            "payment_value": str(round(49.99 + (i % 20) * 10 + 15.00, 2)),
        })

    pd.DataFrame(orders).to_csv(olist_dir / "olist_orders_dataset.csv", index=False)
    pd.DataFrame(items).to_csv(olist_dir / "olist_order_items_dataset.csv", index=False)
    pd.DataFrame(payments).to_csv(olist_dir / "olist_order_payments_dataset.csv", index=False)
    logger.info(f"Sample Olist files successfully generated in {olist_dir}.")


def ingest_olist_datasets(
    engine: Engine,
    olist_dir: Optional[Path] = None,
) -> Dict[str, int]:
    """Scans for Olist CSVs and ingests each into its corresponding staging table.

    Args:
        engine: Database engine.
        olist_dir: Directory containing Olist CSVs.

    Returns:
        Dict mapping table name to row count ingested.
    """
    folder = olist_dir or (settings.data_raw_dir / "olist")
    csv_files = list(folder.glob("*.csv"))

    if not csv_files:
        logger.info(f"No CSVs found in {folder}. Creating sample Olist dataset...")
        generate_sample_olist_files(folder)
        csv_files = list(folder.glob("*.csv"))

    results: Dict[str, int] = {}
    now = datetime.now(timezone.utc)

    for csv_file in csv_files:
        fname = csv_file.name.lower()
        target_table = None

        if "order_item" in fname or "order_items" in fname:
            target_table = "stg_olist_order_items"
        elif "orders" in fname:
            target_table = "stg_olist_orders"
        elif "customer" in fname:
            target_table = "stg_olist_customers"
        elif "product" in fname and "translation" not in fname:
            target_table = "stg_olist_products"
        elif "payment" in fname:
            target_table = "stg_olist_payments"
        elif "seller" in fname:
            target_table = "stg_olist_sellers"
        elif "translation" in fname or "category" in fname:
            target_table = "stg_olist_category_translation"

        if not target_table:
            logger.warning(f"Unrecognized Olist file '{csv_file.name}', skipping.")
            continue

        logger.info(f"Ingesting {csv_file.name} -> {target_table}...")
        df = pd.read_csv(csv_file, dtype=str, keep_default_na=False)
        df["_source"] = "olist_csv"
        df["_ingested_at"] = now

        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {target_table}"))

        df.to_sql(target_table, engine, if_exists="append", index=False)
        results[target_table] = len(df)
        logger.info(f"Ingested {len(df)} rows into {target_table}.")

    return results
