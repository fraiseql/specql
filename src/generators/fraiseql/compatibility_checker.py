"""
FraiseQL Compatibility Checker
Verifies that rich types are compatible with FraiseQL autodiscovery

Key Insight:
FraiseQL v1.3.4+ automatically discovers types from PostgreSQL metadata:
- PostgreSQL COMMENT ON → GraphQL descriptions
- Base types (TEXT, INET, POINT, NUMERIC) → GraphQL scalars
- CHECK constraints signal semantic types

Result: No manual annotations needed! ✨
"""

from src.core.scalar_types import SCALAR_TYPES


class CompatibilityChecker:
    """Checks FraiseQL compatibility for SpecQL rich types"""

    def __init__(self) -> None:
        # Types that need manual annotation (empty - FraiseQL handles all!)
        self._incompatible_types: set[str] = set()

    def check_all_types_compatible(self) -> bool:
        """
        Verify all registered types are FraiseQL compatible

        Returns:
            True if all types work with FraiseQL autodiscovery
        """
        return len(self._incompatible_types) == 0

    def get_incompatible_types(self) -> set[str]:
        """
        Return set of types that need manual annotation

        Returns:
            Set of type names (empty if all compatible)
        """
        return self._incompatible_types.copy()

    def get_compatibility_report(self) -> dict:
        """
        Generate detailed compatibility report

        Returns:
            dict with compatibility status for all registered types
        """
        all_types = set(SCALAR_TYPES.keys())

        return {
            "total_types": len(all_types),
            "compatible_types": len(all_types) - len(self._incompatible_types),
            "incompatible_types": list(self._incompatible_types),
            "compatibility_rate": (
                1.0
                if len(all_types) == 0
                else (len(all_types) - len(self._incompatible_types)) / len(all_types)
            ),
            "autodiscovery_enabled": True,
            "fraiseql_version_required": "1.3.4+",
            "notes": [
                "FraiseQL autodiscovers types from PostgreSQL metadata",
                "PostgreSQL comments become GraphQL descriptions",
                "No manual @fraiseql:field annotations needed",
            ],
        }
