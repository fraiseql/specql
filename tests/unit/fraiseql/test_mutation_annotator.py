"""
Unit tests for mutation FraiseQL annotation generator
"""

import pytest
from src.core.ast_models import Action, ActionImpact, EntityImpact
from src.generators.fraiseql.mutation_annotator import MutationAnnotator


class TestCoreMutationAnnotation:
    """Test core layer function comments (no FraiseQL annotations)"""

    def test_generates_descriptive_comment(self):
        """Test: Core layer generates descriptive comment (no FraiseQL)"""
        action = Action(
            name="qualify_lead",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="update", fields=["status"])
            ),
        )

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_mutation_annotation(action)

        # Core layer should NOT have @fraiseql:mutation
        assert "COMMENT ON FUNCTION crm.qualify_lead" in sql
        assert "@fraiseql:mutation" not in sql
        assert "Core business logic for qualify lead" in sql
        assert "Called by: app.qualify_lead" in sql

    def test_includes_descriptive_comment_for_impact(self):
        """Test: Core layer includes descriptive comment for impact operations"""
        action = Action(
            name="qualify_lead",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="update", fields=["status"])
            ),
        )

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_mutation_annotation(action)

        # Core layer should have descriptive comment about the operation
        assert "COMMENT ON FUNCTION crm.qualify_lead" in sql
        assert "operation on crm.tb_contact" in sql
        assert "@fraiseql:mutation" not in sql

    def test_handles_action_without_impact(self):
        """Test: Core layer handles actions without impact metadata"""
        action = Action(name="simple_action", steps=[], impact=None)

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_mutation_annotation(action)

        assert "COMMENT ON FUNCTION crm.simple_action" in sql
        assert "@fraiseql:mutation" not in sql
        assert "Called by: app.simple_action" in sql

    def test_converts_snake_case_to_camel_case(self):
        """Test: Core layer handles snake_case action names"""
        action = Action(name="create_new_user_account", steps=[], impact=None)

        annotator = MutationAnnotator("auth", "User")
        sql = annotator.generate_mutation_annotation(action)

        # Core layer should reference the app layer function with camelCase
        assert "COMMENT ON FUNCTION auth.create_new_user_account" in sql
        assert "Called by: app.create_new_user_account" in sql
        assert "@fraiseql:mutation" not in sql

    def test_includes_primary_entity_in_comment(self):
        """Test: Core layer includes primary entity in descriptive comment"""
        action = Action(
            name="update_profile",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="User", operation="update", fields=["name", "email"])
            ),
        )

        annotator = MutationAnnotator("auth", "User")
        sql = annotator.generate_mutation_annotation(action)

        # Core layer should mention the entity in the descriptive comment
        assert "COMMENT ON FUNCTION auth.update_profile" in sql
        assert "UPDATE operation on auth.tb_user" in sql
        assert "@fraiseql:mutation" not in sql

    def test_handles_complex_action_name(self):
        """Test: Core layer handles complex action names"""
        action = Action(name="bulk_import_customer_data_from_csv", steps=[], impact=None)

        annotator = MutationAnnotator("crm", "Customer")
        sql = annotator.generate_mutation_annotation(action)

        # Core layer should reference the app layer function
        assert "COMMENT ON FUNCTION crm.bulk_import_customer_data_from_csv" in sql
        assert "Called by: app.bulk_import_customer_data_from_csv" in sql
        assert "@fraiseql:mutation" not in sql

    def test_generates_error_type_comment(self):
        """Test: Core layer includes error handling in comment"""
        action = Action(
            name="delete_item",
            steps=[],
            impact=ActionImpact(primary=EntityImpact(entity="Item", operation="delete", fields=[])),
        )

        annotator = MutationAnnotator("inventory", "Item")
        sql = annotator.generate_mutation_annotation(action)

        # Core layer should mention error handling
        assert "COMMENT ON FUNCTION inventory.delete_item" in sql
        assert "DELETE operation on inventory.tb_item" in sql
        assert "@fraiseql:mutation" not in sql

    def test_handles_different_schemas(self):
        """Test: Core layer works with different schema names"""
        schemas = ["crm", "auth", "inventory", "library", "management"]

        for schema in schemas:
            action = Action(name="test_action", steps=[], impact=None)

            annotator = MutationAnnotator(schema, "TestEntity")
            sql = annotator.generate_mutation_annotation(action)

            assert f"COMMENT ON FUNCTION {schema}.test_action" in sql
            assert f"Called by: app.test_action" in sql
            assert "@fraiseql:mutation" not in sql


