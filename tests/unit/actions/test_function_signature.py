"""
Test function signature generation
"""

import pytest
from src.generators.actions.function_generator import FunctionGenerator
from src.generators.actions.action_context import ActionContext


def create_test_context():
    """Create a test ActionContext"""
    from src.core.ast_models import EntityDefinition

    # Create minimal entity
    entity = EntityDefinition(name="Contact", schema="crm", fields={})

    return ActionContext(
        function_name="crm.qualify_lead",
        entity_schema="crm",
        entity_name="Contact",
        entity=entity,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )


def test_generate_function_signature():
    """Generate proper function signature from action context"""
    context = create_test_context()

    generator = FunctionGenerator()
    signature = generator.generate_signature(context)

    assert "CREATE OR REPLACE FUNCTION crm.qualify_lead(" in signature
    assert "p_contact_id UUID" in signature
    assert "p_caller_id UUID DEFAULT NULL" in signature
    assert "RETURNS mutation_result" in signature


def test_generate_declare_block():
    """Generate DECLARE block with proper variable types"""
    context = create_test_context()

    generator = FunctionGenerator()
    declare_block = generator.generate_declare_block(context)

    assert "DECLARE" in declare_block
    assert "v_pk INTEGER" in declare_block  # Trinity resolution
    assert "v_result mutation_result" in declare_block  # Return value


def test_generate_declare_block_with_impact():
    """Generate DECLARE block with impact metadata when needed"""
    from src.core.ast_models import EntityDefinition

    entity = EntityDefinition(name="Contact", schema="crm", fields={})

    context = ActionContext(
        function_name="crm.qualify_lead",
        entity_schema="crm",
        entity_name="Contact",
        entity=entity,
        steps=[],
        impact={"primary": {"entity": "Contact", "operation": "UPDATE"}},
        has_impact_metadata=True,
    )

    generator = FunctionGenerator()
    declare_block = generator.generate_declare_block(context)

    assert "v_meta mutation_metadata.mutation_impact_metadata" in declare_block


def test_generates_trinity_resolution():
    """Auto-generate Trinity helper call"""
    context = create_test_context()

    generator = FunctionGenerator()
    resolution = generator.generate_trinity_resolution(context)

    assert "v_pk := crm.contact_pk(p_contact_id)" in resolution
