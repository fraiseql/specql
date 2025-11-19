# SpecQL Pattern Implementation Plan for PrintOptim Migration

**Date**: 2025-11-17
**Goal**: Implement reusable patterns to close PrintOptim migration gaps
**Target**: 95%+ automation (from 82% baseline)
**Estimated Effort**: 3-4 weeks development

---

## 🎯 Executive Summary

Instead of extending SpecQL core with new DSL syntax, we can **implement most advanced features as reusable patterns** in `stdlib/`. This approach:

✅ **Faster to implement** - Patterns are YAML templates, not code changes
✅ **Easier to maintain** - No AST changes, parser updates, or generator refactoring
✅ **User-friendly** - Patterns are composable and self-documenting
✅ **Proven architecture** - Existing state machine patterns work well

**3 New Pattern Categories**:
1. **Temporal Patterns** - DATERANGE, SCD, non-overlapping constraints
2. **Validation Patterns** - Recursive dependencies, complex rules
3. **Schema Patterns** - Materialized aggregate views, computed columns

---

## 📦 New Patterns to Implement

### **Category 1: Temporal Patterns** (`stdlib/actions/temporal/`)

#### 1.1 Non-Overlapping Date Range Pattern ✅ DESIGNED
**File**: `stdlib/actions/temporal/non_overlapping_daterange.yaml`
**Status**: Ready to implement
**Effort**: 3-4 days

**What It Does**:
- Generates DATERANGE computed column
- Creates GIST index for overlap detection
- Adds EXCLUSION constraint (database-level enforcement)
- Provides validation helper function (application-level checks)
- Supports multiple scope fields (e.g., per-machine, per-location)
- Handles adjacent ranges (end_date = next start_date)
- Soft delete awareness (deleted_at IS NULL)

**Usage Example**:
```yaml
entity: Allocation
schema: scd
fields:
  machine: ref(Machine)
  location: ref(Location)
  start_date: date
  end_date: date?

actions:
  - name: create_allocation
    pattern: temporal_non_overlapping_daterange
    parameters:
      scope_fields: [fk_machine]
      start_date_field: start_date
      end_date_field: end_date
      check_mode: strict  # Error on overlap
    steps:
      - insert: Allocation
```

**Generated Assets**:
1. Schema extension (DATERANGE column + GIST index)
2. EXCLUSION constraint DDL
3. Validation helper function with overlap detection
4. Detailed violation reporting (JSONB)

**PrintOptim Impact**: ✅ **15 SCD tables** (allocation, contract periods, assignments)

---

#### 1.2 SCD Type 2 Helper Pattern
**File**: `stdlib/actions/temporal/scd_type2_helper.yaml`
**Status**: To design
**Effort**: 2-3 days

**What It Does**:
- Auto-close previous record (set end_date)
- Insert new version with start_date
- Maintain version numbers
- Update is_current flags
- Refresh projections with temporal views

**Usage Example**:
```yaml
entity: Allocation
actions:
  - name: update_allocation_location
    pattern: scd_type2_helper
    parameters:
      effective_date_field: start_date
      end_date_field: end_date
      version_field: version
      current_flag_field: is_current
    steps:
      # Pattern handles versioning automatically
      - update_scd: Allocation
        set:
          location: $input.new_location
        effective_date: $input.effective_date
```

**PrintOptim Impact**: ✅ **10-12 tables** with temporal versioning

---

### **Category 2: Validation Patterns** (`stdlib/actions/validation/`)

#### 2.1 Recursive Dependency Validator ✅ DESIGNED
**File**: `stdlib/actions/validation/recursive_dependency_validator.yaml`
**Status**: Ready to implement
**Effort**: 4-5 days

**What It Does**:
- Resolves transitive REQUIRES dependencies (recursive CTEs)
- Validates REQUIRES_ONE_OF (OR groups)
- Detects CONFLICTS_WITH (mutual exclusions)
- Finds circular dependencies with path tracking
- Enforces category limits (max items per category)
- Template inheritance support (model-specific → generic)

**Usage Example**:
```yaml
entity: ProductConfiguration
schema: catalog
actions:
  - name: validate_configuration
    pattern: recursive_dependency_validator
    parameters:
      dependency_table: catalog.tb_product_dependency
      parent_field: fk_product
      child_field: fk_required_product
      max_depth: 8
      validation_rules:
        - type: transitive_requires
        - type: requires_one_of
        - type: conflicts_with
        - type: circular_dependency
        - type: category_limit
          limit_source: "(SELECT max_accessories FROM ...)"
    steps:
      - insert: ProductConfiguration
```

