# SpecQL Query Pattern Library - Complete Index

**Version**: 2.0 - Includes Advanced Patterns
**Total Patterns**: 16 patterns across 7 categories
**Last Updated**: 2025-11-10

## 📊 Pattern Overview

The SpecQL Query Pattern Library provides declarative templates for complex SQL queries, enabling you to express sophisticated data relationships and aggregations in simple YAML configuration.

### Pattern Categories

| Category | Patterns | Use Case | Complexity |
|----------|----------|----------|------------|
| **Core Patterns** | 7 patterns | Basic query operations | Low-Medium |
| **Temporal Patterns** | 4 patterns | Time-series and historical data | High |
| **Localization Patterns** | 2 patterns | Multi-language support | Medium |
| **Metric Patterns** | 2 patterns | Business KPIs and analytics | High |
| **Security Patterns** | 2 patterns | Access control and data masking | High |

---

## 🔍 Core Patterns

### Junction Patterns
Complex many-to-many relationship resolution through junction tables.

#### 1. Resolver Pattern (`junction/resolver`)
**Complexity**: Medium | **Use Case**: N-to-N relationship traversal

```yaml
query_patterns:
  - name: contract_financing_details
    pattern: junction/resolver
    config:
      source_entity: Contract
      junction_tables:
        - {table: ContractFinancingCondition, left_key: contract_id, right_key: financing_condition_id}
        - {table: FinancingConditionModel, left_key: financing_condition_id, right_key: model_id}
      target_entity: Model
```

**Generated**: Multi-table JOIN with proper sequencing
**Documentation**: [junction/resolver.md](junction/resolver.md)

#### 2. Aggregated Resolver Pattern (`junction/aggregated_resolver`)
**Complexity**: High | **Use Case**: N-to-N with aggregation

```yaml
query_patterns:
  - name: contract_model_summary
    pattern: junction/aggregated_resolver
    config:
      source_entity: Contract
      junction_tables: [...]
      target_entity: Model
      aggregations:
        - metric: total_quantity
          function: SUM
          field: quantity
```

**Generated**: Junction resolution + aggregation
**Documentation**: [junction/aggregated_resolver.md](junction/aggregated_resolver.md)

### Aggregation Patterns
Entity counting and summarization with flexible grouping.

#### 3. Count Aggregation (`aggregation/count_aggregation`)
**Complexity**: Low | **Use Case**: Simple entity counting

```yaml
query_patterns:
  - name: machines_by_location
    pattern: aggregation/count_aggregation
    config:
      counted_entity: Machine
      grouped_by_entity: Location
      metrics:
        - name: machine_count
          function: COUNT
```

**Generated**: GROUP BY with COUNT operations
**Documentation**: [aggregation/count_aggregation.md](aggregation/count_aggregation.md)

#### 4. Hierarchical Count (`aggregation/hierarchical_count`)
**Complexity**: Medium | **Use Case**: Tree structure counting

```yaml
query_patterns:
  - name: allocations_by_location_hierarchy
    pattern: aggregation/hierarchical_count
    config:
      counted_entity: Allocation
      grouped_by_entity: Location
      hierarchy_field: path
```

**Generated**: Recursive CTE for hierarchical aggregation
**Documentation**: [aggregation/hierarchical_count.md](aggregation/hierarchical_count.md)

#### 5. Boolean Flags (`aggregation/boolean_flags`)
**Complexity**: Low | **Use Case**: Presence/absence indicators

```yaml
query_patterns:
  - name: contract_status_flags
    pattern: aggregation/boolean_flags
    config:
      base_entity: Contract
      flag_fields:
        - has_active_allocations: "EXISTS (SELECT 1 FROM allocations WHERE ...)"
        - has_financing: "EXISTS (SELECT 1 FROM financing WHERE ...)"
```

**Generated**: Boolean aggregation queries
**Documentation**: [aggregation/boolean_flags.md](aggregation/boolean_flags.md)

### Extraction Patterns
Filtering optional or conditional entity components.

#### 6. Component Extraction (`extraction/component`)
**Complexity**: Low | **Use Case**: Optional component filtering

```yaml
query_patterns:
  - name: contracts_with_financing
    pattern: extraction/component
    config:
      base_entity: Contract
      component_entity: FinancingCondition
      join_condition: "contract.id = financing_condition.contract_id"
```

**Generated**: LEFT JOIN with NULL filtering
**Documentation**: [extraction/component.md](extraction/component.md)

#### 7. Temporal Extraction (`extraction/temporal`)
**Complexity**: Medium | **Use Case**: Time-based component filtering

```yaml
query_patterns:
  - name: current_contract_components
    pattern: extraction/temporal
    config:
      base_entity: Contract
      component_entity: ContractComponent
      effective_date_field: effective_date
      expiration_date_field: expiration_date
```

