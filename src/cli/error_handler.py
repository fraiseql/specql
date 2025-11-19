import traceback
from datetime import datetime
from pathlib import Path

import click


class ReverseEngineeringError(Exception):
    """Base exception for reverse engineering errors"""

    pass


class ParsingError(ReverseEngineeringError):
    """Error during source code parsing"""

    pass


class MappingError(ReverseEngineeringError):
    """Error during AST to SpecQL mapping"""

    pass


class ValidationError(ReverseEngineeringError):
    """Error during output validation"""

    pass


class ErrorHandler:
    """Centralized error handling for CLI"""

    @staticmethod
    def handle_error(
        error: Exception, file_path: str, fail_fast: bool = False, verbose: bool = False
    ) -> bool:
        """Handle error during processing

        Returns:
            bool: True if processing should continue, False if should stop
        """

        if isinstance(error, ParsingError):
            click.echo(f"✗ Parsing error in {file_path}:", err=True)
            click.echo(f"  {error}", err=True)
        elif isinstance(error, MappingError):
            click.echo(f"✗ Mapping error in {file_path}:", err=True)
            click.echo(f"  {error}", err=True)
        elif isinstance(error, ValidationError):
            click.echo(f"✗ Validation error in {file_path}:", err=True)
            click.echo(f"  {error}", err=True)
        else:
            click.echo(f"✗ Unexpected error in {file_path}:", err=True)
            click.echo(f"  {type(error).__name__}: {error}", err=True)

        if verbose:
            click.echo("\nFull traceback:", err=True)
            traceback.print_exc()

        # Log to error log file
        ErrorHandler._log_error(file_path, error)

        return not fail_fast

    @staticmethod
    def _log_error(file_path: str, error: Exception):
        """Log error to file for later review"""
        error_log = Path("~/.specql/error.log").expanduser()
        error_log.parent.mkdir(exist_ok=True)

        with error_log.open("a") as f:
            f.write(f"\n[{datetime.now()}] {file_path}\n")
            f.write(f"{type(error).__name__}: {error}\n")
            traceback.print_exc(file=f)
