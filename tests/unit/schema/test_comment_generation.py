"""
Tests for PostgreSQL COMMENT Generation
Tests COMMENT ON statement generation for FraiseQL autodiscovery
"""

import pytest
from src.generators.table_generator import TableGenerator
from src.core.ast_models import Entity, FieldDefinition


def test_email_field_generates_descriptive_comment():
    """Test: email type generates descriptive COMMENT"""
    field = FieldDefinition(name="email", type="email", nullable=False)
    entity = Entity(name="Contact", schema="crm", fields={"email": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    # Expected: COMMENT ON COLUMN with rich type description
    assert any("COMMENT ON COLUMN crm.tb_contact.email" in c for c in comments)
    assert any("email address" in c.lower() or "Email" in c for c in comments)


def test_url_field_generates_descriptive_comment():
    """Test: url type generates descriptive COMMENT"""
    field = FieldDefinition(name="website", type="url")
    entity = Entity(name="Contact", schema="crm", fields={"website": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert any("COMMENT ON COLUMN crm.tb_contact.website" in c for c in comments)
    assert any("URL" in c or "website" in c.lower() for c in comments)


def test_coordinates_field_generates_descriptive_comment():
    """Test: coordinates type generates descriptive COMMENT"""
    field = FieldDefinition(name="location", type="coordinates")
    entity = Entity(name="Place", fields={"location": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert any("COMMENT ON COLUMN" in c for c in comments)
    assert any("coordinates" in c.lower() or "geographic" in c.lower() for c in comments)


def test_money_field_generates_descriptive_comment():
    """Test: money type generates descriptive COMMENT"""
    field = FieldDefinition(name="price", type="money")
    entity = Entity(name="Product", fields={"price": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert any("COMMENT ON COLUMN" in c for c in comments)
    assert any("money" in c.lower() or "monetary" in c.lower() for c in comments)


def test_rich_type_comment_includes_validation_info():
    """Test: Comments include validation information"""
    field = FieldDefinition(name="email", type="email")
    entity = Entity(name="Contact", fields={"email": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    # Should mention it's validated
    assert any("validated" in c.lower() or "format" in c.lower() for c in comments)


def test_complete_entity_generates_all_comments():
    """Test: All fields get COMMENT statements"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type="email"),
            "website": FieldDefinition(name="website", type="url"),
            "phone": FieldDefinition(name="phone", type="phoneNumber"),
            "first_name": FieldDefinition(name="first_name", type="text"),
        },
    )

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    # Should have comment for each field
    assert len(comments) == 4
    assert any("email" in c for c in comments)
    assert any("website" in c for c in comments)
    assert any("phone" in c for c in comments)
    assert any("first_name" in c for c in comments)


def test_nullable_field_comment_includes_required_note():
    """Test: Non-nullable fields include (required) in comment"""
    field = FieldDefinition(name="email", type="email", nullable=False)
    entity = Entity(name="Contact", fields={"email": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert any("required" in c.lower() for c in comments)


def test_nullable_field_comment_omits_required_note():
    """Test: Nullable fields don't include (required) in comment"""
    field = FieldDefinition(name="website", type="url", nullable=True)
    entity = Entity(name="Contact", fields={"website": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert not any("required" in c.lower() for c in comments)


def test_enum_field_comment_includes_options():
    """Test: Enum fields include available options in comment"""
    field = FieldDefinition(name="status", type="enum", values=["active", "inactive", "pending"])
    entity = Entity(name="Task", fields={"status": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    comment = next(c for c in comments if "status" in c)
    assert "active" in comment
    assert "inactive" in comment
    assert "pending" in comment


def test_ref_field_comment_includes_target():
    """Test: Reference fields include target entity in comment"""
    field = FieldDefinition(name="company", type="ref", target_entity="Company")
    entity = Entity(name="Contact", fields={"company": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert any("Company" in c for c in comments)


def test_money_field_with_currency_metadata():
    """Test: Money fields with currency metadata include currency info"""
    field = FieldDefinition(name="price", type="money", type_metadata={"currency": "USD"})
    entity = Entity(name="Product", fields={"price": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert any("USD" in c for c in comments)


def test_unknown_type_gets_generic_description():
    """Test: Unknown types get generic description"""
    field = FieldDefinition(name="custom_field", type="customType")
    entity = Entity(name="Entity", fields={"custom_field": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    assert any("Customtype value" in c for c in comments)


def test_ref_field_comment_uses_correct_column_name():
    """Test: Reference fields use fk_* column name, not business field name"""
    field = FieldDefinition(name="company", type="ref", target_entity="Company")
    entity = Entity(name="Contact", schema="crm", fields={"company": field})

    generator = TableGenerator()
    comments = generator.generate_field_comments(entity)

    # Should use fk_company (actual column), NOT company (business field)
    assert any("fk_company" in c for c in comments), (
        "COMMENT should use 'fk_company' (actual database column)"
    )
    assert not any("tb_contact.company IS" in c for c in comments), (
        "COMMENT should NOT use 'company' (business field name, column doesn't exist)"
    )
