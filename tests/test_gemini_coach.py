import sys
import types
import json
import datetime as dt_module
from unittest.mock import patch, MagicMock

from modules.gemini_coach import (
    format_pace,
    format_garmin_for_ai,
    compute_training_stats,
    get_system_prompt,
    get_ai_coach_response,
    DEFAULT_COACH_PROMPT,
    MLX_CACHE,
)


# =====================================================================
# format_pace
# =====================================================================

def test_format_pace_typical():
    # 2.83 m/s → 16.667/2.83 ≈ 5.89 → 5:53
    result = format_pace(2.83)
    assert result == "5:53"


def test_format_pace_fast():
    # 5.0 m/s → 16.667/5 = 3.333 → 3:20
    result = format_pace(5.0)
    assert result == "3:20"


def test_format_pace_zero():
    assert format_pace(0) == "0:00"


def test_format_pace_negative():
    assert format_pace(-1) == "0:00"


def test_format_pace_very_slow():
    # 0.5 m/s → 16.667/0.5 = 33.333 → 33:20
    result = format_pace(0.5)
    assert result == "33:20"


def test_format_pace_seconds_zero_padded():
    # 3.0 m/s → 16.667/3 ≈ 5.556 → 5:33
    result = format_pace(3.0)
    minutes, seconds = result.split(":")
    assert len(seconds) == 2


# =====================================================================
# format_garmin_for_ai
# =====================================================================

def test_format_garmin_empty():
    assert format_garmin_for_ai([]) == "No recent activities recorded."


def test_format_garmin_none():
    assert format_garmin_for_ai(None) == "No recent activities recorded."


def test_format_garmin_running_activity(sample_running_activity):
    result = format_garmin_for_ai([sample_running_activity])
    assert "2026-01-28" in result
    assert "25.5" in result
    assert "Running" in result
    assert "Avg HR: 123" in result
    assert "min/km" in result
    assert "TE:" in result


def test_format_garmin_none_elevation_cadence(sample_strength_activity):
    result = format_garmin_for_ai([sample_strength_activity])
    assert "Elev:" not in result
    assert "Cadence:" not in result


def test_format_garmin_truncates_to_10():
    activities = []
    for i in range(12):
        activities.append({
            "activityId": i,
            "startTimeLocal": f"2026-01-{(i + 1):02d} 08:00:00",
            "activityType": {"typeKey": "running"},
            "distance": 10000,
            "duration": 3000,
            "averageHR": 140,
            "averageSpeed": 3.33,
            "aerobicTrainingEffect": 3.0,
            "trainingEffectLabel": "Improving",
        })
    result = format_garmin_for_ai(activities)
    lines = [l for l in result.strip().split("\n") if l.startswith("- ")]
    assert len(lines) == 10


def test_format_garmin_zero_speed():
    act = {
        "activityId": 1,
        "startTimeLocal": "2026-01-28 08:00:00",
        "activityType": {"typeKey": "running"},
        "distance": 0,
        "duration": 3600,
        "averageHR": 90,
        "averageSpeed": 0,
        "aerobicTrainingEffect": 1.0,
        "trainingEffectLabel": "Recovery",
    }
    result = format_garmin_for_ai([act])
    assert "0:00 min/km" in result


# =====================================================================
# compute_training_stats
# =====================================================================

def _patch_frozen(frozen_cls):
    """Return a context manager that patches datetime.datetime with frozen_cls."""
    return patch.object(dt_module, "datetime", frozen_cls)


def test_compute_stats_empty(frozen_now_jan30):
    with _patch_frozen(frozen_now_jan30):
        assert compute_training_stats([]) == "No training data available."


def test_compute_stats_none(frozen_now_jan30):
    with _patch_frozen(frozen_now_jan30):
        assert compute_training_stats(None) == "No training data available."


def test_compute_stats_weekly_breakdown(weekly_activities, frozen_now_jan30):
    with _patch_frozen(frozen_now_jan30):
        result = compute_training_stats(weekly_activities)
    assert "Weekly breakdown" in result
    # Should have 4 week lines (W02-W05)
    week_lines = [l for l in result.split("\n") if l.strip().startswith("20")]
    assert len(week_lines) == 4
    # W02: 10+8 = 18km
    assert "18.0km" in result
    # W03: 12+6 = 18km
    # W04: 15+10 = 25km
    assert "25.0km" in result
    # W05: 20+8 = 28km
    assert "28.0km" in result


def test_compute_stats_week_over_week(weekly_activities, frozen_now_jan30):
    with _patch_frozen(frozen_now_jan30):
        result = compute_training_stats(weekly_activities)
    # W04=25km, W05=28km → (28-25)/25 = 12%
    assert "Week-over-week" in result
    assert "+12%" in result


def test_compute_stats_month_total(weekly_activities, frozen_now_jan30):
    with _patch_frozen(frozen_now_jan30):
        result = compute_training_stats(weekly_activities)
    # All activities are in Jan 2026, total = 10+8+12+6+15+10+20+8 = 89km
    assert "2026-01" in result
    assert "89.0km" in result


def test_compute_stats_year_total(weekly_activities, frozen_now_jan30):
    with _patch_frozen(frozen_now_jan30):
        result = compute_training_stats(weekly_activities)
    assert "2026" in result
    assert "89.0km" in result


def test_compute_stats_single_week(frozen_now_jan30):
    acts = [
        {"activityId": 1, "startTimeLocal": "2026-01-27 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 10000, "duration": 3000,
         "averageHR": 140, "averageSpeed": 3.33, "elevationGain": 50},
    ]
    with _patch_frozen(frozen_now_jan30):
        result = compute_training_stats(acts)
    assert "Week-over-week" not in result


