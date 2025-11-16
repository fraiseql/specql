import pytest

from src.core.ast_models import FieldDefinition, FieldTier
from src.core.scalar_types import get_composite_type
from src.generators.schema.composite_type_mapper import (
    CompositeDDL,
    CompositeTypeMapper,
)


def test_map_simple_address_field():
    """Test mapping SimpleAddress composite type"""
    field = FieldDefinition(
        name="shipping_address",
        type_name="SimpleAddress",
        nullable=True,
        tier=FieldTier.COMPOSITE,
        composite_def=get_composite_type("SimpleAddress"),
    )

    mapper = CompositeTypeMapper()
    ddl = mapper.map_field(field)

    assert ddl.column_name == "shipping_address"
    assert ddl.postgres_type == "JSONB"
    assert ddl.nullable is True
    assert ddl.validation_function == "validate_simple_address"
    assert ddl.check_constraint == "validate_simple_address(shipping_address)"
    assert "Basic address information" in ddl.comment


def test_map_money_amount_field():
    """Test mapping MoneyAmount composite type"""
    field = FieldDefinition(
        name="price",
        type_name="MoneyAmount",
        nullable=False,
        tier=FieldTier.COMPOSITE,
        composite_def=get_composite_type("MoneyAmount"),
    )

    mapper = CompositeTypeMapper()
    ddl = mapper.map_field(field)

    assert ddl.column_name == "price"
    assert ddl.postgres_type == "JSONB"
    assert ddl.nullable is False
    assert ddl.validation_function == "validate_money_amount"
    assert ddl.check_constraint == "validate_money_amount(price)"


def test_map_field_without_composite_def():
    """Test mapping field that gets composite_def from registry"""
    field = FieldDefinition(
        name="billing_address",
        type_name="SimpleAddress",
        nullable=True,
        tier=FieldTier.COMPOSITE,
        # composite_def not set, should be retrieved from registry
    )

    mapper = CompositeTypeMapper()
    ddl = mapper.map_field(field)

    assert ddl.column_name == "billing_address"
    assert ddl.validation_function == "validate_simple_address"


def test_map_non_composite_field_raises_error():
    """Test that mapping non-composite field raises error"""
    field = FieldDefinition(
        name="email", type_name="email", nullable=False, tier=FieldTier.SCALAR
    )

    mapper = CompositeTypeMapper()
    with pytest.raises(ValueError, match="not a composite type"):
        mapper.map_field(field)


def test_generate_validation_function_simple_address():
    """Test validation function generation for SimpleAddress"""
    composite_def = get_composite_type("SimpleAddress")
    mapper = CompositeTypeMapper()
    function_sql = mapper.generate_validation_function(composite_def)

    assert "CREATE OR REPLACE FUNCTION validate_simple_address" in function_sql
    assert "data ? 'street'" in function_sql
    assert "data ? 'city'" in function_sql
    assert "data ? 'state'" in function_sql
    assert "data ? 'zipCode'" in function_sql
    assert "LANGUAGE plpgsql IMMUTABLE" in function_sql


def test_generate_validation_function_money_amount():
    """Test validation function generation for MoneyAmount"""
    composite_def = get_composite_type("MoneyAmount")
    mapper = CompositeTypeMapper()
    function_sql = mapper.generate_validation_function(composite_def)

    assert "CREATE OR REPLACE FUNCTION validate_money_amount" in function_sql
    assert "data ? 'amount'" in function_sql
    assert "data ? 'currency'" in function_sql


def test_generate_field_ddl_nullable():
    """Test field DDL generation for nullable composite"""
    ddl = CompositeDDL(
        column_name="shipping_address",
        postgres_type="JSONB",
        nullable=True,
        check_constraint="validate_simple_address(shipping_address)",
    )

    mapper = CompositeTypeMapper()
    field_ddl = mapper.generate_field_ddl(ddl)

    assert (
        field_ddl
        == "shipping_address JSONB CHECK (validate_simple_address(shipping_address))"
    )


def test_generate_field_ddl_not_nullable():
    """Test field DDL generation for non-nullable composite"""
    ddl = CompositeDDL(
        column_name="billing_address",
        postgres_type="JSONB",
        nullable=False,
        check_constraint="validate_simple_address(billing_address)",
    )

    mapper = CompositeTypeMapper()
    field_ddl = mapper.generate_field_ddl(ddl)

    assert (
        field_ddl
        == "billing_address JSONB NOT NULL CHECK (validate_simple_address(billing_address))"
    )


def test_generate_gin_index():
    """Test GIN index generation for JSONB field"""
    ddl = CompositeDDL(
        column_name="shipping_address", postgres_type="JSONB", nullable=True
    )

    mapper = CompositeTypeMapper()
    index_sql = mapper.generate_gin_index("crm", "tb_order", ddl)

    expected = """CREATE INDEX idx_tb_order_shipping_address
    ON crm.tb_order USING gin(shipping_address)
    WHERE deleted_at IS NULL;"""
    assert index_sql == expected
