"""
Tests for CLI commands.
"""
import pytest
from click.testing import CliRunner
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.cli_main import cli
from src.modules.analysis_service import WeeklyMetrics, InjuryRiskAnalysis, ActivityMetrics


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_services(monkeypatch):
    """Mock repository services."""
    mock_activity_repo = Mock()
    mock_journal_repo = Mock()
    mock_cache = Mock()

    def mock_get_repository(user_id):
        return mock_activity_repo, mock_journal_repo, mock_cache

    monkeypatch.setattr('src.cli.status.get_repository', mock_get_repository)
    monkeypatch.setattr('src.cli.risk.get_repository', mock_get_repository)
    monkeypatch.setattr('src.cli.metrics.get_repository', mock_get_repository)
    monkeypatch.setattr('src.cli.activity.get_repository', mock_get_repository)
    monkeypatch.setattr('src.cli.sync.get_repository', mock_get_repository)

    return mock_activity_repo, mock_journal_repo, mock_cache


def test_status_command(cli_runner, mock_services, monkeypatch):
    """Test status command displays weekly summary."""
    # Mock AnalysisService
    mock_service = Mock()

    # Create mock data
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    metrics = WeeklyMetrics(
        week_start=week_start,
        total_distance_km=40.5,
        total_duration_min=240,
        session_count=4,
        longest_run_km=22.4,
        avg_hr=128,
        avg_cadence=165,
        acwr=1.15,
        fatigue_index=18,
        injury_risk_score=28,
        intensity_distribution={
            'easy': 3,
            'tempo': 1,
            'hard': 0,
            'easy_km': 32.0,
            'tempo_km': 8.5,
            'hard_km': 0,
            'easy_count': 3,
            'tempo_count': 1,
            'hard_count': 0
        },
        week_over_week_change=5.0
    )

    risk = InjuryRiskAnalysis(
        overall_risk='low',
        risk_score=23.9,
        risk_factors=['Low cadence: 165 spm (target: 170+)'],
        recommendations=['Focus on increasing cadence'],
        soreness_trend='stable',
        acwr=1.15,
        volume_change_pct=15.0,
        avg_cadence=165,
        risk_breakdown={
            'volume_spike': 9.0,
            'low_cadence': 50.0,
            'rising_soreness': 0.0,
            'acwr_deviation': 15.0
        }
    )

    mock_service.get_weekly_summary.return_value = {
        'week_start': week_start,
        'week_end': week_start + timedelta(days=6),
        'metrics': metrics,
        'injury_risk': risk,
        'alerts': [
            {
                'level': 'warning',
                'message': 'Cadence below target: 165 avg (target: 170+)',
                'recommendation': 'Use metronome at 170 BPM on next run'
            }
        ],
        'activities': []
    }

    # Patch AnalysisService
    monkeypatch.setattr('src.cli.status.AnalysisService', lambda *args: mock_service)

    # Run command
    result = cli_runner.invoke(cli, ['--user', 'test', 'status'])

    # Check output
    assert result.exit_code == 0
    assert 'WEEK SUMMARY' in result.output
    assert '40.5 km' in result.output
    assert 'ACWR' in result.output
    assert 'Injury Risk' in result.output


def test_risk_command(cli_runner, mock_services, monkeypatch):
    """Test risk command displays injury risk analysis."""
    mock_service = Mock()

    risk = InjuryRiskAnalysis(
        overall_risk='moderate',
        risk_score=38.5,
        risk_factors=[
            'ACWR 1.23 (safe zone: 0.8-1.3)',
            'Low cadence: 165 spm (target: 170+)'
        ],
        recommendations=[
            'Reduce volume by 10-15% next week',
            'Use metronome at 170 BPM'
        ],
        soreness_trend='stable',
        acwr=1.23,
        volume_change_pct=23.0,
        avg_cadence=165,
        risk_breakdown={
            'volume_spike': 45.0,
            'low_cadence': 50.0,
            'rising_soreness': 20.0,
            'acwr_deviation': 23.0
        }
    )

    mock_service.get_injury_risk.return_value = risk

    monkeypatch.setattr('src.cli.risk.AnalysisService', lambda *args: mock_service)

    result = cli_runner.invoke(cli, ['--user', 'test', 'risk'])

    assert result.exit_code == 0
    assert 'INJURY RISK ANALYSIS' in result.output
    assert 'MODERATE' in result.output
    assert '38.5/100' in result.output
    assert 'RISK BREAKDOWN' in result.output


