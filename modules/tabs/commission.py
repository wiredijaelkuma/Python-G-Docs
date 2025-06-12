"""
Commission Tab Module - Analyzes agent commission data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def process_commission_data():
    """Process the commission CSV file with even/odd columns"""
    try:
        # Read the raw CSV file
        df = pd.read_csv("comissions.csv")
        
        # Extract even and odd columns
        even_df = df.iloc[:, 0:6].copy()
        even_df.columns = ['CustomerID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        odd_df = df.iloc[:, 6:12].copy()
        odd_df.columns = ['CustomerID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        # Combine the dataframes
        combined_df = pd.concat([even_df, odd_df], ignore_index=True)
        
        # Remove rows where CustomerID is empty or AgentName is empty
        combined_df = combined_df[
            (combined_df['CustomerID'].notna() & (combined_df['CustomerID'] != "")) &
            (combined_df['AgentName'].notna() & (combined_df['AgentName'] != ""))
        ]
        
        # Convert dates to datetime
        combined_df['PaymentDate'] = pd.to_datetime(combined_df['PaymentDate'], errors='coerce')
        combined_df['ClearedDate'] = pd.to_datetime(combined_df['ClearedDate'], errors='coerce')
        
        # Create a payment status column
        combined_df['PaymentStatus'] = combined_df['Status'].apply(
            lambda x: 'Cleared' if 'Cleared' in str(x) else 'NSF' if 'NSF' in str(x) or 'Returned' in str(x) else 'Pending'
        )
        
        return combined_df
    except Exception as e:
        st.error(f"Error processing commission data: {e}")
        return pd.DataFrame()

def render_commission_tab(df_filtered, COLORS):
    """Render the commission tab"""
    st.header("Commission Dashboard")
    
    # Process commission data
    commission_df = process_commission_data()
    
    if commission_df.empty:
        st.error("Could not load commission data.")
        return
    
    # Create tabs for different views
    comm_tabs = st.tabs(["Agent Summary", "Recent Payments", "Customer Analysis"])
    
    # Agent Summary Tab
    with comm_tabs[0]:
        st.subheader("Agent Performance Summary")
        
        # Group by agent
        agent_stats = commission_df.groupby('AgentName').agg(
            TotalPayments=('PaymentID', 'count'),
            ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
            NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
            UniqueCustomers=('CustomerID', 'nunique')
        ).reset_index()
        
        # Calculate metrics
        agent_stats['ClearRate'] = (agent_stats['ClearedPayments'] / agent_stats['TotalPayments'] * 100).round(1)
        agent_stats['AvgPaymentsPerCustomer'] = (agent_stats['TotalPayments'] / agent_stats['UniqueCustomers']).round(1)
        agent_stats['EstimatedCommission'] = agent_stats['ClearedPayments'] * 10  # $10 per cleared payment
        
        # Sort by cleared payments
        agent_stats = agent_stats.sort_values('ClearedPayments', ascending=False)
        
        # Create columns for metrics and chart
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Overall metrics
            total_cleared = agent_stats['ClearedPayments'].sum()
            total_nsf = agent_stats['NSFPayments'].sum()
            total_commission = agent_stats['EstimatedCommission'].sum()
            
            st.metric("Total Cleared Payments", f"{total_cleared:,}")
            st.metric("Total NSF Payments", f"{total_nsf:,}")
            st.metric("Total Commission Value", f"${total_commission:,}")
            
            # Top agents
            st.subheader("Top Performing Agents")
            top_agents = agent_stats.head(5)[['AgentName', 'ClearedPayments', 'ClearRate']]
            top_agents.columns = ['Agent', 'Cleared Payments', 'Clear Rate (%)']
            st.dataframe(top_agents, hide_index=True)
        
        with col2:
            # Create bar chart comparing cleared vs NSF
            fig = px.bar(
                agent_stats,
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
            st.plotly_chart(fig, use_container_width=True, key="agent_summary_chart")
        
        # Display full agent stats table
        st.subheader("Complete Agent Performance Data")
        display_df = agent_stats.copy()
        display_df.columns = [
            'Agent', 'Total Payments', 'Cleared', 'NSF', 'Unique Customers', 
            'Clear Rate (%)', 'Avg Payments/Customer', 'Est. Commission ($)'
        ]
        st.dataframe(display_df, hide_index=True, use_container_width=True)
    
    # Recent Payments Tab
    with comm_tabs[1]:
        st.subheader("Recent Payment Activity")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            payment_status = st.selectbox(
                "Payment Status",
                ["All", "Cleared", "NSF", "Pending"],
                index=1  # Default to Cleared
            )
            
            if payment_status == "All":
                filtered_payments = commission_df.copy()
            else:
                filtered_payments = commission_df[commission_df['PaymentStatus'] == payment_status]
        
        with col2:
            time_period = st.selectbox(
                "Time Period",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
                index=1
            )
            
            today = datetime.now()
            if time_period == "Last 7 Days":
                cutoff_date = today - timedelta(days=7)
            elif time_period == "Last 30 Days":
                cutoff_date = today - timedelta(days=30)
            elif time_period == "Last 90 Days":
                cutoff_date = today - timedelta(days=90)
            else:
                cutoff_date = pd.Timestamp.min
            
            filtered_payments = filtered_payments[filtered_payments['PaymentDate'] >= cutoff_date]
        
        # Sort by payment date (most recent first)
        filtered_payments = filtered_payments.sort_values('PaymentDate', ascending=False)
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Payments", f"{len(filtered_payments):,}")
        with col2:
            payment_sum = len(filtered_payments) * 10  # Assuming $10 per payment
            st.metric("Total Value", f"${payment_sum:,}")
        with col3:
            unique_customers = filtered_payments['CustomerID'].nunique()
            st.metric("Unique Customers", f"{unique_customers:,}")
        
        # Payment trend chart
        if not filtered_payments.empty:
            # Group by date
            filtered_payments['Date'] = filtered_payments['PaymentDate'].dt.date
            daily_counts = filtered_payments.groupby('Date').size().reset_index(name='Count')
            daily_counts = daily_counts.sort_values('Date')
            
            # Create line chart
            fig = px.line(
                daily_counts,
                x='Date',
                y='Count',
                title=f'{payment_status} Payments Over Time',
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True, key="payment_trend_chart")
            
            # Recent payments table
            st.subheader("Recent Payments")
            display_cols = ['CustomerID', 'AgentName', 'PaymentID', 'PaymentStatus', 'PaymentDate']
            if payment_status == "Cleared":
                display_cols.append('ClearedDate')
            
            display_df = filtered_payments[display_cols].copy()
            
            # Format dates
            display_df['PaymentDate'] = display_df['PaymentDate'].dt.strftime('%Y-%m-%d')
            if 'ClearedDate' in display_df.columns:
                display_df['ClearedDate'] = display_df['ClearedDate'].dt.strftime('%Y-%m-%d')
            
            # Rename columns for display
            column_map = {
                'CustomerID': 'Customer ID',
                'AgentName': 'Agent',
                'PaymentID': 'Payment ID',
                'PaymentStatus': 'Status',
                'PaymentDate': 'Payment Date',
                'ClearedDate': 'Cleared Date'
            }
            display_df = display_df.rename(columns=column_map)
            
            st.dataframe(display_df.head(50), hide_index=True, use_container_width=True)
            
            if len(filtered_payments) > 50:
                st.info(f"Showing 50 of {len(filtered_payments)} payments. Use the download button to get all data.")
            
            # Download button
            csv = filtered_payments.to_csv(index=False)
            st.download_button(
                label="Download Payment Data",
                data=csv,
                file_name=f"{payment_status.lower()}_payments.csv",
                mime="text/csv",
            )
        else:
            st.info(f"No {payment_status.lower()} payments found for the selected time period.")
    
    # Customer Analysis Tab
    with comm_tabs[2]:
        st.subheader("Customer Lifespan Analysis")
        
        # Calculate customer metrics
        customer_data = commission_df.groupby('CustomerID').agg(
            FirstPayment=('PaymentDate', 'min'),
            LastPayment=('PaymentDate', 'max'),
            TotalPayments=('PaymentID', 'count'),
            ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
            NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
            Agent=('AgentName', 'first')
        ).reset_index()
        
        # Calculate derived metrics
        customer_data['Lifespan'] = (customer_data['LastPayment'] - customer_data['FirstPayment']).dt.days
        customer_data['Lifespan'] = customer_data['Lifespan'].fillna(0).astype(int)
        customer_data['SuccessRate'] = (customer_data['ClearedPayments'] / customer_data['TotalPayments'] * 100).round(1)
        
        # Define customer categories
        customer_data['Category'] = 'One-time'
        customer_data.loc[customer_data['TotalPayments'] >= 3, 'Category'] = 'Repeat'
        customer_data.loc[(customer_data['TotalPayments'] >= 3) & 
                         (customer_data['SuccessRate'] >= 50), 'Category'] = 'Nurtured'
        customer_data.loc[(customer_data['TotalPayments'] >= 6) & 
                         (customer_data['SuccessRate'] >= 75), 'Category'] = 'Premium'
        
        # Filter controls
        col1, col2 = st.columns(2)
        
        with col1:
            category_filter = st.multiselect(
                "Customer Category",
                ['One-time', 'Repeat', 'Nurtured', 'Premium'],
                default=['Nurtured', 'Premium']
            )
            
            if category_filter:
                filtered_customers = customer_data[customer_data['Category'].isin(category_filter)]
            else:
                filtered_customers = customer_data
        
        with col2:
            agent_filter = st.multiselect(
                "Filter by Agent",
                sorted(customer_data['Agent'].unique()),
                default=[]
            )
            
            if agent_filter:
                filtered_customers = filtered_customers[filtered_customers['Agent'].isin(agent_filter)]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Customers", f"{len(filtered_customers):,}")
        with col2:
            avg_lifespan = filtered_customers['Lifespan'].mean()
            st.metric("Avg Lifespan (days)", f"{avg_lifespan:.1f}")
        with col3:
            avg_payments = filtered_customers['TotalPayments'].mean()
            st.metric("Avg Payments", f"{avg_payments:.1f}")
        with col4:
            avg_success = filtered_customers['SuccessRate'].mean()
            st.metric("Avg Success Rate", f"{avg_success:.1f}%")
        
        # Customer category breakdown
        category_counts = filtered_customers['Category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        
        # Order categories
        category_order = ['One-time', 'Repeat', 'Nurtured', 'Premium']
        category_counts['Category'] = pd.Categorical(
            category_counts['Category'], 
            categories=category_order, 
            ordered=True
        )
        category_counts = category_counts.sort_values('Category')
        
        # Create columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Create pie chart for customer categories
            fig = px.pie(
                category_counts,
                values='Count',
                names='Category',
                title='Customer Category Distribution',
                color='Category',
                color_discrete_map={
                    'One-time': COLORS['danger'],
                    'Repeat': COLORS['warning'],
                    'Nurtured': COLORS['primary'],
                    'Premium': COLORS['light_green']
                }
            )
            st.plotly_chart(fig, use_container_width=True, key="category_pie_chart")
        
        with col2:
            # Create scatter plot of lifespan vs success rate
            fig = px.scatter(
                filtered_customers,
                x='Lifespan',
                y='SuccessRate',
                size='TotalPayments',
                color='Category',
                hover_name='CustomerID',
                title='Customer Lifespan vs Success Rate',
                labels={
                    'Lifespan': 'Lifespan (days)',
                    'SuccessRate': 'Success Rate (%)',
                    'TotalPayments': 'Total Payments'
                },
                color_discrete_map={
                    'One-time': COLORS['danger'],
                    'Repeat': COLORS['warning'],
                    'Nurtured': COLORS['primary'],
                    'Premium': COLORS['light_green']
                }
            )
            st.plotly_chart(fig, use_container_width=True, key="lifespan_scatter_chart")
        
        # Agent performance with customers
        st.subheader("Agent Customer Quality")
        
        # Group by agent
        agent_customer_stats = filtered_customers.groupby('Agent').agg(
            TotalCustomers=('CustomerID', 'count'),
            AvgLifespan=('Lifespan', 'mean'),
            AvgPayments=('TotalPayments', 'mean'),
            AvgSuccessRate=('SuccessRate', 'mean'),
            NurturedCustomers=('Category', lambda x: ((x == 'Nurtured') | (x == 'Premium')).sum())
        ).reset_index()
        
        # Calculate nurture rate
        agent_customer_stats['NurtureRate'] = (agent_customer_stats['NurturedCustomers'] / 
                                              agent_customer_stats['TotalCustomers'] * 100).round(1)
        
        # Sort by nurture rate
        agent_customer_stats = agent_customer_stats.sort_values('NurtureRate', ascending=False)
        
        # Format for display
        display_df = agent_customer_stats.copy()
        display_df['AvgLifespan'] = display_df['AvgLifespan'].round(1)
        display_df['AvgPayments'] = display_df['AvgPayments'].round(1)
        display_df['AvgSuccessRate'] = display_df['AvgSuccessRate'].round(1)
        
        display_df.columns = [
            'Agent', 'Total Customers', 'Avg Lifespan (days)', 'Avg Payments', 
            'Avg Success Rate (%)', 'Nurtured Customers', 'Nurture Rate (%)'
        ]
        
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        
        # Customer details table
        st.subheader("Customer Details")
        
        # Format for display
        customer_display = filtered_customers.copy()
        customer_display['FirstPayment'] = customer_display['FirstPayment'].dt.strftime('%Y-%m-%d')
        customer_display['LastPayment'] = customer_display['LastPayment'].dt.strftime('%Y-%m-%d')
        
        customer_display.columns = [
            'Customer ID', 'First Payment', 'Last Payment', 'Total Payments', 
            'Cleared Payments', 'NSF Payments', 'Agent', 'Lifespan (days)', 
            'Success Rate (%)', 'Category'
        ]
        
        st.dataframe(customer_display, hide_index=True, use_container_width=True)