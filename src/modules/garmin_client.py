import os
import json
import shutil
from datetime import date, timedelta, datetime
from garminconnect import Garmin
from modules.data_manager import ensure_user_dirs

def get_token_dir(user_id):
    _, profile_dir, _ = ensure_user_dirs(user_id)
    # Using a specific directory for garth
    return os.path.join(profile_dir, "garmin_tokens")

def is_garmin_authenticated(user_id):
    token_dir = get_token_dir(user_id)
    if not os.path.exists(token_dir) or not os.path.isdir(token_dir):
        return False
    token_files = os.listdir(token_dir)
    if not token_files:
        return False
    # Verify token files are non-empty (empty files = corrupt tokens)
    for tf in token_files:
        filepath = os.path.join(token_dir, tf)
        if os.path.isfile(filepath) and os.path.getsize(filepath) == 0:
            print(f"Corrupt token file detected (empty): {tf}")
            return False
    return True

def sync_garmin_activities(user_id, email=None, password=None, start_date_obj=None, days=7):
    """
    Syncs activities from Garmin Connect in 30-day chunks to prevent API timeouts.
    Uses stored tokens if available, otherwise requires email/password.
    """
    token_dir = get_token_dir(user_id)
    client = None
    resume_error = None

    try:
        # 1. Attempt to resume session
        if is_garmin_authenticated(user_id):
            try:
                print(f"Attempting to resume Garmin session for {user_id}")
                client = Garmin()
                client.login(tokenstore=token_dir)
                print("Session resumed and verified.")
            except Exception as e:
                print(f"Garmin Resume/Verify failed: {e}")
                client = None
                err_str = str(e)
                err_type = type(e).__name__
                if "Expecting value" in err_str or "JSONDecodeError" in err_type:
                    # Corrupt or empty token files — clear them so the login form appears
                    print(f"Corrupt tokens detected, clearing {token_dir}")
                    if os.path.exists(token_dir):
                        shutil.rmtree(token_dir)
                    resume_error = None  # Don't show a confusing error, just show login form
                elif "401" in err_str or "403" in err_str or "Login" in err_str:
                    resume_error = "Session expired. Please re-enter your email and password."
                else:
                    resume_error = f"Garmin connection error: {err_str}"

        # 2. Login with credentials if resume failed or no session
        if client is None:
            if email and password:
                print(f"Logging in with fresh credentials for {user_id}")
                try:
                    client = Garmin(email, password)
                    client.login()

                    # Clean existing tokens before saving new ones
                    if os.path.exists(token_dir):
                        shutil.rmtree(token_dir)
                    os.makedirs(token_dir, exist_ok=True)

                    # Save tokens directly from the instance's own garth client
                    client.garth.dump(token_dir)

                    # Verify file sizes
                    token_files = os.listdir(token_dir)
                    print(f"Saved tokens to {token_dir}. Files: {token_files}")
                    for tf in token_files:
                        size = os.path.getsize(os.path.join(token_dir, tf))
                        print(f"  {tf}: {size} bytes")
                        if size == 0:
                            print(f"CRITICAL: {tf} is empty after save!")
                except Exception as e:
                    return f"Login failed: {str(e)}"
            else:
                if "expired" in str(resume_error).lower() or "401" in str(resume_error) or "403" in str(resume_error):
                    if os.path.exists(token_dir):
                        shutil.rmtree(token_dir)
                    return f"Session expired. Please re-enter your email and password."

                if resume_error:
                    return f"Garmin connection error: {resume_error}. Please try again or re-login."
                return "No active session. Please login."

        # 3. Determine date range
        today = date.today()
        if start_date_obj is None:
            start_date_obj = today - timedelta(days=days)

        # Ensure it's a date object
        if isinstance(start_date_obj, datetime):
            start_date_obj = start_date_obj.date()

        # 4. Fetch activities in 30-day chunks
        all_activities = []
        current_start = start_date_obj

        print(f"Syncing from {start_date_obj} to {today}...")

        while current_start <= today:
            current_end = min(current_start + timedelta(days=30), today)
            print(f"  Fetching chunk: {current_start} to {current_end}")

            try:
                chunk = client.get_activities_by_date(
                    current_start.isoformat(),
                    current_end.isoformat()
                )
                if chunk:
                    all_activities.extend(chunk)
            except Exception as e:
                err_msg = str(e)
                # If we get a JSON error here, it's likely an API timeout, not an auth failure
                if "Expecting value" in err_msg:
                    return f"Garmin API timeout on chunk {current_start}. The date range might be too large or the service is busy. Try a smaller range."
                return f"Sync failed at {current_start}: {err_msg}"

            current_start = current_end + timedelta(days=1)

        # 5. Persist refreshed tokens after successful sync
        try:
            client.garth.dump(token_dir)
        except Exception:
            pass  # Non-fatal; just means next restart may need re-login

        if not all_activities:
            return f"No running activities found since {start_date_obj.isoformat()}."

        _, _, garmin_dir = ensure_user_dirs(user_id)

        saved_count = 0
        seen_ids = set()
        for activity in all_activities:
            activity_id = activity.get("activityId")
            if not activity_id or activity_id in seen_ids:
                continue

            seen_ids.add(activity_id)
            filename = os.path.join(garmin_dir, f"activity_{activity_id}.json")
            with open(filename, "w") as f:
                json.dump(activity, f, indent=4)
            saved_count += 1

        return f"Successfully synced {saved_count} activities since {start_date_obj.isoformat()}."

    except Exception as e:
        print(f"Unexpected Garmin Sync Error: {str(e)}")
        return f"Unexpected Error: {str(e)}"
