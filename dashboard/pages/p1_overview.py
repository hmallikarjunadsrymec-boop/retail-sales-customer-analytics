"""
Page 1: Executive Overview
High-level strategic KPIs, revenue trends, and key performance indicators.
"""

import streamlit as st
import pandas as pd
import altair as alt
from dashboard.styles import render_kpi_card


def render(df_filtered: pd.DataFrame, df_rfm: pd.DataFrame):
    st.markdown("## 📊 Executive Performance Overview")
    st.caption("Strategic commercial performance dashboard reflecting live filtered transactions.")

    if df_filtered.empty:
        st.warning("No transactions match the selected filter criteria. Please adjust your filters.")
        return

    # --- KPI Row ---
    total_rev = float(df_filtered["Revenue"].sum())
    total_orders = int(df_filtered["InvoiceNo"].nunique())
    total_units = int(df_filtered["Quantity"].sum())
    active_customers = int(df_filtered["CustomerID"].dropna().nunique())
    aov = round(total_rev / total_orders, 2) if total_orders > 0 else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Total Revenue", f"£{total_rev:,.2f}", "Gross realized sales", "positive")
    with col2:
        render_kpi_card("Total Orders", f"{total_orders:,}", "Distinct checkouts", "neutral")
    with col3:
        render_kpi_card("Average Order Value", f"£{aov:,.2f}", "Mean basket size", "neutral")
    with col4:
        render_kpi_card("Active Customers", f"{active_customers:,}", "Identified accounts", "positive")
    with col5:
        render_kpi_card("Units Sold", f"{total_units:,}", "Dispatched items", "neutral")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # --- Trend Visualizations ---
    c1, c2 = st.columns([7, 5])

    with c1:
        st.subheader("Monthly Revenue Trend")
        monthly = (
            df_filtered.groupby("YearMonth")
            .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
            .reset_index()
        )

        base = alt.Chart(monthly).encode(x=alt.X("YearMonth:N", title="Year-Month", sort=None))
        bar = base.mark_bar(color="#2b5c8f", cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            y=alt.Y("Revenue:Q", title="Revenue (£ GBP)", axis=alt.Axis(format="~s")),
            tooltip=[
                alt.Tooltip("YearMonth:N", title="Month"),
                alt.Tooltip("Revenue:Q", format="£,.2f", title="Revenue"),
                alt.Tooltip("Orders:Q", format=",", title="Orders")
            ]
        )
        line = base.mark_line(color="#e65100", strokeWidth=2.5, point=True).encode(
            y=alt.Y("Orders:Q", title="Order Count", axis=alt.Axis(orient="right")),
            tooltip=[
                alt.Tooltip("YearMonth:N", title="Month"),
                alt.Tooltip("Orders:Q", format=",", title="Orders")
            ]
        )
        chart = alt.layer(bar, line).resolve_scale(y="independent").properties(height=340)
        st.altair_chart(chart, use_container_width=True)

    with c2:
        st.subheader("Revenue by Category")
        cat_df = (
            df_filtered.groupby("Category")["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=False)
        )
        cat_chart = (
            alt.Chart(cat_df)
            .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
            .encode(
                y=alt.Y("Category:N", sort="-x", title=""),
                x=alt.X("Revenue:Q", title="Revenue (£ GBP)", axis=alt.Axis(format="~s")),
                color=alt.Color("Revenue:Q", scale=alt.Scale(scheme="blues"), legend=None),
                tooltip=[
                    alt.Tooltip("Category:N", title="Category"),
                    alt.Tooltip("Revenue:Q", format="£,.2f", title="Revenue")
                ]
            )
            .properties(height=340)
        )
        st.altair_chart(cat_chart, use_container_width=True)

    # --- Top Products & Markets ---
    col_p, col_c = st.columns(2)

    with col_p:
        st.subheader("Top 5 Products by Revenue")
        top_p = (
            df_filtered.groupby(["StockCode", "Description"])["Revenue"]
            .sum()
            .reset_index()
            .sort_values("Revenue", ascending=False)
            .head(5)
        )
        top_p["Revenue (£)"] = top_p["Revenue"].apply(lambda x: f"£{x:,.2f}")
        st.dataframe(
            top_p.rename(columns={"StockCode": "SKU", "Description": "Product Description"}),
            hide_index=True,
            use_container_width=True
        )

    with col_c:
        st.subheader("Top 5 Geographic Markets")
        top_geo = (
            df_filtered.groupby("Country")
            .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
            .reset_index()
            .sort_values("Revenue", ascending=False)
            .head(5)
        )
        top_geo["Revenue (£)"] = top_geo["Revenue"].apply(lambda x: f"£{x:,.2f}")
        top_geo["Orders"] = top_geo["Orders"].apply(lambda x: f"{x:,}")
        st.dataframe(top_geo, hide_index=True, use_container_width=True)

    # --- CSV Export ---
    st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
    csv_data = monthly.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Monthly Performance Summary (CSV)",
        data=csv_data,
        file_name="monthly_executive_summary.csv",
        mime="text/csv"
    )
