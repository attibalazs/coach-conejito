"""CLI integration tests for auth, stats, trends, export, and journal commands."""
import json
from datetime import date, timedelta

from click.testing import CliRunner

from src.cli_main import cli
from src.modules.repositories import get_repository


def _seed_user_activities(user_id: str):
    act_repo, j_repo, cache = get_repository(user_id)
    today = date.today()
    for i in range(5):
        d = (today - timedelta(days=i * 3)).isoformat()
        act_repo.save({
            "activityId": 700 + i,
            "startTimeLocal": f"{d} 07:30:00",
            "activityType": {"typeKey": "running"},
            "activityName": f"Run {i}",
            "distance": 10000.0,
            "duration": 3200,
            "averageHR": 135,
            "elevationGain": 150.0,
            "elevationLoss": 150.0,
            "averageRunningCadenceInStepsPerMinute": 176.0,
        })
    act_repo.close()
    j_repo.close()
    cache.close()


def test_auth_status_command(test_user):
    runner = CliRunner()
    res = runner.invoke(cli, ["-u", test_user, "auth", "status"])
    assert res.exit_code == 0
    assert "Garmin" in res.output
    assert "Strava" in res.output


def test_stats_json_and_table(test_user):
    _seed_user_activities(test_user)
    runner = CliRunner()

    res_json = runner.invoke(cli, ["-u", test_user, "stats", "--period", "28d", "--format", "json"])
    assert res_json.exit_code == 0
    payload = json.loads(res_json.output)
    assert payload["sessions"] == 5
    assert payload["distance_km"] == 50.0
    assert payload["impact_score"] > 0
    assert payload["cardio_score"] > 0
    assert "dual_load" in payload

    res_tbl = runner.invoke(cli, ["-u", test_user, "stats", "--period", "28d"])
    assert res_tbl.exit_code == 0
    assert "Mechanical Impact" in res_tbl.output


def test_trends_json(test_user):
    _seed_user_activities(test_user)
    runner = CliRunner()
    res = runner.invoke(cli, ["-u", test_user, "trends", "--weeks", "4", "--format", "json"])
    assert res.exit_code == 0
    rows = json.loads(res.output)
    assert len(rows) == 4


def test_export_formats(test_user):
    _seed_user_activities(test_user)
    runner = CliRunner()

    for fmt in ("json", "csv", "markdown"):
        res = runner.invoke(cli, ["-u", test_user, "export", "--days", "30", "--format", fmt])
        assert res.exit_code == 0
        assert len(res.output.strip()) > 0


def test_journal_add_and_list(test_user):
    runner = CliRunner()
    res_add = runner.invoke(
        cli,
        ["-u", test_user, "journal", "add", "--rpe", "6", "--soreness", "3", "--mood", "happy", "--notes", "90g carbs/hr"],
    )
    assert res_add.exit_code == 0

    res_list = runner.invoke(cli, ["-u", test_user, "journal", "list"])
    assert res_list.exit_code == 0
    assert "90g carbs/hr" in res_list.output
