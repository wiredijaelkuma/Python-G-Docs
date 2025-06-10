import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# Set page configuration
st.set_page_config(
    layout="wide", 
    page_title="Pepe's Power Dashboard", 
    page_icon="🐸"
)

# Simple color palette
COLORS = {
    'primary': '#8A7FBA',
    'warning': '#FFD700',
    'danger': '#FF6347',
    'med_green': '#66CDAA',
    'dark_accent': '#40E0D0',
    'light_purple': '#E6E6FA'
}

# Load data function
@st.cache_data(ttl=3600)
def load_data():
    try:
        # Try to load from CSV file
        df = pd.read_csv("processed_combined_data.csv")
        
        # Basic preprocessing
        if 'ENROLLED_DATE' in df.columns:
            df['ENROLLED_DATE'] = pd.to_datetime(df['ENROLLED_DATE'], errors='coerce')
        
        if 'STATUS' in df.columns:
            df['CATEGORY'] = 'OTHER'
            df.loc[df['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            df.loc[df['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            df.loc[df['STATUS'].str.contains('CANCEL|DROP|TERMIN', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
        
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# Main app
def main():
    st.title("Pepe's Power Dashboard")
    
    # Load data
    with st.spinner("Loading data..."):
        df, error = load_data()
    
    if error:
        st.error(f"Error loading data: {error}")
        st.stop()
    
    if df.empty:
        st.warning("No data available. Please check your data file.")
        st.stop()
    
    # Date filter
    st.sidebar.header("Filters")
    
    # Date range
    if 'ENROLLED_DATE' in df.columns:
        min_date = df['ENROLLED_DATE'].min().date()
        max_date = df['ENROLLED_DATE'].max().date()
    else:
        min_date = date(2024, 1, 1)
        max_date = datetime.now().date()
    
    start_date = st.sidebar.date_input("Start Date", min_date)
    end_date = st.sidebar.date_input("End Date", max_date)
    
    # Status filter
    status_options = ['ACTIVE', 'NSF', 'CANCELLED', 'OTHER']
    selected_statuses = st.sidebar.multiselect("Status", status_options, default=status_options)
    
    # Apply filters
    filtered_df = df.copy()
    
    if 'ENROLLED_DATE' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['ENROLLED_DATE'].dt.date >= start_date) & 
            (filtered_df['ENROLLED_DATE'].dt.date <= end_date)
        ]
    
    if selected_statuses and 'CATEGORY' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['CATEGORY'].isin(selected_statuses)]
    
    # Display metrics
    st.header("Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Contracts", len(filtered_df))
    
    with col2:
        active_count = len(filtered_df[filtered_df['CATEGORY'] == 'ACTIVE']) if 'CATEGORY' in filtered_df.columns else 0
        st.metric("Active Contracts", active_count)
    
    with col3:
        nsf_count = len(filtered_df[filtered_df['CATEGORY'] == 'NSF']) if 'CATEGORY' in filtered_df.columns else 0
        st.metric("NSF Cases", nsf_count)
    
    with col4:
        cancelled_count = len(filtered_df[filtered_df['CATEGORY'] == 'CANCELLED']) if 'CATEGORY' in filtered_df.columns else 0
        st.metric("Cancelled", cancelled_count)
    
    # Display data
    st.header("Data Preview")
    st.dataframe(filtered_df.head(10))
    
    # Simple chart
    st.header("Status Distribution")
    if 'CATEGORY' in filtered_df.columns:
        status_counts = filtered_df['CATEGORY'].value_counts()
        st.bar_chart(status_counts)

if __name__ == "__main__":
    main()