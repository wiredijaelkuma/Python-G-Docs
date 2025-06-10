import pandas as pd
import streamlit as st
import time
from datetime import datetime

@st.cache_data(ttl=1800)
def load_csv_data(file_path="processed_combined_data.csv"):
    """
    Fast loading function for small CSV files that are frequently updated
    """
    try:
        # Get file modification time to track updates
        last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Use optimized CSV reading with explicit dtypes
        df = pd.read_csv(
            file_path,
            parse_dates=['ENROLLED_DATE'],
            dtype={
                'STATUS': 'category',
                'SOURCE_SHEET': 'category'
            }
        )
        
        # Standardize column names
        df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]
        
        # Add minimal derived columns
        if 'ENROLLED_DATE' in df.columns:
            df['MONTH_YEAR'] = df['ENROLLED_DATE'].dt.strftime('%Y-%m')
        
        # Simple status categorization
        if 'STATUS' in df.columns and 'CATEGORY' not in df.columns:
            df['CATEGORY'] = 'OTHER'
            df.loc[df['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            df.loc[df['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
            df.loc[df['STATUS'].str.contains('CANCEL|DROP|TERMIN', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
            df['CATEGORY'] = df['CATEGORY'].astype('category')
        
        print(f"Data loaded successfully at {last_modified}")
        return df, None
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(), str(e)