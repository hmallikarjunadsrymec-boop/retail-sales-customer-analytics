"""
SQL Analytics Engine Module
Loads cleaned retail data into SQLite, manages analytical queries, and validates SQL vs Python calculations.
"""

import os
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "processed" / "retail_analytics.db")
PARQUET_PATH = str(BASE_DIR / "data" / "processed" / "retail_cleaned.parquet")
CSV_PATH = str(BASE_DIR / "data" / "processed" / "retail_cleaned.csv")
SCHEMA_PATH = str(BASE_DIR / "sql" / "schema.sql")
QUERIES_PATH = str(BASE_DIR / "sql" / "sales_analysis.sql")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Creates a connection to the SQLite database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    return conn


def init_database(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH):
    """Initializes the database schema using sql/schema.sql."""
    conn = get_connection(db_path)
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    print(f"Database schema initialized at {db_path}.")


def load_cleaned_data_to_sql(db_path: str = DB_PATH, data_path: str = None) -> int:
    """
    Ingests cleaned retail transactions from Parquet/CSV into SQLite.
    """
    init_database(db_path)

    if data_path is None:
        data_path = PARQUET_PATH if os.path.exists(PARQUET_PATH) else CSV_PATH

    print(f"Reading cleaned data from {data_path}...")
    if data_path.endswith(".parquet"):
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)

    # Rename columns to match SQL schema snake_case
    column_mapping = {
        "InvoiceNo": "invoice_no",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "UnitPrice": "unit_price",
        "CustomerID": "customer_id",
        "Country": "country",
        "Revenue": "revenue",
        "Date": "date",
        "Year": "year",
        "Month": "month",
        "MonthName": "month_name",
        "YearMonth": "year_month",
        "Quarter": "quarter",
        "DayOfWeek": "day_of_week",
        "Hour": "hour",
        "OrderValue": "order_value",
        "Category": "category"
    }

    df_sql = df[list(column_mapping.keys())].rename(columns=column_mapping).copy()
    df_sql["invoice_date"] = df_sql["invoice_date"].astype(str)
    df_sql["date"] = df_sql["date"].astype(str)

    conn = get_connection(db_path)
    print(f"Ingesting {len(df_sql)} records into sales_transactions table...")
    df_sql.to_sql("sales_transactions", conn, if_exists="append", index=False, chunksize=25000)
    conn.commit()
    conn.close()
    print("Database ingestion complete.")
    return len(df_sql)


def execute_sql_query(query: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """Executes an arbitrary SQL query and returns results as a pandas DataFrame."""
    conn = get_connection(db_path)
    res_df = pd.read_sql_query(query, conn)
    conn.close()
    return res_df


def parse_sql_queries(queries_path: str = QUERIES_PATH) -> dict[str, str]:
    """
    Parses named queries from sql/sales_analysis.sql.
    Each query block starts with '-- Query Name: <name>'.
    """
    with open(queries_path, "r") as f:
        content = f.read()

    queries = {}
    current_name = None
    current_sql = []

    for line in content.splitlines():
        if line.strip().startswith("-- Query Name:"):
            if current_name and current_sql:
                queries[current_name] = "\n".join(current_sql).strip()
            current_name = line.strip().replace("-- Query Name:", "").strip()
            current_sql = []
        elif current_name:
            if not line.strip().startswith("-- ------------------------------------------------------------------------------"):
                current_sql.append(line)

    if current_name and current_sql:
        queries[current_name] = "\n".join(current_sql).strip()

    return queries


def validate_sql_vs_python(db_path: str = DB_PATH) -> dict:
    """
    Reconciles calculations between Pandas and SQLite to guarantee metric integrity.
    """
    df = pd.read_parquet(PARQUET_PATH) if os.path.exists(PARQUET_PATH) else pd.read_csv(CSV_PATH)
    queries = parse_sql_queries()

    # 1. Executive KPIs Reconciliation
    sql_kpi = execute_sql_query(queries["executive_kpis"], db_path).iloc[0]

    py_total_revenue = round(float(df["Revenue"].sum()), 2)
    py_total_orders = int(df["InvoiceNo"].nunique())
    py_total_customers = int(df["CustomerID"].dropna().nunique())
    py_total_units = int(df["Quantity"].sum())
    py_aov = round(py_total_revenue / py_total_orders, 2)

    kpi_checks = {
        "revenue_matches": abs(float(sql_kpi["total_revenue"]) - py_total_revenue) < 0.05,
        "orders_matches": int(sql_kpi["total_orders"]) == py_total_orders,
        "customers_matches": int(sql_kpi["total_registered_customers"]) == py_total_customers,
        "units_matches": int(sql_kpi["total_units_sold"]) == py_total_units,
        "aov_matches": abs(float(sql_kpi["overall_aov"]) - py_aov) < 0.05
    }

    # 2. Monthly Trend Reconciliation
    sql_monthly = execute_sql_query(queries["monthly_sales_trend"], db_path)
    py_monthly = df.groupby("YearMonth")["Revenue"].sum().round(2).reset_index()
    monthly_matches = (sql_monthly["monthly_revenue"].values == py_monthly["Revenue"].values).all()

    # 3. Top Products Reconciliation
    sql_top_prod = execute_sql_query(queries["top_10_products_revenue"], db_path)
    py_top_prod = (
        df.groupby("StockCode")["Revenue"].sum()
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )
    prod_matches = list(sql_top_prod["stock_code"]) == list(py_top_prod["StockCode"])

    all_passed = all(kpi_checks.values()) and bool(monthly_matches) and bool(prod_matches)

    report = {
        "all_checks_passed": all_passed,
        "kpi_checks": kpi_checks,
        "monthly_trend_matches": bool(monthly_matches),
        "top_products_matches": bool(prod_matches),
        "reconciliation_summary": {
            "sql_revenue": float(sql_kpi["total_revenue"]),
            "python_revenue": py_total_revenue,
            "sql_orders": int(sql_kpi["total_orders"]),
            "python_orders": py_total_orders,
            "sql_aov": float(sql_kpi["overall_aov"]),
            "python_aov": py_aov
        }
    }

    return report


if __name__ == "__main__":
    load_cleaned_data_to_sql()
    validation = validate_sql_vs_python()
    print("\n--- SQL vs Python Validation Report ---")
    print(f"All Checks Passed: {validation['all_checks_passed']}")
    for k, v in validation["reconciliation_summary"].items():
        print(f"  {k}: {v}")
