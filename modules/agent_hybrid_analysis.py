"""
Complete Hybrid Agent Analysis Module - Sales + Commission Data
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_agent_hybrid_analysis(df, COLORS, HEAT_COLORS):
    """Complete hybrid agent analysis combining sales and commission data"""
    st.header("👥 Agent Performance Analysis")
    
    # Separate sales and commission data
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    
    if sales_df.empty:
        st.warning("No sales data available")
        return
    
    # Agent selector - RADIO BUTTONS (WORKING)
    if 'AGENT' in sales_df.columns:
        agents_list = sorted(sales_df['AGENT'].dropna().unique().tolist())
        
        # Show top 10 agents as radio buttons
        top_agents = sales_df['AGENT'].value_counts().head(10).index.tolist()
        agent_options = ['All Agents'] + top_agents
        
        selected_agent = st.radio(
            "👤 Select Agent for Analysis:",
            agent_options,
            index=0,
            horizontal=True,
            key="agent_hybrid_radio"
        )
        
        if selected_agent == 'All Agents':
            agent_sales = sales_df
            agent_commission = commission_df
        else:
            agent_sales = sales_df[sales_df['AGENT'] == selected_agent]
            agent_commission = commission_df[commission_df['AGENT'] == selected_agent] if not commission_df.empty else pd.DataFrame()
    else:
        st.warning("No agent data available")
        return
    
    # Agent subtabs
    subtabs = st.tabs(["💰 Performance Overview", "📈 Sales Analysis", "💳 Commission Analysis"])
    
    with subtabs[0]:
        render_performance_overview(agent_sales, agent_commission, selected_agent, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_sales_analysis(agent_sales, selected_agent, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        render_commission_analysis(agent_commission, selected_agent, COLORS, HEAT_COLORS)

def render_performance_overview(agent_sales, agent_commission, selected_agent, COLORS, HEAT_COLORS):
    """Combined performance overview"""
    st.subheader(f"💰 Performance Overview - {selected_agent}")
    
    # Combined metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", len(agent_sales))
    
    with col2:
        if 'CATEGORY' in agent_sales.columns:
            active_count = len(agent_sales[agent_sales['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_count / len(agent_sales) * 100) if len(agent_sales) > 0 else 0
            st.metric("Active Rate", f"{active_rate:.1f}%")
    
    with col3:
        commission_count = len(agent_commission) if not agent_commission.empty else 0
        st.metric("Commission Payments", commission_count)
    
    with col4:
        if not agent_commission.empty and 'CATEGORY' in agent_commission.columns:
            cleared_count = len(agent_commission[agent_commission['CATEGORY'] == 'CLEARED'])
            success_rate = (cleared_count / len(agent_commission) * 100) if len(agent_commission) > 0 else 0
            st.metric("Payment Success", f"{success_rate:.1f}%")
    
    # Combined charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales Performance")
        if 'CATEGORY' in agent_sales.columns:
            sales_status = agent_sales['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=sales_status.values,
                names=sales_status.index,
                title=f"Sales Status - {selected_agent}",
                color_discrete_map={
                    'ACTIVE': COLORS['success'],
                    'CANCELLED': COLORS['danger'],
                    'NSF': COLORS['warning'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Commission Performance")
        if not agent_commission.empty and 'CATEGORY' in agent_commission.columns:
            commission_status = agent_commission['CATEGORY'].value_counts()
            
            fig = px.bar(
                x=commission_status.index,
                y=commission_status.values,
                title=f"Commission Status - {selected_agent}",
                color=commission_status.values,
                color_continuous_scale=HEAT_COLORS,
                color_discrete_map={
                    'CLEARED': COLORS['success'],
                    'PENDING': COLORS['warning'],
                    'NSF': COLORS['danger']
                }
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No commission data available")
    
    # Combined performance table
    st.subheader("📋 Combined Performance Summary")
    if selected_agent == 'All Agents':
        # All agents summary
        if 'AGENT' in agent_sales.columns and 'CATEGORY' in agent_sales.columns:
            sales_summary = agent_sales.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': [
                    lambda x: (x == 'ACTIVE').sum(),
                    lambda x: (x == 'CANCELLED').sum(),
                    lambda x: (x == 'NSF').sum()
                ]
            })
            
            sales_summary.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
            sales_summary['Active_Rate'] = (sales_summary['Active_Sales'] / sales_summary['Total_Sales'] * 100).round(1)
            
            # Add commission data if available
            if not agent_commission.empty and 'AGENT' in agent_commission.columns:
                commission_summary = agent_commission.groupby('AGENT').agg({
                    'AGENT': 'count',
                    'CATEGORY': lambda x: (x == 'CLEARED').sum() if 'CATEGORY' in agent_commission.columns else 0
                }).rename(columns={'AGENT': 'Total_Payments', 'CATEGORY': 'Cleared_Payments'})
                
                combined_summary = sales_summary.join(commission_summary, how='left').fillna(0)
                combined_summary['Payment_Success_Rate'] = (combined_summary['Cleared_Payments'] / combined_summary['Total_Payments'] * 100).round(1)
                combined_summary['Overall_Score'] = (combined_summary['Active_Rate'] * 0.6 + combined_summary['Payment_Success_Rate'] * 0.4).round(1)
            else:
                combined_summary = sales_summary
            
            combined_summary = combined_summary.sort_values('Active_Rate', ascending=False).reset_index()
            st.dataframe(combined_summary, use_container_width=True, hide_index=True)
    else:
        # Individual agent summary
        summary_data = {
            'Metric': ['Total Sales', 'Active Sales', 'Cancelled Sales', 'NSF Sales', 'Commission Payments'],
            'Count': [
                len(agent_sales),
                len(agent_sales[agent_sales['CATEGORY'] == 'ACTIVE']) if 'CATEGORY' in agent_sales.columns else 0,
                len(agent_sales[agent_sales['CATEGORY'] == 'CANCELLED']) if 'CATEGORY' in agent_sales.columns else 0,
                len(agent_sales[agent_sales['CATEGORY'] == 'NSF']) if 'CATEGORY' in agent_sales.columns else 0,
                len(agent_commission) if not agent_commission.empty else 0
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

def render_sales_analysis(agent_sales, selected_agent, COLORS, HEAT_COLORS):
    """Detailed sales analysis"""
    st.subheader(f"📈 Sales Analysis - {selected_agent}")
    
    if agent_sales.empty:
        st.warning("No sales data available")
        return
    
    # Sales metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", len(agent_sales))
    
    with col2:
        if 'CATEGORY' in agent_sales.columns:
            active_count = len(agent_sales[agent_sales['CATEGORY'] == 'ACTIVE'])
            st.metric("Active Sales", active_count)
    
    with col3:
        if 'CATEGORY' in agent_sales.columns:
            cancelled_count = len(agent_sales[agent_sales['CATEGORY'] == 'CANCELLED'])
            st.metric("Cancelled Sales", cancelled_count)
    
    with col4:
        if 'CATEGORY' in agent_sales.columns:
            nsf_count = len(agent_sales[agent_sales['CATEGORY'] == 'NSF'])
            st.metric("NSF Sales", nsf_count)
    
    # Sales charts
    col1, col2 = st.columns(2)
    
    with col1:
        if 'SOURCE_SHEET' in agent_sales.columns and 'CATEGORY' in agent_sales.columns:
            st.subheader("Sales by Source")
            source_breakdown = agent_sales.groupby(['SOURCE_SHEET', 'CATEGORY']).size().unstack(fill_value=0)
            
            if not source_breakdown.empty:
                fig = px.bar(
                    source_breakdown,
                    title="Sales Breakdown by Source",
                    color_discrete_map={
                        'ACTIVE': COLORS['success'],
                        'CANCELLED': COLORS['danger'],
                        'NSF': COLORS['warning'],
                        'OTHER': COLORS['info']
                    }
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'ENROLLED_DATE' in agent_sales.columns:
            st.subheader("Monthly Sales Trend")
            monthly_sales = agent_sales.groupby(agent_sales['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
            monthly_sales.columns = ['Month', 'Sales']
            
            if not monthly_sales.empty:
                fig = px.line(
                    monthly_sales,
                    x='Month',
                    y='Sales',
                    title="Monthly Sales Trend",
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Detailed sales data
    with st.expander("📋 Detailed Sales Data"):
        display_cols = ['ENROLLED_DATE', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in agent_sales.columns]
        
        if available_cols:
            display_df = agent_sales[available_cols].copy()
            if 'ENROLLED_DATE' in display_df.columns:
                display_df['ENROLLED_DATE'] = display_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                f"📥 Download Sales Data - {selected_agent}",
                csv,
                f"sales_data_{selected_agent.lower().replace(' ', '_')}.csv",
                "text/csv"
            )

def render_commission_analysis(agent_commission, selected_agent, COLORS, HEAT_COLORS):
    """Detailed commission analysis"""
    st.subheader(f"💳 Commission Analysis - {selected_agent}")
    
    if agent_commission.empty:
        st.warning("No commission data available")
        return
    
    # Commission metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Payments", len(agent_commission))
    
    with col2:
        if 'CATEGORY' in agent_commission.columns:
            cleared_count = len(agent_commission[agent_commission['CATEGORY'] == 'CLEARED'])
            st.metric("Cleared Payments", cleared_count)
    
    with col3:
        if 'CATEGORY' in agent_commission.columns:
            pending_count = len(agent_commission[agent_commission['CATEGORY'] == 'PENDING'])
            st.metric("Pending Payments", pending_count)
    
    with col4:
        if 'CATEGORY' in agent_commission.columns:
            nsf_count = len(agent_commission[agent_commission['CATEGORY'] == 'NSF'])
            st.metric("NSF Payments", nsf_count)
    
    # Commission charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Payment Status Distribution")
        if 'CATEGORY' in agent_commission.columns:
            payment_status = agent_commission['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=payment_status.values,
                names=payment_status.index,
                title="Payment Status Distribution",
                color_discrete_map={
                    'CLEARED': COLORS['success'],
                    'PENDING': COLORS['warning'],
                    'NSF': COLORS['danger'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'PROCESSED_DATE' in agent_commission.columns:
            st.subheader("Monthly Payment Trend")
            monthly_payments = agent_commission.groupby(agent_commission['PROCESSED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
            monthly_payments.columns = ['Month', 'Payments']
            
            if not monthly_payments.empty:
                fig = px.line(
                    monthly_payments,
                    x='Month',
                    y='Payments',
                    title="Monthly Payment Trend",
                    markers=True,
                    color_discrete_sequence=[COLORS['secondary']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Detailed commission data
    with st.expander("📋 Detailed Commission Data"):
        display_cols = ['PROCESSED_DATE', 'CLEARED_DATE', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in agent_commission.columns]
        
        if available_cols:
            display_df = agent_commission[available_cols].copy()
            
            # Format dates
            for date_col in ['PROCESSED_DATE', 'CLEARED_DATE']:
                if date_col in display_df.columns:
                    display_df[date_col] = display_df[date_col].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                f"📥 Download Commission Data - {selected_agent}",
                csv,
                f"commission_data_{selected_agent.lower().replace(' ', '_')}.csv",
                "text/csv"
            )