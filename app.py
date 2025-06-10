# PEPE'S POWER SALES DASHBOARD - SIMPLIFIED VERSION
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

# Load custom CSS with beautiful periwinkle gradient styling
with open('assets/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- Constants ---
# Simplified asset paths
ASSETS_DIR = Path("assets")

# --- Color Palette ---
# Periwinkle purples and opaque greens
COLORS = {
    'primary': '#8A7FBA',      # Periwinkle purple
    'secondary': '#6A5ACD',    # Slateblue
    'accent': '#7FFFD4',       # Aquamarine
    'light_accent': '#AFFFEE', # Light aquamarine
    'dark_accent': '#40E0D0',  # Turquoise
    'warning': '#FFD700',      # Gold
    'danger': '#FF6347',       # Tomato
    'light': '#F0F8FF',        # Alice blue
    'dark': '#483D8B',         # Dark slate blue
    'background': '#F8F9FA',   # Light gray background
    'text': '#2E2E2E',         # Near black
    'light_purple': '#E6E6FA', # Lavender
    'med_purple': '#B39DDB',   # Medium purple
    'light_green': '#98FB98',  # Pale green
    'med_green': '#66CDAA',    # Medium aquamarine
}

# --- Helper Functions ---
# Removed unused load_image_base64 function

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load and preprocess data with robust error handling"""
    try:
        # Try to load from the processed file
        try:
            df = pd.read_csv("processed_combined_data.csv")
            
            # Get file modification time for data freshness indicator
            try:
                import os
                data_modified = os.path.getmtime("processed_combined_data.csv")
                st.session_state['data_modified'] = datetime.fromtimestamp(data_modified).strftime('%Y-%m-%d %H:%M')
                data_age = (datetime.now() - datetime.fromtimestamp(data_modified)).total_seconds() / 3600
                st.session_state['data_freshness'] = "✅ Fresh" if data_age < 24 else "⚠️ Outdated"
            except:
                st.session_state['data_modified'] = "Unknown"
                st.session_state['data_freshness'] = "❓ Unknown"
                
        except:
            # If that fails, try to load from uploaded file
            uploaded_file = st.session_state.get('uploaded_file', None)
            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
                st.session_state['data_modified'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                st.session_state['data_freshness'] = "✅ Fresh (Uploaded)"
            else:
                st.error("No data file found. Please upload a CSV file.")
                return pd.DataFrame(), "No data file found"
        
        # Standardize column names
        df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]
        
        # Convert date column
        if 'ENROLLED_DATE' in df.columns:
            df['ENROLLED_DATE'] = pd.to_datetime(df['ENROLLED_DATE'], errors='coerce')
        
        # Clean and standardize status - improved logic for better categorization
        if 'STATUS' in df.columns:
            df['STATUS'] = df['STATUS'].astype(str).str.strip().str.upper()
            
            # Create status category with more comprehensive terms
            active_terms = ["ACTIVE", "ENROLLED", "ENROLLED / ACTIVE", "ENROLLED/ACTIVE"]
            nsf_terms = ["NSF", "ENROLLED / NSF PROBLEM", "ENROLLED/NSF", "NSF PROBLEM"]
            cancelled_terms = ["CANCELLED", "DROPPED", "PENDING CANCELLATION", "SUMMONS: PUSH OUT", "NEEDS ROL", "TERMINATED"]
            
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
            'bg_color': COLORS['primary'],
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
            title={'text': "Active Contracts", 'font': {'color': COLORS['text'], 'size': 24}},
            domain={'x': [0, 0.3], 'y': [0.6, 1]},
            gauge={
                'axis': {'range': [0, total], 'tickfont': {'color': COLORS['text']}},
                'bar': {'color': COLORS['med_green']},
                'bgcolor': COLORS['light_green'],
                'bordercolor': COLORS['dark_accent'],
                'borderwidth': 2,
            },
            number={'font': {'color': COLORS['text'], 'size': 30}}
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=nsf,
            title={'text': "NSF Cases", 'font': {'color': COLORS['text'], 'size': 24}},
            domain={'x': [0.35, 0.65], 'y': [0.6, 1]},
            gauge={
                'axis': {'range': [0, total], 'tickfont': {'color': COLORS['text']}},
                'bar': {'color': COLORS['warning']},
                'bgcolor': 'rgba(255, 215, 0, 0.2)',
                'bordercolor': COLORS['dark_accent'],
                'borderwidth': 2,
            },
            number={'font': {'color': COLORS['text'], 'size': 30}}
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=cancelled,
            title={'text': "Cancelled Contracts", 'font': {'color': COLORS['text'], 'size': 24}},
            domain={'x': [0.7, 1], 'y': [0.6, 1]},
            gauge={
                'axis': {'range': [0, total], 'tickfont': {'color': COLORS['text']}},
                'bar': {'color': COLORS['danger']},
                'bgcolor': 'rgba(255, 99, 71, 0.2)',
                'bordercolor': COLORS['dark_accent'],
                'borderwidth': 2,
            },
            number={'font': {'color': COLORS['text'], 'size': 30}}
        ))
    
    fig.update_layout(
        height=350,
        margin=dict(t=50, b=10),
        grid={'rows': 1, 'columns': 3, 'pattern': "independent"},
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font={'color': COLORS['text']},
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

# --- Custom CSS ---
st.markdown(f"""
<style>
    /* Modern color scheme with periwinkle and greens */
    :root {{
        --primary: {COLORS['primary']};
        --secondary: {COLORS['secondary']};
        --accent: {COLORS['accent']};
        --light-accent: {COLORS['light_accent']};
        --dark-accent: {COLORS['dark_accent']};
        --warning: {COLORS['warning']};
        --danger: {COLORS['danger']};
        --light: {COLORS['light']};
        --dark: {COLORS['dark']};
        --background: {COLORS['background']};
        --text: {COLORS['text']};
        --light-purple: {COLORS['light_purple']};
        --med-purple: {COLORS['med_purple']};
        --light-green: {COLORS['light_green']};
        --med-green: {COLORS['med_green']};
    }}
    
    /* Main containers - background already set by gradient */
    div.stApp {{
        /* Background is set by the gradient above */
    }}
    
    /* Add semi-transparent backgrounds for better readability with background image */
    div.stTabs, div.chart-box, div.metric-card, div[data-testid="stSidebarContent"] {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
    }}
    
    /* Tab styling - BIGGER TABS */
    .stTabs {{
        background-color: var(--light-purple);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 2rem;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px;
        padding: 0 10px;
        background-color: var(--light-purple);
        border-radius: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 16px 30px !important;
        border-radius: 10px !important;
        background-color: var(--background) !important;
        transition: all 0.2s;
        font-size: 20px !important;
        font-weight: 500;
        height: auto !important;
        border: 2px solid var(--primary) !important;
        color: var(--dark) !important;
        min-width: 180px;
        text-align: center;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: var(--primary) !important;
        color: white !important;
        font-weight: 600;
        box-shadow: 0 4px 8px rgba(138, 127, 186, 0.4);
    }}
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
        background-color: var(--med-purple) !important;
        color: white !important;
    }}
    
    /* Metrics styling */
    .metric-card {{
        background-color: var(--light-purple);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(138, 127, 186, 0.2);
        transition: transform 0.2s, box-shadow 0.2s;
        border-left: 5px solid var(--primary);
        margin-bottom: 20px;
    }}
    .metric-title {{
        font-size: 1.1rem;
        color: var(--dark);
        margin-bottom: 8px;
        font-weight: 600;
    }}
    .metric-value {{
        font-size: 2rem;
        font-weight: bold;
        color: var(--secondary);
    }}
    
    /* Chart styling */
    .chart-box {{
        background-color: var(--background);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid var(--light-purple);
        box-shadow: 0 2px 6px rgba(138, 127, 186, 0.1);
    }}
    
    /* Dropdown/selectbox styling */
    .stSelectbox [data-baseweb="select"] {{
        border-radius: 10px !important;
        height: 50px !important;
        font-size: 18px !important;
        border: 2px solid var(--primary) !important;
    }}
    .stMultiSelect [data-baseweb="select"] {{
        border-radius: 10px !important;
        min-height: 50px !important;
        font-size: 18px !important;
        border: 2px solid var(--primary) !important;
    }}
    
    /* Section headers */
    .section-header {{
        color: var(--dark);
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid var(--accent);
    }}
    
    /* Buttons */
    .stButton button {{
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        transition: all 0.2s;
        font-size: 16px !important;
    }}
    .stButton button:hover {{
        background-color: var(--secondary) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(138, 127, 186, 0.4);
    }}
