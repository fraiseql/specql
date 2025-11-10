# SpecQL Query Pattern Library - Detailed Phased Implementation Plan

**Created**: 2025-11-10
**Status**: Implementation Ready
**Total Duration**: 14-16 weeks (3-4 months)
**Complexity**: High - Extends SpecQL core with new declarative query layer

---

## Executive Summary

This plan breaks down the Query Pattern Library implementation into **12 focused phases** following SpecQL's proven TDD methodology. Each phase is scoped for **1-2 weeks** with clear RED → GREEN → REFACTOR → QA cycles.

**Key Principles**:
- ✅ **Test-first**: Every pattern has tests before implementation
- ✅ **Incremental**: Each phase builds on previous work
- ✅ **Validated**: Real PrintOptim patterns validate design
- ✅ **Documented**: User-facing docs created alongside code

---

## Phase 0: Foundation & Design (Week 1-2)

**Objective**: Establish architecture, schemas, and proof-of-concept

### TDD Cycle 1: Pattern System Design

#### 🔴 RED: Write Failing Tests
```bash
# Test: Pattern discovery and registration
uv run pytest tests/unit/patterns/test_pattern_registry.py::test_discover_patterns -v
# Expected: FAILED (pattern registry not implemented)

# Test: Pattern schema validation
uv run pytest tests/unit/patterns/test_pattern_schema.py::test_validate_junction_config -v
# Expected: FAILED (schema validation not implemented)
```

**Test Coverage**:
- Pattern discovery from `stdlib/queries/`
- YAML config schema validation
- Pattern metadata (name, category, parameters)

#### 🟢 GREEN: Implement Pattern Registry
```python
# src/patterns/pattern_registry.py
class PatternRegistry:
    def __init__(self):
        self.patterns = {}

    def discover_patterns(self, base_path: Path) -> Dict[str, Pattern]:
        """Discover all patterns in stdlib/queries/"""
        pass

    def get_pattern(self, pattern_name: str) -> Pattern:
        """Retrieve pattern by name"""
        pass

# src/patterns/pattern_schema.py
class PatternSchema:
    def validate(self, config: Dict) -> ValidationResult:
        """Validate pattern configuration"""
        pass
```

**Files Created**:
- `src/patterns/pattern_registry.py`
- `src/patterns/pattern_schema.py`
- `src/patterns/base_pattern.py`
- `tests/unit/patterns/test_pattern_registry.py`
- `tests/unit/patterns/test_pattern_schema.py`

#### 🔧 REFACTOR: Clean Architecture
- Separate pattern definition from validation
- Add type hints and docstrings
- Follow SpecQL naming conventions

#### ✅ QA: Verify Foundation
```bash
uv run pytest tests/unit/patterns/ -v
uv run ruff check src/patterns/
uv run mypy src/patterns/
```

---

### TDD Cycle 2: Junction Pattern Proof-of-Concept

#### 🔴 RED: Test Junction Pattern Generation
```bash
# Test: Generate junction resolver SQL
uv run pytest tests/integration/patterns/test_junction_pattern.py::test_generate_financing_condition_resolver -v
# Expected: FAILED (junction pattern not implemented)
```

**Test Spec**:
```python
def test_generate_financing_condition_resolver():
    config = {
        "name": "v_financing_condition_and_model_by_contract",
        "pattern": "junction/resolver",
        "config": {
            "source_entity": "Contract",
            "junction_tables": [
                {"table": "ContractFinancingCondition", "left_key": "contract_id", "right_key": "financing_condition_id"},
                {"table": "FinancingConditionModel", "left_key": "financing_condition_id", "right_key": "model_id"}
            ],
            "target_entity": "Model"
        }
    }

    sql = generate_pattern(config)
    assert "CREATE OR REPLACE VIEW" in sql
    assert "INNER JOIN" in sql
    assert "tb_contract" in sql
    assert "tb_financing_condition" in sql
```

#### 🟢 GREEN: Implement Junction Pattern
```python
# src/patterns/junction/resolver.py
def generate_junction_resolver(config: Dict) -> str:
    """Generate N-to-N junction resolver SQL"""
    template = load_template("junction/resolver.sql.jinja2")
    return template.render(**config)
```

**Template Created**:
```jinja2
{# stdlib/queries/junction/resolver.sql.jinja2 #}
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ source_entity.pk_field }},
    {% for junction in junction_tables %}
    {{ junction.target_pk }},
    {% endfor %}
    {{ source_entity.schema }}.tenant_id
FROM {{ source_entity.table }} {{ source_entity.alias }}
{% for junction in junction_tables %}
INNER JOIN {{ junction.table }} {{ junction.alias }}
    ON {{ junction.join_condition }}
{% endfor %}
WHERE {{ source_entity.alias }}.deleted_at IS NULL
{% for junction in junction_tables %}
  AND {{ junction.alias }}.deleted_at IS NULL
{% endfor %};
```

#### 🔧 REFACTOR: Template Organization
- Extract common SQL fragments
- Add SQL formatting utilities
- Create reusable join builders

#### ✅ QA: Verify Junction Pattern
```bash
# Integration test against real database
uv run pytest tests/integration/patterns/test_junction_pattern.py -v

# Validate generated SQL syntax
psql -c "\i /tmp/generated_junction.sql"
```

**Deliverables**:
- ✅ Pattern registry system
- ✅ Junction pattern (proof-of-concept)
- ✅ Jinja2 template infrastructure
- ✅ Integration test framework

---

## Phase 1: Core Pattern Infrastructure (Week 3-4)

**Objective**: Build scalable generator pipeline for all patterns

### TDD Cycle 1: Query Pattern Generator

#### 🔴 RED: Test Pattern Generation Pipeline
```bash
uv run pytest tests/unit/generators/test_query_pattern_generator.py::test_generate_from_entity -v
# Expected: FAILED (query generator not integrated)
```

**Test Spec**:
```python
def test_generate_from_entity():
    entity = {
        "name": "Location",
        "schema": "tenant",
        "query_patterns": [
            {
                "name": "count_allocations_by_location",
                "pattern": "aggregation/hierarchical_count",
                "config": {...}
            }
        ]
    }

    sql_files = QueryPatternGenerator().generate(entity)
    assert len(sql_files) == 1
    assert sql_files[0].name == "v_count_allocations_by_location.sql"
```

#### 🟢 GREEN: Implement Query Generator
```python
# src/generators/query_pattern_generator.py
class QueryPatternGenerator:
    def __init__(self, registry: PatternRegistry):
        self.registry = registry

    def generate(self, entity: Dict) -> List[SQLFile]:
        """Generate SQL files for all query patterns in entity"""
        sql_files = []
        for pattern_config in entity.get("query_patterns", []):
            pattern = self.registry.get_pattern(pattern_config["pattern"])
            sql = pattern.generate(entity, pattern_config)
            sql_files.append(SQLFile(name=f"v_{pattern_config['name']}.sql", content=sql))
        return sql_files
```

**Integration Points**:
- `src/generators/schema_orchestrator.py` - Add query pattern generation step
- `src/cli/generate.py` - Add `--with-query-patterns` flag
- `src/generators/` - New `query_pattern_generator.py`

#### 🔧 REFACTOR: Generator Integration
- Separate query generation from schema generation
- Add topological sort for view dependencies
- Handle cross-entity pattern references

#### ✅ QA: Verify Generator Pipeline
```bash
# Full integration test
specql generate entities/location.yaml --with-query-patterns
ls -la db/schema/02_query_side/tenant/

uv run pytest tests/integration/generators/test_query_pattern_generator.py -v
```

---

### TDD Cycle 2: Dependency Resolution

#### 🔴 RED: Test View Dependency Ordering
```bash
uv run pytest tests/unit/generators/test_view_dependencies.py::test_topological_sort -v
# Expected: FAILED (dependency resolver not implemented)
```

**Test Spec**:
```python
def test_topological_sort():
    patterns = [
        {"name": "v_base", "depends_on": []},
        {"name": "v_intermediate", "depends_on": ["v_base"]},
        {"name": "v_top", "depends_on": ["v_intermediate", "v_base"]}
    ]

    sorted_views = ViewDependencyResolver().sort(patterns)
    assert sorted_views == ["v_base", "v_intermediate", "v_top"]
```

#### 🟢 GREEN: Implement Dependency Resolver
```python
# src/generators/schema/view_dependency.py
class ViewDependencyResolver:
    def sort(self, patterns: List[Dict]) -> List[str]:
        """Topologically sort views by dependencies"""
        graph = self._build_graph(patterns)
        return self._topological_sort(graph)

    def _build_graph(self, patterns: List[Dict]) -> nx.DiGraph:
        """Build dependency graph from patterns"""
        pass
```

#### 🔧 REFACTOR: Dependency Analysis
- Extract dependencies from SQL (parse FROM/JOIN clauses)
- Handle circular dependencies (error reporting)
- Add visualization for debugging

#### ✅ QA: Verify Dependency Resolution
```bash
uv run pytest tests/unit/generators/test_view_dependencies.py -v
specql generate entities/*.yaml --with-query-patterns --dry-run
```

**Deliverables**:
- ✅ Query pattern generator integrated into pipeline
- ✅ View dependency resolution
- ✅ CLI support for query patterns
- ✅ Integration tests

---

## Phase 2: Junction Patterns (Week 5)

**Objective**: Complete junction resolver patterns (15 PrintOptim examples)

### TDD Cycle 1: Basic Junction Resolver

#### 🔴 RED: Test 2-Hop Junction
```bash
uv run pytest tests/unit/patterns/junction/test_resolver.py::test_two_hop_junction -v
```

**Test Coverage**:
- 2-hop junction (A → B → C)
- 3-hop junction (A → B → C → D)
- Multi-tenant filtering
- Cross-schema references

#### 🟢 GREEN: Implement Junction Resolver
```yaml
# stdlib/queries/junction/resolver.yaml
pattern: junction/resolver
description: Resolve N-to-N relationships through junction tables
parameters:
  source_entity:
    type: entity_reference
    required: true
  junction_tables:
    type: array
    items:
      table: string
      left_key: string
      right_key: string
    required: true
  target_entity:
    type: entity_reference
    required: true
  output_fields:
    type: array
    items: string
    default: [pk_*, tenant_id]
```

**Template**:
```jinja2
{# stdlib/queries/junction/resolver.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description Resolves {{ source_entity }} to {{ target_entity }} via {{ junction_tables|length }}-hop junction
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT DISTINCT
    {{ render_output_fields(output_fields) }}
FROM {{ source_entity.schema }}.{{ source_entity.table }} {{ source_entity.alias }}
{% for junction in junction_tables %}
INNER JOIN {{ junction.schema }}.{{ junction.table }} {{ junction.alias }}
    ON {{ junction.alias }}.{{ junction.left_key }} = {{ get_previous_alias(loop.index0) }}.{{ get_previous_pk(loop.index0) }}
{% endfor %}
WHERE {{ source_entity.alias }}.deleted_at IS NULL
{% for junction in junction_tables %}
  AND {{ junction.alias }}.deleted_at IS NULL
{% endfor %}
{% if source_entity.is_multi_tenant %}
  AND {{ source_entity.alias }}.tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid
{% endif %};

-- Indexes
CREATE INDEX IF NOT EXISTS idx_{{ name }}_{{ source_entity.pk }}
    ON {{ schema }}.{{ name }}({{ source_entity.pk_field }});
CREATE INDEX IF NOT EXISTS idx_{{ name }}_{{ target_entity.pk }}
    ON {{ schema }}.{{ name }}({{ target_entity.pk_field }});
```

