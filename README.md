# Pepe's Power Dashboard

A comprehensive sales and performance dashboard built with Streamlit.

## Features
- Overview of key metrics
- Performance analytics
- Agent performance tracking
- Drop rate analysis
- Risk analysis
- Interactive data explorer
- **Google Sheets Integration** - Connect directly to Google Sheets for real-time data

## Setup

### Local Development
1. Install requirements: `pip install -r requirements.txt`
2. Make sure you have a valid `credentials.json` file for Google Sheets API
3. Run the app: `streamlit run app.py`

### Streamlit Cloud Deployment
1. Push your code to GitHub (excluding credentials.json)
2. Deploy on Streamlit Cloud
3. Add your Google API credentials to Streamlit Cloud secrets
4. See `GSHEET_SETUP.md` for detailed instructions

## Data Sources

### 1. Local CSV File
Upload a CSV file with the following columns:
- ENROLLED_DATE: Date of enrollment
- STATUS: Contract status
- AGENT: Sales agent name
- And other optional columns for more detailed analysis

### 2. Google Sheets
Connect directly to your "Forth Py" Google Sheet:
1. Select "Google Sheet" as the data source in the app sidebar
2. The app will automatically connect to the sheet using your credentials

## Google Sheet Structure

Your Google Sheet should have the following worksheets:
- PAC
- MLG
- ELP
- Cordoba

Each worksheet should have these columns:
- CUSTOMER ID
- AGENT
- ENROLLED DATE
- STATUS