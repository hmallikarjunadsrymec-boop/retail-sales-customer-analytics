-- ==============================================================================
-- RETAIL SALES & CUSTOMER ANALYTICS PLATFORM
-- SQLite & ANSI/MySQL-Compatible Database Schema
-- ==============================================================================

DROP TABLE IF EXISTS sales_transactions;

CREATE TABLE sales_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    invoice_date TEXT NOT NULL,
    unit_price REAL NOT NULL,
    customer_id TEXT,
    country TEXT NOT NULL,
    revenue REAL NOT NULL,
    date TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    year_month TEXT NOT NULL,
    quarter TEXT NOT NULL,
    day_of_week TEXT NOT NULL,
    hour INTEGER NOT NULL,
    order_value REAL NOT NULL,
    category TEXT NOT NULL
);

-- Performance Indexes for Analytics Queries
CREATE INDEX idx_sales_invoice ON sales_transactions (invoice_no);
CREATE INDEX idx_sales_customer ON sales_transactions (customer_id);
CREATE INDEX idx_sales_stock ON sales_transactions (stock_code);
CREATE INDEX idx_sales_date ON sales_transactions (invoice_date);
CREATE INDEX idx_sales_year_month ON sales_transactions (year_month);
CREATE INDEX idx_sales_country ON sales_transactions (country);
CREATE INDEX idx_sales_category ON sales_transactions (category);
