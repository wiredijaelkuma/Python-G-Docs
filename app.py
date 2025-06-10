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
from modules.tabs.agents import render_agents_tab
from modules.tabs.risk_analysis import render_risk_analysis
from modules.tabs.data_explorer import render_data_explorer
from modules.tabs.drop_rate import render_drop_rate_tab

# --- Set page configuration first (must be the first Streamlit command) ---
st.set_page_config(
    layout="wide", 
    page_title="Pepe's Power Dashboard",
    page_icon="🐸",
    initial_sidebar_state="expanded"
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
        
        # Data source section - only show this if no data is loaded yet
        if 'df' not in st.session_state:
            st.header("Data Source")
            uploaded_file = st.file_uploader("Upload processed data CSV", type=["csv"])
            if uploaded_file is not None:
                st.session_state['uploaded_file'] = uploaded_file
                st.success("✅ File uploaded successfully!")

    # --- Banner ---
    try:
        st.image(os.path.join(ASSETS_DIR, "banner.png"), use_column_width=True)
    except:
        st.title("Pepe's Power Dashboard")

    # --- Data Loading ---
    with st.spinner("🔍 Loading data..."):
        # Try to load from uploaded file first, then fall back to default file
        if 'uploaded_file' in st.session_state:
            df = pd.read_csv(st.session_state['uploaded_file'])
            load_err = None
        else:
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
    create_header(df_filtered, start, end, status_filter, COLORS)

    # --- Metrics Summary ---
    display_metrics(df_filtered, COLORS)

    # --- Tab Navigation ---
    tabs = st.tabs(["Home", "Overview", "Performance", "Agents", "Drop Rate", "Risk Analysis", "Data Explorer"])
    
    # Home/Landing Page Tab
    with tabs[0]:
        try:
            render_landing_page(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Landing Page: {e}")
            import traceback
            st.exception(traceback.format_exc())
            fallback_landing_page(df_filtered, COLORS)
    
    # Overview Tab
    with tabs[1]:
        try:
            render_overview_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Overview tab: {e}")
            fallback_overview(df_filtered, COLORS)
        
    # Performance Tab
    with tabs[2]:
        try:
            render_performance_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Performance tab: {e}")
            fallback_performance(df_filtered, COLORS)
        
    # Agents Tab
    with tabs[3]:
        try:
            render_agents_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Agents tab: {e}")
            fallback_agents(df_filtered, COLORS)
        
    # Drop Rate Tab
    with tabs[4]:
        try:
            render_drop_rate_tab(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Drop Rate tab: {e}")
            fallback_drop_rate(df_filtered, COLORS)
        
    # Risk Analysis Tab
    with tabs[5]:
        try:
            render_risk_analysis(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Risk Analysis tab: {e}")
            fallback_risk_analysis(df_filtered, COLORS)
        
    # Data Explorer Tab
    with tabs[6]:
        try:
            render_data_explorer(df_filtered, COLORS)
        except Exception as e:
            st.error(f"Error rendering Data Explorer tab: {e}")
            fallback_data_explorer(df_filtered)

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
                active_count = len(recent_df[recent_df['CATEGORY'] == 'ACTIVE'])
                active_rate = (active_count / len(recent_df) * 100) if len(recent_df) > 0 else 0
                st.metric("Active Rate", f"{active_rate:.1f}%")
        
        # Simple table of recent enrollments
        if not recent_df.empty:
            # Determine which columns to show
            display_columns = []
            for col in ['ENROLLED_DATE', 'CUSTOMER_NAME', 'AGENT', 'STATUS', 'CATEGORY', 'AMOUNT']:
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

def fallback_overview(df_filtered, COLORS):
    import plotly.express as px
    
    st.subheader("Status Distribution")
    if 'CATEGORY' in df_filtered.columns:
        fig = px.pie(
            df_filtered['CATEGORY'].value_counts().reset_index(),
            values='count',
            names='CATEGORY',
            color='CATEGORY',
            color_discrete_map={
                'ACTIVE': COLORS['med_green'],
                'NSF': COLORS['warning'],
                'CANCELLED': COLORS['danger'],
                'OTHER': COLORS['dark_accent']
            }
        )
        st.plotly_chart(fig, use_container_width=True)

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

def fallback_agents(df_filtered, COLORS):
    st.subheader("Agent Performance")
    if 'AGENT' in df_filtered.columns:
        agent_counts = df_filtered['AGENT'].value_counts().head(10).reset_index()
        agent_counts.columns = ['Agent', 'Enrollments']
        st.dataframe(agent_counts)

def fallback_drop_rate(df_filtered, COLORS):
    st.subheader("Drop Rate Analysis")
    if 'CATEGORY' in df_filtered.columns and 'ENROLLED_DATE' in df_filtered.columns:
        # Calculate overall drop rate
        total = len(df_filtered)
        cancelled = len(df_filtered[df_filtered['CATEGORY'] == 'CANCELLED'])
        drop_rate = (cancelled / total * 100) if total > 0 else 0
        
        st.metric("Overall Drop Rate", f"{drop_rate:.1f}%")

def fallback_risk_analysis(df_filtered, COLORS):
    st.subheader("Risk Analysis")
    if 'CATEGORY' in df_filtered.columns:
        risk_data = df_filtered['CATEGORY'].value_counts(normalize=True).reset_index()
        risk_data.columns = ['Status', 'Percentage']
        risk_data['Percentage'] = risk_data['Percentage'] * 100
        st.dataframe(risk_data)

def fallback_data_explorer(df_filtered):
    st.subheader("Data Explorer")
    st.dataframe(df_filtered.head(100))

if __name__ == "__main__":
    main()