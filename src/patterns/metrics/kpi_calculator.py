"""KPI Calculator Pattern Implementation"""

from typing import Dict, Any, List
from jinja2 import Template


def generate_kpi_calculator(config: Dict[str, Any]) -> str:
    """Generate KPI calculator view SQL.

    This function handles complex KPI calculations with formula parsing,
    join detection, and threshold logic.
    """
    pattern_config = config.get("config", {})
    name = config.get("name", "v_kpi_metrics")
    schema = pattern_config.get("schema", "tenant")
    base_entity_config = pattern_config.get("base_entity", "Entity")
    time_window = pattern_config.get("time_window", "30 days")
    metrics = pattern_config.get("metrics", [])
    refresh_strategy = pattern_config.get("refresh_strategy", "real_time")

    # Handle base_entity as string or dict
    if isinstance(base_entity_config, str):
        entity_name = base_entity_config
        # Build entity context from name
        entity = {
            "name": entity_name,
            "schema": schema,
            "table": f"tb_{entity_name.lower()}",
            "pk_field": f"pk_{entity_name.lower()}",
            "alias": entity_name[0].lower(),  # Use first letter as alias (Machine -> m)
        }
    else:
        # base_entity is already a dict
        entity_name = base_entity_config.get("name", "Entity")
        entity = {
            "name": entity_name,
            "schema": base_entity_config.get("schema", schema),
            "table": base_entity_config.get("table", f"tb_{entity_name.lower()}"),
            "pk_field": base_entity_config.get("pk_field", f"pk_{entity_name.lower()}"),
            "alias": base_entity_config.get("alias", entity_name[0].lower()),
        }

    # Parse metrics and detect required joins
    from .kpi_builder import JoinDetector

    join_detector = JoinDetector()
    metric_joins = []
    processed_metrics = []

    for metric in metrics:
        formula = metric.get("formula", "0")
        metric.get("name", "metric")

        # Detect required joins using the JoinDetector
        joins_needed = join_detector.detect_joins(formula, entity["name"])

        for join in joins_needed:
            if join not in [j["alias"] for j in metric_joins]:
                metric_joins.append(join)

        processed_metrics.append(
            {
                **metric,
                "requires_aggregation": len(joins_needed) > 0,
                "aggregation_source": build_aggregation_source(formula, joins_needed),
            }
        )

    # Render template
    template = Template(KPI_CALCULATOR_TEMPLATE)
    return template.render(
        name=name,
        schema=schema,
        base_entity=entity,
        time_window=time_window,
        metrics=processed_metrics,
        metric_joins=metric_joins,
        refresh_strategy=refresh_strategy,
    )

    # Render template
    template = Template(KPI_CALCULATOR_TEMPLATE)
    return template.render(
        name=name,
        schema=schema,
        base_entity=entity,
        time_window=time_window,
        metrics=processed_metrics,
        metric_joins=metric_joins,
        refresh_strategy=refresh_strategy,
    )


def detect_required_joins(formula: str) -> List[Dict[str, Any]]:
    """Detect which tables need to be joined based on formula.

    This is a simplified implementation. In practice, this would use
    AST parsing to properly analyze the SQL formula.
    """
    joins = []

    # Simple pattern matching for common join indicators
    if "a.allocation_date" in formula or "a.status" in formula:
        joins.append(
            {
                "table": "tenant.tb_allocation",
                "alias": "a",
                "condition": "a.fk_machine = e.pk_machine",
                "date_field": "allocation_date",
            }
        )

    if "mc.cost" in formula:
        joins.append(
            {
                "table": "tenant.tb_maintenance_cost",
                "alias": "mc",
                "condition": "mc.fk_machine = e.pk_machine",
                "date_field": "date",
            }
        )

    if "r.page_count" in formula:
        joins.append(
            {
                "table": "tenant.tb_reading",
                "alias": "r",
                "condition": "r.fk_machine = e.pk_machine",
                "date_field": "reading_date",
            }
        )

    return joins


