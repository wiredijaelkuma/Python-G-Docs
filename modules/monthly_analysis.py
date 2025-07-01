"""
Monthly Analysis Module
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_monthly_analysis(df, COLORS, PURPLE_SCALES):
    """Render monthly analysis dashboard"""
    
    # Filter out commission data
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else df.copy()
    
    if sales_df.empty or 'ENROLLED_DATE' not in sales_df.columns:
        st.warning("No sales data available with enrollment dates")
        return
    
    # Prepare monthly data
    sales_df = sales_df[sales_df['ENROLLED_DATE'].notna()].copy()
    sales_df['Month'] = sales_df['ENROLLED_DATE'].dt.to_period('M')
    sales_df['Month_Label'] = sales_df['Month'].dt.strftime('%B %Y')
    
    # Get unique months sorted (most recent first)
    months = sorted(sales_df['Month'].unique(), reverse=True)
    month_labels = [m.strftime('%B %Y') for m in months]
    
    if not months:
        st.warning("No monthly data available")
        return
    
    st.markdown("### 📅 Monthly Sales Analysis")
    
    # Month selector
    selected_month_label = st.selectbox(
        "Select Month (Most Recent First):", 
        month_labels,
        key="month_selector"
    )
    
    selected_month = months[month_labels.index(selected_month_label)]
    month_data = sales_df[sales_df['Month'] == selected_month].copy()
    
    # Monthly metrics
    st.markdown(f"#### {selected_month_label} Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_monthly = len(month_data)
        st.metric("📊 Total Sales", total_monthly)
    
    with col2:
        if 'CATEGORY' in month_data.columns:
            active_monthly = len(month_data[month_data['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_monthly / total_monthly * 100) if total_monthly > 0 else 0
            st.metric("✅ Active Rate", f"{active_rate:.1f}%")
    
    with col3:
        if 'AGENT' in month_data.columns:
            avg_per_agent = total_monthly / month_data['AGENT'].nunique() if month_data['AGENT'].nunique() > 0 else 0
            st.metric("👤 Avg per Agent", f"{avg_per_agent:.1f}")
    
    with col4:
        # Calculate weekly average for the month
        weeks_in_month = len(month_data.groupby(month_data['ENROLLED_DATE'].dt.isocalendar().week))
        weekly_avg = total_monthly / weeks_in_month if weeks_in_month > 0 else 0
        st.metric("📈 Weekly Average", f"{weekly_avg:.1f}")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily sales trend for the month
        st.subheader("📈 Daily Sales Trend")
        daily_sales = month_data.groupby(month_data['ENROLLED_DATE'].dt.date).size().reset_index()
        daily_sales.columns = ['Date', 'Sales']
        
        if not daily_sales.empty:
            fig = px.line(
                daily_sales,
                x='Date',
                y='Sales',
                title=f"Daily Sales - {selected_month_label}",
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(font=dict(size=12))
            st.plotly_chart(fig, use_container_width=True, key=f"daily_trend_{selected_month.strftime('%Y%m')}")
    
    with col2:
        # Weekly breakdown within the month
        st.subheader("📊 Weekly Breakdown")
        month_data['Week_of_Month'] = month_data['ENROLLED_DATE'].dt.isocalendar().week
        weekly_breakdown = month_data.groupby('Week_of_Month').size().reset_index()
        weekly_breakdown.columns = ['Week', 'Sales']
        weekly_breakdown['Week'] = 'Week ' + weekly_breakdown['Week'].astype(str)
        
        if not weekly_breakdown.empty:
            fig = px.bar(
                weekly_breakdown,
                x='Week',
                y='Sales',
                title=f"Weekly Distribution - {selected_month_label}",
                color_discrete_sequence=[COLORS['secondary']],
                text='Sales'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(font=dict(size=12))
            st.plotly_chart(fig, use_container_width=True, key=f"weekly_breakdown_{selected_month.strftime('%Y%m')}")
    
    # Month-over-month comparison
    st.subheader("📊 Month-over-Month Comparison")
    
    # Get last 6 months for comparison
    recent_months = months[:6] if len(months) >= 6 else months
    comparison_data = []
    
    for month in recent_months:
        month_df = sales_df[sales_df['Month'] == month]
        comparison_data.append({
            'Month': month.strftime('%b %Y'),
            'Total_Sales': len(month_df),
            'Active_Sales': len(month_df[month_df['CATEGORY'] == 'ACTIVE']) if 'CATEGORY' in month_df.columns else 0,
            'Active_Rate': (len(month_df[month_df['CATEGORY'] == 'ACTIVE']) / len(month_df) * 100) if len(month_df) > 0 and 'CATEGORY' in month_df.columns else 0,
            'Month_Date': month.start_time
        })
    
    comparison_df = pd.DataFrame(comparison_data).sort_values('Month_Date')
    
    if not comparison_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Total sales comparison
            fig = px.bar(
                comparison_df,
                x='Month',
                y='Total_Sales',
                title="6-Month Sales Volume",
                color='Total_Sales',
                color_continuous_scale=PURPLE_SCALES['sequential'],
                text='Total_Sales'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(font=dict(size=12))
            st.plotly_chart(fig, use_container_width=True, key=f"volume_comparison_{datetime.now().strftime('%Y%m%d')}")
        
        with col2:
            # Active rate comparison
            fig = px.line(
                comparison_df,
                x='Month',
                y='Active_Rate',
                title="6-Month Active Rate Trend",
                markers=True,
                color_discrete_sequence=[COLORS['med_green']]
            )
            fig.update_layout(
                yaxis_title="Active Rate (%)",
                font=dict(size=12)
            )
            st.plotly_chart(fig, use_container_width=True, key=f"active_rate_trend_{datetime.now().strftime('%Y%m%d')}")
    
    # Top performers for the month
    st.subheader("🏆 Monthly Top Performers")
    
    if 'AGENT' in month_data.columns:
        monthly_agents = month_data.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': lambda x: (x == 'ACTIVE').sum() if 'CATEGORY' in month_data.columns else 0
        }).rename(columns={'AGENT': 'Total_Sales', 'CATEGORY': 'Active_Sales'})
        
        if 'CATEGORY' in month_data.columns:
            monthly_agents['Cancelled_Sales'] = month_data.groupby('AGENT')['CATEGORY'].apply(lambda x: (x == 'CANCELLED').sum())
            monthly_agents['Active_Rate'] = (monthly_agents['Active_Sales'] / monthly_agents['Total_Sales'] * 100).round(1)
        
        # Sort by ACTIVE sales for ranking (not total)
        monthly_agents = monthly_agents.sort_values('Active_Sales', ascending=False).head(10).reset_index()
        
        # Display as chart and table
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig = px.bar(
                monthly_agents.head(5),
                x='AGENT',
                y='Active_Sales',
                title="Top 5 Agents by Volume",
                color_discrete_sequence=[COLORS['primary']],
                text='Active_Sales'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                xaxis_title="Agent",
                yaxis_title="Active Sales",
                font=dict(size=12)
            )
            st.plotly_chart(fig, use_container_width=True, key=f"top_agents_{selected_month.strftime('%Y%m')}")
        
        with col2:
            st.markdown("**Monthly Leaderboard**")
            st.dataframe(
                monthly_agents[['AGENT', 'Total_Sales', 'Active_Sales', 'Active_Rate']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "AGENT": "Agent",
                    "Total_Sales": "Total",
                    "Active_Sales": "Active",
                    "Active_Rate": "Rate (%)"
                }
            )
    
    # Download section
    with st.expander("📥 Download Monthly Data"):
        if not month_data.empty:
            display_cols = []
            for col in ['ENROLLED_DATE', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']:
                if col in month_data.columns:
                    display_cols.append(col)
            
            if display_cols:
                download_df = month_data[display_cols].copy()
                if 'ENROLLED_DATE' in download_df.columns:
                    download_df['ENROLLED_DATE'] = download_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
                
                csv = download_df.to_csv(index=False)
                st.download_button(
                    f"📥 Download {selected_month_label} Data",
                    csv,
                    f"monthly_sales_{selected_month.strftime('%Y_%m')}.csv",
                    "text/csv",
                    use_container_width=True
                )