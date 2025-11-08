"""Tests for App Wrapper Generator (Team C)"""

import pytest
from src.generators.app_wrapper_generator import AppWrapperGenerator
from src.core.ast_models import Entity, Action


def test_generate_app_wrapper_for_create_action():
    """Generate app wrapper for create action"""
    # Given: Entity with create action
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="create_contact")]
    )

    # When: Generate app wrapper
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: App wrapper function with correct signature
    assert "CREATE OR REPLACE FUNCTION app.create_contact(" in sql
    assert "auth_tenant_id UUID" in sql
    assert "auth_user_id UUID" in sql
    assert "input_payload JSONB" in sql
    assert "RETURNS app.mutation_result" in sql

    # Then: JSONB → Composite Type conversion
    assert "input_data app.type_create_contact_input" in sql
    assert "jsonb_populate_record" in sql

    # Then: Delegation to core layer
    assert "RETURN crm.create_contact(" in sql
    assert "auth_tenant_id," in sql
    assert "input_data," in sql
    assert "input_payload," in sql
    assert "auth_user_id" in sql

    # Then: FraiseQL annotation
    assert "COMMENT ON FUNCTION app.create_contact IS" in sql
    assert "@fraiseql:mutation" in sql


def test_app_wrapper_fraiseql_comment_yaml_format():
    """App wrapper function should have YAML comment format"""
    # Given: Entity with create action
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="create_contact")]
    )

    # When: Generate app wrapper
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: Function comment uses YAML format
    expected_comment = """COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';"""

    assert expected_comment in sql


def test_app_wrapper_jwt_context_parameters():
    """App wrapper extracts JWT context"""
    # Given: Entity with action
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="create_contact")]
    )

    # When: Generate
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: Context parameters are first two params
    assert "auth_tenant_id UUID" in sql
    assert "auth_user_id UUID" in sql
    # Then: Payload is third param
    assert "input_payload JSONB" in sql


def test_app_wrapper_uses_team_b_composite_type():
    """App wrapper references Team B's composite type"""
    # Given: Action name "create_contact"
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="create_contact")]
    )
    action = Action(name="create_contact")

    # When: Generate
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, action)

    # Then: Uses correct composite type name
    assert "app.type_create_contact_input" in sql


def test_app_wrapper_for_update_action():
    """Generate app wrapper for update action"""
    # Given: Entity with update action
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="update_contact")]
    )

    # When: Generate app wrapper
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: App wrapper function with correct signature
    assert "CREATE OR REPLACE FUNCTION app.update_contact(" in sql
    assert "auth_tenant_id UUID" in sql
    assert "auth_user_id UUID" in sql
    assert "input_payload JSONB" in sql
    assert "RETURNS app.mutation_result" in sql

    # Then: Uses correct composite type for update
    assert "app.type_update_contact_input" in sql

    # Then: Delegation to core layer
    assert "RETURN crm.update_contact(" in sql


def test_app_wrapper_for_delete_action():
    """Generate app wrapper for delete action (no composite type)"""
    # Given: Entity with delete action
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="delete_contact")]
    )

    # When: Generate app wrapper
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: App wrapper function with correct signature
    assert "CREATE OR REPLACE FUNCTION app.delete_contact(" in sql
    assert "auth_tenant_id UUID" in sql
    assert "auth_user_id UUID" in sql
    assert "input_payload JSONB" in sql
    assert "RETURNS app.mutation_result" in sql

    # Then: No composite type declaration for delete
    assert "input_data app.type_delete_contact_input" not in sql

    # Then: Delegation to core layer (different signature for delete)
    assert "RETURN crm.delete_contact(" in sql
    assert "auth_tenant_id," in sql
    assert "input_payload," in sql
    assert "auth_user_id" in sql


def test_app_wrapper_error_handling():
    """App wrapper includes error handling"""
    # Given: Any action
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="create_contact")]
    )

    # When: Generate
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: Includes exception handling
    assert "EXCEPTION" in sql
    assert "WHEN OTHERS THEN" in sql
    assert "failed:unexpected_error" in sql
    assert "SQLERRM" in sql
    assert "SQLSTATE" in sql


def test_app_wrapper_fraiseql_annotation():
    """App wrapper includes FraiseQL mutation annotation"""
    # Given: Action with name "create_contact"
    entity = Entity(
        name="Contact", schema="crm", fields={}, actions=[Action(name="create_contact")]
    )

    # When: Generate
    generator = AppWrapperGenerator()
    sql = generator.generate_app_wrapper(entity, entity.actions[0])

    # Then: FraiseQL annotation
    assert "COMMENT ON FUNCTION app.create_contact IS" in sql
    assert "@fraiseql:mutation" in sql
    assert "name: createContact" in sql
    assert "input_type: app.type_create_contact_input" in sql
    assert "success_type: CreateContactSuccess" in sql
    assert "failure_type: CreateContactError" in sql