def test_metrics_weekly_command(cli_runner, mock_services, monkeypatch):
    """Test metrics command with weekly trends."""
    mock_service = Mock()

    # Create mock weekly data
    today = date.today()
    weeks_data = []

    for i in range(4):
        week_date = today - timedelta(weeks=3-i)
        week_start = week_date - timedelta(days=week_date.weekday())

        weeks_data.append(WeeklyMetrics(
            week_start=week_start,
            total_distance_km=40.0 + i * 2,
            total_duration_min=240,
            session_count=4,
            longest_run_km=20.0,
            avg_hr=128,
            avg_cadence=165,
            acwr=1.08 + i * 0.05,
            fatigue_index=20,
            injury_risk_score=20 + i * 5,
            intensity_distribution={'easy': 3, 'tempo': 1, 'hard': 0}
        ))

    mock_service.get_weekly_metrics.side_effect = weeks_data

    monkeypatch.setattr('src.cli.metrics.AnalysisService', lambda *args: mock_service)

    result = cli_runner.invoke(cli, ['--user', 'test', 'metrics', '--weekly', '--last', '4'])

    assert result.exit_code == 0
    assert 'WEEKLY METRICS' in result.output
    assert 'Distance' in result.output
    assert 'ACWR' in result.output


def test_activity_list_command(cli_runner, mock_services, monkeypatch):
    """Test activity list command."""
    mock_activity_repo, _, _ = mock_services

    # Create mock activities
    activities = [
        {
            'activityId': '123',
            'startTimeLocal': '2026-02-01T08:00:00',
            'activityType': {'typeKey': 'running'},
            'distance': 10000,  # 10km in meters
            'duration': 3000,   # 50 minutes
            'averageHR': 135
        },
        {
            'activityId': '124',
            'startTimeLocal': '2026-02-03T08:00:00',
            'activityType': {'typeKey': 'running'},
            'distance': 5000,
            'duration': 1500,
            'averageHR': 125
        }
    ]

    mock_activity_repo.get_latest.return_value = activities

    result = cli_runner.invoke(cli, ['--user', 'test', 'activity', 'list', '--limit', '10'])

    assert result.exit_code == 0
    assert 'RECENT ACTIVITIES' in result.output
    assert '10.0 km' in result.output
    assert '5.0 km' in result.output


def test_activity_show_command(cli_runner, mock_services, monkeypatch):
    """Test activity show command for detailed view."""
    mock_activity_repo, _, _ = mock_services
    mock_service = Mock()

    # Mock activity data
    activity = {
        'activityId': '123',
        'activityName': 'Morning Run',
        'startTimeLocal': '2026-02-01T08:00:00',
        'activityType': {'typeKey': 'running'},
        'distance': 10000,
        'duration': 3000,
        'averageHR': 135,
        'averageRunningCadenceInStepsPerMinute': 165,
        'elevationGain': 150,
        'aerobicTrainingEffect': 3.5,
        'date': '2026-02-01'
    }

    metrics = ActivityMetrics(
        activity_id='123',
        date=date(2026, 2, 1),
        distance_km=10.0,
        duration_min=50.0,
        pace_per_km_sec=300,  # 5:00/km
        avg_hr=135,
        cadence=165,
        elevation_m=150,
        training_effect=3.5,
        vo2_max=53,
        hr_zones={2: 20, 3: 25, 4: 5},
        efficiency_score=2.22,
        activity_type='running'
    )

    mock_activity_repo.get_by_id.return_value = activity
    mock_service.get_activity_metrics.return_value = metrics

    monkeypatch.setattr('src.cli.activity.AnalysisService', lambda *args: mock_service)

    result = cli_runner.invoke(cli, ['--user', 'test', 'activity', 'show', '123'])

    assert result.exit_code == 0
    assert 'Morning Run' in result.output
    assert '10.0 km' in result.output
    assert 'PHYSIOLOGICAL' in result.output


def test_sync_command(cli_runner, mock_services, monkeypatch):
    """Test sync command."""
    mock_garmin = Mock()
    mock_garmin.sync_activities.return_value = [
        {'activityId': '123'},
        {'activityId': '124'}
    ]

    monkeypatch.setattr('src.cli.sync.GarminClient', lambda *args: mock_garmin)

    result = cli_runner.invoke(cli, ['--user', 'test', 'sync', '--days', '7'])

    assert result.exit_code == 0
    assert 'Syncing Garmin data' in result.output
    assert '2 activities' in result.output


def test_cli_user_option(cli_runner):
    """Test that --user option is properly passed."""
    result = cli_runner.invoke(cli, ['--user', 'custom_user', '--help'])

    assert result.exit_code == 0
    assert 'Coach Conejito' in result.output


def test_cli_help(cli_runner):
    """Test CLI help output."""
    result = cli_runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert 'Coach Conejito' in result.output
    assert 'status' in result.output
    assert 'metrics' in result.output
    assert 'risk' in result.output
    assert 'sync' in result.output
    assert 'activity' in result.output
