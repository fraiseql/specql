# PrintOptim Backbone Infrastructure Views - Complete Analysis

**Date**: 2025-11-10
**Analysis**: Identification of non-entity-specific views that serve as infrastructure components, composition layers, and utility functions
**Total Views Analyzed**: 99 view files in `02_query_side/`

## BACKBONE VIEW CATEGORIES

### 1. BASE VIEWS (Simple Entity Wrappers) - Foundation Layer

These provide basic, direct exposure of entity data with soft-delete filtering and minimal enrichment.

#### Location: `02_query_side/020_base_views/`

| View Name | Purpose | Serves | Table Code |
|-----------|---------|--------|-----------|
| **v_locale** | Base exposure of locale/language data | CRM, Catalog | Direct mapping: tb_locale |
| **v_industry** | Hierarchical industry classification with parent relationships | Organization trees, Analytics | catalog.tb_industry + tb_industry_info |
| **v_organization** | Base organization data with hierarchy info | CRM, Organization management | management.tb_organization |

**Infrastructure Role**: These are the foundational read-side views that expose core entities for composition by higher-level views. They handle:
- Soft-delete filtering (WHERE deleted_at IS NULL)
- Type normalization (PK → id aliasing)
- Basic schema schema exposure
- Direct table wrapping without complex joins

**Dependency Impact**: Heavy - almost all domain-specific views depend on at least one of these

---

### 2. CROSS-CUTTING UTILITY VIEWS - System Integration Layer

These views unify data across multiple domain entities for common cross-cutting concerns.

#### Location: `02_query_side/021_common_dim/0214_utilities/`

##### **v_path** (Critical Infrastructure)
**File**: `02141_v_path.sql`

**Purpose**: Unified hierarchical path infrastructure serving all hierarchical entities

**Composition Pattern** (UNION across 6+ entity types):
```sql
SELECT 'industry'::text AS object_name, ... FROM catalog.tb_industry
UNION
SELECT 'organization'::text, ... FROM management.tb_organization
UNION
SELECT 'organizational_unit_level'::text, ... FROM common.tb_organizational_unit_level
UNION
SELECT 'organizational_unit'::text, ... FROM tenant.tb_organizational_unit
UNION
SELECT 'location_level'::text, ... FROM common.tb_location_level
UNION
SELECT 'location'::text, ... FROM tenant.tb_location
```

**Unified Output Columns**:
- `object_name`: Type discriminator (enables polymorphic queries)
- `id`: Public-facing identifier
- `pk`: Primary key in respective table
- `identifier`: Human-readable identifier
- `path`: ltree hierarchical path

**Infrastructure Benefits**:
- Single query point for any hierarchical ancestor/descendant lookup
- Enables permission trees across all domains
- Supports hierarchy visualizations without schema knowledge
- Reduces query complexity for recursive operations

**Used By**: Authorization systems, hierarchy traversal, tree rendering

**Cross-Cutting Role**: High - provides unified interface for heterogeneous hierarchies

---

### 3. ENRICHMENT/COMPOSITION VIEWS - Domain Hydration Layer

These views combine entity data with translations, localization, and structural enrichment.

#### Location: `02_query_side/021_common_dim/0211_geo/`

##### **v_public_address** (Localization & Enrichment)
**File**: `02111_v_public_address.sql`

**Purpose**: Compose rich, localized public address data for display and mapping

**Composition Pattern** (Complex multi-join):
```
tb_public_address
  ├─ JOIN tb_administrative_unit (city lookup)
  ├─ JOIN tb_administrative_unit_info (base labels)
  ├─ LEFT JOIN tl_administrative_unit_info (French localization)
  ├─ LEFT JOIN tb_street_type (e.g., "Rue", "Avenue")
  ├─ LEFT JOIN tl_street_type (localized street types)
  ├─ JOIN tb_postal_code (zip code info)
  ├─ JOIN tb_country (country reference)
  └─ LEFT JOIN tl_country (localized country names)
```

**Output Pattern**:
- Direct columns: `country_name`, `city` (for filtering)
- Rich JSONB: `data` object with nested address structure
- Includes computed fields: `formatted` (HTML-ready address)

