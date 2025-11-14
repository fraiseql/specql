# PrintOptim Backbone Infrastructure Views - Complete Index

Generated: 2025-11-10
Analysis of 99 view files in `reference_sql/0_schema/02_query_side/`

---

## Documents Included

### 1. BACKBONE_VIEWS_ANALYSIS.md (1,015 lines)
**Comprehensive detailed analysis** of all backbone infrastructure views

Contains:
- 9 backbone view categories with detailed descriptions
- SQL patterns and composition examples
- Complete dependency graphs
- Infrastructure role analysis
- Key findings and design patterns

**Use this for**: Deep understanding of architecture, implementation details, pattern examples

### 2. BACKBONE_VIEWS_QUICK_REFERENCE.md (227 lines)
**Quick-reference guide** for common patterns and infrastructure components

Contains:
- Critical infrastructure views summary table
- Materialized views with refresh strategies
- Commodity tables (tv_*) listing
- Composition views and their dependencies
- Design patterns in tabular format
- Infrastructure composition layers

**Use this for**: Quick lookups, decision-making, pattern reference

---

## Key Findings At a Glance

### Total Infrastructure Views: 50-60

Distributed across 7 tiers:
1. Base Views (3) - Table wrapping
2. Utility Views (3) - Cross-cutting
3. Materialized Views (10+) - Performance caching
4. Commodity Tables (10+) - Query optimization
5. Composition Views (15+) - Entity enrichment
6. Aggregation Views (10+) - Statistics
7. Special Infrastructure (5+) - Type resolution

### Critical Infrastructure Views

| View | Type | Purpose | Impact |
|------|------|---------|--------|
| **v_path** | Utility | Polymorphic hierarchy unifier (6+ entity types) | HIGH - System-wide |
| **v_public_address** | Enrichment | Localized address composition (10+ joins) | HIGH - Location features |
| **v_dataflow** | Aggregation | Deep nesting with CTE pattern | MEDIUM - ETL |
| **mv_organization** | Materialized | Denormalized org snapshot | HIGH - CRM |
| **tv_machine** | Commodity | Machine cache with JSONB | HIGH - Machine queries |
| **v_machine_detailed** | Composition | Rich single-object view (11 dependencies) | HIGH - GraphQL |

### Materialized View Refresh Order
```
1. mv_industry
2. mv_count_allocations_by_organizational_unit
3. mv_count_allocations_by_network_configuration
4. mv_organization
5. Other specialized MVs
```

### Design Patterns Summary

10 critical patterns identified:
1. Polymorphic Union (v_path)
2. Materialized View Dependency Chain (mv_organization)
3. FraiseQL Dual-Column (direct columns + JSONB data)
4. Commodity Table Pattern (tv_* cache tables)
5. Localization Fallback (COALESCE)
6. Ltree Hierarchical Operations (path containment)
7. CTE-Based Aggregation (v_dataflow)
8. UNION ALL Completeness (v_count_allocations_optimized)
9. View Composition Chains (5+ levels deep)
10. Temporal Filtering (current/active records)

---

## Architecture Diagram

```
Layer 1: Raw Tables (tb_*)
         ↓
Layer 2: Base Views (v_locale, v_industry, v_organization)
         ↓
Layer 3: Utility Views (v_path, v_public_address, v_dataflow)
         ├─ Polymorphic hierarchies
         ├─ Localization & enrichment
         └─ Deep nesting aggregation
         ↓
Layer 4: Materialized Views (mv_*, performance caching)
         ├─ mv_industry (path expansion)
         ├─ mv_organization (denormalized snapshot)
         └─ mv_count_allocations_by_* (aggregation)
         ↓
Layer 5: Commodity Tables (tv_*, JSONB precomputation)
         ├─ tv_machine (with machine_item_ids array)
         ├─ tv_location (with hierarchy metadata)
         ├─ tv_contract
         └─ tv_allocation
         ↓
Layer 6: Composition Views (entity enrichment)
         ├─ v_machine (11 view dependencies)
         ├─ v_machine_detailed (subquery aggregations)
         ├─ v_contract (org composition)
         ├─ v_location (address + allocations)
         └─ v_machine_item (localized)
         ↓
Layer 7: Specialized Aggregates (analytics, type resolution)
         ├─ v_count_allocations_optimized (UNION + ANTI-JOIN)
         ├─ v_flat_organizational_unit_for_rust_tree (format)
         ├─ v_pk_class_resolver (polymorphic type mapping)
         └─ mv_statistics_for_tree (cross-domain)
```

---

## View Dependency Examples

### Simple: v_locale
```
tb_locale → v_locale
```

### Medium: v_contract
```
tb_contract
├─ mv_organization (client org)
├─ mv_organization (provider org)
└─ tb_currency
```

