"""
Integration tests for full action compilation pipeline
SpecQL YAML → SQL → Validation
"""

from pathlib import Path

from src.core.ast_models import Action, Entity
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator


def read_yaml_file(file_path: str) -> str:
    """Helper to read YAML file content"""
    return Path(file_path).read_text()


def convert_entity_definition_to_entity(entity_def):
    """Convert EntityDefinition to Entity for orchestrator compatibility"""
    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name, steps=action_def.steps, impact=action_def.impact
        )
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


def test_full_create_contact_compilation():
    """
    Full pipeline test:
    1. Parse SpecQL YAML
    2. Generate complete SQL migration
    3. Verify generated SQL contains expected components
    """
    # Parse SpecQL
    parser = SpecQLParser()
    entity_def = parser.parse(
        read_yaml_file("entities/examples/contact_lightweight.yaml")
    )
    entity = convert_entity_definition_to_entity(entity_def)

    # Generate complete schema
    orchestrator = SchemaOrchestrator()
    migration_sql = orchestrator.generate_complete_schema(entity)

    # Verify migration contains all expected components
    assert "CREATE SCHEMA IF NOT EXISTS app;" in migration_sql
    assert "CREATE TYPE app.mutation_result" in migration_sql
    assert "CREATE OR REPLACE FUNCTION app.log_and_return_mutation" in migration_sql

    # Verify table creation
    assert "CREATE TABLE crm.tb_contact" in migration_sql
    assert "pk_contact INTEGER GENERATED" in migration_sql
    assert "PRIMARY KEY" in migration_sql
    assert "tenant_id UUID NOT NULL" in migration_sql

    # Verify Trinity helpers are generated
    assert "CREATE OR REPLACE FUNCTION crm.contact_pk" in migration_sql
    assert "CREATE OR REPLACE FUNCTION crm.contact_id" in migration_sql

    # Verify input types are generated
    assert "CREATE TYPE app.type_create_contact_input" in migration_sql
    assert "CREATE TYPE app.type_qualify_lead_input" in migration_sql


def test_validation_error_structure_in_generated_sql():
    """Test that input types are properly generated for validation"""
    parser = SpecQLParser()
    entity_def = parser.parse(
        read_yaml_file("entities/examples/contact_lightweight.yaml")
    )
    entity = convert_entity_definition_to_entity(entity_def)

    orchestrator = SchemaOrchestrator()
    migration_sql = orchestrator.generate_complete_schema(entity)

    # Verify input types are generated (used for validation in functions)
    assert "CREATE TYPE app.type_create_contact_input" in migration_sql
    assert "email TEXT" in migration_sql  # Required field for validation


def test_trinity_resolution_in_generated_sql():
    """Test FK constraints and helpers are generated for Trinity resolution"""
    parser = SpecQLParser()
    entity_def = parser.parse(
        read_yaml_file("entities/examples/contact_lightweight.yaml")
    )
    entity = convert_entity_definition_to_entity(entity_def)

    orchestrator = SchemaOrchestrator()
    migration_sql = orchestrator.generate_complete_schema(entity)

    # Verify FK constraints are generated
    assert "FOREIGN KEY (fk_company)" in migration_sql
    assert "REFERENCES crm.tb_company(pk_company)" in migration_sql

    # Verify Trinity helper functions are generated
    assert "CREATE OR REPLACE FUNCTION crm.contact_pk" in migration_sql
    assert "CREATE OR REPLACE FUNCTION crm.contact_id" in migration_sql


def test_update_action_compilation_sql():
    """Test that schema supports UPDATE operations"""
    parser = SpecQLParser()
    entity_def = parser.parse(
        read_yaml_file("entities/examples/contact_lightweight.yaml")
    )
    entity = convert_entity_definition_to_entity(entity_def)

    orchestrator = SchemaOrchestrator()
    migration_sql = orchestrator.generate_complete_schema(entity)

    # Verify audit fields are present for updates
    assert "updated_at TIMESTAMPTZ" in migration_sql
    assert "updated_by UUID" in migration_sql

    # Verify indexes exist for efficient updates
    assert "CREATE INDEX" in migration_sql


def test_migration_file_generation():
    """Test that migration files can be generated and contain valid SQL"""
    parser = SpecQLParser()
    entity_def = parser.parse(
        read_yaml_file("entities/examples/contact_lightweight.yaml")
    )
    entity = convert_entity_definition_to_entity(entity_def)

    orchestrator = SchemaOrchestrator()
    migration_sql = orchestrator.generate_complete_schema(entity)

    # Verify it's not empty
    assert len(migration_sql.strip()) > 1000

    # Verify it starts with app foundation
    lines = migration_sql.strip().split("\n")
    assert lines[0].startswith("-- App Schema Foundation") or lines[0].startswith(
        "-- Create app schema"
    )

    # Verify it ends with a complete statement
    assert lines[-1].strip() == ";" or lines[-1].strip().endswith(";")


def test_multiple_entities_integration():
    """Test generating schemas for multiple entities"""
    parser = SpecQLParser()

    # Parse multiple entities
    contact_def = parser.parse(
        read_yaml_file("entities/examples/contact_lightweight.yaml")
    )
    task_def = parser.parse(read_yaml_file("entities/examples/task_lightweight.yaml"))

    contact = convert_entity_definition_to_entity(contact_def)
    task = convert_entity_definition_to_entity(task_def)

    orchestrator = SchemaOrchestrator()

    # Generate separate schemas
    contact_sql = orchestrator.generate_complete_schema(contact)
    task_sql = orchestrator.generate_complete_schema(task)

    # Verify app foundation is generated (may be deduplicated)
    # At least one should have it, or both if deduplication is disabled
    has_app_schema = (
        "CREATE SCHEMA IF NOT EXISTS app;" in contact_sql
        or "CREATE SCHEMA IF NOT EXISTS app;" in task_sql
    )
    assert has_app_schema

    # Verify entity-specific content
    assert "crm.tb_contact" in contact_sql
    assert "projects.tb_task" in task_sql

    # Verify functions
    assert "crm.create_contact" in contact_sql
    assert "crm.qualify_lead" in contact_sql
    assert "projects.assign_task" in task_sql
    assert "projects.complete_task" in task_sql