**Infrastructure Role**: Composition layer that handles:
- Localization fallback (COALESCE on translations)
- Cross-schema reference enrichment
- Structural transformation (flat → hierarchical JSON)
- Display-ready formatting

**Used By**: Location APIs, mapping services, frontend address display

---

#### Location: `02_query_side/026_dataflow/`

##### **v_dataflow** (Deep Nesting & Aggregation)
**File**: `02611_v_dataflow.sql`

**Purpose**: Complete dataflow configuration with nested domain objects

**Pattern** (CTEs + Aggregation):
```sql
WITH dataflow_fields_agg AS (
  SELECT dff.fk_dataflow,
    jsonb_agg(jsonb_build_object(...))
  FROM tb_dataflow_field dff
  LEFT JOIN tb_printoptim_field pf ON ...
  LEFT JOIN tb_field_type ft ON ...
  GROUP BY dff.fk_dataflow
)
SELECT
  df.pk_dataflow AS id,
  jsonb_build_object(
    'fields', dataflow_fields_agg.fields,
    'customer', jsonb_build_object(...),
    'datasupplier', jsonb_build_object(...),
    'email_provider', jsonb_build_object(...),
    'file_read_instruction', CASE WHEN ... END
  ) AS data
FROM tb_dataflow df
LEFT JOIN organization org ON ...
LEFT JOIN datasupplier ds ON ...
LEFT JOIN email_provider ep ON ...
```

**Infrastructure Pattern**:
- CTE for pre-aggregation of nested arrays
- CASE expressions for conditional nesting
- Multiple LEFT JOINs for optional components
- Single JSONB output column for hydration

**Used By**: ETL pipeline configuration, dataflow management APIs

---

### 4. MATERIALIZED VIEWS - Performance & Caching Layer

Cache expensive aggregations for query performance.

#### Location: `02_query_side/022_crm/`

##### **mv_industry** (Hierarchical Expansion)
**File**: `02211_mv_industry.sql`

**Purpose**: Pre-expanded industry hierarchy with path traversal metadata

**Materialization Pattern**:
```sql
WITH industry_nodes AS (
  SELECT i.*, unnest(string_to_array(i.path::text, '.'))::integer AS node_id
  FROM tb_industry i
),
expanded_paths AS (
  SELECT n.*, ancestor_industry.*
  FROM industry_nodes n
  JOIN tb_industry ancestor ON n.node_id = ancestor.id
)
SELECT
  pk_industry AS id,
  jsonb_build_object(
    'path_of_names', array_agg(ancestor_name ORDER BY ...),
    'path_of_nodes', jsonb_agg(jsonb_build_object(...) ORDER BY ...)
  ) AS data
GROUP BY pk_industry, ...
```

**Caching Role**: 
- Materializes path expansion (expensive ltree unpacking)
- Pre-computes ancestor arrays for tree rendering
- Stored as JSONB for frontend consumption
- Indexed for common access patterns

**Refresh Strategy**: Refresh periodically after industry changes
- Used by: `mv_organization` (depends on mv_industry)

**Dependency Chain**: 
```
tb_industry → mv_industry → mv_organization
```

---

##### **mv_organization** (Denormalized Snapshot)
**File**: `02221_mv_organization.sql`

**Purpose**: Flattened organizational snapshot with rich metadata

**Composition Dependencies**:
```
management.tb_organization
├─ management.tb_organization_info (base labels)
├─ catalog.tb_organization_type (org type reference)
├─ mv_industry (nested industry hierarchy - DEPENDS ON mv_industry)
├─ v_public_address (legal address enrichment)
└─ mv_count_allocations_by_organization (allocation metrics - DEPENDS)
```

**Output Pattern**:
```json
{
  "id": "uuid",
  "name": "Organization Name",
  "organization_type": "company",
  "industry": <mv_industry.data>,
  "address": <v_public_address data>,
  "n_direct_allocations": int,
  "n_total_allocations": int,
  "path_of_names": [names],
  "path_of_nodes": [node objects with id, level, name]
}
```

**Refresh Strategy**: 
```
REFRESH mv_industry → mv_count_allocations_by_organization → mv_organization
```

---

