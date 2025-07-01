"""
Comprehensive Commission Analysis Module - 3 Subtabs with 6 Displays Each
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_commission_analysis(df, COLORS, HEAT_COLORS):
    """Complete commission analysis with payment clearance tracking"""
    st.header("💰 Commission Analysis Dashboard")
    
    # Filter commission data
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    
    if commission_df.empty:
        st.warning("No commission data available")
        return
    
    # Payment clearance time selector - RADIO BUTTONS
    clearance_days = st.radio(
        "📅 Payment Clearance Analysis Period:",
        ["7 Days", "14 Days", "30 Days", "90 Days"],
        index=2,
        horizontal=True,
        key="commission_clearance_radio"
    )
    
    # Commission subtabs
    subtabs = st.tabs(["📊 Payment Overview", "⏱️ Processing Analysis", "📈 Performance Metrics"])
    
    with subtabs[0]:
        render_payment_overview(commission_df, clearance_days, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_processing_analysis(commission_df, clearance_days, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        render_performance_metrics(commission_df, clearance_days, COLORS, HEAT_COLORS)

def render_payment_overview(commission_df, clearance_days, COLORS, HEAT_COLORS):
    """Payment overview with 6 displays"""
    st.subheader(f"📊 Payment Overview - {clearance_days} Analysis")
    
    # Calculate clearance period
    days_map = {"7 Days": 7, "14 Days": 14, "30 Days": 30, "90 Days": 90}
    analysis_days = days_map[clearance_days]
    
    # Filter recent payments for analysis
    if 'PROCESSED_DATE' in commission_df.columns:
        cutoff_date = commission_df['PROCESSED_DATE'].max() - timedelta(days=analysis_days)
        recent_payments = commission_df[commission_df['PROCESSED_DATE'] >= cutoff_date]
    else:
        recent_payments = commission_df
    
    # Display 1: Payment metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Payments", len(recent_payments))
    
    with col2:
        if 'CATEGORY' in recent_payments.columns:
            cleared_count = len(recent_payments[recent_payments['CATEGORY'] == 'CLEARED'])
            cleared_rate = (cleared_count / len(recent_payments) * 100) if len(recent_payments) > 0 else 0
            st.metric("Cleared Rate", f"{cleared_rate:.1f}%")
    
    with col3:
        if 'CATEGORY' in recent_payments.columns:
            pending_count = len(recent_payments[recent_payments['CATEGORY'] == 'PENDING'])
            st.metric("Pending Payments", pending_count)
    
    with col4:
        if 'CATEGORY' in recent_payments.columns:
            nsf_count = len(recent_payments[recent_payments['CATEGORY'] == 'NSF'])
            st.metric("NSF Payments", nsf_count)
    
    # Display 2 & 3: Primary charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Payment Status Distribution")
        if 'CATEGORY' in recent_payments.columns:
            status_counts = recent_payments['CATEGORY'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title=f"Payment Status - Last {clearance_days}",
                color_discrete_map={
                    'CLEARED': COLORS['success'],
                    'PENDING': COLORS['warning'],
                    'NSF': COLORS['danger'],
                    'OTHER': COLORS['info']
                }
            )
            st.plotly_chart(fig, use_container_width=True, key="payment_status_pie")
    
    with col2:
        st.subheader("Daily Payment Volume")
        if 'PROCESSED_DATE' in recent_payments.columns:
            daily_payments = recent_payments.groupby(recent_payments['PROCESSED_DATE'].dt.date).size().reset_index()
            daily_payments.columns = ['Date', 'Payments']
            
            if not daily_payments.empty:
                fig = px.bar(
                    daily_payments,
                    x='Date',
                    y='Payments',
                    title=f"Daily Payment Volume - Last {clearance_days}",
                    color='Payments',
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="daily_payment_volume")
    
    # Display 4 & 5: Additional analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Agent Payment Performance")
        if 'AGENT' in recent_payments.columns:
            agent_payments = recent_payments['AGENT'].value_counts().head(10)
            
            fig = px.bar(
                x=agent_payments.index,
                y=agent_payments.values,
                title="Top 10 Agents by Payment Volume",
                color=agent_payments.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key="agent_payment_volume")
    
    with col2:
        st.subheader("Payment Success by Agent")
        if 'AGENT' in recent_payments.columns and 'CATEGORY' in recent_payments.columns:
            agent_success = recent_payments.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'CLEARED').sum()
            }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Cleared'})
            
            agent_success['Success_Rate'] = (agent_success['Cleared'] / agent_success['Total'] * 100).round(1)
            agent_success = agent_success[agent_success['Total'] >= 3].sort_values('Success_Rate', ascending=False).head(10)
            
            if not agent_success.empty:
                fig = px.bar(
                    agent_success,
                    x=agent_success.index,
                    y='Success_Rate',
                    title="Top Agents by Success Rate",
                    color='Success_Rate',
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="agent_success_rate")
    
    # Display 6: Payment summary table
    st.subheader("📋 Payment Summary")
    if 'AGENT' in recent_payments.columns and 'CATEGORY' in recent_payments.columns:
        payment_summary = recent_payments.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'CLEARED').sum(),
                lambda x: (x == 'PENDING').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        payment_summary.columns = ['Total_Payments', 'Cleared', 'Pending', 'NSF']
        payment_summary['Success_Rate'] = (payment_summary['Cleared'] / payment_summary['Total_Payments'] * 100).round(1)
        payment_summary = payment_summary.sort_values('Success_Rate', ascending=False).head(15).reset_index()
        
        st.dataframe(payment_summary, use_container_width=True, hide_index=True)

def render_processing_analysis(commission_df, clearance_days, COLORS, HEAT_COLORS):
    """Processing analysis with 6 displays"""
    st.subheader(f"⏱️ Processing Analysis - {clearance_days} Focus")
    
    # Calculate processing times
    if 'PROCESSED_DATE' in commission_df.columns and 'CLEARED_DATE' in commission_df.columns:
        cleared_payments = commission_df[
            (commission_df['CATEGORY'] == 'CLEARED') & 
            commission_df['PROCESSED_DATE'].notna() & 
            commission_df['CLEARED_DATE'].notna()
        ].copy()
        
        if not cleared_payments.empty:
            cleared_payments['Processing_Days'] = (cleared_payments['CLEARED_DATE'] - cleared_payments['PROCESSED_DATE']).dt.days
    else:
        cleared_payments = pd.DataFrame()
    
    # Display 1: Processing metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not cleared_payments.empty:
            avg_processing = cleared_payments['Processing_Days'].mean()
            st.metric("Avg Processing Time", f"{avg_processing:.1f} days")
        else:
            st.metric("Avg Processing Time", "N/A")
    
    with col2:
        if not cleared_payments.empty:
            fast_payments = len(cleared_payments[cleared_payments['Processing_Days'] <= 7])
            fast_rate = (fast_payments / len(cleared_payments) * 100) if len(cleared_payments) > 0 else 0
            st.metric("Fast Processing", f"{fast_rate:.1f}%")
        else:
            st.metric("Fast Processing", "N/A")
    
    with col3:
        if not cleared_payments.empty:
            slow_payments = len(cleared_payments[cleared_payments['Processing_Days'] > 30])
            st.metric("Slow Payments (>30d)", slow_payments)
        else:
            st.metric("Slow Payments", "N/A")
    
    with col4:
        if not cleared_payments.empty:
            median_processing = cleared_payments['Processing_Days'].median()
            st.metric("Median Processing", f"{median_processing:.1f} days")
        else:
            st.metric("Median Processing", "N/A")
    
    # Display 2 & 3: Processing charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Processing Time Distribution")
        if not cleared_payments.empty:
            fig = px.histogram(
                cleared_payments,
                x='Processing_Days',
                title="Payment Processing Time Distribution",
                nbins=20,
                color_discrete_sequence=[COLORS['primary']]
            )
            fig.update_layout(
                xaxis_title="Processing Days",
                yaxis_title="Count",
                plot_bgcolor='#F8F9FA',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True, key="processing_histogram")
        else:
            st.info("No processing time data available")
    
    with col2:
        st.subheader("Processing Speed Categories")
        if not cleared_payments.empty:
            # Categorize processing speeds
            speed_categories = pd.cut(
                cleared_payments['Processing_Days'],
                bins=[0, 7, 14, 30, float('inf')],
                labels=['Fast (≤7d)', 'Normal (8-14d)', 'Slow (15-30d)', 'Very Slow (>30d)']
            )
            speed_counts = speed_categories.value_counts()
            
            fig = px.bar(
                x=speed_counts.index,
                y=speed_counts.values,
                title="Processing Speed Categories",
                color=speed_counts.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key="processing_categories")
        else:
            st.info("No processing speed data available")
    
    # Display 4 & 5: Agent processing analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Agent Processing Performance")
        if not cleared_payments.empty and 'AGENT' in cleared_payments.columns:
            agent_processing = cleared_payments.groupby('AGENT')['Processing_Days'].mean().sort_values().head(10)
            
            fig = px.bar(
                x=agent_processing.index,
                y=agent_processing.values,
                title="Fastest Processing Agents (Avg Days)",
                color=agent_processing.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(
                yaxis_title="Average Days",
                plot_bgcolor='#F8F9FA',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True, key="agent_processing_speed")
        else:
            st.info("No agent processing data available")
    
    with col2:
        st.subheader("Monthly Processing Trends")
        if not cleared_payments.empty and 'CLEARED_DATE' in cleared_payments.columns:
            monthly_processing = cleared_payments.groupby(
                cleared_payments['CLEARED_DATE'].dt.strftime('%Y-%m')
            )['Processing_Days'].mean().reset_index()
            monthly_processing.columns = ['Month', 'Avg_Days']
            
            if not monthly_processing.empty:
                fig = px.line(
                    monthly_processing,
                    x='Month',
                    y='Avg_Days',
                    title="Monthly Processing Time Trends",
                    markers=True,
                    color_discrete_sequence=[COLORS['secondary']]
                )
                fig.update_layout(
                    yaxis_title="Average Processing Days",
                    plot_bgcolor='#F8F9FA',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True, key="monthly_processing_trend")
        else:
            st.info("No monthly processing data available")
    
    # Display 6: Processing details table
    with st.expander("📋 Detailed Processing Analysis"):
        if not cleared_payments.empty:
            processing_details = cleared_payments[['AGENT', 'PROCESSED_DATE', 'CLEARED_DATE', 'Processing_Days']].copy()
            processing_details['PROCESSED_DATE'] = processing_details['PROCESSED_DATE'].dt.strftime('%Y-%m-%d')
            processing_details['CLEARED_DATE'] = processing_details['CLEARED_DATE'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(processing_details, use_container_width=True, hide_index=True)
            
            csv = processing_details.to_csv(index=False)
            st.download_button(
                "📥 Download Processing Data",
                csv,
                "processing_analysis.csv",
                "text/csv"
            )
        else:
            st.info("No processing data available for export")

def render_performance_metrics(commission_df, clearance_days, COLORS, HEAT_COLORS):
    """Performance metrics with 6 displays"""
    st.subheader(f"📈 Performance Metrics - {clearance_days} Analysis")
    
    # Calculate performance period
    days_map = {"7 Days": 7, "14 Days": 14, "30 Days": 30, "90 Days": 90}
    analysis_days = days_map[clearance_days]
    
    if 'PROCESSED_DATE' in commission_df.columns:
        cutoff_date = commission_df['PROCESSED_DATE'].max() - timedelta(days=analysis_days)
        performance_data = commission_df[commission_df['PROCESSED_DATE'] >= cutoff_date]
    else:
        performance_data = commission_df
    
    # Display 1: Performance KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'CATEGORY' in performance_data.columns:
            success_rate = (len(performance_data[performance_data['CATEGORY'] == 'CLEARED']) / len(performance_data) * 100) if len(performance_data) > 0 else 0
            st.metric("Overall Success Rate", f"{success_rate:.1f}%")
    
    with col2:
        if 'CATEGORY' in performance_data.columns:
            nsf_rate = (len(performance_data[performance_data['CATEGORY'] == 'NSF']) / len(performance_data) * 100) if len(performance_data) > 0 else 0
            st.metric("NSF Rate", f"{nsf_rate:.1f}%")
    
    with col3:
        if 'AGENT' in performance_data.columns:
            active_agents = performance_data['AGENT'].nunique()
            st.metric("Active Agents", active_agents)
    
    with col4:
        daily_avg = len(performance_data) / analysis_days if analysis_days > 0 else 0
        st.metric("Daily Avg Payments", f"{daily_avg:.1f}")
    
    # Display 2 & 3: Performance trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Success Rate Trends")
        if 'PROCESSED_DATE' in performance_data.columns and 'CATEGORY' in performance_data.columns:
            daily_success = performance_data.groupby(performance_data['PROCESSED_DATE'].dt.date).agg({
                'CATEGORY': ['count', lambda x: (x == 'CLEARED').sum()]
            })
            daily_success.columns = ['Total', 'Cleared']
            daily_success['Success_Rate'] = (daily_success['Cleared'] / daily_success['Total'] * 100).round(1)
            daily_success = daily_success.reset_index()
            
            if not daily_success.empty:
                fig = px.line(
                    daily_success,
                    x='PROCESSED_DATE',
                    y='Success_Rate',
                    title="Daily Success Rate Trends",
                    markers=True,
                    color_discrete_sequence=[COLORS['success']]
                )
                fig.update_layout(
                    yaxis_title="Success Rate (%)",
                    plot_bgcolor='#F8F9FA',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True, key="success_rate_trend")
    
    with col2:
        st.subheader("Volume vs Success Correlation")
        if 'AGENT' in performance_data.columns and 'CATEGORY' in performance_data.columns:
            agent_metrics = performance_data.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'CLEARED').sum()
            }).rename(columns={'AGENT': 'Volume', 'CATEGORY': 'Cleared'})
            
            agent_metrics['Success_Rate'] = (agent_metrics['Cleared'] / agent_metrics['Volume'] * 100).round(1)
            agent_metrics = agent_metrics[agent_metrics['Volume'] >= 3]
            
            if not agent_metrics.empty:
                fig = px.scatter(
                    agent_metrics,
                    x='Volume',
                    y='Success_Rate',
                    size='Cleared',
                    title="Volume vs Success Rate by Agent",
                    color='Success_Rate',
                    color_continuous_scale=HEAT_COLORS,
                    hover_name=agent_metrics.index
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="volume_success_scatter")
    
    # Display 4 & 5: Advanced metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Performance Ranking")
        if 'AGENT' in performance_data.columns and 'CATEGORY' in performance_data.columns:
            ranking = performance_data.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': [
                    lambda x: (x == 'CLEARED').sum(),
                    lambda x: (x == 'NSF').sum()
                ]
            })
            ranking.columns = ['Total', 'Cleared', 'NSF']
            ranking['Performance_Score'] = (ranking['Cleared'] * 2 - ranking['NSF']).clip(lower=0)
            ranking = ranking[ranking['Total'] >= 3].sort_values('Performance_Score', ascending=False).head(10)
            
            if not ranking.empty:
                fig = px.bar(
                    ranking,
                    x=ranking.index,
                    y='Performance_Score',
                    title="Top 10 Performance Scores",
                    color='Performance_Score',
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="performance_ranking")
    
    with col2:
        st.subheader("Risk Analysis")
        if 'CATEGORY' in performance_data.columns:
            risk_data = pd.DataFrame({
                'Risk_Level': ['Low Risk (Cleared)', 'Medium Risk (Pending)', 'High Risk (NSF)'],
                'Count': [
                    len(performance_data[performance_data['CATEGORY'] == 'CLEARED']),
                    len(performance_data[performance_data['CATEGORY'] == 'PENDING']),
                    len(performance_data[performance_data['CATEGORY'] == 'NSF'])
                ]
            })
            
            fig = px.pie(
                risk_data,
                values='Count',
                names='Risk_Level',
                title="Payment Risk Distribution",
                color_discrete_map={
                    'Low Risk (Cleared)': COLORS['success'],
                    'Medium Risk (Pending)': COLORS['warning'],
                    'High Risk (NSF)': COLORS['danger']
                }
            )
            st.plotly_chart(fig, use_container_width=True, key="risk_analysis_pie")
    
    # Display 6: Comprehensive metrics table
    st.subheader("📋 Comprehensive Performance Metrics")
    if 'AGENT' in performance_data.columns and 'CATEGORY' in performance_data.columns:
        comprehensive_metrics = performance_data.groupby('AGENT').agg({
            'AGENT': 'count',
            'CATEGORY': [
                lambda x: (x == 'CLEARED').sum(),
                lambda x: (x == 'PENDING').sum(),
                lambda x: (x == 'NSF').sum()
            ]
        })
        
        comprehensive_metrics.columns = ['Total_Payments', 'Cleared', 'Pending', 'NSF']
        comprehensive_metrics['Success_Rate'] = (comprehensive_metrics['Cleared'] / comprehensive_metrics['Total_Payments'] * 100).round(1)
        comprehensive_metrics['NSF_Rate'] = (comprehensive_metrics['NSF'] / comprehensive_metrics['Total_Payments'] * 100).round(1)
        comprehensive_metrics['Risk_Score'] = (comprehensive_metrics['NSF_Rate'] * 2 + (100 - comprehensive_metrics['Success_Rate'])).round(1)
        comprehensive_metrics = comprehensive_metrics.sort_values('Success_Rate', ascending=False).reset_index()
        
        st.dataframe(comprehensive_metrics, use_container_width=True, hide_index=True)
        
        # Export option
        csv = comprehensive_metrics.to_csv(index=False)
        st.download_button(
            f"📥 Download Performance Metrics ({clearance_days})",
            csv,
            f"performance_metrics_{clearance_days.lower().replace(' ', '_')}.csv",
            "text/csv"
        )