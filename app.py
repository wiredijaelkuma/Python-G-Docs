import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import base64
from io import BytesIO
import calendar
from pathlib import Path

# Import optimized data loader
from sheet_loader import load_csv_data

# Import modular components
from data_explorer import render_data_explorer
from risk_analysis import render_risk_analysis
from performance_tab import render_performance_tab
from agents_tab import render_agents_tab
from overview_tab import render_overview_tab
from streamlit_config import configure_page

# --- Set page configuration first (must be the first Streamlit command) ---
configure_page()

# --- Constants ---
# Simplified asset paths
ASSETS_DIR = Path("assets")

# --- Color Palette ---
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

# Load custom CSS
try:
    with open('assets/custom.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass

# --- Helper Functions ---
# Data loading moved to sheet_loader.py

def format_large_number(num):
    """Format large numbers with commas"""
    return f"{num:,}"

# --- Main App Logic ---
def main():
    # --- File Uploader in Sidebar for Data Source ---
    with st.sidebar:
        # Display the Pepe muscle icon
        try:
            st.image("assets/pepe-muscle.jpg", width=180)
        except:
            st.title("🐸 Pepe's Power")
        
        # Add refresh data button with improved functionality
        if st.button("🔄 Refresh Data", key="refresh_button", use_container_width=True):
            st.cache_data.clear()
            st.sidebar.success("✅ Data refreshed successfully!")
            st.rerun()
        
        # Data source section - only show this if no data is loaded yet
        if 'df' not in st.session_state:
            st.header("Data Source")
            uploaded_file = st.file_uploader("Upload processed data CSV", type=["csv"])
            if uploaded_file is not None:
                st.session_state['uploaded_file'] = uploaded_file
                st.success("✅ File uploaded successfully!")

    # --- Banner ---
    try:
        st.image("assets/banner.png", use_column_width=True)
    except:
        st.title("Pepe's Power Dashboard")

    # --- Data Loading ---
    with st.spinner("🔍 Loading data..."):
        df, load_err = load_csv_data("processed_combined_data.csv")
        
    if load_err:
        st.error(f"🚨 Data Load Error: {load_err}")
        st.stop()
        
    if df.empty:
        st.warning("⚠️ No data available. Please upload a CSV file with your data.")
        st.stop()

    # Store data in session state
    st.session_state['df'] = df

    # --- Sidebar Controls ---
    with st.sidebar:
        st.markdown("<div class='section-header'>Dashboard Controls</div>", unsafe_allow_html=True)
        
        # Date Range Selector
        st.subheader("Date Range")
        today = datetime.now().date()
        
        # Handle case where ENROLLED_DATE might not exist or have valid dates
        if 'ENROLLED_DATE' in df.columns and not df['ENROLLED_DATE'].isna().all():
            min_date = df['ENROLLED_DATE'].min().date()
            max_date = max(df['ENROLLED_DATE'].max().date(), today)
        else:
            min_date = date(2024, 10, 1)
            max_date = today
            
        start = st.date_input("Start Date", max_date - timedelta(days=30), min_value=min_date, max_value=max_date)
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
    if 'ENROLLED_DATE' in df.columns:
        mask &= df['ENROLLED_DATE'].notna() & (df['ENROLLED_DATE'].dt.date >= start) & (df['ENROLLED_DATE'].dt.date <= end)
    
    # Apply status filter - only if CATEGORY exists
    status_filter = []
    if show_active: status_filter.append('ACTIVE')
    if show_nsf: status_filter.append('NSF')
    if show_cancelled: status_filter.append('CANCELLED')
    if show_other: status_filter.append('OTHER')
    
    if 'CATEGORY' in df.columns and status_filter:
        mask &= df['CATEGORY'].isin(status_filter)
    
    # Apply source filter - only if SOURCE_SHEET exists and sources are selected
    if 'SOURCE_SHEET' in df.columns and not all_sources and sources:
        mask &= df['SOURCE_SHEET'].isin(sources)
        
    # Apply all filters at once
    df_filtered = df[mask]

    # --- Dashboard Header ---
    st.markdown(f"""
    <div class="section-header">Pepe's Power Sales Dashboard</div>
    <div style="background-color: {COLORS['light_purple']}; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
            <div>
                <b>Date Range:</b> {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}<br>
                <b>Total Contracts:</b> {format_large_number(len(df_filtered))}
            </div>
            <div>
                <b>Status Shown:</b> {', '.join(status_filter)}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Metrics Summary ---
    # Calculate metrics based on filtered data
    total_contracts = len(df_filtered)
    
    # Only calculate these if CATEGORY exists
    if 'CATEGORY' in df_filtered.columns:
        active_contracts = len(df_filtered[df_filtered['CATEGORY'] == 'ACTIVE'])
        nsf_cases = len(df_filtered[df_filtered['CATEGORY'] == 'NSF'])
        cancelled_contracts = len(df_filtered[df_filtered['CATEGORY'] == 'CANCELLED'])
        other_statuses = len(df_filtered[df_filtered['CATEGORY'] == 'OTHER'])
    else:
        active_contracts = nsf_cases = cancelled_contracts = other_statuses = 0
    
    success_rate = (active_contracts / total_contracts * 100) if total_contracts > 0 else 0

    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Contracts</div>
            <div class="metric-value">{format_large_number(total_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid {COLORS['med_green']};">
            <div class="metric-title">Active Contracts</div>
            <div class="metric-value" style="color: {COLORS['med_green']};">{format_large_number(active_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid {COLORS['warning']};">
            <div class="metric-title">NSF Cases</div>
            <div class="metric-value" style="color: {COLORS['warning']};">{format_large_number(nsf_cases)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid {COLORS['danger']};">
            <div class="metric-title">Cancelled</div>
            <div class="metric-value" style="color: {COLORS['danger']};">{format_large_number(cancelled_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid {COLORS['dark_accent']};">
            <div class="metric-title">Success Rate</div>
            <div class="metric-value" style="color: {COLORS['dark_accent']};">{success_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Tab Interface ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "📈 Performance", 
        "🧑 Agents", 
        "🔍 Data Explorer", 
        "🚨 Risk Analysis"
    ])

    # --- Overview Tab ---
    with tab1:
        try:
            render_overview_tab(df_filtered, COLORS, active_contracts, nsf_cases, cancelled_contracts, total_contracts)
        except Exception as e:
            st.error(f"Error in Overview tab: {e}")

    # --- Performance Tab ---
    with tab2:
        try:
            render_performance_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error in Performance tab: {e}")

    # --- Agents Tab ---
    with tab3:
        try:
            render_agents_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error in Agents tab: {e}")

    # --- Data Explorer Tab ---
    with tab4:
        try:
            render_data_explorer(df_filtered, COLORS, start)
        except Exception as e:
            st.error(f"Error in Data Explorer tab: {e}")

    # --- Risk Analysis Tab ---
    with tab5:
        try:
            render_risk_analysis(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error in Risk Analysis tab: {e}")

    # --- Footer ---
    st.markdown("""
    <div class="footer">
        © 2025 Pepe's Power Solutions | Dashboard v3.0
    </div>
    """, unsafe_allow_html=True)

    # --- Notifications ---
    st.toast("Dashboard loaded successfully!", icon="🐸")

# Run the main function
if __name__ == "__main__":
    main()