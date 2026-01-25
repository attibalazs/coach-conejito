# Coach Conejito

## Detailed Project Plan

### Phase 1: Foundation & Data Ingestion
- **Tech Stack:** Python, Pandas.
- **Data Sources:**
    - **Strava:** Python script to authenticate and fetch activities via API.
    - **Garmin:** Support for parsing local `.fit` files using `fitparse`.
- **Storage:** Local file-based storage using JSON/CSV for activity logs.

### Phase 2: The AI Coach (Core Logic)
- **Integration:** Google Gemini API (`google-generativeai`).
- **Workflow:**
    1.  **Aggregator:** Python logic to merge DataFrame stats with text journals.
    2.  **Analysis:** Send context to Gemini to analyze training load and subjective feedback.
    3.  **Output:** Generate a structured training plan displayed in the UI.

### Phase 3: User Interface
- **Framework:** Streamlit.
- **Dashboard:** Interactive charts (Altair/Plotly) showing volume, intensity, and compliance.
- **Journaling:** Streamlit forms for daily RPE and subjective notes.
- **Plan View:** Markdown rendering of the AI-generated schedule.

### Phase 4: Automation
- **Scheduling:** Simple shell scripts or Python functions to run daily updates.
- **Distribution:** Run locally on demand.

## Quick Start
- `pip install -r requirements.txt`: Install dependencies.
- `streamlit run src/app.py`: Launch the Coach Conejito dashboard.
