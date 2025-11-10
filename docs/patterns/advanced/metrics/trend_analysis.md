# Metrics Trend Analysis Pattern

**Category**: Metric Patterns
**Use Case**: Time-series trend detection with moving averages
**Complexity**: High
**Enterprise Feature**: ✅ Yes

## Overview

The trend analysis pattern provides automated trend detection and moving average calculations for time-series KPI data. Essential for:

- Performance trend monitoring
- Predictive analytics and forecasting
- Anomaly detection
- Business intelligence dashboards

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_metric_view` | string | ✅ | - | View containing base metrics |
| `trend_metrics` | array | ✅ | - | Metrics to analyze for trends |
| `trend_detection` | object | ❌ | - | Trend detection configuration |

## Generated SQL Features

- ✅ Moving average calculations (7, 30, 90 day windows)
- ✅ Automated trend detection (INCREASING/DECREASING/STABLE)
- ✅ Window function-based time-series analysis
- ✅ Configurable smoothing algorithms
- ✅ Historical data aggregation

## Examples

### Example 1: Machine Performance Trends

```yaml
views:
  - name: v_machine_performance_trends
    pattern: metrics/trend_analysis
    config:
      base_metric_view: v_machine_utilization_metrics
      trend_metrics:
        - metric: utilization_rate
          periods: [7, 30, 90]
          smoothing: simple
        - metric: downtime_hours
          periods: [7, 30]
          smoothing: simple
      trend_detection:
        enabled: true
        sensitivity: medium
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_machine_performance_trends AS
WITH historical_data AS (
    SELECT
        date_trunc('day', calculated_at) AS metric_date,
        AVG(utilization_rate) AS utilization_rate_daily_avg,
        AVG(downtime_hours) AS downtime_hours_daily_avg
    FROM tenant.v_machine_utilization_metrics
    WHERE calculated_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY date_trunc('day', calculated_at)
),
moving_averages AS (
    SELECT
        metric_date,
        utilization_rate_daily_avg,

        -- 7-day moving average
        AVG(utilization_rate_daily_avg) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS utilization_rate_ma7,

        -- 30-day moving average
        AVG(utilization_rate_daily_avg) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS utilization_rate_ma30,

        -- 90-day moving average
        AVG(utilization_rate_daily_avg) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
        ) AS utilization_rate_ma90,

        -- Downtime metrics
        downtime_hours_daily_avg,
        AVG(downtime_hours_daily_avg) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS downtime_hours_ma7,

        AVG(downtime_hours_daily_avg) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS downtime_hours_ma30

    FROM historical_data
)
SELECT
    *,
    -- Trend detection
    CASE
        WHEN utilization_rate_ma7 > utilization_rate_ma30 * 1.1 THEN 'INCREASING'
        WHEN utilization_rate_ma7 < utilization_rate_ma30 * 0.9 THEN 'DECREASING'
        ELSE 'STABLE'
    END AS utilization_rate_trend,

    CASE
        WHEN downtime_hours_ma7 > downtime_hours_ma30 * 1.1 THEN 'INCREASING'
        WHEN downtime_hours_ma7 < downtime_hours_ma30 * 0.9 THEN 'DECREASING'
        ELSE 'STABLE'
    END AS downtime_hours_trend

FROM moving_averages
ORDER BY metric_date DESC;
```

## Usage Examples

### Trend Monitoring

```sql
-- Current performance trends
SELECT
    metric_date,
    utilization_rate_ma7,
    utilization_rate_ma30,
    utilization_rate_trend,
    downtime_hours_ma7,
    downtime_hours_trend
FROM v_machine_performance_trends
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date DESC;

-- Identify deteriorating performance
SELECT
    metric_date,
    utilization_rate_ma7,
    utilization_rate_trend
FROM v_machine_performance_trends
WHERE utilization_rate_trend = 'DECREASING'
  AND metric_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY metric_date DESC;
```

### Forecasting and Prediction

```sql
-- Simple linear trend extrapolation
WITH trend_data AS (
    SELECT
        metric_date,
        utilization_rate_ma30,
        ROW_NUMBER() OVER (ORDER BY metric_date) AS day_number
    FROM v_machine_performance_trends
    WHERE metric_date >= CURRENT_DATE - INTERVAL '90 days'
),
trend_calc AS (
    SELECT
        REGR_SLOPE(utilization_rate_ma30, day_number) AS slope,
        REGR_INTERCEPT(utilization_rate_ma30, day_number) AS intercept,
        MAX(day_number) AS max_day
    FROM trend_data
)
SELECT
    slope * (max_day + 30) + intercept AS predicted_30day_utilization
