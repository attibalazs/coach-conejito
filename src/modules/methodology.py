"""Methodology calculations: Albon (Ascend) Dual-Load Impact/Cardio, SWAP Economy, Uphill Athlete Decoupling, and Dual CTL/ATL/TSB."""
from datetime import date, timedelta
import json
import math
from statistics import mean, stdev
from typing import Any, Dict, List, Optional, Tuple


# Reference flat-ground easy speed (~5:00/km = 3.333 m/s) for normalizing Impact & Cardio scores
REF_SPEED_MPS = 3.333


def minetti_grade_factor(grade: float) -> float:
    """
    Approximate metabolic cost ratio relative to flat running (Minetti et al. 2002 polynomial).
    Clamped to [-0.35, 0.35] to avoid extreme outliers on GPS spikes.
    Returns multiplier > 1.0 for uphill and < 1.0 for gentle downhill.
    """
    g = max(-0.35, min(0.35, grade))
    cost = 155.4 * g**5 - 30.4 * g**4 - 43.3 * g**3 + 46.3 * g**2 + 19.5 * g + 3.6
    return max(0.5, cost / 3.6)


def mechanical_terrain_factor(grade: float) -> float:
    """
    Albon/Ascend-inspired biomechanical impact multiplier by gradient.
    - Uphills reduce ground-impact shock (lower eccentric load).
    - Downhills amplify musculoskeletal/eccentric pounding.
    """
    g = max(-0.35, min(0.35, grade))
    if g < 0:
        # Downhill: eccentric shock scales up sharply with negative grade
        return 1.0 + 4.5 * abs(g)
    # Uphill: lower impact shock, floored at 0.55
    return max(0.55, 1.0 - 1.5 * g)


def _parse_streams(activity: Dict[str, Any]) -> Optional[Dict[str, List[float]]]:
    """Extract stream arrays from an activity dict if present."""
    raw = activity.get("streams_json")
    if not raw:
        return None
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None
    if not isinstance(raw, dict):
        return None

    parsed: Dict[str, List[float]] = {}
    for key in ("time", "distance", "altitude", "heartrate", "grade_smooth", "velocity_smooth"):
        val = raw.get(key)
        if isinstance(val, dict) and isinstance(val.get("data"), list):
            parsed[key] = val["data"]
        elif isinstance(val, list):
            parsed[key] = val
    return parsed if parsed else None


def compute_impact_and_gap(activity: Dict[str, Any]) -> Tuple[float, Optional[float]]:
    """
    Compute Albon-style Running Impact Score (mechanical load, HR-independent)
    and Grade-Adjusted Pace (sec/km).

    Uses time-series streams when available; falls back to summary elevation gain/loss.
    """
    distance_m = float(activity.get("distance_m") or activity.get("distance") or 0.0)
    duration_sec = float(activity.get("duration_sec") or activity.get("duration") or 0.0)
    if distance_m <= 0 or duration_sec <= 0:
        return 0.0, None

    streams = _parse_streams(activity)
    if streams and "time" in streams and ("velocity_smooth" in streams or "distance" in streams):
        times = streams["time"]
        grades = streams.get("grade_smooth")
        velocities = streams.get("velocity_smooth")
        distances = streams.get("distance")

        n = len(times)
        if n >= 4:
            total_impact = 0.0
            total_gap_dist = 0.0
            total_dt = 0.0

            for i in range(1, n):
                dt = max(0.0, float(times[i]) - float(times[i - 1]))
                if dt <= 0 or dt > 300:
                    continue

                if velocities and i < len(velocities):
                    v = max(0.0, float(velocities[i]))
                elif distances and i < len(distances):
                    v = max(0.0, (float(distances[i]) - float(distances[i - 1])) / dt)
                else:
                    v = distance_m / duration_sec

                if v < 0.5:  # standing/stopped
                    continue

                g = (float(grades[i]) / 100.0) if (grades and i < len(grades)) else 0.0
                gap_v = v * math.sqrt(minetti_grade_factor(g))
                # Mechanical shock scales with actual ground speed & downhill/uphill terrain factor
                speed_ratio = v / REF_SPEED_MPS
                terrain_mult = mechanical_terrain_factor(g)

                total_impact += (dt / 60.0) * (speed_ratio ** 1.15) * terrain_mult
                total_gap_dist += gap_v * dt
                total_dt += dt

            if total_dt > 0 and total_gap_dist > 0:
                avg_gap_speed = total_gap_dist / total_dt
                gap_pace_sec = 1000.0 / avg_gap_speed
                return round(total_impact, 2), round(gap_pace_sec, 1)

    # Summary-level fallback using elevation_gain_m and elevation_loss_m
    elev_gain = float(activity.get("elevation_gain_m") or activity.get("elevationGain") or 0.0)
    elev_loss = float(activity.get("elevation_loss_m") or activity.get("elevationLoss") or elev_gain)
    avg_speed = distance_m / duration_sec

    up_grade = elev_gain / max(distance_m * 0.5, 1.0)
    down_grade = -(elev_loss / max(distance_m * 0.5, 1.0))

    # Weighted terrain impact across uphill half + downhill half
    terrain_mult = 0.5 * mechanical_terrain_factor(up_grade) + 0.5 * mechanical_terrain_factor(down_grade)
    gap_factor = 0.5 * math.sqrt(minetti_grade_factor(up_grade)) + 0.5 * math.sqrt(minetti_grade_factor(down_grade))
    gap_speed = avg_speed * gap_factor
    gap_pace_sec = (1000.0 / gap_speed) if gap_speed > 0 else None

    impact = (duration_sec / 60.0) * ((avg_speed / REF_SPEED_MPS) ** 1.15) * terrain_mult
    return round(impact, 2), round(gap_pace_sec, 1) if gap_pace_sec else None


