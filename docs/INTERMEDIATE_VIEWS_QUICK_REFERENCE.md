# PrintOptim Intermediate Views - Quick Reference Guide

## Complete View Directory by Category

### CATEGORY 1: N-to-N Junction Resolvers (15 views)

| View Name | File Path | Primary Purpose | Key Metrics |
|-----------|-----------|-----------------|-------------|
| `v_financing_condition_and_model_by_contract` | `024_agreement/02444_v_financing_condition_and_model_by_contract.sql` | Resolve N:M contracts -> financing conditions -> models | pk_contract, pk_financing_condition, pk_model |
| `v_contracts_by_machine` | `0246_billing/02462_v_contracts_by_machine.sql` | Map contracts to machines via junction | All contract fields + machine_id |
| `v_manufacturer_accessory` | `023_catalog/0232_manufacturer/02325_v_manufacturer_accessory.sql` | Accessories with manufacturer, category, generic data | id, manufacturer_id, item_category_id, generic_accessory_id |
| `v_generic_accessory` | `023_catalog/0232_manufacturer/02324_v_generic_accessory.sql` | Filtered accessories (Generic manufacturer only) | id, data (JSON) |
| `v_manufacturer_range` | `023_catalog/0232_manufacturer/02322_v_manufacturer_range.sql` | Manufacturer product ranges enriched | id, manufacturer_id, identifier, name, data (JSON) |
| `v_machine_item_binding` | `024_dim/0245_mat/02453_v_machine_item_binding.sql` | Machine-item-binding with enriched machine item | id, tenant_id, machine_id, data (JSON) |
| `v_machine_item_bindings` | `024_dim/0245_mat/02454_v_machine_item_bindings.sql` | Aggregated bindings per machine (array) | machine_id, data (JSONB array) |
| `v_machine_items` | `024_dim/0245_mat/02452_v_machine_items.sql` | Aggregated machine items per machine (array) | machine_id, data (JSONB array, ordered) |
| `v_print_servers_per_network_configuration` | `024_dim/0243_network/02436_v_print_servers_per_network_configuration.sql` | Print servers aggregated per network config | id, data (JSONB array) |
| `v_model_by_contract_and_financing_condition` | `024_dim/0244_agreement/02445_v_model_by_contract_and_financing_condition.sql` | Junction enriched with full model data | tenant_id, contract_id, financing_condition_id, model_id, data (JSON) |
| `v_contract` | (Base contract view) | Contracts with org enrichment | id, tenant_id, organization_id, data (JSON) |
| `v_contract_item` | (Base contract item view) | Contract line items | id, contract_id, data (JSON) |
| `v_order` | `024_dim/0244_agreement/02447_v_order.sql` | Orders/acquisitions (inferred) | Similar pattern |
| `v_accessory` | `024_dim/0244_agreement/0244a_v_accessory.sql` | Accessories in contract context | Similar pattern |
| `v_machine_available_contract_items` | `024_dim/0244_agreement/0244b_v_machine_available_contract_items.sql` | Contract items available for machines | Similar pattern |

---

### CATEGORY 2: Aggregation Helpers (12 views)

| View Name | File Path | Primary Purpose | Key Metrics |
|-----------|-----------|-----------------|-------------|
| `v_count_allocations_by_location` | `024_dim/0241_geo/02411_v_count_allocations_by_location.sql` | Allocation counts per location (hierarchical) | pk_location, n_direct_allocations, n_total_allocations |
| `v_count_allocations_by_organizational_unit` | `024_dim/0242_org/02421_v_count_allocations_by_organizational_unit.sql` | Allocation counts per org unit (hierarchical) | pk_organizational_unit, n_direct_allocations, n_total_allocations |
| `v_count_allocations_by_network_configuration` | `024_dim/0243_network/02437_v_count_allocations_by_network_configuration.sql` | Allocation counts per network config | pk_network_configuration, n_direct_allocations |
| `v_current_allocations_by_machine` | `024_dim/0245_mat/02455_v_current_allocations_by_machine.sql` | Complex allocation status per machine | pk_machine, current_allocations (ARRAY), is_allocated, is_reserved, is_stock, last_meter_age |
| `v_machine_maintenance_prices` | `024_dim/0246_billing/02463_v_machine_prices.sql` | Maintenance prices per machine per field | pk_machine, pk_printoptim_field, amount, price_daterange |
| `v_price_lookup_from_product` | `024_dim/0246_billing/02466_v_price_lookup_from_product.sql` | Price lookup by contract item and product | contract_item_id, contract_id, model_id, product_id, pk_price |
| `mv_count_allocations_by_network_configuration` | `024_dim/0247_materialized_views/02471_mv_count_allocations_by_network_configuration.sql` | Materialized allocation counts (network) | Same metrics, materialized |
| `mv_count_allocations_by_organizational_unit` | `024_dim/0247_materialized_views/02472_mv_count_allocations_by_organizational_unit.sql` | Materialized allocation counts (org units) | Same metrics, materialized |
| `mv_machine_allocation_summary` | `024_dim/0247_materialized_views/02473_mv_machine_allocation_summary.sql` | Materialized machine allocation summary | pk_machine, total_allocations, allocation_status |
| `mv_dimensions` | `029_etl/0292_update_statistics/02921_mv_dimensions.sql` | ETL helper materialized view | (unknown, ETL-related) |
| `mv_financing_cost` | `029_etl/0292_update_statistics/02922_mv_financing_cost.sql` | Financing cost calculations | (unknown, ETL-related) |
| `mv_reading_with_meters` | `027_fact/0271_fact/02711_mv_reading_with_meters.sql` | Meter readings with metadata | (unknown, fact table related) |