##### **mv_count_allocations_by_organizational_unit**
**File**: `02472_mv_count_allocations_by_organizational_unit.sql`

**Purpose**: Aggregated allocation statistics per organizational unit

**Aggregation Pattern**:
```sql
SELECT
  fk_organizational_unit,
  COUNT(*) as total_allocations,
  COUNT(*) FILTER (WHERE end_date IS NULL OR end_date >= CURRENT_DATE) as current_allocations,
  COUNT(*) FILTER (WHERE end_date < CURRENT_DATE) as past_allocations,
  COUNT(DISTINCT fk_machine) as unique_machines,
  MIN(start_date), MAX(COALESCE(end_date, start_date))
FROM tb_allocation
GROUP BY fk_organizational_unit
```

**Indexing Strategy**: 
- Primary index: `idx_mv_count_allocations_by_org_unit_fk` (FK lookup)
- Filtered index: `idx_mv_count_allocations_by_org_unit_current` (active allocations only)

**Used By**: 
- `mv_organization` (dependency)
- Organizational unit analytics
- Dashboard aggregates

---

##### **mv_machine_allocation_summary**
**File**: `02473_mv_machine_allocation_summary.sql`

**Purpose**: Machine-level allocation status and history

**Summary Pattern**:
```sql
SELECT
  fk_machine,
  total_allocations,
  current_allocations,
  CASE WHEN current_allocations > 0 THEN 'ALLOCATED' ELSE 'AVAILABLE' END,
  first_allocation_date,
  last_allocation_date,
  last_deallocation_date
```

**Used By**: Machine lifecycle queries, inventory status views

---

### 5. COMMODITY TABLES (tv_*) - Query Optimization Caching

Denormalized pre-calculated tables for single-object rich queries (vs list queries).

#### Location: `02_query_side/024_dim/`

##### **tv_machine**
**File**: `02458_tv_machine.sql`

**Purpose**: Materialized machine snapshot with rich JSONB data

**Table Structure**:
```sql
CREATE TABLE public.tv_machine (
  id uuid PRIMARY KEY,
  tenant_id uuid,
  fk_customer_org uuid,
  fk_provider_org uuid,
  machine_serial_number TEXT,
  installation_date date,
  installation_year integer,
  removed_at timestamp,
  identifier text,
  machine_item_ids uuid[] (GIN indexed for array search),
  data jsonb (rich nested structure)
)
```

**JSONB Data Structure**:
```json
{
  "contract_id": uuid,
  "order": <order object>,
  "model": <model object>,
  "machine_serial_number": string,
  "customer_machine_id": string,
  "provider_machine_id": string,
  "mac_address": string,
  "delivered_at": ISO8601,
  "installed_at": ISO8601,
  "removed_at": ISO8601,
  "is_current": boolean,
  "is_stock": boolean,
  "is_reserved": boolean,
  "is_unallocated": boolean,
  "n_direct_allocations": int,
  "machine_items": [...],
  "machine_item_bindings": [...],
  "initial_contract": {...},
  "current_contract": {...}
}
```

**Indexing Strategy**:
- `idx_tv_machine_tenant_id` - multi-tenant filtering
- `idx_tv_machine_fk_provider_org` - provider filtering
- `idx_tv_machine_serial_number` - exact match lookup
- `idx_tv_machine_machine_items` - GIN for array containment

**Cache Invalidation**: 
```sql
TRIGGER trg_tv_machine_cache_invalidation
AFTER INSERT OR UPDATE OR DELETE
EXECUTE FUNCTION turbo.fn_tv_table_cache_invalidation()
```

**Update Strategy**: Fine-grained row-level updates (not full refresh)

---

##### **tv_location**
**File**: `02413_tv_location.sql`

**Purpose**: Location hierarchy snapshot with flattened hierarchy metadata

**Key Fields**:
- `path` - ltree hierarchical path
- `location_level_path` - hierarchy level classification
- `is_floor_or_ancestor` - filter flag (excludes sub-floor rooms)
- `int_ordered` - sibling ordering
- `data` - JSONB with path metadata

**Used By**: Location tree rendering, floor-level filtering

---

##### **tv_contract**
**File**: `02448_tv_contract.sql`

