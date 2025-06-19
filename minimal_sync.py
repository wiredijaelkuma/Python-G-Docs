import gspread
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import os
import time

# Configuration
SPREADSHEET_TITLE = "Forth Py"
CREDENTIALS_FILE = 'credentials.json'

def get_gspread_client():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client

def load_and_clean_local_data():
    # Load Cordoba data
    cordoba_data = None
    cordoba_path = os.path.join("..\\Cordoba\\Cordoba_Data", "cordoba_sales_data.csv")
    if os.path.exists(cordoba_path):
        cordoba_data = pd.read_csv(cordoba_path)
        # Map columns
        if 'customer_id' in cordoba_data.columns:
            cordoba_data.rename(columns={'customer_id': 'Customer ID'}, inplace=True)
        elif 'CUSTOMER_ID' in cordoba_data.columns:
            cordoba_data.rename(columns={'CUSTOMER_ID': 'Customer ID'}, inplace=True)
            
        # Fix agent column mapping - check all possible column names
        if 'assigned_to' in cordoba_data.columns:
            cordoba_data.rename(columns={'assigned_to': 'Agent'}, inplace=True)
        elif 'ASSIGNED_TO' in cordoba_data.columns:
            cordoba_data.rename(columns={'ASSIGNED_TO': 'Agent'}, inplace=True)
        elif 'agent' in cordoba_data.columns:
            cordoba_data.rename(columns={'agent': 'Agent'}, inplace=True)
        elif 'AGENT' in cordoba_data.columns:
            cordoba_data.rename(columns={'AGENT': 'Agent'}, inplace=True)
            
        if 'submitted_date' in cordoba_data.columns:
            cordoba_data.rename(columns={'submitted_date': 'Enrolled Date'}, inplace=True)
        elif 'SUBMITTED_DATE' in cordoba_data.columns:
            cordoba_data.rename(columns={'SUBMITTED_DATE': 'Enrolled Date'}, inplace=True)
            
        if 'status' in cordoba_data.columns:
            cordoba_data.rename(columns={'status': 'Status'}, inplace=True)
        elif 'STATUS' in cordoba_data.columns:
            cordoba_data.rename(columns={'STATUS': 'Status'}, inplace=True)
        
        # Ensure all required columns exist
        if 'Customer ID' not in cordoba_data.columns:
            cordoba_data['Customer ID'] = range(1, len(cordoba_data) + 1)
        if 'Agent' not in cordoba_data.columns:
            cordoba_data['Agent'] = ""
        if 'Enrolled Date' not in cordoba_data.columns:
            cordoba_data['Enrolled Date'] = datetime.now().strftime('%Y-%m-%d')
        if 'Status' not in cordoba_data.columns:
            cordoba_data['Status'] = "ACTIVE"
            
        # Simplify status
        cordoba_data['Status'] = cordoba_data['Status'].astype(str).str.upper()
        cordoba_data['Status'] = cordoba_data['Status'].replace({
            'ENROLLED/ACTIVE': 'ACTIVE',
            'ENROLLED / ACTIVE': 'ACTIVE',
            'ENROLLED ACTIVE': 'ACTIVE',
            'ENROLLED/NSF': 'NSF',
            'ENROLLED / NSF': 'NSF',
            'ENROLLED NSF': 'NSF',
            'ENROLLED/CANCELLED': 'CANCELLED',
            'ENROLLED / CANCELLED': 'CANCELLED',
            'ENROLLED CANCELLED': 'CANCELLED',
            'WAITING FIRST PAYMENT': 'ACTIVE'
        })
        
        # Keep only essential columns
        cordoba_data = cordoba_data[['Customer ID', 'Agent', 'Enrolled Date', 'Status']]
        
        # Remove duplicates
        cordoba_data.drop_duplicates(subset=['Customer ID'], keep='first', inplace=True)
        
        # Fill NaN values
        cordoba_data.fillna("", inplace=True)
        
        print(f"Loaded {len(cordoba_data)} Cordoba records")
    
    # Load PAC data
    pac_data = None
    pac_path = os.path.join("..\\Cordoba\\PAC_Data", "pac_sales_data.csv")
    if os.path.exists(pac_path):
        pac_data = pd.read_csv(pac_path)
        # Map columns
        if 'customer_id' in pac_data.columns:
            pac_data.rename(columns={'customer_id': 'Customer ID'}, inplace=True)
        elif 'CUSTOMER_ID' in pac_data.columns:
            pac_data.rename(columns={'CUSTOMER_ID': 'Customer ID'}, inplace=True)
            
        # Fix agent column mapping - check all possible column names
        if 'agent_name' in pac_data.columns:
            pac_data.rename(columns={'agent_name': 'Agent'}, inplace=True)
        elif 'AGENT_NAME' in pac_data.columns:
            pac_data.rename(columns={'AGENT_NAME': 'Agent'}, inplace=True)
        elif 'assigned_to' in pac_data.columns:
            pac_data.rename(columns={'assigned_to': 'Agent'}, inplace=True)
        elif 'ASSIGNED_TO' in pac_data.columns:
            pac_data.rename(columns={'ASSIGNED_TO': 'Agent'}, inplace=True)
        elif 'agent' in pac_data.columns:
            pac_data.rename(columns={'agent': 'Agent'}, inplace=True)
        elif 'AGENT' in pac_data.columns:
            pac_data.rename(columns={'AGENT': 'Agent'}, inplace=True)
            
        if 'enrollment_date' in pac_data.columns:
            pac_data.rename(columns={'enrollment_date': 'Enrolled Date'}, inplace=True)
        elif 'ENROLLMENT_DATE' in pac_data.columns:
            pac_data.rename(columns={'ENROLLMENT_DATE': 'Enrolled Date'}, inplace=True)
        elif 'submitted_date' in pac_data.columns:
            pac_data.rename(columns={'submitted_date': 'Enrolled Date'}, inplace=True)
        elif 'SUBMITTED_DATE' in pac_data.columns:
            pac_data.rename(columns={'SUBMITTED_DATE': 'Enrolled Date'}, inplace=True)
            
        if 'status' in pac_data.columns:
            pac_data.rename(columns={'status': 'Status'}, inplace=True)
        elif 'STATUS' in pac_data.columns:
            pac_data.rename(columns={'STATUS': 'Status'}, inplace=True)
        
        # Ensure all required columns exist
        if 'Customer ID' not in pac_data.columns:
            pac_data['Customer ID'] = range(1001, 1001 + len(pac_data))
        if 'Agent' not in pac_data.columns:
            pac_data['Agent'] = ""
        if 'Enrolled Date' not in pac_data.columns:
            pac_data['Enrolled Date'] = datetime.now().strftime('%Y-%m-%d')
        if 'Status' not in pac_data.columns:
            pac_data['Status'] = "ACTIVE"
            
        # Simplify status
        pac_data['Status'] = pac_data['Status'].astype(str).str.upper()
        pac_data['Status'] = pac_data['Status'].replace({
            'ENROLLED/ACTIVE': 'ACTIVE',
            'ENROLLED / ACTIVE': 'ACTIVE',
            'ENROLLED ACTIVE': 'ACTIVE',
            'ENROLLED/NSF': 'NSF',
            'ENROLLED / NSF': 'NSF',
            'ENROLLED NSF': 'NSF',
            'ENROLLED/CANCELLED': 'CANCELLED',
            'ENROLLED / CANCELLED': 'CANCELLED',
            'ENROLLED CANCELLED': 'CANCELLED',
            'WAITING FIRST PAYMENT': 'ACTIVE'
        })
        
        # Keep only essential columns
        pac_data = pac_data[['Customer ID', 'Agent', 'Enrolled Date', 'Status']]
        
        # Remove duplicates
        pac_data.drop_duplicates(subset=['Customer ID'], keep='first', inplace=True)
        
        # Fill NaN values
        pac_data.fillna("", inplace=True)
        
        print(f"Loaded {len(pac_data)} PAC records")
    
    return cordoba_data, pac_data

