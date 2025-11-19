# Quick Start: Implementing Your First SpecQL Pattern

**Goal**: Implement the `non_overlapping_daterange` pattern in 3-4 days
**Difficulty**: Medium (requires PostgreSQL knowledge)
**Prerequisites**: Understanding of SpecQL action patterns, recursive CTEs, GIST indexes

---

## 📋 Pattern Implementation Checklist

### **Day 1: Pattern Design & Schema Extensions**
- [ ] Create pattern YAML file
- [ ] Define parameters schema
- [ ] Design schema extension template (DATERANGE column)
- [ ] Design EXCLUSION constraint DDL
- [ ] Write initial Jinja2 template

### **Day 2: Validation Helper Function**
- [ ] Design overlap detection query
- [ ] Implement recursive CTE for overlap detection
- [ ] Add adjacent range handling
- [ ] Add violation reporting (JSONB)
- [ ] Test function in isolation

### **Day 3: Action Integration & Testing**
- [ ] Integrate pattern with action steps
- [ ] Write unit tests (15+ cases)
- [ ] Write integration tests (3-5 scenarios)
- [ ] Performance benchmarking
- [ ] Edge case handling

### **Day 4: Documentation & Examples**
- [ ] Write pattern reference docs
- [ ] Create 3-5 usage examples
- [ ] Document generated SQL
- [ ] Add to pattern registry
- [ ] Create PR for review

---

## 🏗️ Step-by-Step Implementation Guide

### **Step 1: Create Pattern File Structure**

```bash
# Create pattern directory
mkdir -p stdlib/actions/temporal

# Create pattern YAML
touch stdlib/actions/temporal/non_overlapping_daterange.yaml

# Create test directory
mkdir -p tests/unit/patterns/temporal

# Create test file
touch tests/unit/patterns/temporal/test_non_overlapping_daterange.py
```

---

### **Step 2: Define Pattern Header** (15 minutes)

```yaml
# stdlib/actions/temporal/non_overlapping_daterange.yaml

pattern: temporal_non_overlapping_daterange
version: 1.0
description: "Temporal constraint pattern for non-overlapping date ranges (SCD Type 2)"
author: SpecQL Team

parameters:
  - name: scope_fields
    type: array<string>
    required: true
    description: "Fields that define the scope (e.g., machine_id for non-overlapping allocations per machine)"

  - name: start_date_field
    type: string
    required: true
    default: start_date
    description: "Start date field name"

  - name: end_date_field
    type: string
    required: true
    default: end_date
    description: "End date field name (nullable for open-ended ranges)"

  - name: check_mode
    type: string
    required: false
    default: strict
    description: "Validation mode: strict (error on overlap) or warning (return overlap info)"

  - name: allow_adjacent
    type: boolean
    required: false
    default: true
    description: "Allow adjacent ranges (end_date = start_date of next)"
```

---

### **Step 3: Schema Extensions Template** (1-2 hours)

```yaml
schema_extensions:
  # Add computed DATERANGE column to tb_ table
  computed_columns:
    - name: "{{ start_date_field }}_{{ end_date_field }}_range"
      type: daterange
      expression: "daterange({{ start_date_field }}, {{ end_date_field }}, '[]')"
      stored: true
      comment: "Computed daterange for overlap detection"

  # Add GIST index on daterange
  indexes:
    - name: "idx_tb_{{ entity.name | lower }}_daterange"
      fields: ["{{ start_date_field }}_{{ end_date_field }}_range"]
      using: gist
      comment: "GIST index for efficient overlap detection"

  # Add exclusion constraint (applied during schema generation)
  exclusion_constraints:
    - name: "excl_{{ entity.name | lower }}_no_overlap"
      using: gist
      columns:
        {% for field in scope_fields %}
        - field: "{{ field }}"
          operator: "="
        {% endfor %}
        - field: "{{ start_date_field }}_{{ end_date_field }}_range"
          operator: "&&"
      condition: "deleted_at IS NULL"
      comment: "Prevent overlapping date ranges within same scope"
```