def compute_cardio_score(
    activity: Dict[str, Any],
    resting_hr: float = 55.0,
    max_hr: float = 190.0,
) -> float:
    """
    Compute Banister TRIMP-based Cardio Score (purely HR + duration).
    """
    duration_min = float(activity.get("duration_sec") or activity.get("duration") or 0.0) / 60.0
    avg_hr = activity.get("avg_hr") or activity.get("averageHR")
    if duration_min <= 0 or not avg_hr:
        return 0.0

    hr_reserve_denom = max(max_hr - resting_hr, 40.0)
    hrr = max(0.0, min(1.2, (float(avg_hr) - resting_hr) / hr_reserve_denom))
    # Banister male/general exponential weighting
    trimp = duration_min * hrr * 0.64 * math.exp(1.92 * hrr)
    return round(trimp, 2)


def compute_speed_score(
    activity: Dict[str, Any],
    gap_pace_sec: Optional[float] = None,
    threshold_pace_sec: float = 270.0,
) -> float:
    """
    Ascend/Albon 3rd pillar: Speed Score based on GAP output relative to threshold pace
    (default threshold: 4:30/km = 270 s/km).
    """
    duration_min = float(activity.get("duration_sec") or activity.get("duration") or 0.0) / 60.0
    if duration_min <= 0:
        return 0.0
    if gap_pace_sec is None:
        _, gap_pace_sec = compute_impact_and_gap(activity)
    if not gap_pace_sec or gap_pace_sec <= 0:
        return 0.0

    intensity_factor = min(1.5, threshold_pace_sec / float(gap_pace_sec))
    return round(duration_min * (intensity_factor ** 2), 2)


