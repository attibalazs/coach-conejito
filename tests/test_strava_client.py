"""Unit tests for StravaClient, OAuth2 token refresh, and cross-source deduplication."""
import json
import os
import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.modules.repositories import ActivityRepository, get_repository
from src.modules.strava_client import (
    StravaAuthError,
    StravaClient,
    StravaRateLimitError,
    exchange_code_for_token,
    get_authorization_url,
    is_strava_authenticated,
    save_strava_tokens,
)


def test_authorization_url():
    url = get_authorization_url("12345")
    assert "client_id=12345" in url
    assert "activity%3Aread_all" in url


def test_exchange_code_for_token(test_user):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "acc_1",
        "refresh_token": "ref_1",
        "expires_at": int(time.time()) + 3600,
        "athlete": {"id": 99},
    }

    with patch("src.modules.strava_client.requests.post", return_value=mock_resp):
        tokens = exchange_code_for_token(test_user, "cid", "csec", "auth_code")

    assert tokens["access_token"] == "acc_1"
    assert is_strava_authenticated(test_user) is True


def test_auto_refresh_expired_token(test_user):
    save_strava_tokens(test_user, {
        "client_id": "cid",
        "client_secret": "csec",
        "access_token": "old_acc",
        "refresh_token": "ref_1",
        "expires_at": int(time.time()) - 100,  # expired
    })

    refresh_resp = MagicMock()
    refresh_resp.status_code = 200
    refresh_resp.json.return_value = {
        "access_token": "new_acc",
        "refresh_token": "ref_2",
        "expires_at": int(time.time()) + 3600,
    }

    activities_resp = MagicMock()
    activities_resp.status_code = 200
    activities_resp.json.return_value = []

    with patch("src.modules.strava_client.requests.post", return_value=refresh_resp) as mock_post, \
         patch("src.modules.strava_client.requests.get", return_value=activities_resp):
        client = StravaClient(test_user)
        res = client.fetch_activities(days=7)

    assert res == []
    assert mock_post.called
    assert client.tokens["access_token"] == "new_acc"


def test_rate_limit_raises(test_user):
    save_strava_tokens(test_user, {
        "client_id": "cid",
        "client_secret": "csec",
        "access_token": "valid_acc",
        "refresh_token": "ref_1",
        "expires_at": int(time.time()) + 3600,
    })

    rate_resp = MagicMock()
    rate_resp.status_code = 429

    with patch("src.modules.strava_client.requests.get", return_value=rate_resp):
        client = StravaClient(test_user)
        with pytest.raises(StravaRateLimitError):
            client.fetch_activities(days=7)


def test_sync_deduplicates_against_garmin_and_attaches_streams(test_user):
    # Pre-seed a Garmin activity in SQLite
    act_repo, j_repo, cache = get_repository(test_user)
    act_repo.save({
        "activityId": 9001,
        "startTimeLocal": "2026-02-01 08:00:00",
        "startTimeGMT": "2026-02-01T08:00:00Z",
        "activityType": {"typeKey": "running"},
        "activityName": "Morning Trail",
        "distance": 10000.0,
        "duration": 3600,
        "averageHR": 142,
    }, source="garmin")
    act_repo.close()
    j_repo.close()
    cache.close()

    save_strava_tokens(test_user, {
        "client_id": "cid",
        "client_secret": "csec",
        "access_token": "valid_acc",
        "refresh_token": "ref_1",
        "expires_at": int(time.time()) + 3600,
    })

    strava_acts = [{
        "id": 55501,
        "name": "Morning Trail",
        "type": "Run",
        "start_date": "2026-02-01T08:00:30Z",
        "start_date_local": "2026-02-01T08:00:30Z",
        "distance": 10050.0,  # within 2%
        "moving_time": 3590,
        "total_elevation_gain": 320.0,
        "average_heartrate": 142.0,
    }]
    strava_streams = {
        "time": {"data": [0, 60, 120]},
        "velocity_smooth": {"data": [3.0, 3.1, 3.2]},
        "grade_smooth": {"data": [0.0, 5.0, -4.0]},
    }

    def fake_get(url, headers=None, params=None, timeout=30):
        resp = MagicMock()
        resp.status_code = 200
        if "/streams" in url:
            resp.json.return_value = strava_streams
        else:
            resp.json.return_value = strava_acts
        return resp

    with patch("src.modules.strava_client.requests.get", side_effect=fake_get):
        client = StravaClient(test_user)
        summary = client.sync_activities(days=30, force=True, include_streams=True)

    assert summary["deduplicated"] == 1
    assert summary["synced"] == 0
    assert summary["streams_fetched"] == 1

    act_repo, j_repo, cache = get_repository(test_user)
    try:
        garmin_act = act_repo.get_by_id("9001")
        strava_dup = act_repo.get_by_id("strava_55501")
        assert garmin_act is not None
        assert strava_dup is None
        assert garmin_act["streams_json"] is not None
    finally:
        act_repo.close()
        j_repo.close()
        cache.close()
