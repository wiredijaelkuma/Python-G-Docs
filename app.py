import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import base64
from io import BytesIO
import calendar

# Set page configuration
st.set_page_config(
    page_title="Pepe's Power Sales Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- Constants ---
# Use relative paths for assets in the same directory as the app
BACKGROUND_IMAGE = "pepe-background.png"
BANNER_IMAGE = "pepe-sunset-banner.png"
LOGO_IMAGE = "pepe-rocket.png"

# --- Helper Functions ---
def load_image_base64(image_path):
    """Load image and convert to base64 with error handling"""
    try:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return data
    except Exception as e:
        st.warning(f"Image not found: {image_path}. Error: {e}")
        return None

def add_bg_from_base64(base64_data):
    """Add background image using base64 string"""
    if base64_data:
        bg_img = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{base64_data}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(bg_img, unsafe_allow_html=True)

def generate_sample_data():
    """Generate sample sales data for demonstration"""
    np.random.seed(42)
    
    # Date range for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Product categories
    products = ['Solar Panels', 'Wind Turbines', 'Battery Storage', 'Smart Grid Solutions']
    regions = ['North', 'South', 'East', 'West']
    
    # Generate data
    data = []
    for date in date_range:
        for product in products:
            for region in regions:
                # Base sales with some randomness
                base_sales = np.random.randint(5000, 20000)
                
                # Add seasonality - higher in summer months
                month = date.month
                season_factor = 1.3 if month in [6, 7, 8] else 0.8 if month in [12, 1, 2] else 1.0
                
                # Add trend - growing over time
                days_from_start = (date - start_date).days
                trend_factor = 1 + (days_from_start / 365) * 0.5
                
                # Product popularity factor
                product_factor = 1.5 if product == 'Solar Panels' else 1.2 if product == 'Battery Storage' else 1.0
                
                # Region factor
                region_factor = 1.3 if region == 'South' else 0.9 if region == 'North' else 1.1
                
                # Calculate final sales
                sales = int(base_sales * season_factor * trend_factor * product_factor * region_factor)
                
                # Add some noise
                sales = max(100, int(sales * np.random.normal(1, 0.1)))
                
                data.append({
                    'Date': date,
                    'Product': product,
                    'Region': region,
                    'Sales': sales,
                    'Units': int(sales / np.random.randint(500, 1000)),
                    'Customer_Satisfaction': min(5.0, max(3.0, np.random.normal(4.2, 0.5)))
                })
    
    return pd.DataFrame(data)

def format_number(num):
    """Format large numbers with K, M suffix"""
    if num >= 1e6:
        return f"{num/1e6:.1f}M"
    elif num >= 1e3:
        return f"{num/1e3:.1f}K"
    else:
        return str(int(num))

# --- Main App ---
def main():
    # Try to load background image
    try:
        bg_image = load_image_base64(BACKGROUND_IMAGE)
        add_bg_from_base64(bg_image)
    except:
        st.warning("Background image not found. Using default background.")
    
    # Header with logo
    col1, col2 = st.columns([1, 5])
    try:
        with col1:
            st.image(LOGO_IMAGE, width=100)
        with col2:
            st.title("PEPE'S POWER SALES DASHBOARD")
            st.subheader("Real-time Analytics for Renewable Energy Sales")
    except:
        st.title("PEPE'S POWER SALES DASHBOARD")
        st.subheader("Real-time Analytics for Renewable Energy Sales")
    
    # Load sample data
    df = generate_sample_data()
    
    # Date filter
    st.sidebar.header("Filters")
    
    # Date range selector
    max_date = df['Date'].max().date()
    min_date = df['Date'].min().date()
    
    with st.sidebar.expander("Date Range", expanded=True):
        date_option = st.radio(
            "Select time period:",
            ["Last 30 days", "Last 90 days", "Last 6 months", "Last year", "Custom"]
        )
        
        if date_option == "Last 30 days":
            start_date = max_date - timedelta(days=30)
            end_date = max_date
        elif date_option == "Last 90 days":
            start_date = max_date - timedelta(days=90)
            end_date = max_date
        elif date_option == "Last 6 months":
            start_date = max_date - timedelta(days=180)
            end_date = max_date
        elif date_option == "Last year":
            start_date = max_date - timedelta(days=365)
            end_date = max_date
        else:  # Custom
            col1, col2 = st.sidebar.columns(2)
            start_date = col1.date_input("Start date", min_date)
            end_date = col2.date_input("End date", max_date)
    
    # Product filter
    with st.sidebar.expander("Products", expanded=True):
        all_products = st.checkbox("Select all products", value=True)
        if all_products:
            selected_products = df['Product'].unique().tolist()
        else:
            selected_products = st.multiselect(
                "Select products:",
                options=df['Product'].unique().tolist(),
                default=df['Product'].unique().tolist()[:2]
            )
    
    # Region filter
    with st.sidebar.expander("Regions", expanded=True):
        all_regions = st.checkbox("Select all regions", value=True)
        if all_regions:
            selected_regions = df['Region'].unique().tolist()
        else:
            selected_regions = st.multiselect(
                "Select regions:",
                options=df['Region'].unique().tolist(),
                default=df['Region'].unique().tolist()[:2]
            )
    
    # Filter data based on selections
    filtered_df = df[
        (df['Date'].dt.date >= start_date) &
        (df['Date'].dt.date <= end_date) &
        (df['Product'].isin(selected_products)) &
        (df['Region'].isin(selected_regions))
    ]
    
    # Main dashboard
    # Key metrics - 4 cards in a row
    st.markdown("### Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Sales
    total_sales = filtered_df['Sales'].sum()
    col1.metric(
        "Total Sales",
        f"${format_number(total_sales)}",
        f"{((total_sales / total_sales) * 100 - 100):.1f}%" if 'prev_total_sales' in locals() else None
    )
    
    # Total Units
    total_units = filtered_df['Units'].sum()
    col2.metric(
        "Total Units Sold",
        format_number(total_units),
        f"{((total_units / total_units) * 100 - 100):.1f}%" if 'prev_total_units' in locals() else None
    )
    
    # Average Sales per Day
    days_count = (filtered_df['Date'].max() - filtered_df['Date'].min()).days + 1
    avg_daily_sales = total_sales / max(days_count, 1)
    col3.metric(
        "Avg. Daily Sales",
        f"${format_number(avg_daily_sales)}"
    )
    
    # Average Customer Satisfaction
    avg_satisfaction = filtered_df['Customer_Satisfaction'].mean()
    col4.metric(
        "Avg. Satisfaction",
        f"{avg_satisfaction:.1f}/5.0"
    )
    
    # Charts
    st.markdown("### Sales Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Sales Trends", "Product Analysis", "Regional Performance"])
    
    with tab1:
        # Time series chart
        st.subheader("Sales Over Time")
        
        # Group by date
        daily_sales = filtered_df.groupby('Date')['Sales'].sum().reset_index()
        
        # Create time series chart
        fig = px.line(
            daily_sales,
            x='Date',
            y='Sales',
            title='Daily Sales Trend',
            labels={'Sales': 'Sales ($)', 'Date': 'Date'},
            template='plotly_white'
        )
        
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Sales ($)',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly chart
        st.subheader("Monthly Sales")
        
        # Add month-year column
        filtered_df['Month-Year'] = filtered_df['Date'].dt.strftime('%b %Y')
        monthly_sales = filtered_df.groupby('Month-Year')['Sales'].sum().reset_index()
        
        # Sort by date
        month_year_order = sorted(filtered_df['Date'].dt.to_period('M').unique())
        month_year_labels = [p.strftime('%b %Y') for p in month_year_order]
        monthly_sales['Month-Year'] = pd.Categorical(monthly_sales['Month-Year'], categories=month_year_labels, ordered=True)
        monthly_sales = monthly_sales.sort_values('Month-Year')
        
        fig = px.bar(
            monthly_sales,
            x='Month-Year',
            y='Sales',
            title='Monthly Sales',
            labels={'Sales': 'Sales ($)', 'Month-Year': 'Month'},
            template='plotly_white'
        )
        
        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='Sales ($)',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            # Product sales breakdown
            product_sales = filtered_df.groupby('Product')['Sales'].sum().reset_index()
            
            fig = px.pie(
                product_sales,
                values='Sales',
                names='Product',
                title='Sales by Product',
                hole=0.4,
                template='plotly_white'
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Product units breakdown
            product_units = filtered_df.groupby('Product')['Units'].sum().reset_index()
            
            fig = px.bar(
                product_units,
                x='Product',
                y='Units',
                title='Units Sold by Product',
                template='plotly_white'
            )
            
            fig.update_layout(
                xaxis_title='Product',
                yaxis_title='Units Sold',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        # Product satisfaction
        product_satisfaction = filtered_df.groupby('Product')['Customer_Satisfaction'].mean().reset_index()
        
        fig = px.bar(
            product_satisfaction,
            x='Product',
            y='Customer_Satisfaction',
            title='Average Customer Satisfaction by Product',
            template='plotly_white',
            color='Customer_Satisfaction',
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(
            xaxis_title='Product',
            yaxis_title='Avg. Satisfaction (1-5)',
            height=400,
            coloraxis_showscale=False
        )
        
        fig.update_yaxes(range=[0, 5])
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            # Region sales breakdown
            region_sales = filtered_df.groupby('Region')['Sales'].sum().reset_index()
            
            fig = px.pie(
                region_sales,
                values='Sales',
                names='Region',
                title='Sales by Region',
                hole=0.4,
                template='plotly_white'
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Region units breakdown
            region_units = filtered_df.groupby('Region')['Units'].sum().reset_index()
            
            fig = px.bar(
                region_units,
                x='Region',
                y='Units',
                title='Units Sold by Region',
                template='plotly_white'
            )
            
            fig.update_layout(
                xaxis_title='Region',
                yaxis_title='Units Sold',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Product by region heatmap
        product_region = filtered_df.pivot_table(
            values='Sales',
            index='Product',
            columns='Region',
            aggfunc='sum'
        ).fillna(0)
        
        fig = px.imshow(
            product_region,
            title='Sales Heatmap: Product vs. Region',
            labels=dict(x="Region", y="Product", color="Sales"),
            color_continuous_scale='Viridis',
            aspect="auto"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Data Table
    st.markdown("### Detailed Data")
    with st.expander("View Raw Data"):
        st.dataframe(
            filtered_df[['Date', 'Product', 'Region', 'Sales', 'Units', 'Customer_Satisfaction']].sort_values('Date', ascending=False),
            use_container_width=True
        )
    
    # Download CSV button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name="pepe_power_sales_data.csv",
        mime="text/csv",
    )
    
    # Footer
    st.markdown("---")
    st.markdown("© 2025 Pepe's Power • Data-Driven Dashboard")

if __name__ == "__main__":
    main()
