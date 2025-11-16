"""Tests for configurable search function generation"""

import pytest
from src.generators.schema.vector_generator import VectorGenerator
from src.core.ast_models import EntityDefinition


class TestSearchFunctionConfiguration:
    """Test that search function generation is optional"""

    @pytest.fixture
    def entity_vectors_only(self):
        """Entity with vectors but no search functions"""
        entity = EntityDefinition(name="Doc", schema="content")
        entity.features = ["semantic_search"]
        entity.search_functions = False  # Disable search functions
        return entity

    @pytest.fixture
    def entity_with_functions(self):
        """Entity with vectors AND search functions"""
        entity = EntityDefinition(name="Doc", schema="content")
        entity.features = ["semantic_search"]
        entity.search_functions = True  # Enable search functions
        return entity

    def test_no_search_function_when_disabled(self, entity_vectors_only):
        """Test no search function generated when disabled"""
        # Arrange
        generator = VectorGenerator()

        # Act
        result = generator.generate(entity_vectors_only)

        # Assert
        assert "CREATE OR REPLACE FUNCTION" not in result
        assert "search_doc_by_embedding" not in result
        # But columns and indexes still generated
        assert "embedding vector(384)" in result
        assert "CREATE INDEX" in result

    def test_search_function_when_enabled(self, entity_with_functions):
        """Test search function generated when enabled"""
        # Arrange
        generator = VectorGenerator()

        # Act
        result = generator.generate(entity_with_functions)

        # Assert
        assert "CREATE OR REPLACE FUNCTION" in result
        assert "search_doc_by_embedding" in result

    def test_default_behavior_backward_compatible(self):
        """Test default behavior maintains backward compatibility"""
        # Arrange - no explicit search_functions config
        entity = EntityDefinition(name="Doc", schema="content")
        entity.features = ["semantic_search"]
        generator = VectorGenerator()

        # Act
        result = generator.generate(entity)

        # Assert - default should generate functions for backward compat
        assert "CREATE OR REPLACE FUNCTION" in result
