"""
Data access layer for Coach Conejito.

This module provides repository classes for efficient data access using SQLite.
"""

import sqlite3
import json
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Any
from pathlib import Path


class ActivityRepository:
    """Repository for activity data access with SQLite backend."""

    def __init__(self, db_path: str):
        """
        Initialize the repository.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name

    def get_by_id(self, activity_id: str) -> Optional[Dict]:
        """Get a single activity by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_dict(row)
        return None

    def get_range(self, start_date: date, end_date: date, activity_type: Optional[str] = None) -> List[Dict]:
        """
        Get activities within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            activity_type: Optional filter by activity type (e.g., 'running')

        Returns:
            List of activity dictionaries sorted by date descending
        """
        cursor = self.conn.cursor()

        if activity_type:
            cursor.execute("""
                SELECT * FROM activities
                WHERE date >= ? AND date <= ?
                  AND activity_type LIKE ?
                ORDER BY date DESC
            """, (start_date.isoformat(), end_date.isoformat(), f"%{activity_type}%"))
        else:
            cursor.execute("""
                SELECT * FROM activities
                WHERE date >= ? AND date <= ?
                ORDER BY date DESC
            """, (start_date.isoformat(), end_date.isoformat()))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_latest(self, limit: int = 10, activity_type: Optional[str] = None) -> List[Dict]:
        """
        Get most recent activities.

        Args:
            limit: Maximum number of activities to return
            activity_type: Optional filter by activity type

        Returns:
            List of activity dictionaries sorted by date descending
        """
        cursor = self.conn.cursor()

        if activity_type:
            cursor.execute("""
                SELECT * FROM activities
                WHERE activity_type LIKE ?
                ORDER BY date DESC
                LIMIT ?
            """, (f"%{activity_type}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM activities
                ORDER BY date DESC
                LIMIT ?
            """, (limit,))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_all_after(self, start_date: date) -> List[Dict]:
        """Get all activities after a given date."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM activities
            WHERE date >= ?
            ORDER BY date DESC
        """, (start_date.isoformat(),))

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def query(self, where_clause: str, params: tuple = ()) -> List[Dict]:
        """
        Execute a custom SQL query.

        Args:
            where_clause: SQL WHERE clause (without 'WHERE' keyword)
            params: Query parameters as tuple

        Returns:
            List of matching activity dictionaries
        """
        cursor = self.conn.cursor()
        sql = f"SELECT * FROM activities WHERE {where_clause} ORDER BY date DESC"
        cursor.execute(sql, params)

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def save(
        self,
        activity: Dict,
        source: str = "garmin",
        streams: Optional[Dict] = None,
    ) -> str:
        """
        Save an activity to the database.

        Accepts either raw Garmin activity dicts or pre-normalized activity dicts.
        Performs cross-source deduplication when saving non-Garmin activities.

        Args:
            activity: Activity data dictionary
            source: Data source identifier ('garmin' or 'strava')
            streams: Optional time-series streams dictionary

        Returns:
            Activity ID
        """
        external_id = str(activity.get("external_id") or activity.get("activityId") or activity.get("id") or "")
        activity_id = str(activity.get("id") or (f"strava_{external_id}" if source == "strava" else external_id))

        # Extract date & start_time_utc
        start_local = activity.get("startTimeLocal") or activity.get("start_date_local") or ""
        start_utc = (
            activity.get("start_time_utc")
            or activity.get("startTimeGMT")
            or activity.get("start_date")
            or start_local
            or None
        )
        if activity.get("date"):
            activity_date = str(activity["date"])[:10]
        elif start_local:
            activity_date = str(start_local)[:10]
        elif start_utc:
            activity_date = str(start_utc)[:10]
        else:
            activity_date = None

        # Extract activity type
        activity_type_key = activity.get("activity_type")
        if not activity_type_key:
            if "activityType" in activity and isinstance(activity["activityType"], dict):
                activity_type_key = activity["activityType"].get("typeKey")
            elif activity.get("type"):
                activity_type_key = str(activity["type"]).lower()

        distance_m = activity.get("distance_m") if "distance_m" in activity else activity.get("distance")
        duration_sec = activity.get("duration_sec") if "duration_sec" in activity else (
            activity.get("duration") if activity.get("duration") is not None else activity.get("moving_time")
        )

        # Cross-source deduplication: if Strava activity matches an existing Garmin activity,
        # enrich streams instead of inserting a duplicate row.
        if source != "garmin" and start_utc and distance_m is not None:
            existing_id = self.find_duplicate(start_utc, float(distance_m), exclude_source=source)
            if existing_id:
                if streams:
                    self.update_streams(existing_id, streams)
                return existing_id

        streams_json = json.dumps(streams) if streams is not None else activity.get("streams_json")

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO activities (
                id, date, activity_type, activity_name,
                distance_m, duration_sec, avg_hr, max_hr,
                cadence, elevation_gain_m, elevation_loss_m,
                vo2_max, aerobic_training_effect, anaerobic_training_effect,
                avg_speed, max_speed, calories, training_load,
                source, external_id, start_time_utc, streams_json,
                raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_id,
            activity_date,
            activity_type_key,
            activity.get("activity_name") or activity.get("activityName") or activity.get("name"),
            distance_m,
            duration_sec,
            activity.get("avg_hr") if "avg_hr" in activity else (activity.get("averageHR") or activity.get("average_heartrate")),
            activity.get("max_hr") if "max_hr" in activity else (activity.get("maxHR") or activity.get("max_heartrate")),
            activity.get("cadence") if "cadence" in activity else (
                activity.get("averageRunningCadenceInStepsPerMinute")
                or (activity.get("average_cadence") * 2 if activity.get("average_cadence") else None)
            ),
            activity.get("elevation_gain_m") if "elevation_gain_m" in activity else (
                activity.get("elevationGain") if activity.get("elevationGain") is not None else activity.get("total_elevation_gain")
            ),
            activity.get("elevation_loss_m") if "elevation_loss_m" in activity else activity.get("elevationLoss"),
            activity.get("vo2_max") if "vo2_max" in activity else activity.get("vO2MaxValue"),
            activity.get("aerobic_training_effect") if "aerobic_training_effect" in activity else activity.get("aerobicTrainingEffect"),
            activity.get("anaerobic_training_effect") if "anaerobic_training_effect" in activity else activity.get("anaerobicTrainingEffect"),
            activity.get("avg_speed") if "avg_speed" in activity else (activity.get("averageSpeed") or activity.get("average_speed")),
            activity.get("max_speed") if "max_speed" in activity else (activity.get("maxSpeed") or activity.get("max_speed")),
            activity.get("calories"),
            activity.get("training_load") if "training_load" in activity else (activity.get("activityTrainingLoad") or activity.get("suffer_score")),
            source,
            external_id,
            start_utc,
            streams_json,
            json.dumps(activity),
        ))

        self.conn.commit()
        return activity_id

    def find_duplicate(
        self,
        start_time_utc: str,
        distance_m: float,
        tolerance_sec: int = 120,
        tolerance_pct: float = 0.02,
        exclude_source: Optional[str] = None,
    ) -> Optional[str]:
        """Find an existing activity matching start time and distance within tolerance."""
        try:
            target_dt = datetime.fromisoformat(str(start_time_utc).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None

        target_date = target_dt.date()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, source, start_time_utc, distance_m
            FROM activities
            WHERE date >= ? AND date <= ?
            """,
            ((target_date - timedelta(days=1)).isoformat(), (target_date + timedelta(days=1)).isoformat()),
        )

        for row in cursor.fetchall():
            if exclude_source and row["source"] == exclude_source:
                continue
            row_dist = row["distance_m"]
            row_ts = row["start_time_utc"]
            if row_dist is None or not row_ts:
                continue
            try:
                row_dt = datetime.fromisoformat(str(row_ts).replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                continue

            if abs((row_dt - target_dt).total_seconds()) <= tolerance_sec:
                max_dist = max(abs(distance_m), abs(row_dist), 1.0)
                if abs(row_dist - distance_m) / max_dist <= tolerance_pct:
                    return row["id"]
        return None

    def update_streams(self, activity_id: str, streams: Dict) -> None:
        """Attach or update streams JSON on an existing activity."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE activities SET streams_json = ? WHERE id = ?",
            (json.dumps(streams), activity_id),
        )
        self.conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert a database row to a dictionary."""
        data = dict(row)

        # Parse raw JSON if available
        if data.get('raw_json'):
            try:
                raw = json.loads(data['raw_json'])
                # Merge with structured fields (structured fields take precedence)
                result = {**raw, **data}
                # Remove raw_json from final output
                result.pop('raw_json', None)
                return result
            except json.JSONDecodeError:
                pass

        return data

    def close(self):
        """Close the database connection."""
        self.conn.close()


class JournalRepository:
    """Repository for journal entry data access."""

    def __init__(self, db_path: str):
        """
        Initialize the repository.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_by_date(self, entry_date: date) -> Optional[Dict]:
        """Get a journal entry for a specific date."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM journals WHERE date = ?", (entry_date.isoformat(),))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_range(self, start_date: date, end_date: date) -> List[Dict]:
        """Get journal entries within a date range."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM journals
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC
        """, (start_date.isoformat(), end_date.isoformat()))

        return [dict(row) for row in cursor.fetchall()]

    def get_latest(self, limit: int = 10) -> List[Dict]:
        """Get most recent journal entries."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM journals
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def save(self, entry: Dict) -> str:
        """
        Save a journal entry.

        Args:
            entry: Journal entry data with 'date', 'rpe', 'mood', 'soreness', 'notes'

        Returns:
            Entry date as string
        """
        entry_date = entry['date']
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO journals (date, rpe, mood, soreness, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry_date,
            entry.get('rpe'),
            entry.get('mood'),
            entry.get('soreness'),
            entry.get('notes'),
            datetime.now()
        ))

        self.conn.commit()
        return entry_date

    def delete(self, entry_date: date) -> bool:
        """Delete a journal entry."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM journals WHERE date = ?", (entry_date.isoformat(),))
        self.conn.commit()
        return cursor.rowcount > 0

    def close(self):
        """Close the database connection."""
        self.conn.close()


