# Metrics KPI Calculator Pattern

**Category**: Metric Patterns
**Use Case**: Business KPI calculations with automated thresholds and formatting
**Complexity**: High
**Enterprise Feature**: ✅ Yes

## Overview

The KPI calculator pattern automates business metric calculations with configurable formulas, thresholds, and formatting. Essential for:

- Executive dashboards and reporting
- Business intelligence metrics
- Performance monitoring and alerting
- KPI tracking across time periods

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_entity` | entity_reference | ✅ | - | Entity to calculate KPIs for |
| `time_window` | string | ❌ | "30 days" | Time window for calculations |
| `metrics` | array | ✅ | - | KPI definitions with formulas |
| `refresh_strategy` | enum | ❌ | real_time | View refresh strategy |

## Generated SQL Features

- ✅ Complex SQL formula evaluation
- ✅ Threshold-based status calculation (OK/WARNING/CRITICAL)
- ✅ Multiple output formats (percentage, currency, etc.)
- ✅ Time-windowed aggregations
- ✅ Materialized view support for performance

## Examples

### Example 1: Machine Utilization Dashboard

```yaml
views:
  - name: v_machine_utilization_metrics
    pattern: metrics/kpi_calculator
    config:
      base_entity: Machine
      time_window: "30 days"
      metrics:
        - name: utilization_rate
          formula: "COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.status = 'active') / 30.0"
          format: percentage
          thresholds:
            warning: 0.5
            critical: 0.3

        - name: downtime_hours
          formula: "COALESCE(SUM(EXTRACT(EPOCH FROM (m.downtime_end - m.downtime_start)) / 3600), 0)"
          format: decimal
          thresholds:
            warning: 24
            critical: 48

        - name: maintenance_cost
          formula: "COALESCE(SUM(mc.cost), 0)"
          format: currency

        - name: print_volume
          formula: "COALESCE(SUM(r.page_count), 0)"
          format: integer
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_machine_utilization_metrics AS
WITH base_data AS (
    SELECT
        m.pk_machine,
        m.*,
        COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.status = 'active') AS active_days,
        SUM(EXTRACT(EPOCH FROM (m.downtime_end - m.downtime_start)) / 3600) AS total_downtime_hours,
        SUM(mc.cost) AS total_maintenance_cost,
        SUM(r.page_count) AS total_print_volume
    FROM tenant.tb_machine m
    LEFT JOIN tenant.tb_allocation a
        ON a.fk_machine = m.pk_machine
        AND a.allocation_date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
    LEFT JOIN tenant.tb_maintenance_cost mc
        ON mc.fk_machine = m.pk_machine
        AND mc.date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
    LEFT JOIN tenant.tb_reading r
        ON r.fk_machine = m.pk_machine
        AND r.reading_date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
    WHERE m.deleted_at IS NULL
    GROUP BY m.pk_machine
),
calculated_metrics AS (
    SELECT
        pk_machine,
        active_days / 30.0 AS utilization_rate,
        COALESCE(total_downtime_hours, 0) AS downtime_hours,
        COALESCE(total_maintenance_cost, 0) AS maintenance_cost,
        COALESCE(total_print_volume, 0) AS print_volume
    FROM base_data
)
SELECT
    cm.*,

    -- Formatted metrics
    ROUND((cm.utilization_rate * 100)::numeric, 2) AS utilization_rate_pct,
    TO_CHAR(cm.maintenance_cost, 'FM$999,999,999.00') AS maintenance_cost_formatted,

    -- Threshold status
    CASE
        WHEN cm.utilization_rate < 0.3 THEN 'CRITICAL'
        WHEN cm.utilization_rate < 0.5 THEN 'WARNING'
        ELSE 'OK'
    END AS utilization_rate_status,

    CASE
        WHEN cm.downtime_hours > 48 THEN 'CRITICAL'
        WHEN cm.downtime_hours > 24 THEN 'WARNING'
        ELSE 'OK'
    END AS downtime_hours_status,

    NOW() AS calculated_at,
    '30 days' AS time_window

FROM calculated_metrics cm;
```

## Usage Examples

### Dashboard Queries

```sql
-- Executive dashboard
SELECT
    pk_machine,
    utilization_rate_pct,
    utilization_rate_status,
    downtime_hours,
    maintenance_cost_formatted,
    print_volume
FROM v_machine_utilization_metrics
ORDER BY utilization_rate ASC;

-- Alert dashboard (critical issues only)
SELECT
    pk_machine,
    utilization_rate_pct,
    utilization_rate_status,
    downtime_hours_status
