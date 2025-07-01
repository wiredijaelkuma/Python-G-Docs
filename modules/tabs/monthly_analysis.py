"""
Monthly Analysis Tab
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Import centralized data processor
from modules.data_processor import normalize_dataframe

def render_monthly_analysis_tab(df_filtered, COLORS):
    """Render the monthly analysis tab"""
    st.header("Monthly Performance Analysis")
    
    # Get the original unfiltered dataframe by loading directly from CSV
    try:
        # Use the filtered data passed to the function
        df_all = df_filtered.copy()
        
        # Identify date column
        date_col = None
        if 'ENROLLED_DATE' in df_all.columns:
            date_col = 'ENROLLED_DATE'
        elif 'ENROLLED DATE' in df_all.columns:
            date_col = 'ENROLLED DATE'
            
        # Clean both dataframes using centralized processor
        df_all = normalize_dataframe(df_all)
        df_filtered = normalize_dataframe(df_filtered)
    except Exception as e:
        st.warning(f"Could not load full dataset: {str(e)}")
        df_all = df_filtered.copy()
    
    try:
        # Check if ENROLLED_DATE exists in the dataframe
        date_column = None
        if 'ENROLLED_DATE' in df_all.columns:
            date_column = 'ENROLLED_DATE'
        elif 'ENROLLED DATE' in df_all.columns:
            date_column = 'ENROLLED DATE'
        else:
            st.error("Enrollment date column not found in the data.")
            return
            
        # Extract year and month from enrollment date for both dataframes
        # Handle NaN values and ensure all values are strings
        df_all['Year_Month'] = df_all[date_column].dt.strftime('%Y-%m').fillna('')
        df_all['Month_Display'] = df_all[date_column].dt.strftime('%B %Y').fillna('')
        
        # Remove rows with empty or NaN dates
        df_all = df_all[df_all['Year_Month'] != '']
        df_all = df_all[df_all['Year_Month'] != 'nan']
        df_all = df_all[df_all['Year_Month'].notna()]
        
        # Do the same for filtered data
        df_filtered['Year_Month'] = df_filtered[date_column].dt.strftime('%Y-%m').fillna('')
        df_filtered['Month_Display'] = df_filtered[date_column].dt.strftime('%B %Y').fillna('')
        
        # Remove rows with empty or NaN dates
        df_filtered = df_filtered[df_filtered['Year_Month'] != '']
        df_filtered = df_filtered[df_filtered['Year_Month'] != 'nan']
        df_filtered = df_filtered[df_filtered['Year_Month'].notna()]
        
        # Get unique year-months and their display names from the unfiltered data
        # Filter out NaN values first
        valid_year_months = [ym for ym in df_all['Year_Month'].unique().tolist() if pd.notna(ym) and ym != 'nan' and ym != '']
        
        # Sort using a custom key function to ensure proper date ordering
        try:
            year_months = sorted(valid_year_months, 
                               key=lambda x: pd.to_datetime(str(x) + '-01'), 
                               reverse=True)
        except Exception as e:
            st.warning(f"Error sorting dates: {str(e)}. Using alphabetical sorting.")
            year_months = sorted(valid_year_months, reverse=True)
        
        if not year_months:
            st.warning("No enrollment date data available.")
            return
            
        # Create a mapping from display name to actual year-month value
        month_display_map = {}
        for ym in year_months:
            # Find a row with this year-month
            rows = df_all[df_all['Year_Month'] == ym]
            if not rows.empty:
                sample_row = rows.iloc[0]
                display_name = sample_row['Month_Display']
                month_display_map[display_name] = ym
            
        # Get display names in sorted order
        try:
            month_display_names = sorted(month_display_map.keys(), 
                                        key=lambda x: pd.to_datetime(x, format='%B %Y'), 
                                        reverse=True)
        except Exception as e:
            # Fallback sorting if datetime conversion fails
            st.warning(f"Date sorting issue: {str(e)}. Using alphabetical sorting instead.")
            month_display_names = sorted(month_display_map.keys(), reverse=True)
        
        # Add option for all months
        month_display_names = ["All Data"] + month_display_names
        
        # Create subtabs for different views
        subtabs = st.tabs(["Monthly Analysis", "Custom Date Range", "Agent Performance", "Status Trends"])
        
        # Tab 1: Monthly Analysis
        with subtabs[0]:
            # Month selector
            col1, col2 = st.columns([1, 1])
            with col1:
                selected_display = st.selectbox("Select Month", month_display_names, key="monthly_select")
            
            # Source sheet selector
            with col2:
                if 'SOURCE_SHEET' in df_all.columns:
                    all_sources = st.checkbox("All Sources", True, key="monthly_all_sources")
                    if not all_sources:
                        sources = st.multiselect("Select Sources", df_all['SOURCE_SHEET'].unique(), key="monthly_sources")
                    else:
                        sources = df_all['SOURCE_SHEET'].unique().tolist()
                else:
                    all_sources = True
                    sources = []
            
            # Filter data for selected month
            if selected_display == "All Data":
                monthly_data = df_all.copy()
                selected_month_display = "All Data"
            else:
                selected_month = month_display_map[selected_display]
                # Use the unfiltered data for the selected month
                monthly_data = df_all[df_all['Year_Month'] == selected_month]
                selected_month_display = selected_display
            
            # Apply source filter if needed
            if 'SOURCE_SHEET' in monthly_data.columns and not all_sources and sources:
                monthly_data = monthly_data[monthly_data['SOURCE_SHEET'].isin(sources)]
                
            # Apply status filters from the main app
            if 'CATEGORY' in monthly_data.columns:
                # Get status filters from session state if available
                status_filter = []
                if 'df' in st.session_state:
                    # Try to infer status filters from the filtered data
                    if 'CATEGORY' in df_filtered.columns:
                        status_filter = df_filtered['CATEGORY'].unique().tolist()
                
                # Only apply if we have status filters
                if status_filter:
                    monthly_data = monthly_data[monthly_data['CATEGORY'].isin(status_filter)]
            
            if monthly_data.empty:
                st.warning(f"No data available for {selected_month_display}. Try adjusting filters.")
                return
                
            # Display monthly metrics
            st.subheader(f"Key Metrics for {selected_month_display}")
            
            # Check if CUSTOMER_ID exists, otherwise use index
            id_column = 'CUSTOMER_ID' if 'CUSTOMER_ID' in monthly_data.columns else 'CUSTOMER ID'
            
            # Calculate metrics
            total_enrollments = len(monthly_data)
            active_count = monthly_data[monthly_data['CATEGORY'] == 'ACTIVE'].shape[0]
            cancelled_count = monthly_data[monthly_data['CATEGORY'] == 'CANCELLED'].shape[0]
            nsf_count = monthly_data[monthly_data['CATEGORY'] == 'NSF'].shape[0] if 'NSF' in monthly_data['CATEGORY'].values else 0
            
            # Calculate rates
            active_rate = (active_count / total_enrollments * 100) if total_enrollments > 0 else 0
            cancelled_rate = (cancelled_count / total_enrollments * 100) if total_enrollments > 0 else 0
            stick_rate = active_rate  # Stick rate is the same as active rate
            
            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Enrollments", total_enrollments)
            col1.metric("Active", active_count)
            col1.metric("Cancelled", cancelled_count)
            
            col2.metric("Active Rate", f"{active_rate:.1f}%")
            col2.metric("Cancellation Rate", f"{cancelled_rate:.1f}%")
            col2.metric("Stick Rate", f"{stick_rate:.1f}%")
            
            col3.metric("NSF Count", nsf_count)
            
            # Agent performance for the month
            st.subheader("Agent Performance")
            
            # Group by agent
            agent_performance = monthly_data.groupby('AGENT').agg(
                Enrollments=(id_column, 'count'),
                Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
                Cancelled=('CATEGORY', lambda x: (x == 'CANCELLED').sum())
            ).reset_index()
            
            # Calculate stick rate for each agent
            agent_performance['Stick Rate'] = (agent_performance['Active'] / agent_performance['Enrollments'] * 100).round(1)
            agent_performance['Stick Rate'] = agent_performance['Stick Rate'].apply(lambda x: f"{x}%")
            
            # Sort by enrollments
            agent_performance = agent_performance.sort_values('Enrollments', ascending=False)
            
            # Display agent performance
            st.dataframe(agent_performance, use_container_width=True)
            
            # Create bar chart for agent enrollments
            fig = px.bar(
                agent_performance,
                x='AGENT',
                y='Enrollments',
                title=f'Enrollments by Agent for {selected_month_display}',
                color_discrete_sequence=[COLORS['primary']]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Status distribution pie chart
            st.subheader("Status Distribution")
            
            status_counts = monthly_data['STATUS'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig = px.pie(
                status_counts,
                values='Count',
                names='Status',
                title=f'Status Distribution for {selected_month_display}',
                color_discrete_sequence=[COLORS['primary'], COLORS['accent'], COLORS['warning'], COLORS['danger']]
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
            # Daily enrollment trend for the month
            st.subheader("Daily Enrollment Trend")
            
            # Only show daily trend if not "All Data"
            if selected_display != "All Data":
                # Extract day from enrollment date
                monthly_data['Day'] = monthly_data[date_column].dt.day
            
                # Group by day
                daily_counts = monthly_data.groupby('Day').size().reset_index()
                daily_counts.columns = ['Day', 'Count']
                
                # Sort by day
                daily_counts = daily_counts.sort_values('Day')
                
                # Create line chart
                fig = px.line(
                    daily_counts,
                    x='Day',
                    y='Count',
                    title=f'Daily Enrollments for {selected_month_display}',
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # For all data, show monthly trend instead
                monthly_trend = monthly_data.groupby(monthly_data[date_column].dt.strftime('%Y-%m')).size().reset_index()
                monthly_trend.columns = ['Month', 'Count']
                monthly_trend = monthly_trend.sort_values('Month')
                
                fig = px.line(
                    monthly_trend,
                    x='Month',
                    y='Count',
                    title='Monthly Enrollment Trend',
                    markers=True,
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Month-over-month comparison
            st.subheader("Month-over-Month Comparison")
            
            # Group all data by year-month
            monthly_trends = df_all.groupby('Year_Month').agg(
                Enrollments=(id_column, 'count'),
                Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
                Cancelled=('CATEGORY', lambda x: (x == 'CANCELLED').sum())
            ).reset_index()
            
            # Calculate stick rate
            monthly_trends['Stick Rate'] = (monthly_trends['Active'] / monthly_trends['Enrollments'] * 100).round(1)
            
            # Sort by year-month chronologically
            try:
                monthly_trends['Month_Sort'] = monthly_trends['Year_Month'].apply(lambda x: pd.to_datetime(str(x) + '-01'))
                monthly_trends = monthly_trends.sort_values('Month_Sort')
                monthly_trends = monthly_trends.drop('Month_Sort', axis=1)
            except Exception as e:
                st.warning(f"Could not sort months chronologically: {str(e)}. Using alphabetical sorting.")
                monthly_trends = monthly_trends.sort_values('Year_Month')
            
            # Create line chart for enrollments trend
            fig = px.line(
                monthly_trends,
                x='Year_Month',
                y='Enrollments',
                title='Monthly Enrollment Trend',
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Create line chart for stick rate trend
            fig = px.line(
                monthly_trends,
                x='Year_Month',
                y='Stick Rate',
                title='Monthly Stick Rate Trend (%)',
                markers=True,
                color_discrete_sequence=[COLORS['accent']]
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Tab 2: Custom Date Range
        with subtabs[1]:
            st.subheader("Custom Date Range Analysis")
            
            # Date range selector
            col1, col2 = st.columns(2)
            with col1:
                min_date = df_all[date_column].min().date()
                max_date = df_all[date_column].max().date()
                start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="custom_start")
            
            with col2:
                end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="custom_end")
            
            # Filter data by date range
            custom_data = df_all[(df_all[date_column].dt.date >= start_date) & 
                                (df_all[date_column].dt.date <= end_date)]
            
            # Apply source filter if needed
            if 'SOURCE_SHEET' in df_all.columns:
                all_sources_custom = st.checkbox("All Sources", True, key="custom_all_sources")
                if not all_sources_custom:
                    sources_custom = st.multiselect("Select Sources", df_all['SOURCE_SHEET'].unique(), key="custom_sources")
                    custom_data = custom_data[custom_data['SOURCE_SHEET'].isin(sources_custom)]
            
            if custom_data.empty:
                st.warning("No data available for the selected date range.")
                return
            
            # Calculate metrics
            total = len(custom_data)
            active = custom_data[custom_data['CATEGORY'] == 'ACTIVE'].shape[0]
            cancelled = custom_data[custom_data['CATEGORY'] == 'CANCELLED'].shape[0]
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Enrollments", total)
            col2.metric("Active", active)
            col3.metric("Cancelled", cancelled)
            
            # Active rate
            active_rate = (active / total * 100) if total > 0 else 0
            st.metric("Active Rate", f"{active_rate:.1f}%")
            
            # Daily trend
            st.subheader("Daily Enrollment Trend")
            custom_data['Date'] = custom_data[date_column].dt.date
            daily_trend = custom_data.groupby('Date').size().reset_index()
            daily_trend.columns = ['Date', 'Count']
            
            fig = px.line(
                daily_trend,
                x='Date',
                y='Count',
                title='Daily Enrollment Trend',
                markers=True,
                color_discrete_sequence=[COLORS['primary']]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Agent performance
            st.subheader("Agent Performance")
            agent_perf = custom_data.groupby('AGENT').agg(
                Enrollments=(id_column, 'count'),
                Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
                Cancelled=('CATEGORY', lambda x: (x == 'CANCELLED').sum())
            ).reset_index()
            
            agent_perf['Active Rate'] = (agent_perf['Active'] / agent_perf['Enrollments'] * 100).round(1)
            agent_perf['Active Rate'] = agent_perf['Active Rate'].apply(lambda x: f"{x}%")
            
            st.dataframe(agent_perf.sort_values('Enrollments', ascending=False), use_container_width=True)
        
        # Tab 3: Agent Performance
        with subtabs[2]:
            st.subheader("Agent Performance Analysis")
            
            # Agent selector
            agents = sorted(df_all['AGENT'].unique())
            selected_agent = st.selectbox("Select Agent", agents, key="agent_select")
            
            # Filter data for selected agent
            agent_data = df_all[df_all['AGENT'] == selected_agent]
            
            # Monthly performance for this agent
            agent_monthly = agent_data.groupby(agent_data[date_column].dt.strftime('%Y-%m')).agg(
                Enrollments=(id_column, 'count'),
                Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
                Cancelled=('CATEGORY', lambda x: (x == 'CANCELLED').sum())
            ).reset_index()
            
            agent_monthly.columns = ['Month', 'Enrollments', 'Active', 'Cancelled']
            agent_monthly['Active Rate'] = (agent_monthly['Active'] / agent_monthly['Enrollments'] * 100).round(1)
            
            # Sort by month
            agent_monthly = agent_monthly.sort_values('Month')
            
            # Display metrics
            st.metric("Total Enrollments", len(agent_data))
            
            # Monthly trend chart
            st.subheader(f"Monthly Performance for {selected_agent}")
            
            # Ensure Month column is properly sorted chronologically
            try:
                agent_monthly['Month_Sort'] = agent_monthly['Month'].apply(lambda x: pd.to_datetime(x + '-01'))
                agent_monthly = agent_monthly.sort_values('Month_Sort')
                agent_monthly = agent_monthly.drop('Month_Sort', axis=1)
            except Exception as e:
                st.warning(f"Could not sort months chronologically: {str(e)}. Using default sorting.")
            
            fig = px.line(
                agent_monthly,
                x='Month',
                y=['Enrollments', 'Active', 'Cancelled'],
                title=f'Monthly Performance Trend for {selected_agent}',
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Active rate trend
            fig = px.line(
                agent_monthly,
                x='Month',
                y='Active Rate',
                title=f'Monthly Active Rate for {selected_agent} (%)',
                markers=True,
                color_discrete_sequence=[COLORS['accent']]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show the data table
            st.subheader("Monthly Performance Data")
            st.dataframe(agent_monthly, use_container_width=True)
        
        # Tab 4: Status Trends
        with subtabs[3]:
            st.subheader("Status Trends Analysis")
            
            # Group by month and status
            status_monthly = df_all.groupby([df_all[date_column].dt.strftime('%Y-%m'), 'STATUS']).size().reset_index()
            status_monthly.columns = ['Month', 'Status', 'Count']
            
            # Ensure Month column is string type
            status_monthly['Month'] = status_monthly['Month'].astype(str)
            
            # Sort by month chronologically
            try:
                status_monthly['Month_Sort'] = status_monthly['Month'].apply(lambda x: pd.to_datetime(x + '-01'))
                status_monthly = status_monthly.sort_values('Month_Sort')
                status_monthly = status_monthly.drop('Month_Sort', axis=1)
            except Exception as e:
                st.warning(f"Could not sort months chronologically: {str(e)}. Using alphabetical sorting.")
                status_monthly = status_monthly.sort_values('Month')
            
            # Status trend chart
            fig = px.line(
                status_monthly,
                x='Month',
                y='Count',
                color='Status',
                title='Monthly Status Trends',
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Category trends (Active vs Cancelled)
            category_monthly = df_all.groupby([df_all[date_column].dt.strftime('%Y-%m'), 'CATEGORY']).size().reset_index()
            category_monthly.columns = ['Month', 'Category', 'Count']
            
            # Ensure Month column is string type
            category_monthly['Month'] = category_monthly['Month'].astype(str)
            
            # Sort by month chronologically
            try:
                category_monthly['Month_Sort'] = category_monthly['Month'].apply(lambda x: pd.to_datetime(x + '-01'))
                category_monthly = category_monthly.sort_values('Month_Sort')
                category_monthly = category_monthly.drop('Month_Sort', axis=1)
            except Exception as e:
                st.warning(f"Could not sort months chronologically: {str(e)}. Using alphabetical sorting.")
                category_monthly = category_monthly.sort_values('Month')
            
            # Category trend chart
            fig = px.line(
                category_monthly,
                x='Month',
                y='Count',
                color='Category',
                title='Monthly Category Trends',
                markers=True,
                color_discrete_sequence=[COLORS['accent'], COLORS['danger'], COLORS['warning']]
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Stacked bar chart of status by month
            fig = px.bar(
                status_monthly,
                x='Month',
                y='Count',
                color='Status',
                title='Monthly Status Distribution',
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())