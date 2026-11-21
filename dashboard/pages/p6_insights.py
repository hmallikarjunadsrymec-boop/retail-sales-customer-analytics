"""
Page 6: Business Insights & Strategic Recommendations
Evidence-based commercial roadmap, churn mitigation, inventory prioritization, and AOV expansion.
"""

import os
import streamlit as st
import pandas as pd


def render(df_filtered: pd.DataFrame, df_rfm: pd.DataFrame):
    st.markdown("## 💡 Business Insights & Strategic Action Plan")
    st.caption("Commercial recommendations derived directly from calculated transactional and behavioral data.")

    # Strategic Q&A Grid
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. Product Focus",
        "2. Retention & Churn",
        "3. Seasonality & Timing",
        "4. High-Value Cohorts",
        "5. AOV Expansion Levers"
    ])

    with tab1:
        st.subheader("Which products should receive more attention?")
        st.markdown("""
        <div class="insight-callout">
            <strong>Key Finding:</strong> Extreme revenue concentration exists in hero decorative SKUs.
            <strong>'REGENCY CAKESTAND 3 TIER' (SKU: 22423)</strong> generated <strong>£174,156.54</strong> across 1,972 orders, while 
            <strong>'WHITE HANGING HEART T-LIGHT HOLDER' (SKU: 85123A)</strong> generated <strong>£106,236.72</strong>.
            The highest velocity item by unit volume is <strong>'JUMBO BAG RED RETROSPOT' (SKU: 85099B)</strong> with <strong>47,363 units sold</strong>.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Actionable Recommendations:**
        1. **Automated Safety-Stock Alerts:** Establish an ERP safety reorder threshold for the Top 10 revenue-generating SKUs. Preventing stockouts on SKU `22423` alone protects over £14,000/month in top-line revenue.
        2. **Merchandising Bundles:** Bundle the high-volume `85099B` (Jumbo Bag) with slower-moving storage lines to liquidate aging inventory while increasing order basket values.
        3. **Wholesale Tier Pricing:** Provide volume-tiered discounts on top SKUs (e.g., 5% off for 50+ units, 10% off for 100+ units) to incentivize wholesale pre-orders.
        """)

    with tab2:
        st.subheader("Which customers need retention campaigns?")
        st.markdown("""
        <div class="warning-callout">
            <strong>Churn Risk Warning:</strong> <strong>656 high-value accounts</strong> in the <strong>'Can\'t Lose Them' (175 accounts)</strong> 
            and <strong>'At Risk' (481 accounts)</strong> segments previously contributed <strong>£810,231.02</strong> in cumulative revenue, 
            but have not placed an order in over 180 days.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Actionable Recommendations:**
        1. **Direct Account Manager Outreach:** Assign the top 50 accounts in 'Can\'t Lose Them' to dedicated account managers for personalized telephone and high-touch contact.
        2. **Bespoke VIP Re-activation Offer:** Deliver a targeted incentive (e.g. £100 credit on orders exceeding £750) rather than generic mass newsletters.
        3. **Automated 90-Day Churn Triggers:** Configure CRM alerts when an active customer exceeds 1.5x their historical purchase cadence without re-ordering.
        """)

    with tab3:
        st.subheader("Which months perform best?")
        st.markdown("""
        <div class="insight-callout">
            <strong>Seasonal Peak:</strong> <strong>November 2011 (`2011-11`)</strong> is the undisputed peak month, generating 
            <strong>£1,453,265.98</strong> across 2,751 orders (+41.2% MoM growth), followed by <strong>October 2011 (£1,104,030.92)</strong> 
            and <strong>September 2011 (£1,029,245.38)</strong>.
            The lowest volume occurs in <strong>February (£508k)</strong> and <strong>April (£515k)</strong>.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Actionable Recommendations:**
        1. **Supply Chain Lead-Time Alignment:** Bulk inventory procurement must be finalized and docked at distribution centers by August 15th to support the September-November wholesale ramp.
        2. **Warehouse Peak Staffing:** Shift temporary logistics labor resources into October-November to prevent fulfillment bottlenecks.
        3. **Q1 Counter-Cyclical Campaigns:** Launch Spring preview promotions in late January to stimulate demand during the historical February slump.
        """)

    with tab4:
        st.subheader("Which customer groups generate the most revenue?")
        st.markdown("""
        <div class="insight-callout">
            <strong>Pareto Revenue Concentration:</strong> The <strong>'Champions' segment (1,119 customers | 25.8% of base)</strong> 
            generates <strong>£5,778,845.26</strong> — representing <strong>65.0% of all customer spend</strong>! 
            Combined with 'Loyal Customers' (£1.17M), just 44.8% of customers account for 78.2% of total revenue.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Actionable Recommendations:**
        1. **Formalize 'Regency Tier' VIP Club:** Guarantee VIP Champions first access to new seasonal collections, dedicated freight rates, and 30-day payment terms.
        2. **Channel Reallocation:** Reallocate 25% of generic top-of-funnel customer acquisition budget into retention and loyalty incentives for Potential Loyalists (£139.6k) to fast-track their progression to Champions.
        """)

    with tab5:
        st.subheader("What opportunities exist to increase Average Order Value (AOV)?")
        st.markdown("""
        <div class="insight-callout">
            <strong>AOV Dynamics:</strong> While the arithmetic mean AOV is <strong>£506.19</strong>, the median order is 
            <strong>£232.00</strong>. This shows a high volume of small orders pulling down operational efficiency.
            Peak ordering hours are <strong>11:00 AM – 3:00 PM Tuesday through Thursday</strong>.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Actionable Recommendations:**
        1. **Tiered Free Shipping Thresholds:** Establish freight-free eligibility at £350 (pulling median £232 orders upward) and £600 for premium expedited delivery.
        2. **Checkout Cross-Sell Carousels:** Introduce 'Frequently Bought Together' recommendation widgets at the cart stage for complementary Home Decor and Kitchen lines.
        3. **Optimized Restock Email Timing:** Dispatch wholesale restocking emails and catalog updates at 10:30 AM on Tuesdays and Thursdays to coincide with confirmed buyer checkouts.
        """)

    st.markdown("<hr style='margin: 25px 0;'>", unsafe_allow_html=True)

    # Download Business Recommendations Report
    rec_path = os.path.join("reports", "BUSINESS_RECOMMENDATIONS.md")
    if os.path.exists(rec_path):
        with open(rec_path, "r", encoding="utf-8") as f:
            report_content = f.read()
        st.download_button(
            label="📄 Download Full Business Recommendations Report (Markdown)",
            data=report_content.encode("utf-8"),
            file_name="BUSINESS_RECOMMENDATIONS.md",
            mime="text/markdown"
        )
