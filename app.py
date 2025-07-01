import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.gsheet_connector import fetch_data_from_sheet

# Page config
st.set_page_config(layout="wide", page_title="Pepe's Power Dashboard", page_icon="🐸")

# Colors
COLORS = {
    'primary': '#8A7FBA',
    'secondary': '#6A5ACD', 
    'accent': '#7FFFD4',
    'warning': '#FFD700',
    'danger': '#FF6347',
    'success': '#98FB98'
}

def main():
    # Sidebar
    with st.sidebar:
        st.title("🐸 Pepe's Power")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("**Google Sheet:** [Forth Py](https://docs.google.com/spreadsheets)")

    # Load data
    with st.spinner("Loading data..."):
        df, error = fetch_data_from_sheet()
        
        if error:
            st.error(f"Error: {error}")
            return
            
        if df.empty:
            st.warning("No data available")
            return

    # Update sidebar with data info
    with st.sidebar:
        st.info(f"Total Records: {len(df)}")
        if 'SOURCE_SHEET' in df.columns:
            for source in df['SOURCE_SHEET'].unique():
                count = len(df[df['SOURCE_SHEET'] == source])
                st.write(f"• {source}: {count}")

    # Header
    st.title("Pepe's Power Dashboard")
    st.markdown(f"**Total Records:** {len(df)} | **Sources:** {', '.join(df['SOURCE_SHEET'].unique()) if 'SOURCE_SHEET' in df.columns else 'N/A'}")

    # Tabs
    tabs = st.tabs(["Overview", "Agents", "Commission", "Data Explorer"])
    
    with tabs[0]:
        render_overview(df, COLORS)
    
    with tabs[1]:
        render_agents(df, COLORS)
    
    with tabs[2]:
        render_commission(df, COLORS)
    
    with tabs[3]:
        render_data_explorer(df, COLORS)

