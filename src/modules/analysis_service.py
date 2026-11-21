"""
Analysis service for Coach Conejito.

This module provides programmatic analysis capabilities including:
- Injury risk detection (ACWR, volume spikes, cadence analysis)
- Performance tracking (pace trends, VO2max, efficiency)
- Fatigue index calculation
- Activity metrics computation
"""

from dataclasses import dataclass, field
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Tuple
from statistics import mean, stdev
import math

from src.modules.repositories import ActivityRepository, JournalRepository, MetricsCache


@dataclass
class ActivityMetrics:
    """Computed metrics for a single activity."""
    activity_id: str
    date: date
    distance_km: float
    duration_min: float
    pace_per_km_sec: Optional[float]  # seconds per km
    avg_hr: Optional[int]
    cadence: Optional[float]
    elevation_m: float
    training_effect: Optional[float]
    vo2_max: Optional[int]
    hr_zones: Dict[int, float] = field(default_factory=dict)  # Zone -> minutes
    efficiency_score: Optional[float] = None  # Pace/HR * 1000
    activity_type: Optional[str] = None

    @property
    def pace_per_km(self) -> timedelta:
        """Get pace as timedelta for formatting."""
        if self.pace_per_km_sec:
            return timedelta(seconds=self.pace_per_km_sec)
        return timedelta(seconds=0)


@dataclass
class WeeklyMetrics:
    """Aggregated weekly metrics."""
    week_start: date
    total_distance_km: float
    total_duration_min: float
    session_count: int
    longest_run_km: float
    avg_hr: Optional[float]
    avg_cadence: Optional[float]
    acwr: Optional[float]  # Acute:Chronic Workload Ratio
    fatigue_index: Optional[float]  # 0-100
    injury_risk_score: Optional[float]  # 0-100
    intensity_distribution: Dict[str, int] = field(default_factory=dict)  # easy/tempo/hard
    vo2_max: Optional[int] = None
    week_over_week_change: Optional[float] = None  # Percentage change from previous week


@dataclass
class InjuryRiskAnalysis:
    """Injury risk assessment."""
    overall_risk: str  # low/medium/high
    risk_score: float  # 0-100
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    soreness_trend: Optional[str] = None  # rising/stable/falling
    acwr: Optional[float] = None
    volume_change_pct: Optional[float] = None
    avg_cadence: Optional[float] = None
    risk_breakdown: Dict[str, float] = field(default_factory=dict)  # Individual risk scores


