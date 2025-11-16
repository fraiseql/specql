"""
Integration tests for self-schema generation.

Tests that SpecQL can generate its own registry schema correctly.
"""

import pytest
from pathlib import Path


class TestSelfSchemaGeneration:
    """Test SpecQL self-schema generation (dogfooding)"""

    @pytest.fixture
    def specql_yaml_dir(self):
        """Directory containing SpecQL YAML for registry"""
        return Path("entities/specql_registry")

    def test_yaml_files_exist(self, specql_yaml_dir):
        """Test that all required YAML files exist"""
        required_files = [
            "domain.yaml",
            "subdomain.yaml",
            "entity_registration.yaml",
            "pattern_library/domain_pattern.yaml",
            "pattern_library/entity_template.yaml",
        ]

        for file_name in required_files:
            file_path = specql_yaml_dir / file_name
            assert file_path.exists(), f"Missing YAML file: {file_name}"