def update_google_sheets(client, cordoba_data, pac_data):
    try:
        sheet = client.open(SPREADSHEET_TITLE)
        
        # Update Cordoba sheet
        if cordoba_data is not None:
            try:
                worksheet = sheet.worksheet("Cordoba")
                worksheet.clear()
                print("Cleared existing Cordoba worksheet")
            except:
                worksheet = sheet.add_worksheet(title="Cordoba", rows=len(cordoba_data)+10, cols=5)
                print("Created new Cordoba worksheet")
            
            # Convert all values to strings to avoid JSON errors
            cordoba_values = cordoba_data.astype(str).values.tolist()
            
            # Upload data
            worksheet.update([['Customer ID', 'Agent', 'Enrolled Date', 'Status']] + cordoba_values)
            print(f"Updated Cordoba sheet with {len(cordoba_data)} records")
            time.sleep(5)
        
        # Update PAC sheet
        if pac_data is not None:
            try:
                worksheet = sheet.worksheet("PAC")
                worksheet.clear()
                print("Cleared existing PAC worksheet")
            except:
                worksheet = sheet.add_worksheet(title="PAC", rows=len(pac_data)+10, cols=5)
                print("Created new PAC worksheet")
            
            # Convert all values to strings to avoid JSON errors
            pac_values = pac_data.astype(str).values.tolist()
            
            # Upload data
            worksheet.update([['Customer ID', 'Agent', 'Enrolled Date', 'Status']] + pac_values)
            print(f"Updated PAC sheet with {len(pac_data)} records")
            time.sleep(5)
        
        return True
    except Exception as e:
        print(f"Error updating Google Sheets: {e}")
        return False

