# app.py - Main application file
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
import os

# Import modules
from modules.utils import load_css, format_large_number
from modules.ui_components import display_metrics, create_header
from modules.tabs.landing_page import render_landing_page
from modules.tabs.overview import render_overview_tab
from modules.tabs.performance import render_performance_tab
from modules.tabs.data_explorer import render_data_explorer
from modules.tabs.commission import render_commission_tab
from modules.tabs.monthly_analysis import render_monthly_analysis_tab
from modules.gsheet_connector import fetch_data_from_sheet

# --- Set page configuration first (must be the first Streamlit command) ---
st.set_page_config(
    layout="wide", 
    page_title="Pepe's Power Dashboard",
    page_icon="🐸",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed to maximize chart space
)

# --- Constants ---
# Simplified asset paths
ASSETS_DIR = Path("assets")

# --- Color Palette ---
# Periwinkle purples and opaque greens
COLORS = {
    'primary': '#8A7FBA',      # Periwinkle purple
    'secondary': '#6A5ACD',    # Slateblue
    'accent': '#7FFFD4',       # Aquamarine
    'light_accent': '#AFFFEE', # Light aquamarine
    'dark_accent': '#40E0D0',  # Turquoise
    'warning': '#FFD700',      # Gold
    'danger': '#FF6347',       # Tomato
    'light': '#F0F8FF',        # Alice blue
    'dark': '#483D8B',         # Dark slate blue
    'background': '#F8F9FA',   # Light gray background
    'text': '#2E2E2E',         # Near black
    'light_purple': '#E6E6FA', # Lavender
    'med_purple': '#B39DDB',   # Medium purple
    'light_green': '#98FB98',  # Pale green
    'med_green': '#66CDAA',    # Medium aquamarine
}