**Generated**: Temporal validity filtering
**Documentation**: [extraction/temporal.md](extraction/temporal.md)

### Hierarchical Patterns
Tree and graph structure traversal.

#### 8. Flattener (`hierarchical/flattener`)
**Complexity**: Medium | **Use Case**: Tree structure flattening

```yaml
query_patterns:
  - name: location_tree_flat
    pattern: hierarchical/flattener
    config:
      entity: Location
      hierarchy_field: path
      include_level: true
      include_path: true
```

**Generated**: Recursive CTE for tree traversal
**Documentation**: [hierarchical/flattener.md](hierarchical/flattener.md)

#### 9. Path Expander (`hierarchical/path_expander`)
**Complexity**: High | **Use Case**: Path-based hierarchy expansion

```yaml
query_patterns:
  - name: location_ancestors
    pattern: hierarchical/path_expander
    config:
      entity: Location
      path_field: path
      expand_direction: ancestors
```

**Generated**: Path manipulation with ltree operators
**Documentation**: [hierarchical/path_expander.md](hierarchical/path_expander.md)

### Polymorphic Patterns
Union-based queries across similar entity types.

#### 10. Type Resolver (`polymorphic/type_resolver`)
**Complexity**: Medium | **Use Case**: Multi-type entity unification

```yaml
query_patterns:
  - name: all_documents
    pattern: polymorphic/type_resolver
    config:
      entity_types:
        - Contract
        - Invoice
        - Quote
      common_fields: [id, title, created_date, status]
      type_discriminator: document_type
```

**Generated**: UNION ALL with type discrimination
**Documentation**: [polymorphic/type_resolver.md](polymorphic/type_resolver.md)

### Wrapper Patterns
View optimization and materialization.

#### 11. Complete Set (`wrapper/complete_set`)
**Complexity**: Low | **Use Case**: View optimization

```yaml
query_patterns:
  - name: optimized_contract_view
    pattern: wrapper/complete_set
    config:
      base_view: v_contract_base
      performance:
        materialized: true
        indexes: [...]
```

**Generated**: Materialized view wrapper
**Documentation**: [wrapper/complete_set.md](wrapper/complete_set.md)

### Assembly Patterns
Complex multi-step query construction.

#### 12. Tree Builder (`assembly/tree_builder`)
**Complexity**: High | **Use Case**: Complex hierarchical assembly

```yaml
query_patterns:
  - name: contract_assembly
    pattern: assembly/tree_builder
    config:
      root_entity: Contract
      assembly_steps: [...]
```

**Generated**: Multi-CTE query assembly
**Documentation**: [assembly/tree_builder.md](assembly/tree_builder.md)

#### 13. Simple Aggregation (`assembly/simple_aggregation`)
**Complexity**: Medium | **Use Case**: Basic assembly with aggregation

```yaml
query_patterns:
  - name: location_summary
    pattern: assembly/simple_aggregation
    config:
      base_entity: Location
      aggregation_steps: [...]
```

**Generated**: CTE-based aggregation assembly
**Documentation**: [assembly/simple_aggregation.md](assembly/simple_aggregation.md)

---

## ⏰ Advanced Patterns

### Temporal Patterns
Time-series data management and historical queries.

#### 14. Snapshot Pattern (`temporal/snapshot`)
**Complexity**: Medium | **Enterprise**: ✅ Yes

Point-in-time entity state queries with temporal validity ranges.

```yaml
query_patterns:
  - name: contract_snapshot
    pattern: temporal/snapshot
    config:
      entity: Contract
      effective_date_field: effective_date
      end_date_field: superseded_date
      snapshot_mode: point_in_time
```

**Features**: tsrange validity, LEAD/LAG window functions, GiST indexing
**Documentation**: [advanced/temporal/snapshot.md](advanced/temporal/snapshot.md)

#### 15. Audit Trail Pattern (`temporal/audit_trail`)
**Complexity**: High | **Enterprise**: ✅ Yes

Complete change history tracking with before/after snapshots.

```yaml
query_patterns:
  - name: contract_audit_trail
    pattern: temporal/audit_trail
    config:
      entity: Contract
      audit_table: tb_contract_audit
      include_user_info: true
      include_diff: true
```

**Features**: Auto audit triggers, JSONB snapshots, retention policies
**Documentation**: [advanced/temporal/audit_trail.md](advanced/temporal/audit_trail.md)

#### 16. SCD Type 2 Pattern (`temporal/scd_type2`)
**Complexity**: Medium | **Enterprise**: ✅ Yes

Slowly Changing Dimensions with automatic version management.

```yaml
query_patterns:
  - name: customer_scd
    pattern: temporal/scd_type2
    config:
      entity: Customer
      effective_date_field: effective_date
      end_date_field: end_date
```

