import streamlit as st

def configure_page():
    """Configure Streamlit page settings for optimal performance"""
    st.set_page_config(
        layout="wide", 
        page_title="Pepe's Power Dashboard", 
        page_icon="🐸",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    # Add custom CSS for better performance
    st.markdown("""
    <style>
    /* Optimize rendering performance */
    .stApp {
        background-color: #F8F9FA;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* Reduce animation overhead */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Try to load custom CSS file if available
    try:
        with open('assets/custom.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        pass