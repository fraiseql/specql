"""
Tests for Rich Type DDL Generation (Team B)
Tests TableGenerator with FraiseQL rich types
"""

import pytest
from src.generators.table_generator import TableGenerator
from src.core.ast_models import Entity, FieldDefinition


def test_email_field_generates_text_with_constraint():
    """Test: email type generates TEXT with CHECK constraint"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"email": FieldDefinition(name="email", type_name="email", nullable=False)},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    # Expected: TEXT with email validation
    assert "email TEXT NOT NULL" in ddl
    assert "CHECK" in ddl
    assert "~*" in ddl  # Regex operator
    assert "@" in ddl  # Email pattern


def test_url_field_generates_text_with_url_constraint():
    """Test: url type generates TEXT with URL validation"""
    entity = Entity(
        name="Page",
        schema="public",
        fields={"website": FieldDefinition(name="website", type_name="url", nullable=True)},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "website TEXT" in ddl
    assert "CHECK" in ddl
    assert "https?" in ddl


def test_ip_address_uses_inet_type():
    """Test: ipAddress type uses PostgreSQL INET (no CHECK needed)"""
    entity = Entity(
        name="Server",
        schema="public",
        fields={"ip_address": FieldDefinition(name="ip_address", type_name="ipAddress")},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    # Expected: PostgreSQL INET type (built-in validation)
    assert "ip_address INET" in ddl
    assert "CHECK" not in ddl  # INET has built-in validation


def test_mac_address_uses_macaddr_type():
    """Test: macAddress type uses PostgreSQL MACADDR"""
    entity = Entity(
        name="Device",
        schema="public",
        fields={"mac": FieldDefinition(name="mac", type_name="macAddress")},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "mac MACADDR" in ddl
    assert "CHECK" not in ddl  # MACADDR has built-in validation


def test_coordinates_generates_point_with_constraint():
    """Test: coordinates type generates POINT with lat/lng validation"""
    entity = Entity(
        name="Location",
        schema="public",
        fields={"location": FieldDefinition(name="location", type_name="coordinates")},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    # Expected: POINT type with bounds check
    assert "location POINT" in ddl
    assert "CHECK" in ddl
    # Latitude: -90 to 90, Longitude: -180 to 180
    assert "-90" in ddl and "90" in ddl
    assert "-180" in ddl and "180" in ddl


def test_money_generates_numeric_with_precision():
    """Test: money type generates NUMERIC(19,4)"""
    entity = Entity(
        name="Product",
        schema="public",
        fields={"price": FieldDefinition(name="price", type_name="money", nullable=False)},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "price NUMERIC(19,4) NOT NULL" in ddl


def test_money_with_metadata_uses_custom_precision():
    """Test: money generates NUMERIC(19,4) default precision"""
    entity = Entity(
        name="Product",
        schema="public",
        fields={"price": FieldDefinition(name="price", type_name="money")},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "price NUMERIC(19,4)" in ddl


def test_phone_number_generates_text_with_e164_constraint():
    """Test: phoneNumber type generates TEXT with E.164 validation"""
    entity = Entity(
        name="Contact",
        schema="public",
        fields={"phone": FieldDefinition(name="phone", type_name="phoneNumber")},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "phone TEXT" in ddl
    assert "CHECK" in ddl
    # E.164 format: +[1-9][0-9]{1,14}
    assert r"\+?" in ddl or "+" in ddl


def test_color_generates_text_with_hex_constraint():
    """Test: color type generates TEXT with hex code validation"""
    entity = Entity(
        name="Theme",
        schema="public",
        fields={"theme_color": FieldDefinition(name="theme_color", type_name="color")},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "theme_color TEXT" in ddl
    assert "CHECK" in ddl
    assert "#" in ddl
    assert "[0-9A-Fa-f]" in ddl


def test_slug_generates_text_with_url_safe_constraint():
    """Test: slug type generates TEXT with lowercase-hyphen validation"""
    entity = Entity(
        name="Post",
        schema="public",
        fields={"slug": FieldDefinition(name="slug", type_name="slug")},
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "slug TEXT" in ddl
    assert "CHECK" in ddl
    assert "[a-z0-9]" in ddl
    assert "[-]" in ddl or "-" in ddl


def test_complete_table_with_multiple_rich_types():
    """Test: Generate complete table with multiple rich types"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email", nullable=False),
            "website": FieldDefinition(name="website", type_name="url"),
            "phone": FieldDefinition(name="phone", type_name="phoneNumber"),
            "ip_address": FieldDefinition(name="ip_address", type_name="ipAddress"),
            "first_name": FieldDefinition(name="first_name", type_name="text"),
        },
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    # Verify table structure
    assert "CREATE TABLE crm.tb_contact" in ddl

    # Verify Trinity pattern (Team B's existing functionality)
    assert "pk_contact INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY" in ddl
    assert "id UUID DEFAULT gen_random_uuid() NOT NULL" in ddl

    # Verify rich type fields
    assert "email TEXT NOT NULL" in ddl
    assert "website TEXT" in ddl
    assert "phone TEXT" in ddl
    assert "ip_address INET" in ddl

    # Verify named constraints
    assert "CONSTRAINT chk_tb_contact_email_check CHECK (email ~* " in ddl
    assert "CONSTRAINT chk_tb_contact_website_check CHECK (website ~* " in ddl
    assert "CONSTRAINT chk_tb_contact_phone_check CHECK (phone ~* " in ddl

    # Verify basic type (backward compatibility)
    assert "first_name TEXT" in ddl


def test_backward_compatibility_basic_types():
    """Test: Existing basic types still work correctly"""
    entity = Entity(
        name="Product",
        schema="sales",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "quantity": FieldDefinition(name="quantity", type_name="integer"),
            "active": FieldDefinition(name="active", type_name="boolean"),
            "metadata": FieldDefinition(name="metadata", type_name="json"),
        },
    )

    generator = TableGenerator()
    ddl = generator.generate_table_ddl(entity)

    assert "name TEXT NOT NULL" in ddl
    assert "quantity INTEGER" in ddl
    assert "active BOOLEAN" in ddl
    assert "metadata JSONB" in ddl
