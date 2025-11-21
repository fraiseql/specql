"""
Rich console output utilities for CLI.
"""

from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

# Global console instance
console = Console()


class CLIOutput:
    """Centralized output handling for CLI commands."""

    def __init__(self, verbose: bool = False, quiet: bool = False):
        self.verbose = verbose
        self.quiet = quiet

    def print(self, message: str, **kwargs) -> None:
        """Print a message if not in quiet mode."""
        if not self.quiet:
            console.print(message, **kwargs)

    def verbose_print(self, message: str, **kwargs) -> None:
        """Print a message only in verbose mode."""
        if self.verbose:
            console.print(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Print an error message (always shown)."""
        console.print(f"❌ {message}", style="bold red", **kwargs)

    def success(self, message: str, **kwargs) -> None:
        """Print a success message."""
        if not self.quiet:
            console.print(f"✅ {message}", style="bold green", **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Print a warning message."""
        if not self.quiet:
            console.print(f"⚠️  {message}", style="bold yellow", **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Print an info message."""
        if not self.quiet:
            console.print(f"ℹ️  {message}", style="bold blue", **kwargs)

    @contextmanager
    def progress(self, description: str = "Processing..."):
        """Context manager for progress display."""
        if self.quiet:
            yield None
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(description, total=100)
                yield progress

    def create_table(self, title: str | None = None, **kwargs) -> Table:
        """Create a Rich table with consistent styling."""
        table = Table(title=title, **kwargs)
        return table

    def print_table(self, table: Table) -> None:
        """Print a table if not in quiet mode."""
        if not self.quiet:
            console.print(table)


# Global output instance (can be configured per command)
output = CLIOutput()


def set_output_config(verbose: bool = False, quiet: bool = False) -> None:
    """Configure global output settings."""
    global output
    output = CLIOutput(verbose=verbose, quiet=quiet)


def print_banner(title: str, version: str | None = None) -> None:
    """Print a formatted banner."""
    banner_text = f"🔧 {title}"
    if version:
        banner_text += f" v{version}"

    panel = Panel(banner_text, border_style="blue", title_align="center")
    console.print(panel)


def print_summary(stats: dict[str, Any]) -> None:
    """Print a summary of operation results."""
    table = Table(title="📊 Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in stats.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)
