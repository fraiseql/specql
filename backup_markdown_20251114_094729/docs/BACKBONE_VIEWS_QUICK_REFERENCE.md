# PrintOptim Backbone Views - Quick Reference

**Purpose**: Identify non-entity-specific infrastructure views that serve as composition layers, utilities, and performance optimizations rather than directly mapping to business entities.

---

## CRITICAL INFRASTRUCTURE VIEWS (Must Document in SpecQL)

### 1. v_path (Polymorphic Hierarchy Unifier)
**Location**: `02_query_side/021_common_dim/0214_utilities/02141_v_path.sql`
**Type**: Utility View (UNION of 6+ hierarchies)
**What it does**: Single query point for any hierarchical ancestor/descendant lookup across all entity types
**Unifies**: industry, organization, org_unit_level, organizational_unit, location_level, location
**Why it matters**: Eliminates need to know entity-specific hierarchy access patterns
**Infrastructure pattern**: Polymorphic queries via type discriminator `object_name`

### 2. v_public_address (Localization & Enrichment)
**Location**: `02_query_side/021_common_dim/0211_geo/02111_v_public_address.sql`
**Type**: Enrichment View
**What it does**: Composition of address data with localization (French/default fallback) and structural transformation
**Joins**: 10+ tables including translation tables (tl_*)
**Why it matters**: Provides standardized address hydration for all location-aware features
**Infrastructure pattern**: Localization fallback via COALESCE

### 3. v_dataflow (Deep Nesting Aggregation)
**Location**: `02_query_side/026_dataflow/0261_dataflow/02611_v_dataflow.sql`
**Type**: Complex Aggregation View
**What it does**: Complete dataflow configuration with CTE-based nested aggregation of field mappings
**Pattern**: CTE for pre-aggregation + CASE for conditional nesting
**Why it matters**: Shows advanced aggregation patterns for ETL pipeline configuration

---

## MATERIALIZED VIEWS (Performance Caching Layer)

### mv_industry (Hierarchical Path Expansion)
**File**: `02_query_side/022_crm/0221_industry/02211_mv_industry.sql`
**Caches**: Expensive ltree path unpacking into ancestor arrays
**Refresh dependency**: None (base table)
**Used by**: `mv_organization`

### mv_organization (Denormalized Organization Snapshot)
**File**: `02_query_side/022_crm/0222_organization/02221_mv_organization.sql`
**Depends on**: `mv_industry`, `v_public_address`, `mv_count_allocations_by_organization`
**Refresh order**: After dependencies
**Key output**: Rich JSONB with nested industry, address, allocations

### mv_count_allocations_by_organizational_unit
**File**: `02_query_side/024_dim/0247_materialized_views/02472_mv_count_allocations_by_organizational_unit.sql`
**Caches**: Aggregated allocation counts (total, current, past, unique machines)
**Used by**: `v_organizational_unit`, `mv_organization`, analytics
**Indexing**: PK lookup + filtered index for active allocations

### mv_machine_allocation_summary
**File**: `02_query_side/024_dim/0247_materialized_views/02473_mv_machine_allocation_summary.sql`
**Caches**: Machine allocation status and history
**Used by**: `v_machine_detailed`, `v_count_allocations_optimized`

### mv_statistics_for_tree (Multi-Domain Aggregate)
**File**: `02_query_side/027_fact/0274_stat/02749_mv_statistics_for_tree.sql`
**Pattern**: UNION ALL of CTEs (locations + org_units)
**Purpose**: Cross-domain statistics with polymorphic `source` column
**Used by**: Analytics dashboards, cost center reporting

---

## COMMODITY TABLES (tv_*) (Query Optimization Cache)

Purpose: Denormalized tables with pre-calculated JSONB for efficient single-object queries

### tv_machine
**File**: `02_query_side/024_dim/0245_mat/02458_tv_machine.sql`
**Key feature**: `machine_item_ids uuid[]` (GIN indexed) for efficient nested list access
**Data structure**: Rich JSONB with contract, model, items, bindings
**Update strategy**: Fine-grained row-level updates (not full refresh)
**Cache invalidation**: Trigger on INSERT/UPDATE/DELETE

### tv_location
**File**: `02_query_side/024_dim/0241_geo/02413_tv_location.sql`
**Key features**: `is_floor_or_ancestor` filter, location_level_path, ltree path
**Used by**: v_location, tree rendering

### tv_contract
**File**: `02_query_side/024_dim/0244_agreement/02448_tv_contract.sql`
**Used by**: v_machine_detailed, v_contracts_by_machine

### tv_allocation
**File**: `02_query_side/025_scd/0252_tv_allocation.sql`
**Used by**: Allocation-related views

---

## COMPOSITION VIEWS (Multi-View Enrichment)

### v_machine (11 View Dependencies)
**File**: `02_query_side/024_dim/0245_mat/02457_v_machine.sql`
**Composes**: v_model, v_order, v_current_contract, v_initial_contract, v_initial_financing_condition, v_current_allocations_by_machine, v_machine_items, v_machine_item_bindings
**Output**: Single JSONB column `data` with complete machine context
**Used by**: v_machine_detailed

