"""
Test if step compilation
"""

import pytest

from src.core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from src.generators.actions.step_compilers.if_compiler import IfStepCompiler
from src.generators.actions.step_compilers.update_compiler import UpdateStepCompiler


def create_test_entity():
    """Create a test EntityDefinition"""
    return EntityDefinition(
        name="Contact",
        schema="crm",
        fields={
            "status": FieldDefinition(name="status", type_name="text"),
            "email": FieldDefinition(name="email", type_name="text"),
            "lead_score": FieldDefinition(name="lead_score", type_name="integer"),
        },
    )


def test_compile_if_then_simple():
    """Compile simple if/then step to PL/pgSQL IF block"""
    step = ActionStep(
        type="if",
        condition="status = 'lead'",
        then_steps=[ActionStep(type="update", fields={"raw_set": "status = 'qualified'"})],
    )
    entity = create_test_entity()
    context = {}

    # Create compiler with step compiler registry
    step_compiler_registry = {
        "update": UpdateStepCompiler(),
    }
    compiler = IfStepCompiler(step_compiler_registry)

    sql = compiler.compile(step, entity, context)

    # Should contain IF block with condition
    assert "IF (v_status = 'lead') THEN" in sql
    # Should contain the nested update step
    assert "UPDATE crm.tb_contact" in sql
    assert "SET status = 'qualified'" in sql
    # Should close the IF block
    assert "END IF;" in sql


def test_compile_if_then_else():
    """Compile if/then/else step to PL/pgSQL IF/ELSE block"""
    step = ActionStep(
        type="if",
        condition="lead_score >= 70",
        then_steps=[ActionStep(type="update", fields={"raw_set": "status = 'qualified'"})],
        else_steps=[ActionStep(type="update", fields={"raw_set": "status = 'nurture'"})],
    )
    entity = create_test_entity()
    context = {}

    step_compiler_registry = {
        "update": UpdateStepCompiler(),
    }
    compiler = IfStepCompiler(step_compiler_registry)

    sql = compiler.compile(step, entity, context)

    # Should contain IF block with condition
    assert "IF (v_lead_score >= 70) THEN" in sql
    # Should contain then branch
    assert "status = 'qualified'" in sql
    # Should contain else branch
    assert "ELSE" in sql
    assert "status = 'nurture'" in sql
    # Should close the IF block
    assert "END IF;" in sql


def test_compile_if_multiple_fields():
    """Compile if step with multiple fields in condition"""
    step = ActionStep(
        type="if",
        condition="status = 'lead' AND lead_score >= 50",
        then_steps=[ActionStep(type="update", fields={"raw_set": "status = 'qualified'"})],
    )
    entity = create_test_entity()
    context = {}

    step_compiler_registry = {
        "update": UpdateStepCompiler(),
    }
    compiler = IfStepCompiler(step_compiler_registry)

    sql = compiler.compile(step, entity, context)

    # Should fetch both fields
    assert "SELECT status, lead_score INTO v_status, v_lead_score" in sql
    # Should replace field names with variables in condition
    assert "IF (v_status = 'lead' AND v_lead_score >= 50) THEN" in sql


def test_compile_if_no_condition():
    """Test error when if step has no condition"""
    step = ActionStep(
        type="if",
        then_steps=[ActionStep(type="update", fields={"raw_set": "status = 'qualified'"})],
    )
    entity = create_test_entity()
    context = {}

    compiler = IfStepCompiler()

    with pytest.raises(ValueError, match="If step must have a condition"):
        compiler.compile(step, entity, context)


def test_compile_if_wrong_type():
    """Test error when wrong step type passed to if compiler"""
    step = ActionStep(
        type="update",
        fields={"raw_set": "status = 'qualified'"},
    )
    entity = create_test_entity()
    context = {}

    compiler = IfStepCompiler()

    with pytest.raises(ValueError, match="Expected if step, got update"):
        compiler.compile(step, entity, context)


def test_compile_if_no_then_steps():
    """Test error when if step has no then_steps"""
    step = ActionStep(
        type="if",
        condition="status = 'lead'",
        then_steps=[],
    )
    entity = create_test_entity()
    context = {}

    compiler = IfStepCompiler()

    # Should not raise error, just compile empty then block
    sql = compiler.compile(step, entity, context)
    assert "IF (v_status = 'lead') THEN" in sql
    assert "END IF;" in sql
