"""
Tests for framework defaults and configuration
"""

import pytest

from src.cli.framework_defaults import (
    get_framework_defaults,
    get_available_frameworks,
    apply_dev_mode_overrides,
    validate_framework_option,
    get_output_dir_for_framework,
)


class TestFrameworkDefaults:
    """Test framework defaults functionality"""

    def test_get_framework_defaults_fraiseql(self):
        """Test getting FraiseQL framework defaults"""
        defaults = get_framework_defaults("fraiseql")

        assert defaults["include_tv"] is True
        assert defaults["trinity_pattern"] is True
        assert defaults["audit_fields"] is True
        assert defaults["use_registry"] is True
        assert defaults["output_format"] == "hierarchical"

    def test_get_framework_defaults_django(self):
        """Test getting Django framework defaults"""
        defaults = get_framework_defaults("django")

        assert defaults["include_tv"] is False
        assert defaults["trinity_pattern"] is False
        assert defaults["use_registry"] is False
        assert defaults["output_format"] == "confiture"

    def test_get_available_frameworks(self):
        """Test getting all available frameworks"""
        frameworks = get_available_frameworks()

        assert "fraiseql" in frameworks
        assert "django" in frameworks
        assert "rails" in frameworks
        assert "prisma" in frameworks

        assert "PostgreSQL + FraiseQL GraphQL" in frameworks["fraiseql"]

    def test_validate_framework_option_valid(self):
        """Test validating valid framework options"""
        assert validate_framework_option("fraiseql") == "fraiseql"
        assert validate_framework_option("django") == "django"
        assert validate_framework_option("DJANGO") == "django"  # Case insensitive

    def test_validate_framework_option_invalid(self):
        """Test validating invalid framework options"""
        with pytest.raises(ValueError, match="Unknown framework 'invalid'"):
            validate_framework_option("invalid")

    def test_validate_framework_option_none(self):
        """Test validating None framework option returns default"""
        assert validate_framework_option(None) == "fraiseql"

    def test_apply_dev_mode_overrides(self):
        """Test applying development mode overrides"""
        original = {
            "include_tv": True,
            "use_registry": True,
            "output_format": "hierarchical",
            "output_dir": "migrations",
        }

        dev_overrides = apply_dev_mode_overrides(original)

        assert dev_overrides["include_tv"] is False
        assert dev_overrides["use_registry"] is False
        assert dev_overrides["output_format"] == "confiture"
        assert dev_overrides["output_dir"] == "db/schema"

    def test_get_output_dir_for_framework_fraiseql(self):
        """Test output directory for FraiseQL framework"""
        output_dir = get_output_dir_for_framework("fraiseql")
        assert output_dir == "migrations"

    def test_get_output_dir_for_framework_django(self):
        """Test output directory for Django framework"""
        output_dir = get_output_dir_for_framework("django")
        assert output_dir == "db/schema"

    def test_get_output_dir_for_framework_dev_mode(self):
        """Test output directory in development mode"""
        output_dir = get_output_dir_for_framework("fraiseql", dev_mode=True)
        assert output_dir == "db/schema"

    def test_get_output_dir_for_framework_custom(self):
        """Test custom output directory"""
        output_dir = get_output_dir_for_framework("fraiseql", custom_dir="custom/path")
        assert output_dir == "custom/path"
