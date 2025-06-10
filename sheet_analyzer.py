import gspread
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- Configuration Variables ---
SPREADSHEET_TITLE = "Forth Py"
CREDENTIALS_FILE = 'credentials.json' 
RAW_DATA_SHEET_NAMES = ["PAC- Raw", "MLG- Raw", "ELP- Raw", "Cordoba- Raw"]
PAC_RAW_SHEET_NAME = "PAC- Raw"
EXPECTED_COL_CUSTOMER_ID = "CUSTOMER ID"
EXPECTED_COL_AGENT = "AGENT"
EXPECTED_COL_ENROLLED_DATE = "ENROLLED DATE"
EXPECTED_COL_STATUS = "STATUS" 

# --- Status Configuration ---
ACTIVE_SALE_STATUSES = ["ACTIVE", "ENROLLED / ACTIVE", "ENROLLED/ACTIVE"] 
POTENTIAL_RESCUE_STATUSES = ["NSF", "ENROLLED / NSF PROBLEM", "ENROLLED/NSF"]

# Visualization Settings
AGENT_COLORS = {
    "Agent A": "#636EFA", "Agent B": "#EF553B", "Agent C": "#00CC96",
    "Agent D": "#AB63FA", "Agent E": "#FFA15A"
}

# --- Helper Function for Standardization ---
def standardize_and_prepare_df(df, sheet_name_for_logging):
    if df.empty:
        return df
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    if EXPECTED_COL_ENROLLED_DATE in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df[EXPECTED_COL_ENROLLED_DATE]):
            df[EXPECTED_COL_ENROLLED_DATE] = pd.to_datetime(df[EXPECTED_COL_ENROLLED_DATE], errors='coerce')
            if df[EXPECTED_COL_ENROLLED_DATE].isnull().all() and not df.empty:
                print(f"    WARNING: All '{EXPECTED_COL_ENROLLED_DATE}' became NaT for '{sheet_name_for_logging}'.")
    
    if EXPECTED_COL_STATUS in df.columns:
        df[EXPECTED_COL_STATUS] = df[EXPECTED_COL_STATUS].astype(str).str.strip().str.upper()
    return df

# --- Date Handling Functions ---
def get_target_week_dates(run_date=date.today()):
    last_sunday = run_date - timedelta(days=(run_date.weekday() + 1) % 7)
    end_date = last_sunday if run_date.weekday() in [0, 1] else last_sunday + timedelta(days=7)
    start_date = end_date - timedelta(days=6)
    return start_date, end_date

def get_target_processing_month_dates(run_date=date.today()):
    if run_date.day <= 2:
        end_date = run_date.replace(day=1) - timedelta(days=1)
        start_date = end_date.replace(day=1)
    else:
        start_date = run_date.replace(day=1)
        end_date = run_date
    return start_date, end_date

# --- Core Data Fetching and Processing Function ---
def get_gspread_client(credentials_file=CREDENTIALS_FILE):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        print("gspread client authentication successful.")
        return client
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Credentials file '{credentials_file}' not found.")
        return None
    except Exception as e:
        print(f"Error during gspread client authentication: {e}")
        return None

def fetch_and_combine_data(gspread_client, spreadsheet_title, raw_sheet_names_list):
    if gspread_client is None: return pd.DataFrame(), {}
    all_individual_dfs = {}
    try:
        sheet_gspread_obj = gspread_client.open(spreadsheet_title)
        for sheet_name in raw_sheet_names_list:
            try:
                worksheet = sheet_gspread_obj.worksheet(sheet_name)
                records = worksheet.get_all_records(empty2zero=False, head=1, default_blank="")
                df = pd.DataFrame(records) if records else pd.DataFrame(worksheet.get_all_values()[1:], columns=worksheet.get_all_values()[0]) if worksheet.get_all_values() and len(worksheet.get_all_values()) > 1 else None
                
                if df is not None:
                    df_processed = standardize_and_prepare_df(df.copy(), sheet_name)
                    df_processed['SOURCE_SHEET'] = sheet_name 
                    all_individual_dfs[sheet_name] = df_processed
                else: all_individual_dfs[sheet_name] = pd.DataFrame() 
            except Exception as e_ws:
                print(f"    Error processing worksheet '{sheet_name}': {e_ws}")
                all_individual_dfs[sheet_name] = pd.DataFrame()
        
        dfs_to_concat = [all_individual_dfs[name] for name in raw_sheet_names_list if name in all_individual_dfs and not all_individual_dfs[name].empty]
        if dfs_to_concat:
            combined_df = pd.concat(dfs_to_concat, ignore_index=True, sort=False)
            if EXPECTED_COL_ENROLLED_DATE in combined_df.columns and not pd.api.types.is_datetime64_any_dtype(combined_df[EXPECTED_COL_ENROLLED_DATE]):
                combined_df[EXPECTED_COL_ENROLLED_DATE] = pd.to_datetime(combined_df[EXPECTED_COL_ENROLLED_DATE], errors='coerce')
            return combined_df, all_individual_dfs
        return pd.DataFrame(), all_individual_dfs
    except Exception as e_open:
        print(f"Error with spreadsheet '{spreadsheet_title}': {e_open}")
        return pd.DataFrame(), {}

