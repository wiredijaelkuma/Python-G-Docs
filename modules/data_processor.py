"""
Data Processing and Normalization Module
"""
import pandas as pd
import streamlit as st
from datetime import datetime

def normalize_dataframe(df):
    """
    Normalize dataframe for consistent processing across all modules
    """
    if df is None or df.empty:
        return df
    
    # Make a copy to avoid modifying original
    df_clean = df.copy()
    
    # Normalize text columns to uppercase and strip whitespace
    text_columns = [
        'STATUS', 'Status', 'CATEGORY', 'Category', 
        'AGENT', 'Agent', 'SOURCE_SHEET', 'Source_Sheet'
    ]
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.upper().str.strip()
    
    # Handle date columns - dates should already be properly formatted from Google Sheets
    date_columns = [
        'ENROLLED_DATE', 'ENROLLED DATE', 'Enrolled Date', 'Enrolled_Date',
        'PROCESSED DATE', 'Processed Date', 
        'CLEARED DATE', 'Cleared Date'
    ]
    for col in date_columns:
        if col in df_clean.columns and not pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Standardize category values if needed
    if 'CATEGORY' not in df_clean.columns:
        # Find status column (could be uppercase or regular case)
        status_col = None
        if 'STATUS' in df_clean.columns:
            status_col = 'STATUS'
        elif 'Status' in df_clean.columns:
            status_col = 'Status'
            
        if status_col:
            # Create CATEGORY column based on STATUS
            df_clean['CATEGORY'] = 'OTHER'
            df_clean.loc[df_clean[status_col].str.contains('ACTIVE|ENROLLED|active|enrolled', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
            df_clean.loc[df_clean[status_col].str.contains('NSF|nsf', case=False, na=False), 'CATEGORY'] = 'NSF'
            df_clean.loc[df_clean[status_col].str.contains('CANCEL|DROP|TERMIN|cancel|drop|termin', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
    
    return df_clean

def get_status_filter_mask(df, show_active=True, show_nsf=True, show_cancelled=True, show_other=True):
    """
    Create a boolean mask for status filtering
    """
    # Find category column (could be uppercase or regular case)
    category_col = None
    if 'CATEGORY' in df.columns:
        category_col = 'CATEGORY'
    elif 'Category' in df.columns:
        category_col = 'Category'
        
    if not category_col:
        return pd.Series(True, index=df.index)
    
    status_filter = []
    if show_active: status_filter.append('ACTIVE')
    if show_nsf: status_filter.append('NSF')
    if show_cancelled: status_filter.append('CANCELLED')
    if show_other: status_filter.append('OTHER')
    
    if not status_filter:
        return pd.Series(False, index=df.index)
    
    return df[category_col].isin(status_filter)

def calculate_metrics(df):
    """
    Calculate standard metrics for any dataframe
    """
    if df.empty:
        return {
            'total': 0,
            'active': 0,
            'cancelled': 0,
            'nsf': 0,
            'other': 0,
            'active_rate': 0,
            'cancelled_rate': 0
        }
    
    # Find category column (could be uppercase or regular case)
    category_col = None
    if 'CATEGORY' in df.columns:
        category_col = 'CATEGORY'
    elif 'Category' in df.columns:
        category_col = 'Category'
        
    total = len(df)
    
    if category_col:
        active = len(df[df[category_col] == 'ACTIVE'])
        cancelled = len(df[df[category_col] == 'CANCELLED'])
        nsf = len(df[df[category_col] == 'NSF'])
        other = len(df[df[category_col] == 'OTHER'])
    else:
        active = 0
        cancelled = 0
        nsf = 0
        other = 0
    
    active_rate = (active / total * 100) if total > 0 else 0
    cancelled_rate = (cancelled / total * 100) if total > 0 else 0
    
    return {
        'total': total,
        'active': active,
        'cancelled': cancelled,
        'nsf': nsf,
        'other': other,
        'active_rate': active_rate,
        'cancelled_rate': cancelled_rate
    }

def safe_date_range(df, date_column='ENROLLED_DATE'):
    """
    Get safe date range from dataframe
    """
    # Try different possible date column names
    date_columns = ['ENROLLED_DATE', 'Enrolled_Date', 'ENROLLED DATE', 'Enrolled Date']
    
    # Find the first available date column
    found_date_column = None
    for col in date_columns:
        if col in df.columns:
            found_date_column = col
            break
    
    if not found_date_column or df.empty:
        from datetime import date
        today = datetime.now().date()
        return date(2024, 1, 1), today
    
    try:
        min_date = df[found_date_column].min().date()
        max_date = df[found_date_column].max().date()
        return min_date, max_date
    except:
        from datetime import date
        today = datetime.now().date()
        return date(2024, 1, 1), today