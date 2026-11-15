"""Main CLI entry point for Coach Conejito"""
import click
from src.cli import status, metrics, risk, sync, activity


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
cli.add_command(status.status)
cli.add_command(metrics.metrics)
cli.add_command(risk.risk)
cli.add_command(sync.sync)
cli.add_command(activity.activity)


if __name__ == '__main__':
    cli()
