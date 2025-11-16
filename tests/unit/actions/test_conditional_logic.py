"""
Tests for Conditional Logic Compilation
Phase 4: Conditional Logic (if/then/else, switch)
"""

import pytest

from src.core.ast_models import ActionStep, Entity, FieldDefinition
from src.generators.actions.conditional_compiler import ConditionalCompiler


class TestConditionalLogic:
    """Test conditional logic compilation to PL/pgSQL"""

    @pytest.fixture
    def compiler(self):
        """Create conditional compiler instance"""
        return ConditionalCompiler()

    @pytest.fixture
    def contact_entity(self):
        """Create test Contact entity"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "status": FieldDefinition(name="status", type_name="text"),
                "lead_score": FieldDefinition(name="lead_score", type_name="integer"),
                "source_type": FieldDefinition(name="source_type", type_name="text"),
            },
        )

    def test_if_then_simple(self, compiler, contact_entity):
        """Test: Compile simple if/then"""
        step = ActionStep(
            type="if",
            condition="status = 'lead'",
            then_steps=[
                ActionStep(
                    type="update", entity="Contact", fields={"status": "qualified"}
                )
            ],
        )

        sql = compiler.compile(step, contact_entity)

        assert "IF (v_status = 'lead') THEN" in sql
        assert "UPDATE crm.tb_contact" in sql
        assert "END IF;" in sql

    def test_if_then_else(self, compiler, contact_entity):
        """Test: Compile if/then/else"""
        step = ActionStep(
            type="if",
            condition="lead_score >= 70",
            then_steps=[ActionStep(type="update", fields={"status": "qualified"})],
            else_steps=[ActionStep(type="update", fields={"status": "nurture"})],
        )

        sql = compiler.compile(step, contact_entity)

        assert "IF (v_lead_score >= 70) THEN" in sql
        assert "ELSE" in sql
        assert "END IF;" in sql

    def test_switch_statement(self, compiler, contact_entity):
        """Test: Compile switch/case"""
        step = ActionStep(
            type="switch",
            expression="source_type",
            cases={
                "Product": [
                    ActionStep(
                        type="insert", entity="Task", fields={"type": "follow_up"}
                    )
                ],
                "ContractItem": [
                    ActionStep(
                        type="insert", entity="Task", fields={"type": "contract_review"}
                    )
                ],
            },
        )

        sql = compiler.compile(step, contact_entity)

        assert "CASE source_type" in sql
        assert "WHEN 'Product' THEN" in sql
        assert "WHEN 'ContractItem' THEN" in sql
        assert "END CASE;" in sql
