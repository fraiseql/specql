"""
End-to-end integration test for mutation FraiseQL annotations
Tests that actions with impact metadata generate proper FraiseQL annotations
"""

import pytest
from src.generators.schema_orchestrator import SchemaOrchestrator
from src.core.ast_models import Entity, Action, ActionImpact, EntityImpact


@pytest.fixture
def entity_with_actions():
    """Create a test entity with actions that have impact metadata"""
    # Create actions with different impact patterns
    qualify_action = Action(
        name="qualify_lead",
        steps=[],
        impact=ActionImpact(
            primary=EntityImpact(
                entity="Contact", operation="update", fields=["status", "qualified_at"]
            )
        ),
    )

    create_action = Action(
        name="create_project",
        steps=[],
        impact=ActionImpact(
            primary=EntityImpact(
                entity="Project", operation="create", fields=["name", "description", "owner_id"]
            )
        ),
    )

    complex_action = Action(
        name="transfer_ownership",
        steps=[],
        impact=ActionImpact(
            primary=EntityImpact(
                entity="Account", operation="update", fields=["owner_id", "transferred_at"]
            ),
            side_effects=[
                EntityImpact(entity="User", operation="update", fields=["account_count"]),
                EntityImpact(
                    entity="AuditLog",
                    operation="create",
                    fields=["action", "old_owner", "new_owner"],
                ),
            ],
        ),
    )

    # Create entity
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={},
        actions=[qualify_action, create_action, complex_action],
    )

    return entity


class TestMutationAnnotationsEndToEnd:
    """Test complete mutation annotation generation pipeline"""

    def test_schema_generation_includes_mutation_annotations(self, entity_with_actions):
        """Test: Schema generation includes FraiseQL mutation annotations"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Should contain FraiseQL mutation annotations
        assert "@fraiseql:mutation" in schema_sql
        assert "COMMENT ON FUNCTION crm.qualify_lead" in schema_sql
        assert "COMMENT ON FUNCTION crm.create_project" in schema_sql
        assert "COMMENT ON FUNCTION crm.transfer_ownership" in schema_sql

    def test_qualify_lead_annotation_structure(self, entity_with_actions):
        """Test: qualify_lead action generates correct annotation structure"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Find the qualify_lead annotation
        assert "name=qualifyLead" in schema_sql
        assert "input=QualifyLeadInput" in schema_sql
        assert "success_type=QualifyLeadSuccess" in schema_sql
        assert "error_type=QualifyLeadError" in schema_sql
        assert "primary_entity=Contact" in schema_sql

    def test_create_project_annotation_structure(self, entity_with_actions):
        """Test: create_project action generates correct annotation structure"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Find the create_project annotation
        assert "name=createProject" in schema_sql
        assert "input=CreateProjectInput" in schema_sql
        assert "success_type=CreateProjectSuccess" in schema_sql
        assert "error_type=CreateProjectError" in schema_sql

    def test_transfer_ownership_complex_annotation(self, entity_with_actions):
        """Test: transfer_ownership action with side effects generates correct annotation"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Find the transfer_ownership annotation
        assert "name=transferOwnership" in schema_sql
        assert "input=TransferOwnershipInput" in schema_sql
        assert "primary_entity=Contact" in schema_sql

        # Should include metadata mapping with side effects
        assert "metadata_mapping" in schema_sql
        assert '"_meta": "MutationImpactMetadata"' in schema_sql
        assert '"primary_impact"' in schema_sql
        assert '"side_effects"' in schema_sql

    def test_annotations_apply_to_database(self, db, entity_with_actions):
        """Test: Generated annotations can be applied to database"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        cursor = db.cursor()

        # Apply the schema
        cursor.execute(schema_sql)
        db.commit()

        # Verify functions exist
        cursor.execute("""
            SELECT proname
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'crm'
              AND p.proname IN ('qualify_lead', 'create_project', 'transfer_ownership')
        """)
        functions = cursor.fetchall()
        function_names = [f[0] for f in functions]

        assert "qualify_lead" in function_names
        assert "create_project" in function_names
        assert "transfer_ownership" in function_names

    def test_function_comments_contain_fraiseql_annotations(self, db, entity_with_actions):
        """Test: Function comments contain FraiseQL annotations"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        cursor = db.cursor()
        cursor.execute(schema_sql)
        db.commit()

        # Check qualify_lead comment
        cursor.execute("""
            SELECT obj_description(
                (SELECT oid FROM pg_proc p
                 JOIN pg_namespace n ON p.pronamespace = n.oid
                 WHERE n.nspname = 'crm' AND p.proname = 'qualify_lead'),
                'pg_proc'
            )
        """)
        comment = cursor.fetchone()
        assert comment is not None
        assert "@fraiseql:mutation" in comment[0]
        assert "name=qualifyLead" in comment[0]

    def test_metadata_mapping_includes_impact_details(self, db, entity_with_actions):
        """Test: Metadata mapping includes detailed impact information"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        cursor = db.cursor()
        cursor.execute(schema_sql)
        db.commit()

        # Check transfer_ownership comment (has side effects)
        cursor.execute("""
            SELECT obj_description(
                (SELECT oid FROM pg_proc p
                 JOIN pg_namespace n ON p.pronamespace = n.oid
                 WHERE n.nspname = 'crm' AND p.proname = 'transfer_ownership'),
                'pg_proc'
            )
        """)
        comment = cursor.fetchone()
        assert comment is not None

        comment_text = comment[0]
        assert '"_meta": "MutationImpactMetadata"' in comment_text
        assert '"primary_impact"' in comment_text
        assert '"operation": "update"' in comment_text
        assert '"entity": "Account"' in comment_text
        assert '"side_effects"' in comment_text

    def test_actions_without_impact_get_basic_annotations(self, db):
        """Test: Actions without impact metadata still get basic annotations"""
        # Create entity with action that has no impact
        simple_action = Action(name="simple_update", steps=[], impact=None)

        entity = Entity(name="TestEntity", schema="test", fields={}, actions=[simple_action])

        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity)

        # Should still generate annotation but with empty metadata_mapping
        assert "@fraiseql:mutation" in schema_sql
        assert "name=simpleUpdate" in schema_sql
        assert "metadata_mapping={}" in schema_sql

    def test_multiple_actions_generate_separate_annotations(self, entity_with_actions):
        """Test: Multiple actions generate separate annotations"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Count occurrences of @fraiseql:mutation
        mutation_count = schema_sql.count("@fraiseql:mutation")
        assert mutation_count == 3  # One for each action

        # Each action should have its own comment
        assert schema_sql.count("COMMENT ON FUNCTION crm.qualify_lead") == 1
        assert schema_sql.count("COMMENT ON FUNCTION crm.create_project") == 1
        assert schema_sql.count("COMMENT ON FUNCTION crm.transfer_ownership") == 1
