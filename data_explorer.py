import streamlit as st
import pandas as pd
from io import BytesIO

def render_data_explorer(df_filtered, COLORS, start):
    """Render the Data Explorer tab with a clean modular layout"""
    
    st.markdown("<h2 style='text-align: center; color: #483D8B;'>Data Explorer</h2>", unsafe_allow_html=True)
    
    # Create a clean modular layout
    with st.container():
        st.markdown("""
        <div class="chart-box">
        <h3>Filter and Search</h3>
        """, unsafe_allow_html=True)
        
        try:
            # Create a clean filter UI with 3 columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Agent filter dropdown
                if 'AGENT' in df_filtered.columns:
                    agent_options = ["All Agents"] + sorted(df_filtered['AGENT'].unique().tolist())
                    selected_agent = st.selectbox("Agent:", agent_options, key="explorer_agent")
            
            with col2:
                # Status filter dropdown
                if 'STATUS' in df_filtered.columns:
                    status_options = ["All Statuses"] + sorted(df_filtered['STATUS'].unique().tolist())
                    selected_status = st.selectbox("Status:", status_options, key="explorer_status")
            
            with col3:
                # Program filter dropdown
                if 'SOURCE_SHEET' in df_filtered.columns:
                    program_options = ["All Programs"] + sorted(df_filtered['SOURCE_SHEET'].str.replace('-Raw', '').str.replace(' Raw', '').unique().tolist())
                    selected_program = st.selectbox("Program:", program_options, key="explorer_program")
            
            # Add date range filter
            if 'ENROLLED_DATE' in df_filtered.columns:
                col1, col2 = st.columns(2)
                with col1:
                    min_date = df_filtered['ENROLLED_DATE'].min().date()
                    max_date = df_filtered['ENROLLED_DATE'].max().date()
                    start_date = st.date_input("From:", min_date, min_value=min_date, max_value=max_date, key="explorer_start")
                with col2:
                    end_date = st.date_input("To:", max_date, min_value=min_date, max_value=max_date, key="explorer_end")
            
            # Add search box
            search_query = st.text_input("Search:", "", placeholder="Enter customer ID, agent name, etc.", key="explorer_search")
            
            # Apply filters
            df_explorer = df_filtered.copy()
            
            # Apply agent filter
            if 'AGENT' in df_explorer.columns and selected_agent != "All Agents":
                df_explorer = df_explorer[df_explorer['AGENT'] == selected_agent]
            
            # Apply status filter
            if 'STATUS' in df_explorer.columns and selected_status != "All Statuses":
                df_explorer = df_explorer[df_explorer['STATUS'] == selected_status]
                
            # Apply program filter
            if 'SOURCE_SHEET' in df_explorer.columns and selected_program != "All Programs":
                clean_program = selected_program
                df_explorer = df_explorer[df_explorer['SOURCE_SHEET'].str.replace('-Raw', '').str.replace(' Raw', '') == clean_program]
            
            # Apply date filter
            if 'ENROLLED_DATE' in df_explorer.columns:
                df_explorer = df_explorer[(df_explorer['ENROLLED_DATE'].dt.date >= start_date) & 
                                        (df_explorer['ENROLLED_DATE'].dt.date <= end_date)]
            
            # Apply search
            if search_query:
                df_explorer = df_explorer[df_explorer.astype(str).apply(
                    lambda row: row.str.contains(search_query, case=False).any(), axis=1)]
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
            
            # Results module
            with st.container():
                st.markdown(f"""
                <div class="chart-box">
                <h3>Results ({len(df_explorer)} records)</h3>
                """, unsafe_allow_html=True)
                
                # Create clean display dataframe
                clean_df = pd.DataFrame()
                
                if len(df_explorer) > 0:
                    # Format date and week
                    if 'ENROLLED_DATE' in df_explorer.columns:
                        clean_df['Date'] = df_explorer['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
                        clean_df['Week'] = df_explorer['ENROLLED_DATE'].dt.strftime('%Y-W%U')
                    
                    # Add status
                    clean_df['Status'] = df_explorer['STATUS'] if 'STATUS' in df_explorer.columns else "N/A"
                    
                    # Add category
                    clean_df['Category'] = df_explorer['CATEGORY'] if 'CATEGORY' in df_explorer.columns else "N/A"
                    
                    # Add program (cleaned)
                    if 'SOURCE_SHEET' in df_explorer.columns:
                        clean_df['Program'] = df_explorer['SOURCE_SHEET'].str.replace('-Raw', '').str.replace(' Raw', '')
                    
                    # Add agent
                    if 'AGENT' in df_explorer.columns:
                        clean_df['Agent'] = df_explorer['AGENT']
                    
                    # Display the clean dataframe
                    st.dataframe(clean_df.sort_values('Date', ascending=False) if 'Date' in clean_df.columns else clean_df, 
                               use_container_width=True, height=400, key="explorer_results_table")
                    
                    # Add export button
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        clean_df.to_excel(writer, index=False)
                        
                        # Format Excel
                        workbook = writer.book
                        worksheet = writer.sheets['Sheet1']
                        
                        # Format headers
                        header_format = workbook.add_format({
                            'bold': True,
                            'bg_color': COLORS['primary'],
                            'color': 'white',
                            'border': 1
                        })
                        
                        for col_num, value in enumerate(clean_df.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                        
                        # Auto-fit columns
                        for i, col in enumerate(clean_df.columns):
                            column_len = max(clean_df[col].astype(str).str.len().max(), len(col)) + 2
                            worksheet.set_column(i, i, column_len)
                    
                    excel_buffer.seek(0)
                    filename = f"pepe_sales_data_{start.strftime('%Y%m%d')}"
                    st.download_button("📤 Download Report", excel_buffer, file_name=f"{filename}.xlsx", 
                                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                     use_container_width=True, key="explorer_download_button")
                else:
                    st.info("No records match your filter criteria.")
                
                st.markdown("""
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error in data explorer: {e}")
            st.info("Could not load data explorer.")