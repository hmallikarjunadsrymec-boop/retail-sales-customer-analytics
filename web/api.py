"""
Unified Retail Analytics Platform & REST API Server
Integrates the complete corporate portal, 7-view executive analytics dashboard,
RFM machine learning models, and Power BI data exports into a single unified web platform.
"""

import os
import json
import sqlite3
import csv
from collections import defaultdict
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "processed" / "retail_analytics.db")
RFM_CSV_PATH = str(BASE_DIR / "data" / "processed" / "customer_rfm.csv")
POWERBI_DIR = str(BASE_DIR / "data" / "processed" / "powerbi")
REPORTS_DIR = str(BASE_DIR / "reports")
TEMPLATES_DIR = str(BASE_DIR / "web" / "templates")
STATIC_DIR = str(BASE_DIR / "web" / "static")

app = FastAPI(
    title="Retail Sales & Customer Analytics Platform",
    description="Unified Enterprise Analytics Web Platform and REST API",
    version="2.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


_rfm_records_cache = None


def load_rfm_records():
    """Loads and caches customer RFM records from CSV without needing pandas."""
    global _rfm_records_cache
    if _rfm_records_cache is not None:
        return _rfm_records_cache
    if not os.path.exists(RFM_CSV_PATH):
        return []
    records = []
    with open(RFM_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            records.append({
                "CustomerID": int(r["CustomerID"]) if r.get("CustomerID") else 0,
                "Recency": int(r["Recency"]) if r.get("Recency") else 0,
                "Frequency": int(r["Frequency"]) if r.get("Frequency") else 0,
                "Monetary": float(r["Monetary"]) if r.get("Monetary") else 0.0,
                "FirstPurchaseDate": r.get("FirstPurchaseDate", ""),
                "LastPurchaseDate": r.get("LastPurchaseDate", ""),
                "Country": r.get("Country", ""),
                "AvgOrderValue": float(r["AvgOrderValue"]) if r.get("AvgOrderValue") else 0.0,
                "CustomerTenureDays": int(r["CustomerTenureDays"]) if r.get("CustomerTenureDays") else 0,
                "R_Score": int(r["R_Score"]) if r.get("R_Score") else 0,
                "F_Score": int(r["F_Score"]) if r.get("F_Score") else 0,
                "M_Score": int(r["M_Score"]) if r.get("M_Score") else 0,
                "RFM_Score": int(r["RFM_Score"]) if r.get("RFM_Score") else 0,
                "Customer_Segment": r.get("Customer_Segment", ""),
                "KMeans_Cluster": int(r["KMeans_Cluster"]) if r.get("KMeans_Cluster") else 0,
                "Cluster_Name": r.get("Cluster_Name", "")
            })
    _rfm_records_cache = records
    return _rfm_records_cache


@app.get("/", response_class=HTMLResponse)
async def serve_unified_app():
    """Serves the unified Single-Page Web Application & Dashboard."""
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    if not os.path.exists(index_file):
        raise HTTPException(status_code=404, detail="Unified web template not found")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard_redirect():
    """Direct route for dashboard bookmarking."""
    return await serve_unified_app()


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
        "one_time_customers": total_reg - repeat_cnt,
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


@app.get("/api/dow-hour")
async def get_dow_hour_distribution():
    """Returns day of week and hourly distribution for temporal analysis."""
    conn = get_db()
    cursor = conn.cursor()

    dow_query = """
    SELECT day_of_week, COUNT(DISTINCT invoice_no) AS orders, ROUND(SUM(revenue), 2) AS revenue
    FROM sales_transactions
    GROUP BY day_of_week;
    """
    dow_rows = cursor.execute(dow_query).fetchall()

    hour_query = """
    SELECT hour, COUNT(DISTINCT invoice_no) AS orders, ROUND(SUM(revenue), 2) AS revenue
    FROM sales_transactions
    GROUP BY hour
    ORDER BY hour ASC;
    """
    hour_rows = cursor.execute(hour_query).fetchall()
    conn.close()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]
    dow_dict = {r["day_of_week"]: dict(r) for r in dow_rows}
    dow_sorted = [dow_dict.get(d, {"day_of_week": d, "orders": 0, "revenue": 0.0}) for d in day_order]

    return {
        "day_of_week": dow_sorted,
        "hours": [dict(r) for r in hour_rows]
    }


@app.get("/api/order-distribution")
async def get_order_distribution():
    """Returns basket size quartiles and binned distribution."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
    WITH invoice_totals AS (
        SELECT invoice_no, ROUND(SUM(revenue), 2) AS order_total
        FROM sales_transactions
        GROUP BY invoice_no
    )
    SELECT order_total FROM invoice_totals WHERE order_total BETWEEN 1 AND 2500;
    """
    rows = cursor.execute(query).fetchall()
    conn.close()

    values = [r["order_total"] for r in rows]
    if values:
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        mean_aov = round(sum(sorted_vals) / n, 2)
        if n % 2 == 1:
            median_aov = sorted_vals[n // 2]
        else:
            median_aov = round((sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2, 2)
        p75_aov = round(float(sorted_vals[int(0.75 * (n - 1))]), 2)
        p95_aov = round(float(sorted_vals[int(0.95 * (n - 1))]), 2)
    else:
        mean_aov = median_aov = p75_aov = p95_aov = 0.0

    return {
        "mean_aov": mean_aov,
        "median_aov": median_aov,
        "p75_aov": p75_aov,
        "p95_aov": p95_aov,
        "sample_values": values[:500]  # Representative sample for charting
    }


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
    records = load_rfm_records()
    if not records:
        raise HTTPException(status_code=404, detail="RFM dataset not found")

    total_cust = len(records)
    total_rev = sum(r["Monetary"] for r in records)

    # Segment aggregations
    seg_map = defaultdict(lambda: {"count": 0, "rev": 0.0, "rec": 0, "freq": 0, "mon": 0.0})
    for r in records:
        s = seg_map[r["Customer_Segment"]]
        s["count"] += 1
        s["rev"] += r["Monetary"]
        s["rec"] += r["Recency"]
        s["freq"] += r["Frequency"]
        s["mon"] += r["Monetary"]

    seg_summary = []
    for seg, s in sorted(seg_map.items(), key=lambda x: x[1]["rev"], reverse=True):
        cnt = s["count"]
        seg_summary.append({
            "Customer_Segment": seg,
            "Customer_Count": cnt,
            "Total_Revenue": round(s["rev"], 2),
            "Avg_Recency": round(s["rec"] / cnt, 1),
            "Avg_Frequency": round(s["freq"] / cnt, 1),
            "Avg_Monetary": round(s["mon"] / cnt, 2),
            "Cust_Share_Pct": round(cnt / total_cust * 100, 2),
            "Rev_Share_Pct": round(s["rev"] / total_rev * 100, 2)
        })

    # Cluster aggregations
    cluster_map = defaultdict(lambda: {"count": 0, "rec": 0, "freq": 0, "mon": 0.0, "name": ""})
    for r in records:
        k = r["KMeans_Cluster"]
        c = cluster_map[k]
        c["count"] += 1
        c["rec"] += r["Recency"]
        c["freq"] += r["Frequency"]
        c["mon"] += r["Monetary"]
        c["name"] = r["Cluster_Name"]

    cluster_summary = []
    for k, c in sorted(cluster_map.items(), key=lambda x: x[1]["mon"], reverse=True):
        cnt = c["count"]
        cluster_summary.append({
            "KMeans_Cluster": k,
            "Cluster_Name": c["name"],
            "Accounts": cnt,
            "Mean_Recency": round(c["rec"] / cnt, 1),
            "Mean_Frequency": round(c["freq"] / cnt, 1),
            "Mean_Spend": round(c["mon"] / cnt, 2),
            "Total_Spend": round(c["mon"], 2)
        })

    return {
        "segments": seg_summary,
        "clusters": cluster_summary,
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
    records = load_rfm_records()
    if not records:
        raise HTTPException(status_code=404, detail="RFM dataset not found")

    filtered = records
    if segment and segment != "All":
        filtered = [r for r in filtered if r["Customer_Segment"] == segment]

    if search:
        s = search.strip().upper()
        filtered = [
            r for r in filtered
            if s in str(r["CustomerID"]).upper() or s in r["Country"].upper()
        ]

    total_records = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = filtered[start_idx:end_idx]

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


@app.get("/download/powerbi/{filename}")
async def download_powerbi_file(filename: str):
    """Provides downloadable Power BI Star Schema CSV files."""
    file_path = os.path.join(POWERBI_DIR, filename)
    if not os.path.exists(file_path):
        if filename == "FactSales.csv" and os.path.exists(DB_PATH):
            def iter_csv():
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT invoice_no, stock_code, customer_id, invoice_date, quantity, unit_price, revenue, country, category "
                    "FROM sales_transactions"
                )
                yield "InvoiceNo,StockCode,CustomerID,InvoiceDate,Quantity,UnitPrice,Revenue,Country,Category\n"
                while True:
                    batch = cursor.fetchmany(5000)
                    if not batch:
                        break
                    yield "".join(
                        f'"{r[0]}","{r[1]}","{r[2]}","{r[3]}",{r[4]},{r[5]},{r[6]},"{r[7]}","{r[8]}"\n'
                        for r in batch
                    )
                conn.close()

            return StreamingResponse(
                iter_csv(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=FactSales.csv"}
            )
        raise HTTPException(status_code=404, detail="Power BI file not found")
    return FileResponse(file_path, media_type="text/csv", filename=filename)


@app.get("/download/report/{filename}")
async def download_report_file(filename: str):
    """Provides downloadable business insights and implementation guides."""
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(file_path, media_type="text/markdown", filename=filename)
