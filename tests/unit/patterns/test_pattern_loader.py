"""
Unit tests for pattern loader functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.patterns.pattern_loader import PatternLoader
from src.patterns.pattern_models import PatternDefinition, PatternParameter


class TestPatternLoader:
    """Test PatternLoader functionality"""

    def test_init_with_default_path(self):
        """Test initialization with default stdlib path"""
        loader = PatternLoader()
        expected_path = Path(__file__).parent.parent.parent.parent / "stdlib" / "actions"
        assert loader.stdlib_path == expected_path

    def test_init_with_custom_path(self):
        """Test initialization with custom path"""
        custom_path = Path("/tmp/custom")
        loader = PatternLoader(custom_path)
        assert loader.stdlib_path == custom_path

    def test_load_pattern_success(self):
        """Test loading a valid pattern"""
        # Create a mock pattern file
        mock_yaml = """
pattern: test_pattern
version: 1.0
description: Test pattern
author: Test Author

parameters:
  - name: param1
    type: string
    required: true
  - name: param2
    type: integer
    default: 42

template: |
  steps:
    - raw_sql: "SELECT 1"
"""

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=mock_yaml)),
        ):
            loader = PatternLoader(Path("/tmp"))
            pattern = loader.load_pattern("test/test_pattern")

            assert pattern.name == "test_pattern"
            assert pattern.version == "1.0"
            assert pattern.description == "Test pattern"
            assert len(pattern.parameters) == 2
            assert pattern.parameters[0].name == "param1"
            assert pattern.parameters[0].required is True
            assert pattern.parameters[1].name == "param2"
            assert pattern.parameters[1].default == 42

    def test_load_pattern_file_not_found(self):
        """Test loading a pattern that doesn't exist"""
        loader = PatternLoader(Path("/tmp"))
        with pytest.raises(FileNotFoundError):
            loader.load_pattern("nonexistent/pattern")

    def test_load_pattern_invalid_yaml(self):
        """Test loading pattern with invalid YAML"""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid: yaml: content: [")),
        ):
            loader = PatternLoader(Path("/tmp"))
            with pytest.raises(ValueError):
                loader.load_pattern("test/invalid")

    def test_validate_config_valid(self):
        """Test validating valid configuration"""
        param = PatternParameter(name="test", type="string", required=True)
        pattern = PatternDefinition(
            name="test",
            version="1.0",
            description="test",
            author="test",
            parameters=[param],
            template="",
        )

        loader = PatternLoader()
        errors = loader.validate_config(pattern, {"test": "value"})
        assert errors == []

    def test_validate_config_missing_required(self):
        """Test validating config with missing required parameter"""
        param = PatternParameter(name="test", type="string", required=True)
        pattern = PatternDefinition(
            name="test",
            version="1.0",
            description="test",
            author="test",
            parameters=[param],
            template="",
        )

        loader = PatternLoader()
        errors = loader.validate_config(pattern, {})
        assert len(errors) == 1
        assert "Missing required parameter 'test'" in errors[0]

    def test_validate_config_wrong_type(self):
        """Test validating config with wrong parameter type"""
        param = PatternParameter(name="test", type="integer", required=True)
        pattern = PatternDefinition(
            name="test",
            version="1.0",
            description="test",
            author="test",
            parameters=[param],
            template="",
        )

        loader = PatternLoader()
        errors = loader.validate_config(pattern, {"test": "not_an_int"})
        assert len(errors) == 1
        assert "invalid value" in errors[0]

    def test_expand_pattern_success(self):
        """Test successful pattern expansion"""
        template = """
steps:
  - raw_sql: "SELECT '{{ entity.name }}' as entity_name"
  - raw_sql: "SELECT '{{ config.param1 }}' as param_value"
"""

        pattern = PatternDefinition(
            name="test",
            version="1.0",
            description="test",
            author="test",
            parameters=[],
            template=template,
        )

        # Mock entity
        entity = Mock()
        entity.name = "TestEntity"
        entity.schema = "test_schema"

        loader = PatternLoader()
        result = loader.expand_pattern(pattern, entity, {"param1": "test_value"})

        assert result.pattern_name == "test"
        assert result.config == {"param1": "test_value"}
        assert len(result.expanded_steps) == 2
        assert result.expanded_steps[0]["raw_sql"] == "SELECT 'TestEntity' as entity_name"
        assert result.expanded_steps[1]["raw_sql"] == "SELECT 'test_value' as param_value"

    def test_expand_pattern_invalid_config(self):
        """Test pattern expansion with invalid config"""
        param = PatternParameter(name="required_param", type="string", required=True)
        pattern = PatternDefinition(
            name="test",
            version="1.0",
            description="test",
            author="test",
            parameters=[param],
            template="",
        )

        entity = Mock()
        loader = PatternLoader()

        with pytest.raises(ValueError) as exc_info:
            loader.expand_pattern(pattern, entity, {})

        assert "Invalid pattern configuration" in str(exc_info.value)

    def test_list_available_patterns(self):
        """Test listing available patterns"""
        # Mock directory structure
        mock_files = [
            Mock(is_file=lambda: True),
            Mock(is_file=lambda: True),
            Mock(is_file=lambda: True),
        ]

        # Mock relative_to to return pattern paths
        mock_files[0].relative_to = Mock(return_value=Path("state_machine/transition.yaml"))
        mock_files[1].relative_to = Mock(return_value=Path("multi_entity/coordinated_update.yaml"))
        mock_files[2].relative_to = Mock(return_value=Path("batch/bulk_operation.yaml"))

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.rglob", return_value=mock_files),
        ):
            loader = PatternLoader()
            patterns = loader.list_available_patterns()

            assert len(patterns) == 3
            assert "state_machine/transition" in patterns
            assert "multi_entity/coordinated_update" in patterns
            assert "batch/bulk_operation" in patterns


# Helper for mocking file operations
def mock_open(read_data=""):
    """Mock for built-in open function"""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.__enter__.return_value.read.return_value = read_data
    return mock
