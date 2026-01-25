import os
import json
import garth
import shutil
from datetime import date, timedelta, datetime
from garminconnect import Garmin
from modules.data_manager import ensure_user_dirs

def get_token_dir(user_id):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    return os.path.join(profile_dir, ".garmin_tokens")

def is_garmin_authenticated(user_id):
    token_dir = get_token_dir(user_id)
    return os.path.exists(token_dir) and os.path.isdir(token_dir) and os.listdir(token_dir)

def sync_garmin_activities(user_id, email=None, password=None, start_date_obj=None, days=7):
    """
    Syncs recent activities from Garmin Connect to the user's raw data folder.
    Uses stored tokens if available, otherwise requires email/password.
    """
    try:
        token_dir = get_token_dir(user_id)
        client = None

        if is_garmin_authenticated(user_id):
            try:
                garth.resume(token_dir)
                client = Garmin()
                client.login()
            except Exception as e:
                print(f"Token login failed: {e}. Cleaning up tokens.")
                if os.path.exists(token_dir):
                    shutil.rmtree(token_dir)
                if not (email and password):
                    return "Session expired or corrupted. Please enter email and password to re-authenticate."
        
        if client is None:
            if not email or not password:
                 return "Authentication required. Please enter email and password."
            client = Garmin(email, password)
            client.login()
            garth.save(token_dir)
            
        today = date.today()
        if start_date_obj is None:
            start_date_obj = today - timedelta(days=days)
        
        # Garmin API expects ISO string YYYY-MM-DD
        activities = client.get_activities_by_date(
            start_date_obj.isoformat(), 
            today.isoformat(), 
            "running"
        )
        
        if not activities:
            return f"No activities found since {start_date_obj.isoformat()}."
            
        _, _, garmin_dir = ensure_user_dirs(user_id)
        
        saved_count = 0
        for activity in activities:
            activity_id = activity.get("activityId")
            if not activity_id:
                continue
            filename = os.path.join(garmin_dir, f"activity_{activity_id}.json")
            with open(filename, "w") as f:
                json.dump(activity, f, indent=4)
            saved_count += 1
            
        return f"Successfully synced {saved_count} activities since {start_date_obj.isoformat()}."

    except Exception as e:
        return f"Garmin Sync Error: {str(e)}"