**Generated Assets**:
1. Recursive CTE validation function
2. Violation reporting (JSONB with details)
3. Resolved dependency tree (for client display)
4. Performance-optimized with path tracking

**PrintOptim Impact**: ✅ **5-7 validation functions** (product config, permissions, BOM)

---

#### 2.2 Template Inheritance Validator
**File**: `stdlib/actions/validation/template_inheritance_validator.yaml`
**Status**: To design
**Effort**: 2-3 days

**What It Does**:
- Resolve configuration templates (model-specific → parent → generic)
- Merge limits/rules with priority ordering
- Handle unlimited (-1) overrides
- Cache resolved templates

**Usage Example**:
```yaml
actions:
  - name: get_category_limit
    pattern: template_inheritance_validator
    parameters:
      template_hierarchy:
        - table: tb_model_category_limit
          scope: model_id
        - table: tb_category_limit
          scope: category_id
        - default: -1  # Unlimited
      limit_field: max_accessories
```

**PrintOptim Impact**: ✅ **3-4 templated validation rules**

---

### **Category 3: Schema Patterns** (`stdlib/schema/`)

#### 3.1 Aggregate Materialized View Pattern ✅ DESIGNED
**File**: `stdlib/schema/aggregate_view.yaml`
**Status**: Ready to implement
**Effort**: 5-6 days

**What It Does**:
- Generates true PostgreSQL materialized views
- Supports FILTER clauses for conditional aggregates
- Dependency-ordered refresh functions
- Multiple refresh modes (manual, auto, incremental)
- Indexes on materialized views
- FraiseQL annotations for GraphQL

**Usage Example**:
```yaml
entity: AllocationStatsByOrgUnit
type: aggregate_view
schema: query

aggregate_from: Allocation
pattern: aggregate_view

group_by:
  - organizational_unit.id
  - organizational_unit.name
  - organizational_unit.path

aggregates:
  - name: current_allocations
    function: count
    filter: "end_date IS NULL OR end_date >= CURRENT_DATE"

  - name: past_allocations
    function: count
    filter: "end_date < CURRENT_DATE"

  - name: total_machines
    function: count_distinct
    field: machine_id

refresh: manual  # or auto, incremental
dependencies: [mv_organization]

indexes:
  - fields: [organizational_unit_id]
  - fields: [org_path]
    using: gist
```

**Generated Assets**:
1. CREATE MATERIALIZED VIEW DDL
2. Refresh function with dependencies
3. Indexes on MV
4. Refresh logging/monitoring
5. Incremental refresh for large datasets

**PrintOptim Impact**: ✅ **22 aggregate views** (stats, analytics, reporting)

---

#### 3.2 Computed Column Pattern
**File**: `stdlib/schema/computed_column.yaml`
**Status**: To design
**Effort**: 2 days

**What It Does**:
- Add GENERATED ALWAYS AS columns
- Support STORED vs. VIRTUAL
- Auto-index computed columns
- Handle dependencies on other columns

**Usage Example**:
```yaml
entity: Allocation
fields:
  start_date: date
  end_date: date?

  # Computed field
  allocation_period:
    type: daterange
    computed: true
    expression: "daterange(start_date, end_date, '[]')"
    stored: true
    index: gist
```

**PrintOptim Impact**: ✅ **20-30 computed columns** (flags, ranges, paths)

---

## 🏗️ Implementation Roadmap

### **Week 1: Temporal Patterns**
**Days 1-4**: Non-overlapping DATERANGE pattern
- [ ] Pattern YAML template (Jinja2)
- [ ] Schema extension generator (DATERANGE, GIST, EXCLUSION)
- [ ] Validation helper function
- [ ] Test suite (15+ test cases)
- [ ] Documentation + examples

**Days 5-7**: SCD Type 2 helper pattern
- [ ] Pattern YAML template
- [ ] Version management logic
- [ ] is_current flag maintenance
- [ ] Test suite (10+ test cases)

**Deliverable**: Temporal pattern library for SCD

---

### **Week 2: Validation Patterns**
**Days 1-5**: Recursive dependency validator
- [ ] Pattern YAML with recursive CTEs
- [ ] Transitive REQUIRES resolution
- [ ] REQUIRES_ONE_OF logic
- [ ] Circular dependency detection
- [ ] Category limit enforcement
- [ ] Test suite (20+ test cases)
- [ ] Performance benchmarking

