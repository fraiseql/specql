# SCD Type 2 Transformer
# Implements Slowly Changing Dimension Type 2 pattern

from core.ast_models import Entity, Pattern

from ..pattern_transformer import PatternTransformer


class SCDType2Transformer(PatternTransformer):
    """Implements Slowly Changing Dimension Type 2 pattern."""

    def applies_to(self, pattern: Pattern) -> bool:
        return pattern.type == "temporal_scd_type2_helper"

    def transform_ddl(self, entity: Entity, ddl: str, pattern: Pattern) -> str:
        """
        Add SCD Type 2 fields and functions to the table DDL.

        Adds:
        - effective_from/effective_to date fields
        - is_current boolean field
        - version tracking
        - SCD management functions
        - Performance indexes
        """
        # Add SCD fields to table
        ddl = self._add_scd_fields(ddl, pattern.params)

        # Add SCD management functions
        ddl += "\n\n" + self._generate_scd_functions(entity, pattern.params)

        # Add performance indexes
        ddl += "\n\n" + self._generate_scd_indexes(entity, pattern.params)

        return ddl

    def _add_scd_fields(self, ddl: str, params: dict) -> str:
        """Add SCD tracking fields to the table DDL."""
        effective_from_field = params.get("effective_date_field", "effective_date")
        effective_to_field = params.get("expiry_date_field", "expiry_date")
        is_current_field = params.get("is_current_field", "is_current")

        # Find insertion point (before closing ); )
        lines = ddl.split("\n")
        insert_index = len(lines) - 2  # Before closing );

        scd_fields = [
            f"    {effective_from_field} TIMESTAMPTZ DEFAULT now() NOT NULL,",
            f"    {effective_to_field} TIMESTAMPTZ,",
            f"    {is_current_field} BOOLEAN DEFAULT true NOT NULL,",
        ]

        lines[insert_index:insert_index] = scd_fields
        return "\n".join(lines)

    def _generate_scd_functions(self, entity: Entity, params: dict) -> str:
        """Generate SCD management functions."""
        natural_key = params.get("natural_key", [])
        tracked_fields = params.get("tracked_fields", [])
        effective_from_field = params.get("effective_date_field", "effective_date")
        effective_to_field = params.get("expiry_date_field", "expiry_date")
        is_current_field = params.get("is_current_field", "is_current")

        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        function_name = f"create_new_version_{entity.name.lower()}"

        # Build natural key condition
        natural_key_conditions = []
        for key in natural_key:
            if key in entity.fields and entity.fields[key].is_reference():
                natural_key_conditions.append(f"fk_{key} = new_data->>'fk_{key}'")
            else:
                natural_key_conditions.append(f"{key} = new_data->>'{key}'")

        natural_key_where = " AND ".join(natural_key_conditions)

        # Build update fields
        update_fields = []
        for field in tracked_fields:
            if field in entity.fields and entity.fields[field].is_reference():
                update_fields.append(f"fk_{field} = (new_data->>'fk_{field}')::uuid")
            else:
                update_fields.append(f"{field} = new_data->>'{field}'")

        function_sql = f"""-- SCD Type 2 management function
CREATE OR REPLACE FUNCTION {entity.schema}.{function_name}(
    natural_key_values jsonb,
    new_data jsonb
)
RETURNS void AS $$
DECLARE
    current_record RECORD;
BEGIN
    -- Find current active record
    SELECT * INTO current_record
    FROM {table_name}
    WHERE {natural_key_where}
      AND {is_current_field} = true;

    IF FOUND THEN
        -- Expire current record
        UPDATE {table_name}
        SET {effective_to_field} = now(),
            {is_current_field} = false
        WHERE pk_{entity.name.lower()} = current_record.pk_{entity.name.lower()};
    END IF;

    -- Insert new version
    INSERT INTO {table_name} (
        id,
        {", ".join(natural_key)},
        {", ".join(tracked_fields)},
        {effective_from_field},
        {effective_to_field},
        {is_current_field}
    ) VALUES (
        gen_random_uuid(),
        {", ".join([f"natural_key_values->>'{k}'" for k in natural_key])},
        {", ".join([f"new_data->>'{f}'" for f in tracked_fields])},
        now(),
        NULL,
        true
    );
END;
$$ LANGUAGE plpgsql;"""

        return function_sql

    def _generate_scd_indexes(self, entity: Entity, params: dict) -> str:
        """Generate performance indexes for SCD queries."""
        natural_key = params.get("natural_key", [])
        effective_from_field = params.get("effective_date_field", "effective_date")
        effective_to_field = params.get("expiry_date_field", "expiry_date")
        is_current_field = params.get("is_current_field", "is_current")

        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        # Map logical field names to physical column names
        physical_natural_key = []
        for key in natural_key:
            if key in entity.fields and entity.fields[key].is_reference():
                physical_natural_key.append(f"fk_{key}")
            else:
                physical_natural_key.append(key)

        indexes = [
            "-- SCD performance indexes",
            f"CREATE INDEX idx_{entity.name.lower()}_scd_current",
            f"  ON {table_name} ({', '.join(physical_natural_key)}, {is_current_field})",
            f"  WHERE {is_current_field} = true;",
            "",
            f"CREATE INDEX idx_{entity.name.lower()}_scd_temporal",
            f"  ON {table_name} ({', '.join(physical_natural_key)}, {effective_from_field}, {effective_to_field});",
        ]

        return "\n".join(indexes)

    def get_priority(self) -> int:
        return 40  # Run after basic table creation</content>
