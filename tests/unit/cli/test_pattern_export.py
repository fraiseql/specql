"""Tests for pattern export functionality"""

import pytest
import yaml
import json
from src.cli.pattern_exporter import PatternExporter
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository,
)
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType


@pytest.fixture
def service_with_patterns():
    """Create service with sample patterns"""
    repository = InMemoryPatternRepository()
    service = PatternService(repository)

    # Add test patterns
    patterns = [
        Pattern(
            id=None,
            name="email_validation",
            category=PatternCategory.VALIDATION,
            description="Validates email addresses",
            parameters={"field_types": ["text", "email"]},
            implementation={"sql": "CHECK email ~* RFC_5322_REGEX"},
            times_instantiated=10,
            source_type=SourceType.MANUAL,
            complexity_score=3,
        ),
        Pattern(
            id=None,
            name="audit_trail",
            category=PatternCategory.AUDIT,
            description="Audit trail with timestamps",
            parameters={"required_fields": ["created_at", "updated_at"]},
            implementation={"sql": "created_at, updated_at fields"},
            times_instantiated=25,
            source_type=SourceType.MANUAL,
            complexity_score=2,
        ),
    ]

    for pattern in patterns:
        repository.save(pattern)

    return service


class TestPatternExport:
    """Test pattern export functionality"""

    def test_export_all_patterns_yaml(self, service_with_patterns, tmp_path):
        """Test exporting all patterns to YAML"""
        output_file = tmp_path / "patterns.yaml"

        # Export
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file)

        # Verify file exists
        assert output_file.exists()

        # Load and verify
        with open(output_file) as f:
            exported = yaml.safe_load(f)

        assert "patterns" in exported
        assert len(exported["patterns"]) == 2
        assert any(p["name"] == "email_validation" for p in exported["patterns"])

    def test_export_all_patterns_json(self, service_with_patterns, tmp_path):
        """Test exporting all patterns to JSON"""
        output_file = tmp_path / "patterns.json"

        # Export
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_json(output_file)

        # Verify
        assert output_file.exists()

        with open(output_file) as f:
            exported = json.load(f)

        assert "patterns" in exported
        assert len(exported["patterns"]) == 2

    def test_export_by_category(self, service_with_patterns, tmp_path):
        """Test exporting patterns filtered by category"""
        output_file = tmp_path / "validation_patterns.yaml"

        # Export only validation patterns
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file, category="validation")

        # Verify
        with open(output_file) as f:
            exported = yaml.safe_load(f)

        # Should only have validation patterns
        assert all(p["category"] == "validation" for p in exported["patterns"])

    def test_export_includes_metadata(self, service_with_patterns, tmp_path):
        """Test that export includes metadata"""
        output_file = tmp_path / "patterns.yaml"

        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file)

        with open(output_file) as f:
            exported = yaml.safe_load(f)

        # Check metadata
        assert "metadata" in exported
        assert "export_date" in exported["metadata"]
        assert "total_patterns" in exported["metadata"]

    def test_export_excludes_embeddings(self, service_with_patterns, tmp_path):
        """Test that embeddings are excluded from export"""
        output_file = tmp_path / "patterns.yaml"

        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file)

        with open(output_file) as f:
            exported = yaml.safe_load(f)

        # Embeddings should not be in export (too large)
        for pattern in exported["patterns"]:
            assert "embedding" not in pattern
