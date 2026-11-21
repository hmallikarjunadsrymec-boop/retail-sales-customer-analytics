"""
Page 5: RFM Customer Segmentation
Behavioral segmentation, RFM score quintiles, K-Means clustering, and cohort targeting.
"""

import streamlit as st
import pandas as pd
import altair as alt
from dashboard.styles import render_kpi_card


def render(df_rfm: pd.DataFrame):
    st.markdown("## 🎯 Customer RFM Segmentation & ML Clustering")
    st.caption("Behavioral customer segmentation based on Recency (R), Frequency (F), and Monetary value (M).")

    if df_rfm.empty:
        st.warning("No RFM data available.")
        return

    # --- KPI Row ---
    total_cust = len(df_rfm)
    total_rev = df_rfm["Monetary"].sum()
    champions_count = (df_rfm["Customer_Segment"] == "Champions").sum()
    champions_rev = df_rfm[df_rfm["Customer_Segment"] == "Champions"]["Monetary"].sum()
    at_risk_count = (df_rfm["Customer_Segment"] == "At Risk").sum()
    cant_lose_count = (df_rfm["Customer_Segment"] == "Can't Lose Them").sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("Segmented Customers", f"{total_cust:,}", "Total registered accounts", "positive")
    with col2:
        champ_share = (champions_rev / total_rev * 100) if total_rev > 0 else 0
        render_kpi_card("Champions Spend Share", f"{champ_share:.1f}%", f"{champions_count:,} accounts (£{champions_rev/1e6:.2f}M)", "positive")
    with col3:
        render_kpi_card("At Risk Customers", f"{at_risk_count:,}", "Requires re-engagement", "negative")
    with col4:
        render_kpi_card("Can't Lose Them", f"{cant_lose_count:,}", "Immediate VIP intervention", "negative")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # --- Segment Breakdown: Count vs Revenue ---
    st.subheader("RFM Behavioral Segments: Customers vs Revenue Contribution")
    seg_summary = (
        df_rfm.groupby("Customer_Segment")
        .agg(
            Customer_Count=("CustomerID", "count"),
            Total_Revenue=("Monetary", "sum"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean"),
            Avg_Monetary=("Monetary", "mean")
        )
        .reset_index()
        .sort_values("Total_Revenue", ascending=False)
    )
    seg_summary["Cust_Share_Pct"] = (seg_summary["Customer_Count"] / total_cust * 100).round(2)
    seg_summary["Rev_Share_Pct"] = (seg_summary["Total_Revenue"] / total_rev * 100).round(2)

    c1, c2 = st.columns(2)
    with c1:
        bar_count = (
            alt.Chart(seg_summary)
            .mark_bar(color="#3b82f6", cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
            .encode(
                y=alt.Y("Customer_Segment:N", sort="-x", title=""),
                x=alt.X("Customer_Count:Q", title="Customer Count"),
                tooltip=[
                    alt.Tooltip("Customer_Segment:N", title="Segment"),
                    alt.Tooltip("Customer_Count:Q", format=",", title="Customers"),
                    alt.Tooltip("Cust_Share_Pct:Q", format=".1f", title="% of Base")
                ]
            )
            .properties(height=300)
        )
        st.altair_chart(bar_count, use_container_width=True)

    with c2:
        bar_rev = (
            alt.Chart(seg_summary)
            .mark_bar(color="#10b981", cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
            .encode(
                y=alt.Y("Customer_Segment:N", sort="-x", title=""),
                x=alt.X("Total_Revenue:Q", title="Total Revenue (£ GBP)", axis=alt.Axis(format="~s")),
                tooltip=[
                    alt.Tooltip("Customer_Segment:N", title="Segment"),
                    alt.Tooltip("Total_Revenue:Q", format="£,.2f", title="Revenue"),
                    alt.Tooltip("Rev_Share_Pct:Q", format=".1f", title="% of Spend")
                ]
            )
            .properties(height=300)
        )
        st.altair_chart(bar_rev, use_container_width=True)

    # --- K-Means Machine Learning Clusters ---
    st.subheader("Machine Learning K-Means Clusters")
    st.caption("Unsupervised clustering evaluated via Elbow Inertia & Silhouette analysis (k=4).")

    cluster_summary = (
        df_rfm.groupby(["KMeans_Cluster", "Cluster_Name"])
        .agg(
            Accounts=("CustomerID", "count"),
            Mean_Recency=("Recency", "mean"),
            Mean_Frequency=("Frequency", "mean"),
            Mean_Spend=("Monetary", "mean"),
            Total_Spend=("Monetary", "sum")
        )
        .reset_index()
        .sort_values("Total_Spend", ascending=False)
    )

    st.dataframe(
        cluster_summary.style.format({
            "Accounts": "{:,}",
            "Mean_Recency": "{:.1f} days",
            "Mean_Frequency": "{:.1f} orders",
            "Mean_Spend": "£{:,.2f}",
            "Total_Spend": "£{:,.2f}"
        }),
        hide_index=True,
        use_container_width=True
    )

    # --- Interactive Segment Filter & Drill-Through ---
    st.subheader("Segment Account Explorer")
    all_segments = list(seg_summary["Customer_Segment"].unique())
    selected_seg = st.selectbox("Select Segment to inspect accounts:", ["All Segments"] + all_segments)

    inspect_df = df_rfm if selected_seg == "All Segments" else df_rfm[df_rfm["Customer_Segment"] == selected_seg]

    display_cols = [
        "CustomerID", "Customer_Segment", "Cluster_Name",
        "Recency", "Frequency", "Monetary", "AvgOrderValue",
        "RFM_Score", "Country", "LastPurchaseDate"
    ]
    st.dataframe(
        inspect_df[display_cols].head(100).style.format({
            "Recency": "{:,} d",
            "Frequency": "{:,}",
            "Monetary": "£{:,.2f}",
            "AvgOrderValue": "£{:,.2f}"
        }),
        hide_index=True,
        use_container_width=True,
        height=320
    )

    # --- CSV Export ---
    csv_bytes = df_rfm.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Full Customer RFM Profiles (CSV)",
        data=csv_bytes,
        file_name="customer_rfm_segments.csv",
        mime="text/csv"
    )
