# modules/tabs/agents.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_agents_tab(df, COLORS):
    """Render the agents tab with performance analysis"""
    
    st.subheader("Agent Performance Analysis")
    
    # Check if agent data is available
    if 'AGENT' in df.columns:
        # Create tabs for different agent views
        agent_tabs = st.tabs(["Overview", "Detailed Performance", "Comparison"])
        
        # Overview Tab
        with agent_tabs[0]:
            # Calculate agent metrics
            agent_data = df.groupby('AGENT').size().reset_index()
            agent_data.columns = ['Agent', 'Total']
            
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
                
                # Calculate rates
                agent_data['Active_Rate'] = (agent_data['Active'] / agent_data['Total'] * 100).round(1)
                agent_data['Cancel_Rate'] = (agent_data['Cancelled'] / agent_data['Total'] * 100).round(1)
                agent_data['NSF_Rate'] = (agent_data['NSF'] / agent_data['Total'] * 100).round(1)
            
            # Display top agents
            st.subheader("Top Performing Agents")
            fig = px.bar(
                agent_data.head(10),
                x='Agent',
                y='Total',
                title='Top 10 Agents by Total Enrollments',
                color='Total',
                color_continuous_scale=px.colors.sequential.Purp
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display agent success rates if available
            if 'Active_Rate' in agent_data.columns:
                st.subheader("Agent Success Rates")
                
                # Filter to agents with significant volume
                min_enrollments = 5  # Minimum enrollments to be included
                qualified_agents = agent_data[agent_data['Total'] >= min_enrollments].copy()
                
                # Sort by active rate
                qualified_agents = qualified_agents.sort_values('Active_Rate', ascending=False)
                
                fig = px.bar(
                    qualified_agents.head(10),
                    x='Agent',
                    y='Active_Rate',
                    title=f'Top 10 Agents by Success Rate (min {min_enrollments} enrollments)',
                    color='Active_Rate',
                    color_continuous_scale=px.colors.sequential.Greens,
                    text='Active_Rate'
                )
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(yaxis_title="Active Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Show agents with highest cancellation rates
                st.subheader("Agents with Highest Cancellation Rates")
                
                # Sort by cancellation rate
                cancel_agents = qualified_agents.sort_values('Cancel_Rate', ascending=False)
                
                fig = px.bar(
                    cancel_agents.head(10),
                    x='Agent',
                    y='Cancel_Rate',
                    title=f'Agents with Highest Cancellation Rates (min {min_enrollments} enrollments)',
                    color='Cancel_Rate',
                    color_continuous_scale=px.colors.sequential.Reds,
                    text='Cancel_Rate'
                )
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(yaxis_title="Cancellation Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Show the data table with all agent metrics
                with st.expander("Show All Agent Metrics"):
                    st.dataframe(agent_data, use_container_width=True)
        
        # Detailed Performance Tab
        with agent_tabs[1]:
            # Agent selector
            agents = sorted(df['AGENT'].unique())
            selected_agent = st.selectbox("Select Agent", agents)
            
            if selected_agent:
                # Filter data for selected agent
                agent_df = df[df['AGENT'] == selected_agent]
                
                # Display agent stats
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Enrollments", len(agent_df))
                
                if 'CATEGORY' in agent_df.columns:
                    active_count = len(agent_df[agent_df['CATEGORY'] == 'ACTIVE'])
                    cancelled_count = len(agent_df[agent_df['CATEGORY'] == 'CANCELLED'])
                    nsf_count = len(agent_df[agent_df['CATEGORY'] == 'NSF'])
                    
                    active_rate = (active_count / len(agent_df) * 100) if len(agent_df) > 0 else 0
                    
                    with col2:
                        st.metric("Active Contracts", active_count)
                    with col3:
                        st.metric("Active Rate", f"{active_rate:.1f}%")
                    with col4:
                        st.metric("Cancelled", cancelled_count)
                
                # Show enrollment trend if dates available
                if 'ENROLLED_DATE' in agent_df.columns:
                    st.subheader(f"{selected_agent}'s Enrollment Trend")
                    
                    # Group by month
                    agent_df['Month'] = agent_df['ENROLLED_DATE'].dt.strftime('%Y-%m')
                    monthly_data = agent_df.groupby('Month').size().reset_index()
                    monthly_data.columns = ['Month', 'Count']
                    
                    fig = px.line(
                        monthly_data,
                        x='Month',
                        y='Count',
                        markers=True,
                        title=f'Monthly Enrollments for {selected_agent}',
                        color_discrete_sequence=[COLORS['primary']]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show status breakdown if available
                if 'CATEGORY' in agent_df.columns:
                    st.subheader(f"{selected_agent}'s Status Distribution")
                    
                    status_counts = agent_df['CATEGORY'].value_counts().reset_index()
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
                    
                    # Show performance over time
                    if 'ENROLLED_DATE' in agent_df.columns:
                        st.subheader(f"{selected_agent}'s Performance Over Time")
                        
                        # Group by month and status
                        agent_df['Month'] = agent_df['ENROLLED_DATE'].dt.strftime('%Y-%m')
                        monthly_status = pd.crosstab(
                            index=agent_df['Month'],
                            columns=agent_df['CATEGORY']
                        ).reset_index()
                        
                        # Calculate total for each month
                        monthly_status['Total'] = monthly_status.sum(axis=1)
                        
                        # Calculate active rate for each month
                        if 'ACTIVE' in monthly_status.columns:
                            monthly_status['Active_Rate'] = (monthly_status['ACTIVE'] / monthly_status['Total'] * 100).round(1)
                        
                        # Create the chart
                        fig = go.Figure()
                        
                        # Add bars for total enrollments
                        fig.add_trace(go.Bar(
                            x=monthly_status['Month'],
                            y=monthly_status['Total'],
                            name='Total Enrollments',
                            marker_color=COLORS['primary']
                        ))
                        
                        # Add line for active rate if available
                        if 'Active_Rate' in monthly_status.columns:
                            fig.add_trace(go.Scatter(
                                x=monthly_status['Month'],
                                y=monthly_status['Active_Rate'],
                                name='Active Rate (%)',
                                mode='lines+markers',
                                marker=dict(color=COLORS['med_green']),
                                yaxis='y2'
                            ))
                        
                        # Update layout with secondary y-axis
                        fig.update_layout(
                            title=f'{selected_agent}\'s Monthly Performance',
                            xaxis_title='Month',
                            yaxis_title='Number of Enrollments',
                            yaxis2=dict(
                                title='Rate (%)',
                                overlaying='y',
                                side='right',
                                range=[0, 100]
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Show recent enrollments
                st.subheader(f"{selected_agent}'s Recent Enrollments")
                if 'ENROLLED_DATE' in agent_df.columns:
                    recent_enrollments = agent_df.sort_values('ENROLLED_DATE', ascending=False).head(10)
                    
                    # Select columns to display
                    display_cols = ['ENROLLED_DATE', 'CATEGORY', 'STATUS']
                    display_cols = [col for col in display_cols if col in recent_enrollments.columns]
                    
                    if display_cols:
                        st.dataframe(recent_enrollments[display_cols], use_container_width=True)
                    else:
                        st.dataframe(recent_enrollments.head(10), use_container_width=True)
                else:
                    st.dataframe(agent_df.head(10), use_container_width=True)
                    
                # Show performance by day of week if date data is available
                if 'ENROLLED_DATE' in agent_df.columns:
                    st.subheader(f"{selected_agent}'s Performance by Day of Week")
                    
                    # Group by day of week
                    agent_df['DayOfWeek'] = agent_df['ENROLLED_DATE'].dt.day_name()
                    
                    # Order days correctly
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    
                    # Get counts by day
                    day_counts = agent_df.groupby('DayOfWeek').size().reindex(day_order).reset_index()
                    day_counts.columns = ['Day', 'Count']
                    
                    # Create the chart
                    fig = px.bar(
                        day_counts,
                        x='Day',
                        y='Count',
                        title=f'{selected_agent}\'s Enrollments by Day of Week',
                        color_discrete_sequence=[COLORS['secondary']]
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Comparison Tab
        with agent_tabs[2]:
            st.subheader("Agent Comparison")
            
            # Multi-select for agents
            selected_agents = st.multiselect(
                "Select Agents to Compare",
                options=sorted(df['AGENT'].unique()),
                default=sorted(df['AGENT'].unique())[:5] if len(df['AGENT'].unique()) > 5 else sorted(df['AGENT'].unique())
            )
            
            if selected_agents:
                # Filter data for selected agents
                compare_df = df[df['AGENT'].isin(selected_agents)]
                
                # Group by agent and calculate metrics
                agent_metrics = compare_df.groupby('AGENT').size().reset_index()
                agent_metrics.columns = ['Agent', 'Total']
                
                # Add status breakdowns if available
                if 'CATEGORY' in compare_df.columns:
                    # Active counts and rates
                    active_counts = compare_df[compare_df['CATEGORY'] == 'ACTIVE'].groupby('AGENT').size()
                    agent_metrics['Active'] = active_counts.reindex(agent_metrics['Agent']).fillna(0)
                    agent_metrics['Active_Rate'] = (agent_metrics['Active'] / agent_metrics['Total'] * 100).round(1)
                    
                    # Cancelled counts and rates
                    cancelled_counts = compare_df[compare_df['CATEGORY'] == 'CANCELLED'].groupby('AGENT').size()
                    agent_metrics['Cancelled'] = cancelled_counts.reindex(agent_metrics['Agent']).fillna(0)
                    agent_metrics['Cancel_Rate'] = (agent_metrics['Cancelled'] / agent_metrics['Total'] * 100).round(1)
                    
                    # NSF counts and rates
                    nsf_counts = compare_df[compare_df['CATEGORY'] == 'NSF'].groupby('AGENT').size()
                    agent_metrics['NSF'] = nsf_counts.reindex(agent_metrics['Agent']).fillna(0)
                    agent_metrics['NSF_Rate'] = (agent_metrics['NSF'] / agent_metrics['Total'] * 100).round(1)
                
                # Create comparison charts
                fig = px.bar(
                    agent_metrics,
                    x='Agent',
                    y='Total',
                    title='Total Enrollments by Agent',
                    color='Agent'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show rate comparison if available
                if 'Active_Rate' in agent_metrics.columns:
                    # Reshape data for grouped bar chart
                    rate_data = pd.melt(
                        agent_metrics,
                        id_vars=['Agent'],
                        value_vars=['Active_Rate', 'Cancel_Rate', 'NSF_Rate'],
                        var_name='Metric',
                        value_name='Rate'
                    )
                    
                    # Clean up metric names
                    rate_data['Metric'] = rate_data['Metric'].str.replace('_Rate', '')
                    
                    fig = px.bar(
                        rate_data,
                        x='Agent',
                        y='Rate',
                        color='Metric',
                        barmode='group',
                        title='Rate Comparison by Agent',
                        color_discrete_map={
                            'Active': COLORS['med_green'],
                            'Cancel': COLORS['danger'],
                            'NSF': COLORS['warning']
                        }
                    )
                    fig.update_layout(yaxis_title="Rate (%)")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show the comparison data table
                st.subheader("Comparison Table")
                st.dataframe(agent_metrics, use_container_width=True)
                
                # Monthly performance comparison if date data is available
                if 'ENROLLED_DATE' in compare_df.columns and len(selected_agents) <= 5:  # Limit to 5 agents for readability
                    st.subheader("Monthly Performance Comparison")
                    
                    # Group by month and agent
                    compare_df['Month'] = compare_df['ENROLLED_DATE'].dt.strftime('%Y-%m')
                    monthly_agent_data = compare_df.groupby(['Month', 'AGENT']).size().reset_index()
                    monthly_agent_data.columns = ['Month', 'Agent', 'Count']
                    
                    # Create line chart
                    fig = px.line(
                        monthly_agent_data,
                        x='Month',
                        y='Count',
                        color='Agent',
                        markers=True,
                        title='Monthly Enrollments by Agent'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Agent data not available")
