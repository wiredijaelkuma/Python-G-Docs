# modules/utils.py
import streamlit as st
from datetime import timedelta

def format_large_number(num):
    """Format large numbers with commas"""
    return f"{num:,}"

def load_css():
    """Load custom CSS with error handling"""
    try:
        with open('assets/custom.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception:
        # Add some basic styling if custom CSS is not available
        st.markdown("""
        <style>
        .metric-card {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .metric-title {
            font-size: 14px;
            color: #666;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .section-header {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #483D8B;
        }
        /* Make charts expand properly */
        .stPlotlyChart {
            width: 100% !important;
        }
        /* Fix sidebar issues */
        .main .block-container {
            max-width: 100% !important;
            padding-left: 5% !important;
            padding-right: 5% !important;
        }
        /* Ensure tables display properly */
        .dataframe-container {
            width: 100% !important;
        }
        /* Fix expander to take full width */
        .streamlit-expanderHeader {
            width: 100% !important;
        }
        .streamlit-expanderContent {
            width: 100% !important;
        }
        /* Make sure expander content takes full width */
        .st-expander {
            width: 100% !important;
        }
        .st-expander > div {
            width: 100% !important;
        }
        /* Fix for plotly charts in expanders */
        .st-expander .stPlotlyChart {
            width: 100% !important;
        }
        </style>
        """, unsafe_allow_html=True)