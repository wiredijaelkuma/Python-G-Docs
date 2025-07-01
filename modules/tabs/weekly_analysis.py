"""
Weekly Analysis Tab - Week over Week Performance
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.data_processor import normalize_dataframe, calculate_metrics

def render_weekly_analysis_tab(df_filtered, COLORS):
    """Render the weekly analysis tab"""
    st.header("Weekly Performance Analysis")
    
    # Normalize data
    df = normalize_dataframe(df_filtered)
    
    # Check for date column
    date_column = 'ENROLLED_DATE' if 'ENROLLED_DATE' in df.columns else None
    if not date_column or df.empty:
        st.warning("No enrollment date data available for weekly analysis.")
        return
    
    try:
        # Add week information
        df['Week_Start'] = df[date_column].dt.to_period('W').dt.start_time
        df['Week_Number'] = df[date_column].dt.isocalendar().week
        df['Year'] = df[date_column].dt.year
        df['Week_Label'] = df['Week_Start'].dt.strftime('Week of %b %d, %Y')
        
        # Create tabs
        tabs = st.tabs(["Week Overview", "Week Comparison", "Historical Analysis", "Agent Weekly Performance"])
        
        # Tab 1: Week Overview
        with tabs[0]:
            st.subheader("Weekly Enrollment Summary")
            
            # Group by week - use index for counting since customer name column varies
            weekly_data = df.groupby(['Week_Start', 'Week_Label']).agg({
                df.columns[0]: 'count',  # Use first column for counting
                'CATEGORY': lambda x: (x == 'ACTIVE').sum()
            }).reset_index()
            
            weekly_data.columns = ['Week_Start', 'Week_Label', 'Total_Enrollments', 'Active_Enrollments']
            weekly_data['Active_Rate'] = (weekly_data['Active_Enrollments'] / weekly_data['Total_Enrollments'] * 100).round(1)
            
            # Sort by week
            weekly_data = weekly_data.sort_values('Week_Start')
            
            # Display recent weeks metrics
            if len(weekly_data) >= 2:
                current_week = weekly_data.iloc[-1]
                previous_week = weekly_data.iloc[-2]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "This Week Enrollments", 
                        int(current_week['Total_Enrollments']),
                        delta=int(current_week['Total_Enrollments'] - previous_week['Total_Enrollments'])
                    )
                
                with col2:
                    st.metric(
                        "This Week Active", 
                        int(current_week['Active_Enrollments']),
                        delta=int(current_week['Active_Enrollments'] - previous_week['Active_Enrollments'])
                    )
                
                with col3:
                    st.metric(
                        "This Week Active Rate", 
                        f"{current_week['Active_Rate']:.1f}%",
                        delta=f"{current_week['Active_Rate'] - previous_week['Active_Rate']:.1f}%"
                    )
                
                with col4:
                    avg_weekly = weekly_data['Total_Enrollments'].mean()
                    st.metric(
                        "Weekly Average", 
                        f"{avg_weekly:.1f}",
                        delta=f"{current_week['Total_Enrollments'] - avg_weekly:.1f}"
                    )
            
            # Weekly trend chart
            st.subheader("Weekly Enrollment Trend")
            
            fig = px.line(
                weekly_data,
                x='Week_Label',
                y='Total_Enrollments',
                title='Total Enrollments by Week',
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Active rate trend
            fig = px.line(
                weekly_data,
                x='Week_Label',
                y='Active_Rate',
                title='Active Rate by Week (%)',
                markers=True,
                color_discrete_sequence=[COLORS['accent']]
            )
            fig.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Weekly data table
            st.subheader("Weekly Summary Table")
            display_data = weekly_data[['Week_Label', 'Total_Enrollments', 'Active_Enrollments', 'Active_Rate']].copy()
            display_data.columns = ['Week', 'Total Enrollments', 'Active Enrollments', 'Active Rate (%)']
            st.dataframe(display_data.sort_values('Week', ascending=False), use_container_width=True, hide_index=True)
        
        # Tab 2: Week Comparison
        with tabs[1]:
            st.subheader("Week-over-Week Comparison")
            
            # Week selector - chronologically sorted
            all_weeks = weekly_data.sort_values('Week_Start')
            week_options = ['All Time'] + all_weeks['Week_Label'].tolist()
            
            col1, col2 = st.columns(2)
            with col1:
                week1 = st.selectbox("Select First Week", week_options, key="week1")
            with col2:
                week2 = st.selectbox("Select Second Week", week_options, index=1 if len(week_options) > 1 else 0, key="week2")
            
            if week1 and week2 and week1 != week2:
                # Handle "All Time" selection
                if week1 == "All Time":
                    week1_data = df
                    week1_label = "All Time"
                else:
                    week1_data = df[df['Week_Label'] == week1]
                    week1_label = week1
                    
                if week2 == "All Time":
                    week2_data = df
                    week2_label = "All Time"
                else:
                    week2_data = df[df['Week_Label'] == week2]
                    week2_label = week2
                
                # Calculate metrics for both weeks
                week1_metrics = calculate_metrics(week1_data)
                week2_metrics = calculate_metrics(week2_data)
                
                # Display comparison
                st.subheader(f"Comparison: {week1_label} vs {week2_label}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Enrollments",
                        week1_metrics['total'],
                        delta=week1_metrics['total'] - week2_metrics['total'],
                        help=f"{week2_label}: {week2_metrics['total']}"
                    )
                
                with col2:
                    st.metric(
                        "Active Enrollments",
                        week1_metrics['active'],
                        delta=week1_metrics['active'] - week2_metrics['active'],
                        help=f"{week2_label}: {week2_metrics['active']}"
                    )
                
                with col3:
                    st.metric(
                        "Active Rate",
                        f"{week1_metrics['active_rate']:.1f}%",
                        delta=f"{week1_metrics['active_rate'] - week2_metrics['active_rate']:.1f}%",
                        help=f"{week2_label}: {week2_metrics['active_rate']:.1f}%"
                    )
                
                with col4:
                    st.metric(
                        "Cancelled",
                        week1_metrics['cancelled'],
                        delta=week1_metrics['cancelled'] - week2_metrics['cancelled'],
                        help=f"{week2_label}: {week2_metrics['cancelled']}"
                    )
                
                # Side-by-side comparison chart
                comparison_data = pd.DataFrame({
                    'Period': [week1_label, week2_label],
                    'Total': [week1_metrics['total'], week2_metrics['total']],
                    'Active': [week1_metrics['active'], week2_metrics['active']],
                    'Cancelled': [week1_metrics['cancelled'], week2_metrics['cancelled']]
                })
                
                fig = px.bar(
                    comparison_data,
                    x='Period',
                    y=['Total', 'Active', 'Cancelled'],
                    title='Period Comparison',
                    barmode='group',
                    color_discrete_sequence=[COLORS['primary'], COLORS['accent'], COLORS['danger']]
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Agent comparison for selected weeks
                st.subheader("Agent Performance Comparison")
                
                if 'AGENT' in df.columns:
                    week1_agents = week1_data.groupby('AGENT').size().reset_index(name='Week1_Count')
                    week2_agents = week2_data.groupby('AGENT').size().reset_index(name='Week2_Count')
                    
                    agent_comparison = pd.merge(week1_agents, week2_agents, on='AGENT', how='outer').fillna(0)
                    agent_comparison['Difference'] = agent_comparison['Week1_Count'] - agent_comparison['Week2_Count']
                    agent_comparison = agent_comparison.sort_values('Week1_Count', ascending=False)
                    
                    st.dataframe(agent_comparison, use_container_width=True, hide_index=True)
        
        # Tab 3: Historical Analysis
        with tabs[2]:
            st.subheader("Historical Deep Dive")
            
            # Date range selector for historical analysis
            col1, col2 = st.columns(2)
            with col1:
                min_date = df[date_column].min().date()
                max_date = df[date_column].max().date()
                hist_start = st.date_input("Historical Start Date", min_date, min_value=min_date, max_value=max_date, key="hist_start")
            
            with col2:
                hist_end = st.date_input("Historical End Date", max_date, min_value=min_date, max_value=max_date, key="hist_end")
            
            # Filter historical data
            hist_data = df[(df[date_column].dt.date >= hist_start) & (df[date_column].dt.date <= hist_end)]
            
            if not hist_data.empty:
                # Historical weekly data
                hist_data['Week_Start'] = hist_data[date_column].dt.to_period('W').dt.start_time
                hist_data['Week_Label'] = hist_data['Week_Start'].dt.strftime('Week of %b %d, %Y')
                
                hist_weekly = hist_data.groupby(['Week_Start', 'Week_Label']).agg({
                    hist_data.columns[0]: 'count',
                    'CATEGORY': lambda x: (x == 'ACTIVE').sum()
                }).reset_index()
                
                hist_weekly.columns = ['Week_Start', 'Week_Label', 'Total_Enrollments', 'Active_Enrollments']
                hist_weekly['Active_Rate'] = (hist_weekly['Active_Enrollments'] / hist_weekly['Total_Enrollments'] * 100).round(1)
                hist_weekly = hist_weekly.sort_values('Week_Start')
                
                # Historical metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Weeks", len(hist_weekly))
                
                with col2:
                    st.metric("Avg Weekly Enrollments", f"{hist_weekly['Total_Enrollments'].mean():.1f}")
                
                with col3:
                    st.metric("Peak Week Enrollments", hist_weekly['Total_Enrollments'].max())
                
                with col4:
                    st.metric("Avg Active Rate", f"{hist_weekly['Active_Rate'].mean():.1f}%")
                
                # Historical trend chart
                fig = px.line(
                    hist_weekly,
                    x='Week_Start',
                    y='Total_Enrollments',
                    title=f'Historical Weekly Trend ({hist_start} to {hist_end})',
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Moving averages
                if len(hist_weekly) >= 4:
                    hist_weekly['4_Week_MA'] = hist_weekly['Total_Enrollments'].rolling(window=4).mean()
                    
                    fig = px.line(
                        hist_weekly,
                        x='Week_Start',
                        y=['Total_Enrollments', '4_Week_MA'],
                        title='Weekly Enrollments with 4-Week Moving Average',
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Historical data table
                st.subheader("Historical Weekly Data")
                display_hist = hist_weekly[['Week_Label', 'Total_Enrollments', 'Active_Enrollments', 'Active_Rate']].copy()
                display_hist.columns = ['Week', 'Total Enrollments', 'Active Enrollments', 'Active Rate (%)']
                st.dataframe(display_hist.sort_values('Week', ascending=False), use_container_width=True, hide_index=True)
            else:
                st.warning("No data available for the selected date range.")
        
        # Tab 4: Agent Weekly Performance
        with tabs[3]:
            st.subheader("Agent Weekly Performance")
            
            if 'AGENT' in df.columns:
                # Agent selector
                agents = sorted(df['AGENT'].unique())
                selected_agent = st.selectbox("Select Agent", agents, key="weekly_agent")
                
                # Filter data for selected agent
                agent_data = df[df['AGENT'] == selected_agent]
                
                # Group by week for this agent
                agent_weekly = agent_data.groupby(['Week_Start', 'Week_Label']).agg({
                    agent_data.columns[0]: 'count',  # Use first column for counting
                    'CATEGORY': lambda x: (x == 'ACTIVE').sum()
                }).reset_index()
                
                agent_weekly.columns = ['Week_Start', 'Week_Label', 'Total', 'Active']
                agent_weekly['Active_Rate'] = pd.to_numeric(agent_weekly['Active'], errors='coerce') / pd.to_numeric(agent_weekly['Total'], errors='coerce') * 100
        agent_weekly['Active_Rate'] = agent_weekly['Active_Rate'].round(1)
                agent_weekly = agent_weekly.sort_values('Week_Start')
                
                if not agent_weekly.empty:
                    # Agent weekly metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Weeks Active", len(agent_weekly))
                    
                    with col2:
                        st.metric("Average Weekly Enrollments", f"{agent_weekly['Total'].mean():.1f}")
                    
                    with col3:
                        st.metric("Average Active Rate", f"{agent_weekly['Active_Rate'].mean():.1f}%")
                    
                    # Agent weekly trend
                    fig = px.line(
                        agent_weekly,
                        x='Week_Label',
                        y='Total',
                        title=f'Weekly Enrollments for {selected_agent}',
                        markers=True,
                        color_discrete_sequence=[COLORS['primary']]
                    )
                    fig.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Agent weekly data table
                    display_agent_data = agent_weekly[['Week_Label', 'Total', 'Active', 'Active_Rate']].copy()
                    display_agent_data.columns = ['Week', 'Total Enrollments', 'Active', 'Active Rate (%)']
                    st.dataframe(display_agent_data.sort_values('Week', ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.info(f"No data found for agent: {selected_agent}")
            else:
                st.warning("Agent information not available in the data.")
    
    except Exception as e:
        st.error(f"Error in weekly analysis: {str(e)}")
        import traceback
        st.error(traceback.format_exc())