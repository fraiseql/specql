# Week 2 Implementation Guide: Pattern Implementation + CLI Excellence

**Phase**: Pattern Implementation & CLI Polish
**Duration**: 7 days (Days 8-14)
**Objective**: Implement 3 missing patterns + Production-grade CLI
**Prerequisites**: Week 1 complete (0 test errors, 112 pattern tests written)

---

## 📋 Week 2 Overview

### **Entry Criteria** (Must be met before starting)
```bash
# Verify Week 1 deliverables
uv run pytest --collect-only 2>&1 | grep -c "ERROR"
# Expected: 0 ✅

uv run pytest tests/unit/patterns --collect-only | grep "collected"
# Expected: 112 tests collected ✅

uv run pytest tests/unit/core tests/unit/generators tests/unit/schema
# Expected: 384+ passed ✅
```

### **Exit Criteria** (Must achieve by end of week)
```bash
# All patterns implemented and tested
uv run pytest tests/unit/patterns -v
# Expected: 112 passed ✅

# All CLI tests passing
uv run pytest tests/unit/cli -v
# Expected: 100% pass rate ✅

# Coverage target maintained
uv run pytest --cov=src --cov-report=term
# Expected: 95%+ coverage ✅
```

---

## 🎯 Week 2 Timeline

### **Days 1-2**: Implement Missing Patterns (SCD Type 2, Template Inheritance, Computed Column)
### **Days 3-4**: CLI Test Fixes & Orchestration Improvements
### **Day 5**: CLI UX Polish & Error Messages
### **Days 6-7**: Integration Testing & Buffer

---

## Day 1 (Monday): SCD Type 2 Helper Pattern

**Objective**: Implement complete SCD Type 2 pattern with automatic versioning

### **Morning Session (4 hours): Pattern Specification & Schema Extension**

#### **Task 1.1: Create Pattern Specification** (1 hour)

Create `stdlib/schema/temporal/scd_type2_helper.yaml`:

```yaml
pattern: temporal_scd_type2_helper
version: 1.0
category: temporal
description: |
  Slowly Changing Dimension Type 2 with automatic version management.
  Maintains full history with version numbers, effective dates, and current version flag.

author: SpecQL Team
created: 2025-11-25
tags: [temporal, versioning, scd, history]

parameters:
  - name: natural_key
    type: array<string>
    required: true
    description: "Fields that uniquely identify the business entity (e.g., [product_code, company])"
    example: ["product_code"]

  - name: version_field
    type: string
    default: version_number
    description: "Field name for version counter"
    validation: "^[a-z][a-z0-9_]*$"

  - name: is_current_field
    type: string
    default: is_current
    description: "Boolean field indicating current version"
    validation: "^[a-z][a-z0-9_]*$"

  - name: effective_date_field
    type: string
    default: effective_date
    description: "When this version became effective"
    validation: "^[a-z][a-z0-9_]*$"

  - name: expiry_date_field
    type: string
    default: expiry_date
    description: "When this version was superseded (NULL for current)"
    validation: "^[a-z][a-z0-9_]*$"

  - name: auto_version
    type: boolean
    default: true
    description: "Automatically manage versions on updates"

schema_extensions:
  fields:
    - name: "{{ version_field }}"
      type: integer
      default: 1
      nullable: false
      comment: "Version number (increments on each change)"

    - name: "{{ is_current_field }}"
      type: boolean
      default: true
      nullable: false
      comment: "True for the current version, false for historical"
      index: true

    - name: "{{ effective_date_field }}"
      type: timestamptz
      default: now()
      nullable: false
      comment: "When this version became effective"

    - name: "{{ expiry_date_field }}"
      type: timestamptz
      nullable: true
      default: null
      comment: "When this version was superseded (NULL for current version)"

  constraints:
    # Only one current version per natural key
    - type: unique
      name: "uniq_{{ entity.name | lower }}_current_version"
      fields: "{{ natural_key + [is_current_field] }}"
      where: "{{ is_current_field }} = true"
      comment: "Ensure only one current version per business entity"

  indexes:
    # Fast current version lookups
    - name: "idx_{{ entity.name | lower }}_current_nk"
      fields: "{{ natural_key + [is_current_field] }}"
      where: "{{ is_current_field }} = true"
      comment: "Optimized index for current version queries"

    # Fast temporal queries
    - name: "idx_{{ entity.name | lower }}_temporal"
      fields: "{{ natural_key + [effective_date_field, expiry_date_field] }}"
      comment: "Index for point-in-time and range queries"

    # Version history ordering
    - name: "idx_{{ entity.name | lower }}_version_order"
      fields: "{{ natural_key + [version_field] }}"
      comment: "Index for version history queries"

action_helpers:
  - function: "create_new_version_{{ entity.name | lower }}"
    description: "Create new version and expire previous"
    returns: uuid
    params:
      - name: natural_key_values
        type: jsonb
        description: "JSON object with natural key field values"
      - name: new_data
        type: jsonb
        description: "JSON object with new field values"
      - name: effective_at
        type: timestamptz
        default: now()
        description: "When new version becomes effective"

    logic: |
      DECLARE
        v_old_id uuid;
        v_new_id uuid;
        v_next_version integer;
      BEGIN
        -- Get current version ID and next version number
        SELECT id, {{ version_field }} + 1
        INTO v_old_id, v_next_version
        FROM {{ schema }}.tb_{{ entity.name | lower }}
        WHERE {{ natural_key_where_clause }}
          AND {{ is_current_field }} = true;

        IF v_old_id IS NULL THEN
          RAISE EXCEPTION 'No current version found for given natural key';
        END IF;

        -- Expire current version
        UPDATE {{ schema }}.tb_{{ entity.name | lower }}
        SET
          {{ is_current_field }} = false,
          {{ expiry_date_field }} = effective_at,
          updated_at = now(),
          updated_by = current_setting('app.current_user_id', true)::uuid
        WHERE id = v_old_id;

        -- Insert new version
        INSERT INTO {{ schema }}.tb_{{ entity.name | lower }} (
          {{ field_list }},
          {{ version_field }},
          {{ is_current_field }},
          {{ effective_date_field }},
          {{ expiry_date_field }}
        )
        SELECT
          {{ field_list_from_jsonb }},
          v_next_version,
          true,
          effective_at,
          NULL
        FROM jsonb_populate_record(NULL::{{ schema }}.tb_{{ entity.name | lower }}, new_data)
        RETURNING id INTO v_new_id;

        RETURN v_new_id;
      END;

  - function: "get_current_version_{{ entity.name | lower }}"
    description: "Get current version ID by natural key"
    returns: uuid
    params:
      - name: natural_key_values
        type: jsonb

    logic: |
      SELECT id
      FROM {{ schema }}.tb_{{ entity.name | lower }}
      WHERE {{ natural_key_where_clause }}
        AND {{ is_current_field }} = true;

  - function: "get_version_at_time_{{ entity.name | lower }}"
    description: "Get version valid at specific point in time"
    returns: uuid
    params:
      - name: natural_key_values
        type: jsonb
      - name: as_of_time
        type: timestamptz

    logic: |
      SELECT id
      FROM {{ schema }}.tb_{{ entity.name | lower }}
      WHERE {{ natural_key_where_clause }}
        AND {{ effective_date_field }} <= as_of_time
        AND ({{ expiry_date_field }} IS NULL OR {{ expiry_date_field }} > as_of_time)
      LIMIT 1;

  - function: "get_version_history_{{ entity.name | lower }}"
    description: "Get all versions ordered by effective date"
    returns: "SETOF {{ schema }}.tb_{{ entity.name | lower }}"
    params:
      - name: natural_key_values
        type: jsonb

    logic: |
      SELECT *
      FROM {{ schema }}.tb_{{ entity.name | lower }}
      WHERE {{ natural_key_where_clause }}
      ORDER BY {{ effective_date_field }} DESC;

validation:
  - rule: natural_key_not_empty
    check: "LENGTH(natural_key) > 0"
    message: "natural_key must contain at least one field"

  - rule: version_field_unique
    check: "version_field NOT IN entity.fields"
    message: "version_field must not conflict with existing entity fields"

  - rule: effective_before_expiry
    check: "effective_date_field < expiry_date_field (if both set)"
    message: "effective_date must be before expiry_date"

examples:
  - name: Product with SCD Type 2
    yaml: |
      entity: Product
      schema: catalog
      fields:
        product_code: text
        name: text
        price: decimal
        category: ref(Category)
      patterns:
        - type: temporal_scd_type2_helper
          params:
            natural_key: [product_code]

    generated_fields:
      - version_number: integer (default 1)
      - is_current: boolean (default true)
      - effective_date: timestamptz (default now())
      - expiry_date: timestamptz (nullable)

    usage: |
      -- Create new version when price changes
      SELECT create_new_version_product(
        '{"product_code": "WIDGET-001"}'::jsonb,
        '{"price": 29.99}'::jsonb
      );

      -- Get current version
      SELECT * FROM catalog.tb_product
      WHERE product_code = 'WIDGET-001' AND is_current = true;

      -- Get version history
      SELECT * FROM get_version_history_product(
        '{"product_code": "WIDGET-001"}'::jsonb
      );

      -- Point-in-time query
      SELECT * FROM catalog.tb_product
      WHERE product_code = 'WIDGET-001'
        AND effective_date <= '2024-01-01'::timestamptz
        AND (expiry_date IS NULL OR expiry_date > '2024-01-01'::timestamptz);

performance:
  - operation: get_current_version
    complexity: O(1)
    notes: "Partial index on is_current=true makes this extremely fast"

  - operation: get_version_at_time
    complexity: O(log n)
    notes: "Index on (natural_key, effective_date, expiry_date)"

  - operation: get_version_history
    complexity: O(k log n)
    notes: "Where k = number of versions for entity"

limitations:
  - "Natural key cannot change (would create new entity, not new version)"
  - "Large version histories (>1000) may need partitioning"
  - "Concurrent version creation requires transaction isolation"

best_practices:
  - "Use meaningful natural keys (business identifiers, not UUIDs)"
  - "Set effective_date explicitly for backdated changes"
  - "Archive old versions periodically if history is very large"
  - "Use table partitioning for tables with millions of versions"
```

