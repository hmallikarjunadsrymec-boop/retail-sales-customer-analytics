"""
Data Cleaning Module
Provides a robust, reproducible data cleaning and feature engineering pipeline for retail sales data.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

CLEANED_CSV_PATH = os.path.join("data", "processed", "retail_cleaned.csv")
CLEANED_PARQUET_PATH = os.path.join("data", "processed", "retail_cleaned.parquet")
RETURNS_CSV_PATH = os.path.join("data", "processed", "retail_cancellations.csv")
CLEANING_METADATA_PATH = os.path.join("data", "processed", "cleaning_summary.json")

ADMIN_STOCK_CODES = {
    "POST", "D", "M", "BANK CHARGES", "AMAZONFEE",
    "CRUK", "DOT", "B", "PADS", "S"
}


def map_category(desc: str) -> str:
    """
    Classifies a product description into a standard retail category.
    """
    if pd.isna(desc):
        return "General Merchandise"
    d = str(desc).upper()
    if any(k in d for k in ["BAG", "TOTE", "SHOPPER", "LUNCH BAG", "JUMBO", "BACKPACK", "PURSE"]):
        return "Bags & Luggage"
    if any(k in d for k in ["MUG", "CUP", "TEA", "BOWL", "PLATE", "BAKE", "CAKE", "JAR", "BOTTLE",
                            "PANTRY", "KITCHEN", "CUTLERY", "SPOON", "FORK", "DISH", "COFFEE"]):
        return "Kitchen & Dining"
    if any(k in d for k in ["HEART", "LANTERN", "CLOCK", "FRAME", "CANDLE", "HANGER", "LIGHT",
                            "CUSHION", "MIRROR", "DOORMAT", "SIGN", "WALL", "ORNAMENT", "VINTAGE"]):
        return "Home Decor"
    if any(k in d for k in ["CHRISTMAS", "XMAS", "TREE", "WARMER", "ADVENT", "SNOW",
                            "HOTTIE", "SANTA", "EASTER", "HALLOWEEN"]):
        return "Seasonal & Holiday"
    if any(k in d for k in ["TOY", "GAME", "BLOCK", "BOXES", "BABUSHKA", "DOLL",
                            "PUZZLE", "PLAYHOUSE", "CHILD", "TEDDY"]):
        return "Toys & Games"
    if any(k in d for k in ["NOTEBOOK", "CARD", "STICKER", "PENCIL", "PEN", "PAPER",
                            "RIBBON", "TAPE", "WRAP", "ALBUM", "STAMP", "BOOK"]):
        return "Stationery & Craft"
    if any(k in d for k in ["NECKLACE", "BRACELET", "EARRING", "RING", "SCARF", "JEWEL"]):
        return "Jewelry & Accessories"
    return "General Merchandise"


def clean_retail_data(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Executes end-to-end cleaning and feature engineering:
    - Identifies duplicates and invalid values
    - Separates cancellations and returns
    - Imputes missing descriptions where possible
    - Formats dates and builds temporal features
    - Computes revenue and order value metrics
    - Standardizes customer identifiers
    - Emits clean sales data and cancellation audit records
    """
    initial_records = len(df_raw)
    df = df_raw.copy()

    # 1. Deduplication
    duplicates_count = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)

    # 2. Standardize column names and types
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()

    # 3. Identify Cancellations & Returns
    is_cancel = (
        df["InvoiceNo"].str.startswith("C", na=False) |
        (df["Quantity"] < 0)
    )
    df["IsCancelled"] = is_cancel

    # Separate cancellations for audit and returns analysis
    df_cancellations = df[is_cancel].copy()

    # 4. Filter for valid sales transactions
    valid_sales_mask = (
        (~is_cancel) &
        (df["Quantity"] > 0) &
        (df["UnitPrice"] > 0.0) &
        (~df["StockCode"].isin(ADMIN_STOCK_CODES))
    )
    df_clean = df[valid_sales_mask].copy().reset_index(drop=True)

    # 5. Clean Description
    # Build lookup for missing descriptions from known StockCodes
    known_desc = (
        df_clean.dropna(subset=["Description"])
        .groupby("StockCode")["Description"]
        .first()
        .to_dict()
    )
    df_clean["Description"] = (
        df_clean["Description"]
        .fillna(df_clean["StockCode"].map(known_desc))
        .fillna("UNKNOWN MERCHANDISE")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # 6. Customer ID standardization
    # Convert float strings like '17850.0' to '17850'
    def format_customer_id(val):
        if pd.isna(val) or str(val).strip() in ("", "nan", "None", "<NA>"):
            return None
        try:
            return str(int(float(val)))
        except (ValueError, TypeError):
            return str(val).strip()

    df_clean["CustomerID"] = df_clean["CustomerID"].apply(format_customer_id)
    df_clean["IsRegisteredCustomer"] = df_clean["CustomerID"].notnull()

    # 7. Date parsing and temporal features
    df_clean["InvoiceDate"] = pd.to_datetime(df_clean["InvoiceDate"], errors="coerce")
    # Drop records where date parsing failed completely (rare safety check)
    df_clean = df_clean.dropna(subset=["InvoiceDate"]).reset_index(drop=True)

    df_clean["Date"] = df_clean["InvoiceDate"].dt.date
    df_clean["Year"] = df_clean["InvoiceDate"].dt.year
    df_clean["Month"] = df_clean["InvoiceDate"].dt.month
    df_clean["MonthName"] = df_clean["InvoiceDate"].dt.strftime("%b")
    df_clean["YearMonth"] = df_clean["InvoiceDate"].dt.strftime("%Y-%m")
    df_clean["Quarter"] = (
        df_clean["InvoiceDate"].dt.year.astype(str) + "-Q" +
        df_clean["InvoiceDate"].dt.quarter.astype(str)
    )
    df_clean["DayOfWeek"] = df_clean["InvoiceDate"].dt.day_name()
    df_clean["DayOfWeekNum"] = df_clean["InvoiceDate"].dt.dayofweek
    df_clean["Hour"] = df_clean["InvoiceDate"].dt.hour

    # 8. Financial and Volume calculations
    df_clean["Revenue"] = (df_clean["Quantity"] * df_clean["UnitPrice"]).round(2)

    # Compute Total Order Value per InvoiceNo
    invoice_totals = df_clean.groupby("InvoiceNo")["Revenue"].transform("sum").round(2)
    df_clean["OrderValue"] = invoice_totals

    # 9. Categorization
    df_clean["Category"] = df_clean["Description"].apply(map_category)

    # 10. Filter extreme bulk adjustment outliers
    # The UCI dataset has extreme outlier test rows with Quantity > 70000 that were cancelled
    outlier_mask = df_clean["Quantity"] > 50000
    extreme_outliers_dropped = int(outlier_mask.sum())
    if extreme_outliers_dropped > 0:
        df_clean = df_clean[~outlier_mask].reset_index(drop=True)

    final_records = len(df_clean)

    # Summary Metadata
    metadata = {
        "initial_raw_records": initial_records,
        "duplicate_rows_removed": duplicates_count,
        "cancellations_and_returns": int(is_cancel.sum()),
        "invalid_price_or_zero_qty_removed": int(initial_records - duplicates_count - len(df_clean) - int(is_cancel.sum())),
        "extreme_outliers_dropped": extreme_outliers_dropped,
        "final_cleaned_records": final_records,
        "retention_rate_pct": round((final_records / initial_records) * 100, 2),
        "total_revenue": round(float(df_clean["Revenue"].sum()), 2),
        "unique_invoices": int(df_clean["InvoiceNo"].nunique()),
        "unique_customers": int(df_clean["CustomerID"].nunique()),
        "unique_products": int(df_clean["StockCode"].nunique()),
        "unique_countries": int(df_clean["Country"].nunique()),
        "date_range_start": str(df_clean["InvoiceDate"].min()),
        "date_range_end": str(df_clean["InvoiceDate"].max()),
        "average_order_value": round(float(df_clean.groupby("InvoiceNo")["Revenue"].sum().mean()), 2)
    }

    return df_clean, df_cancellations, metadata


def save_processed_datasets(df_clean: pd.DataFrame, df_cancel: pd.DataFrame, metadata: dict):
    """
    Persists cleaned datasets and metadata to data/processed/.
    """
    os.makedirs(os.path.dirname(CLEANED_CSV_PATH), exist_ok=True)

    print(f"Saving cleaned CSV to {CLEANED_CSV_PATH}...")
    df_clean.to_csv(CLEANED_CSV_PATH, index=False)

    print(f"Saving cleaned Parquet to {CLEANED_PARQUET_PATH}...")
    df_clean.to_parquet(CLEANED_PARQUET_PATH, index=False)

    print(f"Saving cancellations CSV to {RETURNS_CSV_PATH}...")
    df_cancel.to_csv(RETURNS_CSV_PATH, index=False)

    print(f"Saving cleaning summary to {CLEANING_METADATA_PATH}...")
    with open(CLEANING_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=4)

    print("Data processing complete.")


if __name__ == "__main__":
    from src.data_loader import load_raw_data
    raw = load_raw_data()
    clean_df, cancel_df, meta = clean_retail_data(raw)
    save_processed_datasets(clean_df, cancel_df, meta)
    print("\n--- Cleaning Pipeline Metadata ---")
    for k, v in meta.items():
        print(f"  {k}: {v}")
