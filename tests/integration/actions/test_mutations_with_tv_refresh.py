"""
Integration tests for mutations with tv_refresh integration

Tests that refresh_table_view steps are properly compiled to PERFORM calls
in generated PL/pgSQL functions.
"""

from pathlib import Path

from generators.core_logic_generator import CoreLogicGenerator


def read_yaml_file(file_path: str) -> str:
    """Helper to read YAML file content"""
    return Path(file_path).read_text()


def convert_entity_definition_to_entity(entity_def):
    """Convert EntityDefinition to Entity for generator compatibility"""
    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = type(
            "Action",
            (),
            {
                "name": action_def.name,
                "steps": action_def.steps,
                "impact": getattr(action_def, "impact", None),
            },
        )()
        actions.append(action)

    # Create Entity
    entity = type(
        "Entity",
        (),
        {
            "name": entity_def.name,
            "schema": entity_def.schema,
            "description": getattr(entity_def, "description", ""),
            "fields": entity_def.fields,
            "actions": actions,
            "agents": getattr(entity_def, "agents", []),
            "organization": getattr(entity_def, "organization", ""),
        },
    )()

    return entity


def test_refresh_table_view_self_scope_compilation():
    """
    Test that refresh_table_view with self scope compiles to PERFORM call
    """
    # Create a mock entity with refresh_table_view action
    entity_def = type(
        "EntityDefinition",
        (),
        {
            "name": "Review",
            "schema": "library",
            "fields": {},
            "actions": [
                type(
                    "ActionDefinition",
                    (),
                    {
                        "name": "update_rating",
                        "steps": [
                            type(
                                "ActionStep",
                                (),
                                {
                                    "type": "update",
                                    "fields": {"rating": "p_new_rating"},
                                    "entity": "Review",
                                },
                            )(),
                            type(
                                "ActionStep",
                                (),
                                {
                                    "type": "refresh_table_view",
                                    "refresh_scope": type("RefreshScope", (), {"value": "self"})(),
                                    "propagate_entities": [],
                                },
                            )(),
                        ],
                        "impact": None,
                    },
                )()
            ],
        },
    )()

    entity = convert_entity_definition_to_entity(entity_def)

    # Create generator (mock schema registry)
    schema_registry = type("SchemaRegistry", (), {"is_multi_tenant": lambda schema: False})()

    generator = CoreLogicGenerator(schema_registry)

    # Generate the custom action
    action = entity.actions[0]
    sql = generator.generate_custom_action(entity, action)

    # Verify the generated SQL contains the PERFORM call
    assert "PERFORM library.refresh_tv_review(v_pk_review);" in sql
    assert "-- Refresh table view (self)" in sql


def test_refresh_table_view_propagate_scope_compilation():
    """
    Test that refresh_table_view with propagate scope compiles to multiple PERFORM calls
    """
    # Create a mock entity with refresh_table_view action
    entity_def = type(
        "EntityDefinition",
        (),
        {
            "name": "Review",
            "schema": "library",
            "fields": {},
            "actions": [
                type(
                    "ActionDefinition",
                    (),
                    {
                        "name": "create_review",
                        "steps": [
                            type("ActionStep", (), {"type": "insert", "entity": "Review"})(),
                            type(
                                "ActionStep",
                                (),
                                {
                                    "type": "refresh_table_view",
                                    "refresh_scope": type(
                                        "RefreshScope", (), {"value": "propagate"}
                                    )(),
                                    "propagate_entities": ["author", "book"],
                                },
                            )(),
                        ],
                        "impact": None,
                    },
                )()
            ],
        },
    )()

    entity = convert_entity_definition_to_entity(entity_def)

    # Create generator (mock schema registry)
    schema_registry = type("SchemaRegistry", (), {"is_multi_tenant": lambda schema: False})()

    generator = CoreLogicGenerator(schema_registry)

    # Generate the custom action
    action = entity.actions[0]
    sql = generator.generate_custom_action(entity, action)

    # Verify the generated SQL contains the PERFORM calls
    assert "PERFORM library.refresh_tv_review(v_pk_review);" in sql
    assert "PERFORM library.refresh_tv_author(v_fk_author);" in sql
    assert "PERFORM library.refresh_tv_book(v_fk_book);" in sql
    assert "-- Refresh table view (self + propagate)" in sql


def test_refresh_table_view_batch_scope_compilation():
    """
    Test that refresh_table_view with batch scope compiles to queue INSERT
    """
    # Create a mock entity with refresh_table_view action
    entity_def = type(
        "EntityDefinition",
        (),
        {
            "name": "Review",
            "schema": "library",
            "fields": {},
            "actions": [
                type(
                    "ActionDefinition",
                    (),
                    {
                        "name": "bulk_update_ratings",
                        "steps": [
                            type(
                                "ActionStep",
                                (),
                                {
                                    "type": "update",
                                    "fields": {"rating": "p_new_rating"},
                                    "entity": "Review",
                                },
                            )(),
                            type(
                                "ActionStep",
                                (),
                                {
                                    "type": "refresh_table_view",
                                    "refresh_scope": type("RefreshScope", (), {"value": "batch"})(),
                                    "propagate_entities": [],
                                },
                            )(),
                        ],
                        "impact": None,
                    },
                )()
            ],
        },
    )()

    entity = convert_entity_definition_to_entity(entity_def)

    # Create generator (mock schema registry)
    schema_registry = type("SchemaRegistry", (), {"is_multi_tenant": lambda schema: False})()

    generator = CoreLogicGenerator(schema_registry)

    # Generate the custom action
    action = entity.actions[0]
    sql = generator.generate_custom_action(entity, action)

    # Verify the generated SQL contains the queue INSERT
    assert "INSERT INTO pg_temp.tv_refresh_queue VALUES ('Review', v_pk_review);" in sql
    assert "-- Queue for batch refresh (deferred)" in sql


def test_mutation_result_returns_tv_data():
    """
    Test that mutation results return tv_.data instead of tb_ fields
    """
    # This would require testing the success_response_generator
    # For now, just verify the template includes tv_ data selection
    pass  # TODO: Implement when success response generation is integrated