**Commit Point**: `git commit -m "feat: add SCD Type 2 helper pattern specification"`

---

#### **Task 1.2: Implement Pattern in Schema Generator** (2 hours)

Update `src/generators/schema/pattern_applier.py`:

```python
"""Apply patterns to entity schema."""

from typing import Dict, List, Any
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader

from src.core.models import Entity, Field, Index, Constraint


class PatternApplier:
    """Apply pattern transformations to entities."""

    def __init__(self, pattern_dir: Path = Path("stdlib/schema")):
        self.pattern_dir = pattern_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(pattern_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def apply_pattern(
        self,
        entity: Entity,
        pattern_type: str,
        params: Dict[str, Any],
    ) -> Entity:
        """Apply pattern to entity, returning modified entity."""

        # Load pattern specification
        pattern_spec = self._load_pattern_spec(pattern_type)

        # Validate parameters
        self._validate_params(pattern_spec, params)

        # Apply schema extensions
        entity = self._apply_schema_extensions(entity, pattern_spec, params)

        # Generate helper functions (handled by action compiler)
        # Metadata for FraiseQL
        entity.metadata['patterns'] = entity.metadata.get('patterns', [])
        entity.metadata['patterns'].append({
            'type': pattern_type,
            'params': params,
        })

        return entity

    def _load_pattern_spec(self, pattern_type: str) -> Dict[str, Any]:
        """Load pattern YAML specification."""
        pattern_path = self.pattern_dir / f"{pattern_type}.yaml"

        if not pattern_path.exists():
            # Try subdirectories (temporal/, validation/, schema/)
            for subdir in ['temporal', 'validation', 'schema']:
                pattern_path = self.pattern_dir / subdir / f"{pattern_type}.yaml"
                if pattern_path.exists():
                    break

        if not pattern_path.exists():
            raise ValueError(f"Pattern '{pattern_type}' not found in {self.pattern_dir}")

        with open(pattern_path) as f:
            return yaml.safe_load(f)

    def _validate_params(
        self,
        pattern_spec: Dict[str, Any],
        params: Dict[str, Any],
    ) -> None:
        """Validate pattern parameters against specification."""
        spec_params = {p['name']: p for p in pattern_spec.get('parameters', [])}

        # Check required parameters
        for param_name, param_spec in spec_params.items():
            if param_spec.get('required', False) and param_name not in params:
                raise ValueError(
                    f"Required parameter '{param_name}' missing for pattern "
                    f"'{pattern_spec['pattern']}'"
                )

        # Check unknown parameters
        for param_name in params:
            if param_name not in spec_params:
                raise ValueError(
                    f"Unknown parameter '{param_name}' for pattern "
                    f"'{pattern_spec['pattern']}'"
                )

        # Type validation
        for param_name, param_value in params.items():
            param_spec = spec_params[param_name]
            self._validate_param_type(param_name, param_value, param_spec)

    def _validate_param_type(
        self,
        param_name: str,
        param_value: Any,
        param_spec: Dict[str, Any],
    ) -> None:
        """Validate parameter type."""
        param_type = param_spec.get('type', 'string')

        if param_type == 'string' and not isinstance(param_value, str):
            raise TypeError(f"Parameter '{param_name}' must be string")

        elif param_type == 'boolean' and not isinstance(param_value, bool):
            raise TypeError(f"Parameter '{param_name}' must be boolean")

        elif param_type == 'integer' and not isinstance(param_value, int):
            raise TypeError(f"Parameter '{param_name}' must be integer")

        elif param_type.startswith('array<'):
            if not isinstance(param_value, list):
                raise TypeError(f"Parameter '{param_name}' must be array")

        # Validation regex if specified
        if 'validation' in param_spec and isinstance(param_value, str):
            import re
            if not re.match(param_spec['validation'], param_value):
                raise ValueError(
                    f"Parameter '{param_name}' value '{param_value}' "
                    f"does not match pattern '{param_spec['validation']}'"
                )

    def _apply_schema_extensions(
        self,
        entity: Entity,
        pattern_spec: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Entity:
        """Apply schema extensions from pattern."""
        extensions = pattern_spec.get('schema_extensions', {})

        # Render templates with Jinja2
        template_context = {
            'entity': entity,
            'params': params,
            **params,  # Params available directly
        }

        # Add fields
        if 'fields' in extensions:
            for field_template in extensions['fields']:
                field = self._render_field(field_template, template_context, entity)
                entity.fields.append(field)

        # Add constraints
        if 'constraints' in extensions:
            for constraint_template in extensions['constraints']:
                constraint = self._render_constraint(
                    constraint_template,
                    template_context,
                    entity,
                )
                entity.constraints.append(constraint)

        # Add indexes
        if 'indexes' in extensions:
            for index_template in extensions['indexes']:
                index = self._render_index(index_template, template_context, entity)
                entity.indexes.append(index)

        return entity

    def _render_field(
        self,
        field_template: Dict[str, Any],
        context: Dict[str, Any],
        entity: Entity,
    ) -> Field:
        """Render field template with Jinja2."""
        from jinja2 import Template

        # Render field name
        name_template = Template(field_template['name'])
        name = name_template.render(context)

        # Create field
        field = Field(
            name=name,
            type=field_template['type'],
            nullable=field_template.get('nullable', False),
            default=field_template.get('default'),
            unique=field_template.get('unique', False),
            index=field_template.get('index', False),
            comment=field_template.get('comment', ''),
        )

        return field

    def _render_constraint(
        self,
        constraint_template: Dict[str, Any],
        context: Dict[str, Any],
        entity: Entity,
    ) -> Constraint:
        """Render constraint template."""
        from jinja2 import Template

        # Render constraint fields
        fields_template = Template(str(constraint_template['fields']))
        fields_str = fields_template.render(context)

        # Parse fields (could be Python expression from template)
        import ast
        try:
            fields = ast.literal_eval(fields_str)
            if not isinstance(fields, list):
                fields = [fields]
        except (ValueError, SyntaxError):
            # Not a Python literal, treat as single field name
            fields = [fields_str]

        # Render name
        name = constraint_template.get('name', '')
        if name:
            name_template = Template(name)
            name = name_template.render(context)

        # Render where clause if present
        where = constraint_template.get('where')
        if where:
            where_template = Template(where)
            where = where_template.render(context)

        constraint = Constraint(
            type=constraint_template['type'],
            name=name,
            fields=fields,
            where=where,
            comment=constraint_template.get('comment', ''),
        )

        return constraint

    def _render_index(
        self,
        index_template: Dict[str, Any],
        context: Dict[str, Any],
        entity: Entity,
    ) -> Index:
        """Render index template."""
        from jinja2 import Template

        # Render fields
        fields_template = Template(str(index_template['fields']))
        fields_str = fields_template.render(context)

        # Parse fields
        import ast
        try:
            fields = ast.literal_eval(fields_str)
            if not isinstance(fields, list):
                fields = [fields]
        except (ValueError, SyntaxError):
            fields = [fields_str]

        # Render name if present
        name = index_template.get('name', '')
        if name:
            name_template = Template(name)
            name = name_template.render(context)

        # Render where clause if present
        where = index_template.get('where')
        if where:
            where_template = Template(where)
            where = where_template.render(context)

        index = Index(
            name=name,
            fields=fields,
            unique=index_template.get('unique', False),
            where=where,
            using=index_template.get('using', 'btree'),
            comment=index_template.get('comment', ''),
        )

        return index
```

