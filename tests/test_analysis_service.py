"""
Tests for AnalysisService.
"""

import pytest
import tempfile
import os
from datetime import date, timedelta

from src.modules.repositories import ActivityRepository, JournalRepository, MetricsCache
from src.modules.analysis_service import AnalysisService
from src.modules.migrations.init_db import create_schema
import sqlite3


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    create_schema(conn)
    conn.close()

    yield path
    os.unlink(path)


@pytest.fixture
def repos(temp_db):
    """Create repository instances."""
    activity_repo = ActivityRepository(temp_db)
    journal_repo = JournalRepository(temp_db)
    metrics_cache = MetricsCache(temp_db)

    yield activity_repo, journal_repo, metrics_cache

    activity_repo.close()
    journal_repo.close()
    metrics_cache.close()


@pytest.fixture
def service(repos):
    """Create an AnalysisService instance."""
    activity_repo, journal_repo, metrics_cache = repos
    return AnalysisService(activity_repo, journal_repo, metrics_cache)


def create_activity(activity_date: date, distance_km: float, avg_hr: int = 130, cadence: float = 170):
    """Helper to create test activity."""
    distance_m = distance_km * 1000
    duration_sec = (distance_km / 5) * 60 * 5  # Assume 5 min/km pace

    return {
        'activityId': f"{activity_date.isoformat()}_{distance_km}",
        'startTimeLocal': f"{activity_date.isoformat()} 08:00:00",
        'activityType': {'typeKey': 'running'},
        'distance': distance_m,
        'duration': duration_sec,
        'averageHR': avg_hr,
        'averageRunningCadenceInStepsPerMinute': cadence,
        'elevationGain': 50,
        'vO2MaxValue': 50,
        'aerobicTrainingEffect': 3.0
    }


def create_journal(entry_date: date, rpe: int = 5, soreness: int = 2):
    """Helper to create test journal entry."""
    return {
        'date': entry_date.isoformat(),
        'rpe': rpe,
        'mood': '😊',
        'soreness': soreness,
        'notes': 'Test entry'
    }


class TestACWRCalculation:
    """Tests for ACWR (Acute:Chronic Workload Ratio) calculation."""

    def test_acwr_with_consistent_training(self, service, repos):
        """Test ACWR with consistent training load."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Create 28 days of consistent 40km/week (5.7km/day)
        for days_ago in range(28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.7))

        acwr = service.get_acwr(today)

        # Should be ~1.0 with consistent training
        assert acwr is not None
        assert 0.95 <= acwr <= 1.05

    def test_acwr_with_volume_spike(self, service, repos):
        """Test ACWR detects volume spike."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Previous 3 weeks: 35km/week (5km/day)
        for days_ago in range(7, 28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.0))

        # Last week: 50km (spike to 7.1km/day)
        for days_ago in range(7):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 7.1))

        acwr = service.get_acwr(today)

        # Should be approaching risky zone (>= 1.25)
        assert acwr is not None
        assert acwr >= 1.25

    def test_acwr_with_detraining(self, service, repos):
        """Test ACWR detects detraining."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Previous 3 weeks: 40km/week
        for days_ago in range(7, 28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.7))

        # Last week: only 20km
        for days_ago in range(0, 7, 2):  # Every other day
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.0))

        acwr = service.get_acwr(today)

        # Should be < 0.8
        assert acwr is not None
        assert acwr < 0.8

    def test_acwr_insufficient_data(self, service, repos):
        """Test ACWR returns None with insufficient data."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Only 3 days of data
        for days_ago in range(3):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.0))

        acwr = service.get_acwr(today)

        # Should return None
        assert acwr is None


class TestInjuryRiskAnalysis:
    """Tests for injury risk analysis."""

    def test_low_risk_scenario(self, service, repos):
        """Test low injury risk with good training practices."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Consistent training with good cadence
        for days_ago in range(28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.7, avg_hr=130, cadence=175))

        # Low soreness
        for days_ago in range(7):
            journal_date = today - timedelta(days=days_ago)
            journal_repo.save(create_journal(journal_date, rpe=5, soreness=2))

        risk = service.get_injury_risk(today)

        assert risk is not None
        assert risk.overall_risk == 'low'
        assert risk.risk_score < 30

    def test_high_risk_low_cadence(self, service, repos):
        """Test injury risk with low cadence."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Low cadence running
        for days_ago in range(28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.7, cadence=155))  # Very low

        risk = service.get_injury_risk(today)

        assert risk is not None
        assert any('cadence' in factor.lower() for factor in risk.risk_factors)
        assert risk.avg_cadence < 170

    def test_high_risk_volume_spike(self, service, repos):
        """Test injury risk with volume spike."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Previous weeks: 30km
        for days_ago in range(7, 28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 4.3))

        # Last week: 55km (huge spike)
        for days_ago in range(7):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 7.9))

        risk = service.get_injury_risk(today)

        assert risk is not None
        assert risk.overall_risk in ['moderate', 'high']
        assert any('volume' in factor.lower() or 'acwr' in factor.lower() for factor in risk.risk_factors)

    def test_rising_soreness_trend(self, service, repos):
        """Test injury risk with rising soreness."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Consistent training
        for days_ago in range(28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.7))

        # Rising soreness over the week
        soreness_values = [2, 3, 4, 5, 6, 7, 8]
        for days_ago in range(7):
            journal_date = today - timedelta(days=days_ago)
            journal_repo.save(create_journal(journal_date, soreness=soreness_values[6 - days_ago]))

        risk = service.get_injury_risk(today)

        assert risk is not None
        assert risk.soreness_trend in ['rising', 'high', 'elevated']  # High soreness detected
        assert any('soreness' in factor.lower() for factor in risk.risk_factors)