**Test**: Verify schema extension generates correct DDL
```python
def test_schema_extension_ddl():
    pattern = load_pattern('temporal_non_overlapping_daterange')
    entity = EntityDefinition(name='Allocation', schema='scd', fields={...})
    params = {'scope_fields': ['fk_machine'], 'start_date_field': 'start_date', 'end_date_field': 'end_date'}

    generated_ddl = apply_schema_extensions(pattern, entity, params)

    assert 'DATERANGE GENERATED ALWAYS AS' in generated_ddl
    assert 'USING GIST' in generated_ddl
    assert 'EXCLUDE USING GIST' in generated_ddl
```

---

### **Step 4: Validation Helper Function** (3-4 hours)

```yaml
validation_helper: |
  -- Function to check for overlaps before insert/update
  CREATE OR REPLACE FUNCTION {{ entity.schema }}.check_{{ entity.name | lower }}_daterange_overlap(
    {% for field in scope_fields %}
    p_{{ field }} {{ field_types[field] }},
    {% endfor %}
    p_start_date DATE,
    p_end_date DATE,
    p_exclude_pk INTEGER DEFAULT NULL
  )
  RETURNS TABLE(
    has_overlap BOOLEAN,
    overlap_count INTEGER,
    overlapping_ranges JSONB
  ) AS $$
  DECLARE
    v_overlap_count INTEGER;
    v_overlapping JSONB;
  BEGIN
    -- Build overlap query with FILTER for overlap types
    SELECT
      COUNT(*) > 0,
      COUNT(*)::INTEGER,
      jsonb_agg(jsonb_build_object(
        'id', id,
        'identifier', identifier,
        'start_date', {{ start_date_field }},
        'end_date', {{ end_date_field }},
        'overlap_type',
          CASE
            WHEN {{ start_date_field }} <= p_start_date AND ({{ end_date_field }} IS NULL OR {{ end_date_field }} >= p_end_date) THEN 'contains'
            WHEN {{ start_date_field }} >= p_start_date AND (p_end_date IS NULL OR {{ end_date_field }} <= p_end_date) THEN 'contained'
            WHEN {{ start_date_field }} < p_start_date AND {{ end_date_field }} > p_start_date THEN 'overlaps_start'
            WHEN {{ start_date_field }} < p_end_date AND ({{ end_date_field }} IS NULL OR {{ end_date_field }} > p_end_date) THEN 'overlaps_end'
            {% if allow_adjacent %}
            WHEN {{ end_date_field }} = p_start_date OR {{ start_date_field }} = p_end_date THEN 'adjacent'
            {% endif %}
            ELSE 'unknown'
          END
      ))
    INTO has_overlap, overlap_count, overlapping_ranges
    FROM {{ entity.schema }}.tb_{{ entity.name | lower }}
    WHERE deleted_at IS NULL
      {% for field in scope_fields %}
      AND {{ field }} = p_{{ field }}
      {% endfor %}
      {% if allow_adjacent %}
      AND daterange({{ start_date_field }}, {{ end_date_field }}, '[]') && daterange(p_start_date, p_end_date, '[]')
      AND NOT ({{ end_date_field }} = p_start_date OR {{ start_date_field }} = p_end_date)
      {% else %}
      AND daterange({{ start_date_field }}, {{ end_date_field }}, '[]') && daterange(p_start_date, p_end_date, '[]')
      {% endif %}
      AND (p_exclude_pk IS NULL OR pk_{{ entity.name | lower }} != p_exclude_pk);

    RETURN QUERY SELECT has_overlap, overlap_count, overlapping_ranges;
  END;
  $$ LANGUAGE plpgsql STABLE;
```

