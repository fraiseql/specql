"""
PostgreSQL Integration Tests for Rich Types
Tests that generated SQL actually works in PostgreSQL database
"""

import pytest
import psycopg2
from psycopg2.extras import execute_values
from src.generators.table_generator import TableGenerator
from src.core.ast_models import Entity, FieldDefinition


@pytest.fixture
def test_db():
    """PostgreSQL test database connection"""
    # Use test database - adjust connection string as needed
    conn = psycopg2.connect(
        host="localhost", database="test_specql", user="postgres", password="postgres"
    )
    # Enable pg_trgm extension for URL indexes
    conn.cursor().execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    conn.commit()
    yield conn
    conn.close()


def create_contact_entity_with_email():
    """Helper: Create test entity with email field"""
    return Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type="text", nullable=False),
            "email": FieldDefinition(name="email", type="email", nullable=False),
        },
    )


def create_contact_entity_with_rich_types():
    """Helper: Create test entity with multiple rich types"""
    return Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type="text", nullable=False),
            "email": FieldDefinition(name="email", type="email", nullable=False),
            "website": FieldDefinition(name="website", type="url", nullable=True),
            "phone": FieldDefinition(name="phone", type="phoneNumber", nullable=True),
            "coordinates": FieldDefinition(name="coordinates", type="coordinates", nullable=True),
        },
    )


@pytest.mark.integration
def test_email_constraint_validates_format(test_db):
    """Integration: Email CHECK constraint works in PostgreSQL"""
    entity = create_contact_entity_with_email()
    generator = TableGenerator()
    ddl = generator.generate_complete_ddl(entity)

    cursor = test_db.cursor()

    # Create table
    cursor.execute(ddl)
    test_db.commit()

    # Test valid email
    cursor.execute(
        "INSERT INTO crm.tb_contact (id, tenant_id, name, email) VALUES (%s, %s, %s, %s)",
        (
            "550e8400-e29b-41d4-a716-446655440000",
            "00000000-0000-0000-0000-000000000000",
            "John Doe",
            "valid@example.com",
        ),
    )
    test_db.commit()  # Should succeed

    # Test invalid email - should raise CheckViolation
    with pytest.raises(psycopg2.errors.CheckViolation):
        cursor.execute(
            "INSERT INTO crm.tb_contact (id, tenant_id, name, email) VALUES (%s, %s, %s, %s)",
            (
                "550e8400-e29b-41d4-a716-446655440001",
                "00000000-0000-0000-0000-000000000000",
                "Jane Doe",
                "not-an-email",
            ),
        )
        test_db.commit()

    test_db.rollback()


