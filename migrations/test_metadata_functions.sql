-- Test Metadata Query Functions
-- SQL functions for querying test metadata
-- Generated: 2025-11-09

-- Function 1: get_entity_config
-- Retrieve entity configuration by name
CREATE OR REPLACE FUNCTION test_metadata.get_entity_config(p_entity_name TEXT)
RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT jsonb_build_object(
            'entity_name', entity_name,
            'schema_name', schema_name,
            'table_name', table_name,
            'table_code', table_code,
            'entity_code', entity_code,
            'base_uuid_prefix', base_uuid_prefix,
            'is_tenant_scoped', is_tenant_scoped,
            'default_tenant_id', default_tenant_id,
            'default_user_id', default_user_id,
            'default_seed_count', default_seed_count,
            'seed_strategy', seed_strategy,
            'enable_crud_tests', enable_crud_tests,
            'enable_action_tests', enable_action_tests,
            'enable_constraint_tests', enable_constraint_tests,
            'enable_dedup_tests', enable_dedup_tests,
            'enable_fk_tests', enable_fk_tests,
            'source_yaml_path', source_yaml_path
        )
        FROM test_metadata.tb_entity_test_config
        WHERE entity_name = p_entity_name
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Function 2: get_field_generators
-- Retrieve field generator mappings for entity
CREATE OR REPLACE FUNCTION test_metadata.get_field_generators(p_entity_name TEXT)
RETURNS TABLE (
    field_name TEXT,
    field_type TEXT,
    postgres_type TEXT,
    generator_type TEXT,
    generator_function TEXT,
    generator_params JSONB,
    fk_target_entity TEXT,
    fk_target_schema TEXT,
    fk_target_table TEXT,
    fk_target_pk_field TEXT,
    fk_resolution_query TEXT,
    fk_filter_conditions TEXT,
    fk_dependencies TEXT[],
    generator_group TEXT,
    is_group_leader BOOLEAN,
    group_leader_field TEXT,
    group_dependency_fields TEXT[],
    nullable BOOLEAN,
    unique_constraint BOOLEAN,
    validation_pattern TEXT,
    check_constraint TEXT,
    example_values TEXT[],
    seed_distribution JSONB,
    enum_values TEXT[],
    priority_order INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fg.field_name,
        fg.field_type,
        fg.postgres_type,
        fg.generator_type,
        fg.generator_function,
        fg.generator_params,
        fg.fk_target_entity,
        fg.fk_target_schema,
        fg.fk_target_table,
        fg.fk_target_pk_field,
        fg.fk_resolution_query,
        fg.fk_filter_conditions,
        fg.fk_dependencies,
        fg.generator_group,
        fg.is_group_leader,
        fg.group_leader_field,
        fg.group_dependency_fields,
        fg.nullable,
        fg.unique_constraint,
        fg.validation_pattern,
        fg.check_constraint,
        fg.example_values,
        fg.seed_distribution,
        fg.enum_values,
        fg.priority_order
    FROM test_metadata.tb_field_generator_mapping fg
    JOIN test_metadata.tb_entity_test_config ec ON ec.pk_entity_test_config = fg.fk_entity_test_config
    WHERE ec.entity_name = p_entity_name
    ORDER BY fg.priority_order, fg.field_name;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function 3: get_scenarios
-- Retrieve test scenarios for entity
CREATE OR REPLACE FUNCTION test_metadata.get_scenarios(p_entity_name TEXT)
RETURNS TABLE (
    scenario_code INTEGER,
    scenario_name TEXT,
    scenario_type TEXT,
    test_function_name TEXT,
    target_action TEXT,
    input_overrides JSONB,
    expected_result TEXT,
    expected_error_code TEXT,
    expected_status_pattern TEXT,
    seed_count INTEGER,
    requires_dependencies BOOLEAN,
    dependency_entities TEXT[],
    setup_sql TEXT,
    teardown_sql TEXT,
    description TEXT,
    test_category TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.scenario_code,
        s.scenario_name,
        s.scenario_type,
        s.test_function_name,
        s.target_action,
        s.input_overrides,
        s.expected_result,
        s.expected_error_code,
        s.expected_status_pattern,
        s.seed_count,
        s.requires_dependencies,
        s.dependency_entities,
        s.setup_sql,
        s.teardown_sql,
        s.description,
        s.test_category
    FROM test_metadata.tb_test_scenarios s
    JOIN test_metadata.tb_entity_test_config ec ON ec.pk_entity_test_config = s.fk_entity_test_config
    WHERE ec.entity_name = p_entity_name
      AND s.enabled = TRUE
    ORDER BY s.scenario_code;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function 4: get_group_leader_config
-- Retrieve group leader configuration for entity and group
CREATE OR REPLACE FUNCTION test_metadata.get_group_leader_config(p_entity_name TEXT, p_group_name TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'group_name', p_group_name,
        'leader_field', fg.field_name,
        'dependent_fields', (
            SELECT array_agg(fg2.field_name)
            FROM test_metadata.tb_field_generator_mapping fg2
            WHERE fg2.fk_entity_test_config = ec.pk_entity_test_config
              AND fg2.generator_group = p_group_name
              AND fg2.group_leader_field = fg.field_name
        ),
        'leader_query', fg.generator_params->>'leader_query'
    ) INTO result
    FROM test_metadata.tb_entity_test_config ec
    JOIN test_metadata.tb_field_generator_mapping fg ON fg.fk_entity_test_config = ec.pk_entity_test_config
    WHERE ec.entity_name = p_entity_name
      AND fg.generator_group = p_group_name
      AND fg.is_group_leader = TRUE;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function 5: get_fk_dependencies
-- Retrieve FK dependency information for entity and field
CREATE OR REPLACE FUNCTION test_metadata.get_fk_dependencies(p_entity_name TEXT, p_field_name TEXT)
RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT jsonb_build_object(
            'field_name', fg.field_name,
            'target_entity', fg.fk_target_entity,
            'target_schema', fg.fk_target_schema,
            'target_table', fg.fk_target_table,
            'target_pk_field', fg.fk_target_pk_field,
            'dependencies', fg.fk_dependencies,
            'resolution_query', fg.fk_resolution_query,
            'filter_conditions', fg.fk_filter_conditions
        )
        FROM test_metadata.tb_entity_test_config ec
        JOIN test_metadata.tb_field_generator_mapping fg ON fg.fk_entity_test_config = ec.pk_entity_test_config
        WHERE ec.entity_name = p_entity_name
          AND fg.field_name = p_field_name
          AND fg.generator_type = 'fk_resolve'
    );
END;
$$ LANGUAGE plpgsql STABLE;