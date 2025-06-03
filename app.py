import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
from io import StringIO
import calendar

# Set page configuration
st.set_page_config(
    page_title="Agent Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Helper Functions ---
@st.cache_data
def load_and_process_data(data_string):
    """Load and process the CSV data from string"""
    try:
        # Load data from string
        data = StringIO(data_string)
        df = pd.read_csv(data)
        
        # Convert date columns to datetime
        df['ENROLLED DATE'] = pd.to_datetime(df['ENROLLED DATE'], errors='coerce')
        
        # Extract source from SOURCE_SHEET column
        df['SOURCE'] = df['SOURCE_SHEET'].str.split('-').str[0].str.strip()
        
        # Handle potential name format differences between sources
        if 'CUSTOMER ID' not in df.columns and 'CID' in df.columns:
            df.rename(columns={'CID': 'CUSTOMER ID'}, inplace=True)
            
        return df
    except Exception as e:
        st.error(f"Error processing data: {e}")
        return pd.DataFrame()

def filter_data_by_date(df, start_date, end_date):
    """Filter dataframe by date range"""
    return df[(df['ENROLLED DATE'].dt.date >= start_date) & 
              (df['ENROLLED DATE'].dt.date <= end_date)]

def filter_data_by_status(df, statuses):
    """Filter dataframe by status"""
    return df[df['STATUS'].isin(statuses)]

def filter_data_by_agent(df, agents):
    """Filter dataframe by agent"""
    return df[df['AGENT'].isin(agents)]

def filter_data_by_source(df, sources):
    """Filter dataframe by source"""
    return df[df['SOURCE'].isin(sources)]

def calculate_metrics(df):
    """Calculate key metrics from filtered dataframe"""
    metrics = {
        'total_enrollments': len(df),
        'active_enrollments': len(df[df['STATUS'] == 'ACTIVE']),
        'dropped_enrollments': len(df[df['STATUS'].str.contains('DROPPED', case=False, na=False)]),
        'pending_cancellations': len(df[df['STATUS'] == 'PENDING CANCELLATION']),
        'other_status': len(df[~df['STATUS'].isin(['ACTIVE', 'DROPPED', 'PENDING CANCELLATION'])]),
        'active_rate': len(df[df['STATUS'] == 'ACTIVE']) / len(df) if len(df) > 0 else 0,
        'unique_agents': df['AGENT'].nunique(),
        'unique_sources': df['SOURCE'].nunique()
    }
    return metrics

# --- Main App ---
def main():
    st.title("Agent Performance Dashboard")
    
    # Load data
    data_file = """CUSTOMER ID,AGENT,ENROLLED DATE,STATUS,SOURCE_SHEET
[YOUR CSV DATA HERE]"""
    
    df = load_and_process_data(st.session_state.get('data', data_file))
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date filter
    with st.sidebar.expander("Date Range", expanded=True):
        # Get min and max dates from data
        if not df.empty:
            min_date = df['ENROLLED DATE'].min().date()
            max_date = df['ENROLLED DATE'].max().date()
        else:
            min_date = date.today() - timedelta(days=30)
            max_date = date.today()
            
        date_option = st.radio(
            "Select time period:",
            ["Last 7 days", "Last 30 days", "Last 90 days", "Custom"]
        )
        
        if date_option == "Last 7 days":
            start_date = max_date - timedelta(days=7)
            end_date = max_date
        elif date_option == "Last 30 days":
            start_date = max_date - timedelta(days=30)
            end_date = max_date
        elif date_option == "Last 90 days":
            start_date = max_date - timedelta(days=90)
            end_date = max_date
        else:  # Custom
            col1, col2 = st.sidebar.columns(2)
            start_date = col1.date_input("Start date", min_date)
            end_date = col2.date_input("End date", max_date)
    
    # Status filter
    with st.sidebar.expander("Status", expanded=True):
        if not df.empty:
            all_statuses = sorted(df['STATUS'].unique())
            default_statuses = ['ACTIVE', 'PENDING CANCELLATION'] if 'ACTIVE' in all_statuses else all_statuses[:2]
            
            all_status_selected = st.checkbox("Select all statuses", value=False)
            if all_status_selected:
                selected_statuses = all_statuses
            else:
                selected_statuses = st.multiselect(
                    "Select statuses:",
                    options=all_statuses,
                    default=default_statuses
                )
        else:
            selected_statuses = ['ACTIVE']
    
    # Agent filter
    with st.sidebar.expander("Agent", expanded=True):
        if not df.empty:
            all_agents = sorted(df['AGENT'].unique())
            
            all_agents_selected = st.checkbox("Select all agents", value=True)
            if all_agents_selected:
                selected_agents = all_agents
            else:
                selected_agents = st.multiselect(
                    "Select agents:",
                    options=all_agents,
                    default=all_agents[:5] if len(all_agents) > 5 else all_agents
                )
        else:
            selected_agents = []
    
    # Source filter
    with st.sidebar.expander("Source", expanded=True):
        if not df.empty:
            all_sources = sorted(df['SOURCE'].unique())
            
            all_sources_selected = st.checkbox("Select all sources", value=True)
            if all_sources_selected:
                selected_sources = all_sources
            else:
                selected_sources = st.multiselect(
                    "Select sources:",
                    options=all_sources,
                    default=all_sources
                )
        else:
            selected_sources = []
    
    # Apply filters
    if not df.empty:
        filtered_df = df.copy()
        filtered_df = filter_data_by_date(filtered_df, start_date, end_date)
        filtered_df = filter_data_by_status(filtered_df, selected_statuses)
        filtered_df = filter_data_by_agent(filtered_df, selected_agents)
        filtered_df = filter_data_by_source(filtered_df, selected_sources)
    else:
        filtered_df = pd.DataFrame()
    
    # Calculate metrics
    if not filtered_df.empty:
        metrics = calculate_metrics(filtered_df)
        
        # Display metrics
        st.header("Key Performance Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total Enrollments", metrics['total_enrollments'])
        col2.metric("Active Enrollments", metrics['active_enrollments'], 
                   f"{metrics['active_rate']:.1%}")
        col3.metric("Dropped Enrollments", metrics['dropped_enrollments'])
        col4.metric("Pending Cancellations", metrics['pending_cancellations'])
        
        # Charts
        st.header("Performance Analytics")
        
        tab1, tab2, tab3 = st.tabs(["Enrollment Trends", "Agent Performance", "Source Analysis"])
        
        with tab1:
            # Daily enrollments
            st.subheader("Daily Enrollments")
            daily_enrollments = filtered_df.groupby(filtered_df['ENROLLED DATE'].dt.date).size().reset_index(name='count')
            daily_enrollments.columns = ['Date', 'Enrollments']
            
            fig = px.line(
                daily_enrollments,
                x='Date',
                y='Enrollments',
                title='Daily Enrollment Trend',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Status distribution
            st.subheader("Status Distribution")
            status_counts = filtered_df['STATUS'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig = px.pie(
                status_counts,
                values='Count',
                names='Status',
                title='Enrollment Status Distribution',
                hole=0.4
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Agent performance
            st.subheader("Agent Performance")
            
            agent_performance = filtered_df.groupby('AGENT').size().reset_index(name='Total')
            agent_active = filtered_df[filtered_df['STATUS'] == 'ACTIVE'].groupby('AGENT').size().reset_index(name='Active')
            agent_dropped = filtered_df[filtered_df['STATUS'].str.contains('DROPPED', case=False, na=False)].groupby('AGENT').size().reset_index(name='Dropped')
            
            # Merge dataframes
            agent_stats = agent_performance.merge(agent_active, on='AGENT', how='left')
            agent_stats = agent_stats.merge(agent_dropped, on='AGENT', how='left')
            agent_stats = agent_stats.fillna(0)
            
            # Calculate active rate
            agent_stats['Active Rate'] = agent_stats['Active'] / agent_stats['Total']
            
            # Sort by total enrollments
            agent_stats = agent_stats.sort_values('Total', ascending=False)
            
            # Display top agents
            fig = px.bar(
                agent_stats.head(10),
                x='AGENT',
                y='Total',
                title='Top 10 Agents by Total Enrollments',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display active rates
            fig = px.bar(
                agent_stats.sort_values('Active Rate', ascending=False).head(10),
                x='AGENT',
                y='Active Rate',
                title='Top 10 Agents by Active Rate',
                template='plotly_white',
                color='Active Rate',
                color_continuous_scale='RdYlGn'
            )
            
            fig.update_layout(yaxis_tickformat='.0%')
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Source analysis
            st.subheader("Source Analysis")
            
            source_counts = filtered_df['SOURCE'].value_counts().reset_index()
            source_counts.columns = ['Source', 'Count']
            
            fig = px.pie(
                source_counts,
                values='Count',
                names='Source',
                title='Enrollments by Source',
                hole=0.4
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Source performance over time
            source_time = filtered_df.groupby([filtered_df['ENROLLED DATE'].dt.to_period('M'), 'SOURCE']).size().reset_index(name='Count')
            source_time['Month'] = source_time['ENROLLED DATE'].dt.strftime('%Y-%m')
            
            fig = px.line(
                source_time,
                x='Month',
                y='Count',
                color='SOURCE',
                title='Monthly Enrollments by Source',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Source status distribution
            source_status = filtered_df.groupby(['SOURCE', 'STATUS']).size().reset_index(name='Count')
            
            fig = px.bar(
                source_status,
                x='SOURCE',
                y='Count',
                color='STATUS',
                title='Status Distribution by Source',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.header("Detailed Data")
        with st.expander("View Raw Data", expanded=False):
            st.dataframe(
                filtered_df.sort_values('ENROLLED DATE', ascending=False),
                use_container_width=True
            )
        
        # Download CSV button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name=f"agent_performance_data_{start_date}_to_{end_date}.csv",
            mime="text/csv",
        )
    else:
        st.warning("No data available or all data filtered out. Please adjust your filters.")

if __name__ == "__main__":
    main()
