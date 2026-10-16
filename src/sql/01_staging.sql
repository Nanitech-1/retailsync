-- ==============================================================================
-- 01_staging.sql: Staging Tables for RetailSync Multi-Source Ingestion
-- ==============================================================================

-- Olist Orders Staging
CREATE TABLE IF NOT EXISTS stg_olist_orders (
    order_id VARCHAR(64),
    customer_id VARCHAR(64),
    order_status VARCHAR(32),
    order_purchase_timestamp VARCHAR(32),
    order_approved_at VARCHAR(32),
    order_delivered_carrier_date VARCHAR(32),
    order_delivered_customer_date VARCHAR(32),
    order_estimated_delivery_date VARCHAR(32),
    _source VARCHAR(64) DEFAULT 'olist_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Olist Order Items Staging
CREATE TABLE IF NOT EXISTS stg_olist_order_items (
    order_id VARCHAR(64),
    order_item_id VARCHAR(16),
    product_id VARCHAR(64),
    seller_id VARCHAR(64),
    shipping_limit_date VARCHAR(32),
    price VARCHAR(32),
    freight_value VARCHAR(32),
    _source VARCHAR(64) DEFAULT 'olist_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Olist Customers Staging
CREATE TABLE IF NOT EXISTS stg_olist_customers (
    customer_id VARCHAR(64),
    customer_unique_id VARCHAR(64),
    customer_zip_code_prefix VARCHAR(16),
    customer_city VARCHAR(128),
    customer_state VARCHAR(16),
    _source VARCHAR(64) DEFAULT 'olist_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Olist Products Staging
CREATE TABLE IF NOT EXISTS stg_olist_products (
    product_id VARCHAR(64),
    product_category_name VARCHAR(128),
    product_name_lenght VARCHAR(32),
    product_description_lenght VARCHAR(32),
    product_photos_qty VARCHAR(32),
    product_weight_g VARCHAR(32),
    product_length_cm VARCHAR(32),
    product_height_cm VARCHAR(32),
    product_width_cm VARCHAR(32),
    _source VARCHAR(64) DEFAULT 'olist_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Olist Payments Staging
CREATE TABLE IF NOT EXISTS stg_olist_payments (
    order_id VARCHAR(64),
    payment_sequential VARCHAR(16),
    payment_type VARCHAR(32),
    payment_installments VARCHAR(16),
    payment_value VARCHAR(32),
    _source VARCHAR(64) DEFAULT 'olist_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Olist Sellers Staging
CREATE TABLE IF NOT EXISTS stg_olist_sellers (
    seller_id VARCHAR(64),
    seller_zip_code_prefix VARCHAR(16),
    seller_city VARCHAR(128),
    seller_state VARCHAR(16),
    _source VARCHAR(64) DEFAULT 'olist_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Olist Category Name Translation
CREATE TABLE IF NOT EXISTS stg_olist_category_translation (
    product_category_name VARCHAR(128),
    product_category_name_english VARCHAR(128),
    _source VARCHAR(64) DEFAULT 'olist_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Live API Products Staging (https://dummyjson.com/products)
CREATE TABLE IF NOT EXISTS stg_api_products (
    api_id VARCHAR(32),
    title VARCHAR(256),
    description TEXT,
    price VARCHAR(32),
    discount_percentage VARCHAR(32),
    rating VARCHAR(32),
    stock VARCHAR(32),
    brand VARCHAR(128),
    category VARCHAR(128),
    thumbnail TEXT,
    _source VARCHAR(64) DEFAULT 'dummyjson_api',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messy Supplier Products Staging
CREATE TABLE IF NOT EXISTS stg_supplier_products (
    supplier_sku VARCHAR(64),
    raw_title TEXT,
    raw_category VARCHAR(128),
    raw_price VARCHAR(32),
    supplier_name VARCHAR(128),
    feed_date VARCHAR(64),
    stock_level VARCHAR(32),
    _source VARCHAR(64) DEFAULT 'supplier_csv',
    _ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quarantined Rejected Records
CREATE TABLE IF NOT EXISTS rejected_records (
    id SERIAL PRIMARY KEY,
    source VARCHAR(64) NOT NULL,
    table_name VARCHAR(64) NOT NULL,
    row_data TEXT NOT NULL,
    rule_failed VARCHAR(128) NOT NULL,
    reason TEXT NOT NULL,
    run_id VARCHAR(64) NOT NULL,
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rejected_run_id ON rejected_records(run_id);
CREATE INDEX IF NOT EXISTS idx_rejected_rule ON rejected_records(rule_failed);