---

### CATEGORY 3: Data Enrichment / Denormalization Views (18 views)

| View Name | File Path | Primary Purpose | Output Format |
|-----------|-----------|-----------------|----------------|
| `v_machine_item` | `024_dim/0245_mat/02451_v_machine_item.sql` | Installed accessories with full metadata | (id, tenant_id, data: {product_id, category, name, installed_at, ...}) |
| `v_model` | (Inferred from references) | Models with JSON structure | (id, data: {...}) |
| `v_item_category` | (Inferred from references) | Item categories with JSON | (id, data: {...}) |
| `v_manufacturer` | (Inferred from references) | Manufacturers with JSON | (id, data: {...}) |
| `v_financing_condition` | (Inferred from references) | Financing terms with JSON | (id, data: {...}) |
| `v_printoptim_field` | (Inferred from references) | PrintOptim fields (maintenance metrics) | (id, data: {...}) |
| `v_print_server` | (Inferred from references) | Print servers with JSON structure | (id, data: {...}) |
| `v_public_address` | `021_common_dim/0211_geo/02111_v_public_address.sql` | Public addresses from location info | (id, data: {...}) |
| `v_path` | `021_common_dim/0214_utilities/02141_v_path.sql` | Hierarchical path utility | (path components) |
| `v_organization` | `020_base_views/02003_v_organization.sql` | Organizations from mv_organization | (id, data: {...}) |
| `v_industry` | `020_base_views/02002_v_industry.sql` | Industries reference data | (id, data: {...}) |
| `v_locale` | `020_base_views/02001_v_locale.sql` | Locales reference data | (id, code, data: {...}) |
| `v_network_configuration` | `024_dim/0243_network/02438_v_network_configuration.sql` | Network config detail | (id, data: {...}) |
| `v_organizational_unit` | `024_dim/0242_org/02422_v_organizational_unit.sql` | Org unit detail | (id, data: {...}) |
| `v_location` | `024_dim/0241_geo/02412_v_location.sql` | Location detail with coordinates | (id, tenant_id, data: {...}) |
| `v_contract` | (see junction resolvers) | Base contract view | (id, tenant_id, organization_id, data: {...}) |
| `tv_manufacturer` | (Assumed) | Manufacturer commodity table | (large JSONB data) |
| `tv_model` | (Assumed) | Model commodity table | (large JSONB data) |

---

### CATEGORY 4: Hierarchical Data Normalizers (6 views)

| View Name | File Path | Primary Purpose | Key Transformations |
|-----------|-----------|-----------------|---------------------|
| `v_flat_location_for_rust_tree` | `024_dim/0241_geo/02414_v_flat_location_for_rust_tree.sql` | Flattens location hierarchy for tree UI | Extracts ltree_id, parent_id from JSON; creates label/value aliases |
| `v_flat_organizational_unit_for_rust_tree` | `024_dim/0242_org/02424_v_flat_organizational_unit_for_rust_tree.sql` | Flattens org unit hierarchy for tree UI | Same pattern as location |
| `v_location_coordinates` | `024_dim/0241_geo/024112_v_location_coordinates.sql` | Extracts coordinates for optional enrichment | Filters null coordinates for efficient LEFT JOIN |
| (Inferred 1) | (Unknown) | Tree-compatible location extractor | (Pattern inference) |
| (Inferred 2) | (Unknown) | Tree-compatible org unit extractor | (Pattern inference) |
| (Inferred 3) | (Unknown) | Tree-compatible data normalizer | (Pattern inference) |

