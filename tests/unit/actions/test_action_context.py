"""
Test ActionContext and AST integration
"""

from src.core.ast_models import ActionDefinition, ActionStep
from src.generators.actions.action_context import ActionContext


def test_action_context_from_ast():
    """Build compilation context from action AST"""
    action_ast = ActionDefinition(
        name="qualify_lead",
        steps=[
            ActionStep(type="validate", expression="status = 'lead'", error="not_a_lead"),
            ActionStep(type="update", entity="Contact", fields={"status": "'qualified'"}),
        ],
        impact={
            "primary": {
                "entity": "Contact",
                "operation": "UPDATE",
                "fields": ["status", "updatedAt"],
            }
        },
    )

    entity_ast = type("MockEntity", (), {"schema": "crm", "name": "Contact"})()

    context = ActionContext.from_ast(action_ast, entity_ast)

    assert context.function_name == "crm.qualify_lead"
    assert context.entity_schema == "crm"
    assert context.entity_name == "Contact"
    assert len(context.steps) == 2
    assert context.has_impact_metadata is True