### v_machine_detailed (Single-Object Rich View)
**File**: `02_query_side/024_dim/0245_mat/02460_v_machine_detailed.sql`
**Pattern**: Composition of `tv_machine` with nested subqueries for:
- All contracts (many-to-many)
- Successive applicable contracts (historical chain)
- Applicable prices (contract × model)
- Machine items with status
- Volume statistics
**Used by**: GraphQL rich queries, detail pages

### v_contract (Base Contract Composition)
**File**: `02_query_side/024_dim/0244_agreement/02441_v_contract.sql`
**Depends on**: `mv_organization` (both client and provider), financing conditions subquery
**Extended by**: `v_contract_with_items`

### v_location (Rich Location Composition)
**File**: `02_query_side/024_dim/0241_geo/02412_v_location.sql`
**Composes**: v_public_address, v_count_allocations_by_location, v_location_coordinates
**Pattern**: Complex 130+ line composition with nested aggregations

### v_machine_item (Translation & Enrichment)
**File**: `02_query_side/024_dim/0245_mat/02451_v_machine_item.sql`
**Pattern**: Localized category/accessory information via locale CTE

---

## AGGREGATION & STATISTICS VIEWS

### v_count_allocations_by_organizational_unit
**Pattern**: ltree path containment (o2.path <@ o1.path) for hierarchy traversal
**Outputs**: n_direct_allocations, n_total_allocations
**Used by**: v_organizational_unit, analytics

### v_count_allocations_optimized
**File**: `02_query_side/024_dim/0247_materialized_views/02474_v_count_allocations_optimized.sql`
**Pattern**: UNION ALL of materialized view + ANTI-JOIN for completeness
**Purpose**: Ensures entities with zero allocations included

### v_flat_organizational_unit_for_rust_tree
**File**: `02_query_side/024_dim/0242_org/02424_v_flat_organizational_unit_for_rust_tree.sql`
**Purpose**: Specialized flat hierarchy representation for Rust tree structures
**Pattern**: UNION across multiple hierarchy formats

---

## DESIGN PATTERNS SUMMARY

| Pattern | Purpose | Example |
|---------|---------|---------|
| **Polymorphic Union** | Single query for multiple entity types | `v_path` (6+ hierarchies) |
| **Localization Fallback** | Multi-language support with defaults | `COALESCE(tl_*, tb_*name)` |
| **Materialized + Refresh Order** | Performance caching with dependency tracking | `mv_industry → mv_organization` |
| **FraiseQL Dual Column** | Efficient filtering + hydration | Direct columns + JSONB `data` |
| **Ltree Path Containment** | Hierarchical queries | `child.path <@ parent.path` |
| **CTE Aggregation** | Pre-compute nested structures | v_dataflow's `dataflow_fields_agg` |
| **UNION ALL Completeness** | Include zero-count entities | `v_count_allocations_optimized` |
| **View Composition Chain** | Layer enrichment across views | v_machine → v_machine_detailed |
| **Temporal Filtering** | Current/active records | `start_date <= NOW AND end_date IS NULL` |
| **Subquery Aggregation** | Many-to-many relationship handling | Contract item aggregation in v_machine |

---

## INFRASTRUCTURE COMPOSITION LAYERS

```
Layer 1: Base Views (Table wrapping)
  ↓ v_locale, v_industry, v_organization
  
Layer 2: Utility Views (Cross-cutting)
  ↓ v_path, v_public_address, v_dataflow
  
Layer 3: Materialized Views (Performance caching)
  ↓ mv_industry, mv_organization, mv_count_allocations_*
  
Layer 4: Commodity Tables (Query optimization)
  ↓ tv_machine, tv_location, tv_contract
  
Layer 5: Composition Views (Entity enrichment)
  ↓ v_machine, v_contract, v_location
  
Layer 6: Specialized Aggregates (Analytics/type resolution)
  ↓ v_count_allocations_optimized, v_pk_class_resolver, mv_statistics_for_tree
```

---

## Files to Document in SpecQL

These backbone views don't map to individual entities but represent infrastructure patterns:

1. **Utility Views**: v_path, v_public_address, v_dataflow
2. **Base Materialized Views**: mv_industry, mv_organization, mv_count_allocations_*
3. **Commodity Tables**: tv_machine, tv_location, tv_contract, tv_allocation
4. **Composition Patterns**: v_machine_detailed, v_contract_with_items, v_location
5. **Special Patterns**: v_pk_class_resolver, v_flat_organizational_unit_for_rust_tree, v_count_allocations_optimized

---

## Cache Invalidation Strategy

All commodity tables (tv_*) have triggers:
```sql
CREATE TRIGGER trg_tv_<entity>_cache_invalidation
AFTER INSERT OR UPDATE OR DELETE ON public.tv_<entity>
FOR EACH ROW
EXECUTE FUNCTION turbo.fn_tv_table_cache_invalidation()
```

Materialized views require manual refresh in dependency order:
```
REFRESH mv_industry;
REFRESH mv_count_allocations_by_organizational_unit;
REFRESH mv_organization;
```

---

## Key Takeaway

These backbone infrastructure views represent **query-side architecture decisions** that:
- Unify cross-cutting concerns (hierarchies via v_path)
- Optimize expensive operations (materialization, commodity tables)
- Provide standardized access patterns (dual-column FraiseQL)
- Enable polymorphic queries (type discriminators)
- Cache complex compositions (v_machine_detailed)

They should be documented as **Infrastructure Entities** in SpecQL, not as business entities.
