# Coach Conejito - Technical Architecture

## 1. System Overview
Coach Conejito is a personal training assistant that combines quantitative data (Strava/Garmin) with qualitative data (User Journals) to generate adaptive training plans using Google Gemini.

## 2. Directory Structure
```
/
├── data/
│   ├── raw/               # Raw JSON/FIT files from providers
│   ├── processed/         # Normalized JSON/Parquet data (Activity DataFrame)
│   ├── journal/           # Daily text/markdown entries
│   └── profile/           # User settings and profile.yaml
├── src/
│   ├── app.py             # Main Streamlit Dashboard entry point
│   ├── pages/             # Multi-page Streamlit views (Journal, Settings)
│   ├── modules/
│   │   ├── strava_client.py   # Strava API interaction
│   │   ├── garmin_parser.py   # FIT/TCX file parsing (using fitparse)
│   │   ├── gemini_coach.py    # AI prompting and logic
│   │   └── data_manager.py    # Pandas aggregation and file I/O
├── scripts/               # Standalone scripts (cron jobs for fetching data)
├── requirements.txt       # Python dependencies
└── .streamlit/
    └── config.toml        # Theme and server settings
```

## 3. Data Flow

### A. Data Ingestion
1.  **Strava:**
    *   Python script (`modules/strava_client.py`) performs OAuth2.
    *   Fetches recent activities via `requests`.
    *   Saves raw JSON responses to `data/raw/strava/`.
2.  **Garmin:**
    *   User places `.fit` files into `data/inbox/`.
    *   `modules/garmin_parser.py` uses `fitparse` library to extract metrics.
    *   Parsed data is normalized and merged.
3.  **Normalization:**
    *   All data is converted into a Pandas DataFrame with a standard schema:
        *   `date` (datetime)
        *   `source` (str)
        *   `activity_type` (str)
        *   `distance_km` (float)
        *   `duration_min` (float)
        *   `avg_hr` (int)
        *   `rpe` (int, from journal)

### B. The AI Loop
1.  **Context Construction:**
    *   Load `data/profile/user.yaml` (Goals, Injuries).
    *   Filter Pandas DataFrame for last 14-30 days of activity.
    *   Read recent journal entries.
2.  **Prompting:**
    *   Construct a prompt for Google Gemini: "Analyze this training data..."
3.  **Output:**
    *   Gemini returns the plan in Markdown format.
    *   Displayed directly in the Streamlit UI and saved to `data/plan/current_week.md`.

## 4. Tech Stack Details
-   **Core:** Python 3.10+
-   **UI Framework:** Streamlit (for rapid dashboard creation).
-   **Data Processing:** Pandas (aggregation), Fitparse (Garmin files).
-   **AI:** Google Generative AI SDK (`google-generativeai`).
-   **Configuration:** YAML for config, Streamlit secrets for API keys.

## 5. Security
-   API Keys (Gemini, Strava Client Secret) stored in `.streamlit/secrets.toml`.
-   **Never commit `.env` or `secrets.toml` files.**
-   Local-first architecture ensures personal data resides on the user's machine.