**Commit Point**: `git commit -m "feat: implement pattern applier for SCD Type 2"`

---

#### **Task 1.3: Update Core Parser to Support Patterns** (1 hour)

Update `src/core/parser.py` to parse pattern declarations:

```python
"""SpecQL YAML parser with pattern support."""

class SpecQLParser:
    """Parse SpecQL YAML to Entity AST."""

    def parse(self, yaml_content: str) -> Entity:
        """Parse YAML string to Entity object."""
        data = yaml.safe_load(yaml_content)

        # ... existing field parsing ...

        # Parse patterns
        patterns = []
        if 'patterns' in data:
            for pattern_def in data['patterns']:
                pattern = self._parse_pattern(pattern_def)
                patterns.append(pattern)

        entity.patterns = patterns

        return entity

    def _parse_pattern(self, pattern_def: Dict[str, Any]) -> Pattern:
        """Parse pattern definition."""
        if isinstance(pattern_def, str):
            # Short form: just pattern type
            return Pattern(type=pattern_def, params={})

        elif isinstance(pattern_def, dict):
            # Full form: type + params
            return Pattern(
                type=pattern_def['type'],
                params=pattern_def.get('params', {}),
            )

        else:
            raise ValueError(f"Invalid pattern definition: {pattern_def}")
```

Update `src/core/models.py`:

```python
"""Core AST models."""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Pattern:
    """Pattern application."""
    type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """Entity definition."""
    name: str
    schema: str
    fields: List[Field] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    patterns: List[Pattern] = field(default_factory=list)
    # ... rest of fields ...
```

**Commit Point**: `git commit -m "feat: add pattern parsing to SpecQL parser"`

---

### **Afternoon Session (4 hours): Run Tests & Implement Helper Functions**

#### **Task 1.4: Run SCD Type 2 Tests** (1 hour)

```bash
# Run pattern tests for SCD Type 2
uv run pytest tests/unit/patterns/temporal/test_scd_type2_helper.py -v

# Expected: Some tests pass (schema generation), some fail (helper functions not yet implemented)
```

**Analyze failures**: Note which tests fail due to missing helper function generation.

---

#### **Task 1.5: Implement Action Helper Generation** (3 hours)

Create `src/generators/actions/pattern_helpers_generator.py`:

```python
"""Generate action helper functions from patterns."""

from typing import List, Dict, Any
from jinja2 import Template

from src.core.models import Entity, Pattern


class PatternHelpersGenerator:
    """Generate helper functions for patterns."""

    def generate(
        self,
        entity: Entity,
        pattern: Pattern,
        pattern_spec: Dict[str, Any],
    ) -> List[str]:
        """Generate helper function SQL for pattern."""

        helpers = []

        for helper_spec in pattern_spec.get('action_helpers', []):
            sql = self._generate_helper_function(
                entity,
                pattern,
                helper_spec,
                pattern_spec,
            )
            helpers.append(sql)

        return helpers

    def _generate_helper_function(
        self,
        entity: Entity,
        pattern: Pattern,
        helper_spec: Dict[str, Any],
        pattern_spec: Dict[str, Any],
    ) -> str:
        """Generate single helper function."""

        # Render function name
        func_name_template = Template(helper_spec['function'])
        func_name = func_name_template.render(
            entity=entity,
            params=pattern.params,
            **pattern.params,
        )

        # Render function logic
        logic_template = Template(helper_spec['logic'])

        # Build template context
        context = {
            'entity': entity,
            'schema': entity.schema,
            'params': pattern.params,
            **pattern.params,
            'natural_key_where_clause': self._build_natural_key_where_clause(
                pattern.params.get('natural_key', [])
            ),
            'field_list': ', '.join(f.name for f in entity.fields),
            # Add more helper functions as needed
        }

        logic = logic_template.render(context)

        # Build parameter list
        param_list = []
        for param in helper_spec.get('params', []):
            param_def = f"{param['name']} {param['type']}"
            if 'default' in param:
                param_def += f" DEFAULT {param['default']}"
            param_list.append(param_def)

        # Generate complete function
        sql = f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(
    {', '.join(param_list)}
)
RETURNS {helper_spec['returns']}
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
{logic}
$$;

COMMENT ON FUNCTION {entity.schema}.{func_name} IS '{helper_spec.get('description', '')}';
"""

        return sql

    def _build_natural_key_where_clause(self, natural_key_fields: List[str]) -> str:
        """Build WHERE clause for natural key matching."""
        if not natural_key_fields:
            return "TRUE"

        clauses = []
        for field in natural_key_fields:
            clauses.append(
                f"{field} = (natural_key_values->>'{field}')::{self._get_field_type(field)}"
            )

        return " AND ".join(clauses)

    def _get_field_type(self, field_name: str) -> str:
        """Get PostgreSQL type for field (simplified)."""
        # In real implementation, look up from entity.fields
        return "text"  # Default fallback
```

