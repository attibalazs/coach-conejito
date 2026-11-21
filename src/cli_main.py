"""Main CLI entry point for Coach Conejito"""
import click
from dotenv import load_dotenv

load_dotenv()

from src.cli import status, metrics, risk, sync, activity, auth, stats, trends, export, journal


@click.group()
@click.option('--user', '-u', default='atti', help='User ID')
@click.pass_context
def cli(ctx, user):
    """Coach Conejito - AI-powered running coach CLI

    Fast, queryable insights into your training data.
    """
    ctx.ensure_object(dict)
    ctx.obj['user'] = user


# Register commands
cli.add_command(auth.auth)
cli.add_command(sync.sync)
cli.add_command(status.status)
cli.add_command(metrics.metrics)
cli.add_command(risk.risk)
cli.add_command(activity.activity)
cli.add_command(stats.stats)
cli.add_command(trends.trends)
cli.add_command(export.export)
cli.add_command(journal.journal)


if __name__ == '__main__':
    cli()