**Purpose**: Contract snapshot for rich single-object queries

---

##### **tv_allocation**
**File**: `0252_tv_allocation.sql`

**Purpose**: Allocation status snapshot

---

### 6. COMPOSITION/AGGREGATION VIEWS - Multi-Level Enrichment

Views that compose other views to create richer domain objects.

#### Location: `02_query_side/024_dim/0245_mat/`

##### **v_machine** (Multi-View Composition)
**File**: `02457_v_machine.sql`

**Purpose**: Rich machine view joining multiple related entities

**Composition Pattern**:
```sql
SELECT
  tenant.tb_machine.*,
  v_model.data,
  v_order.data,
  v_current_contract.data,
  v_initial_contract.data,
  v_initial_financing_condition.*,
  v_current_allocations_by_machine.*,
  v_machine_items.data,
  v_machine_item_bindings.data,
  jsonb_build_object(
    'model', v_model.data,
    'order', v_order.data,
    'contract_id', ...,
    'machine_items', v_machine_items.data,
    'machine_item_bindings', v_machine_item_bindings.data,
    'initial_contract', v_initial_contract.data,
    'current_contract', v_current_contract.data
  ) AS data
FROM tenant.tb_machine
  JOIN v_model ON ...
  LEFT JOIN v_order ON ...
  LEFT JOIN v_current_contract ON ...
  LEFT JOIN v_initial_contract ON ...
  LEFT JOIN v_initial_financing_condition ON ...
  LEFT JOIN v_current_allocations_by_machine ON ...
  LEFT JOIN v_machine_items ON ...
  LEFT JOIN v_machine_item_bindings ON ...
```

**View Dependencies** (11 direct dependencies):
1. `v_model` - Product model information
2. `v_order` - Order reference
3. `v_current_contract` - Active contract
4. `v_initial_contract` - Initial contract
5. `v_initial_financing_condition` - First financing terms
6. `v_current_allocations_by_machine` - Current status
7. `v_machine_items` - Installed accessories
8. `v_machine_item_bindings` - Accessory allocations
9. Other implicit views through joins

**Output**: Single JSONB column `data` with complete machine context

**Used By**: 
- `v_machine_detailed` (extension)
- GraphQL machine queries
- Single-machine data loads

---

##### **v_machine_detailed** (Rich Single-Object View)
**File**: `02460_v_machine_detailed.sql`

**Purpose**: Complete machine view with all relationships for single-object GraphQL queries

**Pattern**: Composition of `tv_machine` with nested subqueries:
```sql
SELECT
  m.* FROM tv_machine m,
  (SELECT jsonb_agg(tc.data) FROM tv_contract tc ...) AS contracts,
  (SELECT jsonb_agg(tc.data) FROM tv_contract tc ...) AS successive_contracts,
  (SELECT jsonb_agg(p.data) FROM v_price p ...) AS prices,
  m.data->'machine_items' AS machine_items,
  (SELECT jsonb_build_object(...) FROM tb_volume v ...) AS statistics
```

**Subquery Aggregations**:
- All contracts (many-to-many via tb_machine_contract_relationship)
- Successive applicable contracts (historical chain)
- Applicable prices (contract × model)
- Machine item bindings with status
- Volume statistics (aggregated meters)

**Used By**: Rich GraphQL queries, detailed machine pages

---

##### **v_machine_item** (Translation & Enrichment)
**File**: `02451_v_machine_item.sql`

**Purpose**: Machine accessories with localized categories

**Composition Pattern**:
```sql
SELECT
  tenant.tb_machine_item.*,
  catalog.tb_product.*,
  catalog.tb_accessory.*,
  catalog.tb_item_category.*,
  jsonb_build_object(
    'product_id', fk_product,
    'category', tl_item_category_info.label,
    'name', catalog.tb_accessory.name,
    'reference', catalog.tb_accessory.reference,
    'generic_name', tl_generic_accessory.label,
    'installed_at', to_utc_z(installed_at)
  ) AS data
FROM tb_machine_item
  JOIN tb_product ON ...
  LEFT JOIN tb_accessory ON ...
  JOIN tb_item_category ON ...
  JOIN tb_item_category_info ON ...
  LEFT JOIN tl_item_category_info ON ... WITH LOCALE
  LEFT JOIN tl_accessory ON ... WITH LOCALE
```

