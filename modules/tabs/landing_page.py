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
        
    # Group data by week
    df['Week'] = df['ENROLLED_DATE'].dt.strftime('%Y-%U')
    weekly_data = df.groupby('Week').size().reset_index()
    weekly_data.columns = ['Week', 'Count']
    
    if weekly_data.empty:
        st.warning("No weekly data available for the selected date range")
        return
    
    # Add week ending date for better display
    week_dates = []
    week_labels = []
    for week_str in weekly_data['Week']:
        year, week_num = week_str.split('-')
        # Calculate the date of the Sunday of that week
        try:
            week_date = datetime.strptime(f'{year}-{week_num}-0', '%Y-%U-%w')
            week_dates.append(week_date)
            week_labels.append(week_date.strftime('%b %d, %Y'))
        except ValueError:
            # Handle potential date parsing errors
            week_dates.append(datetime.now())
            week_labels.append(f"Week {week_num}, {year}")
    
    weekly_data['Week_Ending'] = week_labels
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
        format_func=lambda i: weekly_data['Week_Ending'][i],
        index=default_week_idx
    )
    
    selected_week = weekly_data['Week'].iloc[selected_week_idx]
    selected_week_ending = weekly_data['Week_Ending'].iloc[selected_week_idx]
    
    # Filter data for selected week
    week_df = df[df['Week'] == selected_week]
    
    # Display metrics for selected week
    st.markdown(f"### Week Ending: {selected_week_ending}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Enrollments", len(week_df))
    
    if 'CATEGORY' in week_df.columns and len(week_df) > 0:
        active_count = len(week_df[week_df['CATEGORY'] == 'ACTIVE'])
        nsf_count = len(week_df[week_df['CATEGORY'] == 'NSF'])
        cancelled_count = len(week_df[week_df['CATEGORY'] == 'CANCELLED'])
        
        active_rate = (active_count / len(week_df) * 100) if len(week_df) > 0 else 0
        nsf_rate = (nsf_count / len(week_df) * 100) if len(week_df) > 0 else 0
        drop_rate = (cancelled_count / len(week_df) * 100) if len(week_df) > 0 else 0
        
        with col2:
            st.metric("Active Rate", f"{active_rate:.1f}%")
        
        with col3:
            st.metric("NSF Rate", f"{nsf_rate:.1f}%")
        
        with col4:
            st.metric("Drop Rate", f"{drop_rate:.1f}%")
    
    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Weekly Enrollment Trend")
        # Create a line chart showing the last 8 weeks
        recent_weeks = weekly_data.head(8)[::-1]  # Reverse to show chronological order
        
        if not recent_weeks.empty:
            fig = px.line(
                recent_weeks, 
                x='Week_Ending', 
                y='Count',
                markers=True,
                labels={'Count': 'Enrollments', 'Week_Ending': 'Week Ending'},
                color_discrete_sequence=[COLORS['primary']]
            )
            
            # Highlight the selected week
            selected_week_in_chart = selected_week_ending in recent_weeks['Week_Ending'].values
            if selected_week_in_chart:
                idx = recent_weeks[recent_weeks['Week_Ending'] == selected_week_ending].index[0]
                fig.add_trace(go.Scatter(
                    x=[selected_week_ending],
                    y=[recent_weeks['Count'].iloc[idx]],
                    mode='markers',
                    marker=dict(color=COLORS['accent'], size=12),
                    name='Selected Week'
                ))
            
            # Add values as annotations
            for i in range(len(recent_weeks)):
                fig.add_annotation(
                    x=recent_weeks['Week_Ending'].iloc[i],
                    y=recent_weeks['Count'].iloc[i],
                    text=str(recent_weeks['Count'].iloc[i]),
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-30
                )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to display weekly trend")
    
    with chart_col2:
        st.subheader("Status Distribution")
        if 'CATEGORY' in week_df.columns and not week_df.empty:
            status_counts = week_df['CATEGORY'].value_counts().reset_index()
            if not status_counts.empty:
                status_counts.columns = ['Status', 'Count']
                
                fig = px.pie(
                    status_counts,
                    values='Count',
                    names='Status',
                    color='Status',
                    color_discrete_map={
                        'ACTIVE': COLORS['med_green'],
                        'NSF': COLORS['warning'],
                        'CANCELLED': COLORS['danger'],
                        'OTHER': COLORS['dark_accent']
                    }
                )
                
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No status data available for this week")
        else:
            st.warning("Status category data not available")
    
    # Display data table with enrollments for the selected week
    st.subheader("Enrollments for Selected Week")
    
    if week_df.empty:
        st.info("No enrollments found for the selected week")
        return
    
    # Determine which columns to show in the table
    display_columns = []
    for col in ['ENROLLED_DATE', 'CUSTOMER_NAME', 'AGENT', 'STATUS', 'CATEGORY', 'AMOUNT']:
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
        
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
    else:
        st.warning("No data columns available to display")