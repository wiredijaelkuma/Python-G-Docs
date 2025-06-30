# Pepe's Power Dashboard

A comprehensive sales and performance dashboard built with Streamlit.

## Features
- Overview of key metrics
- Performance analytics
- Agent performance tracking
- Drop rate analysis
- Risk analysis
- Interactive data explorer
- Google Sheets Integration - Connects directly to "Forth Py" Google Sheet

## Setup

### Local Development
1. Install requirements: `pip install -r requirements.txt`
2. Make sure you have a valid `credentials.json` file for Google Sheets API
3. Run the app: `streamlit run app.py`

### Streamlit Cloud Deployment
1. Push your code to GitHub (excluding credentials.json)
2. Deploy on Streamlit Cloud
3. Add your Google API credentials to Streamlit Cloud secrets in this format:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour private key content with \n for line breaks\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

## Google Sheet Structure

The app connects to the "Forth Py" Google Sheet with these worksheets:
- PAC
- MLG
- ELP
- Cordoba
- Comission

Enrollment worksheets (PAC, MLG, ELP, Cordoba) should have these columns:
- CUSTOMER ID
- AGENT
- ENROLLED DATE
- STATUS

The Comission worksheet should have these columns:
- Customer ID
- Agent
- Transaction Id
- Status
- Processed Date
- Cleared Date