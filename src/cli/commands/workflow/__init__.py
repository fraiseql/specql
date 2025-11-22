"""
Workflow command group - Multi-step automation for SpecQL operations.
"""

import click

from cli.base import common_options


@click.group()
@common_options
def workflow(verbose, quiet, **kwargs):
    """Multi-step automation for SpecQL operations.

    Workflow commands orchestrate complex operations that involve multiple
    steps, such as full migrations or incremental synchronization.

    Examples:

        specql workflow migrate entities/*.yaml
        specql workflow sync --watch entities/
    """
    pass


# Import and register subcommands
def register_subcommands():
    """Register all workflow subcommands."""
    from cli.commands.workflow.migrate import migrate
    from cli.commands.workflow.sync import sync

    workflow.add_command(migrate)
    workflow.add_command(sync)


# Register subcommands on import
register_subcommands()
