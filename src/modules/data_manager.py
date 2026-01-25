import json
import os
import yaml
import shutil
from datetime import date

DATA_DIR = "data"
USERS_DIR = os.path.join(DATA_DIR, "users")

def ensure_user_dirs(user_id):
    user_dir = os.path.join(USERS_DIR, user_id)
    journal_dir = os.path.join(user_dir, "journal")
    profile_dir = os.path.join(user_dir, "profile")
    raw_garmin_dir = os.path.join(user_dir, "raw", "garmin")
    
    os.makedirs(journal_dir, exist_ok=True)
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs(raw_garmin_dir, exist_ok=True)
    return journal_dir, profile_dir, raw_garmin_dir

def list_users():
    if not os.path.exists(USERS_DIR):
        return []
    return [d for d in os.listdir(USERS_DIR) if os.path.isdir(os.path.join(USERS_DIR, d))]

def save_journal_entry(user_id, entry_date, data):
    journal_dir, _, _ = ensure_user_dirs(user_id)
    filename = os.path.join(journal_dir, f"{entry_date.isoformat()}.json")
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def load_journal_entries(user_id):
    journal_dir, _, _ = ensure_user_dirs(user_id)
    entries = []
    if os.path.exists(journal_dir):
        for filename in os.listdir(journal_dir):
            if filename.endswith(".json"):
                with open(os.path.join(journal_dir, filename), "r") as f:
                    entries.append(json.load(f))
    # Sort by date descending
    return sorted(entries, key=lambda x: x['date'], reverse=True)

def load_garmin_activities(user_id):
    _, _, garmin_dir = ensure_user_dirs(user_id)
    activities = []
    if os.path.exists(garmin_dir):
        for filename in os.listdir(garmin_dir):
            if filename.endswith(".json") and filename.startswith("activity_"):
                with open(os.path.join(garmin_dir, filename), "r") as f:
                    activities.append(json.load(f))
    # Sort by start time descending
    return sorted(activities, key=lambda x: x.get('startTimeLocal', ''), reverse=True)

def save_user_profile(user_id, profile_data):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    filename = os.path.join(profile_dir, "user.yaml")
    with open(filename, "w") as f:
        yaml.dump(profile_data, f)

def load_user_profile(user_id):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    filename = os.path.join(profile_dir, "user.yaml")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return yaml.safe_load(f)
    return {
        "name": user_id.capitalize(),
        "goals": "Run a sub-3 hour marathon.",
        "injuries": "None"
    }

# --- Coach Plan & Chat Storage ---

def save_coach_plan(user_id, plan_text):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    filename = os.path.join(profile_dir, "current_plan.md")
    with open(filename, "w") as f:
        f.write(plan_text)

def load_coach_plan(user_id):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    filename = os.path.join(profile_dir, "current_plan.md")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read()
    return "No plan generated yet. Use the 'Analyze' button or Chat with the Coach to create one."

def save_chat_history(user_id, messages):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    filename = os.path.join(profile_dir, "chat_history.json")
    with open(filename, "w") as f:
        json.dump(messages, f, indent=4)

def load_chat_history(user_id):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    filename = os.path.join(profile_dir, "chat_history.json")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

def create_user(user_id):
    if not user_id: return False
    ensure_user_dirs(user_id)
    if not os.path.exists(os.path.join(USERS_DIR, user_id, "profile", "user.yaml")):
        save_user_profile(user_id, {"name": user_id, "goals": "", "injuries": ""})
    return True
