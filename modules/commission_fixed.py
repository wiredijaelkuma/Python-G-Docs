"""
Fixed Commission Analysis with Proper Transaction ID Handling
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_commission_analysis(df, COLORS, HEAT_COLORS):
    """Complete commission analysis with proper transaction ID handling"""
    st.header("💰 Commission Analysis Dashboard")
    
    # Filter commission data
    commission_df = df[df['SOURCE_SHEET'] == 'Comission'].copy() if 'SOURCE_SHEET' in df.columns else pd.DataFrame()
    
    if commission_df.empty:
        st.warning("No commission data available")
        return
    
    # Debug: Show column names
    st.write("**Available Columns:**", list(commission_df.columns))
    
    # Payment clearance time selector - RADIO BUTTONS
    clearance_days = st.radio(
        "📅 Payment Clearance Analysis Period:",
        ["7 Days", "14 Days", "30 Days", "90 Days"],
        index=2,
        horizontal=True,
        key="commission_clearance_radio"
    )
    
    # Commission Payout Section
    st.subheader(f"💳 Commission Payout Report - Last {clearance_days}")
    
    # Calculate payout period
    days_map = {"7 Days": 7, "14 Days": 14, "30 Days": 30, "90 Days": 90}
    payout_days = days_map[clearance_days]
    
    # Find the correct date and ID columns
    date_cols = [col for col in commission_df.columns if 'DATE' in col.upper()]
    id_cols = [col for col in commission_df.columns if any(x in col.upper() for x in ['ID', 'TRANSACTION', 'CUSTOMER'])]
    
    st.write("**Date Columns Found:**", date_cols)
    st.write("**ID Columns Found:**", id_cols)
    
    # Use the most appropriate date column for filtering
    date_col = None
    if 'CLEARED_DATE' in commission_df.columns:
        date_col = 'CLEARED_DATE'
    elif 'PROCESSED_DATE' in commission_df.columns:
        date_col = 'PROCESSED_DATE'
    elif date_cols:
        date_col = date_cols[0]
    
    # Use the most appropriate ID column
    id_col = None
    if 'TRANSACTION_ID' in commission_df.columns:
        id_col = 'TRANSACTION_ID'
    elif 'CUSTOMER_ID' in commission_df.columns:
        id_col = 'CUSTOMER_ID'
    elif id_cols:
        id_col = id_cols[0]
    
    st.write(f"**Using Date Column:** {date_col}")
    st.write(f"**Using ID Column:** {id_col}")
    
    # Filter cleared payments
    if date_col and date_col in commission_df.columns and 'CATEGORY' in commission_df.columns:
        # Convert date column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(commission_df[date_col]):
            commission_df[date_col] = pd.to_datetime(commission_df[date_col], errors='coerce')
        
        cutoff_date = commission_df[date_col].max() - timedelta(days=payout_days)
        cleared_payments = commission_df[
            (commission_df['CATEGORY'] == 'CLEARED') & 
            (commission_df[date_col] >= cutoff_date) &
            commission_df[date_col].notna()
        ].copy()
        
        if not cleared_payments.empty:
            # Commission payout summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Cleared Payments", len(cleared_payments))
            
            with col2:
                unique_agents = cleared_payments['AGENT'].nunique() if 'AGENT' in cleared_payments.columns else 0
                st.metric("Agents Eligible for Payout", unique_agents)
            
            with col3:
                if id_col and id_col in cleared_payments.columns:
                    unique_transactions = cleared_payments[id_col].nunique()
                    st.metric("Unique Transactions", unique_transactions)
                else:
                    st.metric("Total Records", len(cleared_payments))
            
            # Agent payout breakdown
            st.subheader("📋 Agent Commission Breakdown")
            
            if 'AGENT' in cleared_payments.columns:
                # Create payout summary by agent
                if id_col and id_col in cleared_payments.columns:
                    payout_summary = cleared_payments.groupby('AGENT').agg({
                        id_col: ['count', 'nunique'],
                        date_col: ['min', 'max']
                    })
                    payout_summary.columns = ['Total_Records', 'Unique_Transactions', 'First_Payment', 'Last_Payment']
                else:
                    payout_summary = cleared_payments.groupby('AGENT').agg({
                        'AGENT': 'count',
                        date_col: ['min', 'max']
                    })
                    payout_summary.columns = ['Total_Records', 'First_Payment', 'Last_Payment']
                    payout_summary['Unique_Transactions'] = payout_summary['Total_Records']
                
                # Format dates
                payout_summary['First_Payment'] = payout_summary['First_Payment'].dt.strftime('%Y-%m-%d')
                payout_summary['Last_Payment'] = payout_summary['Last_Payment'].dt.strftime('%Y-%m-%d')
                
                # Sort by transaction count
                payout_summary = payout_summary.sort_values('Unique_Transactions', ascending=False).reset_index()
                
                # Display payout table
                st.dataframe(payout_summary, use_container_width=True, hide_index=True)
                
                # Detailed transaction list
                with st.expander("📄 Detailed Transaction List for Payout"):
                    if id_col and id_col in cleared_payments.columns:
                        # Show available columns for transaction details
                        detail_cols = ['AGENT', id_col, date_col]
                        if 'STATUS' in cleared_payments.columns:
                            detail_cols.append('STATUS')
                        
                        available_detail_cols = [col for col in detail_cols if col in cleared_payments.columns]
                        
                        if available_detail_cols:
                            transaction_details = cleared_payments[available_detail_cols].copy()
                            
                            # Format date column
                            if date_col in transaction_details.columns:
                                transaction_details[date_col] = transaction_details[date_col].dt.strftime('%Y-%m-%d')
                            
                            transaction_details = transaction_details.sort_values(['AGENT', date_col] if date_col in transaction_details.columns else ['AGENT'])
                            
                            st.dataframe(transaction_details, use_container_width=True, hide_index=True)
                            
                            # Download payout data
                            csv = transaction_details.to_csv(index=False)
                            st.download_button(
                                f"📥 Download Payout Report ({clearance_days})",
                                csv,
                                f"commission_payout_{clearance_days.lower().replace(' ', '_')}.csv",
                                "text/csv"
                            )
                        else:
                            st.warning("No suitable columns found for transaction details")
                    else:
                        st.info(f"Transaction ID column ({id_col}) not available for detailed breakdown")
                        
                        # Show basic agent summary instead
                        basic_summary = cleared_payments.groupby('AGENT').size().reset_index()
                        basic_summary.columns = ['AGENT', 'Payment_Count']
                        st.dataframe(basic_summary, use_container_width=True, hide_index=True)
            else:
                st.warning("Agent information not available")
        else:
            st.info(f"No cleared payments found in the last {clearance_days}")
    else:
        st.warning("Date or category information not available for payout analysis")
        
        # Show sample of commission data for debugging
        st.subheader("📋 Commission Data Sample (First 10 Rows)")
        st.dataframe(commission_df.head(10), use_container_width=True)
    
    st.divider()
    
    # Commission subtabs
    subtabs = st.tabs(["📊 Payment Overview", "⏱️ Processing Analysis", "📈 Performance Metrics"])
    
    with subtabs[0]:
        render_payment_overview(commission_df, clearance_days, date_col, id_col, COLORS, HEAT_COLORS)
    
    with subtabs[1]:
        render_processing_analysis(commission_df, clearance_days, date_col, COLORS, HEAT_COLORS)
    
    with subtabs[2]:
        render_performance_metrics(commission_df, clearance_days, date_col, COLORS, HEAT_COLORS)

def render_payment_overview(commission_df, clearance_days, date_col, id_col, COLORS, HEAT_COLORS):
    """Payment overview with proper column handling"""
    st.subheader(f"📊 Payment Overview - {clearance_days} Analysis")
    
    if commission_df.empty:
        st.warning("No commission data available")
        return
    
    # Calculate clearance period
    days_map = {"7 Days": 7, "14 Days": 14, "30 Days": 30, "90 Days": 90}
    analysis_days = days_map[clearance_days]
    
    # Filter recent payments for analysis
    if date_col and date_col in commission_df.columns:
        cutoff_date = commission_df[date_col].max() - timedelta(days=analysis_days)
        recent_payments = commission_df[commission_df[date_col] >= cutoff_date]
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
            st.plotly_chart(fig, use_container_width=True, key="payment_status_pie_overview")
    
    with col2:
        st.subheader("Agent Payment Volume")
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
            st.plotly_chart(fig, use_container_width=True, key="agent_payment_volume_overview")
    
    # Display 4 & 5: Additional analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Daily Payment Volume")
        if date_col and date_col in recent_payments.columns:
            daily_payments = recent_payments.groupby(recent_payments[date_col].dt.date).size().reset_index()
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
                st.plotly_chart(fig, use_container_width=True, key="daily_payment_volume_overview")
        else:
            st.info("Date information not available for daily analysis")
    
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
                st.plotly_chart(fig, use_container_width=True, key="agent_success_rate_overview")
        else:
            st.info("Agent or category information not available")
    
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

def render_processing_analysis(commission_df, clearance_days, date_col, COLORS, HEAT_COLORS):
    """Processing analysis with proper date handling"""
    st.subheader(f"⏱️ Processing Analysis - {clearance_days} Focus")
    
    # Simple processing metrics based on available data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'CATEGORY' in commission_df.columns:
            total_processed = len(commission_df)
            st.metric("Total Processed", total_processed)
    
    with col2:
        if 'CATEGORY' in commission_df.columns:
            cleared_count = len(commission_df[commission_df['CATEGORY'] == 'CLEARED'])
            st.metric("Successfully Cleared", cleared_count)
    
    with col3:
        if 'CATEGORY' in commission_df.columns:
            pending_count = len(commission_df[commission_df['CATEGORY'] == 'PENDING'])
            st.metric("Still Pending", pending_count)
    
    with col4:
        if 'CATEGORY' in commission_df.columns:
            nsf_count = len(commission_df[commission_df['CATEGORY'] == 'NSF'])
            st.metric("Failed (NSF)", nsf_count)
    
    # Processing charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Processing Status Overview")
        if 'CATEGORY' in commission_df.columns:
            status_counts = commission_df['CATEGORY'].value_counts()
            
            fig = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title="Processing Status Distribution",
                color=status_counts.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key="processing_status_bar")
    
    with col2:
        st.subheader("Agent Processing Volume")
        if 'AGENT' in commission_df.columns:
            agent_volume = commission_df['AGENT'].value_counts().head(10)
            
            fig = px.bar(
                x=agent_volume.index,
                y=agent_volume.values,
                title="Top 10 Agents by Processing Volume",
                color=agent_volume.values,
                color_continuous_scale=HEAT_COLORS
            )
            fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True, key="agent_processing_volume")
    
    # Processing details table
    st.subheader("📋 Processing Details")
    if not commission_df.empty:
        # Show available columns for processing analysis
        display_cols = ['AGENT', 'STATUS', 'CATEGORY']
        if date_col:
            display_cols.append(date_col)
        
        available_cols = [col for col in display_cols if col in commission_df.columns]
        
        if available_cols:
            processing_details = commission_df[available_cols].copy()
            
            # Format date if available
            if date_col and date_col in processing_details.columns:
                processing_details[date_col] = processing_details[date_col].dt.strftime('%Y-%m-%d')
            
            st.dataframe(processing_details.head(20), use_container_width=True, hide_index=True)
            
            csv = processing_details.to_csv(index=False)
            st.download_button(
                "📥 Download Processing Data",
                csv,
                "processing_analysis.csv",
                "text/csv"
            )

def render_performance_metrics(commission_df, clearance_days, date_col, COLORS, HEAT_COLORS):
    """Performance metrics with proper data handling"""
    st.subheader(f"📈 Performance Metrics - {clearance_days} Analysis")
    
    # Performance KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'CATEGORY' in commission_df.columns:
            success_rate = (len(commission_df[commission_df['CATEGORY'] == 'CLEARED']) / len(commission_df) * 100) if len(commission_df) > 0 else 0
            st.metric("Overall Success Rate", f"{success_rate:.1f}%")
    
    with col2:
        if 'CATEGORY' in commission_df.columns:
            nsf_rate = (len(commission_df[commission_df['CATEGORY'] == 'NSF']) / len(commission_df) * 100) if len(commission_df) > 0 else 0
            st.metric("NSF Rate", f"{nsf_rate:.1f}%")
    
    with col3:
        if 'AGENT' in commission_df.columns:
            active_agents = commission_df['AGENT'].nunique()
            st.metric("Active Agents", active_agents)
    
    with col4:
        avg_per_agent = len(commission_df) / commission_df['AGENT'].nunique() if 'AGENT' in commission_df.columns and commission_df['AGENT'].nunique() > 0 else 0
        st.metric("Avg per Agent", f"{avg_per_agent:.1f}")
    
    # Performance charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Agent Performance Ranking")
        if 'AGENT' in commission_df.columns and 'CATEGORY' in commission_df.columns:
            agent_performance = commission_df.groupby('AGENT').agg({
                'AGENT': 'count',
                'CATEGORY': lambda x: (x == 'CLEARED').sum()
            }).rename(columns={'AGENT': 'Total', 'CATEGORY': 'Cleared'})
            
            agent_performance['Success_Rate'] = (agent_performance['Cleared'] / agent_performance['Total'] * 100).round(1)
            agent_performance = agent_performance[agent_performance['Total'] >= 3].sort_values('Success_Rate', ascending=False).head(10)
            
            if not agent_performance.empty:
                fig = px.bar(
                    agent_performance,
                    x=agent_performance.index,
                    y='Success_Rate',
                    title="Top 10 Agent Performance",
                    color='Success_Rate',
                    color_continuous_scale=HEAT_COLORS
                )
                fig.update_layout(plot_bgcolor='#F8F9FA', paper_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True, key="agent_performance_ranking")
    
    with col2:
        st.subheader("Risk Analysis")
        if 'CATEGORY' in commission_df.columns:
            risk_data = pd.DataFrame({
                'Risk_Level': ['Low Risk (Cleared)', 'Medium Risk (Pending)', 'High Risk (NSF)'],
                'Count': [
                    len(commission_df[commission_df['CATEGORY'] == 'CLEARED']),
                    len(commission_df[commission_df['CATEGORY'] == 'PENDING']),
                    len(commission_df[commission_df['CATEGORY'] == 'NSF'])
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
            st.plotly_chart(fig, use_container_width=True, key="risk_analysis_pie_metrics")
    
    # Comprehensive metrics table
    st.subheader("📋 Comprehensive Performance Metrics")
    if 'AGENT' in commission_df.columns and 'CATEGORY' in commission_df.columns:
        comprehensive_metrics = commission_df.groupby('AGENT').agg({
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