# --- Visualization Creation Functions ---
def create_bar_chart(df, title, x_col, y_col, color_col=None, color_map=None):
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        return go.Figure().update_layout(title_text=f"{title} (No data/missing cols)")
    fig = px.bar(df, x=x_col, y=y_col, color=color_col, color_discrete_map=color_map, title=title, template='plotly_white', text=y_col)
    fig.update_layout(font_family="Arial", title_font_size=20, title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                     margin=dict(l=20,r=20,t=60,b=20), xaxis_title=None, yaxis_title=None, hovermode="x unified")
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside', marker_line_color='black', marker_line_width=1)
    return fig

def create_line_chart(df, title, x_col, y_col):
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        return go.Figure().update_layout(title_text=f"{title} (No data/missing cols)")
    fig = px.line(df, x=x_col, y=y_col, title=title, template='plotly_white', markers=True)
    fig.update_layout(font_family="Arial", title_font_size=20, title_x=0.5, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                     margin=dict(l=20,r=20,t=60,b=20), xaxis_title=None, yaxis_title=None, hovermode="x unified")
    fig.update_traces(line=dict(width=3), marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey')))
    return fig

def create_gauge_chart(value, min_val, max_val, title):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", 
        value=value, 
        domain={'x': [0, 1], 'y': [0, 1]}, 
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [min_val, max_val]}, 
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, min_val * 0.999], 'color': "lightgray"}, 
                {'range': [min_val, max_val*0.6], 'color': "orange"},
                {'range': [max_val*0.6, max_val*0.8], 'color': "yellow"}, 
                {'range': [max_val*0.8, max_val], 'color': "green"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': max_val*0.85}
        }
    ))
    fig.update_layout(font_family="Arial", margin=dict(l=20,r=20,t=60,b=20), height=300)
    return fig

def create_heatmap_chart(df, title_prefix, date_col='Date', value_col='Daily Active Enrollments'):
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return go.Figure().update_layout(title_text=f"{title_prefix} Heatmap (No data/missing cols)")
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        if df[date_col].isnull().all(): 
            return go.Figure().update_layout(title_text=f"{title_prefix} Heatmap (Date column invalid)")
    
    df_copy = df.copy()
    df_copy['DayOfWeek'] = df_copy[date_col].dt.day_name()
    df_copy['WeekOfYear'] = df_copy[date_col].dt.isocalendar().week
    heatmap_pivot = df_copy.pivot_table(index='DayOfWeek', columns='WeekOfYear', values=value_col, aggfunc='sum', fill_value=0)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_pivot.reindex(days_order).fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values, 
        x=heatmap_pivot.columns, 
        y=heatmap_pivot.index, 
        colorscale='Viridis', 
        hoverongaps=False, 
        text=heatmap_pivot.values, 
        hovertemplate='<b>%{y}</b>, Week %{x}<br>Enrollments: %{z}<extra></extra>'
    ))
    fig.update_layout(
        title=f"{title_prefix} - Enrollment Heatmap", 
        title_x=0.5, 
        xaxis_title="ISO Week of Year", 
        yaxis_title="Day of Week", 
        font_family="Arial", 
        margin=dict(l=50,r=20,t=80,b=50), 
        height=500
    )
    return fig