**Localization Strategy**: Joins translation tables with locale CTE

---

#### Location: `02_query_side/024_dim/0244_agreement/`

##### **v_contract** (Base Contract Composition)
**File**: `02441_v_contract.sql`

**Purpose**: Contract with client/provider organizations and financing conditions

**Composition Pattern**:
```sql
SELECT
  tenant.tb_contract.*,
  mv_organization v_client.*,
  mv_organization v_provider.*,
  catalog.tb_currency.*,
  jsonb_build_object(
    'client', v_client.data,
    'provider', v_provider.data,
    'financing_conditions', (
      SELECT jsonb_agg(DISTINCT fc.data)
      FROM tb_contract_financing_condition cfc
      JOIN v_financing_condition fc ON ...
    ),
    'has_price_list', EXISTS(...)
  ) AS data
FROM tb_contract
  LEFT JOIN mv_organization v_client ON fk_customer_org
  LEFT JOIN mv_organization v_provider ON fk_provider_org
  LEFT JOIN tb_currency ON fk_currency
```

**Dependencies**: 
- `mv_organization` (materialized)
- `v_financing_condition` (via aggregation subquery)

---

##### **v_contract_with_items** (Extended Contract)
**File**: `0244b_extended/024491_v_contract_with_items.sql`

**Purpose**: Contract with nested contract items

**Pattern**: LEFT JOINs v_contract to aggregate items:
```sql
SELECT
  vc.*,
  jsonb_agg(vci.data) AS contract_items
FROM v_contract vc
LEFT JOIN v_contract_item vci ON vci.fk_contract = vc.id
GROUP BY vc.id
```

**Used By**: Contract detail pages, contract management APIs

---

##### **v_current_contract** (Temporal Filtering)
**File**: `02442_v_current_contract.sql`

**Purpose**: Currently active contracts (simple wrapper with temporal filter)

**Pattern**:
```sql
SELECT * FROM v_contract 
WHERE (start_date <= CURRENT_DATE AND (end_date IS NULL OR end_date >= CURRENT_DATE))
```

---

### 7. AGGREGATION & COMPUTATION VIEWS - Statistics Layer

Views that perform aggregations and computations for analytics.

#### Location: `02_query_side/024_dim/0241_geo/`

##### **v_count_allocations_by_location**
**File**: `02411_v_count_allocations_by_location.sql`

**Purpose**: Allocation counts per location with hierarchy support

**Pattern**: Similar to organizational unit counts:
```sql
SELECT o1.pk_location,
  COALESCE(count(DISTINCT a1.id), 0) AS n_direct_allocations,
  COALESCE(count(DISTINCT a2.id), 0) AS n_total_allocations
FROM tb_location o1
  LEFT JOIN tb_location o2 ON o2.path <@ o1.path (ltree containment)
  LEFT JOIN tb_allocation a1 ON a1.fk_location = o1.pk_location AND ... (date range)
  LEFT JOIN tb_allocation a2 ON a2.fk_organizational_unit = o2.pk_organizational_unit AND ...
GROUP BY o1.pk_location
```

**Used By**:
- `v_location` (dependency)
- Location analytics

---

##### **v_location_coordinates** (Computed Field)
**File**: `024112_v_location_coordinates.sql`

**Purpose**: Extraction of geolocation coordinates from address

**Pattern**:
```sql
SELECT
  pk_location,
  tb_location_info.fk_public_address,
  public.v_public_address.data->>'latitude' as latitude,
  public.v_public_address.data->>'longitude' as longitude
FROM tb_location
  JOIN tb_location_info ON ...
  LEFT JOIN v_public_address ON ...
```

**Used By**: `v_location` (for map embedding)

---

##### **v_location** (Rich Location Composition)
**File**: `02412_v_location.sql`

**Purpose**: Complete location with address, hierarchy, and allocations

