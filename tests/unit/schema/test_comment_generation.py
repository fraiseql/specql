"""
Tests for PostgreSQL COMMENT Generation
Tests COMMENT ON statement generation for FraiseQL autodiscovery
"""

import pytest
from src.generators.table_generator import TableGenerator
from src.core.ast_models import Entity, FieldDefinition


def test_email_field_generates_descriptive_comment(table_generator):
    """Test: email type generates descriptive COMMENT"""
    field = FieldDefinition(name="email", type_name="email", nullable=False)
    entity = Entity(name="Contact", schema="crm", fields={"email": field})

    comments = table_generator.generate_field_comments(entity)

    # Expected: COMMENT ON COLUMN with rich type description
    assert any("COMMENT ON COLUMN crm.tb_contact.email" in c for c in comments)
    assert any("email address" in c.lower() or "Email" in c for c in comments)


def test_url_field_generates_descriptive_comment(table_generator):
    """Test: url type generates descriptive COMMENT"""
    field = FieldDefinition(name="website", type_name="url")
    entity = Entity(name="Contact", schema="crm", fields={"website": field})

    comments = table_generator.generate_field_comments(entity)

    assert any("COMMENT ON COLUMN crm.tb_contact.website" in c for c in comments)
    assert any("URL" in c or "website" in c.lower() for c in comments)


def test_coordinates_field_generates_descriptive_comment(table_generator):
    """Test: coordinates type generates descriptive COMMENT"""
    field = FieldDefinition(name="location", type_name="coordinates")
    entity = Entity(name="Place", fields={"location": field})

    comments = table_generator.generate_field_comments(entity)

    assert any("COMMENT ON COLUMN" in c for c in comments)
    assert any("coordinates" in c.lower() or "geographic" in c.lower() for c in comments)


def test_money_field_generates_descriptive_comment(table_generator):
    """Test: money type generates descriptive COMMENT"""
    field = FieldDefinition(name="price", type_name="money")
    entity = Entity(name="Product", fields={"price": field})

    comments = table_generator.generate_field_comments(entity)

    assert any("COMMENT ON COLUMN" in c for c in comments)
    assert any("money" in c.lower() or "monetary" in c.lower() for c in comments)


def test_rich_type_comment_includes_validation_info(table_generator):
    """Test: Comments include validation information"""
    field = FieldDefinition(name="email", type_name="email")
    entity = Entity(name="Contact", fields={"email": field})

    comments = table_generator.generate_field_comments(entity)

    # Should mention it's validated
    assert any("validated" in c.lower() or "format" in c.lower() for c in comments)


def test_complete_entity_generates_all_comments(table_generator):
    """Test: All fields get COMMENT statements"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email"),
            "website": FieldDefinition(name="website", type_name="url"),
            "phone": FieldDefinition(name="phone", type_name="phoneNumber"),
            "first_name": FieldDefinition(name="first_name", type_name="text"),
        },
    )

    comments = table_generator.generate_field_comments(entity)

    # Should have comment for each field
    assert len(comments) == 4
    assert any("email" in c for c in comments)
    assert any("website" in c for c in comments)
    assert any("phone" in c for c in comments)
    assert any("first_name" in c for c in comments)


def test_nullable_field_comment_includes_required_note(table_generator):
    """Test: Non-nullable fields have required: true in YAML comment"""
    field = FieldDefinition(name="email", type_name="email", nullable=False)
    entity = Entity(name="Contact", fields={"email": field})

    comments = table_generator.generate_field_comments(entity)

    # In YAML format, non-nullable fields should have "required: true"
    assert any("required: true" in c for c in comments)


def test_nullable_field_comment_omits_required_note(table_generator):
    """Test: Nullable fields have required: false in YAML comment"""
    field = FieldDefinition(name="website", type_name="url", nullable=True)
    entity = Entity(name="Contact", fields={"website": field})

    comments = table_generator.generate_field_comments(entity)

    # In YAML format, nullable fields should have "required: false"
    assert any("required: false" in c for c in comments)


def test_enum_field_comment_includes_options(table_generator):
    """Test: Enum fields include available options in comment"""
    field = FieldDefinition(
        name="status", type_name="enum", values=["active", "inactive", "pending"]
    )
    entity = Entity(name="Task", fields={"status": field})

    comments = table_generator.generate_field_comments(entity)

    comment = next(c for c in comments if "status" in c)
    assert "active" in comment
    assert "inactive" in comment
    assert "pending" in comment


def test_ref_field_comment_includes_target(table_generator):
    """Test: Reference fields include target entity in comment"""
    field = FieldDefinition(name="company", type_name="ref", reference_entity="Company")
    entity = Entity(name="Contact", fields={"company": field})

    comments = table_generator.generate_field_comments(entity)

    assert any("Company" in c for c in comments)


def test_money_field_with_currency_metadata(table_generator):
    """Test: Money fields generate descriptive comments"""
    field = FieldDefinition(name="price", type_name="money")
    entity = Entity(name="Product", fields={"price": field})

    comments = table_generator.generate_field_comments(entity)

    assert any("money" in c.lower() or "monetary" in c.lower() for c in comments)


def test_unknown_type_gets_generic_description(table_generator):
    """Test: Unknown types get generic description"""
    field = FieldDefinition(name="custom_field", type_name="customType")
    entity = Entity(name="Entity", fields={"custom_field": field})

    comments = table_generator.generate_field_comments(entity)

    assert any("Customtype value" in c for c in comments)


def test_ref_field_comment_uses_correct_column_name(table_generator):
    """Test: Reference fields use fk_* column name, not business field name"""
    field = FieldDefinition(name="company", type_name="ref", reference_entity="Company")
    entity = Entity(name="Contact", schema="crm", fields={"company": field})

    comments = table_generator.generate_field_comments(entity)

    # Should use fk_company (actual column), NOT company (business field)
    assert any("fk_company" in c for c in comments), (
        "COMMENT should use 'fk_company' (actual database column)"
    )
    assert not any("tb_contact.company IS" in c for c in comments), (
        "COMMENT should NOT use 'company' (business field name, column doesn't exist)"
    )
