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
        
        # Check if we have contract duration data
        if 'CANCELLED_DATE' in df.columns:
            # Calculate contract duration for cancelled contracts
            cancelled_df = df[df['CATEGORY'] == 'CANCELLED'].copy()
            
            if cancelled_df.empty:
                st.info("No cancellations found in the selected date range")
                return
                
            # Make sure both columns are datetime
            if pd.api.types.is_datetime64_dtype(cancelled_df['ENROLLED_DATE']) and pd.api.types.is_datetime64_dtype(cancelled_df['CANCELLED_DATE']):
                cancelled_df['DURATION_DAYS'] = (cancelled_df['CANCELLED_DATE'] - cancelled_df['ENROLLED_DATE']).dt.days
                
                # Filter out negative durations or extremely large values
                valid_durations = cancelled_df[(cancelled_df['DURATION_DAYS'] >= 0) & (cancelled_df['DURATION_DAYS'] <= 365)]
                
                if not valid_durations.empty:
                    # Calculate statistics
                    avg_duration = valid_durations['DURATION_DAYS'].mean()
                    median_duration = valid_durations['DURATION_DAYS'].median()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Average Days Until Cancellation", f"{avg_duration:.1f}")
                    with col2:
                        st.metric("Median Days Until Cancellation", f"{median_duration:.1f}")
                    
                    # Create histogram of cancellation timing
                    fig = px.histogram(
                        valid_durations,
                        x='DURATION_DAYS',
                        nbins=30,
                        title='Distribution of Days Until Cancellation',
                        color_discrete_sequence=[COLORS['danger']]
                    )
                    fig.update_layout(xaxis_title="Days Until Cancellation", yaxis_title="Count")
                    st.plotly_chart(fig, use_container_width=True, key="cancellation_timing_histogram")
                    
                    # Group by duration buckets
                    duration_buckets = [
                        (0, 7, '0-7 days'),
                        (8, 30, '8-30 days'),
                        (31, 90, '31-90 days'),
                        (91, 180, '91-180 days'),
                        (181, 365, '181-365 days')
                    ]
                    
                    bucket_counts = []
                    bucket_labels = []
                    
                    for start, end, label in duration_buckets:
                        count = len(valid_durations[(valid_durations['DURATION_DAYS'] >= start) & (valid_durations['DURATION_DAYS'] <= end)])
                        bucket_counts.append(count)
                        bucket_labels.append(label)
                    
                    bucket_data = pd.DataFrame({
                        'Duration': bucket_labels,
                        'Count': bucket_counts
                    })
                    
                    if not bucket_data.empty and bucket_data['Count'].sum() > 0:
                        # Create bar chart of duration buckets
                        fig = px.bar(
                            bucket_data,
                            x='Duration',
                            y='Count',
                            title='Cancellations by Time Period',
                            color_discrete_sequence=[COLORS['danger']]
                        )
                        st.plotly_chart(fig, use_container_width=True, key="cancellation_buckets_chart")
                        
                        # Add percentage calculation
                        bucket_data['Percentage'] = (bucket_data['Count'] / bucket_data['Count'].sum() * 100).round(1)
                        
                        # Show critical periods
                        st.subheader("Critical Drop Periods")
                        
                        # Identify the period with highest drop rate
                        if not bucket_data.empty and 'Count' in bucket_data.columns and bucket_data['Count'].max() > 0:
                            max_period = bucket_data.loc[bucket_data['Count'].idxmax()]
                            
                            st.markdown(f"""
                            #### Highest Drop Period: {max_period['Duration']} ({max_period['Percentage']}%)
                            
                            **Analysis:**
                            - {int(max_period['Count'])} contracts were cancelled during this period
                            - This represents {max_period['Percentage']}% of all cancellations
                            """)
                            
                            # Calculate cumulative percentages
                            bucket_data['Cumulative_Pct'] = bucket_data['Percentage'].cumsum()
                            
                            # Find the 80% threshold period
                            threshold_80 = bucket_data[bucket_data['Cumulative_Pct'] >= 80].iloc[0] if any(bucket_data['Cumulative_Pct'] >= 80) else None
                            
                            if threshold_80 is not None:
                                st.markdown(f"""
                                #### 80% of Cancellations Occur By: {threshold_80['Duration']}
                                
                                **Recommendation:** Focus retention efforts within the first {threshold_80['Duration']} of enrollment.
                                """)
                            
                            # Show the data table
                            st.subheader("Drop Period Analysis")
                            st.dataframe(bucket_data[['Duration', 'Count', 'Percentage', 'Cumulative_Pct']], use_container_width=True)
                        else:
                            st.info("Not enough data to identify critical drop periods")
                    else:
                        st.info("No cancellations found in the defined time periods")
                else:
                    st.warning("No valid cancellation duration data available")
            else:
                st.warning("Cancellation date or enrollment date is not in the correct format")
        else:
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
        
        # Check if we have reason codes or other relevant data
        if 'CANCEL_REASON' in df.columns:
            # Analyze cancellation reasons
            cancelled_df = df[df['CATEGORY'] == 'CANCELLED'].copy()
            
            if cancelled_df.empty:
                st.info("No cancellations found in the selected date range")
                return
                
            reason_counts = cancelled_df['CANCEL_REASON'].value_counts().reset_index()
            reason_counts.columns = ['Reason', 'Count']
            
            if not reason_counts.empty:
                # Calculate percentages
                reason_counts['Percentage'] = (reason_counts['Count'] / reason_counts['Count'].sum() * 100).round(1)
                
                # Sort by count
                reason_counts = reason_counts.sort_values('Count', ascending=False)
                
                # Create chart
                fig = px.bar(
                    reason_counts.head(10),
                    x='Reason',
                    y='Count',
                    title='Top 10 Cancellation Reasons',
                    color='Count',
                    color_continuous_scale=px.colors.sequential.Reds,
                    text='Percentage'
                )
                fig.update_traces(texttemplate='%{text}%', textposition='outside')
                st.plotly_chart(fig, use_container_width=True, key="cancellation_reasons_chart")
                
                # Show the data table
                st.subheader("Cancellation Reasons")
                st.dataframe(reason_counts, use_container_width=True)
                
                # Analyze reasons over time if we have dates
                if 'ENROLLED_DATE' in cancelled_df.columns:
                    st.subheader("Cancellation Reasons Over Time")
                    
                    # Get the top 5 reasons for a cleaner chart
                    top_reasons = reason_counts.head(5)['Reason'].tolist()
                    
                    # Group by month and reason
                    cancelled_df['Month'] = cancelled_df['ENROLLED_DATE'].dt.strftime('%Y-%m')
                    
                    # Filter to only top reasons
                    top_reasons_df = cancelled_df[cancelled_df['CANCEL_REASON'].isin(top_reasons)]
                    
                    if not top_reasons_df.empty:
                        # Group and pivot
                        reason_by_month = pd.crosstab(
                            index=top_reasons_df['Month'],
                            columns=top_reasons_df['CANCEL_REASON']
                        ).reset_index()
                        
                        if not reason_by_month.empty:
                            # Melt for plotting
                            reason_by_month_melted = pd.melt(
                                reason_by_month,
                                id_vars=['Month'],
                                var_name='Reason',
                                value_name='Count'
                            )
                            
                            # Create line chart
                            fig = px.line(
                                reason_by_month_melted,
                                x='Month',
                                y='Count',
                                color='Reason',
                                markers=True,
                                title='Top 5 Cancellation Reasons Over Time'
                            )
                            st.plotly_chart(fig, use_container_width=True, key="reasons_over_time_chart")
                        else:
                            st.info("Not enough data to show reasons over time")
                    else:
                        st.info("No data available for top cancellation reasons")
            else:
                st.info("No cancellation reasons found in the data")
        else:
            # Look for other potential contributing factors
            st.write("No specific cancellation reason codes available. Analyzing other potential factors...")
            
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
                min_contracts = 10  # Minimum contracts to be included
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
                
                # Check for hour of day patterns if time data is available
                if 'ENROLLED_DATE' in cancelled_df.columns and cancelled_df['ENROLLED_DATE'].dt.hour.nunique() > 1:
                    st.subheader("Cancellations by Hour of Enrollment")
                    
                    cancelled_df['Hour'] = cancelled_df['ENROLLED_DATE'].dt.hour
                    hour_counts = cancelled_df.groupby('Hour').size().reset_index()
                    hour_counts.columns = ['Hour', 'Cancellations']
                    
                    # Format hours for display
                    hour_counts['Hour_Display'] = hour_counts['Hour'].apply(
                        lambda x: f"{x}:00 - {x+1}:00"
                    )
                    
                    fig = px.bar(
                        hour_counts,
                        x='Hour_Display',
                        y='Cancellations',
                        title='Cancellations by Hour of Enrollment',
                        color_discrete_sequence=[COLORS['danger']]
                    )
                    st.plotly_chart(fig, use_container_width=True, key="cancellations_by_hour_chart")
            
            # Check for product correlation if product data exists
            if 'PRODUCT' in cancelled_df.columns:
                st.subheader("Cancellations by Product")
                
                # Calculate product cancellation rates
                product_totals = df.groupby('PRODUCT').size()
                product_cancellations = cancelled_df.groupby('PRODUCT').size()
                
                product_data = pd.DataFrame({
                    'Product': product_totals.index,
                    'Total': product_totals.values,
                    'Cancellations': product_cancellations.reindex(product_totals.index, fill_value=0).values
                })
                
                # Calculate cancellation rate
                product_data['Cancel_Rate'] = (product_data['Cancellations'] / product_data['Total'] * 100).round(1)
                
                # Filter to products with significant volume
                min_contracts = 5  # Minimum contracts to be included
                qualified_products = product_data[product_data['Total'] >= min_contracts].copy()
                
                if not qualified_products.empty:
                    # Sort by cancellation rate
                    qualified_products = qualified_products.sort_values('Cancel_Rate', ascending=False)
                    
                    top_products = qualified_products.head(10) if len(qualified_products) >= 10 else qualified_products
                    
                    fig = px.bar(
                        top_products,
                        x='Product',
                        y='Cancel_Rate',
                        title=f'Products by Cancellation Rate (min {min_contracts} contracts)',
                        color='Cancel_Rate',
                        color_continuous_scale=px.colors.sequential.Reds,
                        text='Cancel_Rate'
                    )
                    fig.update_traces(texttemplate='%{text}%', textposition='outside')
                    fig.update_layout(yaxis_title="Cancellation Rate (%)")
                    st.plotly_chart(fig, use_container_width=True, key="product_cancellation_chart")
                    
                    # Show the data table
                    with st.expander("Show Product Cancellation Data"):
                        st.dataframe(qualified_products, use_container_width=True)
                else:
                    st.info(f"No products with at least {min_contracts} contracts found")
            
            if not any(col in cancelled_df.columns for col in ['AGENT', 'PRODUCT']):
                st.info("No additional factors (agent, product) found in the data to analyze")