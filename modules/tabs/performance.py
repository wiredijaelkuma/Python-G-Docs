"""
Performance Tab Module - Analyzes performance metrics
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def process_commission_data(df_filtered):
    """Process commission data for performance metrics"""
    try:
        # Debug: Show available sheets
        if 'SOURCE_SHEET' in df_filtered.columns:
            available_sheets = df_filtered['SOURCE_SHEET'].unique().tolist()
            st.info(f"Available sheets: {available_sheets}")
        else:
            st.warning("No SOURCE_SHEET column found")
            return pd.DataFrame()
            
        # Get commission data from the filtered dataframe (try both spellings)
        commission_sheet = None
        if 'Comission' in df_filtered['SOURCE_SHEET'].values:
            commission_sheet = 'Comission'
        elif 'Commission' in df_filtered['SOURCE_SHEET'].values:
            commission_sheet = 'Commission'
            
        if not commission_sheet:
            st.warning("No commission data found. Please make sure the 'Comission' or 'Commission' worksheet exists in your Google Sheet.")
            return pd.DataFrame()
            
        # Get commission data from the filtered dataframe
        commission_data = df_filtered[df_filtered['SOURCE_SHEET'] == commission_sheet]
        
        if commission_data.empty:
            st.warning("Commission data is empty. Please add data to the 'Comission' worksheet in your Google Sheet.")
            return pd.DataFrame()
            
        # Rename columns to match expected format
        df = commission_data.copy()
        
        # Create column mapping
        column_mapping = {
            'CUSTOMER ID': 'CustomerID',
            'AGENT': 'AgentName',
            'TRANSACTION ID': 'PaymentID',
            'STATUS': 'Status',
            'PROCESSED DATE': 'PaymentDate',
            'CLEARED DATE': 'ClearedDate'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)
        
        # Remove rows where CustomerID is empty
        df = df[df['CustomerID'].notna() & (df['CustomerID'] != "")]
        
        # Create a payment status column
        df['PaymentStatus'] = df['Status'].apply(
            lambda x: 'Cleared' if 'Cleared' in str(x) else 'NSF' if 'NSF' in str(x) or 'Returned' in str(x) else 'Pending'
        )
        
        return df
    except Exception as e:
        st.error(f"Error processing commission data: {e}")
        return pd.DataFrame()

def render_performance_tab(df, COLORS):
    """Render the performance tab with trend analysis"""
    
    st.subheader("Performance Metrics")
    
    # Process commission data for performance metrics
    commission_df = process_commission_data(df)
    
    if commission_df.empty:
        st.error("Could not load commission data for performance metrics.")
        return
    
    # Create tabs for different performance views
    perf_tabs = st.tabs(["Agent Performance", "Stick Rate", "Risk Analysis"])
    
    # Agent Performance Tab
    with perf_tabs[0]:
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
        agent_stats['NSFRate'] = (agent_stats['NSFPayments'] / agent_stats['TotalPayments'] * 100).round(1)
        
        # Sort by cleared payments
        agent_stats = agent_stats.sort_values('ClearedPayments', ascending=False)
        
        # Create columns for metrics and gauge
        col1, col2 = st.columns([2, 1])
        
        with col1:
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
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Calculate overall clear rate
            total_payments = agent_stats['TotalPayments'].sum()
            total_cleared = agent_stats['ClearedPayments'].sum()
            overall_clear_rate = (total_cleared / total_payments * 100) if total_payments > 0 else 0
            
            # Create gauge chart for overall clear rate
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=overall_clear_rate,
                title={'text': "Overall Clear Rate"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': COLORS['light_green']},
                    'steps': [
                        {'range': [0, 30], 'color': COLORS['danger']},
                        {'range': [30, 70], 'color': COLORS['warning']},
                        {'range': [70, 100], 'color': COLORS['light_green']}
                    ]
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        # Display table
        st.subheader("Agent Performance Details")
        st.dataframe(
            agent_stats.rename(columns={
                'AgentName': 'Agent',
                'TotalPayments': 'Total',
                'ClearedPayments': 'Cleared',
                'NSFPayments': 'NSF',
                'UniqueCustomers': 'Unique Customers',
                'ClearRate': 'Clear Rate (%)',
                'NSFRate': 'NSF Rate (%)'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    # Stick Rate Tab
    with perf_tabs[1]:
        st.subheader("Stick Rate Analysis")
        
        # Calculate monthly stick rates
        commission_df['Month'] = commission_df['PaymentDate'].dt.strftime('%Y-%m')
        monthly_total = commission_df.groupby('Month').size()
        monthly_cleared = commission_df[commission_df['PaymentStatus'] == 'Cleared'].groupby('Month').size()
        
        stick_rate_data = pd.DataFrame({
            'Month': monthly_total.index,
            'Total': monthly_total.values,
            'Cleared': monthly_cleared.reindex(monthly_total.index, fill_value=0).values
        })
        
        stick_rate_data['StickRate'] = (stick_rate_data['Cleared'] / stick_rate_data['Total'] * 100).round(1)
        
        # Create columns for chart and gauge
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create the chart
            fig = px.line(
                stick_rate_data, 
                x='Month', 
                y='StickRate',
                markers=True,
                title='Monthly Stick Rate (%)',
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(yaxis_title="Stick Rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Calculate overall stick rate
            total_payments = stick_rate_data['Total'].sum()
            total_cleared = stick_rate_data['Cleared'].sum()
            overall_stick_rate = (total_cleared / total_payments * 100) if total_payments > 0 else 0
            
            # Create gauge chart for overall stick rate
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=overall_stick_rate,
                title={'text': "Overall Stick Rate"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': COLORS['primary']},
                    'steps': [
                        {'range': [0, 30], 'color': COLORS['danger']},
                        {'range': [30, 70], 'color': COLORS['warning']},
                        {'range': [70, 100], 'color': COLORS['light_green']}
                    ]
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        # Year to date analysis
        st.subheader("Year-to-Date Stick Rate")
        
        # Get current year
        current_year = datetime.now().year
        
        # Filter for current year data
        ytd_data = commission_df[commission_df['PaymentDate'].dt.year == current_year]
        
        if not ytd_data.empty:
            # Group by month
            ytd_data['Month'] = ytd_data['PaymentDate'].dt.strftime('%B')  # Month name
            ytd_data['MonthNum'] = ytd_data['PaymentDate'].dt.month  # Month number for sorting
            
            monthly_ytd = ytd_data.groupby(['Month', 'MonthNum']).agg(
                Total=('PaymentID', 'count'),
                Cleared=('PaymentStatus', lambda x: (x == 'Cleared').sum())
            ).reset_index()
            
            # Calculate stick rate
            monthly_ytd['StickRate'] = (monthly_ytd['Cleared'] / monthly_ytd['Total'] * 100).round(1)
            
            # Sort by month number
            monthly_ytd = monthly_ytd.sort_values('MonthNum')
            
            # Create bar chart
            fig = px.bar(
                monthly_ytd,
                x='Month',
                y='StickRate',
                title=f'{current_year} Monthly Stick Rate',
                color='StickRate',
                color_continuous_scale=px.colors.sequential.Viridis,
                text='StickRate'
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    
    # Risk Analysis Tab
    with perf_tabs[2]:
        st.subheader("Risk Analysis")
        
        # Group by agent for risk analysis
        agent_risk = commission_df.groupby('AgentName').agg(
            TotalPayments=('PaymentID', 'count'),
            ClearedPayments=('PaymentStatus', lambda x: (x == 'Cleared').sum()),
            NSFPayments=('PaymentStatus', lambda x: (x == 'NSF').sum()),
            UniqueCustomers=('CustomerID', 'nunique')
        ).reset_index()
        
        # Calculate risk metrics
        agent_risk['NSFRate'] = (agent_risk['NSFPayments'] / agent_risk['TotalPayments'] * 100).round(1)
        agent_risk['RiskScore'] = agent_risk['NSFRate']  # Simple risk score based on NSF rate
        
        # Sort by risk score (highest risk first)
        agent_risk = agent_risk.sort_values('RiskScore', ascending=False)
        
        # Create columns for chart and gauge
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create horizontal bar chart for risk scores
            fig = px.bar(
                agent_risk.head(10),  # Top 10 riskiest agents
                y='AgentName',
                x='RiskScore',
                orientation='h',
                title='Agent Risk Scores (Higher = Riskier)',
                color='RiskScore',
                color_continuous_scale=px.colors.sequential.Reds,
                text='RiskScore'
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Calculate overall risk score
            overall_risk = agent_risk['RiskScore'].mean()
            
            # Create gauge chart for overall risk
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=overall_risk,
                title={'text': "Overall Risk Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': COLORS['danger']},
                    'steps': [
                        {'range': [0, 30], 'color': COLORS['light_green']},
                        {'range': [30, 70], 'color': COLORS['warning']},
                        {'range': [70, 100], 'color': COLORS['danger']}
                    ]
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        # Risk by customer count
        st.subheader("Risk vs Customer Volume")
        
        # Create scatter plot of risk vs customer count
        fig = px.scatter(
            agent_risk,
            x='UniqueCustomers',
            y='RiskScore',
            size='TotalPayments',
            color='RiskScore',
            hover_name='AgentName',
            color_continuous_scale=px.colors.sequential.Reds,
            title='Risk Score vs Customer Volume'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display risk table
        st.subheader("Agent Risk Details")
        st.dataframe(
            agent_risk.rename(columns={
                'AgentName': 'Agent',
                'TotalPayments': 'Total',
                'ClearedPayments': 'Cleared',
                'NSFPayments': 'NSF',
                'UniqueCustomers': 'Customers',
                'NSFRate': 'NSF Rate (%)',
                'RiskScore': 'Risk Score'
            }),
            use_container_width=True,
            hide_index=True
        )