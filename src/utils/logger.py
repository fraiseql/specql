"""
Centralized logging framework for SpecQL

Provides structured logging with contextual information:
- Entity name
- File path
- Operation type
- Team/component identifier

Usage:
    from src.utils.logger import get_logger, LogContext

    # Basic usage
    logger = get_logger(__name__)
    logger.info("Processing entity")

    # With context
    context = LogContext(
        entity_name="Contact",
        file_path="entities/contact.yaml",
        operation="parse"
    )
    logger = get_logger(__name__, context)
    logger.debug("Parsing YAML content")
    logger.info("Entity parsed successfully")
    logger.warning("Field has deprecated type")
    logger.error("Validation failed", exc_info=True)
"""

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class LogContext:
    """Context information for structured logging"""

    entity_name: Optional[str] = None
    file_path: Optional[str] = None
    operation: Optional[str] = None
    schema: Optional[str] = None
    action_name: Optional[str] = None
    team: Optional[str] = None  # Team A-E identifier
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for logging"""
        context = {}
        if self.entity_name:
            context["entity"] = self.entity_name
        if self.file_path:
            context["file"] = self.file_path
        if self.operation:
            context["operation"] = self.operation
        if self.schema:
            context["schema"] = self.schema
        if self.action_name:
            context["action"] = self.action_name
        if self.team:
            context["team"] = self.team
        context.update(self.extra)
        return context

    def format_prefix(self) -> str:
        """Format context as a log prefix"""
        parts = []
        if self.team:
            parts.append(f"[{self.team}]")
        if self.entity_name:
            parts.append(f"[{self.entity_name}]")
        if self.operation:
            parts.append(f"[{self.operation}]")
        if self.file_path:
            parts.append(f"({Path(self.file_path).name})")
        return " ".join(parts) if parts else ""


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that includes context in log messages"""

    def __init__(self, logger: logging.Logger, context: Optional[LogContext] = None):
        super().__init__(logger, {})
        self.context = context or LogContext()

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Add context to log message"""
        prefix = self.context.format_prefix()
        if prefix:
            msg = f"{prefix} {msg}"

        # Add context to extra
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.context.to_dict())

        return msg, kwargs


class SpecQLFormatter(logging.Formatter):
    """Custom formatter for SpecQL logs"""

    # Color codes for terminal output
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def __init__(self, use_colors: bool = True, verbose: bool = False):
        """
        Initialize formatter

        Args:
            use_colors: Whether to use ANSI color codes
            verbose: Whether to include detailed information (timestamp, module)
        """
        self.use_colors = use_colors and sys.stderr.isatty()
        self.verbose = verbose

        if verbose:
            fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
        else:
            fmt = "[%(levelname)s] %(message)s"
            datefmt = None

        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors"""
        if self.use_colors:
            levelname = record.levelname
            color = self.COLORS.get(levelname, self.COLORS["RESET"])
            record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


# Global logging configuration
_logging_configured = False
_default_level = logging.INFO
_verbose_mode = False


def configure_logging(
    level: int = logging.INFO,
    verbose: bool = False,
    use_colors: bool = True,
    format_style: str = "auto",
) -> None:
    """
    Configure global logging settings

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        verbose: Enable verbose output (timestamps, module names)
        use_colors: Enable colored output for terminals
        format_style: Formatting style ('auto', 'simple', 'verbose')
    """
    global _logging_configured, _default_level, _verbose_mode

    if format_style == "auto":
        verbose = verbose or level == logging.DEBUG
    elif format_style == "verbose":
        verbose = True

    _default_level = level
    _verbose_mode = verbose

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add console handler with formatter
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(SpecQLFormatter(use_colors=use_colors, verbose=verbose))
    root_logger.addHandler(console_handler)

    _logging_configured = True


def get_logger(
    name: str,
    context: Optional[LogContext] = None,
    level: Optional[int] = None,
) -> logging.LoggerAdapter:
    """
    Get a context-aware logger

    Args:
        name: Logger name (typically __name__)
        context: Optional context information
        level: Optional logging level override

    Returns:
        Logger adapter with context support

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")

        >>> context = LogContext(entity_name="Contact", operation="parse")
        >>> logger = get_logger(__name__, context)
        >>> logger.debug("Parsing fields")
    """
    # Ensure logging is configured
    if not _logging_configured:
        configure_logging()

    # Get base logger
    base_logger = logging.getLogger(name)

    # Set level if specified
    if level is not None:
        base_logger.setLevel(level)

    # Wrap with context adapter
    return ContextAdapter(base_logger, context)


def get_team_logger(
    team: str,
    module_name: str,
    context: Optional[LogContext] = None,
) -> logging.LoggerAdapter:
    """
    Get a team-specific logger

    Args:
        team: Team identifier (e.g., "Team A", "Parser", "Schema Gen")
        module_name: Module name (typically __name__)
        context: Optional context information

    Returns:
        Logger adapter with team context

    Examples:
        >>> logger = get_team_logger("Team A", __name__)
        >>> logger.info("Parsing entity")

        >>> context = LogContext(entity_name="Contact")
        >>> logger = get_team_logger("Team B", __name__, context)
        >>> logger.debug("Generating schema")
    """
    if context is None:
        context = LogContext()
    context.team = team
    return get_logger(module_name, context)


# Convenience functions for common logging patterns

def log_operation_start(
    logger: logging.LoggerAdapter,
    operation: str,
    **kwargs: Any,
) -> None:
    """Log the start of an operation"""
    details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    msg = f"Starting {operation}"
    if details:
        msg += f" ({details})"
    logger.info(msg)


def log_operation_complete(
    logger: logging.LoggerAdapter,
    operation: str,
    **kwargs: Any,
) -> None:
    """Log the completion of an operation"""
    details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    msg = f"Completed {operation}"
    if details:
        msg += f" ({details})"
    logger.info(msg)


def log_operation_error(
    logger: logging.LoggerAdapter,
    operation: str,
    error: Exception,
    **kwargs: Any,
) -> None:
    """Log an operation error"""
    details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    msg = f"Failed {operation}: {error}"
    if details:
        msg += f" ({details})"
    logger.error(msg, exc_info=True)


def log_validation_error(
    logger: logging.LoggerAdapter,
    field: str,
    error: str,
    **kwargs: Any,
) -> None:
    """Log a validation error"""
    logger.error(f"Validation error in {field}: {error}", extra=kwargs)


def log_milestone(
    logger: logging.LoggerAdapter,
    milestone: str,
    **kwargs: Any,
) -> None:
    """Log a processing milestone"""
    details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    msg = f"Milestone: {milestone}"
    if details:
        msg += f" ({details})"
    logger.info(msg)
