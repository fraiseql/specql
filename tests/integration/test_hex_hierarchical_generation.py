"""Integration tests for hex hierarchical generation with explicit table codes"""

from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator


class TestHexHierarchicalGeneration:
    """Integration tests for hex hierarchical generation with explicit codes"""

    def test_generate_multiple_entities_with_explicit_codes(self, tmp_path):
        """
        Test generating multiple entities with explicit table codes in same run

        Reproduces GitHub Issue #1 scenario:
        - Production migration with 74 entities
        - Each entity has pre-existing 6-digit hex code
        - Hex hierarchical generation should succeed
        """
        # Create test entity files
        manufacturer_yaml = tmp_path / "manufacturer.yaml"
        manufacturer_yaml.write_text("""
entity: Manufacturer
schema: catalog
table_code: "013211"
description: Printer/copier manufacturers

fields:
  name: text
  abbreviation: text
""")

        manufacturer_range_yaml = tmp_path / "manufacturer_range.yaml"
        manufacturer_range_yaml.write_text("""
entity: ManufacturerRange
schema: catalog
table_code: "013212"
description: Product ranges from manufacturers

fields:
  name: text
  manufacturer: ref(Manufacturer)
""")

        # Generate with registry + hierarchical output
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=[str(manufacturer_yaml), str(manufacturer_range_yaml)],
            output_dir=str(output_dir),
        )

        # Both entities should generate successfully
        assert len(result.errors) == 0
        # Should have foundation + 2 entity migrations
        assert len(result.migrations) == 3

        # Check that we have the expected entity migrations
        entity_migrations = [
            m for m in result.migrations if m.name in ["manufacturer", "manufacturerrange"]
        ]
        assert len(entity_migrations) == 2

        # Verify hierarchical structure created in db/schema/
        # When use_registry=True, files are written to db/schema/ directory structure
        schema_base = Path("db/schema")

        # Check that 10_tables directory exists (where entity tables go)
        tables_dir = schema_base / "10_tables"
        assert tables_dir.exists()

        # Verify entity files exist
        manufacturer_files = list(tables_dir.glob("*manufacturer*.sql"))
        assert len(manufacturer_files) > 0

        range_files = list(tables_dir.glob("*manufacturerrange*.sql"))
        assert len(range_files) > 0

    def test_explicit_codes_allow_same_prefix(self):
        """
        Explicit table codes can share prefixes (different subdomains)

        Example:
        - 013211 = Catalog domain, manufacturer subdomain
        - 013311 = Catalog domain, parts subdomain

        These are both valid and should not conflict.
        """
        # TODO: Implement test
        pass

    def test_auto_derived_codes_still_enforce_uniqueness(self):
        """
        Auto-derived codes (no explicit table_code) should still validate uniqueness

        This ensures the fix doesn't break normal auto-derivation behavior.
        """
        # TODO: Implement test
        pass
