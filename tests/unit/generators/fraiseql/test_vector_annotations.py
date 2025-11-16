"""Tests for FraiseQL vector field annotations"""

import pytest
from src.generators.fraiseql.fraiseql_annotator import FraiseQLAnnotator
from src.core.ast_models import EntityDefinition


class TestVectorFieldAnnotations:
    """Test FraiseQL annotations for vector columns"""

    @pytest.fixture
    def entity_with_vectors(self):
        entity = EntityDefinition(name="Document", schema="content")
        entity.features = ["semantic_search", "full_text_search"]
        return entity

    def test_embedding_column_annotation(self, entity_with_vectors):
        """Test embedding column gets proper FraiseQL annotation"""
        # Arrange
        annotator = FraiseQLAnnotator()

        # Act
        result = annotator.annotate_vector_column(entity_with_vectors)

        # Assert
        assert "COMMENT ON COLUMN" in result
        assert "tv_document.embedding" in result
        assert "@fraiseql:field" in result
        assert "name: embedding" in result
        assert "type: [Float!]" in result  # Vector as float array

    def test_search_vector_column_annotation(self, entity_with_vectors):
        """Test search_vector gets proper annotation"""
        # Arrange
        annotator = FraiseQLAnnotator()

        # Act
        result = annotator.annotate_fulltext_column(entity_with_vectors)

        # Assert
        assert "COMMENT ON COLUMN" in result
        assert "tv_document.search_vector" in result
        assert "@fraiseql:field" in result
        assert "name: searchVector" in result

    def test_no_custom_query_annotations_when_functions_disabled(self):
        """Test no @fraiseql:query when using native operators"""
        # Arrange
        entity = EntityDefinition(name="Document", schema="content")
        entity.features = ["semantic_search"]
        entity.search_functions = False
        annotator = FraiseQLAnnotator()

        # Act
        result = annotator.generate_annotations(entity)

        # Assert
        # Should NOT have custom query annotations
        assert "@fraiseql:query" not in result
        assert "searchDocumentByEmbedding" not in result
