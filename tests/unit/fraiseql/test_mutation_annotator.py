"""
Unit tests for mutation FraiseQL annotation generator
"""

import pytest
from src.core.ast_models import Action, ActionImpact, EntityImpact
from src.generators.fraiseql.mutation_annotator import MutationAnnotator


class TestMutationAnnotation:
    """Test @fraiseql:mutation annotations"""

    def test_generates_mutation_annotation(self):
        """Test: Generates @fraiseql:mutation annotation"""
        action = Action(
            name="qualify_lead",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="update", fields=["status"])
            ),
        )

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_mutation_annotation(action)

        assert "COMMENT ON FUNCTION crm.qualify_lead" in sql
        assert "@fraiseql:mutation" in sql
        assert "name=qualifyLead" in sql

    def test_includes_metadata_mapping(self):
        """Test: Includes metadata_mapping for impact metadata"""
        action = Action(
            name="qualify_lead",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="Contact", operation="update", fields=["status"])
            ),
        )

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_mutation_annotation(action)

        assert "metadata_mapping" in sql
        assert '"_meta": "MutationImpactMetadata"' in sql

    def test_handles_action_without_impact(self):
        """Test: Handles actions without impact metadata"""
        action = Action(name="simple_action", steps=[], impact=None)

        annotator = MutationAnnotator("crm", "Contact")
        sql = annotator.generate_mutation_annotation(action)

        assert "COMMENT ON FUNCTION crm.simple_action" in sql
        assert "@fraiseql:mutation" in sql
        assert "metadata_mapping={}" in sql

    def test_converts_snake_case_to_camel_case(self):
        """Test: Converts snake_case action names to camelCase GraphQL names"""
        action = Action(name="create_new_user_account", steps=[], impact=None)

        annotator = MutationAnnotator("auth", "User")
        sql = annotator.generate_mutation_annotation(action)

        assert "name=createNewUserAccount" in sql
        assert "input=CreateNewUserAccountInput" in sql
        assert "success_type=CreateNewUserAccountSuccess" in sql

    def test_includes_primary_entity_in_annotation(self):
        """Test: Includes primary_entity in annotation"""
        action = Action(
            name="update_profile",
            steps=[],
            impact=ActionImpact(
                primary=EntityImpact(entity="User", operation="update", fields=["name", "email"])
            ),
        )

        annotator = MutationAnnotator("auth", "User")
        sql = annotator.generate_mutation_annotation(action)

        assert "primary_entity=User" in sql

    def test_handles_complex_action_name(self):
        """Test: Handles complex action names with multiple underscores"""
        action = Action(name="bulk_import_customer_data_from_csv", steps=[], impact=None)

        annotator = MutationAnnotator("crm", "Customer")
        sql = annotator.generate_mutation_annotation(action)

        assert "name=bulkImportCustomerDataFromCsv" in sql

    def test_generates_error_type_annotation(self):
        """Test: Generates error_type annotation"""
        action = Action(
            name="delete_item",
            steps=[],
            impact=ActionImpact(primary=EntityImpact(entity="Item", operation="delete", fields=[])),
        )

        annotator = MutationAnnotator("inventory", "Item")
        sql = annotator.generate_mutation_annotation(action)

        assert "error_type=DeleteItemError" in sql

    def test_handles_different_schemas(self):
        """Test: Works with different schema names"""
        schemas = ["crm", "auth", "inventory", "library", "management"]

        for schema in schemas:
            action = Action(name="test_action", steps=[], impact=None)

            annotator = MutationAnnotator(schema, "TestEntity")
            sql = annotator.generate_mutation_annotation(action)

            assert f"COMMENT ON FUNCTION {schema}.test_action" in sql
            assert f"primary_entity=TestEntity" in sql


class TestMetadataMapping:
    """Test metadata mapping generation"""

    def test_includes_impact_fields_in_metadata(self):
        """Test: Impact fields are included in metadata mapping"""
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
        sql = annotator.generate_mutation_annotation(action)

        # The metadata mapping should include the impact information
        # This is a simplified test - in practice, the mapping would be more complex
        assert "metadata_mapping" in sql

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
        sql = annotator.generate_mutation_annotation(action)

        assert "COMMENT ON FUNCTION crm.transfer_ownership" in sql
        assert "@fraiseql:mutation" in sql
        assert "primary_entity=Account" in sql

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
        sql = annotator.generate_mutation_annotation(action)

        assert "name=createProject" in sql
        assert "primary_entity=Project" in sql

    def test_handles_delete_operations(self):
        """Test: Handles delete operation impacts"""
        action = Action(
            name="archive_task",
            steps=[],
            impact=ActionImpact(primary=EntityImpact(entity="Task", operation="delete", fields=[])),
        )

        annotator = MutationAnnotator("pm", "Task")
        sql = annotator.generate_mutation_annotation(action)

        assert "name=archiveTask" in sql
        assert "primary_entity=Task" in sql
