"""Activity command - query and view activities"""
import click
from rich.console import Console
from rich.table import Table
from datetime import date

from src.modules.repositories import get_repository
from src.modules.analysis_service import AnalysisService
from src.cli.formatting import (
    format_distance, format_duration, format_pace, format_elevation
)

console = Console()


@click.group()
def activity():
    """Query and view activities"""
    pass


@activity.command()
@click.option('--limit', '-l', default=10, help='Number of activities to show', type=int)
@click.option('--type', '-t', help='Filter by activity type (running, cycling, etc.)')
@click.pass_context
def list(ctx, limit: int, type: str):
    """List recent activities"""
    user_id = ctx.obj['user']

    try:
        # Get services
        activity_repo, journal_repo, cache = get_repository(user_id)
        service = AnalysisService(activity_repo, journal_repo, cache)

        # Get recent activities
        activities = activity_repo.get_latest(limit=limit)

        if type:
            activities = [a for a in activities if a.get('activityType', {}).get('typeKey') == type]

        if not activities:
            console.print("\n[yellow]No activities found[/yellow]\n")
            return

        # Create table
        console.print(f"\n[bold]RECENT ACTIVITIES[/bold] (Last {len(activities)})")
        console.print("═" * 80)

        table = Table(show_header=True, header_style="bold")
        table.add_column("Date", style="cyan")
        table.add_column("Type")
        table.add_column("Distance", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Pace", justify="right")
        table.add_column("Avg HR", justify="right")

        for activity in activities:
            # Parse activity data
            activity_date = activity.get('startTimeLocal', '')[:10]
            activity_type = activity.get('activityType', {}).get('typeKey', 'unknown')
            distance = activity.get('distance', 0)
            duration = activity.get('duration', 0)
            avg_hr = activity.get('averageHR', 0)

            # Calculate pace
            pace_str = "N/A"
            if distance > 0 and duration > 0:
                pace_sec_per_km = duration / (distance / 1000)
                pace_str = format_pace(pace_sec_per_km)

            table.add_row(
                activity_date,
                activity_type.replace('_', ' ').title(),
                format_distance(distance),
                format_duration(duration),
                pace_str,
                f"{int(avg_hr)} bpm" if avg_hr > 0 else "N/A"
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@activity.command()
@click.argument('activity_id')
@click.pass_context
def show(ctx, activity_id: str):
    """Show detailed activity information"""
    user_id = ctx.obj['user']

    try:
        # Get services
        activity_repo, journal_repo, cache = get_repository(user_id)
        service = AnalysisService(activity_repo, journal_repo, cache)

        # Get activity
        activity = activity_repo.get_by_id(activity_id)

        if not activity:
            console.print(f"\n[red]Activity {activity_id} not found[/red]\n")
            raise click.Abort()

        # Get computed metrics
        metrics = service.get_activity_metrics(activity_id)

        # Display header
        activity_date = activity.get('startTimeLocal', '')[:10]
        activity_type = activity.get('activityType', {}).get('typeKey', 'unknown')
        activity_name = activity.get('activityName', 'Unnamed Activity')

        console.print(f"\n[bold]{activity_name}[/bold]")
        console.print(f"{activity_type.replace('_', ' ').title()} - {activity_date}")
        console.print("═" * 60)

        # Basic stats
        console.print("\n[bold]BASIC STATS[/bold]")
        console.print(f"Distance:     {format_distance(metrics.distance_km * 1000)}")
        console.print(f"Duration:     {format_duration(metrics.duration_min * 60)}")
        console.print(f"Pace:         {format_pace(metrics.pace_per_km.total_seconds())}")
        console.print(f"Elevation:    {format_elevation(metrics.elevation_m)}")

        # Physiological data
        console.print("\n[bold]PHYSIOLOGICAL[/bold]")
        console.print(f"Avg HR:       {int(metrics.avg_hr)} bpm")
        console.print(f"Cadence:      {int(metrics.cadence)} spm")

        if metrics.vo2_max:
            console.print(f"VO2 Max:      {metrics.vo2_max}")

        if metrics.training_effect:
            console.print(f"Training Effect: {metrics.training_effect:.1f}")

        # HR Zones
        if metrics.hr_zones:
            console.print("\n[bold]HR ZONES[/bold]")
            for zone, minutes in sorted(metrics.hr_zones.items()):
                if minutes > 0:
                    console.print(f"Zone {zone}:       {minutes:.1f} min")

        # Efficiency
        console.print("\n[bold]EFFICIENCY[/bold]")
        console.print(f"Score:        {metrics.efficiency_score:.2f}")

        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
