"""
SpecQL CLI - Unified command-line interface.
"""

import sys
from pathlib import Path

# Add project root and src to path for imports
project_root = Path(__file__).parent.parent.parent
src_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from importlib.metadata import version  # noqa: E402

import click  # noqa: E402

try:
    VERSION = version("specql")
except Exception:
    VERSION = "dev"


@click.group()
@click.version_option(VERSION, prog_name="specql")
def app():
    """SpecQL - Business YAML to Production PostgreSQL + GraphQL.

    Transform lightweight business domain definitions into production-ready
    database schemas, PL/pgSQL functions, and frontend code.

    Quick start:

        specql validate entities/*.yaml
        specql generate entities/*.yaml
        specql reverse sql db/*.sql -o entities/

    Run 'specql COMMAND --help' for command-specific help.
    """
    pass


def register_commands():
    """Register all CLI commands with lazy loading."""
    # Commands will be registered here in subsequent phases
    # This allows for lazy loading and better startup performance

    # Phase 2: Generate command
    from cli.commands.generate import generate

    app.add_command(generate)

    # Phase 3: Reverse command group
    from cli.commands.reverse import reverse

    app.add_command(reverse)

    # Phase 4: Patterns and Init command groups
    from cli.commands.init import init
    from cli.commands.patterns import patterns

    app.add_command(patterns)
    app.add_command(init)

    # Phase 5: Workflow command group
    from cli.commands.workflow import workflow

    app.add_command(workflow)

    # Phase 6: Validate command
    from cli.commands.validate import validate

    app.add_command(validate)


# Register commands on import
register_commands()


if __name__ == "__main__":
    app()
