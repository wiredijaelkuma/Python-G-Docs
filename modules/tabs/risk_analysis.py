# modules/tabs/risk_analysis.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_risk_analysis(df, COLORS):
    """Render the risk analysis tab with predictive insights"""
    
    st.subheader("Risk Analysis Dashboard")
    
    # Check if we have the necessary data
    if 'CATEGORY' in df.columns:
        # Create tabs for different views
        risk_tabs = st.tabs(["Risk Overview", "Risk Factors", "Prediction"])
        
        # Risk Overview Tab
        with risk_tabs[0]:
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Create risk distribution pie chart
                risk_counts = df['CATEGORY'].value_counts().reset_index()
                risk_counts.columns = ['Risk Category', 'Count']
                
                # Map categories to risk levels
                risk_map = {
                    'ACTIVE': 'Low Risk',
                    'NSF': 'Medium Risk',
                    'CANCELLED': 'High Risk',
                    'OTHER': 'Unknown Risk'
                }
                
                risk_counts['Risk Level'] = risk_counts['Risk Category'].map(risk_map)
                
                fig = px.pie(
                    risk_counts,
                    values='Count',
                    names='Risk Level',
                    color='Risk Level',
                    color_discrete_map={
                        'Low Risk': COLORS['med_green'],
                        'Medium Risk': COLORS['warning'],
                        'High Risk': COLORS['danger'],
                        'Unknown Risk': COLORS['dark_accent']
                    },
                    title='Contract Risk Distribution'
                )
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Display risk metrics
                total = len(df)
                low_risk = len(df[df['CATEGORY'] == 'ACTIVE'])
                medium_risk = len(df[df['CATEGORY'] == 'NSF'])
                high_risk = len(df[df['CATEGORY'] == 'CANCELLED'])
                
                low_risk_pct = (low_risk / total * 100) if total > 0 else 0
                medium_risk_pct = (medium_risk / total * 100) if total > 0 else 0
                high_risk_pct = (high_risk / total * 100) if total > 0 else 0
                
                st.metric("Low Risk Contracts", f"{low_risk} ({low_risk_pct:.1f}%)")
                st.metric("Medium Risk Contracts", f"{medium_risk} ({medium_risk_pct:.1f}%)")
                st.metric("High Risk Contracts", f"{high_risk} ({high_risk_pct:.1f}%)")
                
                # Calculate overall risk score (weighted)
                risk_score = (low_risk * 0 + medium_risk * 50 + high_risk * 100) / total if total > 0 else 0
                
                # Display risk score gauge
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = risk_score,
                    title = {'text': "Portfolio Risk Score"},
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': COLORS['primary']},
                        'steps': [
                            {'range': [0, 33], 'color': COLORS['light_green']},
                            {'range': [33, 66], 'color': COLORS['warning']},
                            {'range': [66, 100], 'color': COLORS['danger']}
                        ]
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
        
        # Risk Factors Tab
        with risk_tabs[1]:
            st.subheader("Risk Factor Analysis")
            
            # Check for various potential risk factors
            potential_factors = []
            
            if 'AGENT' in df.columns:
                potential_factors.append('AGENT')
            
            if 'SOURCE_SHEET' in df.columns:
                potential_factors.append('SOURCE_SHEET')
            
            if 'PRODUCT' in df.columns:
                potential_factors.append('PRODUCT')
            
            if 'PLAN' in df.columns:
                potential_factors.append('PLAN')
            
            if 'PAYMENT_METHOD' in df.columns:
                potential_factors.append('PAYMENT_METHOD')
            
            # Let user select a factor to analyze
            if potential_factors:
                selected_factor = st.selectbox("Select Risk Factor to Analyze", potential_factors)
                
                if selected_factor:
                    # Group by the selected factor and calculate risk metrics
                    factor_total = df.groupby(selected_factor).size()
                    
                    # High risk counts (cancelled)
                    high_risk_counts = df[df['CATEGORY'] == 'CANCELLED'].groupby(selected_factor).size()
                    
                    # Medium risk counts (NSF)
                    medium_risk_counts = df[df['CATEGORY'] == 'NSF'].groupby(selected_factor).size()
                    
                    factor_data = pd.DataFrame({
                        'Factor': factor_total.index,
                        'Total': factor_total.values,
                        'High_Risk': high_risk_counts.reindex(factor_total.index, fill_value=0).values,
                        'Medium_Risk': medium_risk_counts.reindex(factor_total.index, fill_value=0).values
                    })
                    
                    # Calculate risk percentages
                    factor_data['High_Risk_Pct'] = (factor_data['High_Risk'] / factor_data['Total'] * 100).round(1)
                    factor_data['Medium_Risk_Pct'] = (factor_data['Medium_Risk'] / factor_data['Total'] * 100).round(1)
                    factor_data['Combined_Risk_Pct'] = (
                        (factor_data['High_Risk'] + factor_data['Medium_Risk']) / factor_data['Total'] * 100
                    ).round(1)
                    
                    # Calculate risk score
                    factor_data['Risk_Score'] = (
                        (factor_data['Medium_Risk'] * 50 + factor_data['High_Risk'] * 100) / factor_data['Total']
                    ).round(1)
                    
                    # Filter to items with significant volume
                    min_contracts = 5  # Minimum contracts to be included
                    qualified_factors = factor_data[factor_data['Total'] >= min_contracts].copy()
                    
                    # Sort by risk score
                    qualified_factors = qualified_factors.sort_values('Risk_Score', ascending=False)
                    
                    # Show top risk factors
                    st.subheader(f"Top {selected_factor} Risk Factors")
                    
                    # Create bar chart of risk scores
                    fig = px.bar(
                        qualified_factors.head(10),
                        x='Factor',
                        y='Risk_Score',
                        title=f'Top 10 {selected_factor} by Risk Score',
                        color='Risk_Score',
                        color_continuous_scale=px.colors.sequential.Reds,
                        text='Risk_Score'
                    )
                    fig.update_traces(texttemplate='%{text}', textposition='outside')
                    fig.update_layout(yaxis_title="Risk Score")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create stacked bar chart of risk types
                    risk_data_melted = pd.melt(
                        qualified_factors.head(10),
                        id_vars=['Factor', 'Total'],
                        value_vars=['High_Risk_Pct', 'Medium_Risk_Pct'],
                        var_name='Risk_Type',
                        value_name='Percentage'
                    )
                    
                    # Clean up risk type names
                    risk_data_melted['Risk_Type'] = risk_data_melted['Risk_Type'].str.replace('_Pct', '')
                    risk_data_melted['Risk_Type'] = risk_data_melted['Risk_Type'].str.replace('_', ' ')
                    
                    fig = px.bar(
                        risk_data_melted,
                        x='Factor',
                        y='Percentage',
                        color='Risk_Type',
                        title=f'Risk Breakdown by {selected_factor}',
                        barmode='stack',
                        color_discrete_map={
                            'High Risk': COLORS['danger'],
                            'Medium Risk': COLORS['warning']
                        }
                    )
                    fig.update_layout(yaxis_title="Percentage (%)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show the data table
                    with st.expander(f"Show {selected_factor} Risk Data"):
                        st.dataframe(qualified_factors, use_container_width=True)
            else:
                st.warning("No suitable risk factors found in the data")
        
        # Prediction Tab
        with risk_tabs[2]:
            st.subheader("Risk Prediction Model")
            
            # This is a placeholder for a more sophisticated risk prediction model
            # In a real implementation, you would integrate with a machine learning model
            
            st.write("""
            This section would integrate with a machine learning model to predict the risk level for new contracts.
            
            Typical features for such a model might include:
            - Agent performance history
            - Customer demographics
            - Payment method reliability
            - Product type performance
            - Seasonal factors
            - Geographic factors
            """)
            
            # Create a simple demo of risk prediction
            st.subheader("Risk Prediction Demo")
            
            # Create simple form for risk prediction
            col1, col2 = st.columns(2)
            
            with col1:
                # Get available options from the data
                agents = ['Select Agent'] + sorted(df['AGENT'].unique().tolist()) if 'AGENT' in df.columns else []
                products = ['Select Product'] + sorted(df['PRODUCT'].unique().tolist()) if 'PRODUCT' in df.columns else []
                payment_methods = ['Select Payment Method'] + sorted(df['PAYMENT_METHOD'].unique().tolist()) if 'PAYMENT_METHOD' in df.columns else []
                
                # Form inputs
                selected_agent = st.selectbox("Agent", agents if agents else ["No Agent Data"])
                selected_product = st.selectbox("Product", products if products else ["No Product Data"])
                selected_payment = st.selectbox("Payment Method", payment_methods if payment_methods else ["No Payment Data"])
            
            with col2:
                # More form inputs
                month_options = ['January', 'February', 'March', 'April', 'May', 'June', 
                                'July', 'August', 'September', 'October', 'November', 'December']
                selected_month = st.selectbox("Enrollment Month", month_options)
                
                # Dummy fields for demo
                st.selectbox("Customer Age Range", ["18-25", "26-35", "36-45", "46-55", "56-65", "66+"])
                st.selectbox("Prior NSF History", ["None", "1 incident", "2+ incidents"])
            
            # Predict button
            if st.button("Predict Risk Level"):
                # This is a simplified demo calculation - not a real ML model
                # In reality, you would call your trained model here
                
                # Calculate risk factors based on historical data if possible
                agent_risk = 0
                if 'AGENT' in df.columns and selected_agent != 'Select Agent':
                    agent_data = df[df['AGENT'] == selected_agent]
                    if len(agent_data) > 0:
                        cancelled_rate = len(agent_data[agent_data['CATEGORY'] == 'CANCELLED']) / len(agent_data) * 100
                        agent_risk = cancelled_rate
                
                product_risk = 0
                if 'PRODUCT' in df.columns and selected_product != 'Select Product':
                    product_data = df[df['PRODUCT'] == selected_product]
                    if len(product_data) > 0:
                        cancelled_rate = len(product_data[product_data['CATEGORY'] == 'CANCELLED']) / len(product_data) * 100
                        product_risk = cancelled_rate
                
                payment_risk = 0
                if 'PAYMENT_METHOD' in df.columns and selected_payment != 'Select Payment Method':
                    payment_data = df[df['PAYMENT_METHOD'] == selected_payment]
                    if len(payment_data) > 0:
                        cancelled_rate = len(payment_data[payment_data['CATEGORY'] == 'CANCELLED']) / len(payment_data) * 100
                        payment_risk = cancelled_rate
                
                # Add some randomness for the demo
                base_risk = (agent_risk + product_risk + payment_risk) / 3
                random_factor = np.random.uniform(-5, 5)  # Add some randomness
                
                # Calculate final risk score (capped between 0-100)
                risk_score = min(max(base_risk + random_factor, 0), 100)
                
                # Determine risk level
                if risk_score < 20:
                    risk_level = "Very Low Risk"
                    risk_color = COLORS['med_green']
                elif risk_score < 40:
                    risk_level = "Low Risk"
                    risk_color = COLORS['light_green']
                elif risk_score < 60:
                    risk_level = "Medium Risk"
                    risk_color = COLORS['warning']
                elif risk_score < 80:
                    risk_level = "High Risk"
                    risk_color = COLORS['danger']
                else:
                    risk_level = "Very High Risk"
                    risk_color = "darkred"
                
                # Display the prediction result
                st.markdown(f"""
                <div style="background-color: {risk_color}; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-top: 20px;">
                    <h3>Predicted Risk Level: {risk_level}</h3>
                    <h2>Risk Score: {risk_score:.1f}%</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Show risk factors
                st.subheader("Risk Factor Breakdown")
                
                risk_factors = pd.DataFrame({
                    'Factor': ['Agent', 'Product', 'Payment Method', 'Seasonal', 'Random Factor'],
                    'Risk Score': [agent_risk, product_risk, payment_risk, 5.0, random_factor]
                })
                
                fig = px.bar(
                    risk_factors,
                    x='Factor',
                    y='Risk Score',
                    color='Risk Score',
                    color_continuous_scale=px.colors.sequential.Reds,
                    title='Contributing Risk Factors'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Recommendation based on risk level
                st.subheader("Recommendations")
                
                if risk_score < 40:
                    st.success("This contract appears to be low risk. Standard processing recommended.")
                elif risk_score < 70:
                    st.warning("""
                    This contract has moderate risk factors. Consider:
                    - Additional verification steps
                    - More frequent payment monitoring
                    - Customer outreach within first 30 days
                    """)
                else:
                    st.error("""
                    This contract shows high risk indicators. Recommended actions:
                    - Enhanced verification process
                    - Secure additional payment method as backup
                    - Weekly payment monitoring
                    - Proactive customer service outreach
                    - Consider requiring additional deposit
                    """)
    else:
        st.warning("Risk category data not available for analysis")
