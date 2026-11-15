"""Sync command - Garmin data synchronization"""
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.modules.garmin_client import GarminClient
from src.modules.repositories import get_repository

console = Console()


@click.command()
@click.option('--days', '-d', default=7, help='Number of days to sync', type=int)
@click.option('--force', '-f', is_flag=True, help='Force re-sync of existing data')
@click.pass_context
def sync(ctx, days: int, force: bool):
    """Sync Garmin data"""
    user_id = ctx.obj['user']

    try:
        console.print(f"\n[bold]Syncing Garmin data for {user_id}[/bold]")
        console.print(f"Fetching last {days} days of activities...\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            task = progress.add_task("Connecting to Garmin...", total=None)

            # Initialize Garmin client
            garmin = GarminClient(user_id)

            progress.update(task, description="Fetching activities...")

            # Sync activities
            activities = garmin.sync_activities(days=days)

            progress.update(task, description=f"Synced {len(activities)} activities")

            # Invalidate cache after sync
            _, _, cache = get_repository(user_id)
            from datetime import date, timedelta
            cache.invalidate_after(date.today() - timedelta(days=days))

            progress.update(task, description="✓ Sync complete", completed=True)

        console.print(f"\n✅ [green]Successfully synced {len(activities)} activities[/green]")
        console.print(f"   Metrics cache invalidated\n")

    except Exception as e:
        console.print(f"\n[red]Error during sync:[/red] {str(e)}")
        console.print(f"[dim]Make sure you have valid Garmin credentials configured[/dim]\n")
        raise click.Abort()