**Composition** (130+ lines):
```sql
SELECT
  tenant.tb_location.*,
  v_public_address.data,
  v_count_allocations_by_location.*,
  v_location_coordinates.*,
  jsonb_build_object(
    'address', v_public_address.data,
    'allocations', ...,
    'coordinates', ...
  ) AS data
FROM tb_location
  JOIN tb_location_info ON ...
  JOIN v_public_address ON ... (address enrichment)
  LEFT JOIN v_count_allocations_by_location ON ... (allocation stats)
  LEFT JOIN v_location_coordinates ON ... (coordinates)
```

---

#### Location: `02_query_side/024_dim/0242_org/`

##### **v_count_allocations_by_organizational_unit**
**File**: `02421_v_count_allocations_by_organizational_unit.sql`

**Purpose**: Direct and total allocation counts with ltree hierarchy

**Pattern**: Counts both direct allocations and subtree allocations using ltree path containment

---

##### **v_organizational_unit** (Hierarchical Composition)
**File**: `02422_v_organizational_unit.sql`

**Purpose**: Organizational unit with hierarchy and allocation data

---

##### **v_flat_organizational_unit_for_rust_tree** (Special Pattern)
**File**: `02424_v_flat_organizational_unit_for_rust_tree.sql`

**Purpose**: Flattened organizational hierarchy for Rust tree structures

**Pattern**: UNIONs across multiple hierarchy representations:
```sql
SELECT
  pk_organizational_unit AS id,
  fk_parent_organizational_unit AS parent_id,
  ...
  jsonb_build_object(...) AS data
FROM tb_organizational_unit
  LEFT JOIN v_... ON ...
UNION
-- Alternative flat representation
```

**Used By**: Rust-based tree rendering in backend services

---

#### Location: `02_query_side/024_dim/0246_billing/`

##### **v_machine_price** (Price Information)
**File**: `02461_v_machine_price.sql`

**Purpose**: Current applicable prices for a machine

---

##### **v_contracts_by_machine** (Junction Composition)
**File**: `02462_v_contracts_by_machine.sql`

**Purpose**: All contracts associated with a machine

**Pattern**: Uses `tv_contract` commodity table:
```sql
SELECT
  m.id AS machine_id,
  jsonb_agg(tc.data) AS contracts
FROM tv_machine m
  JOIN tenant.tb_machine_contract_relationship mcr ON m.id = mcr.fk_machine
  JOIN tv_contract tc ON mcr.fk_contract = tc.id
GROUP BY m.id
```

---

#### Location: `02_query_side/024_dim/0247_materialized_views/`

##### **v_count_allocations_optimized** (Optimized Aggregate)
**File**: `02474_v_count_allocations_optimized.sql`

**Purpose**: Unified allocation counts using materialized views with coverage completeness

**Pattern** (UNION ALL pattern):
```sql
SELECT * FROM mv_count_allocations_by_network_configuration
UNION ALL
SELECT nc.pk_network_configuration, 0, 0, 0, NULL, NULL
FROM tb_network_configuration nc
WHERE NOT EXISTS (SELECT 1 FROM mv_count_allocations_by_network_configuration ...)
```

**Purpose of UNION ALL**: Ensures entities with zero allocations are included (ANTI-JOIN pattern)

**Optimization**: Uses materialized view but completes with missing records

---

### 8. STATISTICS & ANALYTICS VIEWS - Cross-Cutting Aggregates

#### Location: `02_query_side/027_fact/0274_stat/`

##### **mv_statistics_for_tree** (Multi-Source Aggregate)
**File**: `02749_mv_statistics_for_tree.sql`

**Purpose**: Cross-domain statistics aggregation (locations + org units)

**Pattern** (UNION ALL of CTEs):
```sql
WITH location_data AS (
  SELECT record.date, parent.id, parent.path,
    sum(record.volume), sum(record.cost)
  FROM tb_statistics_day record
    JOIN tb_location parent ON record.location_path <@ parent.path
  GROUP BY date, parent.id
),
organizational_unit_data AS (
  SELECT record.date, org.id, org.path,
    sum(record.volume), sum(record.cost)
  FROM tb_statistics_day record
    JOIN tb_organizational_unit org ON record.org_path <@ org.path
  GROUP BY date, org.id
)
SELECT * FROM location_data UNION ALL SELECT * FROM organizational_unit_data
```