</style>
""", unsafe_allow_html=True)

# --- File Uploader in Sidebar for Data Source ---
with st.sidebar:
    # Display the Pepe muscle icon
    try:
        st.image("assets/pepe-muscle.jpg", width=180)
    except:
        st.title("🐸 Pepe's Power")
    
    # Add refresh data button with improved functionality
    if st.button("🔄 Refresh Data", key="refresh_button", use_container_width=True):
        # Clear all cached data to ensure fresh load
        st.cache_data.clear()
        # Add a success message
        st.sidebar.success("✅ Data refreshed successfully!")
        # Force reload
        st.experimental_rerun()
    
    # Data source section - only show this if no data is loaded yet
    if 'df' not in st.session_state:
        st.header("Data Source")
        uploaded_file = st.file_uploader("Upload processed data CSV", type=["csv"])
        if uploaded_file is not None:
            st.session_state['uploaded_file'] = uploaded_file
            st.success("✅ File uploaded successfully!")

# No need to load assets as base64 anymore

# --- Banner ---
try:
    st.image("assets/banner.png", use_column_width=True)
except:
    st.title("Pepe's Power Dashboard")

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
    st.markdown(f"""
    <div class="section-header">Dashboard Controls</div>
    """, unsafe_allow_html=True)
    
    # Date Range Selector
    st.subheader("Date Range")
    today = datetime.now().date()
    min_date = df['ENROLLED_DATE'].min().date() if 'ENROLLED_DATE' in df.columns else date(2024, 10, 1)
    # Always allow selection up to today regardless of data
    max_date = max(df['ENROLLED_DATE'].max().date() if 'ENROLLED_DATE' in df.columns else date(2024, 10, 1), today)
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
st.markdown(f"""
<div class="section-header">Pepe's Power Sales Dashboard</div>
<div style="background-color: {COLORS['light_purple']}; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <b>Date Range:</b> {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}<br>
            <b>Total Contracts:</b> {format_large_number(len(df_filtered))}
        </div>
        <div>
            <b>Status Shown:</b> {', '.join(status_filter)}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Removed data quality check to simplify UI

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
    <div class="metric-card" style="border-left: 5px solid {COLORS['med_green']};">
        <div class="metric-title">Active Contracts</div>
        <div class="metric-value" style="color: {COLORS['med_green']};">{format_large_number(active_contracts)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {COLORS['warning']};">
        <div class="metric-title">NSF Cases</div>
        <div class="metric-value" style="color: {COLORS['warning']};">{format_large_number(nsf_cases)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {COLORS['danger']};">
        <div class="metric-title">Cancelled</div>
        <div class="metric-value" style="color: {COLORS['danger']};">{format_large_number(cancelled_contracts)}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {COLORS['dark_accent']};">
        <div class="metric-title">Success Rate</div>
        <div class="metric-value" style="color: {COLORS['dark_accent']};">{success_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# --- Tab Interface ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "📈 Performance", 
    "🧑 Agents", 
    "🔍 Data Explorer", 
    "🚨 Risk Analysis"
])

# --- Overview Tab ---
with tab1:
    st.markdown(f"""
    <div class="chart-box">
    <h3>Contract Status Distribution</h3>
    """, unsafe_allow_html=True)
    
    fig = create_status_gauge(active_contracts, nsf_cases, cancelled_contracts, total_contracts)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    </div>
    """, unsafe_allow_html=True)
    
    # Weekly Active Sales for Top Performers - with improved logic
    st.markdown(f"""
    <div class="chart-box">
    <h3>Weekly Active Sales for Top Performers</h3>
    """, unsafe_allow_html=True)
    
    if 'ENROLLED_DATE' in df_filtered.columns and 'AGENT' in df_filtered.columns:
        try:
            # Filter for active contracts only - using the CATEGORY field for proper filtering
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
                # Allow user to select a week with larger dropdown
                selected_week_display = st.selectbox("Select Week:", all_weeks_display, key="weekly_sales_week_selector")
                
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
                    # Add a toggle to show all agents or just top 10
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        show_all = st.checkbox("Show all agents", False, key="show_all_agents_weekly")
                    with col2:
                        st.markdown(f"""
                        <div style="background-color: {COLORS['light_purple']}; padding: 10px; border-radius: 10px; margin-top: 4px;">
                            <b>Active Contracts Only:</b> This chart shows only ACTIVE status contracts, not cancelled or NSF
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Highlight the top performer
                    top_performer = top_agents_selected_week.iloc[0]['AGENT']
                    top_performer_count = top_agents_selected_week.iloc[0]['Active_Contracts']
                    
                    st.markdown(f"""
                    <div class="top-performer">
                        <b>🏆 Top Performer:</b> {top_performer} with {top_performer_count} active contracts this week
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if show_all:
                        display_data = selected_week_data
                        title_text = f"All Agents Active Contracts for {selected_week_display}"
                    else:
                        display_data = top_agents_selected_week
                        title_text = f"Top 10 Active Contracts for {selected_week_display}"
                    
                    fig = px.bar(
                        display_data,
                        x='AGENT',
                        y='Active_Contracts',
                        title=title_text,
                        labels={'AGENT': 'Agent', 'Active_Contracts': 'Active Contracts'},
                        color='Active_Contracts',
                        color_continuous_scale=[COLORS['light_purple'], COLORS['med_purple'], COLORS['primary'], COLORS['secondary']]
                    )
                    fig.update_layout(
                        height=450,  # Increase height
                        xaxis_title="Agent", 
                        yaxis_title="Active Contracts",
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font_color=COLORS['text'],
                        xaxis_tickangle=-45,  # Angle the x-axis labels
                        margin=dict(t=50, b=100),  # Add more bottom margin for labels
                        coloraxis=dict(colorbar=dict(
                            title="Contracts",
                            tickfont=dict(color=COLORS['text']),
                        ))
                    )
                    fig.update_traces(marker_line_color=COLORS['primary'],
                                      marker_line_width=1.5)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add a detailed summary of the week's performance
                    total_active = display_data['Active_Contracts'].sum()
                    
                    # Get total contracts for the week (all statuses)
                    week_start_date = datetime.strptime(selected_week_start_str, '%Y-%m-%d').date()
                    week_end_date = week_start_date + timedelta(days=6)
                    
                    # Filter the original dataframe for the selected week
                    all_contracts_in_week = df_filtered[
                        (df_filtered['ENROLLED_DATE'].dt.date >= week_start_date) & 
                        (df_filtered['ENROLLED_DATE'].dt.date <= week_end_date)
                    ]
                    
                    # Count by status
                    total_contracts = len(all_contracts_in_week)
                    active_count = len(all_contracts_in_week[all_contracts_in_week['CATEGORY'] == 'ACTIVE'])
                    nsf_count = len(all_contracts_in_week[all_contracts_in_week['CATEGORY'] == 'NSF'])
                    cancelled_count = len(all_contracts_in_week[all_contracts_in_week['CATEGORY'] == 'CANCELLED'])
                    other_count = len(all_contracts_in_week[all_contracts_in_week['CATEGORY'] == 'OTHER'])
                    
                    # Calculate success rate
                    success_rate = (active_count / total_contracts * 100) if total_contracts > 0 else 0
                    
                    st.markdown(f"""
                    <div class="week-summary">
                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                            <div style="flex: 1; min-width: 200px;">
                                <b>Week Summary:</b> {total_active} total active contracts for {len(display_data)} agents
                                {f" (showing top 10 of {len(selected_week_data)} agents)" if not show_all and len(selected_week_data) > 10 else ""}
                            </div>
                            <div style="flex: 1; min-width: 200px;">
                                <b>Week Status:</b> {active_count} Active, {nsf_count} NSF, {cancelled_count} Cancelled
                            </div>
                            <div style="flex: 1; min-width: 200px;">
                                <b>Success Rate:</b> {success_rate:.1f}% ({active_count} of {total_contracts} total)
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"No active contracts for top performers in the week of {selected_week_display}.")
            else:
                st.info("No weekly active sales data available.")
        except Exception as e:
            st.error(f"Error in weekly active sales analysis: {e}")
            st.info("Could not generate weekly active sales data.")
    else:
        st.warning("Enrollment date or Agent data not available for weekly sales analysis.")
    
    st.markdown("""
    </div>
    """, unsafe_allow_html=True)
    
    # Two column layout for the remaining charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="chart-box">
        <h3>Top Performing Agents</h3>
        """, unsafe_allow_html=True)
        
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
                barmode='group',
                color_discrete_map={
                    'Active': COLORS['med_green'],
                    'Total': COLORS['primary']
                }
            )
            fig.update_layout(
                height=400,  # Increase height
                plot_bgcolor=COLORS['background'],
                paper_bgcolor=COLORS['background'],
                font_color=COLORS['text'],
                margin=dict(t=50, b=100),  # Add more bottom margin for labels
                xaxis_tickangle=-45,  # Angle the x-axis labels
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor=COLORS['background'],
                    bordercolor=COLORS['primary'],
                    borderwidth=1
                )
            )
            fig.update_traces(marker_line_color=COLORS['primary'],
                              marker_line_width=1.5)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="chart-box">
        <h3>Enrollment Timeline</h3>
        """, unsafe_allow_html=True)
        
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
                fig.update_traces(
                    line=dict(color=COLORS['primary'], width=3),
                    marker=dict(size=8, color=COLORS['secondary'])
                )
                fig.update_layout(
                    height=400,  # Increase height
                    xaxis_rangeslider_visible=True,
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font_color=COLORS['text'],
                    margin=dict(t=50, b=50),  # Add more margin
                    yaxis=dict(gridcolor='rgba(138, 127, 186, 0.2)')
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating enrollment timeline: {e}")
                st.info("Could not generate enrollment timeline.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Full width chart for Status by Source
    st.markdown(f"""
    <div class="chart-box">
    <h3>Status by Source</h3>
    """, unsafe_allow_html=True)
    
    if 'SOURCE_SHEET' in df_filtered.columns:
        try:
            source_status = df_filtered.groupby(['SOURCE_SHEET', 'CATEGORY']).size().unstack(fill_value=0)
            fig = px.bar(
                source_status.reset_index(),
                x='SOURCE_SHEET',
                y=source_status.columns,
                title="Contract Status by Source",
                labels={'value': 'Count', 'variable': 'Status'},
                barmode='stack',
                color_discrete_map={
                    'ACTIVE': COLORS['med_green'],
                    'NSF': COLORS['warning'],
                    'CANCELLED': COLORS['danger'],
                    'OTHER': COLORS['med_purple']
                }
            )
            fig.update_layout(
                height=450,  # Increase height
                plot_bgcolor=COLORS['background'],
                paper_bgcolor=COLORS['background'],
                font_color=COLORS['text'],
                xaxis_tickangle=-45,  # Angle the x-axis labels
                margin=dict(t=50, b=100),  # Add more bottom margin for labels
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor=COLORS['background'],
                    bordercolor=COLORS['primary'],
                    borderwidth=1
                )
            )
            fig.update_traces(marker_line_color='white',
                              marker_line_width=1)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating source status chart: {e}")
            st.info("Could not generate source status chart.")
    else:
        st.warning("Source data not available")
    
    st.markdown("""
    </div>
    """, unsafe_allow_html=True)

# --- Performance Trends Tab ---
with tab2:
    st.markdown(f"""
    <div class="chart-box">
    <h3>Monthly Performance Trends</h3>
    """, unsafe_allow_html=True)
    
    if 'ENROLLED_DATE' in df_filtered.columns:
        try:
            # Create monthly data with status breakdown - improved logic
            # First ensure we have the MONTH_YEAR column
            if 'MONTH_YEAR' not in df_filtered.columns and 'ENROLLED_DATE' in df_filtered.columns:
                df_filtered['MONTH_YEAR'] = df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m')
                
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
            fig.update_traces(
                line=dict(color=COLORS['primary'], width=3),
                marker=dict(size=10, color=COLORS['secondary'])
            )
            fig.update_layout(
                height=400,
                plot_bgcolor=COLORS['background'],
                paper_bgcolor=COLORS['background'],
                font_color=COLORS['text'],
                yaxis=dict(gridcolor='rgba(138, 127, 186, 0.2)'),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
                 
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="chart-box">
                <h3>Contract Status Over Time</h3>
                """, unsafe_allow_html=True)
                
                try:
                    fig = px.area(
                        monthly_data,
                        x='MONTH_YEAR',
                        y=['ACTIVE', 'NSF', 'CANCELLED', 'OTHER'],
                        title="Contract Status Distribution Over Time",
                        labels={'value': 'Contract Count', 'variable': 'Status'},
                        color_discrete_map={
                            'ACTIVE': COLORS['med_green'],
                            'NSF': COLORS['warning'],
                            'CANCELLED': COLORS['danger'],
                            'OTHER': COLORS['med_purple']
                        }
                    )
                    fig.update_layout(
                        height=450,
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font_color=COLORS['text'],
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            bgcolor=COLORS['background'],
                            bordercolor=COLORS['primary'],
                            borderwidth=1
                        ),
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating status over time chart: {e}")
                    st.info("Could not generate status over time chart.")
                
                st.markdown("""
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="chart-box">
                <h3>Weekly Performance</h3>
                """, unsafe_allow_html=True)
                
                try:
                    # Improved approach for weekly data with better week calculation
                    weekly_df = df_filtered.copy()
                    
                    # Create a proper ISO week identifier
                    weekly_df['Week_Start'] = weekly_df['ENROLLED_DATE'].apply(
                        lambda x: x.date() - timedelta(days=x.weekday())
                    )
                    weekly_df['Week'] = weekly_df['Week_Start'].apply(
                        lambda x: f"{x.isocalendar()[0]}-W{x.isocalendar()[1]:02d}"
                    )
                    
                    # Group by week and category
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
                    fig.update_traces(
                        line=dict(color=COLORS['primary'], width=3),
                        marker=dict(size=8, color=COLORS['secondary'])
                    )
                    fig.update_layout(
                        height=450,
                        xaxis_tickangle=-45,
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font_color=COLORS['text'],
                        yaxis=dict(gridcolor='rgba(138, 127, 186, 0.2)')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating weekly performance chart: {e}")
                    st.info("Weekly performance data not available.")
                
                st.markdown("""
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error in performance trends analysis: {e}")
            st.info("Could not generate performance trends.")
    else:
        st.warning("Enrollment date data not available for performance trends analysis.")

# --- Agent Analytics Tab ---
with tab3:
    st.markdown(f"""
    <div class="chart-box">
    <h3>Agent Performance Analytics</h3>
    """, unsafe_allow_html=True)
    
    if 'AGENT' not in df_filtered.columns:
        st.warning("No 'AGENT' column found in dataset.")
    else:
        try:
            agents = df_filtered['AGENT'].dropna().unique()
            
            # Create a more visually appealing agent selector
            selected_agent = st.selectbox("Select agent:", sorted(agents))
            
            agent_df = df_filtered[df_filtered['AGENT'] == selected_agent]
            agent_active = agent_df[agent_df['CATEGORY'] == 'ACTIVE']
            agent_nsf = agent_df[agent_df['CATEGORY'] == 'NSF']
            agent_cancelled = agent_df[agent_df['CATEGORY'] == 'CANCELLED']
            
            # Calculate success rate safely
            success_rate = (len(agent_active)/len(agent_df)*100) if len(agent_df) > 0 else 0
            
            # Create agent metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(f"""
                <div style="background-color: {COLORS['light_purple']}; border-radius: 10px; padding: 15px; text-align: center; border-left: 5px solid {COLORS['primary']};">
                    <div style="font-size: 1.1rem; color: {COLORS['dark']}; font-weight: 600;">Total Contracts</div>
                    <div style="font-size: 2rem; font-weight: bold; color: {COLORS['primary']};">{len(agent_df)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background-color: {COLORS['light_purple']}; border-radius: 10px; padding: 15px; text-align: center; border-left: 5px solid {COLORS['med_green']};">
                    <div style="font-size: 1.1rem; color: {COLORS['dark']}; font-weight: 600;">Active</div>
                    <div style="font-size: 2rem; font-weight: bold; color: {COLORS['med_green']};">{len(agent_active)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background-color: {COLORS['light_purple']}; border-radius: 10px; padding: 15px; text-align: center; border-left: 5px solid {COLORS['warning']};">
                    <div style="font-size: 1.1rem; color: {COLORS['dark']}; font-weight: 600;">NSF</div>
                    <div style="font-size: 2rem; font-weight: bold; color: {COLORS['warning']};">{len(agent_nsf)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div style="background-color: {COLORS['light_purple']}; border-radius: 10px; padding: 15px; text-align: center; border-left: 5px solid {COLORS['danger']};">
                    <div style="font-size: 1.1rem; color: {COLORS['dark']}; font-weight: 600;">Cancelled</div>
                    <div style="font-size: 2rem; font-weight: bold; color: {COLORS['danger']};">{len(agent_cancelled)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
                st.markdown(f"""
                <div style="background-color: {COLORS['light_purple']}; border-radius: 10px; padding: 15px; text-align: center; border-left: 5px solid {COLORS['dark_accent']};">
                    <div style="font-size: 1.1rem; color: {COLORS['dark']}; font-weight: 600;">Success Rate</div>
                    <div style="font-size: 2rem; font-weight: bold; color: {COLORS['dark_accent']};">{success_rate:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="chart-box">
                <h3>Agent's Status Distribution</h3>
                """, unsafe_allow_html=True)
                
                status_counts = agent_df['CATEGORY'].value_counts()
                fig = px.pie(
                    status_counts, 
                    values=status_counts.values, 
                    names=status_counts.index,
                    hole=0.4,
                    title=f"Status Distribution for {selected_agent}",
                    color=status_counts.index,
                    color_discrete_map={
                        'ACTIVE': COLORS['med_green'],
                        'NSF': COLORS['warning'],
                        'CANCELLED': COLORS['danger'],
                        'OTHER': COLORS['med_purple']
                    }
                )
                fig.update_layout(
                    height=400,
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font_color=COLORS['text'],
                    legend=dict(
                        bgcolor=COLORS['background'],
                        bordercolor=COLORS['primary'],
                        borderwidth=1
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="chart-box">
                <h3>Performance Timeline</h3>
                """, unsafe_allow_html=True)
                
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
                        fig.update_traces(
                            line=dict(color=COLORS['primary'], width=3),
                            marker=dict(size=8, color=COLORS['secondary'])
                        )
                        fig.update_layout(
                            height=400,
                            plot_bgcolor=COLORS['background'],
                            paper_bgcolor=COLORS['background'],
                            font_color=COLORS['text'],
                            yaxis=dict(gridcolor='rgba(138, 127, 186, 0.2)')
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error generating agent timeline: {e}")
                        st.info("Could not generate agent timeline.")
                
                st.markdown("""
                </div>
                """, unsafe_allow_html=True)
            
            # Generate and download report
            st.markdown(f"""
            <div class="chart-box">
            <h3>Contract Details</h3>
            """, unsafe_allow_html=True)
            
            # Add a search box for filtering contracts
            search_term = st.text_input("Search contracts:", "")
            if search_term:
                filtered_agent_df = agent_df[agent_df.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)]
            else:
                filtered_agent_df = agent_df
                
            # Display simplified dataframe with only essential columns
            essential_cols = ['CUSTOMER_ID', 'ENROLLED_DATE', 'STATUS', 'CATEGORY']
            display_cols = [col for col in essential_cols if col in filtered_agent_df.columns]
            st.dataframe(filtered_agent_df[display_cols].sort_values('ENROLLED_DATE', ascending=False), 
                       use_container_width=True, height=400)
            
            # Excel report with improved styling
            try:
                excel_bytes = generate_agent_report_excel(agent_df, selected_agent)
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.download_button(
                        label="📊 Download Report",
                        data=excel_bytes,
                        file_name=f"{selected_agent}_performance_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                with col2:
                    st.markdown(f"""
                    <div style="background-color: rgba(127, 255, 212, 0.2); border-left: 4px solid {COLORS['dark_accent']}; 
                    padding: 15px; border-radius: 0 10px 10px 0; margin-top: 4px;">
                        Download a comprehensive Excel report with all metrics and contract details
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating Excel report: {e}")
                st.info("Could not generate Excel report.")
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error in agent analytics: {e}")
            st.info("Could not load agent analytics.")

# --- Data Explorer Tab ---
with tab4:
    st.markdown(f"""
    <div class="chart-box">
    <h3>Data Exploration</h3>
    """, unsafe_allow_html=True)
    
    try:
        # Column selection with improved UI
        default_cols = ['CUSTOMER_ID', 'AGENT', 'ENROLLED_DATE', 'STATUS', 'CATEGORY', 'SOURCE_SHEET']
        available_cols = [col for col in df_filtered.columns if col in default_cols] or df_filtered.columns.tolist()
        
        selected_cols = st.multiselect("Select columns to display:", df_filtered.columns.tolist(), default=available_cols)
        
        if selected_cols:
            # Filter options
            st.subheader("Additional Filters")
            
            col1, col2 = st.columns(2)
            # Agent filter for data explorer
            if 'AGENT' in selected_cols:
                with col1:
                    agent_filter = st.multiselect(
                        "Filter by Agent:", 
                        options=["All"] + sorted(df_filtered['AGENT'].unique().tolist()),
                        default=["All"]
                    )
            
            # Status filter for data explorer
            if 'CATEGORY' in selected_cols:
                with col2:
                    status_filter_explorer = st.multiselect(
                        "Filter by Status:",
                        options=["All"] + sorted(df_filtered['CATEGORY'].unique().tolist()),
                        default=["All"]
                    )
            
            # Apply filters
            df_explorer = df_filtered.copy()
            
            # Apply agent filter
            if 'AGENT' in selected_cols and "All" not in agent_filter:
                df_explorer = df_explorer[df_explorer['AGENT'].isin(agent_filter)]
            
            # Apply status filter
            if 'CATEGORY' in selected_cols and "All" not in status_filter_explorer:
                df_explorer = df_explorer[df_explorer['CATEGORY'].isin(status_filter_explorer)]
            
            # Add search functionality
            search_query = st.text_input("Search in data (searches across all columns):", "")
            if search_query:
                df_explorer = df_explorer[df_explorer.astype(str).apply(
                    lambda row: row.str.contains(search_query, case=False).any(), axis=1)]
            
            # Display data with record count
            st.subheader(f"Filtered Data ({len(df_explorer)} records)")
            
            # Display dataframe
            # Limit to essential columns if too many are selected
            if len(selected_cols) > 5:
                essential_cols = ['CUSTOMER_ID', 'AGENT', 'ENROLLED_DATE', 'STATUS', 'CATEGORY']
                display_cols = [col for col in essential_cols if col in selected_cols]
                if len(display_cols) < 3:  # If not enough essential columns, use the first 4 selected
                    display_cols = selected_cols[:4]
                st.info(f"Showing only essential columns for better readability. Selected: {', '.join(display_cols)}")
            else:
                display_cols = selected_cols
                
            st.dataframe(df_explorer[display_cols], use_container_width=True, height=500)
            
            # Export options with improved UI
            st.subheader("Export Data")
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.radio("Select format:", ["CSV", "Excel"])
            
            with col2:
                filename = st.text_input("Filename:", f"pepe_sales_data_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}")
            
            if export_format == "CSV":
                csv = df_explorer[selected_cols].to_csv(index=False).encode()
                st.download_button("📤 Download CSV", csv, file_name=f"{filename}.csv", mime="text/csv")
            else:
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df_explorer[selected_cols].to_excel(writer, index=False)
                    
                    # Format the Excel file
                    workbook = writer.book
                    worksheet = writer.sheets['Sheet1']
                    
                    # Format headers
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': COLORS['primary'],
                        'color': 'white',
                        'border': 1
                    })
                    
                    for col_num, value in enumerate(df_explorer[selected_cols].columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Auto-fit columns
                    for i, col in enumerate(df_explorer[selected_cols].columns):
                        column_len = max(df_explorer[col].astype(str).str.len().max(), len(col)) + 2
                        worksheet.set_column(i, i, column_len)
                
                excel_buffer.seek(0)
                st.download_button("📤 Download Excel", excel_buffer, file_name=f"{filename}.xlsx", 
                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("Please select at least one column to display")
    except Exception as e:
        st.error(f"Error in data explorer: {e}")
        st.info("Could not load data explorer.")
    
    st.markdown("""
    </div>
    """, unsafe_allow_html=True)

# --- Risk Analysis Tab ---
with tab5:
    st.markdown(f"""
    <div class="chart-box">
    <h3>Risk Analysis</h3>
    """, unsafe_allow_html=True)
    try:
        # Filter for problematic contracts
        flagged = df_filtered[df_filtered['CATEGORY'].isin(["NSF", "CANCELLED", "OTHER"])]
        
        # Add risk summary metrics
        total_risk = len(flagged)
        risk_percentage = (total_risk / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        
        st.markdown(f"""
        <div class="risk-indicator">
            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                <div style="flex: 1; min-width: 200px;">
                    <div style="font-size: 1.1rem; color: #483D8B; font-weight: 600;">Total Risk Contracts</div>
                    <div style="font-size: 2rem; font-weight: bold; color: #FF6347;">{total_risk}</div>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <div style="font-size: 1.1rem; color: #483D8B; font-weight: 600;">Risk Percentage</div>
                    <div style="font-size: 2rem; font-weight: bold; color: #FF6347;">{risk_percentage:.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="chart-box">
            <h3>Cancellation Reasons</h3>
            """, unsafe_allow_html=True)
            
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
                        color_continuous_scale=[COLORS['light_purple'], COLORS['primary'], COLORS['secondary'], COLORS['dark']]
                    )
                    fig.update_layout(
                        height=450,
                        xaxis_tickangle=-45,
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font_color=COLORS['text'],
                        margin=dict(t=50, b=120),  # Extra bottom margin for rotated labels
                        coloraxis=dict(colorbar=dict(
                            title="Count",
                            tickfont=dict(color=COLORS['text']),
                        ))
                    )
                    fig.update_traces(marker_line_color=COLORS['primary'],
                                      marker_line_width=1.5)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating cancellation reasons chart: {e}")
                    st.info("Could not generate cancellation reasons chart.")
            else:
                st.info("No cancellation data available.")
            
        st.markdown("""
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="chart-box">
            <h3>Agents with Most Issues</h3>
            """, unsafe_allow_html=True)
            
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
                        color_continuous_scale=[COLORS['light_purple'], COLORS['primary'], COLORS['secondary'], COLORS['dark']]
                    )
                    fig.update_layout(
                        height=450,
                        xaxis_tickangle=-45,
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font_color=COLORS['text'],
                        margin=dict(t=50, b=120),  # Extra bottom margin for rotated labels
                        coloraxis=dict(colorbar=dict(
                            title="Issues",
                            tickfont=dict(color=COLORS['text']),
                        ))
                    )
                    fig.update_traces(marker_line_color=COLORS['primary'],
                                      marker_line_width=1.5)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating agents with issues chart: {e}")
                    st.info("Could not generate agents with issues chart.")
            else:
                st.info("No agent issue data available.")
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
        
        # Risk analysis by time
        st.markdown(f"""
        <div class="chart-box">
        <h3>Risk Trends Over Time</h3>
        """, unsafe_allow_html=True)
        
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
                fig.update_traces(
                    line=dict(color=COLORS['primary'], width=3),
                    marker=dict(size=10, color=COLORS['danger'], line=dict(width=2, color=COLORS['primary']))
                )
                fig.update_layout(
                    height=450,
                    plot_bgcolor=COLORS['background'],
                    paper_bgcolor=COLORS['background'],
                    font_color=COLORS['text'],
                    yaxis=dict(gridcolor='rgba(138, 127, 186, 0.2)'),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating risk trends chart: {e}")
                st.info("Could not generate risk trends chart.")
        else:
            st.info("No time-based risk data available.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
        
        # Problem contracts with search functionality
        st.markdown(f"""
        <div class="chart-box">
        <h3>Problem Contracts</h3>
        """, unsafe_allow_html=True)
        
        if not flagged.empty:
            # Add search functionality
            search_risk = st.text_input("Search problem contracts:", "")
            if search_risk:
                filtered_flagged = flagged[flagged.astype(str).apply(
                    lambda row: row.str.contains(search_risk, case=False).any(), axis=1)]
            else:
                filtered_flagged = flagged
            
            # Display simplified risk dataframe with only essential columns
            essential_cols = ['CUSTOMER_ID', 'AGENT', 'ENROLLED_DATE', 'STATUS', 'CATEGORY']
            display_cols = [col for col in essential_cols if col in filtered_flagged.columns]
            st.dataframe(filtered_flagged[display_cols].sort_values('ENROLLED_DATE', ascending=False), 
                       use_container_width=True, height=400)
            
            # Export flagged data with better UI
            col1, col2 = st.columns([1, 3])
            with col1:
                csv_flagged = filtered_flagged.to_csv(index=False).encode()
                st.download_button("📤 Download Risk Data", csv_flagged, file_name="risk_contracts.csv", mime="text/csv")
            with col2:
                st.markdown(f"""
                <div style="background-color: rgba(255, 99, 71, 0.1); border-left: 4px solid {COLORS['danger']}; 
                padding: 15px; border-radius: 0 10px 10px 0; margin-top: 4px;">
                    Download the risk data for offline analysis or follow-up actions
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No problem contracts found in the selected data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error in risk analysis: {e}")
        st.info("Could not load risk analysis.")

# --- Footer ---
st.markdown(f"""
<div class="footer">
    © 2025 Pepe's Power Solutions | Dashboard v3.0
</div>
""", unsafe_allow_html=True)

# --- Notifications ---
st.toast("Dashboard loaded successfully!", icon="🐸")

# --- Debug Mode ---
debug_mode = st.sidebar.checkbox("Show Debug Info", False)
if debug_mode:
    st.sidebar.subheader("Debug Information")
    st.sidebar.write("App Version: 2.5.1")
    st.sidebar.write("Current Time:", datetime.now())
    if 'ENROLLED_DATE' in df.columns:
        st.sidebar.write("Data Date Range:", df['ENROLLED_DATE'].min().date(), "to", df['ENROLLED_DATE'].max().date())
    st.sidebar.write("Total Records:", len(df))
    st.sidebar.write("Filtered Records:", len(df_filtered))
