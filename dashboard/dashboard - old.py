import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
import time
import glob

# Set up the dashboard
st.set_page_config(
    page_title="Tamer Incident Analysis",
    layout="wide",
    page_icon="🚨"
)

st.title("🚨 Real-Time Incident Analysis Dashboard")

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    st.error("⚠️ GEMINI_API_KEY environment variable not found!")
    st.stop()

# Define the path to incident data
INCIDENT_DATA_PATH = "/opt/spark-data/data/enriched_incidents_hourly/"

def load_incident_data():
    """
    Load and process incident data from CSV files
    """
    try:
        # Check if directory exists
        if not os.path.exists(INCIDENT_DATA_PATH):
            st.warning(f"📁 Data directory not found: {INCIDENT_DATA_PATH}")
            return pd.DataFrame()
        
        # Get list of all CSV files
        csv_files = glob.glob(os.path.join(INCIDENT_DATA_PATH, "*.csv"))
        
        if not csv_files:
            st.info("📄 No CSV files found in the data directory")
            return pd.DataFrame()
        
        # Read all CSV files into a single DataFrame
        dataframes = []
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                dataframes.append(df)
            except Exception as e:
                st.warning(f"⚠️ Error reading file {file}: {str(e)}")
                continue
        
        if not dataframes:
            return pd.DataFrame()
        
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=True)
        
        # Sort by event_time in descending order (most recent first)
        if 'event_time' in combined_df.columns:
            combined_df = combined_df.sort_values('event_time', ascending=False)
        
        return combined_df
        
    except FileNotFoundError as e:
        st.error(f"📁 File not found: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading incident data: {str(e)}")
        return pd.DataFrame()

def create_analysis_prompt(incident_data):
    """
    Create a detailed prompt for Gemini AI analysis
    """
    prompt = f"""
You are a professional IT operations engineer with expertise in incident management and root cause analysis. 
Please analyze the following incident data and provide a comprehensive assessment.

**INCIDENT DETAILS:**
- **Incident ID:** {incident_data.get('incident_id', 'N/A')}
- **Severity Level:** {incident_data.get('level', 'N/A')}
- **Service Affected:** {incident_data.get('service', 'N/A')}
- **Category:** {incident_data.get('category', 'N/A')}
- **Event Time:** {incident_data.get('event_time', 'N/A')}
- **Message:** {incident_data.get('message', 'N/A')}
- **Affected Users:** {incident_data.get('affected_users', 'N/A')}
- **Duration:** {incident_data.get('duration', 'N/A')} minutes
- **System ID:** {incident_data.get('system_id', 'N/A')}
- **Is Critical:** {incident_data.get('is_critical', 'N/A')}

**ANALYSIS REQUIRED:**

Please provide your analysis in the following structured format using Markdown:

## 🔍 Root Cause Analysis

Analyze the incident data and identify:
- Primary root cause
- Contributing factors
- System vulnerabilities exposed
- Timeline of events (if determinable)

## 📋 Recommended Action Plan

Provide specific, actionable recommendations including:

### Immediate Actions (0-2 hours)
- Emergency response steps
- Containment measures
- Communication requirements

### Short-term Actions (2-24 hours)
- Resolution steps
- Monitoring requirements
- Stakeholder updates

### Long-term Actions (1-30 days)
- Preventive measures
- System improvements
- Process enhancements

## ⚠️ Risk Assessment

Evaluate:
- Business impact severity
- Potential for recurrence
- Related system vulnerabilities

## 📊 Key Metrics & KPIs

Suggest relevant metrics to monitor for:
- Prevention of similar incidents
- System health indicators
- Performance benchmarks

Please ensure your analysis is professional, actionable, and based on industry best practices for IT incident management.
"""
    return prompt

# Create placeholder for auto-refresh
placeholder = st.empty()

