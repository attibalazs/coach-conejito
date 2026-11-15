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

    def save(self, activity: Dict) -> str:
        """
        Save an activity to the database.

        Args:
            activity: Activity data dictionary (Garmin format)

        Returns:
            Activity ID
        """
        activity_id = str(activity.get('activityId'))

        # Extract date from startTimeLocal
        start_time = activity.get('startTimeLocal', '')
        if start_time:
            activity_date = start_time[:10]  # YYYY-MM-DD
        else:
            activity_date = None

        # Extract activity type
        activity_type_key = None
        if 'activityType' in activity and isinstance(activity['activityType'], dict):
            activity_type_key = activity['activityType'].get('typeKey')

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO activities (
                id, date, activity_type, activity_name,
                distance_m, duration_sec, avg_hr, max_hr,
                cadence, elevation_gain_m, elevation_loss_m,
                vo2_max, aerobic_training_effect, anaerobic_training_effect,
                avg_speed, max_speed, calories, training_load,
                raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_id,
            activity_date,
            activity_type_key,
            activity.get('activityName'),
            activity.get('distance'),
            activity.get('duration'),
            activity.get('averageHR'),
            activity.get('maxHR'),
            activity.get('averageRunningCadenceInStepsPerMinute'),
            activity.get('elevationGain'),
            activity.get('elevationLoss'),
            activity.get('vO2MaxValue'),
            activity.get('aerobicTrainingEffect'),
            activity.get('anaerobicTrainingEffect'),
            activity.get('averageSpeed'),
            activity.get('maxSpeed'),
            activity.get('calories'),
            activity.get('activityTrainingLoad'),
            json.dumps(activity)
        ))

        self.conn.commit()
        return activity_id

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


def get_repository(user_id: str) -> tuple[ActivityRepository, JournalRepository, MetricsCache]:
    """
    Get repository instances for a user.

    Args:
        user_id: User identifier

    Returns:
        Tuple of (ActivityRepository, JournalRepository, MetricsCache)
    """
    db_path = f"data/users/{user_id}/coach.db"

    return (
        ActivityRepository(db_path),
        JournalRepository(db_path),
        MetricsCache(db_path)
    )
