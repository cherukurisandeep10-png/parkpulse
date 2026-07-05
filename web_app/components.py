# Author: Sandeep Chowdary
# Project: ParkPulse Telemetry Engine
# Description: Custom CSS and UI helper components for Streamlit dashboard.

import streamlit as st


def apply_custom_styles():
    st.markdown("""
        <style>
        .metric-card {
            background-color: #1E1E2E;
            padding: 1.2rem;
            border-radius: 8px;
            border-left: 4px solid #00F0FF;
            color: #FFFFFF;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .metric-title {
            font-size: 0.85rem;
            color: #A6ADC8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.3rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #FFFFFF;
        }
        .status-parked {
            background-color: #E63946;
            color: #FFFFFF;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
        }
        .status-driving {
            background-color: #2A9D8F;
            color: #FFFFFF;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
        }
        .vehicle-details-box {
            background: #181825;
            border: 1px solid #313244;
            border-radius: 8px;
            padding: 1.2rem;
            color: #cdd6f4;
            margin-top: 0.8rem;
            margin-bottom: 1.2rem;
        }
        </style>
    """, unsafe_allow_html=True)


def render_metric_card(title, value, subtitle=""):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div style="font-size: 0.8rem; color: #89DCEB; margin-top: 0.3rem;">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)
