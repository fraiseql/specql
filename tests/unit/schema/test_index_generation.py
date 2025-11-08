"""
Tests for Index Generation for Rich Types
Tests appropriate index creation for different rich type fields
"""

import pytest
from src.generators.table_generator import TableGenerator
from src.core.ast_models import Entity, FieldDefinition


def test_email_field_gets_btree_index():
    """Test: Email fields get efficient btree indexes for exact lookups"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={"email": FieldDefinition(name="email", type_name="email", nullable=False)},
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: B-tree index for exact lookups
    assert any("idx_tb_contact_email" in idx for idx in indexes)
    assert any("btree" in idx.lower() or "CREATE INDEX" in idx for idx in indexes)


def test_url_field_gets_gin_index_for_pattern_search():
    """Test: URL fields get GIN indexes for pattern matching"""
    entity = Entity(
        name="Page", schema="public", fields={"url": FieldDefinition(name="url", type_name="url")}
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: GIN index for LIKE/regex searches
    assert any("idx_tb_page_url" in idx for idx in indexes)
    assert any("gin" in idx.lower() for idx in indexes)
    assert any("gin_trgm_ops" in idx for idx in indexes)


def test_coordinates_field_gets_gist_index():
    """Test: Coordinates fields get GiST indexes for spatial queries"""
    entity = Entity(
        name="Location",
        schema="public",
        fields={"coordinates": FieldDefinition(name="coordinates", type_name="coordinates")},
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: GiST index for spatial operations
    assert any("idx_tb_location_coordinates" in idx for idx in indexes)
    assert any("gist" in idx.lower() for idx in indexes)


def test_ip_address_field_gets_gist_index():
    """Test: IP address fields get GiST indexes for network operations"""
    entity = Entity(
        name="Server",
        schema="public",
        fields={"ip_address": FieldDefinition(name="ip_address", type_name="ipAddress")},
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: GiST index for contains/overlaps operations
    assert any("idx_tb_server_ip_address" in idx for idx in indexes)
    assert any("gist" in idx.lower() for idx in indexes)
    assert any("inet_ops" in idx for idx in indexes)


def test_mac_address_field_gets_btree_index():
    """Test: MAC address fields get btree indexes"""
    entity = Entity(
        name="Device",
        schema="public",
        fields={"mac": FieldDefinition(name="mac", type_name="macAddress")},
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: B-tree index for exact lookups
    assert any("idx_tb_device_mac" in idx for idx in indexes)
    assert any("btree" in idx.lower() or "CREATE INDEX" in idx for idx in indexes)


def test_phone_field_gets_btree_index():
    """Test: Phone fields get btree indexes"""
    entity = Entity(
        name="Contact",
        schema="public",
        fields={"phone": FieldDefinition(name="phone", type_name="phoneNumber")},
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: B-tree index for exact lookups
    assert any("idx_tb_contact_phone" in idx for idx in indexes)
    assert any("btree" in idx.lower() or "CREATE INDEX" in idx for idx in indexes)


def test_slug_field_gets_btree_index():
    """Test: Slug fields get btree indexes"""
    entity = Entity(
        name="Post", schema="public", fields={"slug": FieldDefinition(name="slug", type_name="slug")}
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: B-tree index for exact lookups
    assert any("idx_tb_post_slug" in idx for idx in indexes)
    assert any("btree" in idx.lower() or "CREATE INDEX" in idx for idx in indexes)


def test_color_field_gets_btree_index():
    """Test: Color fields get btree indexes"""
    entity = Entity(
        name="Theme", schema="public", fields={"color": FieldDefinition(name="color", type_name="color")}
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: B-tree index for exact lookups
    assert any("idx_tb_theme_color" in idx for idx in indexes)
    assert any("btree" in idx.lower() or "CREATE INDEX" in idx for idx in indexes)


def test_money_field_gets_btree_index():
    """Test: Money fields get btree indexes"""
    entity = Entity(
        name="Product",
        schema="public",
        fields={"price": FieldDefinition(name="price", type_name="money")},
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Expected: B-tree index for range queries
    assert any("idx_tb_product_price" in idx for idx in indexes)
    assert any("btree" in idx.lower() or "CREATE INDEX" in idx for idx in indexes)


def test_multiple_rich_types_get_multiple_indexes():
    """Test: Entity with multiple rich types gets multiple indexes"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "email": FieldDefinition(name="email", type_name="email"),
            "website": FieldDefinition(name="website", type_name="url"),
            "phone": FieldDefinition(name="phone", type_name="phoneNumber"),
            "coordinates": FieldDefinition(name="coordinates", type_name="coordinates"),
        },
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Should have indexes for each rich type
    assert len(indexes) == 4
    assert any("email" in idx and "btree" in idx.lower() for idx in indexes)
    assert any("website" in idx and "gin" in idx.lower() for idx in indexes)
    assert any("phone" in idx and "btree" in idx.lower() for idx in indexes)
    assert any("coordinates" in idx and "gist" in idx.lower() for idx in indexes)


def test_no_rich_types_returns_empty_list():
    """Test: Entity with no rich types returns empty index list"""
    entity = Entity(
        name="Simple",
        schema="public",
        fields={
            "name": FieldDefinition(name="name", type_name="text"),
            "count": FieldDefinition(name="count", type_name="integer"),
        },
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Should return empty list for non-rich types
    assert indexes == []


def test_latitude_longitude_get_gist_indexes():
    """Test: Latitude and longitude fields get GiST indexes"""
    entity = Entity(
        name="Place",
        schema="public",
        fields={
            "lat": FieldDefinition(name="lat", type_name="latitude"),
            "lng": FieldDefinition(name="lng", type_name="longitude"),
        },
    )

    generator = TableGenerator()
    indexes = generator.generate_indexes_for_rich_types(entity)

    # Should have GiST indexes for both
    assert len(indexes) == 2
    assert any("lat" in idx and "gist" in idx.lower() for idx in indexes)
    assert any("lng" in idx and "gist" in idx.lower() for idx in indexes)
