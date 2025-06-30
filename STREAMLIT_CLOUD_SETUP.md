# Streamlit Cloud Deployment Guide

## 1. Push to GitHub

Push your code to GitHub, making sure to exclude:
- credentials.json
- .streamlit/secrets.toml

## 2. Set Up Streamlit Cloud Secrets

1. In Streamlit Cloud, go to your app settings
2. Find the "Secrets" section
3. Add your credentials in TOML format like this:

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
```

4. The values should come from your credentials.json file, but formatted as TOML
5. Make sure all string values are in quotes

## 3. Deploy Your App

1. Connect your GitHub repository to Streamlit Cloud
2. Select the main branch and app.py as the entry point
3. Deploy!

## 4. Verify Google Sheets Connection

1. Open your deployed app
2. Select "Google Sheet" as the data source
3. The app should automatically connect to your "Forth Py" Google Sheet

## Troubleshooting

If you encounter connection issues:
1. Check that the secrets are properly configured
2. Verify that your Google Sheet is still shared with the service account email
3. Check the Streamlit Cloud logs for error messages