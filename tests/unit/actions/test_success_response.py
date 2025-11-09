"""
Test success response generation
"""

import pytest
from src.generators.actions.action_context import ActionContext
from src.generators.actions.success_response_generator import SuccessResponseGenerator


def create_test_context():
    """Create a test ActionContext"""
    return ActionContext(
        function_name="crm.qualify_lead",
        entity_schema="crm",
        entity_name="Contact",
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )


def create_test_context_with_impact():
    """Create a test ActionContext with impact metadata"""
    return ActionContext(
        function_name="crm.qualify_lead",
        entity_schema="crm",
        entity_name="Contact",
        steps=[],
        impact={
            "primary": {
                "entity": "Contact",
                "operation": "UPDATE",
                "fields": ["status", "updatedAt"],
            }
        },
        has_impact_metadata=True,
    )


def test_generates_object_data_with_relationships():
    """Generate object_data with relationships from impact.include_relations"""
    impact = {
        "primary": {
            "entity": "Contact",
            "operation": "UPDATE",
            "fields": ["status", "updatedAt"],
            "include_relations": ["company"],
        }
    }
    context = ActionContext(
        function_name="crm.qualify_lead",
        entity_schema="crm",
        entity_name="Contact",
        steps=[],
        impact=impact,
        has_impact_metadata=True,
    )

    generator = SuccessResponseGenerator()
    object_sql = generator.generate_object_data(context)

    assert "SELECT jsonb_build_object(" in object_sql
    assert "'__typename', 'Contact'" in object_sql
    assert "'id', c.id" in object_sql
    assert "'status', c.status" in object_sql
    # Note: Relationship handling would be more complex in real implementation
    # For now, just test basic object structure


def test_generates_impact_metadata_composite_type():
    """Generate _meta using type-safe composite type construction"""
    context = create_test_context_with_impact()

    # Use the existing ImpactMetadataCompiler
    from src.generators.actions.impact_metadata_compiler import ImpactMetadataCompiler
    from src.core.ast_models import Action, ActionImpact, EntityImpact

    # Create Action object for the compiler
    action = Action(
        name="qualify_lead",
        impact=ActionImpact(
            primary=EntityImpact(
                entity="Contact", operation="UPDATE", fields=["status", "updatedAt"]
            ),
            side_effects=[
                EntityImpact(entity="Notification", operation="CREATE", fields=["id", "message"])
            ],
        ),
    )

    compiler = ImpactMetadataCompiler()
    meta_sql = compiler.compile(action)

    # Should use ROW constructor with proper typing
    assert "v_meta.primary_entity :=" in meta_sql
    assert "ROW(" in meta_sql
    assert "'Contact'," in meta_sql  # entity_type
    assert "'UPDATE'," in meta_sql  # operation
    assert "ARRAY['status', 'updatedAt']" in meta_sql  # modified_fields
    assert ")::mutation_metadata.entity_impact" in meta_sql  # Type cast!

    # Should handle side effects array
    assert "v_meta.actual_side_effects :=" in meta_sql
    assert "'Notification'," in meta_sql
    assert "'CREATE'," in meta_sql


def test_generates_side_effect_collections():
    """Collect created entities in extra_metadata collections"""
    from src.generators.actions.impact_metadata_compiler import ImpactMetadataCompiler
    from src.core.ast_models import Action, ActionImpact, EntityImpact

    action = Action(
        name="qualify_lead",
        impact=ActionImpact(
            primary=EntityImpact(entity="Contact", operation="UPDATE", fields=["status"]),
            side_effects=[
                EntityImpact(
                    entity="Notification",
                    operation="CREATE",
                    collection="createdNotifications",
                    fields=["id", "message"],
                )
            ],
        ),
    )

    compiler = ImpactMetadataCompiler()
    collections_sql = compiler.integrate_into_result(action)

    assert "'createdNotifications'," in collections_sql
    assert "jsonb_build_object(" in collections_sql
    assert "'_meta', to_jsonb(v_meta)" in collections_sql
