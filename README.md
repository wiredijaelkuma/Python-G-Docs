# Pepe's Power Dashboard

A Streamlit dashboard for visualizing and analyzing sales data from Google Sheets.

## Features

- Real-time data synchronization with Google Sheets
- Interactive visualizations and filters
- Performance metrics and KPIs
- Agent performance tracking
- Risk analysis

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure Google Sheets API:
   - Place your `credentials.json` file in the root directory
   - Update sheet names in `sheet_analyzer.py` if needed

3. Run the data fetcher:
   ```
   python sheet_analyzer_optimized.py
   ```

4. Launch the dashboard:
   ```
   streamlit run app.py
   ```

## Deployment

This dashboard is optimized for Streamlit Cloud deployment:

1. Push to GitHub
2. Connect your repository to Streamlit Cloud
3. Deploy with the following settings:
   - Main file path: `app.py`
   - Python version: 3.9+
   - Requirements: `requirements.txt`

## Project Structure

- `app.py`: Main Streamlit application
- `sheet_analyzer.py`: Google Sheets data fetcher
- `sheet_analyzer_optimized.py`: Optimized version for better performance
- `sheet_loader.py`: Efficient data loading module
- `streamlit_config.py`: Streamlit configuration settings
- `overview_tab.py`, `performance_tab.py`, etc.: Modular dashboard components
- `assets/`: Static assets and CSS
- `.streamlit/`: Streamlit configuration files

## Performance Optimizations

This dashboard includes several optimizations for better performance:

1. Efficient data loading with pandas category types
2. Optimized Streamlit configuration
3. Modular code structure
4. Reduced animation overhead
5. Proper caching configuration

## License

© 2025 Pepe's Power Solutions