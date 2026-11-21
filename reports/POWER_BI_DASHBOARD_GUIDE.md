# Power BI Dashboard Implementation & Data Modeling Guide
**Project:** Retail Sales & Customer Analytics Platform  
**Target Environment:** Microsoft Power BI Desktop & Power BI Service  
**Data Architecture:** Kimball Star Schema  
**Date of Implementation:** November 2026  

---

## 1. Executive Summary & Architecture Overview

This document provides complete technical blueprints, star schema data models, relationships, DAX measure definitions, and visual design specifications to reproduce the **Retail Sales & Customer Analytics Platform** in Microsoft Power BI.

> **Note on Deliverable Status:**  
> In compliance with strict engineering integrity standards, the cleaned, normalized Star Schema tables have been generated and exported to `data/processed/powerbi/*.csv`. A `.pbix` binary file cannot be generated headlessly without Microsoft Power BI Desktop running in a Windows desktop session. This guide provides exact, turn-key instructions and copy-paste DAX formulas to build the dashboard in Power BI Desktop in under 15 minutes.

---

## 2. Star Schema Data Architecture

The Power BI model follows a Kimball dimensional modeling architecture with **1 central Fact table** and **4 surrounding Dimension tables**:

```
                       +-------------------+
                       |    DimCustomer    |
                       |-------------------|
                       | CustomerID (PK)   |
                       | Customer_Segment  |
                       | Cluster_Name      |
                       | RFM Scores        |
                       +---------+---------+
                                 | 1
                                 |
                                 | *
+-----------------+    *   +-----+------+   *    +-----------------+
|   DimProduct    +--------+ FactSales  +--------+     DimDate     |
|-----------------| 1      |------------|      1 |-----------------|
| StockCode (PK)  |        | InvoiceNo  |        | DateKey (PK)    |
| Description     |        | StockCode  |        | FullDate        |
| Category        |        | CustomerID |        | Year, Quarter   |
| AvgUnitPrice    |        | DateKey    |        | YearMonth       |
+-----------------+        | Quantity   |        | DayOfWeek       |
                           | UnitPrice  |        +-----------------+
                           | Revenue    |
                           | Country    |
                           +-----+------+
                                 | *
                                 |
                                 | 1
                       +---------+---------+
                       |   DimGeography    |
                       |-------------------|
                       | Country (PK)      |
                       | Region            |
                       +-------------------+
```

### Table Specifications & File Locations

| Table Name | Source File | Row Count | Primary / Foreign Keys | Description |
| :--- | :--- | :--- | :--- | :--- |
| **FactSales** | `data/processed/powerbi/FactSales.csv` | 522,707 | FK: `StockCode`, `CustomerID`, `DateKey`, `Country` | Granular line-item transactional sales ledger. |
| **DimCustomer** | `data/processed/powerbi/DimCustomer.csv` | 4,334 | PK: `CustomerID` | Customer profiles with behavioral RFM scores and K-Means clusters. |
| **DimProduct** | `data/processed/powerbi/DimProduct.csv` | 3,803 | PK: `StockCode` | Product catalog with categorized merchandise classifications. |
| **DimDate** | `data/processed/powerbi/DimDate.csv` | 396 | PK: `DateKey` | Continuous date dimension supporting time-intelligence functions. |
| **DimGeography** | `data/processed/powerbi/DimGeography.csv` | 38 | PK: `Country` | Geographic hierarchy mapping countries to regional trade zones. |

---

## 3. Power BI Relationships Setup

In the Power BI Model View (`Model` tab), establish the following relationships:

1. **FactSales[DateKey]** `*` ─── `1` **DimDate[DateKey]**
   - Cardinality: Many to One (`*:1`)
   - Cross-filter direction: Single (`FactSales` filtered by `DimDate`)
   - Mark as Date Table: Set `DimDate[FullDate]` as the official Date Table.

2. **FactSales[CustomerID]** `*` ─── `1` **DimCustomer[CustomerID]**
   - Cardinality: Many to One (`*:1`)
   - Cross-filter direction: Single

3. **FactSales[StockCode]** `*` ─── `1` **DimProduct[StockCode]**
   - Cardinality: Many to One (`*:1`)
   - Cross-filter direction: Single

4. **FactSales[Country]** `*` ─── `1` **DimGeography[Country]**
   - Cardinality: Many to One (`*:1`)
   - Cross-filter direction: Single

---

## 4. Production DAX Measure Library

Create a dedicated measures table in Power BI named `_Measures` and insert the following production DAX calculations.

### 4.1 Base Core Measures

```dax
// 1. Total Gross Revenue
Total Revenue = 
SUM(FactSales[Revenue])

// 2. Total Units Sold
Total Units Sold = 
SUM(FactSales[Quantity])

// 3. Total Order Count
Total Orders = 
DISTINCTCOUNT(FactSales[InvoiceNo])

// 4. Unique Active Customers
Active Customers = 
CALCULATE(
    DISTINCTCOUNT(FactSales[CustomerID]),
    FactSales[CustomerID] <> "GUEST"
)

// 5. Average Order Value (AOV)
Average Order Value = 
DIVIDE(
    [Total Revenue],
    [Total Orders],
    0
)

// 6. Average Items per Order
Average Units per Order = 
DIVIDE(
    [Total Units Sold],
    [Total Orders],
    0
)
```

### 4.2 Time Intelligence & Growth Measures