#### 🔧 REFACTOR: Junction Utilities
- Extract junction chain builder
- Add FK validation (ensure keys exist)
- Optimize multi-hop joins

#### ✅ QA: Validate Junction Patterns
```bash
# Test all 15 PrintOptim junction examples
uv run pytest tests/integration/patterns/junction/ -v

# Generate real-world examples
specql generate stdlib/queries/junction/examples/*.yaml
```

---

### TDD Cycle 2: Junction Aggregation Variant

#### 🔴 RED: Test Junction with Aggregation
```bash
uv run pytest tests/unit/patterns/junction/test_aggregated_junction.py -v
```

**Test Case**: `v_machine_items` (array aggregation)

#### 🟢 GREEN: Implement Aggregated Junction
```yaml
# stdlib/queries/junction/aggregated_resolver.yaml
pattern: junction/aggregated_resolver
description: Junction resolver with JSONB array aggregation
parameters:
  source_entity: entity_reference
  junction_path: array
  aggregate_into: string  # field name for JSONB array
  order_by: array  # optional ordering
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ source_entity.pk_field }},
    jsonb_agg(
        jsonb_build_object({{ render_aggregation_fields(fields) }})
        {% if order_by %}ORDER BY {{ order_by|join(', ') }}{% endif %}
    ) AS {{ aggregate_into }}
FROM {{ source_entity.table }} src
INNER JOIN {{ junction_path[0].table }} j1 ON ...
{% for junction in junction_path[1:] %}
INNER JOIN {{ junction.table }} j{{ loop.index + 1 }} ON ...
{% endfor %}
GROUP BY {{ source_entity.pk_field }};
```

#### 🔧 REFACTOR: Aggregation Helpers
- Create `jsonb_agg` builder utility
- Add nested object support
- Handle NULL aggregations

#### ✅ QA: Test Junction Aggregations
```bash
uv run pytest tests/integration/patterns/junction/test_aggregated_junction.py -v
```

**Deliverables**:
- ✅ Junction resolver pattern (complete)
- ✅ Aggregated junction variant
- ✅ 15 PrintOptim examples converted
- ✅ Documentation for junction patterns

---

## Phase 3: Aggregation Patterns (Week 6-7)

**Objective**: Implement metric calculation patterns (12 PrintOptim examples)

### TDD Cycle 1: Basic Aggregation Helper

#### 🔴 RED: Test Simple Aggregation
```bash
uv run pytest tests/unit/patterns/aggregation/test_count_aggregation.py -v
```

**Test Case**: Count allocations by network configuration

#### 🟢 GREEN: Implement Count Aggregation
```yaml
# stdlib/queries/aggregation/count_aggregation.yaml
pattern: aggregation/count_aggregation
description: Count child entities grouped by parent
parameters:
  counted_entity:
    type: entity_reference
    required: true
  grouped_by_entity:
    type: entity_reference
    required: true
  metrics:
    type: array
    items:
      name: string
      condition: string  # SQL WHERE condition
    required: true
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ grouped_by_entity.pk_field }},
    {% for metric in metrics %}
    COUNT(CASE WHEN {{ metric.condition }} THEN 1 END) AS {{ metric.name }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM {{ grouped_by_entity.table }} parent
LEFT JOIN {{ counted_entity.table }} child
    ON {{ join_condition }}
WHERE parent.deleted_at IS NULL
  AND (child.deleted_at IS NULL OR child.{{ pk_field }} IS NULL)
GROUP BY {{ grouped_by_entity.pk_field }};
```

#### 🔧 REFACTOR: Aggregation Utilities
- Extract COUNT/SUM/AVG builders
- Add FILTER clause support (PostgreSQL 9.4+)
- Handle NULL edge cases

#### ✅ QA: Validate Count Aggregations
```bash
uv run pytest tests/integration/patterns/aggregation/test_count_aggregation.py -v
```

---

### TDD Cycle 2: Hierarchical Aggregation

#### 🔴 RED: Test Hierarchical Counts
```bash
uv run pytest tests/unit/patterns/aggregation/test_hierarchical_count.py -v
```

**Test Case**: `v_count_allocations_by_location` (ltree hierarchical)

#### 🟢 GREEN: Implement Hierarchical Count
```yaml
# stdlib/queries/aggregation/hierarchical_count.yaml
pattern: aggregation/hierarchical_count
description: Hierarchical aggregation using ltree paths
parameters:
  counted_entity: entity_reference
  grouped_by_entity: entity_reference  # Must be hierarchical
  metrics:
    - name: string
      direct: boolean  # Direct children only
      hierarchical: boolean  # All descendants
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    parent.{{ pk_field }},
    {% for metric in metrics %}
    {% if metric.direct %}
    COUNT(CASE WHEN child.{{ fk_field }} = parent.{{ pk_field }} THEN 1 END) AS {{ metric.name }}_direct,
    {% endif %}
    {% if metric.hierarchical %}
    COUNT(CASE WHEN parent.path @> child.{{ hierarchical_path_field }} THEN 1 END) AS {{ metric.name }}_total,
    {% endif %}
    {% endfor %}
    parent.path
FROM {{ grouped_by_entity.table }} parent
LEFT JOIN {{ counted_entity.table }} child
    ON {{ tenant_join }}
WHERE parent.deleted_at IS NULL
  AND (child.deleted_at IS NULL OR child.{{ pk_field }} IS NULL)
GROUP BY parent.{{ pk_field }}, parent.path;
```

**Ltree Utilities**:
- `path @> descendant_path` - Containment check
- `path <@ ancestor_path` - Ancestor check
- `nlevel(path)` - Depth calculation

#### 🔧 REFACTOR: Hierarchical Utilities
- Extract ltree path helpers
- Add depth-limited aggregation
- Support custom path fields

#### ✅ QA: Test Hierarchical Aggregations
```bash
# Test location hierarchy
uv run pytest tests/integration/patterns/aggregation/test_hierarchical_count.py::test_location_hierarchy -v

# Test organizational unit hierarchy
uv run pytest tests/integration/patterns/aggregation/test_hierarchical_count.py::test_org_unit_hierarchy -v
```

---

### TDD Cycle 3: Complex Aggregation (Boolean Flags)

#### 🔴 RED: Test Boolean Flag Aggregation
```bash
uv run pytest tests/unit/patterns/aggregation/test_boolean_flags.py -v
```

**Test Case**: `v_current_allocations_by_machine` (9 boolean flags!)

#### 🟢 GREEN: Implement Boolean Flag Aggregation
```yaml
# stdlib/queries/aggregation/boolean_flags.yaml
pattern: aggregation/boolean_flags
description: Derive boolean status flags from aggregations
parameters:
  source_entity: entity_reference
  flags:
    - name: string
      condition: string  # EXISTS/NOT EXISTS/COUNT > 0
```

**Template**:
```jinja2
SELECT
    {{ source_entity.pk_field }},
    {% for flag in flags %}
    ({{ flag.condition }}) AS {{ flag.name }},
    {% endfor %}
    COALESCE(jsonb_agg(
        CASE WHEN {{ filter_condition }} THEN ... END
    ), '[]'::jsonb) AS {{ array_field }}
FROM {{ source_entity.table }} src
LEFT JOIN {{ related_table }} rel ON ...
GROUP BY {{ source_entity.pk_field }};
```

#### 🔧 REFACTOR: Flag Utilities
- Extract EXISTS/NOT EXISTS builders
- Add temporal flag support (current_date, date ranges)
- Optimize boolean expressions

#### ✅ QA: Validate Boolean Flags
```bash
uv run pytest tests/integration/patterns/aggregation/test_boolean_flags.py -v
```

**Deliverables**:
- ✅ Count aggregation pattern
- ✅ Hierarchical count pattern
- ✅ Boolean flag aggregation pattern
- ✅ 12 PrintOptim aggregation examples converted
- ✅ Documentation

---

## Phase 4: Extraction Patterns (Week 8)

**Objective**: Component extractor patterns for efficient LEFT JOINs (8 examples)

### TDD Cycle 1: Component Extractor

#### 🔴 RED: Test Component Extraction
```bash
uv run pytest tests/unit/patterns/extraction/test_component_extractor.py -v
```

**Test Case**: `v_location_coordinates` (NULL filtering)

#### 🟢 GREEN: Implement Component Extractor
```yaml
# stdlib/queries/extraction/component.yaml
pattern: extraction/component
description: Extract non-null components for efficient LEFT JOIN
parameters:
  source_entity: entity_reference
  source_table: string  # Could be different from entity table
  extracted_fields: array  # Fields to extract
  filter_condition: string  # NULL filtering
  purpose: string  # Documentation
```

**Template**:
```jinja2
-- @fraiseql:view
-- @fraiseql:description {{ purpose }}
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ fk_field }} AS {{ pk_field }},
    {% for field in extracted_fields %}
    {{ field }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM {{ source_schema }}.{{ source_table }}
WHERE deleted_at IS NULL
  {% if filter_condition %}
  AND {{ filter_condition }}
  {% endif %};

-- Index for LEFT JOIN performance
CREATE INDEX IF NOT EXISTS idx_{{ name }}_{{ pk_field }}
    ON {{ schema }}.{{ name }}({{ pk_field }});
```

**Usage Example**:
```sql
-- tv_location uses v_location_coordinates
SELECT
    loc.*,
    coords.latitude,
    coords.longitude
FROM tb_location loc
LEFT JOIN v_location_coordinates coords  -- Only non-null coordinates
    ON coords.pk_location = loc.pk_location;
-- Performance: LEFT JOIN only processes rows WHERE lat/lon IS NOT NULL
```

#### 🔧 REFACTOR: Extraction Utilities
- Auto-detect filterable fields (NOT NULL constraints)
- Add multi-field filtering
- Generate usage examples

#### ✅ QA: Validate Extraction Patterns
```bash
uv run pytest tests/integration/patterns/extraction/test_component_extractor.py -v

# Performance test: LEFT JOIN with vs without extraction
uv run pytest tests/performance/test_extraction_performance.py -v
```

---

### TDD Cycle 2: Temporal Extraction

#### 🔴 RED: Test Temporal Filtering
```bash
uv run pytest tests/unit/patterns/extraction/test_temporal_extractor.py -v
```

**Test Case**: `v_current_contract` (active contracts only)

