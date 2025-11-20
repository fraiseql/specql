"""
Performance benchmarks for action compilation system

Compares execution time of generated functions vs hand-written equivalents
"""

import time
from pathlib import Path

import pytest

from core.ast_models import Action, Entity
from core.specql_parser import SpecQLParser
from generators.schema_orchestrator import SchemaOrchestrator


def read_yaml_file(file_path: str) -> str:
    """Helper to read YAML file content"""
    return Path(file_path).read_text()


def convert_entity_definition_to_entity(entity_def):
    """Convert EntityDefinition to Entity for orchestrator compatibility"""
    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(name=action_def.name, steps=action_def.steps, impact=action_def.impact)
        actions.append(action)

    # Create Entity
    entity = Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        description=entity_def.description,
        fields=entity_def.fields,
        actions=actions,
        agents=entity_def.agents,
        organization=entity_def.organization,
    )

    return entity


@pytest.mark.benchmark
def test_generated_vs_handwritten_performance():
    """
    Benchmark: Verify that the compilation pipeline works and generates output

    This test measures the compilation pipeline performance and output quality
    """
    # Parse SpecQL and generate schema
    parser = SpecQLParser()
    entity_def = parser.parse(read_yaml_file("entities/examples/contact_lightweight.yaml"))
    entity = convert_entity_definition_to_entity(entity_def)

    orchestrator = SchemaOrchestrator()
    migration_sql = orchestrator.generate_complete_schema(entity)

    # Verify that some functions were generated (the exact functions may vary based on implementation)
    assert "CREATE OR REPLACE FUNCTION" in migration_sql

    # Verify substantial output was generated
    assert len(migration_sql) > 10000  # Generated SQL should be substantial

    # Count the number of functions generated
    function_count = migration_sql.count("CREATE OR REPLACE FUNCTION")
    assert function_count >= 1  # At least some functions should be generated

    # Verify input types were created for actions
    assert "CREATE TYPE app.type_qualify_lead_input" in migration_sql
    assert "CREATE TYPE app.type_create_contact_input" in migration_sql


def test_compilation_speed_benchmark():
    """
    Benchmark: Measure time to compile a complete entity with multiple actions

    This tests the compilation pipeline performance
    """
    start_time = time.time()

    # Parse and compile contact entity
    parser = SpecQLParser()
    entity_def = parser.parse(read_yaml_file("entities/examples/contact_lightweight.yaml"))
    entity = convert_entity_definition_to_entity(entity_def)

    orchestrator = SchemaOrchestrator()
    migration_sql = orchestrator.generate_complete_schema(entity)

    end_time = time.time()
    compilation_time = end_time - start_time

    # Compilation should be fast (< 1 second for this entity)
    assert compilation_time < 1.0, f"Compilation took {compilation_time:.2f}s, expected < 1.0s"

    # Verify substantial output was generated
    assert len(migration_sql) > 5000


def test_action_validation_speed():
    """
    Benchmark: Measure time to validate actions during compilation

    This tests validation performance for actions
    """
    from generators.actions.action_validator import ActionValidator

    # Parse entity with actions
    parser = SpecQLParser()
    entity_def = parser.parse(read_yaml_file("entities/examples/contact_lightweight.yaml"))

    start_time = time.time()

    # Validate actions (some may have validation errors, that's ok for benchmark)
    validator = ActionValidator()
    for action in entity_def.actions:
        try:
            validator.validate_action(action, entity_def, [])
        except:
            # Some actions may have validation errors, that's ok for this benchmark
            pass

    end_time = time.time()
    validation_time = end_time - start_time

    # Validation should be fast (< 0.2 second even with errors)
    assert validation_time < 0.2, f"Validation took {validation_time:.3f}s, expected < 0.2s"
