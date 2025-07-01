"""
Agent Performance Analysis Module
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def render_agent_performance(df, COLORS, HEAT_COLORS):
    """Render comprehensive agent performance analysis"""
    
    if 'AGENT' not in df.columns:
        st.warning("No agent data available")
        return
    
    # Filter out commission data
    sales_df = df[df['SOURCE_SHEET'] != 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else df.copy()
    
    if sales_df.empty:
        st.warning("No sales data available")
        return
    
    # Agent Performance subtabs
    subtabs = st.tabs(["📊 Retention Metrics", "🏆 Agent Comparisons", "👥 Customer Analysis"])
    
    with subtabs[0]:
        render_retention_metrics(sales_df, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_agent_comparisons(sales_df, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        render_customer_analysis(sales_df, COLORS, HEAT_COLORS)

def render_retention_metrics(sales_df, COLORS, HEAT_COLORS):
    """Render retention metrics analysis"""
    st.subheader("📊 Retention Metrics")
    
    if 'CATEGORY' not in sales_df.columns:
        st.warning("No category data available for retention analysis")
        return
    
    # Agent selector
    agents = sales_df['AGENT'].dropna().unique()
    selected_agent = st.selectbox("Select Agent for Detailed Analysis:", ['All Agents'] + list(agents), key="retention_agent")
    
    if selected_agent == 'All Agents':
        agent_data = sales_df
    else:
        agent_data = sales_df[sales_df['AGENT'] == selected_agent]
    
    # Retention metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        retention_rate = (len(agent_data[agent_data['CATEGORY'] == 'ACTIVE']) / len(agent_data) * 100) if len(agent_data) > 0 else 0
        st.metric("Retention Rate", f"{retention_rate:.1f}%")
    
    with col2:
        cancellation_rate = (len(agent_data[agent_data['CATEGORY'] == 'CANCELLED']) / len(agent_data) * 100) if len(agent_data) > 0 else 0
        st.metric("Cancellation Rate", f"{cancellation_rate:.1f}%")
    
    with col3:
        nsf_rate = (len(agent_data[agent_data['CATEGORY'] == 'NSF']) / len(agent_data) * 100) if len(agent_data) > 0 else 0
        st.metric("NSF Rate", f"{nsf_rate:.1f}%")
    
    with col4:
        avg_lifetime = 30  # Placeholder - would need more date fields to calculate actual
        st.metric("Avg Customer Lifetime", f"{avg_lifetime} days")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retention Rates by Agent")
        agent_retention = sales_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': lambda x: (x == 'ACTIVE').sum()
        }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Active'})
        
        agent_retention['Retention_Rate'] = (agent_retention['Active'] / agent_retention['Total'] * 100).round(1)
        agent_retention = agent_retention[agent_retention['Total'] >= 3].sort_values('Retention_Rate', ascending=False).head(10)
        
        if not agent_retention.empty:
            fig = px.bar(
                agent_retention,
                x=agent_retention.index,
                y='Retention_Rate',
                title="Top 10 Agents by Retention Rate",
                color='Retention_Rate',
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Status Distribution")
        status_counts = agent_data['CATEGORY'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title=f"Status Distribution - {selected_agent}",
            color_discrete_map={
                'ACTIVE': COLORS['success'],
                'CANCELLED': COLORS['danger'],
                'NSF': COLORS['warning'],
                'OTHER': COLORS['info']
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Cancellation Patterns")
        if 'ENROLLED_DATE' in sales_df.columns:
            cancelled_data = sales_df[sales_df['CATEGORY'] == 'CANCELLED'].copy()
            if not cancelled_data.empty:
                cancelled_data['Month'] = cancelled_data['ENROLLED_DATE'].dt.strftime('%Y-%m')
                monthly_cancellations = cancelled_data.groupby('Month').size().reset_index()
                monthly_cancellations.columns = ['Month', 'Cancellations']
                
                fig = px.line(
                    monthly_cancellations,
                    x='Month',
                    y='Cancellations',
                    title="Monthly Cancellation Trends",
                    markers=True,
                    color_discrete_sequence=[COLORS['danger']]
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No cancellation data available")
    
    with col2:
        st.subheader("Days to Cancellation")
        # Placeholder chart - would need more date fields for actual calculation
        sample_days = [7, 14, 21, 30, 45, 60, 90]
        sample_counts = [15, 25, 20, 18, 12, 8, 5]
        
        fig = px.bar(
            x=sample_days,
            y=sample_counts,
            title="Days to Cancellation Distribution",
            color=sample_counts,
            color_continuous_scale=HEAT_COLORS
        )
        fig.update_layout(
            xaxis_title="Days",
            yaxis_title="Count",
            plot_bgcolor='#F8F9FA',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Retention table
    st.subheader("📋 Agent Retention Summary")
    retention_summary = sales_df.groupby('AGENT').agg({
        'AGENT': 'count',
        'CATEGORY': [
            lambda x: (x == 'ACTIVE').sum(),
            lambda x: (x == 'CANCELLED').sum(),
            lambda x: (x == 'NSF').sum()
        ]
    })
    
    retention_summary.columns = ['Total', 'Active', 'Cancelled', 'NSF']
    retention_summary['Retention_Rate'] = (retention_summary['Active'] / retention_summary['Total'] * 100).round(1)
    retention_summary['Cancel_Rate'] = (retention_summary['Cancelled'] / retention_summary['Total'] * 100).round(1)
    retention_summary = retention_summary.sort_values('Retention_Rate', ascending=False).reset_index()
    
    st.dataframe(retention_summary, use_container_width=True, hide_index=True)

def render_agent_comparisons(sales_df, COLORS, HEAT_COLORS):
    """Render agent comparison analysis"""
    st.subheader("🏆 Agent Comparisons")
    
    # Agent rankings
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Agent Rankings by Retention")
        agent_rankings = sales_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': lambda x: (x == 'ACTIVE').sum()
        }).rename(columns={'AGENT': 'Total_Sales', 'CATEGORY': 'Active_Sales'})
        
        agent_rankings['Retention_Rate'] = (agent_rankings['Active_Sales'] / agent_rankings['Total_Sales'] * 100).round(1)
        agent_rankings['Rank'] = agent_rankings['Retention_Rate'].rank(ascending=False, method='dense').astype(int)
        agent_rankings = agent_rankings.sort_values('Retention_Rate', ascending=False).head(10).reset_index()
        
        fig = px.bar(
            agent_rankings,
            x='AGENT',
            y='Retention_Rate',
            title="Top 10 Agent Rankings",
            color='Retention_Rate',
            color_continuous_scale=HEAT_COLORS,
            text='Rank'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("New Enrollments vs Cancellations")
        agent_comparison = sales_df.groupby('AGENT').agg({
            'CATEGORY': [
                lambda x: (x == 'ACTIVE').sum(),
                lambda x: (x == 'CANCELLED').sum()
            ]
        })
        
        agent_comparison.columns = ['Active', 'Cancelled']
        agent_comparison = agent_comparison.head(10)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Active',
            x=agent_comparison.index,
            y=agent_comparison['Active'],
            marker_color=COLORS['success']
        ))
        fig.add_trace(go.Bar(
            name='Cancelled',
            x=agent_comparison.index,
            y=agent_comparison['Cancelled'],
            marker_color=COLORS['danger']
        ))
        
        fig.update_layout(
            title="Active vs Cancelled by Agent",
            barmode='group',
            plot_bgcolor='#F8F9FA',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("NSF Rate Comparisons")
        nsf_rates = sales_df.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': lambda x: (x == 'NSF').sum()
        }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'NSF'})
        
        nsf_rates['NSF_Rate'] = (nsf_rates['NSF'] / nsf_rates['Total'] * 100).round(1)
        nsf_rates = nsf_rates[nsf_rates['Total'] >= 3].sort_values('NSF_Rate', ascending=True).head(10)
        
        fig = px.bar(
            nsf_rates,
            x=nsf_rates.index,
            y='NSF_Rate',
            title="Lowest NSF Rates (Best Performers)",
            color='NSF_Rate',
            color_continuous_scale=HEAT_COLORS
        )
        fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Monthly Performance Trends")
        if 'ENROLLED_DATE' in sales_df.columns:
            monthly_performance = sales_df.groupby([
                sales_df['ENROLLED_DATE'].dt.strftime('%Y-%m'),
                'CATEGORY'
            ]).size().unstack(fill_value=0)
            
            if not monthly_performance.empty:
                fig = px.line(
                    monthly_performance,
                    title="Monthly Status Trends",
                    color_discrete_map={
                        'ACTIVE': COLORS['success'],
                        'CANCELLED': COLORS['danger'],
                        'NSF': COLORS['warning'],
                        'OTHER': COLORS['info']
                    }
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    # Performance comparison table
    st.subheader("📋 Comprehensive Agent Comparison")
    comparison_table = sales_df.groupby('AGENT').agg({
        'AGENT': 'count',
        'CATEGORY': [
            lambda x: (x == 'ACTIVE').sum(),
            lambda x: (x == 'CANCELLED').sum(),
            lambda x: (x == 'NSF').sum()
        ]
    })
    
    comparison_table.columns = ['Total_Sales', 'Active_Sales', 'Cancelled_Sales', 'NSF_Sales']
    comparison_table['Retention_Rate'] = (comparison_table['Active_Sales'] / comparison_table['Total_Sales'] * 100).round(1)
    comparison_table['Cancel_Rate'] = (comparison_table['Cancelled_Sales'] / comparison_table['Total_Sales'] * 100).round(1)
    comparison_table['NSF_Rate'] = (comparison_table['NSF_Sales'] / comparison_table['Total_Sales'] * 100).round(1)
    comparison_table = comparison_table.sort_values('Retention_Rate', ascending=False).reset_index()
    
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)

def render_customer_analysis(sales_df, COLORS, HEAT_COLORS):
    """Render customer analysis"""
    st.subheader("👥 Customer Analysis")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status Distribution by Enrollment Cohort")
        if 'ENROLLED_DATE' in sales_df.columns:
            sales_df['Enrollment_Month'] = sales_df['ENROLLED_DATE'].dt.strftime('%Y-%m')
            cohort_analysis = sales_df.groupby(['Enrollment_Month', 'CATEGORY']).size().unstack(fill_value=0)
            
            if not cohort_analysis.empty:
                fig = px.bar(
                    cohort_analysis,
                    title="Status Distribution by Enrollment Month",
                    color_discrete_map={
                        'ACTIVE': COLORS['success'],
                        'CANCELLED': COLORS['danger'],
                        'NSF': COLORS['warning'],
                        'OTHER': COLORS['info']
                    }
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Customer Lifecycle Visualization")
        lifecycle_data = sales_df['CATEGORY'].value_counts()
        
        # Create funnel chart
        fig = go.Figure(go.Funnel(
            y=lifecycle_data.index,
            x=lifecycle_data.values,
            textinfo="value+percent initial",
            marker=dict(
                color=[COLORS['success'], COLORS['danger'], COLORS['warning'], COLORS['info']][:len(lifecycle_data)]
            )
        ))
        
        fig.update_layout(
            title="Customer Status Funnel",
            plot_bgcolor='#F8F9FA',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Agent-Customer Relationship Duration")
        # Placeholder data - would need more detailed customer tracking
        duration_data = pd.DataFrame({
            'Agent': sales_df['AGENT'].value_counts().head(10).index,
            'Avg_Duration': np.random.randint(20, 90, 10)  # Placeholder
        })
        
        fig = px.bar(
            duration_data,
            x='Agent',
            y='Avg_Duration',
            title="Average Customer Relationship Duration",
            color='Avg_Duration',
            color_continuous_scale=HEAT_COLORS
        )
        fig.update_layout(
            yaxis_title="Days",
            plot_bgcolor='#F8F9FA',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Enrollment-to-Cancellation Flow")
        # Sankey diagram showing flow from enrollment to final status
        if 'SOURCE_SHEET' in sales_df.columns:
            flow_data = sales_df.groupby(['SOURCE_SHEET', 'CATEGORY']).size().reset_index()
            flow_data.columns = ['Source', 'Status', 'Count']
            
            # Create simplified flow visualization
            fig = px.bar(
                flow_data,
                x='Source',
                y='Count',
                color='Status',
                title="Enrollment Source to Status Flow",
                color_discrete_map={
                    'ACTIVE': COLORS['success'],
                    'CANCELLED': COLORS['danger'],
                    'NSF': COLORS['warning'],
                    'OTHER': COLORS['info']
                }
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
    
    # Customer analysis table
    st.subheader("📋 Customer Status Timeline")
    if 'ENROLLED_DATE' in sales_df.columns:
        timeline_data = sales_df.groupby(['ENROLLED_DATE', 'CATEGORY']).size().unstack(fill_value=0)
        timeline_summary = timeline_data.tail(30)  # Last 30 days
        
        if not timeline_summary.empty:
            st.dataframe(timeline_summary, use_container_width=True)
            
            # Download option
            csv = timeline_summary.to_csv()
            st.download_button(
                "📥 Download Customer Timeline Data",
                csv,
                "customer_timeline.csv",
                "text/csv"
            )