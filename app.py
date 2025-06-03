# PEPE'S POWER SALES DASHBOARD - DATA-DRIVEN VERSION
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import base64
import os
from io import BytesIO
import calendar

# --- Constants ---
BACKGROUND_IMAGE = "assets/pepe-background.png"
BANNER_IMAGE = "assets/pepe-sunset-banner.png"
LOGO_IMAGE = "assets/pepe-rocket.png"

# --- Helper Functions ---
@st.cache_data
def load_image_base64(path):
    """Load image and convert to base64 with error handling"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    st.warning(f"Image not found: {path}")
    return None

@st.cache_data
def load_data():
    """Load and preprocess data with robust error handling"""
    try:
        df = pd.read_csv("processed_combined_data.csv")
        
        # Standardize column names
        df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]
        
        # Convert date column
        if 'ENROLLED_DATE' in df.columns:
            df['ENROLLED_DATE'] = pd.to_datetime(df['ENROLLED_DATE'], errors='coerce')
        
        # Clean and standardize status
        if 'STATUS' in df.columns:
            df['STATUS'] = df['STATUS'].astype(str).str.strip().str.upper()
            
            # Create status category
            active_terms = ["ACTIVE", "ENROLLED", "ENROLLED / ACTIVE"]
            nsf_terms = ["NSF"]
            cancelled_terms = ["CANCELLED", "DROPPED", "PENDING CANCELLATION", "SUMMONS: PUSH OUT", "NEEDS ROL"]
            
            df['CATEGORY'] = np.select(
                [
                    df['STATUS'].isin(active_terms),
                    df['STATUS'].isin(nsf_terms),
                    df['STATUS'].isin(cancelled_terms)
                ],
                ['ACTIVE', 'NSF', 'CANCELLED'],
                default='OTHER'
            )
        
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def generate_agent_report(agent_df, agent_name):
    """Generate professional PDF agent report"""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Agent Performance Report: {agent_name}", ln=True, align='C')
    pdf.ln(10)
    
    # Summary Stats
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Performance Summary", ln=True)
    pdf.set_font("Arial", '', 10)
    
    total = len(agent_df)
    active = len(agent_df[agent_df['CATEGORY'] == 'ACTIVE'])
    nsf = len(agent_df[agent_df['CATEGORY'] == 'NSF'])
    cancelled = len(agent_df[agent_df['CATEGORY'] == 'CANCELLED'])
    success_rate = (active / total * 100) if total > 0 else 0
    
    stats = [
        f"Total Contracts: {total}",
        f"Active Contracts: {active}",
        f"NSF Cases: {nsf}",
        f"Cancelled Contracts: {cancelled}",
        f"Success Rate: {success_rate:.1f}%"
    ]
    
    for stat in stats:
        pdf.cell(0, 8, stat, ln=True)
    
    # Create table
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Recent Contracts", ln=True)
    
    # Table header
    cols = ['CUSTOMER_ID', 'ENROLLED_DATE', 'STATUS', 'SOURCE_SHEET']
    col_widths = [40, 40, 40, 70]
    
    pdf.set_font("Arial", 'B', 10)
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 8, col, border=1)
    pdf.ln()
    
    # Table rows
    pdf.set_font("Arial", '', 9)
    for _, row in agent_df.head(15).iterrows():
        pdf.cell(col_widths[0], 8, str(row.get('CUSTOMER_ID', '')), border=1)
        # Safely get the date and format it
        enrolled_date_str = ''
        if pd.notnull(row.get('ENROLLED_DATE')):
            # Ensure it's a Timestamp, then format it to 'YYYY-MM-DD'
            if isinstance(row['ENROLLED_DATE'], pd.Timestamp):
                enrolled_date_str = row['ENROLLED_DATE'].strftime('%Y-%m-%d')
            else:
                # Fallback if it's somehow not a Timestamp but still present
                enrolled_date_str = str(row['ENROLLED_DATE'])[:10] # Keep the slice if it's already a string-like object
        
        pdf.cell(col_widths[1], 8, enrolled_date_str, border=1)
        pdf.cell(col_widths[2], 8, str(row.get('STATUS', ''))[:15], border=1)
        pdf.cell(col_widths[3], 8, str(row.get('SOURCE_SHEET', ''))[:25], border=1)
        pdf.ln()
    
    # Save to bytes buffer
    pdf_content_bytes = pdf.output(dest='S').encode('latin1')
    pdf_bytes = BytesIO(pdf_content_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes

def create_status_gauge(active, nsf, cancelled, total):
    """Create gauge chart for status distribution"""
    fig = go.Figure()
    
    if total > 0:
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=active,
            title={'text': "Active Contracts"},
            domain={'x': [0, 0.3], 'y': [0.6, 1]},
            gauge={'axis': {'range': [0, total]}, 'bar': {'color': "green"}}
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=nsf,
            title={'text': "NSF Cases"},
            domain={'x': [0.35, 0.65], 'y': [0.6, 1]},
            gauge={'axis': {'range': [0, total]}, 'bar': {'color': "orange"}}
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=cancelled,
            title={'text': "Cancelled Contracts"},
            domain={'x': [0.7, 1], 'y': [0.6, 1]},
            gauge={'axis': {'range': [0, total]}, 'bar': {'color': "red"}}
        ))
    
    fig.update_layout(
        height=300,
        margin=dict(t=50, b=10),
        grid={'rows': 1, 'columns': 3, 'pattern': "independent"}
    )
    return fig

def format_large_number(num):
    """Format large numbers with commas"""
    return f"{num:,}"

def get_current_week_date_range():
    """Get the date range for the current week (Monday to Sunday)"""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    return start_of_week, end_of_week

def get_week_date_range(week_date):
    """Get the full week date range (Monday to Sunday) given a date in that week"""
    # Ensure week_date is a datetime.date object
    if isinstance(week_date, pd.Timestamp):
        week_date = week_date.date()
    elif isinstance(week_date, str):
        week_date = pd.to_datetime(week_date).date()
    
    # Calculate Monday (start) of the week
    start_of_week = week_date - timedelta(days=week_date.weekday())
    # Calculate Sunday (end) of the week
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

# --- UI Configuration ---
st.set_page_config(
    layout="wide", 
    page_title="Pepe's Power Dashboard", 
    page_icon="🐸",
    initial_sidebar_state="expanded"
)

# --- Load Assets ---
bg_img_base64 = load_image_base64(BACKGROUND_IMAGE)
banner_img_base64 = load_image_base64(BANNER_IMAGE)

# --- Custom CSS ---
st.markdown(f"""
<style>
    div.stApp {{
        background: url("data:image/png;base64,{bg_img_base64}") center center fixed;
        background-size: cover;
    }}
    .main-container {{
        background-color: rgba(0, 0, 0, 0.85) !important;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.8);
        color: #f1f1f1;
        margin-bottom: 2rem;
    }}
    .banner-container {{
        position: sticky;
        top: 0;
        z-index: 1000;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #4CAF50;
    }}
    .metric-card {{
        background-color: rgba(40, 40, 40, 0.7);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        transition: transform 0.3s;
    }}
    .metric-card:hover {{
        transform: translateY(-5px);
        background-color: rgba(50, 50, 50, 0.8);
    }}
    .metric-title {{
        font-size: 1rem;
        color: #a5d6a7;
        margin-bottom: 5px;
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: bold;
        color: #4CAF50;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 10px 20px;
        border-radius: 8px !important;
        background-color: rgba(30, 30, 30, 0.7) !important;
        transition: all 0.3s;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #4CAF50 !important;
        color: white !important;
    }}
    footer {{visibility: hidden;}}
    .highlight-active {{ background-color: rgba(76, 175, 80, 0.2) !important; }}
    .highlight-nsf {{ background-color: rgba(255, 165, 0, 0.2) !important; }}
    .highlight-cancelled {{ background-color: rgba(255, 99, 71, 0.2) !important; }}
