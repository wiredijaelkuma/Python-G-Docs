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
import os

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

# Try to import modular components
modules_loaded = True
try:
    from data_explorer import render_data_explorer
    from risk_analysis import render_risk_analysis
    from performance_tab import render_performance_tab
    from agents_tab import render_agents_tab
    from overview_tab import render_overview_tab
except ImportError:
    modules_loaded = False

# --- Helper Functions ---
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
        </style>
        """, unsafe_allow_html=True)

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
            df.loc[df['STATUS'].str.contains('CANCEL|DROP|TERMIN', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
        
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def format_large_number(num):
    """Format large numbers with commas"""
    return f"{num:,}"

# --- Main App Logic ---
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
        <div class="metric-card">
            <div class="metric-title">Active</div>
            <div class="metric-value">{format_large_number(active_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">NSF Cases</div>
            <div class="metric-value">{format_large_number(nsf_cases)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Cancelled</div>
            <div class="metric-value">{format_large_number(cancelled_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Tab Navigation ---
    tabs = st.tabs(["Overview", "Performance", "Agents", "Risk Analysis", "Data Explorer"])
    
    # Only render tabs if modules are loaded
    if modules_loaded:
        # Overview Tab
        with tabs[0]:
            try:
                render_overview_tab(df_filtered, COLORS)
            except Exception as e:
                st.error(f"Error rendering Overview tab: {e}")
                st.write("Displaying basic overview instead:")
                # Basic overview fallback
                if 'CATEGORY' in df_filtered.columns:
                    st.subheader("Status Distribution")
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
            
        # Performance Tab
        with tabs[1]:
            try:
                render_performance_tab(df_filtered, COLORS)
            except Exception as e:
                st.error(f"Error rendering Performance tab: {e}")
                # Basic performance fallback
                if 'ENROLLED_DATE' in df_filtered.columns:
                    st.subheader("Monthly Enrollments")
                    monthly_data = df_filtered.groupby(df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
                    monthly_data.columns = ['Month', 'Count']
                    fig = px.bar(monthly_data, x='Month', y='Count')
                    st.plotly_chart(fig, use_container_width=True)
            
        # Agents Tab
        with tabs[2]:
            try:
                render_agents_tab(df_filtered, COLORS)
            except Exception as e:
                st.error(f"Error rendering Agents tab: {e}")
                # Basic agents fallback
                if 'AGENT' in df_filtered.columns:
                    st.subheader("Agent Performance")
                    agent_data = df_filtered.groupby('AGENT').size().reset_index()
                    agent_data.columns = ['Agent', 'Count']
                    fig = px.bar(agent_data, x='Agent', y='Count')
                    st.plotly_chart(fig, use_container_width=True)
            
        # Risk Analysis Tab
        with tabs[3]:
            try:
                render_risk_analysis(df_filtered, COLORS)
            except Exception as e:
                st.error(f"Error rendering Risk Analysis tab: {e}")
                # Basic risk analysis fallback
                st.subheader("Risk Distribution")
                if 'CATEGORY' in df_filtered.columns:
                    risk_data = pd.DataFrame({
                        'Category': ['Low Risk', 'Medium Risk', 'High Risk'],
                        'Count': [
                            len(df_filtered[df_filtered['CATEGORY'] == 'ACTIVE']),
                            len(df_filtered[df_filtered['CATEGORY'] == 'NSF']),
                            len(df_filtered[df_filtered['CATEGORY'] == 'CANCELLED'])
                        ]
                    })
                    fig = px.bar(risk_data, x='Category', y='Count')
                    st.plotly_chart(fig, use_container_width=True)
            
        # Data Explorer Tab
        with tabs[4]:
            try:
                render_data_explorer(df_filtered, COLORS, start)
            except Exception as e:
                st.error(f"Error rendering Data Explorer tab: {e}")
                # Basic data explorer fallback
                st.subheader("Data Preview")
                st.dataframe(df_filtered.head(100), use_container_width=True)
                
                # Download button
                csv = df_filtered.to_csv(index=False)
                st.download_button(
                    label="Download Filtered Data",
                    data=csv,
                    file_name="filtered_data.csv",
                    mime="text/csv"
                )
    else:
        # Fallback if modules aren't loaded
        # Overview Tab
        with tabs[0]:
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
        
        # Performance Tab
        with tabs[1]:
            st.subheader("Monthly Enrollments")
            if 'ENROLLED_DATE' in df_filtered.columns:
                monthly_data = df_filtered.groupby(df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
                monthly_data.columns = ['Month', 'Count']
                fig = px.bar(monthly_data, x='Month', y='Count')
                st.plotly_chart(fig, use_container_width=True)
        
        # Agents Tab
        with tabs[2]:
            st.subheader("Agent Performance")
            if 'AGENT' in df_filtered.columns:
                agent_data = df_filtered.groupby('AGENT').size().reset_index()
                agent_data.columns = ['Agent', 'Count']
                fig = px.bar(agent_data, x='Agent', y='Count')
                st.plotly_chart(fig, use_container_width=True)
        
        # Risk Analysis Tab
        with tabs[3]:
            st.subheader("Risk Distribution")
            if 'CATEGORY' in df_filtered.columns:
                risk_data = pd.DataFrame({
                    'Category': ['Low Risk', 'Medium Risk', 'High Risk'],
                    'Count': [
                        len(df_filtered[df_filtered['CATEGORY'] == 'ACTIVE']),
                        len(df_filtered[df_filtered['CATEGORY'] == 'NSF']),
                        len(df_filtered[df_filtered['CATEGORY'] == 'CANCELLED'])
                    ]
                })
                fig = px.bar(risk_data, x='Category', y='Count')
                st.plotly_chart(fig, use_container_width=True)
        
        # Data Explorer Tab
        with tabs[4]:
            st.subheader("Data Preview")
            st.dataframe(df_filtered.head(100), use_container_width=True)
            
            # Download button
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="Download Filtered Data",
                data=csv,
                file_name="filtered_data.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()