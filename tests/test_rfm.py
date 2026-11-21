"""
Unit Tests: Customer RFM Segmentation & Machine Learning Clustering
"""

import os
import pytest
import pandas as pd
import numpy as np
from src.segmentation import (
    compute_rfm_metrics,
    assign_rule_based_rfm_segments,
    run_kmeans_clustering,
    RFM_OUTPUT_CSV
)


@pytest.fixture
def sample_sales_df():
    """Generates synthetic transactions for multiple registered customers."""
    records = []
    # Customer 1: Champion (recent, frequent, high spend)
    for i in range(10):
        records.append({
            "InvoiceNo": f"INV_1_{i}",
            "StockCode": "22423",
            "Description": "REGENCY CAKESTAND",
            "Quantity": 10,
            "UnitPrice": 10.0,
            "Revenue": 100.0,
            "InvoiceDate": pd.to_datetime("2011-12-08 10:00:00"),
            "CustomerID": "10001",
            "Country": "United Kingdom"
        })
    # Customer 2: At Risk (long ago, frequent, high spend)
    for i in range(8):
        records.append({
            "InvoiceNo": f"INV_2_{i}",
            "StockCode": "85123A",
            "Description": "HEART T-LIGHT",
            "Quantity": 5,
            "UnitPrice": 10.0,
            "Revenue": 50.0,
            "InvoiceDate": pd.to_datetime("2011-03-01 10:00:00"),
            "CustomerID": "10002",
            "Country": "Germany"
        })
    # Customer 3: One-time recent buyer
    records.append({
        "InvoiceNo": "INV_3_0",
        "StockCode": "22386",
        "Description": "JUMBO BAG",
        "Quantity": 2,
        "UnitPrice": 2.0,
        "Revenue": 4.0,
        "InvoiceDate": pd.to_datetime("2011-12-05 10:00:00"),
        "CustomerID": "10003",
        "Country": "France"
    })
    # Customer 4 to 25 to allow quintile binning
    for c_id in range(10004, 10030):
        records.append({
            "InvoiceNo": f"INV_{c_id}",
            "StockCode": "22386",
            "Description": "JUMBO BAG",
            "Quantity": np.random.randint(1, 5),
            "UnitPrice": 2.0,
            "Revenue": float(np.random.randint(1, 5) * 2),
            "InvoiceDate": pd.to_datetime("2011-06-01 10:00:00") + pd.Timedelta(days=c_id % 100),
            "CustomerID": str(c_id),
            "Country": "United Kingdom"
        })
    return pd.DataFrame(records)


def test_rfm_metric_calculation(sample_sales_df):
    rfm = compute_rfm_metrics(sample_sales_df)
    assert len(rfm) == 29
    # Customer 10001 should have 10 orders, 1000 spend, low recency
    c1 = rfm[rfm["CustomerID"] == "10001"].iloc[0]
    assert c1["Frequency"] == 10
    assert c1["Monetary"] == 1000.0
    assert c1["Recency"] <= 2
    # Recency must be non-negative
    assert (rfm["Recency"] < 0).sum() == 0
    assert (rfm["Frequency"] < 1).sum() == 0


def test_rfm_score_and_segment_assignment(sample_sales_df):
    rfm = compute_rfm_metrics(sample_sales_df)
    rfm_scored = assign_rule_based_rfm_segments(rfm)

    assert "R_Score" in rfm_scored.columns
    assert "F_Score" in rfm_scored.columns
    assert "M_Score" in rfm_scored.columns
    assert "Customer_Segment" in rfm_scored.columns

    # Scores must be within 1 to 5
    assert rfm_scored["R_Score"].between(1, 5).all()
    assert rfm_scored["F_Score"].between(1, 5).all()
    assert rfm_scored["M_Score"].between(1, 5).all()

    # Customer 10001 should be classified as Champions
    c1 = rfm_scored[rfm_scored["CustomerID"] == "10001"].iloc[0]
    assert c1["Customer_Segment"] == "Champions"


def test_kmeans_clustering_execution(sample_sales_df):
    rfm = compute_rfm_metrics(sample_sales_df)
    rfm_scored = assign_rule_based_rfm_segments(rfm)
    clustered, eval_res = run_kmeans_clustering(rfm_scored, max_k=4)

    assert "KMeans_Cluster" in clustered.columns
    assert "Cluster_Name" in clustered.columns
    assert len(clustered["KMeans_Cluster"].unique()) == 4
    assert len(eval_res["silhouette_scores"]) == 3  # k=2, 3, 4


def test_processed_rfm_file_exists():
    assert os.path.exists(RFM_OUTPUT_CSV), "customer_rfm.csv does not exist in data/processed/."
    df_rfm = pd.read_csv(RFM_OUTPUT_CSV)
    assert len(df_rfm) == 4333, f"Expected 4333 registered customers, found {len(df_rfm)}"
