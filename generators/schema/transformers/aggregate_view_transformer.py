# Aggregate View Transformer
# Generates aggregate views based on schema_aggregate_view patterns

from core.ast_models import Entity, Pattern

from ..pattern_transformer import PatternTransformer


class AggregateViewTransformer(PatternTransformer):
    """Generates aggregate views based on aggregate view patterns."""

    def applies_to(self, pattern: Pattern) -> bool:
        return pattern.type in ["schema_aggregate_view", "aggregate_view"]

    def transform_ddl(self, entity: Entity, ddl: str, pattern: Pattern) -> str:
        """
        Append aggregate view definition after main table DDL.

        Input: Table DDL for tb_order
        Output: Table DDL + CREATE MATERIALIZED VIEW mv_order_agg AS ...
        """
        view_sql = self._generate_aggregate_view(entity, pattern.params, pattern)

        # Append view after table DDL
        full_ddl = ddl + "\n\n" + view_sql
        return full_ddl

    def _generate_aggregate_view(self, entity: Entity, config: dict, pattern: Pattern) -> str:
        """
        Generate aggregate view DDL matching the YAML template output.

        Generates MATERIALIZED VIEW with mv_* naming, indexes, refresh functions, and triggers.
        """
        # Use mv_* naming convention like YAML template
        view_name = f"mv_{entity.name.lower()}_agg"

        group_by = config.get("group_by", [])
        aggregates = config.get("aggregates", [])
        refresh_mode = config.get("refresh_mode", "manual")
        indexes = config.get("indexes", [])

        # Map logical field names to physical column names
        def map_field_name(field_name: str) -> str:
            """Map logical field name to physical column name."""
            if field_name in entity.fields:
                field = entity.fields[field_name]
                if field.is_reference():
                    return f"fk_{field_name}"
                else:
                    return field_name
            # If not found in entity fields, assume it's already a physical name
            return field_name

        # Build SELECT clause
        select_parts = []
        for logical_field in group_by:
            physical_col = map_field_name(logical_field)
            select_parts.append(f"    {physical_col} AS {logical_field}")

        for agg in aggregates:
            # Handle different aggregate formats
            if "field" in agg:
                # Test format: {'field': 'total_amount', 'function': 'sum', 'alias': 'total_spent'}
                func = agg["function"].upper()
                logical_field = agg["field"]
                physical_col = map_field_name(logical_field)
                alias = agg.get("alias", f"{func.lower()}_{logical_field}")
            else:
                # Standard format: {'function': 'SUM', 'column': 'total_amount', 'alias': 'total_spent'}
                func = agg["function"].upper()
                physical_col = agg["column"]
                alias = agg.get("alias", f"{func.lower()}_{physical_col}")

            select_parts.append(f"    {func}({physical_col}) AS {alias}")

        select_clause = ",\n".join(select_parts)

        # Build GROUP BY clause (use physical column names)
        group_by_physical = [map_field_name(field) for field in group_by]
        group_clause = ", ".join(group_by_physical) if group_by_physical else ""

        # Generate view DDL
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        view_ddl = f"""-- Materialized view with aggregates
CREATE MATERIALIZED VIEW {entity.schema}.{view_name} AS
SELECT
{select_clause}
FROM {table_name}"""

        if group_clause:
            view_ddl += f"\nGROUP BY {group_clause}"

        view_ddl += ";\n\n"

        # Add indexes
        for index in indexes:
            index_name = index.get("name", f"idx_mv_{entity.name.lower()}_agg_{index['fields'][0]}")
            # Map logical field names to physical for index fields
            physical_fields = [map_field_name(field) for field in index["fields"]]
            fields_str = ", ".join(physical_fields)
            using = index.get("using", "btree")
            view_ddl += f"""-- Index on materialized view
CREATE INDEX {index_name}
  ON {entity.schema}.{view_name}
  USING {using}
  ({fields_str});

"""

        # Add refresh function
        view_ddl += f"""-- Refresh function with dependency ordering
CREATE OR REPLACE FUNCTION {entity.schema}.refresh_mv_{entity.name.lower()}_agg()
RETURNS void AS $$
BEGIN
  -- Refresh this materialized view
  REFRESH MATERIALIZED VIEW {entity.schema}.{view_name};

"""

        if refresh_mode == "auto":
            view_ddl += f"""  -- Update refresh timestamp
  UPDATE {entity.schema}.mv_refresh_log
  SET last_refresh = CURRENT_TIMESTAMP,
      row_count = (SELECT COUNT(*) FROM {entity.schema}.{view_name})
  WHERE mv_name = '{view_name}';
"""

        view_ddl += """END;
$$ LANGUAGE plpgsql;

"""

        # Add trigger for auto refresh
        if refresh_mode == "auto":
            view_ddl += f"""-- Trigger-based auto refresh (on source table changes)
CREATE OR REPLACE FUNCTION {entity.schema}.trigger_refresh_mv_{entity.name.lower()}_agg()
RETURNS TRIGGER AS $$
BEGIN
  -- Mark view as stale (actual refresh can be async)
  INSERT INTO {entity.schema}.mv_refresh_queue (mv_name, triggered_at)
  VALUES ('{view_name}', CURRENT_TIMESTAMP)
  ON CONFLICT (mv_name) DO UPDATE
  SET triggered_at = CURRENT_TIMESTAMP,
      refresh_count = mv_refresh_queue.refresh_count + 1;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_refresh_mv_{entity.name.lower()}_agg
AFTER INSERT OR UPDATE OR DELETE ON {table_name}
FOR EACH STATEMENT
EXECUTE FUNCTION {entity.schema}.trigger_refresh_mv_{entity.name.lower()}_agg();

"""

        # Add FraiseQL annotation
        view_ddl += f"""-- FraiseQL annotation for GraphQL discovery
COMMENT ON MATERIALIZED VIEW {entity.schema}.{view_name} IS '@fraiseql:type=aggregate_view @fraiseql:refresh_mode={refresh_mode}';"""

        return view_ddl

    def get_priority(self) -> int:
        return 30  # Run after tables created
