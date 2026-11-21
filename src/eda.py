"""
Exploratory Data Analysis (EDA) Module
Calculates retail performance metrics and generates professional visualizations using Matplotlib & Seaborn.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

FIGURES_DIR = os.path.join("reports", "eda_figures")
PROCESSED_FILE = os.path.join("data", "processed", "retail_cleaned.parquet")


def set_plotting_style():
    """Configures clean, modern aesthetic styling for matplotlib and seaborn."""
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "axes.labelweight": "semibold",
        "figure.titlesize": 16,
        "figure.titleweight": "bold",
        "figure.dpi": 300
    })


def run_comprehensive_eda(df: pd.DataFrame = None) -> dict:
    """
    Executes full exploratory data analysis on the cleaned retail dataset.
    Saves high-resolution visualizations to reports/eda_figures/.
    """
    if df is None:
        if os.path.exists(PROCESSED_FILE):
            df = pd.read_parquet(PROCESSED_FILE)
        else:
            df = pd.read_csv(os.path.join("data", "processed", "retail_cleaned.csv"))

    os.makedirs(FIGURES_DIR, exist_ok=True)
    set_plotting_style()

    results = {}

    # --- 1. Overall KPIs ---
    total_rev = float(df["Revenue"].sum())
    total_orders = int(df["InvoiceNo"].nunique())
    total_customers = int(df["CustomerID"].dropna().nunique())
    total_items = int(df["Quantity"].sum())
    aov = round(total_rev / total_orders, 2)

    results["kpis"] = {
        "total_revenue": total_rev,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_items_sold": total_items,
        "average_order_value": aov
    }

    # --- 2. Monthly Revenue Trend ---
    monthly = (
        df.groupby("YearMonth")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique")
        )
        .reset_index()
    )
    monthly["MoM_Growth_Pct"] = monthly["Revenue"].pct_change() * 100

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    x = np.arange(len(monthly))
    bars = ax1.bar(x, monthly["Revenue"] / 1000, color="#1f77b4", alpha=0.8, width=0.55, label="Revenue (£k)")
    line = ax2.plot(x, monthly["Orders"], color="#d62728", marker="o", linewidth=2.5, markersize=6, label="Order Count")

    ax1.set_xticks(x)
    ax1.set_xticklabels(monthly["YearMonth"], rotation=45, ha="right")
    ax1.set_ylabel("Revenue (£ Thousands, GBP)", color="#1f77b4")
    ax2.set_ylabel("Number of Orders", color="#d62728")
    ax1.set_title("Monthly Revenue & Order Volume Trend (2010 - 2011)", pad=15)

    # Annotate peaks
    max_idx = monthly["Revenue"].idxmax()
    ax1.annotate(f"Peak: £{monthly.loc[max_idx, 'Revenue']:,.0f}",
                 (max_idx, monthly.loc[max_idx, "Revenue"] / 1000),
                 textcoords="offset points", xytext=(0, 10), ha="center",
                 fontweight="bold", color="#1f77b4")

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "01_monthly_revenue_trend.png"))
    plt.close(fig)

    results["monthly_summary"] = monthly.to_dict(orient="records")

    # --- 3. Top 10 Products by Revenue ---
    top_rev_prod = (
        df.groupby(["StockCode", "Description"])["Revenue"]
        .sum()
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(data=top_rev_prod, y="Description", x="Revenue", palette="Blues_r", ax=ax)
    ax.set_title("Top 10 Products by Total Revenue", pad=15)
    ax.set_xlabel("Total Revenue (£ GBP)")
    ax.set_ylabel("")
    for i, v in enumerate(top_rev_prod["Revenue"]):
        ax.text(v + 1000, i, f"£{v:,.0f}", va="center", fontweight="semibold", fontsize=10)
    ax.set_xlim(0, top_rev_prod["Revenue"].max() * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "02_top_10_products_revenue.png"))
    plt.close(fig)

    results["top_revenue_products"] = top_rev_prod.to_dict(orient="records")

    # --- 4. Top 10 Products by Volume (Units Sold) ---
    top_qty_prod = (
        df.groupby(["StockCode", "Description"])["Quantity"]
        .sum()
        .reset_index()
        .sort_values("Quantity", ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(data=top_qty_prod, y="Description", x="Quantity", palette="Greens_r", ax=ax)
    ax.set_title("Top 10 Best-Selling Products by Units Sold", pad=15)
    ax.set_xlabel("Units Sold")
    ax.set_ylabel("")
    for i, v in enumerate(top_qty_prod["Quantity"]):
        ax.text(v + 500, i, f"{v:,.0f}", va="center", fontweight="semibold", fontsize=10)
    ax.set_xlim(0, top_qty_prod["Quantity"].max() * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "03_top_10_products_volume.png"))
    plt.close(fig)

    # --- 5. Category Performance ---
    cat_summary = (
        df.groupby("Category")
        .agg(
            Revenue=("Revenue", "sum"),
            Units_Sold=("Quantity", "sum"),
            Orders=("InvoiceNo", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    cat_summary["Revenue_Share_Pct"] = (cat_summary["Revenue"] / total_rev * 100).round(2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    sns.barplot(data=cat_summary, x="Revenue", y="Category", palette="mako", ax=ax1)
    ax1.set_title("Revenue by Product Category (£)", pad=12)
    ax1.set_xlabel("Revenue (£)")
    ax1.set_ylabel("")
    for i, v in enumerate(cat_summary["Revenue"]):
        ax1.text(v * 1.02, i, f"£{v:,.0f}", va="center", fontsize=9, fontweight="bold")
    ax1.set_xlim(0, cat_summary["Revenue"].max() * 1.25)

    wedges, texts, autotexts = ax2.pie(
        cat_summary["Revenue"],
        labels=cat_summary["Category"],
        autopct="%1.1f%%",
        startangle=140,
        colors=sns.color_palette("mako", len(cat_summary)),
        textprops=dict(color="black", fontsize=9)
    )
    plt.setp(autotexts, size=9, weight="bold")
    ax2.set_title("Category Revenue Share (%)", pad=12)

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "04_category_revenue_distribution.png"))
    plt.close(fig)

    results["category_performance"] = cat_summary.to_dict(orient="records")

    # --- 6. Country Performance (Pareto) ---
    country_summary = (
        df.groupby("Country")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    country_summary["Rev_Share_Pct"] = (country_summary["Revenue"] / total_rev * 100).round(2)

    top_countries = country_summary.head(10)
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=top_countries, x="Country", y="Revenue", palette="crest", ax=ax)
    ax.set_title("Top 10 Geographic Markets by Revenue (£ GBP)", pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Revenue (£)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha="right")
    for i, v in enumerate(top_countries["Revenue"]):
        ax.text(i, v + 25000, f"£{v/1000:,.0f}k", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylim(0, top_countries["Revenue"].max() * 1.15)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "05_country_revenue_pareto.png"))
    plt.close(fig)

    results["top_countries"] = top_countries.to_dict(orient="records")

    # --- 7. Daily & Hourly Heatmap ---
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]
    df_dow = df[df["DayOfWeek"].isin(day_order)]
    heatmap_data = (
        df_dow.groupby(["DayOfWeek", "Hour"])["InvoiceNo"]
        .nunique()
        .unstack(fill_value=0)
        .reindex(day_order)
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="YlGnBu", annot=True, fmt="d", cbar_kws={"label": "Number of Orders"}, ax=ax)
    ax.set_title("Weekly Purchasing Heatmap: Orders by Day of Week & Hour", pad=15)
    ax.set_xlabel("Hour of Day (24h)")
    ax.set_ylabel("Day of Week")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "06_sales_by_day_and_hour.png"))
    plt.close(fig)

    # --- 8. Order Value (AOV) Distribution ---
    order_totals = df.groupby("InvoiceNo")["Revenue"].sum()
    order_totals_trimmed = order_totals[order_totals.between(0, 2000)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    sns.histplot(order_totals_trimmed, bins=40, kde=True, color="#2b5c8f", ax=ax1)
    ax1.axvline(aov, color="red", linestyle="--", linewidth=2, label=f"Mean AOV: £{aov:,.2f}")
    ax1.axvline(order_totals.median(), color="green", linestyle=":", linewidth=2, label=f"Median: £{order_totals.median():,.2f}")
    ax1.set_title("Order Value Distribution (Up to £2,000)", pad=12)
    ax1.set_xlabel("Order Value (£)")
    ax1.set_ylabel("Frequency")
    ax1.legend()

    sns.boxplot(x=order_totals_trimmed, color="#85c1e9", ax=ax2)
    ax2.set_title("Order Value Boxplot (Trimmed)", pad=12)
    ax2.set_xlabel("Order Value (£)")

    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "07_order_value_distribution.png"))
    plt.close(fig)

    # --- 9. Repeat Purchase Behavior ---
    cust_orders = df.dropna(subset=["CustomerID"]).groupby("CustomerID")["InvoiceNo"].nunique()
    one_time = int((cust_orders == 1).sum())
    repeat = int((cust_orders > 1).sum())
    repeat_rate = round((repeat / total_customers) * 100, 2)

    results["repeat_behavior"] = {
        "one_time_buyers": one_time,
        "repeat_buyers": repeat,
        "repeat_rate_pct": repeat_rate,
        "avg_orders_per_customer": round(float(cust_orders.mean()), 2),
        "max_orders_single_customer": int(cust_orders.max())
    }

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.pie(
        [repeat, one_time],
        labels=[f"Repeat Customers ({repeat_rate}%)", f"One-Time Customers ({100 - repeat_rate:.1f}%)"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#2ca02c", "#d62728"],
        explode=(0.06, 0),
        shadow=True
    )
    ax.set_title("Customer Retention: Repeat vs One-Time Purchasers", pad=15)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "08_repeat_purchase_behavior.png"))
    plt.close(fig)

    # Save summary json
    summary_path = os.path.join("reports", "eda_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"EDA successfully completed. Visualizations saved to {FIGURES_DIR}/")
    return results


if __name__ == "__main__":
    eda_res = run_comprehensive_eda()
    print("Key EDA Results:")
    print("KPIs:", eda_res["kpis"])
    print("Repeat Behavior:", eda_res["repeat_behavior"])
