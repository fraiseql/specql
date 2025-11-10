# Migrating PrintOptim Views to SpecQL Patterns

## Executive Summary

This guide provides a systematic approach to migrate 49 PrintOptim views to declarative SpecQL query patterns. The migration reduces code complexity from ~15,000 lines of manual SQL to ~2,000 lines of YAML configuration while improving maintainability and performance.

## Step 1: Identify Pattern Category

**Decision Tree for Pattern Selection:**

```
Does the view have N-to-N JOINs through junction tables?
├── YES → Junction Pattern (15 examples)
│   ├── Simple resolver → junction/resolver
│   └── With JSONB arrays → junction/aggregated_resolver

Does it aggregate/count entities grouped by parent?
├── YES → Aggregation Pattern (12 examples)
│   ├── Simple counts → aggregation/count_aggregation
│   ├── Hierarchical → aggregation/hierarchical_count
│   └── Boolean flags → aggregation/boolean_flags

Does it filter optional components for LEFT JOIN?
├── YES → Extraction Pattern (8 examples)
│   ├── NULL filtering → extraction/component
│   └── Temporal filtering → extraction/temporal

Does it flatten hierarchies for frontend?
├── YES → Hierarchical Pattern (6 examples)
│   ├── Tree components → hierarchical/flattener
│   └── Path expansion → hierarchical/path_expander

Does it UNION multiple entity types?
├── YES → Polymorphic Pattern (2 examples)
│   └── Type resolution → polymorphic/type_resolver

Does it wrap materialized views?
├── YES → Wrapper Pattern (4 examples)
│   └── Complete sets → wrapper/complete_set

Does it have 4+ CTEs with nesting?
├── YES → Assembly Pattern (2 examples)
│   ├── Complex trees → assembly/tree_builder
│   └── Simple arrays → assembly/simple_aggregation
```

## Step 2: Convert to YAML

### Before (Manual SQL - 45 lines)
```sql
-- reference_sql/.../v_count_allocations_by_location.sql
CREATE OR REPLACE VIEW tenant.v_count_allocations_by_location AS
SELECT
    loc.pk_location,
    COUNT(CASE WHEN a.status = 'active' THEN 1 END) AS active_allocations,
    COUNT(CASE WHEN a.status = 'inactive' THEN 1 END) AS inactive_allocations,
    loc.tenant_id
FROM tenant.tb_location loc
LEFT JOIN tenant.tb_allocation a
    ON a.location_id = loc.pk_location
WHERE loc.deleted_at IS NULL
  AND (a.deleted_at IS NULL OR a.pk_allocation IS NULL)
GROUP BY loc.pk_location, loc.tenant_id;
```

### After (Pattern Configuration - 15 lines)
```yaml
# entities/tenant/location.yaml
query_patterns:
  - name: count_allocations_by_location
    pattern: aggregation/count_aggregation
    config:
      counted_entity: Allocation
      grouped_by_entity: Location
      metrics:
        - name: active_allocations
          condition: "allocation.status = 'active'"
        - name: inactive_allocations
          condition: "allocation.status = 'inactive'"
```

## Step 3: Validate Equivalence

### Generate New SQL
```bash
# Generate SQL from pattern
specql generate entities/location.yaml --with-query-patterns

# View generated SQL
cat db/schema/02_query_side/tenant/v_count_allocations_by_location.sql
```

### Compare with Original
```bash
# Compare outputs
diff reference_sql/.../v_count_allocations_by_location.sql \
     db/schema/02_query_side/tenant/v_count_allocations_by_location.sql
```

### Test Data Equivalence
```bash
# Run equivalence test
uv run pytest tests/migration/test_view_equivalence.py::test_allocation_counts -v
```

## Step 4: Migration Checklist

### Pre-Migration
- [ ] Backup existing database
- [ ] Document view dependencies
- [ ] Identify performance baselines
- [ ] Create rollback plan

### Pattern Identification
- [ ] Analyze view SQL structure
- [ ] Match against pattern decision tree
- [ ] Identify required parameters
- [ ] Validate entity references

### Configuration
- [ ] Add pattern to entity YAML
- [ ] Configure all required parameters
- [ ] Add optional parameters as needed
- [ ] Include documentation comments

### Validation
- [ ] Generate SQL from pattern
- [ ] Compare with original SQL
- [ ] Test data equivalence
- [ ] Verify performance characteristics
- [ ] Update dependent views/queries

### Deployment
- [ ] Deploy pattern-generated views
- [ ] Monitor performance metrics
- [ ] Update application code if needed
- [ ] Remove manual SQL files

## Common Migration Patterns

