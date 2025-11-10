from src.core.ast_models import EntityDefinition, FieldDefinition, FieldTier
from src.core.scalar_types import SCALAR_TYPES


def test_field_definition_scalar_type():
    """Test field definition with scalar rich type"""
    email_scalar = SCALAR_TYPES["email"]

    field = FieldDefinition(
        name="email",
        type_name="email",
        tier=FieldTier.SCALAR,
        scalar_def=email_scalar,
        postgres_type="TEXT",
        fraiseql_type="Email",
        validation_pattern=email_scalar.validation_pattern,
    )

    assert field.is_rich_scalar() is True
    assert field.is_composite() is False
    assert field.is_reference() is False
    assert field.scalar_def.name == "email"


def test_entity_definition():
    """Test entity definition with rich scalar field"""
    entity = EntityDefinition(
        name="Contact", schema="crm", description="Customer contact information"
    )

    email_field = FieldDefinition(
        name="email", type_name="email", tier=FieldTier.SCALAR, scalar_def=SCALAR_TYPES["email"]
    )

    entity.fields["email"] = email_field

    assert "email" in entity.fields
    assert entity.fields["email"].is_rich_scalar()


def test_field_definition_basic_type():
    """Test field definition with basic type"""
    field = FieldDefinition(
        name="name",
        type_name="text",
        tier=FieldTier.BASIC,
        postgres_type="TEXT",
        fraiseql_type="String",
    )

    assert field.is_rich_scalar() is False
    assert field.is_composite() is False
    assert field.is_reference() is False
    assert field.tier == FieldTier.BASIC


def test_field_definition_with_metadata():
    """Test field definition with PostgreSQL and FraiseQL metadata"""
    field = FieldDefinition(
        name="price",
        type_name="money",
        tier=FieldTier.SCALAR,
        scalar_def=SCALAR_TYPES["money"],
        postgres_type="NUMERIC(19,4)",
        postgres_precision=(19, 4),
        fraiseql_type="Money",
        min_value=0.0,
        input_type="number",
        placeholder="0.00",
    )

    assert field.is_rich_scalar() is True
    assert field.postgres_type == "NUMERIC(19,4)"
    assert field.postgres_precision == (19, 4)
    assert field.min_value == 0.0
    assert field.fraiseql_type == "Money"


def test_entity_definition_with_multiple_fields():
    """Test entity with mix of field types"""
    entity = EntityDefinition(name="Product", schema="inventory")

    # Basic field
    name_field = FieldDefinition(name="name", type_name="text", tier=FieldTier.BASIC)

    # Scalar field
    price_field = FieldDefinition(
        name="price", type_name="money", tier=FieldTier.SCALAR, scalar_def=SCALAR_TYPES["money"]
    )

    entity.fields["name"] = name_field
    entity.fields["price"] = price_field

    assert len(entity.fields) == 2
    assert entity.fields["name"].tier == FieldTier.BASIC
    assert entity.fields["price"].tier == FieldTier.SCALAR


def test_field_tier_enum_values():
    """Test FieldTier enum has correct values"""
    assert FieldTier.BASIC.value == "basic"
    assert FieldTier.SCALAR.value == "scalar"
    assert FieldTier.COMPOSITE.value == "composite"
    assert FieldTier.REFERENCE.value == "reference"
