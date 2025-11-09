"""
Integration tests for Tier 1 scalar types

Tests full pipeline:
- Parse SpecQL YAML
- Verify AST structure
- Verify metadata for Team B (PostgreSQL)
- Verify metadata for Team D (FraiseQL)
"""

import pytest
from src.core.specql_parser import SpecQLParser


def test_all_23_scalar_types_parseable():
    """Test that all 22 rich scalar types + boolean can be parsed"""
    yaml_content = """
    entity: AllScalarTypes
    schema: test

    fields:
      # String-based
      email: email!
      phone: phoneNumber
      website: url
      slug: slug
      markdown_content: markdown
      html_content: html

      # Network
      ip: ipAddress
      mac: macAddress

      # Numeric
      price: money!
      discount: percentage

      # Date/Time
      start_date: date
      registration_datetime: datetime!
      opening_time: time
      work_duration: duration

      # Geographic
      location: coordinates
      lat: latitude
      lng: longitude

      # Media
      avatar: image
      document: file
      theme_color: color

      # Identifier
      external_id: uuid

      # Structured
      metadata: json

      # Basic type (not a rich scalar)
      is_active: boolean!
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.fields) == 23

    # Verify each field has correct metadata (boolean is basic, not scalar)
    for field_name, field in entity.fields.items():
        if field_name != "is_active":  # boolean is a basic type
            assert field.is_rich_scalar()
        assert field.postgres_type is not None
        assert field.fraiseql_type is not None

    # Spot check: email
    assert entity.fields["email"].validation_pattern is not None
    assert "@" in entity.fields["email"].validation_pattern

    # Spot check: money
    assert entity.fields["price"].postgres_type == "NUMERIC(19,4)"
    assert entity.fields["price"].min_value == 0.0

    # Spot check: percentage
    assert entity.fields["discount"].max_value == 100.0


def test_parser_generates_correct_postgres_metadata():
    """Test that parser generates correct PostgreSQL metadata for Team B"""
    yaml_content = """
    entity: Product
    fields:
      name: text!
      price: money!
      discount: percentage
      in_stock: boolean!
      created: datetime!
      location: coordinates
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Check PostgreSQL types
    assert entity.fields["name"].postgres_type == "TEXT"
    assert entity.fields["price"].postgres_type == "NUMERIC(19,4)"
    assert entity.fields["discount"].postgres_type == "NUMERIC(5,2)"
    assert entity.fields["in_stock"].postgres_type == "BOOLEAN"
    assert entity.fields["created"].postgres_type == "TIMESTAMPTZ"
    assert entity.fields["location"].postgres_type == "POINT"

    # Check validation metadata
    assert entity.fields["price"].min_value == 0.0
    assert entity.fields["discount"].min_value == 0.0
    assert entity.fields["discount"].max_value == 100.0


def test_parser_generates_correct_fraiseql_metadata():
    """Test that parser generates correct FraiseQL metadata for Team D"""
    yaml_content = """
    entity: Contact
    fields:
      email: email!
      phone: phoneNumber
      website: url
      is_active: boolean
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Check FraiseQL scalar names
    assert entity.fields["email"].fraiseql_type == "Email"
    assert entity.fields["phone"].fraiseql_type == "PhoneNumber"
    assert entity.fields["website"].fraiseql_type == "Url"
    assert entity.fields["is_active"].fraiseql_type == "Boolean"


def test_parser_handles_nullability_correctly():
    """Test that parser handles nullable and non-nullable fields correctly"""
    yaml_content = """
    entity: User
    fields:
      external_id: uuid!
      email: email!
      phone: phoneNumber  # nullable by default
      name: text!
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Non-nullable fields
    assert entity.fields["external_id"].nullable is False
    assert entity.fields["email"].nullable is False
    assert entity.fields["name"].nullable is False

    # Nullable field
    assert entity.fields["phone"].nullable is True


def test_parser_handles_mixed_field_types():
    """Test parsing entity with mix of all field types"""
    yaml_content = """
    entity: ComprehensiveEntity
    schema: test
    description: "Entity with all field types"

    fields:
      # Basic types
      basic_text: text
      basic_int: integer

      # Rich scalar types
      rich_email: email!
      rich_money: money
      rich_date: date
      rich_bool: boolean!

      # Geographic
      coords: coordinates
      lat: latitude
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.fields) == 8

    # Basic types should be BASIC tier
    assert entity.fields["basic_text"].tier.name == "BASIC"
    assert entity.fields["basic_int"].tier.name == "BASIC"
    # Boolean is also a BASIC type, not a rich scalar
    assert entity.fields["rich_bool"].tier.name == "BASIC"

    # Rich types should be SCALAR tier
    assert entity.fields["rich_email"].tier.name == "SCALAR"
    assert entity.fields["rich_money"].tier.name == "SCALAR"
    assert entity.fields["rich_date"].tier.name == "SCALAR"
    assert entity.fields["coords"].tier.name == "SCALAR"
    assert entity.fields["lat"].tier.name == "SCALAR"


def test_parser_preserves_field_metadata():
    """Test that parser preserves all field metadata correctly"""
    yaml_content = """
    entity: TestEntity
    fields:
      test_field: email!
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    field = entity.fields["test_field"]

    # Check all metadata is preserved
    assert field.name == "test_field"
    assert field.type_name == "email"
    assert field.nullable is False
    assert field.tier.name == "SCALAR"
    assert field.scalar_def is not None
    assert field.scalar_def.name == "email"
    assert field.postgres_type == "TEXT"
    assert field.fraiseql_type == "Email"
    assert field.validation_pattern is not None
    assert field.input_type == "email"
    assert field.placeholder == "user@example.com"
