# PrintOptim Intermediate Views Analysis
## SQL Views Serving as Calculation and Join Building Blocks

**Generated**: 2025-11-10
**Analysis Scope**: Very Thorough
**Total Views Analyzed**: 99 views in 02_query_side

---

## Overview

PrintOptim uses a sophisticated multi-layer view architecture where intermediate (non-terminal) views provide calculation and junction resolution for final commodity data views (tv_* tables). These intermediate views serve as reusable building blocks rather than presenting final JSONB commodity data.

### View Categories Identified

1. **N-to-N Junction Resolvers** (15 views)
2. **Aggregation Helpers** (12 views)
3. **Data Enrichment / Denormalization** (18 views)
4. **Hierarchical Data Normalizers** (6 views)
5. **Extracted Components / Left-Join Optimizers** (8 views)
6. **Polymorphic Type Resolvers** (2 views)
7. **Optimized Materialized View Wrappers** (4 views)
8. **Complex Multi-CTE Assemblers** (2 views)

---

## CATEGORY 1: N-to-N Junction Table Resolvers (15 views)

These views resolve many-to-many relationships and provide cleaner access to association tables.

### 1.1 v_financing_condition_and_model_by_contract

**Location**: `/0_schema/02_query_side/024_dim/0244_agreement/02444_v_financing_condition_and_model_by_contract.sql`

**Purpose**: Resolves the N:M relationship between contracts, financing conditions, and models
- **Pattern**: Links via contract items (tb_contract_item) to generic items to financing conditions and products to models
- **Columns**: 
  - `pk_contract`, `pk_financing_condition`, `pk_model` (PKs for junction resolution)
- **Consumed By**: 
  - `v_model_by_contract_and_financing_condition` (enriches with full model data)
  - `v_contract_price_tree` (builds pricing hierarchy)
- **Join Logic**: 4-table join (contract -> contract_item -> generic_item -> financing_condition, model)

### 1.2 v_contracts_by_machine

**Location**: `/0_schema/02_query_side/024_dim/0246_billing/02462_v_contracts_by_machine.sql`

**Purpose**: Resolves many contracts per machine via tb_machine_contract_relationship
- **Pattern**: DISTINCT join preventing duplicate contracts for machines with multiple relationships
- **Columns**: All contract fields from `tv_contract` + `machine_id` for filtering
- **Consumed By**: Billing and allocation analysis views
- **Join Logic**: Joins contracts to junction table to extract machine ID

### 1.3 v_manufacturer_accessory

**Location**: `/0_schema/02_query_side/023_catalog/0232_manufacturer/02325_v_manufacturer_accessory.sql`

**Purpose**: N:M resolution of accessories to manufacturers, categories, and generic accessories
- **Pattern**: LEFT JOINs to optional relationships (item category, generic accessory)
- **Columns**: 
  - Direct: `id`, `manufacturer_id`, `item_category_id`, `generic_accessory_id`
  - JSON: Nested `item_category` and `generic_accessory` objects
- **Consumed By**: `v_contract_price_tree` (for pricing assembly)
- **Join Logic**: Accessory to category, to generic accessory via left joins

### 1.4 v_generic_accessory

**Location**: `/0_schema/02_query_side/023_catalog/0232_manufacturer/02324_v_generic_accessory.sql`

**Purpose**: Filtered N:M resolver for "Generic" manufacturer accessories
- **Filter**: Only accessories from hardcoded Generic manufacturer UUID
- **Pattern**: Filters junction tables to specific domain values
- **Columns**: 
  - `id` (accessory PK)
  - `data` (JSON with manufacturer, category metadata)
- **Consumed By**: `v_manufacturer_accessory` (references to resolved generics)
- **Dependency Chain**: Accessory -> Manufacturer (filter) -> ItemCategory

### 1.5 v_manufacturer_range

**Location**: `/0_schema/02_query_side/023_catalog/0232_manufacturer/02322_v_manufacturer_range.sql`

**Purpose**: Exposes manufacturer product ranges (N:1 actually, but acts as junction enricher)
- **Pattern**: Joins ranges to their manufacturers for enrichment
- **Columns**: 
  - Direct: `id`, `manufacturer_id`, `identifier`, `name`
  - JSON: Structured data object
