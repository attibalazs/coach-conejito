"""Sync command - Garmin & Strava data synchronization."""
from datetime import date, timedelta

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.modules.garmin_client import GarminClient
from src.modules.repositories import get_repository
from src.modules.strava_client import StravaClient

console = Console()


@click.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(["garmin", "strava", "all"], case_sensitive=False),
    default="garmin",
    show_default=True,
    help="Data source to sync",
)
@click.option("--days", "-d", default=7, show_default=True, help="Number of days to sync", type=int)
@click.option("--force", "-f", is_flag=True, help="Force re-sync of existing data")
@click.option("--streams", is_flag=True, help="Fetch time-series streams (elevation/grade/HR) where supported")
@click.option("--wellness", is_flag=True, help="Also sync daily wellness (RHR, HRV, sleep) from Garmin")
@click.pass_context
def sync(ctx, source: str, days: int, force: bool, streams: bool, wellness: bool):
    """Sync activities (and optionally wellness/streams) from Garmin and/or Strava."""
    user_id = ctx.obj["user"]
    source = source.lower()
    sources = ["garmin", "strava"] if source == "all" else [source]

    label = "Garmin data" if source == "garmin" else ", ".join(sources)
    console.print(f"\n[bold]Syncing {label} for {user_id}[/bold] (last {days} days)\n")

    any_success = False
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if "garmin" in sources:
                task = progress.add_task("Syncing Garmin activities...", total=None)
                garmin = GarminClient(user_id)
                activities = garmin.sync_activities(days=days)
                msg = f"Garmin: synced {len(activities)} activities"
                if wellness:
                    progress.update(task, description="Syncing Garmin wellness...")
                    w_count = garmin.sync_wellness(days=days)
                    msg += f", {w_count} wellness days"
                progress.update(task, description=f"✓ {msg}", completed=True)
                any_success = True

            if "strava" in sources:
                task = progress.add_task("Syncing Strava activities...", total=None)
                strava = StravaClient(user_id)
                res = strava.sync_activities(days=days, force=force, include_streams=streams)
                msg = (
                    f"Strava: {res['synced']} new, {res['deduplicated']} matched/deduped"
                    + (f", {res['streams_fetched']} streams" if streams else "")
                )
                progress.update(task, description=f"✓ {msg}", completed=True)
                any_success = True

        if any_success:
            _, _, cache = get_repository(user_id)
            cache.invalidate_after(date.today() - timedelta(days=days))
            cache.close()
            console.print("\n[green]✅ Sync complete[/green] [dim](metrics cache invalidated)[/dim]\n")

    except Exception as exc:
        console.print(f"\n[red]Error during sync:[/red] {exc}")
        console.print(f"[dim]Run `coach -u {user_id} auth status` to verify credentials.[/dim]\n")
        raise click.Abort()
