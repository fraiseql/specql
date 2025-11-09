"""Integration tests for Contact entity"""

import pytest
from uuid import UUID
import psycopg


class TestContactIntegration:
    """Integration tests for Contact CRUD and actions"""

    @pytest.fixture
    def clean_db(self, test_db_connection):
        """Clean Contact table before test"""
        with test_db_connection.cursor() as cur:
            cur.execute("DELETE FROM crm.tb_contact")
        test_db_connection.commit()
        yield test_db_connection

    def test_create_contact_happy_path(self, clean_db):
        """Test creating Contact via app.create function"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            cur.execute(
                """
                SELECT app.create_contact(
                    %s::UUID,
                    %s::UUID,
                    %s::JSONB
                )
                """,
                (tenant_id, user_id, {"email": "test@example.com", "status": "lead", "first_name": "Test", "last_name": "User"})
            )
            result = cur.fetchone()[0]

        assert result['status'] == 'success'
        assert result['object_data']['id'] is not None
        assert result['object_data']['email'] == 'test@example.com'

    def test_create_duplicate_contact_fails(self, clean_db):
        """Test duplicate Contact fails with proper error"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")
        input_data = {"email": "test@example.com", "status": "lead", "first_name": "Test", "last_name": "User"}

        with clean_db.cursor() as cur:
            # First insert
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (tenant_id, user_id, input_data)
            )
            result1 = cur.fetchone()[0]
            assert result1['status'] == 'success'

            # Duplicate insert
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (tenant_id, user_id, input_data)
            )
            result2 = cur.fetchone()[0]

        assert result2['status'].startswith('failed:')
        assert 'duplicate' in result2['message'].lower()

    def test_update_contact_happy_path(self, clean_db):
        """Test updating Contact via app.update function"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            # Create first
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (tenant_id, user_id, {"email": "test@example.com", "status": "lead", "first_name": "Test", "last_name": "User"})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Update
            update_data = {"status": "qualified"}
            cur.execute(
                """
                SELECT app.update_contact(
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

    def test_delete_contact_happy_path(self, clean_db):
        """Test deleting Contact via app.delete function"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            # Create first
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (tenant_id, user_id, {"email": "test@example.com", "status": "lead", "first_name": "Test", "last_name": "User"})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Delete
            cur.execute(
                """
                SELECT app.delete_contact(
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
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            # CREATE
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (tenant_id, user_id, {"email": "test@example.com", "status": "lead", "first_name": "Test", "last_name": "User"})
            )
            create_result = cur.fetchone()[0]
            assert create_result['status'] == 'success'
            contact_id = UUID(create_result['object_data']['id'])

            # READ (verify exists)
            cur.execute(
                "SELECT COUNT(*) FROM crm.tb_contact WHERE id = %s",
                (contact_id,)
            )
            count = cur.fetchone()[0]
            assert count == 1

            # UPDATE
            update_data = {"status": "qualified"}
            cur.execute(
                "SELECT app.update_contact(%s, %s, %s, %s)",
                (tenant_id, user_id, contact_id, json.dumps(update_data))
            )
            update_result = cur.fetchone()[0]
            assert update_result['status'] == 'success'

            # DELETE
            cur.execute(
                "SELECT app.delete_contact(%s, %s, %s)",
                (tenant_id, user_id, contact_id)
            )
            delete_result = cur.fetchone()[0]
            assert delete_result['status'] == 'success'

            # VERIFY DELETED
            cur.execute(
                "SELECT COUNT(*) FROM crm.tb_contact WHERE id = %s",
                (contact_id,)
            )
            final_count = cur.fetchone()[0]
            assert final_count == 0


    def test_qualify_lead(self, clean_db):
        """Test qualify_lead action"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            # Setup: Create Contact with appropriate status
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (tenant_id, user_id, {"email": "qualify@example.com", "status": "lead"})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Execute action
            cur.execute(
                "SELECT crm.qualify_lead(%s, %s)",
                (contact_id, user_id)
            )
            action_result = cur.fetchone()[0]

        assert action_result['status'] == 'success'
        assert action_result['object_data']['status'] == 'qualified'

    def test_convert_to_customer(self, clean_db):
        """Test convert_to_customer action"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            # Setup: Create Contact with appropriate status
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (tenant_id, user_id, {"email": "qualify@example.com", "status": "lead"})
            )
            create_result = cur.fetchone()[0]
            contact_id = UUID(create_result['object_data']['id'])

            # Execute action
            cur.execute(
                "SELECT crm.convert_to_customer(%s, %s)",
                (contact_id, user_id)
            )
            action_result = cur.fetchone()[0]

        assert action_result['status'] == 'success'
        assert action_result['object_data']['status'] == 'qualified'

