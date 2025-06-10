import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_agents_tab(df_filtered, COLORS):
    """Render the Agents tab with agent performance analytics"""
    
    st.markdown("<h2 style='text-align: center; color: #483D8B;'>Agent Performance</h2>", unsafe_allow_html=True)
    
    # Agent Performance Overview
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Agent Performance Overview</h3>
        """, unsafe_allow_html=True)
        
        try:
            if 'AGENT' in df_filtered.columns:
                # Get agent performance data
                agent_performance = df_filtered.groupby(['AGENT', 'CATEGORY']).size().reset_index(name='Count')
                
                # Create pivot table for better visualization
                agent_pivot = agent_performance.pivot_table(
                    index='AGENT', 
                    columns='CATEGORY', 
                    values='Count',
                    fill_value=0
                ).reset_index()
                
                # Ensure all categories exist
                for category in ['ACTIVE', 'NSF', 'CANCELLED', 'OTHER']:
                    if category not in agent_pivot.columns:
                        agent_pivot[category] = 0
                
                # Calculate total and success rate
                agent_pivot['TOTAL'] = agent_pivot['ACTIVE'] + agent_pivot['NSF'] + agent_pivot['CANCELLED'] + agent_pivot['OTHER']
                agent_pivot['SUCCESS_RATE'] = (agent_pivot['ACTIVE'] / agent_pivot['TOTAL'] * 100).round(1)
                
                # Sort by total sales
                agent_pivot = agent_pivot.sort_values('TOTAL', ascending=False)
                
                # Create stacked bar chart
                fig = go.Figure()
                
                # Add traces for each category
                fig.add_trace(go.Bar(
                    x=agent_pivot['AGENT'],
                    y=agent_pivot['ACTIVE'],
                    name='Active',
                    marker_color=COLORS['med_green']
                ))
                
                fig.add_trace(go.Bar(
                    x=agent_pivot['AGENT'],
                    y=agent_pivot['NSF'],
                    name='NSF',
                    marker_color=COLORS['warning']
                ))
                
                fig.add_trace(go.Bar(
                    x=agent_pivot['AGENT'],
                    y=agent_pivot['CANCELLED'],
                    name='Cancelled',
                    marker_color=COLORS['danger']
                ))
                
                fig.add_trace(go.Bar(
                    x=agent_pivot['AGENT'],
                    y=agent_pivot['OTHER'],
                    name='Other',
                    marker_color=COLORS['dark_accent']
                ))
                
                # Update layout with dark text on light background
                fig.update_layout(
                    title='Agent Performance by Contract Status',
                    xaxis_title='Agent',
                    yaxis_title='Number of Contracts',
                    barmode='stack',
                    height=500,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font_color='darkblue',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                # Display the chart with a unique key
                st.plotly_chart(fig, use_container_width=True, key="agents_performance_overview_chart")
                
                # Display the agent performance table
                display_df = agent_pivot.copy()
                display_df['SUCCESS_RATE'] = display_df['SUCCESS_RATE'].apply(lambda x: f"{x}%")
                display_df.columns = ['Agent', 'Active', 'NSF', 'Cancelled', 'Other', 'Total', 'Success Rate']
                
                st.dataframe(display_df, use_container_width=True, height=400, key="agents_performance_overview_table")
                
            else:
                st.info("No agent data available in the dataset.")
            
        except Exception as e:
            st.error(f"Error in agent performance overview: {e}")
            st.info("Could not load agent performance data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Agent Trend Analysis
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Agent Trend Analysis</h3>
        """, unsafe_allow_html=True)
        
        try:
            if 'AGENT' in df_filtered.columns and 'ENROLLED_DATE' in df_filtered.columns:
                # Get top agents
                top_agents = df_filtered['AGENT'].value_counts().head(5).index.tolist()
                
                # Allow user to select agents to display
                selected_agents = st.multiselect(
                    "Select Agents to Display:",
                    options=sorted(df_filtered['AGENT'].unique()),
                    default=top_agents,
                    key="agent_trend_selector"
                )
                
                if selected_agents:
                    # Filter for selected agents
                    agent_trend_df = df_filtered[df_filtered['AGENT'].isin(selected_agents)]
                    
                    # Group by agent and week
                    agent_weekly = agent_trend_df.groupby(['AGENT', 'WEEK_YEAR']).size().reset_index(name='Weekly_Sales')
                    
                    # Create line chart
                    fig = px.line(
                        agent_weekly,
                        x='WEEK_YEAR',
                        y='Weekly_Sales',
                        color='AGENT',
                        title='Weekly Sales Trend by Agent',
                        markers=True,
                        color_discrete_map={agent: COLORS['primary'] if i == 0 else COLORS['secondary'] if i == 1 else 
                                           COLORS['accent'] if i == 2 else COLORS['dark_accent'] if i == 3 else 
                                           COLORS['med_purple'] for i, agent in enumerate(selected_agents)}
                    )
                    
                    # Update layout with dark text on light background
                    fig.update_layout(
                        xaxis_title='Week',
                        yaxis_title='Number of Sales',
                        height=500,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font_color='darkblue',
                        xaxis=dict(
                            tickmode='array',
                            tickvals=agent_weekly['WEEK_YEAR'].unique()[::2],  # Show every other tick to avoid crowding
                            tickangle=45
                        )
                    )
                    
                    # Display the chart with a unique key
                    st.plotly_chart(fig, use_container_width=True, key="agents_trend_chart")
                else:
                    st.info("Please select at least one agent to display the trend.")
            else:
                st.info("Agent trend analysis requires agent and date data, which is not available in the dataset.")
            
        except Exception as e:
            st.error(f"Error in agent trend analysis: {e}")
            st.info("Could not load agent trend data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
    
    # Agent Success Rate Comparison
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Agent Success Rate Comparison</h3>
        """, unsafe_allow_html=True)
        
        try:
            if 'AGENT' in df_filtered.columns and 'CATEGORY' in df_filtered.columns:
                # Calculate success rates for agents with minimum sales
                min_sales = st.slider("Minimum Sales for Comparison:", 1, 50, 5, key="agent_min_sales")
                
                # Get agent counts
                agent_counts = df_filtered['AGENT'].value_counts().reset_index()
                agent_counts.columns = ['AGENT', 'TOTAL']
                
                # Filter for agents with minimum sales
                qualified_agents = agent_counts[agent_counts['TOTAL'] >= min_sales]['AGENT'].tolist()
                
                if qualified_agents:
                    # Filter for qualified agents
                    qualified_df = df_filtered[df_filtered['AGENT'].isin(qualified_agents)]
                    
                    # Calculate success rates
                    success_rates = qualified_df.groupby('AGENT').apply(
                        lambda x: (x['CATEGORY'] == 'ACTIVE').sum() / len(x) * 100
                    ).reset_index(name='SUCCESS_RATE')
                    
                    # Sort by success rate
                    success_rates = success_rates.sort_values('SUCCESS_RATE', ascending=False)
                    
                    # Create horizontal bar chart
                    fig = px.bar(
                        success_rates,
                        y='AGENT',
                        x='SUCCESS_RATE',
                        title=f'Agent Success Rate (Minimum {min_sales} Sales)',
                        orientation='h',
                        color='SUCCESS_RATE',
                        color_continuous_scale=[COLORS['danger'], COLORS['warning'], COLORS['med_green']],
                        text=success_rates['SUCCESS_RATE'].round(1).astype(str) + '%'
                    )
                    
                    # Update layout with dark text on light background
                    fig.update_layout(
                        xaxis_title='Success Rate (%)',
                        yaxis_title='Agent',
                        height=max(400, len(qualified_agents) * 25),  # Dynamic height based on number of agents
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font_color='darkblue',
                        xaxis=dict(range=[0, 100])
                    )
                    
                    fig.update_traces(textposition='outside')
                    
                    # Display the chart with a unique key
                    st.plotly_chart(fig, use_container_width=True, key=f"agents_success_rate_chart_{min_sales}")
                else:
                    st.info(f"No agents have at least {min_sales} sales in the selected period.")
            else:
                st.info("Agent success rate comparison requires agent and category data, which is not available in the dataset.")
            
        except Exception as e:
            st.error(f"Error in agent success rate comparison: {e}")
            st.info("Could not load agent success rate data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)
        
    # Agent Drilldown - NEW SECTION
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Agent Performance Drilldown</h3>
        """, unsafe_allow_html=True)
        
        try:
            if 'AGENT' in df_filtered.columns:
                # Create agent selector
                all_agents = sorted(df_filtered['AGENT'].unique())
                if all_agents:
                    selected_agent = st.selectbox("Select Agent for Detailed Analysis:", all_agents, key="agent_drilldown_selector")
                    
                    # Filter data for selected agent
                    agent_data = df_filtered[df_filtered['AGENT'] == selected_agent]
                    
                    if not agent_data.empty:
                        # Create tabs for different analyses
                        drill_tab1, drill_tab2, drill_tab3 = st.tabs(["📊 Status Breakdown", "📅 Time Trend", "🔍 Program Performance"])
                        
                        with drill_tab1:
                            # Status breakdown
                            status_counts = agent_data['CATEGORY'].value_counts().reset_index()
                            status_counts.columns = ['Status', 'Count']
                            
                            # Create pie chart
                            fig = px.pie(
                                status_counts,
                                values='Count',
                                names='Status',
                                title=f"{selected_agent}'s Status Distribution",
                                color='Status',
                                color_discrete_map={
                                    'ACTIVE': COLORS['med_green'],
                                    'NSF': COLORS['warning'],
                                    'CANCELLED': COLORS['danger'],
                                    'OTHER': COLORS['dark_accent']
                                }
                            )
                            
                            # Update layout with dark text
                            fig.update_layout(
                                height=400,
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                font_color='darkblue'
                            )
                            
                            # Display the chart with a unique key
                            st.plotly_chart(fig, use_container_width=True, key=f"agents_drilldown_status_{selected_agent}")
                            
                            # Display the status breakdown table
                            st.dataframe(status_counts, use_container_width=True, key=f"agents_drilldown_status_table_{selected_agent}")
                        
                        with drill_tab2:
                            if 'ENROLLED_DATE' in agent_data.columns:
                                # Time trend
                                time_trend = agent_data.groupby(agent_data['ENROLLED_DATE'].dt.date).size().reset_index(name='Daily_Sales')
                                time_trend.columns = ['Date', 'Sales']
                                
                                # Create line chart
                                fig = px.line(
                                    time_trend,
                                    x='Date',
                                    y='Sales',
                                    title=f"{selected_agent}'s Sales Trend",
                                    markers=True
                                )
                                
                                # Update layout with dark text
                                fig.update_layout(
                                    xaxis_title='Date',
                                    yaxis_title='Number of Sales',
                                    height=400,
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    font_color='darkblue'
                                )
                                
                                # Display the chart with a unique key
                                st.plotly_chart(fig, use_container_width=True, key=f"agents_drilldown_time_{selected_agent}")
                            else:
                                st.info("Time trend analysis requires date data, which is not available.")
                        
                        with drill_tab3:
                            if 'SOURCE_SHEET' in agent_data.columns:
                                # Program performance
                                agent_data['CLEAN_SOURCE'] = agent_data['SOURCE_SHEET'].str.replace('-Raw', '').str.replace(' Raw', '')
                                program_perf = agent_data.groupby(['CLEAN_SOURCE', 'CATEGORY']).size().reset_index(name='Count')
                                
                                # Create stacked bar chart
                                fig = px.bar(
                                    program_perf,
                                    x='CLEAN_SOURCE',
                                    y='Count',
                                    color='CATEGORY',
                                    title=f"{selected_agent}'s Performance by Program",
                                    barmode='stack',
                                    color_discrete_map={
                                        'ACTIVE': COLORS['med_green'],
                                        'NSF': COLORS['warning'],
                                        'CANCELLED': COLORS['danger'],
                                        'OTHER': COLORS['dark_accent']
                                    }
                                )
                                
                                # Update layout with dark text
                                fig.update_layout(
                                    xaxis_title='Program',
                                    yaxis_title='Number of Contracts',
                                    height=400,
                                    plot_bgcolor='white',
                                    paper_bgcolor='white',
                                    font_color='darkblue',
                                    xaxis_tickangle=45
                                )
                                
                                # Display the chart with a unique key
                                st.plotly_chart(fig, use_container_width=True, key=f"agents_drilldown_program_{selected_agent}")
                                
                                # Calculate success rates by program
                                program_totals = program_perf.groupby('CLEAN_SOURCE')['Count'].sum().reset_index()
                                program_active = program_perf[program_perf['CATEGORY'] == 'ACTIVE'].copy()
                                program_active = program_active.rename(columns={'Count': 'Active_Count'})
                                
                                program_success = pd.merge(program_totals, program_active[['CLEAN_SOURCE', 'Active_Count']], 
                                                         on='CLEAN_SOURCE', how='left')
                                program_success['Active_Count'] = program_success['Active_Count'].fillna(0)
                                program_success['Success_Rate'] = (program_success['Active_Count'] / program_success['Count'] * 100).round(1)
                                
                                # Display the program success table
                                program_success['Success_Rate'] = program_success['Success_Rate'].astype(str) + '%'
                                program_success.columns = ['Program', 'Total Sales', 'Active Sales', 'Success Rate']
                                st.dataframe(program_success, use_container_width=True, key=f"agents_drilldown_program_table_{selected_agent}")
                            else:
                                st.info("Program performance analysis requires program data, which is not available.")
                    else:
                        st.info(f"No data available for {selected_agent} in the selected period.")
                else:
                    st.info("No agent data available for drilldown analysis.")
            else:
                st.info("Agent drilldown requires agent data, which is not available in the dataset.")
            
        except Exception as e:
            st.error(f"Error in agent drilldown: {e}")
            st.info("Could not load agent drilldown data.")
        
        st.markdown("""
        </div>
        """, unsafe_allow_html=True)