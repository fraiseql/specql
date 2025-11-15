"""Tests for pattern import functionality"""
import pytest
import yaml
from src.cli.pattern_importer import PatternImporter
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)


@pytest.fixture
def service():
    """Create empty service"""
    repository = InMemoryPatternRepository()
    return PatternService(repository)


@pytest.fixture
def sample_export_file(tmp_path):
    """Create sample export file"""
    export_data = {
        "metadata": {
            "export_date": "2025-11-12T10:00:00",
            "total_patterns": 2,
            "format_version": "1.0.0"
        },
        "patterns": [
            {
                "name": "test_pattern_1",
                "category": "validation",
                "description": "Test pattern 1",
                "parameters": {"test": "value"},
                "implementation": {"sql": "Test implementation"},
                "complexity_score": 3,
                "source_type": "migrated"
            },
            {
                "name": "test_pattern_2",
                "category": "audit",
                "description": "Test pattern 2",
                "parameters": {},
                "implementation": {"sql": "Implementation 2"},
                "complexity_score": 2,
                "source_type": "migrated"
            }
        ]
    }

    export_file = tmp_path / "test_patterns.yaml"
    with open(export_file, "w") as f:
        yaml.dump(export_data, f)

    return export_file


class TestPatternImport:
    """Test pattern import functionality"""

    def test_import_from_yaml(self, service, sample_export_file):
        """Test importing patterns from YAML"""
        importer = PatternImporter(service)

        # Import
        imported_count = importer.import_from_yaml(sample_export_file)

        assert imported_count == 2

        # Verify patterns were imported
        pattern1 = service.get_pattern_by_name("test_pattern_1")
        assert pattern1 is not None
        assert pattern1.category.value == "validation"

    def test_import_skips_existing(self, service, sample_export_file):
        """Test that import skips existing patterns"""
        importer = PatternImporter(service)

        # First import
        count1 = importer.import_from_yaml(sample_export_file, skip_existing=True)
        assert count1 == 2

        # Second import (should skip)
        count2 = importer.import_from_yaml(sample_export_file, skip_existing=True)
        assert count2 == 0  # All skipped

    def test_import_updates_existing(self, service, sample_export_file):
        """Test that import can update existing patterns"""
        importer = PatternImporter(service)

        # First import
        importer.import_from_yaml(sample_export_file, skip_existing=True)

        # Modify export file
        with open(sample_export_file) as f:
            data = yaml.safe_load(f)

        data["patterns"][0]["description"] = "Updated description"

        with open(sample_export_file, "w") as f:
            yaml.dump(data, f)

        # Second import (update)
        count = importer.import_from_yaml(sample_export_file, skip_existing=False)
        assert count == 2

        # Verify update
        pattern = service.get_pattern_by_name("test_pattern_1")
        assert pattern.description == "Updated description"

    def test_import_regenerates_embeddings(self, service, sample_export_file):
        """Test that import regenerates embeddings"""
        importer = PatternImporter(service)

        # Import with embedding generation
        importer.import_from_yaml(
            sample_export_file,
            generate_embeddings=True
        )

        # Verify embeddings were generated
        pattern = service.get_pattern_by_name("test_pattern_1")
        assert pattern.embedding is not None
        assert len(pattern.embedding) == 384

    def test_import_validates_format(self, service, tmp_path):
        """Test that import validates file format"""
        # Create invalid file (missing required fields)
        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, "w") as f:
            yaml.dump({"patterns": [{"name": "test"}]}, f)  # Missing fields

        importer = PatternImporter(service)

        with pytest.raises(ValueError, match="Invalid pattern"):
            importer.import_from_yaml(invalid_file)