```dax
// 7. Previous Month Revenue (PM)
Revenue Previous Month = 
CALCULATE(
    [Total Revenue],
    PREVIOUSMONTH(DimDate[FullDate])
)

// 8. Month-over-Month Revenue Growth (£)
MoM Revenue Growth Amount = 
IF(
    ISBLANK([Revenue Previous Month]),
    BLANK(),
    [Total Revenue] - [Revenue Previous Month]
)

// 9. Month-over-Month Revenue Growth (%)
MoM Revenue Growth Pct = 
DIVIDE(
    [MoM Revenue Growth Amount],
    [Revenue Previous Month],
    0
)

// 10. Quarter-to-Date Revenue (QTD)
Revenue QTD = 
TOTALQTD(
    [Total Revenue],
    DimDate[FullDate]
)

// 11. Year-to-Date Revenue (YTD)
Revenue YTD = 
TOTALYTD(
    [Total Revenue],
    DimDate[FullDate]
)
```

### 4.3 Customer Behavior & Retention Measures

```dax
// 12. Repeat Customer Count (Customers with > 1 invoice)
Repeat Customers = 
COUNTROWS(
    FILTER(
        VALUES(DimCustomer[CustomerID]),
        DimCustomer[CustomerID] <> "GUEST" &&
        CALCULATE(DISTINCTCOUNT(FactSales[InvoiceNo])) > 1
    )
)

// 13. Customer Retention Rate (%)
Customer Retention Rate = 
DIVIDE(
    [Repeat Customers],
    [Active Customers],
    0
)

// 14. Average Revenue per Customer (ARPU)
Revenue per Customer = 
DIVIDE(
    [Total Revenue],
    [Active Customers],
    0
)
```

---

## 5. Visual Dashboard Layout & Wireframes

The recommended dashboard consists of **3 interactive reporting canvases**:

### Page 1: Executive KPI & Sales Overview
* **Header / Filter Bar:**
  - Date Range Slicer (`DimDate[FullDate]`)
  - Geographic Region Slicer (`DimGeography[Region]`)
  - Product Category Dropdown (`DimProduct[Category]`)
* **KPI Card Row:**
  - Card 1: `Total Revenue` (Formatted as `£10.01M`)
  - Card 2: `Total Orders` (Formatted as `19.77K`)
  - Card 3: `Average Order Value` (Formatted as `£506.19`)
  - Card 4: `Active Customers` (Formatted as `4,333`)
  - Card 5: `Customer Retention Rate` (Formatted as `65.27%`)
* **Visual 1 (Area / Column Chart - 60% Width):**  
  - X-Axis: `DimDate[YearMonth]`
  - Y-Axis: `[Total Revenue]` (Bars) + `[MoM Revenue Growth Pct]` (Line)
* **Visual 2 (Donut Chart - 40% Width):**  
  - Legend: `DimGeography[Region]`
  - Values: `[Total Revenue]`
* **Visual 3 (Table - Bottom 100%):**  
  - Monthly breakdown: `YearMonth`, `Total Revenue`, `Total Orders`, `MoM Revenue Growth Pct`, `Average Order Value`.

### Page 2: Product & Category Intelligence
* **Visual 1 (Horizontal Bar Chart):**  
  - Y-Axis: `DimProduct[Category]`
  - X-Axis: `[Total Revenue]`
  - Data Labels: On (£ and %)
* **Visual 2 (Horizontal Bar Chart):**  
  - Top 10 Products by Revenue: `DimProduct[Description]` ranked by `[Total Revenue]`
* **Visual 3 (Scatter Plot - Product Velocity):**  
  - X-Axis: `[Total Units Sold]`
  - Y-Axis: `[Average Order Value]`
  - Bubble Size: `[Total Revenue]`
  - Details: `DimProduct[Description]`
* **Visual 4 (Decomposition Tree):**  
  - Analyze: `[Total Revenue]`
  - Explain by: `DimGeography[Region]` -> `DimProduct[Category]` -> `DimProduct[Description]`

### Page 3: Customer RFM Segmentation & Cohort Analysis
* **Visual 1 (Clustered Bar Chart):**  
  - Y-Axis: `DimCustomer[Customer_Segment]`
  - X-Axis 1: `[Active Customers]`
  - X-Axis 2: `[Total Revenue]`
* **Visual 2 (Heatmap Matrix):**  
  - Rows: `DimCustomer[R_Score]`
  - Columns: `DimCustomer[F_Score]`
  - Values: `[Total Revenue]` (Conditional formatting background color: Green to Red)
* **Visual 3 (Scatter Plot - K-Means Clusters):**  
  - X-Axis: `DimCustomer[Recency]`
  - Y-Axis: `DimCustomer[Frequency]` (Log scale)
  - Color / Legend: `DimCustomer[Cluster_Name]`
  - Tooltip: `DimCustomer[Monetary]`, `DimCustomer[CustomerID]`
* **Visual 4 (Drill-Through Customer Table):**  
  - Columns: `CustomerID`, `Customer_Segment`, `Cluster_Name`, `Recency`, `Frequency`, `Monetary`, `AvgOrderValue`, `LastPurchaseDate`.

---

## 6. Step-by-Step Power BI Loading Instructions

1. Launch **Microsoft Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Sequentially import the 5 files located in `data/processed/powerbi/`:
   - `FactSales.csv`
   - `DimCustomer.csv`
   - `DimProduct.csv`
   - `DimDate.csv`
   - `DimGeography.csv`
4. In Power Query Editor, verify data types:
   - `DateKey`: Whole Number (`Int64`)
   - `Quantity`, `Year`, `Month`: Whole Number
   - `UnitPrice`, `Revenue`, `Monetary`: Fixed Decimal Number (Currency)
   - Click **Close & Apply**.
5. Go to the **Model View** and verify the 4 relationships described in Section 3.
6. Create the `_Measures` table: Click **Enter Data**, name the table `_Measures`, create the measures listed in Section 4, and delete the default blank column.
7. Build the 3 dashboard pages using the visual specifications in Section 5.
8. Save the file as `Retail_Analytics_Platform.pbix` and publish to Power BI Service.