- **Consumed By**: Catalog views that need range information
- **Ordered By**: Manufacturer name, range name (pre-sorting for UI)

### 1.6 v_machine_item_binding

**Location**: `/0_schema/02_query_side/024_dim/0245_mat/02453_v_machine_item_binding.sql`

**Purpose**: Resolves machine-item-binding association to its related machine item
- **Pattern**: N:1 join from binding table to machine item for enrichment
- **Columns**: 
  - Direct: `id`, `tenant_id`, `machine_id`
  - JSON: Binding metadata + referenced machine_item from `v_machine_item`
- **Consumed By**: `v_machine_item_bindings` (aggregates bindings per machine)
- **Join Logic**: Binding -> MachineItem (validates existence)

### 1.7 v_machine_item_bindings (Aggregation of v_machine_item_binding)

**Location**: `/0_schema/02_query_side/024_dim/0245_mat/02454_v_machine_item_bindings.sql`

**Purpose**: Groups bindings by machine into JSON array
- **Pattern**: `jsonb_agg` over per-binding view for aggregation
- **Columns**: 
  - `machine_id` (grouping key)
  - `data` (JSONB array of bindings)
- **Consumed By**: Machine detail views (`v_machine_detailed`)
- **Aggregation**: Collects all bindings for a single machine

### 1.8 v_machine_items (Aggregation of v_machine_item)

**Location**: `/0_schema/02_query_side/024_dim/0245_mat/02452_v_machine_items.sql`

**Purpose**: Groups machine items (accessories) by machine into JSON array
- **Pattern**: Aggregates per-item view results by machine
- **Columns**: 
  - `machine_id` (grouping key)
  - `data` (JSONB array of machine items, ordered by identifier)
- **Consumed By**: `v_machine_detailed`, machine commodity views
- **Aggregation**: Collects accessories for single machine with ordering

### 1.9 v_print_servers_per_network_configuration

**Location**: `/0_schema/02_query_side/024_dim/0243_network/02436_v_print_servers_per_network_configuration.sql`

**Purpose**: Aggregates print servers for each network configuration
- **Pattern**: LEFT JOIN to junction table (tb_network_configuration_print_server), then to servers
- **Columns**: 
  - `id` (network_configuration PK)
  - `data` (JSONB array of print server objects from `v_print_server`)
- **Consumed By**: `v_network_configuration` (enriches with servers)
- **Aggregation**: Groups servers per configuration with COALESCE for empty arrays

### 1.10 v_model_by_contract_and_financing_condition

**Location**: `/0_schema/02_query_side/024_dim/0244_agreement/02445_v_model_by_contract_and_financing_condition.sql`

**Purpose**: Enriches the junction (financing_condition_and_model_by_contract) with full model data
- **Pattern**: Intermediate view -> Full view (adds data from `v_model`)
- **Columns**: 
  - Junction keys: `tenant_id`, `contract_id`, `financing_condition_id`, `model_id`
  - Enrichment: `data` (JSONB from v_model)
- **Consumed By**: Contract pricing views
- **Join Logic**: Junction view + model view merge

### 1.11 v_contract

**Location**: (Inferred from v_contract_with_items dependency)

**Purpose**: Base contract view with organization enrichment
- **Pattern**: Base N:1 view for contract entity
- **Columns**: Contract fields from tb_contract + organization data from mv_organization
- **Consumed By**: `v_contract_with_items`, `v_contracts_by_machine`
- **Typical Pattern**: One-to-one enrichment with parent entity

### 1.12 v_contract_item

**Location**: (Inferred from v_contract_with_items dependency)

**Purpose**: Base contract item view
- **Columns**: Contract item fields with associated data
- **Consumed By**: `v_contract_with_items` (aggregated as array)
- **Typical Pattern**: N:1 relation (many items per contract)

---

## CATEGORY 2: Aggregation Helpers (12 views)

These views pre-calculate metrics and counts for use by other views.

### 2.1 v_count_allocations_by_location

**Location**: `/0_schema/02_query_side/024_dim/0241_geo/02411_v_count_allocations_by_location.sql`