def build_aggregation_source(formula: str, joins: List[Dict[str, Any]]) -> str:
    """Build the aggregation source expression for a metric.

    This extracts the aggregation part from the formula.
    """
    # For now, return a placeholder. In practice, this would parse the formula
    # and extract aggregation expressions.
    return "COUNT(*) as dummy_aggregation"


# Template for KPI calculator
KPI_CALCULATOR_TEMPLATE = """-- @fraiseql:view
-- @fraiseql:description KPI dashboard for {{ base_entity.name }}
-- @fraiseql:pattern metrics/kpi_calculator

{% if refresh_strategy == 'materialized' %}
CREATE MATERIALIZED VIEW {{ schema }}.{{ name }} AS
{% else %}
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
{% endif %}

WITH base_data AS (
    -- Gather raw data for calculations
    SELECT
        {{ base_entity.pk_field }},
        {{ base_entity.alias }}.*,

        -- Time-windowed aggregations
        {% for metric in metrics %}
        {% if metric.requires_aggregation %}
        {{ metric.aggregation_source }} AS {{ metric.name }}_source,
        {% endif %}
        {% endfor %}

        -- Reference date range
        CURRENT_DATE - INTERVAL '{{ time_window }}' AS window_start,
        CURRENT_DATE AS window_end

    FROM {{ base_entity.schema }}.{{ base_entity.table }} {{ base_entity.alias }}
    {% for join in metric_joins %}
    LEFT JOIN {{ join.table }} {{ join.alias }}
        ON {{ join.condition }}
        AND {{ join.alias }}.date_field BETWEEN CURRENT_DATE - INTERVAL '{{ time_window }}' AND CURRENT_DATE
    {% endfor %}
    WHERE {{ base_entity.alias }}.deleted_at IS NULL
    GROUP BY {{ base_entity.pk_field }}
),
calculated_metrics AS (
    SELECT
        {{ base_entity.pk_field }},

        -- Calculate KPIs
        {% for metric in metrics %}
        {{ metric.formula }} AS {{ metric.name }},
        {% endfor %}

        window_start,
        window_end

    FROM base_data
)
SELECT
    cm.*,

    -- Format metrics
    {% for metric in metrics %}
    {% if metric.format == 'percentage' %}
    ROUND((cm.{{ metric.name }} * 100)::numeric, 2) AS {{ metric.name }}_pct,
    {% elif metric.format == 'currency' %}
    TO_CHAR(cm.{{ metric.name }}, 'FM$999,999,999.00') AS {{ metric.name }}_formatted,
    {% endif %}
    {% endfor %}

    -- Threshold status
    {% for metric in metrics %}
    {% if metric.thresholds %}
    CASE
        WHEN cm.{{ metric.name }} >= {{ metric.thresholds.critical }} THEN 'CRITICAL'
        WHEN cm.{{ metric.name }} >= {{ metric.thresholds.warning }} THEN 'WARNING'
        ELSE 'OK'
    END AS {{ metric.name }}_status,
    {% endif %}
    {% endfor %}

    -- Metadata
    NOW() AS calculated_at,
    '{{ time_window }}' AS time_window

FROM calculated_metrics cm;

{% if refresh_strategy == 'materialized' %}
-- Refresh function
CREATE OR REPLACE FUNCTION {{ schema }}.refresh_{{ name }}()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY {{ schema }}.{{ name }};
END;
$$ LANGUAGE plpgsql;
{% endif %}

-- Index for entity lookup
CREATE INDEX IF NOT EXISTS idx_{{ name }}_entity
    ON {{ schema }}.{{ name }}({{ base_entity.pk_field }});

COMMENT ON {% if refresh_strategy == 'materialized' %}MATERIALIZED VIEW{% else %}VIEW{% endif %} {{ schema }}.{{ name }} IS
    'KPI metrics for {{ base_entity.name }} over {{ time_window }} window. {% if refresh_strategy == 'materialized' %}Refresh: SELECT refresh_{{ name }}();{% endif %}';
"""
