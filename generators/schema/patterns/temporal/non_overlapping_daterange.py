"""Non-overlapping date range pattern implementation."""

from dataclasses import dataclass

from core.ast_models import Entity, Index


@dataclass
class DateRangeConfig:
    """Configuration for non-overlapping date range."""

    start_date_field: str
    end_date_field: str
    scope_fields: list[str] | None = None
    check_mode: str = "strict"  # strict or warning
    allow_adjacent: bool = True


class NonOverlappingDateRangePattern:
    """Ensure date ranges don't overlap using PostgreSQL exclusion constraints."""

    @classmethod
    def apply(cls, entity: Entity, params: dict) -> tuple[Entity, str]:
        """
        Apply non-overlapping date range pattern.

        Creates a computed daterange column, GIST index, and optional
        exclusion constraint to prevent overlapping date ranges.

        Args:
            entity: Entity to add date range validation to
            params:
                - start_date_field: Name of start date field
                - end_date_field: Name of end date field
                - scope_fields: Optional list of fields to scope constraint by
                - check_mode: 'strict' (exclusion constraint) or 'warning' (index only)
                - allow_adjacent: Whether to allow adjacent ranges (default: true)

        Returns:
            Tuple of (modified_entity, additional_sql)
        """
        config = cls._parse_config(params)

        # Add computed daterange column
        cls._add_daterange_column(entity, config)

        # Add GIST index
        cls._add_gist_index(entity, config)

        # Generate exclusion constraint if strict mode
        additional_sql = ""
        if config.check_mode == "strict":
            additional_sql = cls._generate_exclusion_constraint(entity, config)

        return entity, additional_sql

    @classmethod
    def _parse_config(cls, params: dict) -> DateRangeConfig:
        """Parse pattern parameters."""
        start_date_field = params.get("start_date_field")
        end_date_field = params.get("end_date_field")

        if not start_date_field:
            raise ValueError("Non-overlapping date range pattern requires 'start_date_field'")
        if not end_date_field:
            raise ValueError("Non-overlapping date range pattern requires 'end_date_field'")

        scope_fields = params.get("scope_fields", [])
        check_mode = params.get("check_mode", "strict")
        allow_adjacent = params.get("allow_adjacent", True)

        return DateRangeConfig(
            start_date_field=start_date_field,
            end_date_field=end_date_field,
            scope_fields=scope_fields,
            check_mode=check_mode,
            allow_adjacent=allow_adjacent,
        )

    @classmethod
    def _get_daterange_column_name(cls, config: DateRangeConfig) -> str:
        """Generate name for computed daterange column."""
        return f"{config.start_date_field}_{config.end_date_field}_range"

    @classmethod
    def _add_daterange_column(cls, entity: Entity, config: DateRangeConfig) -> None:
        """Add computed daterange column to entity."""
        column_name = cls._get_daterange_column_name(config)

        # Create computed column that generates a daterange
        # Using '[]' bounds (inclusive on both ends)
        computed_column = {
            "name": column_name,
            "type": "DATERANGE",
            "expression": f"daterange({config.start_date_field}, {config.end_date_field}, '[]')",
            "stored": True,
            "comment": "Computed date range for overlap detection",
        }

        if not hasattr(entity, "computed_columns"):
            entity.computed_columns = []
        entity.computed_columns.append(computed_column)

    @classmethod
    def _add_gist_index(cls, entity: Entity, config: DateRangeConfig) -> None:
        """Add GIST index on daterange column."""
        column_name = cls._get_daterange_column_name(config)
        index_name = f"idx_tb_{entity.name.lower()}_daterange"

        # GIST index for efficient range queries
        index = Index(
            name=index_name,
            columns=[column_name],
            type="gist",
        )
        entity.indexes.append(index)

    @classmethod
    def _generate_exclusion_constraint(cls, entity: Entity, config: DateRangeConfig) -> str:
        """Generate exclusion constraint to prevent overlapping ranges."""
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        constraint_name = f"excl_{entity.name.lower()}_no_overlap"
        daterange_column = cls._get_daterange_column_name(config)

        # Build exclusion constraint
        # Format: EXCLUDE USING gist (scope_field WITH =, daterange WITH &&)
        exclusion_elements = []

        # Add scope fields (if any) with equality check
        if config.scope_fields:
            for scope_field in config.scope_fields:
                # Check if it's a reference field
                field_def = entity.fields.get(scope_field)
                if field_def and field_def.type_name == "ref":
                    # Use FK column name
                    exclusion_elements.append(f"fk_{scope_field} WITH =")
                else:
                    exclusion_elements.append(f"{scope_field} WITH =")

        # Add daterange with overlap operator
        # && checks for overlap (including adjacent if using [] bounds)
        # If we want to disallow adjacent ranges, we still use && but with different bounds
        exclusion_elements.append(f"{daterange_column} WITH &&")

        exclusion_clause = ", ".join(exclusion_elements)

        # Generate ALTER TABLE statement
        ddl = f"""ALTER TABLE {table_name}
ADD CONSTRAINT {constraint_name}
EXCLUDE USING gist ({exclusion_clause});"""

        return ddl
