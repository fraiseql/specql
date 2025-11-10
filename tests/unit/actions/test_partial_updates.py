"""
Unit tests for partial update functionality in CoreLogicGenerator
"""

import pytest

from src.core.ast_models import Action, ActionStep, Entity, FieldDefinition


def test_generate_partial_update_assignments(core_logic_generator):
    """Test generation of CASE expressions for partial updates"""
    # Mock entity with fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
            "first_name": FieldDefinition(name="first_name", type_name="text"),
            "last_name": FieldDefinition(name="last_name", type_name="text"),
            "email": FieldDefinition(name="email", type_name="text"),
            "created_at": FieldDefinition(name="created_at", type_name="timestamp"),
            "updated_at": FieldDefinition(name="updated_at", type_name="timestamp"),
            "created_by": FieldDefinition(name="created_by", type_name="uuid"),
            "updated_by": FieldDefinition(name="updated_by", type_name="uuid"),
        },
    )

    step_fields = {"partial_updates": True}

    assignments = core_logic_generator._generate_partial_update_assignments(entity, step_fields)

    # Should generate CASE expressions for user fields only
    expected_assignments = [
        "first_name = CASE WHEN input_payload ? 'first_name'\n                         THEN input_data.first_name\n                         ELSE first_name END",
        "last_name = CASE WHEN input_payload ? 'last_name'\n                         THEN input_data.last_name\n                         ELSE last_name END",
        "email = CASE WHEN input_payload ? 'email'\n                         THEN input_data.email\n                         ELSE email END",
        "updated_at = NOW()",
        "updated_by = auth_user_id",
    ]

    assert assignments == expected_assignments


def test_generate_field_tracking(core_logic_generator):
    """Test generation of field tracking code"""
    # Mock entity with fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
            "first_name": FieldDefinition(name="first_name", type_name="text"),
            "last_name": FieldDefinition(name="last_name", type_name="text"),
            "email": FieldDefinition(name="email", type_name="text"),
            "created_at": FieldDefinition(name="created_at", type_name="timestamp"),
            "updated_at": FieldDefinition(name="updated_at", type_name="timestamp"),
            "created_by": FieldDefinition(name="created_by", type_name="uuid"),
            "updated_by": FieldDefinition(name="updated_by", type_name="uuid"),
        },
    )

    step_fields = {"track_updated_fields": True}

    tracking_code = core_logic_generator._generate_field_tracking(entity, step_fields)

    # Should initialize array and track each field
    assert tracking_code[0] == "v_updated_fields := ARRAY[]::TEXT[];"

    # Should have tracking code for each user field (excluding audit fields)
    field_tracking = [line for line in tracking_code if "IF input_payload ?" in line]
    assert len(field_tracking) == 3  # first_name, last_name, email

    # Check specific field tracking
    assert "first_name" in tracking_code[1]
    assert "last_name" in tracking_code[2]
    assert "email" in tracking_code[3]


