"""Tests for vector embedding generation"""

import pytest
from src.generators.schema.vector_generator import VectorGenerator
from src.core.ast_models import EntityDefinition


class TestVectorGeneration:
    """Test vector embedding column and index generation"""

    @pytest.fixture
    def generator(self):
        return VectorGenerator()

    @pytest.fixture
    def entity_with_vector(self):
        return EntityDefinition(
            name="Pattern",
            schema="specql_registry",
            features=["semantic_search"]
        )

    def test_add_embedding_column(self, generator, entity_with_vector):
        """Test embedding vector(384) column added"""
        # Act
        result = generator.generate_column(entity_with_vector)

        # Assert
        assert "ALTER TABLE specql_registry.tb_pattern ADD COLUMN embedding vector(384)" in result

    def test_hnsw_index_generation(self, generator, entity_with_vector):
        """Test HNSW index created for vector similarity search"""
        # Act
        result = generator.generate_index(entity_with_vector)

        # Assert
        assert "CREATE INDEX idx_tb_pattern_embedding_hnsw" in result
        assert "ON specql_registry.tb_pattern" in result
        assert "USING hnsw (embedding vector_cosine_ops)" in result
        assert "WITH (m = 16, ef_construction = 64)" in result

    def test_table_view_embedding_included(self, generator, entity_with_vector):
        """Test tv_ table also gets embedding column"""
        # Act
        result = generator.generate_tv_column(entity_with_vector)

        # Assert
        assert "ALTER TABLE specql_registry.tv_pattern ADD COLUMN embedding vector(384)" in result

    def test_similarity_search_function(self, generator, entity_with_vector):
        """Test similarity search helper function generated"""
        # Act
        result = generator.generate_search_function(entity_with_vector)

        # Assert
        assert "CREATE OR REPLACE FUNCTION specql_registry.search_pattern_by_embedding" in result
        assert "p_query_embedding vector(384)" in result
        assert "ORDER BY tv.embedding <=> p_query_embedding" in result
        assert "LIMIT p_limit" in result