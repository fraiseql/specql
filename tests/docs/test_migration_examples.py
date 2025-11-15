"""Test migration examples and utilities."""

from pathlib import Path


class TestMigrationExamples:
    """Test that migration examples work correctly."""

    def test_migration_decision_tree_completeness(self):
        """Test that the decision tree covers all pattern categories."""
        migration_guide = Path("docs/migration/printoptim_to_patterns.md")
        content = migration_guide.read_text()

        # Extract pattern categories from decision tree
        import re

        pattern_matches = re.findall(r"→\s*([A-Za-z]+)\s+Pattern", content)
        pattern_categories = set(pattern_matches)

        # Expected categories from stdlib
        expected_categories = {
            "Junction",
            "Aggregation",
            "Extraction",
            "Hierarchical",
            "Polymorphic",
            "Wrapper",
            "Assembly",
        }

        assert pattern_categories == expected_categories, (
            f"Decision tree missing categories: {expected_categories - pattern_categories}"
        )

    def test_migration_examples_are_valid_yaml(self):
        """Test that YAML examples in migration guide are valid."""
        migration_guide = Path("docs/migration/printoptim_to_patterns.md")
        content = migration_guide.read_text()

        # Extract YAML code blocks
        import re

        yaml_blocks = re.findall(r"```yaml\n(.*?)\n```", content, re.DOTALL)

        import yaml

        for i, block in enumerate(yaml_blocks):
            try:
                parsed = yaml.safe_load(block)
                assert isinstance(parsed, (dict, list)), f"Block {i} should parse to dict or list"
            except yaml.YAMLError as e:
                assert False, f"YAML block {i} is invalid: {e}"

    def test_migration_sql_examples_are_valid(self):
        """Test that SQL examples in migration guide look reasonable."""
        migration_guide = Path("docs/migration/printoptim_to_patterns.md")
        content = migration_guide.read_text()

        # Extract SQL code blocks
        import re

        sql_blocks = re.findall(r"```sql\n(.*?)\n```", content, re.DOTALL)

        for i, block in enumerate(sql_blocks):
            # Basic SQL validation - should contain SELECT or CREATE
            assert "SELECT" in block.upper() or "CREATE" in block.upper(), (
                f"SQL block {i} should contain SELECT or CREATE"
            )

            # Should not contain obvious syntax errors
            assert ";;" not in block, f"SQL block {i} has double semicolons"
            assert not block.strip().endswith(";") or block.count(";") <= 1, (
                f"SQL block {i} has multiple statements"
            )

    def test_migration_tracker_matches_totals(self):
        """Test that migration tracker totals are consistent."""
        migration_guide = Path("docs/migration/printoptim_to_patterns.md")
        content = migration_guide.read_text()

        # Extract totals from tracker
        import re

        total_match = re.search(r"Total\s*\|\s*(\d+)", content)
        migrated_match = re.search(r"\*\*Total\*\*\s*\|\s*(\d+)\s*\|\s*(\d+)", content)

        if total_match and migrated_match:
            total = int(total_match.group(1))
            migrated = int(migrated_match.group(2))

            assert migrated <= total, f"Migrated ({migrated}) cannot exceed total ({total})"
            assert migrated == total, f"All migrations should be complete: {migrated}/{total}"

    def test_pattern_documentation_links_exist(self):
        """Test that pattern documentation links in migration guide exist."""
        migration_guide = Path("docs/migration/printoptim_to_patterns.md")
        migration_guide.read_text()

        # Check that referenced pattern docs exist
        pattern_doc_paths = [
            "docs/patterns/junction/index.md",
            "docs/patterns/aggregation/index.md",
            "docs/patterns/extraction/index.md",
            "docs/patterns/hierarchical/index.md",
            "docs/patterns/polymorphic/index.md",
            "docs/patterns/wrapper/index.md",
            "docs/patterns/assembly/index.md",
        ]

        for doc_path in pattern_doc_paths:
            assert Path(doc_path).exists(), f"Referenced documentation missing: {doc_path}"

    def test_migration_steps_are_actionable(self):
        """Test that migration steps provide clear, actionable guidance."""
        migration_guide = Path("docs/migration/printoptim_to_patterns.md")
        content = migration_guide.read_text()

        required_actionable_elements = [
            "specql generate entities/",
            "diff reference_sql/",
            "uv run pytest tests/migration/",
            "pattern: junction/resolver",
            "pattern: aggregation/count_aggregation",
        ]

        for element in required_actionable_elements:
            assert element in content, f"Missing actionable element: {element}"
