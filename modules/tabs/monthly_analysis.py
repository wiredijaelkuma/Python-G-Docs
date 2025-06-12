"""
Monthly Analysis Tab
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

def render_monthly_analysis_tab(df_filtered, COLORS):
    """Render the monthly analysis tab"""
    st.header("Monthly Performance Analysis")
    
    # Create a copy of the dataframe without date filters
    # This ensures we can see all months regardless of the sidebar date filter
    import pandas as pd
    from datetime import datetime, date, timedelta
    
    # Get the original unfiltered dataframe
    if 'df' in st.session_state:
        df_all = st.session_state['df'].copy()
        
        # Convert date columns if needed
        date_col = None
        if 'ENROLLED_DATE' in df_all.columns:
            date_col = 'ENROLLED_DATE'
        elif 'ENROLLED DATE' in df_all.columns:
            date_col = 'ENROLLED DATE'
            
        if date_col and not pd.api.types.is_datetime64_any_dtype(df_all[date_col]):
            try:
                df_all[date_col] = pd.to_datetime(df_all[date_col])
            except:
                pass
    else:
        df_all = df_filtered.copy()
    
    # Debug information
    with st.expander("Debug Information"):
        st.write("Available columns:", df_filtered.columns.tolist())
        if 'SOURCE_SHEET' in df_filtered.columns:
            st.write("Available sources:", df_filtered['SOURCE_SHEET'].unique().tolist())
        st.write("Data shape:", df_filtered.shape)
    
    try:
        # Display info about data source
        st.info("This tab analyzes data from the processed_combined_data.csv file. Make sure this file includes all your data sources.")
        
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
        df_all['Year_Month'] = df_all[date_column].dt.strftime('%Y-%m')
        df_all['Month_Display'] = df_all[date_column].dt.strftime('%B %Y')
        
        df_filtered['Year_Month'] = df_filtered[date_column].dt.strftime('%Y-%m')
        df_filtered['Month_Display'] = df_filtered[date_column].dt.strftime('%B %Y')
        
        # Get unique year-months and their display names from the unfiltered data
        year_months = sorted(df_all['Year_Month'].unique(), reverse=True)
        
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
        month_display_names = sorted(month_display_map.keys(), 
                                    key=lambda x: pd.to_datetime(x, format='%B %Y'), 
                                    reverse=True)
        
        # Add option for all months
        month_display_names = ["All Months"] + month_display_names
            
        # Month selector
        col1, col2 = st.columns([1, 1])
        with col1:
            selected_display = st.selectbox("Select Month", month_display_names)
        
        # Source sheet selector
        with col2:
            if 'SOURCE_SHEET' in df_filtered.columns:
                all_sources = st.checkbox("All Sources", True, key="monthly_all_sources")
                if not all_sources:
                    sources = st.multiselect("Select Sources", df_filtered['SOURCE_SHEET'].unique(), key="monthly_sources")
                else:
                    sources = df_filtered['SOURCE_SHEET'].unique().tolist()
            else:
                all_sources = True
                sources = []
        
        # Filter data for selected month
        if selected_display == "All Months":
            monthly_data = df_filtered.copy()
            selected_month_display = "All Months"
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
            st.warning(f"No data available for {selected_month_display}. This may be due to filtering.")
            
            # Show debug info
            with st.expander("Troubleshooting Information"):
                st.write(f"Selected month: {selected_month_display}")
                if selected_display != "All Months":
                    st.write(f"Raw data for this month: {len(df_all[df_all['Year_Month'] == selected_month])} records")
                    st.write(f"Filtered data for this month: {len(df_filtered[df_filtered['Year_Month'] == selected_month])} records")
                st.write("Try adjusting the filters in the sidebar or selecting a different month.")
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
        
        # Only show daily trend if not "All Months"
        if selected_display != "All Months":
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
            st.info("Daily trend is only available when a specific month is selected.")
        
        # Month-over-month comparison
        st.subheader("Month-over-Month Comparison")
        
        # Group all data by year-month
        monthly_trends = df_filtered.groupby('Year_Month').agg(
            Enrollments=(id_column, 'count'),
            Active=('CATEGORY', lambda x: (x == 'ACTIVE').sum()),
            Cancelled=('CATEGORY', lambda x: (x == 'CANCELLED').sum())
        ).reset_index()
        
        # Calculate stick rate
        monthly_trends['Stick Rate'] = (monthly_trends['Active'] / monthly_trends['Enrollments'] * 100).round(1)
        
        # Sort by year-month
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
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())