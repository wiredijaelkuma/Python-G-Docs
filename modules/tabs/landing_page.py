# modules/tabs/landing_page.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def render_landing_page(df, COLORS):
    """Render the landing page with weekly data and dropdown selector"""
    
    st.markdown("<h2 style='text-align: center;'>Weekly Performance Dashboard</h2>", unsafe_allow_html=True)
    
    # Process data for weekly analysis
    if 'ENROLLED_DATE' not in df.columns:
        st.warning("Enrollment date data not available")
        return
    
    if df.empty:
        st.warning("No data available for the selected filters")
        return
    
    # Filter to only show active deals
    active_df = df[df['CATEGORY'] == 'ACTIVE'] if 'CATEGORY' in df.columns else df
    
    if active_df.empty:
        st.warning("No active deals found in the selected date range")
        return
        
    # Group data by week
    active_df['Week'] = active_df['ENROLLED_DATE'].dt.strftime('%Y-%U')
    weekly_data = active_df.groupby('Week').size().reset_index()
    weekly_data.columns = ['Week', 'Count']
    
    if weekly_data.empty:
        st.warning("No weekly data available for the selected date range")
        return
    
    # Add week starting date for better display
    week_dates = []
    week_labels = []
    for week_str in weekly_data['Week']:
        year, week_num = week_str.split('-')
        # Calculate the date of the Monday of that week (start of week)
        try:
            # Use Monday (1) as the start of the week
            week_date = datetime.strptime(f'{year}-{week_num}-1', '%Y-%U-%w')
            week_dates.append(week_date)
            week_labels.append(week_date.strftime('%b %d, %Y'))
        except ValueError:
            # Handle potential date parsing errors
            week_dates.append(datetime.now())
            week_labels.append(f"Week {week_num}, {year}")
    
    weekly_data['Week_Starting'] = week_labels
    weekly_data['Week_Date'] = week_dates
    
    # Sort by date (newest first)
    weekly_data = weekly_data.sort_values('Week_Date', ascending=False).reset_index(drop=True)
    
    # Create week selector dropdown
    st.subheader("Select Week to Analyze")
    
    # Default to most recent week
    default_week_idx = 0
    selected_week_idx = st.selectbox(
        "Choose a week:", 
        range(len(weekly_data)),
        format_func=lambda i: weekly_data['Week_Starting'][i],
        index=default_week_idx
    )
    
    selected_week = weekly_data['Week'].iloc[selected_week_idx]
    selected_week_starting = weekly_data['Week_Starting'].iloc[selected_week_idx]
    
    # Filter data for selected week (active deals only)
    week_df = active_df[active_df['Week'] == selected_week]
    
    # Display metrics for selected week
    st.markdown(f"### Week Starting: {selected_week_starting}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Active Enrollments", len(week_df))
    
    # Calculate additional metrics if possible
    if 'AMOUNT' in week_df.columns:
        total_amount = week_df['AMOUNT'].sum()
        avg_amount = week_df['AMOUNT'].mean() if len(week_df) > 0 else 0
        
        with col2:
            st.metric("Total Revenue", f"${total_amount:,.2f}")
        
        with col3:
            st.metric("Avg Deal Size", f"${avg_amount:,.2f}")
    
    if 'AGENT' in week_df.columns:
        agent_count = week_df['AGENT'].nunique()
        with col4:
            st.metric("Active Agents", agent_count)
    
    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Weekly Enrollment Trend")
        # Create a line chart showing the last 8 weeks
        recent_weeks = weekly_data.head(8)[::-1]  # Reverse to show chronological order
        
        if not recent_weeks.empty:
            fig = px.line(
                recent_weeks, 
                x='Week_Starting', 
                y='Count',
                markers=True,
                labels={'Count': 'Active Enrollments', 'Week_Starting': 'Week Starting'},
                color_discrete_sequence=[COLORS['primary']]
            )
            
            # Highlight the selected week
            selected_week_in_chart = selected_week_starting in recent_weeks['Week_Starting'].values
            if selected_week_in_chart:
                idx = recent_weeks[recent_weeks['Week_Starting'] == selected_week_starting].index[0]
                fig.add_trace(go.Scatter(
                    x=[selected_week_starting],
                    y=[recent_weeks['Count'].iloc[idx]],
                    mode='markers',
                    marker=dict(color=COLORS['accent'], size=12),
                    name='Selected Week'
                ))
            
            # Add values as annotations
            for i in range(len(recent_weeks)):
                fig.add_annotation(
                    x=recent_weeks['Week_Starting'].iloc[i],
                    y=recent_weeks['Count'].iloc[i],
                    text=str(recent_weeks['Count'].iloc[i]),
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-30
                )
            
            st.plotly_chart(fig, use_container_width=True, key="weekly_trend_line")
            
            # Add a bar chart showing the same data
            fig = px.bar(
                recent_weeks,
                x='Week_Starting',
                y='Count',
                title='Weekly Active Enrollments',
                color_discrete_sequence=[COLORS['primary']]
            )
            
            # Highlight the selected week
            if selected_week_in_chart:
                idx = recent_weeks[recent_weeks['Week_Starting'] == selected_week_starting].index[0]
                fig.add_trace(go.Bar(
                    x=[selected_week_starting],
                    y=[recent_weeks['Count'].iloc[idx]],
                    marker=dict(color=COLORS['accent']),
                    name='Selected Week'
                ))
            
            # Use the full container width for the chart
            st.plotly_chart(fig, use_container_width=True, key="weekly_trend_bar")
        else:
            st.info("Not enough data to display weekly trend")
    
    with chart_col2:
        # Show agent distribution for the selected week
        if 'AGENT' in week_df.columns and not week_df.empty:
            st.subheader("Agent Distribution")
            agent_counts = week_df['AGENT'].value_counts().reset_index()
            agent_counts.columns = ['Agent', 'Count']
            
            # Take top 10 agents
            top_agents = agent_counts.head(10) if len(agent_counts) > 10 else agent_counts
            
            fig = px.bar(
                top_agents,
                x='Agent',
                y='Count',
                title=f'Top Agents for Week Starting {selected_week_starting}',
                color='Count',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig, use_container_width=True, key="agent_distribution")
            
            # Show pie chart of all agents
            fig = px.pie(
                agent_counts,
                values='Count',
                names='Agent',
                title='Agent Distribution (All Agents)'
            )
            fig.update_traces(textinfo='percent+label')
            # Use the full container width for the chart
            st.plotly_chart(fig, use_container_width=True, key="agent_pie")
        else:
            st.warning("Agent data not available for this week")
    
    # Display data table with enrollments for the selected week
    st.subheader("Active Enrollments for Selected Week")
    
    if week_df.empty:
        st.info("No active enrollments found for the selected week")
        return
    
    # Determine which columns to show in the table
    display_columns = []
    for col in ['ENROLLED_DATE', 'CUSTOMER_NAME', 'AGENT', 'SOURCE_SHEET', 'AMOUNT']:
        if col in week_df.columns:
            display_columns.append(col)
    
    if display_columns:
        # Format the table data
        table_df = week_df[display_columns].copy()
        
        # Format date columns if they exist
        if 'ENROLLED_DATE' in table_df.columns:
            table_df['ENROLLED_DATE'] = table_df['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
        
        # Display the table with styling
        column_config = {}
        if 'AMOUNT' in table_df.columns:
            column_config["AMOUNT"] = st.column_config.NumberColumn(
                "Amount",
                format="$%.2f",
            )
        
        if 'SOURCE_SHEET' in table_df.columns:
            column_config["SOURCE_SHEET"] = st.column_config.TextColumn(
                "Campaign",
            )
        
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
    else:
        st.warning("No data columns available to display")