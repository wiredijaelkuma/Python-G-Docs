"""
Simple test script to verify Streamlit secrets are working
"""
import streamlit as st
import json

st.title("Streamlit Secrets Test")

# Check if secrets are available
if hasattr(st, 'secrets'):
    st.success("✅ Streamlit secrets are available")
    
    # Check if Google credentials are available
    if 'gcp_service_account' in st.secrets:
        st.success("✅ Google credentials found in secrets")
        
        # Show available keys (not values)
        creds = st.secrets["gcp_service_account"]
        st.write("Available credential keys:")
        for key in creds:
            st.write(f"- {key}")
            
        # Check required fields
        required_fields = [
            "type", "project_id", "private_key_id", "private_key", 
            "client_email", "client_id", "auth_uri", "token_uri"
        ]
        
        missing = [field for field in required_fields if field not in creds]
        
        if missing:
            st.error(f"❌ Missing required fields: {', '.join(missing)}")
        else:
            st.success("✅ All required credential fields are present")
            
            # Check private key format
            if creds["private_key"].startswith("-----BEGIN PRIVATE KEY-----") and \
               creds["private_key"].endswith("-----END PRIVATE KEY-----\n"):
                st.success("✅ Private key format looks correct")
            else:
                st.error("❌ Private key format is incorrect")
    else:
        st.error("❌ No Google credentials found in secrets")
else:
    st.error("❌ No Streamlit secrets available")

st.write("This app helps verify that your Streamlit secrets are properly configured for Google Sheets integration.")