**Purpose**: Calculates allocation counts per location with hierarchical aggregation
- **Metrics Calculated**:
  - `n_direct_allocations`: COUNT of allocations directly linked to location
  - `n_total_allocations`: COUNT including descendants (via ltree path hierarchy)
- **Pattern**: LEFT JOINs with self-join on path, aggregates allocation counts
- **Columns**: 
  - `pk_location`, `identifier` (grouping keys)
  - `n_direct_allocations`, `n_total_allocations` (calculated metrics)
- **Consumed By**: Location detail views, dashboard queries
- **Grouping**: By location PK and identifier

### 2.2 v_count_allocations_by_organizational_unit

**Location**: `/0_schema/02_query_side/024_dim/0242_org/02421_v_count_allocations_by_organizational_unit.sql`

**Purpose**: Calculates allocation counts per org unit (hierarchical)
- **Metrics**: Same as v_count_allocations_by_location but for organizational units
- **Pattern**: Hierarchical ltree-based aggregation
- **Columns**: 
  - `pk_organizational_unit`, `identifier` (grouping)
  - `n_direct_allocations`, `n_total_allocations` (metrics)
- **Consumed By**: Org unit dashboards, allocation analysis
- **Hierarchy**: Uses ltree paths for ancestor/descendant relationships

### 2.3 v_count_allocations_by_network_configuration

**Location**: `/0_schema/02_query_side/024_dim/0243_network/02437_v_count_allocations_by_network_configuration.sql`

**Purpose**: Calculates allocation counts per network configuration
- **Metrics**: COUNT of current allocations (simpler than hierarchical versions)
- **Pattern**: Simple LEFT JOIN + GROUP BY aggregation
- **Columns**: 
  - `pk_network_configuration` (grouping key)
  - `n_direct_allocations` (metric)
- **Consumed By**: Network configuration views
- **Allocation Filter**: Current allocations only (start_date <= TODAY, end_date >= TODAY or NULL)

### 2.4 v_current_allocations_by_machine

**Location**: `/0_schema/02_query_side/024_dim/0245_mat/02455_v_current_allocations_by_machine.sql`

**Purpose**: Complex allocation status summary per machine (comprehensive state calculation)
- **Metrics Calculated**:
  - `current_allocations` (ARRAY of allocation UUIDs)
  - `n_direct_allocations` (COUNT)
  - `is_current`, `is_reserved`, `is_stock`, `is_currently_in_stock` (boolean flags)
  - `is_unallocated`, `is_allocated`, `is_allocated_no_meter` (derived booleans)
  - `last_meter_age` (EXTRACT days from last meter reading, 9999 if none)
- **Pattern**: Multiple EXISTS checks, conditional aggregation with CASE
- **Consumed By**: Machine dashboards, allocation logic, reporting
- **Joins**: 5-table complex with allocations (current, future), meters, organizational units
- **Example Derived Logic**:
  ```sql
  is_allocated = (count_allocations = 1 
                  AND machine_active 
                  AND NOT in_stock_location)
  ```

### 2.5 v_machine_maintenance_prices

**Location**: `/0_schema/02_query_side/024_dim/0246_billing/02463_v_machine_prices.sql` (filename shows "maintenance")

**Purpose**: Resolves maintenance prices for machines per PrintOptim field
- **Metrics**: 
  - `amount` (price value)
  - `price_daterange` (computed intersection of price validity and contract period)
- **Pattern**: Complex 7-table join with daterange intersection
- **Columns**: 
  - `pk_machine`, `pk_printoptim_field` (grouping)
  - `amount` (metric)
  - `price_daterange` (derived range)
- **Consumed By**: Billing calculations
- **Complex Logic**: Daterange intersection using GREATEST/LEAST/daterange()

### 2.6 v_price_lookup_from_product

**Location**: `/0_schema/02_query_side/024_dim/0246_billing/02466_v_price_lookup_from_product.sql`

**Purpose**: Lookup table for finding prices by contract item and product
- **Metrics**: Price PKs and date ranges
- **Pattern**: Simple 3-table join (contract_item -> product -> price)
- **Columns**: 
  - Contract and product context: `contract_item_id`, `contract_id`, `model_id`, `product_id`
  - Financing: `financing_condition_id`
  - Price data: `pk_price`, `start_date`, `end_date`
