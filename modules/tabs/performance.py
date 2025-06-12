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
    perf_tabs = st.tabs(["Daily Performance", "Agent Performance", "Stick Rate", "Risk Analysis"])
    
    # Daily Performance Tab
    with perf_tabs[0]:
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
    
    # Agent Performance Tab
    with perf_tabs[1]:
        # Check if agent data is available
        if 'AGENT' not in df.columns or df.empty:
            st.warning("Agent data not available or no data matches the current filters")
            return
        
        # Calculate agent metrics
        agent_data = df.groupby('AGENT').size().reset_index()
        agent_data.columns = ['Agent', 'Total']
        
        if agent_data.empty:
            st.warning("No agent data available for the selected filters")
            return
        
        # Sort by total enrollments
        agent_data = agent_data.sort_values('Total', ascending=False)
        
        # Add status breakdowns if available
        if 'CATEGORY' in df.columns:
            # Active counts
            active_counts = df[df['CATEGORY'] == 'ACTIVE'].groupby('AGENT').size()
            agent_data['Active'] = active_counts.reindex(agent_data['Agent']).fillna(0)
            
            # Cancelled counts
            cancelled_counts = df[df['CATEGORY'] == 'CANCELLED'].groupby('AGENT').size()
            agent_data['Cancelled'] = cancelled_counts.reindex(agent_data['Agent']).fillna(0)
            
            # NSF counts
            nsf_counts = df[df['CATEGORY'] == 'NSF'].groupby('AGENT').size()
            agent_data['NSF'] = nsf_counts.reindex(agent_data['Agent']).fillna(0)
            
            # Calculate rates - ensure all values are converted to float first
            agent_data['Active_Rate'] = (agent_data['Active'].astype(float) / agent_data['Total'].astype(float) * 100).round(1)
            agent_data['Cancel_Rate'] = (agent_data['Cancelled'].astype(float) / agent_data['Total'].astype(float) * 100).round(1)
            agent_data['NSF_Rate'] = (agent_data['NSF'].astype(float) / agent_data['Total'].astype(float) * 100).round(1)
        
        # Display top agents
        st.subheader("Top Performing Agents")
        
        if len(agent_data) > 0:
            top_agents = agent_data.head(10) if len(agent_data) >= 10 else agent_data
            fig = px.bar(
                top_agents,
                x='Agent',
                y='Total',
                title='Top Agents by Total Enrollments',
                color='Total',
                color_continuous_scale=px.colors.sequential.Purp
            )
            st.plotly_chart(fig, use_container_width=True, key="top_agents_chart")
            
            # Display agent success rates if available
            if 'Active_Rate' in agent_data.columns:
                st.subheader("Agent Success Rates")
                
                # Filter to agents with significant volume
                min_enrollments = 3  # Minimum enrollments to be included
                qualified_agents = agent_data[agent_data['Total'] >= min_enrollments].copy()
                
                if not qualified_agents.empty:
                    # Sort by active rate
                    qualified_agents = qualified_agents.sort_values('Active_Rate', ascending=False)
                    
                    top_success_agents = qualified_agents.head(10) if len(qualified_agents) >= 10 else qualified_agents
                    fig = px.bar(
                        top_success_agents,
                        x='Agent',
                        y='Active_Rate',
                        title=f'Top Agents by Success Rate (min {min_enrollments} enrollments)',
                        color='Active_Rate',
                        color_continuous_scale=px.colors.sequential.Greens,
                        text='Active_Rate'
                    )
                    fig.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig.update_layout(yaxis_title="Active Rate (%)")
                    st.plotly_chart(fig, use_container_width=True, key="agent_success_rates_chart")
                    
                    # Show agents with highest cancellation rates
                    st.subheader("Agents with Highest Cancellation Rates")
                    
                    # Sort by cancellation rate
                    cancel_agents = qualified_agents.sort_values('Cancel_Rate', ascending=False)
                    
                    top_cancel_agents = cancel_agents.head(10) if len(cancel_agents) >= 10 else cancel_agents
                    fig = px.bar(
                        top_cancel_agents,
                        x='Agent',
                        y='Cancel_Rate',
                        title=f'Agents with Highest Cancellation Rates (min {min_enrollments} enrollments)',
                        color='Cancel_Rate',
                        color_continuous_scale=px.colors.sequential.Reds,
                        text='Cancel_Rate'
                    )
                    fig.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig.update_layout(yaxis_title="Cancellation Rate (%)")
                    st.plotly_chart(fig, use_container_width=True, key="agent_cancel_rates_chart")
                else:
                    st.info(f"No agents with at least {min_enrollments} enrollments found")
                
                # Show the data table with all agent metrics
                with st.expander("Show All Agent Metrics"):
                    # Convert all numeric columns to float to avoid type issues
                    for col in agent_data.columns:
                        if col != 'Agent':
                            agent_data[col] = agent_data[col].astype(float)
                    st.dataframe(agent_data, use_container_width=True)
        else:
            st.info("No agent data available to display")
    
    # Stick Rate Tab (formerly Drop Rate)
    with perf_tabs[2]:
        st.subheader("Stick Rate Analysis")
        
        # Check if we have the necessary data
        if 'CATEGORY' not in df.columns or 'ENROLLED_DATE' not in df.columns or df.empty:
            st.warning("Required data (status categories and enrollment dates) not available for stick rate analysis")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Calculate overall stick rate
            total_contracts = len(df)
            active_contracts = len(df[df['CATEGORY'] == 'ACTIVE'])
            overall_stick_rate = (active_contracts / total_contracts * 100) if total_contracts > 0 else 0
            
            # Calculate monthly stick rates
            df['Month'] = df['ENROLLED_DATE'].dt.strftime('%Y-%m')
            monthly_total = df.groupby('Month').size()
            monthly_active = df[df['CATEGORY'] == 'ACTIVE'].groupby('Month').size()
            
            stick_rate_data = pd.DataFrame({
                'Month': monthly_total.index,
                'Total': monthly_total.values,
                'Active': monthly_active.reindex(monthly_total.index, fill_value=0).values
            })
            
            stick_rate_data['Stick_Rate'] = (stick_rate_data['Active'] / stick_rate_data['Total'] * 100).round(1)
            
            # Create the chart
            fig = px.line(
                stick_rate_data, 
                x='Month', 
                y='Stick_Rate',
                markers=True,
                title='Monthly Stick Rate (%)',
                color_discrete_sequence=[COLORS['med_green']]
            )
            fig.update_layout(yaxis_title="Stick Rate (%)")
            
            # Add a horizontal line for the overall average
            if not stick_rate_data.empty:
                fig.add_shape(
                    type="line",
                    x0=stick_rate_data['Month'].iloc[0],
                    y0=overall_stick_rate,
                    x1=stick_rate_data['Month'].iloc[-1],
                    y1=overall_stick_rate,
                    line=dict(
                        color="green",
                        width=1,
                        dash="dash",
                    )
                )
                
                # Add annotation for the average line
                fig.add_annotation(
                    x=stick_rate_data['Month'].iloc[-1],
                    y=overall_stick_rate,
                    text=f"Overall Avg: {overall_stick_rate:.1f}%",
                    showarrow=True,
                    arrowhead=1,
                    ax=50,
                    ay=0
                )
            
            st.plotly_chart(fig, use_container_width=True, key="monthly_stick_rate_chart")
        
        with col2:
            # Display key metrics
            st.metric("Overall Stick Rate", f"{overall_stick_rate:.1f}%")
            
            # Calculate recent stick rate (last 30 days)
            today = datetime.now()
            thirty_days_ago = today - timedelta(days=30)
            
            recent_df = df[df['ENROLLED_DATE'] >= thirty_days_ago]
            recent_total = len(recent_df)
            recent_active = len(recent_df[recent_df['CATEGORY'] == 'ACTIVE'])
            recent_stick_rate = (recent_active / recent_total * 100) if recent_total > 0 else 0
            
            # Calculate the delta
            delta = recent_stick_rate - overall_stick_rate
            
            st.metric(
                "Last 30 Days Stick Rate", 
                f"{recent_stick_rate:.1f}%",
                delta=f"{delta:.1f}%"
            )
            
            # Show active counts
            st.metric("Total Active", active_contracts)
            st.metric("Last 30 Days Active", recent_active)
            
            # Show the stick rate data table
            with st.expander("Show Monthly Stick Rate Data"):
                st.dataframe(stick_rate_data, use_container_width=True)
        
        # Source analysis
        if 'SOURCE_SHEET' in df.columns:
            st.subheader("Stick Rate by Source")
            
            # Calculate source stick rates
            source_totals = df.groupby('SOURCE_SHEET').size()
            source_active = df[df['CATEGORY'] == 'ACTIVE'].groupby('SOURCE_SHEET').size()
            
            source_data = pd.DataFrame({
                'Source': source_totals.index,
                'Total': source_totals.values,
                'Active': source_active.reindex(source_totals.index, fill_value=0).values
            })
            
            # Calculate stick rate
            source_data['Stick_Rate'] = (source_data['Active'].astype(float) / source_data['Total'].astype(float) * 100).round(1)
            
            # Sort by stick rate
            source_data = source_data.sort_values('Stick_Rate', ascending=False)
            
            fig = px.bar(
                source_data,
                x='Source',
                y='Stick_Rate',
                title='Stick Rate by Source',
                color='Stick_Rate',
                color_continuous_scale=px.colors.sequential.Greens,
                text='Stick_Rate'
            )
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(yaxis_title="Stick Rate (%)")
            st.plotly_chart(fig, use_container_width=True, key="source_stick_rate_chart")
            
            # Show the data table
            with st.expander("Show Source Stick Rate Data"):
                st.dataframe(source_data, use_container_width=True)
    
    # Risk Analysis Tab
    with perf_tabs[3]:
        st.subheader("Risk Analysis")
        
        # Check if agent data is available
        if 'AGENT' not in df.columns or df.empty or 'CATEGORY' not in df.columns:
            st.warning("Agent and category data required for risk analysis")
            return
        
        # Calculate agent risk metrics
        agent_data = df.groupby('AGENT').size().reset_index()
        agent_data.columns = ['Agent', 'Total']
        
        if agent_data.empty:
            st.warning("No agent data available for the selected filters")
            return
        
        # Add status breakdowns
        active_counts = df[df['CATEGORY'] == 'ACTIVE'].groupby('AGENT').size()
        agent_data['Active'] = active_counts.reindex(agent_data['Agent']).fillna(0)
        
        cancelled_counts = df[df['CATEGORY'] == 'CANCELLED'].groupby('AGENT').size()
        agent_data['Cancelled'] = cancelled_counts.reindex(agent_data['Agent']).fillna(0)
        
        nsf_counts = df[df['CATEGORY'] == 'NSF'].groupby('AGENT').size()
        agent_data['NSF'] = nsf_counts.reindex(agent_data['Agent']).fillna(0)
        
        # Calculate risk score (higher is riskier)
        agent_data['Risk_Score'] = ((agent_data['Cancelled'].astype(float) * 1.0 + 
                                    agent_data['NSF'].astype(float) * 0.5) / 
                                    agent_data['Total'].astype(float) * 100).round(1)
        
        # Sort by risk score
        agent_data = agent_data.sort_values('Risk_Score', ascending=False)
        
        # Display high risk agents
        st.subheader("High Risk Agents")
        
        if len(agent_data) > 0:
            # Filter to agents with significant volume
            min_enrollments = 3  # Minimum enrollments to be included
            qualified_agents = agent_data[agent_data['Total'] >= min_enrollments].copy()
            
            if not qualified_agents.empty:
                top_risk_agents = qualified_agents.head(10) if len(qualified_agents) >= 10 else qualified_agents
                fig = px.bar(
                    top_risk_agents,
                    x='Agent',
                    y='Risk_Score',
                    title=f'Highest Risk Agents (min {min_enrollments} enrollments)',
                    color='Risk_Score',
                    color_continuous_scale=px.colors.sequential.Reds,
                    text='Risk_Score'
                )
                fig.update_traces(texttemplate='%{text}', textposition='outside')
                fig.update_layout(yaxis_title="Risk Score")
                st.plotly_chart(fig, use_container_width=True, key="agent_risk_chart")
                
                # Show the data table with all agent metrics
                with st.expander("Show All Agent Risk Data"):
                    # Convert all numeric columns to float to avoid type issues
                    for col in agent_data.columns:
                        if col != 'Agent':
                            agent_data[col] = agent_data[col].astype(float)
                    st.dataframe(agent_data, use_container_width=True)
            else:
                st.info(f"No agents with at least {min_enrollments} enrollments found")
        else:
            st.info("No agent data available to display")
        
        # Source risk analysis
        if 'SOURCE_SHEET' in df.columns:
            st.subheader("Risk Analysis by Source")
            
            # Calculate source risk metrics
            source_totals = df.groupby('SOURCE_SHEET').size()
            source_cancelled = df[df['CATEGORY'] == 'CANCELLED'].groupby('SOURCE_SHEET').size()
            source_nsf = df[df['CATEGORY'] == 'NSF'].groupby('SOURCE_SHEET').size()
            
            source_data = pd.DataFrame({
                'Source': source_totals.index,
                'Total': source_totals.values,
                'Cancelled': source_cancelled.reindex(source_totals.index, fill_value=0).values,
                'NSF': source_nsf.reindex(source_totals.index, fill_value=0).values
            })
            
            # Calculate risk score
            source_data['Risk_Score'] = ((source_data['Cancelled'].astype(float) * 1.0 + 
                                        source_data['NSF'].astype(float) * 0.5) / 
                                        source_data['Total'].astype(float) * 100).round(1)
            
            # Sort by risk score
            source_data = source_data.sort_values('Risk_Score', ascending=False)
            
            fig = px.bar(
                source_data,
                x='Source',
                y='Risk_Score',
                title='Risk Score by Source',
                color='Risk_Score',
                color_continuous_scale=px.colors.sequential.Reds,
                text='Risk_Score'
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_layout(yaxis_title="Risk Score")
            st.plotly_chart(fig, use_container_width=True, key="source_risk_chart")
            
            # Show the data table
            with st.expander("Show Source Risk Data"):
                st.dataframe(source_data, use_container_width=True)