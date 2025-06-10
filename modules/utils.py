# modules/utils.py
import streamlit as st
import pandas as pd

@st.cache_data(ttl=3600)
def load_csv_data(file_path="processed_combined_data.csv"):
    """Load data with minimal processing for speed"""
    try:
        # Simple CSV reading without complex options
        df = pd.read_csv(file_path)
        
        # Standardize column names
        df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]
        
        # Only process essential columns
        if 'ENROLLED_DATE' in df.columns:
            df['ENROLLED_DATE'] = pd.to_datetime(df['ENROLLED_DATE'], errors='coerce')
            df['MONTH_YEAR'] = df['ENROLLED_DATE'].dt.strftime('%Y-%m')
        
        if 'STATUS' in df.columns:
            # Simplified status categorization
            df['CATEGORY'] = 'OTHER'
            df.loc[df['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            df.loc[df['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            df.loc[df['STATUS'].str.contains('CANCEL|DROP|TERMIN|PENDING', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
        
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

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
        </style>
        """, unsafe_allow_html=True)