### Complex: v_machine
```
tb_machine
├─ v_model
├─ v_order
├─ v_current_contract
├─ v_initial_contract
├─ v_initial_financing_condition
├─ v_current_allocations_by_machine
├─ v_machine_items
└─ v_machine_item_bindings
```

### Very Complex: v_machine_detailed
```
tv_machine (commodity table)
├─ tv_contract (subquery aggregation)
│  └─ tb_machine_contract_relationship
├─ v_price (subquery aggregation)
├─ v_volume (statistics aggregation)
└─ Multiple nested subqueries
```

---

## Cache Invalidation Strategy

### Commodity Tables (tv_*)
All have automatic triggers:
```sql
CREATE TRIGGER trg_tv_<entity>_cache_invalidation
AFTER INSERT OR UPDATE OR DELETE
EXECUTE FUNCTION turbo.fn_tv_table_cache_invalidation()
```

Update strategy: Fine-grained row-level updates (not full refresh)

### Materialized Views (mv_*)
Manual refresh required, in dependency order:
```
REFRESH MATERIALIZED VIEW mv_industry;
REFRESH MATERIALIZED VIEW mv_count_allocations_by_organizational_unit;
REFRESH MATERIALIZED VIEW mv_organization;
```

---

## Implementing Similar Infrastructure in SpecQL

When designing SpecQL generators for entity-specific views, replicate:

1. **Base View**: Simple table wrapping with soft-delete filtering
2. **Commodity Table**: Pre-computed JSONB with fine-grained updates
3. **Composition View**: Multi-view enrichment with FraiseQL pattern
4. **Aggregation View**: Materialized aggregates with refresh ordering
5. **Specialized Views**: Domain-specific patterns (temporal, localization)

Each layer should:
- Have clear responsibility
- Compose lower layers, not raw tables
- Use standardized patterns (FraiseQL, ltree, COALESCE)
- Include proper indexing (FK lookups, GIN for arrays, filtered indexes)
- Document refresh/invalidation strategy

---

## Files for Complete Reference

### SQL Pattern Examples
- `reference_sql/0_schema/02_query_side/020_base_views/` - Base views
- `reference_sql/0_schema/02_query_side/021_common_dim/0214_utilities/02141_v_path.sql` - Polymorphic pattern
- `reference_sql/0_schema/02_query_side/026_dataflow/0261_dataflow/02611_v_dataflow.sql` - CTE aggregation
- `reference_sql/0_schema/02_query_side/024_dim/0245_mat/02460_v_machine_detailed.sql` - Composition chain
- `reference_sql/0_schema/02_query_side/024_dim/0247_materialized_views/02474_v_count_allocations_optimized.sql` - UNION + ANTI-JOIN

### Analysis Documents
- `BACKBONE_VIEWS_ANALYSIS.md` - Comprehensive analysis
- `BACKBONE_VIEWS_QUICK_REFERENCE.md` - Quick reference
- This file - Index and summary

---

## For SpecQL Documentation

When creating SpecQL entity definitions, consider:

1. Will this entity need:
   - Localization via translation tables? (COALESCE pattern)
   - Hierarchical queries? (v_path infrastructure)
   - Allocation tracking? (mv_count_allocations_by_*)
   - Rich single-object queries? (commodity table + composition view)
   - Temporal filtering? (current/active record pattern)

2. Create infrastructure views in this order:
   - Base view (if not simple table wrapper)
   - Materialized views (if expensive aggregations)
   - Commodity table (if complex JSONB needed)
   - Composition views (for enrichment)
   - Specialized views (for domain patterns)

3. Document:
   - Refresh dependencies (for materialized views)
   - Cache invalidation (for commodity tables)
   - View composition chain (for enrichment layers)
   - Index strategy (for performance)

---

## Quick Lookups

**Need to understand v_path?**
→ See BACKBONE_VIEWS_ANALYSIS.md, section "2. CROSS-CUTTING UTILITY VIEWS"

**Need refresh order for materialized views?**
→ See BACKBONE_VIEWS_QUICK_REFERENCE.md, "Cache Invalidation Strategy"

**Need pattern examples?**
→ See BACKBONE_VIEWS_QUICK_REFERENCE.md, "Design Patterns Summary"

**Need full SQL examples?**
→ See reference_sql/0_schema/02_query_side/ (check specific view files)

**Need complete dependency graph?**
→ See BACKBONE_VIEWS_ANALYSIS.md, "BACKBONE VIEW DEPENDENCY GRAPH"

---

## Summary Statistics

- Total views analyzed: 99
- Backbone infrastructure views: 50-60
- Critical cross-cutting patterns: 10
- Materialized view dependencies: Complex chains
- Commodity table coverage: 10+ entities
- Maximum composition depth: 5+ view layers
- Architectural layers identified: 7

---

Generated by thorough analysis of PrintOptim query-side (02_query_side) architecture.

For questions about specific patterns, see detailed analysis document.
For quick decisions, see quick reference document.
