"""
Tests for logging framework
"""

import logging
from io import StringIO

from utils.logger import (
    LogContext,
    configure_logging,
    get_logger,
    get_team_logger,
    log_milestone,
    log_operation_complete,
    log_operation_error,
    log_operation_start,
    log_validation_error,
)


class TestLogContext:
    """Tests for LogContext"""

    def test_to_dict_all_fields(self):
        """Test to_dict with all fields"""
        context = LogContext(
            entity_name="Contact",
            file_path="entities/contact.yaml",
            operation="parse",
            schema="crm",
            action_name="create_contact",
            team="Parser",
            extra={"custom": "value"},
        )

        result = context.to_dict()

        assert result["entity"] == "Contact"
        assert result["file"] == "entities/contact.yaml"
        assert result["operation"] == "parse"
        assert result["schema"] == "crm"
        assert result["action"] == "create_contact"
        assert result["team"] == "Parser"
        assert result["custom"] == "value"

    def test_to_dict_partial_fields(self):
        """Test to_dict with only some fields"""
        context = LogContext(entity_name="Contact", operation="parse")

        result = context.to_dict()

        assert result["entity"] == "Contact"
        assert result["operation"] == "parse"
        assert "file" not in result
        assert "schema" not in result

    def test_format_prefix_all_fields(self):
        """Test format_prefix with all fields"""
        context = LogContext(
            entity_name="Contact",
            file_path="entities/contact.yaml",
            operation="parse",
            team="Parser",
        )

        prefix = context.format_prefix()

        assert "[Parser]" in prefix
        assert "[Contact]" in prefix
        assert "[parse]" in prefix
        assert "(contact.yaml)" in prefix

    def test_format_prefix_minimal(self):
        """Test format_prefix with minimal fields"""
        context = LogContext(entity_name="Contact")

        prefix = context.format_prefix()

        assert "[Contact]" in prefix
        assert prefix == "[Contact]"

    def test_format_prefix_empty(self):
        """Test format_prefix with no fields"""
        context = LogContext()

        prefix = context.format_prefix()

        assert prefix == ""


class TestLoggingConfiguration:
    """Tests for logging configuration"""

    def test_configure_logging_default(self):
        """Test default logging configuration"""
        configure_logging()

        logger = logging.getLogger()
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_configure_logging_debug(self):
        """Test debug logging configuration"""
        configure_logging(level=logging.DEBUG, verbose=True)

        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

    def test_configure_logging_quiet(self):
        """Test quiet logging configuration"""
        configure_logging(level=logging.ERROR)

        logger = logging.getLogger()
        assert logger.level == logging.ERROR


class TestGetLogger:
    """Tests for get_logger"""

    def test_get_logger_basic(self):
        """Test basic logger creation"""
        logger = get_logger(__name__)

        assert logger is not None
        assert logger.logger.name == __name__

    def test_get_logger_with_context(self):
        """Test logger with context"""
        context = LogContext(entity_name="Contact", operation="parse")
        logger = get_logger(__name__, context)

        assert logger is not None
        assert logger.context.entity_name == "Contact"
        assert logger.context.operation == "parse"

    def test_get_logger_with_level(self):
        """Test logger with custom level"""
        logger = get_logger(__name__, level=logging.WARNING)

        assert logger.logger.level == logging.WARNING


class TestGetTeamLogger:
    """Tests for get_team_logger"""

    def test_get_team_logger_basic(self):
        """Test basic team logger creation"""
        logger = get_team_logger("Parser", __name__)

        assert logger is not None
        assert logger.context.team == "Parser"

    def test_get_team_logger_with_context(self):
        """Test team logger with additional context"""
        context = LogContext(entity_name="Contact", operation="parse")
        logger = get_team_logger("Schema", __name__, context)

        assert logger.context.team == "Schema"
        assert logger.context.entity_name == "Contact"
        assert logger.context.operation == "parse"


class TestLoggingHelpers:
    """Tests for logging helper functions"""

    def setup_method(self):
        """Set up test fixtures"""
        # Configure logging to capture output
        configure_logging(level=logging.DEBUG)
        self.logger = get_logger(__name__)

    def test_log_operation_start(self):
        """Test log_operation_start"""
        # This should not raise an exception
        log_operation_start(self.logger, "parsing", entity="Contact")

    def test_log_operation_complete(self):
        """Test log_operation_complete"""
        # This should not raise an exception
        log_operation_complete(self.logger, "parsing", entity="Contact", count=5)

    def test_log_operation_error(self):
        """Test log_operation_error"""
        error = ValueError("Test error")
        # This should not raise an exception
        log_operation_error(self.logger, "parsing", error, entity="Contact")

    def test_log_validation_error(self):
        """Test log_validation_error"""
        # This should not raise an exception
        log_validation_error(self.logger, "email", "Invalid format", entity="Contact")

    def test_log_milestone(self):
        """Test log_milestone"""
        # This should not raise an exception
        log_milestone(self.logger, "Schema generated", entity="Contact", files=3)


class TestLoggingIntegration:
    """Integration tests for logging"""

    def test_logging_with_context_adapter(self):
        """Test that context is properly included in log messages"""
        # Create logger with context
        context = LogContext(entity_name="Contact", operation="parse", team="Parser")
        test_logger = get_team_logger("Parser", __name__, context)

        # Set up a string handler to capture log output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.setLevel(logging.INFO)

        # Add handler to the logger's underlying logger
        test_logger.logger.addHandler(handler)
        test_logger.logger.setLevel(logging.INFO)

        # Log a message
        test_logger.info("Test message")

        # Get the logged output
        output = stream.getvalue()

        # Verify context is in the message
        assert "Parser" in output
        assert "Contact" in output
        assert "parse" in output
        assert "Test message" in output

        # Clean up
        test_logger.logger.removeHandler(handler)

    def test_debug_logging_trace_execution(self):
        """Test DEBUG level for trace execution"""
        configure_logging(level=logging.DEBUG)
        logger = get_logger(__name__)

        # Should not raise
        logger.debug("Tracing execution step")

    def test_info_logging_milestones(self):
        """Test INFO level for milestones"""
        configure_logging(level=logging.INFO)
        logger = get_logger(__name__)

        # Should not raise
        logger.info("Milestone reached: Schema generated")

    def test_warning_logging_issues(self):
        """Test WARNING level for issues"""
        configure_logging(level=logging.INFO)
        logger = get_logger(__name__)

        # Should not raise
        logger.warning("Deprecated field type detected")

    def test_error_logging_failures(self):
        """Test ERROR level for failures"""
        configure_logging(level=logging.INFO)
        logger = get_logger(__name__)

        # Should not raise
        logger.error("Validation failed")
