"""
Dashboard Data Access & Caching Layer
Loads cleaned sales data and RFM customer profiles with high-performance caching.
"""

import os
import pandas as pd
import streamlit as st

PROCESSED_PARQUET = os.path.join("data", "processed", "retail_cleaned.parquet")
PROCESSED_CSV = os.path.join("data", "processed", "retail_cleaned.csv")
RFM_PARQUET = os.path.join("data", "processed", "customer_rfm.parquet")
RFM_CSV = os.path.join("data", "processed", "customer_rfm.csv")


@st.cache_data(show_spinner="Loading transactions data...")
def load_sales_data() -> pd.DataFrame:
    """Loads cleaned retail transactions into memory with Parquet acceleration."""
    if os.path.exists(PROCESSED_PARQUET):
        df = pd.read_parquet(PROCESSED_PARQUET)
    elif os.path.exists(PROCESSED_CSV):
        df = pd.read_csv(PROCESSED_CSV)
    else:
        raise FileNotFoundError("Processed retail sales data not found. Please run src/data_cleaner.py first.")

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    return df


@st.cache_data(show_spinner="Loading RFM customer segmentation...")
def load_rfm_data() -> pd.DataFrame:
    """Loads RFM customer segments and cluster profiles."""
    if os.path.exists(RFM_PARQUET):
        df = pd.read_parquet(RFM_PARQUET)
    elif os.path.exists(RFM_CSV):
        df = pd.read_csv(RFM_CSV)
    else:
        raise FileNotFoundError("RFM customer dataset not found. Please run src/segmentation.py first.")

    return df


def filter_sales_data(
    df: pd.DataFrame,
    start_date=None,
    end_date=None,
    selected_countries: list = None,
    selected_categories: list = None
) -> pd.DataFrame:
    """Applies interactive sidebar filters to the transactions dataframe."""
    filtered = df

    if start_date and end_date:
        filtered = filtered[(filtered["Date"] >= start_date) & (filtered["Date"] <= end_date)]

    if selected_countries:
        filtered = filtered[filtered["Country"].isin(selected_countries)]

    if selected_categories:
        filtered = filtered[filtered["Category"].isin(selected_categories)]

    return filtered