#### 🟢 GREEN: Implement Temporal Extractor
```yaml
# stdlib/queries/extraction/temporal.yaml
pattern: extraction/temporal
description: Extract temporally filtered entities (current, future, historical)
parameters:
  source_entity: entity_reference
  temporal_mode:
    enum: [current, future, historical, date_range]
  date_field_start: string
  date_field_end: string
  reference_date: string  # Default: CURRENT_DATE
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT *
FROM {{ source_entity.table }}
WHERE deleted_at IS NULL
  {% if temporal_mode == 'current' %}
  AND {{ date_field_start }} <= {{ reference_date }}
  AND ({{ date_field_end }} IS NULL OR {{ date_field_end }} >= {{ reference_date }})
  {% elif temporal_mode == 'future' %}
  AND {{ date_field_start }} > {{ reference_date }}
  {% elif temporal_mode == 'historical' %}
  AND {{ date_field_end }} < {{ reference_date }}
  {% endif %};
```

#### 🔧 REFACTOR: Temporal Utilities
- Add daterange() support (PostgreSQL range types)
- Handle timezone-aware dates
- Add date overlap operators

#### ✅ QA: Validate Temporal Patterns
```bash
uv run pytest tests/integration/patterns/extraction/test_temporal_extractor.py -v
```

**Deliverables**:
- ✅ Component extractor pattern
- ✅ Temporal extractor pattern
- ✅ 8 PrintOptim extraction examples converted
- ✅ Performance benchmarks
- ✅ Documentation

---

## Phase 5: Hierarchical Patterns (Week 9)

**Objective**: Tree flattening for frontend tree components (6 examples)

### TDD Cycle 1: Hierarchical Flattener

#### 🔴 RED: Test Tree Flattening
```bash
uv run pytest tests/unit/patterns/hierarchical/test_flattener.py -v
```

**Test Case**: `v_flat_location_for_rust_tree`

#### 🟢 GREEN: Implement Hierarchical Flattener
```yaml
# stdlib/queries/hierarchical/flattener.yaml
pattern: hierarchical/flattener
description: Flatten tree structures for frontend tree components
parameters:
  source_table: string  # Usually tv_* commodity table
  extracted_fields:
    - name: string
      expression: string  # JSONB extraction
  frontend_format:
    enum: [rust_tree, react_tree, generic]
  required_fields:
    - id
    - parent_id
    - label
    - value
```

**Template**:
```jinja2
-- @fraiseql:view
-- @fraiseql:description Flattened {{ source_table }} for {{ frontend_format }} component
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {% for field in extracted_fields %}
    {{ field.expression }} AS {{ field.name }},
    {% endfor %}
    -- Required tree fields
    (data->>'id')::uuid AS id,
    NULLIF(data->'parent'->>'id', '')::uuid AS parent_id,
    data->>'{{ label_field }}' AS label,
    data->>'id' AS value,
    {% if path_field %}
    REPLACE(data->>'{{ path_field }}', '.', '_')::text AS ltree_id,
    {% endif %}
    data  -- Include full data for reference
FROM {{ source_schema }}.{{ source_table }}
WHERE deleted_at IS NULL;

-- Index for parent lookup (tree traversal)
CREATE INDEX IF NOT EXISTS idx_{{ name }}_parent
    ON {{ schema }}.{{ name }}(parent_id)
    WHERE parent_id IS NOT NULL;

-- Index for ltree operations
{% if path_field %}
CREATE INDEX IF NOT EXISTS idx_{{ name }}_ltree
    ON {{ schema }}.{{ name }} USING GIST (ltree_id);
{% endif %}
```

**Frontend Integration**:
```typescript
// Generated TypeScript type
interface LocationTreeNode {
  id: string;
  parent_id: string | null;
  ltree_id: string;
  label: string;
  value: string;
  code: string;
  // ... 15 more fields
}

// GraphQL query
query LocationTree {
  flatLocationForRustTree {
    id
    parentId
    ltreeId
    label
    value
  }
}
```

#### 🔧 REFACTOR: Flattener Utilities
- Auto-detect hierarchical fields from entity definition
- Add depth calculation
- Support custom label/value fields

#### ✅ QA: Validate Flatteners
```bash
uv run pytest tests/integration/patterns/hierarchical/test_flattener.py -v

# Frontend integration test
npm run test:tree-component
```

---

### TDD Cycle 2: Path Expansion

#### 🔴 RED: Test Path Expansion
```bash
uv run pytest tests/unit/patterns/hierarchical/test_path_expander.py -v
```

**Test Case**: Expand ltree path to array of ancestor names

#### 🟢 GREEN: Implement Path Expander
```yaml
# stdlib/queries/hierarchical/path_expander.yaml
pattern: hierarchical/path_expander
description: Expand ltree paths to arrays of ancestor data
parameters:
  source_entity: entity_reference
  path_field: string
  expanded_fields:
    - ancestor_ids
    - ancestor_names
    - breadcrumb_labels
```

**Template**:
```jinja2
WITH expanded AS (
  SELECT
    {{ pk_field }},
    path,
    unnest(string_to_array(path::text, '.'))::integer AS ancestor_id
  FROM {{ source_table }}
),
enriched AS (
  SELECT
    e.{{ pk_field }},
    array_agg(a.{{ name_field }} ORDER BY nlevel(a.path)) AS ancestor_names,
    array_agg(a.{{ pk_field }} ORDER BY nlevel(a.path)) AS ancestor_ids
  FROM expanded e
  JOIN {{ source_table }} a ON a.{{ pk_field }} = e.ancestor_id
  GROUP BY e.{{ pk_field }}
)
SELECT * FROM enriched;
```

#### 🔧 REFACTOR: Path Utilities
- Add depth limiting (ancestors up to N levels)
- Support sibling enumeration
- Add leaf/internal node detection

#### ✅ QA: Validate Path Expansion
```bash
uv run pytest tests/integration/patterns/hierarchical/test_path_expander.py -v
```

**Deliverables**:
- ✅ Hierarchical flattener pattern
- ✅ Path expander pattern
- ✅ 6 PrintOptim hierarchical examples converted
- ✅ Frontend integration examples
- ✅ Documentation

---

## Phase 6: Polymorphic Patterns (Week 10)

**Objective**: Type discrimination for ambiguous PKs (2 examples)

### TDD Cycle 1: Type Resolver

#### 🔴 RED: Test Polymorphic Type Resolution
```bash
uv run pytest tests/unit/patterns/polymorphic/test_type_resolver.py -v
```

**Test Case**: `v_pk_class_resolver` (Product | ContractItem)

#### 🟢 GREEN: Implement Type Resolver
```yaml
# stdlib/queries/polymorphic/type_resolver.yaml
pattern: polymorphic/type_resolver
description: Resolve ambiguous PKs to entity types
parameters:
  discriminator_field: string  # e.g., "class"
  variants:
    - entity: entity_reference
      key_field: string
      class_value: string
  output_key: string  # Unified PK field name
```

**Template**:
```jinja2
-- @fraiseql:view
-- @fraiseql:description Polymorphic type resolver for {{ discriminator_field }}
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
{% for variant in variants %}
SELECT
    {{ variant.key_field }} AS {{ output_key }},
    '{{ variant.class_value }}'::text AS {{ discriminator_field }}
FROM {{ variant.entity.schema }}.{{ variant.entity.table }}
WHERE deleted_at IS NULL
{% if not loop.last %}UNION ALL{% endif %}
{% endfor %};

-- Materialized version for performance
CREATE MATERIALIZED VIEW {{ schema }}.m{{ name }} AS
SELECT * FROM {{ schema }}.{{ name }};

-- Unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_m{{ name }}_pk_class
    ON {{ schema }}.m{{ name }}({{ output_key }}, {{ discriminator_field }});

-- Refresh function
CREATE OR REPLACE FUNCTION {{ schema }}.refresh_m{{ name }}()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY {{ schema }}.m{{ name }};
END;
$$ LANGUAGE plpgsql;
```

**Usage**:
```sql
-- Resolve product_or_item_id to actual entity
SELECT
    poi.product_or_item_id,
    resolver.class,
    CASE resolver.class
      WHEN 'product' THEN p.data
      WHEN 'contract_item' THEN ci.data
    END AS resolved_data
FROM tb_pricing poi
JOIN mv_pk_class_resolver resolver
    ON resolver.pk_value = poi.product_or_item_id
LEFT JOIN v_product p
    ON resolver.class = 'product' AND p.id = resolver.pk_value
LEFT JOIN v_contract_item ci
    ON resolver.class = 'contract_item' AND ci.id = resolver.pk_value;
```

#### 🔧 REFACTOR: Polymorphic Utilities
- Add type validation (ensure variants are exhaustive)
- Support nested discriminators
- Generate TypeScript union types

#### ✅ QA: Validate Type Resolvers
```bash
uv run pytest tests/integration/patterns/polymorphic/test_type_resolver.py -v

# Performance test: Materialized view refresh
uv run pytest tests/performance/test_polymorphic_mv_refresh.py -v
```

---

### TDD Cycle 2: Frontend Integration

#### 🔴 RED: Test TypeScript Type Generation
```bash
uv run pytest tests/unit/frontend/test_polymorphic_types.py -v
```

#### 🟢 GREEN: Generate TypeScript Unions
```typescript
// Generated from polymorphic pattern
type ProductOrItemClass = 'product' | 'contract_item';

interface ProductOrItemResolver {
  pk_value: string;
  class: ProductOrItemClass;
}

type ProductOrItem =
  | { class: 'product'; data: Product }
  | { class: 'contract_item'; data: ContractItem };

// Type guard
function isProduct(item: ProductOrItem): item is { class: 'product'; data: Product } {
  return item.class === 'product';
}
```

#### 🔧 REFACTOR: Type Generation
- Extract to `src/generators/frontend/polymorphic_types_generator.py`
- Add GraphQL union types
- Generate discriminated union utilities

#### ✅ QA: Validate Frontend Types
```bash
npm run type-check
```

**Deliverables**:
- ✅ Polymorphic type resolver pattern
- ✅ Materialized view variant
- ✅ TypeScript type generation
- ✅ 2 PrintOptim polymorphic examples converted
- ✅ Documentation

---

## Phase 7: Wrapper Patterns (Week 11)

**Objective**: Complete result set wrappers for materialized views (4 examples)

### TDD Cycle 1: Complete Set Wrapper

#### 🔴 RED: Test Materialized View Wrapper
```bash
uv run pytest tests/unit/patterns/wrapper/test_complete_set.py -v
```

**Test Case**: `v_count_allocations_by_location_optimized`

#### 🟢 GREEN: Implement Complete Set Wrapper
```yaml
# stdlib/queries/wrapper/complete_set.yaml
pattern: wrapper/complete_set
description: Wrap materialized view to ensure complete result sets (zero-count entities)
parameters:
  materialized_view: string
  base_table: string
  key_field: string
  default_values:
    type: object  # Field -> default value mapping
  ensure_zero_count_entities: boolean
```