**Commit Point**: `git commit -m "feat: implement pattern helper function generation"`

---

#### **Task 1.6: Integration Test** (30 min)

Run full test suite for SCD Type 2:

```bash
uv run pytest tests/unit/patterns/temporal/test_scd_type2_helper.py -v

# Expected: All 18 tests passing ✅
```

**Deliverable**: SCD Type 2 pattern fully implemented and tested

**Day 1 Completion Check**:
```bash
uv run pytest tests/unit/patterns/temporal/test_scd_type2_helper.py -v
# Expected: 18 passed ✅

git log --oneline -5
# Expected: 4-5 commits for SCD Type 2 implementation
```

---

## Day 2 (Tuesday): Template Inheritance & Computed Column Patterns

**Objective**: Implement final 2 missing patterns

### **Morning Session (4 hours): Template Inheritance Validator**

#### **Task 2.1: Create Pattern Specification** (1.5 hours)

Create `stdlib/schema/validation/template_inheritance_validator.yaml`:

```yaml
pattern: validation_template_inheritance
version: 1.0
category: validation
description: |
  Resolve configuration from template hierarchy (model → parent → generic).
  Uses recursive CTEs to traverse template chain and merge configurations.

parameters:
  - name: template_field
    type: string
    default: template_id
    description: "Field linking to template entity"

  - name: template_entity
    type: string
    required: true
    description: "Entity name of template (e.g., ProductTemplate)"

  - name: config_field
    type: string
    default: config_data
    description: "JSONB field containing configuration"

  - name: merge_strategy
    type: enum
    values: [override, merge, append]
    default: override
    description: |
      - override: Child completely replaces parent values
      - merge: Deep merge child into parent
      - append: Concatenate arrays, merge objects

  - name: max_depth
    type: integer
    default: 5
    description: "Maximum template hierarchy depth to prevent infinite loops"

schema_extensions:
  fields:
    - name: "{{ template_field }}"
      type: "ref({{ template_entity }})"
      nullable: true
      comment: "Link to parent template for inheritance"
      index: true

action_helpers:
  - function: "resolve_template_{{ entity.name | lower }}"
    description: "Resolve configuration from full template hierarchy"
    returns: jsonb
    params:
      - name: entity_id
        type: uuid
        description: "Entity ID to resolve configuration for"

    logic: |
      DECLARE
        v_resolved_config jsonb;
      BEGIN
        WITH RECURSIVE template_chain AS (
          -- Base case: entity's direct template
          SELECT
            1 as depth,
            e.{{ template_field }} as template_id,
            e.{{ config_field }} as config_data
          FROM {{ schema }}.tb_{{ entity.name | lower }} e
          WHERE e.id = entity_id

          UNION ALL

          -- Recursive case: parent templates
          SELECT
            tc.depth + 1,
            t.{{ template_field }},
            t.{{ config_field }}
          FROM template_chain tc
          JOIN {{ schema }}.tb_{{ template_entity | lower }} t
            ON t.id = tc.template_id
          WHERE tc.depth < {{ max_depth }}
            AND tc.template_id IS NOT NULL
        )
        SELECT
          {% if merge_strategy == 'override' %}
          -- Override: Return most specific (deepest) non-null config
          coalesce(
            (SELECT config_data FROM template_chain ORDER BY depth LIMIT 1),
            '{}'::jsonb
          )
          {% elif merge_strategy == 'merge' %}
          -- Merge: Deep merge from generic to specific
          jsonb_deep_merge(
            config_data ORDER BY depth DESC
          )
          {% elif merge_strategy == 'append' %}
          -- Append: Concatenate arrays, merge objects
          jsonb_append_recursive(
            config_data ORDER BY depth DESC
          )
          {% endif %}
        INTO v_resolved_config
        FROM template_chain;

        RETURN v_resolved_config;
      END;

  - function: "validate_template_depth_{{ entity.name | lower }}"
    description: "Validate template hierarchy doesn't exceed max depth"
    returns: boolean
    params:
      - name: entity_id
        type: uuid

    logic: |
      DECLARE
        v_depth integer;
      BEGIN
        WITH RECURSIVE template_chain AS (
          SELECT
            1 as depth,
            {{ template_field }} as template_id
          FROM {{ schema }}.tb_{{ entity.name | lower }}
          WHERE id = entity_id

          UNION ALL

          SELECT
            tc.depth + 1,
            t.{{ template_field }}
          FROM template_chain tc
          JOIN {{ schema }}.tb_{{ template_entity | lower }} t
            ON t.id = tc.template_id
          WHERE tc.depth < {{ max_depth }} + 1
            AND tc.template_id IS NOT NULL
        )
        SELECT MAX(depth) INTO v_depth
        FROM template_chain;

        IF v_depth > {{ max_depth }} THEN
          RAISE EXCEPTION 'Template hierarchy exceeds maximum depth of {{ max_depth }}';
        END IF;

        RETURN true;
      END;

  - function: "detect_circular_template_{{ entity.name | lower }}"
    description: "Detect circular template dependencies"
    returns: boolean
    params:
      - name: entity_id
        type: uuid

    logic: |
      DECLARE
        v_visited uuid[];
        v_current_id uuid;
      BEGIN
        v_current_id := entity_id;
        v_visited := ARRAY[]::uuid[];

        WHILE v_current_id IS NOT NULL LOOP
          -- Check if we've seen this ID before (circular reference)
          IF v_current_id = ANY(v_visited) THEN
            RAISE EXCEPTION 'Circular template dependency detected';
          END IF;

          -- Add to visited
          v_visited := v_visited || v_current_id;

          -- Get next template
          SELECT {{ template_field }}
          INTO v_current_id
          FROM {{ schema }}.tb_{{ template_entity | lower }}
          WHERE id = v_current_id;
        END LOOP;

        RETURN true;
      END;
```

**Commit Point**: `git commit -m "feat: add template inheritance validator pattern"`

