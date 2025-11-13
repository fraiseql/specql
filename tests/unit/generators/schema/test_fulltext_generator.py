"""Tests for full-text search generation"""

import pytest
from src.generators.schema.fulltext_generator import FullTextGenerator
from src.core.ast_models import Entity, FieldDefinition


class TestFullTextSearch:
    """Test full-text search column and index generation"""

    @pytest.fixture
    def generator(self):
        return FullTextGenerator()

    @pytest.fixture
    def entity_with_text_fields(self):
        return Entity(
            name="Pattern",
            schema="specql_registry",
            fields={
                "pattern_name": FieldDefinition(name="pattern_name", type_name="text"),
                "description": FieldDefinition(name="description", type_name="text"),
                "category": FieldDefinition(name="category", type_name="text"),
            }
        )

    def test_add_search_vector_column(self, generator, entity_with_text_fields):
        """Test tsvector column added with GENERATED ALWAYS"""
        # Act
        result = generator.generate_column(entity_with_text_fields)

        # Assert
        assert "ALTER TABLE specql_registry.tb_pattern" in result
        assert "ADD COLUMN search_vector tsvector" in result
        assert "GENERATED ALWAYS AS" in result
        assert "to_tsvector('english'" in result
        assert "pattern_name" in result
        assert "description" in result
        assert "STORED" in result

    def test_gin_index_generation(self, generator, entity_with_text_fields):
        """Test GIN index created for full-text search"""
        # Act
        result = generator.generate_index(entity_with_text_fields)

        # Assert
        assert "CREATE INDEX idx_tb_pattern_search" in result
        assert "ON specql_registry.tb_pattern USING gin (search_vector)" in result

    def test_search_function_generation(self, generator, entity_with_text_fields):
        """Test full-text search function"""
        # Act
        result = generator.generate_search_function(entity_with_text_fields)

        # Assert
        assert "CREATE OR REPLACE FUNCTION specql_registry.search_pattern_by_text" in result
        assert "p_query TEXT" in result
        assert "WHERE tb.search_vector @@ websearch_to_tsquery('english', p_query)" in result
        assert "ts_rank(tb.search_vector" in result