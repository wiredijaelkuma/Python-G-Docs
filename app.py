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

# Import modular components
from data_explorer import render_data_explorer
from risk_analysis import render_risk_analysis
from performance_tab import render_performance_tab
from agents_tab import render_agents_tab
from overview_tab import render_overview_tab

# --- Set page configuration first (must be the first Streamlit command) ---
st.set_page_config(
    layout="wide", 
    page_title="Pepe's Power Dashboard", 
    page_icon="🐸",
    initial_sidebar_state="expanded"
)

# Load custom CSS with beautiful periwinkle gradient styling
try:
    with open('assets/custom.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except Exception as e:
    st.warning(f"Could not load custom CSS: {e}")

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

# --- Helper Functions ---
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load and preprocess data with robust error handling"""
    try:
        # Try to load from the processed file
        try:
            df = pd.read_csv("processed_combined_data.csv")
        except Exception as file_error:
            # If that fails, try to load from uploaded file
            uploaded_file = st.session_state.get('uploaded_file', None)
            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
            else:
                return pd.DataFrame(), "No data file found. Please upload a CSV file."
        
        # Standardize column names
        df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]
        
        # Convert date column
        if 'ENROLLED_DATE' in df.columns:
            df['ENROLLED_DATE'] = pd.to_datetime(df['ENROLLED_DATE'], errors='coerce')
        
        # Clean and standardize status
        if 'STATUS' in df.columns:
            df['STATUS'] = df['STATUS'].astype(str).str.strip().str.upper()
            
            # Create status category with more comprehensive terms
            active_terms = ["ACTIVE", "ENROLLED", "ENROLLED / ACTIVE", "ENROLLED/ACTIVE"]
            nsf_terms = ["NSF", "ENROLLED / NSF PROBLEM", "ENROLLED/NSF", "NSF PROBLEM"]
            cancelled_terms = ["CANCELLED", "DROPPED", "PENDING CANCELLATION", "SUMMONS: PUSH OUT", "NEEDS ROL", "TERMINATED"]
            
            # Use vectorized operations for better performance
            df['CATEGORY'] = 'OTHER'  # default value
            mask_active = df['STATUS'].str.contains('|'.join(active_terms), case=False, regex=True, na=False)
            mask_nsf = df['STATUS'].str.contains('|'.join(nsf_terms), case=False, regex=True, na=False)
            mask_cancelled = df['STATUS'].str.contains('|'.join(cancelled_terms), case=False, regex=True, na=False)
            
            df.loc[mask_active, 'CATEGORY'] = 'ACTIVE'
            df.loc[mask_nsf, 'CATEGORY'] = 'NSF'
            df.loc[mask_cancelled, 'CATEGORY'] = 'CANCELLED'
        
        # Add derived columns for analysis
        if 'ENROLLED_DATE' in df.columns:
            df['MONTH_YEAR'] = df['ENROLLED_DATE'].dt.strftime('%Y-%m')
            df['WEEK'] = df['ENROLLED_DATE'].dt.isocalendar().week
            df['YEAR'] = df['ENROLLED_DATE'].dt.isocalendar().year
            df['WEEK_YEAR'] = df['YEAR'].astype(str) + '-W' + df['WEEK'].astype(str).str.zfill(2)
            df['DAY_OF_WEEK'] = df['ENROLLED_DATE'].dt.day_name()
            
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

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
            # Clear all cached data to ensure fresh load
            st.cache_data.clear()
            # Add a success message
            st.sidebar.success("✅ Data refreshed successfully!")
            # Force reload
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
        df, load_err = load_data()
        
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
        st.markdown(f"""
        <div class="section-header">Dashboard Controls</div>
        """, unsafe_allow_html=True)
        
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
        
        # Source Filter
        st.subheader("Data Source")
        if 'SOURCE_SHEET' in df.columns:
            all_sources = st.checkbox("All Sources", True)
            if not all_sources:
                sources = st.multiselect("Select sources:", df['SOURCE_SHEET'].unique())
            else:
                sources = df['SOURCE_SHEET'].unique().tolist()
        else:
            all_sources = True
            sources = []

    # --- Apply Filters ---
    # Apply date filter
    if 'ENROLLED_DATE' in df.columns:
        # Handle NaT values in date filtering
        valid_dates = df['ENROLLED_DATE'].notna()
        date_filter = (df['ENROLLED_DATE'].dt.date >= start) & (df['ENROLLED_DATE'].dt.date <= end)
        df_filtered = df[valid_dates & date_filter]
    else:
        df_filtered = df

    # Apply status filter
    status_filter = []
    if show_active: status_filter.append('ACTIVE')
    if show_nsf: status_filter.append('NSF')
    if show_cancelled: status_filter.append('CANCELLED')
    if show_other: status_filter.append('OTHER')
    
    # Check if CATEGORY column exists before filtering
    if 'CATEGORY' in df_filtered.columns and len(status_filter) > 0:
        df_filtered = df_filtered[df_filtered['CATEGORY'].isin(status_filter)]

    # Apply source filter
    if 'SOURCE_SHEET' in df_filtered.columns and not all_sources and sources:
        df_filtered = df_filtered[df_filtered['SOURCE_SHEET'].isin(sources)]

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
    # Handle case where CATEGORY column might not exist
    if 'CATEGORY' in df_filtered.columns:
        active_df = df_filtered[df_filtered['CATEGORY'] == 'ACTIVE']
        nsf_df = df_filtered[df_filtered['CATEGORY'] == 'NSF']
        cancelled_df = df_filtered[df_filtered['CATEGORY'] == 'CANCELLED']
        other_df = df_filtered[df_filtered['CATEGORY'] == 'OTHER']
        
        active_contracts = len(active_df)
        nsf_cases = len(nsf_df)
        cancelled_contracts = len(cancelled_df)
        other_statuses = len(other_df)
    else:
        active_contracts = 0
        nsf_cases = 0
        cancelled_contracts = 0
        other_statuses = 0

    total_contracts = len(df_filtered)
    success_rate = (active_contracts / total_contracts * 100) if total_contracts > 0 else 0

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
    st.markdown(f"""
    <div class="footer">
        © 2025 Pepe's Power Solutions | Dashboard v3.0
    </div>
    """, unsafe_allow_html=True)

    # --- Notifications ---
    st.toast("Dashboard loaded successfully!", icon="🐸")

# Run the main function
if __name__ == "__main__":
    main()