**Features**: Auto versioning triggers, surrogate keys, temporal constraints
**Documentation**: [advanced/temporal/scd_type2.md](advanced/temporal/scd_type2.md)

#### 17. Temporal Range Pattern (`temporal/temporal_range`)
**Complexity**: Low | **Enterprise**: ✅ Yes

Date range filtering for temporal validity periods.

```yaml
query_patterns:
  - name: contracts_current
    pattern: temporal/temporal_range
    config:
      entity: Contract
      start_date_field: effective_date
      end_date_field: expiration_date
      filter_mode: current
```

**Features**: daterange types, GiST indexing, range operators
**Documentation**: [advanced/temporal/temporal_range.md](advanced/temporal/temporal_range.md)

### Localization Patterns
Multi-language support with translation fallback.

#### 18. Translated View Pattern (`localization/translated_view`)
**Complexity**: Medium | **Enterprise**: ✅ Yes

Multi-language entity views with automatic fallback logic.

```yaml
query_patterns:
  - name: product_localized
    pattern: localization/translated_view
    config:
      entity: Product
      translatable_fields: [name, description]
      translation_table: tl_product
      fallback_locale: en_US
```

**Features**: COALESCE fallback, session locale detection, JSONB translations
**Documentation**: [advanced/localization/translated_view.md](advanced/localization/translated_view.md)

#### 19. Locale Aggregation Pattern (`localization/locale_aggregation`)
**Complexity**: Medium | **Enterprise**: ✅ Yes

Aggregations grouped by translated field values.

```yaml
query_patterns:
  - name: products_by_category_localized
    pattern: localization/locale_aggregation
    config:
      entity: Product
      group_by_field: category
      translation_table: tl_product_category
```

**Features**: Localized GROUP BY, multi-locale aggregation
**Documentation**: [advanced/localization/locale_aggregation.md](advanced/localization/locale_aggregation.md)

### Metric Patterns
Business KPI calculations and trend analysis.

#### 20. KPI Calculator Pattern (`metrics/kpi_calculator`)
**Complexity**: High | **Enterprise**: ✅ Yes

Automated business metric calculations with thresholds and formatting.

```yaml
query_patterns:
  - name: machine_utilization_metrics
    pattern: metrics/kpi_calculator
    config:
      base_entity: Machine
      time_window: "30 days"
      metrics:
        - name: utilization_rate
          formula: "COUNT(DISTINCT a.allocation_date) / 30.0"
          format: percentage
          thresholds: {warning: 0.5, critical: 0.3}
```

**Features**: SQL formula evaluation, threshold alerts, multiple formats
**Documentation**: [advanced/metrics/kpi_calculator.md](advanced/metrics/kpi_calculator.md)

#### 21. Trend Analysis Pattern (`metrics/trend_analysis`)
**Complexity**: High | **Enterprise**: ✅ Yes

Time-series trend detection with moving averages.

```yaml
query_patterns:
  - name: utilization_trends
    pattern: metrics/trend_analysis
    config:
      base_metric_view: v_machine_utilization_metrics
      trend_metrics:
        - metric: utilization_rate
          periods: [7, 30, 90]
```

**Features**: Moving averages, trend detection, forecasting
**Documentation**: [advanced/metrics/trend_analysis.md](advanced/metrics/trend_analysis.md)

### Security Patterns
Row-level security and data protection.

#### 22. Permission Filter Pattern (`security/permission_filter`)
**Complexity**: High | **Enterprise**: ✅ Yes

Row-level security with configurable permission checks.

```yaml
query_patterns:
  - name: contracts_accessible
    pattern: security/permission_filter
    config:
      base_entity: Contract
      permission_checks:
        - type: ownership
          field: created_by
        - type: organizational_hierarchy
          field: organization_id
```

**Features**: Multi-permission types, PostgreSQL RLS, hierarchical permissions
**Documentation**: [advanced/security/permission_filter.md](advanced/security/permission_filter.md)

#### 23. Data Masking Pattern (`security/data_masking`)
**Complexity**: Medium | **Enterprise**: ✅ Yes

Dynamic data masking based on user roles.

```yaml
query_patterns:
  - name: contacts_masked
    pattern: security/data_masking
    config:
      base_entity: Contact
      masked_fields:
        - field: email
          mask_type: partial
          unmasked_roles: [admin, hr_manager]
```

**Features**: Role-based masking, multiple mask types, compliance support
**Documentation**: [advanced/security/data_masking.md](advanced/security/data_masking.md)

---

## 📈 Implementation Status

### Phase Completion Summary

