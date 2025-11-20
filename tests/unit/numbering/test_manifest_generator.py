"""
Tests for ManifestGenerator
"""

import pytest

from numbering.manifest_generator import ManifestEntry, ManifestGenerator


def test_manifest_generator_creation():
    """Test creating a manifest generator"""
    generator = ManifestGenerator()
    assert generator is not None


def test_add_entity():
    """Test adding entities to manifest"""
    generator = ManifestGenerator()
    generator.add_entity("manufacturer", "013211")

    manifest = generator.generate_manifest()
    assert len(manifest) == 1
    assert manifest[0].entity_name == "manufacturer"
    assert manifest[0].table_code == "013211"


def test_execution_order_simple():
    """Test execution order for simple case"""
    generator = ManifestGenerator()

    # Add entities in random order
    generator.add_entity("user", "011111")
    generator.add_entity("manufacturer", "013211")
    generator.add_entity("role", "011211")

    manifest = generator.generate_manifest()

    # Should be ordered by table code
    assert len(manifest) == 3
    assert manifest[0].table_code == "011111"  # user
    assert manifest[1].table_code == "011211"  # role
    assert manifest[2].table_code == "013211"  # manufacturer


def test_execution_order_with_dependencies():
    """Test execution order respects dependencies"""
    generator = ManifestGenerator()

    # Add entities with dependencies (manufacturer depends on organization)
    generator.add_entity("manufacturer", "013211")
    generator.add_entity("organization", "012111")
    generator.add_dependency("manufacturer", "organization")  # manufacturer depends on organization

    manifest = generator.generate_manifest()

    # Organization should come before manufacturer
    assert len(manifest) == 2
    org_entry = next(e for e in manifest if e.entity_name == "organization")
    manu_entry = next(e for e in manifest if e.entity_name == "manufacturer")

    assert manifest.index(org_entry) < manifest.index(manu_entry)


def test_circular_dependency_detection():
    """Test detection of circular dependencies"""
    generator = ManifestGenerator()

    generator.add_entity("a", "011111")
    generator.add_entity("b", "011211")
    generator.add_entity("c", "011311")

    generator.add_dependency("a", "b")
    generator.add_dependency("b", "c")
    generator.add_dependency("c", "a")  # Creates circular dependency

    with pytest.raises(ValueError, match="Circular dependency detected"):
        generator.generate_manifest()


def test_manifest_entry_creation():
    """Test ManifestEntry dataclass"""
    entry = ManifestEntry(
        entity_name="manufacturer",
        table_code="013211",
        dependencies=["organization"],
        directory_path="01_write_side/013_catalog/0132_manufacturer/01321_manufacturer",
        file_paths=[
            "01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql"
        ],
    )

    assert entry.entity_name == "manufacturer"
    assert entry.table_code == "013211"
    assert entry.dependencies == ["organization"]
