# Advanced Pattern Features

This document describes the advanced features added to SpecQL Query Patterns in Phase 9.

## Pattern Composition

Patterns can now depend on each other, allowing complex query chains:

```yaml
query_patterns:
  - name: base_data
    pattern: junction/resolver
    config: {...}

  - name: aggregated_metrics
    pattern: aggregation/count_aggregation
    depends_on: [v_base_data]
    config: {...}

  - name: optimized_metrics
    pattern: wrapper/complete_set
    depends_on: [v_aggregated_metrics]
    performance:
      materialized: true
    config: {...}
```

The generator automatically resolves dependencies using topological sorting.

## Multi-Tenant Support

All patterns now automatically include tenant filtering for multi-tenant entities:

- **Schema-based detection**: Entities in `tenant`, `crm`, `management` schemas are considered multi-tenant
- **Automatic filtering**: `WHERE tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid`
- **Configurable**: Can be overridden with `multi_tenant: true/false` in entity definition

## Performance Optimizations

Patterns support performance configuration for better query performance:

```yaml
query_patterns:
  - name: expensive_aggregation
    pattern: aggregation/hierarchical_count
    performance:
      materialized: true
      indexes:
        - fields: [pk_location]
        - fields: [path]
          type: gist
      refresh_strategy: concurrent
    config: {...}
```

### Features

- **Materialized Views**: Convert expensive views to materialized views
- **Custom Indexes**: Add performance indexes automatically
- **Refresh Strategies**: Support concurrent refresh for zero-downtime updates
- **Automatic Refresh Functions**: Generated refresh functions for maintenance

## Usage Examples

### Example 1: Multi-step Analytics Pipeline

```yaml
# Entity: Location
query_patterns:
  # Step 1: Resolve location hierarchy
  - name: location_hierarchy
    pattern: junction/resolver
    config:
      source_entity: Location
      junction_tables: [...]
      target_entity: Location

  # Step 2: Count allocations by location
  - name: allocation_counts
    pattern: aggregation/hierarchical_count
    depends_on: [v_location_hierarchy]
    config:
      counted_entity: Allocation
      grouped_by_entity: Location
      metrics: [...]

  # Step 3: Materialized view for performance
  - name: allocation_counts_optimized
    pattern: wrapper/complete_set
    depends_on: [v_allocation_counts]
    performance:
      materialized: true
      refresh_strategy: concurrent
    config: {...}
```

### Example 2: Multi-Tenant Dashboard Metrics

```yaml
# Entity: Organization
query_patterns:
  - name: org_metrics
    pattern: aggregation/count_aggregation
    # Automatically includes tenant filtering
    config:
      counted_entity: User
      grouped_by_entity: Organization
      metrics: [...]
```

## Migration Notes

- Existing patterns continue to work unchanged
- New features are opt-in via configuration
- Performance optimizations can be added incrementally
- Multi-tenant filtering is automatic for detected entities