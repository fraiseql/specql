"""Temporal non-overlapping daterange pattern implementation."""

from dataclasses import dataclass

from src.core.ast_models import EntityDefinition, FieldDefinition


@dataclass
class DateRangeConfig:
    """Configuration for non-overlapping daterange pattern."""

    scope_fields: list[str]
    start_date_field: str
    end_date_field: str
    check_mode: str = "strict"  # 'strict' or 'warning'
    inclusive_bounds: str = "[)"  # '[)', '[]', '()', '(]'
    allow_adjacent: bool = True


class NonOverlappingDateRangePattern:
    """Prevent overlapping date ranges within a scope."""

    @classmethod
    def apply(cls, entity: EntityDefinition, params: dict) -> None:
        """
        Apply non-overlapping daterange pattern.

        Generates:
        1. Computed daterange column
        2. GIST index on daterange column
        3. EXCLUSION constraint (if strict mode)

        Args:
            entity: Entity to modify
            params: Pattern parameters
                - scope_fields: list[str] - Fields defining scope (e.g., ['machine_id'])
                - start_date_field: str - Start date field name
                - end_date_field: str - End date field name
                - check_mode: 'strict' | 'warning' (default: strict)
                - inclusive_bounds: '[)' | '[]' | '()' | '(]' (default: '[)')
        """
        config = cls._parse_config(params)

        # Validate fields exist
        cls._validate_fields(entity, config)

        # Add computed daterange column
        range_column_name = cls._add_daterange_column(entity, config)

        # Add GIST index
        cls._add_gist_index(entity, range_column_name)

        # Add exclusion constraint (if strict mode)
        if config.check_mode == "strict":
            cls._add_exclusion_constraint(entity, config, range_column_name)
        elif config.check_mode == "warning":
            cls._add_warning_trigger(entity, config, range_column_name)

    @classmethod
    def _parse_config(cls, params: dict) -> DateRangeConfig:
        """Parse pattern parameters."""
        scope_fields = params.get("scope_fields", [])
        if not scope_fields:
            raise ValueError("Non-overlapping daterange pattern requires 'scope_fields'")

        start_field = params.get("start_date_field")
        end_field = params.get("end_date_field")

        if not start_field or not end_field:
            raise ValueError(
                "Non-overlapping daterange pattern requires 'start_date_field' and 'end_date_field'"
            )

        return DateRangeConfig(
            scope_fields=scope_fields,
            start_date_field=start_field,
            end_date_field=end_field,
            check_mode=params.get("check_mode", "strict"),
            inclusive_bounds=params.get("inclusive_bounds", "[)"),
            allow_adjacent=params.get("allow_adjacent", True),
        )

    @classmethod
    def _validate_fields(cls, entity: EntityDefinition, config: DateRangeConfig) -> None:
        """Validate that required fields exist."""
        # Check scope fields
        for field in config.scope_fields:
            if field not in entity.fields:
                raise ValueError(f"Scope field '{field}' not found in entity '{entity.name}'")

        # Check date fields
        if config.start_date_field not in entity.fields:
            raise ValueError(f"Start date field '{config.start_date_field}' not found")
        if config.end_date_field not in entity.fields:
            raise ValueError(f"End date field '{config.end_date_field}' not found")

    @classmethod
    def _add_daterange_column(cls, entity: EntityDefinition, config: DateRangeConfig) -> str:
        """
        Add computed daterange column.

        Returns:
            str: Name of the created range column
        """
        range_col_name = f"{config.start_date_field}_{config.end_date_field}_range"

        # Create computed column
        range_field = FieldDefinition(
            name=range_col_name,
            type_name="DATERANGE",
            nullable=False,
            is_computed=True,
            computed_expression=f"daterange({config.start_date_field}, {config.end_date_field}, '{config.inclusive_bounds}')",
        )

        entity.fields[range_col_name] = range_field

        return range_col_name

    @classmethod
    def _add_gist_index(cls, entity: EntityDefinition, range_column: str) -> None:
        """Add GIST index on range column for efficient overlap queries."""
        index_name = f"idx_{entity.table_name}_daterange"

        # Add index metadata to entity
        if not hasattr(entity, "_indexes"):
            entity._indexes = []

        entity._indexes.append(
            {
                "name": index_name,
                "columns": [range_column],
                "index_type": "gist",
                "comment": "GIST index for efficient date range overlap detection",
            }
        )

    @classmethod
    def _add_exclusion_constraint(
        cls, entity: EntityDefinition, config: DateRangeConfig, range_column: str
    ) -> None:
        """Add exclusion constraint to prevent overlapping ranges."""
        constraint_name = f"excl_{entity.name.lower()}_no_overlap"

        # Build exclusion elements
        # Format: (scope_field1 WITH =, scope_field2 WITH =, range_col WITH &&)
        exclusion_elements = []

        for scope_field in config.scope_fields:
            exclusion_elements.append(f"{scope_field} WITH =")

        exclusion_elements.append(f"{range_column} WITH &&")

        constraint_ddl = f"""
ALTER TABLE {entity.schema}.{entity.table_name}
ADD CONSTRAINT {constraint_name}
EXCLUDE USING gist (
    {", ".join(exclusion_elements)}
);"""

        # Add to entity's custom DDL
        if not hasattr(entity, "_custom_ddl"):
            entity._custom_ddl = []

        entity._custom_ddl.append(constraint_ddl.strip())

    @classmethod
    def _add_warning_trigger(
        cls, entity: EntityDefinition, config: DateRangeConfig, range_column: str
    ) -> None:
        """Add trigger that warns about overlaps but doesn't block them."""
        function_name = f"warn_overlap_{entity.table_name}"
        trigger_name = f"trigger_warn_overlap_{entity.table_name}"

        # Build overlap check query
        scope_conditions = " AND ".join(f"NEW.{field} = {field}" for field in config.scope_fields)

        function_ddl = f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{function_name}()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_overlap_count INTEGER;
BEGIN
    -- Check for overlaps
    SELECT COUNT(*)
    INTO v_overlap_count
    FROM {entity.schema}.{entity.table_name}
    WHERE {scope_conditions}
      AND {range_column} && NEW.{range_column}
      AND pk_id != COALESCE(NEW.pk_id, -1);  -- Exclude current record on UPDATE

    IF v_overlap_count > 0 THEN
        RAISE WARNING 'Date range overlap detected for % (% overlapping records)',
            NEW.identifier, v_overlap_count;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER {trigger_name}
BEFORE INSERT OR UPDATE ON {entity.schema}.{entity.table_name}
FOR EACH ROW
EXECUTE FUNCTION {entity.schema}.{function_name}();
"""

        if not hasattr(entity, "_custom_ddl"):
            entity._custom_ddl = []

        entity._custom_ddl.append(function_ddl.strip())
