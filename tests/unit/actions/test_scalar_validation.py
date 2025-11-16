"""
Tests for Scalar Type Validation in Validate Compiler
Phase 2: Scalar type validation support
"""

import pytest

from src.core.ast_models import ActionStep, Entity, FieldDefinition, FieldTier
from src.generators.actions.step_compilers.validate_compiler import ValidateStepCompiler


class TestScalarValidation:
    """Test scalar type validation in validate steps"""

    @pytest.fixture
    def compiler(self):
        """Create validate compiler instance"""
        return ValidateStepCompiler()

    @pytest.fixture
    def contact_entity(self):
        """Create test Contact entity with scalar fields"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email", type_name="email", tier=FieldTier.SCALAR
                ),
                "phone": FieldDefinition(
                    name="phone", type_name="phoneNumber", tier=FieldTier.SCALAR
                ),
                "first_name": FieldDefinition(name="first_name", type_name="text"),
            },
        )

    def test_scalar_validation_email(self, compiler, contact_entity):
        """Test scalar validation for email field"""
        step = ActionStep(
            type="validate", expression="email is valid", error="invalid_email"
        )

        sql = compiler.compile(step, contact_entity, {})

        assert "Validate scalar: email is valid" in sql
        assert "SELECT email INTO v_email" in sql
        assert "IF (" in sql
        assert "invalid_email" in sql

    def test_scalar_validation_phone(self, compiler, contact_entity):
        """Test scalar validation for phone field"""
        step = ActionStep(
            type="validate", expression="phone is valid", error="invalid_phone"
        )

        sql = compiler.compile(step, contact_entity, {})

        assert "Validate scalar: phone is valid" in sql
        assert "SELECT phone INTO v_phone" in sql

    def test_regular_validation_still_works(self, compiler, contact_entity):
        """Test that regular validation expressions still work"""
        step = ActionStep(
            type="validate", expression="first_name IS NOT NULL", error="name_required"
        )

        sql = compiler.compile(step, contact_entity, {})

        assert "Validate: first_name IS NOT NULL" in sql
        assert "SELECT first_name INTO v_first_name" in sql
        assert "IF NOT (v_first_name IS NOT NULL)" in sql

    def test_is_scalar_validation_detection(self, compiler, contact_entity):
        """Test detection of scalar validation expressions"""
        # Should detect scalar validation
        assert compiler._is_scalar_validation("email is valid", contact_entity) == (
            "email",
            "email",
        )
        assert compiler._is_scalar_validation("phone is valid", contact_entity) == (
            "phone",
            "phoneNumber",
        )

        # Should not detect regular validation
        assert (
            compiler._is_scalar_validation("first_name IS NOT NULL", contact_entity)
            is None
        )
        assert (
            compiler._is_scalar_validation("status = 'active'", contact_entity) is None
        )

        # Should not detect for non-scalar fields
        assert (
            compiler._is_scalar_validation("first_name is valid", contact_entity)
            is None
        )
