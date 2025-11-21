"""
Init command group - Project scaffolding and templates.
"""

import click

from cli.base import common_options


@click.group()
@common_options
def init(verbose, quiet, **kwargs):
    """Create new SpecQL projects, entities, and registries.

    Quickly scaffold new SpecQL projects with proper directory structure,
    create entity templates with common patterns, and initialize schema
    registries for table code management.

    Examples:

        specql init project my-app
        specql init entity Contact --schema=crm
        specql init registry
    """
    pass


# Import and register subcommands
def register_subcommands():
    """Register all init subcommands."""
    from cli.commands.init.entity import entity
    from cli.commands.init.project import project
    from cli.commands.init.registry import registry

    init.add_command(project)
    init.add_command(entity)
    init.add_command(registry)


# Register subcommands on import
register_subcommands()