**Test**: Verify overlap detection logic
```python
def test_overlap_detection():
    # Setup: Create allocation table with pattern
    db.execute("CREATE TABLE scd.tb_allocation (...)")
    db.execute(pattern.validation_helper)

    # Insert test data
    db.execute("INSERT INTO scd.tb_allocation VALUES (1, 1, '2024-01-01', '2024-06-30')")

    # Test 1: Overlapping range
    result = db.query("SELECT * FROM scd.check_allocation_daterange_overlap(1, '2024-03-01', '2024-09-30', NULL)")
    assert result.has_overlap == True
    assert result.overlap_count == 1
    assert result.overlapping_ranges[0]['overlap_type'] == 'overlaps_end'

    # Test 2: Adjacent range (should NOT overlap if allow_adjacent=true)
    result = db.query("SELECT * FROM scd.check_allocation_daterange_overlap(1, '2024-07-01', '2024-12-31', NULL)")
    assert result.has_overlap == False  # Adjacent, not overlapping

    # Test 3: Non-overlapping range
    result = db.query("SELECT * FROM scd.check_allocation_daterange_overlap(1, '2024-08-01', '2024-12-31', NULL)")
    assert result.has_overlap == False
```

---

### **Step 5: Action Integration Template** (2-3 hours)

```yaml
template: |
  steps:
    # Validate no overlapping ranges
    - raw_sql: "
        DECLARE
          v_overlap_check RECORD;
        BEGIN
          -- Check for overlaps
          SELECT * INTO v_overlap_check
          FROM {{ entity.schema }}.check_{{ entity.name | lower }}_daterange_overlap(
            {% for field in scope_fields %}
            input_data.{{ field }},
            {% endfor %}
            input_data.{{ start_date_field }},
            input_data.{{ end_date_field }},
            NULL  -- Exclude PK for updates
          );

          {% if check_mode == 'strict' %}
          -- Strict mode: Error on any overlap
          IF v_overlap_check.has_overlap THEN
            RETURN app.log_and_return_mutation(
              auth_tenant_id, auth_user_id,
              '{{ entity.name | lower }}', NULL,
              'NOOP', 'validation:daterange_overlap',
              ARRAY[]::TEXT[],
              format('Date range overlaps with %s existing record(s)', v_overlap_check.overlap_count),
              NULL, NULL,
              jsonb_build_object(
                'overlap_count', v_overlap_check.overlap_count,
                'overlapping_ranges', v_overlap_check.overlapping_ranges,
                'requested_range', jsonb_build_object(
                  'start_date', input_data.{{ start_date_field }},
                  'end_date', input_data.{{ end_date_field }}
                )
              )
            );
          END IF;
          {% else %}
          -- Warning mode: Return overlap info in metadata
          IF v_overlap_check.has_overlap THEN
            v_warnings := v_warnings || jsonb_build_object(
              'type', 'daterange_overlap',
              'message', format('%s overlapping range(s) detected', v_overlap_check.overlap_count),
              'details', v_overlap_check.overlapping_ranges
            );
          END IF;
          {% endif %}
        END;
        "
```

**Test**: Verify action integration
```python
def test_action_integration():
    # Setup: Entity with pattern action
    entity = EntityDefinition(
        name='Allocation',
        schema='scd',
        fields={
            'machine': FieldDefinition(type_name='ref(Machine)'),
            'start_date': FieldDefinition(type_name='date'),
            'end_date': FieldDefinition(type_name='date?'),
        },
        actions=[{
            'name': 'create_allocation',
            'pattern': 'temporal_non_overlapping_daterange',
            'parameters': {
                'scope_fields': ['fk_machine'],
                'start_date_field': 'start_date',
                'end_date_field': 'end_date',
                'check_mode': 'strict'
            },
            'steps': [
                {'insert': 'Allocation'}
            ]
        }]
    )

    # Generate action function
    generated_sql = generate_action(entity, entity.actions[0])

    # Verify generated function includes overlap check
    assert 'check_allocation_daterange_overlap' in generated_sql
    assert 'validation:daterange_overlap' in generated_sql

    # Test execution
    db.execute(generated_sql)

    # Insert first allocation (should succeed)
    result1 = db.call("scd.create_allocation", {
        'machine_id': uuid1,
        'start_date': '2024-01-01',
        'end_date': '2024-06-30'
    })
    assert result1.status == 'success'

    # Insert overlapping allocation (should fail)
    result2 = db.call("scd.create_allocation", {
        'machine_id': uuid1,
        'start_date': '2024-03-01',
        'end_date': '2024-09-30'
    })
    assert result2.status == 'error'
    assert result2.error_code == 'validation:daterange_overlap'
    assert result2.metadata['overlap_count'] == 1
```