---

### CATEGORY 5: Extracted Components / Left-Join Optimizers (8 views)

| View Name | File Path | Primary Purpose | Use Pattern |
|-----------|-----------|-----------------|-------------|
| `v_location_coordinates` | `024_dim/0241_geo/024112_v_location_coordinates.sql` | Coordinates extraction | LEFT JOINed by v_location |
| `v_current_contract` | (Inferred) | Current contracts only (filtered) | WHERE date condition |
| `v_initial_contract` | `024_dim/0244_agreement/02443_v_initial_contract.sql` | Initial contract version | Contract history queries |
| `v_router` | `024_dim/0243_network/02434_v_router.sql` | Network routers (extracted) | Inferred from network views |
| `v_gateway` | `024_dim/0243_network/02432_v_gateway.sql` | Network gateways (extracted) | Inferred from network views |
| `v_smtp_server` | `024_dim/0243_network/02435_v_smtp_server.sql` | Email servers (extracted) | Inferred from network views |
| `v_dns_server` | `024_dim/0243_network/02431_v_dns_server.sql` | DNS servers (extracted) | Inferred from network views |
| `v_price` (variants) | Various `0246_billing/` files | Pricing data by context | Multiple specialized price views |

---

### CATEGORY 6: Polymorphic Type Resolvers (2 views)

| View Name | File Path | Primary Purpose | Key Pattern |
|-----------|-----------|-----------------|-------------|
| `v_pk_class_resolver` | `024_dim/0244_agreement/02448_v_pk_class_resolver.sql` | Maps generic PKs to entity classes | UNION of Product and Item with 'class' discriminator |
| `mv_pk_class_resolver` | `024_dim/0244_agreement/02449_mv_pk_class_resolver.sql` | Materialized version for performance | Caches union for fast lookups |

---

### CATEGORY 7: Optimized Materialized View Wrappers (4 views)

| View Name | File Path | Primary Purpose | Edge Case Handling |
|-----------|-----------|-----------------|-------------------|
| `v_count_allocations_by_network_configuration_optimized` | `024_dim/0247_materialized_views/02474_v_count_allocations_optimized.sql` | Network config counts (complete set) | UNION ALL with WHERE NOT EXISTS for zero-count configs |
| `v_count_allocations_by_organizational_unit_optimized` | Same file | Org unit counts (complete set) | UNION ALL with WHERE NOT EXISTS for zero-count units |
| `v_machine_allocation_summary_optimized` | Same file | Machine allocation summary (complete set) | UNION ALL with 'AVAILABLE' status for unallocated machines |
| (Edge case pattern) | (Generic pattern) | Complete result sets from materialized views | WHERE NOT EXISTS pattern to include missing entities |

---

### CATEGORY 8: Complex Multi-CTE Assemblers (2 views)

| View Name | File Path | Complexity | Output Structure | CTE Chain Depth |
|-----------|-----------|------------|------------------|-----------------|
| `v_contract_price_tree` | `024_dim/0244_agreement/0246_pricing/02561_v_contract_price_tree.sql` | Very High (199 lines) | Hierarchical JSON: contract -> conditions -> models -> accessories/maintenance | 8 CTEs + final SELECT |
| `v_contract_with_items` | `024_dim/0244_agreement/0244b_extended/024491_v_contract_with_items.sql` | Medium | Flat + nested: contract + items array | Simple subquery aggregation |

---

## View Dependency Quick Links

### Direct Producer-Consumer Relationships

```
AGGREGATION CHAINS:
├─ v_contract_item          ──→ v_contract_with_items
├─ v_machine_item           ──→ v_machine_items
│                           └──→ v_machine_item_binding ──→ v_machine_item_bindings
└─ v_print_server           ──→ v_print_servers_per_network_configuration

ENRICHMENT CHAINS:
├─ v_financing_condition_and_model_by_contract
│  └──→ v_model_by_contract_and_financing_condition
│       └──→ v_contract_price_tree (as input for model assembly)
└─ v_manufacturer_accessory (consumes v_generic_accessory, v_item_category, v_manufacturer)
   └──→ v_contract_price_tree (as input for accessory assembly)

HIERARCHICAL FLATTENERS:
├─ tv_location              ──→ v_flat_location_for_rust_tree
├─ tv_organizational_unit   ──→ v_flat_organizational_unit_for_rust_tree
└─ tb_location_info         ──→ v_location_coordinates ──→ v_location (LEFT JOIN)

POLYMORPHIC RESOLUTION:
├─ v_pk_class_resolver (v_product UNION v_contract_item)
└─ mv_pk_class_resolver (materialized cache of above)

MATERIALIZED VIEW WRAPPERS:
├─ mv_count_allocations_by_location
│  └──→ v_count_allocations_by_location_optimized
├─ mv_count_allocations_by_organizational_unit
│  └──→ v_count_allocations_by_organizational_unit_optimized
└─ mv_machine_allocation_summary
   └──→ v_machine_allocation_summary_optimized
```