class AnalysisService:
    """
    Core analysis service for running metrics and injury risk.
    """

    # HR zone thresholds (as percentage of max HR or absolute values)
    ZONE_1_MAX = 130  # Recovery/easy
    ZONE_2_MAX = 140  # Aerobic
    ZONE_3_MAX = 160  # Tempo
    # ZONE_4_MAX = 175  # Threshold
    # ZONE_5_MAX = 185  # VO2 Max

    # Injury risk thresholds
    ACWR_SAFE_MIN = 0.8
    ACWR_SAFE_MAX = 1.3
    ACWR_RISKY = 1.5
    MIN_CADENCE_TARGET = 170
    MIN_CADENCE_CRITICAL = 160

    def __init__(
        self,
        activity_repo: ActivityRepository,
        journal_repo: JournalRepository,
        metrics_cache: Optional[MetricsCache] = None
    ):
        """
        Initialize the analysis service.

        Args:
            activity_repo: Repository for activity data
            journal_repo: Repository for journal entries
            metrics_cache: Optional cache for computed metrics
        """
        self.activity_repo = activity_repo
        self.journal_repo = journal_repo
        self.metrics_cache = metrics_cache

    def get_activity_metrics(self, activity_id: str) -> Optional[ActivityMetrics]:
        """
        Calculate all metrics for a single activity.

        Args:
            activity_id: Activity identifier

        Returns:
            ActivityMetrics or None if activity not found
        """
        activity = self.activity_repo.get_by_id(activity_id)
        if not activity:
            return None

        # Extract basic data
        distance_m = activity.get('distance_m') or activity.get('distance', 0)
        duration_sec = activity.get('duration_sec') or activity.get('duration', 0)
        distance_km = distance_m / 1000 if distance_m else 0
        duration_min = duration_sec / 60 if duration_sec else 0

        # Calculate pace (seconds per km)
        pace_per_km_sec = None
        if distance_km > 0 and duration_sec > 0:
            pace_per_km_sec = duration_sec / distance_km

        # Calculate efficiency score (lower = better)
        efficiency_score = None
        avg_hr = activity.get('avg_hr') or activity.get('averageHR')
        if pace_per_km_sec and avg_hr:
            efficiency_score = (pace_per_km_sec / avg_hr) * 1000

        # Extract HR zones (time in seconds -> convert to minutes)
        hr_zones = {}
        for i in range(1, 6):
            zone_time = activity.get(f'hrTimeInZone_{i}', 0)
            if zone_time:
                hr_zones[i] = zone_time / 60  # Convert to minutes

        # Parse date
        activity_date = activity.get('date')
        if isinstance(activity_date, str):
            activity_date = datetime.fromisoformat(activity_date).date()

        return ActivityMetrics(
            activity_id=activity_id,
            date=activity_date,
            distance_km=distance_km,
            duration_min=duration_min,
            pace_per_km_sec=pace_per_km_sec,
            avg_hr=avg_hr,
            cadence=activity.get('cadence') or activity.get('averageRunningCadenceInStepsPerMinute'),
            elevation_m=(activity.get('elevation_gain_m') or activity.get('elevationGain', 0)),
            training_effect=(activity.get('aerobic_training_effect') or activity.get('aerobicTrainingEffect')),
            vo2_max=(activity.get('vo2_max') or activity.get('vO2MaxValue')),
            hr_zones=hr_zones,
            efficiency_score=efficiency_score,
            activity_type=(activity.get('activity_type') or activity.get('activityType', {}).get('typeKey') if isinstance(activity.get('activityType'), dict) else None)
        )

    def get_weekly_metrics(self, week_start: date, use_cache: bool = True) -> WeeklyMetrics:
        """
        Calculate aggregated metrics for a specific week.

        Args:
            week_start: Start date of the week (should be Monday)
            use_cache: Whether to use cached metrics if available

        Returns:
            WeeklyMetrics for the week
        """
        # Check cache first
        if use_cache and self.metrics_cache:
            cached = self.metrics_cache.get_weekly_metrics(week_start)
            if cached:
                return WeeklyMetrics(
                    week_start=week_start,
                    total_distance_km=cached['total_distance_km'] or 0,
                    total_duration_min=cached['total_duration_min'] or 0,
                    session_count=cached['session_count'] or 0,
                    longest_run_km=cached['longest_run_km'] or 0,
                    avg_hr=cached['avg_hr'],
                    avg_cadence=cached['avg_cadence'],
                    acwr=cached['acwr'],
                    fatigue_index=cached['fatigue_index'],
                    injury_risk_score=cached['injury_risk_score'],
                    intensity_distribution={
                        'easy': cached['easy_runs'] or 0,
                        'tempo': cached['tempo_runs'] or 0,
                        'hard': cached['hard_runs'] or 0
                    }
                )

        # Calculate from scratch
        week_end = week_start + timedelta(days=6)
        activities = self.activity_repo.get_range(week_start, week_end, activity_type='running')

        if not activities:
            return WeeklyMetrics(
                week_start=week_start,
                total_distance_km=0,
                total_duration_min=0,
                session_count=0,
                longest_run_km=0,
                avg_hr=None,
                avg_cadence=None,
                acwr=None,
                fatigue_index=None,
                injury_risk_score=None,
                intensity_distribution={'easy': 0, 'tempo': 0, 'hard': 0}
            )

        # Aggregate metrics
        total_distance = sum(a.get('distance_m', 0) for a in activities) / 1000
        total_duration = sum(a.get('duration_sec', 0) for a in activities) / 60
        longest_run = max((a.get('distance_m', 0) for a in activities), default=0) / 1000

        # Average HR and cadence (only for activities with data)
        hrs = [a.get('avg_hr') or a.get('averageHR') for a in activities if a.get('avg_hr') or a.get('averageHR')]
        avg_hr = mean(hrs) if hrs else None

        cadences = [
            a.get('cadence') or a.get('averageRunningCadenceInStepsPerMinute')
            for a in activities
            if a.get('cadence') or a.get('averageRunningCadenceInStepsPerMinute')
        ]
        avg_cadence = mean(cadences) if cadences else None

        # Intensity distribution
        easy_runs = sum(1 for a in activities if (a.get('avg_hr') or a.get('averageHR') or 999) < self.ZONE_1_MAX)
        tempo_runs = sum(1 for a in activities if self.ZONE_1_MAX <= (a.get('avg_hr') or a.get('averageHR') or 0) < self.ZONE_3_MAX)
        hard_runs = sum(1 for a in activities if (a.get('avg_hr') or a.get('averageHR') or 0) >= self.ZONE_3_MAX)

        # Calculate ACWR, fatigue, injury risk
        acwr = self.get_acwr(week_end)
        fatigue_index = self.get_fatigue_index(week_end)
        injury_risk = self.get_injury_risk(week_end)

        metrics = WeeklyMetrics(
            week_start=week_start,
            total_distance_km=total_distance,
            total_duration_min=total_duration,
            session_count=len(activities),
            longest_run_km=longest_run,
            avg_hr=avg_hr,
            avg_cadence=avg_cadence,
            acwr=acwr,
            fatigue_index=fatigue_index,
            injury_risk_score=injury_risk.risk_score if injury_risk else None,
            intensity_distribution={'easy': easy_runs, 'tempo': tempo_runs, 'hard': hard_runs}
        )

        # Cache the results
        if self.metrics_cache:
            self.metrics_cache.save_weekly_metrics({
                'week_start': week_start,
                'total_distance_km': metrics.total_distance_km,
                'total_duration_min': metrics.total_duration_min,
                'session_count': metrics.session_count,
                'longest_run_km': metrics.longest_run_km,
                'avg_hr': metrics.avg_hr,
                'avg_cadence': metrics.avg_cadence,
                'acwr': metrics.acwr,
                'fatigue_index': metrics.fatigue_index,
                'injury_risk_score': metrics.injury_risk_score,
                'easy_runs': easy_runs,
                'tempo_runs': tempo_runs,
                'hard_runs': hard_runs
            })

        return metrics

    def get_acwr(self, reference_date: date) -> Optional[float]:
        """
        Calculate Acute:Chronic Workload Ratio.

        ACWR = (Last 7 days volume) / (Last 28 days average weekly volume)

        Safe zone: 0.8-1.3
        Risky: >1.5

        Args:
            reference_date: Date to calculate ACWR for

        Returns:
            ACWR value or None if insufficient data
        """
        # Acute load: last 7 days
        acute_start = reference_date - timedelta(days=6)
        acute_activities = self.activity_repo.get_range(acute_start, reference_date, activity_type='running')
        acute_load = sum(a.get('distance_m', 0) for a in acute_activities) / 1000

        # Chronic load: last 28 days (4 weeks average)
        chronic_start = reference_date - timedelta(days=27)
        chronic_activities = self.activity_repo.get_range(chronic_start, reference_date, activity_type='running')

        if len(chronic_activities) < 7:  # Need at least some data
            return None

        chronic_load = sum(a.get('distance_m', 0) for a in chronic_activities) / 1000
        chronic_weekly_avg = chronic_load / 4

        if chronic_weekly_avg == 0:
            return None

        acwr = acute_load / chronic_weekly_avg
        return round(acwr, 2)

    def get_fatigue_index(self, reference_date: date) -> Optional[float]:
        """
        Calculate fatigue index (0-100).

        Composite score based on:
        - Soreness trend (30%)
        - ACWR load (30%)
        - RPE deviation (20%)
        - HR consistency (20%)

        Args:
            reference_date: Date to calculate fatigue for

        Returns:
            Fatigue index 0-100 (0=fresh, 100=exhausted) or None
        """
        # Get last 7 days of journals
        week_start = reference_date - timedelta(days=6)
        journals = self.journal_repo.get_range(week_start, reference_date)

        if not journals:
            return None

        # Soreness score (0-100)
        soreness_values = [j.get('soreness', 0) for j in journals if j.get('soreness') is not None]
        soreness_score = (mean(soreness_values) / 10 * 100) if soreness_values else 0

        # ACWR fatigue
        acwr = self.get_acwr(reference_date)
        acwr_fatigue = 0
        if acwr and acwr > 1.3:
            acwr_fatigue = min((acwr - 1.0) * 100, 100)

        # RPE deviation (simplified - just use average RPE)
        rpe_values = [j.get('rpe', 0) for j in journals if j.get('rpe') is not None]
        rpe_score = (mean(rpe_values) / 10 * 100) if rpe_values else 0

        # Weighted composite
        fatigue = (
            soreness_score * 0.30 +
            acwr_fatigue * 0.30 +
            rpe_score * 0.20 +
            0 * 0.20  # HR drift placeholder
        )

        return round(min(fatigue, 100), 1)

    def get_injury_risk(self, reference_date: date) -> Optional[InjuryRiskAnalysis]:
        """
        Assess current injury risk based on multiple factors.

        Risk score calculation (0-100):
        - Volume spike (40%)
        - Low cadence (30%)
        - Rising soreness (20%)
        - ACWR deviation (10%)

        Args:
            reference_date: Date to assess risk for

        Returns:
            InjuryRiskAnalysis or None if insufficient data
        """
        risk_factors = []
        recommendations = []

        # 1. ACWR / Volume spike (40% weight)
        acwr = self.get_acwr(reference_date)
        volume_spike_score = 0

        if acwr is None:
            return None  # Need enough data

        if acwr > self.ACWR_RISKY:
            volume_spike_score = 100
            risk_factors.append(f"High volume spike: ACWR {acwr:.2f} (safe: {self.ACWR_SAFE_MIN}-{self.ACWR_SAFE_MAX})")
            recommendations.append(f"Reduce volume by 15-20% next week (target ACWR: 1.0-1.2)")
        elif acwr > self.ACWR_SAFE_MAX:
            volume_spike_score = 50 + 50 * ((acwr - self.ACWR_SAFE_MAX) / (self.ACWR_RISKY - self.ACWR_SAFE_MAX))
            risk_factors.append(f"Moderate volume increase: ACWR {acwr:.2f} (safe: {self.ACWR_SAFE_MIN}-{self.ACWR_SAFE_MAX})")
            recommendations.append(f"Monitor closely, consider easier week ahead")
        elif acwr < self.ACWR_SAFE_MIN:
            volume_spike_score = 20
            risk_factors.append(f"Low training load: ACWR {acwr:.2f} (may indicate detraining)")

        # 2. Cadence analysis (30% weight)
        week_start = reference_date - timedelta(days=6)
        recent_runs = self.activity_repo.get_range(week_start, reference_date, activity_type='running')

        cadences = [
            a.get('cadence') or a.get('averageRunningCadenceInStepsPerMinute')
            for a in recent_runs
            if a.get('cadence') or a.get('averageRunningCadenceInStepsPerMinute')
        ]

        cadence_score = 0
        avg_cadence = None
        if cadences:
            avg_cadence = mean(cadences)
            if avg_cadence < self.MIN_CADENCE_CRITICAL:
                cadence_score = 100
                risk_factors.append(f"Very low cadence: {avg_cadence:.0f} spm (target: {self.MIN_CADENCE_TARGET}+)")
                recommendations.append(f"Use metronome at {self.MIN_CADENCE_TARGET} BPM on all runs")
            elif avg_cadence < self.MIN_CADENCE_TARGET:
                cadence_score = 50 + 50 * ((self.MIN_CADENCE_TARGET - avg_cadence) / 10)
                risk_factors.append(f"Low cadence: {avg_cadence:.0f} spm (target: {self.MIN_CADENCE_TARGET}+)")
                recommendations.append(f"Focus on increasing cadence to {self.MIN_CADENCE_TARGET}+ spm")

        # 3. Soreness trend (20% weight)
        journals = self.journal_repo.get_range(week_start, reference_date)
        soreness_values = [j.get('soreness', 0) for j in journals if j.get('soreness') is not None]

        soreness_score = 0
        soreness_trend = "unknown"
        if len(soreness_values) >= 3:
            # Check for rising trend (simple: compare first half vs second half)
            mid = len(soreness_values) // 2
            first_half_avg = mean(soreness_values[:mid])
            second_half_avg = mean(soreness_values[mid:])

            if second_half_avg > first_half_avg + 1:
                soreness_trend = "rising"
                soreness_score = 80
                risk_factors.append(f"Rising soreness trend over last {len(soreness_values)} days")
                recommendations.append("Add recovery days, ice and stretch after runs")
            elif any(s >= 7 for s in soreness_values):
                soreness_trend = "high"
                soreness_score = 100
                risk_factors.append(f"High soreness levels (max: {max(soreness_values)}/10)")
                recommendations.append("Consider rest day or very light activity")
            elif mean(soreness_values) > 5:
                soreness_trend = "elevated"
                soreness_score = 60
                risk_factors.append(f"Elevated soreness (avg: {mean(soreness_values):.1f}/10)")
            else:
                soreness_trend = "stable"
                soreness_score = 20 * mean(soreness_values) / 5

        # 4. ACWR deviation (10% weight)
        acwr_deviation = abs(acwr - 1.0) * 100 if acwr else 0

        # Calculate overall risk score
        risk_score = (
            volume_spike_score * 0.40 +
            cadence_score * 0.30 +
            soreness_score * 0.20 +
            acwr_deviation * 0.10
        )
        risk_score = min(risk_score, 100)

        # Determine risk level
        if risk_score < 30:
            overall_risk = "low"
        elif risk_score < 60:
            overall_risk = "moderate"
        else:
            overall_risk = "high"

        # Calculate volume change
        volume_change_pct = None
        if acwr:
            volume_change_pct = (acwr - 1.0) * 100

        return InjuryRiskAnalysis(
            overall_risk=overall_risk,
            risk_score=round(risk_score, 1),
            risk_factors=risk_factors,
            recommendations=recommendations,
            soreness_trend=soreness_trend,
            acwr=acwr,
            volume_change_pct=volume_change_pct,
            avg_cadence=avg_cadence,
            risk_breakdown={
                'volume_spike': round(volume_spike_score, 1),
                'low_cadence': round(cadence_score, 1),
                'rising_soreness': round(soreness_score, 1),
                'acwr_deviation': round(acwr_deviation, 1)
            }
        )

    def get_weekly_summary(self, reference_date: date) -> Dict:
        """
        Get a comprehensive weekly summary including metrics and risk analysis.

        Args:
            reference_date: Date within the week to analyze

        Returns:
            Dictionary with weekly metrics, injury risk, and alerts
        """
        # Calculate week start (Monday)
        week_start = reference_date - timedelta(days=reference_date.weekday())

        metrics = self.get_weekly_metrics(week_start)
        risk = self.get_injury_risk(reference_date)

        # Calculate week-over-week change
        prev_week_start = week_start - timedelta(days=7)
        try:
            prev_metrics = self.get_weekly_metrics(prev_week_start)
            if prev_metrics.total_distance_km > 0:
                change_pct = ((metrics.total_distance_km - prev_metrics.total_distance_km) / prev_metrics.total_distance_km) * 100
                metrics.week_over_week_change = round(change_pct, 1)
        except Exception:
            pass

        # Get week activities for intensity distribution with distances
        week_end = week_start + timedelta(days=6)
        activities = self.activity_repo.get_range(week_start, week_end, activity_type='running')

        # Calculate distances for each intensity level
        easy_km = sum((a.get('distance_m', 0) / 1000) for a in activities if (a.get('avg_hr') or a.get('averageHR') or 999) < self.ZONE_1_MAX)
        tempo_km = sum((a.get('distance_m', 0) / 1000) for a in activities if self.ZONE_1_MAX <= (a.get('avg_hr') or a.get('averageHR') or 0) < self.ZONE_3_MAX)
        hard_km = sum((a.get('distance_m', 0) / 1000) for a in activities if (a.get('avg_hr') or a.get('averageHR') or 0) >= self.ZONE_3_MAX)

        # Update intensity distribution with both counts and distances
        metrics.intensity_distribution.update({
            'easy_km': easy_km,
            'tempo_km': tempo_km,
            'hard_km': hard_km,
            'easy_count': metrics.intensity_distribution.get('easy', 0),
            'tempo_count': metrics.intensity_distribution.get('tempo', 0),
            'hard_count': metrics.intensity_distribution.get('hard', 0)
        })

        # Generate alerts
        alerts = []
        if metrics.avg_cadence and metrics.avg_cadence < self.MIN_CADENCE_TARGET:
            alerts.append({
                'level': 'warning',
                'message': f"Cadence below target: {metrics.avg_cadence:.0f} avg (target: {self.MIN_CADENCE_TARGET}+)",
                'recommendation': f"Use metronome at {self.MIN_CADENCE_TARGET} BPM on next run"
            })

        if risk and risk.overall_risk in ['moderate', 'high']:
            alerts.append({
                'level': 'warning' if risk.overall_risk == 'moderate' else 'critical',
                'message': f"Injury risk {risk.overall_risk}: {risk.risk_score:.0f}/100",
                'recommendation': risk.recommendations[0] if risk.recommendations else "Monitor closely"
            })

        return {
            'week_start': week_start,
            'week_end': week_start + timedelta(days=6),
            'metrics': metrics,
            'injury_risk': risk,
            'alerts': alerts,
            'activities': activities
        }

    def detect_trends(self, metric_name: str, weeks: int = 8) -> Dict:
        """
        Detect trend for a specific metric over time.

        Args:
            metric_name: Metric to analyze (distance, pace, hr, cadence, vo2_max)
            weeks: Number of weeks to analyze

        Returns:
            Dictionary with direction, change_pct, and confidence
        """
        # Get weekly data
        today = date.today()
        weekly_values = []

        for i in range(weeks - 1, -1, -1):
            week_date = today - timedelta(weeks=i)
            week_start = week_date - timedelta(days=week_date.weekday())

            try:
                weekly = self.get_weekly_metrics(week_start)

                if metric_name == 'distance':
                    value = weekly.total_distance_km
                elif metric_name == 'acwr':
                    value = weekly.acwr
                elif metric_name == 'hr':
                    value = weekly.avg_hr
                elif metric_name == 'cadence':
                    value = weekly.avg_cadence
                else:
                    value = None

                if value is not None:
                    weekly_values.append(value)
            except Exception:
                continue

        if len(weekly_values) < 3:
            return {
                'direction': 'unknown',
                'change_pct': 0,
                'confidence': 'low'
            }

        # Simple linear trend detection
        first_half = weekly_values[:len(weekly_values)//2]
        second_half = weekly_values[len(weekly_values)//2:]

        first_avg = mean(first_half)
        second_avg = mean(second_half)

        if first_avg == 0:
            change_pct = 0
        else:
            change_pct = ((second_avg - first_avg) / first_avg) * 100

        # Determine direction
        if change_pct > 5:
            direction = 'improving' if metric_name in ['distance', 'cadence', 'vo2_max'] else 'increasing'
        elif change_pct < -5:
            direction = 'declining' if metric_name in ['distance', 'cadence', 'vo2_max'] else 'decreasing'
        else:
            direction = 'stable'

        # Confidence based on consistency
        confidence = 'high' if len(weekly_values) >= weeks * 0.8 else 'medium'

        return {
            'direction': direction,
            'change_pct': round(change_pct, 1),
            'confidence': confidence
        }

    @staticmethod
    def _is_running_activity(act: Dict) -> bool:
        t = str(act.get("activity_type") or "").lower()
        return "running" in t or t in ("run", "trail_run", "virtual_run", "treadmill_running")

    def _summarize_activities_window(self, activities: List[Dict], start_d: date, end_d: date) -> Dict:
        """
        Compute aggregate running volume, Albon Impact vs Cardio, SWAP polarization,
        and Uphill Athlete decoupling. Non-running activities (cycling, strength, yoga)
        contribute to Cardio (TRIMP) and cross_training counts, not running distance/Impact/cadence.
        """
        from src.modules.methodology import (
            compute_aerobic_decoupling,
            compute_benzie_biomechanics,
            compute_cardio_score,
            compute_impact_and_gap,
            compute_monotony_and_strain,
            compute_speed_score,
        )

        total_dist_km = 0.0
        total_dur_min = 0.0
        total_elev_gain = 0.0
        total_elev_loss = 0.0
        total_impact = 0.0
        total_cardio = 0.0
        total_speed = 0.0
        hrs: List[float] = []
        cadences: List[float] = []
        gcts: List[float] = []
        vert_oscs: List[float] = []
        strides: List[float] = []
        efficiencies: List[float] = []
        decouplings: List[float] = []
        intensity_sec = {"easy": 0.0, "tempo": 0.0, "hard": 0.0}
        daily_impact: Dict[date, float] = {}
        daily_cardio: Dict[date, float] = {}
        running_sessions = 0
        cycling_sessions = 0
        cycling_km = 0.0
        strength_sessions = 0

        for act in activities:
            act_type = str(act.get("activity_type") or "").lower()
            is_run = self._is_running_activity(act)

            cardio = compute_cardio_score(act)
            total_cardio += cardio

            act_date_str = str(act.get("date") or "")[:10]
            try:
                act_d = date.fromisoformat(act_date_str)
                daily_cardio[act_d] = daily_cardio.get(act_d, 0.0) + cardio
            except ValueError:
                act_d = None

            if not is_run:
                if "cycling" in act_type or "biking" in act_type or "ride" in act_type:
                    cycling_sessions += 1
                    cycling_km += (act.get("distance_m") or 0) / 1000.0
                elif "strength" in act_type:
                    strength_sessions += 1
                continue

            running_sessions += 1
            dist_km = (act.get("distance_m") or 0) / 1000.0
            dur_min = (act.get("duration_sec") or 0) / 60.0
            total_dist_km += dist_km
            total_dur_min += dur_min
            total_elev_gain += float(act.get("elevation_gain_m") or 0.0)
            total_elev_loss += float(act.get("elevation_loss_m") or 0.0)

            impact, gap_pace = compute_impact_and_gap(act)
            speed = compute_speed_score(act, gap_pace_sec=gap_pace)
            total_impact += impact
            total_speed += speed

            if act_d is not None:
                daily_impact[act_d] = daily_impact.get(act_d, 0.0) + impact

            hr = act.get("avg_hr")
            if hr:
                hrs.append(float(hr))
                if gap_pace and gap_pace > 0:
                    # GAP speed (m/s) / HR * 100
                    efficiencies.append(round((1000.0 / gap_pace) / float(hr) * 100.0, 3))

            # Time-in-zone polarization: prefer second-by-second HR stream when available
            used_stream_hr = False
            raw_streams = act.get("streams_json")
            if raw_streams:
                try:
                    import json as _json
                    st = _json.loads(raw_streams) if isinstance(raw_streams, str) else raw_streams
                    t_arr = (st.get("time") or {}).get("data") if isinstance(st.get("time"), dict) else st.get("time")
                    hr_arr = (st.get("heartrate") or {}).get("data") if isinstance(st.get("heartrate"), dict) else st.get("heartrate")
                    if t_arr and hr_arr:
                        for i in range(1, min(len(t_arr), len(hr_arr))):
                            dt = float(t_arr[i]) - float(t_arr[i - 1])
                            if dt <= 0 or dt > 60:
                                continue
                            h_val = float(hr_arr[i])
                            if h_val < self.ZONE_2_MAX:
                                intensity_sec["easy"] += dt
                            elif h_val < self.ZONE_3_MAX:
                                intensity_sec["tempo"] += dt
                            else:
                                intensity_sec["hard"] += dt
                        used_stream_hr = True
                except Exception:
                    used_stream_hr = False

            if not used_stream_hr and hr:
                dur_s = float(act.get("duration_sec") or 0.0)
                if hr < self.ZONE_2_MAX:
                    intensity_sec["easy"] += dur_s
                elif hr < self.ZONE_3_MAX:
                    intensity_sec["tempo"] += dur_s
                else:
                    intensity_sec["hard"] += dur_s

            bio = compute_benzie_biomechanics(act)
            if bio["cadence_spm"] is not None:
                cadences.append(bio["cadence_spm"])
            if bio["ground_contact_time_ms"] is not None:
                gcts.append(bio["ground_contact_time_ms"])
            if bio["vertical_oscillation_cm"] is not None:
                vert_oscs.append(bio["vertical_oscillation_cm"])
            if bio["stride_length_m"] is not None:
                strides.append(bio["stride_length_m"])

            dec = compute_aerobic_decoupling(act)
            if dec is not None:
                decouplings.append(dec)

        n_sessions = running_sessions
        tot_int = sum(intensity_sec.values()) or 1.0
        polarization = {
            "easy_pct": round(intensity_sec["easy"] / tot_int * 100, 1),
            "tempo_pct": round(intensity_sec["tempo"] / tot_int * 100, 1),
            "hard_pct": round(intensity_sec["hard"] / tot_int * 100, 1),
        }

        # Last 7 days of window for Foster Monotony & Strain
        last_7_impact = [daily_impact.get(end_d - timedelta(days=i), 0.0) for i in range(7)]
        monotony, strain = compute_monotony_and_strain(last_7_impact)

        return {
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "sessions": n_sessions,
            "distance_km": round(total_dist_km, 2),
            "duration_min": round(total_dur_min, 1),
            "elevation_gain_m": round(total_elev_gain, 0),
            "elevation_loss_m": round(total_elev_loss, 0),
            "impact_score": round(total_impact, 1),
            "cardio_score": round(total_cardio, 1),
            "speed_score": round(total_speed, 1),
            "impact_to_cardio_ratio": round(total_impact / total_cardio, 2) if total_cardio > 0 else None,
            "avg_hr": round(mean(hrs), 1) if hrs else None,
            "avg_cadence": round(mean(cadences), 1) if cadences else None,
            "avg_gct_ms": round(mean(gcts), 1) if gcts else None,
            "avg_vertical_oscillation_cm": round(mean(vert_oscs), 2) if vert_oscs else None,
            "avg_stride_length_m": round(mean(strides), 2) if strides else None,
            "aerobic_efficiency": round(mean(efficiencies), 3) if efficiencies else None,
            "avg_decoupling_pct": round(mean(decouplings), 2) if decouplings else None,
            "polarization": polarization,
            "monotony_7d": monotony,
            "strain_7d": strain,
            "cross_training": {
                "cycling_sessions": cycling_sessions,
                "cycling_km": round(cycling_km, 1),
                "strength_sessions": strength_sessions,
            },
        }

    def get_period_summary(
        self,
        days: int = 28,
        end_date: Optional[date] = None,
        compare_previous: bool = True,
    ) -> Dict:
        """
        Compute methodology-driven period summary (Albon Dual-Load, SWAP Polarization/Economy,
        Uphill Athlete Decoupling, and Coggan Dual CTL/ATL/TSB).
        """
        from src.modules.methodology import (
            compute_cardio_score,
            compute_ctl_atl_tsb,
            compute_impact_and_gap,
            compute_speed_score,
        )

        end_d = end_date or date.today()
        start_d = end_d - timedelta(days=days - 1)
        activities = self.activity_repo.get_range(start_d, end_d)
        summary = self._summarize_activities_window(activities, start_d, end_d)

        # Dual/Triple CTL / ATL / TSB (needs ~84 days of history for accurate 42d EMA)
        hist_start = end_d - timedelta(days=90)
        hist_activities = self.activity_repo.get_range(hist_start, end_d)
        daily_impact: Dict[date, float] = {}
        daily_cardio: Dict[date, float] = {}
        daily_speed: Dict[date, float] = {}
        for act in hist_activities:
            try:
                act_d = date.fromisoformat(str(act.get("date") or "")[:10])
            except ValueError:
                continue
            car = compute_cardio_score(act)
            daily_cardio[act_d] = daily_cardio.get(act_d, 0.0) + car
            if self._is_running_activity(act):
                imp, gap_p = compute_impact_and_gap(act)
                spd = compute_speed_score(act, gap_pace_sec=gap_p)
                daily_impact[act_d] = daily_impact.get(act_d, 0.0) + imp
                daily_speed[act_d] = daily_speed.get(act_d, 0.0) + spd

        summary["dual_load"] = {
            "impact": compute_ctl_atl_tsb(daily_impact, end_d),
            "cardio": compute_ctl_atl_tsb(daily_cardio, end_d),
            "speed": compute_ctl_atl_tsb(daily_speed, end_d),
        }

        if compare_previous:
            prev_end = start_d - timedelta(days=1)
            prev_start = prev_end - timedelta(days=days - 1)
            prev_acts = self.activity_repo.get_range(prev_start, prev_end)
            prev = self._summarize_activities_window(prev_acts, prev_start, prev_end)

            def _pct(cur, old):
                if old is None or old == 0 or cur is None:
                    return None
                return round(((cur - old) / old) * 100.0, 1)

            summary["delta_vs_previous"] = {
                "distance_pct": _pct(summary["distance_km"], prev["distance_km"]),
                "impact_pct": _pct(summary["impact_score"], prev["impact_score"]),
                "cardio_pct": _pct(summary["cardio_score"], prev["cardio_score"]),
                "efficiency_pct": _pct(summary["aerobic_efficiency"], prev["aerobic_efficiency"]),
            }

        return summary

    def get_trend_series(self, num_weeks: int = 12, end_date: Optional[date] = None) -> List[Dict]:
        """Return weekly time-series rows for trend analysis across all methodology metrics."""
        end_d = end_date or date.today()
        current_week_start = end_d - timedelta(days=end_d.weekday())
        rows: List[Dict] = []

        for i in range(num_weeks - 1, -1, -1):
            w_start = current_week_start - timedelta(weeks=i)
            w_end = w_start + timedelta(days=6)
            acts = self.activity_repo.get_range(w_start, w_end)
            row = self._summarize_activities_window(acts, w_start, w_end)
            iso_year, iso_week, _ = w_start.isocalendar()
            row["week"] = f"{iso_year}-W{iso_week:02d}"

            try:
                risk = self.detect_injury_risk(w_end)
                row["injury_risk_score"] = round(risk.risk_score, 1)
                row["injury_risk_level"] = risk.overall_risk
                row["acwr"] = round(risk.acwr, 2) if risk.acwr is not None else None
                row["risk_factors"] = risk.risk_factors
            except Exception:
                row["injury_risk_score"] = None
                row["injury_risk_level"] = None
                row["acwr"] = None
                row["risk_factors"] = []

            rows.append(row)

        return rows
