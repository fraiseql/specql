"""Aggregate view pattern implementation."""

from dataclasses import dataclass

from core.ast_models import Entity, FieldDefinition, Index


@dataclass
class AggregateViewConfig:
    """Configuration for aggregate view."""

    group_by: list[str]
    aggregates: list[dict]  # List of {field, function, alias}
    refresh_mode: str = "manual"  # auto, manual, incremental
    indexes: list[dict] | None = None


class AggregateViewPattern:
    """Generate materialized aggregate views for entities."""

    @classmethod
    def apply(cls, entity: Entity, params: dict) -> tuple[Entity, str]:
        """
        Apply aggregate view pattern.

        Creates a materialized view with GROUP BY and aggregate functions,
        with optional auto-refresh triggers.

        Args:
            entity: Entity to create aggregate view for
            params:
                - group_by: List of fields to group by
                - aggregates: List of {field, function, alias} dicts
                - refresh_mode: 'auto', 'manual', or 'incremental'
                - indexes: Optional list of index definitions

        Returns:
            Tuple of (modified_entity, additional_sql)
        """
        config = cls._parse_config(params)

        # Generate aggregate view DDL
        view_ddl = cls._generate_view_ddl(entity, config)

        # Generate indexes if specified
        index_ddls = cls._generate_indexes(entity, config)

        # Generate refresh triggers if auto mode
        trigger_ddl = ""
        if config.refresh_mode == "auto":
            trigger_ddl = cls._generate_refresh_triggers(entity, config)

        # Store aggregate view info in entity for template access
        if not hasattr(entity, "aggregate_views"):
            entity.aggregate_views = []

        view_info = {
            "name": cls._get_view_name(entity),
            "ddl": view_ddl,
            "trigger_ddl": trigger_ddl,
            "refresh_mode": config.refresh_mode,
        }
        entity.aggregate_views.append(view_info)

        # Store indexes in aggregate_view_indexes for template
        if index_ddls:
            if not hasattr(entity, "aggregate_view_indexes"):
                entity.aggregate_view_indexes = []
            for idx_ddl in index_ddls:
                entity.aggregate_view_indexes.append(idx_ddl)

        # Return empty additional_sql since template handles rendering
        return entity, ""

    @classmethod
    def _parse_config(cls, params: dict) -> AggregateViewConfig:
        """Parse pattern parameters."""
        group_by = params.get("group_by", [])
        aggregates = params.get("aggregates", [])
        refresh_mode = params.get("refresh_mode", "manual")
        indexes = params.get("indexes", [])

        if not group_by:
            raise ValueError("Aggregate view pattern requires 'group_by' fields")

        # Process aggregates - ensure each has alias
        processed_aggregates = []
        for agg in aggregates:
            field = agg.get("field")
            function = agg.get("function", "count")
            alias = agg.get("alias")

            # Generate default alias if not provided
            if not alias:
                alias = f"{function.lower()}_{field}"

            processed_aggregates.append(
                {"field": field, "function": function.upper(), "alias": alias}
            )

        return AggregateViewConfig(
            group_by=group_by,
            aggregates=processed_aggregates,
            refresh_mode=refresh_mode,
            indexes=indexes,
        )

    @classmethod
    def _get_view_name(cls, entity: Entity) -> str:
        """Generate view name."""
        return f"mv_{entity.name.lower()}_agg"

    @classmethod
    def _generate_view_ddl(cls, entity: Entity, config: AggregateViewConfig) -> str:
        """Generate CREATE MATERIALIZED VIEW DDL."""
        view_name = cls._get_view_name(entity)
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        full_view_name = f"{entity.schema}.{view_name}"

        # Build SELECT clause
        select_parts = []

        # Add group by columns
        for field in config.group_by:
            # Check if it's a reference field
            field_def = entity.fields.get(field)
            if field_def and field_def.type_name == "ref":
                # Use FK column name
                fk_column = f"fk_{field}"
                select_parts.append(f"{fk_column} AS {field}")
            else:
                select_parts.append(field)

        # Add aggregate functions
        for agg in config.aggregates:
            field = agg["field"]
            function = agg["function"]
            alias = agg["alias"]
            select_parts.append(f"{function}({field}) AS {alias}")

        select_clause = ",\n    ".join(select_parts)

        # Build GROUP BY clause
        group_by_parts = []
        for field in config.group_by:
            field_def = entity.fields.get(field)
            if field_def and field_def.type_name == "ref":
                # Use FK column name
                group_by_parts.append(f"fk_{field}")
            else:
                group_by_parts.append(field)

        group_by_clause = ", ".join(group_by_parts)

        # Build DDL
        ddl = f"""CREATE MATERIALIZED VIEW {full_view_name} AS
SELECT
    {select_clause}
FROM {table_name}
GROUP BY {group_by_clause};

COMMENT ON MATERIALIZED VIEW {full_view_name} IS '@fraiseql:type=aggregate_view @fraiseql:refresh_mode={config.refresh_mode}';"""

        return ddl

    @classmethod
    def _generate_indexes(cls, entity: Entity, config: AggregateViewConfig) -> list[str]:
        """Generate indexes on materialized view."""
        if not config.indexes:
            return []

        view_name = cls._get_view_name(entity)
        full_view_name = f"{entity.schema}.{view_name}"

        index_statements = []
        for idx in config.indexes:
            idx_name = idx.get("name")
            fields = idx.get("fields", [])
            using = idx.get("using", "btree")

            if not idx_name or not fields:
                continue

            # Build field list (handle FK references)
            field_list = []
            for field in fields:
                field_def = entity.fields.get(field)
                if field_def and field_def.type_name == "ref":
                    field_list.append(f"fk_{field}")
                else:
                    field_list.append(field)

            fields_str = ", ".join(field_list)
            index_sql = (
                f"CREATE INDEX {idx_name} ON {full_view_name} USING {using} ({fields_str});"
            )
            index_statements.append(index_sql)

        return index_statements

    @classmethod
    def _generate_refresh_triggers(cls, entity: Entity, config: AggregateViewConfig) -> str:
        """Generate auto-refresh triggers for materialized view."""
        view_name = cls._get_view_name(entity)
        full_view_name = f"{entity.schema}.{view_name}"
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        function_name = f"{entity.schema}.refresh_{view_name}"
        trigger_name = f"tr_refresh_{view_name}"

        ddl = f"""CREATE OR REPLACE FUNCTION {function_name}()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW {full_view_name};
    RETURN NULL;
END;
$$;

CREATE TRIGGER {trigger_name}
AFTER INSERT OR UPDATE OR DELETE ON {table_name}
FOR EACH STATEMENT
EXECUTE FUNCTION {function_name}();"""

        return ddl
