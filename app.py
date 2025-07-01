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
    
    /* Clean tabs */
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
    
    /* Date inputs */
    .stDateInput > div > div > input {
        font-size: 16px;
        padding: 12px;
        border: 2px solid #4A90E2;
        border-radius: 8px;
    }
    
    /* Selectbox - Fixed styling */
    .stSelectbox label {
        font-size: 16px;
        font-weight: 600;
        color: #343A40;
    }
    
    .stSelectbox > div > div {
        font-size: 16px;
        padding: 12px;
        border: 2px solid #4A90E2;
        border-radius: 8px;
        background: white;
        color: #343A40;
    }
    
    .stSelectbox div[data-baseweb="select"] {
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
        from modules.agent_analysis import render_agent_analysis
        render_agent_analysis(df, COLORS, HEAT_COLORS)
    
    with tabs[2]:
        render_commission(df, COLORS, HEAT_COLORS)
    
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
        render_weekly_dashboard(sales_df, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_monthly_dashboard(sales_df, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        render_trends_dashboard(sales_df, COLORS, HEAT_COLORS)

def render_trends_dashboard(sales_df, COLORS, HEAT_COLORS):
    st.subheader("📈 Performance Trends")
    
    # Time range selector - FIXED
    time_options = ["Last 30 Days", "Last 60 Days", "Last 90 Days", "Last 180 Days"]
    time_range = st.selectbox(
        "Select Time Range:",
        options=time_options,
        index=2,
        key="trends_time_selector"
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
        # Calculate growth (compare first half vs second half)
        mid_date = start_date + (end_date - start_date) / 2
        first_half = len(trend_data[trend_data['ENROLLED_DATE'] < mid_date])
        second_half = len(trend_data[trend_data['ENROLLED_DATE'] >= mid_date])
        growth = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        st.metric("Sales Growth", f"{growth:+.1f}%")
    
    with col3:
        if 'AGENT' in trend_data.columns:
            avg_per_agent = len(trend_data) / trend_data['AGENT'].nunique() if trend_data['AGENT'].nunique() > 0 else 0
            efficiency = min(avg_per_agent * 10, 100)  # Scale to percentage
            st.metric("Team Efficiency", f"{efficiency:.1f}%")
    
    with col4:
        if 'CATEGORY' in trend_data.columns:
            conversion_rate = (len(trend_data[trend_data['CATEGORY'] == 'ACTIVE']) / len(trend_data) * 100) if len(trend_data) > 0 else 0
            st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales Velocity")
        # Weekly sales over time
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
            # Agent stick rates
            agent_performance = trend_data.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'ACTIVE').sum()
            }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Active'})
            
            # Calculate weighted stick rate (considers both rate and volume)
            agent_performance['Stick_Rate'] = (agent_performance['Active'] / agent_performance['Total'] * 100).round(1)
            agent_performance['Volume_Weight'] = (agent_performance['Total'] / agent_performance['Total'].max() * 100).round(1)
            agent_performance['Weighted_Score'] = (agent_performance['Stick_Rate'] * 0.7 + agent_performance['Volume_Weight'] * 0.3).round(1)
            
            # Filter agents with minimum activity and sort by weighted score
            agent_performance = agent_performance[agent_performance['Total'] >= 3]  # Min 3 sales
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

def render_weekly_dashboard(sales_df, COLORS, HEAT_COLORS):
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
            max_value=max_date
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
    
    # Charts
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

def render_monthly_dashboard(sales_df, COLORS, HEAT_COLORS):
    st.subheader("📆 Monthly Analysis")
    
    # Month selection
    sales_df['Month'] = sales_df['ENROLLED_DATE'].dt.to_period('M')
    available_months = sorted(sales_df['Month'].unique(), reverse=True)
    
    if not available_months:
        st.warning("No monthly data available")
        return
    
    selected_month_date = st.date_input(
        "Select Any Date in Month:",
        value=available_months[0].start_time.date(),
        min_value=available_months[-1].start_time.date(),
        max_value=available_months[0].start_time.date()
    )
    
    selected_month = pd.Timestamp(selected_month_date).to_period('M')
    selected_month_str = selected_month.strftime('%B %Y')
    
    # Filter data for selected month
    month_data = sales_df[sales_df['Month'] == selected_month].copy()
    
    # Monthly metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", len(month_data))
    
    with col2:
        if 'CATEGORY' in month_data.columns:
            active_count = len(month_data[month_data['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_count / len(month_data) * 100) if len(month_data) > 0 else 0
            st.metric("Active Rate", f"{active_rate:.1f}%")
    
    with col3:
        if 'AGENT' in month_data.columns:
            avg_per_agent = len(month_data) / month_data['AGENT'].nunique() if month_data['AGENT'].nunique() > 0 else 0
            st.metric("Avg per Agent", f"{avg_per_agent:.1f}")
    
    with col4:
        weeks_in_month = len(month_data.groupby(month_data['ENROLLED_DATE'].dt.isocalendar().week))
        weekly_avg = len(month_data) / weeks_in_month if weeks_in_month > 0 else 0
        st.metric("Weekly Average", f"{weekly_avg:.1f}")

def render_commission(df, COLORS, HEAT_COLORS):
    st.header("Commission Dashboard")
    
    if 'SOURCE_SHEET' not in df.columns or 'Comission' not in df['SOURCE_SHEET'].values:
        st.warning("No commission data found")
        return
    
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy()
    
    if commission_df.empty:
        st.warning("Commission data is empty")
        return
    
    st.success(f"Commission data loaded: {len(commission_df)} records")
    
    # Commission metrics with enhanced processing
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Payments", len(commission_df))
    
    with col2:
        if 'CATEGORY' in commission_df.columns:
            cleared_count = len(commission_df[commission_df['CATEGORY'] == 'CLEARED'])
            st.metric("Cleared Payments", cleared_count)
    
    with col3:
        if 'CATEGORY' in commission_df.columns:
            pending_count = len(commission_df[commission_df['CATEGORY'] == 'PENDING'])
            st.metric("Pending Payments", pending_count)
    
    with col4:
        if 'AGENT' in commission_df.columns:
            st.metric("Unique Agents", commission_df['AGENT'].nunique())
    
    # Enhanced commission analysis
    if 'CATEGORY' in commission_df.columns:
        st.subheader("Payment Status Distribution")
        status_counts = commission_df['CATEGORY'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Commission Payment Status",
            color_discrete_map={
                'CLEARED': COLORS['success'],
                'PENDING': COLORS['warning'],
                'NSF': COLORS['danger'],
                'OTHER': COLORS['info']
            }
        )
        st.plotly_chart(fig, use_container_width=True)

def render_data_explorer(df, COLORS):
    st.header("Data Explorer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'SOURCE_SHEET' in df.columns:
            source_options = df['SOURCE_SHEET'].unique().tolist()
            sources = st.multiselect(
                "Filter by Source", 
                options=source_options,
                default=source_options
            )
        else:
            sources = []
    
    with col2:
        if 'CATEGORY' in df.columns:
            category_options = df['CATEGORY'].unique().tolist()
            categories = st.multiselect(
                "Filter by Category", 
                options=category_options,
                default=category_options
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