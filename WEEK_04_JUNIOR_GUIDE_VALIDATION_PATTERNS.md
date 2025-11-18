# Week 4 Junior Guide: Validation Patterns (Recursive Dependencies + Template Inheritance)

**Target Audience**: Junior engineers
**Goal**: Fix 29 skipped validation pattern tests
**Prerequisites**: Temporal patterns completed
**Time Estimate**: 5-6 days
**Difficulty**: ⭐⭐⭐ Advanced (recursive SQL, complex logic)

---

## 📊 Current Status

```bash
uv run pytest tests/unit/patterns/validation/ -v | grep SKIPPED | wc -l
# Result: 29 skipped tests

# Breakdown:
# - Recursive Dependency Validator: ~17 tests
# - Template Inheritance: ~12 tests
```

---

## Part 1: Recursive Dependency Validator

### 🎯 Real-World Problem: Product Configuration

Imagine configuring a car with features:

**Dependencies**:
- Bluetooth requires WiFi
- WiFi requires Power Management
- Backup Camera requires either Rear Sensors OR Parking Assist

**Complex scenario**:
```
User selects: [Bluetooth, Backup Camera]

System validates:
  ❌ Missing WiFi (required by Bluetooth)
  ❌ Missing Power Management (required by WiFi)
  ❌ Missing Rear Sensors OR Parking Assist (required by Backup Camera)
```

**Solution**: Recursive SQL query to find all dependencies!

---

### 📝 Key Concepts

#### 1. Recursive CTE (Common Table Expression)

PostgreSQL can query tree/graph structures recursively:

```sql
WITH RECURSIVE dependency_tree AS (
    -- BASE CASE: Direct dependencies of Bluetooth
    SELECT feature_id, requires_feature_id, 1 as depth
    FROM feature_dependencies
    WHERE feature_id = 'bluetooth'

    UNION ALL

    -- RECURSIVE CASE: Dependencies of dependencies
    SELECT fd.feature_id, fd.requires_feature_id, dt.depth + 1
    FROM feature_dependencies fd
    JOIN dependency_tree dt ON dt.requires_feature_id = fd.feature_id
    WHERE dt.depth < 10  -- Prevent infinite loops
)
SELECT * FROM dependency_tree;
```

**Result**:
```
feature_id  | requires_feature_id | depth
------------|---------------------|------
bluetooth   | wifi                | 1
wifi        | power_mgmt          | 2
```

**Visualization**:
```
bluetooth
  └── wifi (depth 1)
      └── power_mgmt (depth 2)
```

#### 2. Dependency Types

**REQUIRES**: A needs B
```yaml
rules:
  - bluetooth REQUIRES wifi
```

**REQUIRES_ONE_OF**: A needs at least one of [B, C, D]
```yaml
rules:
  - backup_camera REQUIRES_ONE_OF [rear_sensors, parking_assist, 360_camera]
```

**CONFLICTS_WITH**: A and B cannot coexist
```yaml
rules:
  - low_power_mode CONFLICTS_WITH high_performance_mode
```

---

### 🛠️ Implementation (Days 1-3)

#### Day 1: Create Validation Function Generator

**Create file**: `src/patterns/validation/recursive_dependency_validator.py`

```python
"""Recursive dependency validator pattern implementation."""

from dataclasses import dataclass
from typing import Optional
from src.core.ast_models import EntityDefinition


@dataclass
class DependencyConfig:
    """Configuration for recursive dependency validation."""
    dependency_entity: str  # Entity storing dependencies (e.g., "FeatureDependency")
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

        # Add to entity's custom DDL
        if not hasattr(entity, '_validation_functions'):
            entity._validation_functions = []

        entity._validation_functions.extend(functions)

    @classmethod
    def _parse_config(cls, params: dict) -> DependencyConfig:
        """Parse pattern parameters."""
        dependency_entity = params.get("dependency_entity")
        if not dependency_entity:
            raise ValueError("Recursive dependency validator requires 'dependency_entity'")

        return DependencyConfig(
            dependency_entity=dependency_entity,
            max_depth=params.get("max_depth", 10),
            check_circular=params.get("check_circular", True)
        )

    @classmethod
    def _generate_validation_functions(cls, entity: EntityDefinition,
                                       config: DependencyConfig) -> list[str]:
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
    def _generate_find_dependencies_function(cls, entity: EntityDefinition,
                                            config: DependencyConfig) -> str:
        """
        Generate function to find all dependencies recursively.

        Returns array of required feature IDs.
        """
        func_name = f"find_all_dependencies_{entity.name.lower()}"
        dep_table = f"tb_{config.dependency_entity.lower()}"

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
    def _generate_validate_dependencies_function(cls, entity: EntityDefinition,
                                                 config: DependencyConfig) -> str:
        """Generate function to validate all dependencies are satisfied."""
        func_name = f"validate_dependencies_{entity.name.lower()}"
        dep_table = f"tb_{config.dependency_entity.lower()}"

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
    def _generate_check_conflicts_function(cls, entity: EntityDefinition,
                                          config: DependencyConfig) -> str:
        """Generate function to check for conflicting features."""
        func_name = f"check_conflicts_{entity.name.lower()}"
        dep_table = f"tb_{config.dependency_entity.lower()}"

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
    def _generate_circular_check_function(cls, entity: EntityDefinition,
                                         config: DependencyConfig) -> str:
        """Generate function to detect circular dependencies."""
        func_name = f"check_circular_dependencies_{entity.name.lower()}"
        dep_table = f"tb_{config.dependency_entity.lower()}"

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
```

#### Day 2: Testing Recursive Dependencies