**Days 6-7**: Template inheritance validator
- [ ] Pattern YAML
- [ ] Hierarchy resolution
- [ ] Merge strategy
- [ ] Test suite (8+ test cases)

**Deliverable**: Complex validation pattern library

---

### **Week 3: Schema Patterns**
**Days 1-6**: Aggregate materialized view pattern
- [ ] Pattern YAML with FILTER support
- [ ] Refresh orchestration
- [ ] Dependency ordering
- [ ] Manual/auto/incremental modes
- [ ] Test suite (15+ test cases)
- [ ] Performance testing

**Day 7**: Computed column pattern
- [ ] Pattern YAML
- [ ] GENERATED ALWAYS support
- [ ] Index generation
- [ ] Test suite (10+ test cases)

**Deliverable**: Schema pattern library

---

### **Week 4: Integration & Testing**
**Days 1-3**: PrintOptim migration testing
- [ ] Apply patterns to 245 PrintOptim tables
- [ ] Measure auto-migration rate
- [ ] Identify remaining gaps
- [ ] Performance benchmarking

**Days 4-5**: Documentation
- [ ] Pattern usage guide
- [ ] Migration case study
- [ ] Video walkthrough
- [ ] API reference

**Days 6-7**: Polish & release
- [ ] Code review
- [ ] Edge case handling
- [ ] Release v1.3.0 with patterns

**Deliverable**: Production-ready pattern library

---

## 🧪 Testing Strategy

### **Unit Tests** (stdlib/tests/patterns/)
```bash
tests/unit/patterns/
├── temporal/
│   ├── test_non_overlapping_daterange.py
│   └── test_scd_type2_helper.py
├── validation/
│   ├── test_recursive_dependency_validator.py
│   └── test_template_inheritance.py
└── schema/
    ├── test_aggregate_view.py
    └── test_computed_column.py
```

**Coverage Target**: 90%+ for all patterns

---

### **Integration Tests** (tests/integration/patterns/)
```bash
tests/integration/patterns/
├── test_printoptim_allocation_e2e.py  # Full SCD workflow
├── test_product_configuration_e2e.py  # Recursive validation
└── test_aggregate_refresh_e2e.py      # MV refresh orchestration
```

**Test Scenarios**:
1. Create overlapping allocations (should fail)
2. Create adjacent allocations (should succeed)
3. Resolve complex product dependencies
4. Detect circular dependencies
5. Refresh MV with dependencies
6. Incremental MV refresh

---

### **Performance Benchmarks**
```python
# Benchmark recursive validation
- 100 products, 500 dependencies, depth 8: < 100ms
- Circular detection with 1000 nodes: < 200ms

# Benchmark aggregate MV refresh
- 1M allocation records: < 5s (full refresh)
- 10K changed records: < 500ms (incremental)

# Benchmark overlap detection
- 100K allocations, 10K machines: < 50ms per check
```

---

## 📊 Impact Analysis

### **Before Patterns** (Current State)
- Auto-migration: 82%
- Manual work: 120-190 hours
- Coverage: 143/174 tables

### **After Patterns** (Projected)
- Auto-migration: **95%+**
- Manual work: **20-40 hours** (83% reduction!)
- Coverage: **165+/174 tables**

### **ROI Calculation**
| Metric | Value |
|--------|-------|
| Development effort | 80-100 hours (4 weeks) |
| Time saved per migration | 80-150 hours |
| Break-even | **1 enterprise migration** |
| Long-term value | Reusable across all projects |

---

## 🎯 Pattern Categories Summary

### **✅ Fully Designed** (Ready to implement)
1. **Temporal: Non-overlapping DATERANGE** - 15 tables
2. **Validation: Recursive dependency validator** - 5-7 functions
3. **Schema: Aggregate materialized view** - 22 views

**Total Coverage**: ~45 tables/views/functions (26% of manual work)

### **⏳ To Design** (Additional patterns)
4. **Temporal: SCD Type 2 helper** - 10-12 tables
5. **Validation: Template inheritance** - 3-4 rules
6. **Schema: Computed columns** - 20-30 fields

**Total Coverage**: ~40 additional assets (23% of manual work)

### **Combined Impact**: **49% automation** of previously manual work

