"""Template inheritance pattern implementation."""

from dataclasses import dataclass

from src.core.ast_models import EntityDefinition, FieldDefinition, Index


@dataclass
class TemplateConfig:
    """Configuration for template inheritance."""

    template_entity: str
    template_field: str = "template_id"
    max_depth: int = 5
    merge_strategy: str = "override"  # 'override', 'merge', 'append'


class TemplateInheritancePattern:
    """Generate functions to resolve configuration from template hierarchy."""

    @classmethod
    def apply(cls, entity: EntityDefinition, params: dict) -> None:
        """Apply template inheritance pattern."""
        config = cls._parse_config(params, entity.name)

        # Add template field to entity if not present
        if config.template_field not in entity.fields:
            entity.fields[config.template_field] = FieldDefinition(
                name=config.template_field, type_name="integer", nullable=True
            )

        # Add index for template field
        index_name = f"idx_{entity.name.lower()}_{config.template_field}"
        entity.indexes.append(Index(columns=[config.template_field], type="btree", name=index_name))

        # Generate resolution functions
        functions = cls._generate_resolution_functions(entity, config)

        entity.functions.extend(functions)

        # Add trigger and index as custom DDL
        if not hasattr(entity, "_custom_ddl"):
            entity._custom_ddl = []

        # Add validation trigger
        trigger_sql = cls._generate_validation_trigger(entity, config)
        entity._custom_ddl.append(trigger_sql)

        # Add template field index (ensures it's in DDL output)
        index_sql = cls._generate_template_index(entity, config)
        entity._custom_ddl.append(index_sql)

    @classmethod
    def _parse_config(cls, params: dict, entity_name: str = "self") -> TemplateConfig:
        """Parse pattern configuration."""
        template_entity = params.get("template_entity")
        if not template_entity:
            # For self-referencing inheritance, use current entity as template
            template_entity = entity_name

        return TemplateConfig(
            template_entity=template_entity,
            template_field=params.get("template_field", "template_id"),
            max_depth=params.get("max_depth", 5),
            merge_strategy=params.get("merge_strategy", "override"),
        )

    @classmethod
    def _generate_resolution_functions(
        cls, entity: EntityDefinition, config: TemplateConfig
    ) -> list[str]:
        """Generate template resolution functions."""
        return [
            cls._generate_resolve_template_function(entity, config),
            cls._generate_get_template_chain_function(entity, config),
            cls._generate_depth_validation_function(entity, config),
            cls._generate_validation_trigger(entity, config),
        ]

    @classmethod
    def _generate_resolve_template_function(
        cls, entity: EntityDefinition, config: TemplateConfig
    ) -> str:
        """Generate function to resolve configuration from template chain."""
        func_name = f"resolve_template_{entity.name.lower()}"
        template_table = f"tb_{config.template_entity.lower()}"

        return f"""
-- Resolve configuration from template inheritance chain
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    p_entity_id UUID
)
RETURNS JSONB
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE template_chain AS (
        -- BASE: Entity's direct template
        SELECT
            1 as level,
            t.id as template_id,
            t.config_data
        FROM {entity.schema}.{entity.table_name} e
        JOIN {entity.schema}.{template_table} t ON t.id = e.{config.template_field}
        WHERE e.id = p_entity_id

        UNION ALL

        -- RECURSIVE: Parent templates
        SELECT
            tc.level + 1,
            t.parent_template_id,
            t.config_data
        FROM template_chain tc
        JOIN {entity.schema}.{template_table} t ON t.id = tc.template_id
        WHERE tc.level < {config.max_depth}
          AND t.parent_template_id IS NOT NULL
    )
    -- Merge configurations (deepest first, then override with specific)
    SELECT
        COALESCE(
            (
                SELECT jsonb_object_agg(key, value)
                FROM (
                    SELECT key, value
                    FROM template_chain,
                         LATERAL jsonb_each(config_data)
                    ORDER BY level DESC  -- Parent first, child overrides
                ) merged
            ),
            '{{}}'::jsonb
        );
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name}(UUID)
IS 'Resolve merged configuration from template inheritance chain (max depth: {config.max_depth})';
"""

    @classmethod
    def _generate_get_template_chain_function(
        cls, entity: EntityDefinition, config: TemplateConfig
    ) -> str:
        """Generate function to get template chain (for debugging)."""
        func_name = f"get_template_chain_{entity.name.lower()}"
        template_table = f"tb_{config.template_entity.lower()}"

        return f"""
-- Get template inheritance chain
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    p_entity_id UUID
)
RETURNS TABLE(
    level INTEGER,
    template_id UUID,
    template_name TEXT,
    config_data JSONB
)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE template_chain AS (
        SELECT
            1 as level,
            t.id,
            t.identifier as name,
            t.config_data
        FROM {entity.schema}.{entity.table_name} e
        JOIN {entity.schema}.{template_table} t ON t.id = e.{config.template_field}
        WHERE e.id = p_entity_id

        UNION ALL

        SELECT
            tc.level + 1,
            t.id,
            t.identifier,
            t.config_data
        FROM template_chain tc
        JOIN {entity.schema}.{template_table} t ON t.id = tc.template_id
        WHERE tc.level < {config.max_depth}
    )
    SELECT * FROM template_chain ORDER BY level;
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name}(UUID)
IS 'Get template inheritance chain for debugging';
"""

    @classmethod
    def _generate_depth_validation_function(
        cls, entity: EntityDefinition, config: TemplateConfig
    ) -> str:
        """Generate function to validate template depth."""
        func_name = f"validate_template_depth_{entity.name.lower()}"
        template_table = f"tb_{config.template_entity.lower()}"

        return f"""
-- Validate template inheritance depth
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    p_entity_id UUID
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
  v_depth integer;
BEGIN
  WITH RECURSIVE template_chain AS (
    SELECT
      1 as depth,
      {config.template_field} as template_id
    FROM {entity.schema}.tb_{entity.name.lower()}
    WHERE id = p_entity_id

    UNION ALL

    SELECT
      tc.depth + 1,
      t.{config.template_field}
    FROM template_chain tc
    JOIN {entity.schema}.{template_table} t
      ON t.id = tc.template_id
    WHERE tc.depth < {config.max_depth} + 1
      AND tc.template_id IS NOT NULL
  )
  SELECT MAX(depth) INTO v_depth
  FROM template_chain;

  IF v_depth > {config.max_depth} THEN
    RAISE EXCEPTION 'Template hierarchy exceeds maximum depth of {config.max_depth}';
  END IF;

  RETURN true;
END;
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name}(UUID)
IS 'Validate template inheritance depth does not exceed maximum';
"""

    @classmethod
    def _generate_validation_trigger(cls, entity: EntityDefinition, config: TemplateConfig) -> str:
        """Generate trigger to validate template changes."""
        trigger_name = f"trg_validate_template_{entity.name.lower()}"
        func_name = f"validate_template_depth_{entity.name.lower()}"

        return f"""
-- Validation trigger function
CREATE OR REPLACE FUNCTION {entity.schema}.{trigger_name}_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Validate template depth on insert/update
  IF NEW.{config.template_field} IS NOT NULL THEN
    PERFORM {entity.schema}.{func_name}(NEW.id);
  END IF;
  RETURN NEW;
END;
$$;

-- Trigger
CREATE TRIGGER {trigger_name}
  BEFORE INSERT OR UPDATE ON {entity.schema}.tb_{entity.name.lower()}
  FOR EACH ROW
  EXECUTE FUNCTION {entity.schema}.{trigger_name}_func();
"""

    @classmethod
    def _generate_template_index(cls, entity: EntityDefinition, config: TemplateConfig) -> str:
        """Generate index for template field lookups."""
        table_name = f"tb_{entity.name.lower()}"
        idx_name = f"idx_{entity.name.lower()}_{config.template_field}"

        return f"""
-- Index for template lookups
CREATE INDEX {idx_name}
ON {entity.schema}.{table_name}({config.template_field})
WHERE {config.template_field} IS NOT NULL;
"""