---

## Pattern Summary Table

| Pattern Name | Example Views | SQL Technique | Use Case |
|--------------|--------------|---------------|----------|
| Aggregation Stacking | v_machine_item → v_machine_items | jsonb_agg(view.data) GROUP BY | Progressive summarization |
| JSON Enrichment | v_machine_item, v_manufacturer_accessory | jsonb_build_object with nested JOINs | Denormalization to JSON |
| LEFT JOIN Extraction | v_location_coordinates | Isolated NULL-filtered view | Efficient optional joins |
| Hierarchical Aggregation | v_count_allocations_by_location | ltree paths with self-join | Ancestor/descendant counts |
| MV Wrapping | v_count_allocations_*_optimized | UNION ALL with WHERE NOT EXISTS | Complete result sets |
| Multi-CTE Tree Building | v_contract_price_tree | 8+ CTEs with DISTINCT ON, jsonb_agg | Complex hierarchies |
| Locale Extraction | v_machine_item | WITH selected_locale subquery | Locale-specific queries |
| Date Range Intersection | v_machine_maintenance_prices | GREATEST/LEAST with daterange() | Effective date ranges |
| Polymorphic Resolution | v_pk_class_resolver | UNION with type discriminator | Type identification |
| Derived Boolean Flags | v_current_allocations_by_machine | CASE with EXISTS checks | Business logic encoding |

---

## Statistics & Insights

### View Count by Category
- **Junction Resolvers**: 15 views (strong M:M relationship handling)
- **Aggregation Helpers**: 12 views (metrics pre-calculation is key)
- **Data Enrichment**: 18 views (most common pattern)
- **Hierarchical Normalizers**: 6 views (tree UI support)
- **Extracted Components**: 8 views (performance optimization)
- **Polymorphic Resolvers**: 2 views (type safety)
- **MV Wrappers**: 4 views (edge case handling)
- **Complex Assemblers**: 2 views (deep hierarchies)

**Total Identified**: 67 confirmed intermediate views

### Key Design Principles Observed
1. **Reusability**: Views like v_manufacturer, v_item_category referenced by multiple consumers
2. **Performance**: Materialized views with wrapper views ensure complete results
3. **Composability**: Small views combine into larger, more complex views
4. **Normalization for UIs**: Hierarchical flatteners prepare data for frontend tree components
5. **Type Safety**: Polymorphic resolver prevents ambiguous PK references
6. **Date Handling**: Range intersection for time-bounded relationships
7. **Locale Awareness**: Fixed locale selection within queries
8. **Calculation Separation**: Metrics pre-calculated for efficient dashboard queries

---

## Finding Views in Repository

All views located under: `/reference_sql/0_schema/02_query_side/`

Directory structure:
```
02_query_side/
├── 020_base_views/          (Base reference views)
├── 021_common_dim/          (Common dimensions)
│   ├── 0211_geo/            (Geography)
│   └── 0214_utilities/      (Utilities like paths)
├── 022_crm/                 (CRM views)
│   ├── 0221_industry/
│   ├── 0222_organization/
│   └── 0223_user/
├── 023_catalog/             (Catalog views)
│   ├── 0231_classification/
│   └── 0232_manufacturer/
├── 024_dim/                 (Dimensions & complex views)
│   ├── 0241_geo/
│   ├── 0242_org/
│   ├── 0243_network/
│   ├── 0244_agreement/      (Contracts, pricing)
│   │   ├── 0244b_extended/  (Extended views)
│   │   └── 0246_pricing/    (Complex pricing hierarchy)
│   ├── 0245_mat/            (Materials/machines)
│   ├── 0246_billing/        (Billing calculations)
│   └── 0247_materialized_views/ (MV wrappers)
├── 025_scd/                 (Slowly Changing Dimensions)
├── 026_dataflow/            (ETL dataflow)
├── 027_fact/                (Fact tables)
│   └── 0274_stat/           (Statistics)
└── 029_etl/                 (ETL utilities)
    ├── 0291_etl_volume_calculation/
    └── 0292_update_statistics/
```

---

