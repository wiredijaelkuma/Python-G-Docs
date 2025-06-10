import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- Constants ---
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_TITLE = "Pepe's Power Sales"
RAW_DATA_SHEET_NAMES = ["PAC-Raw", "Pepe-Raw", "Frog-Raw"]

# Expected column names
EXPECTED_COL_ENROLLED_DATE = "ENROLLED_DATE"
EXPECTED_COL_STATUS = "STATUS"
EXPECTED_COL_AGENT = "AGENT"

# Status categories
ACTIVE_SALE_STATUSES = ["ACTIVE", "ENROLLED / ACTIVE", "ENROLLED/ACTIVE"]
POTENTIAL_RESCUE_STATUSES = ["NSF", "ENROLLED / NSF PROBLEM", "ENROLLED/NSF"]
NON_ACTIVE_SALE_STATUSES = ["CANCELLED", "DROPPED", "PENDING CANCELLATION", "TERMINATED", "NEEDS ROL"]

# Agent colors for consistent visualization
AGENT_COLORS = {
    "JOHN": "#1f77b4",
    "SARAH": "#ff7f0e",
    "MIKE": "#2ca02c",
    "LISA": "#d62728",
    "DAVID": "#9467bd",
    "EMMA": "#8c564b",
    "ALEX": "#e377c2",
    "OLIVIA": "#7f7f7f",
    "JAMES": "#bcbd22",
    "SOPHIA": "#17becf"
}

# --- Helper Functions ---
def get_gspread_client(credentials_file):
    """Establish connection to Google Sheets API"""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error establishing gspread client: {e}")
        return None

def fetch_and_combine_data(client, spreadsheet_title, sheet_names):
    """Fetch data from multiple sheets and combine into a single DataFrame"""
    try:
        # Open the spreadsheet
        spreadsheet = client.open(spreadsheet_title)
        
        # Initialize empty list to store DataFrames
        all_dfs = []
        
        # Process each sheet
        for sheet_name in sheet_names:
            try:
                # Get the worksheet
                worksheet = spreadsheet.worksheet(sheet_name)
                
                # Get all values
                data = worksheet.get_all_values()
                
                # Convert to DataFrame
                if data:
                    headers = data[0]
                    rows = data[1:]
                    df = pd.DataFrame(rows, columns=headers)
                    
                    # Add source sheet column
                    df['SOURCE_SHEET'] = sheet_name
                    
                    # Append to list
                    all_dfs.append(df)
                    print(f"Successfully fetched {len(df)} rows from '{sheet_name}'")
                else:
                    print(f"No data found in sheet '{sheet_name}'")
            
            except Exception as e:
                print(f"Error processing sheet '{sheet_name}': {e}")
        
        # Combine all DataFrames
        if all_dfs:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            print(f"Combined DataFrame created with {len(combined_df)} total rows")
            
            # Process the combined DataFrame
            combined_df = process_combined_data(combined_df)
            
            return combined_df, all_dfs
        else:
            print("No DataFrames to combine")
            return pd.DataFrame(), []
    
    except Exception as e:
        print(f"Error in fetch_and_combine_data: {e}")
        return pd.DataFrame(), []

def process_combined_data(df):
    """Process and clean the combined DataFrame"""
    try:
        # Standardize column names
        df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]
        
        # Convert date columns
        if EXPECTED_COL_ENROLLED_DATE in df.columns:
            df[EXPECTED_COL_ENROLLED_DATE] = pd.to_datetime(df[EXPECTED_COL_ENROLLED_DATE], errors='coerce')
        
        # Clean and standardize status
        if EXPECTED_COL_STATUS in df.columns:
            df[EXPECTED_COL_STATUS] = df[EXPECTED_COL_STATUS].astype(str).str.strip().str.upper()
        
        # Add derived columns for analysis
        if EXPECTED_COL_ENROLLED_DATE in df.columns:
            df['MONTH_YEAR'] = df[EXPECTED_COL_ENROLLED_DATE].dt.strftime('%Y-%m')
            df['WEEK'] = df[EXPECTED_COL_ENROLLED_DATE].dt.isocalendar().week.astype(int)
            df['YEAR'] = df[EXPECTED_COL_ENROLLED_DATE].dt.isocalendar().year.astype(int)
            df['WEEK_YEAR'] = df['YEAR'].astype(str) + '-W' + df['WEEK'].astype(str).str.zfill(2)
            df['DAY_OF_WEEK'] = df[EXPECTED_COL_ENROLLED_DATE].dt.day_name()
        
        return df
    
    except Exception as e:
        print(f"Error in process_combined_data: {e}")
        return df

