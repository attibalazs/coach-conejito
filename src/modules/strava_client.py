"""Strava API v3 client with OAuth2 token refresh, activity sync, and stream fetching."""
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

from src.modules.data_manager import ensure_user_dirs
from src.modules.repositories import ActivityRepository

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"


class StravaAuthError(Exception):
    """Raised when Strava authentication or token refresh fails."""


class StravaRateLimitError(Exception):
    """Raised when Strava API rate limit is exceeded."""


def get_strava_token_path(user_id: str) -> str:
    """Return path to stored Strava OAuth tokens for a user."""
    _, profile_dir, _ = ensure_user_dirs(user_id)
    return os.path.join(profile_dir, "strava_tokens.json")


def get_strava_raw_dir(user_id: str) -> str:
    """Return path to raw Strava activity JSON directory for a user."""
    raw_dir = os.path.join("data", "users", user_id, "raw", "strava")
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir


def load_strava_tokens(user_id: str) -> Optional[Dict[str, Any]]:
    """Load stored Strava tokens if present and valid JSON."""
    token_path = get_strava_token_path(user_id)
    if not os.path.exists(token_path):
        return None
    try:
        with open(token_path, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not data.get("refresh_token"):
            return None
        return data
    except (OSError, json.JSONDecodeError):
        return None


def save_strava_tokens(user_id: str, tokens: Dict[str, Any]) -> str:
    """Persist Strava OAuth tokens to disk."""
    token_path = get_strava_token_path(user_id)
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(tokens, f, indent=2)
    return token_path


def is_strava_authenticated(user_id: str) -> bool:
    """Check whether Strava credentials/tokens exist for a user."""
    tokens = load_strava_tokens(user_id)
    return bool(tokens and tokens.get("refresh_token") and tokens.get("client_id") and tokens.get("client_secret"))


def get_authorization_url(
    client_id: str,
    redirect_uri: str = "http://localhost:8765/callback",
    scope: str = "read,activity:read_all",
) -> str:
    """Build Strava OAuth2 authorization URL."""
    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": scope,
    })
    return f"{STRAVA_AUTH_URL}?{params}"


def exchange_code_for_token(
    user_id: str,
    client_id: str,
    client_secret: str,
    code: str,
) -> Dict[str, Any]:
    """Exchange an OAuth2 authorization code for Strava access/refresh tokens."""
    resp = requests.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise StravaAuthError(f"Strava token exchange failed ({resp.status_code}): {resp.text}")

    payload = resp.json()
    tokens = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "expires_at": payload["expires_at"],
        "athlete": payload.get("athlete"),
    }
    save_strava_tokens(user_id, tokens)
    return tokens


