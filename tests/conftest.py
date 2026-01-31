import os
import json
import pytest
from unittest.mock import patch
from datetime import datetime, date


@pytest.fixture
def data_dirs(tmp_path):
    """Redirect data_manager paths to tmp_path for isolation."""
    data_dir = str(tmp_path / "data")
    users_dir = os.path.join(data_dir, "users")
    with patch("modules.data_manager.DATA_DIR", data_dir), \
         patch("modules.data_manager.USERS_DIR", users_dir):
        yield tmp_path


@pytest.fixture
def test_user(data_dirs):
    """Create a test user with directories ready."""
    from modules.data_manager import ensure_user_dirs
    ensure_user_dirs("testrunner")
    return "testrunner"


@pytest.fixture
def sample_running_activity():
    return {
        "activityId": 12345,
        "activityName": "Morning Run",
        "startTimeLocal": "2026-01-28 07:30:00",
        "activityType": {"typeKey": "running"},
        "distance": 25500,
        "duration": 9000,
        "averageHR": 123,
        "maxHR": 155,
        "averageSpeed": 2.83,
        "elevationGain": 250,
        "averageRunningCadenceInStepsPerMinute": 160,
        "aerobicTrainingEffect": 3.2,
        "trainingEffectLabel": "Improving",
        "vO2MaxValue": 52,
        "calories": 1800,
    }


@pytest.fixture
def sample_strength_activity():
    return {
        "activityId": 67890,
        "activityName": "Gym Session",
        "startTimeLocal": "2026-01-27 18:00:00",
        "activityType": {"typeKey": "strength_training"},
        "distance": 0,
        "duration": 3600,
        "averageHR": 95,
        "maxHR": 130,
        "averageSpeed": 0,
        "aerobicTrainingEffect": 1.5,
        "trainingEffectLabel": "Recovery",
        "calories": 400,
    }


@pytest.fixture
def weekly_activities():
    """8 activities across 4 ISO weeks in Jan 2026 (W02-W05)."""
    base = [
        # W02 (Jan 5-11)
        {"activityId": 1, "startTimeLocal": "2026-01-06 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 10000, "duration": 3000,
         "averageHR": 140, "averageSpeed": 3.33, "elevationGain": 50},
        {"activityId": 2, "startTimeLocal": "2026-01-08 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 8000, "duration": 2500,
         "averageHR": 138, "averageSpeed": 3.2, "elevationGain": 30},
        # W03 (Jan 12-18)
        {"activityId": 3, "startTimeLocal": "2026-01-13 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 12000, "duration": 3600,
         "averageHR": 142, "averageSpeed": 3.33, "elevationGain": 80},
        {"activityId": 4, "startTimeLocal": "2026-01-15 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 6000, "duration": 2000,
         "averageHR": 135, "averageSpeed": 3.0, "elevationGain": 20},
        # W04 (Jan 19-25)
        {"activityId": 5, "startTimeLocal": "2026-01-20 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 15000, "duration": 4500,
         "averageHR": 145, "averageSpeed": 3.33, "elevationGain": 120},
        {"activityId": 6, "startTimeLocal": "2026-01-22 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 10000, "duration": 3000,
         "averageHR": 140, "averageSpeed": 3.33, "elevationGain": 60},
        # W05 (Jan 26-Feb 1)
        {"activityId": 7, "startTimeLocal": "2026-01-27 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 20000, "duration": 6000,
         "averageHR": 148, "averageSpeed": 3.33, "elevationGain": 200},
        {"activityId": 8, "startTimeLocal": "2026-01-29 08:00:00",
         "activityType": {"typeKey": "running"}, "distance": 8000, "duration": 2400,
         "averageHR": 136, "averageSpeed": 3.33, "elevationGain": 40},
    ]
    return base


@pytest.fixture
def sample_journal_entry():
    return {
        "date": "2026-01-28",
        "rpe": 6,
        "mood": "good",
        "soreness": 3,
        "notes": "Legs felt a bit heavy after yesterday's long run.",
    }


@pytest.fixture
def sample_profile():
    return {
        "name": "Test Runner",
        "goals": "Complete a 50km ultra in under 6 hours",
        "injuries": "Mild plantar fasciitis in left foot",
    }


class FrozenDatetime(datetime):
    """datetime subclass that freezes now() but preserves strptime()."""

    @classmethod
    def now(cls, tz=None):
        return cls(2026, 1, 30, 12, 0, 0)


@pytest.fixture
def frozen_now_jan30():
    """Patch datetime.datetime inside gemini_coach so now() returns 2026-01-30 12:00."""
    return FrozenDatetime