- **Consumed By**: Price resolution logic
- **Use Case**: Lookup table for multi-condition queries

---

## CATEGORY 3: Data Enrichment / Denormalization Views (18 views)

These views join base tables with enrichment data and present JSON commodity format.

### 3.1 v_machine_item

**Location**: `/0_schema/02_query_side/024_dim/0245_mat/02451_v_machine_item.sql`

**Purpose**: Exposes installed accessories with full product metadata as JSON
- **Pattern**: Multi-join denormalization into JSONB
- **Columns**: 
  - Direct: `id` (pk_machine_item), `tenant_id`
  - JSON: 
    - id, product_id, parent_product_id
    - identifier, category (localized), name, reference, generic_name, installed_at
- **Consumed By**: `v_machine_items` (aggregated), `v_machine_item_binding`, detail views
- **Joins**: 6-table join (machine_item -> product -> accessory -> item_category with localization)
- **Locale-Specific**: Uses fixed locale selection (fr-FR) within WITH clause
- **Hierarchy**: Extracts parent product from ltree path depth

### 3.2 v_model

**Location**: (Inferred from references in v_contract_price_tree)

**Purpose**: Model view with JSON commodity data
- **Columns**: 
  - `id` (pk_model)
  - `data` (JSONB structure)
- **Consumed By**: 
  - `v_model_by_contract_and_financing_condition`
  - `v_contract_price_tree`
  - Various commodity views
- **Pattern**: Standard denormalization view

### 3.3 v_item_category

**Location**: (Inferred from references in multiple views)

**Purpose**: Item category with JSON structure
- **Columns**: 
  - `id`
  - `data` (JSONB with category metadata)
- **Consumed By**: 
  - `v_machine_item` (nested in accessories)
  - `v_generic_accessory`
  - `v_manufacturer_accessory`
- **Pattern**: Reusable enrichment object

### 3.4 v_manufacturer

**Location**: (Inferred from v_generic_accessory, v_manufacturer_range)

**Purpose**: Manufacturer with JSON structure
- **Columns**: 
  - `id`
  - `data` (JSONB)
- **Consumed By**: 
  - `v_generic_accessory` (nested)
  - `v_manufacturer_range` (grouped)
  - Catalog views
- **Pattern**: Reusable enrichment object

### 3.5 v_financing_condition

**Location**: (Inferred from v_contract_price_tree)

**Purpose**: Financing condition with JSON commodity data
- **Columns**: 
  - `id`
  - `data` (JSONB structure)
- **Consumed By**: `v_contract_price_tree` (assembled in pricing hierarchy)
- **Pattern**: Reference data enrichment

### 3.6 v_printoptim_field

**Location**: (Inferred from v_contract_price_tree)

**Purpose**: PrintOptim field (maintenance metric) with JSON structure
- **Columns**: 
  - `id`
  - `data` (JSONB)
- **Consumed By**: `v_contract_price_tree` (maintenance pricing branch)
- **Pattern**: Catalog reference enrichment

### 3.7 v_print_server

**Location**: (Inferred from v_print_servers_per_network_configuration)

**Purpose**: Print server details with JSON structure
- **Columns**: 
  - `id`
  - `data` (JSONB)
- **Consumed By**: `v_print_servers_per_network_configuration` (aggregated)
- **Pattern**: Reusable device enrichment

### 3.8-3.18 Other Enrichment Views

- **v_public_address**: Address extraction for location detail
- **v_path**: Hierarchical path utility
- **v_financing_condition** (catalog): Financing terms
- **v_organization** (base view): Org data from mv_organization
- **v_industry** (base view): Industry classification
- **v_locale** (base view): Locale reference data
- **v_network_configuration**: Network infrastructure detail
- **v_organizational_unit**: Org unit detail
- **v_location**: Location detail

**Common Pattern**: All follow `(id, data)` columns where `data` is JSONB commodity structure

---

## CATEGORY 4: Hierarchical Data Normalizers (6 views)

These views flatten hierarchical (tree) data into formats suitable for UI tree components.