---

#### **Task 2.2: Implement JSONB Merge Functions** (1.5 hours)

These are PostgreSQL functions needed by the pattern. Create in `src/generators/schema/jsonb_helpers.py`:

```python
"""Generate PostgreSQL JSONB helper functions."""


class JSONBHelpersGenerator:
    """Generate JSONB utility functions for patterns."""

    @staticmethod
    def generate_deep_merge() -> str:
        """Generate jsonb_deep_merge aggregate function."""
        return """
-- Deep merge JSONB objects (child overrides parent)
CREATE OR REPLACE FUNCTION jsonb_deep_merge(jsonb, jsonb)
RETURNS jsonb
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT
    jsonb_object_agg(
      key,
      CASE
        WHEN jsonb_typeof($1->key) = 'object' AND jsonb_typeof($2->key) = 'object'
        THEN jsonb_deep_merge($1->key, $2->key)
        ELSE coalesce($2->key, $1->key)
      END
    )
  FROM (
    SELECT key FROM jsonb_object_keys($1)
    UNION
    SELECT key FROM jsonb_object_keys($2)
  ) keys;
$$;

-- Aggregate function for multiple JSONB objects
CREATE OR REPLACE AGGREGATE jsonb_deep_merge_agg(jsonb) (
  SFUNC = jsonb_deep_merge,
  STYPE = jsonb,
  INITCOND = '{}'
);
"""

    @staticmethod
    def generate_append_recursive() -> str:
        """Generate jsonb_append_recursive for array concatenation."""
        return """
-- Append arrays, merge objects recursively
CREATE OR REPLACE FUNCTION jsonb_append_recursive(jsonb, jsonb)
RETURNS jsonb
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT
    CASE
      WHEN jsonb_typeof($1) = 'array' AND jsonb_typeof($2) = 'array'
      THEN $1 || $2

      WHEN jsonb_typeof($1) = 'object' AND jsonb_typeof($2) = 'object'
      THEN jsonb_deep_merge($1, $2)

      ELSE coalesce($2, $1)
    END;
$$;
"""
```

---

#### **Task 2.3: Run Template Inheritance Tests** (1 hour)

```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance_validator.py -v

# Expected: 16 tests passing ✅
```

---

### **Afternoon Session (4 hours): Computed Column Pattern**

#### **Task 2.4: Create Pattern Specification** (1.5 hours)

Create `stdlib/schema/schema/computed_column.yaml`:

```yaml
pattern: schema_computed_column
version: 1.0
category: schema
description: |
  Add GENERATED ALWAYS AS computed columns with automatic indexing.
  Supports both STORED (precomputed) and VIRTUAL (computed on read).

parameters:
  - name: column_name
    type: string
    required: true
    description: "Name of computed column"
    validation: "^[a-z][a-z0-9_]*$"

  - name: expression
    type: string
    required: true
    description: "SQL expression for computed value"
    example: "LOWER(email)"

  - name: type
    type: string
    required: true
    description: "PostgreSQL type of result"
    example: "text"

  - name: stored
    type: boolean
    default: true
    description: "STORED (precomputed) vs VIRTUAL (computed on read)"

  - name: index
    type: boolean
    default: false
    description: "Create index on computed column"

  - name: index_type
    type: enum
    values: [btree, gin, gist, hash]
    default: btree
    description: "Type of index to create"

  - name: comment
    type: string
    default: ""
    description: "Column comment"

schema_extensions:
  computed_columns:
    - name: "{{ column_name }}"
      type: "{{ type }}"
      expression: "{{ expression }}"
      stored: "{{ stored }}"
      comment: "{{ comment or 'Computed: ' + expression }}"

  indexes:
    - name: "idx_{{ entity.name | lower }}_{{ column_name }}"
      fields: ["{{ column_name }}"]
      using: "{{ index_type }}"
      when: "{{ index }}"
      comment: "Index on computed column {{ column_name }}"

examples:
  - name: Email normalization
    yaml: |
      entity: User
      fields:
        email: text
      patterns:
        - type: schema_computed_column
          params:
            column_name: email_normalized
            expression: "LOWER(TRIM(email))"
            type: text
            stored: true
            index: true

    generated:
      - email_normalized text GENERATED ALWAYS AS (LOWER(TRIM(email))) STORED
      - CREATE INDEX idx_user_email_normalized ON tb_user(email_normalized);

  - name: Full name concatenation
    yaml: |
      entity: Contact
      fields:
        first_name: text
        last_name: text
      patterns:
        - type: schema_computed_column
          params:
            column_name: full_name
            expression: "first_name || ' ' || last_name"
            type: text
            stored: false

    generated:
      - full_name text GENERATED ALWAYS AS (first_name || ' ' || last_name) VIRTUAL

  - name: Price with tax
    yaml: |
      entity: Product
      fields:
        base_price: decimal
        tax_rate: decimal
      patterns:
        - type: schema_computed_column
          params:
            column_name: price_with_tax
            expression: "base_price * (1 + tax_rate)"
            type: decimal
            stored: true

    generated:
      - price_with_tax decimal GENERATED ALWAYS AS (base_price * (1 + tax_rate)) STORED

performance:
  - operation: Read STORED column
    complexity: O(1)
    notes: "Same as normal column, value is precomputed"

  - operation: Read VIRTUAL column
    complexity: O(1) + cost of expression
    notes: "Computed on every read, use for rarely accessed columns"

  - operation: Index on STORED column
    complexity: O(log n)
    notes: "Full index performance, recommended for queries"

limitations:
  - "VIRTUAL columns cannot have indexes (PostgreSQL limitation pre-v15)"
  - "Expression cannot reference other computed columns"
  - "Expression must be deterministic (no now(), random(), etc.)"

best_practices:
  - "Use STORED for frequently queried columns"
  - "Use VIRTUAL for derived data rarely accessed"
  - "Index STORED computed columns used in WHERE/ORDER BY"
  - "Keep expressions simple for better performance"
```

**Commit Point**: `git commit -m "feat: add computed column pattern"`

---

#### **Task 2.5: Implement Computed Column in Schema Generator** (1.5 hours)

Update `src/generators/schema/table_generator.py`:

```python
"""Table DDL generation with computed column support."""


class TableGenerator:
    """Generate CREATE TABLE DDL."""

    def _generate_computed_columns(self, entity: Entity) -> List[str]:
        """Generate computed column definitions."""
        computed_cols = []

        for pattern in entity.patterns:
            if pattern.type == 'schema_computed_column':
                col_def = self._generate_computed_column(entity, pattern)
                computed_cols.append(col_def)

        return computed_cols

    def _generate_computed_column(
        self,
        entity: Entity,
        pattern: Pattern,
    ) -> str:
        """Generate single computed column definition."""
        params = pattern.params

        col_name = params['column_name']
        col_type = params['type']
        expression = params['expression']
        stored = params.get('stored', True)

        storage = 'STORED' if stored else 'VIRTUAL'

        ddl = f"{col_name} {col_type} GENERATED ALWAYS AS ({expression}) {storage}"

        return ddl
```

---

#### **Task 2.6: Run Computed Column Tests** (1 hour)