**Template**:
```jinja2
-- @fraiseql:view
-- @fraiseql:description Complete result set wrapper for {{ materialized_view }}
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
-- Include all results from materialized view
SELECT * FROM {{ schema }}.{{ materialized_view }}

UNION ALL

-- Include missing entities with default values
SELECT
    base.{{ key_field }},
    {% for field, default in default_values.items() %}
    {{ default }} AS {{ field }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM {{ base_schema }}.{{ base_table }} base
WHERE NOT EXISTS (
    SELECT 1
    FROM {{ schema }}.{{ materialized_view }} mv
    WHERE mv.{{ key_field }} = base.{{ key_field }}
)
AND base.deleted_at IS NULL;

COMMENT ON VIEW {{ schema }}.{{ name }} IS
    'Wraps {{ materialized_view }} to include all {{ base_table }} entities, even those with zero counts';
```

**Performance Characteristics**:
- Materialized view: Fast aggregation lookup
- UNION ALL: Includes missing entities
- NOT EXISTS: Efficient anti-join
- Result: Complete result set without full re-aggregation

#### 🔧 REFACTOR: Wrapper Utilities
- Auto-detect default values from field types
- Add refresh trigger integration
- Support multiple MV sources

#### ✅ QA: Validate Wrappers
```bash
uv run pytest tests/integration/patterns/wrapper/test_complete_set.py -v

# Data completeness test
uv run pytest tests/integration/patterns/wrapper/test_zero_count_inclusion.py -v
```

---

### TDD Cycle 2: Refresh Orchestration

#### 🔴 RED: Test Materialized View Refresh
```bash
uv run pytest tests/unit/patterns/wrapper/test_mv_refresh.py -v
```

#### 🟢 GREEN: Generate Refresh Functions
```sql
-- Auto-generated refresh orchestration
CREATE OR REPLACE FUNCTION {{ schema }}.refresh_{{ mv_name }}()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY {{ schema }}.{{ mv_name }};

  -- Update metadata
  INSERT INTO app.mv_refresh_log (mv_name, refreshed_at, duration_ms)
  VALUES ('{{ mv_name }}', NOW(), ...);
END;
$$ LANGUAGE plpgsql;

-- Trigger on base table changes
CREATE TRIGGER trg_invalidate_{{ mv_name }}
AFTER INSERT OR UPDATE OR DELETE ON {{ base_table }}
FOR EACH STATEMENT
EXECUTE FUNCTION {{ schema }}.invalidate_mv_cache('{{ mv_name }}');
```

#### 🔧 REFACTOR: Refresh Strategy
- Add incremental refresh support
- Implement refresh scheduling
- Create dependency-aware refresh chains

#### ✅ QA: Validate Refresh Orchestration
```bash
uv run pytest tests/integration/patterns/wrapper/test_mv_refresh.py -v
```

**Deliverables**:
- ✅ Complete set wrapper pattern
- ✅ Materialized view refresh orchestration
- ✅ 4 PrintOptim wrapper examples converted
- ✅ Performance benchmarks
- ✅ Documentation

---

## Phase 8: Assembly Patterns (Week 12)

**Objective**: Multi-CTE tree builders for deep hierarchies (2 examples)

### TDD Cycle 1: Tree Builder Foundation

#### 🔴 RED: Test Multi-CTE Assembly
```bash
uv run pytest tests/unit/patterns/assembly/test_tree_builder.py -v
```

**Test Case**: `v_contract_price_tree` (199 lines, 8 CTEs, 4 levels deep)

#### 🟢 GREEN: Implement Tree Builder
```yaml
# stdlib/queries/assembly/tree_builder.yaml
pattern: assembly/tree_builder
description: Build deeply nested hierarchies with multi-CTE composition
parameters:
  root_entity: entity_reference
  hierarchy:
    - level: string  # CTE name
      source: string  # View or table
      group_by: array  # Grouping keys
      child_levels: array  # Nested levels
      array_field: string  # JSONB array field name
  max_depth: integer  # Default: 4
```

**Template** (Simplified):
```jinja2
-- @fraiseql:view
-- @fraiseql:description Complex tree assembly for {{ root_entity }}
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
WITH
  -- CTE 1: Root entities
  {{ hierarchy[0].level }} AS (
    SELECT {{ render_fields(hierarchy[0].fields) }}
    FROM {{ hierarchy[0].source }}
  ),

  -- CTE 2: First child level
  {% for level in hierarchy[0].child_levels %}
  {{ level.level }} AS (
    SELECT
      {{ level.group_by|join(', ') }},
      jsonb_agg(DISTINCT jsonb_build_object(
        {% for field in level.fields %}
        '{{ field.name }}', {{ field.expression }}{% if not loop.last %},{% endif %}
        {% endfor %}
      )) AS {{ level.array_field }}
    FROM {{ level.source }}
    GROUP BY {{ level.group_by|join(', ') }}
  ),
  {% endfor %}

  -- Recursive CTEs for deeper levels...
  {% for level in hierarchy[0].child_levels %}
    {% if level.child_levels %}
    {{ render_child_cte(level) }}
    {% endif %}
  {% endfor %}

-- Final assembly
SELECT
  root.{{ pk_field }},
  jsonb_build_object(
    'id', root.id,
    {% for level in hierarchy[0].child_levels %}
    '{{ level.array_field }}', COALESCE({{ level.level }}.{{ level.array_field }}, '[]'::jsonb){% if not loop.last %},{% endif %}
    {% endfor %}
  ) AS data
FROM {{ hierarchy[0].level }} root
{% for level in hierarchy[0].child_levels %}
LEFT JOIN {{ level.level }}
  ON {{ render_join_condition(level) }}
{% endfor %};
```

**Complexity Handling**:
- **8 CTEs**: Break down into manageable steps
- **DISTINCT aggregation**: Prevent duplicates from multiple JOINs
- **COALESCE**: Handle empty arrays gracefully
- **Nested JSONB**: Build hierarchical structure incrementally

#### 🔧 REFACTOR: Assembly Utilities
- Extract CTE builder utility
- Add JSONB nesting helpers
- Validate hierarchy depth limits

#### ✅ QA: Validate Tree Assembly
```bash
uv run pytest tests/integration/patterns/assembly/test_tree_builder.py -v

# Performance test: Large tree assembly
uv run pytest tests/performance/test_tree_builder_performance.py -v
```

---

### TDD Cycle 2: Simplified Assembly Variant

#### 🔴 RED: Test Simple Subquery Assembly
```bash
uv run pytest tests/unit/patterns/assembly/test_simple_assembly.py -v
```

**Test Case**: `v_contract_with_items` (subquery aggregation)

#### 🟢 GREEN: Implement Simple Assembly
```yaml
# stdlib/queries/assembly/simple_aggregation.yaml
pattern: assembly/simple_aggregation
description: Simple nested aggregation with subquery
parameters:
  parent_entity: entity_reference
  child_entity: entity_reference
  child_array_field: string
  child_fields: array
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
  parent.*,
  (
    SELECT jsonb_agg(jsonb_build_object(
      {% for field in child_fields %}
      '{{ field.name }}', child.{{ field.name }}{% if not loop.last %},{% endif %}
      {% endfor %}
    ))
    FROM {{ child_entity.table }} child
    WHERE child.{{ parent_fk }} = parent.{{ pk_field }}
      AND child.deleted_at IS NULL
  ) AS {{ child_array_field }}
FROM {{ parent_entity.table }} parent
WHERE parent.deleted_at IS NULL;
```

**Use Case**: 1-level nesting (simpler than tree_builder)

#### 🔧 REFACTOR: Assembly Variants
- Create assembly pattern selector (simple vs complex)
- Add depth detection
- Optimize JSONB construction

#### ✅ QA: Validate Simple Assembly
```bash
uv run pytest tests/integration/patterns/assembly/test_simple_assembly.py -v
```

**Deliverables**:
- ✅ Tree builder pattern (complex assembly)
- ✅ Simple aggregation pattern
- ✅ 2 PrintOptim assembly examples converted
- ✅ Performance analysis
- ✅ Documentation

---

## Phase 9: Advanced Pattern Features (Week 13)

**Objective**: Cross-cutting concerns and pattern composition

### TDD Cycle 1: Pattern Composition

#### 🔴 RED: Test Pattern Chaining
```bash
uv run pytest tests/unit/patterns/test_pattern_composition.py -v
```

**Test Case**: Junction → Aggregation → Wrapper chain

#### 🟢 GREEN: Implement Pattern Dependencies
```yaml
# Example: Multi-step pattern composition
views:
  - name: v_financing_condition_by_contract
    pattern: junction/resolver
    config: {...}

  - name: v_count_financing_conditions
    pattern: aggregation/count_aggregation
    depends_on: [v_financing_condition_by_contract]
    config: {...}

  - name: mv_count_financing_conditions
    pattern: wrapper/materialized
    depends_on: [v_count_financing_conditions]
    config: {...}
```

**Dependency Resolution**:
```python
# src/patterns/pattern_composer.py
class PatternComposer:
    def resolve_dependencies(self, patterns: List[Dict]) -> List[Dict]:
        """Topologically sort patterns by dependencies"""
        graph = nx.DiGraph()
        for pattern in patterns:
            graph.add_node(pattern['name'])
            for dep in pattern.get('depends_on', []):
                graph.add_edge(dep, pattern['name'])
        return list(nx.topological_sort(graph))
```

#### 🔧 REFACTOR: Composition Engine
- Add circular dependency detection
- Support conditional pattern inclusion
- Generate dependency diagrams

#### ✅ QA: Validate Pattern Composition
```bash
uv run pytest tests/integration/patterns/test_pattern_composition.py -v
```

---

### TDD Cycle 2: Multi-Tenant Support

#### 🔴 RED: Test Multi-Tenant Patterns
```bash
uv run pytest tests/unit/patterns/test_multi_tenant.py -v
```

**Test Case**: Automatic tenant_id filtering

#### 🟢 GREEN: Add Tenant Awareness
```jinja2
{# All patterns auto-include tenant filtering #}
{% if entity.is_multi_tenant %}
WHERE {{ entity.alias }}.tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid
  AND {{ entity.alias }}.deleted_at IS NULL
{% else %}
WHERE {{ entity.alias }}.deleted_at IS NULL
{% endif %}
```

**RLS Integration**:
```sql
-- Auto-generated RLS policies for pattern views
CREATE POLICY rls_{{ view_name }}_tenant
ON {{ schema }}.{{ view_name }}
FOR SELECT
USING (tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid);
```

#### 🔧 REFACTOR: Tenant Utilities
- Auto-detect multi-tenant entities from schema registry
- Add cross-tenant aggregation support (for admin views)
- Generate tenant isolation tests

#### ✅ QA: Validate Multi-Tenant Patterns
```bash
uv run pytest tests/integration/patterns/test_multi_tenant.py -v
```

---

### TDD Cycle 3: Performance Optimizations

#### 🔴 RED: Test Query Performance
```bash
uv run pytest tests/performance/test_pattern_performance.py -v
```

**Benchmarks**:
- Junction resolver: < 50ms (10k rows)
- Hierarchical aggregation: < 200ms (5k nodes)
- Tree builder: < 500ms (1k entities, 4 levels)

