import gspread
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from oauth2client.service_account import ServiceAccountCredentials
import os
import time

# --- Configuration Variables ---
SPREADSHEET_TITLE = "Forth Py"
CREDENTIALS_FILE = 'credentials.json' 
RAW_DATA_SHEET_NAMES = ["PAC", "MLG", "ELP", "Cordoba"]
EXPECTED_COL_CUSTOMER_ID = "CUSTOMER ID"
EXPECTED_COL_AGENT = "AGENT"
EXPECTED_COL_ENROLLED_DATE = "ENROLLED DATE"
EXPECTED_COL_STATUS = "STATUS" 

# --- Status Configuration ---
ACTIVE_SALE_STATUSES = ["ACTIVE", "ENROLLED / ACTIVE", "ENROLLED/ACTIVE"] 
POTENTIAL_RESCUE_STATUSES = ["NSF", "ENROLLED / NSF PROBLEM", "ENROLLED/NSF"]

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
                    
                    # Standardize column names
                    df.columns = [str(col).strip().upper() for col in df.columns]
                    
                    # Add source column if not exists
                    if 'SOURCE_SHEET' not in df.columns:
                        df['SOURCE_SHEET'] = sheet_name
                    
                    # Convert date column
                    if EXPECTED_COL_ENROLLED_DATE in df.columns:
                        df[EXPECTED_COL_ENROLLED_DATE] = pd.to_datetime(df[EXPECTED_COL_ENROLLED_DATE], errors='coerce')
                    
                    # Add CATEGORY column for better filtering
                    if EXPECTED_COL_STATUS in df.columns:
                        df['CATEGORY'] = 'OTHER'
                        df.loc[df[EXPECTED_COL_STATUS].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
                        df.loc[df[EXPECTED_COL_STATUS].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
                        df.loc[df[EXPECTED_COL_STATUS].str.contains('CANCEL|DROP|TERMIN|NEEDS ROL', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
                    
                    all_individual_dfs[sheet_name] = df
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

def sync_local_data_to_google_sheet():
    """Sync local Cordoba/PAC data to Google Sheet without overwriting MLG/ELP data"""
    print("Starting bidirectional sync...")
    
    # Load local data from Cordoba directory
    local_data = {}
    
    # Load Cordoba sales data
    cordoba_sales_path = os.path.join("..\\Cordoba\\Cordoba_Data", "cordoba_sales_data.csv")
    if os.path.exists(cordoba_sales_path):
        try:
            cordoba_df = pd.read_csv(cordoba_sales_path)
            # Standardize column names
            cordoba_df.columns = [col.upper().replace(' ', '_') for col in cordoba_df.columns]
            # Add source column
            cordoba_df['SOURCE_SHEET'] = 'Cordoba'
            
            # Map columns to expected format
            if 'CUSTOMER_NAME' in cordoba_df.columns:
                cordoba_df['CUSTOMER_NAME'] = cordoba_df['CUSTOMER_NAME'].astype(str)
            if 'SUBMITTED_DATE' in cordoba_df.columns:
                cordoba_df['ENROLLED_DATE'] = pd.to_datetime(cordoba_df['SUBMITTED_DATE'], errors='coerce')
                cordoba_df[EXPECTED_COL_ENROLLED_DATE] = cordoba_df['ENROLLED_DATE']
            if 'STATUS' in cordoba_df.columns:
                cordoba_df['STATUS'] = cordoba_df['STATUS'].astype(str)
                # Simplify statuses for Streamlit
                cordoba_df.loc[cordoba_df["STATUS"].str.contains("WAITING|FIRST|PAYMENT", case=False, na=False), "STATUS"] = "ACTIVE"
            
            # Add CATEGORY column for better filtering
            cordoba_df['CATEGORY'] = 'OTHER'
            cordoba_df.loc[cordoba_df['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            cordoba_df.loc[cordoba_df['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            cordoba_df.loc[cordoba_df['STATUS'].str.contains('CANCEL|DROP|TERMIN|NEEDS ROL', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
            
            local_data['Cordoba'] = cordoba_df
            print(f"Loaded {len(cordoba_df)} Cordoba records")
        except Exception as e:
            print(f"Error loading Cordoba data: {e}")
    
    # Load PAC sales data (if available)
    pac_sales_path = os.path.join("..\\Cordoba\\PAC_Data", "pac_sales_data.csv")
    if os.path.exists(pac_sales_path):
        try:
            pac_df = pd.read_csv(pac_sales_path)
            # Standardize column names
            pac_df.columns = [col.upper().replace(' ', '_') for col in pac_df.columns]
            # Add source column
            pac_df['SOURCE_SHEET'] = 'PAC'
            
            # Map columns to expected format
            if 'CUSTOMER_NAME' in pac_df.columns:
                pac_df['CUSTOMER_NAME'] = pac_df['CUSTOMER_NAME'].astype(str)
            if 'SUBMITTED_DATE' in pac_df.columns:
                pac_df['ENROLLED_DATE'] = pd.to_datetime(pac_df['SUBMITTED_DATE'], errors='coerce')
                pac_df[EXPECTED_COL_ENROLLED_DATE] = pac_df['ENROLLED_DATE']
            if 'STATUS' in pac_df.columns:
                pac_df['STATUS'] = pac_df['STATUS'].astype(str)
                # Simplify statuses for Streamlit
                pac_df.loc[pac_df["STATUS"].str.contains("WAITING|FIRST|PAYMENT", case=False, na=False), "STATUS"] = "ACTIVE"
            
            # Add CATEGORY column for better filtering
            pac_df['CATEGORY'] = 'OTHER'
            pac_df.loc[pac_df['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            pac_df.loc[pac_df['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            pac_df.loc[pac_df['STATUS'].str.contains('CANCEL|DROP|TERMIN|NEEDS ROL', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
            
            local_data['PAC'] = pac_df
            print(f"Loaded {len(pac_df)} PAC records")
        except Exception as e:
            print(f"Error loading PAC data: {e}")
    
    # Connect to Google Sheets
    client = get_gspread_client()
    if not client:
        print("Failed to connect to Google Sheets")
        return False
        
    try:
        # Open the spreadsheet
        sheet = client.open(SPREADSHEET_TITLE)
        
        # Update only PAC and Cordoba data
        for sheet_name in ["PAC", "Cordoba"]:
            if sheet_name in local_data and not local_data[sheet_name].empty:
                source_df = local_data[sheet_name]
                
                # Get or create worksheet
                try:
                    worksheet = sheet.worksheet(sheet_name)
                    worksheet.clear()
                    print(f"Cleared existing {sheet_name} worksheet")
                except:
                    worksheet = sheet.add_worksheet(title=sheet_name, rows=len(source_df)+10, cols=20)
                    print(f"Created new {sheet_name} worksheet")
                
                # Upload data
                headers = source_df.columns.tolist()
                values = source_df.values.tolist()
                
                # Convert datetime objects to strings and handle NaN values
                for i, row in enumerate(values):
                    for j, val in enumerate(row):
                        # Handle NaN, None, NaT and other non-JSON compliant values first
                        if pd.isna(val) or val is None:
                            values[i][j] = ""
                        elif isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                            values[i][j] = ""
                        # Then handle valid datetime objects
                        elif isinstance(val, pd.Timestamp) or isinstance(val, datetime):
                            try:
                                values[i][j] = val.strftime('%Y-%m-%d')
                            except:
                                values[i][j] = ""
                
                worksheet.update([headers] + values)
                print(f"Updated {sheet_name} sheet with {len(source_df)} records")
                
                # Wait to avoid rate limits
                time.sleep(5)
        
        # Now fetch all data and combine
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
                print(f"Successfully saved combined data ({len(combined_df)} rows) to '{output_csv_path}'")
                return True
            except Exception as e_csv:
                print(f"Error saving data to CSV: {e_csv}")
                return False
        else:
            print("Combined DataFrame was empty. No CSV file was saved.")
            return False
            
    except Exception as e:
        print(f"Error syncing data: {e}")
        return False

if __name__ == "__main__":
    print(f"--- Bidirectional sync started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # Sync local data to Google Sheets and update combined CSV
    success = sync_local_data_to_google_sheet()
    
    if success:
        print("Bidirectional sync completed successfully!")
    else:
        print("Bidirectional sync encountered errors.")
        
    print(f"--- Bidirectional sync finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")