```bash
uv run pytest tests/unit/patterns/schema/test_computed_column.py -v

# Expected: 14 tests passing ✅
```

---

**Day 2 Completion Check**:
```bash
# All pattern tests should pass
uv run pytest tests/unit/patterns -v
# Expected: 112 passed ✅

# Coverage check
uv run pytest --cov=src/generators --cov-report=term
# Expected: 95%+ ✅
```

**Deliverable**: All 6 patterns fully implemented and tested

---

## Days 3-4 (Wed-Thu): CLI Test Fixes & Orchestration

**Objective**: Fix all CLI test failures, improve orchestration

### **Day 3 Morning: CLI Test Analysis**

#### **Task 3.1: Categorize CLI Test Failures** (2 hours)

```bash
# Run CLI tests with detailed output
uv run pytest tests/unit/cli/ -v --tb=short > cli_test_results.txt

# Analyze and categorize failures
python scripts/analyze_cli_failures.py cli_test_results.txt
```

Create `scripts/analyze_cli_failures.py`:

```python
"""Analyze CLI test failures and categorize them."""

import sys
import re
from collections import defaultdict


def analyze_failures(results_file):
    """Parse pytest output and categorize failures."""

    with open(results_file) as f:
        content = f.read()

    # Extract failures
    failure_pattern = r'FAILED tests/unit/cli/(\w+)\.py::(\w+)::(\w+) - (.+)'
    failures = re.findall(failure_pattern, content)

    # Categorize
    categories = defaultdict(list)

    for module, test_class, test_name, error in failures:
        # Categorize by error type
        if 'ValidationError' in error:
            category = 'Validation'
        elif 'FileNotFoundError' in error or 'path' in error.lower():
            category = 'File Operations'
        elif 'DependencyError' in error or 'import' in error.lower():
            category = 'Dependencies'
        elif 'AssertionError' in error:
            category = 'Logic Errors'
        else:
            category = 'Other'

        categories[category].append({
            'module': module,
            'test': f"{test_class}::{test_name}",
            'error': error[:100],
        })

    # Report
    print("CLI Test Failure Analysis")
    print("=" * 80)

    for category, failures in sorted(categories.items()):
        print(f"\n{category}: {len(failures)} failures")
        print("-" * 40)
        for failure in failures[:5]:  # Show first 5
            print(f"  {failure['module']}: {failure['test']}")
            print(f"    Error: {failure['error']}")

    print(f"\nTotal: {sum(len(f) for f in categories.values())} failures")


if __name__ == '__main__':
    analyze_failures(sys.argv[1])
```

**Expected Output**:
```
CLI Test Failure Analysis
================================================================================

Validation: 12 failures
----------------------------------------
  validate: TestEntityValidation::test_missing_required_field
    Error: Expected ValidationError for missing 'schema' field
  ...

File Operations: 8 failures
----------------------------------------
  generate: TestSchemaGeneration::test_output_directory_creation
    Error: FileNotFoundError: [Errno 2] No such file or directory: 'output/db'
  ...

Dependencies: 3 failures
----------------------------------------
  ...

Total: 27 failures
```

---

#### **Task 3.2: Fix Validation Errors** (2 hours)

Focus on validation test failures. Update `src/cli/validate.py`:

```python
"""CLI validation command with improved error handling."""

import click
from rich.console import Console
from pathlib import Path

from src.core.parser import SpecQLParser
from src.core.validator import EntityValidator

console = Console()


@click.command()
@click.argument('entity_files', nargs=-1, type=click.Path(exists=True))
@click.option('--strict', is_flag=True, help='Fail on warnings')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def validate(entity_files, strict, verbose):
    """Validate SpecQL entity definitions."""

    if not entity_files:
        console.print("[red]Error:[/red] No entity files specified", style="bold")
        console.print("Usage: specql validate entities/*.yaml")
        raise click.Abort()

    parser = SpecQLParser()
    validator = EntityValidator()

    total_files = len(entity_files)
    errors = []
    warnings = []

    for file_path in entity_files:
        console.print(f"Validating {file_path}...", end=" ")

        try:
            # Parse entity
            with open(file_path) as f:
                yaml_content = f.read()

            entity = parser.parse(yaml_content)

            # Validate
            validation_result = validator.validate(entity)

            if validation_result.errors:
                console.print("[red]✗ FAILED[/red]")
                errors.extend([
                    {
                        'file': file_path,
                        'type': 'error',
                        'message': error,
                    }
                    for error in validation_result.errors
                ])

            elif validation_result.warnings:
                console.print("[yellow]⚠ WARNINGS[/yellow]")
                warnings.extend([
                    {
                        'file': file_path,
                        'type': 'warning',
                        'message': warning,
                    }
                    for warning in validation_result.warnings
                ])

            else:
                console.print("[green]✓ PASSED[/green]")

        except Exception as e:
            console.print("[red]✗ ERROR[/red]")
            errors.append({
                'file': file_path,
                'type': 'parse_error',
                'message': str(e),
            })

    # Summary
    console.print()
    console.print("=" * 80)
    console.print(f"Validated {total_files} files")
    console.print(f"  [green]✓[/green] Passed: {total_files - len(errors) - len(warnings)}")
    console.print(f"  [yellow]⚠[/yellow] Warnings: {len(warnings)}")
    console.print(f"  [red]✗[/red] Errors: {len(errors)}")

    # Show details
    if errors and verbose:
        console.print("\n[red]Errors:[/red]")
        for error in errors:
            console.print(f"  {error['file']}: {error['message']}")

    if warnings and verbose:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  {warning['file']}: {warning['message']}")

    # Exit code
    if errors or (strict and warnings):
        raise click.ClickException("Validation failed")
```

---

### **Day 3 Afternoon: File Operation Fixes** (4 hours)

Fix file generation and output directory issues.

Update `src/cli/generate.py`:

