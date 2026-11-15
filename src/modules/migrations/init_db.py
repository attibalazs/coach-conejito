"""
Database initialization and migration script for Coach Conejito.

This module handles:
- SQLite database schema creation
- Migration of existing JSON data to SQLite
- Index creation for query optimization
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


SCHEMA_VERSION = 1


def create_schema(conn: sqlite3.Connection):
    """Create the database schema with all tables and indexes."""
    cursor = conn.cursor()

    # Activities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id TEXT PRIMARY KEY,
            date DATE NOT NULL,
            activity_type TEXT,
            activity_name TEXT,
            distance_m REAL,
            duration_sec INTEGER,
            avg_hr INTEGER,
            max_hr INTEGER,
            cadence REAL,
            elevation_gain_m REAL,
            elevation_loss_m REAL,
            vo2_max INTEGER,
            aerobic_training_effect REAL,
            anaerobic_training_effect REAL,
            avg_speed REAL,
            max_speed REAL,
            calories REAL,
            training_load REAL,
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Journals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            date DATE PRIMARY KEY,
            rpe INTEGER,
            mood TEXT,
            soreness INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Weekly metrics cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_metrics (
            week_start DATE PRIMARY KEY,
            total_distance_km REAL,
            total_duration_min REAL,
            session_count INTEGER,
            longest_run_km REAL,
            avg_hr REAL,
            avg_cadence REAL,
            acwr REAL,
            fatigue_index REAL,
            injury_risk_score REAL,
            easy_runs INTEGER,
            tempo_runs INTEGER,
            hard_runs INTEGER,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Schema version table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_date ON activities(date DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_type_date ON activities(activity_type, date DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_distance ON activities(distance_m DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_date ON journals(date DESC)")

    # Record schema version
    cursor.execute("""
        INSERT OR REPLACE INTO schema_version (version, applied_at)
        VALUES (?, ?)
    """, (SCHEMA_VERSION, datetime.now()))

    conn.commit()
    print(f"✓ Database schema created (version {SCHEMA_VERSION})")


def migrate_activities(conn: sqlite3.Connection, user_id: str) -> int:
    """
    Migrate activity data from JSON files to SQLite.

    Returns:
        Number of activities migrated
    """
    garmin_dir = Path(f"data/users/{user_id}/raw/garmin")

    if not garmin_dir.exists():
        print(f"⚠ No Garmin data directory found for user {user_id}")
        return 0

    cursor = conn.cursor()
    migrated = 0
    skipped = 0

    for json_file in sorted(garmin_dir.glob("activity_*.json")):
        try:
            with open(json_file, 'r') as f:
                activity = json.load(f)

            activity_id = str(activity.get('activityId'))

            # Check if already exists
            cursor.execute("SELECT id FROM activities WHERE id = ?", (activity_id,))
            if cursor.fetchone():
                skipped += 1
                continue

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

            # Insert activity
            cursor.execute("""
                INSERT INTO activities (
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

            migrated += 1

        except Exception as e:
            print(f"⚠ Error migrating {json_file.name}: {e}")
            continue

    conn.commit()
    print(f"✓ Migrated {migrated} activities ({skipped} already existed)")
    return migrated


def migrate_journals(conn: sqlite3.Connection, user_id: str) -> int:
    """
    Migrate journal entries from JSON files to SQLite.

    Returns:
        Number of journal entries migrated
    """
    journal_dir = Path(f"data/users/{user_id}/journal")

    if not journal_dir.exists():
        print(f"⚠ No journal directory found for user {user_id}")
        return 0

    cursor = conn.cursor()
    migrated = 0
    skipped = 0

    for json_file in sorted(journal_dir.glob("*.json")):
        try:
            with open(json_file, 'r') as f:
                entry = json.load(f)

            entry_date = entry.get('date')

            # Check if already exists
            cursor.execute("SELECT date FROM journals WHERE date = ?", (entry_date,))
            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute("""
                INSERT INTO journals (date, rpe, mood, soreness, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entry_date,
                entry.get('rpe'),
                entry.get('mood'),
                entry.get('soreness'),
                entry.get('notes')
            ))

            migrated += 1

        except Exception as e:
            print(f"⚠ Error migrating {json_file.name}: {e}")
            continue

    conn.commit()
    print(f"✓ Migrated {migrated} journal entries ({skipped} already existed)")
    return migrated


def get_db_path(user_id: str) -> Path:
    """Get the database path for a user."""
    db_dir = Path(f"data/users/{user_id}")
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "coach.db"


def migrate_user_data(user_id: str, force: bool = False) -> dict:
    """
    Run full migration for a user's data.

    Args:
        user_id: User identifier
        force: If True, recreate database from scratch

    Returns:
        Dictionary with migration statistics
    """
    db_path = get_db_path(user_id)

    if force and db_path.exists():
        print(f"⚠ Removing existing database at {db_path}")
        os.remove(db_path)

    print(f"\nMigrating data for user: {user_id}")
    print(f"Database: {db_path}")
    print("=" * 60)

    conn = sqlite3.connect(str(db_path))

    try:
        # Create schema
        create_schema(conn)

        # Migrate data
        activities_count = migrate_activities(conn, user_id)
        journals_count = migrate_journals(conn, user_id)

        print("=" * 60)
        print(f"✓ Migration complete!")
        print(f"  - Activities: {activities_count}")
        print(f"  - Journals: {journals_count}")

        return {
            'success': True,
            'activities': activities_count,
            'journals': journals_count,
            'db_path': str(db_path)
        }

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        conn.close()


def main():
    """CLI entry point for migration script."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.modules.migrations.init_db <user_id> [--force]")
        print("\nExample:")
        print("  python -m src.modules.migrations.init_db atti")
        print("  python -m src.modules.migrations.init_db atti --force")
        sys.exit(1)

    user_id = sys.argv[1]
    force = "--force" in sys.argv

    result = migrate_user_data(user_id, force=force)

    if not result['success']:
        sys.exit(1)


if __name__ == "__main__":
    main()
