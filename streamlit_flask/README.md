# Pepe's Power Dashboard with Flask API

This is a hybrid Streamlit-Flask application that provides both a web dashboard and an API for accessing the data.

## Features

- **Streamlit Dashboard**: Interactive web interface with filters, charts, and data exploration
- **Flask API**: REST API endpoint for accessing the filtered data
- **Real-time Data Sync**: API data is updated whenever filters are changed in the dashboard
- **CSV Data Source**: Reads data from the CSV file in the parent directory
- **Downloadable Data**: Export filtered data as CSV

## How to Run

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the app:
   ```
   streamlit run app.py
   ```

3. Access the dashboard at http://localhost:8501
4. Access the API at http://localhost:8080/api/data

## Deployment on Streamlit Cloud

This app is designed to be deployed on Streamlit Cloud:

1. Push this directory to your GitHub repository
2. In Streamlit Cloud, set the main file path to `streamlit_flask/app.py`
3. The Flask API will run in the same process as the Streamlit app

## API Documentation

The API provides access to the filtered data in JSON format:

```json
{
  "metrics": {
    "total": 100,
    "active": 75,
    "nsf": 15,
    "cancelled": 10
  },
  "status_counts": {
    "ACTIVE": 75,
    "NSF": 15,
    "CANCELLED": 10
  },
  "monthly_data": {
    "2024-01": {
      "ACTIVE": 25,
      "NSF": 5,
      "CANCELLED": 3
    },
    "2024-02": {
      "ACTIVE": 50,
      "NSF": 10,
      "CANCELLED": 7
    }
  },
  "data": [
    {
      "CUSTOMER_ID": "123",
      "AGENT": "John",
      "ENROLLED_DATE": "2024-01-15",
      "STATUS": "ACTIVE",
      "CATEGORY": "ACTIVE"
    },
    ...
  ]
}
```