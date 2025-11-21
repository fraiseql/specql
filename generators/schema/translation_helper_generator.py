from core.ast_models import EntityDefinition
from utils.safe_slug import safe_slug


class TranslationHelperGenerator:
    """
    Generates helper functions for translation table lookups.

    Creates functions like get_{entity}_{field}() that retrieve translated
    field values with automatic locale fallback. Requires get_default_locale()
    function to be available in the target schema.
    """

    def generate(self, entity: EntityDefinition) -> str:
        """
        Generate helper functions for all translatable fields.

        Args:
            entity: EntityDefinition with translations config

        Returns:
            SQL string with helper function definitions

        Raises:
            ValueError: If translatable fields are not found in entity

        Note:
            Requires {schema}.get_default_locale() function to exist
        """
        if not entity.translations or not entity.translations.enabled:
            return ""

        # Validate that all translatable fields exist in the entity
        self._validate_translatable_fields(entity)

        helpers = []

        for field_name in entity.translations.fields:
            helpers.append(self._generate_field_helper(entity, field_name))

        return "\n\n".join(helpers)

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

    def _generate_field_helper(self, entity: EntityDefinition, field_name: str) -> str:
        """Generate helper function for a single translatable field"""
        table_name = safe_slug(entity.name)
        translation_table = f"tl_{table_name}"

        # Get field SQL type
        field_def = entity.fields[field_name]
        return_type = self._map_field_type(field_def)

        function_sql = f"""
-- Helper function: Get translated {field_name}
CREATE OR REPLACE FUNCTION {entity.schema}.get_{table_name}_{field_name}(
    p_{table_name}_pk UUID,
    p_locale_pk UUID DEFAULT NULL
)
RETURNS {return_type} AS $$
BEGIN
    RETURN (
        SELECT {field_name}
        FROM {entity.schema}.{translation_table}
        WHERE fk_{table_name} = p_{table_name}_pk
          AND fk_locale = COALESCE(p_locale_pk, {entity.schema}.get_default_locale())
          AND deleted_at IS NULL
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION {entity.schema}.get_{table_name}_{field_name}(UUID, UUID) IS
    'Get translated {field_name} for {entity.name}. Falls back to default locale if translation not found.';
""".strip()

        return function_sql

    def _map_field_type(self, field_def) -> str:
        """
        Map SpecQL field type to SQL return type for helper functions.

        Args:
            field_def: FieldDefinition with type_name

        Returns:
            SQL type string for function return type
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
        return type_map.get(field_def.type_name.lower(), "TEXT")
