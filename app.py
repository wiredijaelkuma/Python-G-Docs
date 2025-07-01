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

# Heat map colors - light to dark blue
HEAT_COLORS = ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3', '#1E88E5', '#1976D2']

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
        st.image(os.path.join(ASSETS_DIR, "banner.png"), use_container_width=True)
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
        render_agents(df, COLORS, HEAT_COLORS)
    
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
    subtabs = st.tabs(["📅 Weekly", "📆 Monthly"])
    
    with subtabs[0]:
        render_weekly_dashboard(sales_df, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_monthly_dashboard(sales_df, COLORS, HEAT_COLORS)

def render_weekly_dashboard(sales_df, COLORS, HEAT_COLORS):
    st.subheader("📅 Weekly Analysis")
    
    # Date range for weeks
    min_date = sales_df['ENROLLED_DATE'].min().date()
    max_date = sales_df['ENROLLED_DATE'].max().date()
    
    # Week selection with date picker
    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input(
            "Select Week Starting Date:",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        # Calculate week range
        week_start = pd.Timestamp(selected_date)
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
                st.plotly_chart(fig, use_container_width=True)

def render_monthly_dashboard(sales_df, COLORS, HEAT_COLORS):
    st.subheader("📆 Monthly Analysis")
    
    # Month selection
    sales_df['Month'] = sales_df['ENROLLED_DATE'].dt.to_period('M')
    available_months = sorted(sales_df['Month'].unique(), reverse=True)
    
    if not available_months:
        st.warning("No monthly data available")
        return
    
    # Month picker using selectbox with formatted options
    month_options = [m.strftime('%B %Y') for m in available_months]
    selected_month_str = st.selectbox("Select Month:", month_options)
    selected_month = available_months[month_options.index(selected_month_str)]
    
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
    
    # Monthly charts
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
                st.plotly_chart(fig, use_container_width=True)

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

if __name__ == "__main__":
    main()