"""
Reverse engineering command group - Convert existing code to SpecQL YAML.
"""

import click

from cli.base import common_options


@click.group()
@common_options
def reverse(verbose, quiet, **kwargs):
    """Reverse engineer existing code to SpecQL YAML.

    Supports multiple languages and frameworks:

        specql reverse sql db/tables/*.sql
        specql reverse python src/models.py
        specql reverse project ./my-app

    Use 'specql reverse SUBCOMMAND --help' for details.
    """
    pass


# Import and register subcommands
def register_subcommands():
    """Register all reverse subcommands."""
    from cli.commands.reverse.java import java
    from cli.commands.reverse.project import project
    from cli.commands.reverse.python import python
    from cli.commands.reverse.rust import rust
    from cli.commands.reverse.sql import sql
    from cli.commands.reverse.typescript import typescript

    reverse.add_command(sql)
    reverse.add_command(python)
    reverse.add_command(typescript)
    reverse.add_command(rust)
    reverse.add_command(java)
    reverse.add_command(project)


# Register subcommands on import
register_subcommands()
