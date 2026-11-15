"""Shared formatting utilities for CLI output"""
from datetime import timedelta
from typing import Optional


def format_pace(seconds_per_km: float) -> str:
    """Format pace as MM:SS/km"""
    if seconds_per_km <= 0:
        return "N/A"

    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}/km"


def format_duration(total_seconds: float) -> str:
    """Format duration as HH:MM:SS or MM:SS"""
    if total_seconds <= 0:
        return "0:00"

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes:02d}min"
    else:
        return f"{minutes}min {seconds:02d}s"


def format_distance(meters: float) -> str:
    """Format distance in km"""
    if meters <= 0:
        return "0 km"

    km = meters / 1000
    return f"{km:.1f} km"


def format_elevation(meters: float) -> str:
    """Format elevation gain"""
    return f"{int(meters)} m"


def risk_color(score: float) -> str:
    """Return color name for risk score (0-100)"""
    if score < 30:
        return "green"
    elif score < 60:
        return "yellow"
    else:
        return "red"


def risk_emoji(score: float) -> str:
    """Return emoji for risk level"""
    if score < 30:
        return "✅"
    elif score < 60:
        return "⚠️"
    else:
        return "🚨"


def trend_arrow(change_pct: float) -> str:
    """Return arrow for trend direction"""
    if change_pct > 5:
        return "↗"
    elif change_pct < -5:
        return "↘"
    else:
        return "→"


def format_change(change_pct: float) -> str:
    """Format percentage change with arrow"""
    arrow = trend_arrow(change_pct)
    return f"{arrow} {abs(change_pct):.0f}%"


def format_hr_zone(zone: int) -> str:
    """Format HR zone name"""
    zones = {
        1: "Recovery",
        2: "Aerobic",
        3: "Tempo",
        4: "Threshold",
        5: "VO2 Max"
    }
    return zones.get(zone, "Unknown")


def intensity_emoji(hr: int) -> str:
    """Return emoji for intensity based on HR"""
    if hr < 130:
        return "🟢"  # Easy
    elif hr < 145:
        return "🟡"  # Tempo
    else:
        return "🔴"  # Hard
