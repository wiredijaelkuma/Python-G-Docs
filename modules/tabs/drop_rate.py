# modules/tabs/drop_rate.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def render_drop_rate_tab(df, COLORS):
    """Render the drop rate tab with detailed analysis"""
    
    st.subheader("Drop Rate Analysis")
    
    # Check if we have the necessary data
    if 'CATEGORY' not in df.columns or 'ENROLLED_DATE' not in df.columns or df.empty:
        st.warning("Required data (status categories and enrollment dates) not available for drop rate analysis")
        return
    
    # Create tabs for different views
    drop_tabs = st.tabs(["Overview", "Time Analysis", "Contributing Factors"])
    
    # Overview Tab
    with drop_tabs[0]:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Calculate overall drop rate
            total_contracts = len(df)
            cancelled_contracts = len(df[df['CATEGORY'] == 'CANCELLED'])
            overall_drop_rate = (cancelled_contracts / total_contracts * 100) if total_contracts > 0 else 0
            
            # Calculate monthly drop rates
            df['Month'] = df['ENROLLED_DATE'].dt.strftime('%Y-%m')
            monthly_total = df.groupby('Month').size()
            monthly_drops = df[df['CATEGORY'] == 'CANCELLED'].groupby('Month').size()
            
            drop_rate_data = pd.DataFrame({
                'Month': monthly_total.index,
                'Total': monthly_total.values,
                'Dropped': monthly_drops.reindex(monthly_total.index, fill_value=0).values
            })
            
            drop_rate_data['Drop_Rate'] = (drop_rate_data['Dropped'] / drop_rate_data['Total'] * 100).round(1)
            
            # Create the chart
            fig = px.line(
                drop_rate_data, 
                x='Month', 
                y='Drop_Rate',
                markers=True,
                title='Monthly Drop Rate (%)',
                color_discrete_sequence=[COLORS['danger']]
            )
            fig.update_layout(yaxis_title="Drop Rate (%)")
            
            # Add a horizontal line for the overall average
            if not drop_rate_data.empty:
                fig.add_shape(
                    type="line",
                    x0=drop_rate_data['Month'].iloc[0],
                    y0=overall_drop_rate,
                    x1=drop_rate_data['Month'].iloc[-1],
                    y1=overall_drop_rate,
                    line=dict(
                        color="red",
                        width=1,
                        dash="dash",
                    )
                )
                
                # Add annotation for the average line
                fig.add_annotation(
                    x=drop_rate_data['Month'].iloc[-1],
                    y=overall_drop_rate,
                    text=f"Overall Avg: {overall_drop_rate:.1f}%",
                    showarrow=True,
                    arrowhead=1,
                    ax=50,
                    ay=0
                )
            
            st.plotly_chart(fig, use_container_width=True, key="monthly_drop_rate_chart")
        
        with col2:
            # Display key metrics
            st.metric("Overall Drop Rate", f"{overall_drop_rate:.1f}%")
            
            # Calculate recent drop rate (last 30 days)
            today = datetime.now()
            thirty_days_ago = today - timedelta(days=30)
            
            recent_df = df[df['ENROLLED_DATE'] >= thirty_days_ago]
            recent_total = len(recent_df)
            recent_drops = len(recent_df[recent_df['CATEGORY'] == 'CANCELLED'])
            recent_drop_rate = (recent_drops / recent_total * 100) if recent_total > 0 else 0
            
            # Calculate the delta
            delta = recent_drop_rate - overall_drop_rate
            
            st.metric(
                "Last 30 Days Drop Rate", 
                f"{recent_drop_rate:.1f}%",
                delta=f"{delta:.1f}%",
                delta_color="inverse"  # Inverse because lower is better for drop rates
            )
            
            # Show drop counts
            st.metric("Total Drops", cancelled_contracts)
            st.metric("Last 30 Days Drops", recent_drops)
            
            # Show the drop rate data table
            with st.expander("Show Monthly Drop Rate Data"):
                st.dataframe(drop_rate_data, use_container_width=True)
    
    # Time Analysis Tab
    with drop_tabs[1]:
        st.subheader("Drop Timing Analysis")
        
        # Alternative analysis based on just category and enrolled date
        if 'ENROLLED_DATE' in df.columns:
            # Group cancellations by month
            cancelled_df = df[df['CATEGORY'] == 'CANCELLED'].copy()
            
            if cancelled_df.empty:
                st.info("No cancellations found in the selected date range")
                return
                
            cancelled_df['Month'] = cancelled_df['ENROLLED_DATE'].dt.strftime('%Y-%m')
            
            monthly_cancellations = cancelled_df.groupby('Month').size().reset_index()
            monthly_cancellations.columns = ['Month', 'Cancellations']
            
            if not monthly_cancellations.empty:
                # Create chart
                fig = px.bar(
                    monthly_cancellations,
                    x='Month',
                    y='Cancellations',
                    title='Monthly Cancellations',
                    color_discrete_sequence=[COLORS['danger']]
                )
                st.plotly_chart(fig, use_container_width=True, key="monthly_cancellations_chart")
                
                # Calculate month-over-month change
                if len(monthly_cancellations) > 1:
                    monthly_cancellations['Previous'] = monthly_cancellations['Cancellations'].shift(1)
                    monthly_cancellations['MoM_Change'] = monthly_cancellations['Cancellations'] - monthly_cancellations['Previous']
                    
                    # Avoid division by zero
                    monthly_cancellations['MoM_Pct_Change'] = 0.0
                    mask = monthly_cancellations['Previous'] > 0
                    monthly_cancellations.loc[mask, 'MoM_Pct_Change'] = (
                        monthly_cancellations.loc[mask, 'MoM_Change'] / 
                        monthly_cancellations.loc[mask, 'Previous'] * 100
                    ).round(1)
                    
                    # Filter out the first row with NaN values
                    mom_data = monthly_cancellations.dropna()
                    
                    if not mom_data.empty:
                        # Create month-over-month change chart
                        fig = px.bar(
                            mom_data,
                            x='Month',
                            y='MoM_Change',
                            title='Month-over-Month Change in Cancellations',
                            color='MoM_Change',
                            color_continuous_scale=px.colors.diverging.RdBu_r  # Red for increases, blue for decreases
                        )
                        st.plotly_chart(fig, use_container_width=True, key="mom_change_chart")
                        
                        # Show the data table
                        st.subheader("Monthly Cancellation Trends")
                        st.dataframe(
                            monthly_cancellations[['Month', 'Cancellations', 'MoM_Change', 'MoM_Pct_Change']].fillna(''),
                            use_container_width=True
                        )
            else:
                st.info("No monthly cancellation data available")
        else:
            st.warning("Insufficient data for cancellation timing analysis")
    
    # Contributing Factors Tab
    with drop_tabs[2]:
        st.subheader("Drop Contributing Factors")
        
        # Look for other potential contributing factors
        cancelled_df = df[df['CATEGORY'] == 'CANCELLED'].copy()
        
        if cancelled_df.empty:
            st.info("No cancellations found in the selected date range")
            return
        
        # Check for agent correlation if agent data exists
        if 'AGENT' in cancelled_df.columns:
            st.subheader("Cancellations by Agent")
            
            # Calculate agent cancellation rates
            agent_totals = df.groupby('AGENT').size()
            agent_cancellations = cancelled_df.groupby('AGENT').size()
            
            agent_data = pd.DataFrame({
                'Agent': agent_totals.index,
                'Total': agent_totals.values,
                'Cancellations': agent_cancellations.reindex(agent_totals.index, fill_value=0).values
            })
            
            # Calculate cancellation rate
            agent_data['Cancel_Rate'] = (agent_data['Cancellations'] / agent_data['Total'] * 100).round(1)
            
            # Filter to agents with significant volume
            min_contracts = 3  # Minimum contracts to be included
            qualified_agents = agent_data[agent_data['Total'] >= min_contracts].copy()
            
            if not qualified_agents.empty:
                # Sort by cancellation rate
                qualified_agents = qualified_agents.sort_values('Cancel_Rate', ascending=False)
                
                top_agents = qualified_agents.head(10) if len(qualified_agents) >= 10 else qualified_agents
                
                fig = px.bar(
                    top_agents,
                    x='Agent',
                    y='Cancel_Rate',
                    title=f'Top Agents by Cancellation Rate (min {min_contracts} contracts)',
                    color='Cancel_Rate',
                    color_continuous_scale=px.colors.sequential.Reds,
                    text='Cancel_Rate'
                )
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                fig.update_layout(yaxis_title="Cancellation Rate (%)")
                st.plotly_chart(fig, use_container_width=True, key="agent_cancellation_chart")
                
                # Show the data table
                with st.expander("Show Agent Cancellation Data"):
                    st.dataframe(qualified_agents.sort_values('Cancel_Rate', ascending=False), use_container_width=True)
            else:
                st.info(f"No agents with at least {min_contracts} contracts found")
        
        # Check for time-based patterns
        if 'ENROLLED_DATE' in cancelled_df.columns:
            st.subheader("Cancellations by Day of Week")
            
            # Group by day of week
            cancelled_df['DayOfWeek'] = cancelled_df['ENROLLED_DATE'].dt.day_name()
            
            # Order days correctly
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Create a DataFrame with all days
            day_df = pd.DataFrame({'Day': day_order})
            
            # Get counts by day
            day_counts = cancelled_df.groupby('DayOfWeek').size().reset_index()
            day_counts.columns = ['Day', 'Cancellations']
            
            # Merge to ensure all days are included
            day_counts = pd.merge(day_df, day_counts, on='Day', how='left').fillna(0)
            
            # Create the chart
            fig = px.bar(
                day_counts,
                x='Day',
                y='Cancellations',
                title='Cancellations by Enrollment Day of Week',
                color_discrete_sequence=[COLORS['danger']]
            )
            st.plotly_chart(fig, use_container_width=True, key="cancellations_by_day_chart")
        
        # Check for source correlation if source data exists
        if 'SOURCE_SHEET' in cancelled_df.columns:
            st.subheader("Cancellations by Source")
            
            # Calculate source cancellation rates
            source_totals = df.groupby('SOURCE_SHEET').size()
            source_cancellations = cancelled_df.groupby('SOURCE_SHEET').size()
            
            source_data = pd.DataFrame({
                'Source': source_totals.index,
                'Total': source_totals.values,
                'Cancellations': source_cancellations.reindex(source_totals.index, fill_value=0).values
            })
            
            # Calculate cancellation rate
            source_data['Cancel_Rate'] = (source_data['Cancellations'] / source_data['Total'] * 100).round(1)
            
            # Sort by cancellation rate
            source_data = source_data.sort_values('Cancel_Rate', ascending=False)
            
            fig = px.bar(
                source_data,
                x='Source',
                y='Cancel_Rate',
                title='Cancellation Rate by Source',
                color='Cancel_Rate',
                color_continuous_scale=px.colors.sequential.Reds,
                text='Cancel_Rate'
            )
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            fig.update_layout(yaxis_title="Cancellation Rate (%)")
            st.plotly_chart(fig, use_container_width=True, key="source_cancellation_chart")
            
            # Show the data table
            with st.expander("Show Source Cancellation Data"):
                st.dataframe(source_data, use_container_width=True)