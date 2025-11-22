"""Test command group for SpecQL CLI"""

import click

# Import and register subcommands
from .generate import generate
from .reverse import reverse
from .seed import seed


@click.group()
def test():
    """Testing tools: seed data, test generation, and reverse engineering.

    Generate test seed data, auto-generate tests, or reverse engineer
    existing tests to SpecQL test specifications.

    Examples:

        specql test seed entities/*.yaml -o seeds/
        specql test generate entities/*.yaml --type pgtap
        specql test reverse tests/*.sql -o specs/
    """
    pass


test.add_command(seed)
test.add_command(generate)
test.add_command(reverse)
