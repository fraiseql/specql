"""
Patterns command group - Detect and apply architectural patterns.
"""

import click

from cli.base import common_options


@click.group()
@common_options
def patterns(verbose, quiet, **kwargs):
    """Detect and apply architectural patterns in SpecQL YAML.

    Patterns help identify common database design patterns like audit trails,
    soft deletes, multi-tenancy, and more. Apply patterns to automatically
    enhance your entity definitions.

    Examples:

        specql patterns detect entities/*.yaml
        specql patterns apply audit-trail contact.yaml
    """
    pass


# Import and register subcommands
def register_subcommands():
    """Register all patterns subcommands."""
    from cli.commands.patterns.apply import apply
    from cli.commands.patterns.detect import detect

    patterns.add_command(detect)
    patterns.add_command(apply)


# Register subcommands on import
register_subcommands()
