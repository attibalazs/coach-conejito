import os
import json
import yaml
from datetime import date

from modules.data_manager import (
    ensure_user_dirs,
    list_users,
    save_journal_entry,
    load_journal_entries,
    load_garmin_activities,
    save_user_profile,
    load_user_profile,
    save_coach_plan,
    load_coach_plan,
    save_chat_history,
    load_chat_history,
    create_user,
    save_model_prompt,
    load_model_prompt,
)


# --- ensure_user_dirs ---

def test_ensure_user_dirs_creates_all_directories(data_dirs):
    journal_dir, profile_dir, raw_garmin_dir = ensure_user_dirs("alice")
    assert os.path.isdir(journal_dir)
    assert os.path.isdir(profile_dir)
    assert os.path.isdir(raw_garmin_dir)
    assert journal_dir.endswith(os.path.join("alice", "journal"))
    assert raw_garmin_dir.endswith(os.path.join("alice", "raw", "garmin"))


def test_ensure_user_dirs_idempotent(data_dirs):
    ensure_user_dirs("alice")
    ensure_user_dirs("alice")  # should not raise


# --- list_users ---

def test_list_users_empty(data_dirs):
    assert list_users() == []


def test_list_users_with_users(data_dirs):
    ensure_user_dirs("alice")
    ensure_user_dirs("bob")
    users = list_users()
    assert sorted(users) == ["alice", "bob"]


def test_list_users_ignores_files(data_dirs):
    ensure_user_dirs("alice")
    # Create a file in USERS_DIR
    from modules.data_manager import USERS_DIR
    with open(os.path.join(USERS_DIR, "not_a_user.txt"), "w") as f:
        f.write("junk")
    users = list_users()
    assert users == ["alice"]


# --- journal entries ---

def test_save_and_load_journal_entry(test_user):
    entry = {"date": "2026-01-28", "rpe": 7, "mood": "good", "soreness": 3, "notes": "test"}
    save_journal_entry(test_user, date(2026, 1, 28), entry)
    entries = load_journal_entries(test_user)
    assert len(entries) == 1
    assert entries[0] == entry


def test_load_journal_entries_sorted_desc(test_user):
    for d in [15, 20, 10]:
        entry = {"date": f"2026-01-{d:02d}", "rpe": 5, "mood": "ok", "soreness": 1, "notes": ""}
        save_journal_entry(test_user, date(2026, 1, d), entry)
    entries = load_journal_entries(test_user)
    dates = [e["date"] for e in entries]
    assert dates == ["2026-01-20", "2026-01-15", "2026-01-10"]


def test_load_journal_entries_empty(test_user):
    assert load_journal_entries(test_user) == []


# --- garmin activities ---

def test_load_garmin_activities_sorted_desc(test_user):
    _, _, garmin_dir = ensure_user_dirs(test_user)
    for i, dt in enumerate(["2026-01-10", "2026-01-20", "2026-01-15"]):
        data = {"activityId": i, "startTimeLocal": f"{dt} 08:00:00"}
        with open(os.path.join(garmin_dir, f"activity_{i}.json"), "w") as f:
            json.dump(data, f)
    activities = load_garmin_activities(test_user)
    dates = [a["startTimeLocal"][:10] for a in activities]
    assert dates == ["2026-01-20", "2026-01-15", "2026-01-10"]


def test_load_garmin_activities_ignores_non_activity_files(test_user):
    _, _, garmin_dir = ensure_user_dirs(test_user)
    # Valid activity file
    with open(os.path.join(garmin_dir, "activity_1.json"), "w") as f:
        json.dump({"activityId": 1, "startTimeLocal": "2026-01-10 08:00:00"}, f)
    # Non-activity file
    with open(os.path.join(garmin_dir, "notes.json"), "w") as f:
        json.dump({"note": "test"}, f)
    activities = load_garmin_activities(test_user)
    assert len(activities) == 1


def test_load_garmin_activities_empty(test_user):
    assert load_garmin_activities(test_user) == []


# --- user profile ---

def test_save_and_load_user_profile(test_user, sample_profile):
    save_user_profile(test_user, sample_profile)
    loaded = load_user_profile(test_user)
    assert loaded["name"] == sample_profile["name"]
    assert loaded["goals"] == sample_profile["goals"]
    assert loaded["injuries"] == sample_profile["injuries"]


def test_load_user_profile_defaults(test_user):
    profile = load_user_profile(test_user)
    assert profile["name"] == "Testrunner"
    assert "goals" in profile
    assert "injuries" in profile


# --- coach plan ---

def test_save_and_load_coach_plan(test_user):
    plan = "## Week 1\n- Monday: Easy 5km\n- Tuesday: Rest"
    save_coach_plan(test_user, plan)
    loaded = load_coach_plan(test_user)
    assert loaded == plan


def test_load_coach_plan_default(test_user):
    plan = load_coach_plan(test_user)
    assert "No plan generated yet" in plan


# --- chat history ---

def test_save_and_load_chat_history(test_user):
    messages = [
        {"role": "user", "content": "How should I train today?"},
        {"role": "assistant", "content": "Easy 8km at zone 2."},
    ]
    save_chat_history(test_user, messages)
    loaded = load_chat_history(test_user)
    assert loaded == messages


def test_load_chat_history_empty(test_user):
    assert load_chat_history(test_user) == []


# --- create_user ---

def test_create_user_creates_dirs_and_profile(data_dirs):
    result = create_user("newathlete")
    assert result is True
    from modules.data_manager import USERS_DIR
    profile_path = os.path.join(USERS_DIR, "newathlete", "profile", "user.yaml")
    assert os.path.exists(profile_path)


def test_create_user_empty_id(data_dirs):
    assert create_user("") is False


def test_create_user_existing_preserves_profile(data_dirs):
    create_user("veteran")
    custom = {"name": "Veteran Runner", "goals": "BQ", "injuries": "None"}
    save_user_profile("veteran", custom)
    create_user("veteran")  # second call
    loaded = load_user_profile("veteran")
    assert loaded["name"] == "Veteran Runner"


# --- model prompts ---

def test_save_and_load_model_prompt(test_user):
    save_model_prompt(test_user, "phi4-mini:3.8b", "You are a strict coach.")
    loaded = load_model_prompt(test_user, "phi4-mini:3.8b")
    assert loaded == "You are a strict coach."


def test_model_prompt_sanitizes_name(test_user):
    save_model_prompt(test_user, "org/model:v2", "custom prompt")
    loaded = load_model_prompt(test_user, "org/model:v2")
    assert loaded == "custom prompt"
    # Verify the file on disk uses sanitized name
    _, profile_dir, _ = ensure_user_dirs(test_user)
    prompt_file = os.path.join(profile_dir, "prompts", "org_model_v2.txt")
    assert os.path.exists(prompt_file)


def test_load_model_prompt_returns_none_when_missing(test_user):
    assert load_model_prompt(test_user, "nonexistent-model") is None
