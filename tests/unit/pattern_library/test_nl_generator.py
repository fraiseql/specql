"""Unit tests for NL Pattern Generator."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.pattern_library.nl_generator import NLPatternGenerator


class TestNLPatternGenerator:
    """Test NL Pattern Generator functionality."""

    @pytest.fixture
    def mock_grok_provider(self):
        """Mock GrokProvider for testing."""
        mock_provider = Mock()
        mock_provider.call_json.return_value = {
            "name": "test_pattern",
            "category": "workflow",
            "description": "A test pattern for workflows",
            "parameters": {
                "entity": {
                    "type": "string",
                    "required": True,
                    "description": "Target entity name",
                }
            },
            "implementation": {
                "fields": [
                    {
                        "name": "pk_test_id",
                        "type": "integer",
                        "description": "Primary key",
                    },
                    {"name": "id", "type": "uuid", "description": "Unique identifier"},
                    {
                        "name": "identifier",
                        "type": "text",
                        "description": "Human-readable identifier",
                    },
                    {
                        "name": "created_at",
                        "type": "timestamp",
                        "description": "Creation timestamp",
                    },
                    {
                        "name": "updated_at",
                        "type": "timestamp",
                        "description": "Update timestamp",
                    },
                    {
                        "name": "status",
                        "type": "enum(draft,active)",
                        "default": "draft",
                        "description": "Status field",
                    },
                ],
                "actions": [
                    {
                        "name": "activate",
                        "steps": [
                            {"validate": "status = 'draft'"},
                            {"update": "SET status = 'active', updated_at = now()"},
                        ],
                    }
                ],
            },
        }
        mock_provider.close = Mock()
        return mock_provider

    @pytest.fixture
    def generator(self, mock_grok_provider):
        """Create generator with mocked Grok provider."""
        with patch(
            "src.pattern_library.nl_generator.GrokProvider",
            return_value=mock_grok_provider,
        ):
            gen = NLPatternGenerator(log_to_db=False)
            return gen

    def test_initialization(self, generator):
        """Test generator initialization."""
        assert generator.grok is not None
        assert generator.template is not None
        assert "SpecQL" in generator.template

    def test_generate_valid_pattern(self, generator, mock_grok_provider):
        """Test successful pattern generation."""
        description = "A simple approval workflow"

        pattern, confidence, message = generator.generate(description)

        assert isinstance(pattern, dict)
        assert "name" in pattern
        assert "category" in pattern
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert isinstance(message, str)

        # Verify Grok was called
        mock_grok_provider.call_json.assert_called_once()

    def test_generate_with_category_hint(self, generator, mock_grok_provider):
        """Test generation with category hint."""
        description = "Track user changes"
        category = "audit"

        generator.generate(description, category)

        # Verify category was passed to template
        call_args = mock_grok_provider.call_json.call_args[0][0]
        assert category in call_args

    def test_validation_valid_pattern(self, generator):
        """Test validation of a valid pattern."""
        valid_pattern = {
            "name": "test_pattern",
            "category": "workflow",
            "description": "A test pattern",
            "parameters": {"entity": {"type": "string", "required": True}},
            "implementation": {
                "fields": [
                    {"name": "id", "type": "uuid", "description": "Primary key"},
                    {
                        "name": "created_at",
                        "type": "timestamp",
                        "description": "Creation time",
                    },
                ],
                "actions": [
                    {"name": "create", "steps": [{"validate": "id IS NOT NULL"}]}
                ],
            },
        }

        is_valid, message = generator._validate_pattern(valid_pattern)

        assert is_valid is True
        assert "passed" in message.lower()

    def test_validation_missing_required_fields(self, generator):
        """Test validation fails for missing required fields."""
        invalid_pattern = {
            "name": "test_pattern"
            # Missing category, description, parameters, implementation
        }

        is_valid, message = generator._validate_pattern(invalid_pattern)

        assert is_valid is False
        assert "Missing fields" in message

    def test_validation_invalid_category(self, generator):
        """Test validation fails for invalid category."""
        invalid_pattern = {
            "name": "test_pattern",
            "category": "invalid_category",
            "description": "Test",
            "parameters": {"entity": {"type": "string"}},
            "implementation": {"fields": []},
        }

        is_valid, message = generator._validate_pattern(invalid_pattern)

        assert is_valid is False
        assert "Invalid category" in message

    def test_validation_invalid_field_names(self, generator):
        """Test validation fails for invalid field names."""
        invalid_pattern = {
            "name": "test_pattern",
            "category": "workflow",
            "description": "Test",
            "parameters": {"entity": {"type": "string"}},
            "implementation": {
                "fields": [
                    {"name": "InvalidName", "type": "text"}  # Should be snake_case
                ]
            },
        }

        is_valid, message = generator._validate_pattern(invalid_pattern)

        assert is_valid is False
        assert "snake_case" in message

    def test_validation_missing_implementation(self, generator):
        """Test validation fails when implementation lacks fields and actions."""
        invalid_pattern = {
            "name": "test_pattern",
            "category": "workflow",
            "description": "Test",
            "parameters": {"entity": {"type": "string"}},
            "implementation": {},  # Empty implementation
        }

        is_valid, message = generator._validate_pattern(invalid_pattern)

        assert is_valid is False
        assert "fields" in message and "actions" in message

    def test_confidence_scoring_complete_pattern(self, generator):
        """Test confidence scoring for a complete pattern."""
        complete_pattern = {
            "name": "approval_workflow",
            "category": "workflow",
            "description": "Two-stage approval workflow",
            "parameters": {
                "entity": {"type": "string", "required": True},
                "approver_role": {"type": "string"},
            },
            "implementation": {
                "fields": [
                    {"name": "pk_approval_id", "type": "integer"},
                    {"name": "id", "type": "uuid"},
                    {"name": "identifier", "type": "text"},
                    {"name": "created_at", "type": "timestamp"},
                    {"name": "updated_at", "type": "timestamp"},
                    {
                        "name": "approval_status",
                        "type": "enum(pending,approved,rejected)",
                    },
                ],
                "actions": [
                    {
                        "name": "approve",
                        "steps": [
                            {"validate": "approval_status = 'pending'"},
                            {"update": "SET approval_status = 'approved'"},
                        ],
                    }
                ],
            },
        }

        confidence = generator._score_confidence(
            complete_pattern, "approval workflow pattern"
        )

        assert confidence > 0.8  # Should be high for complete pattern

    def test_confidence_scoring_incomplete_pattern(self, generator):
        """Test confidence scoring for an incomplete pattern."""
        incomplete_pattern = {
            "name": "test",
            "category": "workflow",
            "description": "Test",
            "parameters": {},
            "implementation": {},
        }

        confidence = generator._score_confidence(incomplete_pattern, "some description")

        assert confidence < 0.5  # Should be low for incomplete pattern

    def test_save_pattern(self, generator):
        """Test saving pattern to database."""
        pattern = {
            "name": "test_pattern",
            "category": "workflow",
            "description": "Test pattern",
            "parameters": {"entity": {"type": "string", "required": True}},
            "implementation": {
                "fields": [{"name": "id", "type": "uuid", "description": "ID"}]
            },
        }

        with patch.dict("os.environ", {"SPECQL_DB_URL": "postgresql://test"}):
            with patch("psycopg.connect") as mock_connect:
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = (123,)  # Return tuple, not list
                mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
                mock_connect.return_value.__enter__.return_value = mock_conn

                pattern_id = generator.save_pattern(pattern, 0.85)

                assert pattern_id == 123
                mock_cursor.execute.assert_called_once()
                mock_conn.commit.assert_called_once()

    def test_save_pattern_no_db_url(self, generator):
        """Test save fails without DB URL."""
        pattern = {
            "name": "test",
            "category": "workflow",
            "description": "test",
            "parameters": {},
            "implementation": {},
        }

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="SPECQL_DB_URL"):
                generator.save_pattern(pattern, 0.8)

    def test_retry_on_validation_failure(self, generator, mock_grok_provider):
        """Test retry mechanism when validation fails."""
        # First call returns invalid pattern (missing required fields)
        # Second call returns valid pattern
        mock_grok_provider.call_json.side_effect = [
            {  # Invalid - missing description, parameters, implementation
                "name": "invalid",
                "category": "workflow",
            },
            {  # Valid on retry
                "name": "valid_pattern",
                "category": "workflow",
                "description": "Valid pattern for testing",
                "parameters": {
                    "entity": {
                        "type": "string",
                        "required": True,
                        "description": "Entity",
                    }
                },
                "implementation": {
                    "fields": [
                        {"name": "id", "type": "uuid", "description": "ID"},
                        {
                            "name": "created_at",
                            "type": "timestamp",
                            "description": "Created",
                        },
                    ]
                },
            },
        ]

        pattern, confidence, message = generator.generate(
            "test description", max_retries=2
        )

        assert pattern["name"] == "valid_pattern"
        assert mock_grok_provider.call_json.call_count == 2

    def test_max_retries_exceeded(self, generator, mock_grok_provider):
        """Test failure when max retries exceeded."""
        mock_grok_provider.call_json.return_value = {"invalid": "pattern"}

        with pytest.raises(RuntimeError, match="Failed to generate valid pattern"):
            generator.generate("test", max_retries=2)

    def test_template_not_found(self):
        """Test error when template file not found."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                NLPatternGenerator(log_to_db=False)
