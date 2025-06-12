"""
Ultra-minimal Commission Tab
"""
import streamlit as st
import pandas as pd

def render_commission_tab(df_filtered, COLORS):
    """Render the commission tab"""
    st.header("Commission Dashboard")
    
    try:
        # Read CSV directly
        df = pd.read_csv("comissions.csv", header=0)
        
        # Create a clean dataframe with just the data we need
        data = []
        
        # Process even columns (0-5)
        for i in range(len(df)):
            if pd.notna(df.iloc[i, 1]) and df.iloc[i, 1] != "":  # Check if agent name exists
                data.append({
                    'CustomerID': str(df.iloc[i, 0]),
                    'AgentName': str(df.iloc[i, 1]),
                    'PaymentID': str(df.iloc[i, 2]),
                    'Status': str(df.iloc[i, 3]),
                    'PaymentDate': str(df.iloc[i, 4]),
                    'ClearedDate': str(df.iloc[i, 5])
                })
        
        # Process odd columns (6-11)
        for i in range(len(df)):
            if pd.notna(df.iloc[i, 7]) and df.iloc[i, 7] != "":  # Check if agent name exists
                data.append({
                    'CustomerID': str(df.iloc[i, 6]),
                    'AgentName': str(df.iloc[i, 7]),
                    'PaymentID': str(df.iloc[i, 8]),
                    'Status': str(df.iloc[i, 9]),
                    'PaymentDate': str(df.iloc[i, 10]),
                    'ClearedDate': str(df.iloc[i, 11])
                })
        
        # Convert to dataframe
        payments_df = pd.DataFrame(data)
        
        # Create tabs
        tabs = st.tabs(["Agent Summary", "Recent Cleared Payments"])
        
        # Tab 1: Agent Summary
        with tabs[0]:
            st.subheader("Agent Payment Summary")
            
            # Get list of agents without sorting
            agents = list(set([a for a in payments_df['AgentName'] if a]))
            
            # Agent selector
            selected_agent = st.selectbox("Select Agent", agents)
            
            # Filter data for selected agent
            agent_data = payments_df[payments_df['AgentName'] == selected_agent]
            
            # Get unique customer IDs for this agent
            customer_ids = list(set([c for c in agent_data['CustomerID'] if c]))
            
            # Create summary for each customer
            customer_summary = []
            for cid in customer_ids:
                customer_payments = agent_data[agent_data['CustomerID'] == cid]
                
                # Count payment statuses
                cleared = sum('Cleared' in str(s) for s in customer_payments['Status'])
                nsf = sum(('NSF' in str(s) or 'Returned' in str(s)) for s in customer_payments['Status'])
                pending = sum('Pending' in str(s) for s in customer_payments['Status'])
                
                customer_summary.append({
                    'CustomerID': cid,
                    'TotalPayments': len(customer_payments),
                    'Cleared': cleared,
                    'NSF': nsf,
                    'Pending': pending
                })
            
            # Convert to dataframe
            if customer_summary:
                summary_df = pd.DataFrame(customer_summary)
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
        
        # Tab 2: Recent Cleared Payments
        with tabs[1]:
            st.subheader("Recent Cleared Payments")
            
            # Filter for cleared payments only
            cleared_payments = payments_df[[('Cleared' in str(s)) for s in payments_df['Status']]]
            
            # Display the table
            st.dataframe(cleared_payments, use_container_width=True)
            
            # Agent summary
            st.subheader("Agent Summary")
            
            # Count cleared payments by agent
            agent_counts = {}
            for agent in set(cleared_payments['AgentName']):
                agent_counts[agent] = sum(cleared_payments['AgentName'] == agent)
            
            # Convert to dataframe
            agent_summary = pd.DataFrame([
                {'Agent': agent, 'Cleared Payments': count}
                for agent, count in agent_counts.items()
            ])
            
            # Display agent summary
            st.dataframe(agent_summary, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())