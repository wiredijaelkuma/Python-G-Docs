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
RAW_DATA_SHEET_NAMES = ["PAC", "Pepe", "Frog"]  # Removed "-Raw" suffix

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
            df[EXPECTED_COL_STATUS] = df[EXPECTED_COL_STATUS].astype('category')
            
            # Add CATEGORY column for better filtering
            df['CATEGORY'] = 'OTHER'
            df.loc[df[EXPECTED_COL_STATUS].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            df.loc[df[EXPECTED_COL_STATUS].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            df.loc[df[EXPECTED_COL_STATUS].str.contains('CANCEL|DROP|TERMIN|NEEDS ROL|PENDING', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
            df['CATEGORY'] = df['CATEGORY'].astype('category')
        
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
            'axis': {'range': [min_val, max_val], 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_val, max_val*0.3], 'color': "lightcoral"},
                {'range': [max_val*0.3, max_val*0.7], 'color': "khaki"},
                {'range': [max_val*0.7, max_val], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_val*0.8
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="white",
        font=dict(color='darkblue')
    )
    
    return fig