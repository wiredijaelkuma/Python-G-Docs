"""
Google Sheets connector
"""
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

SPREADSHEET_TITLE = "Forth Py"
CREDENTIALS_FILE = 'credentials.json'
RAW_SHEET_NAMES = ["PAC", "MLG", "ELP", "Cordoba", "Comission"]

def get_credentials():
    try:
        creds = dict(st.secrets["gcp_service_account"])
        if "universe_domain" not in creds:
            creds["universe_domain"] = "googleapis.com"
        return creds
    except Exception:
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                if "universe_domain" not in creds:
                    creds["universe_domain"] = "googleapis.com"
                return creds
        except Exception as e:
            st.error(f"Error loading credentials: {e}")
            return None

@st.cache_data(ttl=300)
def get_gspread_client():
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = get_credentials()
        
        if not creds_dict:
            return None, "Failed to load credentials"
            
        try:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
        except ImportError:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp:
                json.dump(creds_dict, temp)
                temp_name = temp.name
            
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(temp_name, scope)
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
            
        client = gspread.authorize(creds)
        return client, None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=300)
def fetch_data_from_sheet(spreadsheet_title=SPREADSHEET_TITLE, sheet_names=RAW_SHEET_NAMES):
    client, error = get_gspread_client()
    
    if error:
        return pd.DataFrame(), f"Authentication error: {error}"
    
    try:
        sheet = client.open(spreadsheet_title)
        all_dfs = []
        
        for sheet_name in sheet_names:
            try:
                worksheet = sheet.worksheet(sheet_name)
                data = worksheet.get_all_values()
                
                if len(data) > 1:
                    headers = data[0]
                    rows = data[1:]
                    
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
                    
                    df = pd.DataFrame(rows, columns=fixed_headers)
                    df.columns = [str(col).strip().upper() for col in df.columns]
                    df['SOURCE_SHEET'] = sheet_name
                    all_dfs.append(df)
                else:
                    st.warning(f"Worksheet '{sheet_name}' is empty or has no data rows")
            except Exception as e:
                st.warning(f"Error fetching data from worksheet '{sheet_name}': {e}")
        
        if not all_dfs:
            return pd.DataFrame(), "No data found in any worksheet"
        
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Process date columns
        if 'ENROLLED DATE' in combined_df.columns:
            combined_df['ENROLLED DATE'] = pd.to_datetime(combined_df['ENROLLED DATE'], errors='coerce')
            combined_df.rename(columns={'ENROLLED DATE': 'ENROLLED_DATE'}, inplace=True)
        
        if 'PROCESSED DATE' in combined_df.columns:
            combined_df['PROCESSED DATE'] = pd.to_datetime(combined_df['PROCESSED DATE'], errors='coerce')
            
        if 'CLEARED DATE' in combined_df.columns:
            combined_df['CLEARED DATE'] = pd.to_datetime(combined_df['CLEARED DATE'], errors='coerce')
        
        # Add category column
        if 'STATUS' in combined_df.columns:
            combined_df['CATEGORY'] = 'OTHER'
            combined_df.loc[combined_df['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            combined_df.loc[combined_df['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            combined_df.loc[combined_df['STATUS'].str.contains('CANCEL|DROP|TERMIN|NEEDS ROL', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
        
        return combined_df, None
    except Exception as e:
        return pd.DataFrame(), str(e)