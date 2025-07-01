"""
Fixed Hybrid Agent Analysis Module - Unique Keys for All Charts
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_agent_hybrid_analysis(df, COLORS, HEAT_COLORS):
    """Complete hybrid agent analysis with unique chart keys"""
    st.header("👥 Agent Performance Analysis")
    
    # Separate sales and commission data
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    
    if sales_df.empty:
        st.warning("No sales data available")
        return
    
    # Agent selector - RADIO BUTTONS (WORKING)
    if 'AGENT' in sales_df.columns:
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
        render_performance_overview_enhanced(agent_sales, agent_commission, selected_agent, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_sales_analysis_enhanced(agent_sales, selected_agent, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        render_commission_analysis_enhanced(agent_commission, selected_agent, COLORS, HEAT_COLORS)

def render_performance_overview_enhanced(agent_sales, agent_commission, selected_agent, COLORS, HEAT_COLORS):
    """Performance overview with 6 displays"""
    st.subheader(f"💰 Performance Overview - {selected_agent}")
    
    # Display 1: Combined metrics
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
    
    # Display 2 & 3: Performance charts
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
            st.plotly_chart(fig, use_container_width=True, key="perf_sales_pie")
    
    with col2:
        st.subheader("Commission Performance")
        if not agent_commission.empty and 'CATEGORY' in agent_commission.columns:
            commission_status = agent_commission['CATEGORY'].value_counts()
            
            fig = px.bar(
                x=commission_status.index,
                y=commission_status.values,
                title=f"Commission Status - {selected_agent}",
                color=commission_status.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key="perf_commission_bar")
        else:
            st.info("No commission data available")
    
    # Display 4 & 5: Additional analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance Trends")
        if 'ENROLLED_DATE' in agent_sales.columns:
            monthly_trend = agent_sales.groupby(agent_sales['ENROLLED_DATE'].dt.strftime('%Y-%m')).size().reset_index()
            monthly_trend.columns = ['Month', 'Sales']
            
            if not monthly_trend.empty:
                fig = px.line(
                    monthly_trend,
                    x='Month',
                    y='Sales',
                    title="Monthly Sales Trend",
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="perf_monthly_trend")
    
    with col2:
        st.subheader("Source Distribution")
        if 'SOURCE_SHEET' in agent_sales.columns:
            source_dist = agent_sales['SOURCE_SHEET'].value_counts()
            
            fig = px.bar(
                x=source_dist.index,
                y=source_dist.values,
                title="Sales by Source",
                color=source_dist.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key="perf_source_dist")
    
    # Display 6: Performance summary table
    st.subheader("📋 Performance Summary")
    if selected_agent == 'All Agents':
        if 'AGENT' in agent_sales.columns and 'CATEGORY' in agent_sales.columns:
            summary = agent_sales.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'ACTIVE').sum()
            }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Active'})
            
            summary['Active_Rate'] = (summary['Active'] / summary['Total'] * 100).round(1)
            summary = summary.sort_values('Active_Rate', ascending=False).head(10).reset_index()
            
            st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        summary_data = {
            'Metric': ['Total Sales', 'Active Sales', 'Cancelled', 'NSF', 'Commission Payments'],
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

def render_sales_analysis_enhanced(agent_sales, selected_agent, COLORS, HEAT_COLORS):
    """Sales analysis with 6 displays"""
    st.subheader(f"📈 Sales Analysis - {selected_agent}")
    
    if agent_sales.empty:
        st.warning("No sales data available")
        return
    
    # Display 1: Sales metrics
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
    
    # Display 2 & 3: Primary charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Sales by Source")
        if 'SOURCE_SHEET' in agent_sales.columns and 'CATEGORY' in agent_sales.columns:
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
                st.plotly_chart(fig, use_container_width=True, key="sales_source_breakdown")
    
    with col2:
        st.subheader("Monthly Sales Trend")
        if 'ENROLLED_DATE' in agent_sales.columns:
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
                st.plotly_chart(fig, use_container_width=True, key="sales_monthly_trend")
    
    # Display 4 & 5: Additional analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status Distribution")
        if 'CATEGORY' in agent_sales.columns:
            status_counts = agent_sales['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Sales Status Distribution",
                color_discrete_map={
                    'ACTIVE': COLORS['success'],
                    'CANCELLED': COLORS['danger'],
                    'NSF': COLORS['warning'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True, key="sales_status_pie")
    
    with col2:
        st.subheader("Weekly Performance")
        if 'ENROLLED_DATE' in agent_sales.columns:
            weekly_sales = agent_sales.groupby(agent_sales['ENROLLED_DATE'].dt.to_period('W').dt.start_time).size().reset_index()
            weekly_sales.columns = ['Week', 'Sales']
            
            if not weekly_sales.empty:
                fig = px.bar(
                    weekly_sales.tail(8),  # Last 8 weeks
                    x='Week',
                    y='Sales',
                    title="Recent Weekly Performance",
                    color='Sales',
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="sales_weekly_perf")
    
    # Display 6: Detailed data table
    with st.expander("📋 Detailed Sales Data & Export"):
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

def render_commission_analysis_enhanced(agent_commission, selected_agent, COLORS, HEAT_COLORS):
    """Commission analysis with 6 displays"""
    st.subheader(f"💳 Commission Analysis - {selected_agent}")
    
    if agent_commission.empty:
        st.warning("No commission data available")
        return
    
    # Display 1: Commission metrics
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
    
    # Display 2 & 3: Primary charts
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
            st.plotly_chart(fig, use_container_width=True, key="comm_status_pie")
    
    with col2:
        st.subheader("Monthly Payment Trend")
        if 'PROCESSED_DATE' in agent_commission.columns:
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
                st.plotly_chart(fig, use_container_width=True, key="comm_monthly_trend")
    
    # Display 4 & 5: Additional analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Payment Success Rate")
        if 'CATEGORY' in agent_commission.columns:
            success_data = pd.DataFrame({
                'Status': ['Cleared', 'Pending', 'NSF'],
                'Count': [
                    len(agent_commission[agent_commission['CATEGORY'] == 'CLEARED']),
                    len(agent_commission[agent_commission['CATEGORY'] == 'PENDING']),
                    len(agent_commission[agent_commission['CATEGORY'] == 'NSF'])
                ]
            })
            
            fig = px.bar(
                success_data,
                x='Status',
                y='Count',
                title="Payment Success Analysis",
                color='Count',
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key="comm_success_bar")
    
    with col2:
        st.subheader("Weekly Payment Volume")
        if 'PROCESSED_DATE' in agent_commission.columns:
            weekly_payments = agent_commission.groupby(agent_commission['PROCESSED_DATE'].dt.to_period('W').dt.start_time).size().reset_index()
            weekly_payments.columns = ['Week', 'Payments']
            
            if not weekly_payments.empty:
                fig = px.bar(
                    weekly_payments.tail(8),
                    x='Week',
                    y='Payments',
                    title="Recent Weekly Payment Volume",
                    color='Payments',
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="comm_weekly_vol")
    
    # Display 6: Detailed commission data
    with st.expander("📋 Detailed Commission Data & Export"):
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