def get_week_dates(week_number, year=None):
    """Get start and end dates for a given week number"""
    if year is None:
        year = date.today().year
    
    # Convert to int to avoid numpy type issues
    week_number = int(week_number)
    year = int(year)
    
    # Use the ISO calendar to get the correct dates
    # Find the first day of the year
    first_day = date(year, 1, 1)
    
    # Find the first day of the first ISO week
    # In ISO calendar, weeks start on Monday
    first_week_day = first_day
    while first_week_day.isocalendar()[1] != 1:
        first_week_day += timedelta(days=1)
    
    # Calculate the start date of the target week
    # Weeks start on Monday in ISO calendar
    start_week = first_week_day + timedelta(weeks=week_number-1)
    
    # Calculate the end date of the target week (Sunday)
    end_week = start_week + timedelta(days=6)
    
    return start_week, end_week

def get_current_week_number():
    """Get the current ISO week number"""
    return date.today().isocalendar()[1]

def get_target_processing_month_dates(run_date=date.today()):
    """Get start and end dates for the target processing month"""
    # Default to current month
    year = run_date.year
    month = run_date.month
    
    # Get first day of the month
    start_month = date(year, month, 1)
    
    # Get last day of the month
    if month == 12:
        end_month = date(year, month, 31)
    else:
        end_month = date(year, month + 1, 1) - timedelta(days=1)
    
    return start_month, end_month

def create_bar_chart(df, title, x_col, y_col, color_col=None, color_map=None):
    """Create a bar chart with consistent styling"""
    if color_col:
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col, 
            title=title,
            color=color_col,
            color_discrete_map=color_map
        )
    else:
        fig = px.bar(
            df, 
            x=x_col, 
            y=y_col, 
            title=title
        )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='darkblue'),
        xaxis=dict(showgrid=True, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )
    
    return fig

def create_line_chart(df, title, x_col, y_col):
    """Create a line chart with consistent styling"""
    fig = px.line(
        df, 
        x=x_col, 
        y=y_col, 
        title=title,
        markers=True
    )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='darkblue'),
        xaxis=dict(showgrid=True, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )
    
    return fig

def create_heatmap_chart(df, title, date_col='Date', value_col='Daily Active Enrollments'):
    """Create a calendar heatmap chart"""
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])
    
    # Extract year, month, and day
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['day'] = df[date_col].dt.day
    
    # Create the heatmap
    fig = px.density_heatmap(
        df,
        x='day',
        y='month',
        z=value_col,
        title=title,
        labels={'day': 'Day of Month', 'month': 'Month', value_col: value_col},
        color_continuous_scale=['#f7fbff', '#08306b']
    )
    
    # Update layout
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='darkblue'),
        xaxis=dict(dtick=1, title='Day of Month'),
        yaxis=dict(dtick=1, title='Month')
    )
    
    return fig

