# /dashboard_api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
import glob
import google.generativeai as genai

app = FastAPI(title="Incident Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INCIDENT_DATA_PATH = "/opt/spark-data/data/enriched_incidents_hourly/"

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
else:
    print("WARNING: GEMINI_API_KEY environment variable not found!")

# --- Helper Functions ---

def load_incident_data_sync():
    """Loads and cleans incident data from CSV files."""
    if not os.path.exists(INCIDENT_DATA_PATH):
        return pd.DataFrame()
    csv_files = glob.glob(os.path.join(INCIDENT_DATA_PATH, "*.csv"))
    if not csv_files:
        return pd.DataFrame()
    
    dataframes = [pd.read_csv(file) for file in csv_files if os.path.getsize(file) > 0]
    if not dataframes:
        return pd.DataFrame()
    
    combined_df = pd.concat(dataframes, ignore_index=True)
    if 'event_time' in combined_df.columns:
        combined_df['event_time'] = pd.to_datetime(combined_df['event_time'])
        combined_df = combined_df.sort_values('event_time', ascending=False)
    
    # This function now handles all the cleaning.
    return combined_df.replace({np.nan: None, pd.NaT: None})

def create_correlation_analysis_prompt(primary_incident, correlated_incidents_df):
    """Creates a detailed prompt for Gemini AI analysis."""
    correlated_str = ""
    if not correlated_incidents_df.empty:
        for _, row in correlated_incidents_df.iterrows():
            correlated_str += f"- Time: {row.get('event_time')} | Level: {row.get('level')} | Message: {row.get('message')}\n"
    else:
        correlated_str = "No other incidents found for this service in the time window."
    
    return f"""
    **PRIMARY INCIDENT FOR ANALYSIS:**
    - Incident ID: {primary_incident.get('incident_id', 'N/A')}
    - Raw Message: {primary_incident.get('message', 'N/A')}

    **CORRELATED INCIDENTS:**
    {correlated_str}

    **ANALYSIS REQUIRED:**
    Provide a root cause analysis and recommended action plan.
    """

# --- API Endpoints ---

@app.get("/api/kpis")
async def get_kpis():
    # We get the already cleaned DataFrame here.
    df = load_incident_data_sync()
    if df.empty:
        return {"total": 0, "critical": 0, "warning": 0, "services": 0}
    
    return {
        "total": len(df),
        "critical": len(df[df['level'] == 'ERROR']),
        "warning": len(df[df['level'] == 'WARNING']),
        "services": df['service'].nunique() if 'service' in df.columns else 0
    }

@app.get("/api/incidents")
async def get_incidents():
    # We get the already cleaned DataFrame here.
    df = load_incident_data_sync()
    if df.empty:
        return []
    return df.to_dict(orient='records')

@app.post("/api/analyze/{incident_id}")
async def analyze_incident(incident_id: str):
    if not model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured on the server.")
    
    # We get the already cleaned DataFrame here.
    df = load_incident_data_sync()
    if df.empty:
        raise HTTPException(status_code=404, detail="Incident data is currently unavailable.")
    
    primary_incident_df = df[df['incident_id'] == incident_id]
    if primary_incident_df.empty:
        raise HTTPException(status_code=404, detail=f"Incident with ID '{incident_id}' not found.")
    
    primary_incident = primary_incident_df.iloc[0]
    incident_time = pd.to_datetime(primary_incident['event_time'])
    time_window = pd.Timedelta(minutes=30)
    
    correlated_df = df[
        (df['service'] == primary_incident['service']) &
        (pd.to_datetime(df['event_time']) >= incident_time - time_window) &
        (pd.to_datetime(df['event_time']) <= incident_time + time_window) &
        (df['incident_id'] != incident_id)
    ]

    try:
        prompt = create_correlation_analysis_prompt(primary_incident.to_dict(), correlated_df)
        response = model.generate_content(prompt)
        return {"analysis": response.text}
    except Exception as e:
        print(f"ERROR during Gemini analysis: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during AI analysis: {e}")