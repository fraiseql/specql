# Aggregate View Transformer
# Generates aggregate views based on schema_aggregate_view patterns

from typing import Dict, List
from core.ast_models import Entity, Pattern
from generators.schema.pattern_transformer import PatternTransformer


class AggregateViewTransformer(PatternTransformer):
    """Generates aggregate views based on aggregate view patterns."""

    def applies_to(self, pattern: Pattern) -> bool:
        return pattern.type == "schema_aggregate_view"

    def transform_ddl(self, entity: Entity, ddl: str, pattern: Pattern) -> str:
        """
        Append aggregate view definitions after main table DDL.

        Input: Table DDL for tb_metric
        Output: Table DDL + CREATE VIEW tv_metric_summary AS ...
        """
        view_config = pattern.params.get("aggregates", [])

        if not view_config:
            return ddl

        view_ddl_parts = []
        for agg_config in view_config:
            view_name = agg_config.get("view_name", f"tv_{entity.name.lower()}_summary")
            view_sql = self._generate_aggregate_view(entity, agg_config)
            view_ddl_parts.append(view_sql)

        # Append views after table DDL
        full_ddl = ddl + "\n\n" + "\n\n".join(view_ddl_parts)
        return full_ddl

    def _generate_aggregate_view(self, entity: Entity, config: dict) -> str:
        """
        Generate aggregate view DDL.

        config = {
            'view_name': 'tv_metric_summary',
            'group_by': ['service_id'],
            'aggregates': [
                {'function': 'SUM', 'column': 'value', 'alias': 'total'},
                {'function': 'COUNT', 'column': 'id', 'alias': 'count'}
            ]
        }
        """
        view_name = config["view_name"]
        group_by = config.get("group_by", [])
        aggregates = config.get("aggregates", [])

        # Build SELECT clause
        select_parts = []
        for col in group_by:
            select_parts.append(f"    {col}")

        for agg in aggregates:
            func = agg["function"].upper()
            col = agg["column"]
            alias = agg.get("alias", f"{func.lower()}_{col}")
            select_parts.append(f"    {func}({col}) AS {alias}")

        select_clause = ",\n".join(select_parts)

        # Build GROUP BY clause
        group_clause = ", ".join(group_by) if group_by else ""

        # Generate view DDL
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        view_ddl = f"""-- ============================================================================
-- Aggregate View: {view_name}
-- ============================================================================
CREATE VIEW {entity.schema}.{view_name} AS
SELECT
{select_clause}
FROM {table_name}"""

        if group_clause:
            view_ddl += f"\nGROUP BY {group_clause}"

        view_ddl += ";\n"

        # Add comment with FraiseQL metadata
        view_ddl += f"""
COMMENT ON VIEW {entity.schema}.{view_name} IS
'Aggregate view for {entity.name}.

@fraiseql:pattern:schema_aggregate_view
';"""

        return view_ddl

    def get_priority(self) -> int:
        return 30  # Run after tables created
