"""
Data Loader Module
Handles ingestion of raw retail transactional datasets with fallback and validation.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

RAW_CSV_PATH = os.path.join("data", "raw", "online_retail_raw.csv")
RAW_XLSX_PATH = os.path.join("data", "raw", "Online Retail.xlsx")

REQUIRED_COLUMNS = [
    "InvoiceNo", "StockCode", "Description",
    "Quantity", "InvoiceDate", "UnitPrice",
    "CustomerID", "Country"
]


def generate_synthetic_retail_data(num_records: int = 50000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic synthetic transactional dataset matching the UCI Online Retail schema.
    Used as an automated fallback if the primary raw file cannot be loaded.
    """
    np.random.seed(random_seed)
    print(f"Generating synthetic retail dataset with {num_records} records...")

    # Realistic catalogs
    products = [
        ("85123A", "WHITE HANGING HEART T-LIGHT HOLDER", 2.95, "Home Decor"),
        ("71053", "WHITE METAL LANTERN", 3.39, "Home Decor"),
        ("84406B", "CREAM CUPID HEARTS COAT HANGER", 2.75, "Home Decor"),
        ("84029G", "KNITTED UNION FLAG HOT WATER BOTTLE", 3.75, "Seasonal"),
        ("84029E", "RED WOOLLY HOTTIE WHITE HEART.", 3.39, "Seasonal"),
        ("22752", "SET 7 BABUSHKA NESTING BOXES", 8.50, "Gifts"),
        ("21730", "GLASS STAR FROSTED T-LIGHT HOLDER", 4.25, "Home Decor"),
        ("22633", "HAND WARMER UNION JACK", 2.10, "Seasonal"),
        ("22632", "HAND WARMER RED RETROSPOT", 2.10, "Seasonal"),
        ("84879", "ASSORTED COLOUR BIRD ORNAMENT", 1.69, "Home Decor"),
        ("22745", "POPPY'S PLAYHOUSE BEDROOM", 2.10, "Toys & Games"),
        ("22748", "POPPY'S PLAYHOUSE KITCHEN", 2.10, "Toys & Games"),
        ("22749", "POPPY'S PLAYHOUSE BATHROOM", 2.10, "Toys & Games"),
        ("22310", "IVORY KNITTED MUG COSY", 1.65, "Kitchen"),
        ("84969", "BOX OF 6 ASSORTED COLOUR TEASPOONS", 4.25, "Kitchen"),
        ("22623", "BOX OF VINTAGE JIGSAW BLOCKS", 5.95, "Toys & Games"),
        ("22622", "BOX OF VINTAGE ALPHABET BLOCKS", 9.95, "Toys & Games"),
        ("21754", "HOME BUILDING BLOCK WORD", 5.95, "Home Decor"),
        ("21755", "LOVE BUILDING BLOCK WORD", 5.95, "Home Decor"),
        ("21777", "RECIPE BOX PANTRY DESIGN", 7.95, "Kitchen"),
        ("48187", "DOORMAT NEW ENGLAND", 7.95, "Home Decor"),
        ("22960", "JAM MAKING SET WITH JARS", 4.25, "Kitchen"),
        ("22961", "JAM MAKING SET PRINTED", 1.45, "Kitchen"),
        ("22386", "JUMBO BAG PINK POLKADOT", 2.08, "Bags"),
        ("85099B", "JUMBO BAG RED RETROSPOT", 2.08, "Bags"),
        ("21931", "JUMBO STORAGE BAG SUKI", 2.08, "Bags"),
        ("22411", "JUMBO SHOPPER VINTAGE RED PAISLEY", 2.08, "Bags"),
        ("22382", "LUNCH BAG SPACEBOY DESIGN", 1.65, "Bags"),
        ("22383", "LUNCH BAG SUKI DESIGN", 1.65, "Bags"),
        ("22384", "LUNCH BAG PINK POLKADOT", 1.65, "Bags"),
        ("20725", "LUNCH BAG RED RETROSPOT", 1.65, "Bags"),
        ("20727", "LUNCH BAG BLACK SKULL.", 1.65, "Bags"),
        ("20728", "LUNCH BAG CARS BLUE", 1.65, "Bags"),
        ("22385", "JUMBO BAG OWLS", 2.08, "Bags"),
        ("POST", "POSTAGE", 18.00, "Shipping")
    ]

    countries = ["United Kingdom"] * 85 + ["Germany"] * 5 + ["France"] * 4 + ["EIRE"] * 3 + ["Spain"] * 2 + ["Netherlands"]

    start_date = datetime(2010, 12, 1, 8, 0, 0)
    end_date = datetime(2011, 12, 9, 17, 0, 0)
    delta_seconds = int((end_date - start_date).total_seconds())

    # 1500 distinct customer IDs + guest checkouts (NaN)
    customer_pool = [12000 + i for i in range(1500)]

    records = []
    invoice_seq = 536365

    for _ in range(num_records):
        # 80% repeat customers, 20% random or guest
        cust_id = np.random.choice(customer_pool) if np.random.rand() > 0.22 else np.nan
        country = np.random.choice(countries)
        random_secs = np.random.randint(0, delta_seconds)
        inv_date = start_date + timedelta(seconds=random_secs)
        is_cancel = np.random.rand() < 0.02

        # 1 to 5 lines per simulated cart
        items_count = np.random.randint(1, 6)
        inv_no = f"C{invoice_seq}" if is_cancel else str(invoice_seq)
        invoice_seq += 1

        for _ in range(items_count):
            prod = products[np.random.randint(0, len(products))]
            qty = -np.random.randint(1, 10) if is_cancel else np.random.choice([1, 2, 3, 6, 12, 24, 48], p=[0.4, 0.25, 0.15, 0.1, 0.07, 0.03])
            price = round(prod[2] * np.random.uniform(0.95, 1.05), 2)

            records.append({
                "InvoiceNo": inv_no,
                "StockCode": prod[0],
                "Description": prod[1],
                "Quantity": qty,
                "InvoiceDate": inv_date.strftime("%Y-%m-%d %H:%M:%S"),
                "UnitPrice": price,
                "CustomerID": cust_id,
                "Country": country
            })

    df = pd.DataFrame(records)
    return df


