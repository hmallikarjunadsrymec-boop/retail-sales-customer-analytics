"""
FastAPI Web Application & REST API Server
Powers the corporate analytics website and the real-time interactive analytics dashboard.
"""

import os
import json
import sqlite3
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

DB_PATH = os.path.join("data", "processed", "retail_analytics.db")
RFM_CSV_PATH = os.path.join("data", "processed", "customer_rfm.csv")
TEMPLATES_DIR = os.path.join("web", "templates")
STATIC_DIR = os.path.join("web", "static")

app = FastAPI(
    title="Retail Sales & Customer Analytics Web Platform",
    description="REST API and web interface for retail performance and customer intelligence",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/", response_class=HTMLResponse)
async def serve_website():
    """Serves the main corporate landing website."""
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_file):
        raise HTTPException(status_code=404, detail="Website template not found")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the interactive web analytics dashboard."""
    dash_file = os.path.join(TEMPLATES_DIR, "dashboard.html")
    if not os.path.exists(dash_file):
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    with open(dash_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/kpis")
async def get_kpis(country: str = None, category: str = None):
    """Returns high-level executive KPIs from SQLite."""
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if country and country != "All":
        where_clauses.append("country = ?")
        params.append(country)
    if category and category != "All":
        where_clauses.append("category = ?")
        params.append(category)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    SELECT 
        ROUND(SUM(revenue), 2) AS total_revenue,
        COUNT(DISTINCT invoice_no) AS total_orders,
        COUNT(DISTINCT customer_id) AS total_customers,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS overall_aov
    FROM sales_transactions
    {where_sql};
    """
    row = cursor.execute(query, params).fetchone()

    # Repeat rate calculation
    repeat_query = f"""
    WITH cust_orders AS (
        SELECT customer_id, COUNT(DISTINCT invoice_no) as ord_cnt
        FROM sales_transactions
        {where_sql} {'AND' if where_sql else 'WHERE'} customer_id IS NOT NULL AND customer_id != ''
        GROUP BY customer_id
    )
    SELECT 
        COUNT(CASE WHEN ord_cnt > 1 THEN 1 END) as repeat_count,
        COUNT(*) as total_registered
    FROM cust_orders;
    """
    repeat_row = cursor.execute(repeat_query, params).fetchone()
    conn.close()

    total_reg = repeat_row["total_registered"] or 0
    repeat_cnt = repeat_row["repeat_count"] or 0
    repeat_rate = round((repeat_cnt / total_reg * 100), 2) if total_reg > 0 else 0.0

    return {
        "total_revenue": row["total_revenue"] or 0.0,
        "total_orders": row["total_orders"] or 0,
        "total_customers": row["total_customers"] or 0,
        "total_units_sold": row["total_units_sold"] or 0,
        "overall_aov": row["overall_aov"] or 0.0,
        "repeat_customers": repeat_cnt,
        "repeat_rate_pct": repeat_rate
    }


