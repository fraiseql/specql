"""End-to-end tests for translation table generation"""

from cli.generate import convert_entity_definition_to_entity
from core.specql_parser import SpecQLParser
from generators.schema_orchestrator import SchemaOrchestrator


def test_translation_table_e2e():
    """End-to-end test: YAML → DDL with translation tables"""
    yaml_content = """
entity: Manufacturer
schema: catalog
fields:
  code: text
  name: text
  description: text
translations:
  enabled: true
  fields: [name, description]
"""

    # Parse YAML to entity definition
    parser = SpecQLParser()
    entity_def = parser.parse(yaml_content)

    print(f"DEBUG: entity_def.translations = {entity_def.translations}")

    # Convert to Entity for orchestrator
    entity = convert_entity_definition_to_entity(entity_def)

    # Generate DDL using schema orchestrator
    orchestrator = SchemaOrchestrator()
    output = orchestrator.generate_complete_schema(entity)

    # Should include main table
    assert "CREATE TABLE catalog.tb_manufacturer" in output

    # Should include translation table
    assert "CREATE TABLE catalog.tl_manufacturer" in output

    # Should include helper functions
    assert "get_manufacturer_name" in output
    assert "get_manufacturer_description" in output
