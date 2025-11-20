"""
Tests for Conditional Logic Compilation
Phase 4: Conditional Logic (if/then/else, switch)
"""

import pytest

from core.ast_models import ActionStep, Entity, FieldDefinition
from generators.actions.conditional_compiler import ConditionalCompiler


class TestConditionalLogic:
    """Test conditional logic compilation to PL/pgSQL"""

    @pytest.fixture
    def compiler(self):
        """Create conditional compiler instance"""
        compiler = ConditionalCompiler()
        compiler.step_compiler_registry = {
            "if": compiler
        }  # Self-reference for recursive compilation
        return compiler

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
                ActionStep(type="update", entity="Contact", fields={"status": "qualified"})
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
                "Product": [ActionStep(type="insert", entity="Task", fields={"type": "follow_up"})],
                "ContractItem": [
                    ActionStep(type="insert", entity="Task", fields={"type": "contract_review"})
                ],
            },
        )

        sql = compiler.compile(step, contact_entity)

        assert "CASE source_type" in sql
        assert "WHEN 'Product' THEN" in sql
        assert "WHEN 'ContractItem' THEN" in sql
        assert "END CASE;" in sql

    def test_nested_conditionals_edge_case(self, compiler, contact_entity):
        """Test: Compile deeply nested conditionals (edge case)"""
        # Create a deeply nested conditional structure
        step = ActionStep(
            type="if",
            condition="status = 'lead'",
            then_steps=[
                ActionStep(
                    type="if",
                    condition="lead_score >= 80",
                    then_steps=[
                        ActionStep(
                            type="if",
                            condition="source_type = 'premium'",
                            then_steps=[ActionStep(type="update", fields={"status": "hot_lead"})],
                            else_steps=[ActionStep(type="update", fields={"status": "qualified"})],
                        )
                    ],
                    else_steps=[
                        ActionStep(
                            type="if",
                            condition="lead_score >= 50",
                            then_steps=[ActionStep(type="update", fields={"status": "warm_lead"})],
                            else_steps=[ActionStep(type="update", fields={"status": "cold_lead"})],
                        )
                    ],
                )
            ],
            else_steps=[ActionStep(type="update", fields={"status": "inactive"})],
        )

        sql = compiler.compile(step, contact_entity)

        # Verify the nested structure is compiled correctly
        assert "IF (v_status = 'lead') THEN" in sql
        assert "IF (v_lead_score >= 80) THEN" in sql
        assert "IF (v_source_type = 'premium') THEN" in sql
        assert "IF (v_lead_score >= 50) THEN" in sql  # Separate IF in else branch
        assert "ELSE" in sql  # For the outer else
        assert sql.count("END IF;") == 4  # Four nested IF statements