```python
"""CLI generate command with robust file operations."""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import os

from src.cli.orchestrator import GenerationOrchestrator

console = Console()


@click.command()
@click.argument('entity_files', nargs=-1, type=click.Path(exists=True))
@click.option(
    '--output-schema',
    type=click.Path(),
    default='db/schema',
    help='Output directory for schema files',
)
@click.option(
    '--output-frontend',
    type=click.Path(),
    help='Output directory for frontend code',
)
@click.option('--with-impacts', is_flag=True, help='Generate mutation impacts')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def generate(entity_files, output_schema, output_frontend, with_impacts, verbose):
    """Generate PostgreSQL schema from SpecQL entities."""

    if not entity_files:
        console.print("[red]Error:[/red] No entity files specified", style="bold")
        console.print("Usage: specql generate entities/*.yaml")
        raise click.Abort()

    # Ensure output directories exist
    output_schema_path = Path(output_schema)
    output_schema_path.mkdir(parents=True, exist_ok=True)

    if output_frontend:
        output_frontend_path = Path(output_frontend)
        output_frontend_path.mkdir(parents=True, exist_ok=True)
    else:
        output_frontend_path = None

    # Initialize orchestrator
    orchestrator = GenerationOrchestrator(
        output_schema_dir=output_schema_path,
        output_frontend_dir=output_frontend_path,
    )

    # Generate with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:

        # Parse entities
        task = progress.add_task("Parsing entities...", total=None)
        entities = orchestrator.parse_entities(entity_files)
        progress.update(task, completed=True)

        # Generate schema
        task = progress.add_task("Generating schema DDL...", total=None)
        schema_files = orchestrator.generate_schema(entities)
        progress.update(task, completed=True)

        # Generate actions
        task = progress.add_task("Generating action functions...", total=None)
        action_files = orchestrator.generate_actions(entities)
        progress.update(task, completed=True)

        # Generate FraiseQL metadata
        task = progress.add_task("Generating FraiseQL metadata...", total=None)
        fraiseql_files = orchestrator.generate_fraiseql(entities)
        progress.update(task, completed=True)

        # Generate frontend (if requested)
        if output_frontend_path:
            task = progress.add_task("Generating frontend code...", total=None)
            frontend_files = orchestrator.generate_frontend(entities, with_impacts)
            progress.update(task, completed=True)
        else:
            frontend_files = []

    # Summary
    total_files = len(schema_files) + len(action_files) + len(fraiseql_files) + len(frontend_files)

    console.print(f"\n[green]✓[/green] Successfully generated {total_files} files")

    if verbose:
        console.print(f"  Schema DDL: {len(schema_files)} files")
        console.print(f"  Action functions: {len(action_files)} files")
        console.print(f"  FraiseQL metadata: {len(fraiseql_files)} files")
        if frontend_files:
            console.print(f"  Frontend code: {len(frontend_files)} files")
```

---

### **Day 4: Orchestration Improvements** (Full day)

Improve generation orchestrator with better dependency ordering and error handling.

Update `src/cli/orchestrator.py`:

```python
"""Generation orchestrator with improved dependency management."""

from typing import List, Dict, Set
from pathlib import Path
from collections import defaultdict

from src.core.parser import SpecQLParser
from src.core.models import Entity
from src.generators.schema.schema_orchestrator import SchemaOrchestrator
from src.generators.actions.action_orchestrator import ActionOrchestrator
from src.generators.fraiseql.mutation_annotator import MutationAnnotator


class GenerationOrchestrator:
    """Orchestrate full schema + action + frontend generation."""

    def __init__(
        self,
        output_schema_dir: Path,
        output_frontend_dir: Path | None = None,
    ):
        self.output_schema_dir = output_schema_dir
        self.output_frontend_dir = output_frontend_dir

        self.parser = SpecQLParser()
        self.schema_gen = SchemaOrchestrator(output_dir=output_schema_dir)
        self.action_gen = ActionOrchestrator(output_dir=output_schema_dir)

    def parse_entities(self, entity_files: List[str]) -> List[Entity]:
        """Parse all entity files."""
        entities = []

        for file_path in entity_files:
            with open(file_path) as f:
                yaml_content = f.read()

            entity = self.parser.parse(yaml_content)
            entity.metadata['source_file'] = file_path
            entities.append(entity)

        return entities

    def generate_schema(self, entities: List[Entity]) -> List[Path]:
        """Generate schema DDL in dependency order."""

        # Sort by dependencies (topological sort)
        ordered_entities = self._topological_sort(entities)

        schema_files = []

        for entity in ordered_entities:
            files = self.schema_gen.generate(entity)
            schema_files.extend(files)

        return schema_files

    def generate_actions(self, entities: List[Entity]) -> List[Path]:
        """Generate action functions."""
        action_files = []

        for entity in entities:
            files = self.action_gen.generate(entity)
            action_files.extend(files)

        return action_files

    def generate_fraiseql(self, entities: List[Entity]) -> List[Path]:
        """Generate FraiseQL metadata comments."""
        fraiseql_files = []

        annotator = MutationAnnotator(output_dir=self.output_schema_dir)

        for entity in entities:
            files = annotator.generate(entity)
            fraiseql_files.extend(files)

        return fraiseql_files

    def generate_frontend(
        self,
        entities: List[Entity],
        with_impacts: bool = False,
    ) -> List[Path]:
        """Generate frontend TypeScript code."""
        if not self.output_frontend_dir:
            return []

        from src.generators.frontend.typescript_types_generator import TypeScriptTypesGenerator
        from src.generators.frontend.mutation_impacts_generator import MutationImpactsGenerator

        frontend_files = []

        # TypeScript types
        ts_gen = TypeScriptTypesGenerator(output_dir=self.output_frontend_dir)
        for entity in entities:
            files = ts_gen.generate(entity)
            frontend_files.extend(files)

        # Mutation impacts
        if with_impacts:
            impacts_gen = MutationImpactsGenerator(output_dir=self.output_frontend_dir)
            for entity in entities:
                files = impacts_gen.generate(entity)
                frontend_files.extend(files)

        return frontend_files

    def _topological_sort(self, entities: List[Entity]) -> List[Entity]:
        """Sort entities by dependency order (referenced entities first)."""

        # Build dependency graph
        graph: Dict[str, Set[str]] = defaultdict(set)
        entity_map: Dict[str, Entity] = {}

        for entity in entities:
            entity_map[entity.name] = entity

            # Find ref() dependencies
            for field in entity.fields:
                if field.type.startswith('ref('):
                    ref_entity = field.type[4:-1]  # Extract entity name from ref(Entity)
                    graph[entity.name].add(ref_entity)

        # Topological sort using DFS
        visited = set()
        result = []

        def dfs(entity_name: str):
            if entity_name in visited:
                return

            visited.add(entity_name)

            # Visit dependencies first
            for dep in graph.get(entity_name, []):
                if dep in entity_map:  # Only if dependency is in our entity set
                    dfs(dep)

            # Add entity to result
            if entity_name in entity_map:
                result.append(entity_map[entity_name])

        # Process all entities
        for entity_name in entity_map:
            dfs(entity_name)

        return result
```

**Day 4 Completion Check**:
```bash
# CLI tests should be passing
uv run pytest tests/unit/cli -v
# Expected: High pass rate (80%+)

# Integration test
specql generate entities/contact.yaml --output-schema=/tmp/test_output
ls /tmp/test_output/10_tables/
# Expected: contact.sql exists ✅
```

---

## Day 5 (Friday): CLI UX Polish

**Objective**: Excellent error messages, progress indicators, helpful output

### **Morning: Error Message Improvements** (4 hours)

Create comprehensive error handling with helpful messages.

Update `src/cli/error_handler.py`:

```python
"""Centralized error handling for CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import click

console = Console()


class CLIError(Exception):
    """Base CLI error with rich formatting."""

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        details: str | None = None,
    ):
        self.message = message
        self.hint = hint
        self.details = details
        super().__init__(message)

    def display(self):
        """Display formatted error message."""
        console.print()
        console.print(Panel(
            f"[red bold]Error:[/red bold] {self.message}",
            border_style="red",
        ))

        if self.details:
            console.print(f"\n[dim]{self.details}[/dim]")

        if self.hint:
            console.print(f"\n[yellow]💡 Hint:[/yellow] {self.hint}")

        console.print()


class ValidationError(CLIError):
    """Entity validation error."""
    pass


class GenerationError(CLIError):
    """Schema generation error."""
    pass


class DependencyError(CLIError):
    """Missing dependency error."""

    def __init__(self, package: str, feature: str, pip_extra: str):
        message = f"{feature} requires {package}"
        hint = f"Install with: [cyan]pip install specql[{pip_extra}][/cyan]"
        super().__init__(message, hint=hint)


def handle_cli_errors(func):
    """Decorator to handle CLI errors gracefully."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except CLIError as e:
            e.display()
            raise click.Abort()

        except FileNotFoundError as e:
            error = CLIError(
                message=f"File not found: {e.filename}",
                hint="Check the file path and try again",
            )
            error.display()
            raise click.Abort()

        except Exception as e:
            # Unexpected error
            console.print_exception(show_locals=True)
            console.print("\n[red]An unexpected error occurred[/red]")
            console.print(f"Please report this issue: https://github.com/yourproject/issues")
            raise click.Abort()

    return wrapper
```

---

### **Afternoon: Progress Indicators & Output Polish** (4 hours)

Add detailed progress indicators for long operations.

Example for schema generation with detailed progress:

```python
"""Enhanced progress reporting."""

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)


def generate_with_progress(entities: List[Entity]) -> List[Path]:
    """Generate schema with detailed progress reporting."""

    total_entities = len(entities)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as progress:

        # Overall progress
        main_task = progress.add_task(
            "Generating schema...",
            total=total_entities,
        )

        files = []

        for i, entity in enumerate(entities, 1):
            # Update task description
            progress.update(
                main_task,
                description=f"[{i}/{total_entities}] Generating {entity.name}...",
                completed=i-1,
            )

            # Generate
            entity_files = schema_gen.generate(entity)
            files.extend(entity_files)

        progress.update(main_task, completed=total_entities)

    return files
```

**Day 5 Completion Check**:
```bash
# CLI tests all passing
uv run pytest tests/unit/cli -v
# Expected: 100% pass rate ✅

# Manual UX test
specql validate entities/invalid.yaml
# Expected: Beautiful error messages with hints ✅

specql generate entities/*.yaml --verbose
# Expected: Detailed progress bars ✅
```

---

## Days 6-7 (Weekend): Integration Testing & Buffer

### **Day 6: End-to-End Integration Tests**

Create comprehensive integration tests covering full workflows.

Create `tests/integration/test_full_generation_workflow.py`:

```python
"""End-to-end integration tests for full generation workflow."""

import pytest
from pathlib import Path
import subprocess


class TestFullGenerationWorkflow:
    """Test complete generation workflow from YAML to SQL."""

    def test_simple_entity_generation(self, tmp_path):
        """Test generating simple entity end-to-end."""

        # Create entity YAML
        entity_yaml = tmp_path / "contact.yaml"
        entity_yaml.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  name: text
  company: ref(Company)
actions:
  - name: create_contact
    steps:
      - insert: Contact
""")

        # Generate
        output_dir = tmp_path / "output"
        result = subprocess.run(
            [
                "specql",
                "generate",
                str(entity_yaml),
                f"--output-schema={output_dir}",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Verify files generated
        table_file = output_dir / "10_tables" / "contact.sql"
        assert table_file.exists()

        # Verify content
        content = table_file.read_text()
        assert "CREATE TABLE crm.tb_contact" in content
        assert "email TEXT" in content
        assert "fk_company UUID" in content

    def test_entity_with_patterns(self, tmp_path):
        """Test generating entity with patterns."""

        entity_yaml = tmp_path / "product.yaml"
        entity_yaml.write_text("""
entity: Product
schema: catalog
fields:
  product_code: text
  name: text
  price: decimal
patterns:
  - type: temporal_scd_type2_helper
    params:
      natural_key: [product_code]
""")

        output_dir = tmp_path / "output"
        result = subprocess.run(
            ["specql", "generate", str(entity_yaml), f"--output-schema={output_dir}"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Verify SCD Type 2 fields added
        table_file = output_dir / "10_tables" / "product.sql"
        content = table_file.read_text()

        assert "version_number INTEGER" in content
        assert "is_current BOOLEAN" in content
        assert "effective_date TIMESTAMPTZ" in content
        assert "expiry_date TIMESTAMPTZ" in content

        # Verify helper functions generated
        helper_file = output_dir / "30_functions" / "product_helpers.sql"
        assert helper_file.exists()

        content = helper_file.read_text()
        assert "create_new_version_product" in content
        assert "get_current_version_product" in content
```

---

### **Day 7: Buffer & Documentation**

- Fix any remaining test failures
- Update documentation
- Code review and cleanup
- Prepare for Week 3

---

## 📊 Week 2 Success Metrics

### **Quantitative Metrics**
```bash
# Pattern implementation
uv run pytest tests/unit/patterns -v
# Expected: 112 passed ✅

# CLI tests
uv run pytest tests/unit/cli -v
# Expected: 100% pass rate ✅

# Integration tests
uv run pytest tests/integration -v
# Expected: All passing ✅

# Coverage
uv run pytest --cov=src --cov-report=term
# Expected: 95%+ ✅

# Total tests
uv run pytest --collect-only | grep "collected"
# Expected: 520+ tests ✅
```

### **Qualitative Metrics**
- ✅ All 6 patterns working with real entities
- ✅ CLI provides excellent user experience
- ✅ Error messages are helpful and actionable
- ✅ Progress indicators for long operations
- ✅ File generation is robust (atomic writes, rollback on error)

### **Deliverables**
- ✅ 3 new patterns implemented (SCD Type 2, Template Inheritance, Computed Column)
- ✅ All 112 pattern tests passing
- ✅ All CLI tests passing
- ✅ Production-grade CLI with beautiful UX
- ✅ Comprehensive integration tests
- ✅ Updated documentation

---

## 🚀 Handoff to Week 3

**Status Check**:
```bash
# Full test suite
uv run pytest
# Expected: 520+ passed, 95%+ coverage ✅

# Patterns ready for PrintOptim
find stdlib/schema -name "*.yaml" | wc -l
# Expected: 16+ pattern files ✅

# CLI production-ready
specql --help
specql generate --help
specql validate --help
# Expected: Beautiful help text, clear examples ✅
```

**Week 3 Preview**:
- Apply patterns to PrintOptim (245 tables)
- Validate 95%+ automation
- Performance benchmarking
- Integration testing at scale

**Confidence Level**: 85% ✅

---

**Week 2 Completion Criteria**:
- [ ] All 6 patterns implemented with tests (112 tests passing)
- [ ] All CLI tests passing (100% pass rate)
- [ ] Coverage maintained at 95%+
- [ ] CLI UX polished (helpful errors, progress indicators)
- [ ] Integration tests passing
- [ ] Documentation updated

**Risk Assessment**: **MEDIUM**
- Pattern implementation complexity managed by TDD
- CLI test fixes straightforward (mostly validation/orchestration)
- Buffer days (6-7) provide safety margin

---

**Created**: 2025-11-18
**Author**: Claude Code (Sonnet 4.5)
**Version**: 1.0
