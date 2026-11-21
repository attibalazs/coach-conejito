"""Stats command - methodology-driven period summaries (Albon Dual-Load, SWAP Polarization, Uphill Athlete)."""
from datetime import date
import json

import click
from rich.console import Console
from rich.table import Table

from src.modules.analysis_service import AnalysisService
from src.modules.repositories import get_repository

console = Console()

PERIOD_DAYS = {
    "7d": 7,
    "28d": 28,
    "90d": 90,
}


def _resolve_days(period: str) -> int:
    if period == "ytd":
        today = date.today()
        return (today - date(today.year, 1, 1)).days + 1
    return PERIOD_DAYS[period]


@click.command()
@click.option(
    "--period",
    "-p",
    type=click.Choice(["7d", "28d", "90d", "ytd"], case_sensitive=False),
    default="28d",
    show_default=True,
    help="Summary period",
)
@click.option("--compare/--no-compare", default=True, help="Compare against previous period")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format",
)
@click.pass_context
def stats(ctx, period: str, compare: bool, fmt: str):
    """Show period statistics: Albon Impact vs Cardio, SWAP polarization, & Dual CTL/ATL/TSB."""
    user_id = ctx.obj["user"]
    days = _resolve_days(period.lower())

    activity_repo, journal_repo, cache = get_repository(user_id)
    try:
        service = AnalysisService(activity_repo, journal_repo, cache)
        summary = service.get_period_summary(days=days, compare_previous=compare)
    finally:
        activity_repo.close()
        journal_repo.close()
        cache.close()

    if fmt.lower() == "json":
        click.echo(json.dumps(summary, indent=2))
        return

    console.print(
        f"\n[bold]TRAINING STATS ({period.upper()})[/bold] "
        f"[dim]{summary['start_date']} → {summary['end_date']}[/dim]"
    )

    deltas = summary.get("delta_vs_previous") or {}

    def _fmt_delta(val):
        if val is None:
            return "-"
        sign = "+" if val >= 0 else ""
        color = "green" if val >= 0 else "red"
        return f"[{color}]{sign}{val}%[/{color}]"

    vol_table = Table(title="Volume & Dual-Load (Albon / Ascend)")
    vol_table.add_column("Metric", style="cyan")
    vol_table.add_column("Value", justify="right")
    vol_table.add_column("vs Prev", justify="right")

    vol_table.add_row("Sessions", str(summary["sessions"]), "-")
    vol_table.add_row("Distance", f"{summary['distance_km']:.1f} km", _fmt_delta(deltas.get("distance_pct")))
    vol_table.add_row("Duration", f"{summary['duration_min']:.0f} min", "-")
    vol_table.add_row("Elevation +/-", f"+{summary['elevation_gain_m']:.0f}m / -{summary['elevation_loss_m']:.0f}m", "-")
    vol_table.add_row("Mechanical Impact", f"{summary['impact_score']:.1f}", _fmt_delta(deltas.get("impact_pct")))
    vol_table.add_row("Cardio Score (TRIMP)", f"{summary['cardio_score']:.1f}", _fmt_delta(deltas.get("cardio_pct")))
    vol_table.add_row("Speed Score (Ascend)", f"{summary.get('speed_score', 0.0):.1f}", "-")
    ratio = summary.get("impact_to_cardio_ratio")
    vol_table.add_row("Impact : Cardio Ratio", f"{ratio:.2f}" if ratio is not None else "-", "-")
    eff = summary.get("aerobic_efficiency")
    vol_table.add_row("Aerobic Efficiency (GAP/HR)", f"{eff:.3f}" if eff is not None else "-", _fmt_delta(deltas.get("efficiency_pct")))
    dec = summary.get("avg_decoupling_pct")
    vol_table.add_row("Avg Decoupling (Pa:HR)", f"{dec:.1f}%" if dec is not None else "-", "-")
    console.print(vol_table)

    dual = summary["dual_load"]
    load_table = Table(title="Dual Fitness / Fatigue / Form (CTL / ATL / TSB)")
    load_table.add_column("Load Type", style="cyan")
    load_table.add_column("CTL (42d)", justify="right")
    load_table.add_column("ATL (7d)", justify="right")
    load_table.add_column("TSB (Form)", justify="right")
    for label, key in [("Mechanical Impact", "impact"), ("Cardio (TRIMP)", "cardio"), ("Speed (GAP vs Thr)", "speed")]:
        d = dual[key]
        load_table.add_row(label, f"{d['ctl']:.1f}", f"{d['atl']:.1f}", f"{d['tsb']:+.1f}")
    console.print(load_table)

    pol = summary["polarization"]
    console.print(
        f"\n[bold]SWAP Polarization:[/bold] "
        f"Easy {pol['easy_pct']}% | Tempo {pol['tempo_pct']}% | Hard {pol['hard_pct']}%"
    )
    cad = f"{summary['avg_cadence']:.0f} spm" if summary.get("avg_cadence") is not None else "-"
    gct = f"{summary['avg_gct_ms']:.0f} ms" if summary.get("avg_gct_ms") is not None else "-"
    vo = f"{summary['avg_vertical_oscillation_cm']:.1f} cm" if summary.get("avg_vertical_oscillation_cm") is not None else "-"
    console.print(
        f"[bold]Benzie Biomechanics:[/bold] Cadence {cad} (175-185) | GCT {gct} (<240) | Vert Osc {vo} (~7.5)"
    )
    if summary.get("monotony_7d") is not None:
        console.print(
            f"[bold]Foster 7d Monotony / Strain:[/bold] "
            f"{summary['monotony_7d']} / {summary['strain_7d']}"
        )
    console.print()
