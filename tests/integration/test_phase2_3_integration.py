"""
Integration tests for Phase 2 (Composite Types) and Phase 3 (Entity References)

Tests full pipeline:
- Parse SpecQL YAML with all field types
- Verify AST structure includes all tiers
- Verify metadata for Teams B & D
"""

import pytest
from src.core.specql_parser import SpecQLParser


def test_complete_entity_with_all_field_types():
    """Test parsing a complete entity with all three tiers of field types"""
    yaml_content = """
    entity: Company
    schema: business
    description: "A business company"

    fields:
      # Basic types (Tier 1)
      name: text!
      founded_year: integer
      is_public: boolean

      # Scalar rich types (Tier 1)
      website: url
      email: email!
      phone: phoneNumber
      tax_id: text  # Could be a custom scalar in future

      # Composite types (Tier 2)
      headquarters: SimpleAddress!
      mailing_address: SimpleAddress
      contact_info: ContactInfo
      business_hours: BusinessHours

      # Reference types (Tier 3)
      ceo: ref(Person)!
      parent_company: ref(Company)
      subsidiaries: ref(Company)
      industry: ref(Industry)
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Entity metadata
    assert entity.name == "Company"
    assert entity.schema == "business"
    assert entity.description == "A business company"

    # Should have 15 fields total
    assert len(entity.fields) == 15

    # Test Tier 1: Basic types
    assert entity.fields["name"].tier.value == "basic"
    assert entity.fields["name"].nullable is False
    assert entity.fields["name"].postgres_type == "TEXT"

    assert entity.fields["founded_year"].tier.value == "basic"
    assert entity.fields["founded_year"].postgres_type == "INTEGER"

    assert entity.fields["is_public"].tier.value == "basic"
    assert entity.fields["is_public"].postgres_type == "BOOLEAN"

    # Test Tier 1: Scalar rich types
    assert entity.fields["website"].tier.value == "scalar"
    assert entity.fields["website"].scalar_def.name == "url"
    assert entity.fields["website"].fraiseql_type == "Url"

    assert entity.fields["email"].tier.value == "scalar"
    assert entity.fields["email"].nullable is False
    assert entity.fields["email"].validation_pattern is not None

    assert entity.fields["phone"].tier.value == "scalar"
    assert entity.fields["phone"].scalar_def.name == "phoneNumber"

    # Test Tier 2: Composite types
    assert entity.fields["headquarters"].tier.value == "composite"
    assert entity.fields["headquarters"].nullable is False
    assert entity.fields["headquarters"].postgres_type == "JSONB"
    assert entity.fields["headquarters"].composite_def.name == "SimpleAddress"

    assert entity.fields["contact_info"].tier.value == "composite"
    assert entity.fields["contact_info"].composite_def.name == "ContactInfo"

    assert entity.fields["business_hours"].tier.value == "composite"
    assert entity.fields["business_hours"].composite_def.name == "BusinessHours"

    # Test Tier 3: Reference types
    assert entity.fields["ceo"].tier.value == "reference"
    assert entity.fields["ceo"].nullable is False
    # Trinity Pattern: FK columns are INTEGER (reference pk_*), not UUID
    assert entity.fields["ceo"].postgres_type == "INTEGER"
    assert entity.fields["ceo"].fraiseql_type == "ID"
    assert entity.fields["ceo"].reference_entity == "Person"

    assert entity.fields["parent_company"].tier.value == "reference"
    assert entity.fields["parent_company"].reference_entity == "Company"
    assert entity.fields["parent_company"].postgres_type == "INTEGER"

    assert entity.fields["industry"].tier.value == "reference"
    assert entity.fields["industry"].reference_entity == "Industry"
    assert entity.fields["industry"].postgres_type == "INTEGER"


def test_composite_type_field_validation():
    """Test that composite fields have proper validation schemas"""
    yaml_content = """
    entity: Product
    fields:
      dimensions: Dimensions!
      price: MoneyAmount
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Dimensions composite
    dims_field = entity.fields["dimensions"]
    assert dims_field.composite_def is not None
    dims_schema = dims_field.fraiseql_schema
    assert dims_schema["type"] == "object"
    assert "width" in dims_schema["properties"]
    assert "height" in dims_schema["properties"]
    assert "depth" in dims_schema["properties"]

    # MoneyAmount composite
    price_field = entity.fields["price"]
    assert price_field.composite_def is not None
    price_schema = price_field.fraiseql_schema
    assert "amount" in price_schema["properties"]
    assert "currency" in price_schema["properties"]


