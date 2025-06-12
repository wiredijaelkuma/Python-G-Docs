"""
Simple Commission Tab Module
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
        
        # Clean the data
        combined_df = combined_df.dropna(subset=['AgentName', 'PaymentID'])
        combined_df['PaymentDate'] = pd.to_datetime(combined_df['PaymentDate'], errors='coerce')
        combined_df['ClearedDate'] = pd.to_datetime(combined_df['ClearedDate'], errors='coerce')
        combined_df['Status'] = combined_df['Status'].astype(str)
        
        # Create payment status column
        combined_df['PaymentStatus'] = 'Other'
        combined_df.loc[combined_df['Status'].str.contains('Cleared', case=False, na=False), 'PaymentStatus'] = 'Cleared'
        combined_df.loc[combined_df['Status'].str.contains('NSF|Returned', case=False, na=False), 'PaymentStatus'] = 'NSF'
        
        # Create tabs
        tabs = st.tabs(["Agent Payments", "Recent Cleared Payments", "Customer History"])
        
        # Tab 1: Agent Payments
        with tabs[0]:
            st.subheader("Agent Payment Summary")
            
            # Filter options
            col1, col2 = st.columns(2)
            
            with col1:
                # Get list of agents
                agents = sorted(combined_df['AgentName'].unique())
                selected_agent = st.selectbox("Select Agent", agents)
            
            with col2:
                # Date range filter
                date_range = st.selectbox(
                    "Date Range",
                    ["All Time", "Last 7 Days", "Last 14 Days", "Last 30 Days", "Last 90 Days"]
                )
                
                today = datetime.now()
                if date_range == "Last 7 Days":
                    start_date = today - timedelta(days=7)
                elif date_range == "Last 14 Days":
                    start_date = today - timedelta(days=14)
                elif date_range == "Last 30 Days":
                    start_date = today - timedelta(days=30)
                elif date_range == "Last 90 Days":
                    start_date = today - timedelta(days=90)
                else:
                    start_date = datetime(2000, 1, 1)  # Very old date to include all
            
            # Filter data
            agent_data = combined_df[combined_df['AgentName'] == selected_agent]
            agent_data = agent_data[agent_data['PaymentDate'] >= start_date]
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_payments = len(agent_data)
                st.metric("Total Payments", str(total_payments))
            
            with col2:
                cleared_payments = len(agent_data[agent_data['PaymentStatus'] == 'Cleared'])
                st.metric("Cleared Payments", str(cleared_payments))
            
            with col3:
                nsf_payments = len(agent_data[agent_data['PaymentStatus'] == 'NSF'])
                st.metric("NSF Payments", str(nsf_payments))
            
            # Display payment status chart
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
                        'Other': COLORS['warning']
                    }
                )
                st.plotly_chart(fig, use_container_width=True, key="agent_status_pie")
            
            # Display customer table
            st.subheader("Customer Payment Details")
            
            # Group by customer
            customer_data = agent_data.groupby('CustomerID').agg(
                TotalPayments=('PaymentID', 'count'),
                ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
                NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
                FirstPayment=('PaymentDate', 'min'),
                LastPayment=('PaymentDate', 'max')
            ).reset_index()
            
            # Format dates
            customer_data['FirstPayment'] = customer_data['FirstPayment'].dt.strftime('%Y-%m-%d')
            customer_data['LastPayment'] = customer_data['LastPayment'].dt.strftime('%Y-%m-%d')
            
            # Rename columns
            customer_data.columns = ['Customer ID', 'Total Payments', 'Cleared', 'NSF', 'First Payment', 'Last Payment']
            
            # Display table
            st.dataframe(customer_data, use_container_width=True, hide_index=True)
            
            # Display all payments
            st.subheader("All Payments")
            
            # Format dates
            display_data = agent_data[['CustomerID', 'PaymentID', 'PaymentStatus', 'PaymentDate', 'ClearedDate']].copy()
            display_data['PaymentDate'] = display_data['PaymentDate'].dt.strftime('%Y-%m-%d')
            display_data['ClearedDate'] = display_data['ClearedDate'].dt.strftime('%Y-%m-%d')
            
            # Rename columns
            display_data.columns = ['Customer ID', 'Payment ID', 'Status', 'Payment Date', 'Cleared Date']
            
            # Sort by payment date (newest first)
            display_data = display_data.sort_values('Payment Date', ascending=False)
            
            # Display table
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        
        # Tab 2: Recent Cleared Payments
        with tabs[1]:
            st.subheader("Recent Cleared Payments")
            
            # Filter for cleared payments
            cleared_payments = combined_df[combined_df['PaymentStatus'] == 'Cleared'].copy()
            
            # Date filter
            col1, col2 = st.columns(2)
            
            with col1:
                time_period = st.selectbox(
                    "Time Period",
                    ["Last 7 Days", "Last 14 Days", "Last 30 Days", "All Cleared"],
                    key="cleared_time_period"
                )
                
                today = datetime.now()
                if time_period == "Last 7 Days":
                    cutoff_date = today - timedelta(days=7)
                elif time_period == "Last 14 Days":
                    cutoff_date = today - timedelta(days=14)
                elif time_period == "Last 30 Days":
                    cutoff_date = today - timedelta(days=30)
                else:
                    cutoff_date = datetime(2000, 1, 1)  # Very old date
                
                filtered_cleared = cleared_payments[cleared_payments['ClearedDate'] >= cutoff_date]
            
            with col2:
                # Calculate commission date (7 days after cleared date)
                filtered_cleared['CommissionDate'] = filtered_cleared['ClearedDate'] + pd.Timedelta(days=7)
                
                # Filter by commission date
                commission_filter = st.selectbox(
                    "Commission Status",
                    ["All", "Due Now", "Future"]
                )
                
                if commission_filter == "Due Now":
                    filtered_cleared = filtered_cleared[filtered_cleared['CommissionDate'] <= today]
                elif commission_filter == "Future":
                    filtered_cleared = filtered_cleared[filtered_cleared['CommissionDate'] > today]
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                total_cleared = len(filtered_cleared)
                st.metric("Total Cleared Payments", str(total_cleared))
            
            with col2:
                commission_amount = total_cleared * 10  # Assuming $10 per cleared payment
                st.metric("Commission Amount", f"${commission_amount}")
            
            # Group by agent
            agent_cleared = filtered_cleared.groupby('AgentName').size().reset_index(name='Count')
            agent_cleared = agent_cleared.sort_values('Count', ascending=False)
            
            # Create bar chart
            if not agent_cleared.empty:
                fig = px.bar(
                    agent_cleared,
                    x='AgentName',
                    y='Count',
                    title='Cleared Payments by Agent',
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True, key="cleared_by_agent")
            
            # Display cleared payments table
            st.subheader("Cleared Payments Detail")
            
            # Format dates
            display_cleared = filtered_cleared[['AgentName', 'CustomerID', 'PaymentID', 'PaymentDate', 'ClearedDate', 'CommissionDate']].copy()
            display_cleared['PaymentDate'] = display_cleared['PaymentDate'].dt.strftime('%Y-%m-%d')
            display_cleared['ClearedDate'] = display_cleared['ClearedDate'].dt.strftime('%Y-%m-%d')
            display_cleared['CommissionDate'] = display_cleared['CommissionDate'].dt.strftime('%Y-%m-%d')
            
            # Rename columns
            display_cleared.columns = ['Agent', 'Customer ID', 'Payment ID', 'Payment Date', 'Cleared Date', 'Commission Date']
            
            # Sort by cleared date (newest first)
            display_cleared = display_cleared.sort_values('Cleared Date', ascending=False)
            
            # Display table
            st.dataframe(display_cleared, use_container_width=True, hide_index=True)
        
        # Tab 3: Customer History
        with tabs[2]:
            st.subheader("Customer Payment History")
            
            # Customer filter
            customers = sorted(combined_df['CustomerID'].unique())
            selected_customer = st.selectbox("Select Customer", customers)
            
            # Filter data
            customer_data = combined_df[combined_df['CustomerID'] == selected_customer]
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_payments = len(customer_data)
                st.metric("Total Payments", str(total_payments))
            
            with col2:
                cleared_payments = len(customer_data[customer_data['PaymentStatus'] == 'Cleared'])
                st.metric("Cleared Payments", str(cleared_payments))
            
            with col3:
                success_rate = (cleared_payments / total_payments * 100) if total_payments > 0 else 0
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Display payment history
            st.subheader("Payment History")
            
            # Format dates
            display_history = customer_data[['AgentName', 'PaymentID', 'PaymentStatus', 'PaymentDate', 'ClearedDate']].copy()
            display_history['PaymentDate'] = display_history['PaymentDate'].dt.strftime('%Y-%m-%d')
            display_history['ClearedDate'] = display_history['ClearedDate'].dt.strftime('%Y-%m-%d')
            
            # Rename columns
            display_history.columns = ['Agent', 'Payment ID', 'Status', 'Payment Date', 'Cleared Date']
            
            # Sort by payment date (newest first)
            display_history = display_history.sort_values('Payment Date', ascending=False)
            
            # Display table
            st.dataframe(display_history, use_container_width=True, hide_index=True)
            
            # Payment timeline
            if len(customer_data) > 1:
                st.subheader("Payment Timeline")
                
                # Create timeline data
                timeline_data = customer_data[['PaymentDate', 'PaymentStatus']].copy()
                timeline_data = timeline_data.sort_values('PaymentDate')
                
                # Create line chart
                fig = px.line(
                    timeline_data,
                    x='PaymentDate',
                    y=[1] * len(timeline_data),  # Constant value for line
                    color='PaymentStatus',
                    markers=True,
                    title=f"Payment Timeline for Customer {selected_customer}",
                    color_discrete_map={
                        'Cleared': COLORS['light_green'],
                        'NSF': COLORS['danger'],
                        'Other': COLORS['warning']
                    }
                )
                fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)
                st.plotly_chart(fig, use_container_width=True, key="customer_timeline")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())