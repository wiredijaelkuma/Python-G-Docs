"""
Commission Dashboard Module
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_commission_dashboard(df, COLORS, HEAT_COLORS):
    """Render comprehensive commission dashboard"""
    st.header("💰 Commission Dashboard")
    
    if 'SOURCE_SHEET' not in df.columns or 'Comission' not in df['SOURCE_SHEET'].values:
        st.warning("No commission data found")
        return
    
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy()
    
    if commission_df.empty:
        st.warning("Commission data is empty")
        return
    
    st.success(f"Commission data loaded: {len(commission_df)} records")
    
    # Commission metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Payments", len(commission_df))
    
    with col2:
        if 'CATEGORY' in commission_df.columns:
            cleared_count = len(commission_df[commission_df['CATEGORY'] == 'CLEARED'])
            st.metric("Cleared Payments", cleared_count)
    
    with col3:
        if 'CATEGORY' in commission_df.columns:
            pending_count = len(commission_df[commission_df['CATEGORY'] == 'PENDING'])
            st.metric("Pending Payments", pending_count)
    
    with col4:
        if 'CATEGORY' in commission_df.columns:
            nsf_count = len(commission_df[commission_df['CATEGORY'] == 'NSF'])
            st.metric("NSF Payments", nsf_count)
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Payment Status Distribution")
        if 'CATEGORY' in commission_df.columns:
            status_counts = commission_df['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Commission Payment Status",
                color_discrete_map={
                    'CLEARED': COLORS['success'],
                    'PENDING': COLORS['warning'],
                    'NSF': COLORS['danger'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Agent Payment Volume")
        if 'AGENT' in commission_df.columns:
            agent_payments = commission_df['AGENT'].value_counts().head(10)
            
            fig = px.bar(
                x=agent_payments.index,
                y=agent_payments.values,
                title="Top 10 Agents by Payment Volume",
                color=agent_payments.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Payment Success Rate by Agent")
        if 'AGENT' in commission_df.columns and 'CATEGORY' in commission_df.columns:
            agent_success = commission_df.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'CLEARED').sum()
            }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Cleared'})
            
            agent_success['Success_Rate'] = (agent_success['Cleared'] / agent_success['Total'] * 100).round(1)
            agent_success = agent_success[agent_success['Total'] >= 3].sort_values('Success_Rate', ascending=False).head(10)
            
            if not agent_success.empty:
                fig = px.bar(
                    agent_success,
                    x=agent_success.index,
                    y='Success_Rate',
                    title="Top Agents by Payment Success Rate",
                    color='Success_Rate',
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Monthly Payment Trends")
        if 'PROCESSED_DATE' in commission_df.columns:
            commission_df['Month'] = commission_df['PROCESSED_DATE'].dt.strftime('%Y-%m')
            monthly_payments = commission_df.groupby('Month').size().reset_index()
            monthly_payments.columns = ['Month', 'Payments']
            
            if not monthly_payments.empty:
                fig = px.line(
                    monthly_payments,
                    x='Month',
                    y='Payments',
                    title="Monthly Payment Volume",
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Agent Performance Table
    st.subheader("📋 Agent Commission Performance")
    if 'AGENT' in commission_df.columns and 'CATEGORY' in commission_df.columns:
        agent_commission_summary = commission_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'CLEARED').sum(),
                lambda x: (x == 'PENDING').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        agent_commission_summary.columns = ['Total_Payments', 'Cleared', 'Pending', 'NSF']
        agent_commission_summary['Success_Rate'] = (agent_commission_summary['Cleared'] / agent_commission_summary['Total_Payments'] * 100).round(1)
        agent_commission_summary['NSF_Rate'] = (agent_commission_summary['NSF'] / agent_commission_summary['Total_Payments'] * 100).round(1)
        agent_commission_summary = agent_commission_summary.sort_values('Success_Rate', ascending=False).reset_index()
        
        st.dataframe(agent_commission_summary, use_container_width=True, hide_index=True)
    
    # Time-based Analysis
    st.subheader("📅 Time-based Commission Analysis")
    
    # Time range selector
    time_options = ["Last 30 Days", "Last 60 Days", "Last 90 Days", "All Time"]
    from modules.dropdown_utils import create_time_range_selector
    selected_range = create_time_range_selector("commission")
    
    # Filter by time range
    if selected_range != "All Time" and 'PROCESSED_DATE' in commission_df.columns:
        days_map = {"Last 30 Days": 30, "Last 60 Days": 60, "Last 90 Days": 90}
        cutoff_date = commission_df['PROCESSED_DATE'].max() - timedelta(days=days_map[selected_range])
        filtered_commission = commission_df[commission_df['PROCESSED_DATE'] >= cutoff_date]
    else:
        filtered_commission = commission_df
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status Breakdown by Time")
        if 'CATEGORY' in filtered_commission.columns:
            time_status = filtered_commission['CATEGORY'].value_counts()
            
            fig = px.bar(
                x=time_status.index,
                y=time_status.values,
                title=f"Payment Status - {selected_range}",
                color=time_status.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Daily Payment Activity")
        if 'PROCESSED_DATE' in filtered_commission.columns:
            daily_payments = filtered_commission.groupby(filtered_commission['PROCESSED_DATE'].dt.date).size().reset_index()
            daily_payments.columns = ['Date', 'Payments']
            
            if not daily_payments.empty:
                fig = px.line(
                    daily_payments,
                    x='Date',
                    y='Payments',
                    title=f"Daily Payment Activity - {selected_range}",
                    markers=True,
                    color_discrete_sequence=[COLORS['secondary']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Detailed Commission Data
    with st.expander("📋 Detailed Commission Data"):
        display_cols = ['PROCESSED_DATE', 'CLEARED_DATE', 'AGENT', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in commission_df.columns]
        
        if available_cols:
            display_df = commission_df[available_cols].copy()
            
            # Format dates
            for date_col in ['PROCESSED_DATE', 'CLEARED_DATE']:
                if date_col in display_df.columns:
                    display_df[date_col] = display_df[date_col].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                "📥 Download Commission Data",
                csv,
                "commission_data.csv",
                "text/csv"
            )