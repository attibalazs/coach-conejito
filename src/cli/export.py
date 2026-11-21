"""Export command - dump analysis-ready activities, methodology metrics, wellness, and journals."""
import csv
from datetime import date, timedelta
import io
import json

import click

from src.modules.analysis_service import AnalysisService
from src.modules.methodology import (
    compute_aerobic_decoupling,
    compute_benzie_biomechanics,
    compute_cardio_score,
    compute_impact_and_gap,
    compute_speed_score,
)
from src.modules.repositories import get_repository, get_wellness_repository


@click.command()
@click.option("--days", "-d", default=90, show_default=True, type=int, help="Number of days to export")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "csv", "markdown"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Export format",
)
@click.option("--out", "-o", type=click.Path(), help="Optional file path to write output to")
@click.pass_context
def export(ctx, days: int, fmt: str, out: str):
    """Export training data + methodology metrics for analysis."""
    user_id = ctx.obj["user"]
    end_d = date.today()
    start_d = end_d - timedelta(days=days - 1)

    activity_repo, journal_repo, cache = get_repository(user_id)
    wellness_repo = get_wellness_repository(user_id)
    try:
        activities = activity_repo.get_range(start_d, end_d)
        journals = journal_repo.get_range(start_d, end_d)
        wellness = wellness_repo.get_range(start_d, end_d)
        service = AnalysisService(activity_repo, journal_repo, cache)
        period_summary = service.get_period_summary(days=days, end_date=end_d, compare_previous=True)
        num_weeks = max(4, min(52, (days + 6) // 7))
        weekly_trends = service.get_trend_series(num_weeks=num_weeks, end_date=end_d)
    finally:
        activity_repo.close()
        journal_repo.close()
        cache.close()
        wellness_repo.close()

    enriched_activities = []
    for act in activities:
        impact, gap_pace = compute_impact_and_gap(act)
        cardio = compute_cardio_score(act)
        speed = compute_speed_score(act, gap_pace_sec=gap_pace)
        decoupling = compute_aerobic_decoupling(act)
        bio = compute_benzie_biomechanics(act)
        enriched_activities.append({
            "id": act.get("id"),
            "date": act.get("date"),
            "source": act.get("source", "garmin"),
            "name": act.get("activity_name") or act.get("activityName") or act.get("name"),
            "type": act.get("activity_type"),
            "distance_km": round((act.get("distance_m") or 0) / 1000.0, 2),
            "duration_min": round((act.get("duration_sec") or 0) / 60.0, 1),
            "elevation_gain_m": act.get("elevation_gain_m"),
            "elevation_loss_m": act.get("elevation_loss_m"),
            "avg_hr": act.get("avg_hr"),
            "max_hr": act.get("max_hr"),
            "cadence": bio["cadence_spm"],
            "gct_ms": bio["ground_contact_time_ms"],
            "vertical_oscillation_cm": bio["vertical_oscillation_cm"],
            "stride_length_m": bio["stride_length_m"],
            "impact_score": impact,
            "cardio_score": cardio,
            "speed_score": speed,
            "gap_pace_sec_per_km": gap_pace,
            "decoupling_pct": decoupling,
        })

    fmt = fmt.lower()
    if fmt == "json":
        output_text = json.dumps(
            {
                "user_id": user_id,
                "window": {"start": start_d.isoformat(), "end": end_d.isoformat(), "days": days},
                "summary": period_summary,
                "weekly_trends": weekly_trends,
                "activities": enriched_activities,
                "wellness": wellness,
                "journals": journals,
            },
            indent=2,
            default=str,
        )
    elif fmt == "csv":
        buf = io.StringIO()
        fieldnames = [
            "id", "date", "source", "name", "type", "distance_km", "duration_min",
            "elevation_gain_m", "elevation_loss_m", "avg_hr", "max_hr", "cadence",
            "gct_ms", "vertical_oscillation_cm", "stride_length_m",
            "impact_score", "cardio_score", "speed_score", "gap_pace_sec_per_km", "decoupling_pct",
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_activities)
        output_text = buf.getvalue()
    else:
        lines = [
            f"# Training Export ({user_id}) — {start_d.isoformat()} to {end_d.isoformat()}",
            "",
            f"- **Sessions:** {period_summary['sessions']}",
            f"- **Distance:** {period_summary['distance_km']:.1f} km",
            f"- **Elevation:** +{period_summary['elevation_gain_m']:.0f}m / -{period_summary['elevation_loss_m']:.0f}m",
            f"- **Mechanical Impact:** {period_summary['impact_score']:.1f}",
            f"- **Cardio Score (TRIMP):** {period_summary['cardio_score']:.1f}",
            f"- **Polarization:** Easy {period_summary['polarization']['easy_pct']}% | "
            f"Tempo {period_summary['polarization']['tempo_pct']}% | Hard {period_summary['polarization']['hard_pct']}%",
            "",
            "| Date | Source | Name | Dist (km) | Dur (min) | HR | Impact | Cardio | Drift % |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for a in enriched_activities:
            drift = f"{a['decoupling_pct']:.1f}%" if a["decoupling_pct"] is not None else "-"
            hr = str(a["avg_hr"]) if a["avg_hr"] is not None else "-"
            lines.append(
                f"| {a['date']} | {a['source']} | {a['name'] or '-'} | "
                f"{a['distance_km']:.2f} | {a['duration_min']:.1f} | {hr} | "
                f"{a['impact_score']:.1f} | {a['cardio_score']:.1f} | {drift} |"
            )
        output_text = "\n".join(lines) + "\n"

    if out:
        with open(out, "w") as f:
            f.write(output_text)
        click.echo(f"Exported {len(enriched_activities)} activities to {out}")
    else:
        click.echo(output_text)