class MetricsCache:
    """Cache for computed weekly metrics."""

    def __init__(self, db_path: str):
        """
        Initialize the cache.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_weekly_metrics(self, week_start: date) -> Optional[Dict]:
        """Retrieve cached weekly metrics."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM weekly_metrics WHERE week_start = ?", (week_start.isoformat(),))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def save_weekly_metrics(self, metrics: Dict) -> None:
        """
        Save weekly metrics to cache.

        Args:
            metrics: Dictionary with week_start and computed metrics
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO weekly_metrics (
                week_start, total_distance_km, total_duration_min,
                session_count, longest_run_km, avg_hr, avg_cadence,
                acwr, fatigue_index, injury_risk_score,
                easy_runs, tempo_runs, hard_runs, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics['week_start'].isoformat() if isinstance(metrics['week_start'], date) else metrics['week_start'],
            metrics.get('total_distance_km'),
            metrics.get('total_duration_min'),
            metrics.get('session_count'),
            metrics.get('longest_run_km'),
            metrics.get('avg_hr'),
            metrics.get('avg_cadence'),
            metrics.get('acwr'),
            metrics.get('fatigue_index'),
            metrics.get('injury_risk_score'),
            metrics.get('easy_runs'),
            metrics.get('tempo_runs'),
            metrics.get('hard_runs'),
            datetime.now()
        ))

        self.conn.commit()

    def invalidate_after(self, start_date: date) -> None:
        """Invalidate cached metrics after a given date."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM weekly_metrics WHERE week_start >= ?", (start_date.isoformat(),))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()