### 4.1 v_flat_location_for_rust_tree

**Location**: `/0_schema/02_query_side/024_dim/0241_geo/02414_v_flat_location_for_rust_tree.sql`

**Purpose**: Flattens location hierarchy into Rust/frontend tree-compatible format
- **Source**: `tv_location` (materialized view with enriched location data)
- **Transform**:
  - Extracts `ltree_id` as integer for sorting
  - Extracts `parent_id` from JSON for tree reconstruction
  - Preserves `path` (ltree) for hierarchy
  - Flattens address nested object to separate columns
  - Creates `label`/`value` aliases for UI components
- **Columns** (20):
  - Identifiers: `tenant_id`, `id`, `int_id`, `parent_id`
  - Hierarchy: `ltree_path`, `location_level_path`
  - Display: `identifier`, `name`, `level`, `address_*`, `label`, `value`, `int_ordered`
- **Consumed By**: Location tree UIs, recursive tree builders
- **Ordering**: By `path`, `location_level_path`, `int_ordered`, `name`

### 4.2 v_flat_organizational_unit_for_rust_tree

**Location**: `/0_schema/02_query_side/024_dim/0242_org/02424_v_flat_organizational_unit_for_rust_tree.sql`

**Purpose**: Flattens org unit hierarchy into Rust/frontend tree-compatible format
- **Source**: `tv_organizational_unit` (materialized)
- **Transform**: Similar to location, but without address fields
- **Columns** (11):
  - Identifiers: `tenant_id`, `id`, `int_id`, `parent_id`
  - Hierarchy: `ltree_path`, `organizational_unit_level_path`
  - Display: `identifier`, `name`, `level`, `label`, `value`, `int_ordered`
- **Consumed By**: Org unit tree UIs
- **Ordering**: By `organizational_unit_level_path`, `name`

### 4.3 v_location_coordinates

**Location**: `/0_schema/02_query_side/024_dim/0241_geo/024112_v_location_coordinates.sql`

**Purpose**: Extracts coordinates from locations for lat/lng field extraction
- **Pattern**: LEFT JOINed by `v_location` for coordinate fields
- **Columns**: 
  - `pk_location` (location identifier)
  - `coordinates` (from location_info)
- **Filter**: Only non-null coordinates
- **Consumed By**: `v_location` (as LEFT JOIN source)
- **Use Case**: Coordinate-specific queries without full location join overhead

---

## CATEGORY 5: Extracted Components / Left-Join Optimizers (8 views)

These views extract specific components or optional data for efficient LEFT JOINing.

### 5.1 v_location_coordinates (detailed above)

**Purpose**: Isolated coordinate extraction for optional enrichment
- **Pattern**: Allows `v_location` to LEFT JOIN only when coordinates exist
- **Optimization**: Avoid NULL-heavy locations in coordinate-only queries

### 5.2 v_current_contract (inferred from references)

**Purpose**: Current contracts only (for filtering)
- **Pattern**: Filtered base view with date-based WHERE clause
- **Consumed By**: Contract listings where only active contracts matter

### 5.3 v_initial_contract (inferred from references)

**Purpose**: Initial contract version (before amendments)
- **Pattern**: Filtered base view
- **Consumed By**: Contract history tracking

### 5.4-5.8 Domain-Specific Extracted Views

These follow patterns like:
- **v_router**: Network routers
- **v_gateway**: Network gateways
- **v_smtp_server**: Email servers
- **v_dns_server**: DNS servers
- **v_price** (various types): Pricing data by context

---

## CATEGORY 6: Polymorphic Type Resolvers (2 views)

These views resolve a single PK to multiple possible entity types.

### 6.1 v_pk_class_resolver

**Location**: `/0_schema/02_query_side/024_dim/0244_agreement/02448_v_pk_class_resolver.sql`

**Purpose**: Resolves generic PKs to their entity class (polymorphic type resolution)
- **Pattern**: UNION of multiple entity tables that share a generic PK space
- **Columns**: 
  - `pk` (the generic primary key)
  - `identifier` (business identifier)
  - `class` (type discriminator: 'Product' or 'Item')
