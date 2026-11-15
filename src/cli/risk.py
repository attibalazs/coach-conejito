"""Risk command - detailed injury risk assessment"""
import click
from rich.console import Console
from rich.table import Table
from datetime import date as dt_date

from src.modules.repositories import get_repository
from src.modules.analysis_service import AnalysisService
from src.cli.formatting import risk_emoji, risk_color

console = Console()


@click.command()
@click.option('--date', '-d', help='Date to analyze (YYYY-MM-DD)')
@click.option('--detailed', is_flag=True, help='Show detailed breakdown')
@click.pass_context
def risk(ctx, date: str, detailed: bool):
    """Show detailed injury risk analysis"""
    user_id = ctx.obj['user']

    try:
        # Get services
        activity_repo, journal_repo, cache = get_repository(user_id)
        service = AnalysisService(activity_repo, journal_repo, cache)

        # Parse date
        analysis_date = dt_date.fromisoformat(date) if date else dt_date.today()

        # Get risk analysis
        risk_data = service.get_injury_risk(analysis_date)

        # Header
        console.print(f"\n[bold]INJURY RISK ANALYSIS[/bold] ({analysis_date.strftime('%b %d, %Y')})")
        console.print("═" * 60)

        # Overall risk
        risk_level = risk_data.overall_risk.upper()
        risk_score = risk_data.risk_score
        emoji = risk_emoji(risk_score)
        color = risk_color(risk_score)

        console.print(f"\nOVERALL RISK: [{color}]{emoji} {risk_level}[/{color}] ({risk_score:.1f}/100)\n")

        # Risk breakdown table
        console.print("[bold]RISK BREAKDOWN:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Factor", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Weight", justify="right")

        # Get breakdown from risk data
        breakdown = risk_data.risk_breakdown
        table.add_row("Volume Spike", f"{breakdown['volume_spike']:.0f}/100", "40%")
        table.add_row("Low Cadence", f"{breakdown['low_cadence']:.0f}/100", "30%")
        table.add_row("Rising Soreness", f"{breakdown['rising_soreness']:.0f}/100", "20%")
        table.add_row("ACWR Deviation", f"{breakdown['acwr_deviation']:.0f}/100", "10%")

        console.print(table)

        # Identified risk factors
        if risk_data.risk_factors:
            console.print(f"\n[bold]IDENTIFIED RISK FACTORS:[/bold]")
            for factor in risk_data.risk_factors:
                severity_emoji = "🔴" if "high" in factor.lower() else "🟡" if "moderate" in factor.lower() else "🟢"
                console.print(f"  {severity_emoji} {factor}")

        # Soreness trend
        if risk_data.soreness_trend:
            console.print(f"\n[bold]SORENESS TREND:[/bold]")
            trend = risk_data.soreness_trend
            if trend == "rising":
                console.print(f"  📈 [yellow]Rising[/yellow] - Monitor closely")
            elif trend == "stable":
                console.print(f"  → [green]Stable[/green] - No concerns")
            else:
                console.print(f"  📉 [green]Falling[/green] - Recovery progressing")

        # Recommendations
        if risk_data.recommendations:
            console.print(f"\n[bold]RECOMMENDATIONS:[/bold]")
            for i, rec in enumerate(risk_data.recommendations, 1):
                console.print(f"  {i}. {rec}")

        # ACWR details
        console.print(f"\n[bold]WORKLOAD METRICS:[/bold]")
        console.print(f"  ACWR: {risk_data.acwr:.2f}")
        console.print(f"  Volume Change: {risk_data.volume_change_pct:+.1f}%")

        if risk_data.acwr > 1.3:
            console.print(f"  ⚠️  [yellow]ACWR above safe zone (>1.3)[/yellow]")
        elif risk_data.acwr < 0.8:
            console.print(f"  ⚠️  [yellow]ACWR below safe zone (<0.8) - detraining risk[/yellow]")
        else:
            console.print(f"  ✅ [green]ACWR in safe zone (0.8-1.3)[/green]")

        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
