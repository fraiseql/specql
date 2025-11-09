"""
Integration Tests for TableGenerator
Tests complete DDL generation, foreign keys, constraints, and orchestration
"""

import pytest
from src.generators.table_generator import TableGenerator
from src.core.ast_models import Entity, FieldDefinition


def test_complete_ddl_with_foreign_keys(table_generator):
    """Test: FK fields generate proper ALTER TABLE statements"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company")
        },
    )

    fk_ddl = table_generator.generate_foreign_keys_ddl(entity)

    assert "ALTER TABLE ONLY crm.tb_contact" in fk_ddl
    assert "FOREIGN KEY (fk_company)" in fk_ddl
    assert "REFERENCES crm.tb_company(pk_company)" in fk_ddl


def test_complete_ddl_with_enum_constraints(table_generator):
    """Test: Enum fields generate CHECK constraints"""
    entity = Entity(
        name="Task",
        schema="public",
        fields={
            "status": FieldDefinition(
                name="status", type_name="enum", values=["pending", "in_progress", "completed"]
            )
        },
    )

    ddl = table_generator.generate_table_ddl(entity)

    assert "CONSTRAINT chk_task_status_enum CHECK" in ddl
    assert "status IN ('pending', 'in_progress', 'completed')" in ddl


def test_generate_indexes_ddl_with_foreign_keys(table_generator):
    """Test: Foreign key fields get indexes"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company")
        },
    )

    index_ddl = table_generator.generate_indexes_ddl(entity)

    # Should have UUID index, FK index
    assert "idx_tb_contact_id" in index_ddl
    assert "idx_tb_contact_company" in index_ddl
    assert "btree" in index_ddl.lower()


def test_generate_indexes_ddl_with_enum_fields(table_generator):
    """Test: Enum fields get indexes"""
    entity = Entity(
        name="Task",
        schema="public",
        fields={
            "status": FieldDefinition(
                name="status", type_name="enum", values=["pending", "completed"]
            )
        },
    )

    index_ddl = table_generator.generate_indexes_ddl(entity)

    # Should have UUID index, enum index
    assert "idx_tb_task_id" in index_ddl
    assert "idx_tb_task_status" in index_ddl


def test_generate_complete_ddl_orchestration(table_generator):
    """Test: generate_complete_ddl() combines all pieces correctly"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
            "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company"),
            "status": FieldDefinition(
                name="status", type_name="enum", values=["active", "inactive"]
            ),
        },
    )

    complete_ddl = table_generator.generate_complete_ddl(entity)

    # Should contain all parts
    assert "CREATE TABLE crm.tb_contact" in complete_ddl
    assert "name TEXT NOT NULL" in complete_ddl
    assert "email TEXT NOT NULL" in complete_ddl
    assert "fk_company INTEGER" in complete_ddl
    assert "status TEXT" in complete_ddl

    # Should have constraints
    assert "CONSTRAINT chk_tb_contact_email_check" in complete_ddl
    assert "CONSTRAINT chk_contact_status_enum" in complete_ddl

    # Should have indexes
    assert "CREATE INDEX idx_tb_contact_id" in complete_ddl
    assert "CREATE INDEX idx_tb_contact_company" in complete_ddl
    assert "CREATE INDEX idx_tb_contact_status" in complete_ddl
    assert "CREATE INDEX idx_tb_contact_email" in complete_ddl  # Rich type index

    # Should have comments
    assert "COMMENT ON TABLE crm.tb_contact" in complete_ddl
    assert "COMMENT ON COLUMN crm.tb_contact.email" in complete_ddl
    assert "Email address" in complete_ddl and "validated format" in complete_ddl


def test_tenant_specific_schema_gets_multi_tenant_fields(table_generator):
    """Test: Tenant-specific schemas get tenant_id and organization fields"""
    entity = Entity(
        name="Contact",
        schema="crm",  # tenant-specific schema
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
        },
    )

    ddl = table_generator.generate_table_ddl(entity)

    # Should include tenant fields
    assert "tenant_id UUID NOT NULL" in ddl
    # Note: fk_organization is commented out in template


def test_common_schema_skips_multi_tenant_fields(table_generator):
    """Test: Common schemas don't get tenant fields"""
    entity = Entity(
        name="Locale",
        schema="common",  # common schema
        fields={
            "code": FieldDefinition(name="code", type_name="text", nullable=False),
        },
    )

    ddl = table_generator.generate_table_ddl(entity)

    # Should NOT include tenant fields
    assert "tenant_id" not in ddl


def test_rich_types_in_complete_ddl(table_generator):
    """Test: Rich types are properly integrated in complete DDL"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
            "website": FieldDefinition(name="website", type_name="url", nullable=True),
            "phone": FieldDefinition(name="phone", type_name="phoneNumber", nullable=True),
            "coordinates": FieldDefinition(
                name="coordinates", type_name="coordinates", nullable=True
            ),
        },
    )

    complete_ddl = table_generator.generate_complete_ddl(entity)

    # Should have rich type constraints
    assert "chk_tb_contact_email_check" in complete_ddl
    assert "chk_tb_contact_website_check" in complete_ddl
    assert "chk_tb_contact_phone_check" in complete_ddl
    assert "chk_tb_contact_coordinates_bounds" in complete_ddl

    # Should have rich type indexes
    assert "idx_tb_contact_email" in complete_ddl
    assert "idx_tb_contact_website" in complete_ddl
    assert "idx_tb_contact_phone" in complete_ddl
    assert "idx_tb_contact_coordinates" in complete_ddl

    # Should have descriptive comments
    assert "Email address (validated format)" in complete_ddl
    assert "URL/website address (validated format)" in complete_ddl
    assert "Phone number in E.164 format" in complete_ddl
    assert "Geographic coordinates (latitude, longitude)" in complete_ddl


def test_no_duplicate_comments_in_complete_ddl(table_generator):
    """Test: Complete DDL has no duplicate COMMENT statements"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
        },
    )

    complete_ddl = table_generator.generate_complete_ddl(entity)

    # Extract all COMMENT ON COLUMN lines
    lines = complete_ddl.split("\n")
    comment_lines = [line for line in lines if "COMMENT ON COLUMN" in line]

    # Extract column targets (e.g., "crm.tb_contact.email")
    targets = []
    for line in comment_lines:
        # Find text between "COMMENT ON COLUMN" and "IS"
        start = line.find("COMMENT ON COLUMN") + len("COMMENT ON COLUMN")
        end = line.find("IS", start)
        if end != -1:
            target = line[start:end].strip()
            targets.append(target)

    # Check for duplicates
    unique_targets = set(targets)
    assert len(targets) == len(unique_targets), f"Duplicate COMMENT targets found: {targets}"


def test_audit_fields_always_present(table_generator):
    """Test: Audit fields are always included"""
    entity = Entity(
        name="Simple",
        schema="public",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
        },
    )

    ddl = table_generator.generate_table_ddl(entity)

    # Trinity pattern audit fields
    assert "created_at TIMESTAMPTZ NOT NULL DEFAULT now()" in ddl
    assert "created_by UUID" in ddl
    assert "updated_at TIMESTAMPTZ NOT NULL DEFAULT now()" in ddl
    assert "updated_by UUID" in ddl
    assert "deleted_at TIMESTAMPTZ" in ddl
    assert "deleted_by UUID" in ddl
