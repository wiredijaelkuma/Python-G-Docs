# Google Sheets Integration for Streamlit Cloud

This document explains how to set up the Google Sheets integration for your Streamlit dashboard when deploying to Streamlit Cloud.

## Streamlit Cloud Setup

### 1. Prepare Your Repository

1. Make sure your GitHub repository includes:
   - All application code
   - `requirements.txt` with all dependencies
   - `.streamlit` folder with any configuration

2. **DO NOT include your `credentials.json` file in the repository**

### 2. Set Up Streamlit Cloud Secrets

1. In Streamlit Cloud, navigate to your app settings
2. Find the "Secrets" section
3. Add your Google API credentials as a secret in the following format:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour private key content here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
```

4. Copy the content from your local `credentials.json` file into this format

### 3. Update Your Code for Streamlit Cloud

Add the following code to your `gsheet_connector.py` file to handle Streamlit Cloud secrets:

```python
def get_credentials():
    """Get credentials from local file or Streamlit secrets"""
    import json
    import os
    
    # Check if running on Streamlit Cloud
    if 'STREAMLIT_SHARING_MODE' in os.environ or 'STREAMLIT_APP_ID' in os.environ:
        # Use Streamlit secrets
        import streamlit as st
        return st.secrets["gcp_service_account"]
    else:
        # Use local credentials file
        with open('credentials.json', 'r') as f:
            return json.load(f)
```

### 4. Share Your Google Sheet

1. Share your Google Sheet with the service account email address (found in your credentials.json file)
2. Give it "Editor" access

## Testing Locally vs. Cloud

- **Local testing**: Will use your local `credentials.json` file
- **Streamlit Cloud**: Will use the secrets you configured in Streamlit Cloud

## Troubleshooting

If you encounter issues:

1. Check that your Google Sheet is shared with the service account email
2. Verify that all required secrets are properly configured in Streamlit Cloud
3. Check the Streamlit Cloud logs for specific error messages