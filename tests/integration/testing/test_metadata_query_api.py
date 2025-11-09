"""Integration tests for test metadata query API functions"""

import pytest
import psycopg


@pytest.fixture
def test_db():
    """PostgreSQL test database connection"""
    try:
        conn = psycopg.connect(
            host="localhost", port=5433, dbname="test_specql", user="postgres", password="postgres"
        )
        # Clean up any existing test metadata
        cursor = conn.cursor()
        try:
            cursor.execute("DROP SCHEMA IF EXISTS test_metadata CASCADE;")
        except:
            pass  # Ignore errors
        conn.commit()

        # Create test_metadata schema and tables
        with open("migrations/test_metadata_schema.sql", "r") as f:
            schema_sql = f.read()
        cursor.execute(schema_sql)
        conn.commit()

        # Create functions
        with open("migrations/test_metadata_functions.sql", "r") as f:
            functions_sql = f.read()
        cursor.execute(functions_sql)
        conn.commit()

        yield conn

        # Cleanup after test
        conn.close()
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


def test_get_entity_config(test_db):
    """Should retrieve entity config by name"""
    # First populate some test metadata
    test_db.execute("""
        INSERT INTO test_metadata.tb_entity_test_config
        (entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix)
        VALUES
        ('Contact', 'crm', 'tb_contact', 123210, 'CON', '012321');
    """)

    # Now test the function
    result = test_db.execute("SELECT test_metadata.get_entity_config('Contact')").fetchone()

    assert result is not None
    config = result[0]  # Returns JSONB
    assert config["entity_name"] == "Contact"
    assert config["schema_name"] == "crm"
    assert config["table_name"] == "tb_contact"
    assert config["table_code"] == 123210
    assert config["entity_code"] == "CON"
    assert config["base_uuid_prefix"] == "012321"


def test_get_entity_config_not_found(test_db):
    """Should return null for non-existent entity"""
    result = test_db.execute(
        "SELECT test_metadata.get_entity_config('NonExistentEntity')"
    ).fetchone()

    assert result[0] is None


def test_get_field_generators(test_db):
    """Should retrieve field generators for entity"""
    # First populate entity config
    test_db.execute("""
        INSERT INTO test_metadata.tb_entity_test_config
        (pk_entity_test_config, entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix)
        VALUES
        (1, 'Contact', 'crm', 'tb_contact', 123210, 'CON', '012321');
    """)

    # Populate field generators
    test_db.execute("""
        INSERT INTO test_metadata.tb_field_generator_mapping
        (fk_entity_test_config, field_name, field_type, postgres_type, generator_type, generator_function, priority_order, fk_target_entity, fk_target_schema, fk_target_table, fk_target_pk_field)
        VALUES
        (1, 'email', 'email', 'TEXT', 'random', 'test_random_email', 10, NULL, NULL, NULL, NULL),
        (1, 'first_name', 'text', 'TEXT', 'random', 'test_random_text', 5, NULL, NULL, NULL, NULL),
        (1, 'fk_company', 'ref(Company)', 'INTEGER', 'fk_resolve', NULL, 20, 'Company', 'crm', 'tb_company', 'pk_company');
    """)

    # Test the function
    results = test_db.execute(
        "SELECT * FROM test_metadata.get_field_generators('Contact') ORDER BY field_name"
    ).fetchall()

    assert len(results) == 3

    # Check email field
    email_row = next(row for row in results if row[0] == "email")
    assert email_row[1] == "email"  # field_type
    assert email_row[2] == "TEXT"  # postgres_type
    assert email_row[3] == "random"  # generator_type
    assert email_row[4] == "test_random_email"  # generator_function

    # Check FK field
    fk_row = next(row for row in results if row[0] == "fk_company")
    assert fk_row[1] == "ref(Company)"  # field_type
    assert fk_row[2] == "INTEGER"  # postgres_type
    assert fk_row[3] == "fk_resolve"  # generator_type
    assert fk_row[6] == "Company"  # fk_target_entity


def test_get_field_generators_empty_entity(test_db):
    """Should return empty result set for entity with no fields"""
    # First populate entity config
    test_db.execute("""
        INSERT INTO test_metadata.tb_entity_test_config
        (entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix)
        VALUES
        ('EmptyEntity', 'test', 'tb_empty', 999999, 'EMP', '999999');
    """)

    # Test the function
    results = test_db.execute(
        "SELECT * FROM test_metadata.get_field_generators('EmptyEntity')"
    ).fetchall()

    assert len(results) == 0


