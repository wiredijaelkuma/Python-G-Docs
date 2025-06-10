import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import os
from flask import Flask, jsonify, request
import threading
import json
from io import StringIO

# --- Set page configuration first (must be the first Streamlit command) ---
st.set_page_config(
    layout="wide", 
    page_title="Pepe's Power Dashboard", 
    page_icon="🐸",
    initial_sidebar_state="expanded"
)

# --- Constants ---
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

# --- Flask API Setup ---
# Create a Flask app for API endpoints
flask_app = Flask(__name__)

# Global variable to store data
data_cache = None
last_update_time = None

@flask_app.route('/api/data')
def get_data():
    global data_cache
    if data_cache is not None:
        return jsonify(data_cache)
    else:
        return jsonify({"error": "No data available"})

def run_flask():
    flask_app.run(port=8080)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# --- Helper Functions ---
@st.cache_data(ttl=3600)
def load_data():
    """Load data with minimal processing for speed"""
    try:
        # Simple CSV reading without complex options
        df = pd.read_csv("processed_combined_data.csv")
        
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

def update_api_data(df_filtered):
    """Update the Flask API data cache"""
    global data_cache, last_update_time
    
    # Calculate metrics
    total_contracts = len(df_filtered)
    
    if 'CATEGORY' in df_filtered.columns:
        active_contracts = len(df_filtered[df_filtered['CATEGORY'] == 'ACTIVE'])
        nsf_cases = len(df_filtered[df_filtered['CATEGORY'] == 'NSF'])
        cancelled_contracts = len(df_filtered[df_filtered['CATEGORY'] == 'CANCELLED'])
    else:
        active_contracts = nsf_cases = cancelled_contracts = 0
    
    # Status distribution
    status_counts = df_filtered['CATEGORY'].value_counts().to_dict() if 'CATEGORY' in df_filtered.columns else {}
    
    # Monthly trends
    monthly_data = {}
    if 'ENROLLED_DATE' in df_filtered.columns:
        monthly_df = df_filtered.groupby([df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m'), 'CATEGORY']).size().reset_index()
        monthly_df.columns = ['Month', 'Category', 'Count']
        
        for _, row in monthly_df.iterrows():
            month = row['Month']
            category = row['Category']
            count = row['Count']
            
            if month not in monthly_data:
                monthly_data[month] = {}
            
            monthly_data[month][category] = count
    
    # Create data for API
    data_cache = {
        "metrics": {
            "total": total_contracts,
            "active": active_contracts,
            "nsf": nsf_cases,
            "cancelled": cancelled_contracts
        },
        "status_counts": status_counts,
        "monthly_data": monthly_data,
        "data": df_filtered.head(100).to_dict(orient='records')  # Limit to 100 rows for API
    }
    
    last_update_time = datetime.now()

# --- Main App Logic ---
def main():
    # --- Sidebar ---
    with st.sidebar:
        st.title("🐸 Pepe's Power")
        
        # Add refresh data button
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
    st.title("Pepe's Power Dashboard")
    st.markdown("---")

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
        st.markdown("## Dashboard Controls")
        
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
    
    # Update API data
    update_api_data(df_filtered)

    # --- Dashboard Header ---
    st.markdown(f"""
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
        st.metric("Total Contracts", format_large_number(total_contracts))

    with col2:
        st.metric("Active Contracts", format_large_number(active_contracts))

    with col3:
        st.metric("NSF Cases", format_large_number(nsf_cases))

    with col4:
        st.metric("Cancelled", format_large_number(cancelled_contracts))

    with col5:
        st.metric("Success Rate", f"{success_rate:.1f}%")

    # --- Tab Interface ---
    tab1, tab2, tab3 = st.tabs([
        "📊 Overview", 
        "📈 Performance", 
        "🔍 Data Explorer"
    ])

    # --- Overview Tab ---
    with tab1:
        st.header("Status Distribution")
        
        # Status distribution pie chart
        if 'CATEGORY' in df_filtered.columns:
            status_counts = df_filtered['CATEGORY'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig = px.pie(
                status_counts, 
                values='Count', 
                names='Status',
                color='Status',
                color_discrete_map={
                    'ACTIVE': COLORS['med_green'],
                    'NSF': COLORS['warning'],
                    'CANCELLED': COLORS['danger'],
                    'OTHER': COLORS['dark_accent']
                }
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        # Monthly trends
        st.header("Monthly Trends")
        if 'ENROLLED_DATE' in df_filtered.columns:
            monthly_df = df_filtered.groupby([df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m'), 'CATEGORY']).size().reset_index()
            monthly_df.columns = ['Month', 'Category', 'Count']
            
            fig = px.bar(
                monthly_df,
                x='Month',
                y='Count',
                color='Category',
                barmode='stack',
                color_discrete_map={
                    'ACTIVE': COLORS['med_green'],
                    'NSF': COLORS['warning'],
                    'CANCELLED': COLORS['danger'],
                    'OTHER': COLORS['dark_accent']
                }
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # --- Performance Tab ---
    with tab2:
        st.header("Success Rate Over Time")
        
        if 'ENROLLED_DATE' in df_filtered.columns and 'CATEGORY' in df_filtered.columns:
            # Group by month
            monthly_df = df_filtered.groupby(df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m')).agg(
                Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
                Total=('CATEGORY', 'count')
            ).reset_index()
            
            monthly_df['Success_Rate'] = monthly_df['Active'] / monthly_df['Total'] * 100
            monthly_df = monthly_df.sort_values('ENROLLED_DATE')
            
            fig = px.line(
                monthly_df,
                x='ENROLLED_DATE',
                y='Success_Rate',
                markers=True,
                labels={'ENROLLED_DATE': 'Month', 'Success_Rate': 'Success Rate (%)'}
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
            
        st.header("Agent Performance")
        if 'AGENT' in df_filtered.columns and 'CATEGORY' in df_filtered.columns:
            agent_df = df_filtered.groupby('AGENT').agg(
                Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
                Total=('CATEGORY', 'count')
            ).reset_index()
            
            agent_df['Success_Rate'] = agent_df['Active'] / agent_df['Total'] * 100
            agent_df = agent_df.sort_values('Success_Rate', ascending=False)
            
            fig = px.bar(
                agent_df,
                x='AGENT',
                y='Success_Rate',
                color='Success_Rate',
                color_continuous_scale=['red', 'yellow', 'green'],
                labels={'AGENT': 'Agent', 'Success_Rate': 'Success Rate (%)'}
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

    # --- Data Explorer Tab ---
    with tab3:
        st.header("Data Preview")
        st.dataframe(df_filtered, use_container_width=True)
        
        # Download button
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data",
            data=csv,
            file_name="filtered_data.csv",
            mime="text/csv"
        )
        
        # API Information
        st.header("API Access")
        st.info("""
        This dashboard provides an API endpoint to access the filtered data:
        
        - **Endpoint:** http://localhost:8080/api/data
        - **Method:** GET
        - **Format:** JSON
        
        The API returns the current filtered data including metrics, status counts, monthly trends, and a preview of the data.
        """)
        
        if last_update_time:
            st.write(f"Last API data update: {last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Run the main function
if __name__ == "__main__":
    main()