"""
Retail Sales & Customer Analytics Platform
Main Streamlit Application Entrypoint
"""

import streamlit as st
import datetime
from dashboard.styles import apply_custom_styles
from dashboard.data_access import load_sales_data, load_rfm_data, filter_sales_data
from dashboard.pages import (
    p1_overview,
    p2_sales,
    p3_products,
    p4_customers,
    p5_rfm,
    p6_insights
)

# 1. Page Configuration
st.set_page_config(
    page_title="Retail Sales & Customer Analytics Platform",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS Theme
apply_custom_styles()


def main():
    # 3. Data Loading with Graceful Error Handling
    try:
        df_sales = load_sales_data()
        df_rfm = load_rfm_data()
    except Exception as e:
        st.error(f"❌ Error loading analytics data: {e}")
        st.info("Ensure you have executed the data cleaning and segmentation pipelines first:\n"
                "1. `python -m src.data_cleaner`\n"
                "2. `python -m src.segmentation`")
        return

    # 4. Sidebar Controls & Global Filters
    st.sidebar.title("🛍️ Retail Analytics")
    st.sidebar.caption("Executive Decision-Support Platform")
    st.sidebar.markdown("---")

    # Navigation Menu
    pages = {
        "📊 Executive Overview": p1_overview.render,
        "📈 Sales Analytics": p2_sales.render,
        "📦 Product Performance": p3_products.render,
        "👥 Customer Analytics": p4_customers.render,
        "🎯 RFM Customer Segmentation": p5_rfm.render,
        "💡 Business Insights": p6_insights.render
    }

    selected_page_name = st.sidebar.radio("Navigate View", list(pages.keys()))
    st.sidebar.markdown("---")

    # Global Interactive Filters
    st.sidebar.subheader("🔍 Global Filters")

    min_date = df_sales["Date"].min()
    max_date = df_sales["Date"].max()

    date_range = st.sidebar.date_input(
        "Transaction Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    elif isinstance(date_range, tuple) and len(date_range) == 1:
        start_date = date_range[0]
        end_date = max_date
    else:
        start_date, end_date = min_date, max_date

    # Country Filter
    all_countries = sorted(df_sales["Country"].unique().tolist())
    # Default to top 5 countries or all
    selected_countries = st.sidebar.multiselect(
        "Country Filter (Empty = All)",
        options=all_countries,
        default=[]
    )

    # Category Filter
    all_categories = sorted(df_sales["Category"].unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Product Category (Empty = All)",
        options=all_categories,
        default=[]
    )

    # Filter transactions
    df_filtered = filter_sales_data(
        df_sales,
        start_date=start_date,
        end_date=end_date,
        selected_countries=selected_countries if selected_countries else None,
        selected_categories=selected_categories if selected_categories else None
    )

    # Sidebar Data Status Widget
    st.sidebar.markdown("---")
    st.sidebar.caption("System Health & Data Lineage")
    st.sidebar.caption(f"• Ingested Records: **{len(df_sales):,}**")
    st.sidebar.caption(f"• Filtered Records: **{len(df_filtered):,}**")
    st.sidebar.caption("• Database: **SQLite 3 (Active)**")
    st.sidebar.caption("• RFM Model: **K-Means (k=4)**")

    # 5. Route to Selected Page
    page_fn = pages[selected_page_name]
    if selected_page_name in ["📊 Executive Overview", "👥 Customer Analytics", "💡 Business Insights"]:
        page_fn(df_filtered, df_rfm)
    elif selected_page_name in ["📈 Sales Analytics", "📦 Product Performance"]:
        page_fn(df_filtered)
    elif selected_page_name == "🎯 RFM Customer Segmentation":
        page_fn(df_rfm)


if __name__ == "__main__":
    main()
