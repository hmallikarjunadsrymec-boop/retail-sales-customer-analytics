-- ==============================================================================
-- RETAIL SALES & CUSTOMER ANALYTICS PLATFORM
-- SQL Analytical Queries Suite (SQLite & ANSI / MySQL Compatible)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXECUTIVE KPI SUMMARY
-- Computes Total Gross Revenue, Total Orders, Units Sold, Active Customers, and Overall AOV
-- ------------------------------------------------------------------------------
-- Query Name: executive_kpis
SELECT 
    ROUND(SUM(revenue), 2) AS total_revenue,
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS total_registered_customers,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS overall_aov
FROM sales_transactions;


-- ------------------------------------------------------------------------------
-- 2. MONTHLY REVENUE & ORDER TRENDS
-- Aggregates monthly performance metrics
-- ------------------------------------------------------------------------------
-- Query Name: monthly_sales_trend
SELECT 
    year_month,
    ROUND(SUM(revenue), 2) AS monthly_revenue,
    COUNT(DISTINCT invoice_no) AS total_orders,
    COUNT(DISTINCT customer_id) AS active_customers,
    SUM(quantity) AS units_sold,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS monthly_aov
FROM sales_transactions
GROUP BY year_month
ORDER BY year_month ASC;


-- ------------------------------------------------------------------------------
-- 3. MONTH-OVER-MONTH (MoM) REVENUE GROWTH RATE
-- Uses SQL Window Function LAG() to calculate month-over-month percentage change
-- ------------------------------------------------------------------------------
-- Query Name: mom_revenue_growth
WITH monthly_metrics AS (
    SELECT 
        year_month,
        ROUND(SUM(revenue), 2) AS current_month_revenue,
        COUNT(DISTINCT invoice_no) AS total_orders
    FROM sales_transactions
    GROUP BY year_month
)
SELECT 
    year_month,
    current_month_revenue,
    LAG(current_month_revenue, 1) OVER (ORDER BY year_month) AS previous_month_revenue,
    ROUND(
        (current_month_revenue - LAG(current_month_revenue, 1) OVER (ORDER BY year_month)) 
        / LAG(current_month_revenue, 1) OVER (ORDER BY year_month) * 100.0, 
        2
    ) AS mom_growth_pct,
    total_orders
FROM monthly_metrics
ORDER BY year_month ASC;


-- ------------------------------------------------------------------------------
-- 4. TOP 10 REVENUE-GENERATING PRODUCTS
-- Identifies hero inventory driving business top-line
-- ------------------------------------------------------------------------------
-- Query Name: top_10_products_revenue
SELECT 
    stock_code,
    MAX(description) AS description,
    MAX(category) AS category,
    SUM(quantity) AS total_quantity_sold,
    ROUND(AVG(unit_price), 2) AS avg_unit_price,
    ROUND(SUM(revenue), 2) AS total_revenue,
    COUNT(DISTINCT invoice_no) AS order_appearances
FROM sales_transactions
GROUP BY stock_code
ORDER BY total_revenue DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- 5. TOP 10 BEST-SELLING PRODUCTS BY VOLUME
-- High-velocity merchandise by total units dispatched
-- ------------------------------------------------------------------------------
-- Query Name: top_10_products_volume
SELECT 
    stock_code,
    MAX(description) AS description,
    MAX(category) AS category,
    SUM(quantity) AS total_quantity_sold,
    ROUND(SUM(revenue), 2) AS total_revenue,
    COUNT(DISTINCT invoice_no) AS order_appearances
FROM sales_transactions
GROUP BY stock_code
ORDER BY total_quantity_sold DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- 6. TOP 10 HIGH-VALUE CUSTOMERS
-- Ranks accounts by cumulative spend, order frequency, and average ticket size
-- ------------------------------------------------------------------------------
-- Query Name: top_10_customers
SELECT 
    customer_id,
    country,
    COUNT(DISTINCT invoice_no) AS total_orders,
    SUM(quantity) AS total_items_purchased,
    ROUND(SUM(revenue), 2) AS total_spend,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS customer_aov,
    MIN(date) AS first_purchase_date,
    MAX(date) AS last_purchase_date
