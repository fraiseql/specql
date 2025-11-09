"""Tests for index generation strategy with partial index support."""

import pytest
from src.generators.schema.index_strategy import (
    generate_index,
    generate_btree_index,
    generate_gin_index,
    generate_gist_index,
)


class TestGenerateIndex:
    """Test the core generate_index function."""

    def test_basic_btree_index(self):
        """Test basic B-tree index generation."""
        result = generate_index(
            table_name="tenant.tb_location", index_name="idx_location_name", columns=["name"]
        )

        expected = """CREATE INDEX idx_location_name
    ON tenant.tb_location (name)
    WHERE deleted_at IS NULL;"""

        assert result == expected

    def test_unique_index_no_partial(self):
        """Test that unique indexes don't get partial clause."""
        result = generate_index(
            table_name="tenant.tb_location",
            index_name="idx_location_name",
            columns=["name"],
            unique=True,
        )

        expected = """CREATE UNIQUE INDEX idx_location_name
    ON tenant.tb_location (name);"""

        assert result == expected

    def test_gin_index(self):
        """Test GIN index generation."""
        result = generate_index(
            table_name="tenant.tb_order",
            index_name="idx_order_metadata",
            columns=["metadata"],
            index_type="gin",
        )

        expected = """CREATE INDEX idx_order_metadata
    ON tenant.tb_order USING gin(metadata)
    WHERE deleted_at IS NULL;"""

        assert result == expected

    def test_multiple_columns(self):
        """Test index with multiple columns."""
        result = generate_index(
            table_name="tenant.tb_location",
            index_name="idx_location_coords",
            columns=["latitude", "longitude"],
        )

        expected = """CREATE INDEX idx_location_coords
    ON tenant.tb_location (latitude, longitude)
    WHERE deleted_at IS NULL;"""

        assert result == expected

    def test_partial_disabled(self):
        """Test disabling partial index."""
        result = generate_index(
            table_name="tenant.tb_location",
            index_name="idx_location_name",
            columns=["name"],
            partial=False,
        )

        expected = """CREATE INDEX idx_location_name
    ON tenant.tb_location (name);"""

        assert result == expected


class TestConvenienceFunctions:
    """Test the convenience index generation functions."""

    def test_generate_btree_index(self):
        """Test B-tree index convenience function."""
        result = generate_btree_index(
            table_name="tenant.tb_location",
            index_name="idx_location_parent",
            columns=["fk_parent_location"],
        )

        expected = """CREATE INDEX idx_location_parent
    ON tenant.tb_location (fk_parent_location)
    WHERE deleted_at IS NULL;"""

        assert result == expected

    def test_generate_gin_index(self):
        """Test GIN index convenience function."""
        result = generate_gin_index(
            table_name="tenant.tb_order", index_name="idx_order_data", columns=["order_data"]
        )

        expected = """CREATE INDEX idx_order_data
    ON tenant.tb_order USING gin(order_data)
    WHERE deleted_at IS NULL;"""

        assert result == expected

    def test_generate_gist_index(self):
        """Test GIST index convenience function."""
        result = generate_gist_index(
            table_name="tenant.tb_location", index_name="idx_location_geom", columns=["geom"]
        )

        expected = """CREATE INDEX idx_location_geom
    ON tenant.tb_location USING gist(geom)
    WHERE deleted_at IS NULL;"""

        assert result == expected

    def test_generate_gist_index(self):
        """Test GIST index convenience function."""
        result = generate_gist_index(
            table_name="tenant.tb_location", index_name="idx_location_geom", columns=["geom"]
        )

        expected = """CREATE INDEX idx_location_geom
    ON tenant.tb_location USING gist(geom)
    WHERE deleted_at IS NULL;"""

        assert result == expected
