# Computed Column Transformer
# Adds GENERATED ALWAYS AS columns based on schema_computed_column patterns

from core.ast_models import Entity, Pattern

from ..pattern_transformer import PatternTransformer


class ComputedColumnTransformer(PatternTransformer):
    """Adds GENERATED ALWAYS AS columns based on computed column patterns."""

    def applies_to(self, pattern: Pattern) -> bool:
        return pattern.type == "schema_computed_column"

    def transform_ddl(self, entity: Entity, ddl: str, pattern: Pattern) -> str:
        """
        Add computed columns to the CREATE TABLE DDL.

        Input DDL:
            CREATE TABLE sales.tb_order (
                quantity INTEGER,
                unit_price DECIMAL,
                ...
            );

        Output DDL:
            CREATE TABLE sales.tb_order (
                quantity INTEGER,
                unit_price DECIMAL,
                total_amount DECIMAL GENERATED ALWAYS AS (quantity * unit_price) STORED,
                ...
            );
        """
        # Handle both formats: single column or list of columns
        if "column_name" in pattern.params:
            # Single computed column format
            computed_config = [pattern.params]
        else:
            # List format
            computed_config = pattern.params.get("computed_columns", [])

        if not computed_config:
            return ddl

        # Parse CREATE TABLE to find insertion point
        lines = ddl.split("\n")
        insert_index = self._find_computed_column_insertion_point(lines)

        # Generate computed column definitions
        computed_lines = []
        for col_config in computed_config:
            col_def = self._generate_computed_column(col_config)
            computed_lines.append(col_def)

        # Insert into DDL
        lines[insert_index:insert_index] = computed_lines

        # Add pattern metadata to table comment
        ddl_with_metadata = "\n".join(lines)
        return self._add_pattern_metadata(ddl_with_metadata, pattern)

    def _generate_computed_column(self, config: dict) -> str:
        """
        Generate a computed column definition.

        config = {
            'name' or 'column_name': 'total_amount',
            'type': 'decimal',
            'expression': 'quantity * unit_price',
            'stored': true,
            'nullable': false
        }
        """
        col_name = config.get("name") or config.get("column_name")
        col_type = config["type"]
        expression = config["expression"]
        stored = "STORED" if config.get("stored", True) else ""
        nullable = "" if config.get("nullable", False) else "NOT NULL"

        return f"    {col_name} {col_type} GENERATED ALWAYS AS ({expression}) {stored} {nullable},"

    def _find_computed_column_insertion_point(self, lines: list[str]) -> int:
        """Find line index where computed columns should be inserted."""
        # Insert before "-- Foreign Keys" or "-- Audit Fields" or closing );
        for i, line in enumerate(lines):
            if (
                "-- Foreign Keys" in line
                or "-- Audit Fields" in line
                or line.strip().startswith(");")
            ):
                return i
        return len(lines) - 2  # Before closing );

    def _add_pattern_metadata(self, ddl: str, pattern: Pattern) -> str:
        """Add @fraiseql:pattern annotation to table comment."""
        # Find COMMENT ON TABLE line and add pattern info
        if "COMMENT ON TABLE" in ddl:
            ddl = ddl.replace(
                "@fraiseql:type\ntrinity: true\n';",
                "@fraiseql:type\ntrinity: true\n\n@fraiseql:pattern:schema_computed_column\n';",
            )
        return ddl

    def get_priority(self) -> int:
        return 50  # Run after basic DDL, before indexes