def test_nested_composite_relationships():
    """Test entities with relationships to other entities via references"""
    yaml_content = """
    entity: Order
    fields:
      customer: ref(Customer)!
      items: text  # JSON array of item refs
      shipping_address: SimpleAddress!
      billing_address: SimpleAddress
      total: MoneyAmount!
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    assert len(entity.fields) == 5

    # Reference to Customer
    customer_field = entity.fields["customer"]
    assert customer_field.is_reference()
    assert customer_field.reference_entity == "Customer"

    # Composite addresses
    shipping_field = entity.fields["shipping_address"]
    assert shipping_field.is_composite()
    assert shipping_field.composite_def.name == "SimpleAddress"

    billing_field = entity.fields["billing_address"]
    assert billing_field.is_composite()
    assert billing_field.nullable is True  # Default nullable

    # Money composite
    total_field = entity.fields["total"]
    assert total_field.is_composite()
    assert total_field.composite_def.name == "MoneyAmount"
    assert total_field.nullable is False


def test_polymorphic_references():
    """Test polymorphic reference fields"""
    yaml_content = """
    entity: Activity
    fields:
      actor: ref(User|Admin|System)!
      subject: ref(Post|Comment|User)
      target: ref(Post|Comment|User|Admin)
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # All should be reference fields
    for field_name in ["actor", "subject", "target"]:
        field = entity.fields[field_name]
        assert field.is_reference()
        # Trinity Pattern: FK columns are INTEGER (reference pk_*), not UUID
        assert field.postgres_type == "INTEGER"
        assert field.fraiseql_type == "ID"

    # Actor (non-nullable)
    assert entity.fields["actor"].nullable is False
    assert entity.fields["actor"].reference_entity == "User"  # First in union

    # Subject and target (nullable by default)
    assert entity.fields["subject"].nullable is True
    assert entity.fields["target"].nullable is True


def test_composite_type_examples():
    """Test that composite types provide useful examples"""
    from src.core.scalar_types import get_composite_type

    # Test SimpleAddress
    address_def = get_composite_type("SimpleAddress")
    assert address_def is not None
    assert "street" in address_def.example
    assert "city" in address_def.example

    # Test MoneyAmount
    money_def = get_composite_type("MoneyAmount")
    assert money_def is not None
    assert "amount" in money_def.example
    assert "currency" in money_def.example

    # Test PersonName
    name_def = get_composite_type("PersonName")
    assert name_def is not None
    assert "firstName" in name_def.example
    assert "lastName" in name_def.example


def test_all_tier_types_in_single_entity():
    """Test that a single entity can use all three tiers effectively"""
    yaml_content = """
    entity: EcommerceProduct
    fields:
      # Basic
      sku: text!
      name: text!
      description: text

      # Scalar
      price: money!
      weight_grams: integer
      color: color

      # Composite
      dimensions: Dimensions
      manufacturer: ContactInfo

      # References
      category: ref(ProductCategory)!
      supplier: ref(Supplier)
      reviews: text  # JSON array
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Count fields by tier
    basic_count = sum(1 for f in entity.fields.values() if f.tier.value == "basic")
    scalar_count = sum(1 for f in entity.fields.values() if f.tier.value == "scalar")
    composite_count = sum(1 for f in entity.fields.values() if f.tier.value == "composite")
    reference_count = sum(1 for f in entity.fields.values() if f.tier.value == "reference")

    assert basic_count == 5  # sku, name, description, weight_grams, reviews
    assert scalar_count == 2  # price, color
    assert composite_count == 2  # dimensions, manufacturer
    assert reference_count == 2  # category, supplier

    # Verify specific field properties
    assert entity.fields["sku"].nullable is False
    assert entity.fields["price"].nullable is False
    assert entity.fields["category"].nullable is False
    assert entity.fields["supplier"].nullable is True  # Default