#### 🟢 GREEN: Add Performance Hints
```yaml
# Pattern-level performance configuration
views:
  - name: v_expensive_aggregation
    pattern: aggregation/hierarchical_count
    performance:
      materialized: true  # Convert to MV
      indexes:
        - fields: [pk_location]
        - fields: [path]
          type: gist
      refresh_strategy: on_demand
```

**Generated Optimization**:
```sql
-- Materialized view for expensive query
CREATE MATERIALIZED VIEW {{ schema }}.m{{ name }} AS
SELECT * FROM {{ schema }}.{{ name }};

-- Performance indexes
CREATE INDEX idx_m{{ name }}_pk ON {{ schema }}.m{{ name }}(pk_location);
CREATE INDEX idx_m{{ name }}_path ON {{ schema }}.m{{ name }} USING GIST (path);

-- Analyze for query planner
ANALYZE {{ schema }}.m{{ name }};
```

#### 🔧 REFACTOR: Performance Utilities
- Add EXPLAIN ANALYZE integration
- Auto-suggest materialization for slow views
- Generate performance reports

#### ✅ QA: Validate Performance
```bash
uv run pytest tests/performance/test_pattern_performance.py -v --benchmark
```

**Deliverables**:
- ✅ Pattern composition system
- ✅ Multi-tenant support
- ✅ Performance optimization framework
- ✅ Benchmarking suite
- ✅ Documentation

---

## Phase 10: Documentation & Examples (Week 14 + Week 24)

**Objective**: Comprehensive docs and migration guides for ALL patterns (core + advanced)

**Scope**:
- **Week 14**: Document 7 core patterns (Phases 2-8)
- **Week 24**: Document 4 advanced patterns (Phases 13-16) - Done after implementation

**Total Pattern Documentation**: 11 pattern categories, 59 total patterns

### TDD Cycle 1: Core Pattern Reference Docs (Week 14)

#### 🔴 RED: Documentation Completeness Test
```bash
uv run pytest tests/docs/test_documentation_coverage.py -v
# Expected: FAILED (missing docs for 7 core pattern categories)
```

**Test Coverage - Core Patterns**:
- ✅ Junction patterns (2 variants) - 15 PrintOptim examples
- ✅ Aggregation patterns (3 variants) - 12 PrintOptim examples
- ✅ Extraction patterns (2 variants) - 8 PrintOptim examples
- ✅ Hierarchical patterns (2 variants) - 6 PrintOptim examples
- ✅ Polymorphic patterns (1 variant) - 2 PrintOptim examples
- ✅ Wrapper patterns (1 variant) - 4 PrintOptim examples
- ✅ Assembly patterns (2 variants) - 2 PrintOptim examples
- ✅ Every parameter documented with types and examples
- ✅ Migration guide for PrintOptim patterns

#### 🟢 GREEN: Generate Pattern Docs
```markdown
# docs/patterns/junction/resolver.md

## Junction Resolver Pattern

**Category**: Junction Patterns
**Use Case**: Resolve many-to-many relationships through junction tables
**Complexity**: Medium
**PrintOptim Examples**: 15 views

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_entity` | entity_reference | ✅ | Starting entity in N-to-N relationship |
| `junction_tables` | array | ✅ | Intermediate junction tables |
| `target_entity` | entity_reference | ✅ | Final entity to resolve to |
| `output_fields` | array | ❌ | Fields to include (default: all PKs) |

### Generated SQL

```sql
CREATE OR REPLACE VIEW tenant.v_example AS
SELECT ...
```

### Examples

#### Example 1: Contract → Financing Condition → Model

```yaml
views:
  - name: v_financing_condition_and_model_by_contract
    pattern: junction/resolver
    config:
      source_entity: Contract
      junction_tables:
        - {table: ContractFinancingCondition, left_key: contract_id, right_key: financing_condition_id}
        - {table: FinancingConditionModel, left_key: financing_condition_id, right_key: model_id}
      target_entity: Model
```

### When to Use

✅ Use when:
- Resolving N-to-N relationships
- Need efficient junction table traversal
- Want to expose intermediate junction data

❌ Don't use when:
- Simple 1-to-N relationships (use direct JOIN)
- Need aggregation (use aggregation patterns)
```

#### 🔧 REFACTOR: Documentation Generation
- Auto-generate parameter tables from YAML schema
- Extract examples from tests
- Generate interactive SQL playground links

#### ✅ QA: Validate Documentation
```bash
# All patterns documented
uv run pytest tests/docs/test_documentation_coverage.py -v

# Links valid
uv run pytest tests/docs/test_documentation_links.py -v
```

---

### TDD Cycle 2: Migration Guide

#### 🔴 RED: Migration Example Tests
```bash
uv run pytest tests/docs/test_migration_examples.py -v
```

#### 🟢 GREEN: Create Migration Guide
```markdown
# docs/migration/printoptim_to_patterns.md

## Migrating PrintOptim Views to SpecQL Patterns

### Step 1: Identify Pattern Category

**Decision Tree**:
```
Does the view have N-to-N JOINs?
  ✅ → Junction Pattern

Does it aggregate/count entities?
  ✅ → Aggregation Pattern

Does it filter optional components?
  ✅ → Extraction Pattern

Does it flatten hierarchies?
  ✅ → Hierarchical Pattern

Does it UNION multiple entity types?
  ✅ → Polymorphic Pattern

Does it wrap a materialized view?
  ✅ → Wrapper Pattern

Does it have 4+ CTEs with nesting?
  ✅ → Assembly Pattern
```

### Step 2: Convert to YAML

**Before** (45 lines SQL):
```sql
-- reference_sql/.../v_count_allocations_by_location.sql
CREATE OR REPLACE VIEW tenant.v_count_allocations_by_location AS
SELECT ...
```

**After** (15 lines YAML):
```yaml
# entities/tenant/location.yaml
query_patterns:
  - name: count_allocations_by_location
    pattern: aggregation/hierarchical_count
    config: {...}
```

### Step 3: Validate Equivalence

```bash
# Generate new SQL
specql generate entities/tenant/location.yaml --with-query-patterns

# Compare output
diff reference_sql/.../v_count_allocations_by_location.sql \
     db/schema/02_query_side/tenant/v_count_allocations_by_location.sql

# Test data equivalence
uv run pytest tests/migration/test_view_equivalence.py::test_allocation_counts -v
```

### Migration Checklist

- [ ] Identify pattern category
- [ ] Extract configuration parameters
- [ ] Add to entity YAML
- [ ] Generate SQL
- [ ] Compare with original
- [ ] Test data equivalence
- [ ] Update dependent views
- [ ] Remove manual SQL file
```

#### 🔧 REFACTOR: Migration Utilities
- Create pattern detection CLI tool
- Add SQL → YAML converter
- Generate diff reports

#### ✅ QA: Validate Migration Guide
```bash
# Test migration examples
uv run pytest tests/migration/ -v
```

---

### TDD Cycle 3: Advanced Pattern Documentation (Week 24)

**Note**: This cycle runs AFTER Phase 16 (advanced patterns implementation)

#### 🔴 RED: Advanced Pattern Documentation Test
```bash
uv run pytest tests/docs/test_advanced_pattern_docs.py -v
# Expected: FAILED (missing docs for 4 advanced pattern categories)
```

**Test Coverage - Advanced Patterns**:
- ✅ Temporal patterns (4 variants) - Snapshot, audit trail, SCD Type 2, temporal range
- ✅ Localization patterns (2 variants) - Translated views, locale aggregation
- ✅ Metric patterns (2 variants) - KPI calculator, trend analysis
- ✅ Security patterns (2 variants) - Permission filter, data masking

#### 🟢 GREEN: Generate Advanced Pattern Docs

**Directory Structure**:
```
docs/patterns/
├── core/                           # Core patterns (Week 14)
│   ├── junction/
│   │   ├── resolver.md
│   │   └── aggregated_resolver.md
│   ├── aggregation/
│   │   ├── count_aggregation.md
│   │   ├── hierarchical_count.md
│   │   └── boolean_flags.md
│   ├── extraction/
│   │   ├── component.md
│   │   └── temporal.md
│   ├── hierarchical/
│   │   ├── flattener.md
│   │   └── path_expander.md
│   ├── polymorphic/
│   │   └── type_resolver.md
│   ├── wrapper/
│   │   └── complete_set.md
│   └── assembly/
│       ├── tree_builder.md
│       └── simple_aggregation.md
│
└── advanced/                       # Advanced patterns (Week 24)
    ├── temporal/
    │   ├── snapshot.md
    │   ├── audit_trail.md
    │   ├── scd_type2.md
    │   └── temporal_range.md
    ├── localization/
    │   ├── translated_view.md
    │   └── locale_aggregation.md
    ├── metrics/
    │   ├── kpi_calculator.md
    │   └── trend_analysis.md
    └── security/
        ├── permission_filter.md
        └── data_masking.md
```

**Example Advanced Pattern Doc**:
```markdown
# docs/patterns/advanced/temporal/snapshot.md

## Temporal Snapshot Pattern

**Category**: Temporal Patterns
**Use Case**: Point-in-time queries, version history tracking
**Complexity**: Medium
**Enterprise Feature**: ✅ Yes

### Overview

The temporal snapshot pattern enables querying historical states of entities using PostgreSQL range types (`tsrange`). This pattern is essential for:
- Contract version tracking
- Audit compliance (SOC2, GDPR)
- Historical reporting
- Time-travel queries

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity` | entity_reference | ✅ | - | Entity to snapshot |
| `effective_date_field` | string | ✅ | - | When version became effective |
| `end_date_field` | string | ❌ | NULL | When version was superseded |
| `snapshot_mode` | enum | ❌ | point_in_time | Snapshot retrieval mode |
| `include_validity_range` | boolean | ❌ | true | Include tsrange column |

### Generated SQL Features

- ✅ `tsrange` validity periods with GiST indexing
- ✅ `LEAD()` window function for auto-computed end dates
- ✅ Point-in-time queries using `@>` operator
- ✅ `is_current` flag for active versions
- ✅ Temporal joins with overlapping ranges

### Examples

#### Example 1: Contract Version History

```yaml
views:
  - name: v_contract_snapshot
    pattern: temporal/snapshot
    config:
      entity: Contract
      effective_date_field: effective_date
      end_date_field: superseded_date
      snapshot_mode: full_history
      include_validity_range: true
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_contract_snapshot AS
SELECT
    pk_contract,
    c.*,
    tsrange(effective_date, LEAD(effective_date) OVER (
        PARTITION BY pk_contract ORDER BY effective_date
    ), '[)') AS valid_period,
    superseded_date IS NULL AS is_current
FROM tenant.tb_contract c
ORDER BY pk_contract, effective_date DESC;

CREATE INDEX idx_v_contract_snapshot_temporal
    ON tenant.v_contract_snapshot USING GIST (pk_contract, valid_period);
```

**Query as of date**:
```sql
SELECT * FROM v_contract_snapshot
WHERE pk_contract = 123
  AND valid_period @> '2024-01-15'::date;