**Create integration test**:
```python
def test_recursive_dependency_validation(test_db):
    """Test recursive dependency validation end-to-end."""

    # Setup: Create feature dependency table
    test_db.execute("""
        CREATE TABLE catalog.tb_feature_dependency (
            pk_id SERIAL PRIMARY KEY,
            feature_id UUID NOT NULL,
            requires_feature_id UUID NOT NULL,
            dependency_type TEXT NOT NULL CHECK (dependency_type IN ('REQUIRES', 'CONFLICTS_WITH'))
        );
    """)

    # Setup: Insert dependency rules
    # bluetooth -> wifi -> power_mgmt
    test_db.execute("""
        INSERT INTO catalog.tb_feature_dependency (feature_id, requires_feature_id, dependency_type)
        VALUES
            (gen_random_uuid(), gen_random_uuid(), 'REQUIRES'),  -- bluetooth requires wifi
            (gen_random_uuid(), gen_random_uuid(), 'REQUIRES');  -- wifi requires power_mgmt
    """)

    # Generate validation functions (from pattern)
    entity_yaml = """
    entity: ProductConfiguration
    schema: catalog
    fields:
      selected_features: list(ref(Feature))

    patterns:
      - type: validation_recursive_dependency_validator
        params:
          dependency_entity: FeatureDependency
          max_depth: 10
    """

    # Generate and apply DDL
    ddl = generate_ddl(parse_yaml(entity_yaml))
    test_db.execute(ddl)

    # Test: Validate with missing dependencies
    result = test_db.execute("""
        SELECT * FROM catalog.validate_dependencies_productconfiguration(
            ARRAY['bluetooth_id']::UUID[]
        );
    """).fetchone()

    assert result.is_valid == False
    assert 'wifi' in str(result.missing_dependencies)
```

---

## Part 2: Template Inheritance Pattern

### 🎯 Real-World Problem: Configuration Templates

Imagine product templates with inheritance:

```
Generic Product Template
    ├── attributes: [weight, dimensions]
    └── config: {packaging: "standard"}

    ↓ inherits

Electronics Template (extends Generic)
    ├── attributes: [weight, dimensions, voltage, wattage]  # Merged!
    └── config: {packaging: "antistatic"}  # Overridden!

    ↓ inherits

Laptop Template (extends Electronics)
    ├── attributes: [weight, dimensions, voltage, wattage, screen_size, battery_life]
    └── config: {packaging: "foam-padded"}
```

**Challenge**: Resolve full configuration by traversing hierarchy!

---

### 📝 Key Concepts

#### 1. Recursive Hierarchy Traversal

```sql
WITH RECURSIVE template_chain AS (
    -- BASE: Product's direct template
    SELECT 1 as level, template_id, config_data
    FROM products
    WHERE id = 'laptop-001'

    UNION ALL

    -- RECURSIVE: Parent templates
    SELECT tc.level + 1, t.parent_template_id, t.config_data
    FROM template_chain tc
    JOIN templates t ON t.id = tc.template_id
    WHERE tc.level < 5  -- Max 5 levels
)
SELECT * FROM template_chain ORDER BY level DESC;
```

#### 2. JSONB Merging

PostgreSQL can merge JSON objects:
```sql
SELECT
    jsonb_build_object('a', 1, 'b', 2) ||
    jsonb_build_object('b', 3, 'c', 4);
-- Result: {"a": 1, "b": 3, "c": 4}  (later values override)
```

---

### 🛠️ Implementation (Days 4-5)

**Create file**: `src/patterns/validation/template_inheritance.py`

```python
"""Template inheritance pattern implementation."""

from dataclasses import dataclass
from typing import Optional
from src.core.ast_models import EntityDefinition


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
        config = cls._parse_config(params)

        # Generate resolution function
        functions = cls._generate_resolution_functions(entity, config)

        if not hasattr(entity, '_template_functions'):
            entity._template_functions = []

        entity._template_functions.extend(functions)

    @classmethod
    def _parse_config(cls, params: dict) -> TemplateConfig:
        """Parse pattern configuration."""
        template_entity = params.get("template_entity")
        if not template_entity:
            raise ValueError("Template inheritance requires 'template_entity'")

        return TemplateConfig(
            template_entity=template_entity,
            template_field=params.get("template_field", "template_id"),
            max_depth=params.get("max_depth", 5),
            merge_strategy=params.get("merge_strategy", "override")
        )

    @classmethod
    def _generate_resolution_functions(cls, entity: EntityDefinition,
                                       config: TemplateConfig) -> list[str]:
        """Generate template resolution functions."""
        return [
            cls._generate_resolve_template_function(entity, config),
            cls._generate_get_template_chain_function(entity, config)
        ]

    @classmethod
    def _generate_resolve_template_function(cls, entity: EntityDefinition,
                                           config: TemplateConfig) -> str:
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
    def _generate_get_template_chain_function(cls, entity: EntityDefinition,
                                             config: TemplateConfig) -> str:
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
```

---

## ✅ Verification

```bash
# Test recursive dependencies
uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py -v
# Expected: ✅ 17 PASSED

# Test template inheritance
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py -v
# Expected: ✅ 12 PASSED

# All validation patterns
uv run pytest tests/unit/patterns/validation/ -v
# Expected: ✅ 29 PASSED, 0 SKIPPED
```

---

## 🎓 Key SQL Concepts

### Recursive CTEs
```sql
WITH RECURSIVE name AS (
    SELECT ... -- BASE CASE
    UNION ALL
    SELECT ... FROM name -- RECURSIVE CASE
)
SELECT * FROM name;
```

### Cycle Detection
```sql
WHERE NOT (new_id = ANY(path_array))  -- Prevent revisiting nodes
```

### JSONB Operations
```sql
-- Merge (later overrides)
jsonb1 || jsonb2

-- Deep merge
jsonb_object_agg(key, value)
```

---

**Great work! You've completed the most complex patterns! 🎉**