</style>
""", unsafe_allow_html=True)

# --- Banner ---
if banner_img_base64:
    st.markdown(f"""
    <div class="banner-container">
        <img src="data:image/png;base64,{banner_img_base64}" style="width:100%; border-radius:0 0 10px 10px;"/>
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image(LOGO_IMAGE, width=200)
    st.title("Dashboard Controls")
    
    # Date Range Selector
    st.subheader("Date Range")
    today = datetime.now().date()
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
    
    # Source Filter
    st.subheader("Data Source")
    all_sources = st.checkbox("All Sources", True)
    sources = st.multiselect("Select sources:", ["PAC- Raw", "MLG- Raw", "ELP- Raw", "Cordoba- Raw"])

# --- Data Loading ---
with st.spinner("🔍 Loading data..."):
    df, load_err = load_data()
    
if load_err:
    st.error(f"🚨 Data Load Error: {load_err}")
    st.stop()
    
if df.empty:
    st.warning("⚠️ No data available with current filters")
    st.stop()

# --- Data Processing ---
# Apply date filter
if 'ENROLLED_DATE' in df.columns:
    df = df[(df['ENROLLED_DATE'].dt.date >= start) & (df['ENROLLED_DATE'].dt.date <= end)]

# Apply status filter
status_filter = []
if show_active: status_filter.append('ACTIVE')
if show_nsf: status_filter.append('NSF')
if show_cancelled: status_filter.append('CANCELLED')
if show_other: status_filter.append('OTHER')
df = df[df['CATEGORY'].isin(status_filter)]

