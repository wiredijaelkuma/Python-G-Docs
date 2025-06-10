# modules/ui_components.py
import streamlit as st
from modules.utils import format_large_number

def create_header(df_filtered, start, end, status_filter, COLORS):
    """Create the dashboard header with filter information"""
    st.markdown(f"""
    <div class="section-header">Pepe's Power Sales Dashboard</div>
    <div style="background-color: {COLORS['light_purple']}; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
            <div>
                <b>Date Range:</b> {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}<br>
                <b>Total Contracts:</b> {format_large_number(len(df_filtered))}
            </div>
            <div>
                <b>Status Shown:</b> {', '.join(status_filter)}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_metrics(df_filtered, COLORS):
    """Display key metrics in cards"""
    # Calculate metrics based on filtered data
    total_contracts = len(df_filtered)
    
    # Only calculate these if CATEGORY exists
    if 'CATEGORY' in df_filtered.columns:
        active_contracts = len(df_filtered[df_filtered['CATEGORY'] == 'ACTIVE'])
        nsf_cases = len(df_filtered[df_filtered['CATEGORY'] == 'NSF'])
        cancelled_contracts = len(df_filtered[df_filtered['CATEGORY'] == 'CANCELLED'])
        other_statuses = len(df_filtered[df_filtered['CATEGORY'] == 'OTHER'])
    else:
        active_contracts = nsf_cases = cancelled_contracts = other_statuses = 0
    
    success_rate = (active_contracts / total_contracts * 100) if total_contracts > 0 else 0

    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Contracts</div>
            <div class="metric-value">{format_large_number(total_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Active</div>
            <div class="metric-value">{format_large_number(active_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">NSF Cases</div>
            <div class="metric-value">{format_large_number(nsf_cases)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Cancelled</div>
            <div class="metric-value">{format_large_number(cancelled_contracts)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Success Rate</div>
            <div class="metric-value">{success_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
