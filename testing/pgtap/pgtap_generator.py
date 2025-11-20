"""pgTAP test generator for PostgreSQL database testing."""

import json
from datetime import datetime
from typing import Any


class PgTAPGenerator:
    """Generates pgTAP tests from entity configurations and test metadata."""

    def __init__(self):
        """Initialize the pgTAP generator."""
        pass

    def generate_structure_tests(self, entity_config: dict[str, Any]) -> str:
        """Generate schema structure validation tests.

        Args:
            entity_config: Entity configuration dictionary containing:
                - entity_name: Name of the entity (e.g., 'Contact')
                - schema_name: Schema name (e.g., 'crm')
                - table_name: Table name (e.g., 'tb_contact')

        Returns:
            SQL string containing pgTAP structure tests
        """
        entity = entity_config["entity_name"]
        schema = entity_config["schema_name"]
        table = entity_config["table_name"]

        return f"""-- Structure Tests for {entity}
-- Auto-generated: {datetime.now().isoformat()}
BEGIN;
SELECT plan(10);

-- Table exists
SELECT has_table(
    '{schema}'::name,
    '{table}'::name,
    '{entity} table should exist'
);

-- Trinity pattern columns
SELECT has_column('{schema}', '{table}', 'pk_{entity.lower()}', 'Has INTEGER PK');
SELECT has_column('{schema}', '{table}', 'id', 'Has UUID id');
SELECT has_column('{schema}', '{table}', 'identifier', 'Has TEXT identifier');

-- Audit columns
SELECT has_column('{schema}', '{table}', 'created_at', 'Has created_at');
SELECT has_column('{schema}', '{table}', 'updated_at', 'Has updated_at');
SELECT has_column('{schema}', '{table}', 'deleted_at', 'Has deleted_at for soft delete');

-- Primary key constraint
SELECT col_is_pk('{schema}', '{table}', 'pk_{entity.lower()}', 'pk_{entity.lower()} is primary key');

-- UUID unique constraint
SELECT col_is_unique('{schema}', '{table}', 'id', 'id is unique');

SELECT * FROM finish();
ROLLBACK;
"""

    def generate_crud_tests(
        self, entity_config: dict[str, Any], field_mappings: list[dict[str, Any]]
    ) -> str:
        """Generate CRUD operation tests.

        Args:
            entity_config: Entity configuration dictionary
            field_mappings: List of field mapping dictionaries

        Returns:
            SQL string containing pgTAP CRUD tests
        """
        entity = entity_config["entity_name"]
        schema = entity_config["schema_name"]

        # Build sample input JSON from field mappings
        input_fields = {}
        for field in field_mappings:
            if field.get("generator_type") in ("random", "fixed"):
                field_name = field["field_name"]
                field_type = field.get("field_type", "")

                if field_type == "email":
                    input_fields[field_name] = "test@example.com"
                elif field_type.startswith("enum("):
                    # Extract enum values from field_type like 'enum(lead,qualified,customer)'
                    enum_part = field_type[5:-1]  # Remove 'enum(' and ')'
                    values = [v.strip() for v in enum_part.split(",")]
                    input_fields[field_name] = values[0] if values else "default"
                elif field_type in ("text", "varchar"):
                    input_fields[field_name] = f"test_{field_name}"
                elif field_type.startswith("varchar("):
                    input_fields[field_name] = f"test_{field_name}"
                elif field_type in ("integer", "bigint"):
                    input_fields[field_name] = 123
                elif field_type == "boolean":
                    input_fields[field_name] = True
                elif field_type == "uuid":
                    input_fields[field_name] = "01232122-0000-0000-2000-000000000001"
                else:
                    input_fields[field_name] = f"test_{field_name}"

        input_json = json.dumps(input_fields)

        return f"""-- CRUD Tests for {entity}
-- Auto-generated: {datetime.now().isoformat()}
BEGIN;
SELECT plan(15);

-- Test: CREATE succeeds
PREPARE create_test AS
    SELECT app.create_{entity.lower()}(
        '{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}'::UUID,
        '{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}'::UUID,
        '{input_json}'::JSONB
    );

SELECT lives_ok(
    'create_test',
    'create_{entity.lower()} should execute without error'
);

-- Test: CREATE returns success
DO $$
DECLARE
    v_result app.mutation_result;
BEGIN
    v_result := app.create_{entity.lower()}(
        '{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}'::UUID,
        '{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}'::UUID,
        '{input_json}'::JSONB
    );

    PERFORM ok(
        v_result.status = 'success',
        'CREATE should return success status'
    );

    PERFORM ok(
        v_result.object_data IS NOT NULL,
        'CREATE should return object_data'
    );

    PERFORM ok(
        (v_result.object_data->>'id') IS NOT NULL,
        'object_data should contain id'
    );
END $$;

-- Test: Record exists in database
DO $$
DECLARE
    v_result app.mutation_result;
    v_id UUID;
    v_count INTEGER;
BEGIN
    v_result := app.create_{entity.lower()}(
        '{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}'::UUID,
        '{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}'::UUID,
        '{input_json}'::JSONB
    );
    v_id := (v_result.object_data->>'id')::UUID;

    SELECT COUNT(*) INTO v_count
    FROM {schema}.{entity_config["table_name"]}
    WHERE id = v_id;

    PERFORM is(v_count, 1, 'Record should exist in table');
END $$;

SELECT * FROM finish();
ROLLBACK;
"""

    def generate_constraint_tests(
        self, entity_config: dict[str, Any], scenarios: list[dict[str, Any]]
    ) -> str:
        """Generate constraint violation tests from scenarios.

        Args:
            entity_config: Entity configuration dictionary
            scenarios: List of test scenario dictionaries

        Returns:
            SQL string containing pgTAP constraint tests
        """
        tests = []

        for scenario in scenarios:
            if scenario.get("scenario_type") == "constraint_violation":
                test = f"""
-- Constraint Test: {scenario["scenario_name"]}
-- Auto-generated: {datetime.now().isoformat()}
DO $$
DECLARE
    v_result app.mutation_result;
BEGIN
    -- First insert (should succeed)
    v_result := app.create_{entity_config["entity_name"].lower()}(
        '{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}'::UUID,
        '{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}'::UUID,
        '{json.dumps(scenario.get("input_overrides", {}))}'::JSONB
    );

    PERFORM ok(
        v_result.status = 'success',
        'First insert should succeed'
    );

    -- Duplicate insert (should fail)
    v_result := app.create_{entity_config["entity_name"].lower()}(
        '{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}'::UUID,
        '{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}'::UUID,
        '{json.dumps(scenario.get("input_overrides", {}))}'::JSONB
    );

    PERFORM like(
        v_result.status,
        'failed:%',
        '{scenario["scenario_name"]} should fail with error'
    );

    PERFORM like(
        v_result.message,
        '%{scenario.get("expected_error_code", "duplicate")}%',
        'Error message should mention constraint violation'
    );
END $$;
"""
                tests.append(test)

        return "\n\n".join(tests)

    def generate_action_tests(
        self,
        entity_config: dict[str, Any],
        actions: list[dict[str, Any]],
        scenarios: list[dict[str, Any]],
    ) -> str:
        """Generate tests for custom actions.

        Args:
            entity_config: Entity configuration dictionary
            actions: List of action dictionaries
            scenarios: List of test scenario dictionaries

        Returns:
            SQL string containing pgTAP action tests
        """
        tests = []

        for action in actions:
            action_name = action["name"]
            schema = entity_config["schema_name"]

            # Find scenarios for this action
            action_scenarios = [s for s in scenarios if s.get("target_action") == action_name]

            for scenario in action_scenarios:
                test = f"""-- Action Test: {action_name} - {scenario["scenario_name"]}
-- Auto-generated: {datetime.now().isoformat()}
BEGIN;
SELECT plan(5);

{scenario.get("setup_sql", "")}

-- Execute action
DO $$
DECLARE
    v_contact_id UUID := '01232122-0000-0000-2000-000000000001';
    v_result app.mutation_result;
BEGIN
    v_result := {schema}.{action_name}(
        v_contact_id,
        '{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}'::UUID
    );

    -- Verify expected result
    PERFORM {"ok" if scenario.get("expected_result") == "success" else "isnt"}(
        v_result.status,
        'success',
        '{action_name} should {"succeed" if scenario.get("expected_result") == "success" else "fail"}'
    );

    -- Verify updated_fields
    PERFORM ok(
        array_length(v_result.updated_fields, 1) > 0,
        'updated_fields should not be empty'
    );

    -- Verify object_data
    PERFORM ok(
        v_result.object_data IS NOT NULL,
        'object_data should contain result'
    );
END $$;

SELECT * FROM finish();
ROLLBACK;
"""
                tests.append(test)

        return "\n\n".join(tests)