def test_compile_partial_update_step(core_logic_generator):
    """Test compilation of partial update step"""
    # Mock entity with fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
            "first_name": FieldDefinition(name="first_name", type_name="text"),
            "last_name": FieldDefinition(name="last_name", type_name="text"),
            "email": FieldDefinition(name="email", type_name="text"),
            "created_at": FieldDefinition(name="created_at", type_name="timestamp"),
            "updated_at": FieldDefinition(name="updated_at", type_name="timestamp"),
            "created_by": FieldDefinition(name="created_by", type_name="uuid"),
            "updated_by": FieldDefinition(name="updated_by", type_name="uuid"),
        },
    )

    step = ActionStep(type="update", fields={"partial_updates": True, "track_updated_fields": True})

    action = Action(name="update_contact", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain partial update SQL
    sql = "\n".join(compiled)
    assert "UPDATE crm.tb_contact" in sql
    assert "CASE WHEN input_payload ? 'first_name'" in sql
    assert "v_updated_fields := ARRAY[]::TEXT[];" in sql
    assert "IF input_payload ? 'first_name' THEN" in sql


def test_compile_regular_update_step(core_logic_generator):
    """Test compilation of regular (non-partial) update step"""
    # Mock entity with fields
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid"),
            "tenant_id": FieldDefinition(name="tenant_id", type_name="uuid"),
            "first_name": FieldDefinition(name="first_name", type_name="text"),
            "last_name": FieldDefinition(name="last_name", type_name="text"),
            "email": FieldDefinition(name="email", type_name="text"),
            "created_at": FieldDefinition(name="created_at", type_name="timestamp"),
            "updated_at": FieldDefinition(name="updated_at", type_name="timestamp"),
            "created_by": FieldDefinition(name="created_by", type_name="uuid"),
            "updated_by": FieldDefinition(name="updated_by", type_name="uuid"),
        },
    )

    step = ActionStep(type="update", fields={"first_name": "John", "last_name": "Doe"})

    action = Action(name="update_contact", steps=[step])

    compiled = core_logic_generator._compile_action_steps(action, entity)

    # Should contain regular update SQL
    sql = "\n".join(compiled)
    assert "UPDATE crm.tb_contact" in sql
    assert "first_name = 'John'" in sql
    assert "last_name = 'Doe'" in sql
    assert "updated_at = now()" in sql
    assert "updated_by = auth_user_id" in sql

    def test_generate_partial_update_assignments(self):
        """Test generation of CASE expressions for partial updates"""
        step_fields = {"partial_updates": True}

        assignments = self.generator._generate_partial_update_assignments(self.entity, step_fields)

        # Should generate CASE expressions for user fields only
        expected_assignments = [
            "first_name = CASE WHEN input_payload ? 'first_name'\n                         THEN input_data.first_name\n                         ELSE first_name END",
            "last_name = CASE WHEN input_payload ? 'last_name'\n                         THEN input_data.last_name\n                         ELSE last_name END",
            "email = CASE WHEN input_payload ? 'email'\n                         THEN input_data.email\n                         ELSE email END",
            "updated_at = NOW()",
            "updated_by = auth_user_id",
        ]

        assert assignments == expected_assignments

    def test_generate_field_tracking(self):
        """Test generation of field tracking code"""
        step_fields = {"track_updated_fields": True}

        tracking_code = self.generator._generate_field_tracking(self.entity, step_fields)

        # Should initialize array and track each field
        assert tracking_code[0] == "v_updated_fields := ARRAY[]::TEXT[];"

        # Should have tracking code for each user field
        field_tracking = [line for line in tracking_code if "IF input_payload ?" in line]
        assert len(field_tracking) == 3  # first_name, last_name, email

        # Check specific field tracking
        assert "first_name" in tracking_code[1]
        assert "last_name" in tracking_code[2]
        assert "email" in tracking_code[3]

    def test_compile_partial_update_step(self):
        """Test compilation of partial update step"""
        step = ActionStep(
            type="update", fields={"partial_updates": True, "track_updated_fields": True}
        )

        compiled = self.generator._compile_action_steps(
            type("MockAction", (), {"steps": [step]})(),
            type(
                "MockEntity", (), {"name": "Contact", "schema": "crm", "fields": self.entity.fields}
            )(),
        )

        # Should contain partial update SQL
        sql = "\n".join(compiled)
        assert "UPDATE crm.tb_contact" in sql
        assert "CASE WHEN input_payload ? 'first_name'" in sql
        assert "v_updated_fields := ARRAY[]::TEXT[];" in sql
        assert "IF input_payload ? 'first_name' THEN" in sql

    def test_compile_regular_update_step(self):
        """Test compilation of regular (non-partial) update step"""
        step = ActionStep(type="update", fields={"first_name": "John", "last_name": "Doe"})

        compiled = self.generator._compile_action_steps(
            type("MockAction", (), {"steps": [step]})(),
            type(
                "MockEntity", (), {"name": "Contact", "schema": "crm", "fields": self.entity.fields}
            )(),
        )

        # Should contain regular update SQL
        sql = "\n".join(compiled)
        assert "UPDATE crm.tb_contact" in sql
        assert "first_name = 'John'" in sql
        assert "last_name = 'Doe'" in sql
        assert "updated_at = now()" in sql
        assert "updated_by = auth_user_id" in sql
