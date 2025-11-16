"""Integration test: Vector columns in tv_ tables"""

from src.generators.schema_orchestrator import SchemaOrchestrator
from src.core.specql_parser import SpecQLParser


def test_complete_vector_generation():
    """Test that vector columns flow through entire generation pipeline"""

    yaml_content = """
entity: Document
schema: content
fields:
  title: text!
  content: text
features:
  - semantic_search
  - full_text_search
table_views:
  mode: force
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    orchestrator = SchemaOrchestrator()
    files = orchestrator.generate_table_views([entity])

    # Find tv_ file
    tv_file = next(f for f in files if "tv_document" in f.name)
    content = tv_file.content

    # Verify vector columns in table definition
    assert "embedding vector(384)" in content
    assert "search_vector tsvector" in content

    # Verify indexes created
    assert "idx_tv_document_embedding_hnsw" in content
    assert "USING hnsw (embedding vector_cosine_ops)" in content
    assert "idx_tv_document_search_vector" in content
    assert "USING gin (search_vector)" in content

    # Verify refresh function copies columns
    assert "base.embedding" in content
    assert "base.search_vector" in content

    # Verify NOT in JSONB
    jsonb_start = content.find("jsonb_build_object")
    jsonb_end = content.find("AS data", jsonb_start)
    jsonb_section = content[jsonb_start:jsonb_end]
    assert "'embedding'" not in jsonb_section
    assert "'search_vector'" not in jsonb_section


def test_backward_compatibility_without_features():
    """Test entities without vector features don't get vector columns"""

    yaml_content = """
entity: Contact
schema: crm
fields:
  email: text!
table_views:
  mode: force
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    orchestrator = SchemaOrchestrator()
    files = orchestrator.generate_table_views([entity])

    tv_file = next(f for f in files if "tv_contact" in f.name)
    content = tv_file.content

    # Should NOT have vector columns
    assert "embedding vector" not in content
    assert "search_vector tsvector" not in content
