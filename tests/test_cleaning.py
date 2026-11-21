"""
Unit Tests: Data Cleaning & Feature Engineering Pipeline
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.data_cleaner import clean_retail_data, map_category, ADMIN_STOCK_CODES


@pytest.fixture
def sample_raw_data():
    """Provides a synthetic raw DataFrame with realistic edge cases."""
    data = [
        # Normal sales transaction
        {"InvoiceNo": "536365", "StockCode": "85123A", "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
         "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 2.55, "CustomerID": 17850.0, "Country": "United Kingdom"},
        # Exact duplicate
        {"InvoiceNo": "536365", "StockCode": "85123A", "Description": "WHITE HANGING HEART T-LIGHT HOLDER",
         "Quantity": 6, "InvoiceDate": "2010-12-01 08:26:00", "UnitPrice": 2.55, "CustomerID": 17850.0, "Country": "United Kingdom"},
        # Cancellation invoice (starts with C)
        {"InvoiceNo": "C536379", "StockCode": "D", "Description": "Discount",
         "Quantity": -1, "InvoiceDate": "2010-12-01 09:41:00", "UnitPrice": 27.50, "CustomerID": 14527.0, "Country": "United Kingdom"},
        # Negative quantity without C
        {"InvoiceNo": "536380", "StockCode": "22960", "Description": "JAM MAKING SET WITH JARS",
         "Quantity": -5, "InvoiceDate": "2010-12-01 09:50:00", "UnitPrice": 4.25, "CustomerID": 15311.0, "Country": "United Kingdom"},
        # Zero UnitPrice (inventory adjustment)
        {"InvoiceNo": "536381", "StockCode": "84029G", "Description": "damaged stock",
         "Quantity": 10, "InvoiceDate": "2010-12-01 10:00:00", "UnitPrice": 0.0, "CustomerID": np.nan, "Country": "United Kingdom"},
        # Admin StockCode (POSTAGE)
        {"InvoiceNo": "536382", "StockCode": "POST", "Description": "POSTAGE",
         "Quantity": 1, "InvoiceDate": "2010-12-01 10:15:00", "UnitPrice": 18.00, "CustomerID": 12431.0, "Country": "Germany"},
        # Guest Checkout (null CustomerID) with valid merchandise
        {"InvoiceNo": "536383", "StockCode": "22386", "Description": "JUMBO BAG PINK POLKADOT",
         "Quantity": 4, "InvoiceDate": "2010-12-01 10:30:00", "UnitPrice": 1.95, "CustomerID": np.nan, "Country": "United Kingdom"},
        # Missing description for known StockCode
        {"InvoiceNo": "536384", "StockCode": "85123A", "Description": None,
         "Quantity": 2, "InvoiceDate": "2010-12-01 11:00:00", "UnitPrice": 2.55, "CustomerID": 17850.0, "Country": "United Kingdom"},
        # Extreme balance adjustment outlier
        {"InvoiceNo": "536385", "StockCode": "23084", "Description": "RABBIT NIGHT LIGHT",
         "Quantity": 80000, "InvoiceDate": "2010-12-01 12:00:00", "UnitPrice": 1.50, "CustomerID": 16446.0, "Country": "United Kingdom"}
    ]
    return pd.DataFrame(data)


def test_deduplication(sample_raw_data):
    clean_df, _, meta = clean_retail_data(sample_raw_data)
    assert meta["duplicate_rows_removed"] == 1


def test_cancellations_and_negative_quantities_filtered(sample_raw_data):
    clean_df, cancel_df, _ = clean_retail_data(sample_raw_data)
    # C536379 and 536380 (Quantity -5) must be classified as cancellations
    assert len(cancel_df) >= 2
    assert (clean_df["Quantity"] <= 0).sum() == 0
    assert (clean_df["InvoiceNo"].str.startswith("C")).sum() == 0


def test_zero_price_and_admin_codes_removed(sample_raw_data):
    clean_df, _, _ = clean_retail_data(sample_raw_data)
    assert (clean_df["UnitPrice"] <= 0).sum() == 0
    assert clean_df["StockCode"].isin(ADMIN_STOCK_CODES).sum() == 0


def test_missing_description_imputation(sample_raw_data):
    clean_df, _, _ = clean_retail_data(sample_raw_data)
    # The row with StockCode 85123A and null description should be imputed from known description
    imputed_row = clean_df[(clean_df["InvoiceNo"] == "536384") & (clean_df["StockCode"] == "85123A")]
    assert len(imputed_row) == 1
    assert imputed_row.iloc[0]["Description"] == "WHITE HANGING HEART T-LIGHT HOLDER"


def test_customer_id_formatting(sample_raw_data):
    clean_df, _, _ = clean_retail_data(sample_raw_data)
    # CustomerID 17850.0 should format as string "17850" without decimal
    cust_17850 = clean_df[clean_df["CustomerID"] == "17850"]
    assert len(cust_17850) > 0
    # Guest checkout should have None/null CustomerID
    guest_rows = clean_df[clean_df["InvoiceNo"] == "536383"]
    assert len(guest_rows) == 1
    assert pd.isna(guest_rows.iloc[0]["CustomerID"])


def test_temporal_and_financial_features(sample_raw_data):
    clean_df, _, _ = clean_retail_data(sample_raw_data)
    row = clean_df[clean_df["InvoiceNo"] == "536365"].iloc[0]
    assert row["Revenue"] == round(6 * 2.55, 2)
    assert row["YearMonth"] == "2010-12"
    assert row["Quarter"] == "2010-Q4"
    assert row["Category"] == "Home Decor"


def test_category_mapping():
    assert map_category("LUNCH BAG CARS BLUE") == "Bags & Luggage"
    assert map_category("SET 3 RETRO KITCHEN CANISTERS") == "Kitchen & Dining"
    assert map_category("WHITE HANGING HEART") == "Home Decor"
    assert map_category("PAPER CRAFT LITTLE BIRDIE") == "Stationery & Craft"
    assert map_category("UNKNOWN XYZ ITEM") == "General Merchandise"
