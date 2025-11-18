"""Recursive dependency validator pattern implementation."""

from dataclasses import dataclass
from typing import Optional
from src.core.ast_models import EntityDefinition


@dataclass
class DependencyConfig:
    """Configuration for recursive dependency validation."""

    dependency_entity: Optional[str] = None  # Entity storing dependencies (for cross-entity deps)
    parent_field: Optional[str] = None  # Field for self-referencing hierarchies
    max_depth: int = 10
    check_circular: bool = True


class RecursiveDependencyValidator:
    """Generate validation functions for recursive dependencies."""

    @classmethod
    def apply(cls, entity: EntityDefinition, params: dict) -> None:
        """
        Apply recursive dependency validation pattern.

        Generates:
        1. Recursive CTE function to find all dependencies
        2. Validation function to check dependencies
        3. Conflict detection function

        Args:
            entity: Entity to validate (e.g., ProductConfiguration)
            params:
                - dependency_entity: Entity storing dependency rules
                - max_depth: Maximum recursion depth (default: 10)
        """
        config = cls._parse_config(params)

        # Generate validation functions
        functions = cls._generate_validation_functions(entity, config)

        # Add to entity's functions
        entity.functions.extend(functions)

    @classmethod
    def _parse_config(cls, params: dict) -> DependencyConfig:
        """Parse pattern parameters."""
        dependency_entity = params.get("dependency_entity")
        parent_field = params.get("parent_field")

        # Safe null check
        has_dependency_entity = dependency_entity is not None and dependency_entity != ""
        has_parent_field = parent_field is not None and parent_field != ""

        if not has_dependency_entity and not has_parent_field:
            raise ValueError(
                "Recursive dependency validator requires either 'dependency_entity' or 'parent_field'"
            )

        if has_dependency_entity and has_parent_field:
            raise ValueError("Cannot specify both 'dependency_entity' and 'parent_field'")

        # Fix allow_cycles handling
        allow_cycles = params.get("allow_cycles", False)  # Default to False (check for cycles)
        check_circular = not allow_cycles

        return DependencyConfig(
            dependency_entity=dependency_entity,
            parent_field=parent_field,
            max_depth=params.get("max_depth", 10),
            check_circular=check_circular,
        )

    @classmethod
    def _generate_validation_functions(
        cls, entity: EntityDefinition, config: DependencyConfig
    ) -> list[str]:
        """Generate all validation functions."""
        functions = []

        # 1. Find all dependencies (recursive)
        functions.append(cls._generate_find_dependencies_function(entity, config))

        # 2. Validate dependencies are satisfied
        functions.append(cls._generate_validate_dependencies_function(entity, config))

        # 3. Check for conflicts
        functions.append(cls._generate_check_conflicts_function(entity, config))

        # 4. Detect circular dependencies
        if config.check_circular:
            functions.append(cls._generate_circular_check_function(entity, config))

        return functions

    @classmethod
    def _generate_find_dependencies_function(
        cls, entity: EntityDefinition, config: DependencyConfig
    ) -> str:
        """
        Generate function to find all dependencies recursively.

        Returns array of required feature IDs.
        """
        func_name = f"find_all_dependencies_{entity.name.lower()}"

        if config.dependency_entity:
            dep_table = (
                f"tb_{config.dependency_entity.lower()}"
                if config.dependency_entity
                else entity.table_name
            )
        else:
            dep_table = f"tb_{entity.name.lower()}"

        return f"""
-- Find all dependencies recursively
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    p_feature_ids UUID[]
)
RETURNS TABLE(
    feature_id UUID,
    requires_feature_id UUID,
    depth INTEGER,
    path UUID[]
)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE dependency_tree AS (
        -- BASE CASE: Direct dependencies of selected features
        SELECT
            fd.feature_id,
            fd.requires_feature_id,
            1 as depth,
            ARRAY[fd.feature_id, fd.requires_feature_id] as path
        FROM {entity.schema}.{dep_table} fd
        WHERE fd.feature_id = ANY(p_feature_ids)
          AND fd.dependency_type = 'REQUIRES'

        UNION ALL

        -- RECURSIVE CASE: Dependencies of dependencies
        SELECT
            fd.feature_id,
            fd.requires_feature_id,
            dt.depth + 1,
            dt.path || fd.requires_feature_id
        FROM {entity.schema}.{dep_table} fd
        JOIN dependency_tree dt ON dt.requires_feature_id = fd.feature_id
        WHERE dt.depth < {config.max_depth}
          AND NOT (fd.requires_feature_id = ANY(dt.path))  -- Prevent cycles
    )
    SELECT * FROM dependency_tree;
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name}(UUID[])
IS 'Find all dependencies recursively up to depth {config.max_depth}';
"""

    @classmethod
    def _generate_validate_dependencies_function(
        cls, entity: EntityDefinition, config: DependencyConfig
    ) -> str:
        """Generate function to validate all dependencies are satisfied."""
        func_name = f"validate_dependencies_{entity.name.lower()}"
        dep_table = (
            f"tb_{config.dependency_entity.lower()}"
            if config.dependency_entity
            else entity.table_name
        )

        return f"""
-- Validate that all dependencies are satisfied
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    p_selected_features UUID[]
)
RETURNS TABLE(
    is_valid BOOLEAN,
    missing_dependencies UUID[],
    error_message TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_all_required UUID[];
    v_missing UUID[];
BEGIN
    -- Find all required features (recursive)
    SELECT ARRAY_AGG(DISTINCT requires_feature_id)
    INTO v_all_required
    FROM {entity.schema}.find_all_dependencies_{entity.name.lower()}(p_selected_features);

    -- Find missing dependencies (required but not selected)
    SELECT ARRAY_AGG(required_id)
    INTO v_missing
    FROM unnest(COALESCE(v_all_required, ARRAY[]::UUID[])) AS required_id
    WHERE NOT (required_id = ANY(p_selected_features));

    -- Return validation result
    IF v_missing IS NULL OR array_length(v_missing, 1) IS NULL THEN
        RETURN QUERY SELECT TRUE, NULL::UUID[], NULL::TEXT;
    ELSE
        RETURN QUERY SELECT
            FALSE,
            v_missing,
            format('Missing %s required dependencies', array_length(v_missing, 1))::TEXT;
    END IF;
END;
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name}(UUID[])
IS 'Validate all dependencies are satisfied for selected features';
"""

    @classmethod
    def _generate_check_conflicts_function(
        cls, entity: EntityDefinition, config: DependencyConfig
    ) -> str:
        """Generate function to check for conflicting features."""
        func_name = f"check_conflicts_{entity.name.lower()}"
        dep_table = (
            f"tb_{config.dependency_entity.lower()}"
            if config.dependency_entity
            else entity.table_name
        )

        return f"""
-- Check for conflicting features
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    p_selected_features UUID[]
)
RETURNS TABLE(
    has_conflicts BOOLEAN,
    conflicting_pairs JSONB,
    error_message TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_conflicts JSONB;
BEGIN
    -- Find conflicts (features that CONFLICT_WITH each other)
    SELECT jsonb_agg(
        jsonb_build_object(
            'feature_id', fd.feature_id,
            'conflicts_with', fd.requires_feature_id
        )
    )
    INTO v_conflicts
    FROM {entity.schema}.{dep_table} fd
    WHERE fd.dependency_type = 'CONFLICTS_WITH'
      AND fd.feature_id = ANY(p_selected_features)
      AND fd.requires_feature_id = ANY(p_selected_features);

    -- Return result
    IF v_conflicts IS NULL THEN
        RETURN QUERY SELECT FALSE, NULL::JSONB, NULL::TEXT;
    ELSE
        RETURN QUERY SELECT
            TRUE,
            v_conflicts,
            format('Found %s conflicting feature pairs', jsonb_array_length(v_conflicts))::TEXT;
    END IF;
END;
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name}(UUID[])
IS 'Check for conflicting features in selection';
"""

    @classmethod
    def _generate_circular_check_function(
        cls, entity: EntityDefinition, config: DependencyConfig
    ) -> str:
        """Generate function to detect circular dependencies."""
        func_name = f"check_circular_dependencies_{entity.name.lower()}"
        dep_table = (
            f"tb_{config.dependency_entity.lower()}"
            if config.dependency_entity
            else entity.table_name
        )

        return f"""
-- Detect circular dependencies in dependency graph
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}()
RETURNS TABLE(
    has_circular BOOLEAN,
    circular_path UUID[],
    error_message TEXT
)
LANGUAGE sql
STABLE
AS $$
    WITH RECURSIVE dep_graph AS (
        SELECT
            feature_id,
            requires_feature_id,
            ARRAY[feature_id, requires_feature_id] as path,
            FALSE as is_circular
        FROM {entity.schema}.{dep_table}
        WHERE dependency_type = 'REQUIRES'

        UNION ALL

        SELECT
            dg.feature_id,
            fd.requires_feature_id,
            dg.path || fd.requires_feature_id,
            (fd.requires_feature_id = ANY(dg.path)) as is_circular
        FROM dep_graph dg
        JOIN {entity.schema}.{dep_table} fd ON fd.feature_id = dg.requires_feature_id
        WHERE array_length(dg.path, 1) < {config.max_depth}
          AND NOT dg.is_circular
    )
    SELECT
        EXISTS(SELECT 1 FROM dep_graph WHERE is_circular) as has_circular,
        (SELECT path FROM dep_graph WHERE is_circular LIMIT 1) as circular_path,
        (SELECT 'Circular dependency detected: ' || array_to_string(path, ' -> ')
         FROM dep_graph WHERE is_circular LIMIT 1) as error_message;
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name}()
IS 'Detect circular dependencies in feature dependency graph';
"""
