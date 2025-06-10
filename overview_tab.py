import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from sheet_analyzer_module import get_most_recent_week_data, get_program_usage_stats, get_current_week_number

def render_overview_tab(df_filtered, COLORS, active_contracts, nsf_cases, cancelled_contracts, total_contracts):
    """Render the Overview tab with summary charts and metrics"""
    
    st.markdown("<h2 style='text-align: center; color: #483D8B;'>Sales Overview Dashboard</h2>", unsafe_allow_html=True)
    
    # Current Week Performance - UPDATED SECTION
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Current Week Performance</h3>
        """, unsafe_allow_html=True)
        
        try:
            # Get current week number
            current_week = get_current_week_number()
            current_year = date.today().year
            
            # Filter data for current week
            if 'WEEK' in df_filtered.columns and 'YEAR' in df_filtered.columns:
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
                        st.plotly_chart(fig, use_container_width=True, key="overview_current_week_chart")
                        st.dataframe(agent_summary, use_container_width=True, height=200, key="overview_current_week_table")
                    else:
                        st.info(f"No active sales for the current week (Week {current_week})")
                else:
                    st.info(f"No data available for the current week (Week {current_week})")
            else:
                # Fallback to most recent week data
                recent_summary, recent_fig = get_most_recent_week_data(df_filtered)
                
                # Display the chart with a unique key
                st.plotly_chart(recent_fig, use_container_width=True, key="overview_recent_week_chart")
                
                # Display the summary table
                if not isinstance(recent_summary, pd.DataFrame) or "Message" in recent_summary.columns:
                    st.info("No data available for the most recent week")
                else:
                    st.dataframe(recent_summary, use_container_width=True, height=200, key="overview_recent_week_table")
        
        except Exception as e:
            st.error(f"Error in current week performance: {e}")
            st.info("Could not load current week performance data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Program Usage Statistics
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Program Usage Statistics</h3>
        """, unsafe_allow_html=True)
        
        try:
            # Get program usage stats
            program_stats, program_fig = get_program_usage_stats(df_filtered)
            
            # Display the chart with a unique key
            st.plotly_chart(program_fig, use_container_width=True, key="overview_program_usage_chart")
            
            # Display the summary table
            if not isinstance(program_stats, pd.DataFrame) or "Message" in program_stats.columns:
                st.info("No program usage data available")
            else:
                st.dataframe(program_stats, use_container_width=True, height=200, key="overview_program_stats_table")
        
        except Exception as e:
            st.error(f"Error in program usage stats: {e}")
            st.info("Could not load program usage statistics.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Status summary module
    with st.container():
        st.markdown(f"""
        <div class="chart-box">
        <h3>Contract Status Distribution</h3>
        """, unsafe_allow_html=True)
        
        # Create gauge chart for status distribution
        fig = create_status_gauge(active_contracts, nsf_cases, cancelled_contracts, total_contracts, COLORS)
        st.plotly_chart(fig, use_container_width=True, key="overview_status_gauge_chart")
        
        # Add a clean summary below the gauge
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Rate", f"{(active_contracts/total_contracts*100):.1f}%" if total_contracts > 0 else "0%")
        with col2:
            st.metric("NSF Rate", f"{(nsf_cases/total_contracts*100):.1f}%" if total_contracts > 0 else "0%")
        with col3:
            st.metric("Cancellation Rate", f"{(cancelled_contracts/total_contracts*100):.1f}%" if total_contracts > 0 else "0%")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Time Series Analysis
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Sales Trend Analysis</h3>
        """, unsafe_allow_html=True)
        
        try:
            if 'ENROLLED_DATE' in df_filtered.columns:
                # Create tabs for different time periods
                trend_tab1, trend_tab2 = st.tabs(["📅 Daily Trend", "📊 Weekly Trend"])
                
                with trend_tab1:
                    # Daily trend
                    daily_sales = df_filtered.groupby(df_filtered['ENROLLED_DATE'].dt.date).size().reset_index(name='Daily_Sales')
                    daily_sales.columns = ['Date', 'Sales']
                    
                    # Create line chart
                    fig = px.line(
                        daily_sales,
                        x='Date',
                        y='Sales',
                        title='Daily Sales Trend',
                        markers=True,
                        line_shape='linear'
                    )
                    
                    # Add 7-day moving average
                    daily_sales['MA7'] = daily_sales['Sales'].rolling(window=7, min_periods=1).mean()
                    
                    fig.add_trace(
                        go.Scatter(
                            x=daily_sales['Date'],
                            y=daily_sales['MA7'],
                            mode='lines',
                            name='7-Day Moving Average',
                            line=dict(color=COLORS['secondary'], width=3, dash='dash')
                        )
                    )
                    
                    # Update layout with dark text on light background
                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Number of Sales',
                        height=400,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font_color='darkblue'
                    )
                    
                    # Display the chart with a unique key
                    st.plotly_chart(fig, use_container_width=True, key="overview_daily_trend_chart")
                
                with trend_tab2:
                    # Weekly trend
                    weekly_sales = df_filtered.groupby('WEEK_YEAR').size().reset_index(name='Weekly_Sales')
                    
                    # Create bar chart
                    fig = px.bar(
                        weekly_sales,
                        x='WEEK_YEAR',
                        y='Weekly_Sales',
                        title='Weekly Sales Trend',
                        color='Weekly_Sales',
                        color_continuous_scale=[COLORS['light_purple'], COLORS['primary'], COLORS['secondary']]
                    )
                    
                    # Update layout with dark text on light background
                    fig.update_layout(
                        xaxis_title='Week',
                        yaxis_title='Number of Sales',
                        height=400,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font_color='darkblue',
                        xaxis=dict(
                            tickmode='array',
                            tickvals=weekly_sales['WEEK_YEAR'].iloc[::2],  # Show every other tick to avoid crowding
                            tickangle=45
                        )
                    )
                    
                    # Display the chart with a unique key
                    st.plotly_chart(fig, use_container_width=True, key="overview_weekly_trend_chart")
            else:
                st.info("Time series analysis requires date data, which is not available in the dataset.")
            
        except Exception as e:
            st.error(f"Error in time series analysis: {e}")
            st.info("Could not load time series data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Status Distribution by Source
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Status Distribution by Source</h3>
        """, unsafe_allow_html=True)
        
        try:
            if 'SOURCE_SHEET' in df_filtered.columns and 'CATEGORY' in df_filtered.columns:
                # Clean source names
                df_filtered['CLEAN_SOURCE'] = df_filtered['SOURCE_SHEET'].str.replace('-Raw', '').str.replace(' Raw', '')
                
                # Get status distribution by source
                source_status = df_filtered.groupby(['CLEAN_SOURCE', 'CATEGORY']).size().reset_index(name='Count')
                
                # Create stacked bar chart
                fig = px.bar(
                    source_status,
                    x='CLEAN_SOURCE',
                    y='Count',
                    color='CATEGORY',
                    title='Contract Status by Source',
                    barmode='stack',
                    color_discrete_map={
                        'ACTIVE': COLORS['med_green'],
                        'NSF': COLORS['warning'],
                        'CANCELLED': COLORS['danger'],
                        'OTHER': COLORS['dark_accent']
                    }
                )
                
                # Update layout with dark text on light background
                fig.update_layout(
                    xaxis_title='Source',
                    yaxis_title='Number of Contracts',
                    height=400,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font_color='darkblue',
                    xaxis_tickangle=45,
                    legend_title='Status'
                )
                
                # Display the chart with a unique key
                st.plotly_chart(fig, use_container_width=True, key="overview_source_status_chart")
                
                # Calculate and display success rates by source
                source_totals = source_status.groupby('CLEAN_SOURCE')['Count'].sum().reset_index()
                source_active = source_status[source_status['CATEGORY'] == 'ACTIVE'].copy()
                source_active = source_active.rename(columns={'Count': 'Active_Count'})
                
                source_success = pd.merge(source_totals, source_active[['CLEAN_SOURCE', 'Active_Count']], 
                                         on='CLEAN_SOURCE', how='left')
                source_success['Active_Count'] = source_success['Active_Count'].fillna(0)
                source_success['Success_Rate'] = (source_success['Active_Count'] / source_success['Count'] * 100).round(1)
                source_success = source_success.sort_values('Success_Rate', ascending=False)
                
                # Display as a horizontal bar chart
                fig = px.bar(
                    source_success,
                    y='CLEAN_SOURCE',
                    x='Success_Rate',
                    title='Success Rate by Source',
                    orientation='h',
                    color='Success_Rate',
                    color_continuous_scale=[COLORS['danger'], COLORS['warning'], COLORS['med_green']],
                    text=source_success['Success_Rate'].astype(str) + '%'
                )
                
                # Update layout with dark text on light background
                fig.update_layout(
                    xaxis_title='Success Rate (%)',
                    yaxis_title='Source',
                    height=400,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font_color='darkblue',
                    xaxis=dict(range=[0, 100])
                )
                
                fig.update_traces(textposition='outside')
                
                # Display the chart with a unique key
                st.plotly_chart(fig, use_container_width=True, key="overview_source_success_chart")
                
            else:
                st.info("Source distribution analysis requires source and category data, which is not available in the dataset.")
            
        except Exception as e:
            st.error(f"Error in source distribution analysis: {e}")
            st.info("Could not load source distribution data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)

def create_status_gauge(active, nsf, cancelled, total, COLORS):
    """Create gauge chart for status distribution"""
    fig = go.Figure()
    
    if total > 0:
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=active,
            title={'text': "Active Contracts", 'font': {'color': 'darkblue', 'size': 24}},
            domain={'x': [0, 0.3], 'y': [0.6, 1]},
            gauge={
                'axis': {'range': [0, total], 'tickfont': {'color': 'darkblue'}},
                'bar': {'color': COLORS['med_green']},
                'bgcolor': COLORS['light_green'],
                'bordercolor': COLORS['dark_accent'],
                'borderwidth': 2,
            },
            number={'font': {'color': 'darkblue', 'size': 30}}
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=nsf,
            title={'text': "NSF Cases", 'font': {'color': 'darkblue', 'size': 24}},
            domain={'x': [0.35, 0.65], 'y': [0.6, 1]},
            gauge={
                'axis': {'range': [0, total], 'tickfont': {'color': 'darkblue'}},
                'bar': {'color': COLORS['warning']},
                'bgcolor': 'rgba(255, 215, 0, 0.2)',
                'bordercolor': COLORS['dark_accent'],
                'borderwidth': 2,
            },
            number={'font': {'color': 'darkblue', 'size': 30}}
        ))
        
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=cancelled,
            title={'text': "Cancelled Contracts", 'font': {'color': 'darkblue', 'size': 24}},
            domain={'x': [0.7, 1], 'y': [0.6, 1]},
            gauge={
                'axis': {'range': [0, total], 'tickfont': {'color': 'darkblue'}},
                'bar': {'color': COLORS['danger']},
                'bgcolor': 'rgba(255, 99, 71, 0.2)',
                'bordercolor': COLORS['dark_accent'],
                'borderwidth': 2,
            },
            number={'font': {'color': 'darkblue', 'size': 30}}
        ))
    
    fig.update_layout(
        height=350,
        margin=dict(t=50, b=10),
        grid={'rows': 1, 'columns': 3, 'pattern': "independent"},
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'color': 'darkblue'},
    )
    return fig