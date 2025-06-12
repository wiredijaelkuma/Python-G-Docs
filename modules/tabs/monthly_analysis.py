"""
Monthly Analysis Tab
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

def render_monthly_analysis_tab(df_filtered, COLORS):
    """Render the monthly analysis tab"""
    st.header("Monthly Performance Analysis")
    
    try:
        # Check if ENROLLED_DATE exists in the dataframe
        if 'ENROLLED_DATE' not in df_filtered.columns:
            st.error("ENROLLED_DATE column not found in the data.")
            return
            
        # Extract year and month from ENROLLED_DATE
        df_filtered['Year_Month'] = df_filtered['ENROLLED_DATE'].dt.strftime('%Y-%m')
        
        # Get unique year-months for dropdown
        year_months = sorted(df_filtered['Year_Month'].unique(), reverse=True)
        
        if not year_months:
            st.warning("No enrollment date data available.")
            return
            
        # Month selector
        selected_month = st.selectbox("Select Month", year_months)
        
        # Filter data for selected month
        monthly_data = df_filtered[df_filtered['Year_Month'] == selected_month]
        
        if monthly_data.empty:
            st.info(f"No data available for {selected_month}.")
            return
            
        # Display monthly metrics
        st.subheader(f"Key Metrics for {selected_month}")
        
        # Calculate metrics
        total_enrollments = len(monthly_data)
        active_count = monthly_data[monthly_data['CATEGORY'] == 'ACTIVE'].shape[0]
        cancelled_count = monthly_data[monthly_data['CATEGORY'] == 'CANCELLED'].shape[0]
        nsf_count = monthly_data[monthly_data['CATEGORY'] == 'NSF'].shape[0] if 'NSF' in monthly_data['CATEGORY'].values else 0
        
        # Calculate rates
        active_rate = (active_count / total_enrollments * 100) if total_enrollments > 0 else 0
        cancelled_rate = (cancelled_count / total_enrollments * 100) if total_enrollments > 0 else 0
        stick_rate = active_rate  # Stick rate is the same as active rate
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Enrollments", total_enrollments)
        col1.metric("Active", active_count)
        col1.metric("Cancelled", cancelled_count)
        
        col2.metric("Active Rate", f"{active_rate:.1f}%")
        col2.metric("Cancellation Rate", f"{cancelled_rate:.1f}%")
        col2.metric("Stick Rate", f"{stick_rate:.1f}%")
        
        col3.metric("NSF Count", nsf_count)
        
        # Agent performance for the month
        st.subheader("Agent Performance")
        
        # Group by agent
        agent_performance = monthly_data.groupby('AGENT').agg(
            Enrollments=('CUSTOMER ID', 'count'),
            Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
            Cancelled=('CATEGORY', lambda x: (x == 'CANCELLED').sum())
        ).reset_index()
        
        # Calculate stick rate for each agent
        agent_performance['Stick Rate'] = (agent_performance['Active'] / agent_performance['Enrollments'] * 100).round(1)
        agent_performance['Stick Rate'] = agent_performance['Stick Rate'].apply(lambda x: f"{x}%")
        
        # Sort by enrollments
        agent_performance = agent_performance.sort_values('Enrollments', ascending=False)
        
        # Display agent performance
        st.dataframe(agent_performance, use_container_width=True)
        
        # Create bar chart for agent enrollments
        fig = px.bar(
            agent_performance,
            x='AGENT',
            y='Enrollments',
            title=f'Enrollments by Agent for {selected_month}',
            color_discrete_sequence=[COLORS['primary']]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Status distribution pie chart
        st.subheader("Status Distribution")
        
        status_counts = monthly_data['STATUS'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        fig = px.pie(
            status_counts,
            values='Count',
            names='Status',
            title=f'Status Distribution for {selected_month}',
            color_discrete_sequence=[COLORS['primary'], COLORS['accent'], COLORS['warning'], COLORS['danger']]
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
        # Daily enrollment trend for the month
        st.subheader("Daily Enrollment Trend")
        
        # Extract day from ENROLLED_DATE
        monthly_data['Day'] = monthly_data['ENROLLED_DATE'].dt.day
        
        # Group by day
        daily_counts = monthly_data.groupby('Day').size().reset_index()
        daily_counts.columns = ['Day', 'Count']
        
        # Sort by day
        daily_counts = daily_counts.sort_values('Day')
        
        # Create line chart
        fig = px.line(
            daily_counts,
            x='Day',
            y='Count',
            title=f'Daily Enrollments for {selected_month}',
            markers=True,
            color_discrete_sequence=[COLORS['primary']]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Month-over-month comparison
        st.subheader("Month-over-Month Comparison")
        
        # Group all data by year-month
        monthly_trends = df_filtered.groupby('Year_Month').agg(
            Enrollments=('CUSTOMER ID', 'count'),
            Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
            Cancelled=('CATEGORY', lambda x: (x == 'CANCELLED').sum())
        ).reset_index()
        
        # Calculate stick rate
        monthly_trends['Stick Rate'] = (monthly_trends['Active'] / monthly_trends['Enrollments'] * 100).round(1)
        
        # Sort by year-month
        monthly_trends = monthly_trends.sort_values('Year_Month')
        
        # Create line chart for enrollments trend
        fig = px.line(
            monthly_trends,
            x='Year_Month',
            y='Enrollments',
            title='Monthly Enrollment Trend',
            markers=True,
            color_discrete_sequence=[COLORS['primary']]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Create line chart for stick rate trend
        fig = px.line(
            monthly_trends,
            x='Year_Month',
            y='Stick Rate',
            title='Monthly Stick Rate Trend (%)',
            markers=True,
            color_discrete_sequence=[COLORS['accent']]
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())