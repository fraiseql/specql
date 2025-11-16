"""Integration test for vector configuration system"""

import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.schema.vector_generator import VectorGenerator


class TestVectorConfigIntegration:
    """Test complete vector configuration flow"""

    @pytest.fixture
    def parser(self):
        return SpecQLParser()

    @pytest.fixture
    def generator(self):
        return VectorGenerator()

    def test_yaml_to_sql_with_search_functions_enabled(self, parser, generator):
        """Test YAML with search_functions: true generates functions"""
        yaml_content = """
entity: Document
schema: content
features:
  - semantic_search
vector_config:
  search_functions: true

fields:
  title: text!
  content: text
"""

        entity = parser.parse(yaml_content)
        sql = generator.generate(entity)

        # Should generate columns, indexes, AND functions
        assert "embedding vector(384)" in sql
        assert "CREATE INDEX" in sql
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "search_document_by_embedding" in sql

    def test_yaml_to_sql_with_search_functions_disabled(self, parser, generator):
        """Test YAML with search_functions: false skips functions"""
        yaml_content = """
entity: Document
schema: content
features:
  - semantic_search
vector_config:
  search_functions: false

fields:
  title: text!
  content: text
"""

        entity = parser.parse(yaml_content)
        sql = generator.generate(entity)

        # Should generate columns and indexes, but NOT functions
        assert "embedding vector(384)" in sql
        assert "CREATE INDEX" in sql
        assert "CREATE OR REPLACE FUNCTION" not in sql
        assert "search_document_by_embedding" not in sql

    def test_yaml_to_sql_default_behavior(self, parser, generator):
        """Test YAML without vector_config defaults to generating functions"""
        yaml_content = """
entity: Document
schema: content
features:
  - semantic_search

fields:
  title: text!
  content: text
"""

        entity = parser.parse(yaml_content)
        sql = generator.generate(entity)

        # Should generate everything (backward compatibility)
        assert "embedding vector(384)" in sql
        assert "CREATE INDEX" in sql
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "search_document_by_embedding" in sql

    def test_no_vector_features_no_generation(self, parser, generator):
        """Test entity without semantic_search generates nothing"""
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text!
  name: text
"""

        entity = parser.parse(yaml_content)
        sql = generator.generate(entity)

        # Should generate nothing
        assert sql == ""
