import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.gsheet_connector import fetch_data_from_sheet
import base64
import os

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

def get_background_image():
    """Get base64 encoded background image"""
    try:
        with open(os.path.join(ASSETS_DIR, "wallpaper-pepe-cash.jpg"), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

def load_css():
    bg_image = get_background_image()
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        font-size: 18px;
        font-weight: 600;
        padding: 12px 24px;
        border-radius: 8px;
        margin: 0 4px;
        background: rgba(255, 255, 255, 0.9);
    }}
    
    .stTabs [aria-selected="true"] {{
        background: #4A90E2;
        color: white;
    }}
    
    .stSelectbox > div > div {{
        font-size: 16px;
        padding: 12px;
        border: 2px solid #4A90E2;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.9);
        color: #343A40;
    }}
    
    .main .block-container {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 2rem;
        margin-top: 1rem;
    }}
    </style>
    """, unsafe_allow_html=True)

def main():
    load_css()
    
    # Banner
    try:
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
        st.markdown("**Google Sheet:** [Forth Py](https://docs.google.com/spreadsheets/d/1p6b1FzANAyPHdH6BQkGFkoqhp0K2D1E5fdcgNLurRk4/edit?usp=sharing)")

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
        from modules.commission_clean import render_commission_analysis
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