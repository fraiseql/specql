"""
End-to-end integration test for mutation FraiseQL annotations
Tests that actions with impact metadata generate proper FraiseQL annotations
"""

import pytest

# Mark all tests as requiring database
pytestmark = pytest.mark.database
from core.ast_models import Action, ActionImpact, Entity, EntityImpact, FieldDefinition
from generators.schema_orchestrator import SchemaOrchestrator


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
        name="create_contact",
        steps=[],
        impact=ActionImpact(
            primary=EntityImpact(
                entity="Contact", operation="create", fields=["first_name", "last_name", "email"]
            )
        ),
    )

    complex_action = Action(
        name="update_contact",
        steps=[],
        impact=ActionImpact(
            primary=EntityImpact(
                entity="Contact", operation="update", fields=["status", "updated_at"]
            ),
            side_effects=[
                EntityImpact(
                    entity="AuditLog", operation="create", fields=["action", "contact_id"]
                ),
            ],
        ),
    )

    # Create entity
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "first_name": FieldDefinition(name="first_name", type_name="text", nullable=False),
            "last_name": FieldDefinition(name="last_name", type_name="text", nullable=False),
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
            "status": FieldDefinition(name="status", type_name="text", nullable=False),
            "qualified_at": FieldDefinition(
                name="qualified_at", type_name="timestamp", nullable=True
            ),
        },
        actions=[qualify_action, create_action, complex_action],
    )

    return entity