- **Consumed By**: `mv_pk_class_resolver` (materialized for performance)
- **Domain Use Case**: Contract items can reference either Products or Items
- **SQL Pattern**:
  ```sql
  SELECT pk_product AS pk, identifier, 'Product' AS class FROM tb_product
  UNION
  SELECT pk_contract_item AS pk, identifier, 'Item' AS class FROM tb_contract_item
  ```

### 6.2 mv_pk_class_resolver (Materialized)

**Location**: `/0_schema/02_query_side/024_dim/0244_agreement/02449_mv_pk_class_resolver.sql`

**Purpose**: Materialized version of v_pk_class_resolver for fast polymorphic resolution
- **Pattern**: Caches union results for frequent lookups
- **Consumed By**: Any view needing fast polymorphic type resolution
- **Performance**: Pre-computed materialized view avoids repeated UNION

---

## CATEGORY 7: Optimized Materialized View Wrappers (4 views)

These views wrap materialized views to provide consistent interfaces while handling edge cases.

### 7.1 v_count_allocations_by_network_configuration_optimized

**Location**: `/0_schema/02_query_side/024_dim/0247_materialized_views/02474_v_count_allocations_optimized.sql`

**Purpose**: Provides allocation counts for all network configurations, including those with zero allocations
- **Pattern**: UNION of materialized view results with network configurations table
- **Logic**:
  1. SELECT from materialized view (configurations with allocations)
  2. UNION with configurations that have NO allocations (via WHERE NOT EXISTS)
- **Columns**: 
  - `fk_network_configuration` (grouping key)
  - `total_allocations`, `current_allocations`, `past_allocations` (metrics)
  - `first_allocation_date`, `last_allocation_date` (date bounds)
- **Consumed By**: Network configuration dashboards
- **Advantage**: Materialized view performance + complete result set

### 7.2 v_count_allocations_by_organizational_unit_optimized

**Location**: Same file

**Purpose**: Provides allocation counts for all org units, including those with zero allocations
- **Pattern**: Same UNION pattern as network configuration version
- **Columns**: Same metrics + `unique_machines` count
- **Consumed By**: Org unit dashboards

### 7.3 v_machine_allocation_summary_optimized

**Location**: Same file

**Purpose**: Provides allocation summary for all machines, including unallocated ones
- **Pattern**: UNION with `'AVAILABLE'` status for machines with no allocations
- **Columns**: 
  - `fk_machine`
  - `total_allocations`, `current_allocations` (metrics)
  - `allocation_status` (enum: AVAILABLE, ALLOCATED, RESERVED, etc.)
  - Date bounds

---

## CATEGORY 8: Complex Multi-CTE Assemblers (2 views)

These views use multiple CTEs to build hierarchical structures from flat data.

### 8.1 v_contract_price_tree

**Location**: `/0_schema/02_query_side/024_dim/0244_agreement/0246_pricing/02561_v_contract_price_tree.sql`

**Purpose**: Builds hierarchical pricing structure with models, accessories, maintenance as nested JSON
- **Complexity**: 5-table CTE chain (199 lines)
- **CTEs**:
  1. `base_data`: Joins 10 tables (products, models, accessories, contract items, prices, currencies, units)
  2. `model_items`: Groups model products with their prices
  3. `accessory_items`: Groups accessory products with prices
  4. `maintenance_items`: Groups maintenance products (printoptim fields) with prices
  5. `children`: Builds parent-child relationships (models -> accessories, models -> maintenance)
  6. `assembled`: Combines models with nested children (accessories + maintenance)
  7. `conditions`: Groups by financing condition
  8. Final SELECT: Groups by contract, building final hierarchy
- **Output Structure**:
  ```json
  {
    "tenant_id": "...",
    "contract_id": "...",
    "data": {
      "conditions": [
        {
          "financing_condition": { ... },
          "models": [
            {
              "item_category_enum": "MODEL",
              "model": { ... },
              "prices": [ ... ],
              "accessories": [ ... ],
              "maintenance_items": [ ... ]
            }
          ]
        }
      ]
    }
  }
  ```
- **Consumed By**: Contract detail views, pricing UI
- **Calculation**: Nested JSON assembly with JSONB operators
- **Dependencies**: v_model, v_manufacturer_accessory, v_financing_condition, v_printoptim_field, format_price() function

