# Coach Conejito

## Project Overview
**Coach Conejito** is an AI-powered personal running coach application. It aggregates objective training data (from Garmin) and subjective athlete feedback (daily journals) to generate adaptive training plans using Large Language Models (LLMs).

The application is built with **Python** and **Streamlit**, designed to run locally for privacy and control. It supports multiple LLM backends including Google Gemini (Cloud), Ollama (Local), and MLX (macOS Native).

## Key Features
-   **AI Coaching:** Generates daily/weekly training prescriptions based on fatigue, load, and goals.
-   **Garmin Integration:** Syncs activities directly from Garmin Connect.
-   **Journaling:** specific subjective metrics (RPE, Mood, Soreness) that the AI considers alongside hard data.
-   **Local-First Data:** All data is stored in local JSON/YAML files under the `data/` directory.

## Technical Architecture

### Directory Structure
-   `src/app.py`: Main entry point for the Streamlit application.
-   `src/modules/`:
    -   `gemini_coach.py`: Core logic for constructing prompts and calling LLM APIs (Gemini, Ollama, MLX).
    -   `garmin_client.py`: Handles Garmin Connect authentication (`garth`) and activity syncing.
    -   `data_manager.py`: Handles file I/O for user profiles, journals, and activity logs.
-   `data/`: Storage for user data (gitignored, except for structure).
    -   `users/{user_id}/`: Dedicated folder for each athlete containing `raw/`, `journal/`, and `profile/`.

### Tech Stack
-   **Frontend/App:** Streamlit
-   **Data Processing:** Pandas, Python standard library
-   **LLM Integration:** `google-generativeai`, `mlx-lm`, `requests` (for Ollama)
-   **Garmin API:** `garminconnect` (unofficial API wrapper)

## Development & Usage

### Prerequisites
-   Python 3.10+
-   A Garmin Connect account (for data sync)
-   API Key for Google Gemini (optional, if using Cloud) or a local Ollama/MLX setup.

### Installation
This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

```bash
# Install dependencies
uv sync
```

### Running the App
```bash
# Run with uv
uv run streamlit run src/app.py
```

### Key Workflows
1.  **Onboarding:** Create a user in the sidebar.
2.  **Sync Data:** Go to "Settings" -> "Garmin" to login and sync recent activities.
3.  **Journal:** Log daily subjective feelings in the "Journal" tab.
4.  **Chat/Plan:** Use the "Command Center" to chat with the AI Coach. The AI has access to your recent training load and journal entries to provide context-aware advice.

## Configuration
-   **LLM Selection:** Models can be switched dynamically in the Settings or Chat UI.
-   **System Prompts:** Custom system prompts can be defined per model/user in the Settings to tweak the coaching style.
