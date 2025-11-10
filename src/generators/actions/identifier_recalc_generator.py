"""
Identifier Recalculation Generator

Generates PostgreSQL functions for recalculating entity identifiers based on SpecQL configuration.
Supports hierarchical and composite identifier strategies.
"""

from src.core.ast_models import EntityDefinition
from src.core.separators import Separators


class IdentifierRecalcGenerator:
    """Generates identifier recalculation functions."""

    def generate_recalc_function(self, entity: EntityDefinition) -> str:
        """Generate the appropriate recalculation function based on entity configuration."""

        if entity.identifier and entity.identifier.strategy == "composite_hierarchical":
            return self._generate_composite_hierarchical_strategy(entity)
        elif entity.hierarchical:
            return self._generate_hierarchical_strategy(entity)
        else:
            return self._generate_simple_strategy(entity)

    def _generate_simple_strategy(self, entity: EntityDefinition) -> str:
        """Generate simple identifier recalculation (non-hierarchical)."""
        # Placeholder - will be implemented if needed
        return "-- Simple strategy not implemented yet"

    def _generate_hierarchical_strategy(self, entity: EntityDefinition) -> str:
        """Generate hierarchical identifier recalculation with DOT separator."""

        entity_lower = entity.name.lower()
        schema = entity.schema

        # Get separator (default is now DOT)
        separator = Separators.HIERARCHY
        if entity.identifier and entity.identifier.separator:
            separator = entity.identifier.separator

        # Check for tenant prefix
        has_tenant_prefix = self._should_apply_tenant_prefix(entity)
        tenant_expr = ""
        if has_tenant_prefix:
            tenant_lookup = self._get_tenant_identifier_expression(entity)
            tenant_expr = f"{tenant_lookup} || '{Separators.TENANT}' || "

        # Build component expression
        component_expr = self._build_component_expression(
            entity.identifier.components
            if entity.identifier
            else [{"field": "name", "transform": "slugify"}]
        )

        return f"""
-- Recalculate hierarchical identifiers (separator: '{separator}')
CREATE OR REPLACE FUNCTION {schema}.recalculate_{entity_lower}_identifier(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
) RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER := 0;
BEGIN
    -- Build hierarchical identifiers using recursive CTE
    WITH RECURSIVE hierarchy AS (
        -- Root nodes
        SELECT
            t.pk_{entity_lower},
            {tenant_expr}{component_expr} AS base_identifier
        FROM {schema}.tb_{entity_lower} t
        WHERE t.fk_parent_{entity_lower} IS NULL

        UNION ALL

        -- Child nodes (use configured separator: '{separator}')
        SELECT
            child.pk_{entity_lower},
            parent.base_identifier || '{separator}' || {component_expr}
        FROM {schema}.tb_{entity_lower} child
        JOIN hierarchy parent ON child.fk_parent_{entity_lower} = parent.pk_{entity_lower}
    )
    UPDATE {schema}.tb_{entity_lower} t
    SET
        identifier = h.base_identifier,
        base_identifier = h.base_identifier,
        identifier_recalculated_at = now(),
        identifier_recalculated_by = ctx.updated_by
    FROM hierarchy h
    WHERE t.pk_{entity_lower} = h.pk_{entity_lower}
      AND (
          t.identifier IS DISTINCT FROM h.base_identifier OR
          t.base_identifier IS DISTINCT FROM h.base_identifier
      );

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalculate_{entity_lower}_identifier IS
'Recalculate hierarchical identifiers for {entity.name}.
Separator: {separator} (default: dot for hierarchy)
Pattern: {{tenant}}|{{parent}}{separator}{{child}}';
""".strip()

    def _generate_composite_hierarchical_strategy(self, entity: EntityDefinition) -> str:
        """Generate composite hierarchical identifier (allocation pattern)."""

        entity_lower = entity.name.lower()
        schema = entity.schema

        # Get separators
        composition_sep = entity.identifier.composition_separator or Separators.COMPOSITION

        # Check for tenant prefix
        has_tenant_prefix = self._should_apply_tenant_prefix(entity)
        tenant_field = self._detect_tenant_field(entity) if has_tenant_prefix else None

        # Build component expressions
        component_exprs = []
        for comp in entity.identifier.components:
            expr = f"t.{comp.field}"

            # Apply transforms
            if comp.transform == "slugify":
                expr = f"public.safe_slug({expr})"
            elif comp.transform == "uppercase":
                expr = f"UPPER({expr})"
            elif comp.transform == "lowercase":
                expr = f"LOWER({expr})"

            # Strip tenant prefix if requested
            if comp.strip_tenant_prefix and has_tenant_prefix and tenant_field:
                tenant_lookup = self._get_tenant_identifier_expression(entity)
                expr = f"""REGEXP_REPLACE(
                    {expr},
                    '^' || {tenant_lookup} || '\\{Separators.TENANT}',
                    ''
                )"""

            # Apply character replacements
            if comp.replace:
                for old_char, new_char in comp.replace.items():
                    expr = f"REPLACE({expr}, '{old_char}', '{new_char}')"

            component_exprs.append(expr)

        # Join components with composition separator
        components_joined = f" || '{composition_sep}' || ".join(component_exprs)

        # Add tenant prefix if applicable
        if has_tenant_prefix:
            tenant_lookup = self._get_tenant_identifier_expression(entity)
            base_identifier_expr = (
                f"{tenant_lookup} || '{Separators.TENANT}' || {components_joined}"
            )
        else:
            base_identifier_expr = components_joined

        return f"""
-- Recalculate composite hierarchical identifiers (allocation pattern)
-- Composition separator: '{composition_sep}'
CREATE OR REPLACE FUNCTION {schema}.recalculate_{entity_lower}_identifier(
    ctx core.recalculation_context DEFAULT ROW(NULL, NULL, NULL)::core.recalculation_context
) RETURNS INTEGER AS $$
DECLARE
    v_updated_count INTEGER := 0;
BEGIN
    -- Create temp table
    DROP TABLE IF EXISTS tmp_{entity_lower}_identifiers;
    CREATE TEMP TABLE tmp_{entity_lower}_identifiers (
        pk_{entity_lower} INTEGER,
        base_identifier TEXT,
        unique_identifier TEXT,
        sequence_number INTEGER
    ) ON COMMIT DROP;

    -- Calculate composite identifiers
    INSERT INTO tmp_{entity_lower}_identifiers (pk_{entity_lower}, base_identifier)
    SELECT
        t.pk_{entity_lower},
        {base_identifier_expr} AS base_identifier
    FROM {schema}.tb_{entity_lower} t
    WHERE
        CASE
            WHEN ctx.pk IS NOT NULL THEN t.id = ctx.pk
            WHEN ctx.pk_tenant IS NOT NULL THEN t.tenant_id = ctx.pk_tenant
            ELSE true
        END;

    -- Deduplicate (same logic as simple strategy)
    -- ... deduplication loop ...

    -- Apply updates
    UPDATE {schema}.tb_{entity_lower} t
    SET
        identifier = tmp.unique_identifier,
        base_identifier = tmp.base_identifier,
        sequence_number = tmp.sequence_number,
        identifier_recalculated_at = now(),
        identifier_recalculated_by = ctx.updated_by
    FROM tmp_{entity_lower}_identifiers tmp
    WHERE t.pk_{entity_lower} = tmp.pk_{entity_lower}
      AND (
          t.identifier IS DISTINCT FROM tmp.unique_identifier OR
          t.sequence_number IS DISTINCT FROM tmp.sequence_number
      );

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;
    RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION {schema}.recalculate_{entity_lower}_identifier IS
'Recalculate composite hierarchical identifiers for {entity.name}.
Strategy: composite_hierarchical
Pattern: {{tenant}}|{{comp1}}{composition_sep}{{comp2}}{composition_sep}...
Components have tenant prefix stripped to avoid duplication.';
""".strip()

    def _should_apply_tenant_prefix(self, entity: EntityDefinition) -> bool:
        """Check if tenant prefix should be applied."""
        # Simple heuristic: if entity has tenant_id field, apply prefix
        return any(field.name == "tenant_id" for field in entity.fields.values())

    def _detect_tenant_field(self, entity: EntityDefinition) -> str | None:
        """Detect the tenant field name."""
        for field in entity.fields.values():
            if field.name == "tenant_id":
                return field.name
        return None

    def _get_tenant_identifier_expression(self, entity: EntityDefinition) -> str:
        """Get expression to lookup tenant identifier."""
        tenant_field = self._detect_tenant_field(entity)
        if tenant_field:
            return f"(SELECT identifier FROM management.tb_tenant WHERE id = t.{tenant_field})"
        return "'unknown-tenant'"

    def _build_component_expression(self, components: list) -> str:
        """Build SQL expression for identifier components."""
        if not components:
            return "public.safe_slug(t.name)"  # Default fallback

        expressions = []
        for comp in components:
            if isinstance(comp, dict):
                field = comp["field"]
                transform = comp.get("transform", "slugify")
            else:
                # Simple string component
                field = comp
                transform = "slugify"

            expr = f"t.{field}"
            if transform == "slugify":
                expr = f"public.safe_slug({expr})"
            elif transform == "uppercase":
                expr = f"UPPER({expr})"
            elif transform == "lowercase":
                expr = f"LOWER({expr})"

            expressions.append(expr)

        return " || '_' || ".join(expressions)  # Default join with underscore for now
