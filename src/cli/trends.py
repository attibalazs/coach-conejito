"""Trends command - weekly time-series across SWAP, Albon, and Uphill Athlete metrics."""
import json

import click
from rich.console import Console
from rich.table import Table

from src.modules.analysis_service import AnalysisService
from src.modules.repositories import get_repository

console = Console()


@click.command()
@click.option("--weeks", "-w", default=12, show_default=True, type=int, help="Number of weeks to display")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format",
)
@click.pass_context
def trends(ctx, weeks: int, fmt: str):
    """Show weekly training trends (Volume, Impact, Cardio, Efficiency, Decoupling)."""
    user_id = ctx.obj["user"]

    activity_repo, journal_repo, cache = get_repository(user_id)
    try:
        service = AnalysisService(activity_repo, journal_repo, cache)
        rows = service.get_trend_series(num_weeks=weeks)
    finally:
        activity_repo.close()
        journal_repo.close()
        cache.close()

    if fmt.lower() == "json":
        click.echo(json.dumps(rows, indent=2))
        return

    table = Table(title=f"Weekly Trends (Last {weeks} Weeks) — {user_id}")
    table.add_column("Week", style="cyan")
    table.add_column("Runs", justify="right")
    table.add_column("Dist (km)", justify="right")
    table.add_column("Vert+ (m)", justify="right")
    table.add_column("Impact", justify="right")
    table.add_column("Cardio", justify="right")
    table.add_column("Eff (GAP/HR)", justify="right")
    table.add_column("Drift %", justify="right")
    table.add_column("Cad", justify="right")
    table.add_column("GCT ms", justify="right")
    table.add_column("Easy %", justify="right")

    for r in rows:
        eff = f"{r['aerobic_efficiency']:.3f}" if r.get("aerobic_efficiency") is not None else "-"
        drift = f"{r['avg_decoupling_pct']:.1f}%" if r.get("avg_decoupling_pct") is not None else "-"
        cad = f"{r['avg_cadence']:.0f}" if r.get("avg_cadence") is not None else "-"
        gct = f"{r['avg_gct_ms']:.0f}" if r.get("avg_gct_ms") is not None else "-"
        easy = f"{r['polarization']['easy_pct']:.0f}%" if r["sessions"] > 0 else "-"
        table.add_row(
            r["week"],
            str(r["sessions"]),
            f"{r['distance_km']:.1f}",
            f"{r['elevation_gain_m']:.0f}",
            f"{r['impact_score']:.1f}",
            f"{r['cardio_score']:.1f}",
            eff,
            drift,
            cad,
            gct,
            easy,
        )

    console.print()
    console.print(table)
    console.print()