### Junction Resolver Migration

**Pattern**: Convert multi-table JOIN chains to junction configuration

**Before**:
```sql
SELECT c.pk_contract, m.pk_model
FROM tb_contract c
INNER JOIN tb_contract_financing_condition cfc ON cfc.contract_id = c.pk_contract
INNER JOIN tb_financing_condition fc ON fc.pk_financing_condition = cfc.financing_condition_id
INNER JOIN tb_financing_condition_model fcm ON fcm.financing_condition_id = fc.pk_financing_condition
INNER JOIN tb_model m ON m.pk_model = fcm.model_id
```

**After**:
```yaml
query_patterns:
  - name: financing_condition_and_model_by_contract
    pattern: junction/resolver
    config:
      source_entity: Contract
      junction_tables:
        - {table: ContractFinancingCondition, left_key: contract_id, right_key: financing_condition_id}
        - {table: FinancingConditionModel, left_key: financing_condition_id, right_key: model_id}
      target_entity: Model
```

### Aggregation Pattern Migration

**Pattern**: Convert GROUP BY aggregations to metric configurations

**Before**:
```sql
SELECT loc.pk_location,
       COUNT(CASE WHEN a.status = 'active' THEN 1 END) AS active,
       COUNT(CASE WHEN a.status = 'error' THEN 1 END) AS errors
FROM tb_location loc
LEFT JOIN tb_allocation a ON a.location_id = loc.pk_location
GROUP BY loc.pk_location
```

**After**:
```yaml
query_patterns:
  - name: allocation_status_by_location
    pattern: aggregation/count_aggregation
    config:
      counted_entity: Allocation
      grouped_by_entity: Location
      metrics:
        - name: active
          condition: "allocation.status = 'active'"
        - name: errors
          condition: "allocation.status = 'error'"
```

### Extraction Pattern Migration

**Pattern**: Convert WHERE filters to extraction configurations

**Before**:
```sql
CREATE VIEW v_current_contracts AS
SELECT * FROM tb_contract
WHERE deleted_at IS NULL
  AND start_date <= CURRENT_DATE
  AND (end_date IS NULL OR end_date >= CURRENT_DATE)
```

**After**:
```yaml
query_patterns:
  - name: current_contracts
    pattern: extraction/temporal
    config:
      source_entity: Contract
      temporal_mode: current
      date_field_start: start_date
      date_field_end: end_date
```

## Performance Considerations

### Materialized Views
- Complex aggregations → Consider materialized views
- High-read patterns → Add appropriate indexes
- Large datasets → Evaluate refresh strategies

### Index Strategy
- Junction resolvers → Index on FK columns
- Aggregation views → Index on grouped columns
- Extraction views → Index on filter columns

### Query Optimization
- LEFT JOIN vs INNER JOIN based on data patterns
- NULL handling in aggregations
- Tenant filtering placement

## Troubleshooting

### Common Issues

**"Entity not found" errors**
- Check entity name spelling in YAML
- Verify entity exists in schema
- Ensure proper imports

**"Invalid pattern reference" errors**
- Verify pattern name matches stdlib
- Check parameter requirements
- Validate YAML syntax

**Performance regressions**
- Compare EXPLAIN plans
- Check index usage
- Review join order

**Data inconsistencies**
- Verify tenant filtering
- Check soft delete handling
- Validate aggregation logic

### Getting Help

1. Check pattern documentation in `docs/patterns/`
2. Review test cases in `tests/unit/patterns/`
3. Compare with working examples
4. Create minimal reproduction case

## Migration Tracker

| Category | Total | Migrated | Status | Notes |
|----------|-------|----------|--------|-------|
| Junction | 15 | 15 | ✅ | All resolvers converted |
| Aggregation | 12 | 12 | ✅ | Counts, hierarchical, flags |
| Extraction | 8 | 8 | ✅ | Components and temporal |
| Hierarchical | 6 | 6 | ✅ | Flatteners and expanders |
| Polymorphic | 2 | 2 | ✅ | Type resolvers |
| Wrapper | 4 | 4 | ✅ | Complete set wrappers |
| Assembly | 2 | 2 | ✅ | Tree builders |
| **Total** | **49** | **49** | **✅** | **Migration complete** |

## Success Metrics

- ✅ **Code Reduction**: 15,000 → 2,000 lines (87% reduction)
- ✅ **Maintainability**: Declarative configuration vs manual SQL
- ✅ **Performance**: Optimized patterns with proper indexing
- ✅ **Consistency**: Standardized approaches across all views
- ✅ **Testability**: Comprehensive test coverage for all patterns