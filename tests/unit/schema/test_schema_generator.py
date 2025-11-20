from unittest.mock import patch

from core.ast_models import EntityDefinition, FieldDefinition, FieldTier
from core.scalar_types import get_composite_type
from generators.schema.schema_generator import SchemaGenerator


def test_generate_table_with_composite_field():
    """Test table generation with composite field"""
    entity = EntityDefinition(
        name="Order",
        schema="crm",
        fields={
            "shipping_address": FieldDefinition(
                name="shipping_address",
                type_name="SimpleAddress",
                nullable=True,
                tier=FieldTier.COMPOSITE,
                composite_def=get_composite_type("SimpleAddress"),
            )
        },
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table(entity)

    assert "CREATE TABLE crm.tb_order" in ddl
    assert "shipping_address JSONB CHECK (validate_simple_address(shipping_address))" in ddl
    assert "CREATE INDEX crm_idx_tb_order_shipping_address" in ddl
    assert "validate_simple_address" in ddl


def test_generate_table_with_reference_field():
    """Test table generation with reference field"""
    entity = EntityDefinition(
        name="Contact",
        schema="crm",
        fields={
            "company": FieldDefinition(
                name="company",
                type_name="ref",
                nullable=False,
                tier=FieldTier.REFERENCE,
                reference_entity="Company",
                reference_schema="crm",
            )
        },
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table(entity)

    assert "CREATE TABLE crm.tb_contact" in ddl
    assert "fk_company INTEGER NOT NULL" in ddl
    assert "REFERENCES crm.tb_company(pk_company)" in ddl
    assert "ON DELETE RESTRICT ON UPDATE CASCADE" in ddl
    assert "CREATE INDEX idx_contact_company" in ddl


def test_generate_table_with_mixed_fields():
    """Test table generation with composite and reference fields"""
    entity = EntityDefinition(
        name="Order",
        schema="crm",
        fields={
            "customer": FieldDefinition(
                name="customer",
                type_name="ref",
                nullable=False,
                tier=FieldTier.REFERENCE,
                reference_entity="Customer",
                reference_schema="crm",
            ),
            "billing_address": FieldDefinition(
                name="billing_address",
                type_name="SimpleAddress",
                nullable=False,
                tier=FieldTier.COMPOSITE,
                composite_def=get_composite_type("SimpleAddress"),
            ),
            "shipping_address": FieldDefinition(
                name="shipping_address",
                type_name="SimpleAddress",
                nullable=True,
                tier=FieldTier.COMPOSITE,
                composite_def=get_composite_type("SimpleAddress"),
            ),
        },
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table(entity)

    # Check table creation
    assert "CREATE TABLE crm.tb_order" in ddl

    # Check reference field
    assert "fk_customer INTEGER NOT NULL" in ddl
    assert "REFERENCES crm.tb_customer(pk_customer)" in ddl
    assert "CREATE INDEX idx_order_customer" in ddl

    # Check composite fields
    assert "billing_address JSONB NOT NULL CHECK (validate_simple_address(billing_address))" in ddl
    assert "shipping_address JSONB CHECK (validate_simple_address(shipping_address))" in ddl
    assert "CREATE INDEX crm_idx_tb_order_billing_address" in ddl
    assert "CREATE INDEX crm_idx_tb_order_shipping_address" in ddl

    # Check validation functions are included
    assert "validate_simple_address" in ddl


def test_generate_table_with_description():
    """Test table generation includes description comments"""
    entity = EntityDefinition(
        name="Order",
        schema="crm",
        description="Customer orders",
        fields={
            "customer": FieldDefinition(
                name="customer",
                type_name="ref",
                nullable=False,
                tier=FieldTier.REFERENCE,
                reference_entity="Customer",
                reference_schema="crm",
            )
        },
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table(entity)

    assert "-- Table: Order" in ddl
    assert "-- Customer orders" in ddl


def test_generate_table_empty_entity():
    """Test table generation with no fields"""
    entity = EntityDefinition(name="Empty", schema="test", fields={})

    generator = SchemaGenerator()
    ddl = generator.generate_table(entity)

    assert "CREATE TABLE test.tb_empty" in ddl
    assert "-- Business fields" in ddl
    # Should have empty business fields section


def test_generate_trinity_helper_functions():
    """Test Trinity helper functions generation"""
    entity = EntityDefinition(name="Contact", schema="crm", fields={})

    generator = SchemaGenerator()
    helpers = generator._generate_trinity_helper_functions(entity)

    assert len(helpers) == 3
    assert (
        "CREATE OR REPLACE FUNCTION crm.contact_pk(p_id UUID, p_tenant_id UUID DEFAULT NULL)"
        in helpers[0]
    )
    assert "CREATE OR REPLACE FUNCTION crm.contact_id(p_pk INTEGER)" in helpers[1]
    assert "CREATE OR REPLACE FUNCTION crm.contact_identifier(p_pk INTEGER)" in helpers[2]
    assert "SELECT pk_contact" in helpers[0]
    assert "FROM crm.tb_contact" in helpers[0]
    assert "WHERE id = p_id" in helpers[0]
    assert "tenant_id = p_tenant_id" in helpers[0]
    assert "SELECT id" in helpers[1]
    assert "WHERE pk_contact = p_pk" in helpers[1]
    assert "SELECT identifier" in helpers[2]


def test_generate_trinity_fields():
    """Test Trinity fields generation"""
    entity = EntityDefinition(name="Contact", schema="crm", fields={})

    generator = SchemaGenerator()
    fields = generator._generate_trinity_fields(entity)

    assert len(fields) == 4
    assert "pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY" in fields[0]
    assert "id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE" in fields[1]
    assert "tenant_id UUID NOT NULL" in fields[2]
    assert "identifier TEXT UNIQUE" in fields[3]


def test_generate_trinity_indexes():
    """Test Trinity indexes generation"""
    entity = EntityDefinition(name="Contact", schema="crm", fields={})

    generator = SchemaGenerator()
    indexes = generator._generate_trinity_indexes(entity)

    assert len(indexes) == 2
    assert "CREATE INDEX idx_contact_id_tenant ON crm.tb_contact(id, tenant_id);" in indexes[0]
    assert "CREATE INDEX idx_contact_tenant ON crm.tb_contact(tenant_id);" in indexes[1]


def test_generate_table_with_trinity_helpers():
    """Test that Trinity helper functions are included in full DDL"""
    entity = EntityDefinition(
        name="User",
        schema="auth",
        fields={"username": FieldDefinition(name="username", type_name="text", nullable=False)},
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table(entity)

    assert "CREATE TABLE auth.tb_user" in ddl
    assert "-- Trinity Pattern" in ddl
    assert "pk_user INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY" in ddl
    assert "id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE" in ddl
    assert "tenant_id UUID NOT NULL" in ddl
    assert "identifier TEXT UNIQUE" in ddl
    assert "-- Trinity Indexes" in ddl
    assert "CREATE INDEX idx_user_id_tenant ON auth.tb_user(id, tenant_id);" in ddl
    assert "CREATE INDEX idx_user_tenant ON auth.tb_user(tenant_id);" in ddl
    assert "-- Trinity Helper Functions" in ddl
    assert "auth.user_pk(p_id UUID, p_tenant_id UUID DEFAULT NULL)" in ddl
    assert "auth.user_id(p_pk INTEGER)" in ddl
    assert "auth.user_identifier(p_pk INTEGER)" in ddl


@patch("generators.schema.schema_generator.should_split_entity")
def test_generate_table_with_node_info_split(mock_should_split):
    """Test that schema generator uses node+info split when should_split_entity returns True"""
    # Mock should_split_entity to return True
    mock_should_split.return_value = True

    entity = EntityDefinition(
        name="ComplexEntity",
        schema="test",
        fields={
            "path": FieldDefinition(name="path", type_name="ltree", nullable=False),
            "fk_parent_complexentity": FieldDefinition(
                name="fk_parent_complexentity",
                type_name="ref",
                nullable=True,
                reference_entity="ComplexEntity",
            ),
            "business_field1": FieldDefinition(
                name="business_field1", type_name="text", nullable=False
            ),
            "business_field2": FieldDefinition(
                name="business_field2", type_name="text", nullable=True
            ),
        },
    )

    generator = SchemaGenerator()
    ddl = generator.generate_table(entity)

    # Should contain node table, info table, and view
    assert "CREATE TABLE test.tb_complexentity_node" in ddl
    assert "CREATE TABLE test.tb_complexentity_info" in ddl
    assert "CREATE VIEW test.v_complexentity AS" in ddl

    # Should not contain single table creation (exact match)
    assert "CREATE TABLE test.tb_complexentity (" not in ddl