def create_gauge_chart(value, min_val, max_val, title):
    """Create a gauge chart with consistent styling"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'color': 'darkblue', 'size': 24}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickfont': {'color': 'darkblue'}},
            'bar': {'color': "#2ca02c" if value >= 70 else "#ff7f0e" if value >= 50 else "#d62728"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [min_val, 50], 'color': 'rgba(214, 39, 40, 0.2)'},
                {'range': [50, 70], 'color': 'rgba(255, 127, 14, 0.2)'},
                {'range': [70, max_val], 'color': 'rgba(44, 160, 44, 0.2)'}
            ]
        },
        number={'font': {'color': 'darkblue', 'size': 40}, 'suffix': '%'}
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(t=50, b=10, l=30, r=30),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': 'darkblue'},
    )
    
    return fig

# --- Analysis Functions ---
def prepare_weekly_performance(combined_df, week_number, year=None):
    """Prepare weekly performance data for the specified week"""
    required_cols = [EXPECTED_COL_ENROLLED_DATE, EXPECTED_COL_STATUS, EXPECTED_COL_AGENT]
    if combined_df.empty or not all(col in combined_df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in combined_df.columns]
        return pd.DataFrame([{"Message": f"Weekly performance: Data empty or missing: {missing}"}]), go.Figure()
    
    # Get the start and end dates for the week
    if year is None and 'YEAR' in combined_df.columns:
        # Use the most recent year that has data for this week
        years_with_week = combined_df[combined_df['WEEK'] == int(week_number)]['YEAR'].unique()
        if len(years_with_week) > 0:
            year = max(years_with_week)
        else:
            year = date.today().year
    elif year is None:
        year = date.today().year
    
    start_week, end_week = get_week_dates(week_number, year)
    
    # Filter data for the week
    weekly_df = combined_df[(combined_df[EXPECTED_COL_ENROLLED_DATE].dt.date >= start_week) & 
                           (combined_df[EXPECTED_COL_ENROLLED_DATE].dt.date <= end_week)]
    
    # Filter for active sales
    active_weekly_sales_df = weekly_df[weekly_df[EXPECTED_COL_STATUS].isin(ACTIVE_SALE_STATUSES)]

    if active_weekly_sales_df.empty:
        return pd.DataFrame([{"Message": f"No active sales for Week {week_number} ({start_week.strftime('%b %d')}-{end_week.strftime('%b %d')})"}]), go.Figure().update_layout(title_text=f"Week {week_number} ({start_week.strftime('%b %d')}-{end_week.strftime('%b %d')}) (No active sales)")
        
    agent_summary = active_weekly_sales_df.groupby(EXPECTED_COL_AGENT).size().reset_index(name='Active Enrollments')
    agent_summary = agent_summary.sort_values('Active Enrollments', ascending=False)
    fig_title = f"Week {week_number} ({start_week.strftime('%b %d')}-{end_week.strftime('%b %d')}) Active Performance"
    fig = create_bar_chart(agent_summary, fig_title, EXPECTED_COL_AGENT, 'Active Enrollments', color_col=EXPECTED_COL_AGENT, color_map=AGENT_COLORS)
    return agent_summary, fig

def get_most_recent_week_data(combined_df):
    """Get data for the most recent week with sales"""
    if combined_df.empty or EXPECTED_COL_ENROLLED_DATE not in combined_df.columns:
        return pd.DataFrame([{"Message": "No data available for recent week analysis"}]), go.Figure()
    
    # Get the current week number
    current_week = get_current_week_number()
    current_year = date.today().year
    
    # Try to get data for the current week
    current_week_summary, current_week_fig = prepare_weekly_performance(combined_df, current_week, current_year)
    
    # If no data for current week, try the previous week
    if "Message" in current_week_summary.columns:
        previous_week = current_week - 1
        if previous_week < 1:
            previous_week = 52
            previous_year = current_year - 1
        else:
            previous_year = current_year
            
        return prepare_weekly_performance(combined_df, previous_week, previous_year)
    
    return current_week_summary, current_week_fig

def prepare_monthly_tracker(combined_df, run_date=date.today()):
    """Prepare monthly tracker data for the specified month"""
    required_cols = [EXPECTED_COL_ENROLLED_DATE, EXPECTED_COL_STATUS]
    if combined_df.empty or not all(col in combined_df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in combined_df.columns]
        return pd.DataFrame([{"Message": f"Monthly tracker: Data empty or missing: {missing}"}]), go.Figure(), go.Figure()

    start_month, end_month = get_target_processing_month_dates(run_date)
    month_year_str = start_month.strftime("%B %Y")
    monthly_df = combined_df[(combined_df[EXPECTED_COL_ENROLLED_DATE].dt.date >= start_month) & 
                            (combined_df[EXPECTED_COL_ENROLLED_DATE].dt.date <= end_month)]
    active_monthly_sales_df = monthly_df[monthly_df[EXPECTED_COL_STATUS].isin(ACTIVE_SALE_STATUSES)]

    if active_monthly_sales_df.empty:
        return pd.DataFrame([{"Message": f"No active sales for {month_year_str}"}]), go.Figure().update_layout(title_text=f"Daily Active Enrollments - {month_year_str} (No data)"), go.Figure()

    daily_counts = active_monthly_sales_df.groupby(active_monthly_sales_df[EXPECTED_COL_ENROLLED_DATE].dt.date).size().reset_index(name='Daily Active Enrollments')
    daily_counts.columns = ['Date', 'Daily Active Enrollments']
    daily_counts['Date'] = pd.to_datetime(daily_counts['Date'])
    daily_counts = daily_counts.sort_values('Date')
    
    fig_line = create_line_chart(daily_counts, f"Daily Active Enrollments - {month_year_str}", "Date", "Daily Active Enrollments")
    fig_heatmap = create_heatmap_chart(daily_counts, f"{month_year_str}", date_col='Date', value_col='Daily Active Enrollments')
    return daily_counts, fig_line, fig_heatmap

def prepare_pac_metrics(pac_df_period, run_date_for_month_str=date.today()):
    """Prepare PAC metrics for the specified month"""
    required_cols = [EXPECTED_COL_ENROLLED_DATE, EXPECTED_COL_STATUS]
    month_year_str = get_target_processing_month_dates(run_date_for_month_str)[0].strftime("%B %Y")

    if pac_df_period.empty or not all(col in pac_df_period.columns for col in required_cols):
        missing = [col for col in required_cols if col not in pac_df_period.columns]
        msg_df = pd.DataFrame([{"Message": f"PAC metrics ({month_year_str}): Data empty or missing: {missing}"}])
        summary_empty = pd.DataFrame({"Metric": ["Total Active Sales", "Potential Rescue", "Other Non-Active", "Stick Rate Base", "Stick Rate (%)"], 
                                     "Value": [0,0,0,0,"0.0"]})
        return msg_df, summary_empty, go.Figure(), go.Figure()

    # Active Sales in the period
    active_sales_df = pac_df_period[pac_df_period[EXPECTED_COL_STATUS].isin(ACTIVE_SALE_STATUSES)]
    num_active_sales = len(active_sales_df)

    # Potential Rescue in the period
    potential_rescue_df = pac_df_period[pac_df_period[EXPECTED_COL_STATUS].isin(POTENTIAL_RESCUE_STATUSES)]
    num_potential_rescue = len(potential_rescue_df)
    
    # Non-Active for Stick Rate (everything NOT an active sale status)
    non_active_for_stick_rate_df = pac_df_period[~pac_df_period[EXPECTED_COL_STATUS].isin(ACTIVE_SALE_STATUSES)]
    num_non_active_for_stick_rate = len(non_active_for_stick_rate_df)

    # Stick Rate Calculation
    stick_rate_base = num_active_sales + num_non_active_for_stick_rate
    stick_rate = (num_active_sales / stick_rate_base * 100) if stick_rate_base > 0 else 0.0
    
    # Calculate "Other Non-Active"
    other_non_active_mask = (~pac_df_period[EXPECTED_COL_STATUS].isin(ACTIVE_SALE_STATUSES)) & \
                            (~pac_df_period[EXPECTED_COL_STATUS].isin(POTENTIAL_RESCUE_STATUSES))
    num_other_non_active = len(pac_df_period[other_non_active_mask])

    daily_active_sales_table = pd.DataFrame({'Date': [], 'Daily Active Sales': []})
    fig_sales = go.Figure().update_layout(title_text=f"PAC Daily Active Sales - {month_year_str} (No active sales)")
    
    if num_active_sales > 0:
        daily_active_sales_table = active_sales_df.groupby(active_sales_df[EXPECTED_COL_ENROLLED_DATE].dt.date).size().reset_index(name='Daily Active Sales')
        daily_active_sales_table.columns = ['Date', 'Daily Active Sales']
        daily_active_sales_table['Date'] = pd.to_datetime(daily_active_sales_table['Date'])
        daily_active_sales_table = daily_active_sales_table.sort_values('Date')
        fig_sales = create_bar_chart(daily_active_sales_table, f"PAC Daily Active Sales - {month_year_str}", "Date", "Daily Active Sales")
            
    fig_gauge = create_gauge_chart(stick_rate, 0, 100, f"Stick Rate: {stick_rate:.1f}% - {month_year_str}")
    
    summary_metrics_df = pd.DataFrame({
        "Metric": [
            f"Total Active Sales ({month_year_str})", 
            f"Potential Rescue (e.g., NSF) ({month_year_str})", 
            f"Other Non-Active (Not Active/NSF) ({month_year_str})",
            f"Stick Rate Base (Total in Period) ({month_year_str})",
            f"Stick Rate (%) - {month_year_str}"
        ],
        "Value": [
            num_active_sales, 
            num_potential_rescue,
            num_other_non_active, 
            stick_rate_base,
            f"{stick_rate:.1f}"
        ]
    })
    return daily_active_sales_table, summary_metrics_df, fig_sales, fig_gauge

def get_program_usage_stats(combined_df):
    """Get statistics on which program is being used the most"""
    if combined_df.empty or 'SOURCE_SHEET' not in combined_df.columns:
        return pd.DataFrame([{"Message": "No program usage data available"}]), go.Figure()
    
    # Clean source names
    combined_df['CLEAN_SOURCE'] = combined_df['SOURCE_SHEET'].str.replace('-Raw', '').str.replace(' Raw', '')
    
    # Get program usage counts
    program_counts = combined_df.groupby('CLEAN_SOURCE').size().reset_index(name='Count')
    program_counts = program_counts.sort_values('Count', ascending=False)
    
    # Calculate percentages
    total = program_counts['Count'].sum()
    program_counts['Percentage'] = (program_counts['Count'] / total * 100).round(1)
    program_counts['Percentage_Label'] = program_counts['Percentage'].astype(str) + '%'
    
    # Create chart
    fig = px.bar(
        program_counts,
        x='CLEAN_SOURCE',
        y='Count',
        title='Program Usage Statistics',
        text='Percentage_Label',
        color='Count',
        color_continuous_scale=['#E6E6FA', '#8A7FBA', '#6A5ACD', '#483D8B']
    )
    
    fig.update_layout(
        xaxis_title='Program',
        yaxis_title='Number of Contracts',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='darkblue'),
        xaxis=dict(showgrid=True, gridcolor='lightgray'),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )
    
    fig.update_traces(textposition='outside')
    
    return program_counts, fig