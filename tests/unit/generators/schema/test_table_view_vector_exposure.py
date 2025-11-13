"""Tests for vector column exposure in table views"""

import pytest
from src.generators.schema.table_view_generator import TableViewGenerator
from src.core.ast_models import EntityDefinition, FieldDefinition, TableViewConfig, TableViewMode


class TestVectorColumnExposure:
    """Test that vector columns are exposed in tv_ table views"""

    @pytest.fixture
    def entity_with_vectors(self):
        entity = EntityDefinition(
            name="Document",
            schema="content",
            fields={
                "title": FieldDefinition(name="title", type_name="text"),
                "content": FieldDefinition(name="content", type_name="text"),
            },
            table_views=TableViewConfig(mode=TableViewMode.FORCE)  # Force table view generation
        )
        # Mark that this entity has vector features enabled
        entity.features = ["semantic_search", "full_text_search"]
        return entity

    def test_tv_includes_vector_column(self, entity_with_vectors):
        """Test tv_ table includes embedding column"""
        # Arrange
        generator = TableViewGenerator(entity_with_vectors, {})

        # Act
        result = generator.generate_schema()

        # Assert
        # tv_ table should have embedding column
        assert "embedding vector(384)" in result

    def test_tv_includes_search_vector_column(self, entity_with_vectors):
        """Test tv_ table includes search_vector column"""
        # Arrange
        generator = TableViewGenerator(entity_with_vectors, {})

        # Act
        result = generator.generate_schema()

        # Assert
        # tv_ table should have search_vector column
        assert "search_vector tsvector" in result

    def test_refresh_function_copies_vector_columns(self, entity_with_vectors):
        """Test refresh function copies vector columns from tb_ to tv_"""
        # Arrange
        generator = TableViewGenerator(entity_with_vectors, {})

        # Act
        result = generator.generate_schema()

        # Assert
        # Refresh function should SELECT vector columns
        assert "base.embedding" in result
        assert "base.search_vector" in result

    def test_vector_columns_not_in_jsonb(self, entity_with_vectors):
        """Test vector columns are NOT in JSONB data (too large)"""
        # Arrange
        generator = TableViewGenerator(entity_with_vectors, {})

        # Act
        result = generator.generate_schema()

        # Assert
        # JSONB should NOT include vector columns (they're separate columns)
        jsonb_section = result[result.find("jsonb_build_object"):result.find("AS data")]
        assert "'embedding'" not in jsonb_section
        assert "'search_vector'" not in jsonb_section