"""
Unified error handling for CLI commands.
"""

from contextlib import contextmanager

import click
from rich.console import Console

console = Console(stderr=True)


class CLIError(click.ClickException):
    """Base exception for CLI errors with Rich formatting."""

    def __init__(self, message: str, hint: str | None = None, exit_code: int = 1):
        super().__init__(message)
        self.hint = hint
        self.exit_code = exit_code

    def format_message(self) -> str:
        """Format error message with Rich styling."""
        from rich.text import Text

        # Create error message with styling
        error_text = Text("Error: ", style="bold red")
        error_text.append(self.message)

        if self.hint:
            error_text.append(f"\n💡 {self.hint}", style="dim cyan")

        # Return plain text for Click compatibility
        return str(error_text)

    def show(self, file=None) -> None:
        """Show the error with Rich formatting."""
        from rich.panel import Panel

        error_content = f"Error: {self.message}"
        if self.hint:
            error_content += f"\n\n💡 {self.hint}"

        panel = Panel(error_content, title="❌ Error", border_style="red", title_align="left")
        console.print(panel)


class ValidationError(CLIError):
    """Error for validation failures with file location."""

    def __init__(
        self,
        message: str,
        file: str | None = None,
        line: int | None = None,
        column: int | None = None,
    ):
        self.file = file
        self.line = line
        self.column = column

        # Build location string
        location_parts = []
        if file:
            location_parts.append(file)
        if line is not None:
            location_parts.append(str(line))
        if column is not None:
            location_parts.append(str(column))

        location = ":".join(location_parts) if location_parts else ""

        if location:
            full_message = f"{location}: {message}"
        else:
            full_message = message

        super().__init__(full_message)

    def format_message(self) -> str:
        """Format validation error with file location."""
        from rich.text import Text

        text = Text()

        if self.file:
            text.append(self.file, style="bold blue")
            if self.line is not None:
                text.append(f":{self.line}", style="bold blue")
                if self.column is not None:
                    text.append(f":{self.column}", style="bold blue")
            text.append(": ", style="bold blue")

        text.append("Error: ", style="bold red")
        text.append(self.message, style="red")

        if self.hint:
            text.append(f"\n💡 {self.hint}", style="dim cyan")

        return str(text)


class ConfigurationError(CLIError):
    """Error for configuration issues."""

    pass


class FileNotFoundError(CLIError):
    """Error for missing files."""

    def __init__(self, file_path: str, hint: str | None = None):
        message = f"File not found: {file_path}"
        super().__init__(message, hint=hint or "Check that the file exists and the path is correct")


@contextmanager
def handle_cli_error(show_traceback: bool = False):
    """Context manager for consistent error handling.

    Args:
        show_traceback: Whether to show full traceback on unexpected errors
    """
    try:
        yield
    except CLIError:
        raise  # Re-raise CLI errors as-is
    except click.ClickException:
        raise  # Re-raise Click exceptions as-is
    except KeyboardInterrupt:
        console.print("\n❌ Operation cancelled by user", style="yellow")
        raise click.Abort()
    except Exception as e:
        if show_traceback:
            raise CLIError(f"Unexpected error: {e}") from e
        else:
            raise CLIError(f"Unexpected error: {e}")


def format_error_summary(errors: list[Exception]) -> str:
    """Format a summary of multiple errors."""
    if not errors:
        return ""

    from rich.text import Text

    text = Text(f"Found {len(errors)} error(s):\n", style="bold red")

    for i, error in enumerate(errors, 1):
        text.append(f"{i}. ", style="red")
        if isinstance(error, CLIError):
            text.append(str(error.message), style="red")
        else:
            text.append(str(error), style="red")
        text.append("\n")

    return str(text)
