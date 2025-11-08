import pytest
from src.core.specql_parser import SpecQLParser
from src.core.type_registry import TypeRegistry, FRAISEQL_RICH_TYPES


def test_parse_email_type():
    """Test: Parse email rich type"""
    yaml_content = """
entity: Contact
fields:
  email: email
"""
    entity = SpecQLParser().parse_string(yaml_content)

    # Expected: email field with rich type
    assert "email" in entity.fields
    email_field = entity.fields["email"]
    assert email_field.type == "email"
    assert email_field.is_rich_type() is True
    assert email_field.get_postgres_type() == "TEXT"


def test_parse_multiple_rich_types():
    """Test: Parse multiple different rich types"""
    yaml_content = """
entity: Contact
fields:
  email: email
  website: url
  phone: phoneNumber
  ip_address: ipAddress
  mac_address: macAddress
  location: coordinates
  price: money
  birth_date: date
"""
    entity = SpecQLParser().parse_string(yaml_content)

    # Expected: all fields parsed with correct types
    assert entity.fields["email"].type == "email"
    assert entity.fields["website"].type == "url"
    assert entity.fields["phone"].type == "phoneNumber"
    assert entity.fields["ip_address"].type == "ipAddress"
    assert entity.fields["mac_address"].type == "macAddress"
    assert entity.fields["location"].type == "coordinates"
    assert entity.fields["price"].type == "money"
    assert entity.fields["birth_date"].type == "date"

    # All should be recognized as rich types
    for field_name, field_def in entity.fields.items():
        assert field_def.is_rich_type() is True


def test_parse_rich_type_with_nullable():
    """Test: Rich types with nullable modifier"""
    yaml_content = """
entity: Contact
fields:
  email: email!        # NOT NULL
  website: url         # nullable
"""
    entity = SpecQLParser().parse_string(yaml_content)

    assert entity.fields["email"].nullable is False
    assert entity.fields["website"].nullable is True


def test_parse_rich_type_with_default():
    """Test: Rich types with default values"""
    yaml_content = """
entity: Settings
fields:
  theme_color: color = '#000000'
  default_url: url = 'https://example.com'
"""
    entity = SpecQLParser().parse_string(yaml_content)

    assert entity.fields["theme_color"].default == "#000000"
    assert entity.fields["default_url"].default == "https://example.com"


def test_parse_complex_money_type():
    """Test: Money type with currency metadata"""
    yaml_content = """
entity: Product
fields:
  price: money(currency=USD, precision=2)
"""
    entity = SpecQLParser().parse_string(yaml_content)

    price_field = entity.fields["price"]
    assert price_field.type == "money"
    assert price_field.type_metadata is not None
    assert price_field.type_metadata["currency"] == "USD"
    assert price_field.type_metadata["precision"] == 2


def test_backward_compatibility_with_basic_types():
    """Test: Existing basic types still work"""
    yaml_content = """
entity: Contact
fields:
  name: text
  age: integer
  active: boolean
  metadata: jsonb
  company: ref(Company)
  tags: list(text)
  status: enum(active, inactive)
"""
    entity = SpecQLParser().parse_string(yaml_content)

    # Basic types should NOT be rich types
    assert entity.fields["name"].is_rich_type() is False
    assert entity.fields["age"].is_rich_type() is False
    assert entity.fields["active"].is_rich_type() is False

    # ref, list, enum should still work
    assert entity.fields["company"].type == "ref"
    assert entity.fields["tags"].type == "list"
    assert entity.fields["status"].type == "enum"


def test_invalid_rich_type_raises_error():
    """Test: Unknown type raises validation error"""
    yaml_content = """
entity: Contact
fields:
  mystery: unknownType
"""

    with pytest.raises(ValueError) as exc_info:
        SpecQLParser().parse_string(yaml_content)

    assert "Unknown type: unknownType" in str(exc_info.value)


def test_type_registry_completeness():
    """Test: Type registry contains all FraiseQL types"""
    registry = TypeRegistry()

    # Verify all expected types are present
    expected_types = [
        "email",
        "url",
        "phone",
        "phoneNumber",
        "ipAddress",
        "macAddress",
        "markdown",
        "html",
        "money",
        "percentage",
        "date",
        "datetime",
        "time",
        "duration",
        "coordinates",
        "latitude",
        "longitude",
        "image",
        "file",
        "color",
        "uuid",
        "slug",
    ]

    for expected_type in expected_types:
        assert registry.is_rich_type(expected_type) is True
        assert registry.get_postgres_type(expected_type) is not None