class TestAppMutationAnnotation:
    """Test app layer function annotations (with FraiseQL)"""

    def test_generates_fraiseql_annotation(self):
        """Test: App layer generates @fraiseql:mutation annotation"""
        action = Action(
            name="qualify_lead",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="update", fields=["status"])
            ),
        )

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_app_mutation_annotation(action)

        # App layer SHOULD have @fraiseql:mutation
        assert "COMMENT ON FUNCTION app.qualify_lead" in sql
        assert "@fraiseql:mutation" in sql
        assert "name: qualifyLead" in sql

    def test_includes_fraiseql_metadata(self):
        """Test: App layer includes FraiseQL annotation metadata"""
        action = Action(
            name="qualify_lead",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="update", fields=["status"])
            ),
        )

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "@fraiseql:mutation" in sql
        assert "name: qualifyLead" in sql
        assert "input_type: app.type_qualify_lead_input" in sql

    def test_handles_action_without_impact(self):
        """Test: App layer handles actions without impact metadata"""
        action = Action(name="simple_action", steps=[], impact=None)

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "COMMENT ON FUNCTION app.simple_action" in sql
        assert "@fraiseql:mutation" in sql
        assert "name: simpleAction" in sql

    def test_converts_snake_case_to_camel_case(self):
        """Test: App layer converts snake_case action names to camelCase GraphQL names"""
        action = Action(name="create_new_user_account", steps=[], impact=None)

        annotator = MutationAnnotator("auth", "User")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "name: createNewUserAccount" in sql
        assert "input_type: app.type_create_new_user_account_input" in sql
        assert "success_type: CreateNewUserAccountSuccess" in sql

    def test_includes_primary_entity_in_description(self):
        """Test: App layer includes primary entity in description"""
        action = Action(
            name="update_profile",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="User", operation="update", fields=["name", "email"])
            ),
        )

        annotator = MutationAnnotator("auth", "User")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "Updates an existing User record" in sql

    def test_handles_complex_action_name(self):
        """Test: App layer handles complex action names with multiple underscores"""
        action = Action(name="bulk_import_customer_data_from_csv", steps=[], impact=None)

        annotator = MutationAnnotator("crm", "Customer")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "name: bulkImportCustomerDataFromCsv" in sql

    def test_generates_error_type_annotation(self):
        """Test: App layer generates error_type annotation"""
        action = Action(
            name="delete_item",
            steps=[],
            impact=ActionImpact(primary=EntityImpact(entity="Item", operation="delete", fields=[])),
        )

        annotator = MutationAnnotator("inventory", "Item")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "failure_type: DeleteItemError" in sql

    def test_handles_different_schemas(self):
        """Test: App layer works with different schema names"""
        schemas = ["crm", "auth", "inventory", "library", "management"]

        for schema in schemas:
            action = Action(name="test_action", steps=[], impact=None)

            annotator = MutationAnnotator(schema, "TestEntity")
            sql = annotator.generate_app_mutation_annotation(action)

            assert f"COMMENT ON FUNCTION app.test_action" in sql
            assert f"operation on TestEntity" in sql


class TestMetadataMapping:
    """Test metadata mapping generation"""

    def test_includes_impact_fields_in_description(self):
        """Test: Impact information is included in app layer description"""
        action = Action(
            name="update_contact",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(
                    entity="Contact",
                    operation="update",
                    fields=["status", "priority", "assigned_to"],
                )
            ),
        )

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_app_mutation_annotation(action)

        # The description should mention the operation type
        assert "Updates an existing Contact record" in sql

    def test_handles_multiple_impact_entities(self):
        """Test: Handles actions that impact multiple entities"""
        action = Action(
            name="transfer_ownership",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="Account", operation="update", fields=["owner_id"]),
                side_effects=[
                    EntityImpact(entity="User", operation="update", fields=["account_count"])
                ],
            ),
        )

        annotator = MutationAnnotator("crm", "Account")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "COMMENT ON FUNCTION app.transfer_ownership" in sql
        assert "@fraiseql:mutation" in sql
        assert "operation on Account" in sql

    def test_handles_create_operations(self):
        """Test: Handles create operation impacts"""
        action = Action(
            name="create_project",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(
                    entity="Project", operation="create", fields=["name", "description", "owner_id"]
                )
            ),
        )

        annotator = MutationAnnotator("pm", "Project")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "name: createProject" in sql
        assert "Creates a new Project record" in sql

    def test_handles_delete_operations(self):
        """Test: Handles delete operation impacts"""
        action = Action(
            name="archive_task",
            steps=[],
            impact=ActionImpact(primary=EntityImpact(entity="Task", operation="delete", fields=[])),
        )

        annotator = MutationAnnotator("pm", "Task")
        sql = annotator.generate_app_mutation_annotation(action)

        assert "name: archiveTask" in sql
        assert "operation on Task" in sql
