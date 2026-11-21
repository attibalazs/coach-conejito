"""Journal command - lightweight N=1 subjective logging (RPE, mood, soreness, notes)."""
from datetime import date

import click
from rich.console import Console
from rich.table import Table

from src.modules.repositories import get_repository

console = Console()


@click.group()
def journal():
    """Log and view daily subjective athlete feedback (N=1 context)."""


@journal.command("add")
@click.option("--date", "entry_date", default=None, help="Date YYYY-MM-DD (defaults to today)")
@click.option("--rpe", type=click.IntRange(1, 10), required=True, help="Session RPE (1-10)")
@click.option("--soreness", type=click.IntRange(1, 10), required=True, help="Muscle soreness (1-10)")
@click.option("--mood", default="good", show_default=True, help="Mood / mental state (e.g. energized, tired, stressed)")
@click.option("--notes", default="", help="Free-text notes (e.g. fueling carbs/hr, sleep, niggles)")
@click.pass_context
def journal_add(ctx, entry_date: str, rpe: int, soreness: int, mood: str, notes: str):
    """Save a daily journal entry."""
    user_id = ctx.obj["user"]
    target_date = date.fromisoformat(entry_date) if entry_date else date.today()

    activity_repo, journal_repo, cache = get_repository(user_id)
    try:
        journal_repo.save({
            "date": target_date.isoformat(),
            "rpe": rpe,
            "soreness": soreness,
            "mood": mood,
            "notes": notes,
        })
        console.print(f"[green]✓ Saved journal for {target_date.isoformat()}[/green] (RPE {rpe}/10, Soreness {soreness}/10, Mood: {mood})")
    finally:
        activity_repo.close()
        journal_repo.close()
        cache.close()


@journal.command("list")
@click.option("--limit", "-l", default=10, show_default=True, type=int, help="Number of recent entries")
@click.pass_context
def journal_list(ctx, limit: int):
    """List recent journal entries."""
    user_id = ctx.obj["user"]
    activity_repo, journal_repo, cache = get_repository(user_id)
    try:
        entries = journal_repo.get_latest(limit=limit)
    finally:
        activity_repo.close()
        journal_repo.close()
        cache.close()

    table = Table(title=f"Recent Journal Entries ({user_id})")
    table.add_column("Date", style="cyan")
    table.add_column("RPE", justify="right")
    table.add_column("Soreness", justify="right")
    table.add_column("Mood")
    table.add_column("Notes")

    for e in entries:
        table.add_row(
            str(e.get("date", "")),
            f"{e['rpe']}/10" if e.get("rpe") is not None else "-",
            f"{e['soreness']}/10" if e.get("soreness") is not None else "-",
            e.get("mood") or "-",
            e.get("notes") or "",
        )
    console.print(table)
