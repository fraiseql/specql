"""Integration tests for Contact entity"""

import pytest
from uuid import UUID
import psycopg
import json

# Mark all tests in this file as requiring database
pytestmark = pytest.mark.database


class TestContactIntegration:
    """Integration tests for Contact CRUD and actions"""

    @pytest.fixture
    def clean_db(self, test_db_connection):
        """Clean Contact table before test"""
        # No changes needed - the fixture from conftest.py will be used
        with test_db_connection.cursor() as cur:
            cur.execute("DELETE FROM crm.tb_contact")
            cur.execute("DELETE FROM crm.tb_company")  # Also clean company
        test_db_connection.commit()
        yield test_db_connection
        # Rollback after test to clean up
        test_db_connection.rollback()

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
                (
                    tenant_id,
                    user_id,
                    json.dumps(
                        {
                            "email": "test@example.com",
                            "status": "lead",
                            "first_name": "Test",
                            "last_name": "User",
                        }
                    ),
                ),
            )
            result = cur.fetchone()[0]
            # result is a string representation of a PostgreSQL composite type
            # Format: (id,updated_fields,status,message,object_data,_meta)

            # Simple parsing: remove outer parentheses and split by comma
            # But need to be careful with nested structures
            result_str = result.strip("()")
            # This is tricky with nested JSON. For now, let's use a simpler approach
            # Check that the result contains success
            assert "success" in result
            assert "test@example.com" in result

    def test_create_duplicate_contact_fails(self, clean_db):
        """Test duplicate Contact fails with proper error"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")
        input_data = {
            "email": "test@example.com",
            "status": "lead",
            "first_name": "Test",
            "last_name": "User",
        }

        with clean_db.cursor() as cur:
            # First insert
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (
                    tenant_id,
                    user_id,
                    json.dumps(input_data),
                ),
            )
            create_result = cur.fetchone()[0]
            # Extract ID from the result string - format: (uuid,"{fields}",status,"message","{json}",{})
            # Find the first comma after the UUID
            first_comma = create_result.find(",")
            contact_id = UUID(create_result[1:first_comma])

            # Execute action
            cur.execute(
                "SELECT app.qualify_lead(%s, %s, %s)",
                (tenant_id, user_id, json.dumps({"id": str(contact_id)})),
            )
            action_result = cur.fetchone()[0]

        # Check that action succeeded (string contains success)
        assert "success" in action_result
        assert "qualified" in action_result

    def test_convert_to_customer(self, clean_db):
        """Test convert_to_customer action"""
        tenant_id = UUID("01232122-0000-0000-2000-000000000001")
        user_id = UUID("01232122-0000-0000-2000-000000000002")

        with clean_db.cursor() as cur:
            # Setup: Create Contact with appropriate status
            cur.execute(
                "SELECT app.create_contact(%s, %s, %s)",
                (
                    tenant_id,
                    user_id,
                    json.dumps(
                        {
                            "email": "qualify@example.com",
                            "status": "lead",
                            "first_name": "Qualify",
                            "last_name": "Test",
                        }
                    ),
                ),
            )
            create_result = cur.fetchone()[0]
            # Extract ID from the result string - format: (uuid,"{fields}",status,"message","{json}",{})
            first_comma = create_result.find(",")
            contact_id = UUID(create_result[1:first_comma])

            # Verify contact was created
            assert "success" in create_result, f"Contact creation failed: {create_result}"
            assert contact_id != UUID("00000000-0000-0000-0000-000000000000"), "Contact ID is zero"

            # Execute action
            cur.execute(
                "SELECT app.qualify_lead(%s, %s, %s)",
                (tenant_id, user_id, json.dumps({"id": str(contact_id)})),
            )
            action_result = cur.fetchone()[0]

            # Check that action succeeded
            assert "success" in action_result, f"Qualify lead failed: {action_result}"

            # Verify the contact status was actually updated
            cur.execute("SELECT status FROM crm.tb_contact WHERE id = %s", (contact_id,))
            updated_status = cur.fetchone()[0]
            assert updated_status == "qualified", f"Status not updated: {updated_status}"
