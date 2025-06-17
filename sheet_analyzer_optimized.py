import gspread
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- Configuration Variables ---
SPREADSHEET_TITLE = "Forth Py"
CREDENTIALS_FILE = 'credentials.json' 
RAW_DATA_SHEET_NAMES = ["PAC", "MLG", "ELP", "Cordoba"]
PAC_RAW_SHEET_NAME = "PAC"
EXPECTED_COL_CUSTOMER_ID = "CUSTOMER ID"
EXPECTED_COL_AGENT = "AGENT"
EXPECTED_COL_ENROLLED_DATE = "ENROLLED DATE"
EXPECTED_COL_STATUS = "STATUS" 

# --- Status Configuration ---
ACTIVE_SALE_STATUSES = ["ACTIVE", "ENROLLED / ACTIVE", "ENROLLED/ACTIVE"] 
POTENTIAL_RESCUE_STATUSES = ["NSF", "ENROLLED / NSF PROBLEM", "ENROLLED/NSF"]

# --- Helper Function for Standardization ---
def standardize_and_prepare_df(df, sheet_name_for_logging):
    if df.empty:
        return df
    df.columns = [str(col).strip().upper() for col in df.columns]
    
    if EXPECTED_COL_ENROLLED_DATE in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df[EXPECTED_COL_ENROLLED_DATE]):
            df[EXPECTED_COL_ENROLLED_DATE] = pd.to_datetime(df[EXPECTED_COL_ENROLLED_DATE], errors='coerce')
    
    if EXPECTED_COL_STATUS in df.columns:
        df[EXPECTED_COL_STATUS] = df[EXPECTED_COL_STATUS].astype('category')
    return df

# --- Core Data Fetching and Processing Function ---
def get_gspread_client(credentials_file=CREDENTIALS_FILE):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        print("gspread client authentication successful.")
        return client
    except Exception as e:
        print(f"Error during gspread client authentication: {e}")
        return None

def fetch_and_combine_data(gspread_client, spreadsheet_title, raw_sheet_names_list):
    if gspread_client is None: 
        return pd.DataFrame(), {}
    
    all_individual_dfs = {}
    try:
        sheet_gspread_obj = gspread_client.open(spreadsheet_title)
        for sheet_name in raw_sheet_names_list:
            try:
                worksheet = sheet_gspread_obj.worksheet(sheet_name)
                
                # Get all values including headers
                all_values = worksheet.get_all_values()
                
                if len(all_values) > 1:  # At least headers and one row
                    # Get headers from first row
                    headers = all_values[0]
                    
                    # Fix duplicate/empty headers by adding column numbers
                    fixed_headers = []
                    header_counts = {}
                    
                    for i, header in enumerate(headers):
                        if header == "" or header is None:
                            header = f"Column_{i+1}"
                        
                        if header in header_counts:
                            header_counts[header] += 1
                            header = f"{header}_{header_counts[header]}"
                        else:
                            header_counts[header] = 0
                            
                        fixed_headers.append(header)
                    
                    # Create DataFrame with fixed headers
                    df = pd.DataFrame(all_values[1:], columns=fixed_headers)
                    df_processed = standardize_and_prepare_df(df.copy(), sheet_name)
                    df_processed['SOURCE_SHEET'] = sheet_name 
                    all_individual_dfs[sheet_name] = df_processed
                else: 
                    all_individual_dfs[sheet_name] = pd.DataFrame() 
            except Exception as e_ws:
                print(f"    Error processing worksheet '{sheet_name}': {e_ws}")
                all_individual_dfs[sheet_name] = pd.DataFrame()
        
        dfs_to_concat = [all_individual_dfs[name] for name in raw_sheet_names_list if name in all_individual_dfs and not all_individual_dfs[name].empty]
        if dfs_to_concat:
            combined_df = pd.concat(dfs_to_concat, ignore_index=True, sort=False)
            
            # Convert date column once after concatenation
            if EXPECTED_COL_ENROLLED_DATE in combined_df.columns:
                combined_df[EXPECTED_COL_ENROLLED_DATE] = pd.to_datetime(combined_df[EXPECTED_COL_ENROLLED_DATE], errors='coerce')
            
            return combined_df, all_individual_dfs
        return pd.DataFrame(), all_individual_dfs
    except Exception as e_open:
        print(f"Error with spreadsheet '{spreadsheet_title}': {e_open}")
        return pd.DataFrame(), {}

# --- Main execution block ---
if __name__ == "__main__":
    print(f"--- sheet_analyzer_optimized.py script run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    client = get_gspread_client(CREDENTIALS_FILE)
    
    if client:
        print("Fetching and combining data from Google Sheets...")
        combined_df, all_dfs = fetch_and_combine_data(client, SPREADSHEET_TITLE, RAW_DATA_SHEET_NAMES)
        
        if not combined_df.empty:
            output_csv_path = "processed_combined_data.csv"
            try:
                # Add CATEGORY column for better filtering in the app
                if EXPECTED_COL_STATUS in combined_df.columns:
                    # Create CATEGORY column using efficient vectorized operations
                    combined_df['CATEGORY'] = 'OTHER'
                    
                    # Use more efficient string operations
                    combined_df.loc[combined_df[EXPECTED_COL_STATUS].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
                    combined_df.loc[combined_df[EXPECTED_COL_STATUS].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
                    combined_df.loc[combined_df[EXPECTED_COL_STATUS].str.contains('CANCEL|DROP|TERMIN|NEEDS ROL', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
                    
                    # Convert to category for memory efficiency
                    combined_df['CATEGORY'] = combined_df['CATEGORY'].astype('category')
                
                # Save the processed data
                combined_df.to_csv(output_csv_path, index=False)
                print(f"\nSuccessfully saved combined data ({len(combined_df)} rows) to '{output_csv_path}'")
            except Exception as e_csv:
                print(f"Error saving data to CSV: {e_csv}")
        else:
            print("\nCombined DataFrame was empty. No CSV file was saved.")
    else:
        print("Could not establish gspread client. Data fetching skipped.")
        
    print(f"--- sheet_analyzer_optimized.py script run finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")