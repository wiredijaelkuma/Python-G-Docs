# modules/tabs/overview.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def render_overview_tab(df, COLORS):
    """Render the overview tab with key metrics and charts"""
    
    # Create two columns for the layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Weekly Enrollment Trends")
        # Weekly trend analysis
        if 'ENROLLED_DATE' in df.columns:
            # Group by week and count enrollments
            df['Week'] = df['ENROLLED_DATE'].dt.strftime('%Y-%U')
            weekly_data = df.groupby('Week').size().reset_index()
            weekly_data.columns = ['Week', 'Count']
            
            # Add week ending date for better display
            week_dates = []
            for week_str in weekly_data['Week']:
                year, week_num = week_str.split('-')
                # Calculate the date of the Sunday of that week
                week_date = datetime.strptime(f'{year}-{week_num}-0', '%Y-%U-%w')
                week_dates.append(week_date.strftime('%b %d, %Y'))
            
            weekly_data['Week_Ending'] = week_dates
            
            # Create the chart
            fig = px.line(
                weekly_data, 
                x='Week_Ending', 
                y='Count',
                markers=True,
                labels={'Count': 'Enrollments', 'Week_Ending': 'Week Ending'},
                title='Weekly Enrollment Count',
                color_discrete_sequence=[COLORS['primary']]
            )
            
            # Add annotations for the last 4 data points
            for i in range(min(4, len(weekly_data))):
                idx = len(weekly_data) - 1 - i
                fig.add_annotation(
                    x=weekly_data['Week_Ending'].iloc[idx],
                    y=weekly_data['Count'].iloc[idx],
                    text=str(weekly_data['Count'].iloc[idx]),
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-30
                )
                
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Enrollment date data not available")
    
    with col2:
        st.subheader("Status Distribution")
        if 'CATEGORY' in df.columns:
            # Create a pie chart for status distribution
            status_counts = df['CATEGORY'].value_counts().reset_index()
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
                },
                title='Contract Status Distribution'
            )
            
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Status category data not available")
    
    # Latest Metrics Section
    st.subheader("Latest Weekly Metrics")
    
    # Create metrics for the most recent week
    if 'ENROLLED_DATE' in df.columns:
        # Get the most recent week's data
        today = datetime.now()
        one_week_ago = today - timedelta(days=7)
        
        recent_df = df[df['ENROLLED_DATE'] >= one_week_ago]
        
        # Calculate metrics
        total_recent = len(recent_df)
        
        if 'CATEGORY' in recent_df.columns:
            active_recent = len(recent_df[recent_df['CATEGORY'] == 'ACTIVE'])
            cancelled_recent = len(recent_df[recent_df['CATEGORY'] == 'CANCELLED'])
            nsf_recent = len(recent_df[recent_df['CATEGORY'] == 'NSF'])
            
            # Calculate rates
            active_rate = (active_recent / total_recent * 100) if total_recent > 0 else 0
            drop_rate = (cancelled_recent / total_recent * 100) if total_recent > 0 else 0
            nsf_rate = (nsf_recent / total_recent * 100) if total_recent > 0 else 0
            
            # Display metrics in a grid
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("New Enrollments", total_recent)
            
            with col2:
                st.metric("Active Rate", f"{active_rate:.1f}%")
            
            with col3:
                st.metric("Drop Rate", f"{drop_rate:.1f}%")
            
            with col4:
                st.metric("NSF Rate", f"{nsf_rate:.1f}%")
        else:
            st.metric("New Enrollments (Last 7 Days)", total_recent)
    else:
        st.warning("Recent enrollment data not available")
