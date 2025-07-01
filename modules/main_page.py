"""
Main Page Module - Weekly Sales Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_main_page(df, COLORS, PURPLE_SCALES):
    """Render the main dashboard page with weekly sales focus"""
    
    # Filter out commission data for sales analysis
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else df.copy()
    
    if sales_df.empty or 'ENROLLED_DATE' not in sales_df.columns:
        st.warning("No sales data available with enrollment dates")
        return
    
    # Prepare weekly data
    sales_df = sales_df[sales_df['ENROLLED_DATE'].notna()].copy()
    sales_df['Week'] = sales_df['ENROLLED_DATE'].dt.to_period('W').dt.start_time
    sales_df['Week_Label'] = sales_df['Week'].dt.strftime('%b %d, %Y')
    
    # Get unique weeks sorted (most recent first)
    weeks = sorted(sales_df['Week'].unique(), reverse=True)
    week_labels = [w.strftime('%b %d, %Y') for w in weeks]
    
    if not weeks:
        st.warning("No weekly data available")
        return
    
    # Week selector with bigger styling
    st.markdown("### 📊 Weekly Sales Dashboard")
    selected_week_label = st.selectbox(
        "Select Week (Most Recent First):", 
        week_labels,
        key="week_selector"
    )
    
    # Get selected week data
    selected_week = weeks[week_labels.index(selected_week_label)]
    week_data = sales_df[sales_df['Week'] == selected_week].copy()
    
    # Weekly metrics
    st.markdown(f"#### Week of {selected_week_label}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sales = len(week_data)
        st.metric("📈 Total Sales", total_sales, delta=None)
    
    with col2:
        if 'CATEGORY' in week_data.columns:
            active_sales = len(week_data[week_data['CATEGORY'] == 'ACTIVE'])
            active_rate = (active_sales / total_sales * 100) if total_sales > 0 else 0
            st.metric("✅ Active Sales", f"{active_sales} ({active_rate:.1f}%)")
    
    with col3:
        if 'CATEGORY' in week_data.columns:
            cancelled_sales = len(week_data[week_data['CATEGORY'] == 'CANCELLED'])
            cancel_rate = (cancelled_sales / total_sales * 100) if total_sales > 0 else 0
            st.metric("❌ Cancelled", f"{cancelled_sales} ({cancel_rate:.1f}%)")
    
    with col4:
        if 'AGENT' in week_data.columns:
            unique_agents = week_data['AGENT'].nunique()
            st.metric("👥 Active Agents", unique_agents)
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        # Sales by source (excluding commission)
        if 'SOURCE_SHEET' in week_data.columns:
            st.subheader("🏢 Sales by Source")
            source_counts = week_data['SOURCE_SHEET'].value_counts()
            
            if not source_counts.empty:
                fig = px.bar(
                    x=source_counts.index, 
                    y=source_counts.values,
                    title=f"Sales Distribution - Week of {selected_week_label}",
                    color=source_counts.values,
                    color_continuous_scale=PURPLE_SCALES['sequential'],
                    text=source_counts.values
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    xaxis_title="Source",
                    yaxis_title="Number of Sales",
                    showlegend=False,
                    font=dict(size=14)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No source data available for this week")
    
    with col2:
        # Top agents for the week
        if 'AGENT' in week_data.columns:
            st.subheader("🏆 Top Agents This Week")
            agent_counts = week_data['AGENT'].value_counts().head(10)
            
            if not agent_counts.empty:
                fig = px.bar(
                    x=agent_counts.values,
                    y=agent_counts.index,
                    orientation='h',
                    title=f"Top Performers - Week of {selected_week_label}",
                    color=agent_counts.values,
                    color_continuous_scale=PURPLE_SCALES['sequential'],
                    text=agent_counts.values
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    xaxis_title="Number of Sales",
                    yaxis_title="Agent",
                    showlegend=False,
                    font=dict(size=14),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No agent data available for this week")
    
    # Weekly trend comparison
    st.subheader("📈 Weekly Trend Analysis")
    
    # Get last 8 weeks for trend
    recent_weeks = weeks[:8] if len(weeks) >= 8 else weeks
    trend_data = []
    
    for week in recent_weeks:
        week_df = sales_df[sales_df['Week'] == week]
        trend_data.append({
            'Week': week.strftime('%b %d'),
            'Total_Sales': len(week_df),
            'Active_Sales': len(week_df[week_df['CATEGORY'] == 'ACTIVE']) if 'CATEGORY' in week_df.columns else 0,
            'Week_Date': week
        })
    
    trend_df = pd.DataFrame(trend_data).sort_values('Week_Date')
    
    if not trend_df.empty:
        fig = go.Figure()
        
        # Add total sales line
        fig.add_trace(go.Scatter(
            x=trend_df['Week'],
            y=trend_df['Total_Sales'],
            mode='lines+markers',
            name='Total Sales',
            line=dict(color=COLORS['primary'], width=3),
            marker=dict(size=8)
        ))
        
        # Add active sales line
        fig.add_trace(go.Scatter(
            x=trend_df['Week'],
            y=trend_df['Active_Sales'],
            mode='lines+markers',
            name='Active Sales',
            line=dict(color=COLORS['med_green'], width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="8-Week Sales Trend",
            xaxis_title="Week",
            yaxis_title="Number of Sales",
            font=dict(size=14),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed weekly data table
    with st.expander("📋 Detailed Weekly Data", expanded=False):
        if not week_data.empty:
            # Select relevant columns for display
            display_cols = []
            for col in ['ENROLLED_DATE', 'AGENT', 'SOURCE_SHEET', 'STATUS', 'CATEGORY']:
                if col in week_data.columns:
                    display_cols.append(col)
            
            if display_cols:
                display_df = week_data[display_cols].copy()
                
                # Format date
                if 'ENROLLED_DATE' in display_df.columns:
                    display_df['ENROLLED_DATE'] = display_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Download button
                csv = display_df.to_csv(index=False)
                st.download_button(
                    f"📥 Download Week Data ({selected_week_label})",
                    csv,
                    f"sales_week_{selected_week.strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                st.info("No displayable columns available")
        else:
            st.info("No data available for the selected week")