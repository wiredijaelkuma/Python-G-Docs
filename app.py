# PEPE'S POWER SALES DASHBOARD - DATA-DRIVEN VERSION
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import base64
from io import BytesIO
import calendar
from pathlib import Path

# --- Set page configuration first (must be the first Streamlit command) ---
st.set_page_config(
    layout="wide", 
    page_title="Pepe's Power Dashboard", 
    page_icon="🐸",
    initial_sidebar_state="expanded"
)

# --- Constants ---
# Define asset paths correctly for Streamlit Cloud
ASSETS_DIR = Path("assets")
BACKGROUND_IMAGE = ASSETS_DIR / "pepe-background.png"
BANNER_IMAGE = ASSETS_DIR / "pepe-sunset-banner.png"
LOGO_IMAGE = ASSETS_DIR / "pepe-rocket.png"

# --- Helper Functions ---
@st.cache_data
def load_image_base64(path):
    """Load image and convert to base64 with error handling"""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        st.warning(f"Image not found: {path}. Error: {e}")
        return None

@st.cache_data
def load_data():
    """Load and preprocess data with robust error handling"""
    try:
        # First try to load from the processed file
        try:
            df = pd.read_csv("processed_combined_data.csv")
        except:
            # If that fails, try to load from uploaded file
            uploaded_file = st.session_state.get('uploaded_file', None)
            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
            else:
                st.error("No data file found. Please upload a CSV file.")
                return pd.DataFrame(), "No data file found"
        
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
            nsf_terms = ["NSF", "ENROLLED / NSF PROBLEM"]
            cancelled_terms = ["CANCELLED", "DROPPED", "PENDING CANCELLATION", "SUMMONS: PUSH OUT", "NEEDS ROL"]
            
            # Use vectorized operations for better performance
            df['CATEGORY'] = 'OTHER'  # default value
            mask_active = df['STATUS'].str.contains('|'.join(active_terms), case=False, regex=True, na=False)
            mask_nsf = df['STATUS'].str.contains('|'.join(nsf_terms), case=False, regex=True, na=False)
            mask_cancelled = df['STATUS'].str.contains('|'.join(cancelled_terms), case=False, regex=True, na=False)
            
            df.loc[mask_active, 'CATEGORY'] = 'ACTIVE'
            df.loc[mask_nsf, 'CATEGORY'] = 'NSF'
            df.loc[mask_cancelled, 'CATEGORY'] = 'CANCELLED'
        
        # Add derived columns for analysis
        if 'ENROLLED_DATE' in df.columns:
            df['MONTH_YEAR'] = df['ENROLLED_DATE'].dt.strftime('%Y-%m')
            df['WEEK'] = df['ENROLLED_DATE'].dt.isocalendar().week
            df['YEAR'] = df['ENROLLED_DATE'].dt.isocalendar().year
            df['WEEK_YEAR'] = df['YEAR'].astype(str) + '-W' + df['WEEK'].astype(str).str.zfill(2)
            df['DAY_OF_WEEK'] = df['ENROLLED_DATE'].dt.day_name()
            
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def generate_agent_report_excel(agent_df, agent_name):
    """Generate professional Excel agent report"""
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Summary sheet
        summary_data = {
            'Metric': [
                'Total Contracts',
                'Active Contracts',
                'NSF Cases',
                'Cancelled Contracts',
                'Success Rate (%)'
            ],
            'Value': [
                len(agent_df),
                len(agent_df[agent_df['CATEGORY'] == 'ACTIVE']),
                len(agent_df[agent_df['CATEGORY'] == 'NSF']),
                len(agent_df[agent_df['CATEGORY'] == 'CANCELLED']),
                (len(agent_df[agent_df['CATEGORY'] == 'ACTIVE']) / len(agent_df) * 100) if len(agent_df) > 0 else 0
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Format the summary sheet
        workbook = writer.book
        summary_sheet = writer.sheets['Summary']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4CAF50',
            'color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1
        })
        
        # Apply formats
        for col_num, value in enumerate(summary_df.columns.values):
            summary_sheet.write(0, col_num, value, header_format)
        
        # Write the data with cell format
        for row_num in range(len(summary_df)):
            for col_num in range(len(summary_df.columns)):
                if col_num == 1 and row_num == 4:  # Format success rate as percentage
                    summary_sheet.write(row_num + 1, col_num, summary_df.iloc[row_num, col_num] / 100, 
                                      workbook.add_format({'border': 1, 'num_format': '0.0%'}))
                else:
                    summary_sheet.write(row_num + 1, col_num, summary_df.iloc[row_num, col_num], cell_format)
        
        # Contract details sheet
        agent_df.to_excel(writer, sheet_name='Contract Details', index=False)
        
        # Format the contract details sheet
        details_sheet = writer.sheets['Contract Details']
        
        # Apply header format
        for col_num, value in enumerate(agent_df.columns.values):
            details_sheet.write(0, col_num, value, header_format)
        
        # Auto-fit columns
        for i, col in enumerate(agent_df.columns):
            column_len = max(agent_df[col].astype(str).str.len().max(), len(col)) + 2
            details_sheet.set_column(i, i, column_len)
    
    buffer.seek(0)
    return buffer

