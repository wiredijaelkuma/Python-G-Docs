# app.py - Main application file
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
import os

# Import modules
from modules.utils import load_css, load_csv_data, format_large_number
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
    
    # --- File Uploader in Sidebar for Data Source ---
    with st.sidebar:
        # Display the Pepe muscle icon
        try:
            st.image(os.path.join(ASSETS_DIR, "pepe-muscle.jpg"), width=180)
        except:
            st.title("🐸 Pepe's Power")
        
        # Add refresh data button with improved functionality
        if st.button("🔄 Refresh Data", key="refresh_button", use_container_width=True):
            st.cache_data.clear()
            st.sidebar.success("✅ Data refreshed successfully!")
            st.rerun()
        
        # Data source selection
        st.header("Data Source")
        data_source = st.radio(
            "Select data source:",
            ["Local CSV", "Google Sheet"],
            index=0,
            key="data_source"
        )
        
        if data_source == "Local CSV":
            uploaded_file = st.file_uploader("Upload processed data CSV", type=["csv"])
            if uploaded_file is not None:
                st.session_state['uploaded_file'] = uploaded_file
                st.success("✅ File uploaded successfully!")
        else:  # Google Sheet
            # Using default Google Sheet "Forth Py" with existing credentials.json
            st.info("Using Google Sheet: 'Forth Py'")
            st.session_state['spreadsheet_name'] = "Forth Py"
            st.session_state['credentials_file'] = "credentials.json"

    # --- Banner ---
    try:
        st.image(os.path.join(ASSETS_DIR, "banner.png"), use_container_width=True)
    except:
        st.title("Pepe's Power Dashboard")

    # --- Data Loading ---
    with st.spinner("🔍 Loading data..."):
        # Determine data source and load accordingly
        data_source = st.session_state.get('data_source', "Local CSV")
        
        if data_source == "Google Sheet":
            # Load from Google Sheets
            st.info("Fetching data from Google Sheet: 'Forth Py'")
            
            try:
                # Check if we have access to secrets
                if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                    st.success("Found Google credentials in Streamlit secrets")
                else:
                    st.warning("No Google credentials found in Streamlit secrets, will try local file")
                    
                df, load_err = fetch_data_from_sheet()
                
                if not load_err and not df.empty:
                    st.success(f"Successfully loaded {len(df)} records from Google Sheets")
                    
                    # Save to processed_combined_data.csv for backup/offline use
                    try:
                        df.to_csv("processed_combined_data.csv", index=False)
                    except Exception as e:
                        st.sidebar.warning(f"Could not save backup: {e}")
            except Exception as e:
                st.error(f"Error connecting to Google Sheets: {e}")
                load_err = str(e)
        else:
            # Try to load from uploaded file first, then fall back to default file
            if 'uploaded_file' in st.session_state:
                df = pd.read_csv(st.session_state['uploaded_file'])
                load_err = None
            else:
                df, load_err = load_csv_data("processed_combined_data.csv")
        
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

    # --- Sidebar Controls ---
    with st.sidebar:
        st.markdown("<div class='section-header'>Dashboard Controls</div>", unsafe_allow_html=True)
        
        # Date Range Selector
        st.subheader("Date Range")
        today = datetime.now().date()
        
        # Get safe date range using data processor
        from modules.data_processor import safe_date_range
        min_date, max_date = safe_date_range(df)
        max_date = max(max_date, today)
            
        # Ensure default start date is within valid range
        default_start = max(min_date, max_date - timedelta(days=30))
        
        start = st.date_input("Start Date", default_start, min_value=min_date, max_value=max_date)
        end = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
        
        # Status Filter
        st.subheader("Status Filter")
        show_active = st.checkbox("Active", True)
        show_nsf = st.checkbox("NSF", True)
        show_cancelled = st.checkbox("Cancelled", True)
        show_other = st.checkbox("Other Statuses", True)
        
        # Source Filter - only if SOURCE_SHEET exists
        if 'SOURCE_SHEET' in df.columns:
            st.subheader("Data Source")
            all_sources = st.checkbox("All Sources", True)
            if not all_sources:
                sources = st.multiselect("Select sources:", df['SOURCE_SHEET'].unique())
            else:
                sources = df['SOURCE_SHEET'].unique().tolist()
        else:
            all_sources = True
            sources = []

    # --- Apply Filters ---
    # Create a copy of the index for filtering
    mask = pd.Series(True, index=df.index)
    
    # Apply date filter - only if ENROLLED_DATE exists
    date_col = None
    if 'ENROLLED_DATE' in df.columns:
        date_col = 'ENROLLED_DATE'
    elif 'ENROLLED DATE' in df.columns:
        date_col = 'ENROLLED DATE'
        
    if date_col:
        mask &= df[date_col].notna() & (df[date_col].dt.date >= start) & (df[date_col].dt.date <= end)
    
    # Apply status filter using data processor
    from modules.data_processor import get_status_filter_mask
    status_mask = get_status_filter_mask(df, show_active, show_nsf, show_cancelled, show_other)
    mask &= status_mask
    
    # Create status_filter list for header function
    status_filter = []
    if show_active: status_filter.append('ACTIVE')
    if show_nsf: status_filter.append('NSF')
    if show_cancelled: status_filter.append('CANCELLED')
    if show_other: status_filter.append('OTHER')
    
    # Apply source filter - only if SOURCE_SHEET exists and sources are selected
    if 'SOURCE_SHEET' in df.columns and not all_sources and sources:
        mask &= df['SOURCE_SHEET'].isin(sources)
        
    # Apply all filters at once
    df_filtered = df[mask]

    # --- Dashboard Header ---
    create_header(df_filtered, start, end, status_filter, COLORS)

    # --- Metrics Summary ---
    display_metrics(df_filtered, COLORS)

    # --- Tab Navigation ---
    tabs = st.tabs([
        "Home", "Weekly Analysis", "Monthly Analysis", "Performance", "Data Explorer", "Commission"
    ])
    
    # Home/Landing Page Tab
    with tabs[0]:
        try:
            render_landing_page(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Landing Page: {e}")
            import traceback
            st.exception(traceback.format_exc())
            fallback_landing_page(df_filtered, COLORS)
    
    # Weekly Analysis Tab
    with tabs[1]:
        try:
            from modules.tabs.weekly_analysis import render_weekly_analysis_tab
            render_weekly_analysis_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Weekly Analysis tab: {e}")
            st.info("The Weekly Analysis tab provides week-over-week performance comparisons.")
    
    # Monthly Analysis Tab
    with tabs[2]:
        try:
            render_monthly_analysis_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Monthly Analysis tab: {e}")
            import traceback
            st.exception(traceback.format_exc())
            
            # Provide a simple fallback monthly analysis
            st.subheader("Monthly Analysis (Fallback View)")
            if 'ENROLLED_DATE' in df_filtered.columns:
                try:
                    # Convert to string to avoid type comparison issues
                    df_filtered['Year_Month'] = df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m')
                    
                    # Group by month
                    monthly_counts = df_filtered.groupby('Year_Month').size().reset_index()
                    monthly_counts.columns = ['Month', 'Count']
                    
                    # Sort by month
                    monthly_counts = monthly_counts.sort_values('Month')
                    
                    # Create simple bar chart
                    import plotly.express as px
                    fig = px.bar(
                        monthly_counts,
                        x='Month',
                        y='Count',
                        title='Monthly Enrollment Count',
                        color_discrete_sequence=[COLORS['primary']]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as fallback_error:
                    st.error(f"Could not create fallback view: {fallback_error}")
                    st.info("The Monthly Analysis tab provides detailed metrics and trends by month.")
            else:
                st.info("The Monthly Analysis tab provides detailed metrics and trends by month.")
    
    # Performance Tab
    with tabs[3]:
        try:
            render_performance_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Performance tab: {e}")
            fallback_performance(df_filtered, COLORS)
        
    # Data Explorer Tab
    with tabs[4]:
        try:
            render_data_explorer(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Data Explorer tab: {e}")
            fallback_data_explorer(df_filtered)
            
    # Commission Tab
    with tabs[5]:
        try:
            render_commission_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Commission tab: {e}")
            st.info("The Commission tab displays agent performance metrics and payment trends.")

def fallback_landing_page(df_filtered, COLORS):
    import plotly.express as px
    
    st.subheader("Weekly Performance Summary")
    if 'ENROLLED_DATE' in df_filtered.columns and not df_filtered.empty:
        # Get the most recent week's data
        today = datetime.now()
        one_week_ago = today - timedelta(days=7)
        
        recent_df = df_filtered[df_filtered['ENROLLED_DATE'] >= one_week_ago]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("New Enrollments (Last 7 Days)", len(recent_df))
            
        with col2:
            if 'CATEGORY' in recent_df.columns and len(recent_df) > 0:
                active_count = len(recent_df[recent_df['CATEGORY'].str.upper() == 'ACTIVE'])
                active_rate = (active_count / len(recent_df) * 100) if len(recent_df) > 0 else 0
                st.metric("Active Rate", f"{active_rate:.1f}%")
        
        # Simple table of recent enrollments
        if not recent_df.empty:
            # Determine which columns to show
            display_columns = []
            for col in ['ENROLLED_DATE', 'CUSTOMER_NAME', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY', 'AMOUNT']:
                if col in recent_df.columns:
                    display_columns.append(col)
            
            if display_columns:
                table_df = recent_df[display_columns].copy()
                
                # Format date columns
                if 'ENROLLED_DATE' in table_df.columns:
                    table_df['ENROLLED_DATE'] = table_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
                
                st.dataframe(table_df.head(10), use_container_width=True, hide_index=True)
            else:
                st.info("No data columns available to display")
        else:
            st.info("No recent enrollments to display")
    else:
        st.warning("Enrollment date data not available or no data matches the current filters")

def fallback_performance(df_filtered, COLORS):
    import plotly.express as px
    
    st.subheader("Monthly Enrollments")
    if 'ENROLLED_DATE' in df_filtered.columns:
        monthly_data = df_filtered.groupby(df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
        monthly_data.columns = ['Month', 'Count']
        
        fig = px.bar(
            monthly_data,
            x='Month',
            y='Count',
            title='Monthly Enrollment Count',
            color_discrete_sequence=[COLORS['primary']]
        )
        st.plotly_chart(fig, use_container_width=True)

def fallback_data_explorer(df_filtered):
    st.subheader("Data Explorer")
    st.dataframe(df_filtered.head(100), use_container_width=True)

if __name__ == "__main__":
    main()