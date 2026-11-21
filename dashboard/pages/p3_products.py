"""
Page 3: Product Performance
Catalog velocity, hero SKUs, category performance, and product drill-down.
"""

import streamlit as st
import pandas as pd
import altair as alt


def render(df_filtered: pd.DataFrame):
    st.markdown("## 📦 Product & Category Performance")
    st.caption("Inventory sales velocity, top revenue generators, category share, and product-level analytics.")

    if df_filtered.empty:
        st.warning("No transactions match the selected filter criteria.")
        return

    # --- Top 10 Products: Revenue vs Volume ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Products by Revenue (£)")
        top_rev = (
            df_filtered.groupby(["StockCode", "Description", "Category"])["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=False)
            .head(10)
        )
        chart_rev = (
            alt.Chart(top_rev)
            .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
            .encode(
                y=alt.Y("Description:N", sort="-x", title="", axis=alt.Axis(labelLimit=250)),
                x=alt.X("Revenue:Q", title="Total Revenue (£ GBP)", axis=alt.Axis(format="~s")),
                color=alt.Color("Category:N", legend=alt.Legend(title="Category")),
                tooltip=[
                    alt.Tooltip("StockCode:N", title="SKU"),
                    alt.Tooltip("Description:N", title="Product"),
                    alt.Tooltip("Category:N", title="Category"),
                    alt.Tooltip("Revenue:Q", format="£,.2f", title="Revenue")
                ]
            )
            .properties(height=380)
        )
        st.altair_chart(chart_rev, use_container_width=True)

    with col2:
        st.subheader("Top 10 Best-Sellers by Units Sold")
        top_qty = (
            df_filtered.groupby(["StockCode", "Description", "Category"])["Quantity"]
            .sum()
            .reset_index()
            .sort_values("Quantity", ascending=False)
            .head(10)
        )
        chart_qty = (
            alt.Chart(top_qty)
            .mark_bar(color="#059669", cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
            .encode(
                y=alt.Y("Description:N", sort="-x", title="", axis=alt.Axis(labelLimit=250)),
                x=alt.X("Quantity:Q", title="Total Units Sold", axis=alt.Axis(format="~s")),
                tooltip=[
                    alt.Tooltip("StockCode:N", title="SKU"),
                    alt.Tooltip("Description:N", title="Product"),
                    alt.Tooltip("Category:N", title="Category"),
                    alt.Tooltip("Quantity:Q", format=",", title="Units Sold")
                ]
            )
            .properties(height=380)
        )
        st.altair_chart(chart_qty, use_container_width=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # --- Category Performance Table ---
    st.subheader("Category Performance Summary")
    total_rev = df_filtered["Revenue"].sum()
    cat_summary = (
        df_filtered.groupby("Category")
        .agg(
            Revenue=("Revenue", "sum"),
            Units_Sold=("Quantity", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Distinct_SKUs=("StockCode", "nunique")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    cat_summary["Revenue_Share_Pct"] = (cat_summary["Revenue"] / total_rev * 100).round(2)
    cat_summary["Avg_Realized_Price"] = (cat_summary["Revenue"] / cat_summary["Units_Sold"]).round(2)

    st.dataframe(
        cat_summary.style.format({
            "Revenue": "£{:,.2f}",
            "Units_Sold": "{:,}",
            "Orders": "{:,}",
            "Distinct_SKUs": "{:,}",
            "Revenue_Share_Pct": "{:.2f}%",
            "Avg_Realized_Price": "£{:.2f}"
        }),
        hide_index=True,
        use_container_width=True
    )

    # --- Interactive SKU Catalog Search ---
    st.subheader("Product Catalog Search & Drill-Down")
    search_query = st.text_input("🔍 Search product catalog by description or SKU code:", "")

    prod_catalog = (
        df_filtered.groupby(["StockCode", "Description", "Category"])
        .agg(
            Total_Revenue=("Revenue", "sum"),
            Units_Sold=("Quantity", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Avg_Price=("UnitPrice", "mean")
        )
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
    )

    if search_query:
        mask = (
            prod_catalog["Description"].str.contains(search_query.upper(), na=False) |
            prod_catalog["StockCode"].str.contains(search_query.upper(), na=False)
        )
        prod_catalog = prod_catalog[mask]

    st.dataframe(
        prod_catalog.head(50).style.format({
            "Total_Revenue": "£{:,.2f}",
            "Units_Sold": "{:,}",
            "Orders": "{:,}",
            "Avg_Price": "£{:.2f}"
        }),
        hide_index=True,
        use_container_width=True,
        height=320
    )

    # --- CSV Export ---
    csv_bytes = cat_summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Category Performance (CSV)",
        data=csv_bytes,
        file_name="category_performance.csv",
        mime="text/csv"
    )