---

### **Step 6: Usage Examples** (1 hour)

```yaml
examples:
  - name: allocation_non_overlapping
    description: "Machine allocations cannot overlap for same machine"
    entity: Allocation
    schema: scd
    config:
      scope_fields: [fk_machine]
      start_date_field: start_date
      end_date_field: end_date
      check_mode: strict
      allow_adjacent: true

  - name: contract_period_tracking
    description: "Contract periods with overlap warnings"
    entity: Contract
    schema: crm
    config:
      scope_fields: [fk_customer_org, fk_provider_org]
      start_date_field: effective_date
      end_date_field: termination_date
      check_mode: warning
      allow_adjacent: false

  - name: employee_assignment
    description: "Employee can only be assigned to one project at a time"
    entity: ProjectAssignment
    schema: projects
    config:
      scope_fields: [fk_employee]
      start_date_field: assignment_start
      end_date_field: assignment_end
      check_mode: strict
      allow_adjacent: true
```

---

### **Step 7: Documentation** (1-2 hours)

Create `docs/patterns/TEMPORAL_NON_OVERLAPPING_DATERANGE.md`:

```markdown
# Pattern: temporal_non_overlapping_daterange

## Purpose
Prevent overlapping date ranges within a defined scope (e.g., machine allocations, contract periods, employee assignments).

## Generated Assets
1. Computed DATERANGE column (GENERATED ALWAYS AS)
2. GIST index for efficient overlap detection
3. EXCLUSION constraint (database-level enforcement)
4. Validation helper function (application-level checks)

## Parameters
- **scope_fields**: Fields defining the scope (e.g., `[fk_machine]`)
- **start_date_field**: Start date column name (default: `start_date`)
- **end_date_field**: End date column name (default: `end_date`)
- **check_mode**: `strict` (error) or `warning` (info only)
- **allow_adjacent**: Allow adjacent ranges (default: `true`)

## Usage
[See examples above]

## Performance
- Overlap check: O(log n) with GIST index
- Typical query time: < 5ms for 100K records

## Limitations
- Requires PostgreSQL 9.2+ (DATERANGE type)
- Does not support time-of-day (only dates)
- Maximum of 10 scope fields (PostgreSQL EXCLUSION limit)
```

---

## 🧪 Testing Strategy

### **Unit Tests** (15+ test cases)
```python
# tests/unit/patterns/temporal/test_non_overlapping_daterange.py

class TestNonOverlappingDateRange:
    def test_basic_overlap_detection(self):
        """Test basic overlap detection"""
        # [Implementation]

    def test_adjacent_ranges_allowed(self):
        """Test adjacent ranges don't trigger overlap when allowed"""
        # [Implementation]

    def test_adjacent_ranges_disallowed(self):
        """Test adjacent ranges trigger overlap when disallowed"""
        # [Implementation]

    def test_open_ended_ranges(self):
        """Test ranges with NULL end_date"""
        # [Implementation]

    def test_multiple_scope_fields(self):
        """Test with multiple scope fields (machine + location)"""
        # [Implementation]

    def test_soft_delete_awareness(self):
        """Test that deleted records are ignored"""
        # [Implementation]

    def test_overlap_type_classification(self):
        """Test overlap type detection (contains, contained, overlaps_start, overlaps_end)"""
        # [Implementation]

    def test_strict_mode_error(self):
        """Test strict mode returns error on overlap"""
        # [Implementation]

    def test_warning_mode_metadata(self):
        """Test warning mode adds metadata but allows insert"""
        # [Implementation]

    def test_exclusion_constraint_enforcement(self):
        """Test PostgreSQL EXCLUSION constraint prevents overlaps"""
        # [Implementation]

    def test_gist_index_performance(self):
        """Test GIST index improves query performance"""
        # [Implementation]

    def test_daterange_generation(self):
        """Test computed DATERANGE column generation"""
        # [Implementation]

    def test_violation_reporting(self):
        """Test detailed violation JSONB structure"""
        # [Implementation]

    def test_update_overlap_detection(self):
        """Test overlap detection during updates (exclude current PK)"""
        # [Implementation]

    def test_null_end_date_handling(self):
        """Test NULL end_date (open-ended range) handling"""
        # [Implementation]
```

