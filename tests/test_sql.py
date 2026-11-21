"""
Unit Tests: SQL Engine & Metric Reconciliation
Validates that SQLite analytical queries produce results 100% consistent with Python.
"""

import os
import sqlite3
import pytest
import pandas as pd
from src.sql_engine import (
    DB_PATH,
    get_connection,
    execute_sql_query,
    parse_sql_queries,
    validate_sql_vs_python
)


def test_database_connection_and_table_exists():
    """Verifies that SQLite database is online and sales_transactions table exists."""
    assert os.path.exists(DB_PATH), "Database file does not exist."
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_transactions';")
    table = cursor.fetchone()
    conn.close()
    assert table is not None, "sales_transactions table does not exist in SQLite database."


def test_sql_vs_python_executive_kpis():
    """Asserts that SQLite executive KPIs reconcile with Python calculations."""
    report = validate_sql_vs_python()
    assert report["kpi_checks"]["revenue_matches"], "SQL revenue does not match Python revenue."
    assert report["kpi_checks"]["orders_matches"], "SQL order count does not match Python order count."
    assert report["kpi_checks"]["customers_matches"], "SQL customer count does not match Python customer count."
    assert report["kpi_checks"]["units_matches"], "SQL units sold count does not match Python units sold."
    assert report["kpi_checks"]["aov_matches"], "SQL AOV does not match Python AOV."


def test_sql_vs_python_monthly_trend():
    """Asserts that monthly revenue totals in SQL exactly match Python."""
    report = validate_sql_vs_python()
    assert report["monthly_trend_matches"], "Monthly trend revenue mismatch between SQL and Python."


def test_sql_vs_python_top_products():
    """Asserts that top 10 products by revenue in SQL match Python ranking."""
    report = validate_sql_vs_python()
    assert report["top_products_matches"], "Top products ranking mismatch between SQL and Python."


def test_sql_mom_growth_window_function():
    """Verifies that the SQL LAG() window function correctly calculates month-over-month growth."""
    queries = parse_sql_queries()
    df_mom = execute_sql_query(queries["mom_revenue_growth"])
    assert "mom_growth_pct" in df_mom.columns
    assert len(df_mom) >= 12
    # First month should have NULL previous revenue and NULL growth
    assert pd.isna(df_mom.iloc[0]["previous_month_revenue"])
    assert pd.isna(df_mom.iloc[0]["mom_growth_pct"])
    # Second month must have valid calculated float values
    assert not pd.isna(df_mom.iloc[1]["previous_month_revenue"])
    assert not pd.isna(df_mom.iloc[1]["mom_growth_pct"])
