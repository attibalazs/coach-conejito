# 🐰 Coach Conejito

**AI-powered personal running coach with privacy-first Garmin integration**

Coach Conejito combines your Garmin training data with AI-driven analysis to provide personalized running coaching advice. Built on a local-first, multi-athlete architecture with support for multiple LLM backends (Gemini, Ollama, MLX).

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**What it does:** Coach Conejito syncs your Garmin activities, combines them with subjective journal entries (RPE, mood, soreness), and uses AI to provide personalized training advice through an interactive chat interface.

**Why it exists:**
- **Privacy-first**: All data stored locally in JSON files (no cloud database)
- **Multi-athlete**: Manage training for multiple athletes from one installation
- **Flexible AI**: Choose between cloud (Gemini) or local (Ollama, MLX) models
- **Contextual coaching**: AI coach sees your training load, recent activities, and subjective feedback

**Key differentiators:**
- Runs entirely on your machine (except optional Gemini API calls)
- Stores Garmin credentials locally with automatic token refresh
- Per-model custom system prompts for coaching personalization
- Rolling chat history with persistent active training plans

---

## Features

### Core Functionality
- **Garmin Integration**: OAuth-based sync with automatic token persistence
- **Daily Journaling**: Track RPE, mood, soreness, and notes
- **AI Coaching Chat**: Interactive conversation with context-aware coach
- **Active Training Plans**: Pin AI responses as your current training plan
- **Multi-Athlete Support**: Manage separate data/profiles for multiple athletes

### LLM Backends
Choose from three backend types:
- **Gemini (Cloud)**: `gemini-1.5-flash`, `gemini-1.5-pro` via Google AI API
- **Ollama (Local)**: Any Ollama model (e.g., `deepseek-r1:8b`, `qwen2.5-coder`, `phi4`)
- **MLX (macOS Native)**: Apple Silicon-optimized models (e.g., `mlx-deepseek-8b`, `mlx-phi4`)

### Data & Privacy
- **Local-first storage**: All data in `data/users/<athlete_id>/`
- **Persistent tokens**: Garmin OAuth tokens automatically refreshed
- **No external dependencies**: Runs offline (except for Garmin sync and Gemini API)
- **Per-athlete isolation**: Each athlete's data completely separated

### Training Analysis
- **Weekly/Monthly/Yearly aggregates**: Pre-computed training load statistics
- **Activity details**: Distance, pace, HR, elevation, cadence, Training Effect
- **Subjective correlation**: AI sees both objective metrics and how you feel
- **Custom prompts**: Tailor coaching style per model (stored per athlete)

---

## Quick Start

Get running in 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/coach-conejito.git
cd coach-conejito

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. (Optional) Set up Gemini API key
# For Gemini models only - skip if using Ollama/MLX
echo "GEMINI_API_KEY=your-api-key-here" > .env

# 5. Run the application
uv run streamlit run src/app.py
```

**First-time setup in the UI:**
1. Create an athlete profile in the sidebar
2. Go to **Settings** → **Garmin** and log in
3. Click **Sync Last 7 Days** to import activities
4. Go to **Journal** and add your first entry
5. Return to **Command Center** and chat with your coach

---

## Installation

### Prerequisites
- **Python 3.9+** (Python 3.11+ recommended)
- **uv** or **pip** package manager
- **Garmin Connect account** (for activity sync)
- **LLM access** (one of):
  - Gemini API key ([get one here](https://ai.google.dev/))
  - Ollama installed locally ([installation guide](https://ollama.ai/))
  - Apple Silicon Mac for MLX models

### Installation with uv (Recommended)

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/yourusername/coach-conejito.git
cd coach-conejito
uv sync
```

### Alternative Installation with pip

```bash
git clone https://github.com/yourusername/coach-conejito.git
cd coach-conejito
pip install -r requirements.txt  # Note: requirements.txt not included, use uv or generate from pyproject.toml
```

### Environment Variables

Create a `.env` file in the project root (optional, only for Gemini):

```bash
GEMINI_API_KEY=your-gemini-api-key-here
```

Alternatively, enter your API key directly in the **Settings** page of the Streamlit UI.