@app.get("/api/monthly")
async def get_monthly_trend(country: str = None, category: str = None):
    """Returns monthly revenue, order volume, and MoM growth rate."""
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = []
    params = []
    if country and country != "All":
        where_clauses.append("country = ?")
        params.append(country)
    if category and category != "All":
        where_clauses.append("category = ?")
        params.append(category)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    WITH monthly_summary AS (
        SELECT 
            year_month,
            ROUND(SUM(revenue), 2) AS revenue,
            COUNT(DISTINCT invoice_no) AS orders,
            COUNT(DISTINCT customer_id) AS customers,
            SUM(quantity) AS units_sold,
            ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS aov
        FROM sales_transactions
        {where_sql}
        GROUP BY year_month
        ORDER BY year_month ASC
    )
    SELECT 
        year_month,
        revenue,
        orders,
        customers,
        units_sold,
        aov,
        ROUND((revenue - LAG(revenue, 1) OVER (ORDER BY year_month)) / LAG(revenue, 1) OVER (ORDER BY year_month) * 100.0, 2) AS mom_growth_pct
    FROM monthly_summary;
    """
    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [dict(r) for r in rows]


@app.get("/api/top-products")
async def get_top_products(by: str = "revenue", limit: int = 10, category: str = None):
    """Returns top products by revenue or volume."""
    conn = get_db()
    cursor = conn.cursor()

    where_clause = ""
    params = []
    if category and category != "All":
        where_clause = "WHERE category = ?"
        params.append(category)

    order_col = "total_revenue" if by == "revenue" else "total_quantity"
    query = f"""
    SELECT 
        stock_code,
        MAX(description) AS description,
        MAX(category) AS category,
        ROUND(AVG(unit_price), 2) AS avg_price,
        SUM(quantity) AS total_quantity,
        ROUND(SUM(revenue), 2) AS total_revenue,
        COUNT(DISTINCT invoice_no) AS order_count
    FROM sales_transactions
    {where_clause}
    GROUP BY stock_code
    ORDER BY {order_col} DESC
    LIMIT ?;
    """
    params.append(limit)
    rows = cursor.execute(query, params).fetchall()
    conn.close()

    return [dict(r) for r in rows]


@app.get("/api/categories")
async def get_categories():
    """Returns category-level revenue and market share."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT 
        category,
        ROUND(SUM(revenue), 2) AS revenue,
        ROUND(SUM(revenue) * 100.0 / (SELECT SUM(revenue) FROM sales_transactions), 2) AS share_pct,
        SUM(quantity) AS units_sold,
        COUNT(DISTINCT invoice_no) AS orders
    FROM sales_transactions
    GROUP BY category
    ORDER BY revenue DESC;
    """
    rows = cursor.execute(query).fetchall()
    conn.close()

    return [dict(r) for r in rows]


@app.get("/api/countries")
async def get_countries(limit: int = 10):
    """Returns top geographic markets by revenue."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT 
        country,
        ROUND(SUM(revenue), 2) AS revenue,
        ROUND(SUM(revenue) * 100.0 / (SELECT SUM(revenue) FROM sales_transactions), 2) AS share_pct,
        COUNT(DISTINCT invoice_no) AS orders,
        COUNT(DISTINCT customer_id) AS customers,
        ROUND(SUM(revenue) / COUNT(DISTINCT invoice_no), 2) AS aov
    FROM sales_transactions
    GROUP BY country
    ORDER BY revenue DESC
    LIMIT ?;
    """
    rows = cursor.execute(query, (limit,)).fetchall()
    conn.close()

    return [dict(r) for r in rows]


@app.get("/api/rfm")
async def get_rfm_summary():
    """Returns RFM segment statistics and K-Means cluster summaries."""
    if not os.path.exists(RFM_CSV_PATH):
        raise HTTPException(status_code=404, detail="RFM dataset not found")

    df_rfm = pd.read_csv(RFM_CSV_PATH)
    total_rev = df_rfm["Monetary"].sum()
    total_cust = len(df_rfm)

    seg_summary = (
        df_rfm.groupby("Customer_Segment")
        .agg(
            Customer_Count=("CustomerID", "count"),
            Total_Revenue=("Monetary", "sum"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean"),
            Avg_Monetary=("Monetary", "mean")
        )
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
    )
    seg_summary["Cust_Share_Pct"] = (seg_summary["Customer_Count"] / total_cust * 100).round(2)
    seg_summary["Rev_Share_Pct"] = (seg_summary["Total_Revenue"] / total_rev * 100).round(2)
    seg_summary["Total_Revenue"] = seg_summary["Total_Revenue"].round(2)
    seg_summary["Avg_Recency"] = seg_summary["Avg_Recency"].round(1)
    seg_summary["Avg_Frequency"] = seg_summary["Avg_Frequency"].round(1)
    seg_summary["Avg_Monetary"] = seg_summary["Avg_Monetary"].round(2)

    cluster_summary = (
        df_rfm.groupby(["KMeans_Cluster", "Cluster_Name"])
        .agg(
            Accounts=("CustomerID", "count"),
            Mean_Recency=("Recency", "mean"),
            Mean_Frequency=("Frequency", "mean"),
            Mean_Spend=("Monetary", "mean"),
            Total_Spend=("Monetary", "sum")
        )
        .reset_index()
        .sort_values("Total_Spend", ascending=False)
    )
    cluster_summary["Mean_Recency"] = cluster_summary["Mean_Recency"].round(1)
    cluster_summary["Mean_Frequency"] = cluster_summary["Mean_Frequency"].round(1)
    cluster_summary["Mean_Spend"] = cluster_summary["Mean_Spend"].round(2)
    cluster_summary["Total_Spend"] = cluster_summary["Total_Spend"].round(2)

    return {
        "segments": seg_summary.to_dict(orient="records"),
        "clusters": cluster_summary.to_dict(orient="records"),
        "total_customers": total_cust,
        "total_revenue": round(float(total_rev), 2)
    }


@app.get("/api/customers")
async def get_customers(
    segment: str = None,
    search: str = None,
    page: int = 1,
    page_size: int = 25
):
    """Returns paginated customer accounts with RFM details."""
    if not os.path.exists(RFM_CSV_PATH):
        raise HTTPException(status_code=404, detail="RFM dataset not found")

    df_rfm = pd.read_csv(RFM_CSV_PATH)
    filtered = df_rfm

    if segment and segment != "All":
        filtered = filtered[filtered["Customer_Segment"] == segment]

    if search:
        s = search.strip().upper()
        mask = (
            filtered["CustomerID"].astype(str).str.contains(s, na=False) |
            filtered["Country"].astype(str).str.upper().str.contains(s, na=False)
        )
        filtered = filtered[mask]

    total_records = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    page_data = filtered.iloc[start_idx:end_idx].to_dict(orient="records")

    return {
        "total_records": total_records,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_records + page_size - 1) // page_size,
        "data": page_data
    }


@app.get("/api/filters")
async def get_available_filters():
    """Returns lists of countries and categories for dynamic UI dropdowns."""
    conn = get_db()
    cursor = conn.cursor()

    countries = [r["country"] for r in cursor.execute("SELECT DISTINCT country FROM sales_transactions ORDER BY country ASC;").fetchall()]
    categories = [r["category"] for r in cursor.execute("SELECT DISTINCT category FROM sales_transactions ORDER BY category ASC;").fetchall()]
    conn.close()

    return {
        "countries": ["All"] + countries,
        "categories": ["All"] + categories
    }
