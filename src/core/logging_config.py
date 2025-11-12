"""
Structured logging configuration for SpecQL.
"""

import logging
import sys


def setup_logging(level: str = "INFO", format: str = "json") -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format: Output format (json, text)
    """
    if format == "json":
        # For production: structured JSON logs
        try:
            import json_log_formatter

            formatter = json_log_formatter.JSONFormatter()
        except ImportError:
            # Fallback to basic JSON-like format if json_log_formatter not available
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
            )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
    else:
        # For development: human-readable logs
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)