@pytest.mark.integration
def test_indexes_created_correctly(test_db):
    """Integration: Rich type indexes exist in PostgreSQL"""
    entity = create_contact_entity_with_rich_types()
    generator = TableGenerator()
    ddl = generator.generate_complete_ddl(entity)

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Query pg_indexes to verify
    cursor.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'tb_contact'
        AND schemaname = 'crm'
        AND indexname LIKE 'idx_tb_contact_%'
    """)

    indexes = {row[0]: row[1] for row in cursor.fetchall()}

    # Verify email B-tree index
    assert "idx_tb_contact_email" in indexes
    assert "btree" in indexes["idx_tb_contact_email"].lower()
    assert "email" in indexes["idx_tb_contact_email"]

    # Verify website GIN index
    assert "idx_tb_contact_website" in indexes
    assert "gin" in indexes["idx_tb_contact_website"].lower()
    assert "gin_trgm_ops" in indexes["idx_tb_contact_website"]

    # Verify phone B-tree index
    assert "idx_tb_contact_phone" in indexes
    assert "btree" in indexes["idx_tb_contact_phone"].lower()

    # Verify coordinates GiST index
    assert "idx_tb_contact_coordinates" in indexes
    assert "gist" in indexes["idx_tb_contact_coordinates"].lower()


@pytest.mark.integration
def test_comments_appear_in_postgresql(test_db):
    """Integration: COMMENT ON statements work in PostgreSQL"""
    entity = create_contact_entity_with_rich_types()
    generator = TableGenerator()
    ddl = generator.generate_complete_ddl(entity)

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Query col_description to verify comments
    cursor.execute("""
        SELECT
            a.attname AS column_name,
            col_description('crm.tb_contact'::regclass, a.attnum) AS description
        FROM pg_attribute a
        WHERE a.attrelid = 'crm.tb_contact'::regclass
        AND a.attnum > 0
        AND NOT a.attisdropped
        AND a.attname IN ('email', 'website', 'phone', 'coordinates')
    """)

    comments = {row[0]: row[1] for row in cursor.fetchall()}

    assert "email address" in comments["email"].lower()
    assert "validated format" in comments["email"].lower()
    assert "url" in comments["website"].lower() or "website" in comments["website"].lower()
    assert "phone" in comments["phone"].lower()
    assert "coordinates" in comments["coordinates"].lower()


@pytest.mark.integration
def test_url_pattern_matching_with_gin_index(test_db):
    """Integration: URL GIN index enables efficient pattern matching"""
    entity = create_contact_entity_with_rich_types()
    generator = TableGenerator()
    ddl = generator.generate_complete_ddl(entity)

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Insert test data
    test_data = [
        (
            "550e8400-e29b-41d4-a716-446655440000",
            "00000000-0000-0000-0000-000000000000",
            "John",
            "john@example.com",
            "https://john.com",
            "+1234567890",
            "(10.0, 20.0)",
        ),
        (
            "550e8400-e29b-41d4-a716-446655440001",
            "00000000-0000-0000-0000-000000000000",
            "Jane",
            "jane@example.com",
            "https://jane.org",
            "+1987654321",
            "(15.5, 25.5)",
        ),
        (
            "550e8400-e29b-41d4-a716-446655440002",
            "00000000-0000-0000-0000-000000000000",
            "Bob",
            "bob@example.com",
            "https://bob.net",
            "+1123456789",
            "(5.0, 15.0)",
        ),
    ]

    execute_values(
        cursor,
        "INSERT INTO crm.tb_contact (id, tenant_id, name, email, website, phone, coordinates) VALUES %s",
        test_data,
    )
    test_db.commit()

    # Test pattern matching uses GIN index
    cursor.execute("EXPLAIN SELECT * FROM crm.tb_contact WHERE website LIKE '%example%'")
    explain_plan = cursor.fetchall()

    explain_text = "\n".join(row[0] for row in explain_plan)
    assert "Bitmap Index Scan" in explain_text or "Index Scan" in explain_text

    # Verify we get correct results
    cursor.execute("SELECT name FROM crm.tb_contact WHERE website LIKE '%example%' ORDER BY name")
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0][0] == "John"


@pytest.mark.integration
def test_coordinates_gist_index_for_spatial_queries(test_db):
    """Integration: Coordinates GiST index enables spatial operations"""
    entity = create_contact_entity_with_rich_types()
    generator = TableGenerator()
    ddl = generator.generate_complete_ddl(entity)

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Insert test data with coordinates
    test_data = [
        (
            "550e8400-e29b-41d4-a716-446655440000",
            "00000000-0000-0000-0000-000000000000",
            "Location A",
            "a@example.com",
            None,
            None,
            "(10.0, 20.0)",
        ),
        (
            "550e8400-e29b-41d4-a716-446655440001",
            "00000000-0000-0000-0000-000000000000",
            "Location B",
            "b@example.com",
            None,
            None,
            "(15.5, 25.5)",
        ),
        (
            "550e8400-e29b-41d4-a716-446655440002",
            "00000000-0000-0000-0000-000000000000",
            "Location C",
            "c@example.com",
            None,
            None,
            "(5.0, 15.0)",
        ),
    ]

    execute_values(
        cursor,
        "INSERT INTO crm.tb_contact (id, tenant_id, name, email, website, phone, coordinates) VALUES %s",
        test_data,
    )
    test_db.commit()

    # Test spatial query uses GiST index
    cursor.execute("EXPLAIN SELECT * FROM crm.tb_contact WHERE coordinates <@ box '(0,0),(20,30)'")
    explain_plan = cursor.fetchall()

    explain_text = "\n".join(row[0] for row in explain_plan)
    assert "Index Scan" in explain_text or "Bitmap Index Scan" in explain_text

    # Verify we get correct results (points within bounding box)
    cursor.execute(
        "SELECT name FROM crm.tb_contact WHERE coordinates <@ box '(0,0),(20,30)' ORDER BY name"
    )
    results = cursor.fetchall()
    assert len(results) == 3  # All points are within the box


@pytest.mark.integration
def test_enum_constraints_work(test_db):
    """Integration: Enum field constraints validate correctly"""
    entity = Entity(
        name="Task",
        schema="public",
        fields={
            "title": FieldDefinition(name="title", type="text", nullable=False),
            "status": FieldDefinition(
                name="status", type="enum", values=["pending", "in_progress", "completed"]
            ),
        },
    )

    generator = TableGenerator()
    ddl = generator.generate_complete_ddl(entity)

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Test valid enum value
    cursor.execute(
        "INSERT INTO public.tb_task (id, title, status) VALUES (%s, %s, %s)",
        ("550e8400-e29b-41d4-a716-446655440000", "Test Task", "pending"),
    )
    test_db.commit()  # Should succeed

    # Test invalid enum value - should raise CheckViolation
    with pytest.raises(psycopg2.errors.CheckViolation):
        cursor.execute(
            "INSERT INTO public.tb_task (id, title, status) VALUES (%s, %s, %s)",
            ("550e8400-e29b-41d4-a716-446655440001", "Another Task", "invalid_status"),
        )
        test_db.commit()

    test_db.rollback()


@pytest.mark.integration
def test_foreign_key_constraints_work(test_db):
    """Integration: Foreign key constraints work correctly"""
    # Create parent table first
    parent_entity = Entity(
        name="Company",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type="text", nullable=False),
        },
    )

    # Create child table with FK
    child_entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type="text", nullable=False),
            "company": FieldDefinition(name="company", type="ref", target_entity="Company"),
        },
    )

    generator = TableGenerator()

    # Create parent table
    parent_ddl = generator.generate_complete_ddl(parent_entity)
    cursor = test_db.cursor()
    cursor.execute(parent_ddl)

    # Create child table
    child_ddl = generator.generate_complete_ddl(child_entity)
    cursor.execute(child_ddl)
    test_db.commit()

    # Insert parent record
    cursor.execute(
        "INSERT INTO crm.tb_company (id, tenant_id, name) VALUES (%s, %s, %s)",
        (
            "550e8400-e29b-41d4-a716-446655440000",
            "00000000-0000-0000-0000-000000000000",
            "ACME Corp",
        ),
    )
    test_db.commit()

    # Insert child record with valid FK
    cursor.execute(
        "INSERT INTO crm.tb_contact (id, tenant_id, name, fk_company) VALUES (%s, %s, %s, %s)",
        (
            "550e8400-e29b-41d4-a716-446655440001",
            "00000000-0000-0000-0000-000000000000",
            "John Doe",
            1,
        ),
    )
    test_db.commit()  # Should succeed

    # Try to insert child with invalid FK - should raise ForeignKeyViolation
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        cursor.execute(
            "INSERT INTO crm.tb_contact (id, tenant_id, name, fk_company) VALUES (%s, %s, %s, %s)",
            (
                "550e8400-e29b-41d4-a716-446655440002",
                "00000000-0000-0000-0000-000000000000",
                "Jane Doe",
                999,
            ),
        )
        test_db.commit()

    test_db.rollback()