```

### When to Use

✅ Use when:
- Tracking entity version history
- Need point-in-time queries
- Audit trail requirements
- Slowly changing dimension (SCD) tracking

❌ Don't use when:
- Only need current state (use base table)
- Simple created_at/updated_at is sufficient
- No historical query requirements

### Related Patterns

- **Audit Trail Pattern** - Complete change history with diffs
- **SCD Type 2 Pattern** - Data warehouse slowly changing dimensions
- **Temporal Range Pattern** - Date range filtering

### Performance Considerations

- GiST indexes on `tsrange` columns: Fast range queries
- Window functions (`LEAD`): Computed at view query time
- Materialized variant: For high-traffic historical queries

### Compliance

- ✅ **GDPR**: Audit trail for data changes
- ✅ **SOC2**: Historical access logging
- ✅ **HIPAA**: Medical record versioning
```

#### 🔧 REFACTOR: Documentation Generator

```python
# src/docs/pattern_doc_generator.py
class PatternDocGenerator:
    """Auto-generate pattern documentation from YAML schemas"""

    def generate_pattern_docs(self, pattern_category: str) -> List[str]:
        """Generate markdown docs for all patterns in category"""
        docs = []

        for pattern in self.registry.get_patterns(pattern_category):
            doc = self._generate_single_pattern_doc(pattern)
            docs.append(doc)

        return docs

    def _generate_single_pattern_doc(self, pattern: Dict) -> str:
        """Generate markdown for single pattern"""
        template = load_template("docs/pattern_doc.md.jinja2")

        return template.render(
            name=pattern['name'],
            description=pattern['description'],
            complexity=pattern['complexity'],
            parameters=pattern['parameters'],
            examples=pattern['examples'],
            use_cases=self._extract_use_cases(pattern),
            related_patterns=self._find_related_patterns(pattern)
        )

    def generate_pattern_index(self) -> str:
        """Generate master pattern index"""
        return f"""
# SpecQL Query Pattern Library

## Pattern Categories

### Core Patterns (7 categories, 49 patterns)
{self._render_category_list('core')}

### Advanced Patterns (4 categories, 10 patterns)
{self._render_category_list('advanced')}

## Quick Pattern Selector

{self._generate_decision_tree()}
"""
```

#### ✅ QA: Validate All Pattern Documentation

```bash
# Test core pattern docs
uv run pytest tests/docs/test_core_pattern_docs.py -v

# Test advanced pattern docs
uv run pytest tests/docs/test_advanced_pattern_docs.py -v

# Validate all links
uv run pytest tests/docs/test_documentation_links.py -v

# Test code examples
uv run pytest tests/docs/test_doc_code_examples.py -v
```

**Deliverables**:
- ✅ Pattern reference documentation (all 11 categories)
- ✅ 59 total pattern docs (49 core + 10 advanced)
- ✅ Migration guide for PrintOptim patterns
- ✅ Advanced pattern best practices (temporal, security, i18n, metrics)
- ✅ 50+ working examples
- ✅ Interactive pattern selector tool
- ✅ Video tutorials (optional)
- ✅ MkDocs integration

---

## Phase 11: Testing & Validation (Week 15 + Week 25)

**Objective**: Comprehensive test coverage and pattern migration validation

**Scope**:
- **Week 15**: Core patterns integration testing (Phases 2-8)
- **Week 25**: Advanced patterns integration testing (Phases 13-16)

### TDD Cycle 1: Core Patterns Integration Testing (Week 15)

#### 🔴 RED: End-to-End Integration Tests
```bash
uv run pytest tests/integration/test_core_patterns_pipeline.py -v
# Expected: Comprehensive E2E tests for 7 core pattern categories
```

**Test Coverage - Core Patterns**:
```python
def test_full_pattern_pipeline():
    """Test: YAML → SQL → Database → Query → Validation"""
    # 1. Generate SQL from pattern YAML
    sql = generate_pattern("entities/location.yaml")

    # 2. Execute against test database
    execute_sql(sql)

    # 3. Query generated view
    results = query("SELECT * FROM v_count_allocations_by_location")

    # 4. Validate correctness
    assert len(results) > 0
    assert all(r['n_direct_allocations'] >= 0 for r in results)
```

#### 🟢 GREEN: Implement Core E2E Tests
```python
# tests/integration/test_core_patterns_pipeline.py
class TestCorePatternsPipeline:
    """E2E tests for all 7 core pattern categories"""

    def test_junction_pattern_e2e(self):
        """Junction: YAML → SQL → DB → Query"""
        pass

    def test_aggregation_pattern_e2e(self):
        """Aggregation: YAML → SQL → DB → Query"""
        pass

    def test_extraction_pattern_e2e(self):
        """Extraction: YAML → SQL → DB → Query"""
        pass

    def test_hierarchical_pattern_e2e(self):
        """Hierarchical: YAML → SQL → DB → Query"""
        pass

    def test_polymorphic_pattern_e2e(self):
        """Polymorphic: YAML → SQL → DB → Query"""
        pass

    def test_wrapper_pattern_e2e(self):
        """Wrapper: YAML → SQL → DB → Query"""
        pass

    def test_assembly_pattern_e2e(self):
        """Assembly: YAML → SQL → DB → Query"""
        pass
```

#### 🔧 REFACTOR: Test Infrastructure
- Create reusable test database fixtures
- Add data seeding utilities
- Generate coverage reports

#### ✅ QA: Verify Core Test Coverage
```bash
uv run pytest --cov=src/patterns --cov=src/generators/query_pattern_generator.py --cov-report=html
# Target: 90%+ coverage for core patterns
```

---

### TDD Cycle 2: Core PrintOptim Migration (Week 15)

#### 🔴 RED: PrintOptim View Equivalence Tests
```bash
uv run pytest tests/migration/printoptim/test_view_equivalence.py -v
```

**Test Strategy**:
```python
def test_view_equivalence(view_name: str):
    """Test that pattern-generated view matches manual SQL view"""
    # Query original view
    original_results = query(f"SELECT * FROM printoptim.{view_name}")

    # Query pattern-generated view
    generated_results = query(f"SELECT * FROM specql.{view_name}")

    # Compare results
    assert len(original_results) == len(generated_results)
    assert original_results == generated_results
```

#### 🟢 GREEN: Migrate 20+ PrintOptim Views
```bash
# Convert junction views
specql migrate reference_sql/.../02444_v_financing_condition_and_model_by_contract.sql

# Convert aggregation views
specql migrate reference_sql/.../02411_v_count_allocations_by_location.sql

# Convert hierarchical views
specql migrate reference_sql/.../02414_v_flat_location_for_rust_tree.sql
```

**Migration Tracker**:
| Category | Total | Migrated | Status |
|----------|-------|----------|--------|
| Junction | 15 | 15 | ✅ |
| Aggregation | 12 | 12 | ✅ |
| Extraction | 8 | 8 | ✅ |
| Hierarchical | 6 | 6 | ✅ |
| Polymorphic | 2 | 2 | ✅ |
| Wrapper | 4 | 4 | ✅ |
| Assembly | 2 | 2 | ✅ |
| **Total** | **49** | **49** | **✅** |

#### 🔧 REFACTOR: Migration Tooling
- Automate SQL → YAML conversion
- Generate migration reports
- Create rollback scripts

#### ✅ QA: Validate PrintOptim Migration
```bash
# All views migrated
uv run pytest tests/migration/printoptim/ -v

# Performance comparison
uv run pytest tests/performance/test_printoptim_comparison.py -v
```

**Deliverables (Week 15 - Core Patterns)**:
- ✅ 90%+ test coverage for core patterns
- ✅ 49 PrintOptim views migrated
- ✅ View equivalence validation
- ✅ Performance benchmarks
- ✅ Migration report

---

### TDD Cycle 3: Advanced Patterns Integration Testing (Week 25)

**Note**: This cycle runs AFTER Phase 16 (advanced patterns implementation)

#### 🔴 RED: Advanced Patterns E2E Tests
```bash
uv run pytest tests/integration/test_advanced_patterns_pipeline.py -v
# Expected: Comprehensive E2E tests for 4 advanced pattern categories
```

#### 🟢 GREEN: Implement Advanced E2E Tests
```python
# tests/integration/test_advanced_patterns_pipeline.py
class TestAdvancedPatternsPipeline:
    """E2E tests for all 4 advanced pattern categories"""

    def test_temporal_snapshot_e2e(self):
        """Temporal Snapshot: YAML → SQL → DB → Point-in-time query"""
        # Test tsrange queries, version history
        pass

    def test_temporal_audit_trail_e2e(self):
        """Audit Trail: YAML → SQL → DB → Change tracking"""
        # Test INSERT/UPDATE/DELETE triggers, audit log queries
        pass

    def test_temporal_scd_type2_e2e(self):
        """SCD Type 2: YAML → SQL → DB → Version management"""
        # Test version creation, current/historical queries
        pass

    def test_localization_e2e(self):
        """Localization: YAML → SQL → DB → Multi-locale queries"""
        # Test fallback logic, locale switching
        pass

    def test_kpi_calculator_e2e(self):
        """KPI Calculator: YAML → SQL → DB → Metric calculations"""
        # Test formula parsing, threshold checks
        pass

    def test_trend_analysis_e2e(self):
        """Trend Analysis: YAML → SQL → DB → Moving averages"""
        # Test MA calculations, trend detection
        pass

    def test_permission_filter_e2e(self):
        """Permission Filter: YAML → SQL → DB → Access control"""
        # Test RLS, ownership checks, role-based filtering
        pass

    def test_data_masking_e2e(self):
        """Data Masking: YAML → SQL → DB → PII protection"""
        # Test partial masking, role-based unmasking
        pass
```

#### 🔧 REFACTOR: Advanced Test Infrastructure
- Add temporal data fixtures (historical versions)
- Create multi-locale test data
- Add user/role test fixtures for security patterns
- Performance benchmarks for KPI calculations

#### ✅ QA: Verify Advanced Test Coverage
```bash
# Advanced patterns test coverage
uv run pytest --cov=src/patterns/temporal --cov=src/patterns/localization \
             --cov=src/patterns/metrics --cov=src/patterns/security \
             --cov-report=html
# Target: 95%+ coverage for advanced patterns

# Security-specific testing
uv run pytest tests/security/ -v

# Compliance testing
uv run pytest tests/compliance/ -v
```

**Deliverables (Week 25 - Advanced Patterns)**:
- ✅ 95%+ test coverage for advanced patterns
- ✅ Security audit (penetration testing for permission filters)
- ✅ Compliance validation (GDPR, SOC2, HIPAA)
- ✅ Performance benchmarks for temporal queries
- ✅ Multi-locale testing
- ✅ Advanced pattern integration report

---

## Phase 12: Productionization & Polish (Week 16 + Week 26)

**Objective**: Production-ready releases with comprehensive documentation

**Scope**:
- **Week 16**: v1.0 Release (Core patterns)
- **Week 26**: v1.1 Release (Advanced patterns)