# --- Analysis Functions ---
def prepare_weekly_summary(combined_df, run_date=date.today()):
    required_cols = [EXPECTED_COL_ENROLLED_DATE, EXPECTED_COL_STATUS, EXPECTED_COL_AGENT]
    if combined_df.empty or not all(col in combined_df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in combined_df.columns]
        return pd.DataFrame([{"Message": f"Weekly summary: Data empty or missing: {missing}"}]), go.Figure()

    start_week, end_week = get_target_week_dates(run_date)
    week_number = start_week.isocalendar()[1]
    weekly_df = combined_df[(combined_df[EXPECTED_COL_ENROLLED_DATE].dt.date >= start_week) & 
                           (combined_df[EXPECTED_COL_ENROLLED_DATE].dt.date <= end_week)]
    active_weekly_sales_df = weekly_df[weekly_df[EXPECTED_COL_STATUS].isin(ACTIVE_SALE_STATUSES)]

    if active_weekly_sales_df.empty:
        return pd.DataFrame([{"Message": f"No active sales for Week {week_number}"}]), go.Figure().update_layout(title_text=f"Week {week_number} (No active sales)")
        
    agent_summary = active_weekly_sales_df.groupby(EXPECTED_COL_AGENT).size().reset_index(name='Active Enrollments')
    agent_summary = agent_summary.sort_values('Active Enrollments', ascending=False)
    fig_title = f"Week {week_number} ({start_week.strftime('%b %d')}-{end_week.strftime('%b %d')}) Active Performance"
    fig = create_bar_chart(agent_summary, fig_title, EXPECTED_COL_AGENT, 'Active Enrollments', color_col=EXPECTED_COL_AGENT, color_map=AGENT_COLORS)
    return agent_summary, fig

def prepare_monthly_tracker(combined_df, run_date=date.today()):
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

# --- Main execution block ---
if __name__ == "__main__":
    print(f"--- sheet_analyzer.py script run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    client = get_gspread_client(CREDENTIALS_FILE)
    
    if client:
        print("Fetching and combining data from Google Sheets...")
        combined_df, all_dfs = fetch_and_combine_data(client, SPREADSHEET_TITLE, RAW_DATA_SHEET_NAMES)
        
        if not combined_df.empty:
            output_csv_path = "C:\\Users\\Mijae\\OneDrive\\Desktop\\Python G-Docs\\processed_combined_data.csv"
            try:
                # Add CATEGORY column for better filtering in the app
                if EXPECTED_COL_STATUS in combined_df.columns:
                    # Define status categories for the app
                    active_terms = ["ACTIVE", "ENROLLED / ACTIVE", "ENROLLED/ACTIVE"]
                    nsf_terms = ["NSF", "ENROLLED / NSF PROBLEM", "ENROLLED/NSF"]
                    cancelled_terms = ["CANCELLED", "DROPPED", "PENDING CANCELLATION", "TERMINATED", "NEEDS ROL"]
                    
                    # Create CATEGORY column
                    combined_df['CATEGORY'] = 'OTHER'
                    
                    # Apply categorization using vectorized operations
                    combined_df.loc[combined_df[EXPECTED_COL_STATUS].isin(active_terms), 'CATEGORY'] = 'ACTIVE'
                    combined_df.loc[combined_df[EXPECTED_COL_STATUS].isin(nsf_terms), 'CATEGORY'] = 'NSF'
                    combined_df.loc[combined_df[EXPECTED_COL_STATUS].isin(cancelled_terms), 'CATEGORY'] = 'CANCELLED'
                    
                    # Handle partial matches for complex statuses
                    for term in active_terms:
                        mask = combined_df[EXPECTED_COL_STATUS].str.contains(term, case=False, na=False)
                        combined_df.loc[mask, 'CATEGORY'] = 'ACTIVE'
                    
                    for term in nsf_terms:
                        mask = combined_df[EXPECTED_COL_STATUS].str.contains(term, case=False, na=False)
                        combined_df.loc[mask, 'CATEGORY'] = 'NSF'
                    
                    for term in cancelled_terms:
                        mask = combined_df[EXPECTED_COL_STATUS].str.contains(term, case=False, na=False)
                        combined_df.loc[mask, 'CATEGORY'] = 'CANCELLED'
                
                # Save the processed data
                combined_df.to_csv(output_csv_path, index=False)
                print(f"\nSuccessfully saved combined data ({len(combined_df)} rows) to '{output_csv_path}'")
            except Exception as e_csv:
                print(f"Error saving data to CSV: {e_csv}")
        else:
            print("\nCombined DataFrame was empty. No CSV file was saved.")
    else:
        print("Could not establish gspread client. Data fetching skipped.")
        
    print(f"--- sheet_analyzer.py script run finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")