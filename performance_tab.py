import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
from sheet_analyzer_module import prepare_weekly_performance, prepare_monthly_tracker, prepare_pac_metrics, get_current_week_number

def render_performance_tab(df_filtered, COLORS):
    """Render the Performance tab with weekly and monthly analytics"""
    
    st.markdown("<h2 style='text-align: center; color: #483D8B;'>Performance Analytics</h2>", unsafe_allow_html=True)
    
    # Weekly Performance Section
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Weekly Performance</h3>
        """, unsafe_allow_html=True)
        
        try:
            # Get current week number
            today = date.today()
            current_week = get_current_week_number()
            current_year = today.year
            
            # Create week selector
            available_weeks = sorted(df_filtered['WEEK'].unique(), reverse=True) if 'WEEK' in df_filtered.columns else [current_week]
            
            col1, col2 = st.columns([1, 3])
            with col1:
                selected_week = st.selectbox(
                    "Select Week:", 
                    available_weeks,
                    index=0 if current_week in available_weeks else 0,
                    key="performance_week_selector"
                )
            
            # Get year for the selected week
            if 'WEEK' in df_filtered.columns and 'YEAR' in df_filtered.columns:
                years_with_week = df_filtered[df_filtered['WEEK'] == int(selected_week)]['YEAR'].unique()
                if len(years_with_week) > 0:
                    selected_year = max(years_with_week)
                else:
                    selected_year = today.year
            else:
                selected_year = today.year
                
            # Display the selected week range
            start_week, end_week = get_week_dates(int(selected_week), int(selected_year))
            st.write(f"Week Range: {start_week.strftime('%b %d, %Y')} - {end_week.strftime('%b %d, %Y')}")
            
            # Direct filtering for current week data
            if int(selected_week) == current_week and int(selected_year) == current_year:
                # Filter data for current week
                current_week_data = df_filtered[(df_filtered['WEEK'] == current_week) & 
                                              (df_filtered['YEAR'] == current_year)]
                
                if not current_week_data.empty:
                    # Filter for active sales
                    active_sales = current_week_data[current_week_data['CATEGORY'] == 'ACTIVE']
                    
                    if not active_sales.empty:
                        # Create agent summary
                        agent_summary = active_sales.groupby('AGENT').size().reset_index(name='Active Enrollments')
                        agent_summary = agent_summary.sort_values('Active Enrollments', ascending=False)
                        
                        # Create chart
                        fig = px.bar(
                            agent_summary,
                            x='AGENT',
                            y='Active Enrollments',
                            title=f"Current Week (Week {current_week}) Active Performance",
                            color='AGENT'
                        )
                        
                        fig.update_layout(
                            xaxis_title='Agent',
                            yaxis_title='Active Enrollments',
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            font_color='darkblue'
                        )
                        
                        # Display chart and table
                        st.plotly_chart(fig, use_container_width=True, key=f"performance_weekly_chart_{selected_week}")
                        st.dataframe(agent_summary, use_container_width=True, height=200, key=f"performance_weekly_table_{selected_week}")
                    else:
                        st.info(f"No active sales for the current week (Week {current_week})")
                else:
                    st.info(f"No data available for the current week (Week {current_week})")
            else:
                # Use the prepare_weekly_performance function for historical weeks
                weekly_summary, weekly_fig = prepare_weekly_performance(df_filtered, selected_week, selected_year)
                
                # Display the chart with a unique key
                st.plotly_chart(weekly_fig, use_container_width=True, key=f"performance_weekly_chart_{selected_week}")
                
                # Display the summary table
                if not isinstance(weekly_summary, pd.DataFrame) or "Message" in weekly_summary.columns:
                    st.info(f"No data available for Week {selected_week}")
                else:
                    st.dataframe(weekly_summary, use_container_width=True, height=200, key=f"performance_weekly_table_{selected_week}")
            
        except Exception as e:
            st.error(f"Error in weekly performance: {e}")
            st.info("Could not load weekly performance data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Monthly Tracker Section
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Monthly Performance Tracker</h3>
        """, unsafe_allow_html=True)
        
        try:
            # Get current month
            today = date.today()
            current_month = today.month
            current_year = today.year
            
            # Create month selector
            months = list(calendar.month_name)[1:]  # Skip empty first element
            years = sorted(df_filtered['YEAR'].unique()) if 'YEAR' in df_filtered.columns else [current_year]
            
            col1, col2 = st.columns(2)
            with col1:
                selected_month = st.selectbox(
                    "Select Month:", 
                    months,
                    index=current_month-1,
                    key="performance_month_selector"
                )
            with col2:
                selected_year = st.selectbox(
                    "Select Year:", 
                    years,
                    index=0,
                    key="performance_year_selector"
                )
            
            # Create a date object for the selected month/year
            selected_date = date(selected_year, months.index(selected_month) + 1, 1)
            
            # Generate monthly tracker data using sheet_analyzer function
            daily_counts, fig_line, fig_heatmap = prepare_monthly_tracker(df_filtered, selected_date)
            
            # Display the charts in tabs
            monthly_tab1, monthly_tab2 = st.tabs(["📈 Line Chart", "🔥 Heatmap"])
            
            with monthly_tab1:
                st.plotly_chart(fig_line, use_container_width=True, key=f"performance_monthly_line_{selected_month}_{selected_year}")
            
            with monthly_tab2:
                st.plotly_chart(fig_heatmap, use_container_width=True, key=f"performance_monthly_heatmap_{selected_month}_{selected_year}")
            
            # Display the summary table
            if not isinstance(daily_counts, pd.DataFrame) or "Message" in daily_counts.columns:
                st.info(f"No data available for {selected_month} {selected_year}")
            else:
                st.dataframe(daily_counts, use_container_width=True, height=200, key=f"performance_monthly_table_{selected_month}_{selected_year}")
            
        except Exception as e:
            st.error(f"Error in monthly tracker: {e}")
            st.info("Could not load monthly tracker data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # PAC Metrics Section
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>PAC Performance Metrics</h3>
        """, unsafe_allow_html=True)
        
        try:
            # Use the same month/year selection as above
            selected_month_name = st.session_state.get("performance_month_selector", calendar.month_name[current_month])
            selected_year_val = st.session_state.get("performance_year_selector", current_year)
            
            # Create a date object for the selected month/year
            month_idx = list(calendar.month_name).index(selected_month_name)
            selected_date = date(selected_year_val, month_idx, 1)
            
            # Generate PAC metrics data using sheet_analyzer function
            daily_sales, summary_metrics, fig_sales, fig_gauge = prepare_pac_metrics(df_filtered, selected_date)
            
            # Display the summary metrics
            if not isinstance(summary_metrics, pd.DataFrame) or "Message" in summary_metrics.columns:
                st.info(f"No PAC metrics available for {selected_month_name} {selected_year_val}")
            else:
                # Display the gauge chart and sales chart side by side
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(fig_gauge, use_container_width=True, key=f"performance_pac_gauge_{selected_month_name}_{selected_year_val}")
                with col2:
                    st.plotly_chart(fig_sales, use_container_width=True, key=f"performance_pac_sales_{selected_month_name}_{selected_year_val}")
                
                # Display the summary metrics table
                st.subheader("PAC Performance Summary")
                st.dataframe(summary_metrics, use_container_width=True, height=200, key=f"performance_pac_metrics_{selected_month_name}_{selected_year_val}")
            
        except Exception as e:
            st.error(f"Error in PAC metrics: {e}")
            st.info("Could not load PAC metrics data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)

def get_week_dates(week_number, year):
    """Get start and end dates for a given week number"""
    # Use the ISO calendar to get the correct dates
    # Find the first day of the year
    first_day = date(year, 1, 1)
    
    # Find the first day of the first ISO week
    # In ISO calendar, weeks start on Monday
    first_week_day = first_day
    while first_week_day.isocalendar()[1] != 1:
        first_week_day += timedelta(days=1)
    
    # Calculate the start date of the target week
    # Weeks start on Monday in ISO calendar
    start_week = first_week_day + timedelta(weeks=week_number-1)
    
    # Calculate the end date of the target week (Sunday)
    end_week = start_week + timedelta(days=6)
    
    return start_week, end_week