class TestMutationAnnotationsEndToEnd:
    """Test complete mutation annotation generation pipeline"""

    def test_schema_generation_includes_mutation_annotations(self, entity_with_actions):
        """Test: Schema generation includes mutation annotations for all actions"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Core layer functions should have descriptive comments
        assert "COMMENT ON FUNCTION crm.qualify_lead" in schema_sql
        assert "COMMENT ON FUNCTION crm.create_contact" in schema_sql
        assert "COMMENT ON FUNCTION crm.update_contact" in schema_sql
        assert "Core business logic" in schema_sql

        # App layer functions should have @fraiseql:mutation annotations
        assert "COMMENT ON FUNCTION app.qualify_lead" in schema_sql
        assert "COMMENT ON FUNCTION app.create_contact" in schema_sql
        assert "COMMENT ON FUNCTION app.update_contact" in schema_sql
        assert "@fraiseql:mutation" in schema_sql  # App layer has this

    def test_qualify_lead_annotation_structure(self, entity_with_actions):
        """Test: qualify_lead action generates correct core and app layer comments"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Core layer should have descriptive comment
        assert "COMMENT ON FUNCTION crm.qualify_lead" in schema_sql
        assert "Core business logic for qualify lead" in schema_sql
        assert "Called by: app.qualify_lead" in schema_sql

        # App layer should have @fraiseql:mutation annotation
        assert "COMMENT ON FUNCTION app.qualify_lead" in schema_sql
        assert "@fraiseql:mutation" in schema_sql
        assert "name: qualifyLead" in schema_sql

    def test_create_contact_annotation_structure(self, entity_with_actions):
        """Test: create_contact action generates correct core and app layer comments"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        assert "COMMENT ON FUNCTION crm.create_contact" in schema_sql
        assert "Called by: app.create_contact" in schema_sql

        # App layer should have @fraiseql:mutation annotation
        assert "COMMENT ON FUNCTION app.create_contact" in schema_sql
        assert "@fraiseql:mutation" in schema_sql
        assert "name: createContact" in schema_sql

        # Core layer doesn't include metadata mapping - that's for app layer
        # assert "metadata_mapping" in schema_sql

    def test_annotations_apply_to_database(self, test_db, isolated_schema, entity_with_actions):
        """Test: Generated annotations can be applied to database"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Replace schema references with isolated schema
        schema_sql = schema_sql.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
        schema_sql = schema_sql.replace("crm.", f"{isolated_schema}.")
        schema_sql = schema_sql.replace("CREATE SCHEMA app", f"CREATE SCHEMA {isolated_schema}app")
        schema_sql = schema_sql.replace("app.", f"{isolated_schema}app.")
        schema_sql = schema_sql.replace("CREATE SCHEMA test", f"CREATE SCHEMA {isolated_schema}")
        schema_sql = schema_sql.replace("test.", f"{isolated_schema}.")

        cursor = test_db.cursor()

        # Create the app schema first
        app_schema = f"{isolated_schema}app"
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {app_schema}")

        # Apply the schema
        cursor.execute(schema_sql)
        test_db.commit()

        # Verify functions exist
        cursor.execute(
            f"""
            SELECT proname
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = '{isolated_schema}'
              AND p.proname IN ('qualify_lead', 'create_contact', 'update_contact')
        """
        )
        functions = cursor.fetchall()
        function_names = [f[0] for f in functions]

        assert "qualify_lead" in function_names
        assert "create_contact" in function_names
        assert "update_contact" in function_names

    def test_function_comments_contain_fraiseql_annotations(
        self, test_db, isolated_schema, entity_with_actions
    ):
        """Test: Function comments contain FraiseQL annotations"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Replace schema references with isolated schema
        schema_sql = schema_sql.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
        schema_sql = schema_sql.replace("crm.", f"{isolated_schema}.")
        schema_sql = schema_sql.replace("CREATE SCHEMA app", f"CREATE SCHEMA {isolated_schema}app")
        schema_sql = schema_sql.replace("app.", f"{isolated_schema}app.")

        cursor = test_db.cursor()

        # Create the app schema first
        app_schema = f"{isolated_schema}app"
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {app_schema}")

        cursor.execute(schema_sql)
        test_db.commit()

        # Check qualify_lead comment
        cursor.execute(
            f"""
            SELECT obj_description(p.oid, 'pg_proc')
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = '{isolated_schema}' AND p.proname = 'qualify_lead'
        """
        )
        comment = cursor.fetchone()
        assert comment is not None
        # Core functions don't have @fraiseql:mutation annotations
        assert "Core business logic for qualify lead" in comment[0]
        assert "Called by:" in comment[0]

    def test_metadata_mapping_includes_impact_details(
        self, test_db, isolated_schema, entity_with_actions
    ):
        """Test: Metadata mapping includes detailed impact information"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # Replace schema references with isolated schema
        schema_sql = schema_sql.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
        schema_sql = schema_sql.replace("crm.", f"{isolated_schema}.")
        schema_sql = schema_sql.replace("CREATE SCHEMA app", f"CREATE SCHEMA {isolated_schema}app")
        schema_sql = schema_sql.replace("app.", f"{isolated_schema}app.")

        cursor = test_db.cursor()

        # Create the app schema first
        app_schema = f"{isolated_schema}app"
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {app_schema}")

        cursor.execute(schema_sql)
        test_db.commit()

        # Check update_contact comment (has side effects)
        cursor.execute(
            f"""
            SELECT obj_description(p.oid, 'pg_proc')
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = '{isolated_schema}' AND p.proname = 'update_contact'
        """
        )
        result = cursor.fetchone()
        comment_text = result[0] if result else ""
        assert "update_contact" in comment_text
        assert f"Called by: {isolated_schema}app.update_contact" in comment_text
        # Core functions have descriptive comments but not JSON metadata mapping
        assert "UPDATE operation" in comment_text

    def test_actions_without_impact_get_basic_annotations(self, test_db):
        """Test: Actions without impact metadata get basic annotations"""
        simple_action = Action(name="simple_update", steps=[], impact=None)

        entity = Entity(name="TestEntity", schema="test", fields={}, actions=[simple_action])

        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity)

        # Core layer functions have descriptive comments
        assert "COMMENT ON FUNCTION test.simple_update" in schema_sql
        # App layer functions have @fraiseql:mutation annotations
        assert "COMMENT ON FUNCTION app.simple_update" in schema_sql
        assert "@fraiseql:mutation" in schema_sql

    def test_multiple_actions_generate_separate_annotations(self, entity_with_actions):
        """Test: Multiple actions generate separate core and app layer comments"""
        orchestrator = SchemaOrchestrator()
        schema_sql = orchestrator.generate_complete_schema(entity_with_actions)

        # App layer has @fraiseql:mutation annotations (one per action)
        mutation_count = schema_sql.count("@fraiseql:mutation")
        assert mutation_count == 3

        # Each action should have core and app layer comments
        assert schema_sql.count("COMMENT ON FUNCTION crm.qualify_lead") == 1
        assert schema_sql.count("COMMENT ON FUNCTION crm.create_contact") == 1
        assert schema_sql.count("COMMENT ON FUNCTION crm.update_contact") == 1
        assert schema_sql.count("COMMENT ON FUNCTION app.qualify_lead") == 1
        assert schema_sql.count("COMMENT ON FUNCTION app.create_contact") == 1
        assert schema_sql.count("COMMENT ON FUNCTION app.update_contact") == 1
