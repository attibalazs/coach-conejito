"""Unit tests for Albon Impact, Cardio TRIMP, Uphill Athlete Decoupling, and Dual CTL/ATL/TSB."""
from datetime import date, timedelta
import json

from src.modules.methodology import (
    compute_aerobic_decoupling,
    compute_benzie_biomechanics,
    compute_cardio_score,
    compute_ctl_atl_tsb,
    compute_impact_and_gap,
    compute_monotony_and_strain,
    compute_speed_score,
    mechanical_terrain_factor,
)


def test_downhill_has_higher_mechanical_impact_than_uphill():
    assert mechanical_terrain_factor(-0.10) > mechanical_terrain_factor(0.0)
    assert mechanical_terrain_factor(0.0) > mechanical_terrain_factor(0.10)


def test_impact_and_gap_with_streams_downhill_vs_uphill():
    times = [i * 60 for i in range(30)]
    vel = [3.33] * 30

    downhill_act = {
        "distance_m": 6000,
        "duration_sec": 1800,
        "streams_json": json.dumps({
            "time": times,
            "velocity_smooth": vel,
            "grade_smooth": [-10.0] * 30,
        }),
    }
    uphill_act = {
        "distance_m": 6000,
        "duration_sec": 1800,
        "streams_json": json.dumps({
            "time": times,
            "velocity_smooth": vel,
            "grade_smooth": [10.0] * 30,
        }),
    }

    down_impact, down_gap = compute_impact_and_gap(downhill_act)
    up_impact, up_gap = compute_impact_and_gap(uphill_act)

    assert down_impact > up_impact
    # Uphill GAP should be faster (lower sec/km) than downhill GAP at identical raw velocity
    assert up_gap < down_gap


def test_cardio_score_increases_with_hr_and_duration():
    easy = compute_cardio_score({"duration_sec": 3600, "avg_hr": 130})
    hard = compute_cardio_score({"duration_sec": 3600, "avg_hr": 170})
    assert hard > easy > 0


def test_aerobic_decoupling_detects_cardiac_drift():
    # 40 minutes (2400s), 1 point per minute
    times = [i * 60 for i in range(41)]
    vel = [3.33] * 41
    # HR rises from 135 in first half to 155 in second half -> significant positive drift
    hrs = [135] * 21 + [155] * 20
    grades = [0.0] * 41

    act = {
        "streams_json": json.dumps({
            "time": times,
            "velocity_smooth": vel,
            "heartrate": hrs,
            "grade_smooth": grades,
        })
    }
    drift = compute_aerobic_decoupling(act)
    assert drift is not None
    assert drift > 5.0


def test_dual_ctl_atl_tsb_and_monotony():
    today = date(2026, 5, 1)
    loads = {today - timedelta(days=i): 50.0 for i in range(42)}
    res = compute_ctl_atl_tsb(loads, today)
    assert res["ctl"] > 0
    assert res["atl"] > 0

    monotony, strain = compute_monotony_and_strain([50, 0, 60, 0, 70, 0, 100])
    assert monotony is not None and monotony > 0
    assert strain is not None and strain > 0


def test_benzie_biomechanics_extraction_and_unit_normalization():
    act = {
        "cadence": 178.0,
        "avgGroundContactTime": 232.0,
        "avgVerticalOscillation": 76.0,  # mm -> 7.6 cm
        "avgStrideLength": 118.0,  # cm -> 1.18 m
    }
    bio = compute_benzie_biomechanics(act)
    assert bio["cadence_spm"] == 178.0
    assert bio["ground_contact_time_ms"] == 232.0
    assert bio["vertical_oscillation_cm"] == 7.6
    assert bio["stride_length_m"] == 1.18


def test_speed_score_scales_with_gap_pace():
    fast = compute_speed_score({"duration_sec": 1800}, gap_pace_sec=270.0)
    slow = compute_speed_score({"duration_sec": 1800}, gap_pace_sec=360.0)
    assert fast > slow > 0
