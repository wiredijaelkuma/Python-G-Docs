"""
Monthly Dashboard Module
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_monthly_dashboard(sales_df, COLORS, HEAT_COLORS):
    """Render monthly analysis dashboard"""
    st.subheader("📆 Monthly Analysis")
    
    # Month selection
    sales_df['Month'] = sales_df['ENROLLED_DATE'].dt.to_period('M')
    available_months = sorted(sales_df['Month'].unique(), reverse=True)
    
    if not available_months:
        st.warning("No monthly data available")
        return
    
    selected_month_date = st.date_input(
        "Select Any Date in Month:",
        value=available_months[0].start_time.date(),
        min_value=available_months[-1].start_time.date(),
        max_value=available_months[0].start_time.date(),
        key="monthly_date_picker"
    )
    
    selected_month = pd.Timestamp(selected_month_date).to_period('M')
    selected_month_str = selected_month.strftime('%B %Y')
    
    # Filter data for selected month
    month_data = sales_df[sales_df['Month'] == selected_month].copy()
    
    if month_data.empty:
        st.warning("No data for selected month")
        return
    
    # Monthly metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sales", len(month_data))
    
    with col2:
        if 'CATEGORY' in month_data.columns:
            active_count = len(month_data[month_data['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_count / len(month_data) * 100) if len(month_data) > 0 else 0
            st.metric("Active Rate", f"{active_rate:.1f}%")
    
    with col3:
        if 'AGENT' in month_data.columns:
            avg_per_agent = len(month_data) / month_data['AGENT'].nunique() if month_data['AGENT'].nunique() > 0 else 0
            st.metric("Avg per Agent", f"{avg_per_agent:.1f}")
    
    with col4:
        weeks_in_month = len(month_data.groupby(month_data['ENROLLED_DATE'].dt.isocalendar().week))
        weekly_avg = len(month_data) / weeks_in_month if weeks_in_month > 0 else 0
        st.metric("Weekly Average", f"{weekly_avg:.1f}")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Daily Trend")
        daily_sales = month_data.groupby(month_data['ENROLLED_DATE'].dt.date).size().reset_index()
        daily_sales.columns = ['Date', 'Sales']
        
        if not daily_sales.empty:
            fig = px.line(
                daily_sales,
                x='Date',
                y='Sales',
                title=f"Daily Sales - {selected_month_str}",
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'AGENT' in month_data.columns:
            st.subheader("Top Monthly Performers")
            if 'CATEGORY' in month_data.columns:
                monthly_agents = month_data[month_data['CATEGORY'] == 'ACTIVE']['AGENT'].value_counts().head(10)
            else:
                monthly_agents = month_data['AGENT'].value_counts().head(10)
            
            if not monthly_agents.empty:
                fig = px.bar(
                    monthly_agents.head(5),
                    x=monthly_agents.head(5).index,
                    y=monthly_agents.head(5).values,
                    title="Top 5 Agents (Active Sales)",
                    color=monthly_agents.head(5).values,
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weekly Breakdown")
        month_data['Week_of_Month'] = month_data['ENROLLED_DATE'].dt.isocalendar().week
        weekly_breakdown = month_data.groupby('Week_of_Month').size().reset_index()
        weekly_breakdown.columns = ['Week', 'Sales']
        weekly_breakdown['Week'] = 'Week ' + weekly_breakdown['Week'].astype(str)
        
        if not weekly_breakdown.empty:
            fig = px.bar(
                weekly_breakdown,
                x='Week',
                y='Sales',
                title=f"Weekly Distribution - {selected_month_str}",
                color='Sales',
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'SOURCE_SHEET' in month_data.columns and 'CATEGORY' in month_data.columns:
            st.subheader("Source Performance")
            source_breakdown = month_data.groupby(['SOURCE_SHEET', 'CATEGORY']).size().unstack(fill_value=0)
            
            if not source_breakdown.empty:
                fig = px.bar(
                    source_breakdown,
                    title=f"Source Breakdown - {selected_month_str}",
                    color_discrete_map={
                        'ACTIVE': COLORS['success'],
                        'CANCELLED': COLORS['danger'],
                        'NSF': COLORS['warning'],
                        'OTHER': COLORS['info']
                    }
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Monthly Agent Performance Table
    st.subheader("📋 Monthly Agent Performance")
    if 'AGENT' in month_data.columns and 'CATEGORY' in month_data.columns:
        monthly_agent_summary = month_data.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        monthly_agent_summary.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
        monthly_agent_summary['Active_Rate'] = (monthly_agent_summary['Active_Sales'] / monthly_agent_summary['Total_Sales'] * 100).round(1)
        monthly_agent_summary = monthly_agent_summary.sort_values('Active_Sales', ascending=False).reset_index()
        
        st.dataframe(monthly_agent_summary, use_container_width=True, hide_index=True)
    
    # Detailed Monthly Data
    with st.expander("📋 Detailed Monthly Data"):
        display_cols = ['ENROLLED_DATE', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']
        available_cols = [col for col in display_cols if col in month_data.columns]
        
        if available_cols:
            display_df = month_data[available_cols].copy()
            if 'ENROLLED_DATE' in display_df.columns:
                display_df['ENROLLED_DATE'] = display_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv = display_df.to_csv(index=False)
            st.download_button(
                f"📥 Download Monthly Data",
                csv,
                f"monthly_data_{selected_month.strftime('%Y_%m')}.csv",
                "text/csv"
            )