class WellnessRepository:
    """Repository for daily wellness metrics (resting HR, HRV, sleep, body battery)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def save(self, wellness: Dict) -> str:
        """Save or update a daily wellness record."""
        entry_date = wellness["date"]
        if isinstance(entry_date, date):
            entry_date = entry_date.isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO daily_wellness (
                date, resting_hr, hrv_ms, sleep_score, sleep_duration_sec,
                body_battery_high, body_battery_low, stress_avg, raw_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                resting_hr = COALESCE(excluded.resting_hr, daily_wellness.resting_hr),
                hrv_ms = COALESCE(excluded.hrv_ms, daily_wellness.hrv_ms),
                sleep_score = COALESCE(excluded.sleep_score, daily_wellness.sleep_score),
                sleep_duration_sec = COALESCE(excluded.sleep_duration_sec, daily_wellness.sleep_duration_sec),
                body_battery_high = COALESCE(excluded.body_battery_high, daily_wellness.body_battery_high),
                body_battery_low = COALESCE(excluded.body_battery_low, daily_wellness.body_battery_low),
                stress_avg = COALESCE(excluded.stress_avg, daily_wellness.stress_avg),
                raw_json = COALESCE(excluded.raw_json, daily_wellness.raw_json),
                updated_at = excluded.updated_at
            """,
            (
                entry_date,
                wellness.get("resting_hr"),
                wellness.get("hrv_ms"),
                wellness.get("sleep_score"),
                wellness.get("sleep_duration_sec"),
                wellness.get("body_battery_high"),
                wellness.get("body_battery_low"),
                wellness.get("stress_avg"),
                json.dumps(wellness.get("raw")) if wellness.get("raw") is not None else None,
                datetime.now(),
            ),
        )
        self.conn.commit()
        return entry_date

    def get_range(self, start_date: date, end_date: date) -> List[Dict]:
        """Get daily wellness records within a date range."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM daily_wellness
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_latest(self, limit: int = 14) -> List[Dict]:
        """Get most recent daily wellness records."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM daily_wellness ORDER BY date DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


def _ensure_db(db_path: str) -> None:
    """Ensure the SQLite database exists and is migrated to the latest schema."""
    from src.modules.migrations.init_db import create_schema, migrate_schema

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    conn = sqlite3.connect(db_path)
    try:
        if is_new:
            create_schema(conn)
        else:
            # Check if activities table exists; if not, create full schema, else migrate
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
            if cur.fetchone() is None:
                create_schema(conn)
            else:
                migrate_schema(conn)
    finally:
        conn.close()


def get_repository(user_id: str) -> tuple[ActivityRepository, JournalRepository, MetricsCache]:
    """
    Get repository instances for a user.

    Args:
        user_id: User identifier

    Returns:
        Tuple of (ActivityRepository, JournalRepository, MetricsCache)
    """
    db_path = f"data/users/{user_id}/coach.db"
    _ensure_db(db_path)

    return (
        ActivityRepository(db_path),
        JournalRepository(db_path),
        MetricsCache(db_path)
    )


def get_wellness_repository(user_id: str) -> WellnessRepository:
    """Get WellnessRepository instance for a user."""
    db_path = f"data/users/{user_id}/coach.db"
    _ensure_db(db_path)
    return WellnessRepository(db_path)