### **Integration Tests** (3-5 scenarios)
```python
# tests/integration/patterns/test_temporal_e2e.py

class TestTemporalPatternsE2E:
    def test_allocation_lifecycle(self):
        """Test full allocation lifecycle with overlaps"""
        # 1. Create first allocation
        # 2. Attempt overlapping allocation (should fail)
        # 3. Create adjacent allocation (should succeed)
        # 4. Update allocation to create overlap (should fail)
        # 5. End first allocation
        # 6. Create new allocation in now-free period (should succeed)

    def test_printoptim_allocation_schema(self):
        """Test pattern with actual PrintOptim allocation schema"""
        # Load PrintOptim allocation entity
        # Apply pattern
        # Verify all generated SQL
        # Test real-world scenarios

    def test_performance_with_large_dataset(self):
        """Test performance with 100K+ allocations"""
        # Insert 100K allocations
        # Measure overlap check time
        # Verify < 100ms per check
```

---

## 📊 Success Criteria

### **Functionality**
- [ ] Detects all overlap types (contains, contained, overlaps_start, overlaps_end, adjacent)
- [ ] Handles open-ended ranges (NULL end_date)
- [ ] Supports multiple scope fields
- [ ] Respects soft delete (deleted_at IS NULL)
- [ ] Generates valid EXCLUSION constraint DDL

### **Performance**
- [ ] Overlap check < 5ms for 1K records
- [ ] Overlap check < 50ms for 100K records
- [ ] GIST index reduces query time by 90%+

### **Code Quality**
- [ ] 90%+ test coverage
- [ ] All edge cases handled
- [ ] Clear error messages
- [ ] Comprehensive documentation

### **Integration**
- [ ] Works with SpecQL action compiler
- [ ] Compatible with existing patterns
- [ ] FraiseQL metadata generated
- [ ] TypeScript types generated

---

## 🚀 Next Steps After Day 4

1. **PR Review**: Submit pattern for team review
2. **Beta Testing**: Apply to 2-3 test projects
3. **Performance Tuning**: Optimize for large datasets
4. **Documentation**: Add to pattern library docs
5. **Next Pattern**: Begin SCD Type 2 helper pattern

---

## 💡 Tips & Tricks

### **Common Pitfalls**
1. **Forgetting soft delete**: Always include `deleted_at IS NULL` in overlap checks
2. **Adjacent range logic**: Be precise about `=` vs. `>` comparisons
3. **NULL handling**: Open-ended ranges (NULL end_date) require special logic
4. **Performance**: Always use GIST index for DATERANGE queries

### **Debugging**
```sql
-- Test overlap detection manually
SELECT * FROM scd.check_allocation_daterange_overlap(
  1,  -- machine FK
  '2024-01-01'::DATE,  -- start
  '2024-06-30'::DATE,  -- end
  NULL  -- exclude PK
);

-- Check EXCLUSION constraint
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'scd.tb_allocation'::regclass
  AND contype = 'x';  -- EXCLUSION constraints
```

### **Performance Monitoring**
```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT * FROM scd.tb_allocation
WHERE deleted_at IS NULL
  AND fk_machine = 123
  AND daterange(start_date, end_date, '[]') && daterange('2024-01-01', '2024-06-30', '[]');
```

---

**Quick Start Guide Created By**: Claude Code (Sonnet 4.5)
**Estimated Time**: 3-4 days for first pattern
**Next Pattern**: scd_type2_helper (2-3 days)