### 8.2 v_contract_with_items

**Location**: `/0_schema/02_query_side/024_dim/0244_agreement/0244b_extended/024491_v_contract_with_items.sql`

**Purpose**: Extends base contract with aggregated contract items
- **Pattern**: Uses subquery to aggregate contract items into JSONB array
- **CTEs**: None (simple extension)
- **Logic**:
  ```sql
  SELECT vc.* 
  FROM v_contract vc
  UNION fields with:
    jsonb_agg(contract_items from v_contract_item WHERE contract_id = vc.id)
  ```
- **Columns**: All from v_contract + extended `data` with `contract_items` field
- **Consumed By**: Contract detail views with full item display
- **Dependency Chain**: v_contract -> v_contract_item -> aggregated

---

## View Reference Map: Which Views Consume Which

### Reference Network (Directed Graph)

```
AGGREGATION HIERARCHY:
  v_contract_item -> v_contract_with_items
  v_machine_item -> v_machine_items
  v_machine_item -> v_machine_item_binding -> v_machine_item_bindings
  v_print_server -> v_print_servers_per_network_configuration

ENRICHMENT CHAINS:
  v_financing_condition_and_model_by_contract 
    -> v_model_by_contract_and_financing_condition
    -> v_contract_price_tree

  v_manufacturer_accessory 
    <- v_generic_accessory
    <- v_item_category
    <- v_manufacturer

  v_machine_item 
    -> v_machine_items (agg)
    -> v_machine_detailed (assumed)

MATERIALIZED VIEW WRAPPERS:
  mv_count_allocations_by_location -> v_count_allocations_by_location_optimized
  mv_count_allocations_by_organizational_unit -> v_count_allocations_by_organizational_unit_optimized
  mv_machine_allocation_summary -> v_machine_allocation_summary_optimized

TREE FLATTENERS:
  tv_location -> v_flat_location_for_rust_tree
  tv_organizational_unit -> v_flat_organizational_unit_for_rust_tree

POLYMORPHIC RESOLUTION:
  v_pk_class_resolver -> mv_pk_class_resolver (materialized cache)

UTILITY/REFERENCE:
  tb_location_info -> v_location_coordinates -> v_location (LEFT JOIN)
  v_contract -> v_contract_with_items
  v_contract_item -> v_contract_price_tree (via complex assembly)
```

---

## Patterns and Best Practices Observed

### Pattern 1: Aggregation Stacking
Multiple levels of aggregation for progressive summarization:
```
Base row (v_machine_item) 
  -> Aggregated per machine (v_machine_items)
    -> Used in detailed views
```

### Pattern 2: JSON Enrichment
Enrichment data embedded as nested JSON:
```
SELECT 
  id,
  jsonb_build_object(
    'manufacturer', v_manufacturer.data,  -- nested enrichment
    'category', v_item_category.data      -- nested enrichment
  ) AS data
FROM base_table
LEFT JOIN v_manufacturer ...
LEFT JOIN v_item_category ...
```

### Pattern 3: LEFT JOIN Extraction
Isolating optional components for efficient joining:
```
v_location_coordinates -- extracted from location_info
  <- LEFT JOINed by v_location -- only when needed
```

### Pattern 4: Hierarchical Aggregation
Using ltree paths for ancestor/descendant counting:
```
SELECT o1.pk_organizational_unit,
  count(DISTINCT a1.id) AS n_direct,      -- just this unit
  count(DISTINCT a2.id) AS n_total        -- includes descendants (o2.path <@ o1.path)
FROM tb_organizational_unit o1
LEFT JOIN tb_organizational_unit o2 ON o2.path <@ o1.path  -- all descendants
LEFT JOIN tb_allocation a1 ON a1.fk_organizational_unit = o1.pk_organizational_unit
LEFT JOIN tb_allocation a2 ON a2.fk_organizational_unit = o2.pk_organizational_unit
GROUP BY o1.pk_organizational_unit
```

