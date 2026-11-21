"""
Page 2: Sales Analytics
Deep-dive temporal analysis, order size distributions, day/hour patterns, and growth rates.
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt


def render(df_filtered: pd.DataFrame):
    st.markdown("## 📈 Sales Performance & Temporal Dynamics")
    st.caption("Detailed breakdown of revenue seasonality, growth rates, ticket size distribution, and ordering windows.")

    if df_filtered.empty:
        st.warning("No transactions match the selected filter criteria.")
        return

    # --- Monthly Trend with MoM Growth ---
    st.subheader("Monthly Revenue & Month-over-Month (MoM) Growth")
    monthly = (
        df_filtered.groupby("YearMonth")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            Units_Sold=("Quantity", "sum")
        )
        .reset_index()
    )
    monthly["AOV"] = (monthly["Revenue"] / monthly["Orders"]).round(2)
    monthly["MoM_Growth_Pct"] = (monthly["Revenue"].pct_change() * 100).round(2)

    col1, col2 = st.columns([7, 5])
    with col1:
        # MoM bar chart
        growth_chart = (
            alt.Chart(monthly.dropna(subset=["MoM_Growth_Pct"]))
            .mark_bar()
            .encode(
                x=alt.X("YearMonth:N", title="Month", sort=None),
                y=alt.Y("MoM_Growth_Pct:Q", title="MoM Growth (%)"),
                color=alt.condition(
                    alt.datum.MoM_Growth_Pct > 0,
                    alt.value("#16a34a"),
                    alt.value("#dc2626")
                ),
                tooltip=[
                    alt.Tooltip("YearMonth:N", title="Month"),
                    alt.Tooltip("MoM_Growth_Pct:Q", format="+.2f", title="Growth %"),
                    alt.Tooltip("Revenue:Q", format="£,.2f", title="Revenue")
                ]
            )
            .properties(height=300)
        )
        st.altair_chart(growth_chart, use_container_width=True)

    with col2:
        st.dataframe(
            monthly.style.format({
                "Revenue": "£{:,.2f}",
                "Orders": "{:,}",
                "Customers": "{:,}",
                "Units_Sold": "{:,}",
                "AOV": "£{:,.2f}",
                "MoM_Growth_Pct": "{:+.2f}%"
            }),
            hide_index=True,
            use_container_width=True,
            height=300
        )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # --- Day of Week & Hour Analysis ---
    c_day, c_hour = st.columns(2)

    with c_day:
        st.subheader("Sales by Day of the Week")
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]
        df_dow = df_filtered[df_filtered["DayOfWeek"].isin(day_order)]
        dow_df = (
            df_dow.groupby("DayOfWeek")
            .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
            .reindex(day_order)
            .reset_index()
        )
        dow_chart = (
            alt.Chart(dow_df)
            .mark_bar(color="#0284c7", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("DayOfWeek:N", sort=day_order, title=""),
                y=alt.Y("Revenue:Q", title="Revenue (£ GBP)", axis=alt.Axis(format="~s")),
                tooltip=[
                    alt.Tooltip("DayOfWeek:N", title="Day"),
                    alt.Tooltip("Revenue:Q", format="£,.2f", title="Revenue"),
                    alt.Tooltip("Orders:Q", format=",", title="Orders")
                ]
            )
            .properties(height=280)
        )
        st.altair_chart(dow_chart, use_container_width=True)

    with c_hour:
        st.subheader("Sales by Hour of Day")
        hour_df = (
            df_filtered.groupby("Hour")
            .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
            .reset_index()
        )
        hour_chart = (
            alt.Chart(hour_df)
            .mark_area(color="#38bdf8", opacity=0.6, line=dict(color="#0284c7", width=2.5))
            .encode(
                x=alt.X("Hour:Q", title="Hour of Day (24h)", scale=alt.Scale(domain=[6, 20])),
                y=alt.Y("Orders:Q", title="Order Count"),
                tooltip=[
                    alt.Tooltip("Hour:Q", title="Hour"),
                    alt.Tooltip("Orders:Q", format=",", title="Orders"),
                    alt.Tooltip("Revenue:Q", format="£,.2f", title="Revenue")
                ]
            )
            .properties(height=280)
        )
        st.altair_chart(hour_chart, use_container_width=True)

    # --- Order Value (AOV) Distribution ---
    st.subheader("Order Value Distribution (Basket Size)")
    order_rev = df_filtered.groupby("InvoiceNo")["Revenue"].sum()
    mean_aov = order_rev.mean()
    median_aov = order_rev.median()
    p95_aov = order_rev.quantile(0.95)

    st.caption(f"**Mean AOV:** £{mean_aov:,.2f} | **Median AOV:** £{median_aov:,.2f} | **95th Percentile:** £{p95_aov:,.2f}")

    # Binned histogram up to 95th percentile for clean display
    hist_data = order_rev[order_rev <= p95_aov].reset_index()
    hist_chart = (
        alt.Chart(hist_data)
        .mark_bar(color="#64748b", opacity=0.85)
        .encode(
            x=alt.X("Revenue:Q", bin=alt.Bin(maxbins=40), title="Order Value (£ GBP)"),
            y=alt.Y("count()", title="Frequency (Number of Orders)"),
            tooltip=[
                alt.Tooltip("Revenue:Q", bin=True, title="Order Range"),
                alt.Tooltip("count()", title="Invoices")
            ]
        )
        .properties(height=250)
    )
    st.altair_chart(hist_chart, use_container_width=True)

    # --- CSV Export ---
    csv_bytes = monthly.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Sales Analytics Data (CSV)",
        data=csv_bytes,
        file_name="sales_performance_metrics.csv",
        mime="text/csv"
    )
