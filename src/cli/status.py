"""Status command - weekly summary with alerts and metrics"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import date, timedelta
from typing import Dict, Any

from src.modules.repositories import get_repository
from src.modules.analysis_service import AnalysisService
from src.cli.formatting import (
    format_distance, format_pace, risk_emoji, risk_color,
    format_change, intensity_emoji
)

console = Console()


@click.command()
@click.option('--week', '-w', help='ISO week (e.g., 2026-W06)')
@click.pass_context
def status(ctx, week):
    """Show weekly summary with alerts and metrics"""
    user_id = ctx.obj['user']

    try:
        # Get services
        activity_repo, journal_repo, cache = get_repository(user_id)
        service = AnalysisService(activity_repo, journal_repo, cache)

        # Calculate week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Get summary data
        weekly = service.get_weekly_summary(today)
        metrics = weekly['metrics']
        risk = weekly['injury_risk']
        alerts = weekly.get('alerts', [])
        activities = weekly.get('activities', [])

        # Header
        console.print(f"\n[bold]WEEK SUMMARY[/bold] ({week_start.strftime('%b %d')}-{week_end.strftime('%d, %Y')})")
        console.print("─" * 50)

        # Basic stats
        console.print(f"Distance:     {format_distance(metrics.total_distance_km * 1000)}", end="")
        if metrics.week_over_week_change:
            console.print(f" ({format_change(metrics.week_over_week_change)} from last week)")
        else:
            console.print()

        console.print(f"Long run:     {format_distance(metrics.longest_run_km * 1000)}")
        console.print(f"Sessions:     {metrics.session_count} runs")

        if metrics.avg_hr > 0:
            hr_status = "aerobic ✓" if metrics.avg_hr < 135 else "moderate"
            console.print(f"Avg HR:       {int(metrics.avg_hr)} bpm ({hr_status})")

        if metrics.avg_cadence > 0:
            cadence_status = risk_emoji(50) if metrics.avg_cadence < 170 else "✅"
            console.print(f"Avg Cadence:  {int(metrics.avg_cadence)} spm {cadence_status}")

        # Alerts section
        if alerts:
            console.print(f"\n⚠️  [yellow]ALERTS ({len(alerts)})[/yellow]")
            console.print("─" * 50)
            for alert in alerts:
                console.print(f"• {alert['message']}")
                if 'recommendation' in alert:
                    console.print(f"  → {alert['recommendation']}")

        # Key metrics
        console.print(f"\n📊 [bold]KEY METRICS[/bold]")
        console.print("─" * 50)

        acwr_status = risk_emoji(0) if 0.8 <= metrics.acwr <= 1.3 else risk_emoji(40)
        console.print(f"ACWR:         {metrics.acwr:.2f} (safe zone: 0.8-1.3) {acwr_status}")

        risk_status = risk_emoji(risk.risk_score)
        risk_level = risk.overall_risk.upper()
        console.print(f"Injury Risk:  {risk.risk_score:.1f}/100 ({risk_level}) {risk_status}")

        fatigue_status = risk_emoji(0) if metrics.fatigue_index < 30 else risk_emoji(metrics.fatigue_index)
        fatigue_level = "low" if metrics.fatigue_index < 30 else "moderate" if metrics.fatigue_index < 60 else "high"
        console.print(f"Fatigue:      {fatigue_level.title()} {fatigue_status}")

        if metrics.vo2_max:
            console.print(f"VO2 max:      {metrics.vo2_max} (stable)")

        # Intensity distribution
        if metrics.intensity_distribution:
            console.print(f"\n[bold]INTENSITY DISTRIBUTION[/bold]")
            console.print("─" * 50)

            dist = metrics.intensity_distribution
            easy_count = dist.get('easy_count', 0)
            easy_km = dist.get('easy_km', 0)
            tempo_count = dist.get('tempo_count', 0)
            tempo_km = dist.get('tempo_km', 0)
            hard_count = dist.get('hard_count', 0)
            hard_km = dist.get('hard_km', 0)

            if easy_count > 0:
                console.print(f"Easy (HR <130):    {easy_count} run{'s' if easy_count > 1 else ''}, {format_distance(easy_km * 1000)}")
            if tempo_count > 0:
                console.print(f"Tempo (HR 130-145): {tempo_count} run{'s' if tempo_count > 1 else ''}, {format_distance(tempo_km * 1000)}")
            if hard_count > 0:
                console.print(f"Hard (HR >145):    {hard_count} run{'s' if hard_count > 1 else ''}, {format_distance(hard_km * 1000)}")

            # Assessment
            total_runs = easy_count + tempo_count + hard_count
            if total_runs > 0:
                easy_pct = (easy_count / total_runs) * 100
                if easy_pct >= 60:
                    console.print(f"Assessment: ✅ Good easy/hard balance")
                else:
                    console.print(f"Assessment: ⚠️  Consider more easy runs")

        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
