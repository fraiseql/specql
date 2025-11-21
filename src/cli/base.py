"""
Shared CLI utilities and decorators.
"""

import logging
from collections.abc import Callable
from typing import Any

import click


def common_options(f: Callable) -> Callable:
    """Decorator to add common options to a Click command.

    Adds --verbose/-v, --quiet/-q, and --output-dir/-o options.
    """
    # Add options in reverse order (Click applies them bottom-up)
    f = click.option("--output-dir", "-o", type=click.Path(), help="Output directory")(f)
    f = click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")(f)
    f = click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")(f)
    return f


def validate_common_options(verbose: bool, quiet: bool, **kwargs: Any) -> dict[str, Any]:
    """Validate common options and configure logging.

    Args:
        verbose: Enable verbose logging
        quiet: Suppress non-error output
        **kwargs: Other options

    Returns:
        Validated kwargs

    Raises:
        click.UsageError: If verbose and quiet are both specified
    """
    if verbose and quiet:
        raise click.UsageError("--verbose and --quiet are mutually exclusive")

    # Configure logging based on flags
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logging.getLogger().setLevel(logging.INFO)

    return kwargs