def main():
    # Load CSS
    load_css()
    
    # --- Simplified Sidebar ---
    with st.sidebar:
        try:
            st.image(os.path.join(ASSETS_DIR, "pepe-muscle.jpg"), width=180)
        except:
            st.title("🐸 Pepe's Power")
        
        if st.button("🔄 Refresh Data", key="refresh_button", use_container_width=True):
            st.cache_data.clear()
            st.sidebar.success("✅ Data refreshed successfully!")
            st.rerun()
        
        st.header("Data Source")
        st.markdown("**Google Sheet:** [Forth Py](https://docs.google.com/spreadsheets)")

    # --- Banner ---
    try:
        st.image(os.path.join(ASSETS_DIR, "banner.png"), use_container_width=True)
    except:
        st.title("Pepe's Power Dashboard")

    # --- Data Loading ---
    with st.spinner("🔍 Loading data..."):
        # Load from Google Sheets
        st.info("Fetching data from Google Sheet: 'Forth Py'")
        
        try:
            df, load_err = fetch_data_from_sheet()
            
            if not load_err and not df.empty:
                st.success(f"Successfully loaded {len(df)} records from Google Sheets")
                
                # Save to processed_combined_data.csv for backup/offline use
                try:
                    df.to_csv("processed_combined_data.csv", index=False)
                except Exception:
                    pass  # Silently ignore backup errors
        except Exception as e:
            st.error(f"Error connecting to Google Sheets: {e}")
            load_err = str(e)
        
        # Fix duplicate column names
        if load_err is None and not df.empty:
            # Remove duplicate columns
            df = df.loc[:, ~df.columns.duplicated()]
            
            # Convert date columns to datetime
            date_col = None
            if 'ENROLLED_DATE' in df.columns:
                date_col = 'ENROLLED_DATE'
            elif 'ENROLLED DATE' in df.columns:
                date_col = 'ENROLLED DATE'
                
            if date_col:
                try:
                    df[date_col] = pd.to_datetime(df[date_col])
                except:
                    st.warning(f"Could not convert {date_col} to datetime format.")
        
        # Show error details in an expander if there was an error
        if load_err:
            with st.expander("Error Details"):
                st.code(load_err)
        
    if load_err:
        st.error(f"🚨 Data Load Error: {load_err}")
        st.stop()
        
    if df.empty:
        st.warning("⚠️ No data available. Please upload a CSV file with your data.")
        st.stop()

    # Normalize data using centralized processor
    from modules.data_processor import normalize_dataframe
    df = normalize_dataframe(df)
    
    # Store data in session state
    st.session_state['df'] = df
    
    # Update sidebar with record count
    with st.sidebar:
        st.info(f"Total Records: {len(df)}")
        if 'SOURCE_SHEET' in df.columns:
            st.write("**Data Sources:**")
            for source in df['SOURCE_SHEET'].unique():
                count = len(df[df['SOURCE_SHEET'] == source])
                st.write(f"• {source}: {count} records")





    # --- Dashboard Header ---
    st.title("Pepe's Power Dashboard")
    st.markdown(f"**Total Records:** {len(df)} | **Data Sources:** {', '.join(df['SOURCE_SHEET'].unique()) if 'SOURCE_SHEET' in df.columns else 'N/A'}")

    # --- Metrics Summary ---
    display_metrics(df, COLORS)

    # --- Tab Navigation ---
    tabs = st.tabs([
        "Home", "Weekly Analysis", "Monthly Analysis", "Performance", "Data Explorer", "Commission"
    ])
    
    # Home/Landing Page Tab
    with tabs[0]:
        try:
            render_landing_page(df, COLORS)
        except Exception as e:
            st.error(f"Error rendering Landing Page: {e}")
            fallback_landing_page(df, COLORS)
    
    # Weekly Analysis Tab
    with tabs[1]:
        try:
            from modules.tabs.weekly_analysis import render_weekly_analysis_tab
            render_weekly_analysis_tab(df, COLORS)
        except Exception as e:
            st.error(f"Error rendering Weekly Analysis tab: {e}")
            st.info("The Weekly Analysis tab provides week-over-week performance comparisons.")
    
    # Monthly Analysis Tab
    with tabs[2]:
        try:
            render_monthly_analysis_tab(df, COLORS)
        except Exception as e:
            st.error(f"Error rendering Monthly Analysis tab: {e}")
            fallback_monthly_analysis(df, COLORS)
    
    # Performance Tab
    with tabs[3]:
        try:
            render_performance_tab(df, COLORS)
        except Exception as e:
            st.error(f"Error rendering Performance tab: {e}")
            fallback_performance(df, COLORS)
        
    # Data Explorer Tab
    with tabs[4]:
        try:
            render_data_explorer(df, COLORS)
        except Exception as e:
            st.error(f"Error rendering Data Explorer tab: {e}")
            fallback_data_explorer(df)
            
    # Commission Tab
    with tabs[5]:
        try:
            render_commission_tab(df, COLORS)
        except Exception as e:
            st.error(f"Error rendering Commission tab: {e}")
            st.info("The Commission tab displays agent performance metrics and payment trends.")

def fallback_landing_page(df, COLORS):
    st.subheader("Data Overview")
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            if 'SOURCE_SHEET' in df.columns:
                st.metric("Data Sources", df['SOURCE_SHEET'].nunique())
        with col3:
            if 'CATEGORY' in df.columns:
                active_count = len(df[df['CATEGORY'] == 'ACTIVE'])
                st.metric("Active Records", active_count)
    else:
        st.warning("No data available")

def fallback_performance(df, COLORS):
    st.subheader("Performance Overview")
    if 'SOURCE_SHEET' in df.columns:
        source_counts = df['SOURCE_SHEET'].value_counts()
        st.bar_chart(source_counts)

def fallback_data_explorer(df):
    st.subheader("Data Explorer")
    st.dataframe(df.head(100), use_container_width=True)

def fallback_monthly_analysis(df, COLORS):
    st.subheader("Monthly Analysis")
    if 'ENROLLED_DATE' in df.columns:
        monthly_data = df.groupby(df['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
        monthly_data.columns = ['Month', 'Count']
        st.bar_chart(monthly_data.set_index('Month'))
    else:
        st.info("No date data available for monthly analysis")

if __name__ == "__main__":
    main()