# Auto-refresh loop
while True:
    with placeholder.container():
        # Load incident data
        df = load_incident_data()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total Incidents", len(df))
        
        with col2:
            if not df.empty and 'is_critical' in df.columns:
                critical_count = df['is_critical'].sum() if df['is_critical'].dtype == bool else len(df[df['is_critical'] == True])
                st.metric("🚨 Critical Incidents", critical_count)
            else:
                st.metric("🚨 Critical Incidents", "N/A")
        
        with col3:
            if not df.empty and 'level' in df.columns:
                error_count = len(df[df['level'].str.upper() == 'ERROR']) if 'level' in df.columns else 0
                st.metric("❌ Error Level", error_count)
            else:
                st.metric("❌ Error Level", "N/A")
        
        with col4:
            if not df.empty and 'service' in df.columns:
                unique_services = df['service'].nunique() if 'service' in df.columns else 0
                st.metric("🔧 Affected Services", unique_services)
            else:
                st.metric("🔧 Affected Services", "N/A")
        
        st.markdown("---")
        
        # Display main data table
        if not df.empty:
            st.subheader(f"📊 Incident Data Table ({len(df)} records)")
            
            # Add filters
            col1, col2 = st.columns(2)
            with col1:
                if 'level' in df.columns:
                    level_filter = st.selectbox(
                        "Filter by Level:",
                        options=['All'] + list(df['level'].unique()),
                        key="level_filter"
                    )
                    if level_filter != 'All':
                        df = df[df['level'] == level_filter]
            
            with col2:
                if 'service' in df.columns:
                    service_filter = st.selectbox(
                        "Filter by Service:",
                        options=['All'] + list(df['service'].dropna().unique()),
                        key="service_filter"
                    )
                    if service_filter != 'All':
                        df = df[df['service'] == service_filter]
            
            # Display filtered data
            st.dataframe(
                df,
                use_container_width=True,
                height=400
            )
            
            # AI Analysis Section
            if not df.empty and 'incident_id' in df.columns:
                st.markdown("---")
                st.subheader("🔬 Select an Incident for AI Analysis")
                
                # Create incident selection dropdown
                incident_options = df['incident_id'].dropna().unique().tolist()
                
                if incident_options:
                    selected_incident_id = st.selectbox(
                        "Choose an incident to analyze:",
                        options=incident_options,
                        key="incident_selector"
                    )
                    
                    if selected_incident_id:
                        # Get selected incident data
                        selected_incident = df[df['incident_id'] == selected_incident_id].iloc[0]
                        
                        # Display incident details
                        st.subheader(f"📋 Incident Details: {selected_incident_id}")
                        
                        # Create columns for incident details
                        detail_col1, detail_col2 = st.columns(2)
                        
                        with detail_col1:
                            st.write("**Basic Information:**")
                            st.write(f"- **Level:** {selected_incident.get('level', 'N/A')}")
                            st.write(f"- **Service:** {selected_incident.get('service', 'N/A')}")
                            st.write(f"- **Category:** {selected_incident.get('category', 'N/A')}")
                            st.write(f"- **Event Time:** {selected_incident.get('event_time', 'N/A')}")
                        
                        with detail_col2:
                            st.write("**Impact Information:**")
                            st.write(f"- **Affected Users:** {selected_incident.get('affected_users', 'N/A')}")
                            st.write(f"- **Duration:** {selected_incident.get('duration', 'N/A')} minutes")
                            st.write(f"- **Critical:** {selected_incident.get('is_critical', 'N/A')}")
                            st.write(f"- **System ID:** {selected_incident.get('system_id', 'N/A')}")
                        
                        # Display full message
                        st.write("**Incident Message:**")
                        st.code(selected_incident.get('message', 'N/A'), language=None)
                        
                        # Analysis button
                        if st.button("🤖 Analyze with AI", type="primary"):
                            with st.spinner("🤖 Gemini is analyzing the incident..."):
                                try:
                                    # Create analysis prompt
                                    prompt = create_analysis_prompt(selected_incident.to_dict())
                                    
                                    # Generate AI response
                                    response = model.generate_content(prompt)
                                    
                                    # Display AI analysis
                                    st.markdown("---")
                                    st.subheader("🤖 AI Analysis Results")
                                    st.markdown(response.text)
                                    
                                except Exception as e:
                                    st.error(f"❌ Error during AI analysis: {str(e)}")
                else:
                    st.info("No incident IDs available for analysis")
        else:
            st.info("📭 No incident data available. Waiting for data...")
            st.markdown("""
            **Possible reasons:**
            - Spark streaming job hasn't started yet
            - No incidents have been generated
            - Data directory path is incorrect
            - CSV files haven't been created yet
            """)
        
        # Auto-refresh indicator
        st.markdown("---")
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"🔄 Last updated: {current_time} | Auto-refreshing every 10 seconds...")
    
    # Wait 10 seconds before refreshing
    time.sleep(10)