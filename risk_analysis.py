import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

def render_risk_analysis(df_filtered, COLORS):
    """Render the Risk Analysis tab with a clean modular layout"""
    
    st.markdown("<h2 style='text-align: center; color: #483D8B;'>Risk Analysis</h2>", unsafe_allow_html=True)
    
    try:
        # Filter for problematic contracts
        flagged = df_filtered[df_filtered['CATEGORY'].isin(["NSF", "CANCELLED", "OTHER"])]
        
        # Risk summary module
        with st.container():
            st.markdown("""
            <div class="chart-box">
            <h3>Risk Summary</h3>
            """, unsafe_allow_html=True)
            
            # Add risk summary metrics
            total_risk = len(flagged)
            risk_percentage = (total_risk / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
            
            st.markdown(f"""
            <div class="risk-indicator">
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div style="flex: 1; min-width: 200px;">
                        <div style="font-size: 1.1rem; color: #483D8B; font-weight: 600;">Total Risk Contracts</div>
                        <div style="font-size: 2rem; font-weight: bold; color: #FF6347;">{total_risk}</div>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <div style="font-size: 1.1rem; color: #483D8B; font-weight: 600;">Risk Percentage</div>
                        <div style="font-size: 2rem; font-weight: bold; color: #FF6347;">{risk_percentage:.1f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
        
        # Risk charts module
        col1, col2 = st.columns(2)
        
        # Cancellation reasons chart
        with col1:
            st.markdown("""
            <div class="chart-box">
            <h3>Cancellation Reasons</h3>
            """, unsafe_allow_html=True)
            
            if 'STATUS' in flagged.columns and not flagged.empty:
                try:
                    # Get top 10 status reasons
                    status_counts = flagged['STATUS'].value_counts().head(10).reset_index()
                    status_counts.columns = ['Status', 'Count']
                    fig = px.bar(
                        status_counts, 
                        x='Status', 
                        y='Count',
                        title="Top Cancellation Reasons",
                        color='Count',
                        color_continuous_scale=[COLORS['light_purple'], COLORS['primary'], COLORS['secondary'], COLORS['dark']]
                    )
                    fig.update_layout(
                        height=450,
                        xaxis_tickangle=-45,
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font_color=COLORS['text'],
                        margin=dict(t=50, b=120),
                        coloraxis=dict(colorbar=dict(
                            title="Count",
                            tickfont=dict(color=COLORS['text']),
                        ))
                    )
                    fig.update_traces(marker_line_color=COLORS['primary'],
                                      marker_line_width=1.5)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating cancellation reasons chart: {e}")
                    st.info("Could not generate cancellation reasons chart.")
            else:
                st.info("No cancellation data available.")
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
        
        # Agents with issues chart
        with col2:
            st.markdown("""
            <div class="chart-box">
            <h3>Agents with Most Issues</h3>
            """, unsafe_allow_html=True)
            
            if 'AGENT' in flagged.columns and not flagged.empty:
                try:
                    agent_issues = flagged.groupby('AGENT').size().reset_index(name='Issue_Count')
                    agent_issues = agent_issues.sort_values('Issue_Count', ascending=False).head(10)
                    fig = px.bar(
                        agent_issues,
                        x='AGENT',
                        y='Issue_Count',
                        title="Top Agents by Issue Count",
                        color='Issue_Count',
                        color_continuous_scale=[COLORS['light_purple'], COLORS['primary'], COLORS['secondary'], COLORS['dark']]
                    )
                    fig.update_layout(
                        height=450,
                        xaxis_tickangle=-45,
                        plot_bgcolor=COLORS['background'],
                        paper_bgcolor=COLORS['background'],
                        font_color=COLORS['text'],
                        margin=dict(t=50, b=120),
                        coloraxis=dict(colorbar=dict(
                            title="Issues",
                            tickfont=dict(color=COLORS['text']),
                        ))
                    )
                    fig.update_traces(marker_line_color=COLORS['primary'],
                                      marker_line_width=1.5)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating agents with issues chart: {e}")
                    st.info("Could not generate agents with issues chart.")
            else:
                st.info("No agent issue data available.")
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
        
        # Problem contracts module
        with st.container():
            st.markdown("""
            <div class="chart-box">
            <h3>Problem Contracts</h3>
            """, unsafe_allow_html=True)
            
            if not flagged.empty:
                # Add search functionality
                search_risk = st.text_input("Search problem contracts:", "", placeholder="Enter search term...")
                if search_risk:
                    filtered_flagged = flagged[flagged.astype(str).apply(
                        lambda row: row.str.contains(search_risk, case=False).any(), axis=1)]
                else:
                    filtered_flagged = flagged
                
                # Create clean display dataframe
                clean_df = pd.DataFrame()
                
                # Format date and week
                if 'ENROLLED_DATE' in filtered_flagged.columns:
                    clean_df['Date'] = filtered_flagged['ENROLLED_DATE'].dt.strftime('%Y-%m-%d')
                    clean_df['Week'] = filtered_flagged['ENROLLED_DATE'].dt.strftime('%Y-W%U')
                
                # Add status
                clean_df['Status'] = filtered_flagged['STATUS'] if 'STATUS' in filtered_flagged.columns else "N/A"
                
                # Add program (cleaned)
                if 'SOURCE_SHEET' in filtered_flagged.columns:
                    clean_df['Program'] = filtered_flagged['SOURCE_SHEET'].str.replace('-Raw', '').str.replace(' Raw', '')
                
                # Add agent
                if 'AGENT' in filtered_flagged.columns:
                    clean_df['Agent'] = filtered_flagged['AGENT']
                
                # Display the clean dataframe
                st.dataframe(clean_df.sort_values('Date', ascending=False) if 'Date' in clean_df.columns else clean_df, 
                           use_container_width=True, height=400)
                
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
                st.download_button("📤 Download Risk Report", excel_buffer, file_name="risk_contracts.xlsx", 
                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 use_container_width=True)
            else:
                st.info("No problem contracts found in the selected data.")
            
            st.markdown("""
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error in risk analysis: {e}")
        st.info("Could not load risk analysis.")