FROM sales_transactions
WHERE customer_id IS NOT NULL AND customer_id != ''
GROUP BY customer_id, country
ORDER BY total_spend DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- 7. AVERAGE ORDER VALUE (AOV) DISTRIBUTION STATS
-- Aggregates invoice-level spend into order summary
-- ------------------------------------------------------------------------------
-- Query Name: invoice_aov_summary
WITH invoice_totals AS (
    SELECT 
        invoice_no,
        customer_id,
        country,
        ROUND(SUM(revenue), 2) AS invoice_revenue,
        SUM(quantity) AS invoice_quantity
    FROM sales_transactions
    GROUP BY invoice_no, customer_id, country
)
SELECT 
    ROUND(AVG(invoice_revenue), 2) AS avg_order_value,
    ROUND(MIN(invoice_revenue), 2) AS min_order_value,
    ROUND(MAX(invoice_revenue), 2) AS max_order_value,
    ROUND(AVG(invoice_quantity), 1) AS avg_items_per_order,
    COUNT(invoice_no) AS total_invoices
FROM invoice_totals;


-- ------------------------------------------------------------------------------
-- 8. CUSTOMER RETENTION & REPEAT PURCHASE BEHAVIOR
-- Analyzes frequency distribution (Single vs Multi-order customers)
-- ------------------------------------------------------------------------------
-- Query Name: customer_repeat_behavior
WITH customer_order_counts AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT invoice_no) AS order_count,
        SUM(revenue) AS total_spend
    FROM sales_transactions
    WHERE customer_id IS NOT NULL AND customer_id != ''
    GROUP BY customer_id
),
customer_segments AS (
    SELECT 
        customer_id,
        order_count,
        total_spend,
        CASE 
            WHEN order_count = 1 THEN 'One-Time Buyer'
            WHEN order_count BETWEEN 2 AND 5 THEN 'Repeat Buyer (2-5 Orders)'
            ELSE 'Frequent Buyer (>5 Orders)'
        END AS buyer_type
    FROM customer_order_counts
)
SELECT 
    buyer_type,
    COUNT(customer_id) AS customer_count,
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM customer_order_counts), 2) AS customer_share_pct,
    ROUND(SUM(total_spend), 2) AS total_segment_revenue,
    ROUND(SUM(total_spend) * 100.0 / (SELECT SUM(revenue) FROM sales_transactions WHERE customer_id IS NOT NULL), 2) AS revenue_share_pct,
    ROUND(AVG(order_count), 2) AS avg_orders_per_customer,
    ROUND(AVG(total_spend), 2) AS avg_spend_per_customer
FROM customer_segments
GROUP BY buyer_type
ORDER BY customer_count DESC;


-- ------------------------------------------------------------------------------
-- 9. COUNTRY-WISE GEOGRAPHIC PERFORMANCE
-- Ranks global markets by revenue, customer base, and average revenue per order
-- ------------------------------------------------------------------------------
-- Query Name: country_sales_performance
SELECT 
    country,
    ROUND(SUM(revenue), 2) AS country_revenue,
    ROUND(SUM(revenue) * 100.0 / (SELECT SUM(revenue) FROM sales_transactions), 2) AS revenue_share_pct,
    COUNT(DISTINCT invoice_no) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count,
    ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS aov
FROM sales_transactions
GROUP BY country
ORDER BY country_revenue DESC;


-- ------------------------------------------------------------------------------
-- 10. PRODUCT CATEGORY PERFORMANCE
-- Evaluates category volume, revenue contribution, and average selling price
-- ------------------------------------------------------------------------------
-- Query Name: category_performance
SELECT 
    category,
    ROUND(SUM(revenue), 2) AS category_revenue,
    ROUND(SUM(revenue) * 100.0 / (SELECT SUM(revenue) FROM sales_transactions), 2) AS revenue_share_pct,
    SUM(quantity) AS units_sold,
    COUNT(DISTINCT invoice_no) AS orders_containing_category,
    ROUND(SUM(revenue) / SUM(quantity), 2) AS avg_realized_unit_price
FROM sales_transactions
GROUP BY category
ORDER BY category_revenue DESC;
