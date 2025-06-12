"""
Minimal Commission Tab
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_commission_tab(df_filtered, COLORS):
    """Render the commission tab with minimal functionality"""
    st.header("Commission Dashboard")
    
    try:
        # Read CSV directly with specific column names
        df = pd.read_csv("comissions.csv", header=0)
        
        # Create a clean dataframe with just the data we need
        data = []
        
        # Process even columns (0-5)
        for i in range(len(df)):
            if pd.notna(df.iloc[i, 1]) and df.iloc[i, 1] != "":  # Check if agent name exists
                data.append({
                    'CustomerID': df.iloc[i, 0],
                    'AgentName': df.iloc[i, 1],
                    'PaymentID': df.iloc[i, 2],
                    'Status': df.iloc[i, 3],
                    'PaymentDate': df.iloc[i, 4],
                    'ClearedDate': df.iloc[i, 5]
                })
        
        # Process odd columns (6-11)
        for i in range(len(df)):
            if pd.notna(df.iloc[i, 7]) and df.iloc[i, 7] != "":  # Check if agent name exists
                data.append({
                    'CustomerID': df.iloc[i, 6],
                    'AgentName': df.iloc[i, 7],
                    'PaymentID': df.iloc[i, 8],
                    'Status': df.iloc[i, 9],
                    'PaymentDate': df.iloc[i, 10],
                    'ClearedDate': df.iloc[i, 11]
                })
        
        # Convert to dataframe
        payments_df = pd.DataFrame(data)
        
        # Convert dates
        payments_df['PaymentDate'] = pd.to_datetime(payments_df['PaymentDate'], errors='coerce')
        payments_df['ClearedDate'] = pd.to_datetime(payments_df['ClearedDate'], errors='coerce')
        
        # Simple tab for recent cleared payments
        st.subheader("Recent Cleared Payments")
        
        # Filter for cleared payments only
        cleared_payments = payments_df[payments_df['Status'].str.contains('Cleared', na=False)]
        
        # Sort by cleared date (most recent first)
        cleared_payments = cleared_payments.sort_values('ClearedDate', ascending=False)
        
        # Format dates for display
        cleared_payments_display = cleared_payments.copy()
        cleared_payments_display['PaymentDate'] = cleared_payments_display['PaymentDate'].dt.strftime('%Y-%m-%d')
        cleared_payments_display['ClearedDate'] = cleared_payments_display['ClearedDate'].dt.strftime('%Y-%m-%d')
        
        # Display the table
        st.dataframe(cleared_payments_display, use_container_width=True)
        
        # Simple agent summary
        st.subheader("Agent Summary")
        
        # Count cleared payments by agent
        agent_counts = cleared_payments.groupby('AgentName').size().reset_index()
        agent_counts.columns = ['Agent', 'Cleared Payments']
        agent_counts = agent_counts.sort_values('Cleared Payments', ascending=False)
        
        # Display agent summary
        st.dataframe(agent_counts, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())