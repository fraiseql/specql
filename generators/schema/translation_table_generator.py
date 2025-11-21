from core.ast_models import EntityDefinition
from generators.schema.naming_conventions import NamingConventions
from utils.safe_slug import safe_slug


class TranslationTableGenerator:
    """
    Generates tl_* translation tables for entities with translations config.

    Creates translation tables following the Hybrid Trinity Pattern:
    - INTEGER primary key (pk_{entity}_translation)
    - UUID id field (for API access)
    - No identifier field (computed virtually from parent + locale)

    Translation tables store locale-specific versions of translatable fields
    and maintain referential integrity with both the parent entity and locale tables.
    """

    def __init__(self, naming: NamingConventions | None = None):
        """
        Initialize the translation table generator.

        Args:
            naming: Naming conventions instance (optional, creates default if None)
        """
        self.naming = naming or NamingConventions()

    def generate(self, entity: EntityDefinition) -> str:
        """
        Generate translation table DDL for entities with translations enabled.

        Args:
            entity: EntityDefinition with translations config

        Returns:
            DDL string for translation table, or empty string if translations not enabled

        Raises:
            ValueError: If translatable fields are not found in entity
        """
        if not entity.translations or not entity.translations.enabled:
            return ""

        # Validate that all translatable fields exist in the entity
        self._validate_translatable_fields(entity)

        # Validate that translatable fields are appropriate for translation
        self._validate_field_types_for_translation(entity)

        table_name = self._get_translation_table_name(entity)
        parent_table_name = safe_slug(entity.name)

        ddl_parts = []

        # CREATE TABLE
        ddl_parts.append(f"-- Translation Table: {entity.name}")
        ddl_parts.append(f"CREATE TABLE {entity.schema}.{table_name} (")

        # Hybrid Trinity pattern (2 fields: INTEGER PK + UUID, no identifier)
        ddl_parts.append("    -- Hybrid Trinity Pattern")
        ddl_parts.append(
            f"    pk_{parent_table_name}_translation INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,"
        )
        ddl_parts.append("    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),")
        ddl_parts.append("    -- Note: No identifier field (computed virtually)")
        ddl_parts.append("")

        # Foreign keys
        ddl_parts.append("    -- Foreign Keys")
        ddl_parts.append(f"    fk_{parent_table_name} UUID NOT NULL")
        ddl_parts.append(
            f"        REFERENCES {entity.schema}.tb_{parent_table_name}(pk_{parent_table_name})"
        )
        ddl_parts.append("        ON DELETE CASCADE,")
        ddl_parts.append("    fk_locale UUID NOT NULL")
        ddl_parts.append("        REFERENCES common.tb_locale(pk_locale)")
        ddl_parts.append("        ON DELETE CASCADE,")
        ddl_parts.append("")

        # Translatable fields
        ddl_parts.append("    -- Translatable Fields")
        for field_name in entity.translations.fields:
            field_def = entity.fields.get(field_name)
            if field_def:
                sql_type = self._map_field_type(field_def)
                nullable = "NULL" if field_def.nullable else "NOT NULL"
                ddl_parts.append(f"    {field_name} {sql_type} {nullable},")
        ddl_parts.append("")

        # Audit fields
        ddl_parts.append("    -- Audit Fields")
        ddl_parts.append("    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),")
        ddl_parts.append("    created_by UUID,")
        ddl_parts.append("    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),")
        ddl_parts.append("    updated_by UUID,")
        ddl_parts.append("    deleted_at TIMESTAMPTZ,")
        ddl_parts.append("    deleted_by UUID,")
        ddl_parts.append("")

        # Unique constraint
        ddl_parts.append("    -- Unique Constraint")
        ddl_parts.append(
            f"    CONSTRAINT {table_name}_uniq UNIQUE (fk_{parent_table_name}, fk_locale)"
        )

        ddl_parts.append(");")
        ddl_parts.append("")

        # Comments
        ddl_parts.append(
            f"COMMENT ON TABLE {entity.schema}.{table_name} IS 'Translation table for {entity.name}. Stores locale-specific translatable fields.';"
        )

        return "\n".join(ddl_parts)

    def _validate_translatable_fields(self, entity: EntityDefinition) -> None:
        """Validate that all translatable fields exist in the entity"""
        if not entity.translations or not entity.translations.fields:
            return

        missing_fields = []
        for field_name in entity.translations.fields:
            if field_name not in entity.fields:
                missing_fields.append(field_name)

        if missing_fields:
            raise ValueError(
                f"Entity '{entity.name}' has translations config but missing fields: {missing_fields}. "
                f"Available fields: {list(entity.fields.keys())}"
            )

    def _validate_field_types_for_translation(self, entity: EntityDefinition) -> None:
        """Validate that translatable fields are appropriate for translation (text-based only)"""
        if not entity.translations or not entity.translations.fields:
            return

        # Text-based types that make sense for translation
        text_types = {"text", "string"}

        invalid_fields = []
        for field_name in entity.translations.fields:
            field_def = entity.fields.get(field_name)
            if field_def and field_def.type_name.lower() not in text_types:
                invalid_fields.append(f"{field_name} ({field_def.type_name})")

        if invalid_fields:
            raise ValueError(
                f"Entity '{entity.name}' has translations config with non-text fields: {invalid_fields}. "
                f"Translations are only supported for text-based fields."
            )

    def _get_translation_table_name(self, entity: EntityDefinition) -> str:
        """
        Get translation table name following tl_* convention.

        Uses custom table_name from translations config if specified,
        otherwise generates tl_{entity_slug}.

        Args:
            entity: EntityDefinition with translations config

        Returns:
            Translation table name (e.g., "tl_manufacturer")
        """
        if entity.translations and entity.translations.table_name:
            return entity.translations.table_name
        return f"tl_{safe_slug(entity.name)}"

    def _map_field_type(self, field_def) -> str:
        """
        Map SpecQL field type to SQL type for translation tables.

        Args:
            field_def: FieldDefinition with type_name

        Returns:
            SQL type string

        Raises:
            ValueError: If field type is not supported for translations
        """
        type_map = {
            "text": "TEXT",
            "integer": "INTEGER",
            "decimal": "DECIMAL",
            "boolean": "BOOLEAN",
            "timestamp": "TIMESTAMPTZ",
            "date": "DATE",
            "jsonb": "JSONB",
        }

        sql_type = type_map.get(field_def.type_name.lower())
        if not sql_type:
            raise ValueError(
                f"Field '{field_def.name}' has unsupported type '{field_def.type_name}' for translations. "
                f"Supported types: {list(type_map.keys())}"
            )

        return sql_type
