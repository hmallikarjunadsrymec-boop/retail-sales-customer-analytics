"""
Dashboard Styling & UI Component Helpers
Provides professional CSS themes, KPI card formatting, and responsive styling for Streamlit.
"""

import streamlit as st


def apply_custom_styles():
    """Injects modern, corporate-grade CSS styling into the Streamlit app."""
    st.markdown("""
        <style>
        /* Modern corporate typography and container layout */
        .main .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
            max-width: 1350px;
        }

        /* KPI Card Styling */
        .kpi-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 18px 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            margin-bottom: 12px;
            transition: transform 0.15s ease-in-out;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            border-color: #cbd5e1;
        }
        .kpi-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 1.85rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.2;
        }
        .kpi-delta {
            font-size: 0.82rem;
            margin-top: 5px;
            font-weight: 500;
        }
        .delta-positive { color: #16a34a; }
        .delta-neutral { color: #64748b; }
        .delta-negative { color: #dc2626; }

        /* Section Headings */
        .section-header {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1e293b;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
            margin-top: 20px;
            margin-bottom: 16px;
        }

        /* Callout Box */
        .insight-callout {
            background-color: #f0fdf4;
            border-left: 4px solid #16a34a;
            padding: 14px 18px;
            border-radius: 4px;
            margin: 12px 0 20px 0;
            font-size: 0.95rem;
            color: #166534;
        }
        .warning-callout {
            background-color: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 14px 18px;
            border-radius: 4px;
            margin: 12px 0 20px 0;
            font-size: 0.95rem;
            color: #92400e;
        }

        /* Clean Table Headers */
        thead th {
            background-color: #f1f5f9 !important;
            color: #334155 !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, subtext: str = "", delta_type: str = "neutral"):
    """Renders a styled KPI metric card."""
    delta_class = f"delta-{delta_type}"
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {f'<div class="kpi-delta {delta_class}">{subtext}</div>' if subtext else ''}
        </div>
    """, unsafe_allow_html=True)