@st.cache_data
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

# --- File Uploader in Sidebar for Data Source ---
with st.sidebar:
    # Try to display the logo image with fallback
    try:
        st.image(str(LOGO_IMAGE), width=200)
    except:
        st.title("🚀 Pepe's Power")
    
    # Data source section - only show this if no data is loaded yet
    if 'df' not in st.session_state:
        st.header("Data Source")
        uploaded_file = st.file_uploader("Upload processed data CSV", type=["csv"])
        if uploaded_file is not None:
            st.session_state['uploaded_file'] = uploaded_file
            st.success("✅ File uploaded successfully!")

# --- Load Assets ---
bg_img_base64 = load_image_base64(BACKGROUND_IMAGE)
banner_img_base64 = load_image_base64(BANNER_IMAGE)

# --- Custom CSS ---
if bg_img_base64:
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
else:
    # Fallback CSS without background image
    st.markdown("""
    <style>
        div.stApp {
            background-color: #121212;
        }
        .main-container {
            background-color: rgba(0, 0, 0, 0.85) !important;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.8);
            color: #f1f1f1;
            margin-bottom: 2rem;
        }
        .banner-container {
            position: sticky;
            top: 0;
            z-index: 1000;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid #4CAF50;
        }
        .metric-card {
            background-color: rgba(40, 40, 40, 0.7);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transition: transform 0.3s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            background-color: rgba(50, 50, 50, 0.8);
        }
        .metric-title {
            font-size: 1rem;
            color: #a5d6a7;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #4CAF50;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            border-radius: 8px !important;
            background-color: rgba(30, 30, 30, 0.7) !important;
            transition: all 0.3s;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4CAF50 !important;
            color: white !important;
        }
        footer {visibility: hidden;}
        .highlight-active { background-color: rgba(76, 175, 80, 0.2) !important; }
        .highlight-nsf { background-color: rgba(255, 165, 0, 0.2) !important; }
        .highlight-cancelled { background-color: rgba(255, 99, 71, 0.2) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Banner ---
if banner_img_base64:
    st.markdown(f"""
    <div class="banner-container">
        <img src="data:image/png;base64,{banner_img_base64}" style="width:100%; border-radius:0 0 10px 10px;"/>
    </div>
    """, unsafe_allow_html=True)

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
    st.title("Dashboard Controls")
    
    # Date Range Selector
    st.subheader("Date Range")
    today = datetime.now().date()
    min_date = df['ENROLLED_DATE'].min().date() if 'ENROLLED_DATE' in df.columns else date(2024, 10, 1)
    max_date = df['ENROLLED_DATE'].max().date() if 'ENROLLED_DATE' in df.columns else today
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
    if 'SOURCE_SHEET' in df.columns:
        all_sources = st.checkbox("All Sources", True)
        if not all_sources:
            sources = st.multiselect("Select sources:", df['SOURCE_SHEET'].unique())
        else:
            sources = df['SOURCE_SHEET'].unique().tolist()
    else:
        all_sources = True
        sources = []

# --- Apply Filters ---
# Apply date filter
if 'ENROLLED_DATE' in df.columns:
    df_filtered = df[(df['ENROLLED_DATE'].dt.date >= start) & (df['ENROLLED_DATE'].dt.date <= end)]
else:
    df_filtered = df

# Apply status filter
status_filter = []
if show_active: status_filter.append('ACTIVE')
if show_nsf: status_filter.append('NSF')
if show_cancelled: status_filter.append('CANCELLED')
if show_other: status_filter.append('OTHER')
df_filtered = df_filtered[df_filtered['CATEGORY'].isin(status_filter)]

# Apply source filter
if 'SOURCE_SHEET' in df_filtered.columns and not all_sources:
    df_filtered = df_filtered[df_filtered['SOURCE_SHEET'].isin(sources)]

# --- Dashboard Header ---
st.title("Pepe's Power Sales Dashboard")
st.markdown(f"""
<div class="main-container">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <b>Date Range:</b> {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}<br>
            <b>Total Contracts:</b> {format_large_number(len(df_filtered))}
        </div>
        <div>
            <b>Status Shown:</b> {', '.join(status_filter)}<br>
            <b>Data Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Metrics Summary ---
active_df = df_filtered[df_filtered['CATEGORY'] == 'ACTIVE']
nsf_df = df_filtered[df_filtered['CATEGORY'] == 'NSF']
cancelled_df = df_filtered[df_filtered['CATEGORY'] == 'CANCELLED']
other_df = df_filtered[df_filtered['CATEGORY'] == 'OTHER']

total_contracts = len(df_filtered)
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

# --- Overview Tab ---
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Contract Status Distribution")
        fig = create_status_gauge(active_contracts, nsf_cases, cancelled_contracts, total_contracts)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Top Performing Agents")
        if 'AGENT' in df_filtered.columns:
            agent_stats = df_filtered.groupby('AGENT').agg(
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
            st.plotly_chart(fig, use_container_width=True)
            
        # --- Weekly Active Sales for Top Performers ---
        st.subheader("Weekly Active Sales for Top Performers")
        if 'ENROLLED_DATE' in df_filtered.columns and 'AGENT' in df_filtered.columns:
            try:
                # Filter for active contracts only
                active_df_weekly = df_filtered[df_filtered['CATEGORY'] == 'ACTIVE'].copy()
                
                # Create a week identifier
                active_df_weekly['WEEK_START_DATE'] = active_df_weekly['ENROLLED_DATE'].apply(
                    lambda x: x.date() - timedelta(days=x.weekday())
                )
                
                # Group by week start date and agent
                weekly_agent_performance = active_df_weekly.groupby([
                    'WEEK_START_DATE', 'AGENT'
                ]).size().reset_index(name='Active_Contracts')
                
                # Create a user-friendly week string
                weekly_agent_performance['WEEK_DISPLAY'] = weekly_agent_performance['WEEK_START_DATE'].apply(
                    lambda x: f"{x.strftime('%Y-%m-%d')} to {(x + timedelta(days=6)).strftime('%Y-%m-%d')}"
                )
                
                # Sort by week start date in descending order
                weekly_agent_performance = weekly_agent_performance.sort_values('WEEK_START_DATE', ascending=False)
                
                # Get all unique display weeks for the dropdown
                all_weeks_display = weekly_agent_performance['WEEK_DISPLAY'].unique()
                
                if len(all_weeks_display) > 0:
                    # Allow user to select a week
                    selected_week_display = st.selectbox("Select Week:", all_weeks_display)
                    
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
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No active contracts for top performers in the week of {selected_week_display}.")
                else:
                    st.info("No weekly active sales data available.")
            except Exception as e:
                st.error(f"Error in weekly active sales analysis: {e}")
                st.info("Could not generate weekly active sales data.")
        else:
            st.warning("Enrollment date or Agent data not available for weekly sales analysis.")
        
    with col2:
        st.subheader("Enrollment Timeline")
        if 'ENROLLED_DATE' in df_filtered.columns:
            try:
                timeline_df = df_filtered.set_index('ENROLLED_DATE').resample('D').size().reset_index(name='Count')
                fig = px.line(
                    timeline_df, 
                    x='ENROLLED_DATE', 
                    y='Count', 
                    title="Daily Contract Enrollment",
                    labels={'ENROLLED_DATE': 'Date', 'Count': 'Contracts'}
                )
                fig.update_xaxes(rangeslider_visible=True)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating enrollment timeline: {e}")
                st.info("Could not generate enrollment timeline.")
            
            st.subheader("Status by Source")
            if 'SOURCE_SHEET' in df_filtered.columns:
                try:
                    source_status = df_filtered.groupby(['SOURCE_SHEET', 'CATEGORY']).size().unstack(fill_value=0)
                    fig = px.bar(
                        source_status.reset_index(),
                        x='SOURCE_SHEET',
                        y=source_status.columns,
                        title="Contract Status by Source",
                        labels={'value': 'Count', 'variable': 'Status'},
                        barmode='stack'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating source status chart: {e}")
                    st.info("Could not generate source status chart.")
            else:
                st.warning("Source data not available")

# --- Performance Trends Tab ---
with tab2:
    st.subheader("Monthly Performance Trends")
    
    if 'ENROLLED_DATE' in df_filtered.columns:
        try:
            # Create monthly data with status breakdown
            monthly_data = df_filtered.groupby(['MONTH_YEAR', 'CATEGORY']).size().unstack(fill_value=0).reset_index()
            
            # Ensure all status columns exist
            for status in ['ACTIVE', 'NSF', 'CANCELLED', 'OTHER']:
                if status not in monthly_data.columns:
                    monthly_data[status] = 0
            
            # Calculate total contracts and success rate
            monthly_data['Total'] = monthly_data['ACTIVE'] + monthly_data['NSF'] + monthly_data['CANCELLED'] + monthly_data['OTHER']
            monthly_data['Success_Rate'] = (monthly_data['ACTIVE'] / monthly_data['Total']) * 100
            
            # Sort by month-year
            monthly_data['Sort_Key'] = pd.to_datetime(monthly_data['MONTH_YEAR'] + '-01')
            monthly_data = monthly_data.sort_values('Sort_Key')
            
            fig = px.line(
                monthly_data,
                x='MONTH_YEAR',
                y='Success_Rate',
                title="Monthly Success Rate Trend",
                labels={'MONTH_YEAR': 'Month', 'Success_Rate': 'Success Rate (%)'},
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
                 
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Contract Status Over Time")
                try:
                    fig = px.area(
                        monthly_data,
                        x='MONTH_YEAR',
                        y=['ACTIVE', 'NSF', 'CANCELLED', 'OTHER'],
                        title="Contract Status Distribution Over Time",
                        labels={'value': 'Contract Count', 'variable': 'Status'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating status over time chart: {e}")
                    st.info("Could not generate status over time chart.")
            
            with col2:
                st.subheader("Weekly Performance")
                try:
                    # Use a simpler approach for weekly data
                    weekly_df = df_filtered.copy()
                    weekly_df['Week'] = weekly_df['ENROLLED_DATE'].dt.strftime('%Y-W%U')
                    weekly_counts = weekly_df.groupby(['Week', 'CATEGORY']).size().reset_index(name='Count')
                    
                    # Create a pivot table
                    weekly_pivot = weekly_counts.pivot(index='Week', columns='CATEGORY', values='Count').fillna(0)
                    
                    # Ensure all status columns exist
                    for status in ['ACTIVE', 'NSF', 'CANCELLED', 'OTHER']:
                        if status not in weekly_pivot.columns:
                            weekly_pivot[status] = 0
                            
                    # Calculate success rate
                    weekly_pivot['Total'] = weekly_pivot.sum(axis=1)
                    weekly_pivot['Success_Rate'] = (weekly_pivot['ACTIVE'] / weekly_pivot['Total'] * 100)
                    
                    # Create the chart
                    fig = px.line(
                        weekly_pivot.reset_index(),
                        x='Week',
                        y='Success_Rate',
                        title="Weekly Success Rate",
                        labels={'Week': 'Week', 'Success_Rate': 'Success Rate (%)'},
                        markers=True
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating weekly performance chart: {e}")
                    st.info("Weekly performance data not available.")
        except Exception as e:
            st.error(f"Error in performance trends analysis: {e}")
            st.info("Could not generate performance trends.")
    else:
        st.warning("Enrollment date data not available for performance trends analysis.")

# --- Agent Analytics Tab ---
with tab3:
    st.subheader("Agent Performance Analytics")
    
    if 'AGENT' not in df_filtered.columns:
        st.warning("No 'AGENT' column found in dataset.")
    else:
        try:
            agents = df_filtered['AGENT'].dropna().unique()
            selected_agent = st.selectbox("Select agent:", sorted(agents))
            
            agent_df = df_filtered[df_filtered['AGENT'] == selected_agent]
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
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Performance Timeline")
                if 'ENROLLED_DATE' in agent_df.columns:
                    try:
                        agent_timeline = agent_df.set_index('ENROLLED_DATE').resample('W').size().reset_index(name='Contracts')
                        fig = px.line(
                            agent_timeline,
                            x='ENROLLED_DATE',
                            y='Contracts',
                            title="Weekly Contract Volume",
                            labels={'ENROLLED_DATE': 'Date', 'Contracts': 'Contracts'},
                            markers=True
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error generating agent timeline: {e}")
                        st.info("Could not generate agent timeline.")
            
            # Generate and download report
            st.subheader("Contract Details")
            st.dataframe(agent_df.sort_values('ENROLLED_DATE', ascending=False), use_container_width=True)
            
            # Excel report
            try:
                excel_bytes = generate_agent_report_excel(agent_df, selected_agent)
                st.download_button(
                    label="📊 Download Agent Report (Excel)",
                    data=excel_bytes,
                    file_name=f"{selected_agent}_performance_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error generating Excel report: {e}")
                st.info("Could not generate Excel report.")
        except Exception as e:
            st.error(f"Error in agent analytics: {e}")
            st.info("Could not load agent analytics.")

# --- Data Explorer Tab ---
with tab4:
    st.subheader("Data Exploration")
    
    try:
        # Column selection
        default_cols = ['CUSTOMER_ID', 'AGENT', 'ENROLLED_DATE', 'STATUS', 'CATEGORY', 'SOURCE_SHEET']
        available_cols = [col for col in df_filtered.columns if col in default_cols] or df_filtered.columns.tolist()
        selected_cols = st.multiselect("Select columns:", df_filtered.columns.tolist(), default=available_cols)
        
        if selected_cols:
            # Filter options
            st.subheader("Additional Filters")
            
            # Agent filter for data explorer
            if 'AGENT' in selected_cols:
                agent_filter = st.multiselect(
                    "Filter by Agent:", 
                    options=["All"] + sorted(df_filtered['AGENT'].unique().tolist()),
                    default=["All"]
                )
                
                if "All" not in agent_filter:
                    df_explorer = df_filtered[df_filtered['AGENT'].isin(agent_filter)]
                else:
                    df_explorer = df_filtered
            else:
                df_explorer = df_filtered
            
            # Display data with conditional formatting
            st.subheader("Filtered Data")
            
            # Display dataframe without styling (more compatible)
            st.dataframe(df_explorer[selected_cols], use_container_width=True)
            
            # Export options
            st.subheader("Export Data")
            export_format = st.radio("Select format:", ["CSV", "Excel"])
            filename = f"pepe_sales_data_{start}_{end}"
            
            if export_format == "CSV":
                csv = df_explorer[selected_cols].to_csv(index=False).encode()
                st.download_button("📤 Download CSV", csv, file_name=f"{filename}.csv", mime="text/csv")
            else:
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df_explorer[selected_cols].to_excel(writer, index=False)
                excel_buffer.seek(0)
                st.download_button("📤 Download Excel", excel_buffer, file_name=f"{filename}.xlsx", 
                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("Please select at least one column to display")
    except Exception as e:
        st.error(f"Error in data explorer: {e}")
        st.info("Could not load data explorer.")

# --- Risk Analysis Tab ---
with tab5:
    st.subheader("Risk Analysis")
    
    try:
        # Filter for problematic contracts
        flagged = df_filtered[df_filtered['CATEGORY'].isin(["NSF", "CANCELLED", "OTHER"])]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Cancellation Reasons")
            if 'STATUS' in flagged.columns and not flagged.empty:
                try:
                    # Get top 10 status reasons
                    status_counts = flagged['STATUS'].value_counts().head(10).reset_index()
                    status_counts.columns = ['Status', 'Count']
                    fig = px.bar(
                        status_counts, 
                        x='Status', 
                        y='Count',
                        title="Top Cancellation Reasons",
                        color='Count',
                        color_continuous_scale='OrRd'
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating cancellation reasons chart: {e}")
                    st.info("Could not generate cancellation reasons chart.")
            else:
                st.info("No cancellation data available.")
        
        with col2:
            st.subheader("Agents with Most Issues")
            if 'AGENT' in flagged.columns and not flagged.empty:
                try:
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
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating agents with issues chart: {e}")
                    st.info("Could not generate agents with issues chart.")
            else:
                st.info("No agent issue data available.")
        
        # Risk analysis by time
        st.subheader("Risk Trends Over Time")
        if 'ENROLLED_DATE' in flagged.columns and not flagged.empty:
            try:
                # Monthly risk trend - using 'ME' instead of 'M' to avoid deprecation warning
                monthly_risk = flagged.set_index('ENROLLED_DATE').resample('ME').size().reset_index(name='Issues')
                monthly_risk['Month'] = monthly_risk['ENROLLED_DATE'].dt.strftime('%Y-%m')
                
                fig = px.line(
                    monthly_risk,
                    x='Month',
                    y='Issues',
                    title="Monthly Issue Volume",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating risk trends chart: {e}")
                st.info("Could not generate risk trends chart.")
        else:
            st.info("No time-based risk data available.")
        
        st.subheader("Problem Contracts")
        if not flagged.empty:
            st.dataframe(flagged.sort_values('ENROLLED_DATE', ascending=False), use_container_width=True)
            
            # Export flagged data
            csv_flagged = flagged.to_csv(index=False).encode()
            st.download_button("📤 Download Risk Data", csv_flagged, file_name="risk_contracts.csv", mime="text/csv")
        else:
            st.info("No problem contracts found in the selected data.")
    except Exception as e:
        st.error(f"Error in risk analysis: {e}")
        st.info("Could not load risk analysis.")

# --- Footer ---
st.markdown("---")
st.caption(f"© 2025 Pepe's Power Solutions | Dashboard v2.5 | Data updated {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- Notifications ---
st.toast("Dashboard loaded successfully!", icon="🐸")
