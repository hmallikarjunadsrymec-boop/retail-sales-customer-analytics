"""
Power BI Data Preparation & Star Schema Export Module
Transforms cleaned retail sales and RFM datasets into optimized Star Schema tables for Power BI.
"""

import os
import pandas as pd
import numpy as np

POWERBI_DIR = os.path.join("data", "processed", "powerbi")
RETAIL_PARQUET = os.path.join("data", "processed", "retail_cleaned.parquet")
RETAIL_CSV = os.path.join("data", "processed", "retail_cleaned.csv")
RFM_CSV = os.path.join("data", "processed", "customer_rfm.csv")


def export_powerbi_star_schema() -> dict[str, str]:
    """
    Exports normalized Fact and Dimension tables in CSV format for direct Power BI ingestion.
    """
    os.makedirs(POWERBI_DIR, exist_ok=True)
    print("Preparing Star Schema tables for Power BI...")

    # Load cleaned sales data
    if os.path.exists(RETAIL_PARQUET):
        df_sales = pd.read_parquet(RETAIL_PARQUET)
    else:
        df_sales = pd.read_csv(RETAIL_CSV)

    df_rfm = pd.read_csv(RFM_CSV)

    # 1. FactSales Table
    df_sales["DateKey"] = pd.to_datetime(df_sales["Date"]).dt.strftime("%Y%m%d").astype(int)
    fact_sales = df_sales[[
        "InvoiceNo", "StockCode", "CustomerID", "DateKey",
        "Quantity", "UnitPrice", "Revenue", "Country"
    ]].copy()
    fact_sales["CustomerID"] = fact_sales["CustomerID"].fillna("GUEST")

    fact_sales_path = os.path.join(POWERBI_DIR, "FactSales.csv")
    fact_sales.to_csv(fact_sales_path, index=False)
    print(f"  Exported FactSales ({len(fact_sales):,} rows) to {fact_sales_path}")

    # 2. DimCustomer Table
    dim_customer = df_rfm[[
        "CustomerID", "Country", "Customer_Segment", "Cluster_Name",
        "R_Score", "F_Score", "M_Score", "RFM_Score",
        "Recency", "Frequency", "Monetary", "AvgOrderValue",
        "FirstPurchaseDate", "LastPurchaseDate"
    ]].copy()
    # Add Guest placeholder for star-schema referential integrity
    guest_row = pd.DataFrame([{
        "CustomerID": "GUEST",
        "Country": "Unknown",
        "Customer_Segment": "Guest / Unregistered",
        "Cluster_Name": "Guest Checkout",
        "R_Score": 0, "F_Score": 0, "M_Score": 0, "RFM_Score": "000",
        "Recency": 0, "Frequency": 0, "Monetary": 0.0, "AvgOrderValue": 0.0,
        "FirstPurchaseDate": "2010-12-01", "LastPurchaseDate": "2011-12-09"
    }])
    dim_customer = pd.concat([dim_customer, guest_row], ignore_index=True)

    dim_customer_path = os.path.join(POWERBI_DIR, "DimCustomer.csv")
    dim_customer.to_csv(dim_customer_path, index=False)
    print(f"  Exported DimCustomer ({len(dim_customer):,} rows) to {dim_customer_path}")

    # 3. DimProduct Table
    dim_product = (
        df_sales.groupby("StockCode")
        .agg(
            Description=("Description", "first"),
            Category=("Category", "first"),
            AvgUnitPrice=("UnitPrice", "mean")
        )
        .reset_index()
    )
    dim_product["AvgUnitPrice"] = dim_product["AvgUnitPrice"].round(2)

    dim_product_path = os.path.join(POWERBI_DIR, "DimProduct.csv")
    dim_product.to_csv(dim_product_path, index=False)
    print(f"  Exported DimProduct ({len(dim_product):,} rows) to {dim_product_path}")

    # 4. DimDate Table
    dates = pd.date_range(start="2010-12-01", end="2011-12-31", freq="D")
    dim_date = pd.DataFrame({
        "DateKey": dates.strftime("%Y%m%d").astype(int),
        "FullDate": dates.strftime("%Y-%m-%d"),
        "Year": dates.year,
        "Quarter": "Q" + dates.quarter.astype(str),
        "YearQuarter": dates.year.astype(str) + "-Q" + dates.quarter.astype(str),
        "Month": dates.month,
        "MonthName": dates.strftime("%B"),
        "MonthShort": dates.strftime("%b"),
        "YearMonth": dates.strftime("%Y-%m"),
        "DayOfWeek": dates.strftime("%A"),
        "DayOfWeekNum": dates.dayofweek,
        "IsWeekend": dates.dayofweek.isin([5, 6]).astype(int)
    })

    dim_date_path = os.path.join(POWERBI_DIR, "DimDate.csv")
    dim_date.to_csv(dim_date_path, index=False)
    print(f"  Exported DimDate ({len(dim_date):,} rows) to {dim_date_path}")

    # 5. DimGeography Table
    all_countries = df_sales["Country"].unique()
    geo_records = []
    for c in all_countries:
        if c == "United Kingdom":
            region = "Domestic (UK)"
        elif c in ["Germany", "France", "EIRE", "Spain", "Netherlands", "Belgium", "Switzerland", "Portugal", "Norway", "Italy", "Channel Islands", "Finland", "Cyprus", "Austria", "Sweden", "Denmark", "Poland", "Greece", "Malta", "Lithuania", "Iceland", "Czech Republic", "European Community"]:
            region = "Continental Europe"
        else:
            region = "Rest of World"
        geo_records.append({"Country": c, "Region": region})

    dim_geo = pd.DataFrame(geo_records)
    dim_geo_path = os.path.join(POWERBI_DIR, "DimGeography.csv")
    dim_geo.to_csv(dim_geo_path, index=False)
    print(f"  Exported DimGeography ({len(dim_geo):,} rows) to {dim_geo_path}")

    return {
        "FactSales": fact_sales_path,
        "DimCustomer": dim_customer_path,
        "DimProduct": dim_product_path,
        "DimDate": dim_date_path,
        "DimGeography": dim_geo_path
    }


if __name__ == "__main__":
    exports = export_powerbi_star_schema()
    print("\nPower BI Star Schema export successfully generated:")
    for k, v in exports.items():
        print(f"  {k} -> {v}")