def render_overview(df, COLORS):
    st.header("Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(df))
    
    with col2:
        if 'CATEGORY' in df.columns:
            active_count = len(df[df['CATEGORY'] == 'ACTIVE'])
            st.metric("Active", active_count)
    
    with col3:
        if 'CATEGORY' in df.columns:
            cancelled_count = len(df[df['CATEGORY'] == 'CANCELLED'])
            st.metric("Cancelled", cancelled_count)
    
    with col4:
        if 'SOURCE_SHEET' in df.columns:
            st.metric("Data Sources", df['SOURCE_SHEET'].nunique())

    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if 'SOURCE_SHEET' in df.columns:
            source_counts = df['SOURCE_SHEET'].value_counts()
            fig = px.pie(values=source_counts.values, names=source_counts.index, 
                        title="Records by Source", color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'CATEGORY' in df.columns:
            category_counts = df['CATEGORY'].value_counts()
            fig = px.bar(x=category_counts.index, y=category_counts.values,
                        title="Records by Category", color=category_counts.index,
                        color_discrete_map={'ACTIVE': COLORS['success'], 'CANCELLED': COLORS['danger'], 'NSF': COLORS['warning']})
            st.plotly_chart(fig, use_container_width=True)

    # Monthly trend
    if 'ENROLLED_DATE' in df.columns:
        st.subheader("Monthly Enrollment Trend")
        df_with_date = df[df['ENROLLED_DATE'].notna()].copy()
        if not df_with_date.empty:
            df_with_date['Month'] = df_with_date['ENROLLED_DATE'].dt.strftime('%Y-%m')
            monthly_counts = df_with_date.groupby('Month').size().reset_index()
            monthly_counts.columns = ['Month', 'Count']
            
            fig = px.line(monthly_counts, x='Month', y='Count', markers=True,
                         title="Monthly Enrollments", color_discrete_sequence=[COLORS['primary']])
            st.plotly_chart(fig, use_container_width=True)

def render_agents(df, COLORS):
    st.header("Agent Performance")
    
    if 'AGENT' not in df.columns:
        st.warning("No agent data available")
        return
    
    # Agent selector
    agents = df['AGENT'].dropna().unique()
    selected_agent = st.selectbox("Select Agent", ['All Agents'] + list(agents))
    
    if selected_agent == 'All Agents':
        agent_df = df
        st.subheader("All Agents Performance")
    else:
        agent_df = df[df['AGENT'] == selected_agent]
        st.subheader(f"{selected_agent} Performance")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(agent_df))
    
    with col2:
        if 'CATEGORY' in agent_df.columns:
            active_count = len(agent_df[agent_df['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_count / len(agent_df) * 100) if len(agent_df) > 0 else 0
            st.metric("Active", f"{active_count} ({active_rate:.1f}%)")
    
    with col3:
        if 'CATEGORY' in agent_df.columns:
            cancelled_count = len(agent_df[agent_df['CATEGORY'] == 'CANCELLED'])
            cancel_rate = (cancelled_count / len(agent_df) * 100) if len(agent_df) > 0 else 0
            st.metric("Cancelled", f"{cancelled_count} ({cancel_rate:.1f}%)")
    
    with col4:
        if 'CATEGORY' in agent_df.columns:
            nsf_count = len(agent_df[agent_df['CATEGORY'] == 'NSF'])
            nsf_rate = (nsf_count / len(agent_df) * 100) if len(agent_df) > 0 else 0
            st.metric("NSF", f"{nsf_count} ({nsf_rate:.1f}%)")

    # Agent comparison chart
    if selected_agent == 'All Agents' and 'CATEGORY' in df.columns:
        st.subheader("Agent Comparison")
        
        agent_stats = df.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': lambda x: (x == 'ACTIVE').sum()
        }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Active'})
        
        agent_stats['Active_Rate'] = (agent_stats['Active'] / agent_stats['Total'] * 100).round(1)
        agent_stats = agent_stats.sort_values('Active_Rate', ascending=False).head(10)
        
        fig = px.bar(agent_stats, x=agent_stats.index, y='Active_Rate',
                    title="Top 10 Agents by Active Rate", color='Active_Rate',
                    color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

def render_commission(df, COLORS):
    st.header("Commission Dashboard")
    
    # Check for commission data
    if 'SOURCE_SHEET' not in df.columns or 'Comission' not in df['SOURCE_SHEET'].values:
        st.warning("No commission data found")
        return
    
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy()
    
    if commission_df.empty:
        st.warning("Commission data is empty")
        return
    
    st.success(f"Commission data loaded: {len(commission_df)} records")
    
    # Show available columns
    with st.expander("Available Columns"):
        st.write(commission_df.columns.tolist())
        st.dataframe(commission_df.head(3))
    
    # Basic metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Payments", len(commission_df))
    
    with col2:
        if 'STATUS' in commission_df.columns:
            cleared_count = len(commission_df[commission_df['STATUS'].str.contains('Cleared', na=False)])
            st.metric("Cleared Payments", cleared_count)
    
    with col3:
        if 'AGENT' in commission_df.columns:
            unique_agents = commission_df['AGENT'].nunique()
            st.metric("Unique Agents", unique_agents)
    
    # Status distribution
    if 'STATUS' in commission_df.columns:
        st.subheader("Payment Status Distribution")
        status_counts = commission_df['STATUS'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index,
                    title="Payment Status", color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
    
    # Agent performance
    if 'AGENT' in commission_df.columns and 'STATUS' in commission_df.columns:
        st.subheader("Agent Payment Performance")
        
        agent_stats = commission_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'STATUS': lambda x: x.str.contains('Cleared', na=False).sum()
        }).rename(columns={'AGENT': 'Total', 'STATUS': 'Cleared'})
        
        agent_stats['Clear_Rate'] = (agent_stats['Cleared'] / agent_stats['Total'] * 100).round(1)
        agent_stats = agent_stats.sort_values('Clear_Rate', ascending=False)
        
        fig = px.bar(agent_stats.head(10), x=agent_stats.head(10).index, y='Clear_Rate',
                    title="Top 10 Agents by Clear Rate", color='Clear_Rate',
                    color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

def render_data_explorer(df, COLORS):
    st.header("Data Explorer")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        if 'SOURCE_SHEET' in df.columns:
            sources = st.multiselect("Filter by Source", df['SOURCE_SHEET'].unique(), default=df['SOURCE_SHEET'].unique())
        else:
            sources = []
    
    with col2:
        if 'CATEGORY' in df.columns:
            categories = st.multiselect("Filter by Category", df['CATEGORY'].unique(), default=df['CATEGORY'].unique())
        else:
            categories = []
    
    # Apply filters
    filtered_df = df.copy()
    if sources and 'SOURCE_SHEET' in df.columns:
        filtered_df = filtered_df[filtered_df['SOURCE_SHEET'].isin(sources)]
    if categories and 'CATEGORY' in df.columns:
        filtered_df = filtered_df[filtered_df['CATEGORY'].isin(categories)]
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} records")
    
    # Display data
    st.dataframe(filtered_df, use_container_width=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download CSV", csv, "data.csv", "text/csv")

if __name__ == "__main__":
    main()