"""Compiler for aggregate steps"""


from src.core.ast_models import ActionStep, EntityDefinition

from src.generators.actions.step_compilers.base import StepCompiler


class AggregateStepCompiler(StepCompiler):
    """Compiles aggregate steps to PL/pgSQL SELECT INTO statements"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Generate aggregate SELECT INTO statement

        Returns:
            PL/pgSQL SELECT INTO statement
        """
        operation = step.aggregate_operation or "count"
        field = step.aggregate_field or "*"
        table = step.aggregate_from
        where_clause = step.aggregate_where
        group_by = step.aggregate_group_by
        result_var = step.aggregate_as

        # Build the aggregate expression
        if operation.lower() == "count" and field.lower() == "id":
            agg_expr = "COUNT(*)"
        else:
            agg_expr = f"{operation.upper()}({field})"

        # Build the query
        query_parts = [f"SELECT {agg_expr}"]

        if group_by:
            query_parts.append(f"FROM {table}")
            if where_clause:
                query_parts.append(f"WHERE {where_clause}")
            query_parts.append(f"GROUP BY {group_by}")
        else:
            query_parts.append(f"FROM {table}")
            if where_clause:
                query_parts.append(f"WHERE {where_clause}")

        query = " ".join(query_parts)

        # Generate SELECT INTO statement
        if group_by:
            # For grouped aggregates, we need to handle the result differently
            # This would typically return multiple rows, so we'll store as a result set
            return f"{result_var} := ARRAY({query});"
        else:
            # Single value aggregate
            return f"SELECT {agg_expr} INTO {result_var} FROM {table}" + \
                   (f" WHERE {where_clause}" if where_clause else "") + ";"