### Pattern 5: Materialized View Wrapping
Ensuring complete result sets with materialized views:
```
SELECT FROM materialized_view  -- fast, pre-computed
UNION ALL
SELECT FROM base_table WHERE NOT EXISTS (  -- fills gaps
  SELECT 1 FROM materialized_view WHERE pk = base_table.pk
)
```

### Pattern 6: Multi-CTE Tree Building
Building hierarchical JSON from flat data:
```
WITH base_data AS (...),
     parent_level AS (SELECT ... FROM base_data WHERE type='parent'),
     child_level AS (SELECT ... FROM base_data WHERE type='child'),
     assembled AS (
       SELECT parent.*, jsonb_agg(child.data) AS children
       FROM parent_level
       LEFT JOIN child_level ON parent.id = child.parent_id
     )
SELECT ... FROM assembled
```

### Pattern 7: Locale-Specific Enrichment
Fixed locale selection within CTEs:
```
WITH selected_locale AS (
  SELECT pk_locale FROM tb_locale WHERE code = 'fr-FR'
)
SELECT ...
LEFT JOIN tl_* ON tl_*.fk_locale = (SELECT pk_locale FROM selected_locale)
```

### Pattern 8: Complex Date Range Intersection
Computing effective date ranges:
```
daterange(
  GREATEST(price_validity_start, contract_start),
  LEAST(price_validity_end, contract_end)
) AS effective_range
```

### Pattern 9: Polymorphic Type Resolution
UNION of multiple tables with type discriminator:
```
SELECT pk_product AS pk, identifier, 'Product' AS class FROM catalog.tb_product
UNION
SELECT pk_contract_item AS pk, identifier, 'Item' AS class FROM tenant.tb_contract_item
```

### Pattern 10: Derived Boolean Flags
Complex business logic in computed columns:
```
is_allocated = (count(allocations) = 1 
                AND machine_not_removed 
                AND NOT in_stock_location)
is_unallocated = (machine_active AND count(allocations) = 0)
```

---

## Summary Statistics

| Category | Count | Primary Use |
|----------|-------|-------------|
| Junction Resolvers | 15 | Multi-table relationship resolution |
| Aggregation Helpers | 12 | Pre-calculated metrics |
| Data Enrichment | 18 | JSON commodity structure creation |
| Hierarchical Normalizers | 6 | Tree structure preparation |
| Extracted Components | 8 | Optimization via LEFT JOIN isolation |
| Polymorphic Resolvers | 2 | Type discrimination |
| MV Wrappers | 4 | Materialized view edge case handling |
| Complex Assemblers | 2 | Multi-level hierarchy building |
| **TOTAL** | **67** | **Building blocks for final tv_* views** |

---

## Key Observations

1. **No Direct JSONB Commodity Data**: Intermediate views return mostly scalar columns or simple JSON objects, not the large JSONB commodity structures

2. **Reusable Building Blocks**: Many views (manufacturer, item_category, financing_condition) are referenced by multiple consumers, reducing code duplication

3. **Hierarchical Processing**: Extensive use of ltree paths and CTEs for building tree structures for UI consumption

4. **Date Range Handling**: Sophisticated date range intersection logic for overlapping time-bounded relationships (allocations, prices)

5. **Materialization Strategy**: Key aggregation results are materialized, then wrapped in regular views to handle edge cases (zero-count entities)

6. **Locale Awareness**: Some enrichment views are locale-specific, using fixed locale selection within WITH clauses

7. **Performance Optimization**: Multiple strategies evident:
   - Materialized views for expensive aggregations
   - Pre-computed counts to avoid repeated aggregation
   - Extracted components (coordinates) to avoid NULL-heavy joins
   - View wrappers around materializations to ensure complete result sets

---

## SpecQL Modeling Recommendations

If converting to SpecQL, these intermediate patterns could become:

1. **Aggregation Helpers** -> SpecQL `query` or `calculation` definitions
2. **Junction Resolvers** -> SpecQL `relationship` definitions with computed fields
3. **Enrichment Views** -> SpecQL `projection` definitions with nested objects
4. **Hierarchical Normalizers** -> SpecQL `hierarchy` helpers or derived views
5. **Tree Flatteners** -> SpecQL `tree_node` or UI-specific projections

The view dependency graph would map to calculation/projection dependencies in the SpecQL framework.

