"""
Page 4: Customer Analytics
Purchasing patterns, repeat purchase behavior, customer lifetime metrics, and geographic distribution.
"""

import streamlit as st
import pandas as pd
import altair as alt
from dashboard.styles import render_kpi_card


def render(df_filtered: pd.DataFrame, df_rfm: pd.DataFrame):
    st.markdown("## 👥 Customer Purchasing Behavior")
    st.caption("Account retention, repeat order dynamics, purchasing frequency, and top client accounts.")

    # Filter to registered accounts in the current filtered transactions
    valid_cust_df = df_filtered.dropna(subset=["CustomerID"]).copy()
    if valid_cust_df.empty:
        st.warning("No registered customer transactions found in the selected filter range.")
        return

    cust_summary = (
        valid_cust_df.groupby("CustomerID")
        .agg(
            Total_Spend=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Units_Purchased=("Quantity", "sum"),
            Country=("Country", "first"),
            First_Order=("Date", "min"),
            Last_Order=("Date", "max")
        )
        .reset_index()
    )
    cust_summary["AOV"] = (cust_summary["Total_Spend"] / cust_summary["Orders"]).round(2)

    total_customers = len(cust_summary)
    repeat_customers = int((cust_summary["Orders"] > 1).sum())
    one_time_customers = total_customers - repeat_customers
    repeat_rate = round((repeat_customers / total_customers * 100), 2) if total_customers > 0 else 0.0

    # --- KPI Row ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Active Registered Customers", f"{total_customers:,}", "In current filtered view", "positive")
    with c2:
        render_kpi_card("Repeat Buyers", f"{repeat_customers:,}", f"{repeat_rate}% repeat rate", "positive")
    with c3:
        render_kpi_card("One-Time Buyers", f"{one_time_customers:,}", f"{100 - repeat_rate:.1f}% single order", "neutral")
    with c4:
        avg_spend = cust_summary["Total_Spend"].mean()
        render_kpi_card("Average Spend / Customer", f"£{avg_spend:,.2f}", "Mean lifetime value", "neutral")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # --- Visualizations: Retention Donut & Frequency Distribution ---
    col1, col2 = st.columns([5, 7])

    with col1:
        st.subheader("Customer Retention Mix")
        mix_df = pd.DataFrame([
            {"Type": "Repeat Customers", "Count": repeat_customers},
            {"Type": "One-Time Buyers", "Count": one_time_customers}
        ])
        pie_chart = (
            alt.Chart(mix_df)
            .mark_arc(innerRadius=65)
            .encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Type:N", scale=alt.Scale(range=["#16a34a", "#dc2626"]), legend=alt.Legend(title="Type")),
                tooltip=[
                    alt.Tooltip("Type:N"),
                    alt.Tooltip("Count:Q", format=","),
                    alt.Tooltip("Count:Q", title="% of Total", format=".1%")
                ]
            )
            .properties(height=280)
        )
        st.altair_chart(pie_chart, use_container_width=True)

    with col2:
        st.subheader("Order Frequency Distribution")
        freq_bins = pd.cut(
            cust_summary["Orders"],
            bins=[0, 1, 2, 5, 10, 50, 1000],
            labels=["1 Order", "2 Orders", "3-5 Orders", "6-10 Orders", "11-50 Orders", "50+ Orders"]
        ).value_counts().reset_index()
        freq_bins.columns = ["Order_Bucket", "Customer_Count"]

        freq_chart = (
            alt.Chart(freq_bins)
            .mark_bar(color="#4f46e5", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("Order_Bucket:N", sort=None, title="Lifetime Orders"),
                y=alt.Y("Customer_Count:Q", title="Number of Accounts"),
                tooltip=[
                    alt.Tooltip("Order_Bucket:N", title="Frequency Range"),
                    alt.Tooltip("Customer_Count:Q", format=",", title="Customers")
                ]
            )
            .properties(height=280)
        )
        st.altair_chart(freq_chart, use_container_width=True)

    # --- Top 10 High Value Customers ---
    st.subheader("Top 10 High-Value Client Accounts")
    top_cust = cust_summary.sort_values("Total_Spend", ascending=False).head(10)
    st.dataframe(
        top_cust.style.format({
            "Total_Spend": "£{:,.2f}",
            "Orders": "{:,}",
            "Units_Purchased": "{:,}",
            "AOV": "£{:,.2f}"
        }),
        hide_index=True,
        use_container_width=True
    )

    # --- Customer Search ---
    st.subheader("Customer Account Lookup")
    cust_search = st.text_input("🔍 Search customer by Customer ID:", "")
    if cust_search:
        matches = cust_summary[cust_summary["CustomerID"].str.contains(cust_search.strip(), na=False)]
        st.dataframe(
            matches.style.format({
                "Total_Spend": "£{:,.2f}",
                "Orders": "{:,}",
                "Units_Purchased": "{:,}",
                "AOV": "£{:,.2f}"
            }),
            hide_index=True,
            use_container_width=True
        )

    # --- CSV Export ---
    csv_bytes = cust_summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Customer Purchasing Ledger (CSV)",
        data=csv_bytes,
        file_name="customer_purchasing_summary.csv",
        mime="text/csv"
    )
