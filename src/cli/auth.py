"""Auth command - manage Garmin and Strava credentials via CLI."""
import os
from urllib.parse import parse_qs, urlparse

import click
from rich.console import Console
from rich.table import Table

from src.modules.garmin_client import GarminClient, is_garmin_authenticated, get_token_dir
from src.modules.strava_client import (
    exchange_code_for_token,
    get_authorization_url,
    get_strava_token_path,
    is_strava_authenticated,
)

console = Console()


def _extract_code(raw_input: str) -> str:
    """Extract OAuth authorization code from either a raw code or a callback URL."""
    text = raw_input.strip()
    if text.startswith("http"):
        parsed = urlparse(text)
        codes = parse_qs(parsed.query).get("code")
        if codes:
            return codes[0]
    return text


@click.group()
def auth():
    """Manage Garmin and Strava authentication."""


@auth.command("status")
@click.pass_context
def auth_status(ctx):
    """Show authentication status for Garmin and Strava."""
    user_id = ctx.obj["user"]

    garmin_ok = is_garmin_authenticated(user_id)
    strava_ok = is_strava_authenticated(user_id)

    table = Table(title=f"Auth Status ({user_id})")
    table.add_column("Provider", style="cyan")
    table.add_column("Status")
    table.add_column("Token Location", style="dim")

    table.add_row(
        "Garmin",
        "[green]Authenticated[/green]" if garmin_ok else "[yellow]Not configured[/yellow]",
        get_token_dir(user_id),
    )
    table.add_row(
        "Strava",
        "[green]Authenticated[/green]" if strava_ok else "[yellow]Not configured[/yellow]",
        get_strava_token_path(user_id),
    )
    console.print(table)


@auth.command("garmin")
@click.option("--email", envvar="GARMIN_EMAIL", prompt="Garmin email", help="Garmin Connect email")
@click.option("--password", envvar="GARMIN_PASSWORD", prompt=True, hide_input=True, help="Garmin Connect password")
@click.pass_context
def auth_garmin(ctx, email: str, password: str):
    """Authenticate with Garmin Connect and save session tokens."""
    user_id = ctx.obj["user"]
    try:
        GarminClient.login(user_id, email, password)
        console.print(f"[green]✓ Garmin authenticated for '{user_id}'[/green]")
        console.print(f"[dim]Tokens saved to {get_token_dir(user_id)}[/dim]")
    except Exception as exc:
        console.print(f"[red]Garmin login failed:[/red] {exc}")
        raise click.Abort()


@auth.command("strava")
@click.option("--client-id", envvar="STRAVA_CLIENT_ID", prompt="Strava Client ID", help="Strava API Client ID")
@click.option(
    "--client-secret",
    envvar="STRAVA_CLIENT_SECRET",
    prompt="Strava Client Secret",
    hide_input=True,
    help="Strava API Client Secret",
)
@click.option("--code", help="Authorization code or full callback URL (skips prompt)")
@click.pass_context
def auth_strava(ctx, client_id: str, client_secret: str, code: str):
    """Authenticate with Strava via OAuth2."""
    user_id = ctx.obj["user"]

    if not code:
        url = get_authorization_url(client_id)
        console.print("\n[bold]1. Open this URL in your browser and authorize Coach Conejito:[/bold]")
        console.print(f"[cyan]{url}[/cyan]\n")
        console.print("[dim]2. After approving, copy the full redirected localhost URL (or just the `code=` value) and paste it below.[/dim]")
        code = click.prompt("Authorization code or callback URL")

    extracted = _extract_code(code)
    try:
        exchange_code_for_token(user_id, client_id, client_secret, extracted)
        console.print(f"[green]✓ Strava authenticated for '{user_id}'[/green]")
        console.print(f"[dim]Tokens saved to {get_strava_token_path(user_id)}[/dim]")
    except Exception as exc:
        console.print(f"[red]Strava authentication failed:[/red] {exc}")
        raise click.Abort()
