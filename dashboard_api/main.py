# /dashboard_api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
import glob
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    incident_context: List[dict]
    history: List[Dict[str, Any]]

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
    
    return combined_df.replace({np.nan: None, pd.NaT: None})

# --- THIS IS THE MODIFIED PROMPT FUNCTION ---
def create_correlation_analysis_prompt(primary_incident, correlated_incidents_df):
    """Creates a highly structured prompt for a professional Gemini AI analysis."""
    
    correlated_incidents_str = ""
    if not correlated_incidents_df.empty:
        for _, row in correlated_incidents_df.iterrows():
            correlated_incidents_str += f"- Time: {row.get('event_time')} | Level: {row.get('level')} | Message: {row.get('message')}\n"
    else:
        correlated_incidents_str = "No other incidents found for this service in the time window."

    # This new prompt is very specific about the expected Markdown structure, including the table.
    prompt = f"""
You are a top-tier Principal Site Reliability Engineer (SRE). Your task is to perform a deep, correlated root cause analysis and generate a report in a specific Markdown format.

**Primary Incident for Analysis:**
- **Incident ID:** `{primary_incident.get('incident_id', 'N/A')}`
- **Service Affected:** `{primary_incident.get('service', 'N/A')}`
- **Raw Message:** `{primary_incident.get('message', 'N/A')}`

**Correlated Incidents (for context):**
{correlated_incidents_str}

**REPORTING INSTRUCTIONS:**
Generate a report with the following sections. Use Markdown H2 headings (##) for each section title EXACTLY as written below. Use bullet points (-) for lists.

## Incident Summary
Provide a one-paragraph summary of the entire event, explaining what happened and the immediate impact.

## Correlation and Timeline Analysis
(Provide a one-paragraph summary of the timeline. Then, YOU MUST create a Markdown table with the headers "Timestamp", "Event ID", and "Explanation". Populate it with the key events in chronological order.)
EXAMPLE of the required table format:
| Timestamp | Event ID | Explanation |
|---|---|---|
| 2025-08-10 20:53:07 | INC-0C334253 | Hardware failure detected, potential early indicator. |
| 2025-08-10 20:53:20 | SYS-0434 | Resource thresholds exceeded (CPU, Memory, Disk). |
| 2025-08-10 21:14:00 | INC-43E30A42 | The primary hardware failure incident occurs. |

## Hypothesized Root Cause
Based on all available data, state the single most likely root cause. Be specific.

## Recommended Action Plan
Provide a clear, actionable checklist for remediation in one sentence and then list the following short term and long term actions.

### Short-term (Immediate Containment)
- Actionable step 1 (e.g., Roll back the affected service).
- Actionable step 2 (e.g., Increase resource allocation).

### Long-term (Prevention)
- Actionable step 1 (e.g., Add memory profiling to the CI/CD pipeline).
- Actionable step 2 (e.g., Implement stricter alerting).
"""
    return prompt

# --- API Endpoints ---

@app.get("/api/kpis")
async def get_kpis():
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
    df = load_incident_data_sync()
    if df.empty:
        return []
    return df.to_dict(orient='records')

@app.post("/api/analyze/{incident_id}")
async def analyze_incident(incident_id: str):
    if not model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured on the server.")
    
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
    
@app.post("/api/chat")
async def handle_chat(request: ChatRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Gemini API is not configured on the server.")

    history_str = "\n".join([f"- {msg.get('role')}: {msg.get('content')}" for msg in request.history])
    incident_context_str = "\n".join([f"- {inc.get('event_time')}: {inc.get('message')}" for inc in request.incident_context])

    prompt = f"""
You are a world-class SRE AI Chat Assistant named 'iPulse'. Your goal is to help engineers troubleshoot issues. You have memory of the current conversation.

Current Conversation History (for context):
{history_str}

Recent Incident Context (for context):
{incident_context_str}

User's New Message:
"{request.message}"

Based on the conversation history AND the recent incident context, provide a helpful and relevant response to the user's new message. Address the user directly.
"""

    try:
        response = model.generate_content(prompt)
        return {"reply": response.text}
    except Exception as e:
        print(f"ERROR during LLM chat generation: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during AI chat generation: {e}")