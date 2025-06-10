# modules/tabs/performance.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def render_performance_tab(df, COLORS):
    """Render the performance tab with trend analysis"""
    
    st.subheader("Performance Metrics")
    
    # Create tabs for different performance views
    perf_tabs = st.tabs(["Monthly Trends", "Daily Performance", "Conversion Metrics"])
    
    # Monthly Trends Tab
    with perf_tabs[0]:
        if 'ENROLLED_DATE' in df.columns:
            # Group by month and calculate metrics
            df['Month'] = df['ENROLLED_DATE'].dt.strftime('%Y-%m')
            monthly_data = df.groupby('Month').size().reset_index()
            monthly_data.columns = ['Month', 'Total']
            
            # Add status breakdowns if available
            if 'CATEGORY' in df.columns:
                # Active counts
                active_counts = df[df['CATEGORY'] == 'ACTIVE'].groupby('Month').size()
                monthly_data['Active'] = active_counts.reindex(monthly_data['Month']).fillna(0)
                
                # Cancelled counts
                cancelled_counts = df[df['CATEGORY'] == 'CANCELLED'].groupby('Month').size()
                monthly_data['Cancelled'] = cancelled_counts.reindex(monthly_data['Month']).fillna(0)
                
                # NSF counts
                nsf_counts = df[df['CATEGORY'] == 'NSF'].groupby('Month').size()
                monthly_data['NSF'] = nsf_counts.reindex(monthly_data['Month']).fillna(0)
                
                # Calculate rates
                monthly_data['Active_Rate'] = (monthly_data['Active'] / monthly_data['Total'] * 100).round(1)
                monthly_data['Cancel_Rate'] = (monthly_data['Cancelled'] / monthly_data['Total'] * 100).round(1)
                monthly_data['NSF_Rate'] = (monthly_data['NSF'] / monthly_data['Total'] * 100).round(1)
            
            # Create the chart
            fig = go.Figure()
            
            # Add bars for total enrollments
            fig.add_trace(go.Bar(
                x=monthly_data['Month'],
                y=monthly_data['Total'],
                name='Total Enrollments',
                marker_color=COLORS['primary']
            ))
            
            # Add lines for rates if available
            if 'Active_Rate' in monthly_data.columns:
                fig.add_trace(go.Scatter(
                    x=monthly_data['Month'],
                    y=monthly_data['Active_Rate'],
                    name='Active Rate (%)',
                    mode='lines+markers',
                    marker=dict(color=COLORS['med_green']),
                    yaxis='y2'
                ))
                
                fig.add_trace(go.Scatter(
                    x=monthly_data['Month'],
                    y=monthly_data['Cancel_Rate'],
                    name='Cancel Rate (%)',
                    mode='lines+markers',
                    marker=dict(color=COLORS['danger']),
                    yaxis='y2'
                ))
            
            # Update layout with secondary y-axis
            fig.update_layout(
                title='Monthly Enrollment Trends',
                xaxis_title='Month',
                yaxis_title='Number of Enrollments',
                yaxis2=dict(
                    title='Rate (%)',
                    overlaying='y',
                    side='right',
                    range=[0, 100]
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, key="monthly_trends_chart")
            
            # Show the data table
            with st.expander("Show Monthly Data"):
                st.dataframe(monthly_data, use_container_width=True)
            
            # Month-over-Month Analysis
            st.subheader("Month-over-Month Performance")
            
            # Calculate MoM changes
            if len(monthly_data) > 1:
                mom_data = monthly_data.copy()
                mom_data['Prev_Total'] = mom_data['Total'].shift(1)
                mom_data['MoM_Change'] = mom_data['Total'] - mom_data['Prev_Total']
                mom_data['MoM_Pct_Change'] = (mom_data['MoM_Change'] / mom_data['Prev_Total'] * 100).round(1)
                
                # Filter out the first row with NaN values
                mom_data = mom_data.dropna()
                
                if not mom_data.empty:
                    # Create MoM change chart
                    fig = px.bar(
                        mom_data,
                        x='Month',
                        y='MoM_Pct_Change',
                        title='Month-over-Month Growth Rate (%)',
                        color='MoM_Pct_Change',
                        color_continuous_scale=px.colors.diverging.RdBu,
                        text='MoM_Pct_Change'
                    )
                    fig.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig.update_layout(yaxis_title="MoM Change (%)")
                    st.plotly_chart(fig, use_container_width=True, key="mom_change_chart")
        else:
            st.warning("Enrollment date data not available")
    
    # Daily Performance Tab
    with perf_tabs[1]:
        if 'ENROLLED_DATE' in df.columns:
            # Group by day of week
            df['DayOfWeek'] = df['ENROLLED_DATE'].dt.day_name()
            
            # Order days correctly
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Get counts by day
            day_counts = df.groupby('DayOfWeek').size().reindex(day_order).reset_index()
            day_counts.columns = ['Day', 'Count']
            
            # Create the chart
            fig = px.bar(
                day_counts,
                x='Day',
                y='Count',
                title='Enrollments by Day of Week',
                color_discrete_sequence=[COLORS['secondary']]
            )
            st.plotly_chart(fig, use_container_width=True, key="day_of_week_chart")
            
            # Time of day analysis if time data is available
            if 'ENROLLED_DATE' in df.columns and df['ENROLLED_DATE'].dt.hour.nunique() > 1:
                st.subheader("Enrollments by Hour of Day")
                
                df['Hour'] = df['ENROLLED_DATE'].dt.hour
                hour_counts = df.groupby('Hour').size().reset_index()
                hour_counts.columns = ['Hour', 'Count']
                
                # Format hours for display
                hour_counts['Hour_Display'] = hour_counts['Hour'].apply(
                    lambda x: f"{x}:00 - {x+1}:00"
                )
                
                fig = px.bar(
                    hour_counts,
                    x='Hour_Display',
                    y='Count',
                    title='Enrollments by Hour of Day',
                    color_discrete_sequence=[COLORS['accent']]
                )
                st.plotly_chart(fig, use_container_width=True, key="hour_of_day_chart")
                
                # Show daily patterns by weekday/weekend
                st.subheader("Weekday vs. Weekend Performance")
                
                # Add weekday/weekend flag
                df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])
                df['WeekdayType'] = df['IsWeekend'].map({True: 'Weekend', False: 'Weekday'})
                
                # Count by weekday type
                weekday_type_counts = df.groupby('WeekdayType').size().reset_index()
                weekday_type_counts.columns = ['Type', 'Count']
                
                # Calculate daily average (to account for fewer weekend days)
                weekday_type_counts['Days'] = weekday_type_counts['Type'].map({'Weekday': 5, 'Weekend': 2})
                weekday_type_counts['Daily_Average'] = (weekday_type_counts['Count'] / weekday_type_counts['Days']).round(1)
                
                # Create comparison chart
                fig = px.bar(
                    weekday_type_counts,
                    x='Type',
                    y='Daily_Average',
                    title='Average Daily Enrollments: Weekday vs. Weekend',
                    color='Type',
                    color_discrete_map={
                        'Weekday': COLORS['primary'],
                        'Weekend': COLORS['accent']
                    },
                    text='Daily_Average'
                )
                fig.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True, key="weekday_weekend_chart")
                
                # Hour distribution by weekday/weekend
                df['Hour'] = df['ENROLLED_DATE'].dt.hour
                
                # Group by weekday type and hour
                hour_type_data = df.groupby(['WeekdayType', 'Hour']).size().reset_index()
                hour_type_data.columns = ['WeekdayType', 'Hour', 'Count']
                
                # Format hours for display
                hour_type_data['Hour_Display'] = hour_type_data['Hour'].apply(
                    lambda x: f"{x}:00 - {x+1}:00"
                )
                
                # Create chart
                fig = px.bar(
                    hour_type_data,
                    x='Hour_Display',
                    y='Count',
                    color='WeekdayType',
                    barmode='group',
                    title='Hourly Distribution: Weekday vs. Weekend',
                    color_discrete_map={
                        'Weekday': COLORS['primary'],
                        'Weekend': COLORS['accent']
                    }
                )
                st.plotly_chart(fig, use_container_width=True, key="hourly_distribution_chart")
        else:
            st.warning("Enrollment date data not available")
    
    # Conversion Metrics Tab
    with perf_tabs[2]:
        st.subheader("Conversion Metrics")
        
        # Check if we have the necessary columns
        if 'LEAD_DATE' in df.columns and 'ENROLLED_DATE' in df.columns:
            # Calculate conversion time
            df['CONVERSION_DAYS'] = (df['ENROLLED_DATE'] - df['LEAD_DATE']).dt.days
            
            # Filter out negative values or extremely large values
            conversion_df = df[(df['CONVERSION_DAYS'] >= 0) & (df['CONVERSION_DAYS'] <= 90)]
            
            # Calculate average conversion time
            avg_conversion = conversion_df['CONVERSION_DAYS'].mean()
            median_conversion = conversion_df['CONVERSION_DAYS'].median()
            
            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Days to Convert", f"{avg_conversion:.1f}")
            with col2:
                st.metric("Median Days to Convert", f"{median_conversion:.1f}")
            
            # Create histogram
            fig = px.histogram(
                conversion_df,
                x='CONVERSION_DAYS',
                nbins=30,
                title='Distribution of Lead-to-Enrollment Conversion Time',
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(xaxis_title="Days to Convert", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True, key="conversion_histogram")
            
            # Show conversion rates by month if available
            if 'MONTH_YEAR' in df.columns:
                st.subheader("Monthly Conversion Rates")
                
                # Group by month and calculate metrics
                monthly_leads = df.groupby('MONTH_YEAR').size()
                monthly_conversions = df[df['CONVERSION_DAYS'].notna()].groupby('MONTH_YEAR').size()
                
                conversion_data = pd.DataFrame({
                    'Month': monthly_leads.index,
                    'Leads': monthly_leads.values,
                    'Conversions': monthly_conversions.reindex(monthly_leads.index, fill_value=0).values
                })
                
                conversion_data['Conversion_Rate'] = (conversion_data['Conversions'] / conversion_data['Leads'] * 100).round(1)
                
                # Create chart
                fig = px.line(
                    conversion_data,
                    x='Month',
                    y='Conversion_Rate',
                    markers=True,
                    title='Monthly Lead-to-Enrollment Conversion Rate (%)',
                    color_discrete_sequence=[COLORS['med_green']]
                )
                fig.update_layout(yaxis_title="Conversion Rate (%)")
                st.plotly_chart(fig, use_container_width=True, key="monthly_conversion_chart")
                
                # Show the data table
                with st.expander("Show Monthly Conversion Data"):
                    st.dataframe(conversion_data, use_container_width=True)
            
            # Conversion by source if available
            if 'SOURCE_SHEET' in df.columns:
                st.subheader("Conversion by Source")
                
                # Calculate conversion rates by source
                source_leads = df.groupby('SOURCE_SHEET').size()
                source_conversions = df[df['CONVERSION_DAYS'].notna()].groupby('SOURCE_SHEET').size()
                
                source_data = pd.DataFrame({
                    'Source': source_leads.index,
                    'Leads': source_leads.values,
                    'Conversions': source_conversions.reindex(source_leads.index, fill_value=0).values
                })
                
                source_data['Conversion_Rate'] = (source_data['Conversions'] / source_data['Leads'] * 100).round(1)
                
                # Sort by conversion rate
                source_data = source_data.sort_values('Conversion_Rate', ascending=False)
                
                # Filter to sources with significant volume
                min_leads = 10  # Minimum leads to be included
                qualified_sources = source_data[source_data['Leads'] >= min_leads].copy()
                
                # Create chart
                fig = px.bar(
                    qualified_sources,
                    x='Source',
                    y='Conversion_Rate',
                    title=f'Conversion Rate by Source (min {min_leads} leads)',
                    color='Conversion_Rate',
                    color_continuous_scale=px.colors.sequential.Blues,
                    text='Conversion_Rate'
                )
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(yaxis_title="Conversion Rate (%)")
                st.plotly_chart(fig, use_container_width=True, key="source_conversion_chart")
                
                # Show the data table
                with st.expander("Show Source Conversion Data"):
                    st.dataframe(qualified_sources, use_container_width=True)
            
            # Conversion by agent if available
            if 'AGENT' in df.columns:
                st.subheader("Conversion by Agent")
                
                # Calculate conversion rates by agent
                agent_leads = df.groupby('AGENT').size()
                agent_conversions = df[df['CONVERSION_DAYS'].notna()].groupby('AGENT').size()
                
                agent_data = pd.DataFrame({
                    'Agent': agent_leads.index,
                    'Leads': agent_leads.values,
                    'Conversions': agent_conversions.reindex(agent_leads.index, fill_value=0).values
                })
                
                agent_data['Conversion_Rate'] = (agent_data['Conversions'] / agent_data['Leads'] * 100).round(1)
                agent_data['Avg_Days_to_Convert'] = df.groupby('AGENT')['CONVERSION_DAYS'].mean().reindex(agent_leads.index).round(1)
                
                # Sort by conversion rate
                agent_data = agent_data.sort_values('Conversion_Rate', ascending=False)
                
                # Filter to agents with significant volume
                min_leads = 5  # Minimum leads to be included
                qualified_agents = agent_data[agent_data['Leads'] >= min_leads].copy()
                
                # Create chart
                fig = px.bar(
                    qualified_agents.head(10),
                    x='Agent',
                    y='Conversion_Rate',
                    title=f'Top 10 Agents by Conversion Rate (min {min_leads} leads)',
                    color='Conversion_Rate',
                    color_continuous_scale=px.colors.sequential.Blues,
                    text='Conversion_Rate'
                )
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(yaxis_title="Conversion Rate (%)")
                st.plotly_chart(fig, use_container_width=True, key="agent_conversion_chart")
                
                # Show the data table
                with st.expander("Show Agent Conversion Data"):
                    st.dataframe(qualified_agents, use_container_width=True)
                
                # Show average conversion time by agent
                st.subheader("Average Conversion Time by Agent")
                
                # Filter to agents with conversion data
                agents_with_conversion = qualified_agents[qualified_agents['Avg_Days_to_Convert'].notna()].copy()
                
                # Sort by conversion time (ascending is better)
                agents_with_conversion = agents_with_conversion.sort_values('Avg_Days_to_Convert')
                
                # Create chart
                fig = px.bar(
                    agents_with_conversion.head(10),
                    x='Agent',
                    y='Avg_Days_to_Convert',
                    title=f'Top 10 Agents by Fastest Conversion Time (min {min_leads} leads)',
                    color='Avg_Days_to_Convert',
                    color_continuous_scale=px.colors.sequential.Blues_r,  # Reversed so darker is better (lower)
                    text='Avg_Days_to_Convert'
                )
                fig.update_traces(texttemplate='%{text} days', textposition='outside')
                fig.update_layout(yaxis_title="Average Days to Convert")
                st.plotly_chart(fig, use_container_width=True, key="agent_conversion_time_chart")
        else:
            st.warning("Lead date or enrollment date data not available for conversion metrics")
            
            # Check if we can show any conversion-related metrics
            if 'CATEGORY' in df.columns:
                st.subheader("Status Distribution")
                
                # Create status distribution chart
                status_counts = df['CATEGORY'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                
                # Calculate percentages
                status_counts['Percentage'] = (status_counts['Count'] / status_counts['Count'].sum() * 100).round(1)
                
                fig = px.pie(
                    status_counts,
                    values='Count',
                    names='Status',
                    title='Contract Status Distribution',
                    color='Status',
                    color_discrete_map={
                        'ACTIVE': COLORS['med_green'],
                        'NSF': COLORS['warning'],
                        'CANCELLED': COLORS['danger'],
                        'OTHER': COLORS['dark_accent']
                    }
                )
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True, key="status_distribution_chart")
                
                # If we have agent data, show performance by agent
                if 'AGENT' in df.columns:
                    st.subheader("Performance by Agent")
                    
                    # Calculate agent metrics
                    agent_data = df.groupby('AGENT').size().reset_index()
                    agent_data.columns = ['Agent', 'Total']
                    
                    # Active counts
                    active_counts = df[df['CATEGORY'] == 'ACTIVE'].groupby('AGENT').size()
                    agent_data['Active'] = active_counts.reindex(agent_data['Agent']).fillna(0)
                    
                    # Calculate success rate
                    agent_data['Success_Rate'] = (agent_data['Active'] / agent_data['Total'] * 100).round(1)
                    
                    # Sort by success rate
                    agent_data = agent_data.sort_values('Success_Rate', ascending=False)
                    
                    # Filter to agents with significant volume
                    min_contracts = 5  # Minimum contracts to be included
                    qualified_agents = agent_data[agent_data['Total'] >= min_contracts].copy()
                    
                    # Create chart
                    fig = px.bar(
                        qualified_agents.head(10),
                        x='Agent',
                        y='Success_Rate',
                        title=f'Top 10 Agents by Success Rate (min {min_contracts} contracts)',
                        color='Success_Rate',
                        color_continuous_scale=px.colors.sequential.Greens,
                        text='Success_Rate'
                    )
                    fig.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig.update_layout(yaxis_title="Success Rate (%)")
                    st.plotly_chart(fig, use_container_width=True, key="agent_success_rate_chart")