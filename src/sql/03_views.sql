-- ==============================================================================
-- 03_views.sql: Analytics Views for Business Reporting
-- ==============================================================================

-- 1. Monthly Revenue by Category with Month-over-Month Growth (LAG)
DROP VIEW IF EXISTS v_revenue_by_category_monthly;
CREATE VIEW v_revenue_by_category_monthly AS
WITH monthly_category_revenue AS (
    SELECT
        d.year,
        d.month,
        COALESCE(p.standardized_category, p.product_category_name_english, 'uncategorized') AS category,
        ROUND(SUM(f.price), 2) AS total_revenue,
        COUNT(DISTINCT f.order_id) AS total_orders
    FROM fact_orders f
    JOIN dim_date d ON f.order_date_key = d.date_key
    LEFT JOIN dim_products p ON f.product_key = p.product_key
    GROUP BY d.year, d.month, category
)
SELECT
    year,
    month,
    category,
    total_revenue,
    total_orders,
    LAG(total_revenue) OVER (PARTITION BY category ORDER BY year, month) AS prev_month_revenue,
    ROUND(
        (total_revenue - LAG(total_revenue) OVER (PARTITION BY category ORDER BY year, month))
        / NULLIF(LAG(total_revenue) OVER (PARTITION BY category ORDER BY year, month), 0) * 100.0, 2
    ) AS mom_growth_pct
FROM monthly_category_revenue;

-- 2. Top Products by Category using DENSE_RANK()
DROP VIEW IF EXISTS v_top_products_by_category;
CREATE VIEW v_top_products_by_category AS
WITH product_sales AS (
    SELECT
        p.product_key,
        COALESCE(p.standardized_title, p.product_id) AS product_name,
        COALESCE(p.standardized_category, p.product_category_name_english, 'uncategorized') AS category,
        ROUND(SUM(f.price), 2) AS total_sales,
        COUNT(f.order_item_key) AS units_sold
    FROM fact_orders f
    JOIN dim_products p ON f.product_key = p.product_key
    GROUP BY p.product_key, product_name, category
)
SELECT
    category,
    product_key,
    product_name,
    total_sales,
    units_sold,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_sales DESC) AS sales_rank
FROM product_sales;

-- 3. Repeat Customer Rate (Orders > 1)
DROP VIEW IF EXISTS v_repeat_customer_rate;
CREATE VIEW v_repeat_customer_rate AS
WITH customer_order_counts AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT f.order_id) AS order_count
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_key = c.customer_key
    WHERE c.customer_unique_id IS NOT NULL
    GROUP BY c.customer_unique_id
)
SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(
        SUM(CASE WHEN order_count > 1 THEN 1.0 ELSE 0.0 END) / NULLIF(COUNT(*), 0) * 100.0,
        2
    ) AS repeat_customer_percentage
FROM customer_order_counts;

-- 4. Delivery Delay Analysis by Seller (Late vs Estimated Delivery)
DROP VIEW IF EXISTS v_delivery_delay_by_seller;
CREATE VIEW v_delivery_delay_by_seller AS
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(f.order_item_key) AS total_orders_delivered,
    SUM(CASE WHEN f.is_late_delivery THEN 1 ELSE 0 END) AS late_deliveries,
    ROUND(
        AVG(f.days_to_delivery), 2
    ) AS avg_delivery_days,
    ROUND(
        SUM(CASE WHEN f.is_late_delivery THEN 1.0 ELSE 0.0 END) / NULLIF(COUNT(f.order_item_key), 0) * 100.0,
        2
    ) AS late_delivery_rate_pct
FROM fact_orders f
JOIN dim_sellers s ON f.seller_key = s.seller_key
WHERE f.order_delivered_customer_date IS NOT NULL
GROUP BY s.seller_id, s.seller_city, s.seller_state;

-- 5. Supplier vs Live API Price Comparison
DROP VIEW IF EXISTS v_supplier_vs_api_price_comparison;
CREATE VIEW v_supplier_vs_api_price_comparison AS
SELECT
    s.supplier_sku,
    s.raw_title AS supplier_product_title,
    ROUND(CAST(s.raw_price AS NUMERIC), 2) AS supplier_price,
    a.title AS api_product_title,
    ROUND(CAST(a.price AS NUMERIC), 2) AS api_price,
    ROUND(CAST(s.raw_price AS NUMERIC) - CAST(a.price AS NUMERIC), 2) AS price_difference,
    ROUND(
        (CAST(s.raw_price AS NUMERIC) - CAST(a.price AS NUMERIC)) / NULLIF(CAST(a.price AS NUMERIC), 0) * 100.0,
        2
    ) AS price_difference_pct
FROM stg_supplier_products s
JOIN stg_api_products a ON LOWER(TRIM(s.raw_title)) = LOWER(TRIM(a.title))
WHERE s.raw_price IS NOT NULL AND a.price IS NOT NULL;
