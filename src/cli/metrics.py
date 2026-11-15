"""Metrics command - trend analysis"""
import click
from rich.console import Console
from rich.table import Table
from datetime import date, timedelta

from src.modules.repositories import get_repository
from src.modules.analysis_service import AnalysisService
from src.cli.formatting import (
    format_distance, format_change, trend_arrow, risk_emoji
)

console = Console()


@click.command()
@click.option('--weekly', '-w', is_flag=True, help='Show weekly trends')
@click.option('--last', '-l', default=4, help='Number of weeks to show', type=int)
@click.option('--metric', '-m', help='Show specific metric (distance, pace, hr, cadence)')
@click.pass_context
def metrics(ctx, weekly: bool, last: int, metric: str):
    """Show metric trends and analysis"""
    user_id = ctx.obj['user']

    try:
        # Get services
        activity_repo, journal_repo, cache = get_repository(user_id)
        service = AnalysisService(activity_repo, journal_repo, cache)

        if weekly or not metric:
            show_weekly_trends(service, last)
        else:
            show_metric_trend(service, metric, last)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


def show_weekly_trends(service: AnalysisService, num_weeks: int):
    """Show weekly metrics table"""
    console.print(f"\n[bold]WEEKLY METRICS[/bold] (Last {num_weeks} Weeks)")
    console.print("═" * 80)

    # Create table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Week", style="cyan")
    table.add_column("Distance", justify="right")
    table.add_column("Sessions", justify="right")
    table.add_column("ACWR", justify="right")
    table.add_column("Injury Risk", justify="right")

    # Get data for each week
    today = date.today()
    weeks_data = []

    for i in range(num_weeks - 1, -1, -1):
        week_date = today - timedelta(weeks=i)
        week_start = week_date - timedelta(days=week_date.weekday())

        try:
            weekly = service.get_weekly_metrics(week_start)

            # Format week string
            iso_year, iso_week, _ = week_start.isocalendar()
            week_str = f"{iso_year}-W{iso_week:02d}"

            # Format values
            distance = format_distance(weekly.total_distance_km * 1000)
            sessions = str(weekly.session_count)
            acwr = f"{weekly.acwr:.2f}"
            risk = f"{risk_emoji(weekly.injury_risk_score)} {weekly.injury_risk_score:.0f}/100"

            table.add_row(week_str, distance, sessions, acwr, risk)
            weeks_data.append(weekly)

        except Exception:
            # Week might not have data
            continue

    console.print(table)

    # Show trends if we have enough data
    if len(weeks_data) >= 2:
        console.print(f"\n[bold]TRENDS[/bold] ({num_weeks} weeks):")

        first = weeks_data[0]
        last = weeks_data[-1]

        # Distance trend
        if first.total_distance_km > 0:
            dist_change = ((last.total_distance_km - first.total_distance_km) / first.total_distance_km) * 100
            arrow = trend_arrow(dist_change)
            console.print(f"  Distance:     {arrow} {abs(dist_change):.0f}% ({first.total_distance_km:.1f} → {last.total_distance_km:.1f} km)")

        # ACWR trend
        acwr_change = ((last.acwr - first.acwr) / first.acwr) * 100 if first.acwr > 0 else 0
        arrow = trend_arrow(acwr_change)
        console.print(f"  ACWR:         {arrow} {abs(acwr_change):.0f}% ({first.acwr:.2f} → {last.acwr:.2f})")

        # Injury risk trend
        risk_change = ((last.injury_risk_score - first.injury_risk_score) / max(first.injury_risk_score, 1)) * 100
        arrow = trend_arrow(risk_change)
        console.print(f"  Injury Risk:  {arrow} {abs(risk_change):.0f}% ({first.injury_risk_score:.0f} → {last.injury_risk_score:.0f})")

        # Warnings
        warnings = []
        if last.acwr > 1.3:
            warnings.append("ACWR in risky zone (>1.3)")
        elif last.acwr > 1.2:
            warnings.append("ACWR approaching risky zone (>1.3)")

        if last.injury_risk_score > 60:
            warnings.append("High injury risk - consider rest")
        elif last.injury_risk_score > 40:
            warnings.append("Injury risk increasing - monitor closely")

        if risk_change > 50:
            warnings.append("Rapid injury risk increase")

        if warnings:
            console.print(f"\n⚠️  [yellow]WARNINGS:[/yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")

    console.print()


def show_metric_trend(service: AnalysisService, metric_name: str, num_weeks: int):
    """Show trend for a specific metric"""
    console.print(f"\n[bold]{metric_name.upper()} TREND[/bold] (Last {num_weeks} Weeks)")
    console.print("═" * 60)

    # Get trend data
    trend = service.detect_trends(metric_name, weeks=num_weeks)

    console.print(f"Direction: {trend.direction.upper()}")
    console.print(f"Change:    {trend.change_pct:+.1f}%")
    console.print(f"Confidence: {trend.confidence.upper()}")

    if trend.direction == "improving":
        console.print(f"\n✅ [green]Metric is improving over time[/green]")
    elif trend.direction == "declining":
        console.print(f"\n⚠️  [yellow]Metric is declining - investigate[/yellow]")
    else:
        console.print(f"\n→ [blue]Metric is stable[/blue]")

    console.print()
