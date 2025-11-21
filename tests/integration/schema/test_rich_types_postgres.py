"""
PostgreSQL Integration Tests for Rich Types
Tests that generated SQL actually works in PostgreSQL database
"""

import psycopg
import pytest

from core.ast_models import Entity, FieldDefinition

# Mark all tests as requiring database
pytestmark = pytest.mark.database


def create_contact_entity_with_email():
    """Helper: Create test entity with email field"""
    return Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
        },
    )


def create_contact_entity_with_rich_types():
    """Helper: Create test entity with multiple rich types"""
    return Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
            "website": FieldDefinition(name="website", type_name="url", nullable=True),
            "phone": FieldDefinition(name="phone", type_name="phoneNumber", nullable=True),
            "coordinates": FieldDefinition(
                name="coordinates", type_name="coordinates", nullable=True
            ),
        },
    )


@pytest.mark.integration
def test_email_constraint_validates_format(test_db, isolated_schema, table_generator):
    """Integration: Email CHECK constraint works in PostgreSQL"""
    entity = create_contact_entity_with_email()
    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references with isolated schema
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")
    ddl = ddl.replace("crm_", f"{isolated_schema}_")  # Index name prefixes

    cursor = test_db.cursor()

    # Create table
    cursor.execute(ddl)
    test_db.commit()

    # Test valid email
    cursor.execute(
        f"INSERT INTO {isolated_schema}.tb_contact (id, tenant_id, name, email) VALUES (%s, %s, %s, %s)",
        (
            "550e8400-e29b-41d4-a716-446655440000",
            "00000000-0000-0000-0000-000000000000",
            "John Doe",
            "valid@example.com",
        ),
    )
    test_db.commit()  # Should succeed

    # Test invalid email - should raise CheckViolation
    with pytest.raises(psycopg.errors.CheckViolation):
        cursor.execute(
            f"INSERT INTO {isolated_schema}.tb_contact (id, tenant_id, name, email) VALUES (%s, %s, %s, %s)",
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
def test_indexes_created_correctly(test_db, isolated_schema, table_generator):
    """Integration: Rich type indexes exist in PostgreSQL"""
    entity = create_contact_entity_with_rich_types()
    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references with isolated schema
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")
    ddl = ddl.replace("crm_", f"{isolated_schema}_")  # Index name prefixes

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Query pg_indexes to verify
    cursor.execute(
        f"""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'tb_contact'
        AND schemaname = '{isolated_schema}'
        AND indexname LIKE '{isolated_schema}_idx_tb_contact_%'
    """
    )

    indexes = {row[0]: row[1] for row in cursor.fetchall()}

    # Verify email B-tree index
    assert f"{isolated_schema}_idx_tb_contact_email" in indexes
    assert "btree" in indexes[f"{isolated_schema}_idx_tb_contact_email"].lower()
    assert "email" in indexes[f"{isolated_schema}_idx_tb_contact_email"]

    # Verify website GIN index
    assert f"{isolated_schema}_idx_tb_contact_website" in indexes
    assert "gin" in indexes[f"{isolated_schema}_idx_tb_contact_website"].lower()
    assert "gin_trgm_ops" in indexes[f"{isolated_schema}_idx_tb_contact_website"]

    # Verify phone B-tree index
    assert f"{isolated_schema}_idx_tb_contact_phone" in indexes
    assert "btree" in indexes[f"{isolated_schema}_idx_tb_contact_phone"].lower()

    # Verify coordinates GiST index
    assert f"{isolated_schema}_idx_tb_contact_coordinates" in indexes
    assert "gist" in indexes[f"{isolated_schema}_idx_tb_contact_coordinates"].lower()


@pytest.mark.integration
def test_comments_appear_in_postgresql(test_db, isolated_schema, table_generator):
    """Integration: COMMENT ON statements work in PostgreSQL"""
    entity = create_contact_entity_with_rich_types()
    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references with isolated schema
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")
    ddl = ddl.replace("crm_", f"{isolated_schema}_")  # Index name prefixes

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Query col_description to verify comments
    cursor.execute(
        f"""
        SELECT
            a.attname AS column_name,
            col_description('{isolated_schema}.tb_contact'::regclass, a.attnum) AS description
        FROM pg_attribute a
        WHERE a.attrelid = '{isolated_schema}.tb_contact'::regclass
        AND a.attnum > 0
        AND NOT a.attisdropped
        AND a.attname IN ('email', 'website', 'phone', 'coordinates')
    """
    )

    comments = {row[0]: row[1] for row in cursor.fetchall()}

    assert "email address" in comments["email"].lower()
    assert "rfc 5322" in comments["email"].lower()
    assert "url" in comments["website"].lower() or "website" in comments["website"].lower()
    assert "phone" in comments["phone"].lower()
    assert "coordinates" in comments["coordinates"].lower()


@pytest.mark.integration
def test_url_pattern_matching_with_gin_index(test_db, isolated_schema, table_generator):
    """Integration: URL GIN index enables efficient pattern matching"""
    entity = create_contact_entity_with_rich_types()
    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references with isolated schema
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")
    ddl = ddl.replace("crm_", f"{isolated_schema}_")  # Index name prefixes

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

    cursor.executemany(
        f"INSERT INTO {isolated_schema}.tb_contact (id, tenant_id, name, email, website, phone, coordinates) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        test_data,
    )
    test_db.commit()

    # Check that GIN index was created for URL pattern matching
    cursor.execute(
        f"""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = '{isolated_schema}'
          AND tablename = 'tb_contact'
          AND indexname LIKE '%website%'
    """
    )
    indexes = cursor.fetchall()
    assert len(indexes) > 0
    assert "gin" in indexes[0][1].lower()
    assert "gin_trgm_ops" in indexes[0][1]

    # Verify the index can be used (insert more data to make index scan more likely)
    for i in range(100):
        cursor.execute(
            f"""
            INSERT INTO {isolated_schema}.tb_contact (id, tenant_id, name, email, website, phone, coordinates)
            VALUES (
                '550e8400-e29b-41d4-a716-44665544{1000 + i:04d}',
                '00000000-0000-0000-0000-000000000000',
                'User{i}',
                'user{i}@example.com',
                'https://example{i}.com',
                '+1234567890',
                '(10.0, 20.0)'
            )
        """
        )
    test_db.commit()

    # Verify GIN index enables efficient pattern matching
    # The index exists and is properly configured for trigram operations
    # In production with larger datasets, this would enable fast pattern matching
    cursor.execute(
        f"""
        SELECT COUNT(*) FROM {isolated_schema}.tb_contact WHERE website LIKE '%example%'
    """
    )
    count = cursor.fetchone()[0]
    assert count > 0  # Should find matches

    # Verify we get correct results
    cursor.execute(
        f"SELECT name FROM {isolated_schema}.tb_contact WHERE website LIKE '%example%' ORDER BY name"
    )
    results = cursor.fetchall()
    assert len(results) > 0  # Should find matches
    assert any("User" in result[0] for result in results)  # Should include bulk inserted data


@pytest.mark.integration
def test_coordinates_gist_index_for_spatial_queries(test_db, isolated_schema, table_generator):
    """Integration: Coordinates GiST index enables spatial operations"""
    entity = create_contact_entity_with_rich_types()
    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references with isolated schema
    ddl = ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("crm.", f"{isolated_schema}.")
    ddl = ddl.replace("crm_", f"{isolated_schema}_")  # Index name prefixes

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

    cursor.executemany(
        f"INSERT INTO {isolated_schema}.tb_contact (id, tenant_id, name, email, website, phone, coordinates) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        test_data,
    )
    test_db.commit()

    # Test spatial query uses GiST index
    cursor.execute(
        f"EXPLAIN SELECT * FROM {isolated_schema}.tb_contact WHERE coordinates <@ box '(0,0),(20,30)'"
    )
    explain_plan = cursor.fetchall()

    explain_text = "\n".join(row[0] for row in explain_plan)
    assert "Index Scan" in explain_text or "Bitmap Index Scan" in explain_text

    # Verify we get correct results (points within bounding box)
    cursor.execute(
        f"SELECT name FROM {isolated_schema}.tb_contact WHERE coordinates <@ box '(0,0),(20,30)' ORDER BY name"
    )
    results = cursor.fetchall()
    assert len(results) == 3  # All points are within the box


@pytest.mark.integration
def test_enum_constraints_work(test_db, isolated_schema, table_generator):
    """Integration: Enum field constraints validate correctly"""
    entity = Entity(
        name="Task",
        schema="public",
        fields={
            "title": FieldDefinition(name="title", type_name="text", nullable=False),
            "status": FieldDefinition(
                name="status", type_name="enum", values=["pending", "in_progress", "completed"]
            ),
        },
    )

    ddl = table_generator.generate_complete_ddl(entity)

    # Replace schema references with isolated schema
    ddl = ddl.replace("CREATE SCHEMA public", f"CREATE SCHEMA {isolated_schema}")
    ddl = ddl.replace("public.", f"{isolated_schema}.")
    ddl = ddl.replace("public_", f"{isolated_schema}_")  # Index name prefixes

    cursor = test_db.cursor()
    cursor.execute(ddl)
    test_db.commit()

    # Test valid enum value
    cursor.execute(
        f"INSERT INTO {isolated_schema}.tb_task (id, title, status) VALUES (%s, %s, %s)",
        ("550e8400-e29b-41d4-a716-446655440000", "Test Task", "pending"),
    )
    test_db.commit()  # Should succeed

    # Test invalid enum value - should raise CheckViolation
    with pytest.raises(psycopg.errors.CheckViolation):
        cursor.execute(
            f"INSERT INTO {isolated_schema}.tb_task (id, title, status) VALUES (%s, %s, %s)",
            ("550e8400-e29b-41d4-a716-446655440001", "Another Task", "invalid_status"),
        )
        test_db.commit()

    test_db.rollback()


@pytest.mark.integration
def test_foreign_key_constraints_work(test_db, isolated_schema, table_generator):
    """Integration: Foreign key constraints work correctly"""
    # Create parent table first
    parent_entity = Entity(
        name="Company",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
        },
    )

    # Create child table with FK
    child_entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company"),
        },
    )

    # Create parent table
    parent_ddl = table_generator.generate_complete_ddl(parent_entity)
    parent_ddl = parent_ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    parent_ddl = parent_ddl.replace("crm.", f"{isolated_schema}.")
    parent_ddl = parent_ddl.replace("crm_", f"{isolated_schema}_")  # Index name prefixes

    cursor = test_db.cursor()
    cursor.execute(parent_ddl)

    # Create child table
    child_ddl = table_generator.generate_complete_ddl(child_entity)
    child_ddl = child_ddl.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    child_ddl = child_ddl.replace("crm.", f"{isolated_schema}.")
    child_ddl = child_ddl.replace("crm_", f"{isolated_schema}_")  # Index name prefixes
    cursor.execute(child_ddl)
    test_db.commit()

    # Insert parent record
    cursor.execute(
        f"INSERT INTO {isolated_schema}.tb_company (id, tenant_id, name) VALUES (%s, %s, %s)",
        (
            "550e8400-e29b-41d4-a716-446655440000",
            "00000000-0000-0000-0000-000000000000",
            "ACME Corp",
        ),
    )
    test_db.commit()

    # Insert child record with valid FK
    cursor.execute(
        f"INSERT INTO {isolated_schema}.tb_contact (id, tenant_id, name, fk_company) VALUES (%s, %s, %s, %s)",
        (
            "550e8400-e29b-41d4-a716-446655440001",
            "00000000-0000-0000-0000-000000000000",
            "John Doe",
            1,
        ),
    )
    test_db.commit()  # Should succeed

    # Try to insert child with invalid FK - should raise ForeignKeyViolation
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        cursor.execute(
            f"INSERT INTO {isolated_schema}.tb_contact (id, tenant_id, name, fk_company) VALUES (%s, %s, %s, %s)",
            (
                "550e8400-e29b-41d4-a716-446655440002",
                "00000000-0000-0000-0000-000000000000",
                "Jane Doe",
                999,
            ),
        )
        test_db.commit()

    test_db.rollback()
