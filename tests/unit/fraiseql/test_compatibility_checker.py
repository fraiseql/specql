"""
Unit tests for FraiseQL compatibility checker
"""

from src.generators.fraiseql.compatibility_checker import CompatibilityChecker


class TestCompatibilityChecker:
    """Test FraiseQL compatibility checker functionality"""

    def test_init_creates_checker(self):
        """Test: CompatibilityChecker initializes correctly"""
        checker = CompatibilityChecker()
        assert checker is not None
        assert hasattr(checker, "check_all_types_compatible")
        assert hasattr(checker, "get_incompatible_types")
        assert hasattr(checker, "get_compatibility_report")

    def test_check_all_types_compatible_returns_true(self):
        """Test: All types are compatible (no manual annotations needed)"""
        checker = CompatibilityChecker()
        assert checker.check_all_types_compatible() is True

    def test_get_incompatible_types_returns_empty_set(self):
        """Test: No types need manual annotation"""
        checker = CompatibilityChecker()
        incompatible = checker.get_incompatible_types()
        assert isinstance(incompatible, set)
        assert len(incompatible) == 0

    def test_get_compatibility_report_structure(self):
        """Test: Compatibility report has expected structure"""
        checker = CompatibilityChecker()
        report = checker.get_compatibility_report()

        required_keys = [
            "total_types",
            "compatible_types",
            "incompatible_types",
            "compatibility_rate",
            "autodiscovery_enabled",
            "fraiseql_version_required",
            "notes",
        ]

        for key in required_keys:
            assert key in report

    def test_get_compatibility_report_values(self):
        """Test: Compatibility report has correct values"""
        checker = CompatibilityChecker()
        report = checker.get_compatibility_report()

        assert report["compatible_types"] >= 0
        assert report["total_types"] >= report["compatible_types"]
        assert len(report["incompatible_types"]) == 0
        assert report["compatibility_rate"] == 1.0
        assert report["autodiscovery_enabled"] is True
        assert report["fraiseql_version_required"] == "1.3.4+"
        assert isinstance(report["notes"], list)
        assert len(report["notes"]) > 0

    def test_autodiscovery_enabled(self):
        """Test: Autodiscovery is enabled"""
        checker = CompatibilityChecker()
        report = checker.get_compatibility_report()
        assert report["autodiscovery_enabled"] is True

    def test_fraiseql_version_requirement(self):
        """Test: Correct FraiseQL version requirement"""
        checker = CompatibilityChecker()
        report = checker.get_compatibility_report()
        assert report["fraiseql_version_required"] == "1.3.4+"

    def test_notes_contain_key_information(self):
        """Test: Notes contain key autodiscovery information"""
        checker = CompatibilityChecker()
        report = checker.get_compatibility_report()

        notes = " ".join(report["notes"]).lower()
        assert "autodiscover" in notes or "automatic" in notes
        assert "comment" in notes
        assert "graphql" in notes
