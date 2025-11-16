"""Test documentation completeness for query patterns."""

from pathlib import Path
from typing import Set


class TestDocumentationCoverage:
    """Test that all query patterns have comprehensive documentation."""

    def test_all_patterns_have_reference_docs(self):
        """Test that every pattern has a reference documentation page."""
        patterns_dir = Path("stdlib/queries")
        docs_patterns_dir = Path("docs/patterns")

        # Get all pattern categories from stdlib
        pattern_categories = self._get_pattern_categories(patterns_dir)

        # Check each category has documentation
        missing_docs = []
        for category in pattern_categories:
            doc_path = docs_patterns_dir / category / "index.md"
            if not doc_path.exists():
                missing_docs.append(f"docs/patterns/{category}/index.md")

        # Allow some missing docs during development
        if missing_docs:
            assert False, f"Missing documentation (development in progress): {missing_docs}"

    def test_pattern_docs_have_required_sections(self):
        """Test that pattern documentation includes all required sections."""
        docs_patterns_dir = Path("docs/patterns")

        required_sections = ["## Overview", "## Parameters", "## Examples", "## When to Use"]

        for doc_file in docs_patterns_dir.rglob("*.md"):
            if doc_file.name in ["README.md", "getting_started.md", "advanced_features.md"]:
                continue

            content = doc_file.read_text()

            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)

            assert not missing_sections, f"{doc_file} missing required sections: {missing_sections}"

    def test_examples_reference_real_patterns(self):
        """Test that documentation examples reference existing patterns."""
        docs_patterns_dir = Path("docs/patterns")
        patterns_dir = Path("stdlib/queries")

        # Get all available patterns
        available_patterns = self._get_all_patterns(patterns_dir)

        # Check examples in docs (skip README and getting_started as they cover action patterns)
        for doc_file in docs_patterns_dir.rglob("*.md"):
            if doc_file.name in ["README.md", "getting_started.md"]:
                continue

            content = doc_file.read_text()

            # Extract pattern references from examples
            import re

            pattern_refs = re.findall(r"pattern:\s*([a-zA-Z_/-]+)", content)

            invalid_refs = []
            for ref in pattern_refs:
                if ref not in available_patterns:
                    invalid_refs.append(ref)

            assert not invalid_refs, f"{doc_file} references invalid patterns: {invalid_refs}"

    def test_migration_guide_exists(self):
        """Test that migration guide exists and is comprehensive."""
        migration_guide = Path("docs/migration/production_to_patterns.md")

        assert migration_guide.exists(), "Migration guide not found"

        content = migration_guide.read_text()

        required_sections = [
            "# Migrating Production Views to SpecQL Patterns",
            "## Step 1: Identify Pattern Category",
            "## Step 2: Convert to YAML",
            "## Step 3: Validate Equivalence",
            "## Step 4: Migration Checklist",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        assert not missing_sections, f"Migration guide missing sections: {missing_sections}"

    def _get_pattern_categories(self, patterns_dir: Path) -> Set[str]:
        """Get all pattern categories from stdlib/queries."""
        return {p.name for p in patterns_dir.iterdir() if p.is_dir()}

    def _get_all_patterns(self, patterns_dir: Path) -> Set[str]:
        """Get all pattern names from stdlib/queries."""
        patterns = set()
        for category_dir in patterns_dir.iterdir():
            if category_dir.is_dir():
                for yaml_file in category_dir.glob("*.yaml"):
                    # Extract pattern name from filename
                    pattern_name = yaml_file.stem
                    patterns.add(f"{category_dir.name}/{pattern_name}")

        return patterns
