"""
Complete Performance Trends Dashboard Module
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_trends_dashboard(sales_df, COLORS, HEAT_COLORS):
    """Complete trends dashboard with all displays and working dropdown"""
    st.subheader("📈 Performance Trends")
    
    # Time range selector - RADIO BUTTONS (WORKING)
    time_range = st.radio(
        "📅 Select Time Range:",
        ["Last 30 Days", "Last 60 Days", "Last 90 Days", "Last 180 Days"],
        index=2,
        horizontal=True,
        key="trends_time_radio"
    )
    
    # Calculate date range
    end_date = sales_df['ENROLLED_DATE'].max()
    days_map = {"Last 30 Days": 30, "Last 60 Days": 60, "Last 90 Days": 90, "Last 180 Days": 180}
    start_date = end_date - timedelta(days=days_map[time_range])
    
    # Filter data for selected range
    trend_data = sales_df[
        (sales_df['ENROLLED_DATE'] >= start_date) & 
        (sales_df['ENROLLED_DATE'] <= end_date)
    ].copy()
    
    if trend_data.empty:
        st.warning("No data for selected time range")
        return
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'CATEGORY' in trend_data.columns:
            stick_rate = (len(trend_data[trend_data['CATEGORY'] == 'ACTIVE']) / len(trend_data) * 100) if len(trend_data) > 0 else 0
            st.metric("Stick Rate", f"{stick_rate:.1f}%")
    
    with col2:
        mid_date = start_date + (end_date - start_date) / 2
        first_half = len(trend_data[trend_data['ENROLLED_DATE'] < mid_date])
        second_half = len(trend_data[trend_data['ENROLLED_DATE'] >= mid_date])
        growth = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        st.metric("Sales Growth", f"{growth:+.1f}%")
    
    with col3:
        if 'AGENT' in trend_data.columns:
            avg_per_agent = len(trend_data) / trend_data['AGENT'].nunique() if trend_data['AGENT'].nunique() > 0 else 0
            efficiency = min(avg_per_agent * 10, 100)
            st.metric("Team Efficiency", f"{efficiency:.1f}%")
    
    with col4:
        if 'CATEGORY' in trend_data.columns:
            conversion_rate = (len(trend_data[trend_data['CATEGORY'] == 'ACTIVE']) / len(trend_data) * 100) if len(trend_data) > 0 else 0
            st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales Velocity")
        trend_data['Week'] = trend_data['ENROLLED_DATE'].dt.to_period('W').dt.start_time
        weekly_sales = trend_data.groupby('Week').size().reset_index()
        weekly_sales.columns = ['Week', 'Sales']
        
        if not weekly_sales.empty:
            fig = px.line(
                weekly_sales,
                x='Week',
                y='Sales',
                title=f"Weekly Sales Velocity - {time_range}",
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Agent Consistency")
        if 'AGENT' in trend_data.columns and 'CATEGORY' in trend_data.columns:
            agent_performance = trend_data.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'ACTIVE').sum()
            }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Active'})
            
            agent_performance['Stick_Rate'] = (agent_performance['Active'] / agent_performance['Total'] * 100).round(1)
            agent_performance['Volume_Weight'] = (agent_performance['Total'] / agent_performance['Total'].max() * 100).round(1)
            agent_performance['Weighted_Score'] = (agent_performance['Stick_Rate'] * 0.7 + agent_performance['Volume_Weight'] * 0.3).round(1)
            
            agent_performance = agent_performance[agent_performance['Total'] >= 3]
            agent_performance = agent_performance.sort_values('Weighted_Score', ascending=False).head(10)
            
            if not agent_performance.empty:
                fig = px.bar(
                    agent_performance,
                    x=agent_performance.index,
                    y='Weighted_Score',
                    title="Top Agents by Weighted Performance",
                    color='Weighted_Score',
                    color_continuous_scale=HEAT_COLORS,
                    hover_data=['Stick_Rate', 'Total', 'Active']
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weekly vs Monthly Comparison")
        weekly_avg = trend_data.groupby(trend_data['ENROLLED_DATE'].dt.to_period('W')).size().mean()
        monthly_avg = trend_data.groupby(trend_data['ENROLLED_DATE'].dt.to_period('M')).size().mean()
        
        comparison_data = pd.DataFrame({
            'Period': ['Weekly Average', 'Monthly Average'],
            'Sales': [weekly_avg, monthly_avg * 4]  # Scale monthly to 4 weeks
        })
        
        fig = px.bar(
            comparison_data,
            x='Period',
            y='Sales',
            title="Weekly vs Monthly Performance",
            color='Sales',
            color_continuous_scale=HEAT_COLORS
        )
        fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Source Performance Trends")
        if 'SOURCE_SHEET' in trend_data.columns and 'CATEGORY' in trend_data.columns:
            source_performance = trend_data.groupby('SOURCE_SHEET').agg({
                'SOURCE_SHEET': 'count',
                'CATEGORY': lambda x: (x == 'ACTIVE').sum()
            }).rename(columns={'SOURCE_SHEET': 'Total', 'CATEGORY': 'Active'})
            
            source_performance['Active_Rate'] = (source_performance['Active'] / source_performance['Total'] * 100).round(1)
            
            fig = px.bar(
                source_performance,
                x=source_performance.index,
                y='Active_Rate',
                title="Source Active Rates",
                color='Active_Rate',
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 3
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Trend Analysis")
        if 'ENROLLED_DATE' in trend_data.columns:
            monthly_trend = trend_data.groupby(trend_data['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
            monthly_trend.columns = ['Month', 'Sales']
            
            if not monthly_trend.empty:
                fig = px.line(
                    monthly_trend,
                    x='Month',
                    y='Sales',
                    title=f"Monthly Sales Trend - {time_range}",
                    markers=True,
                    color_discrete_sequence=[COLORS['secondary']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Status Distribution Over Time")
        if 'CATEGORY' in trend_data.columns:
            status_trend = trend_data.groupby([
                trend_data['ENROLLED_DATE'].dt.strftime('%Y-%m'),
                'CATEGORY'
            ]).size().unstack(fill_value=0)
            
            if not status_trend.empty:
                fig = px.area(
                    status_trend,
                    title="Status Distribution Trends",
                    color_discrete_map={
                        'ACTIVE': COLORS['success'],
                        'CANCELLED': COLORS['danger'],
                        'NSF': COLORS['warning'],
                        'OTHER': COLORS['info']
                    }
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Performance Tables
    st.subheader("📋 Top Performers by Stick Rate")
    if 'AGENT' in trend_data.columns and 'CATEGORY' in trend_data.columns:
        detailed_performance = trend_data.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        detailed_performance.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
        detailed_performance['Stick_Rate'] = (detailed_performance['Active_Sales'] / detailed_performance['Total_Sales'] * 100).round(1)
        detailed_performance['Volume_Weight'] = (detailed_performance['Total_Sales'] / detailed_performance['Total_Sales'].max() * 100).round(1)
        detailed_performance['Weighted_Score'] = (detailed_performance['Stick_Rate'] * 0.7 + detailed_performance['Volume_Weight'] * 0.3).round(1)
        detailed_performance['Performance_Rank'] = detailed_performance['Weighted_Score'].rank(ascending=False, method='dense').astype(int)
        
        # Filter agents with minimum activity
        qualified_agents = detailed_performance[detailed_performance['Total_Sales'] >= 3]
        qualified_agents = qualified_agents.sort_values('Weighted_Score', ascending=False).reset_index()
        
        st.dataframe(qualified_agents, use_container_width=True, hide_index=True)
    
    # Trend Analysis Summary
    with st.expander("📈 Detailed Trend Analysis"):
        display_cols = ['ENROLLED_DATE', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in trend_data.columns]
        
        if available_cols:
            display_df = trend_data[available_cols].copy()
            if 'ENROLLED_DATE' in display_df.columns:
                display_df['ENROLLED_DATE'] = display_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                f"📥 Download Trend Data ({time_range})",
                csv,
                f"trend_analysis_{time_range.lower().replace(' ', '_')}.csv",
                "text/csv"
            )