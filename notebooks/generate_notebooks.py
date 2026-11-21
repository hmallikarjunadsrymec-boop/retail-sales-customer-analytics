"""
Generator script to build production-grade Jupyter Notebooks for EDA and Customer Segmentation.
"""

import json
import os

NOTEBOOKS_DIR = "notebooks"


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "language_info": {"name": "python", "version": "3.14.6"},
            "kernelspec": {"name": "python3", "display_name": "Python 3"}
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }


def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [s + "\n" for s in source.splitlines()]
    }


def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [s + "\n" for s in source.splitlines()]
    }


def create_all_notebooks():
    os.makedirs(NOTEBOOKS_DIR, exist_ok=True)

    # Notebook 1: EDA & Cleaning
    nb1_cells = [
        md_cell("""# Retail Sales & Customer Analytics Platform
## Notebook 01: Data Ingestion, Cleaning & Exploratory Data Analysis
**Role:** Senior Data Scientist, Data Analyst & BI Engineer

This notebook walks through the data engineering pipeline:
1. Loading raw transactional data from the UCI Online Retail dataset.
2. Data cleaning (deduplication, cancellations, invalid price/quantities, missing values).
3. Feature engineering (Revenue, Date features, Category classifications).
4. Exploratory Data Analysis with Matplotlib and Seaborn."""),

        code_cell("""import os
import sys
# Ensure src is discoverable from notebooks directory
sys.path.insert(0, os.path.abspath('..'))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.data_loader import load_raw_data, get_raw_dataset_summary
from src.data_cleaner import clean_retail_data, save_processed_datasets
from src.eda import run_comprehensive_eda

%matplotlib inline
sns.set_theme(style='whitegrid')"""),

        md_cell("### 1. Ingest Raw Dataset & Profile Health"),
        code_cell("""df_raw = load_raw_data('../data/raw/online_retail_raw.csv')
print('Raw shape:', df_raw.shape)
summary = get_raw_dataset_summary(df_raw)
for k, v in summary.items():
    print(f'  {k}: {v}')"""),

        md_cell("### 2. Run Data Cleaning & Feature Engineering"),
        code_cell("""df_clean, df_cancel, meta = clean_retail_data(df_raw)
print('--- Cleaning Summary ---')
for k, v in meta.items():
    print(f'  {k}: {v}')"""),

        md_cell("### 3. Exploratory Data Analysis"),
        code_cell("""eda_res = run_comprehensive_eda(df_clean)
print('Executive KPIs:', eda_res['kpis'])
print('Customer Repeat Purchase Behavior:', eda_res['repeat_behavior'])"""),

        md_cell("### 4. Monthly Revenue Trend Visual"),
        code_cell("""monthly = pd.DataFrame(eda_res['monthly_summary'])
fig, ax1 = plt.subplots(figsize=(11, 5))
ax2 = ax1.twinx()

ax1.bar(monthly['YearMonth'], monthly['Revenue'] / 1000, color='#1f77b4', alpha=0.8, label='Revenue (£k)')
ax2.plot(monthly['YearMonth'], monthly['Orders'], color='#d62728', marker='o', linewidth=2, label='Orders')

ax1.set_ylabel('Revenue (£ Thousands)')
ax2.set_ylabel('Orders')
ax1.set_title('Monthly Revenue & Order Count Trend')
ax1.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.show()"""),

        md_cell("### 5. Category Breakdown"),
        code_cell("""cat_df = pd.DataFrame(eda_res['category_performance'])
plt.figure(figsize=(10, 4))
sns.barplot(data=cat_df, x='Revenue', y='Category', palette='mako')
plt.title('Gross Realized Revenue by Product Category (£ GBP)')
plt.tight_layout()
plt.show()""")
    ]

    nb1_path = os.path.join(NOTEBOOKS_DIR, "01_retail_eda_and_cleaning.ipynb")
    with open(nb1_path, "w", encoding="utf-8") as f:
        json.dump(make_notebook(nb1_cells), f, indent=2)
    print(f"Generated {nb1_path}")

    # Notebook 2: RFM Customer Segmentation
    nb2_cells = [
        md_cell("""# Retail Sales & Customer Analytics Platform
## Notebook 02: Customer RFM Segmentation & Machine Learning Clustering
**Role:** Senior Data Scientist & ML Engineer

This notebook walks through behavioral customer intelligence:
1. Calculation of Recency (R), Frequency (F), and Monetary Value (M).
2. Rule-based RFM scoring and segment categorization (Champions, Loyal Customers, At Risk, Can't Lose Them, etc.).
3. Unsupervised K-Means clustering with feature log-transforms, standardization, and Elbow/Silhouette evaluation.
4. Business interpretation and marketing strategy."""),

        code_cell("""import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.segmentation import run_full_segmentation_pipeline

%matplotlib inline
sns.set_theme(style='whitegrid')"""),

        md_cell("### 1. Execute Customer RFM Pipeline"),
        code_cell("""rfm_df = run_full_segmentation_pipeline()
print(f'Successfully segmented {len(rfm_df)} registered customer accounts.')
rfm_df.head()"""),

        md_cell("### 2. Segment Distribution & Revenue Contribution"),
        code_cell("""seg_summary = rfm_df.groupby('Customer_Segment').agg(
    Customer_Count=('CustomerID', 'count'),
    Total_Revenue=('Monetary', 'sum'),
    Avg_Recency=('Recency', 'mean'),
    Avg_Frequency=('Frequency', 'mean'),
    Avg_Spend=('Monetary', 'mean')
).reset_index().sort_values('Total_Revenue', ascending=False)

seg_summary['Revenue_Share_%'] = (seg_summary['Total_Revenue'] / rfm_df['Monetary'].sum() * 100).round(2)
display(seg_summary)"""),

        md_cell("### 3. Visualizing Customer Segments: Volume vs Value"),
        code_cell("""fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

sns.barplot(data=seg_summary, y='Customer_Segment', x='Customer_Count', palette='viridis', ax=ax1)
ax1.set_title('Customer Count by RFM Segment')
ax1.set_xlabel('Accounts')
ax1.set_ylabel('')

sns.barplot(data=seg_summary, y='Customer_Segment', x='Total_Revenue', palette='plasma', ax=ax2)
ax2.set_title('Total Revenue Contribution (£ GBP)')
ax2.set_xlabel('Revenue (£)')
ax2.set_ylabel('')

plt.tight_layout()
plt.show()"""),

        md_cell("### 4. K-Means Clustering Profiles"),
        code_cell("""cluster_summary = rfm_df.groupby(['KMeans_Cluster', 'Cluster_Name']).agg(
    Accounts=('CustomerID', 'count'),
    Mean_Recency=('Recency', 'mean'),
    Mean_Frequency=('Frequency', 'mean'),
    Mean_Spend=('Monetary', 'mean'),
    Total_Spend=('Monetary', 'sum')
).reset_index().sort_values('Total_Spend', ascending=False)

display(cluster_summary)""")
    ]

    nb2_path = os.path.join(NOTEBOOKS_DIR, "02_customer_segmentation_rfm.ipynb")
    with open(nb2_path, "w", encoding="utf-8") as f:
        json.dump(make_notebook(nb2_cells), f, indent=2)
    print(f"Generated {nb2_path}")


if __name__ == "__main__":
    create_all_notebooks()