def fetch_and_combine_data(client):
    try:
        sheet = client.open(SPREADSHEET_TITLE)
        all_data = []
        
        # Fetch data from each sheet
        for sheet_name in ["PAC", "MLG", "ELP", "Cordoba"]:
            try:
                worksheet = sheet.worksheet(sheet_name)
                data = worksheet.get_all_values()
                
                if len(data) > 1:
                    headers = data[0]
                    rows = data[1:]
                    
                    # Create DataFrame
                    df = pd.DataFrame(rows, columns=headers)
                    
                    # Add source column if needed for debugging
                    # df['Source'] = sheet_name
                    
                    all_data.append(df)
            except Exception as e:
                print(f"Error fetching {sheet_name} data: {e}")
        
        if all_data:
            # Combine all data
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Ensure consistent column names
            for col in combined_df.columns:
                if col.upper() == 'CUSTOMER ID':
                    combined_df.rename(columns={col: 'Customer ID'}, inplace=True)
                elif col.upper() == 'AGENT':
                    combined_df.rename(columns={col: 'Agent'}, inplace=True)
                elif col.upper() == 'ENROLLED DATE':
                    combined_df.rename(columns={col: 'Enrolled Date'}, inplace=True)
                elif col.upper() == 'STATUS':
                    combined_df.rename(columns={col: 'Status'}, inplace=True)
            
            # Ensure all required columns exist
            for col in ['Customer ID', 'Agent', 'Enrolled Date', 'Status']:
                if col not in combined_df.columns:
                    combined_df[col] = ""
            
            # Keep only essential columns
            combined_df = combined_df[['Customer ID', 'Agent', 'Enrolled Date', 'Status']]
            
            # Remove duplicates
            combined_df.drop_duplicates(subset=['Customer ID'], keep='first', inplace=True)
            
            # Fill NaN values
            combined_df.fillna("", inplace=True)
            
            return combined_df
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error combining data: {e}")
        return pd.DataFrame()

def main():
    print(f"--- Minimal sync started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # Load and clean local data
    cordoba_data, pac_data = load_and_clean_local_data()
    
    # Connect to Google Sheets
    client = get_gspread_client()
    
    # Update Google Sheets
    if client:
        update_google_sheets(client, cordoba_data, pac_data)
        
        # Fetch and combine all data
        combined_df = fetch_and_combine_data(client)
        
        if not combined_df.empty:
            # Save combined data
            combined_df.to_csv("processed_combined_data.csv", index=False)
            print(f"Saved {len(combined_df)} records to processed_combined_data.csv")
        else:
            print("No data to save")
    else:
        print("Failed to connect to Google Sheets")
    
    print(f"--- Minimal sync completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

if __name__ == "__main__":
    main()