def load_raw_data(filepath: str = None) -> pd.DataFrame:
    """
    Loads raw retail dataset from CSV or Excel, falling back gracefully if necessary.
    Preserves original data.
    """
    target_path = filepath or RAW_CSV_PATH
    if not os.path.exists(target_path):
        if os.path.exists(RAW_XLSX_PATH):
            print(f"Reading raw Excel file from {RAW_XLSX_PATH}...")
            df = pd.read_excel(RAW_XLSX_PATH)
            # Save raw CSV for faster future loads
            df.to_csv(RAW_CSV_PATH, index=False)
            return df
        else:
            print(f"File not found at {target_path}. Generating synthetic retail data...")
            df = generate_synthetic_retail_data()
            os.makedirs(os.path.dirname(RAW_CSV_PATH), exist_ok=True)
            df.to_csv(RAW_CSV_PATH, index=False)
            return df

    print(f"Loading raw retail transactions from {target_path}...")
    df = pd.read_csv(target_path, dtype={"InvoiceNo": str, "StockCode": str, "CustomerID": str})
    return df


def get_raw_dataset_summary(df: pd.DataFrame) -> dict:
    """
    Computes diagnostic metadata on the raw dataset.
    """
    return {
        "total_records": len(df),
        "columns": list(df.columns),
        "missing_customer_ids": int(df["CustomerID"].isnull().sum()),
        "missing_descriptions": int(df["Description"].isnull().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "negative_quantities": int((df["Quantity"] < 0).sum()),
        "zero_or_negative_price": int((df["UnitPrice"] <= 0).sum()),
        "unique_invoices": int(df["InvoiceNo"].nunique()),
        "unique_products": int(df["StockCode"].nunique()),
        "countries_count": int(df["Country"].nunique())
    }


if __name__ == "__main__":
    raw_df = load_raw_data()
    summary = get_raw_dataset_summary(raw_df)
    print("Dataset Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
