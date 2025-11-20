"""
SpecQL CLI Main Entry Point
"""

import click

from cli.cache_commands import cache
from cli.detect_patterns import detect_patterns
from cli.reverse import reverse as reverse_sql_cmd
from cli.reverse_python import reverse_python
from cli.validate import validate


@click.group()
def app():
    """SpecQL - Business-focused YAML to PostgreSQL + GraphQL code generator"""
    pass


# Add commands
app.add_command(reverse_python)
app.add_command(reverse_sql_cmd)
app.add_command(validate)
app.add_command(detect_patterns)
app.add_command(cache)


if __name__ == "__main__":
    app()
