"""Detector for Info/Instance dual-table patterns."""

from dataclasses import dataclass


@dataclass
class InfoInstanceDetectionResult:
    """Result of detecting info/instance pattern for a single table."""

    is_info_table: bool
    is_instance_table: bool
    base_entity_name: str | None = None
    info_fk_column: str | None = None  # For instance tables
    parent_fk_column: str | None = None  # For instance tables (self-ref)


@dataclass
class InfoInstancePair:
    """A matched pair of info and instance tables."""

    info_table: str
    instance_table: str
    base_entity_name: str
    translation_table: str | None = None


class InfoInstanceDetector:
    """Detects Info/Instance dual-table patterns.

    The Info/Instance pattern is used for hierarchical reference data:
    - tb_{entity}_info: Defines WHAT the entity is (vocabulary)
    - tb_{entity}: Defines WHERE it sits in hierarchy (structure)

    Example:
        tb_administrative_unit_info (name, code, level)
        tb_administrative_unit (parent ref, path, info ref)
    """

    def detect(self, table_name: str, columns: list[str]) -> InfoInstanceDetectionResult:
        """Detect if a table is part of info/instance pattern."""
        normalized = self._normalize_table_name(table_name)

        # Check for _info suffix first
        if normalized.endswith("_info"):
            base_name = normalized[:-5]
            return InfoInstanceDetectionResult(
                is_info_table=True,
                is_instance_table=False,
                base_entity_name=base_name,
            )

        # Check for instance table pattern
        info_fk = self._find_info_fk_column(normalized, columns)
        if info_fk:
            parent_fk = self._find_parent_fk_column(normalized, columns)
            return InfoInstanceDetectionResult(
                is_info_table=False,
                is_instance_table=True,
                base_entity_name=normalized,
                info_fk_column=info_fk,
                parent_fk_column=parent_fk,
            )

        return InfoInstanceDetectionResult(
            is_info_table=False,
            is_instance_table=False,
        )

    def _normalize_table_name(self, table_name: str) -> str:
        """Remove common prefixes from table name."""
        return table_name.removeprefix("tb_").removeprefix("tv_").lower()

    def _find_info_fk_column(self, base_name: str, columns: list[str]) -> str | None:
        """Find FK column pointing to info table."""
        expected_fk = f"fk_{base_name}_info"
        for col in columns:
            if col.lower() == expected_fk:
                return col
        return None

    def _find_parent_fk_column(self, base_name: str, columns: list[str]) -> str | None:
        """Find self-referential FK column for hierarchy."""
        expected_fk = f"fk_parent_{base_name}"
        for col in columns:
            if col.lower() == expected_fk:
                return col
        return None

    def detect_pairs(
        self, tables: list[dict], translation_tables: dict[str, str] | None = None
    ) -> list[InfoInstancePair]:
        """Find info/instance pairs among a list of tables.

        Args:
            tables: List of dicts with 'name' and 'columns' keys
            translation_tables: Map of parent_name → translation_table_name

        Returns:
            List of InfoInstancePair objects
        """
        # First pass: categorize all tables
        info_tables = {}  # base_name → table_name
        instance_tables = {}  # base_name → (table_name, info_fk, parent_fk)

        for table in tables:
            result = self.detect(table["name"], table["columns"])

            if result.is_info_table:
                info_tables[result.base_entity_name] = table["name"]
            elif result.is_instance_table:
                instance_tables[result.base_entity_name] = (
                    table["name"],
                    result.info_fk_column,
                    result.parent_fk_column,
                )

        # Second pass: match pairs
        pairs = []
        for base_name, info_table_name in info_tables.items():
            if base_name in instance_tables:
                instance_info = instance_tables[base_name]

                # Check for translation table
                tl_table = None
                if translation_tables:
                    # Try both patterns: tl_{base}_info and tl_{base}
                    tl_table = translation_tables.get(f"{base_name}_info")
                    if not tl_table:
                        tl_table = translation_tables.get(base_name)

                pairs.append(
                    InfoInstancePair(
                        info_table=info_table_name,
                        instance_table=instance_info[0],
                        base_entity_name=base_name,
                        translation_table=tl_table,
                    )
                )

        return pairs
