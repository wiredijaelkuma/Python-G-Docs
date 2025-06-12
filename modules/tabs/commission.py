"""
Minimal Commission Tab
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def load_commission_data():
    """Load and process commission data"""
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
        
        return payments_df
    except Exception as e:
        st.error(f"Error loading commission data: {str(e)}")
        return pd.DataFrame()

def render_agent_summary(payments_df):
    """Render agent summary with payment status by unique ID"""
    st.subheader("Agent Payment Summary")
    
    # Get list of agents
    agents = sorted(payments_df['AgentName'].unique())
    
    # Agent selector
    selected_agent = st.selectbox("Select Agent", agents)
    
    # Filter data for selected agent
    agent_data = payments_df[payments_df['AgentName'] == selected_agent]
    
    # Get unique customer IDs for this agent
    customer_ids = agent_data['CustomerID'].unique()
    
    # Create summary for each customer
    customer_summary = []
    for cid in customer_ids:
        customer_payments = agent_data[agent_data['CustomerID'] == cid]
        
        # Count payment statuses
        cleared = sum(customer_payments['Status'].str.contains('Cleared', na=False))
        nsf = sum(customer_payments['Status'].str.contains('NSF|Returned', na=False))
        pending = sum(customer_payments['Status'].str.contains('Pending', na=False))
        rejected = sum(customer_payments['Status'].str.contains('Rejected', na=False))
        
        customer_summary.append({
            'CustomerID': cid,
            'TotalPayments': len(customer_payments),
            'Cleared': cleared,
            'NSF': nsf,
            'Pending': pending,
            'Rejected': rejected,
            'FirstPayment': customer_payments['PaymentDate'].min(),
            'LastPayment': customer_payments['PaymentDate'].max()
        })
    
    # Convert to dataframe
    if customer_summary:
        summary_df = pd.DataFrame(customer_summary)
        
        # Format dates
        summary_df['FirstPayment'] = summary_df['FirstPayment'].dt.strftime('%Y-%m-%d')
        summary_df['LastPayment'] = summary_df['LastPayment'].dt.strftime('%Y-%m-%d')
        
        # Sort by total payments
        summary_df = summary_df.sort_values('TotalPayments', ascending=False)
        
        # Display summary
        st.dataframe(summary_df, use_container_width=True)
        
        # Show overall stats
        st.subheader(f"Overall Stats for {selected_agent}")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Customers", len(customer_ids))
        col2.metric("Total Payments", len(agent_data))
        col3.metric("Cleared Payments", sum(summary_df['Cleared']))
        col4.metric("NSF Payments", sum(summary_df['NSF']))
    else:
        st.info(f"No data found for agent: {selected_agent}")

def render_recent_cleared(payments_df):
    """Render recent cleared payments"""
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
    
    # Agent summary
    st.subheader("Agent Summary")
    
    # Count cleared payments by agent
    agent_counts = cleared_payments.groupby('AgentName').size().reset_index()
    agent_counts.columns = ['Agent', 'Cleared Payments']
    agent_counts = agent_counts.sort_values('Cleared Payments', ascending=False)
    
    # Display agent summary
    st.dataframe(agent_counts, use_container_width=True)

def render_commission_tab(df_filtered, COLORS):
    """Render the commission tab"""
    st.header("Commission Dashboard")
    
    try:
        # Load commission data
        payments_df = load_commission_data()
        
        if payments_df.empty:
            st.error("Could not load commission data.")
            return
        
        # Create tabs
        tabs = st.tabs(["Agent Summary", "Recent Cleared Payments"])
        
        # Tab 1: Agent Summary
        with tabs[0]:
            render_agent_summary(payments_df)
        
        # Tab 2: Recent Cleared Payments
        with tabs[1]:
            render_recent_cleared(payments_df)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())