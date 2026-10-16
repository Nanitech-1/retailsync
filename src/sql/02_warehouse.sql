-- ==============================================================================
-- 02_warehouse.sql: Star Schema Dimension and Fact Tables
-- ==============================================================================

-- LLM Enrichment Cache
CREATE TABLE IF NOT EXISTS llm_cache (
    raw_text VARCHAR(256) PRIMARY KEY,
    standardized_category VARCHAR(128),
    standardized_title VARCHAR(256),
    provider VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Customers
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_key VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) UNIQUE,
    customer_unique_id VARCHAR(64),
    customer_zip_code VARCHAR(16),
    customer_city VARCHAR(128),
    customer_state VARCHAR(16),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dim_cust_unique ON dim_customers(customer_unique_id);

-- Dimension: Products
CREATE TABLE IF NOT EXISTS dim_products (
    product_key VARCHAR(64) PRIMARY KEY,
    product_id VARCHAR(64) UNIQUE,
    product_category_name VARCHAR(128),
    product_category_name_english VARCHAR(128),
    standardized_category VARCHAR(128),
    standardized_title VARCHAR(256),
    price NUMERIC(12, 2),
    source VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dim_prod_cat ON dim_products(standardized_category);

-- Dimension: Sellers
CREATE TABLE IF NOT EXISTS dim_sellers (
    seller_key VARCHAR(64) PRIMARY KEY,
    seller_id VARCHAR(64) UNIQUE,
    seller_zip_code VARCHAR(16),
    seller_city VARCHAR(128),
    seller_state VARCHAR(16),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_key DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Fact: Orders (Order Items Grain)
CREATE TABLE IF NOT EXISTS fact_orders (
    order_item_key VARCHAR(128) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    order_item_id INTEGER NOT NULL,
    customer_key VARCHAR(64),
    product_key VARCHAR(64),
    seller_key VARCHAR(64),
    order_status VARCHAR(32),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    price NUMERIC(12, 2),
    freight_value NUMERIC(12, 2),
    payment_value NUMERIC(12, 2),
    payment_type VARCHAR(32),
    order_date_key DATE,
    days_to_delivery NUMERIC(8, 2),
    is_late_delivery BOOLEAN,
    run_id VARCHAR(64),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_key) REFERENCES dim_customers(customer_key),
    CONSTRAINT fk_fact_product FOREIGN KEY (product_key) REFERENCES dim_products(product_key),
    CONSTRAINT fk_fact_seller FOREIGN KEY (seller_key) REFERENCES dim_sellers(seller_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_cust_key ON fact_orders(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_prod_key ON fact_orders(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sell_key ON fact_orders(seller_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_date ON fact_orders(order_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_id ON fact_orders(order_id);
