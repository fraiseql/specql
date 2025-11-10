"""Pytest integration test generator for database testing."""

import json
from typing import Any


class PytestGenerator:
    """Generates pytest integration tests from entity configurations and test metadata."""

    def __init__(self):
        """Initialize the pytest generator."""
        pass

    def generate_pytest_integration_tests(
        self, entity_config: dict[str, Any], actions: list[dict[str, Any]]
    ) -> str:
        """Generate pytest integration tests for an entity.

        Args:
            entity_config: Entity configuration dictionary
            actions: List of action dictionaries for the entity

        Returns:
            Python code string containing pytest integration tests
        """
        entity = entity_config["entity_name"]
        schema = entity_config["schema_name"]

        # Build sample input data based on entity config
        sample_input_data = self._build_sample_input_data(entity_config)

        # Generate action test methods
        action_test_methods = []
        for action in actions:
            action_test_methods.append(self._generate_action_test_method(action, entity_config))

        return f'''"""Integration tests for {entity} entity"""

import pytest
from uuid import UUID
import psycopg


class Test{entity}Integration:
    """Integration tests for {entity} CRUD and actions"""

    @pytest.fixture
    def clean_db(self, test_db_connection):
        """Clean {entity} table before test"""
        with test_db_connection.cursor() as cur:
            cur.execute("DELETE FROM {schema}.{entity_config["table_name"]}")
        test_db_connection.commit()
        yield test_db_connection

    def test_create_{entity.lower()}_happy_path(self, clean_db):
        """Test creating {entity} via app.create function"""
        tenant_id = UUID("{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}")
        user_id = UUID("{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}")

        with clean_db.cursor() as cur:
            cur.execute(
                """
                SELECT app.create_{entity.lower()}(
                    %s::UUID,
                    %s::UUID,
                    %s::JSONB
                )
                """,
                (tenant_id, user_id, {json.dumps(sample_input_data)})
            )
            result = cur.fetchone()[0]

        assert result['status'] == 'success'
        assert result['object_data']['id'] is not None
        assert result['object_data']['email'] == 'test@example.com'

    def test_create_duplicate_{entity.lower()}_fails(self, clean_db):
        """Test duplicate {entity} fails with proper error"""
        tenant_id = UUID("{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}")
        user_id = UUID("{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}")
        input_data = {json.dumps(sample_input_data)}

        with clean_db.cursor() as cur:
            # First insert
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, input_data)
            )
            result1 = cur.fetchone()[0]
            assert result1['status'] == 'success'

            # Duplicate insert
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, input_data)
            )
            result2 = cur.fetchone()[0]

        assert result2['status'].startswith('failed:')
        assert 'duplicate' in result2['message'].lower()

    def test_update_{entity.lower()}_happy_path(self, clean_db):
        """Test updating {entity} via app.update function"""
        tenant_id = UUID("{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}")
        user_id = UUID("{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}")

        with clean_db.cursor() as cur:
            # Create first
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, {json.dumps(sample_input_data)})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Update
            update_data = {{"status": "qualified"}}
            cur.execute(
                """
                SELECT app.update_{entity.lower()}(
                    %s::UUID,
                    %s::UUID,
                    %s::UUID,
                    %s::JSONB
                )
                """,
                (tenant_id, user_id, contact_id, json.dumps(update_data))
            )
            update_result = cur.fetchone()[0]

        assert update_result['status'] == 'success'
        assert update_result['object_data']['status'] == 'qualified'

    def test_delete_{entity.lower()}_happy_path(self, clean_db):
        """Test deleting {entity} via app.delete function"""
        tenant_id = UUID("{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}")
        user_id = UUID("{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}")

        with clean_db.cursor() as cur:
            # Create first
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, {json.dumps(sample_input_data)})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Delete
            cur.execute(
                """
                SELECT app.delete_{entity.lower()}(
                    %s::UUID,
                    %s::UUID,
                    %s::UUID
                )
                """,
                (tenant_id, user_id, contact_id)
            )
            delete_result = cur.fetchone()[0]

        assert delete_result['status'] == 'success'

    def test_full_crud_workflow(self, clean_db):
        """Test complete CRUD workflow: create → read → update → delete"""
        tenant_id = UUID("{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}")
        user_id = UUID("{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}")

        with clean_db.cursor() as cur:
            # CREATE
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, {json.dumps(sample_input_data)})
            )
            create_result = cur.fetchone()[0]
            assert create_result['status'] == 'success'
            contact_id = UUID(create_result['object_data']['id'])

            # READ (verify exists)
            cur.execute(
                "SELECT COUNT(*) FROM {schema}.{entity_config["table_name"]} WHERE id = %s",
                (contact_id,)
            )
            count = cur.fetchone()[0]
            assert count == 1

            # UPDATE
            update_data = {{"status": "qualified"}}
            cur.execute(
                "SELECT app.update_{entity.lower()}(%s, %s, %s, %s)",
                (tenant_id, user_id, contact_id, json.dumps(update_data))
            )
            update_result = cur.fetchone()[0]
            assert update_result['status'] == 'success'

            # DELETE
            cur.execute(
                "SELECT app.delete_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, contact_id)
            )
            delete_result = cur.fetchone()[0]
            assert delete_result['status'] == 'success'

            # VERIFY DELETED
            cur.execute(
                "SELECT COUNT(*) FROM {schema}.{entity_config["table_name"]} WHERE id = %s",
                (contact_id,)
            )
            final_count = cur.fetchone()[0]
            assert final_count == 0

{"".join(action_test_methods)}
'''

    def _build_sample_input_data(self, entity_config: dict[str, Any]) -> dict[str, Any]:
        """Build sample input data for testing based on entity config."""
        # This is a simplified version - in practice this would be more sophisticated
        # and based on the actual field mappings from the metadata
        return {
            "email": "test@example.com",
            "status": "lead",
            "first_name": "Test",
            "last_name": "User",
        }

    def _generate_action_test_method(
        self, action: dict[str, Any], entity_config: dict[str, Any]
    ) -> str:
        """Generate a test method for a custom action."""
        action_name = action["name"]
        entity = entity_config["entity_name"]
        schema = entity_config["schema_name"]

        return f'''
    def test_{action_name}(self, clean_db):
        """Test {action_name} action"""
        tenant_id = UUID("{entity_config.get("default_tenant_id", "01232122-0000-0000-2000-000000000001")}")
        user_id = UUID("{entity_config.get("default_user_id", "01232122-0000-0000-2000-000000000002")}")

        with clean_db.cursor() as cur:
            # Setup: Create {entity} with appropriate status
            cur.execute(
                "SELECT app.create_{entity.lower()}(%s, %s, %s)",
                (tenant_id, user_id, {{"email": "qualify@example.com", "status": "lead"}})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Execute action
            cur.execute(
                "SELECT {schema}.{action_name}(%s, %s)",
                (contact_id, user_id)
            )
            action_result = cur.fetchone()[0]

        assert action_result['status'] == 'success'
        assert action_result['object_data']['status'] == 'qualified'
'''
