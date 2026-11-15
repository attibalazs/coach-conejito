"""
Tests for repository layer.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import date, timedelta
from pathlib import Path

from src.modules.repositories import ActivityRepository, JournalRepository, MetricsCache
from src.modules.migrations.init_db import create_schema


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    create_schema(conn)
    conn.close()

    yield path

    # Cleanup
    os.unlink(path)


@pytest.fixture
def activity_repo(temp_db):
    """Create an ActivityRepository instance."""
    repo = ActivityRepository(temp_db)
    yield repo
    repo.close()


@pytest.fixture
def journal_repo(temp_db):
    """Create a JournalRepository instance."""
    repo = JournalRepository(temp_db)
    yield repo
    repo.close()


@pytest.fixture
def metrics_cache(temp_db):
    """Create a MetricsCache instance."""
    cache = MetricsCache(temp_db)
    yield cache
    cache.close()


def create_test_activity(activity_id: str, activity_date: str, distance_m: float = 5000, avg_hr: int = 140):
    """Helper to create test activity data."""
    return {
        'activityId': activity_id,
        'startTimeLocal': f"{activity_date} 08:00:00",
        'activityType': {'typeKey': 'running'},
        'activityName': 'Test Run',
        'distance': distance_m,
        'duration': 1800,  # 30 minutes
        'averageHR': avg_hr,
        'averageRunningCadenceInStepsPerMinute': 170,
        'elevationGain': 50,
        'vO2MaxValue': 50
    }


class TestActivityRepository:
    """Tests for ActivityRepository."""

    def test_save_and_get_by_id(self, activity_repo):
        """Test saving and retrieving an activity."""
        activity = create_test_activity('12345', '2026-01-01')
        activity_id = activity_repo.save(activity)

        assert activity_id == '12345'

        retrieved = activity_repo.get_by_id('12345')
        assert retrieved is not None
        assert retrieved['id'] == '12345'
        assert retrieved['distance_m'] == 5000
        assert retrieved['avg_hr'] == 140

    def test_get_range(self, activity_repo):
        """Test retrieving activities in a date range."""
        # Create activities
        activity_repo.save(create_test_activity('1', '2026-01-01', 5000))
        activity_repo.save(create_test_activity('2', '2026-01-05', 8000))
        activity_repo.save(create_test_activity('3', '2026-01-10', 6000))

        # Query range
        activities = activity_repo.get_range(
            date(2026, 1, 3),
            date(2026, 1, 12)
        )

        assert len(activities) == 2
        assert activities[0]['id'] == '3'  # Sorted descending by date
        assert activities[1]['id'] == '2'

    def test_get_latest(self, activity_repo):
        """Test retrieving latest activities."""
        # Create multiple activities
        for i in range(5):
            activity_date = f"2026-01-{i+1:02d}"
            activity_repo.save(create_test_activity(str(i), activity_date))

        latest = activity_repo.get_latest(3)
        assert len(latest) == 3
        assert latest[0]['id'] == '4'  # Most recent

    def test_activity_type_filter(self, activity_repo):
        """Test filtering by activity type."""
        running = create_test_activity('1', '2026-01-01')
        running['activityType'] = {'typeKey': 'running'}
        activity_repo.save(running)

        cycling = create_test_activity('2', '2026-01-02')
        cycling['activityType'] = {'typeKey': 'cycling'}
        activity_repo.save(cycling)

        runs = activity_repo.get_latest(10, activity_type='running')
        assert len(runs) == 1
        assert runs[0]['id'] == '1'


class TestJournalRepository:
    """Tests for JournalRepository."""

    def test_save_and_get_by_date(self, journal_repo):
        """Test saving and retrieving journal entries."""
        entry = {
            'date': '2026-01-01',
            'rpe': 5,
            'mood': '😊',
            'soreness': 2,
            'notes': 'Felt good today'
        }

        journal_repo.save(entry)

        retrieved = journal_repo.get_by_date(date(2026, 1, 1))
        assert retrieved is not None
        assert retrieved['rpe'] == 5
        assert retrieved['soreness'] == 2

    def test_get_range(self, journal_repo):
        """Test retrieving journal entries in a range."""
        for day in range(1, 6):
            entry = {
                'date': f'2026-01-{day:02d}',
                'rpe': day,
                'soreness': day
            }
            journal_repo.save(entry)

        entries = journal_repo.get_range(date(2026, 1, 2), date(2026, 1, 4))
        assert len(entries) == 3

    def test_update_entry(self, journal_repo):
        """Test updating an existing entry."""
        entry = {
            'date': '2026-01-01',
            'rpe': 5,
            'soreness': 2
        }
        journal_repo.save(entry)

        # Update
        entry['rpe'] = 7
        entry['soreness'] = 4
        journal_repo.save(entry)

        retrieved = journal_repo.get_by_date(date(2026, 1, 1))
        assert retrieved['rpe'] == 7
        assert retrieved['soreness'] == 4

    def test_delete_entry(self, journal_repo):
        """Test deleting a journal entry."""
        entry = {
            'date': '2026-01-01',
            'rpe': 5
        }
        journal_repo.save(entry)

        deleted = journal_repo.delete(date(2026, 1, 1))
        assert deleted is True

        retrieved = journal_repo.get_by_date(date(2026, 1, 1))
        assert retrieved is None


class TestMetricsCache:
    """Tests for MetricsCache."""

    def test_save_and_get_weekly_metrics(self, metrics_cache):
        """Test caching weekly metrics."""
        metrics = {
            'week_start': date(2026, 1, 6),  # Monday
            'total_distance_km': 45.5,
            'total_duration_min': 240,
            'session_count': 4,
            'longest_run_km': 20.0,
            'avg_hr': 135.0,
            'avg_cadence': 168.0,
            'acwr': 1.15,
            'fatigue_index': 25.0,
            'injury_risk_score': 18.0,
            'easy_runs': 3,
            'tempo_runs': 1,
            'hard_runs': 0
        }

        metrics_cache.save_weekly_metrics(metrics)

        retrieved = metrics_cache.get_weekly_metrics(date(2026, 1, 6))
        assert retrieved is not None
        assert retrieved['total_distance_km'] == 45.5
        assert retrieved['acwr'] == 1.15

    def test_invalidate_after(self, metrics_cache):
        """Test cache invalidation."""
        # Save metrics for multiple weeks
        for week in range(1, 4):
            metrics = {
                'week_start': date(2026, 1, week * 7),
                'total_distance_km': 40.0,
                'session_count': 4
            }
            metrics_cache.save_weekly_metrics(metrics)

        # Invalidate after week 2
        metrics_cache.invalidate_after(date(2026, 1, 14))

        # Week 1 should still exist
        week1 = metrics_cache.get_weekly_metrics(date(2026, 1, 7))
        assert week1 is not None

        # Week 3 should be gone
        week3 = metrics_cache.get_weekly_metrics(date(2026, 1, 21))
        assert week3 is None