def test_get_scenarios(test_db):
    """Should retrieve test scenarios for entity"""
    # First populate entity config
    test_db.execute("""
        INSERT INTO test_metadata.tb_entity_test_config
        (pk_entity_test_config, entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix)
        VALUES
        (1, 'Contact', 'crm', 'tb_contact', 123210, 'CON', '012321');
    """)

    # Populate scenarios
    test_db.execute("""
        INSERT INTO test_metadata.tb_test_scenarios
        (fk_entity_test_config, scenario_code, scenario_name, scenario_type, expected_result, enabled)
        VALUES
        (1, 0, 'happy_path_create', 'happy_path', 'success', TRUE),
        (1, 1000, 'duplicate_email', 'dedup', 'error', TRUE),
        (1, 2000, 'disabled_scenario', 'custom_action', 'success', FALSE);
    """)

    # Test the function
    results = test_db.execute(
        "SELECT * FROM test_metadata.get_scenarios('Contact') ORDER BY scenario_code"
    ).fetchall()

    # Should only return enabled scenarios
    assert len(results) == 2

    # Check happy path scenario
    happy_row = next(row for row in results if row[0] == 0)
    assert happy_row[1] == "happy_path_create"
    assert happy_row[2] == "happy_path"
    assert happy_row[6] == "success"

    # Check duplicate scenario
    dup_row = next(row for row in results if row[0] == 1000)
    assert dup_row[1] == "duplicate_email"
    assert dup_row[2] == "dedup"
    assert dup_row[6] == "error"


def test_get_scenarios_no_enabled_scenarios(test_db):
    """Should return empty result set when no enabled scenarios"""
    # First populate entity config
    test_db.execute("""
        INSERT INTO test_metadata.tb_entity_test_config
        (pk_entity_test_config, entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix)
        VALUES
        (1, 'Contact', 'crm', 'tb_contact', 123210, 'CON', '012321');
    """)

    # Populate only disabled scenarios
    test_db.execute("""
        INSERT INTO test_metadata.tb_test_scenarios
        (fk_entity_test_config, scenario_code, scenario_name, scenario_type, expected_result, enabled)
        VALUES
        (1, 0, 'disabled_scenario', 'happy_path', 'success', FALSE);
    """)

    # Test the function
    results = test_db.execute("SELECT * FROM test_metadata.get_scenarios('Contact')").fetchall()

    assert len(results) == 0


def test_get_group_leader_config(test_db):
    """Should retrieve group leader configuration"""
    # First populate entity config
    test_db.execute("""
        INSERT INTO test_metadata.tb_entity_test_config
        (pk_entity_test_config, entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix)
        VALUES
        (1, 'Contact', 'crm', 'tb_contact', 123210, 'CON', '012321');
    """)

    # Populate group leader field
    test_db.execute("""
        INSERT INTO test_metadata.tb_field_generator_mapping
        (fk_entity_test_config, field_name, field_type, postgres_type, generator_type, is_group_leader, generator_group, generator_params)
        VALUES
        (1, 'country_code', 'text', 'TEXT', 'group_leader', TRUE, 'address_group',
         '{"leader_query": "SELECT country_code, postal_code, city_code FROM dim.tb_address WHERE deleted_at IS NULL ORDER BY RANDOM() LIMIT 1"}'::JSONB);
    """)

    # Populate group dependent fields
    test_db.execute("""
        INSERT INTO test_metadata.tb_field_generator_mapping
        (fk_entity_test_config, field_name, field_type, postgres_type, generator_type, generator_group, group_leader_field)
        VALUES
        (1, 'postal_code', 'text', 'TEXT', 'group_dependent', 'address_group', 'country_code'),
        (1, 'city_code', 'text', 'TEXT', 'group_dependent', 'address_group', 'country_code');
    """)

    # Test the function (this will fail until implemented)
    result = test_db.execute(
        "SELECT test_metadata.get_group_leader_config('Contact', 'address_group')"
    ).fetchone()

    assert result is not None
    config = result[0]  # Returns JSONB
    assert config["group_name"] == "address_group"
    assert config["leader_field"] == "country_code"
    assert set(config["dependent_fields"]) == {"postal_code", "city_code"}
    assert "leader_query" in config


def test_get_fk_dependencies(test_db):
    """Should retrieve FK dependency information"""
    # First populate entity config
    test_db.execute("""
        INSERT INTO test_metadata.tb_entity_test_config
        (pk_entity_test_config, entity_name, schema_name, table_name, table_code, entity_code, base_uuid_prefix)
        VALUES
        (1, 'Contact', 'crm', 'tb_contact', 123210, 'CON', '012321');
    """)

    # Populate FK field with dependencies
    test_db.execute("""
        INSERT INTO test_metadata.tb_field_generator_mapping
        (fk_entity_test_config, field_name, field_type, postgres_type, generator_type, fk_target_entity, fk_dependencies)
        VALUES
        (1, 'fk_company', 'ref(Company)', 'INTEGER', 'fk_resolve', 'Company', ARRAY['tenant_id', 'user_id']);
    """)

    # Test the function (this will fail until implemented)
    result = test_db.execute(
        "SELECT test_metadata.get_fk_dependencies('Contact', 'fk_company')"
    ).fetchone()

    assert result is not None
    deps = result[0]  # Returns JSONB
    assert deps["field_name"] == "fk_company"
    assert deps["target_entity"] == "Company"
    assert deps["dependencies"] == ["tenant_id", "user_id"]
