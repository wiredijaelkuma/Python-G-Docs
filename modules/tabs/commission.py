"""
Commission Tab Module - Analyzes agent commission data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import pandas as pd
from datetime import datetime

def process_commission_data(file_path="comissions.csv"):
    """Process the commission CSV file with even/odd columns"""
    try:
        # Read the raw CSV file
        df = pd.read_csv(file_path)
        
        # Extract even and odd columns
        even_df = df.iloc[:, 0:6].copy()
        even_df.columns = ['CustomerID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        odd_df = df.iloc[:, 6:12].copy()
        odd_df.columns = ['CustomerID', 'AgentName', 'PaymentID', 'Status', 'PaymentDate', 'ClearedDate']
        
        # Combine the dataframes
        combined_df = pd.concat([even_df, odd_df], ignore_index=True)
        
        # Remove rows where CustomerID is empty
        combined_df = combined_df[combined_df['CustomerID'].notna() & (combined_df['CustomerID'] != "")]
        
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
    
    try:
        # Process the commission data
        commission_df = process_commission_data()
        
        if commission_df.empty:
            st.error("Could not load commission data.")
            return
        
        # Create tabs for different views
        comm_tabs = st.tabs(["Expected Payments", "Agent Performance", "Customer Lifespan"])
        
        # Expected Payments Tab
        with comm_tabs[0]:
            st.subheader("Expected Commission Payments")
            
            # Filter for only cleared payments
            cleared_df = commission_df[commission_df['PaymentStatus'] == 'Cleared'].copy()
            
            if cleared_df.empty:
                st.info("No cleared payments found in the data.")
                return
                
            # Add 7 days to cleared date to get expected payment date
            cleared_df['ExpectedPaymentDate'] = cleared_df['ClearedDate'] + pd.Timedelta(days=7)
            
            # Time period filter
            col1, col2 = st.columns(2)
            
            with col1:
                payment_window = st.selectbox(
                    "Payment Window",
                    ["Next 7 Days", "Next 14 Days", "Next 30 Days", "All Expected"],
                    index=0
                )
                
                # Filter by expected payment date
                today = pd.Timestamp.now()
                if payment_window == "Next 7 Days":
                    end_date = today + pd.Timedelta(days=7)
                elif payment_window == "Next 14 Days":
                    end_date = today + pd.Timedelta(days=14)
                elif payment_window == "Next 30 Days":
                    end_date = today + pd.Timedelta(days=30)
                else:
                    end_date = cleared_df['ExpectedPaymentDate'].max()
                
                # Filter by expected payment date
                expected_payments = cleared_df[
                    (cleared_df['ExpectedPaymentDate'] >= today) & 
                    (cleared_df['ExpectedPaymentDate'] <= end_date)
                ]
            
            with col2:
                # Agent filter
                agents = cleared_df['AgentName'].fillna("Unknown").unique().tolist()
                agents = sorted([str(a) for a in agents if a])
                    
                selected_agents = st.multiselect(
                    "Select Agents",
                    agents,
                    default=agents
                )
                
                if selected_agents and not expected_payments.empty:
                    expected_payments = expected_payments[expected_payments['AgentName'].isin(selected_agents)]
            
            # Display metrics
            total_expected = len(expected_payments)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Expected Payments", f"{total_expected:,}")
            with col2:
                # Assuming $10 per commission
                st.metric("Total Commission Value", f"${total_expected * 10:,}")
            
            if not expected_payments.empty:
                # Group by agent
                agent_expected = expected_payments.groupby('AgentName').size().reset_index(name='ExpectedCount')
                agent_expected = agent_expected.sort_values('ExpectedCount', ascending=False)
                
                # Create bar chart
                fig = px.bar(
                    agent_expected,
                    x='AgentName',
                    y='ExpectedCount',
                    title='Expected Payments by Agent',
                    labels={'ExpectedCount': 'Number of Expected Payments', 'AgentName': 'Agent'},
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True, key="expected_payments_chart")
                
                # Display table of expected payments
                st.subheader("Expected Payments Detail")
                display_cols = ['CustomerID', 'AgentName', 'PaymentID', 'PaymentDate', 'ClearedDate', 'ExpectedPaymentDate']
                display_df = expected_payments[display_cols].copy()
                
                # Format dates
                display_df['PaymentDate'] = display_df['PaymentDate'].dt.strftime('%Y-%m-%d')
                display_df['ClearedDate'] = display_df['ClearedDate'].dt.strftime('%Y-%m-%d')
                display_df['ExpectedPaymentDate'] = display_df['ExpectedPaymentDate'].dt.strftime('%Y-%m-%d')
                
                # Show table
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Download button
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download Expected Payments",
                    data=csv,
                    file_name="expected_payments.csv",
                    mime="text/csv",
                )
            else:
                st.info("No expected payments found for the selected time period.")
        
        # Agent Performance Tab
        with comm_tabs[1]:
            st.subheader("Agent Performance")
            
            # Group by agent
            agent_stats = commission_df.groupby('AgentName').agg(
                TotalPayments=('PaymentID', 'count'),
                ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
                NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
                UniqueCustomers=('CustomerID', 'nunique')
            ).reset_index()
            
            # Fill NaN values
            agent_stats = agent_stats.fillna(0)
            
            # Calculate rates
            agent_stats['ClearRate'] = (agent_stats['ClearedPayments'] / agent_stats['TotalPayments'] * 100).round(1)
            
            # Sort by cleared payments
            agent_stats = agent_stats.sort_values('ClearedPayments', ascending=False)
            
            # Display table
            st.dataframe(
                agent_stats.rename(columns={
                    'AgentName': 'Agent',
                    'TotalPayments': 'Total Payments',
                    'ClearedPayments': 'Cleared',
                    'NSFPayments': 'NSF',
                    'UniqueCustomers': 'Unique Customers',
                    'ClearRate': 'Clear Rate (%)'
                }),
                use_container_width=True,
                hide_index=True
            )
            
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
            st.plotly_chart(fig, use_container_width=True, key="agent_performance_chart")
        
        # Customer Lifespan Tab
        with comm_tabs[2]:
            st.subheader("Customer Lifespan Analysis")
            
            # Group by CustomerID to get payment history
            customer_stats = commission_df.groupby('CustomerID').agg(
                FirstPayment=('PaymentDate', 'min'),
                LastPayment=('PaymentDate', 'max'),
                TotalPayments=('PaymentID', 'count'),
                ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
                NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
                Agent=('AgentName', 'first')
            ).reset_index()
            
            # Fill NaN values
            customer_stats['Agent'] = customer_stats['Agent'].fillna("Unknown")
            
            # Calculate lifespan in days
            customer_stats['Lifespan'] = (customer_stats['LastPayment'] - customer_stats['FirstPayment']).dt.days
            customer_stats['Lifespan'] = customer_stats['Lifespan'].fillna(0).astype(int)
            
            # Calculate success rate
            customer_stats['SuccessRate'] = (customer_stats['ClearedPayments'] / customer_stats['TotalPayments'] * 100).round(1)
            
            # Identify nurtured IDs (3+ payments with 50%+ success rate)
            customer_stats['Nurtured'] = (customer_stats['TotalPayments'] >= 3) & (customer_stats['SuccessRate'] >= 50)
            
            # Filter controls
            col1, col2 = st.columns(2)
            
            with col1:
                min_payments = st.slider("Minimum Number of Payments", 1, 
                                        max(1, int(customer_stats['TotalPayments'].max())), 1)
                filtered_customers = customer_stats[customer_stats['TotalPayments'] >= min_payments]
            
            with col2:
                show_nurtured = st.checkbox("Show Only Nurtured Customers", value=False)
                if show_nurtured:
                    filtered_customers = filtered_customers[filtered_customers['Nurtured']]
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Customers", f"{len(filtered_customers):,}")
            with col2:
                avg_lifespan = filtered_customers['Lifespan'].mean()
                st.metric("Average Lifespan (days)", f"{avg_lifespan:.1f}")
            with col3:
                nurtured_count = filtered_customers['Nurtured'].sum()
                st.metric("Nurtured Customers", f"{nurtured_count:,}")
            
            if not filtered_customers.empty:
                # Display table
                st.subheader("Customer Lifespan Details")
                display_cols = ['CustomerID', 'Agent', 'FirstPayment', 'LastPayment', 
                                'Lifespan', 'TotalPayments', 'ClearedPayments', 'NSFPayments', 
                                'SuccessRate', 'Nurtured']
                display_df = filtered_customers[display_cols].copy()
                
                # Format dates
                display_df['FirstPayment'] = display_df['FirstPayment'].dt.strftime('%Y-%m-%d')
                display_df['LastPayment'] = display_df['LastPayment'].dt.strftime('%Y-%m-%d')
                
                # Show table
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No customers match the current filters.")
    
    except Exception as e:
        st.error(f"Error in commission tab: {str(e)}")
        import traceback
        st.error(traceback.format_exc())