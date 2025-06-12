"""
Commission Tab Module - Analyzes agent commission data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def process_commission_data(file_path="comissions.csv"):
    """
    Process the commission CSV file which has an unusual structure with even/odd columns
    """
    try:
        # Read the raw CSV file
        df = pd.read_csv(file_path)
        
        # Extract even columns (columns 0-5)
        even_df = df.iloc[:, 0:6].copy()
        even_df.columns = ['AgentID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        # Extract odd columns (columns 6-11)
        odd_df = df.iloc[:, 6:12].copy()
        odd_df.columns = ['AgentID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        # Combine the dataframes, ignoring empty rows
        combined_df = pd.concat([even_df, odd_df], ignore_index=True)
        
        # Remove rows where AgentID is empty
        combined_df = combined_df[combined_df['AgentID'].notna() & (combined_df['AgentID'] != "")]
        
        # Convert dates to datetime
        combined_df['PaymentDate'] = pd.to_datetime(combined_df['PaymentDate'], errors='coerce')
        combined_df['ClearedDate'] = pd.to_datetime(combined_df['ClearedDate'], errors='coerce')
        
        # Create a week number and month for filtering
        combined_df['WeekNumber'] = combined_df['PaymentDate'].dt.isocalendar().week
        combined_df['Month'] = combined_df['PaymentDate'].dt.strftime('%Y-%m')
        
        # Create a payment status column
        combined_df['PaymentStatus'] = combined_df['Status'].apply(
            lambda x: 'Cleared' if 'Cleared' in str(x) else 'NSF' if 'NSF' in str(x) or 'Returned' in str(x) else 'Other'
        )
        
        return combined_df
    except Exception as e:
        st.error(f"Error processing commission data: {e}")
        return pd.DataFrame()

def render_commission_tab(df_filtered, COLORS):
    """
    Render the commission tab with agent performance metrics and payment trends
    """
    st.header("Commission Dashboard")
    
    # Process the commission data
    commission_df = process_commission_data()
    
    if commission_df.empty:
        st.error("Could not load commission data. Please check the CSV file format.")
        return
    
    # Create tabs for different views
    comm_tabs = st.tabs(["Cleared Payments", "ID Lifespan", "Agent Summary"])
    
    # Cleared Payments Tab - Focus on payments that should be paid to agents
    with comm_tabs[0]:
        st.subheader("Cleared Payments to be Paid")
        
        # Filter for only cleared payments
        cleared_df = commission_df[commission_df['PaymentStatus'] == 'Cleared'].copy()
        
        # Time period filter
        col1, col2 = st.columns(2)
        
        with col1:
            time_period = st.selectbox(
                "Time Period",
                ["Last Week", "Last 2 Weeks", "Last Month", "Last 3 Months", "All Time"],
                index=1
            )
            
            # Calculate date range based on selection
            today = datetime.now().date()
            if time_period == "Last Week":
                start_date = today - timedelta(days=7)
            elif time_period == "Last 2 Weeks":
                start_date = today - timedelta(days=14)
            elif time_period == "Last Month":
                start_date = today - timedelta(days=30)
            elif time_period == "Last 3 Months":
                start_date = today - timedelta(days=90)
            else:
                start_date = cleared_df['PaymentDate'].min().date()
            
            # Filter by date
            filtered_cleared = cleared_df[cleared_df['PaymentDate'].dt.date >= start_date]
        
        with col2:
            # Agent filter
            agents = sorted(cleared_df['AgentName'].unique())
            selected_agents = st.multiselect(
                "Select Agents",
                agents,
                default=agents
            )
            
            if selected_agents:
                filtered_cleared = filtered_cleared[filtered_cleared['AgentName'].isin(selected_agents)]
        
        # Display metrics
        total_cleared = len(filtered_cleared)
        total_amount = total_cleared  # Assuming each cleared payment is worth 1 unit
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Cleared Payments", f"{total_cleared:,}")
        with col2:
            st.metric("Total Commission Amount", f"${total_amount:,}")
        
        # Group by agent
        agent_cleared = filtered_cleared.groupby('AgentName').size().reset_index(name='ClearedCount')
        agent_cleared = agent_cleared.sort_values('ClearedCount', ascending=False)
        
        # Create bar chart
        fig = px.bar(
            agent_cleared,
            x='AgentName',
            y='ClearedCount',
            title='Cleared Payments by Agent',
            labels={'ClearedCount': 'Number of Cleared Payments', 'AgentName': 'Agent'},
            color='ClearedCount',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table of cleared payments
        st.subheader("Cleared Payments Detail")
        display_cols = ['AgentID', 'AgentName', 'PaymentID', 'PaymentDate', 'ClearedDate']
        display_df = filtered_cleared[display_cols].copy()
        
        # Format dates
        display_df['PaymentDate'] = display_df['PaymentDate'].dt.strftime('%Y-%m-%d')
        display_df['ClearedDate'] = display_df['ClearedDate'].dt.strftime('%Y-%m-%d')
        
        # Rename columns
        display_df.columns = ['Agent ID', 'Agent Name', 'Payment ID', 'Payment Date', 'Cleared Date']
        
        # Show table
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download Cleared Payments",
            data=csv,
            file_name="cleared_payments.csv",
            mime="text/csv",
        )
    
    # ID Lifespan Tab - Track the lifespan of unique IDs
    with comm_tabs[1]:
        st.subheader("Customer ID Lifespan")
        
        # Group by AgentID to get payment history
        id_stats = commission_df.groupby('AgentID').agg(
            FirstPayment=('PaymentDate', 'min'),
            LastPayment=('PaymentDate', 'max'),
            TotalPayments=('PaymentID', 'count'),
            ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
            NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
            Agent=('AgentName', 'first')
        ).reset_index()
        
        # Calculate lifespan in days
        id_stats['Lifespan'] = (id_stats['LastPayment'] - id_stats['FirstPayment']).dt.days
        
        # Calculate success rate
        id_stats['SuccessRate'] = (id_stats['ClearedPayments'] / id_stats['TotalPayments'] * 100).round(1)
        
        # Sort by lifespan
        id_stats = id_stats.sort_values('Lifespan', ascending=False)
        
        # Filter controls
        col1, col2 = st.columns(2)
        
        with col1:
            min_payments = st.slider("Minimum Number of Payments", 1, 
                                    int(id_stats['TotalPayments'].max()), 1)
            filtered_ids = id_stats[id_stats['TotalPayments'] >= min_payments]
        
        with col2:
            agents = sorted(id_stats['Agent'].unique())
            selected_agents = st.multiselect(
                "Filter by Agent",
                agents,
                default=[]
            )
            
            if selected_agents:
                filtered_ids = filtered_ids[filtered_ids['Agent'].isin(selected_agents)]
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Unique IDs", f"{len(filtered_ids):,}")
        with col2:
            avg_lifespan = filtered_ids['Lifespan'].mean()
            st.metric("Average Lifespan (days)", f"{avg_lifespan:.1f}")
        with col3:
            avg_success = filtered_ids['SuccessRate'].mean()
            st.metric("Average Success Rate", f"{avg_success:.1f}%")
        
        # Create scatter plot of lifespan vs success rate
        fig = px.scatter(
            filtered_ids,
            x='Lifespan',
            y='SuccessRate',
            size='TotalPayments',
            color='Agent',
            hover_name='AgentID',
            title='ID Lifespan vs Success Rate',
            labels={
                'Lifespan': 'Lifespan (days)',
                'SuccessRate': 'Success Rate (%)',
                'TotalPayments': 'Total Payments'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table
        st.subheader("ID Lifespan Details")
        display_cols = ['AgentID', 'Agent', 'FirstPayment', 'LastPayment', 
                        'Lifespan', 'TotalPayments', 'ClearedPayments', 'NSFPayments', 'SuccessRate']
        display_df = filtered_ids[display_cols].copy()
        
        # Format dates
        display_df['FirstPayment'] = display_df['FirstPayment'].dt.strftime('%Y-%m-%d')
        display_df['LastPayment'] = display_df['LastPayment'].dt.strftime('%Y-%m-%d')
        display_df['SuccessRate'] = display_df['SuccessRate'].apply(lambda x: f"{x}%")
        
        # Rename columns
        display_df.columns = ['ID', 'Agent', 'First Payment', 'Last Payment', 
                             'Lifespan (days)', 'Total Payments', 'Cleared', 'NSF', 'Success Rate']
        
        # Show table
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Agent Summary Tab
    with comm_tabs[2]:
        st.subheader("Agent Commission Summary")
        
        # Time period filter
        time_period = st.selectbox(
            "Time Period",
            ["Last Week", "Last 2 Weeks", "Last Month", "Last 3 Months", "All Time"],
            index=2,
            key="agent_summary_period"
        )
        
        # Calculate date range based on selection
        today = datetime.now().date()
        if time_period == "Last Week":
            start_date = today - timedelta(days=7)
        elif time_period == "Last 2 Weeks":
            start_date = today - timedelta(days=14)
        elif time_period == "Last Month":
            start_date = today - timedelta(days=30)
        elif time_period == "Last 3 Months":
            start_date = today - timedelta(days=90)
        else:
            start_date = commission_df['PaymentDate'].min().date()
        
        # Filter by date
        filtered_data = commission_df[commission_df['PaymentDate'].dt.date >= start_date]
        
        # Group by agent
        agent_summary = filtered_data.groupby('AgentName').agg(
            TotalPayments=('PaymentID', 'count'),
            ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
            NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
            UniqueIDs=('AgentID', 'nunique')
        ).reset_index()
        
        # Calculate rates
        agent_summary['ClearRate'] = (agent_summary['ClearedPayments'] / agent_summary['TotalPayments'] * 100).round(1)
        agent_summary['CommissionAmount'] = agent_summary['ClearedPayments']  # Assuming $1 per cleared payment
        
        # Sort by cleared payments
        agent_summary = agent_summary.sort_values('ClearedPayments', ascending=False)
        
        # Display table
        st.dataframe(
            agent_summary.rename(columns={
                'AgentName': 'Agent',
                'TotalPayments': 'Total Payments',
                'ClearedPayments': 'Cleared',
                'NSFPayments': 'NSF',
                'UniqueIDs': 'Unique IDs',
                'ClearRate': 'Clear Rate (%)',
                'CommissionAmount': 'Commission ($)'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Create bar chart comparing cleared vs NSF
        fig = px.bar(
            agent_summary,
            x='AgentName',
            y=['ClearedPayments', 'NSFPayments'],
            title='Payment Status by Agent',
            labels={
                'value': 'Number of Payments',
                'AgentName': 'Agent',
                'variable': 'Payment Status'
            },
            color_discrete_map={
                'ClearedPayments': COLORS['light_green'],
                'NSFPayments': COLORS['danger']
            },
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Download button
        csv = agent_summary.to_csv(index=False)
        st.download_button(
            label="Download Agent Summary",
            data=csv,
            file_name="agent_summary.csv",
            mime="text/csv",
        )