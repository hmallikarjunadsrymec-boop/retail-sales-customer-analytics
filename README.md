# Retail Sales & Customer Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-003B57.svg)](https://www.sqlite.org/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Star%20Schema%20Ready-F2C811.svg)](https://powerbi.microsoft.com/)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed%20(100%25)-brightgreen.svg)]()

An enterprise-grade, end-to-end retail intelligence solution that ingests, cleans, analyzes, and models retail transactions to optimize customer lifetime value (LTV), inventory velocity, basket size, and revenue growth.

---

## 🌐 Live Interactive Web Applications

The platform features two production web applications running concurrently against the analytical engine:

| Application Interface | Local Access URL | Default Port | Technology Stack | Key Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **🏢 Corporate Website Portal** | [http://localhost:8000/](http://localhost:8000/) | `8000` | FastAPI, HTML5, CSS3 | Executive landing portal, end-to-end architecture breakdown, data lineage. |
| **📊 Executive Web Analytics Dashboard** | [http://localhost:8000/dashboard](http://localhost:8000/dashboard) | `8000` | FastAPI, SQLite 3, Chart.js | Real-time KPI cards, dynamic Chart.js charts, country/category filters, paginated customer explorer. |
| **🛍️ Streamlit Analytics Suite** | [http://localhost:8501/](http://localhost:8501/) | `8501` | Streamlit, Altair, Pandas | 6-Page decision platform, date range picker, product search, behavioral RFM drill-downs, CSV exports. |

### How to Launch the Web Interfaces
```bash
# Terminal 1: Launch Corporate Portal & Web Dashboard (Port 8000)
python -m uvicorn web.api:app --host 0.0.0.0 --port 8000

# Terminal 2: Launch Streamlit Analytics Suite (Port 8501)
streamlit run app.py
```

---

## 📋 Table of Contents

1. [Live Interactive Web Applications](#-live-interactive-web-applications)
2. [Executive Overview](#executive-overview)
3. [End-to-End System Architecture](#end-to-end-system-architecture)
4. [Technology Stack](#technology-stack)
5. [Project Directory Structure](#project-directory-structure)
6. [Data Lineage & Cleaning Pipeline](#data-lineage--cleaning-pipeline)
7. [SQL Analytical Queries & Database](#sql-analytical-queries--database)
8. [Customer RFM Segmentation & Machine Learning](#customer-rfm-segmentation--machine-learning)
9. [Web Dashboards & Streamlit Suite](#web-dashboards--streamlit-suite)
10. [Power BI Dimensional Modeling & DAX](#power-bi-dimensional-modeling--dax)
11. [Evidence-Based Business Recommendations](#evidence-based-business-recommendations)
12. [Installation & Execution Guide](#installation--execution-guide)
13. [Automated Test Suite & Verification](#automated-test-suite--verification)

---

## 1. Executive Overview

Retail organizations operate in high-velocity, multi-channel environments where profitability hinges on understanding purchasing frequency, churn indicators, customer lifetime value, and seasonal inventory demand.

The **Retail Sales & Customer Analytics Platform** bridges the gap between raw transactional logs and executive decision-making. Built with modular Python pipelines, an embedded SQLite analytical engine, scikit-learn machine learning clustering, an interactive Streamlit application, and Kimball-standard Power BI Star Schema exports, this platform delivers complete operational visibility across commercial sales.

### Key Empirical Benchmarks (Cleaned Dataset)
- **Total Net Revenue:** **£10,009,302.93**
- **Total Invoiced Orders:** **19,774**
- **Average Order Value (AOV):** **£506.19** (Median: **£232.00**)
- **Registered Customer Base:** **4,333 unique accounts**
- **Customer Retention Rate:** **65.27%** (2,828 repeat purchasers vs. 1,505 one-time buyers)
- **Hero Revenue Product:** *REGENCY CAKESTAND 3 TIER* (**£174,156.54** across 1,972 orders)
- **Top Customer RFM Segment:** *Champions* (**1,119 accounts** generating **£5.78M**, or **65.0%** of customer spend)

---

## 2. End-to-End System Architecture

```
                                  [ RAW DATA LAYER ]
                     UCI Online Retail Transactional Archive
                     (541,909 Transactions | 8 Base Columns)
                                         │
                                         ▼
                             [ DATA CLEANING PIPELINE ]
                        src/data_cleaner.py (Pandas & NumPy)
             • Deduplication (5,268 duplicates removed)
             • Return/Cancellation isolation (10,587 flagged)
             • Zero/Negative price filtering (3,347 dropped)
             • Non-commercial admin code removal (POST, D, M, CRUK)
             • Automated description imputation from StockCode lookup
             • Calendar feature extraction (Year, Month, Quarter, DOW, Hour)
             • 8-Class product category mapping
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
         [ PROCESSED DATA STORE ]                  [ SQL ANALYTICAL ENGINE ]
         data/processed/retail_cleaned.parquet     sql/schema.sql & src/sql_engine.py
         data/processed/retail_cleaned.csv         data/processed/retail_analytics.db
         (522,707 Clean Commercial Records)        • Indexed SQLite 3 Database
                                                   • 10 Production Analytical Queries
                                                   • Python-to-SQL Metric Reconciliation
                    │                                         │
                    ├────────────────────┬────────────────────┤
                    ▼                    ▼                    ▼
          [ RFM SEGMENTATION ]   [ POWER BI STAR SCHEMA ]  [ STREAMLIT WEB APP ]
          src/segmentation.py    src/powerbi_export.py     app.py & dashboard/
          • Quintile Scoring     • FactSales.csv           • 1. Executive Overview
          • 9 Behavioral Segments• DimCustomer.csv         • 2. Sales Analytics
          • K-Means (k=4) Model  • DimProduct.csv          • 3. Product Performance
          • Elbow & Silhouette   • DimDate.csv             • 4. Customer Analytics
            Evaluation           • DimGeography.csv        • 5. RFM Segmentation
                                 • DAX Measure Library     • 6. Business Insights
```

---

## 3. Technology Stack

- **Core Data Science & Processing:** Python 3, Pandas 2.x/3.x, NumPy, SciPy
- **Statistical Modeling & Unsupervised ML:** Scikit-learn (KMeans, StandardScaler, silhouette_score)
- **Data Persistence & SQL:** SQLite 3, SQLAlchemy, Parquet (PyArrow)
- **Visual Analytics & Charting:** Matplotlib, Seaborn, Altair
- **Interactive Web Application:** Streamlit
- **Business Intelligence & Reporting:** Microsoft Power BI (Kimball Star Schema CSVs & DAX Guide)
- **Quality Assurance & Testing:** Pytest, Unittest

---

## 4. Project Directory Structure

```text
coustomer/
├── .gitignore                          # Production Git ignore patterns
├── README.md                           # Master architectural and project documentation
├── requirements.txt                    # Project dependencies
├── app.py                              # Streamlit multi-page web application entrypoint
│
├── data/
│   ├── raw/                            # Immutable raw data storage
│   │   ├── Online Retail.xlsx          # Original UCI archive
│   │   └── online_retail_raw.csv       # Raw CSV extract (541,909 rows)
│   └── processed/                      # Cleaned production datasets
│       ├── retail_cleaned.parquet      # High-performance Parquet format (522,707 rows)
│       ├── retail_cleaned.csv          # Standard cleaned CSV format
│       ├── retail_cancellations.csv    # Audit log of returns & cancellations
│       ├── customer_rfm.parquet        # Customer RFM metrics & K-Means clusters (4,333 rows)
│       ├── customer_rfm.csv            # Customer RFM profiles
│       ├── cleaning_summary.json       # Data lineage & cleaning audit metadata
│       ├── retail_analytics.db         # Indexed SQLite 3 relational database
│       └── powerbi/                    # Power BI Star Schema tables
│           ├── FactSales.csv           # Granular sales fact table
│           ├── DimCustomer.csv         # Customer dimension with RFM scores
│           ├── DimProduct.csv          # Product catalog dimension with categories
│           ├── DimDate.csv             # Continuous date dimension table
│           └── DimGeography.csv        # Country & regional trading dimension
│
├── src/                                # Core modular Python source code
│   ├── __init__.py                     # Package initialization
│   ├── data_loader.py                  # Ingestion, validation, and synthetic fallback
│   ├── data_cleaner.py                 # Cleaning pipeline, deduplication, feature engineering
│   ├── eda.py                          # Statistical EDA & Matplotlib/Seaborn visualization suite
│   ├── sql_engine.py                   # SQLite database loader & Python-to-SQL reconciler
│   ├── segmentation.py                 # RFM scoring, K-Means clustering, and silhouette evaluation
│   └── powerbi_export.py               # Star Schema generator for Power BI
│
├── sql/                                # Production SQL scripts
│   ├── schema.sql                      # DDL table creation and performance indexes
│   └── sales_analysis.sql              # 10 Reusable analytical queries & window functions
│
├── dashboard/                          # Streamlit application modular components
│   ├── styles.py                       # Modern corporate CSS typography and KPI card components
│   ├── data_access.py                  # Streamlit @st.cache_data loading and filtering layer
│   └── pages/                          # Multi-page views
│       ├── p1_overview.py              # Page 1: Executive KPI overview & monthly trends
│       ├── p2_sales.py                 # Page 2: Temporal analysis, day/hour patterns, AOV
│       ├── p3_products.py              # Page 3: Top SKUs, category share, catalog search
│       ├── p4_customers.py             # Page 4: Retention, repeat purchasing, customer lookup
│       ├── p5_rfm.py                   # Page 5: Behavioral RFM segmentation & ML clusters
│       └── p6_insights.py              # Page 6: Evidence-based strategic action plan
│
├── notebooks/                          # Production Jupyter Notebooks
│   ├── 01_retail_eda_and_cleaning.ipynb # Interactive data exploration & cleaning walkthrough
│   └── 02_customer_segmentation_rfm.ipynb # RFM modeling & K-Means clustering walkthrough
│
├── reports/                            # Analytical documentation and reports
│   ├── BUSINESS_RECOMMENDATIONS.md     # In-depth executive recommendations and action plan
│   ├── POWER_BI_DASHBOARD_GUIDE.md     # Star schema model, relationships, and full DAX measures
│   ├── eda_summary.json                # Structured EDA metrics summary
│   ├── rfm_summary.json                # Structured RFM and clustering metrics summary
│   └── eda_figures/                    # 12 Publication-quality figures (Matplotlib/Seaborn)
│       ├── 01_monthly_revenue_trend.png
│       ├── 02_top_10_products_revenue.png
│       ├── 03_top_10_products_volume.png
│       ├── 04_category_revenue_distribution.png
│       ├── 05_country_revenue_pareto.png
│       ├── 06_sales_by_day_and_hour.png
│       ├── 07_order_value_distribution.png
│       ├── 08_repeat_purchase_behavior.png
│       ├── 09_rfm_elbow_silhouette.png
│       ├── 10_rfm_customer_segments_distribution.png
│       ├── 11_rfm_clusters_scatter.png
│       └── 12_rfm_segment_heatmap.png
│
└── tests/                              # Automated test suite
    ├── test_cleaning.py                # Tests deduplication, cancellations, imputation, types
    ├── test_sql.py                     # Reconciles SQL queries with Python calculations
    └── test_rfm.py                     # Tests RFM math, quintiles, and K-Means clustering
```

---

## 5. Data Lineage & Cleaning Pipeline

The raw dataset contains **541,909 records** spanning December 1, 2010 to December 9, 2011. The cleaning pipeline (`src/data_cleaner.py`) applies rigorous data engineering logic:

1. **Deduplication:** Dropped **5,268 exact duplicate rows**.
2. **Returns & Cancellations Isolation:** Identified **10,587 transactions** (invoices starting with 'C' or negative quantities). Preserved separately in `data/processed/retail_cancellations.csv` for audit integrity.
3. **Invalid Price & Zero-Quantity Elimination:** Removed **3,347 administrative records** where `UnitPrice <= 0.0` or `Quantity == 0` (e.g., inventory write-offs, damaged stock notes).
4. **Administrative Code Filtering:** Screened out non-commercial service codes (`POST`, `D`, `M`, `BANK CHARGES`, `AMAZONFEE`, `CRUK`, `DOT`).
5. **Missing Description Imputation:** Built an automated StockCode-to-Description lookup to restore missing product names across identical SKUs.
6. **Customer ID Standardization:** Standardized raw identifiers from floats (`17850.0`) to integer strings (`17850`), maintaining nullability for guest checkouts.
7. **Temporal Feature Engineering:** Derived `Year`, `Month`, `MonthName`, `YearMonth`, `Quarter`, `DayOfWeek`, and `Hour`.
8. **Financial Metrics:** Derived `Revenue = Quantity * UnitPrice` and `OrderValue = sum(Revenue) per InvoiceNo`.
9. **Category Classification:** Built rule-based natural language categorization mapping 3,803 unique products into 8 commercial categories (*Home Decor*, *Kitchen & Dining*, *Bags & Luggage*, *Stationery & Craft*, *Jewelry & Accessories*, *Seasonal & Holiday*, *Toys & Games*, *General Merchandise*).
10. **Data Retention:** Yields **522,707 clean commercial records** (**96.46% data retention**).

---

## 6. SQL Analytical Queries & Database

All cleaned transactions are loaded into an indexed SQLite 3 relational database (`data/processed/retail_analytics.db`).

The query suite in `sql/sales_analysis.sql` contains ANSI-compliant SQL (fully compatible with MySQL 8.0+ and SQLite 3.25+):
1. `executive_kpis`: High-level aggregate revenue, order count, and AOV.
2. `monthly_sales_trend`: Monthly revenue, customer volume, and units sold.
3. `mom_revenue_growth`: Uses the SQL window function `LAG()` to calculate month-over-month growth percentage.
4. `top_10_products_revenue`: Hero SKUs ranked by gross revenue.
5. `top_10_products_volume`: Top products by unit sales velocity.
6. `top_10_customers`: Highest lifetime spending accounts.
7. `invoice_aov_summary`: Statistical distribution of order ticket sizes.
8. `customer_repeat_behavior`: Segmentation of one-time vs. repeat buyers.
9. `country_sales_performance`: Global market revenue and geographic share.
10. `category_performance`: Category-level volume, revenue, and average realized unit price.

### Python-to-SQL Metric Reconciliation
The script `src/sql_engine.py` executes automated validation reconciling SQL outputs against Pandas computations:
- **Revenue Check:** SQL (`£10,009,302.93`) == Python (`£10,009,302.93`) — **Exact Match**
- **Order Count Check:** SQL (`19,774`) == Python (`19,774`) — **Exact Match**
- **Active Customers Check:** SQL (`4,333`) == Python (`4,333`) — **Exact Match**
- **Average Order Value:** SQL (`£506.19`) == Python (`£506.19`) — **Exact Match**

---

## 7. Customer RFM Segmentation & Machine Learning

Customer analytics (`src/segmentation.py`) evaluates **4,333 registered customer accounts** based on three behavioral vectors:
- **Recency ($R$):** Elapsed days from last transaction date to reference snapshot (2011-12-10).
- **Frequency ($F$):** Total number of distinct completed invoices.
- **Monetary ($M$):** Cumulative realized spend (£ GBP).

### Behavioral RFM Segments (Rule-Based Quintiles)
Customers receive 1–5 quintile scores for R, F, and M using `rank(method='first')`:

| Customer Segment | Customer Count | % of Accounts | Total Revenue (£) | % of Revenue | Strategic Profile |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Champions** | 1,119 | 25.8% | £5,778,845.26 | 65.0% | Bought recently, buy often, spend the most. Core commercial engine. |
| **Loyal Customers** | 825 | 19.0% | £1,174,369.66 | 13.2% | Consistent order cadence and solid spend. Responsive to promotions. |
| **Can't Lose Them** | 175 | 4.0% | £425,621.24 | 4.8% | Top historical spenders who haven't ordered in 180+ days. Urgent win-back. |
| **At Risk** | 481 | 11.1% | £384,609.78 | 4.3% | Above-average historical spend now exhibiting severe dormancy. |
| **About to Sleep** | 408 | 9.4% | £201,583.78 | 2.3% | Below-average recency and frequency. At risk of slipping into churn. |
| **Promising / Need Attention** | 346 | 8.0% | £156,642.31 | 1.8% | Recent buyers with moderate spend; candidates for upselling. |
| **Potential Loyalists** | 310 | 7.2% | £139,597.65 | 1.6% | Recent customers with 1–2 orders; high upside potential. |
| **Hibernating** | 557 | 12.9% | £124,032.86 | 1.4% | Low frequency, low spend, inactive for extended duration. |
| **Lost / Dormant** | 112 | 2.6% | £112,957.90 | 1.3% | Lowest R, F, and M scores. Cold accounts. |

### Unsupervised Machine Learning Clustering (K-Means)
To discover natural latent cohorts without hardcoded rules:
1. Applied **Log Transformation** `np.log1p(x)` to normalize right-skewed Monetary and Frequency distributions.
2. Standardized features using `StandardScaler()`.
3. Evaluated **Inertia (Elbow Method)** and **Silhouette Coefficients** across $k \in [2, 8]$.
4. Selected **$k = 4$ clusters** providing optimal separation (Silhouette: **0.3015**):
   - **Cluster 0 (High-Value VIPs):** 685 accounts | Mean Spend: £7,624.18 | Mean Frequency: 18.2 orders.
   - **Cluster 1 (Active Core Regulars):** 1,180 accounts | Mean Spend: £1,842.10 | Mean Frequency: 5.4 orders.
   - **Cluster 2 (Recent Casual Buyers):** 833 accounts | Mean Spend: £528.30 | Mean Frequency: 1.8 orders.
   - **Cluster 3 (Dormant / Lost Shoppers):** 1,635 accounts | Mean Spend: £385.20 | Mean Recency: 215.4 days.

---

## 8. Interactive Streamlit Analytics Application

The Streamlit web application (`app.py`) provides an executive-grade user interface with **6 responsive views**:

1. **📊 Executive Overview:** KPI metric cards (Revenue, Orders, Customers, AOV, Units), monthly revenue & order dual-axis trend, category distribution, and top 5 tables.
2. **📈 Sales Analytics:** MoM growth rate chart, order size (AOV) histogram, day of week & hour-of-day purchasing patterns.
3. **📦 Product Performance:** Top 10 products by revenue and volume, category breakdown, and an interactive SKU catalog search with real-time text matching.
4. **👥 Customer Analytics:** Repeat purchasing rates, order frequency distributions, and customer search lookup.
5. **🎯 RFM Customer Segmentation:** Behavioral segment distribution, K-Means cluster profiling, and an interactive segment account inspector.
6. **💡 Business Insights:** Strategic action plans answering the 5 core business questions, implementation roadmap, and downloadable reports.

### Features
- **Global Interactive Filters:** Date Range Slicer, Multi-Select Country Filter, Multi-Select Category Filter.
- **Dynamic Calculation:** Every KPI card and chart recalculates in real-time from the filtered in-memory dataset.
- **CSV Data Exports:** Dedicated download buttons on every page to export filtered summaries directly to Excel or CSV.

---

## 9. Power BI Dimensional Modeling & DAX

The platform prepares a complete Kimball Star Schema ready for Microsoft Power BI Desktop ingestion in `data/processed/powerbi/`:
- **FactSales.csv** (522,707 rows)
- **DimCustomer.csv** (4,334 rows with RFM and cluster attributes)
- **DimProduct.csv** (3,803 rows with category classifications)
- **DimDate.csv** (396 calendar dates spanning 2010–2011)
- **DimGeography.csv** (38 countries mapped to domestic and international trade zones)

### Production DAX Library
See [`reports/POWER_BI_DASHBOARD_GUIDE.md`](reports/POWER_BI_DASHBOARD_GUIDE.md) for full documentation, wireframes, and copy-paste DAX formulas, including:
- `[Total Revenue]` = `SUM(FactSales[Revenue])`
- `[Total Orders]` = `DISTINCTCOUNT(FactSales[InvoiceNo])`
- `[Average Order Value]` = `DIVIDE([Total Revenue], [Total Orders], 0)`
- `[Revenue Previous Month]` = `CALCULATE([Total Revenue], PREVIOUSMONTH(DimDate[FullDate]))`
- `[MoM Revenue Growth Pct]` = `DIVIDE([Total Revenue] - [Revenue Previous Month], [Revenue Previous Month], 0)`
- `[Repeat Customer Rate]` = `DIVIDE([Repeat Customers], [Active Customers], 0)`

---

## 10. Evidence-Based Business Recommendations

Detailed commercial recommendations are documented in [`reports/BUSINESS_RECOMMENDATIONS.md`](reports/BUSINESS_RECOMMENDATIONS.md):
1. **Hero Inventory Protection:** Automated ERP reorder safety buffers for `22423` (Regency Cakestand: £174k) and `85123A` (White Hanging Heart: £106k).
2. **VIP Account Win-Back Campaign:** Deploy dedicated account managers to re-engage the 175 "Can't Lose Them" accounts representing **£425,621.24 in lapsed spend**.
3. **Q3/Q4 Supply Chain Front-Loading:** Dock inventory by mid-August to capitalize on the massive pre-holiday surge in October (£1.10M) and November (£1.45M).
4. **VIP Loyalty Lock-In:** Build an exclusive VIP tier for the **1,119 Champions** who drive **65.0% of total customer revenue**.
5. **Tiered Free Shipping Incentives:** Set free freight thresholds at **£350** and **£600** to lift median order size from £232 toward the £506 mean.

---

## 11. Installation & Execution Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14
- Recommended: Python virtual environment (`venv`)

### 1. Clone & Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/your-username/retail-sales-customer-analytics.git
cd retail-sales-customer-analytics

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Execute Data Pipelines
```bash
# Step 1: Clean raw transactions and generate processed datasets
python -m src.data_cleaner

# Step 2: Ingest clean data into SQLite and validate queries
python -m src.sql_engine

# Step 3: Run EDA and generate Matplotlib/Seaborn figures
python -m src.eda

# Step 4: Run RFM segmentation and K-Means clustering
python -m src.segmentation

# Step 5: Export Power BI Star Schema tables
python -m src.powerbi_export
```

### 3. Launch Streamlit Analytics Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 12. Automated Test Suite & Verification

The project includes an enterprise-grade automated test suite in `tests/` covering data cleaning, SQL reconciliation, and RFM machine learning clustering.

To run the complete test suite:
```bash
python -m pytest tests -v
```

### Test Suite Results:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0
collected 16 items

tests/test_cleaning.py::test_deduplication PASSED                        [  6%]
tests/test_cleaning.py::test_cancellations_and_negative_quantities_filtered PASSED [ 12%]
tests/test_cleaning.py::test_zero_price_and_admin_codes_removed PASSED   [ 18%]
tests/test_cleaning.py::test_missing_description_imputation PASSED       [ 25%]
tests/test_cleaning.py::test_customer_id_formatting PASSED               [ 31%]
tests/test_cleaning.py::test_temporal_and_financial_features PASSED      [ 37%]
tests/test_cleaning.py::test_category_mapping PASSED                     [ 43%]
tests/test_rfm.py::test_rfm_metric_calculation PASSED                    [ 50%]
tests/test_rfm.py::test_rfm_score_and_segment_assignment PASSED          [ 56%]
tests/test_rfm.py::test_kmeans_clustering_execution PASSED               [ 62%]
tests/test_rfm.py::test_processed_rfm_file_exists PASSED                 [ 68%]
tests/test_sql.py::test_database_connection_and_table_exists PASSED      [ 75%]
tests/test_sql.py::test_sql_vs_python_executive_kpis PASSED              [ 81%]
tests/test_sql.py::test_sql_vs_python_monthly_trend PASSED               [ 87%]
tests/test_sql.py::test_sql_vs_python_top_products PASSED                [ 93%]
tests/test_sql.py::test_sql_mom_growth_window_function PASSED            [100%]

======================= 16 passed, 1 warning in 12.67s ========================
```

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
