"""
Basic Commission Tab Module
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def render_commission_tab(df_filtered, COLORS):
    """Render the commission tab"""
    st.header("Commission Dashboard")
    
    try:
        # Read the raw CSV file
        df = pd.read_csv("comissions.csv")
        
        # Extract even columns
        even_df = df.iloc[:, 0:6].copy()
        even_df.columns = ['CustomerID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        # Extract odd columns
        odd_df = df.iloc[:, 6:12].copy()
        odd_df.columns = ['CustomerID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        # Combine the dataframes
        combined_df = pd.concat([even_df, odd_df], ignore_index=True)
        
        # Clean the data - convert all to strings to avoid comparison issues
        combined_df = combined_df.fillna("")
        combined_df['AgentName'] = combined_df['AgentName'].astype(str)
        combined_df['CustomerID'] = combined_df['CustomerID'].astype(str)
        combined_df['PaymentID'] = combined_df['PaymentID'].astype(str)
        combined_df['Status'] = combined_df['Status'].astype(str)
        
        # Remove rows with empty agent names
        combined_df = combined_df[combined_df['AgentName'] != ""]
        
        # Convert dates to datetime
        combined_df['PaymentDate'] = pd.to_datetime(combined_df['PaymentDate'], errors='coerce')
        combined_df['ClearedDate'] = pd.to_datetime(combined_df['ClearedDate'], errors='coerce')
        
        # Create payment status column
        combined_df['PaymentStatus'] = 'Other'
        combined_df.loc[combined_df['Status'].str.contains('Cleared', case=False, na=False), 'PaymentStatus'] = 'Cleared'
        combined_df.loc[combined_df['Status'].str.contains('NSF|Returned', case=False, na=False), 'PaymentStatus'] = 'NSF'
        combined_df.loc[combined_df['Status'].str.contains('Pending', case=False, na=False), 'PaymentStatus'] = 'Pending'
        
        # Create tabs
        tabs = st.tabs(["Agent View", "Payment Status", "Customer View"])
        
        # Tab 1: Agent View
        with tabs[0]:
            st.subheader("Agent Payment Data")
            
            # Get list of agents (already converted to strings)
            agents = list(combined_df['AgentName'].unique())
            agents.sort()
            
            # Agent selector
            selected_agent = st.selectbox("Select Agent", agents)
            
            # Filter data for selected agent
            agent_data = combined_df[combined_df['AgentName'] == selected_agent]
            
            # Count payments by status
            cleared = len(agent_data[agent_data['PaymentStatus'] == 'Cleared'])
            nsf = len(agent_data[agent_data['PaymentStatus'] == 'NSF'])
            pending = len(agent_data[agent_data['PaymentStatus'] == 'Pending'])
            total = len(agent_data)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Payments", total)
            col2.metric("Cleared", cleared)
            col3.metric("NSF", nsf)
            col4.metric("Pending", pending)
            
            # Show payment status distribution
            status_counts = agent_data['PaymentStatus'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            if not status_counts.empty:
                fig = px.pie(
                    status_counts, 
                    values='Count', 
                    names='Status',
                    title=f"Payment Status for {selected_agent}",
                    color='Status',
                    color_discrete_map={
                        'Cleared': COLORS['light_green'],
                        'NSF': COLORS['danger'],
                        'Pending': COLORS['warning'],
                        'Other': COLORS['secondary']
                    }
                )
                st.plotly_chart(fig, use_container_width=True, key="agent_status_pie")
            
            # Show customer list for this agent
            st.subheader("Customers")
            
            # Get unique customers
            customers = agent_data['CustomerID'].unique()
            customer_counts = []
            
            for customer in customers:
                customer_data = agent_data[agent_data['CustomerID'] == customer]
                customer_counts.append({
                    'CustomerID': customer,
                    'Total': len(customer_data),
                    'Cleared': len(customer_data[customer_data['PaymentStatus'] == 'Cleared']),
                    'NSF': len(customer_data[customer_data['PaymentStatus'] == 'NSF']),
                    'Pending': len(customer_data[customer_data['PaymentStatus'] == 'Pending'])
                })
            
            # Convert to dataframe
            if customer_counts:
                customer_df = pd.DataFrame(customer_counts)
                st.dataframe(customer_df, use_container_width=True, hide_index=True)
            else:
                st.info("No customers found for this agent")
            
            # Show all payments
            st.subheader("All Payments")
            
            # Format for display
            display_data = agent_data[['CustomerID', 'PaymentID', 'PaymentStatus', 'PaymentDate', 'ClearedDate']].copy()
            
            # Convert dates to strings
            display_data['PaymentDate'] = display_data['PaymentDate'].dt.strftime('%Y-%m-%d')
            display_data['ClearedDate'] = display_data['ClearedDate'].dt.strftime('%Y-%m-%d')
            
            # Fill NaN with empty string
            display_data = display_data.fillna("")
            
            # Sort by payment date
            if 'PaymentDate' in display_data.columns:
                display_data = display_data.sort_values('PaymentDate', ascending=False)
            
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        
        # Tab 2: Payment Status
        with tabs[1]:
            st.subheader("Payment Status Analysis")
            
            # Status filter
            status_options = ["All", "Cleared", "NSF", "Pending"]
            selected_status = st.selectbox("Filter by Status", status_options)
            
            # Date range filter
            date_options = ["All Time", "Last 7 Days", "Last 14 Days", "Last 30 Days"]
            selected_date = st.selectbox("Date Range", date_options)
            
            # Apply filters
            if selected_status == "All":
                status_filtered = combined_df
            else:
                status_filtered = combined_df[combined_df['PaymentStatus'] == selected_status]
            
            # Apply date filter
            today = datetime.now()
            if selected_date == "Last 7 Days":
                cutoff = today - timedelta(days=7)
                date_filtered = status_filtered[status_filtered['PaymentDate'] >= cutoff]
            elif selected_date == "Last 14 Days":
                cutoff = today - timedelta(days=14)
                date_filtered = status_filtered[status_filtered['PaymentDate'] >= cutoff]
            elif selected_date == "Last 30 Days":
                cutoff = today - timedelta(days=30)
                date_filtered = status_filtered[status_filtered['PaymentDate'] >= cutoff]
            else:
                date_filtered = status_filtered
            
            # Display metrics
            total_filtered = len(date_filtered)
            st.metric("Total Filtered Payments", total_filtered)
            
            # Group by agent
            agent_counts = date_filtered.groupby('AgentName').size().reset_index()
            agent_counts.columns = ['Agent', 'Count']
            agent_counts = agent_counts.sort_values('Count', ascending=False)
            
            # Show bar chart
            if not agent_counts.empty:
                fig = px.bar(
                    agent_counts,
                    x='Agent',
                    y='Count',
                    title=f"{selected_status} Payments by Agent ({selected_date})",
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True, key="status_by_agent")
            
            # Show payment details
            st.subheader("Payment Details")
            
            # Format for display
            display_filtered = date_filtered[['AgentName', 'CustomerID', 'PaymentID', 'PaymentStatus', 'PaymentDate', 'ClearedDate']].copy()
            
            # Convert dates to strings
            display_filtered['PaymentDate'] = display_filtered['PaymentDate'].dt.strftime('%Y-%m-%d')
            display_filtered['ClearedDate'] = display_filtered['ClearedDate'].dt.strftime('%Y-%m-%d')
            
            # Fill NaN with empty string
            display_filtered = display_filtered.fillna("")
            
            # Sort by payment date
            if 'PaymentDate' in display_filtered.columns:
                display_filtered = display_filtered.sort_values('PaymentDate', ascending=False)
            
            st.dataframe(display_filtered, use_container_width=True, hide_index=True)
        
        # Tab 3: Customer View
        with tabs[2]:
            st.subheader("Customer Payment History")
            
            # Get list of customers (already converted to strings)
            customers = list(combined_df['CustomerID'].unique())
            customers.sort()
            
            # Customer selector
            selected_customer = st.selectbox("Select Customer", customers)
            
            # Filter data for selected customer
            customer_data = combined_df[combined_df['CustomerID'] == selected_customer]
            
            # Count payments by status
            cleared = len(customer_data[customer_data['PaymentStatus'] == 'Cleared'])
            nsf = len(customer_data[customer_data['PaymentStatus'] == 'NSF'])
            pending = len(customer_data[customer_data['PaymentStatus'] == 'Pending'])
            total = len(customer_data)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Payments", total)
            col2.metric("Cleared", cleared)
            col3.metric("NSF", nsf)
            col4.metric("Pending", pending)
            
            # Show payment history
            st.subheader("Payment History")
            
            # Format for display
            display_history = customer_data[['AgentName', 'PaymentID', 'PaymentStatus', 'PaymentDate', 'ClearedDate']].copy()
            
            # Convert dates to strings
            display_history['PaymentDate'] = display_history['PaymentDate'].dt.strftime('%Y-%m-%d')
            display_history['ClearedDate'] = display_history['ClearedDate'].dt.strftime('%Y-%m-%d')
            
            # Fill NaN with empty string
            display_history = display_history.fillna("")
            
            # Sort by payment date
            if 'PaymentDate' in display_history.columns:
                display_history = display_history.sort_values('PaymentDate', ascending=False)
            
            st.dataframe(display_history, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())