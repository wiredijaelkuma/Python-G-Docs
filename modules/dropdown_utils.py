"""
Dropdown Utilities Module - Fixed dropdown components
"""
import streamlit as st

def create_selectbox(label, options, default_index=0, key=None):
    """Create a properly functioning selectbox with visible text"""
    
    # Ensure options is a list
    if not isinstance(options, list):
        options = list(options)
    
    # Create selectbox with explicit parameters
    selected = st.selectbox(
        label=label,
        options=options,
        index=default_index,
        key=key,
        help=f"Select from {len(options)} options"
    )
    
    return selected

def create_time_range_selector(key_suffix=""):
    """Create standardized time range selector"""
    time_options = ["Last 30 Days", "Last 60 Days", "Last 90 Days", "Last 180 Days"]
    
    return create_selectbox(
        label="📅 Select Time Range:",
        options=time_options,
        default_index=2,  # Default to "Last 90 Days"
        key=f"time_range_{key_suffix}"
    )

def create_agent_selector(agents_list, key_suffix=""):
    """Create standardized agent selector"""
    if len(agents_list) == 0:
        return "All Agents"
    
    options = ["All Agents"] + sorted(list(agents_list))
    
    return create_selectbox(
        label="👤 Select Agent:",
        options=options,
        default_index=0,
        key=f"agent_selector_{key_suffix}"
    )