---

## Usage

### Running the Application

```bash
uv run streamlit run src/app.py
```

The app will open in your browser at `http://localhost:8501`.

### Key Workflows

#### 1. Athlete Management
- Click **➕ New Athlete** in the sidebar
- Enter a unique athlete ID (e.g., `john`, `sarah_ultra`)
- Switch between athletes using the dropdown

#### 2. Syncing Garmin Data
- Go to **Settings** → **Garmin**
- Enter your Garmin Connect email/password
- Click **Login & Sync** (optionally enable bulk sync for last 30 days)
- Tokens are saved locally and auto-refresh on subsequent syncs
- Use **Sync Last 7 Days** for quick updates

#### 3. Daily Journaling
- Navigate to **Journal** page
- Fill in:
  - Date (defaults to today)
  - RPE (Rate of Perceived Exertion, 1-10)
  - Mood (emoji scale)
  - Soreness (0-10)
  - Notes (freeform text)
- Click **Save**

#### 4. Chatting with Your AI Coach
- Go to **Command Center** → **Coach Chat**
- Select your preferred model from the dropdown
- Type questions like:
  - "What should I run tomorrow?"
  - "Am I overtraining?"
  - "Plan my next week"
- Click **📌 Set last response as Active Plan** to pin advice

#### 5. Switching LLM Models
Select from the dropdown in **Command Center** or **Settings**:
- `gemini-1.5-flash` (fast, requires API key)
- `deepseek-r1:8b` (Ollama, requires Ollama running)
- `mlx-phi4` (MLX, requires Apple Silicon)

---

## Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)                 │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │ Command Center│  │    Journal    │  │   Settings  │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
└────────────┬────────────────┬────────────────┬─────────┘
             │                │                │
             ▼                ▼                ▼
┌────────────────────────────────────────────────────────┐
│                    Core Modules                        │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ gemini_coach.py │  │data_manager.py│ │garmin_    │ │
│  │ (Multi-LLM)     │  │ (File I/O)    │ │client.py  │ │
│  └─────────────────┘  └──────────────┘  └───────────┘ │
└────────────┬────────────────┬────────────────┬─────────┘
             │                │                │
             ▼                ▼                ▼
