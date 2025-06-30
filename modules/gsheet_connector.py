"""
Streamlined Google Sheets connector for Streamlit Cloud deployment
"""
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import json

# Configuration constants
SPREADSHEET_TITLE = "Forth Py"
CREDENTIALS_FILE = 'credentials.json'
RAW_SHEET_NAMES = ["PAC", "MLG", "ELP", "Cordoba"]

def get_credentials():
    """Get credentials from local file or Streamlit secrets"""
    # First try Streamlit secrets
    try:
        creds = dict(st.secrets["gcp_service_account"])
        # Add universe_domain if missing (required by newer versions)
        if "universe_domain" not in creds:
            creds["universe_domain"] = "googleapis.com"
        return creds
    except Exception:
        # Fall back to local credentials file
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                # Add universe_domain if missing (required by newer versions)
                if "universe_domain" not in creds:
                    creds["universe_domain"] = "googleapis.com"
                return creds
        except Exception as e:
            st.error(f"Error loading credentials: {e}")
            return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_gspread_client():
    """Get an authorized Google Sheets client"""
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        
        # Get credentials from appropriate source
        creds_dict = get_credentials()
        
        if not creds_dict:
            return None, "Failed to load credentials"
            
        # Create credentials from dict
        try:
            # Try using google-auth (preferred for Streamlit Cloud)
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=scope
            )
        except ImportError:
            # Fall back to oauth2client
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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_data_from_sheet(spreadsheet_title=SPREADSHEET_TITLE, sheet_names=RAW_SHEET_NAMES):
    """Fetch and process data from Google Sheets"""
    # Add debug info
    st.write("Debug: Running on Streamlit Cloud:", 'STREAMLIT_SHARING_MODE' in os.environ or 'STREAMLIT_APP_ID' in os.environ)
    
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
                
                if len(data) > 1:  # Skip empty worksheets
                    headers = data[0]
                    rows = data[1:]
                    
                    # Fix duplicate/empty headers
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
                    
                    # Create DataFrame
                    df = pd.DataFrame(rows, columns=fixed_headers)
                    
                    # Standardize column names
                    df.columns = [str(col).strip().upper() for col in df.columns]
                    
                    # Add source column
                    df['SOURCE_SHEET'] = sheet_name
                    
                    all_dfs.append(df)
            except Exception as e:
                st.warning(f"Error fetching data from worksheet '{sheet_name}': {e}")
        
        if not all_dfs:
            return pd.DataFrame(), "No data found in any worksheet"
        
        # Combine all data
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Process date columns
        if 'ENROLLED DATE' in combined_df.columns:
            combined_df['ENROLLED DATE'] = pd.to_datetime(combined_df['ENROLLED DATE'], errors='coerce')
            # Rename to match app's expected column name
            combined_df.rename(columns={'ENROLLED DATE': 'ENROLLED_DATE'}, inplace=True)
        
        # Add category column if status exists
        if 'STATUS' in combined_df.columns:
            # Create CATEGORY column using efficient vectorized operations
            combined_df['CATEGORY'] = 'OTHER'
            combined_df.loc[combined_df['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            combined_df.loc[combined_df['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            combined_df.loc[combined_df['STATUS'].str.contains('CANCEL|DROP|TERMIN|NEEDS ROL', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
        
        return combined_df, None
    except Exception as e:
        return pd.DataFrame(), str(e)