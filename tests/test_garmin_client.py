import os
import json
from unittest.mock import patch, MagicMock
from datetime import date

from modules.garmin_client import get_token_dir, is_garmin_authenticated, sync_garmin_activities
from modules.data_manager import ensure_user_dirs


# =====================================================================
# get_token_dir
# =====================================================================

def test_get_token_dir_path(test_user):
    token_dir = get_token_dir(test_user)
    assert token_dir.endswith(os.path.join("profile", "garmin_tokens"))


# =====================================================================
# is_garmin_authenticated
# =====================================================================

def test_not_authenticated_no_tokens(test_user):
    assert is_garmin_authenticated(test_user) is False


def test_authenticated_with_files(test_user):
    token_dir = get_token_dir(test_user)
    os.makedirs(token_dir, exist_ok=True)
    with open(os.path.join(token_dir, "oauth1_token.json"), "w") as f:
        f.write('{"token": "abc123"}')
    assert is_garmin_authenticated(test_user) is True


def test_not_authenticated_empty_dir(test_user):
    token_dir = get_token_dir(test_user)
    os.makedirs(token_dir, exist_ok=True)
    assert is_garmin_authenticated(test_user) is False


def test_not_authenticated_empty_file(test_user):
    token_dir = get_token_dir(test_user)
    os.makedirs(token_dir, exist_ok=True)
    with open(os.path.join(token_dir, "oauth1_token.json"), "w") as f:
        pass  # 0-byte file
    assert is_garmin_authenticated(test_user) is False


# =====================================================================
# sync_garmin_activities
# =====================================================================

def test_sync_fresh_login(test_user):
    mock_client = MagicMock()
    mock_client.get_activities_by_date.return_value = [
        {"activityId": 100, "startTimeLocal": "2026-01-28 08:00:00", "distance": 10000},
        {"activityId": 101, "startTimeLocal": "2026-01-29 08:00:00", "distance": 8000},
    ]
    mock_garth = MagicMock()
    mock_client.garth = mock_garth

    with patch("modules.garmin_client.Garmin", return_value=mock_client):
        result = sync_garmin_activities(
            test_user, email="test@example.com", password="pass123",
            start_date_obj=date(2026, 1, 28), days=7,
        )

    assert "Successfully synced 2 activities" in result
    _, _, garmin_dir = ensure_user_dirs(test_user)
    assert os.path.exists(os.path.join(garmin_dir, "activity_100.json"))
    assert os.path.exists(os.path.join(garmin_dir, "activity_101.json"))


def test_sync_resume_session(test_user):
    # Pre-create token files
    token_dir = get_token_dir(test_user)
    os.makedirs(token_dir, exist_ok=True)
    with open(os.path.join(token_dir, "oauth1_token.json"), "w") as f:
        f.write('{"token": "saved"}')

    mock_client = MagicMock()
    mock_client.get_activities_by_date.return_value = [
        {"activityId": 200, "startTimeLocal": "2026-01-28 08:00:00", "distance": 5000},
    ]
    mock_garth = MagicMock()
    mock_client.garth = mock_garth

    with patch("modules.garmin_client.Garmin", return_value=mock_client):
        result = sync_garmin_activities(
            test_user, start_date_obj=date(2026, 1, 28), days=7,
        )

    assert "Successfully synced 1 activities" in result


def test_sync_expired_session(test_user):
    # Pre-create token files
    token_dir = get_token_dir(test_user)
    os.makedirs(token_dir, exist_ok=True)
    with open(os.path.join(token_dir, "oauth1_token.json"), "w") as f:
        f.write('{"token": "old"}')

    mock_client = MagicMock()
    mock_client.login.side_effect = Exception("401 Unauthorized")

    with patch("modules.garmin_client.Garmin", return_value=mock_client):
        result = sync_garmin_activities(test_user)

    assert "Session expired" in result
    # Token dir should be cleared
    assert not os.path.exists(token_dir)


def test_sync_corrupt_tokens(test_user):
    token_dir = get_token_dir(test_user)
    os.makedirs(token_dir, exist_ok=True)
    with open(os.path.join(token_dir, "oauth1_token.json"), "w") as f:
        f.write('{"token": "corrupt"}')

    mock_client = MagicMock()
    mock_client.login.side_effect = json.JSONDecodeError("Expecting value", "", 0)

    with patch("modules.garmin_client.Garmin", return_value=mock_client):
        result = sync_garmin_activities(test_user)

    # Corrupt tokens detected → cleared, no credentials → "No active session"
    assert "No active session" in result
    assert not os.path.exists(token_dir)


def test_sync_no_session_no_credentials(test_user):
    result = sync_garmin_activities(test_user)
    assert "No active session" in result


def test_sync_deduplicates(test_user):
    mock_client = MagicMock()
    # Two chunks return overlapping activity IDs
    # Range: Dec 1 → Jan 31 requires two 30-day chunks
    mock_client.get_activities_by_date.side_effect = [
        [
            {"activityId": 300, "startTimeLocal": "2025-12-05 08:00:00", "distance": 10000},
            {"activityId": 301, "startTimeLocal": "2025-12-28 08:00:00", "distance": 12000},
        ],
        [
            {"activityId": 301, "startTimeLocal": "2025-12-28 08:00:00", "distance": 12000},
            {"activityId": 302, "startTimeLocal": "2026-01-20 08:00:00", "distance": 8000},
        ],
    ]
    mock_garth = MagicMock()
    mock_client.garth = mock_garth

    with patch("modules.garmin_client.Garmin", return_value=mock_client):
        result = sync_garmin_activities(
            test_user, email="test@example.com", password="pass123",
            start_date_obj=date(2025, 12, 1), days=60,
        )

    assert "Successfully synced 3 activities" in result
    _, _, garmin_dir = ensure_user_dirs(test_user)
    activity_files = [f for f in os.listdir(garmin_dir) if f.startswith("activity_")]
    assert len(activity_files) == 3
