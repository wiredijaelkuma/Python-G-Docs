"""
Commission Dashboard Tab
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

def render_commission_tab(df_filtered, COLORS):
    """Render the enhanced commission dashboard tab"""
    st.header("Commission Dashboard")
    
    try:
        # Read CSV directly
        df = pd.read_csv("comissions.csv", header=0)
        
        # Create a clean dataframe with just the data we need
        data = []
        
        # Process even columns (0-5, 10)
        for i in range(len(df)):
            if pd.notna(df.iloc[i, 1]) and df.iloc[i, 1] != "":  # Check if agent name exists
                row_data = {
                    'CustomerID': str(df.iloc[i, 0]),
                    'AgentName': str(df.iloc[i, 1]),
                    'PaymentID': str(df.iloc[i, 2]),
                    'Status': str(df.iloc[i, 3]),
                    'PaymentDate': str(df.iloc[i, 4]),
                    'ClearedDate': str(df.iloc[i, 11]) if i < len(df) and len(df.columns) > 11 and pd.notna(df.iloc[i, 11]) else ""
                }
                data.append(row_data)
        
        # Process odd columns (5-10, 11)
        for i in range(len(df)):
            if pd.notna(df.iloc[i, 6]) and df.iloc[i, 6] != "":  # Check if agent name exists
                row_data = {
                    'CustomerID': str(df.iloc[i, 5]),
                    'AgentName': str(df.iloc[i, 6]),
                    'PaymentID': str(df.iloc[i, 7]),
                    'Status': str(df.iloc[i, 8]),
                    'PaymentDate': str(df.iloc[i, 9]),
                    'ClearedDate': str(df.iloc[i, 10]) if i < len(df) and len(df.columns) > 10 and pd.notna(df.iloc[i, 10]) else ""
                }
                data.append(row_data)
        
        # Convert to dataframe
        payments_df = pd.DataFrame(data)
        
        # Clean and validate data
        payments_df = payments_df[payments_df['AgentName'].notna() & (payments_df['AgentName'] != "") & (payments_df['AgentName'] != "nan")]
        payments_df['CustomerID'] = payments_df['CustomerID'].replace('nan', '')
        payments_df['PaymentID'] = payments_df['PaymentID'].replace('nan', '')
        payments_df['Status'] = payments_df['Status'].fillna('Unknown')
        
        # Remove any duplicate payment IDs
        payments_df = payments_df.drop_duplicates(subset=['PaymentID'], keep='first')
        
        # Parse dates
        for date_col in ['PaymentDate', 'ClearedDate']:
            try:
                # Convert date strings to datetime objects where possible
                # Handle the format "Month DD YYYY" (e.g., "June 11 2025")
                payments_df[date_col] = pd.to_datetime(payments_df[date_col], format='%B %d %Y', errors='coerce')
            except Exception as e:
                st.warning(f"Error parsing {date_col}: {str(e)}")
                # Try alternative parsing as fallback
                try:
                    payments_df[date_col] = pd.to_datetime(payments_df[date_col], errors='coerce')
                except:
                    pass
        
        # Create tabs
        tabs = st.tabs(["Dashboard Overview", "Agent Performance", "Payment Analysis", "Raw Data"])
        
        # Get unique agent names (manually to avoid sorting issues)
        agent_names = []
        for agent in payments_df['AgentName']:
            if agent and agent not in agent_names and agent != "nan" and agent != "None" and pd.notna(agent):
                # Ensure agent name is a valid string
                try:
                    agent_str = str(agent).strip()
                    if agent_str and agent_str not in agent_names:
                        agent_names.append(agent_str)
                except:
                    pass
                    
        # Sort agent names alphabetically
        agent_names.sort()
        
        # Tab 1: Dashboard Overview
        with tabs[0]:
            st.subheader("Commission Dashboard Overview")
            
            # Calculate key metrics
            total_payments = len(payments_df)
            cleared_payments = payments_df[payments_df['Status'].str.contains('Cleared', na=False)].shape[0]
            nsf_payments = payments_df[payments_df['Status'].str.contains('NSF|Returned', na=False, regex=True)].shape[0]
            pending_payments = payments_df[payments_df['Status'].str.contains('Pending', na=False)].shape[0]
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Payments", total_payments)
            col2.metric("Cleared", cleared_payments)
            col3.metric("NSF/Returned", nsf_payments)
            col4.metric("Pending", pending_payments)
            
            # Recent Cleared Payments (Last 14 Days)
            st.subheader("Cleared Payments in Last 14 Days")
            
            # Get current date and date 14 days ago
            from datetime import datetime, timedelta
            today = datetime.now()
            fourteen_days_ago = today - timedelta(days=14)
            
            # Filter for cleared payments in the last 14 days
            recent_cleared = payments_df[
                (payments_df['Status'].str.contains('Cleared', na=False)) & 
                (payments_df['ClearedDate'].notna()) & 
                (payments_df['ClearedDate'] >= fourteen_days_ago)
            ]
            
            if not recent_cleared.empty:
                # Sort by cleared date
                recent_cleared = recent_cleared.sort_values('ClearedDate')
                
                # Group by agent and count payments
                agent_payment_counts = recent_cleared.groupby('AgentName').size().reset_index()
                agent_payment_counts.columns = ['Agent', 'PaymentCount']
                agent_payment_counts = agent_payment_counts.sort_values('PaymentCount', ascending=False)
                
                # Create columns for display
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Add payment number to each agent's payments
                    agent_payment_numbers = {}
                    for agent in recent_cleared['AgentName'].unique():
                        agent_payments = recent_cleared[recent_cleared['AgentName'] == agent].sort_values('ClearedDate')
                        agent_payments['PaymentNumber'] = range(1, len(agent_payments) + 1)
                        agent_payment_numbers[agent] = agent_payments
                    
                    # Combine all agent payments with numbers
                    numbered_payments = pd.concat(agent_payment_numbers.values())
                    
                    # Select columns to display
                    display_df = numbered_payments[['AgentName', 'PaymentNumber', 'PaymentID', 'ClearedDate', 'PaymentDate']].copy()
                    display_df.columns = ['Agent', 'Payment #', 'Payment ID', 'Cleared Date', 'Payment Date']
                    
                    # Format dates
                    display_df['Cleared Date'] = display_df['Cleared Date'].dt.strftime('%Y-%m-%d')
                    display_df['Payment Date'] = display_df['Payment Date'].dt.strftime('%Y-%m-%d')
                    
                    # Display the table
                    st.dataframe(display_df, use_container_width=True)
                
                with col2:
                    # Display agent payment counts
                    st.subheader("Payments by Agent")
                    st.dataframe(agent_payment_counts, use_container_width=True)
                    
                    # Calculate when agents need to be paid
                    st.subheader("Payment Due")
                    
                    # Group by agent and get earliest cleared date
                    agent_earliest_payment = recent_cleared.groupby('AgentName')['ClearedDate'].min().reset_index()
                    agent_earliest_payment.columns = ['Agent', 'First Cleared Date']
                    
                    # Calculate payment due date (7 days after first cleared payment)
                    agent_earliest_payment['Payment Due Date'] = agent_earliest_payment['First Cleared Date'] + timedelta(days=7)
                    agent_earliest_payment['Days Until Due'] = (agent_earliest_payment['Payment Due Date'] - datetime.now()).dt.days
                    
                    # Format for display
                    agent_earliest_payment['First Cleared Date'] = agent_earliest_payment['First Cleared Date'].dt.strftime('%Y-%m-%d')
                    agent_earliest_payment['Payment Due Date'] = agent_earliest_payment['Payment Due Date'].dt.strftime('%Y-%m-%d')
                    
                    # Sort by days until due
                    agent_earliest_payment = agent_earliest_payment.sort_values('Days Until Due')
                    
                    # Display the table
                    st.dataframe(agent_earliest_payment[['Agent', 'Payment Due Date', 'Days Until Due']], use_container_width=True)
            else:
                st.info("No cleared payments in the last 14 days.")
            
            # Payment Status Distribution
            st.subheader("Payment Status Distribution")
            status_counts = payments_df['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig = px.pie(
                status_counts, 
                values='Count', 
                names='Status',
                color_discrete_sequence=[COLORS['primary'], COLORS['danger'], COLORS['warning'], COLORS['accent']]
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
            # Payment Trends Over Time
            st.subheader("Payment Trends Over Time")
            
            # Group by payment date
            if 'PaymentDate' in payments_df.columns:
                # Extract just the date part and count payments by date
                payments_df['PaymentDateOnly'] = payments_df['PaymentDate'].dt.date
                date_counts = payments_df.groupby('PaymentDateOnly').size().reset_index()
                date_counts.columns = ['Date', 'Count']
                
                # Sort by date
                date_counts = date_counts.sort_values('Date')
                
                # Create line chart
                fig = px.line(
                    date_counts, 
                    x='Date', 
                    y='Count',
                    title='Daily Payment Volume',
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True)
            
        # Tab 2: Agent Performance
        with tabs[1]:
            st.subheader("Agent Performance")
            
            # Agent selector
            selected_agent = st.selectbox("Select Agent", agent_names)
            
            # Filter data for selected agent
            agent_data = payments_df[payments_df['AgentName'] == selected_agent]
            
            if not agent_data.empty:
                # Calculate agent metrics
                total_agent_payments = len(agent_data)
                agent_cleared = agent_data[agent_data['Status'].str.contains('Cleared', na=False)].shape[0]
                agent_nsf = agent_data[agent_data['Status'].str.contains('NSF|Returned', na=False, regex=True)].shape[0]
                agent_pending = agent_data[agent_data['Status'].str.contains('Pending', na=False)].shape[0]
                
                # Display agent metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Payments", total_agent_payments)
                col2.metric("Cleared", agent_cleared)
                col3.metric("NSF/Returned", agent_nsf)
                col4.metric("Pending", agent_pending)
                
                # Calculate success rate
                if total_agent_payments > 0:
                    success_rate = (agent_cleared / total_agent_payments) * 100
                    nsf_rate = (agent_nsf / total_agent_payments) * 100
                else:
                    success_rate = 0
                    nsf_rate = 0
                
                # Display success rate gauge
                st.subheader(f"Success Rate: {success_rate:.1f}%")
                
                # Create gauge chart for success rate
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = success_rate,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Success Rate"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': COLORS['primary']},
                        'steps': [
                            {'range': [0, 50], 'color': COLORS['danger']},
                            {'range': [50, 75], 'color': COLORS['warning']},
                            {'range': [75, 100], 'color': COLORS['accent']}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': success_rate
                        }
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
                
                # Customer performance for this agent
                st.subheader("Customer Performance")
                
                # Group by customer ID
                customer_performance = agent_data.groupby('CustomerID').agg(
                    TotalPayments=('PaymentID', 'count'),
                    Cleared=('Status', lambda x: (x.str.contains('Cleared', na=False)).sum()),
                    NSF=('Status', lambda x: (x.str.contains('NSF|Returned', na=False, regex=True)).sum()),
                    Pending=('Status', lambda x: (x.str.contains('Pending', na=False)).sum())
                ).reset_index()
                
                # Calculate success rate for each customer
                customer_performance['SuccessRate'] = (customer_performance['Cleared'] / customer_performance['TotalPayments'] * 100).round(1)
                
                # Display customer performance
                st.dataframe(customer_performance, use_container_width=True)
                
                # Payment trend over time for this agent
                st.subheader("Payment Trend")
                
                if 'PaymentDateOnly' in agent_data.columns:
                    # Group by date and status
                    agent_date_status = agent_data.groupby(['PaymentDateOnly', 'Status']).size().reset_index()
                    agent_date_status.columns = ['Date', 'Status', 'Count']
                    
                    # Create line chart by status
                    fig = px.line(
                        agent_date_status, 
                        x='Date', 
                        y='Count',
                        color='Status',
                        title=f'Daily Payment Volume for {selected_agent}',
                        markers=True,
                        color_discrete_sequence=[COLORS['accent'], COLORS['danger'], COLORS['warning']]
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No data found for agent: {selected_agent}")
        
        # Tab 3: Payment Analysis
        with tabs[2]:
            st.subheader("Payment Analysis")
            
            # Status filter
            status_options = ['All'] + list(payments_df['Status'].unique())
            selected_status = st.selectbox("Filter by Status", status_options)
            
            # Filter data based on selection
            if selected_status == 'All':
                filtered_payments = payments_df
            else:
                filtered_payments = payments_df[payments_df['Status'] == selected_status]
            
            # Top agents by payment volume
            st.subheader("Top Agents by Payment Volume")
            
            # Group by agent
            agent_counts = filtered_payments.groupby('AgentName').size().reset_index()
            agent_counts.columns = ['Agent', 'Count']
            
            # Sort by count descending
            agent_counts = agent_counts.sort_values('Count', ascending=False)
            
            # Create bar chart
            fig = px.bar(
                agent_counts.head(10), 
                x='Agent', 
                y='Count',
                title='Top 10 Agents by Payment Volume',
                color_discrete_sequence=[COLORS['primary']]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Payment status by agent
            st.subheader("Payment Status by Agent")
            
            # Group by agent and status
            agent_status = payments_df.groupby(['AgentName', 'Status']).size().reset_index()
            agent_status.columns = ['Agent', 'Status', 'Count']
            
            # Create stacked bar chart
            fig = px.bar(
                agent_status, 
                x='Agent', 
                y='Count',
                color='Status',
                title='Payment Status Distribution by Agent',
                color_discrete_sequence=[COLORS['primary'], COLORS['danger'], COLORS['warning'], COLORS['accent']]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Payment processing time analysis (for cleared payments)
            st.subheader("Payment Processing Time Analysis")
            
            # Filter for cleared payments with both dates
            cleared_with_dates = payments_df[
                (payments_df['Status'].str.contains('Cleared', na=False)) & 
                (payments_df['PaymentDate'].notna()) & 
                (payments_df['ClearedDate'].notna())
            ]
            
            if not cleared_with_dates.empty:
                # Calculate processing time in days
                cleared_with_dates['ProcessingDays'] = (cleared_with_dates['ClearedDate'] - cleared_with_dates['PaymentDate']).dt.days
                
                # Filter out negative or unreasonable values
                cleared_with_dates = cleared_with_dates[cleared_with_dates['ProcessingDays'] >= 0]
                
                # Create histogram
                fig = px.histogram(
                    cleared_with_dates,
                    x='ProcessingDays',
                    title='Payment Processing Time (Days)',
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Average processing time by agent
                st.subheader("Average Processing Time by Agent")
                
                # Group by agent
                agent_processing = cleared_with_dates.groupby('AgentName')['ProcessingDays'].mean().reset_index()
                agent_processing.columns = ['Agent', 'AvgProcessingDays']
                agent_processing['AvgProcessingDays'] = agent_processing['AvgProcessingDays'].round(1)
                
                # Sort by average processing days
                agent_processing = agent_processing.sort_values('AvgProcessingDays')
                
                # Create bar chart
                fig = px.bar(
                    agent_processing,
                    x='Agent',
                    y='AvgProcessingDays',
                    title='Average Processing Time by Agent (Days)',
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to analyze processing times.")
        
        # Tab 4: Raw Data
        with tabs[3]:
            st.subheader("Raw Payment Data")
            
            # Add data inspection tools
            with st.expander("Data Inspection Tools"):
                st.subheader("Data Quality Check")
                
                # Check for missing values
                missing_values = payments_df.isna().sum()
                st.write("Missing Values by Column:")
                st.write(missing_values)
                
                # Check for invalid dates
                invalid_payment_dates = payments_df[payments_df['PaymentDate'].isna()].shape[0]
                st.write(f"Invalid Payment Dates: {invalid_payment_dates}")
                
                # Show sample of original CSV
                st.subheader("Original CSV Sample")
                st.dataframe(df.head(5), use_container_width=True)
                
                # Show column mapping
                st.subheader("Column Mapping")
                st.write("Even columns (0-5, 10):")
                st.write("- Column 0 → CustomerID")
                st.write("- Column 1 → AgentName")
                st.write("- Column 2 → PaymentID")
                st.write("- Column 3 → Status")
                st.write("- Column 4 → PaymentDate")
                st.write("- Column 10 → ClearedDate")
                
                st.write("Odd columns (5-11):")
                st.write("- Column 5 → CustomerID")
                st.write("- Column 6 → AgentName")
                st.write("- Column 7 → PaymentID")
                st.write("- Column 8 → Status")
                st.write("- Column 9 → PaymentDate")
                st.write("- Column 11 → ClearedDate")
            
            # Display the raw data
            st.dataframe(payments_df, use_container_width=True)
            
            # Download option
            csv = payments_df.to_csv(index=False)
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name="commission_data.csv",
                mime="text/csv",
            )
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())