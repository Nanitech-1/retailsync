"""Generates a messy supplier CSV dataset with deliberate data quality anomalies.

Used as one of the 3 ingestion sources in RetailSync to test validation,
quarantine rules, and LLM text standardization.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Common DummyJSON titles to ensure match for v_supplier_vs_api_price_comparison
REAL_TITLES = [
    ("Essence Mascara Lash Princess", "Beauty", 9.99),
    ("Eyeshadow Palette with Mirror", "Beauty", 19.99),
    ("Powder Canister", "Beauty", 14.99),
    ("Red Lipstick", "Beauty", 12.99),
    ("Red Nail Polish", "Beauty", 8.99),
    ("Calvin Klein CK One", "Fragrances", 49.99),
    ("Chanel Coco Noir Eau De", "Fragrances", 129.99),
    ("Dior J'adore", "Fragrances", 89.99),
    ("Dolce Shine Eau de", "Fragrances", 69.99),
    ("Gucci Bloom Eau de", "Fragrances", 79.99),
    ("Annibale Colombo Bed", "Furniture", 1899.99),
    ("Annibale Colombo Sofa", "Furniture", 2499.99),
    ("Bedside Table African Cherry", "Furniture", 299.99),
    ("Knoll Saarinen Executive Chair", "Furniture", 499.99),
    ("Wooden Bathroom Sink With Mirror", "Furniture", 799.99),
]

CATEGORY_VARIANTS = {
    "Beauty": ["Beauty", "beauty ", " BEAUTY", "BEAUTY", "Cosmetics", "cosmetics"],
    "Fragrances": ["Fragrances", "fragrance ", "PERFUMES", "fragrances", "Scent"],
    "Furniture": ["Furniture", "furniture ", "FURNITURE", "Home Furniture", "home-furniture"],
    "Electronics": ["Electronics", "ELECTRONIC", "electronics ", " Gadgets", "ELEC"],
    "Kitchen": ["Kitchen", "Home & Kitchen", "home_kitchen", "KITCHEN", "Kitchenware"],
}

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m-%d-%Y",
    "%Y/%m/%d %H:%M:%S",
    "%d-%b-%Y",
]

SUPPLIERS = [
    "Apex Global Logistics",
    "Nordic Retail Supply",
    "Pacific Wholesale Co",
    "Vertex Distribution",
    "Delta Trade Partners",
]


def generate_supplier_data(output_path: Path, num_rows: int = 2000) -> None:
    """Generates synthetic messy supplier product data.

    Args:
        output_path: Path to save the generated CSV.
        num_rows: Number of records to create (~2000 default).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    random.seed(42)

    rows = []
    base_date = datetime(2024, 1, 1)

    # 1. First inject matching product titles from DummyJSON with deliberate price variations
    copies_per_title = max(1, (num_rows // 4) // max(1, len(REAL_TITLES)))
    for title, cat, true_price in REAL_TITLES:
        if len(rows) >= num_rows // 3:
            break
        for _ in range(copies_per_title):
            if len(rows) >= num_rows:
                break
            sku = f"SUP-REAL-{abs(hash(title)) % 100000:05d}"
            cat_choice = random.choice(CATEGORY_VARIANTS.get(cat, [cat]))
            price_val = round(true_price * random.uniform(0.85, 1.25), 2)
            d_fmt = random.choice(DATE_FORMATS)
            feed_dt = (base_date + timedelta(days=random.randint(1, 300))).strftime(d_fmt)

            rows.append({
                "supplier_sku": sku,
                "raw_title": title if random.random() > 0.1 else f"  {title.lower()}  ",
                "raw_category": cat_choice,
                "raw_price": str(price_val),
                "supplier_name": random.choice(SUPPLIERS),
                "feed_date": feed_dt,
                "stock_level": str(random.randint(5, 500)),
            })

    # 2. Generate remaining random rows up to num_rows with anomalies
    categories_keys = list(CATEGORY_VARIANTS.keys())
    sku_pool = [f"SKU-{i:05d}" for i in range(1, int(num_rows * 0.75))]

    while len(rows) < num_rows:
        # Deliberate duplicate SKU rate (~10%)
        sku = random.choice(sku_pool)
        cat_key = random.choice(categories_keys)
        raw_cat = random.choice(CATEGORY_VARIANTS[cat_key])
        supplier = random.choice(SUPPLIERS)

        # Base price
        base_price = round(random.uniform(5.0, 500.0), 2)

        # Anomaly injections
        anomaly_roll = random.random()
        if anomaly_roll < 0.05:
            # Missing price (null / empty)
            raw_price = ""
        elif anomaly_roll < 0.09:
            # Negative price
            raw_price = str(-abs(base_price))
        elif anomaly_roll < 0.12:
            # Non-numeric corrupted price
            raw_price = "N/A"
        else:
            raw_price = str(base_price)

        # Feed date formatting
        d_fmt = random.choice(DATE_FORMATS)
        rand_dt = base_date + timedelta(days=random.randint(0, 365))
        feed_date_str = rand_dt.strftime(d_fmt) if random.random() > 0.03 else "INVALID_DATE"

        # Raw title with occasional weird casing or null
        if random.random() < 0.03:
            raw_title = ""
        else:
            raw_title = f"{supplier.split()[0]} {cat_key} Item {sku[-4:]}"
            if random.random() < 0.2:
                raw_title = raw_title.upper()
            elif random.random() < 0.2:
                raw_title = f"   {raw_title.lower()}   "

        # Stock level with occasional negative/missing
        if random.random() < 0.04:
            stock = ""
        elif random.random() < 0.02:
            stock = "-10"
        else:
            stock = str(random.randint(0, 1000))

        rows.append({
            "supplier_sku": sku,
            "raw_title": raw_title,
            "raw_category": raw_cat,
            "raw_price": raw_price,
            "supplier_name": supplier,
            "feed_date": feed_date_str,
            "stock_level": stock,
        })

    # Shuffle rows so anomalies are distributed
    random.shuffle(rows)

    fieldnames = [
        "supplier_sku",
        "raw_title",
        "raw_category",
        "raw_price",
        "supplier_name",
        "feed_date",
        "stock_level",
    ]

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully generated {len(rows)} supplier records at: {output_path}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.config import settings
    target_csv = settings.data_raw_dir / "supplier_products.csv"
    generate_supplier_data(target_csv, num_rows=2000)