# Apply source filter
if 'SOURCE_SHEET' in df.columns and not all_sources and sources:
    df = df[df['SOURCE_SHEET'].isin(sources)]

# Categorization
df['MONTH_YEAR'] = df['ENROLLED_DATE'].dt.to_period('M').astype(str)
df['WEEK'] = df['ENROLLED_DATE'].dt.isocalendar().week
df['YEAR'] = df['ENROLLED_DATE'].dt.isocalendar().year
df['WEEK_YEAR'] = df['YEAR'].astype(str) + '-W' + df['WEEK'].astype(str).str.zfill(2)
df['DAY_OF_WEEK'] = df['ENROLLED_DATE'].dt.day_name()

# --- Dashboard Header ---
st.title("Pepe's Power Sales Dashboard")
st.markdown(f"""
<div class="main-container">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <b>Date Range:</b> {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}<br>
            <b>Total Contracts:</b> {format_large_number(len(df))}
        </div>
        <div>
            <b>Status Shown:</b> {', '.join(status_filter)}<br>
            <b>Data Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Metrics Summary ---
active_df = df[df['CATEGORY'] == 'ACTIVE']
nsf_df = df[df['CATEGORY'] == 'NSF']
cancelled_df = df[df['CATEGORY'] == 'CANCELLED']
other_df = df[df['CATEGORY'] == 'OTHER']

total_contracts = len(df)
active_contracts = len(active_df)
nsf_cases = len(nsf_df)
cancelled_contracts = len(cancelled_df)
other_statuses = len(other_df)

success_rate = (active_contracts / total_contracts * 100) if total_contracts > 0 else 0

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
        <div class="metric-title">Active Contracts</div>
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

# --- Tab Interface ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "📈 Performance Trends", 
    "🧑 Agent Analytics", 
    "🔍 Data Explorer", 
    "🚨 Risk Analysis"
])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Contract Status Distribution")
        fig = create_status_gauge(active_contracts, nsf_cases, cancelled_contracts, total_contracts)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Top Performing Agents")
        if 'AGENT' in df.columns:
            agent_stats = df.groupby('AGENT').agg(
                Total=('CUSTOMER_ID', 'count'),
                Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
                Success_Rate=('CATEGORY', lambda x: (x == 'ACTIVE').mean() * 100)
            )
            agent_stats = agent_stats.sort_values('Total', ascending=False).head(10)
            fig = px.bar(
                agent_stats.reset_index(),
                x='AGENT',
                y=['Active', 'Total'],
                title="Top Agents by Contract Volume",
                labels={'value': 'Contract Count', 'variable': 'Status'},
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True, key="top_agents_bar_chart")
            
        # --- Weekly Active Sales for Top Performers ---
        st.subheader("Weekly Active Sales for Top Performers")
        if 'ENROLLED_DATE' in df.columns and 'AGENT' in df.columns:
            # Filter for active contracts only
            active_df_weekly = df[df['CATEGORY'] == 'ACTIVE'].copy()
            
            # Get current week's date range (Monday to Sunday)
            current_week_start, current_week_end = get_current_week_date_range()
            
            # Create a proper week identifier that includes year to avoid confusion between years
            active_df_weekly['WEEK_START_DATE'] = active_df_weekly['ENROLLED_DATE'].apply(
                lambda x: x.date() - timedelta(days=x.weekday())
            )
            
            # Group by week start date and agent
            weekly_agent_performance = active_df_weekly.groupby([
                'WEEK_START_DATE', 'AGENT'
            ]).size().reset_index(name='Active_Contracts')
            
            # Create a user-friendly week string (e.g., "YYYY-MM-DD to YYYY-MM-DD")
            weekly_agent_performance['WEEK_DISPLAY'] = weekly_agent_performance['WEEK_START_DATE'].apply(
                lambda x: f"{x.strftime('%Y-%m-%d')} to {(x + timedelta(days=6)).strftime('%Y-%m-%d')}"
            )
            
            # Sort by week start date in descending order
            weekly_agent_performance = weekly_agent_performance.sort_values('WEEK_START_DATE', ascending=False)
            
            # Get all unique display weeks for the dropdown, maintaining the sorted order
            all_weeks_display = weekly_agent_performance['WEEK_DISPLAY'].unique()
            
            if len(all_weeks_display) > 0:
                # Allow user to select a week
                selected_week_display = st.selectbox("Select Week:", all_weeks_display, key="weekly_sales_selectbox")
                
                # Extract the week start date from the selected display string
                selected_week_start_str = selected_week_display.split(" to ")[0]
                selected_week_start = datetime.strptime(selected_week_start_str, '%Y-%m-%d').date()
                
                # Filter data for the selected week
                selected_week_data = weekly_agent_performance[
                    weekly_agent_performance['WEEK_START_DATE'] == selected_week_start
                ]
                
                # Sort by Active_Contracts for the selected week
                selected_week_data = selected_week_data.sort_values(by='Active_Contracts', ascending=False)
                
                # Display top performers for the selected week
                top_agents_selected_week = selected_week_data.head(10)
                
                if not top_agents_selected_week.empty:
                    fig = px.bar(
                        top_agents_selected_week,
                        x='AGENT',
                        y='Active_Contracts',
                        title=f"Top 10 Active Contracts for {selected_week_display}",
                        labels={'AGENT': 'Agent', 'Active_Contracts': 'Active Contracts'},
                        color='Active_Contracts',
                        color_continuous_scale=px.colors.sequential.Greens
                    )
                    fig.update_layout(xaxis_title="Agent", yaxis_title="Active Contracts")
                    st.plotly_chart(fig, use_container_width=True, key="weekly_active_sales_chart")
                else:
                    st.info(f"No active contracts for top performers in the week of {selected_week_display}.")
            else:
                st.info("No weekly active sales data available.")
        else:
            st.warning("Enrollment date or Agent data not available for weekly sales analysis.")
        
    with col2:
        st.subheader("Enrollment Timeline")
        if 'ENROLLED_DATE' in df.columns:
            timeline_df = df.set_index('ENROLLED_DATE').resample('D').size().reset_index(name='Count')
            fig = px.line(
                timeline_df, 
                x='ENROLLED_DATE', 
                y='Count', 
                title="Daily Contract Enrollment",
                labels={'ENROLLED_DATE': 'Date', 'Count': 'Contracts'}
            )
            fig.update_xaxes(rangeslider_visible=True)
            st.plotly_chart(fig, use_container_width=True, key="enrollment_timeline_chart")
            
            st.subheader("Status by Source")
            if 'SOURCE_SHEET' in df.columns:
                source_status = df.groupby(['SOURCE_SHEET', 'CATEGORY']).size().unstack(fill_value=0)
                fig = px.bar(
                    source_status.reset_index(),
                    x='SOURCE_SHEET',
                    y=source_status.columns,
                    title="Contract Status by Source",
                    labels={'value': 'Count', 'variable': 'Status'},
                    barmode='stack'
                )
                st.plotly_chart(fig, use_container_width=True, key="status_by_source_chart")
            else:
                st.warning("Source data not available")

with tab2:
    st.subheader("Monthly Performance Trends")
    
    if 'ENROLLED_DATE' in df.columns:
        monthly_data = df.groupby(['MONTH_YEAR', 'CATEGORY']).size().unstack(fill_value=0).reset_index()
        columns_to_sum = [col for col in ['ACTIVE', 'NSF', 'CANCELLED', 'OTHER'] if col in monthly_data.columns]
        total_monthly_contracts = monthly_data[columns_to_sum].sum(axis=1)
        monthly_data['Success_Rate'] = (monthly_data['ACTIVE'] / total_monthly_contracts) * 100
        monthly_data['Success_Rate'] = monthly_data['Success_Rate'].fillna(0)
        
        fig = px.line(
            monthly_data,
            x='MONTH_YEAR',
            y='Success_Rate',
            title="Monthly Success Rate Trend",
            labels={'MONTH_YEAR': 'Month', 'Success_Rate': 'Success Rate (%)'}
        )
        st.plotly_chart(fig, use_container_width=True, key="monthly_success_rate_chart")
             
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Contract Status Over Time")
            fig = px.area(
                monthly_data,
                x='MONTH_YEAR',
                y=['ACTIVE', 'NSF', 'CANCELLED'],
                title="Contract Status Distribution Over Time",
                labels={'value': 'Contract Count', 'variable': 'Status'}
            )
            st.plotly_chart(fig, use_container_width=True, key="status_over_time_area_chart")
        
        with col2:
            st.subheader("Weekly Performance")
            # Use WEEK_YEAR instead of just WEEK to avoid confusion between years
            weekly_data = df.groupby(['WEEK_YEAR', 'CATEGORY']).size().unstack(fill_value=0).reset_index()
            # Calculate total by summing only numeric columns
            numeric_columns = weekly_data.select_dtypes(include=['number']).columns
            weekly_data['Total'] = weekly_data[numeric_columns].sum(axis=1)

            # Safely calculate success rate
            if 'ACTIVE' in weekly_data.columns and 'Total' in weekly_data.columns:
                weekly_data['Success_Rate'] = weekly_data['ACTIVE'].div(weekly_data['Total']).fillna(0) * 100
            else:
                weekly_data['Success_Rate'] = 0
                            
            fig = px.line(
                weekly_data,
                x='WEEK_YEAR',
                y='Success_Rate',
                title="Weekly Success Rate",
                labels={'WEEK_YEAR': 'Week', 'Success_Rate': 'Success Rate (%)'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True, key="weekly_success_rate_chart")

with tab3:
    st.subheader("Agent Performance Analytics")
    
    if 'AGENT' not in df.columns:
        st.warning("No 'AGENT' column found in dataset.")
    else:
        agents = df['AGENT'].dropna().unique()
        selected_agent = st.selectbox("Select agent:", sorted(agents))
        
        agent_df = df[df['AGENT'] == selected_agent]
        agent_active = agent_df[agent_df['CATEGORY'] == 'ACTIVE']
        agent_nsf = agent_df[agent_df['CATEGORY'] == 'NSF']
        agent_cancelled = agent_df[agent_df['CATEGORY'] == 'CANCELLED']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Contracts", len(agent_df))
        col2.metric("Active", len(agent_active))
        col3.metric("NSF", len(agent_nsf))
        col4.metric("Cancelled", len(agent_cancelled))
        col5.metric("Success Rate", f"{(len(agent_active)/len(agent_df)*100):.1f}%" if len(agent_df) > 0 else "N/A")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Agent's Status Distribution")
            status_counts = agent_df['CATEGORY'].value_counts()
            fig = px.pie(
                status_counts, 
                values=status_counts.values, 
                names=status_counts.index,
                hole=0.4,
                title=f"Status Distribution for {selected_agent}"
            )
            st.plotly_chart(fig, use_container_width=True, key=f"agent_status_pie_{selected_agent}")
        
        with col2:
            st.subheader("Performance Timeline")
            if 'ENROLLED_DATE' in agent_df.columns:
                agent_timeline = agent_df.set_index('ENROLLED_DATE').resample('W').size()
                fig = px.line(
                    agent_timeline.reset_index(),
                    x='ENROLLED_DATE',
                    y=0,
                    title="Weekly Contract Volume",
                    labels={'ENROLLED_DATE': 'Date', '0': 'Contracts'}
                )
                st.plotly_chart(fig, use_container_width=True, key=f"agent_timeline_chart_{selected_agent}")
        
        # Generate and download report
        st.subheader("Contract Details")
        st.dataframe(agent_df, use_container_width=True)
        
        # Enhanced PDF report
        pdf_bytes = generate_agent_report(agent_df, selected_agent)
        st.download_button(
            label="📄 Download Agent Report",
            data=pdf_bytes,
            file_name=f"{selected_agent}_performance_report.pdf",
            mime="application/pdf"
        )

with tab4:
    st.subheader("Data Exploration")
    
    # Column selection
    default_cols = ['CUSTOMER_ID', 'AGENT', 'ENROLLED_DATE', 'STATUS', 'CATEGORY', 'SOURCE_SHEET']
    available_cols = [col for col in df.columns if col in default_cols] or df.columns.tolist()
    selected_cols = st.multiselect("Select columns:", df.columns.tolist(), default=available_cols)
    
    if selected_cols:
        # Status-based highlighting
        def highlight_status(row):
            if row['CATEGORY'] == 'ACTIVE':
                return ['background-color: rgba(76, 175, 80, 0.2)'] * len(row)
            elif row['CATEGORY'] == 'NSF':
                return ['background-color: rgba(255, 165, 0, 0.2)'] * len(row)
            elif row['CATEGORY'] == 'CANCELLED':
                return ['background-color: rgba(255, 99, 71, 0.2)'] * len(row)
            return [''] * len(row)
        
        styled_df = df[selected_cols].style.apply(highlight_status, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # Export options
        st.subheader("Export Data")
        export_format = st.radio("Select format:", ["CSV", "Excel"])
        filename = f"pepe_sales_data_{start}_{end}"
        
        if export_format == "CSV":
            csv = df[selected_cols].to_csv(index=False).encode()
            st.download_button("📤 Download CSV", csv, file_name=f"{filename}.csv")
        else:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df[selected_cols].to_excel(writer, index=False)
            st.download_button("📤 Download Excel", excel_buffer.getvalue(), file_name=f"{filename}.xlsx")
    else:
        st.warning("Please select at least one column to display")

with tab5:
    st.subheader("Risk Analysis")
    
    flagged = df[df['CATEGORY'].isin(["NSF", "CANCELLED", "OTHER"])]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cancellation Reasons")
        if 'STATUS' in flagged.columns:
            status_counts = flagged['STATUS'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.bar(
                status_counts, 
                x='Status', 
                y='Count',
                title="Cancellation Reasons",
                color='Count',
                color_continuous_scale='OrRd'
            )
            st.plotly_chart(fig, use_container_width=True, key="cancellation_reasons_chart")
    
    with col2:
        st.subheader("Agents with Most Issues")
        if 'AGENT' in flagged.columns:
            agent_issues = flagged.groupby('AGENT').size().reset_index(name='Issue_Count')
            agent_issues = agent_issues.sort_values('Issue_Count', ascending=False).head(10)
            fig = px.bar(
                agent_issues,
                x='AGENT',
                y='Issue_Count',
                title="Top Agents by Issue Count",
                color='Issue_Count',
                color_continuous_scale='OrRd'
            )
            st.plotly_chart(fig, use_container_width=True, key="agents_with_issues_chart")
    
    st.subheader("Problem Contracts")
    st.dataframe(flagged, use_container_width=True)
    
    # Export flagged data
    csv_flagged = flagged.to_csv(index=False).encode()
    st.download_button("📤 Download Risk Data", csv_flagged, file_name="risk_contracts.csv")

# --- Footer ---
st.markdown("---")
st.caption(f"© 2025 Pepe's Power Solutions | Dashboard v2.2 | Data updated {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- Notifications ---
st.toast("Dashboard loaded successfully!", icon="🐸")