### TDD Cycle 1: Error Handling & Validation (Week 16)

#### 🔴 RED: Test Error Cases
```bash
uv run pytest tests/unit/patterns/test_error_handling.py -v
```

**Error Cases**:
- Invalid pattern configuration
- Missing required parameters
- Circular dependencies
- Type mismatches
- SQL generation failures

#### 🟢 GREEN: Implement Error Handling
```python
# src/patterns/pattern_validator.py
class PatternValidator:
    def validate(self, config: Dict) -> ValidationResult:
        """Validate pattern configuration with detailed error messages"""
        errors = []

        # Required parameters
        if 'source_entity' not in config:
            errors.append(ValidationError(
                field='source_entity',
                message='Required parameter missing',
                suggestion='Add source_entity: YourEntity'
            ))

        # Entity existence
        if not self.entity_exists(config['source_entity']):
            errors.append(ValidationError(
                field='source_entity',
                message=f"Entity '{config['source_entity']}' not found",
                suggestion='Check entity name spelling or import entity definition'
            ))

        return ValidationResult(errors=errors)
```

**User-Friendly Errors**:
```bash
$ specql generate entities/location.yaml --with-query-patterns

❌ Error in query pattern 'count_allocations_by_location':

   Field: counted_entity
   Problem: Entity 'Alocation' not found
   Suggestion: Did you mean 'Allocation'? Check spelling.

   Location: entities/location.yaml:15
```

#### 🔧 REFACTOR: Error Reporting
- Add suggestions for common mistakes
- Improve error messages with context
- Create error code documentation

#### ✅ QA: Validate Error Handling
```bash
uv run pytest tests/unit/patterns/test_error_handling.py -v
```

---

### TDD Cycle 2: Core Documentation Site (Week 16)

#### 🔴 RED: Documentation Site Build Test
```bash
uv run pytest tests/docs/test_site_build.py -v
```

#### 🟢 GREEN: Build MkDocs Site (v1.0)
```yaml
# mkdocs.yml (v1.0 - Core Patterns)
site_name: SpecQL Query Patterns
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Core Patterns:
    - Junction: patterns/core/junction/index.md
    - Aggregation: patterns/core/aggregation/index.md
    - Extraction: patterns/core/extraction/index.md
    - Hierarchical: patterns/core/hierarchical/index.md
    - Polymorphic: patterns/core/polymorphic/index.md
    - Wrapper: patterns/core/wrapper/index.md
    - Assembly: patterns/core/assembly/index.md
  - Advanced Patterns (Coming Soon): patterns/advanced/index.md
  - Migration Guide: migration/index.md
  - API Reference: api/index.md
```

**Interactive Examples**:
```markdown
# patterns/junction/resolver.md

## Try It Yourself

```yaml
views:
  - name: v_your_junction
    pattern: junction/resolver
    config:
      source_entity: YourEntity  # ← Edit this
      junction_tables:
        - {table: YourJunction, left_key: ..., right_key: ...}
      target_entity: TargetEntity
```

[Generate SQL →](#) [See Full Example →](#)
```

#### 🔧 REFACTOR: Site Polish
- Add search functionality
- Create pattern selector tool
- Add code syntax highlighting

#### ✅ QA: Launch Documentation Site
```bash
mkdocs build
mkdocs serve

# Test navigation
uv run pytest tests/docs/test_navigation.py -v
```

---

### TDD Cycle 3: v1.0 Release Preparation (Week 16)

#### 🔴 RED: Release Checklist Tests
```bash
uv run pytest tests/release/test_v1_0_readiness.py -v
```

**v1.0 Release Checklist (Core Patterns)**:
- [ ] All core pattern tests passing (439 existing + ~200 core = 639 tests)
- [ ] Core pattern documentation complete (7 categories)
- [ ] Migration guide published (PrintOptim → SpecQL)
- [ ] Performance benchmarks run (49 patterns)
- [ ] Breaking changes documented
- [ ] Changelog updated
- [ ] Version bumped to v1.0.0

#### 🟢 GREEN: Finalize v1.0 Release
```bash
# Run full test suite (core patterns)
make test
uv run pytest tests/integration/test_core_patterns_pipeline.py -v

# Generate changelog
git-changelog > CHANGELOG.md

# Bump version
bump2version major  # 0.9.0 → 1.0.0

# Tag release
git tag -a v1.0.0 -m "Query Pattern Library v1.0 - Core Patterns"
```

#### ✅ QA: v1.0 Production Release
```bash
# Final validation
uv run pytest --cov --cov-report=html
make teamA-test teamB-test teamC-test teamD-test teamE-test

# Publish documentation
mkdocs gh-deploy

# Announce release
echo "🎉 SpecQL Query Pattern Library v1.0.0 Released! (Core Patterns)"
```

**v1.0 Deliverables**:
- ✅ 7 core pattern categories (49 patterns)
- ✅ Comprehensive error handling
- ✅ Documentation site published
- ✅ Migration guide complete
- ✅ Community announcement

---

### TDD Cycle 4: v1.1 Release Preparation (Week 26)

**Note**: This cycle runs AFTER Phase 16 (advanced patterns implementation)

#### 🔴 RED: v1.1 Release Checklist Tests
```bash
uv run pytest tests/release/test_v1_1_readiness.py -v
```

**v1.1 Release Checklist (Advanced Patterns)**:
- [ ] All advanced pattern tests passing (~100 new tests)
- [ ] Advanced pattern documentation complete (4 categories)
- [ ] Security audit passed
- [ ] Compliance validation (GDPR, SOC2, HIPAA)
- [ ] Performance benchmarks run (10 advanced patterns)
- [ ] Breaking changes documented
- [ ] Changelog updated
- [ ] Version bumped to v1.1.0

#### 🟢 GREEN: Finalize v1.1 Release
```bash
# Run full test suite (core + advanced)
make test
uv run pytest tests/integration/test_advanced_patterns_pipeline.py -v

# Security audit
uv run pytest tests/security/ -v
uv run pytest tests/compliance/ -v

# Generate changelog
git-changelog > CHANGELOG.md

# Bump version
bump2version minor  # 1.0.0 → 1.1.0

# Tag release
git tag -a v1.1.0 -m "Query Pattern Library v1.1 - Advanced Patterns (Temporal, Localization, Metrics, Security)"
```

#### 🟢 GREEN: Update MkDocs Site (v1.1)
```yaml
# mkdocs.yml (v1.1 - All Patterns)
site_name: SpecQL Query Patterns
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Core Patterns:
    - Junction: patterns/core/junction/index.md
    - Aggregation: patterns/core/aggregation/index.md
    - Extraction: patterns/core/extraction/index.md
    - Hierarchical: patterns/core/hierarchical/index.md
    - Polymorphic: patterns/core/polymorphic/index.md
    - Wrapper: patterns/core/wrapper/index.md
    - Assembly: patterns/core/assembly/index.md
  - Advanced Patterns:  # NEW in v1.1
    - Temporal: patterns/advanced/temporal/index.md
    - Localization: patterns/advanced/localization/index.md
    - Metrics: patterns/advanced/metrics/index.md
    - Security: patterns/advanced/security/index.md
  - Migration Guide: migration/index.md
  - API Reference: api/index.md
  - Compliance: compliance/index.md  # NEW in v1.1
```

#### ✅ QA: v1.1 Production Release
```bash
# Final validation (all patterns)
uv run pytest --cov --cov-report=html
make teamA-test teamB-test teamC-test teamD-test teamE-test

# Security verification
uv run pytest tests/security/ --tb=short

# Publish updated documentation
mkdocs gh-deploy

# Announce release
echo "🎉 SpecQL Query Pattern Library v1.1.0 Released! (Advanced Patterns: Temporal, Localization, Metrics, Security)"
```

**v1.1 Deliverables**:
- ✅ 11 total pattern categories (59 patterns: 49 core + 10 advanced)
- ✅ Enterprise features (temporal, security, i18n, KPIs)
- ✅ Security audit & compliance validation
- ✅ Updated documentation site
- ✅ Community announcement

---

## Combined Release Summary

### v1.0.0 (Week 16) - Core Patterns
- **7 pattern categories**: Junction, Aggregation, Extraction, Hierarchical, Polymorphic, Wrapper, Assembly
- **49 patterns** from PrintOptim production SQL
- **639 tests** passing
- **90%+ code coverage**
- **Complete documentation** for core patterns

### v1.1.0 (Week 26) - Advanced Patterns
- **4 new pattern categories**: Temporal, Localization, Metrics, Security
- **10 advanced patterns** for enterprise use cases
- **739 tests** passing (639 + 100)
- **95%+ code coverage** (all patterns)
- **Enterprise features**: Audit trails, RLS, KPIs, i18n
- **Compliance**: GDPR, SOC2, HIPAA validated

---

## Additional Pattern Ideas

Beyond the 7 core categories from PrintOptim, here are **5 additional pattern categories** that would enhance SpecQL:

### 8. Temporal Patterns (`queries/temporal/`)

**Use Case**: Time-series data, historical tracking, audit trails

**Pattern: `temporal/snapshot`**
```yaml
views:
  - name: v_contract_snapshot_by_date
    pattern: temporal/snapshot
    config:
      entity: Contract
      snapshot_date_field: effective_date
      include_history: true
      retention_period: 7 years
```

**Generated SQL**:
```sql
-- Point-in-time snapshot
CREATE OR REPLACE VIEW v_contract_snapshot_by_date AS
SELECT
  c.*,
  tsrange(c.effective_date, LEAD(c.effective_date) OVER (PARTITION BY c.id ORDER BY c.effective_date), '[)') AS valid_period
FROM tb_contract_history c
WHERE c.deleted_at IS NULL;
```

**PrintOptim Applications**: SCD Type 2 tables, audit history views

---

### 9. Metric Patterns (`queries/metrics/`)

**Use Case**: KPI calculations, dashboard metrics, business intelligence

**Pattern: `metrics/kpi_calculator`**
```yaml
views:
  - name: v_machine_utilization_metrics
    pattern: metrics/kpi_calculator
    config:
      base_entity: Machine
      time_window: 30 days
      metrics:
        - name: utilization_rate
          formula: "COUNT(active_days) / 30.0"
        - name: downtime_hours
          formula: "SUM(EXTRACT(EPOCH FROM downtime_duration) / 3600)"
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW v_machine_utilization_metrics AS
WITH base_data AS (
  SELECT
    m.pk_machine,
    COUNT(DISTINCT a.allocation_date) AS active_days,
    SUM(m.downtime_end - m.downtime_start) AS downtime_duration
  FROM tb_machine m
  LEFT JOIN tb_allocation a ON ...
  WHERE a.allocation_date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY m.pk_machine
)
SELECT
  pk_machine,
  active_days / 30.0 AS utilization_rate,
  EXTRACT(EPOCH FROM downtime_duration) / 3600 AS downtime_hours
FROM base_data;
```

**PrintOptim Applications**: Allocation metrics, machine performance KPIs

---

### 10. Localization Patterns (`queries/localization/`)