**Polymorphic Pattern**: Single result set with `source` discriminator column

**Used By**: Analytics dashboards, cost center reporting

---

#### Location: `02_query_side/024_dim/0246_billing/`

##### **mv_maintenance_price** (Specialized Aggregate)
**File**: `02464_mv_maintenance_price.sql`

**Purpose**: Maintenance pricing summary (specialized subset)

---

#### Location: `02_query_side/029_etl/`

##### **mv_financing_cost** (ETL Aggregation)
**File**: `0292_update_statistics/02922_mv_financing_cost.sql`

**Purpose**: Financing cost calculations for ETL pipeline

**Pattern**: Aggregates financing terms with cost calculations

---

### 9. SPECIAL INFRASTRUCTURE VIEWS

#### **v_pk_class_resolver** (Type Resolution)
**File**: `024_dim/0244_agreement/02449_mv_pk_class_resolver.sql`

**Purpose**: Maps primary keys to class/entity types for polymorphic resolution

**Pattern**: UNION across entity tables to create PK → entity type mapping

**Used By**: GraphQL type resolution, polymorphic queries

---

#### **v_turbo_query** (GraphQL Integration)
**File**: `029_graphql/0291_turbo_query/02911_v_turbo_query.sql`

**Purpose**: Integration point for Turbo Router/GraphQL schema

---

---

## BACKBONE VIEW DEPENDENCY GRAPH

### Tier 1: Base Views (Foundational)
```
v_locale, v_industry, v_organization
└─ Direct table wrapping (tb_*)
```

### Tier 2: Utility Views (Cross-Cutting)
```
v_path (UNION of 6+ hierarchies)
  ├─ v_path uses: industry, organization, org_unit, location paths
  
v_public_address (Localization)
  ├─ tb_public_address + tl_* translation tables
  └─ Used by: v_location, mv_organization
```

### Tier 3: Base Materialized Views
```
mv_industry ─── (depends on tb_industry)
  └─ Used by: mv_organization

mv_count_allocations_by_organizational_unit ─── (from tb_allocation)
  └─ Used by: v_organizational_unit, mv_organization

mv_machine_allocation_summary ─── (from tb_allocation)
  └─ Used by: v_machine_detailed, v_count_allocations_optimized
```

### Tier 4: Commodity Tables (tv_*)
```
tv_machine ─── (denormalized from tb_machine + enrichment)
  └─ Used by: v_machine_detailed, v_contracts_by_machine

tv_location ─── (denormalized from tb_location)
  └─ Used by: v_location

tv_contract ─── (denormalized from tb_contract)
  └─ Used by: v_machine_detailed, v_contracts_by_machine

tv_allocation ─── (denormalized from tb_allocation)
  └─ Used by: allocation-related views
```

### Tier 5: Composition Views (Entity Enrichment)
```
v_contract ─────────── (mv_organization, tb_currency)
  ├─ v_contract_with_items (+ contract items aggregation)
  └─ v_current_contract (temporal filter)

v_machine ───────────── (11 view dependencies)
  └─ v_machine_detailed (enriched single-object)

v_location ─────────── (v_public_address, v_count_allocations_by_location)

v_organizational_unit ─ (v_count_allocations_by_organizational_unit)

v_machine_item ──────── (localization, category enrichment)
```

### Tier 6: Specialized Aggregates
```
v_count_allocations_optimized ─ (mv_count_allocations_by_org_unit + completeness)

v_dataflow ──────────────────── (deep nesting, CTE aggregation)

mv_statistics_for_tree ────────── (UNION ALL multi-domain aggregates)

v_flat_organizational_unit_for_rust_tree ─ (specialized tree format)
```

---

## INFRASTRUCTURE PATTERNS IDENTIFIED

### Pattern 1: Soft-Delete Filtering
Consistently applied at base view level:
```sql
WHERE deleted_at IS NULL  -- or IS NULL checks on related entities
```

### Pattern 2: Materialized Views with Refresh Dependencies
```
mv_industry → mv_organization
           ↓
    Refresh order matters - must refresh dependencies first
```

