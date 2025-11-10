# Query Pattern Library - Quick Summary

## The Big Idea

Add **declarative query patterns** to SpecQL's stdlib, enabling 80% code reduction for intermediate views.

**Before** (45 lines SQL):
```sql
CREATE VIEW v_count_allocations_by_location AS
SELECT loc.pk_location, COUNT(...) AS n_direct, COUNT(...) AS n_total
FROM tb_location loc LEFT JOIN tb_allocation a ON ...
WHERE ... GROUP BY ...;
-- + indexes + comments
```

**After** (15 lines YAML):
```yaml
query_patterns:
  - name: count_allocations_by_location
    pattern: aggregation/hierarchical_count
    config:
      counted_entity: Allocation
      metrics:
        - n_direct_allocations: {direct: true}
        - n_total_allocations: {hierarchical: true}
```

---

## What's Missing Today?

SpecQL has:
- ✅ **Action patterns** (`stdlib/actions/`) - CRUD, state machines, batch ops
- ✅ **Entity patterns** (`stdlib/{domain}/`) - Reusable entities
- ✅ **Table views** (built-in) - Commodity tables with JSONB

SpecQL lacks:
- ❌ **Query patterns** - Intermediate views between `tb_*` and `tv_*`

**Gap**: Users write 67+ types of intermediate views manually (junction resolvers, aggregations, extractors, etc.)

---

## 7 Pattern Categories (from PrintOptim)

| Pattern | Uses | Purpose | Example |
|---------|------|---------|---------|
| **Junction Resolver** | 15 | N-to-N mappings | Contract → FinancingCondition → Model |
| **Aggregation Helper** | 12 | Pre-calculated metrics | Count allocations per location (hierarchical) |
| **Component Extractor** | 8 | Efficient LEFT JOINs | Non-null coordinates for optional enrichment |
| **Hierarchical Flattener** | 6 | Tree UI support | Flatten ltree to 20 flat columns |
| **Polymorphic Resolver** | 2 | Type discrimination | Product \| ContractItem union |
| **Wrapper** | 4 | Complete result sets | Include zero-count entities in MV results |
| **Tree Builder** | 2 | Deep hierarchies | 8-CTE, 4-level nested JSON assembly |

**Total**: 67 real-world patterns from production SQL

---

## Example Pattern: Junction Resolver

### Pattern Config (YAML)
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

### Generated SQL
```sql
CREATE VIEW tenant.v_financing_condition_and_model_by_contract AS
SELECT
    c.pk_contract,
    fc.pk_financing_condition,
    m.pk_model,
    c.tenant_id
FROM tenant.tb_contract c
INNER JOIN tenant.tb_contract_financing_condition cfc ON ...
INNER JOIN tenant.tb_financing_condition fc ON ...
INNER JOIN tenant.tb_financing_condition_model fcm ON ...
INNER JOIN catalog.tb_model m ON ...
WHERE c.deleted_at IS NULL AND ... ;
```

---

## Implementation Plan (8 Weeks)

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Infrastructure** | Week 1-2 | Directory structure, schemas, templates, generator integration |
| **Core Patterns** | Week 3-4 | 4 highest-value patterns (junction, aggregation, extraction, hierarchical) |
| **Advanced Patterns** | Week 5-6 | Polymorphic, wrapper, tree builder patterns |
| **Documentation** | Week 7 | Reference docs, examples, migration guide |
| **Testing** | Week 8 | Integration tests, PrintOptim migration, benchmarks |

---

## Benefits

### For Users
- **80% code reduction** (150 lines SQL → 20 lines YAML)
- **Consistency** across all views
- **Discoverability** of proven patterns
- **Rapid development** via copy-paste-customize

### For SpecQL
- **Completeness** - Full coverage (actions + entities + queries)
- **Differentiation** - Unique in the ORM/framework space
- **Validation** - 67 production-tested patterns from PrintOptim

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Patterns too complex | Escape hatch for custom SQL, focus on 80% use case |
| Generator performance | Template caching, incremental generation |
| SQL correctness | Integration tests, side-by-side validation |
| Adoption resistance | Show dramatic code reduction, gradual migration |

---

## Success Metrics

- **67 patterns** converted from PrintOptim
- **80%+ code reduction** (SQL → YAML)
- **100% test coverage** for generated SQL
- **< 100ms** pattern generation time
- **10+ community contributions** within 6 months

---

## Next Steps

### This Week
1. **Review proposal** with SpecQL maintainers
2. **Prioritize patterns** based on impact
3. **Spike junction resolver** as proof-of-concept
4. **Create GitHub issue** with implementation plan

### Next Month
1. **Phase 1 + 2**: Infrastructure + 4 core patterns
2. **Convert 10 PrintOptim views** to patterns
3. **Draft documentation** for pattern library

---

## Related Documents

- **QUERY_PATTERN_LIBRARY_PROPOSAL.md** - Full detailed proposal (30 pages)
- **INTERMEDIATE_VIEWS_ANALYSIS.md** - Deep dive on 67 PrintOptim patterns
- **INTERMEDIATE_VIEWS_QUICK_REFERENCE.md** - Pattern lookup table
- **BACKBONE_VIEWS_ANALYSIS.md** - Infrastructure view patterns

---

**Status**: Proposal
**Author**: Claude
**Date**: 2025-11-10
**Estimated Effort**: 8 weeks (1 developer)
**Impact**: High - Completes SpecQL's declarative vision ✨
