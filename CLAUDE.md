# CLAUDE.md

This file provides guidance for Claude Code instances working in this repository.

## Common Commands

```bash
# Install dependencies (using uv package manager)
uv sync

# Run the Streamlit coaching app
uv run streamlit run app.py

# Run tests
uv run pytest

# Sync Garmin data
uv run python -m coach_conejito.garmin_sync
```

## High-Level Architecture

Coach Conejito is an AI-powered running coach that provides personalized training advice based on your running data.

### Core Workflow

1. **Data Aggregation**: Garmin data (activities, sleep, daily summaries) is synced and stored locally in JSON files
2. **Context Construction**: The `prepare_context_for_ai()` function aggregates recent data into a structured context
3. **LLM Generation**: The context is sent to an LLM backend with a system prompt to generate coaching advice

### Multi-Backend LLM Support

The system supports three LLM backends via `coach_conejito/llm_backends.py`:

- **Gemini** (default): Uses Google's Gemini API via `google-generativeai`
- **Ollama**: Local models via Ollama's API
- **MLX**: Apple Silicon-optimized local inference via `mlx-lm`

Backend selection is controlled by `COACH_LLM_BACKEND` environment variable and can be changed in the Streamlit UI.

### Data Storage

All data is stored locally in `~/.coach_conejito/`:
- `garmin_tokens.json`: OAuth tokens for Garmin API (auto-refreshed)
- `garmin_data/`: JSON files for activities, sleep, and daily summaries
- `coaching_history.json`: Chat history and generated advice

### Garmin Integration

OAuth flow is handled by `garmin_sync.py`:
- Initial authorization opens browser and starts local callback server
- Tokens are persisted and automatically refreshed
- Sync fetches last 30 days of data by default

## Key Files

- `app.py`: Streamlit UI for the coaching chat interface
- `coach_conejito/coach_ai.py`: Core coaching logic and context preparation
- `coach_conejito/garmin_sync.py`: Garmin API OAuth and data synchronization
- `coach_conejito/llm_backends.py`: LLM backend abstraction layer
- `tests/test_coach.py`: Unit tests for coaching functionality

## Testing

Tests use pytest with fixtures for mock data. Run `uv run pytest` to execute.

The test suite includes:
- LLM backend mocking to avoid API calls
- Sample Garmin data for context preparation
- Validation of coaching advice generation

## Important Patterns

### LLM Backend Configuration

The system uses a factory pattern for LLM backends. Each backend implements `generate_response(messages)` and returns a string. Environment variables control API keys and backend selection:

```python
# In coach_ai.py
backend = get_llm_backend()  # Auto-selects based on COACH_LLM_BACKEND
response = backend.generate_response(messages)
```

### Token Persistence

Garmin OAuth tokens are saved to `~/.coach_conejito/garmin_tokens.json` and automatically loaded on subsequent runs. The `GarminSync` class handles refresh token logic internally - no manual token management needed.

### Data Aggregation Strategy

`prepare_context_for_ai()` in `coach_ai.py` aggregates the last 7 days of data by default. It combines:
- Daily summaries (steps, HR, stress, sleep)
- Detailed activities (runs with pace, HR zones, distance)
- Recent sleep data (stages, scores)

This creates a comprehensive but focused context window for the LLM.

### System Prompt Location

The coaching system prompt is defined in `coach_ai.py` as `SYSTEM_PROMPT`. It instructs the LLM to act as a running coach and provides guidelines for advice generation. Modify this to change the coach's personality or focus areas.