| Phase | Category | Status | Patterns | Weeks |
|-------|----------|--------|----------|-------|
| **1-8** | Core Patterns | ✅ Complete | 7 patterns | 1-13 |
| **13** | Temporal | ✅ Complete | 4 patterns | 17-18 |
| **14** | Localization | ✅ Complete | 2 patterns | 19 |
| **15** | Metrics | ✅ Complete | 2 patterns | 20-21 |
| **16** | Security | ✅ Complete | 2 patterns | 22-23 |
| **10** | Documentation | ✅ Complete | - | 14 + 24 |

### Test Coverage

- **Unit Tests**: 95%+ coverage for all patterns
- **Integration Tests**: Real database validation
- **Performance Tests**: Query optimization validation
- **Security Tests**: Penetration testing and compliance validation

### Enterprise Features

- ✅ **Multi-tenant support**: Automatic tenant filtering
- ✅ **Performance optimization**: Materialized views, custom indexes
- ✅ **Security compliance**: GDPR, SOC2, HIPAA patterns
- ✅ **Temporal features**: Audit trails, time-series analysis
- ✅ **Internationalization**: Multi-language support

---

## 🚀 Getting Started

### 1. Choose Your Pattern Category

| Need | Category | Example Pattern |
|------|----------|-----------------|
| Complex relationships | Junction | `junction/resolver` |
| Counting/grouping | Aggregation | `aggregation/count_aggregation` |
| Optional components | Extraction | `extraction/component` |
| Tree structures | Hierarchical | `hierarchical/flattener` |
| Historical data | Temporal | `temporal/snapshot` |
| Multi-language | Localization | `localization/translated_view` |
| Business metrics | Metrics | `metrics/kpi_calculator` |
| Access control | Security | `security/permission_filter` |

### 2. Configure Your Pattern

Start with basic configuration and add complexity:

```yaml
# entities/your_entity.yaml
query_patterns:
  - name: your_view_name
    pattern: category/pattern_name
    config:
      # Required parameters
      entity: YourEntity
      # ... pattern-specific config
```

### 3. Generate and Test

```bash
# Generate SQL
specql generate entities/your_entity.yaml --with-query-patterns

# Test patterns
uv run pytest tests/unit/patterns/ -v
uv run pytest tests/integration/patterns/ -v
```

---

## 📚 Documentation Index

### Core Pattern Documentation
- [Junction Patterns](junction/)
- [Aggregation Patterns](aggregation/)
- [Extraction Patterns](extraction/)
- [Hierarchical Patterns](hierarchical/)
- [Polymorphic Patterns](polymorphic/)
- [Wrapper Patterns](wrapper/)
- [Assembly Patterns](assembly/)

### Advanced Pattern Documentation
- [Temporal Patterns](advanced/temporal/)
- [Localization Patterns](advanced/localization/)
- [Metric Patterns](advanced/metrics/)
- [Security Patterns](advanced/security/)

### Implementation Guides
- [Getting Started](getting_started.md)
- [Advanced Features](advanced_features.md)
- [Migration Guide](../migration/printoptim_to_patterns.md)
- [Performance Tuning](performance.md)
- [Security Best Practices](security.md)

---

## 🎯 Pattern Selection Guide

### Decision Tree

```
Does your query involve complex JOINs?
├── Yes → Junction Patterns
│   └── Need aggregation? → aggregated_resolver
│   └── Simple traversal? → resolver

Does your query count or group entities?
├── Yes → Aggregation Patterns
│   ├── Hierarchical data? → hierarchical_count
│   ├── Simple counting? → count_aggregation
│   └── Boolean presence? → boolean_flags

Does your query filter optional components?
├── Yes → Extraction Patterns
│   ├── Time-based? → temporal
│   └── Simple filtering? → component

Does your query traverse tree structures?
├── Yes → Hierarchical Patterns
│   ├── Flatten tree? → flattener
│   └── Expand paths? → path_expander

Does your query combine similar entity types?
├── Yes → Polymorphic Patterns → type_resolver

Does your query need optimization?
├── Yes → Wrapper Patterns → complete_set

Does your query involve time-series data?
├── Yes → Temporal Patterns
│   ├── Point-in-time? → snapshot
│   ├── Change history? → audit_trail
│   ├── Version management? → scd_type2
│   └── Date filtering? → temporal_range

Does your query need multi-language support?
├── Yes → Localization Patterns
│   ├── Entity translation? → translated_view
│   └── Localized aggregation? → locale_aggregation

Does your query calculate business metrics?
├── Yes → Metric Patterns
│   ├── KPI calculation? → kpi_calculator
│   └── Trend analysis? → trend_analysis

Does your query need access control?
├── Yes → Security Patterns
│   ├── Row filtering? → permission_filter
│   └── Data masking? → data_masking
```

---

*SpecQL Query Pattern Library v2.0 - Declarative SQL Query Generation*