┌────────────────────────────────────────────────────────┐
│              Local Data Storage                        │
│  data/users/<athlete_id>/                              │
│    ├── journal/          (daily entries as JSON)       │
│    ├── profile/          (user.yaml, chat_history.json)│
│    │   ├── prompts/      (per-model custom prompts)    │
│    │   └── garmin_tokens/ (OAuth tokens)               │
│    └── raw/garmin/       (activity_*.json files)       │
└────────────────────────────────────────────────────────┘
```

### Project Structure

```
coach-conejito/
├── src/
│   ├── app.py                    # Streamlit UI entry point
│   └── modules/
│       ├── gemini_coach.py       # Multi-LLM backend + context builder
│       ├── garmin_client.py      # Garmin OAuth + sync logic
│       └── data_manager.py       # File I/O for all data types
├── tests/
│   ├── test_gemini_coach.py      # LLM backend tests
│   ├── test_garmin_client.py     # Garmin sync tests
│   ├── test_data_manager.py      # Data persistence tests
│   └── conftest.py               # Pytest fixtures
├── data/                          # Created at runtime (gitignored)
├── pyproject.toml                # Project dependencies (uv)
├── CLAUDE.md                     # Developer documentation
└── readme.md                     # This file
```

### Key Components

#### `gemini_coach.py` (Multi-LLM Backend)
- **Context Builder**: Aggregates athlete profile, Garmin activities, journals into LLM prompt
- **Training Stats**: Pre-computes weekly/monthly/yearly metrics
- **Backend Routing**: Auto-selects Gemini/Ollama/MLX based on model name
- **Prompt Management**: Per-model custom system prompts with athlete data appended

#### `garmin_client.py` (OAuth & Sync)
- **Token Persistence**: Saves Garmin OAuth tokens to `profile/garmin_tokens/`
- **Auto Refresh**: Reuses tokens across sessions, refreshes when expired
- **Chunked Sync**: Fetches activities in 30-day chunks to prevent API timeouts
- **Error Handling**: Detects corrupt tokens, session expiry, bulk sync limits

#### `data_manager.py` (File I/O)
- **User Isolation**: Each athlete gets separate directory tree
- **JSON/YAML Storage**: Activities (JSON), profile (YAML), journals (JSON)
- **Chat History**: Persists conversation state per athlete
- **Prompt Storage**: Custom system prompts saved per (athlete, model) pair

### Data Flow

1. **User syncs Garmin** → `garmin_client.py` fetches activities → Saved to `data/users/<id>/raw/garmin/`
2. **User adds journal entry** → `data_manager.py` writes to `journal/<date>.json`
3. **User sends chat message** → `gemini_coach.py` builds context from Garmin + journals + profile
4. **AI generates response** → Backend (Gemini/Ollama/MLX) called via unified interface
5. **Response displayed** → Appended to chat history → Persisted to disk

---

## Configuration

### LLM Backend Selection

**In the UI:** Use the model dropdown in **Command Center** or **Settings**.

**Adding new models:** Edit `MODEL_OPTIONS` in `src/app.py`:

```python
MODEL_OPTIONS = [
    "deepseek-r1:8b",       # Ollama
    "mlx-phi4",             # MLX
    "gemini-1.5-flash",     # Gemini
    "your-custom-model"     # Add here
]
```

### Custom System Prompts

1. Go to **Settings** → **System Prompt**
2. Edit the coaching instructions (training rules, response format, style)
3. Click **Save Prompt** (saved per model)
4. Click **Reset to Default** to restore the built-in prompt

**Storage location:** `data/users/<athlete_id>/profile/prompts/<model_name>.txt`

### User Profile Configuration

**Settings** → **Profile**:
- **Goals**: E.g., "Run a sub-3 hour marathon"
- **Injuries**: E.g., "Left knee patellar tendonitis"

This information is automatically included in every AI prompt.

### Garmin Token Management

Tokens are stored in `data/users/<athlete_id>/profile/garmin_tokens/` and managed automatically:
- **First login**: Tokens saved after successful authentication
- **Subsequent syncs**: Tokens reused and refreshed
- **Expiry handling**: Prompts re-login if refresh fails
- **Manual reset**: Check **Force Re-login** in **Settings** → **Garmin**

---

## Development

### Setting Up Dev Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/yourusername/coach-conejito.git
cd coach-conejito
uv sync

# Verify installation
uv run pytest
```

### Project Commands

```bash
# Run the app
uv run streamlit run src/app.py

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Sync Garmin data (standalone script, if implemented)
uv run python -m src.modules.garmin_client
```

### Code Organization Patterns

#### Adding a New LLM Backend

Edit `src/modules/gemini_coach.py` in the `get_ai_coach_response()` function:

```python
# Example: Add OpenAI backend
if model_name.startswith("gpt-"):
    import openai
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[{"role": "system", "content": full_prompt}]
    )
    return response.choices[0].message.content, time.time() - start_time
```

#### Adding a New Data Type

1. Add storage functions in `data_manager.py`:
   ```python
   def save_my_data(user_id, data):
       _, profile_dir, _ = ensure_user_dirs(user_id)
       with open(os.path.join(profile_dir, "my_data.json"), "w") as f:
           json.dump(data, f)
   ```

2. Update UI in `app.py` to display/edit

3. Update `gemini_coach.py` context builder if AI needs access

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_gemini_coach.py

# Run with coverage report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html  # View coverage in browser
```

### Coverage Reporting

```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=term-missing

# HTML report for detailed line-by-line coverage
uv run pytest --cov=src --cov-report=html
```

### Test Fixtures Overview

Located in `tests/conftest.py`:
- **`mock_user_id`**: Temporary test athlete ID
- **`mock_garmin_data`**: Sample activity JSON
- **`mock_journal_entries`**: Sample RPE/mood/soreness data
- **`mock_ollama_response`**: Fake Ollama API response

### Writing New Tests

```python
# tests/test_my_feature.py
def test_my_feature(mock_user_id):
    from modules.data_manager import save_my_data, load_my_data

    save_my_data(mock_user_id, {"key": "value"})
    result = load_my_data(mock_user_id)

    assert result["key"] == "value"