**Use Case**: Multi-language views, regional data, translation fallbacks

**Pattern: `localization/translated_view`**
```yaml
views:
  - name: v_product_localized
    pattern: localization/translated_view
    config:
      base_entity: Product
      translatable_fields:
        - name
        - description
        - specifications
      fallback_locale: en_US
      current_locale_source: CURRENT_SETTING('app.current_locale')
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW v_product_localized AS
SELECT
  p.pk_product,
  COALESCE(tl.name, base.name) AS name,
  COALESCE(tl.description, base.description) AS description,
  COALESCE(tl.specifications, base.specifications) AS specifications,
  CURRENT_SETTING('app.current_locale')::text AS locale
FROM tb_product p
JOIN tl_product base ON base.fk_product = p.pk_product AND base.locale = 'en_US'
LEFT JOIN tl_product tl ON tl.fk_product = p.pk_product
  AND tl.locale = CURRENT_SETTING('app.current_locale')::text;
```

**PrintOptim Applications**: Industry names, street types, country names (all have `tl_*` tables)

---

### 11. Security Patterns (`queries/security/`)

**Use Case**: Row-level security, permission filtering, data masking

**Pattern: `security/permission_filter`**
```yaml
views:
  - name: v_contract_accessible_by_user
    pattern: security/permission_filter
    config:
      base_entity: Contract
      permission_checks:
        - type: ownership
          field: created_by
        - type: organizational_hierarchy
          field: organization_id
        - type: role_based
          allowed_roles: [admin, contract_manager]
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW v_contract_accessible_by_user AS
SELECT c.*
FROM tb_contract c
WHERE c.deleted_at IS NULL
  AND (
    -- Ownership check
    c.created_by = CURRENT_SETTING('app.current_user_id')::uuid
    OR
    -- Organizational hierarchy check
    c.organization_id IN (
      SELECT ou.pk_organizational_unit
      FROM tb_organizational_unit ou
      WHERE ou.path <@ (SELECT path FROM tb_user WHERE id = CURRENT_SETTING('app.current_user_id')::uuid)
    )
    OR
    -- Role-based check
    EXISTS (
      SELECT 1 FROM tb_user_role ur
      WHERE ur.user_id = CURRENT_SETTING('app.current_user_id')::uuid
        AND ur.role IN ('admin', 'contract_manager')
    )
  );
```

**PrintOptim Applications**: Multi-tenant isolation, user-scoped data access

---

### 12. Caching Patterns (`queries/caching/`)

**Use Case**: Frequently accessed data, expensive calculations, denormalization

**Pattern: `caching/incremental_materialized_view`**
```yaml
views:
  - name: mv_contract_summary
    pattern: caching/incremental_materialized_view
    config:
      base_view: v_contract_with_items
      refresh_strategy:
        type: incremental
        delta_table: tb_contract
        delta_key: updated_at
        delta_window: 1 hour
      indexes:
        - fields: [pk_contract]
        - fields: [organization_id, status]
```

**Generated SQL**:
```sql
-- Materialized view
CREATE MATERIALIZED VIEW mv_contract_summary AS
SELECT * FROM v_contract_with_items;

-- Incremental refresh function
CREATE OR REPLACE FUNCTION refresh_mv_contract_summary_incremental()
RETURNS void AS $$
BEGIN
  -- Delete stale rows
  DELETE FROM mv_contract_summary
  WHERE pk_contract IN (
    SELECT pk_contract FROM tb_contract
    WHERE updated_at >= NOW() - INTERVAL '1 hour'
  );

  -- Insert updated rows
  INSERT INTO mv_contract_summary
  SELECT * FROM v_contract_with_items
  WHERE pk_contract IN (
    SELECT pk_contract FROM tb_contract
    WHERE updated_at >= NOW() - INTERVAL '1 hour'
  );
END;
$$ LANGUAGE plpgsql;

-- Scheduled refresh
SELECT cron.schedule('refresh_mv_contract_summary', '*/15 * * * *', 'SELECT refresh_mv_contract_summary_incremental()');
```

**PrintOptim Applications**: Dashboard caching, report materialization

---

## Summary: Pattern Category Roadmap

### Core Patterns (v1.0)

| Category | Priority | Week | PrintOptim Examples | Value |
|----------|----------|------|---------------------|-------|
| **Junction** | P0 | 5 | 15 | Core N-to-N resolution |
| **Aggregation** | P0 | 6-7 | 12 | Metrics & KPIs |
| **Extraction** | P1 | 8 | 8 | Performance optimization |
| **Hierarchical** | P1 | 9 | 6 | Tree UI support |
| **Polymorphic** | P1 | 10 | 2 | Type safety |
| **Wrapper** | P1 | 11 | 4 | Complete result sets |
| **Assembly** | P1 | 12 | 2 | Complex hierarchies |

**v1.0 Subtotal**: 7 categories, 49 patterns, Week 16 release

### Advanced Patterns (v1.1)

| Category | Priority | Week | Patterns | Value |
|----------|----------|------|----------|-------|
| **Temporal** | P2 | 17-18 | 4 | Time-series, audit, SCD |
| **Localization** | P2 | 19 | 2 | Multi-language, i18n |
| **Metrics** | P2 | 20-21 | 2 | KPI calculations, BI |
| **Security** | P2 | 22-23 | 2 | RLS, data masking, compliance |

**v1.1 Subtotal**: 4 categories, 10 patterns, Week 26 release

### Total Pattern Library

**Total Phases**: 16 phases (12 core + 4 advanced)
**Total Patterns**: 59 patterns (49 core + 10 advanced)
**Total Categories**: 11 categories
**Total Duration**: 26 weeks (~6 months)

---

## Success Metrics

### v1.0 Quantitative Targets (Core Patterns)
- ✅ **49 patterns** from PrintOptim converted to YAML
- ✅ **80%+ code reduction** (SQL lines → YAML lines)
- ✅ **100% test coverage** for generated SQL
- ✅ **< 100ms** pattern generation time
- ✅ **639 passing tests** (439 existing + 200 core)
- ✅ **90%+ code coverage** for core pattern system

### v1.1 Quantitative Targets (All Patterns)
- ✅ **59 total patterns** (49 core + 10 advanced)
- ✅ **739 passing tests** (439 existing + 200 core + 100 advanced)
- ✅ **95%+ code coverage** for complete pattern system
- ✅ **GDPR/SOC2/HIPAA compliance** validated
- ✅ **Security audit** passed
- ✅ **Enterprise features** production-ready

### Qualitative Targets
- ✅ Documentation complete and comprehensive (59 pattern docs)
- ✅ Migration guide validates with real PrintOptim data
- ✅ Community feedback positive (GitHub stars, issues)
- ✅ Performance benchmarks meet targets
- ✅ Zero breaking changes to existing SpecQL features
- ✅ Enterprise adoption (temporal, security, i18n features)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Pattern complexity too high | Medium | High | Escape hatch for custom SQL, focus on 80% use case |
| Generator performance issues | Low | Medium | Template caching, incremental generation |
| SQL correctness bugs | Medium | High | Comprehensive integration tests, side-by-side validation |
| Adoption resistance | Low | Medium | Dramatic code reduction examples, gradual migration |
| Scope creep | Medium | Medium | Stick to 7 core patterns for v1.0, defer extensions to v1.1 |

---

## Timeline Summary

### Core Patterns (v1.0) - Weeks 1-16

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **Phase 0** | Week 1-2 | Foundation | Pattern registry, junction POC |
| **Phase 1** | Week 3-4 | Infrastructure | Query generator, dependency resolution |
| **Phase 2** | Week 5 | Junction | 15 junction patterns |
| **Phase 3** | Week 6-7 | Aggregation | 12 aggregation patterns |
| **Phase 4** | Week 8 | Extraction | 8 extraction patterns |
| **Phase 5** | Week 9 | Hierarchical | 6 hierarchical patterns |
| **Phase 6** | Week 10 | Polymorphic | 2 polymorphic patterns |
| **Phase 7** | Week 11 | Wrapper | 4 wrapper patterns |
| **Phase 8** | Week 12 | Assembly | 2 assembly patterns |
| **Phase 9** | Week 13 | Advanced Features | Composition, multi-tenant, performance |
| **Phase 10** | Week 14 | Documentation | Core pattern docs, migration guide |
| **Phase 11** | Week 15 | Testing | Integration tests, PrintOptim migration |
| **Phase 12** | Week 16 | **v1.0 Release** | Error handling, docs site, production release |

**v1.0 Total**: 16 weeks (4 months) - **49 patterns**

### Advanced Patterns (v1.1) - Weeks 17-26

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **Phase 13** | Week 17-18 | Temporal | 4 patterns (snapshot, audit, SCD, range) |
| **Phase 14** | Week 19 | Localization | 2 patterns (translated views, aggregation) |
| **Phase 15** | Week 20-21 | Metrics | 2 patterns (KPI calculator, trend analysis) |
| **Phase 16** | Week 22-23 | Security | 2 patterns (permission filter, data masking) |
| **Phase 10** | Week 24 | Documentation | Advanced pattern docs |
| **Phase 11** | Week 25 | Testing | Advanced pattern integration, security audit |
| **Phase 12** | Week 26 | **v1.1 Release** | Compliance validation, docs update, production release |

**v1.1 Total**: 10 weeks (2.5 months) - **10 advanced patterns**

### Combined Timeline

**Grand Total**: 26 weeks (~6 months) - **59 patterns across 11 categories**

**Milestones**:
- **Week 16**: v1.0 Release (Core Patterns)
- **Week 26**: v1.1 Release (Advanced Patterns)

---

## Next Steps

### This Week
1. ✅ Review this implementation plan
2. ✅ Get stakeholder approval
3. ✅ Set up project tracking (GitHub project board)
4. ✅ Create Phase 0 milestone

### Next Month
1. Complete Phase 0-1 (Foundation + Infrastructure)
2. Implement 2-3 core patterns (Junction + Aggregation)
3. Convert 10 PrintOptim examples
4. Draft initial documentation

### Next Quarter
1. Complete all 7 core pattern categories
2. Migrate 49 PrintOptim views
3. Publish documentation site
4. Release v0.10.0

---

**Created**: 2025-11-10
**Updated**: 2025-11-10 (Added advanced patterns documentation & testing phases)
**Author**: Claude (Assistant)
**Status**: Ready for Implementation

**Timeline**:
- **v1.0 (Core Patterns)**: 16 weeks (4 months) - 49 patterns
- **v1.1 (Advanced Patterns)**: +10 weeks (2.5 months) - 10 patterns
- **Total**: 26 weeks (~6 months) - 59 patterns across 11 categories

**Estimated Effort**: 1 developer full-time
**Impact**: Very High - Completes SpecQL's declarative vision with production-validated patterns + enterprise features 🚀

**Releases**:
- ✅ **v1.0.0** (Week 16): Core patterns (junction, aggregation, extraction, hierarchical, polymorphic, wrapper, assembly)
- ✅ **v1.1.0** (Week 26): Advanced patterns (temporal, localization, metrics, security)
