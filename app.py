import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.gsheet_connector import fetch_data_from_sheet

# Page config
st.set_page_config(layout="wide", page_title="Pepe's Power Dashboard", page_icon="🐸", initial_sidebar_state="collapsed")

# Assets directory
ASSETS_DIR = "assets"

# Clean color palette
COLORS = {
    'primary': '#4A90E2',      # Clean blue
    'secondary': '#7B68EE',    # Medium slate blue
    'success': '#5CB85C',      # Success green
    'warning': '#F0AD4E',      # Warning orange
    'danger': '#D9534F',       # Danger red
    'info': '#5BC0DE',         # Info cyan
    'light': '#F8F9FA',        # Light gray
    'dark': '#343A40',         # Dark gray
}

# Heat map colors - darker blues for better visibility
HEAT_COLORS = ['#64B5F6', '#42A5F5', '#2196F3', '#1E88E5', '#1976D2', '#1565C0', '#0D47A1', '#0A3D91']

def load_css():
    st.markdown("""
    <style>
    .stApp {
        background: #F8F9FA;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 18px;
        font-weight: 600;
        padding: 12px 24px;
        border-radius: 8px;
        margin: 0 4px;
    }
    
    .stTabs [aria-selected="true"] {
        background: #4A90E2;
        color: white;
    }
    
    .stSelectbox > div > div {
        font-size: 16px;
        padding: 12px;
        border: 2px solid #4A90E2;
        border-radius: 8px;
        background: white;
        color: #343A40;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    load_css()
    
    # Banner
    try:
        import os
        st.image(os.path.join(ASSETS_DIR, "banner.jpg"), use_container_width=True)
    except:
        st.title("🐸 Pepe's Power Dashboard")
    
    # Sidebar
    with st.sidebar:
        try:
            st.image(os.path.join(ASSETS_DIR, "pepe-muscle.jpg"), width=180)
        except:
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

    # Update sidebar
    with st.sidebar:
        st.info(f"Total Records: {len(df)}")
        if 'SOURCE_SHEET' in df.columns:
            for source in df['SOURCE_SHEET'].unique():
                count = len(df[df['SOURCE_SHEET'] == source])
                st.write(f"• {source}: {count}")

    # Main tabs
    tabs = st.tabs(["📊 Dashboard", "👥 Agents", "💰 Commission", "🔍 Data"])
    
    with tabs[0]:
        render_dashboard(df, COLORS, HEAT_COLORS)
    
    with tabs[1]:
        from modules.agent_hybrid_fixed import render_agent_hybrid_analysis
        render_agent_hybrid_analysis(df, COLORS, HEAT_COLORS)
    
    with tabs[2]:
        from modules.commission_fixed import render_commission_analysis
        render_commission_analysis(df, COLORS, HEAT_COLORS)
    
    with tabs[3]:
        render_data_explorer(df, COLORS)

def render_dashboard(df, COLORS, HEAT_COLORS):
    # Filter out commission data
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else df.copy()
    
    if sales_df.empty or 'ENROLLED_DATE' not in sales_df.columns:
        st.warning("No sales data available")
        return
    
    # Prepare data
    sales_df = sales_df[sales_df['ENROLLED_DATE'].notna()].copy()
    
    # Dashboard subtabs
    subtabs = st.tabs(["📅 Weekly", "📆 Monthly", "📈 Trends"])
    
    with subtabs[0]:
        render_weekly_complete(sales_df, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        from modules.monthly_dashboard import render_monthly_dashboard
        render_monthly_dashboard(sales_df, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        from modules.trends_dashboard import render_trends_dashboard
        render_trends_dashboard(sales_df, COLORS, HEAT_COLORS)

def render_weekly_complete(sales_df, COLORS, HEAT_COLORS):
    """Complete weekly dashboard with all displays"""
    st.subheader("📅 Weekly Analysis")
    
    # Date range for weeks
    min_date = sales_df['ENROLLED_DATE'].min().date()
    max_date = sales_df['ENROLLED_DATE'].max().date()
    
    # Week selection with date picker
    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input(
            "Select Any Date in Week:",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="weekly_date_picker"
        )
    
    with col2:
        # Calculate Monday-Sunday week for selected date
        selected_dt = pd.Timestamp(selected_date)
        days_since_monday = selected_dt.weekday()
        week_start = selected_dt - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        st.info(f"Week: {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")
    
    # Filter data for selected week
    week_data = sales_df[
        (sales_df['ENROLLED_DATE'] >= week_start) & 
        (sales_df['ENROLLED_DATE'] <= week_end)
    ].copy()
    
    if week_data.empty:
        st.warning("No data for selected week")
        return
    
    # Weekly metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", len(week_data))
    
    with col2:
        if 'CATEGORY' in week_data.columns:
            active_count = len(week_data[week_data['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_count / len(week_data) * 100) if len(week_data) > 0 else 0
            st.metric("Active Sales", f"{active_count} ({active_rate:.1f}%)")
    
    with col3:
        if 'CATEGORY' in week_data.columns:
            cancelled_count = len(week_data[week_data['CATEGORY'] == 'CANCELLED'])
            st.metric("Cancelled", cancelled_count)
    
    with col4:
        if 'AGENT' in week_data.columns:
            st.metric("Active Agents", week_data['AGENT'].nunique())
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        if 'SOURCE_SHEET' in week_data.columns and 'CATEGORY' in week_data.columns:
            st.subheader("Sales by Source")
            source_breakdown = week_data.groupby(['SOURCE_SHEET', 'CATEGORY']).size().unstack(fill_value=0)
            
            if not source_breakdown.empty:
                fig = px.bar(
                    source_breakdown,
                    title="Sales Breakdown by Source",
                    color_discrete_map={
                        'ACTIVE': COLORS['success'],
                        'CANCELLED': COLORS['danger'],
                        'NSF': COLORS['warning'],
                        'OTHER': COLORS['info']
                    }
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'AGENT' in week_data.columns:
            st.subheader("Top Agents")
            if 'CATEGORY' in week_data.columns:
                active_agents = week_data[week_data['CATEGORY'] == 'ACTIVE']['AGENT'].value_counts().head(10)
            else:
                active_agents = week_data['AGENT'].value_counts().head(10)
            
            if not active_agents.empty:
                fig = px.bar(
                    x=active_agents.values,
                    y=active_agents.index,
                    orientation='h',
                    title="Top Performers (Active Sales)",
                    color=active_agents.values,
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Daily Sales Trend")
        daily_sales = week_data.groupby(week_data['ENROLLED_DATE'].dt.date).size().reset_index()
        daily_sales.columns = ['Date', 'Sales']
        
        if not daily_sales.empty:
            fig = px.line(
                daily_sales,
                x='Date',
                y='Sales',
                title="Daily Sales This Week",
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'CATEGORY' in week_data.columns:
            st.subheader("Status Distribution")
            status_counts = week_data['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Weekly Status Breakdown",
                color_discrete_map={
                    'ACTIVE': COLORS['success'],
                    'CANCELLED': COLORS['danger'],
                    'NSF': COLORS['warning'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Agent Performance Table
    st.subheader("📋 Weekly Agent Performance")
    if 'AGENT' in week_data.columns and 'CATEGORY' in week_data.columns:
        agent_summary = week_data.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        agent_summary.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
        agent_summary['Active_Rate'] = (agent_summary['Active_Sales'] / agent_summary['Total_Sales'] * 100).round(1)
        agent_summary = agent_summary.sort_values('Active_Sales', ascending=False).reset_index()
        
        st.dataframe(agent_summary, use_container_width=True, hide_index=True)

def render_trends_complete(sales_df, COLORS, HEAT_COLORS):
    """Complete trends dashboard with working dropdown"""
    st.subheader("📈 Performance Trends")
    
    # Time range selector - WORKING
    time_range = st.selectbox(
        "📅 Select Time Range:",
        ["Last 30 Days", "Last 60 Days", "Last 90 Days", "Last 180 Days"],
        index=2,
        key="trends_time_range_fixed"
    )
    
    # Calculate date range
    end_date = sales_df['ENROLLED_DATE'].max()
    days_map = {"Last 30 Days": 30, "Last 60 Days": 60, "Last 90 Days": 90, "Last 180 Days": 180}
    start_date = end_date - timedelta(days=days_map[time_range])
    
    # Filter data for selected range
    trend_data = sales_df[
        (sales_df['ENROLLED_DATE'] >= start_date) & 
        (sales_df['ENROLLED_DATE'] <= end_date)
    ].copy()
    
    if trend_data.empty:
        st.warning("No data for selected time range")
        return
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'CATEGORY' in trend_data.columns:
            stick_rate = (len(trend_data[trend_data['CATEGORY'] == 'ACTIVE']) / len(trend_data) * 100) if len(trend_data) > 0 else 0
            st.metric("Stick Rate", f"{stick_rate:.1f}%")
    
    with col2:
        mid_date = start_date + (end_date - start_date) / 2
        first_half = len(trend_data[trend_data['ENROLLED_DATE'] < mid_date])
        second_half = len(trend_data[trend_data['ENROLLED_DATE'] >= mid_date])
        growth = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        st.metric("Sales Growth", f"{growth:+.1f}%")
    
    with col3:
        if 'AGENT' in trend_data.columns:
            avg_per_agent = len(trend_data) / trend_data['AGENT'].nunique() if trend_data['AGENT'].nunique() > 0 else 0
            efficiency = min(avg_per_agent * 10, 100)
            st.metric("Team Efficiency", f"{efficiency:.1f}%")
    
    with col4:
        if 'CATEGORY' in trend_data.columns:
            conversion_rate = (len(trend_data[trend_data['CATEGORY'] == 'ACTIVE']) / len(trend_data) * 100) if len(trend_data) > 0 else 0
            st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales Velocity")
        trend_data['Week'] = trend_data['ENROLLED_DATE'].dt.to_period('W').dt.start_time
        weekly_sales = trend_data.groupby('Week').size().reset_index()
        weekly_sales.columns = ['Week', 'Sales']
        
        if not weekly_sales.empty:
            fig = px.line(
                weekly_sales,
                x='Week',
                y='Sales',
                title=f"Weekly Sales Velocity - {time_range}",
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Agent Consistency")
        if 'AGENT' in trend_data.columns and 'CATEGORY' in trend_data.columns:
            agent_performance = trend_data.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'ACTIVE').sum()
            }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Active'})
            
            agent_performance['Stick_Rate'] = (agent_performance['Active'] / agent_performance['Total'] * 100).round(1)
            agent_performance['Volume_Weight'] = (agent_performance['Total'] / agent_performance['Total'].max() * 100).round(1)
            agent_performance['Weighted_Score'] = (agent_performance['Stick_Rate'] * 0.7 + agent_performance['Volume_Weight'] * 0.3).round(1)
            
            agent_performance = agent_performance[agent_performance['Total'] >= 3]
            agent_performance = agent_performance.sort_values('Weighted_Score', ascending=False).head(10)
            
            if not agent_performance.empty:
                fig = px.bar(
                    agent_performance,
                    x=agent_performance.index,
                    y='Weighted_Score',
                    title="Top Agents by Weighted Performance",
                    color='Weighted_Score',
                    color_continuous_scale=HEAT_COLORS,
                    hover_data=['Stick_Rate', 'Total', 'Active']
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)

def render_agents_complete(df, COLORS, HEAT_COLORS):
    """Complete agents dashboard refactor"""
    st.header("👥 Agent Performance Analysis")
    
    # Filter sales data
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else df.copy()
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    
    if sales_df.empty:
        st.warning("No sales data available")
        return
    
    # Agent selector - WORKING
    if 'AGENT' in sales_df.columns:
        agents_list = ['All Agents'] + sorted(sales_df['AGENT'].dropna().unique().tolist())
        selected_agent = st.selectbox(
            "👤 Select Agent for Analysis:",
            agents_list,
            index=0,
            key="agent_selector_main"
        )
        
        if selected_agent == 'All Agents':
            agent_sales = sales_df
            agent_commission = commission_df
        else:
            agent_sales = sales_df[sales_df['AGENT'] == selected_agent]
            agent_commission = commission_df[commission_df['AGENT'] == selected_agent] if not commission_df.empty else pd.DataFrame()
    else:
        st.warning("No agent data available")
        return
    
    # Agent metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", len(agent_sales))
    
    with col2:
        if 'CATEGORY' in agent_sales.columns:
            active_count = len(agent_sales[agent_sales['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_count / len(agent_sales) * 100) if len(agent_sales) > 0 else 0
            st.metric("Active Rate", f"{active_rate:.1f}%")
    
    with col3:
        if 'CATEGORY' in agent_sales.columns:
            cancelled_count = len(agent_sales[agent_sales['CATEGORY'] == 'CANCELLED'])
            st.metric("Cancelled", cancelled_count)
    
    with col4:
        commission_count = len(agent_commission) if not agent_commission.empty else 0
        st.metric("Commission Payments", commission_count)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales Performance")
        if 'CATEGORY' in agent_sales.columns:
            status_counts = agent_sales['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title=f"Sales Status - {selected_agent}",
                color_discrete_map={
                    'ACTIVE': COLORS['success'],
                    'CANCELLED': COLORS['danger'],
                    'NSF': COLORS['warning'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Commission Performance")
        if not agent_commission.empty and 'CATEGORY' in agent_commission.columns:
            commission_status = agent_commission['CATEGORY'].value_counts()
            
            fig = px.bar(
                x=commission_status.index,
                y=commission_status.values,
                title=f"Commission Status - {selected_agent}",
                color=commission_status.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No commission data available")
    
    # Performance table
    st.subheader("📋 Agent Performance Summary")
    if 'AGENT' in sales_df.columns and 'CATEGORY' in sales_df.columns:
        performance_summary = sales_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        performance_summary.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
        performance_summary['Active_Rate'] = (performance_summary['Active_Sales'] / performance_summary['Total_Sales'] * 100).round(1)
        performance_summary = performance_summary.sort_values('Active_Rate', ascending=False).reset_index()
        
        st.dataframe(performance_summary, use_container_width=True, hide_index=True)

def render_data_explorer(df, COLORS):
    st.header("Data Explorer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'SOURCE_SHEET' in df.columns:
            source_options = df['SOURCE_SHEET'].unique().tolist()
            sources = st.multiselect(
                "Filter by Source", 
                source_options,
                default=source_options,
                key="data_explorer_sources"
            )
        else:
            sources = []
    
    with col2:
        if 'CATEGORY' in df.columns:
            category_options = df['CATEGORY'].unique().tolist()
            categories = st.multiselect(
                "Filter by Category", 
                category_options,
                default=category_options,
                key="data_explorer_categories"
            )
        else:
            categories = []
    
    # Apply filters
    filtered_df = df.copy()
    if sources and 'SOURCE_SHEET' in df.columns:
        filtered_df = filtered_df[filtered_df['SOURCE_SHEET'].isin(sources)]
    if categories and 'CATEGORY' in df.columns:
        filtered_df = filtered_df[filtered_df['CATEGORY'].isin(categories)]
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} records")
    st.dataframe(filtered_df, use_container_width=True)
    
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download CSV", csv, "data.csv", "text/csv")

if __name__ == "__main__":
    main()