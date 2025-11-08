"""
Tests for Validation Step Compilation
Phase 2: Validation Step Compilation
"""

import pytest

from src.core.ast_models import ActionStep, Entity, FieldDefinition
from src.generators.actions.validation_step_compiler import ValidationStepCompiler


class TestValidationSteps:
    """Test validation step compilation to PL/pgSQL"""

    @pytest.fixture
    def compiler(self):
        """Create validation step compiler instance"""
        return ValidationStepCompiler()

    @pytest.fixture
    def contact_entity(self):
        """Create test Contact entity"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "status": FieldDefinition(name="status", type_name="text"),
                "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company"),
            },
        )

    def test_simple_equality_validation(self, compiler, contact_entity):
        """Test: Compile simple equality validation"""
        step = ActionStep(type="validate", expression="status = 'lead'", error="not_a_lead")

        sql = compiler.compile(step, contact_entity)

        # Expected: IF NOT validation THEN error response
        assert "IF NOT (p_status = 'lead') THEN" in sql
        assert "v_result.status := 'error';" in sql
        assert "v_result.message := 'not_a_lead';" in sql
        assert "RETURN v_result;" in sql

    def test_null_check_validation(self, compiler, contact_entity):
        """Test: Compile NULL validation"""
        step = ActionStep(type="validate", expression="email IS NOT NULL", error="email_required")

        sql = compiler.compile(step, contact_entity)

        assert "IF NOT (p_email IS NOT NULL) THEN" in sql
        assert "'email_required'" in sql

    def test_pattern_match_validation(self, compiler, contact_entity):
        """Test: Compile regex pattern validation"""
        step = ActionStep(
            type="validate", expression="email MATCHES email_pattern", error="invalid_email"
        )

        sql = compiler.compile(step, contact_entity)

        # Expected: PostgreSQL regex operator
        assert "IF NOT (email ~ '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}') THEN" in sql

    def test_exists_query_validation(self, compiler, contact_entity):
        """Test: Compile EXISTS subquery validation"""
        step = ActionStep(
            type="validate",
            expression="NOT EXISTS Contact WHERE email = input.email",
            error="duplicate_email",
        )

        sql = compiler.compile(step, contact_entity)

        # Expected: Subquery in validation
        assert "IF NOT (NOT EXISTS (SELECT 1 FROM crm.tb_contact" in sql
        assert "WHERE email = p_email" in sql
