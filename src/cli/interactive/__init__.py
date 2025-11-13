"""
Interactive CLI module for SpecQL

Provides a Textual-based terminal UI for real-time SpecQL development
with live preview, syntax highlighting, and pattern suggestions.
"""

import click
from .app import run_interactive

__all__ = ["interactive_command"]


@click.command()
def interactive():
    """
    Launch interactive SpecQL builder

    Features:
    - Live YAML editor with syntax highlighting
    - Real-time SQL preview
    - Pattern detection and suggestions
    - One-click generation

    Examples:
        specql interactive
    """
    run_interactive()