class TestWeeklyMetrics:
    """Tests for weekly metrics calculation."""

    def test_weekly_metrics_aggregation(self, service, repos):
        """Test correct aggregation of weekly metrics."""
        activity_repo, journal_repo, _ = repos

        # Week of Feb 3-9, 2026 (Mon-Sun)
        week_start = date(2026, 2, 3)

        # Add 4 runs during the week
        runs = [
            (date(2026, 2, 3), 5.0, 130),
            (date(2026, 2, 5), 10.0, 135),
            (date(2026, 2, 7), 8.0, 128),
            (date(2026, 2, 9), 20.0, 125)  # Long run
        ]

        for run_date, distance, hr in runs:
            activity_repo.save(create_activity(run_date, distance, avg_hr=hr))

        metrics = service.get_weekly_metrics(week_start)

        assert metrics.total_distance_km == 43.0
        assert metrics.session_count == 4
        assert metrics.longest_run_km == 20.0
        assert 125 <= metrics.avg_hr <= 135  # Should be close to average

    def test_intensity_distribution(self, service, repos):
        """Test intensity distribution calculation."""
        activity_repo, journal_repo, _ = repos
        week_start = date(2026, 2, 3)

        # 3 easy runs (HR < 130), 1 tempo (HR 135)
        activity_repo.save(create_activity(date(2026, 2, 3), 5.0, avg_hr=125))
        activity_repo.save(create_activity(date(2026, 2, 4), 5.0, avg_hr=128))
        activity_repo.save(create_activity(date(2026, 2, 5), 5.0, avg_hr=129))
        activity_repo.save(create_activity(date(2026, 2, 6), 8.0, avg_hr=138))

        metrics = service.get_weekly_metrics(week_start)

        assert metrics.intensity_distribution['easy'] == 3
        assert metrics.intensity_distribution['tempo'] >= 1


class TestFatigueIndex:
    """Tests for fatigue index calculation."""

    def test_low_fatigue(self, service, repos):
        """Test low fatigue with good recovery."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Consistent light training
        for days_ago in range(28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.0))

        # Low soreness and RPE
        for days_ago in range(7):
            journal_date = today - timedelta(days=days_ago)
            journal_repo.save(create_journal(journal_date, rpe=3, soreness=1))

        fatigue = service.get_fatigue_index(today)

        assert fatigue is not None
        assert fatigue < 30

    def test_high_fatigue(self, service, repos):
        """Test high fatigue with heavy training and poor recovery."""
        activity_repo, journal_repo, _ = repos
        today = date(2026, 2, 1)

        # Heavy training
        for days_ago in range(7, 28):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 5.0))

        for days_ago in range(7):
            activity_date = today - timedelta(days=days_ago)
            activity_repo.save(create_activity(activity_date, 9.0))

        # High soreness and RPE
        for days_ago in range(7):
            journal_date = today - timedelta(days=days_ago)
            journal_repo.save(create_journal(journal_date, rpe=8, soreness=7))

        fatigue = service.get_fatigue_index(today)

        assert fatigue is not None
        assert fatigue > 50


class TestActivityMetrics:
    """Tests for individual activity metrics."""

    def test_activity_metrics_calculation(self, service, repos):
        """Test computation of activity-level metrics."""
        activity_repo, _, _ = repos

        # Create a specific activity
        activity_date = date(2026, 2, 1)
        distance_km = 10.0
        avg_hr = 140
        cadence = 170

        activity = create_activity(activity_date, distance_km, avg_hr, cadence)
        activity_id = activity_repo.save(activity)

        metrics = service.get_activity_metrics(activity_id)

        assert metrics is not None
        assert metrics.distance_km == distance_km
        assert metrics.avg_hr == avg_hr
        assert metrics.cadence == cadence
        assert metrics.pace_per_km_sec is not None
        assert metrics.efficiency_score is not None

    def test_efficiency_score(self, service, repos):
        """Test efficiency score calculation."""
        activity_repo, _, _ = repos

        # Two activities with different efficiency
        # Activity 1: 5:00/km at 140 HR
        act1 = create_activity(date(2026, 2, 1), 10.0, avg_hr=140, cadence=170)
        act1['duration'] = 3000  # 50 min = 5:00/km
        act1_id = activity_repo.save(act1)

        # Activity 2: 5:00/km at 130 HR (more efficient)
        act2 = create_activity(date(2026, 2, 2), 10.0, avg_hr=130, cadence=170)
        act2['duration'] = 3000
        act2_id = activity_repo.save(act2)

        metrics1 = service.get_activity_metrics(act1_id)
        metrics2 = service.get_activity_metrics(act2_id)

        # Activity 2 should be more efficient (higher score)
        assert metrics2.efficiency_score > metrics1.efficiency_score