FROM v_machine_utilization_metrics
WHERE utilization_rate_status = 'CRITICAL'
   OR downtime_hours_status = 'CRITICAL';
```

### Trend Analysis

```sql
-- Performance over time (assuming daily snapshots)
SELECT
    DATE_TRUNC('week', calculated_at) AS week,
    AVG(utilization_rate) AS avg_utilization,
    SUM(print_volume) AS total_volume
FROM v_machine_utilization_metrics
WHERE calculated_at >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY DATE_TRUNC('week', calculated_at)
ORDER BY week;
```

### Capacity Planning

```sql
-- Identify underutilized machines
SELECT
    pk_machine,
    utilization_rate_pct,
    CASE
        WHEN utilization_rate < 0.3 THEN 'REDUNDANT'
        WHEN utilization_rate < 0.5 THEN 'UNDERUTILIZED'
        ELSE 'OPTIMAL'
    END AS capacity_status
FROM v_machine_utilization_metrics
ORDER BY utilization_rate ASC;
```

## Formula Syntax

KPI formulas support full PostgreSQL SQL expressions:

### Aggregation Functions
```sql
COUNT(*)                                    -- Row count
SUM(sales_amount)                          -- Sum values
AVG(response_time)                         -- Average
MAX(temperature)                           -- Maximum
MIN(temperature)                           -- Minimum
COUNT(DISTINCT customer_id)                -- Distinct count
```

### Conditional Aggregations
```sql
COUNT(*) FILTER (WHERE status = 'active')  -- Conditional count
SUM(amount) FILTER (WHERE type = 'revenue') -- Conditional sum
AVG(score) FILTER (WHERE score > 0)        -- Filtered average
```

### Mathematical Operations
```sql
(active_days / 30.0)                       -- Utilization rate
COALESCE(SUM(cost), 0)                     -- Null-safe sum
EXTRACT(EPOCH FROM (end_time - start_time)) / 3600  -- Hours calculation
```

### Window Functions
```sql
ROW_NUMBER() OVER (ORDER BY amount DESC)   -- Ranking
LAG(amount) OVER (ORDER BY date)           -- Previous value
```

## Threshold Configuration

### Status Levels
- **OK**: Metric within acceptable range
- **WARNING**: Metric approaching critical levels
- **CRITICAL**: Metric requires immediate attention

### Example Thresholds
```yaml
thresholds:
  warning: 0.5    # 50% utilization
  critical: 0.3   # 30% utilization
```

## Output Formats

| Format | Example Output | Use Case |
|--------|----------------|----------|
| `percentage` | `85.50` | Rates, utilization |
| `currency` | `$1,234.56` | Money values |
| `integer` | `1,234` | Whole numbers |
| `decimal` | `1234.56` | Precise decimals |

## When to Use

✅ **Use when**:
- Building executive dashboards
- Need automated KPI calculations
- Require threshold-based alerting
- Complex business metrics with formulas

❌ **Don't use when**:
- Simple counts (use aggregation patterns)
- No alerting needed (use basic aggregation)
- Real-time requirements (consider streaming)

## Performance Considerations

- **Materialized Views**: Use `refresh_strategy: materialized` for complex calculations
- **Indexing**: Ensure base tables have proper indexes for time-window queries
- **Refresh Frequency**: Balance freshness vs. performance
- **Partitioning**: Consider date partitioning for historical data

## Advanced Features

### Custom Refresh Functions

```sql
-- Manual refresh for materialized KPI views
SELECT refresh_machine_utilization_metrics();

-- Automated refresh (requires pg_cron)
SELECT cron.schedule(
    'refresh_kpis',
    '0 */4 * * *',  -- Every 4 hours
    'SELECT refresh_machine_utilization_metrics()'
);
```

### Multi-timeframe KPIs

```yaml
views:
  - name: v_machine_metrics_multi_timeframe
    pattern: metrics/kpi_calculator
    config:
      base_entity: Machine
      metrics:
        - name: utilization_7d
          formula: "COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.allocation_date >= CURRENT_DATE - INTERVAL '7 days') / 7.0"
        - name: utilization_30d
          formula: "COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.allocation_date >= CURRENT_DATE - INTERVAL '30 days') / 30.0"
        - name: utilization_90d
          formula: "COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.allocation_date >= CURRENT_DATE - INTERVAL '90 days') / 90.0"
```

## Related Patterns

- **Trend Analysis**: Time-series analysis of KPI changes
- **Aggregation Patterns**: Basic counting and summing
- **Alerting Patterns**: Automated notifications based on thresholds