"""
Comprehensive Agent Analysis Module - Sales + Commission Data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def render_agent_analysis(df, COLORS, HEAT_COLORS):
    """Render comprehensive agent analysis with sales and commission data"""
    
    if 'AGENT' not in df.columns:
        st.warning("No agent data available")
        return
    
    # Separate sales and commission data
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    
    # Agent Analysis subtabs
    subtabs = st.tabs(["💰 Lifespan Analysis", "📈 Payment Trends", "🎯 Performance Metrics"])
    
    with subtabs[0]:
        render_lifespan_analysis(sales_df, commission_df, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_payment_trends(sales_df, commission_df, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        render_performance_metrics(sales_df, commission_df, COLORS, HEAT_COLORS)

def render_lifespan_analysis(sales_df, commission_df, COLORS, HEAT_COLORS):
    """Analyze customer lifespan using sales and commission data"""
    st.subheader("💰 Customer Lifespan Analysis")
    
    # Agent selector with proper styling
    if not sales_df.empty:
        agents = ['All Agents'] + sorted(sales_df['AGENT'].dropna().unique().tolist())
        selected_agent = st.selectbox(
            "🔍 Select Agent for Analysis:",
            options=agents,
            index=0,
            key="lifespan_agent_selector"
        )
        
        if selected_agent == 'All Agents':
            agent_sales = sales_df
            agent_commission = commission_df
        else:
            agent_sales = sales_df[sales_df['AGENT'] == selected_agent] if not sales_df.empty else pd.DataFrame()
            agent_commission = commission_df[commission_df['AGENT'] == selected_agent] if not commission_df.empty else pd.DataFrame()
    else:
        st.warning("No sales data available")
        return
    
    # Lifespan metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_customers = len(agent_sales) if not agent_sales.empty else 0
        st.metric("Total Customers", total_customers)
    
    with col2:
        if not agent_sales.empty and 'CATEGORY' in agent_sales.columns:
            active_customers = len(agent_sales[agent_sales['CATEGORY'] == 'ACTIVE'])
            st.metric("Active Customers", active_customers)
        else:
            st.metric("Active Customers", 0)
    
    with col3:
        if not agent_sales.empty and 'CATEGORY' in agent_sales.columns:
            cancelled_customers = len(agent_sales[agent_sales['CATEGORY'] == 'CANCELLED'])
            st.metric("Cancelled Customers", cancelled_customers)
        else:
            st.metric("Cancelled Customers", 0)
    
    with col4:
        total_payments = len(agent_commission) if not agent_commission.empty else 0
        st.metric("Total Payments", total_payments)
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Status Distribution")
        if not agent_sales.empty and 'CATEGORY' in agent_sales.columns:
            status_counts = agent_sales['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title=f"Status Distribution - {selected_agent}",
                color_discrete_map={
                    'ACTIVE': COLORS['success'],
                    'CANCELLED': COLORS['danger'],
                    'NSF': COLORS['warning'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available")
    
    with col2:
        st.subheader("Payment Status Distribution")
        if not agent_commission.empty and 'STATUS' in agent_commission.columns:
            payment_status = agent_commission['STATUS'].value_counts()
            
            fig = px.bar(
                x=payment_status.index,
                y=payment_status.values,
                title=f"Payment Status - {selected_agent}",
                color=payment_status.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No payment data available")
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Lifespan Timeline")
        if not agent_sales.empty and 'ENROLLED_DATE' in agent_sales.columns:
            # Create lifespan analysis
            monthly_enrollments = agent_sales.groupby(agent_sales['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
            monthly_enrollments.columns = ['Month', 'New_Customers']
            
            if not monthly_enrollments.empty:
                fig = px.line(
                    monthly_enrollments,
                    x='Month',
                    y='New_Customers',
                    title="Monthly Customer Enrollments",
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No enrollment date data available")
    
    with col2:
        st.subheader("NSF Trend Analysis")
        if not agent_sales.empty and 'CATEGORY' in agent_sales.columns and 'ENROLLED_DATE' in agent_sales.columns:
            nsf_data = agent_sales[agent_sales['CATEGORY'] == 'NSF'].copy()
            if not nsf_data.empty:
                monthly_nsf = nsf_data.groupby(nsf_data['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
                monthly_nsf.columns = ['Month', 'NSF_Count']
                
                fig = px.bar(
                    monthly_nsf,
                    x='Month',
                    y='NSF_Count',
                    title="Monthly NSF Trends",
                    color='NSF_Count',
                    color_continuous_scale=[[0, COLORS['warning']], [1, COLORS['danger']]]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No NSF data available")
        else:
            st.info("No NSF trend data available")
    
    # Lifespan summary table
    st.subheader("📋 Customer Lifespan Summary")
    if not agent_sales.empty:
        lifespan_summary = agent_sales.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        lifespan_summary.columns = ['Total_Customers', 'Active', 'Cancelled', 'NSF']
        lifespan_summary['Retention_Rate'] = (lifespan_summary['Active'] / lifespan_summary['Total_Customers'] * 100).round(1)
        lifespan_summary['Churn_Rate'] = (lifespan_summary['Cancelled'] / lifespan_summary['Total_Customers'] * 100).round(1)
        lifespan_summary = lifespan_summary.sort_values('Retention_Rate', ascending=False).reset_index()
        
        st.dataframe(lifespan_summary, use_container_width=True, hide_index=True)

def render_payment_trends(sales_df, commission_df, COLORS, HEAT_COLORS):
    """Analyze payment trends and patterns"""
    st.subheader("📈 Payment Trends Analysis")
    
    # Time range selector
    time_options = ["Last 30 Days", "Last 60 Days", "Last 90 Days", "Last 180 Days", "All Time"]
    selected_range = st.selectbox(
        "📅 Select Time Range:",
        options=time_options,
        index=2,
        key="payment_trends_time_range"
    )
    
    # Filter data based on time range
    if selected_range != "All Time" and not commission_df.empty:
        days_map = {"Last 30 Days": 30, "Last 60 Days": 60, "Last 90 Days": 90, "Last 180 Days": 180}
        if 'ENROLLED_DATE' in commission_df.columns:
            cutoff_date = commission_df['ENROLLED_DATE'].max() - timedelta(days=days_map[selected_range])
            filtered_commission = commission_df[commission_df['ENROLLED_DATE'] >= cutoff_date]
        else:
            filtered_commission = commission_df
    else:
        filtered_commission = commission_df
    
    if filtered_commission.empty:
        st.warning("No commission data available for selected time range")
        return
    
    # Payment metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_payments = len(filtered_commission)
        st.metric("Total Payments", total_payments)
    
    with col2:
        if 'STATUS' in filtered_commission.columns:
            cleared_payments = len(filtered_commission[filtered_commission['STATUS'].str.contains('Cleared', na=False)])
            st.metric("Cleared Payments", cleared_payments)
    
    with col3:
        if 'STATUS' in filtered_commission.columns:
            pending_payments = len(filtered_commission[~filtered_commission['STATUS'].str.contains('Cleared', na=False)])
            st.metric("Pending Payments", pending_payments)
    
    with col4:
        unique_agents = filtered_commission['AGENT'].nunique() if 'AGENT' in filtered_commission.columns else 0
        st.metric("Active Agents", unique_agents)
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Payment Volume by Agent")
        if 'AGENT' in filtered_commission.columns:
            agent_payments = filtered_commission['AGENT'].value_counts().head(10)
            
            fig = px.bar(
                x=agent_payments.index,
                y=agent_payments.values,
                title="Top 10 Agents by Payment Volume",
                color=agent_payments.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Payment Success Rate")
        if 'AGENT' in filtered_commission.columns and 'STATUS' in filtered_commission.columns:
            agent_success = filtered_commission.groupby('AGENT').agg({
                'AGENT': 'count',
                'STATUS': lambda x: x.str.contains('Cleared', na=False).sum()
            }).rename(columns={'AGENT': 'Total', 'STATUS': 'Cleared'})
            
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
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Payment Trends")
        if 'ENROLLED_DATE' in filtered_commission.columns:
            monthly_payments = filtered_commission.groupby(filtered_commission['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
            monthly_payments.columns = ['Month', 'Payments']
            
            fig = px.line(
                monthly_payments,
                x='Month',
                y='Payments',
                title=f"Payment Trends - {selected_range}",
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Payment Status Breakdown")
        if 'STATUS' in filtered_commission.columns:
            status_breakdown = filtered_commission['STATUS'].value_counts()
            
            fig = px.pie(
                values=status_breakdown.values,
                names=status_breakdown.index,
                title="Payment Status Distribution",
                color_discrete_sequence=HEAT_COLORS
            )
            st.plotly_chart(fig, use_container_width=True)

def render_performance_metrics(sales_df, commission_df, COLORS, HEAT_COLORS):
    """Comprehensive performance metrics combining sales and commission data"""
    st.subheader("🎯 Comprehensive Performance Metrics")
    
    # Combined performance analysis
    if not sales_df.empty and not commission_df.empty:
        # Merge sales and commission data by agent
        sales_summary = sales_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': lambda x: (x == 'ACTIVE').sum() if 'CATEGORY' in sales_df.columns else 0
        }).rename(columns={'AGENT': 'Total_Sales', 'CATEGORY': 'Active_Sales'})
        
        commission_summary = commission_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'STATUS': lambda x: x.str.contains('Cleared', na=False).sum() if 'STATUS' in commission_df.columns else 0
        }).rename(columns={'AGENT': 'Total_Payments', 'STATUS': 'Cleared_Payments'})
        
        # Combine data
        combined_performance = sales_summary.join(commission_summary, how='outer').fillna(0)
        combined_performance['Sales_Retention_Rate'] = (combined_performance['Active_Sales'] / combined_performance['Total_Sales'] * 100).round(1)
        combined_performance['Payment_Success_Rate'] = (combined_performance['Cleared_Payments'] / combined_performance['Total_Payments'] * 100).round(1)
        combined_performance['Overall_Score'] = (combined_performance['Sales_Retention_Rate'] * 0.6 + combined_performance['Payment_Success_Rate'] * 0.4).round(1)
        
        # Filter qualified agents
        qualified_agents = combined_performance[
            (combined_performance['Total_Sales'] >= 3) | (combined_performance['Total_Payments'] >= 3)
        ].sort_values('Overall_Score', ascending=False)
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_retention = qualified_agents['Sales_Retention_Rate'].mean()
            st.metric("Avg Sales Retention", f"{avg_retention:.1f}%")
        
        with col2:
            avg_payment_success = qualified_agents['Payment_Success_Rate'].mean()
            st.metric("Avg Payment Success", f"{avg_payment_success:.1f}%")
        
        with col3:
            top_performer_score = qualified_agents['Overall_Score'].max()
            st.metric("Top Performance Score", f"{top_performer_score:.1f}")
        
        with col4:
            total_qualified = len(qualified_agents)
            st.metric("Qualified Agents", total_qualified)
        
        # Performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Overall Performance Ranking")
            top_performers = qualified_agents.head(10)
            
            fig = px.bar(
                top_performers,
                x=top_performers.index,
                y='Overall_Score',
                title="Top 10 Overall Performance",
                color='Overall_Score',
                color_continuous_scale=HEAT_COLORS,
                hover_data=['Sales_Retention_Rate', 'Payment_Success_Rate']
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Sales vs Payment Performance")
            
            fig = px.scatter(
                qualified_agents,
                x='Sales_Retention_Rate',
                y='Payment_Success_Rate',
                size='Overall_Score',
                color='Overall_Score',
                title="Sales Retention vs Payment Success",
                color_continuous_scale=HEAT_COLORS,
                hover_name=qualified_agents.index
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance table
        st.subheader("📋 Comprehensive Performance Table")
        display_performance = qualified_agents.reset_index()
        st.dataframe(display_performance, use_container_width=True, hide_index=True)
        
        # Download option
        csv = display_performance.to_csv(index=False)
        st.download_button(
            "📥 Download Performance Data",
            csv,
            "agent_performance_analysis.csv",
            "text/csv"
        )
    
    else:
        st.warning("Insufficient data for comprehensive performance analysis")