---

## 🔄 Pattern Development Workflow

### **1. Design Phase**
```yaml
# Create pattern YAML in stdlib/
pattern: pattern_name
version: 1.0
description: "..."
author: SpecQL Team

parameters:
  - name: param1
    type: string
    required: true

template: |
  steps:
    # Jinja2 template logic
```

### **2. Test Phase**
```python
# Create test in tests/unit/patterns/
def test_pattern_basic():
    pattern = load_pattern('pattern_name')
    result = apply_pattern(pattern, entity, params)
    assert result.generated_sql contains expected_sql
```

### **3. Integration Phase**
```python
# Apply to real entity
entity = EntityDefinition(...)
entity.actions.append({
    'name': 'action_name',
    'pattern': 'pattern_name',
    'parameters': {...}
})
generated_sql = generate_action(entity, action)
```

### **4. Documentation Phase**
```markdown
# Add to docs/patterns/
- Pattern description
- Parameters reference
- Usage examples
- Generated code samples
```

---

## 🚀 Rollout Strategy

### **Phase 1: Core Temporal Patterns** (Week 1)
**Target**: SCD allocations, contract periods
**Risk**: Low (well-understood problem domain)
**Users**: PrintOptim + 2-3 test projects

### **Phase 2: Validation Patterns** (Week 2)
**Target**: Product configurations, permissions
**Risk**: Medium (complex recursive logic)
**Users**: PrintOptim + manufacturing projects

### **Phase 3: Schema Patterns** (Week 3)
**Target**: Analytics aggregations, reporting
**Risk**: Low (similar to existing tv_ system)
**Users**: All projects with analytics needs

### **Phase 4: Production Release** (Week 4)
**Target**: General availability
**Risk**: Low (fully tested)
**Users**: All SpecQL users

---

## 📚 Documentation Deliverables

### **1. Pattern Reference Guide**
```markdown
# SpecQL Pattern Library

## Temporal Patterns
- non_overlapping_daterange
- scd_type2_helper

## Validation Patterns
- recursive_dependency_validator
- template_inheritance_validator

## Schema Patterns
- aggregate_view
- computed_column
```

### **2. Migration Guide**
```markdown
# Migrating Complex PostgreSQL Schemas to SpecQL

## Advanced Features via Patterns
- SCD (Slowly Changing Dimensions)
- Recursive validation
- Aggregate materialized views
- Temporal constraints
```

### **3. PrintOptim Case Study**
```markdown
# Case Study: PrintOptim Migration

## Challenge
- 245 tables, 457 functions, 22 materialized views
- Complex SCD patterns, recursive validation
- 120-190 hours estimated manual work

## Solution
- SpecQL patterns for temporal, validation, schema
- 95% auto-migration rate
- 20-40 hours manual work (83% reduction)

## Results
- 4 weeks development investment
- Reusable across all enterprise migrations
- Break-even after 1 migration
```

---

## ✅ Success Criteria

### **Development Phase**
- [ ] All 6 patterns implemented
- [ ] 90%+ test coverage
- [ ] Performance benchmarks met
- [ ] Documentation complete

### **Integration Phase**
- [ ] PrintOptim migration achieves 95%+ automation
- [ ] Manual work reduced to 20-40 hours
- [ ] No performance regressions
- [ ] Clean SQL generation

### **Production Phase**
- [ ] Pattern library released in v1.3.0
- [ ] Migration guide published
- [ ] Video tutorials created
- [ ] Community feedback positive

---

## 🎓 Next Steps

### **Immediate** (This Week)
1. ✅ Review pattern designs with team
2. ✅ Finalize parameter schemas
3. ✅ Set up pattern test infrastructure
4. 🚀 Begin Week 1 implementation (temporal patterns)

### **Short-Term** (Next 4 Weeks)
1. Implement all 6 core patterns
2. Test against PrintOptim schema
3. Measure automation improvements
4. Document patterns + examples

### **Long-Term** (Next Quarter)
1. Expand pattern library based on user needs
2. Add pattern composition (patterns calling patterns)
3. Visual pattern builder (UI tool)
4. Pattern marketplace (community contributions)

---

**Assessment Created By**: Claude Code (Sonnet 4.5)
**Pattern Design Confidence**: High (based on existing pattern architecture)
**Implementation Risk**: Low (leverages proven Jinja2 templating)
**Expected Timeline**: 4 weeks to production-ready