```

---

## Troubleshooting

### Common Issues

#### Garmin Authentication Failures

**Symptoms:** "Session expired" or "Login failed" errors

**Solutions:**
1. Click **Force Re-login** in **Settings** → **Garmin**
2. Verify email/password are correct
3. Check if Garmin account is locked (try logging in on Garmin Connect website)
4. Clear corrupt tokens manually:
   ```bash
   rm -rf data/users/<athlete_id>/profile/garmin_tokens/
   ```

#### MLX Models Not Loading

**Symptoms:** "Error with MLX: No module named 'mlx_lm'"

**Solutions:**
1. Verify Apple Silicon Mac (MLX requires M1/M2/M3/M4)
2. Reinstall dependencies:
   ```bash
   uv sync --reinstall-package mlx-lm
   ```
3. Check model name mapping in `gemini_coach.py` (lines 189-194)

#### Ollama Connection Issues

**Symptoms:** "Could not connect to Ollama"

**Solutions:**
1. Verify Ollama is running:
   ```bash
   ollama list  # Should show installed models
   ```
2. Start Ollama if not running:
   ```bash
   ollama serve
   ```
3. Check Ollama API endpoint (default: `http://localhost:11434`)

#### Chat History Not Persisting

**Symptoms:** Messages disappear after reload

**Solutions:**
1. Check file permissions on `data/` directory
2. Verify chat history file exists:
   ```bash
   cat data/users/<athlete_id>/profile/chat_history.json
   ```
3. Check for JSON syntax errors in chat history file
4. Clear and restart:
   ```bash
   rm data/users/<athlete_id>/profile/chat_history.json
   ```

#### High API Costs (Gemini)

**Solutions:**
1. Switch to `gemini-1.5-flash` (cheaper than `gemini-1.5-pro`)
2. Use local models (Ollama/MLX) for routine queries
3. Limit chat history context (code currently uses last 6 messages)
4. Set API usage limits in Google AI Studio

---

## Contributing

Contributions are welcome! Here's how to get started:

### Development Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes**
   - Add tests for new features
   - Update documentation (README, CLAUDE.md)
4. **Run tests**
   ```bash
   uv run pytest --cov=src
   ```
5. **Commit with descriptive messages**
   ```bash
   git commit -m "Add support for Strava integration"
   ```
6. **Push and create a Pull Request**

### Code Standards

- **Python style**: Follow PEP 8 (use `black` for formatting)
- **Type hints**: Add type annotations for function signatures
- **Docstrings**: Use Google-style docstrings for modules/functions
- **Tests**: Maintain >80% code coverage

### Areas for Contribution

**High Priority:**
- [ ] Strava integration (activity sync alternative to Garmin)
- [ ] Data visualization (weekly volume charts, pace progression)
- [ ] Training plan templates (marathon, ultra, 5K plans)
- [ ] Export functionality (PDF training reports)

**Medium Priority:**
- [ ] Mobile-responsive UI improvements
- [ ] Multi-language support for coaching prompts
- [ ] Activity manual entry (for non-Garmin users)
- [ ] Heart rate zone configuration per athlete

**Good First Issues:**
- [ ] Add dark mode toggle
- [ ] Improve error messages
- [ ] Add unit conversion (miles ↔ km)
- [ ] Add example .env file to repo

---

## License

This project is licensed under the MIT License. See `LICENSE` file for details.

---

## Acknowledgments

**Libraries & Tools:**
- [Streamlit](https://streamlit.io/) - Web UI framework
- [garminconnect](https://github.com/cyberjunky/python-garminconnect) - Garmin API client
- [google-generativeai](https://ai.google.dev/) - Gemini API
- [mlx-lm](https://github.com/ml-explore/mlx-lm) - Apple Silicon inference
- [Ollama](https://ollama.ai/) - Local LLM runtime

**Inspiration:**
Built for runners who want AI-powered coaching without sacrificing data privacy.

---

**Questions or issues?** Open an issue on GitHub or contact the maintainers.

**Happy running! 🏃‍♂️🐰**