FROM trend_calc;
```

### Anomaly Detection

```sql
-- Detect unusual utilization spikes/drops
SELECT
    metric_date,
    utilization_rate_daily_avg,
    utilization_rate_ma30,
    CASE
        WHEN utilization_rate_daily_avg > utilization_rate_ma30 * 1.5 THEN 'SPIKE'
        WHEN utilization_rate_daily_avg < utilization_rate_ma30 * 0.5 THEN 'DROP'
        ELSE 'NORMAL'
    END AS anomaly_type
FROM v_machine_performance_trends
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
  AND (utilization_rate_daily_avg > utilization_rate_ma30 * 1.5
       OR utilization_rate_daily_avg < utilization_rate_ma30 * 0.5)
ORDER BY ABS(utilization_rate_daily_avg - utilization_rate_ma30) DESC;
```

## Moving Average Types

### Simple Moving Average (SMA)
```sql
AVG(metric_value) OVER (
    ORDER BY date
    ROWS BETWEEN (period - 1) PRECEDING AND CURRENT ROW
)
```

### Weighted Moving Average (WMA)
```sql
-- Custom weights: recent days more important
SUM(metric_value * weight) / SUM(weight) OVER (...)
```

### Exponential Moving Average (EMA)
```sql
-- Smooths with exponential decay
metric_value * (2.0 / (period + 1)) + previous_ema * (1 - 2.0 / (period + 1))
```

## Trend Detection Algorithms

### Simple Threshold-based
```sql
CASE
    WHEN short_ma > long_ma * 1.1 THEN 'INCREASING'
    WHEN short_ma < long_ma * 0.9 THEN 'DECREASING'
    ELSE 'STABLE'
END
```

### Percentage Change
```sql
CASE
    WHEN (short_ma - long_ma) / long_ma > 0.05 THEN 'INCREASING'
    WHEN (short_ma - long_ma) / long_ma < -0.05 THEN 'DECREASING'
    ELSE 'STABLE'
END
```

### Statistical Significance
```sql
-- Use statistical tests for trend significance
-- (Requires more complex analysis)
```

## When to Use

✅ **Use when**:
- Monitoring KPI changes over time
- Building predictive analytics
- Detecting performance anomalies
- Creating trend-based alerts

❌ **Don't use when**:
- No historical data available
- Real-time analysis only
- Simple current state monitoring

## Performance Considerations

- **Data Volume**: Moving averages require sufficient historical data
- **Window Functions**: Can be expensive on large datasets
- **Materialized Views**: Consider for frequently accessed trend data
- **Indexing**: Ensure date columns are properly indexed

## Advanced Analytics

### Seasonal Decomposition

```sql
-- Decompose trends into seasonal, trend, and residual components
WITH seasonal_data AS (
    SELECT
        metric_date,
        EXTRACT(DOW FROM metric_date) AS day_of_week,
        utilization_rate_daily_avg,
        AVG(utilization_rate_daily_avg) OVER (PARTITION BY EXTRACT(DOW FROM metric_date)) AS seasonal_avg
    FROM v_machine_performance_trends
)
SELECT
    metric_date,
    utilization_rate_daily_avg,
    seasonal_avg,
    utilization_rate_daily_avg - seasonal_avg AS detrended_value
FROM seasonal_data;
```

### Correlation Analysis

```sql
-- Analyze relationship between different metrics
SELECT
    CORR(utilization_rate_ma30, downtime_hours_ma30) AS utilization_downtime_corr,
    CORR(utilization_rate_ma30, maintenance_cost) AS utilization_cost_corr
FROM v_machine_performance_trends
WHERE metric_date >= CURRENT_DATE - INTERVAL '90 days';
```

## Integration with Alerting

```sql
-- Create alerts based on trend changes
CREATE OR REPLACE FUNCTION check_performance_trends()
RETURNS TABLE(alert_type TEXT, severity TEXT, message TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'TREND'::text,
        CASE
            WHEN utilization_rate_trend = 'DECREASING' THEN 'WARNING'
            ELSE 'INFO'
        END,
        'Utilization trend: ' || utilization_rate_trend
    FROM v_machine_performance_trends
    WHERE metric_date = CURRENT_DATE
      AND utilization_rate_trend IN ('INCREASING', 'DECREASING');
END;
$$ LANGUAGE plpgsql;
```

## Related Patterns

- **KPI Calculator**: Generate base metrics for trend analysis
- **Alerting Patterns**: Automated notifications for trend changes
- **Time-series Patterns**: Specialized time-series data handling