"""SCD Type 2 helper pattern implementation."""

from dataclasses import dataclass

from core.ast_models import Entity, FieldDefinition, Index


@dataclass
class SCDType2Config:
    """Configuration for SCD Type 2."""

    natural_key: list[str]
    tracked_fields: list[str]
    effective_date_field: str = "effective_date"
    expiry_date_field: str = "expiry_date"
    is_current_field: str = "is_current"
    version_field: str | None = None


class SCDType2HelperPattern:
    """Slowly Changing Dimension Type 2 helper pattern."""

    @classmethod
    def apply(cls, entity: Entity, params: dict) -> tuple[Entity, str]:
        """
        Apply SCD Type 2 helper pattern.

        Adds fields and functions for tracking historical changes to records.

        Args:
            entity: Entity to add SCD Type 2 tracking to
            params:
                - natural_key: List of fields that form the natural key
                - tracked_fields: List of fields to track changes for
                - effective_date_field: Name of effective date field (default: effective_date)
                - expiry_date_field: Name of expiry date field (default: expiry_date)
                - is_current_field: Name of is_current flag field (default: is_current)
                - version_field: Optional version field name

        Returns:
            Tuple of (modified_entity, additional_sql)
        """
        config = cls._parse_config(params)

        # Add SCD fields to entity
        cls._add_scd_fields(entity, config)

        # Add indexes for performance
        cls._add_scd_indexes(entity, config)

        # Generate helper function for creating new versions
        function_sql = cls._generate_helper_function(entity, config)

        # Store function in entity.functions for template rendering
        if not hasattr(entity, "functions") or entity.functions is None:
            entity.functions = []
        entity.functions.append(function_sql)

        # Return entity and empty additional SQL (functions rendered via template)
        return entity, ""

    @classmethod
    def _parse_config(cls, params: dict) -> SCDType2Config:
        """Parse pattern parameters."""
        natural_key = params.get("natural_key", [])
        tracked_fields = params.get("tracked_fields", [])

        if not natural_key:
            raise ValueError("SCD Type 2 pattern requires 'natural_key'")

        # Handle alternative parameter names
        effective_date_field = params.get("effective_date_field") or params.get(
            "effective_from_field", "effective_date"
        )
        expiry_date_field = params.get("expiry_date_field") or params.get(
            "effective_to_field", "expiry_date"
        )
        is_current_field = params.get("is_current_field", "is_current")
        version_field = params.get("version_field")

        return SCDType2Config(
            natural_key=natural_key,
            tracked_fields=tracked_fields,
            effective_date_field=effective_date_field,
            expiry_date_field=expiry_date_field,
            is_current_field=is_current_field,
            version_field=version_field,
        )

    @classmethod
    def _add_scd_fields(cls, entity: Entity, config: SCDType2Config) -> None:
        """Add SCD Type 2 fields to entity."""
        # Add effective date field
        if config.effective_date_field not in entity.fields:
            entity.fields[config.effective_date_field] = FieldDefinition(
                name=config.effective_date_field,
                type_name="timestamp",
                nullable=False,
                default="CURRENT_TIMESTAMP",
                description="Effective start date for this version",
            )

        # Add expiry date field
        if config.expiry_date_field not in entity.fields:
            entity.fields[config.expiry_date_field] = FieldDefinition(
                name=config.expiry_date_field,
                type_name="timestamp",
                nullable=True,
                description="Effective end date for this version (NULL if current)",
            )

        # Add is_current field
        if config.is_current_field not in entity.fields:
            entity.fields[config.is_current_field] = FieldDefinition(
                name=config.is_current_field,
                type_name="boolean",
                nullable=False,
                default="true",
                description="Flag indicating if this is the current version",
            )

        # Add version field if specified
        if config.version_field and config.version_field not in entity.fields:
            entity.fields[config.version_field] = FieldDefinition(
                name=config.version_field,
                type_name="integer",
                nullable=False,
                default="1",
                description="Version number",
            )

    @classmethod
    def _add_scd_indexes(cls, entity: Entity, config: SCDType2Config) -> None:
        """Add indexes for SCD Type 2 queries."""
        # Composite index on natural_key + effective dates for efficient lookups
        composite_fields = config.natural_key + [
            config.effective_date_field,
            config.expiry_date_field,
        ]

        # Create index on natural key and effective dates
        index_name = f"idx_tb_{entity.name.lower()}_scd_lookup"
        index = Index(
            name=index_name,
            columns=composite_fields,
            type="btree",
        )
        entity.indexes.append(index)

        # Add index on is_current for filtering current records
        current_index = Index(
            name=f"idx_tb_{entity.name.lower()}_{config.is_current_field}",
            columns=[config.is_current_field],
            type="btree",
        )
        entity.indexes.append(current_index)

    @classmethod
    def _generate_helper_function(cls, entity: Entity, config: SCDType2Config) -> str:
        """Generate helper function for creating new SCD versions."""
        function_name = f"{entity.schema}.create_new_version_{entity.name.lower()}"
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        # Build natural key WHERE clause
        natural_key_where = []
        for key_field in config.natural_key:
            field_def = entity.fields.get(key_field)
            if field_def:
                pg_type = field_def.get_postgres_type()
                natural_key_where.append(
                    f"{key_field} = (natural_key_values->>'{key_field}')::{pg_type}"
                )

        natural_key_where_clause = " AND ".join(natural_key_where)

        # Build field list for INSERT (excluding SCD fields)
        scd_fields = {
            config.effective_date_field,
            config.expiry_date_field,
            config.is_current_field,
        }
        if config.version_field:
            scd_fields.add(config.version_field)

        insert_fields = []
        for field_name, field_def in entity.fields.items():
            if field_name not in scd_fields:
                insert_fields.append(field_name)

        field_list = ", ".join(insert_fields)

        # Build field values from JSONB
        field_values = []
        for field_name in insert_fields:
            field_def = entity.fields[field_name]
            pg_type = field_def.get_postgres_type()
            field_values.append(f"(new_data->>'{field_name}')::{pg_type}")

        field_list_from_jsonb = ", ".join(field_values)

        # Generate function SQL
        function_sql = f"""CREATE OR REPLACE FUNCTION {function_name}(
    natural_key_values jsonb,
    new_data jsonb
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Expire the current version
    UPDATE {table_name}
    SET
        {config.expiry_date_field} = CURRENT_TIMESTAMP,
        {config.is_current_field} = false
    WHERE {natural_key_where_clause}
      AND {config.is_current_field} = true;

    -- Insert new version
    INSERT INTO {table_name} (
        {field_list},
        {config.effective_date_field},
        {config.expiry_date_field},
        {config.is_current_field}
    ) VALUES (
        {field_list_from_jsonb},
        CURRENT_TIMESTAMP,
        NULL,
        true
    );
END;
$$;"""

        return function_sql