def compute_aerobic_decoupling(activity: Dict[str, Any]) -> Optional[float]:
    """
    Uphill Athlete (Johnston/House) Aerobic Decoupling (Pa:HR drift %).
    Compares first-half vs second-half GAP-speed / HR efficiency.
    Returns percentage drift (e.g. 3.4 means 3.4% drift; <5% indicates strong aerobic base).
    """
    streams = _parse_streams(activity)
    if not streams:
        return None
    times = streams.get("time")
    hrs = streams.get("heartrate")
    velocities = streams.get("velocity_smooth")
    grades = streams.get("grade_smooth")
    if not (times and hrs and velocities):
        return None

    n = min(len(times), len(hrs), len(velocities))
    if n < 20 or times[n - 1] < 1200:  # Require at least 20 minutes
        return None

    # Skip first 5 minutes (300s) warmup if run is >= 25 min
    start_t = 300.0 if times[n - 1] >= 1500 else 0.0
    mid_t = start_t + (times[n - 1] - start_t) / 2.0

    half1_eff: List[float] = []
    half2_eff: List[float] = []

    for i in range(n):
        t = float(times[i])
        if t < start_t:
            continue
        hr = float(hrs[i])
        v = float(velocities[i])
        if hr < 80 or v < 1.0:
            continue
        g = (float(grades[i]) / 100.0) if (grades and i < len(grades)) else 0.0
        gap_v = v * math.sqrt(minetti_grade_factor(g))
        eff = gap_v / hr
        if t <= mid_t:
            half1_eff.append(eff)
        else:
            half2_eff.append(eff)

    if len(half1_eff) < 5 or len(half2_eff) < 5:
        return None

    e1 = mean(half1_eff)
    e2 = mean(half2_eff)
    if e1 <= 0:
        return None
    decoupling = ((e1 - e2) / e1) * 100.0
    return round(decoupling, 2)


def compute_ctl_atl_tsb(
    daily_loads: Dict[date, float],
    as_of: date,
    ctl_days: int = 42,
    atl_days: int = 7,
) -> Dict[str, float]:
    """
    Compute Coggan/Banister CTL (Fitness), ATL (Fatigue), and TSB (Form) as of `as_of`.
    """
    if not daily_loads:
        return {"ctl": 0.0, "atl": 0.0, "tsb": 0.0}

    start = min(min(daily_loads.keys()), as_of - timedelta(days=ctl_days * 2))
    ctl = 0.0
    atl = 0.0
    ctl_alpha = 2.0 / (ctl_days + 1)
    atl_alpha = 2.0 / (atl_days + 1)

    cur = start
    while cur <= as_of:
        load = daily_loads.get(cur, 0.0)
        ctl = ctl + ctl_alpha * (load - ctl)
        atl = atl + atl_alpha * (load - atl)
        cur += timedelta(days=1)

    return {
        "ctl": round(ctl, 2),
        "atl": round(atl, 2),
        "tsb": round(ctl - atl, 2),
    }


def compute_monotony_and_strain(daily_loads_7d: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Foster's Training Monotony (mean / stdev over 7 days) and Strain (weekly_load * monotony).
    """
    if len(daily_loads_7d) < 7:
        return None, None
    total = sum(daily_loads_7d)
    if total == 0:
        return 0.0, 0.0
    avg = mean(daily_loads_7d)
    sd = stdev(daily_loads_7d)
    if sd == 0:
        return None, None
    monotony = avg / sd
    strain = total * monotony
    return round(monotony, 2), round(strain, 1)


def compute_benzie_biomechanics(activity: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extract Shane Benzie (Running Reborn) biomechanical metrics from an activity:
    - cadence_spm (target: 175-185 spm)
    - ground_contact_time_ms (crisp elastic recoil: <240 ms)
    - vertical_oscillation_cm (target: ~7.5 cm)
    - stride_length_m
    """
    cadence = activity.get("cadence") or activity.get("averageRunningCadenceInStepsPerMinute")
    gct = activity.get("avgGroundContactTime") or activity.get("ground_contact_time_ms")
    vo = activity.get("avgVerticalOscillation") or activity.get("vertical_oscillation_cm")
    stride = activity.get("avgStrideLength") or activity.get("stride_length_m")

    vo_cm: Optional[float] = None
    if vo is not None:
        vo_val = float(vo)
        # Garmin sometimes reports in mm (>30) vs cm
        vo_cm = round(vo_val / 10.0 if vo_val > 30.0 else vo_val, 2)

    stride_m: Optional[float] = None
    if stride is not None:
        st_val = float(stride)
        # Garmin reports avgStrideLength in cm (>10) vs meters
        stride_m = round(st_val / 100.0 if st_val > 10.0 else st_val, 2)

    return {
        "cadence_spm": round(float(cadence), 1) if cadence is not None else None,
        "ground_contact_time_ms": round(float(gct), 1) if gct is not None else None,
        "vertical_oscillation_cm": vo_cm,
        "stride_length_m": stride_m,
    }
