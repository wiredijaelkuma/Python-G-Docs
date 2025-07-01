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
    
    /* Selectbox */
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
    
    # Detailed Data
    with st.expander("📋 Detailed Weekly Data"):
        display_cols = ['ENROLLED_DATE', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in week_data.columns]
        
        if available_cols:
            display_df = week_data[available_cols].copy()
            if 'ENROLLED_DATE' in display_df.columns:
                display_df['ENROLLED_DATE'] = display_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                f"📥 Download Week Data",
                csv,
                f"weekly_data_{week_start.strftime('%Y%m%d')}.csv",
                "text/csv"
            )

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
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Daily Trend")
        daily_sales = month_data.groupby(month_data['ENROLLED_DATE'].dt.date).size().reset_index()
        daily_sales.columns = ['Date', 'Sales']
        
        if not daily_sales.empty:
            fig = px.line(
                daily_sales,
                x='Date',
                y='Sales',
                title=f"Daily Sales - {selected_month_str}",
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'AGENT' in month_data.columns:
            st.subheader("Top Monthly Performers")
            if 'CATEGORY' in month_data.columns:
                monthly_agents = month_data[month_data['CATEGORY'] == 'ACTIVE']['AGENT'].value_counts().head(10)
            else:
                monthly_agents = month_data['AGENT'].value_counts().head(10)
            
            if not monthly_agents.empty:
                fig = px.bar(
                    monthly_agents.head(5),
                    x=monthly_agents.head(5).index,
                    y=monthly_agents.head(5).values,
                    title="Top 5 Agents (Active Sales)",
                    color=monthly_agents.head(5).values,
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weekly Breakdown")
        month_data['Week_of_Month'] = month_data['ENROLLED_DATE'].dt.isocalendar().week
        weekly_breakdown = month_data.groupby('Week_of_Month').size().reset_index()
        weekly_breakdown.columns = ['Week', 'Sales']
        weekly_breakdown['Week'] = 'Week ' + weekly_breakdown['Week'].astype(str)
        
        if not weekly_breakdown.empty:
            fig = px.bar(
                weekly_breakdown,
                x='Week',
                y='Sales',
                title=f"Weekly Distribution - {selected_month_str}",
                color='Sales',
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'SOURCE_SHEET' in month_data.columns and 'CATEGORY' in month_data.columns:
            st.subheader("Source Performance")
            source_breakdown = month_data.groupby(['SOURCE_SHEET', 'CATEGORY']).size().unstack(fill_value=0)
            
            if not source_breakdown.empty:
                fig = px.bar(
                    source_breakdown,
                    title=f"Source Breakdown - {selected_month_str}",
                    color_discrete_map={
                        'ACTIVE': COLORS['success'],
                        'CANCELLED': COLORS['danger'],
                        'NSF': COLORS['warning'],
                        'OTHER': COLORS['info']
                    }
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Monthly Agent Performance Table
    st.subheader("📋 Monthly Agent Performance")
    if 'AGENT' in month_data.columns and 'CATEGORY' in month_data.columns:
        monthly_agent_summary = month_data.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        monthly_agent_summary.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
        monthly_agent_summary['Active_Rate'] = (monthly_agent_summary['Active_Sales'] / monthly_agent_summary['Total_Sales'] * 100).round(1)
        monthly_agent_summary = monthly_agent_summary.sort_values('Active_Sales', ascending=False).reset_index()
        
        st.dataframe(monthly_agent_summary, use_container_width=True, hide_index=True)
    
    # Detailed Monthly Data
    with st.expander("📋 Detailed Monthly Data"):
        display_cols = ['ENROLLED_DATE', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in month_data.columns]
        
        if available_cols:
            display_df = month_data[available_cols].copy()
            if 'ENROLLED_DATE' in display_df.columns:
                display_df['ENROLLED_DATE'] = display_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                f"📥 Download Monthly Data",
                csv,
                f"monthly_data_{selected_month.strftime('%Y_%m')}.csv",
                "text/csv"
            )

def render_agents(df, COLORS, HEAT_COLORS):
    st.header("Agent Performance")
    
    if 'AGENT' not in df.columns:
        st.warning("No agent data available")
        return
    
    agents = df['AGENT'].dropna().unique()
    selected_agent = st.selectbox("Select Agent", ['All Agents'] + list(agents))
    
    if selected_agent == 'All Agents':
        agent_df = df
    else:
        agent_df = df[df['AGENT'] == selected_agent]
    
    # Agent metrics
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
            st.metric("Cancelled", cancelled_count)
    
    with col4:
        if 'CATEGORY' in agent_df.columns:
            nsf_count = len(agent_df[agent_df['CATEGORY'] == 'NSF'])
            st.metric("NSF", nsf_count)

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
    
    # Commission metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Payments", len(commission_df))
    
    with col2:
        if 'STATUS' in commission_df.columns:
            cleared_count = len(commission_df[commission_df['STATUS'].str.contains('Cleared', na=False)])
            st.metric("Cleared Payments", cleared_count)
    
    with col3:
        if 'AGENT' in commission_df.columns:
            st.metric("Unique Agents", commission_df['AGENT'].nunique())

def render_data_explorer(df, COLORS):
    st.header("Data Explorer")
    
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
    st.dataframe(filtered_df, use_container_width=True)
    
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download CSV", csv, "data.csv", "text/csv")

def render_trends_dashboard(sales_df, COLORS, HEAT_COLORS):
    st.subheader("📈 Performance Trends")
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range:", 
        ["Last 30 Days", "Last 60 Days", "Last 90 Days", "Last 180 Days"],
        index=2,  # Default to Last 90 Days
        key="trends_time_range"
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
    
    # Charts row 1
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
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weekly vs Monthly Comparison")
        # Compare weekly and monthly averages
        weekly_avg = trend_data.groupby(trend_data['ENROLLED_DATE'].dt.to_period('W')).size().mean()
        monthly_avg = trend_data.groupby(trend_data['ENROLLED_DATE'].dt.to_period('M')).size().mean()
        
        comparison_data = pd.DataFrame({
            'Period': ['Weekly Average', 'Monthly Average'],
            'Sales': [weekly_avg, monthly_avg * 4]  # Scale monthly to 4 weeks
        })
        
        fig = px.bar(
            comparison_data,
            x='Period',
            y='Sales',
            title="Weekly vs Monthly Performance",
            color='Sales',
            color_continuous_scale=HEAT_COLORS
        )
        fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Source Performance Trends")
        if 'SOURCE_SHEET' in trend_data.columns and 'CATEGORY' in trend_data.columns:
            source_performance = trend_data.groupby('SOURCE_SHEET').agg({
                'SOURCE_SHEET': 'count',
                'CATEGORY': lambda x: (x == 'ACTIVE').sum()
            }).rename(columns={'SOURCE_SHEET': 'Total', 'CATEGORY': 'Active'})
            
            source_performance['Active_Rate'] = (source_performance['Active'] / source_performance['Total'] * 100).round(1)
            
            fig = px.bar(
                source_performance,
                x=source_performance.index,
                y='Active_Rate',
                title="Source Active Rates",
                color='Active_Rate',
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    # Performance Tables
    st.subheader("📋 Top Performers by Stick Rate")
    if 'AGENT' in trend_data.columns and 'CATEGORY' in trend_data.columns:
        detailed_performance = trend_data.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        detailed_performance.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
        detailed_performance['Stick_Rate'] = (detailed_performance['Active_Sales'] / detailed_performance['Total_Sales'] * 100).round(1)
        detailed_performance['Volume_Weight'] = (detailed_performance['Total_Sales'] / detailed_performance['Total_Sales'].max() * 100).round(1)
        detailed_performance['Weighted_Score'] = (detailed_performance['Stick_Rate'] * 0.7 + detailed_performance['Volume_Weight'] * 0.3).round(1)
        detailed_performance['Performance_Rank'] = detailed_performance['Weighted_Score'].rank(ascending=False, method='dense').astype(int)
        
        # Filter agents with minimum activity
        qualified_agents = detailed_performance[detailed_performance['Total_Sales'] >= 3]
        qualified_agents = qualified_agents.sort_values('Weighted_Score', ascending=False).reset_index()
        
        st.dataframe(qualified_agents, use_container_width=True, hide_index=True)
    
    # Trend Analysis Summary
    with st.expander("📈 Detailed Trend Analysis"):
        display_cols = ['ENROLLED_DATE', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in trend_data.columns]
        
        if available_cols:
            display_df = trend_data[available_cols].copy()
            if 'ENROLLED_DATE' in display_df.columns:
                display_df['ENROLLED_DATE'] = display_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                f"📅 Download Trend Data ({time_range})",
                csv,
                f"trend_analysis_{time_range.lower().replace(' ', '_')}.csv",
                "text/csv"
            )

if __name__ == "__main__":
    main()