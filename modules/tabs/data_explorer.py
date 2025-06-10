# modules/tabs/data_explorer.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def render_data_explorer(df, COLORS):
    """Render the data explorer tab with interactive analysis tools"""
    
    st.subheader("Data Explorer")
    
    if df.empty:
        st.warning("No data available for exploration. Please adjust your filters.")
        return
    
    # Create tabs for different explorer views
    explorer_tabs = st.tabs(["Data Viewer", "Column Analysis", "Custom Query"])
    
    # Data Viewer Tab
    with explorer_tabs[0]:
        st.subheader("Data Preview")
        
        # Column selector
        all_columns = df.columns.tolist()
        default_columns = min(10, len(all_columns))
        
        selected_columns = st.multiselect(
            "Select Columns to Display",
            options=all_columns,
            default=all_columns[:default_columns]
        )
        
        # Filter options
        with st.expander("Filter Options"):
            # Let user select a column to filter on
            filter_column = st.selectbox(
                "Select Column to Filter",
                options=["None"] + all_columns
            )
            
            if filter_column != "None":
                # Get the column data type
                col_type = df[filter_column].dtype
                
                # Create appropriate filter control based on data type
                if pd.api.types.is_numeric_dtype(col_type):
                    # Numeric filter
                    min_val = float(df[filter_column].min())
                    max_val = float(df[filter_column].max())
                    
                    filter_range = st.slider(
                        f"Filter range for {filter_column}",
                        min_value=min_val,
                        max_value=max_val,
                        value=(min_val, max_val)
                    )
                    
                    # Apply filter
                    filtered_df = df[(df[filter_column] >= filter_range[0]) & (df[filter_column] <= filter_range[1])]
                    
                elif pd.api.types.is_datetime64_dtype(col_type):
                    # Date filter
                    min_date = df[filter_column].min().date()
                    max_date = df[filter_column].max().date()
                    
                    start_date = st.date_input(
                        "Start Date",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    end_date = st.date_input(
                        "End Date",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    # Apply filter
                    filtered_df = df[(df[filter_column].dt.date >= start_date) & (df[filter_column].dt.date <= end_date)]
                    
                else:
                    # Categorical filter
                    unique_values = df[filter_column].unique()
                    
                    if len(unique_values) <= 50:  # Only show if reasonable number of options
                        selected_values = st.multiselect(
                            f"Select {filter_column} values",
                            options=unique_values,
                            default=unique_values
                        )
                        
                        # Apply filter
                        filtered_df = df[df[filter_column].isin(selected_values)]
                    else:
                        st.warning(f"Too many unique values in {filter_column} to display as a filter. Please use the search box.")
                        filtered_df = df
            else:
                filtered_df = df
        
        # Show data table
        if selected_columns:
            # Add search functionality
            search_term = st.text_input("Search in data (case-insensitive)")
            
            if search_term:
                # Search across all string columns
                mask = pd.Series(False, index=filtered_df.index)
                
                for col in selected_columns:
                    if filtered_df[col].dtype == 'object':  # Only search string columns
                        mask |= filtered_df[col].astype(str).str.contains(search_term, case=False, na=False)
                
                search_results = filtered_df[mask]
                st.dataframe(search_results[selected_columns], use_container_width=True)
                st.info(f"Found {len(search_results)} records matching '{search_term}'")
            else:
                # Show all rows
                st.dataframe(filtered_df[selected_columns], use_container_width=True)
        else:
            st.warning("Please select at least one column to display.")
        
        # Download button for filtered data
        if not filtered_df.empty and selected_columns:
            csv = filtered_df[selected_columns].to_csv(index=False)
            st.download_button(
                label="Download Filtered Data",
                data=csv,
                file_name="filtered_data.csv",
                mime="text/csv"
            )
    
    # Column Analysis Tab
    with explorer_tabs[1]:
        st.subheader("Column Analysis")
        
        # Column selector
        all_columns = df.columns.tolist()
        analysis_column = st.selectbox(
            "Select Column to Analyze",
            options=all_columns
        )
        
        if analysis_column:
            # Get column data
            col_data = df[analysis_column]
            col_type = col_data.dtype
            
            # Display basic statistics
            st.subheader(f"Analysis of {analysis_column}")
            
            # Count of non-null values
            non_null_count = col_data.count()
            null_count = col_data.isna().sum()
            total_count = len(col_data)
            
            # Create metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Non-null Values", non_null_count)
            
            with col2:
                st.metric("Null Values", null_count)
            
            with col3:
                completeness = (non_null_count / total_count * 100) if total_count > 0 else 0
                st.metric("Completeness", f"{completeness:.1f}%")
            
            # Different analysis based on data type
            if pd.api.types.is_numeric_dtype(col_type):
                # Numeric column analysis
                numeric_stats = col_data.describe()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Mean", f"{numeric_stats['mean']:.2f}")
                
                with col2:
                    st.metric("Median", f"{numeric_stats['50%']:.2f}")
                
                with col3:
                    st.metric("Min", f"{numeric_stats['min']:.2f}")
                
                with col4:
                    st.metric("Max", f"{numeric_stats['max']:.2f}")
                
                # Create histogram
                fig = px.histogram(
                    df,
                    x=analysis_column,
                    nbins=30,
                    title=f"Distribution of {analysis_column}",
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True, key="column_histogram")
                
                # Create box plot
                fig = px.box(
                    df,
                    y=analysis_column,
                    title=f"Box Plot of {analysis_column}",
                    color_discrete_sequence=[COLORS['primary']]
                )
                st.plotly_chart(fig, use_container_width=True, key="column_boxplot")
                
            elif pd.api.types.is_datetime64_dtype(col_type):
                # Date column analysis
                if col_data.notna().any():  # Check if there's at least one non-null value
                    date_stats = pd.DataFrame({
                        'Statistic': ['Minimum', 'Maximum', 'Range'],
                        'Value': [
                            col_data.min().strftime('%Y-%m-%d'),
                            col_data.max().strftime('%Y-%m-%d'),
                            f"{(col_data.max() - col_data.min()).days} days"
                        ]
                    })
                    
                    st.table(date_stats)
                    
                    # Group by month and year
                    col_data_valid = col_data.dropna()
                    if not col_data_valid.empty:
                        monthly_counts = col_data_valid.dt.strftime('%Y-%m').value_counts().sort_index()
                        monthly_data = pd.DataFrame({
                            'Month': monthly_counts.index,
                            'Count': monthly_counts.values
                        })
                        
                        # Create time series chart
                        fig = px.line(
                            monthly_data,
                            x='Month',
                            y='Count',
                            markers=True,
                            title=f"Distribution of {analysis_column} by Month",
                            color_discrete_sequence=[COLORS['primary']]
                        )
                        st.plotly_chart(fig, use_container_width=True, key="column_timeseries")
                        
                        # Day of week distribution
                        dow_counts = col_data_valid.dt.day_name().value_counts()
                        
                        # Order days correctly
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        dow_data = pd.DataFrame({
                            'Day': day_order,
                            'Count': [dow_counts.get(day, 0) for day in day_order]
                        })
                        
                        fig = px.bar(
                            dow_data,
                            x='Day',
                            y='Count',
                            title=f"Distribution of {analysis_column} by Day of Week",
                            color_discrete_sequence=[COLORS['secondary']]
                        )
                        st.plotly_chart(fig, use_container_width=True, key="column_dayofweek")
                    else:
                        st.warning("No valid date values to analyze")
                else:
                    st.warning("No valid date values to analyze")
                
            else:
                # Categorical column analysis
                if col_data.notna().any():  # Check if there's at least one non-null value
                    value_counts = col_data.value_counts().reset_index()
                    if not value_counts.empty:
                        value_counts.columns = ['Value', 'Count']
                        
                        # Calculate percentage
                        value_counts['Percentage'] = (value_counts['Count'] / value_counts['Count'].sum() * 100).round(1)
                        
                        # Show the top values
                        top_n = min(20, len(value_counts))
                        st.write(f"Top {top_n} Values:")
                        
                        # Create bar chart
                        fig = px.bar(
                            value_counts.head(top_n),
                            x='Value',
                            y='Count',
                            title=f"Top {top_n} Values in {analysis_column}",
                            color='Count',
                            color_continuous_scale=px.colors.sequential.Purp,
                            text='Percentage'
                        )
                        fig.update_traces(texttemplate='%{text}%', textposition='outside')
                        st.plotly_chart(fig, use_container_width=True, key="column_barchart")
                        
                        # Show the data table
                        with st.expander(f"Show all values for {analysis_column}"):
                            st.dataframe(value_counts, use_container_width=True)
                    else:
                        st.warning("No data to display for this column")
                else:
                    st.warning("No non-null values to analyze in this column")
    
    # Custom Query Tab
    with explorer_tabs[2]:
        st.subheader("Custom Query")
        
        st.write("""
        Use this section to create custom queries against the data.
        Enter SQL-like conditions in the format: `column_name operator value`
        
        Examples:
        - `CATEGORY == "ACTIVE"`
        - `ENROLLED_DATE > "2023-01-01"`
        - `AGENT == "John Doe" and CATEGORY == "CANCELLED"`
        """)
        
        # Query input
        query = st.text_area("Enter Query Condition", height=100)
        
        # Execute button
        if st.button("Execute Query"):
            if query:
                try:
                    # Execute the query
                    result_df = df.query(query)
                    
                    # Show results
                    st.write(f"Found {len(result_df)} matching records")
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Download button for query results
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        label="Download Query Results",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv"
                    )
                    
                    # Show a sample visualization based on the query results
                    if len(result_df) > 0:
                        st.subheader("Quick Visualization")
                        
                        # Select columns for visualization
                        viz_options = []
                        
                        # Add numeric columns
                        numeric_cols = result_df.select_dtypes(include=['number']).columns.tolist()
                        if numeric_cols:
                            viz_options.append("Histogram")
                            viz_options.append("Scatter Plot")
                        
                        # Add categorical columns
                        cat_cols = result_df.select_dtypes(exclude=['number', 'datetime']).columns.tolist()
                        if cat_cols:
                            viz_options.append("Bar Chart")
                            viz_options.append("Pie Chart")
                        
                        # Add time series option if date columns exist
                        date_cols = result_df.select_dtypes(include=['datetime']).columns.tolist()
                        if date_cols:
                            viz_options.append("Time Series")
                        
                        # Let user select visualization type
                        if viz_options:
                            viz_type = st.selectbox("Select Visualization Type", viz_options)
                            
                            if viz_type == "Histogram" and numeric_cols:
                                hist_col = st.selectbox("Select Column for Histogram", numeric_cols)
                                fig = px.histogram(
                                    result_df,
                                    x=hist_col,
                                    title=f"Histogram of {hist_col}",
                                    color_discrete_sequence=[COLORS['primary']]
                                )
                                st.plotly_chart(fig, use_container_width=True, key="query_histogram")
                            
                            elif viz_type == "Scatter Plot" and len(numeric_cols) >= 2:
                                x_col = st.selectbox("Select X Column", numeric_cols)
                                y_col = st.selectbox("Select Y Column", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                                
                                # Optional color column
                                color_options = ["None"] + cat_cols
                                color_col = st.selectbox("Color by (optional)", color_options)
                                
                                if color_col == "None":
                                    fig = px.scatter(
                                        result_df,
                                        x=x_col,
                                        y=y_col,
                                        title=f"{y_col} vs {x_col}",
                                        color_discrete_sequence=[COLORS['primary']]
                                    )
                                else:
                                    fig = px.scatter(
                                        result_df,
                                        x=x_col,
                                        y=y_col,
                                        color=color_col,
                                        title=f"{y_col} vs {x_col} (colored by {color_col})"
                                    )
                                st.plotly_chart(fig, use_container_width=True, key="query_scatter")
                            
                            elif viz_type == "Bar Chart" and cat_cols:
                                x_col = st.selectbox("Select Category Column", cat_cols)
                                
                                # Optional value column
                                y_options = ["Count"] + numeric_cols
                                y_col = st.selectbox("Value Column (optional)", y_options)
                                
                                if y_col == "Count":
                                    value_counts = result_df[x_col].value_counts().reset_index()
                                    value_counts.columns = ['Value', 'Count']
                                    
                                    fig = px.bar(
                                        value_counts,
                                        x='Value',
                                        y='Count',
                                        title=f"Count of {x_col}",
                                        color_discrete_sequence=[COLORS['primary']]
                                    )
                                else:
                                    # Group by the category and calculate the mean of the value column
                                    grouped = result_df.groupby(x_col)[y_col].mean().reset_index()
                                    
                                    fig = px.bar(
                                        grouped,
                                        x=x_col,
                                        y=y_col,
                                        title=f"Average {y_col} by {x_col}",
                                        color_discrete_sequence=[COLORS['primary']]
                                    )
                                st.plotly_chart(fig, use_container_width=True, key="query_bar")
                            
                            elif viz_type == "Pie Chart" and cat_cols:
                                pie_col = st.selectbox("Select Category Column", cat_cols)
                                
                                value_counts = result_df[pie_col].value_counts().reset_index()
                                value_counts.columns = ['Value', 'Count']
                                
                                fig = px.pie(
                                    value_counts,
                                    values='Count',
                                    names='Value',
                                    title=f"Distribution of {pie_col}"
                                )
                                st.plotly_chart(fig, use_container_width=True, key="query_pie")
                            
                            elif viz_type == "Time Series" and date_cols:
                                x_col = st.selectbox("Select Date Column", date_cols)
                                
                                # Let user choose aggregation level
                                agg_level = st.selectbox(
                                    "Aggregation Level",
                                    ["Day", "Week", "Month", "Year"]
                                )
                                
                                # Let user choose value column or count
                                y_options = ["Count"] + numeric_cols
                                y_col = st.selectbox("Value Column", y_options)
                                
                                # Create time series based on selections
                                if y_col == "Count":
                                    # Group by time period and count
                                    if agg_level == "Day":
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y-%m-%d')
                                    elif agg_level == "Week":
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y-%U')
                                    elif agg_level == "Month":
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y-%m')
                                    else:  # Year
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y')
                                    
                                    time_data = result_df.groupby('Period').size().reset_index()
                                    time_data.columns = ['Period', 'Count']
                                    
                                    fig = px.line(
                                        time_data,
                                        x='Period',
                                        y='Count',
                                        markers=True,
                                        title=f"Count by {agg_level}",
                                        color_discrete_sequence=[COLORS['primary']]
                                    )
                                else:
                                    # Group by time period and calculate mean of value column
                                    if agg_level == "Day":
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y-%m-%d')
                                    elif agg_level == "Week":
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y-%U')
                                    elif agg_level == "Month":
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y-%m')
                                    else:  # Year
                                        result_df['Period'] = result_df[x_col].dt.strftime('%Y')
                                    
                                    time_data = result_df.groupby('Period')[y_col].mean().reset_index()
                                    
                                    fig = px.line(
                                        time_data,
                                        x='Period',
                                        y=y_col,
                                        markers=True,
                                        title=f"Average {y_col} by {agg_level}",
                                        color_discrete_sequence=[COLORS['primary']]
                                    )
                                st.plotly_chart(fig, use_container_width=True, key="query_timeseries")
                        else:
                            st.warning("No suitable columns available for visualization.")
                except Exception as e:
                    st.error(f"Error executing query: {str(e)}")
            else:
                st.warning("Please enter a query to execute.")