def test_compute_stats_skips_empty_date(frozen_now_jan30):
    acts = [
        {"activityId": 1, "startTimeLocal": "", "distance": 5000, "duration": 1500},
        {"activityId": 2, "startTimeLocal": "2026-01-27 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 10000, "duration": 3000,
         "averageHR": 140, "averageSpeed": 3.33, "elevationGain": 50},
    ]
    with _patch_frozen(frozen_now_jan30):
        result = compute_training_stats(acts)
    # Only 1 valid activity → 10km
    assert "10.0km" in result


# =====================================================================
# get_system_prompt
# =====================================================================

def test_system_prompt_uses_default(test_user):
    prompt = get_system_prompt(test_user)
    assert "Coach Conejito" in prompt
    assert "RESPONSE FORMAT" in prompt


def test_system_prompt_uses_custom(test_user):
    from modules.data_manager import save_model_prompt
    save_model_prompt(test_user, "phi4-mini:3.8b", "You are a trail running guru.")
    prompt = get_system_prompt(test_user, model_name="phi4-mini:3.8b")
    assert "trail running guru" in prompt
    assert "RESPONSE FORMAT" not in prompt  # default prompt replaced


def test_system_prompt_includes_profile(test_user, sample_profile):
    from modules.data_manager import save_user_profile
    save_user_profile(test_user, sample_profile)
    prompt = get_system_prompt(test_user)
    assert sample_profile["name"] in prompt
    assert sample_profile["goals"] in prompt
    assert sample_profile["injuries"] in prompt


def test_system_prompt_includes_today(test_user):
    prompt = get_system_prompt(test_user)
    assert "TODAY:" in prompt


def test_system_prompt_includes_training_stats(test_user):
    prompt = get_system_prompt(test_user)
    assert "TRAINING LOAD" in prompt


# =====================================================================
# get_ai_coach_response — Ollama
# =====================================================================

def test_ollama_success(test_user):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "Rest today, run tomorrow."}
    mock_resp.raise_for_status = MagicMock()

    with patch("modules.gemini_coach.requests.post", return_value=mock_resp):
        text, duration = get_ai_coach_response(
            api_key="", user_id=test_user, model_name="deepseek-r1:8b",
            chat_mode=False,
        )
    assert "Rest today" in text
    assert duration > 0 or duration == 0  # timing can be near-zero in tests


def test_ollama_connection_error(test_user):
    import requests as req
    with patch("modules.gemini_coach.requests.post", side_effect=req.exceptions.ConnectionError):
        text, duration = get_ai_coach_response(
            api_key="", user_id=test_user, model_name="deepseek-r1:8b",
            chat_mode=False,
        )
    assert "Could not connect to Ollama" in text


# =====================================================================
# get_ai_coach_response — Gemini
# =====================================================================

def test_gemini_success(test_user):
    mock_genai = MagicMock()
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Great job on your long run."
    mock_model_instance.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model_instance

    # google.generativeai is already in sys.modules from the real install;
    # swap it out for the duration of the call.
    orig = sys.modules.get("google.generativeai")
    try:
        sys.modules["google.generativeai"] = mock_genai
        text, duration = get_ai_coach_response(
            api_key="test-key-123", user_id=test_user,
            model_name="gemini-1.5-flash", chat_mode=False,
        )
    finally:
        if orig is not None:
            sys.modules["google.generativeai"] = orig
        else:
            sys.modules.pop("google.generativeai", None)
    assert "Great job" in text


def test_gemini_no_api_key(test_user):
    text, duration = get_ai_coach_response(
        api_key="", user_id=test_user, model_name="gemini-1.5-flash",
        chat_mode=False,
    )
    assert "Please provide a valid Gemini API Key" in text


# =====================================================================
# get_ai_coach_response — MLX
# =====================================================================

def test_mlx_success(test_user):
    mock_mlx_lm = types.ModuleType("mlx_lm")
    mock_mlx_lm.load = MagicMock(return_value=("mock_model", "mock_tokenizer"))
    mock_mlx_lm.generate = MagicMock(return_value="Do hill sprints tomorrow.")

    # Reset cache before test
    MLX_CACHE["model"] = None
    MLX_CACHE["tokenizer"] = None
    MLX_CACHE["path"] = None

    with patch.dict(sys.modules, {"mlx_lm": mock_mlx_lm}):
        text, duration = get_ai_coach_response(
            api_key="", user_id=test_user, model_name="mlx-deepseek-8b",
            chat_mode=False,
        )
    assert "hill sprints" in text

    # Cleanup
    MLX_CACHE["model"] = None
    MLX_CACHE["tokenizer"] = None
    MLX_CACHE["path"] = None


# =====================================================================
# get_ai_coach_response — prompt modes
# =====================================================================

def test_chat_mode_prompt(test_user):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "Chat reply."}
    mock_resp.raise_for_status = MagicMock()

    with patch("modules.gemini_coach.requests.post", return_value=mock_resp) as mock_post:
        get_ai_coach_response(
            api_key="", user_id=test_user, model_name="deepseek-r1:8b",
            chat_mode=True, user_message="How are my legs?",
            history=[{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}],
        )
    called_payload = mock_post.call_args[1]["json"]
    assert "CHAT HISTORY" in called_payload["prompt"]
    assert "How are my legs?" in called_payload["prompt"]


def test_analyze_mode_prompt(test_user):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "Analysis done."}
    mock_resp.raise_for_status = MagicMock()

    with patch("modules.gemini_coach.requests.post", return_value=mock_resp) as mock_post:
        get_ai_coach_response(
            api_key="", user_id=test_user, model_name="deepseek-r1:8b",
            chat_mode=False,
        )
    called_payload = mock_post.call_args[1]["json"]
    assert "actionable assessment" in called_payload["prompt"]