### Pattern 3: FraiseQL JSON Pattern
Views include dual-column pattern:
- Direct columns (for filtering)
- Single JSONB `data` column (for hydration)
```sql
SELECT id, tenant_id, identifier, ... (for filtering)
SELECT jsonb_build_object(...) AS data (for hydration)
```

### Pattern 4: Temporal Filtering
Current/active record filtering:
```sql
WHERE (start_date <= CURRENT_DATE AND (end_date IS NULL OR end_date >= CURRENT_DATE))
```

### Pattern 5: Localization with Fallback
```sql
COALESCE(tl_translation.label, tb_base.name) -- French first, fallback to base
```

### Pattern 6: Hierarchical Path Operations
Heavy use of ltree:
```sql
LEFT JOIN parent ON child.path <@ parent.path  -- containment
ORDER BY nlevel(path)  -- depth-first
```

### Pattern 7: Array Aggregation for Nested Lists
```sql
jsonb_agg(jsonb_build_object(...) ORDER BY ...)
array_agg(name ORDER BY ...)
```

### Pattern 8: View Composition via JOIN
Higher-level views compose lower-level views rather than tables:
```sql
FROM tb_machine
  JOIN v_model ON ...        -- composing v_model
  LEFT JOIN v_order ON ...   -- composing v_order
  LEFT JOIN v_current_contract ON ... -- composing v_current_contract
```

### Pattern 9: Subquery Aggregation for Many-to-Many
```sql
(SELECT jsonb_agg(...)
 FROM junction_table jt
 JOIN related_table rt ON ...
 WHERE jt.parent_id = outer.id
) AS aggregated_children
```

### Pattern 10: Cache Invalidation Triggers
```sql
CREATE TRIGGER trg_tv_table_cache_invalidation
AFTER INSERT OR UPDATE OR DELETE ON table
EXECUTE FUNCTION turbo.fn_tv_table_cache_invalidation()
```

---

## SUMMARY: INFRASTRUCTURE LAYERS

| Layer | Type | Purpose | Examples | Count |
|-------|------|---------|----------|-------|
| **1. Base** | Views | Table wrapping + soft-delete | v_locale, v_industry, v_organization | 3 |
| **2. Utility** | Views | Cross-cutting infrastructure | v_path, v_public_address, v_dataflow | 3 |
| **3. Materialized** | MVs | Performance caching | mv_industry, mv_organization, mv_machine_allocation_summary | 10+ |
| **4. Commodity** | Tables | Query optimization | tv_machine, tv_location, tv_contract | 10+ |
| **5. Composition** | Views | Multi-view enrichment | v_machine, v_contract, v_location | 15+ |
| **6. Aggregation** | Views | Statistics/analytics | v_count_allocations_*, mv_statistics_for_tree | 10+ |
| **7. Special** | Views | Type resolution, tree formats | v_pk_class_resolver, v_flat_organizational_unit_for_rust_tree | 5+ |

**Total Backbone Infrastructure Views**: ~50-60 views
**Total Domain-Specific Views**: ~40 views (entity-mapped)

---

## KEY FINDINGS

### Cross-Cutting Concerns
1. **Hierarchy Management**: v_path unifies all hierarchical queries
2. **Localization**: Consistent COALESCE pattern for French/default fallback
3. **Allocation Tracking**: mv_count_allocations_by_* used across multiple domains
4. **Temporal Queries**: Current/active record filtering widespread
5. **Denormalization**: Commodity tables pre-compute expensive joins

### Composition Layers
- Views compose other views, not tables (higher layers)
- Materialized views used for expensive aggregations
- Commodity tables (tv_*) bridge transactional and query sides
- Deep nesting via JSONB for single-object rich queries

### Performance Strategies
1. Materialized view refresh ordering
2. Fine-grained index design (GIN for arrays, filtered indexes)
3. Cache invalidation triggers for commodity tables
4. FraiseQL pattern (dual columns) for efficient filtering/hydration

### Design Patterns
- Polymorphic queries (v_path, v_statistics_for_tree)
- Hierarchical traversal (ltree + path containment)
- Soft deletes (consistent deleted_at filtering)
- View composition chains (5+ levels deep)

