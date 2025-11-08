from src.core.ast_models import ActionDefinition, EntityDefinition
from src.generators.actions.function_scaffolding import (
    FunctionScaffoldingGenerator,
    FunctionSignature,
)


def test_generate_signature():
    """Test function signature generation"""
    entity = EntityDefinition(name="Contact", schema="crm")
    action = ActionDefinition(name="qualify_lead", steps=[])

    generator = FunctionScaffoldingGenerator()
    scaffolding = generator.generate(action, entity)

    sig = scaffolding.signature
    assert sig.function_name == "crm.qualify_lead"
    assert sig.returns == "mutation_result"
    assert len(sig.parameters) >= 2  # entity_id + caller_id


def test_generate_variables_includes_pk():
    """Test that variables include v_pk for Trinity Pattern"""
    entity = EntityDefinition(name="Contact", schema="crm")
    action = ActionDefinition(name="qualify_lead", steps=[])

    generator = FunctionScaffoldingGenerator()
    scaffolding = generator.generate(action, entity)

    vars_str = "\n".join(scaffolding.variables)
    assert "v_pk INTEGER" in vars_str
    assert "v_result mutation_result" in vars_str


def test_render_complete_function():
    """Test complete function rendering"""
    sig = FunctionSignature(
        function_name="crm.qualify_lead",
        schema="crm",
        parameters=[
            {"name": "p_contact_id", "type": "UUID", "required": True},
            {"name": "p_caller_id", "type": "UUID", "default": "NULL"},
        ],
        returns="mutation_result",
    )

    from src.generators.actions.function_scaffolding import FunctionScaffolding

    scaffolding = FunctionScaffolding(
        signature=sig,
        variables=["v_pk INTEGER;", "v_result mutation_result;"],
        body="    -- Function body\n    v_result.status := 'success';",
        error_handling=True,
    )

    generator = FunctionScaffoldingGenerator()
    ddl = generator.render(scaffolding)

    assert "CREATE OR REPLACE FUNCTION crm.qualify_lead" in ddl
    assert "p_contact_id UUID" in ddl
    assert "p_caller_id UUID DEFAULT NULL" in ddl
    assert "RETURNS mutation_result" in ddl
    assert "v_pk INTEGER" in ddl
    assert "EXCEPTION" in ddl
    assert "LANGUAGE plpgsql" in ddl
