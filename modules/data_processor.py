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
    text_columns = ['STATUS', 'CATEGORY', 'AGENT', 'SOURCE_SHEET']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.upper().str.strip()
    
    # Handle date columns - dates should already be properly formatted from Google Sheets
    date_columns = ['ENROLLED_DATE', 'ENROLLED DATE', 'PROCESSED DATE', 'CLEARED DATE']
    for col in date_columns:
        if col in df_clean.columns and not pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Standardize category values if needed
    if 'CATEGORY' not in df_clean.columns and 'STATUS' in df_clean.columns:
        # Create CATEGORY column based on STATUS
        df_clean['CATEGORY'] = 'OTHER'
        df_clean.loc[df_clean['STATUS'].str.contains('ACTIVE|ENROLLED', case=False, na=False), 'CATEGORY'] = 'ACTIVE'
        df_clean.loc[df_clean['STATUS'].str.contains('NSF', case=False, na=False), 'CATEGORY'] = 'NSF'
        df_clean.loc[df_clean['STATUS'].str.contains('CANCEL|DROP|TERMIN', case=False, na=False), 'CATEGORY'] = 'CANCELLED'
    
    return df_clean

def get_status_filter_mask(df, show_active=True, show_nsf=True, show_cancelled=True, show_other=True):
    """
    Create a boolean mask for status filtering
    """
    if 'CATEGORY' not in df.columns:
        return pd.Series(True, index=df.index)
    
    status_filter = []
    if show_active: status_filter.append('ACTIVE')
    if show_nsf: status_filter.append('NSF')
    if show_cancelled: status_filter.append('CANCELLED')
    if show_other: status_filter.append('OTHER')
    
    if not status_filter:
        return pd.Series(False, index=df.index)
    
    return df['CATEGORY'].isin(status_filter)

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
    
    total = len(df)
    active = len(df[df['CATEGORY'] == 'ACTIVE']) if 'CATEGORY' in df.columns else 0
    cancelled = len(df[df['CATEGORY'] == 'CANCELLED']) if 'CATEGORY' in df.columns else 0
    nsf = len(df[df['CATEGORY'] == 'NSF']) if 'CATEGORY' in df.columns else 0
    other = len(df[df['CATEGORY'] == 'OTHER']) if 'CATEGORY' in df.columns else 0
    
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
    if date_column not in df.columns or df.empty:
        from datetime import date
        today = datetime.now().date()
        return date(2024, 1, 1), today
    
    try:
        min_date = df[date_column].min().date()
        max_date = df[date_column].max().date()
        return min_date, max_date
    except:
        from datetime import date
        today = datetime.now().date()
        return date(2024, 1, 1), today