class StravaClient:
    """Client for fetching and syncing Strava activities and streams."""

    STREAM_KEYS = "time,distance,altitude,heartrate,cadence,grade_smooth,velocity_smooth"

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tokens = load_strava_tokens(user_id)
        if not self.tokens:
            raise StravaAuthError(
                f"Strava is not authenticated for user '{user_id}'. Run `coach -u {user_id} auth strava` first."
            )

    def _ensure_valid_token(self) -> str:
        """Refresh access token if expired or expiring within 60 seconds."""
        expires_at = self.tokens.get("expires_at", 0)
        if time.time() < expires_at - 60 and self.tokens.get("access_token"):
            return self.tokens["access_token"]

        resp = requests.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": self.tokens["client_id"],
                "client_secret": self.tokens["client_secret"],
                "grant_type": "refresh_token",
                "refresh_token": self.tokens["refresh_token"],
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise StravaAuthError(f"Strava token refresh failed ({resp.status_code}): {resp.text}")

        payload = resp.json()
        self.tokens.update({
            "access_token": payload["access_token"],
            "refresh_token": payload["refresh_token"],
            "expires_at": payload["expires_at"],
        })
        save_strava_tokens(self.user_id, self.tokens)
        return self.tokens["access_token"]

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute an authenticated GET request against Strava API v3."""
        token = self._ensure_valid_token()
        resp = requests.get(
            f"{STRAVA_API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
            timeout=30,
        )
        if resp.status_code == 429:
            raise StravaRateLimitError("Strava API rate limit exceeded. Try again in 15 minutes.")
        if resp.status_code == 401:
            raise StravaAuthError("Strava access token rejected (401). Re-run `coach auth strava`.")
        if resp.status_code != 200:
            raise RuntimeError(f"Strava API error ({resp.status_code}): {resp.text}")
        return resp.json()

    def fetch_activities(
        self,
        days: int = 30,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch paginated athlete activities within the given date window."""
        end_dt = datetime.combine(end_date or date.today(), datetime.max.time(), tzinfo=timezone.utc)
        start_d = start_date or (date.today() - timedelta(days=days))
        start_dt = datetime.combine(start_d, datetime.min.time(), tzinfo=timezone.utc)

        after_ts = int(start_dt.timestamp())
        before_ts = int(end_dt.timestamp())

        all_activities: List[Dict[str, Any]] = []
        page = 1
        while True:
            batch = self._get(
                "/athlete/activities",
                params={"after": after_ts, "before": before_ts, "page": page, "per_page": 100},
            )
            if not batch:
                break
            all_activities.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return all_activities

    def fetch_activity_streams(self, activity_id: str) -> Dict[str, Any]:
        """Fetch time-series streams (altitude, grade, HR, velocity, cadence) for an activity."""
        return self._get(
            f"/activities/{activity_id}/streams",
            params={"keys": self.STREAM_KEYS, "key_by_type": "true"},
        )

    def fetch_activity_detail(self, activity_id: str) -> Dict[str, Any]:
        """Fetch detailed Strava activity including segment_efforts, laps, and splits."""
        return self._get(f"/activities/{activity_id}")

    def sync_activities(
        self,
        days: int = 30,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        force: bool = False,
        include_streams: bool = False,
    ) -> Dict[str, Any]:
        """Fetch activities from Strava, save raw JSONs, and store in SQLite with deduplication."""
        from src.modules.repositories import _ensure_db

        activities = self.fetch_activities(days=days, start_date=start_date, end_date=end_date)
        raw_dir = get_strava_raw_dir(self.user_id)
        db_path = os.path.join("data", "users", self.user_id, "coach.db")
        _ensure_db(db_path)
        repo = ActivityRepository(db_path)

        synced = 0
        deduplicated = 0
        streams_fetched = 0
        errors: List[str] = []

        try:
            for act in activities:
                act_id = str(act.get("id", ""))
                if not act_id:
                    continue

                raw_file = os.path.join(raw_dir, f"activity_{act_id}.json")
                if not force and os.path.exists(raw_file) and not include_streams:
                    # Still ensure it's in DB if missing
                    pass

                with open(raw_file, "w") as f:
                    json.dump(act, f, indent=2)

                streams: Optional[Dict[str, Any]] = None
                streams_file = os.path.join(raw_dir, f"streams_{act_id}.json")
                if include_streams:
                    if not force and os.path.exists(streams_file):
                        try:
                            with open(streams_file, "r") as f:
                                streams = json.load(f)
                        except (OSError, json.JSONDecodeError):
                            streams = None
                    if streams is None:
                        try:
                            streams = self.fetch_activity_streams(act_id)
                            with open(streams_file, "w") as f:
                                json.dump(streams, f, indent=2)
                            streams_fetched += 1
                        except StravaRateLimitError:
                            raise
                        except Exception as exc:
                            errors.append(f"Streams failed for {act_id}: {exc}")

                saved_id = repo.save(act, source="strava", streams=streams)
                if saved_id != f"strava_{act_id}":
                    deduplicated += 1
                else:
                    synced += 1
        finally:
            repo.close()

        return {
            "total_fetched": len(activities),
            "synced": synced,
            "deduplicated": deduplicated,
            "streams_fetched": streams_fetched,
            "errors": errors,
        }
