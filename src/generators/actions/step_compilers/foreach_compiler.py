"""
ForEach Step Compiler

Compiles 'foreach' steps to PL/pgSQL iteration logic.

Example SpecQL:
    - foreach: item in related_orders
      then:
        - update: Order SET status = 'processed' WHERE id = item.id

Generated PL/pgSQL:
    -- ForEach: item in related_orders
    FOR v_item IN
        SELECT * FROM crm.tb_order
        WHERE fk_contact = v_pk
    LOOP
        -- Update: Order SET status = 'processed' WHERE id = item.id
        UPDATE crm.tb_order
        SET status = 'processed', updated_at = NOW(), updated_by = v_user_id
        WHERE pk_order = v_item.pk_order;
    END LOOP;
"""

from src.core.ast_models import ActionStep, EntityDefinition


class ForEachStepCompiler:
    """Compiles foreach steps to PL/pgSQL FOR loops"""

    def __init__(self, step_compiler_registry=None):
        """
        Initialize with step compiler registry for compiling nested steps

        Args:
            step_compiler_registry: Dict mapping step types to compilers
        """
        self.step_compiler_registry = step_compiler_registry or {}

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile foreach step to PL/pgSQL FOR loop

        Args:
            step: ActionStep with type='foreach'
            entity: EntityDefinition for table/schema context
            context: Compilation context (variables, etc.)

        Returns:
            PL/pgSQL code for iteration logic
        """
        if step.type != "foreach":
            raise ValueError(f"Expected foreach step, got {step.type}")

        # Parse the foreach expression: "item in collection"
        if step.foreach_expr:
            iterator_var, collection_expr = self._parse_foreach_expression(step.foreach_expr)
        elif step.iterator_var and step.collection:
            iterator_var = step.iterator_var
            collection_expr = step.collection
        else:
            raise ValueError(
                "Foreach step must have either foreach_expr or iterator_var and collection"
            )

        # Generate the query to iterate over
        iteration_query = self._generate_iteration_query(collection_expr, entity, context)

        # Compile the steps to execute for each item
        loop_body = self._compile_loop_body(step.then_steps, entity, context, iterator_var)

        expr_display = step.foreach_expr or f"{iterator_var} in {collection_expr}"
        return f"""
    -- ForEach: {expr_display}
    FOR {iterator_var} IN
{iteration_query}
    LOOP{loop_body}
    END LOOP;"""

    def _parse_foreach_expression(self, expr: str) -> tuple[str, str]:
        """
        Parse foreach expression like "item in related_orders"

        Args:
            expr: The foreach expression

        Returns:
            Tuple of (iterator_variable, collection_expression)
        """
        if " in " not in expr:
            raise ValueError(
                f"Invalid foreach expression: {expr}. Expected format: 'var in collection'"
            )

        iterator_var, collection_expr = expr.split(" in ", 1)
        iterator_var = iterator_var.strip()
        collection_expr = collection_expr.strip()

        if not iterator_var or not collection_expr:
            raise ValueError(f"Invalid foreach expression: {expr}")

        return iterator_var, collection_expr

    def _generate_iteration_query(
        self, collection_expr: str, entity: EntityDefinition, context: dict
    ) -> str:
        """
        Generate the query for the FOR loop to iterate over

        Args:
            collection_expr: The collection to iterate (e.g., "related_orders", "(SELECT ...)", etc.)
            entity: Entity definition
            context: Compilation context

        Returns:
            SQL query for the FOR loop
        """
        # Check if it's a subquery
        expr_upper = collection_expr.strip().upper()
        if expr_upper.startswith("SELECT") or (
            expr_upper.startswith("(") and "SELECT" in expr_upper
        ):
            # Use the subquery directly
            return f"""        {collection_expr}"""

        # Handle simple cases like "related_orders"
        if collection_expr.startswith("related_"):
            # Handle related entities: "related_orders" -> query orders related to current entity
            related_entity = collection_expr[8:]  # Remove "related_" prefix
            # Convert plural to singular: "orders" -> "order"
            if related_entity.endswith("s"):
                related_entity = related_entity[:-1]

            fk_column = f"fk_{entity.name.lower()}"

            return f"""        SELECT * FROM {entity.schema}.tb_{related_entity}
        WHERE {fk_column} = v_pk"""

        # Handle field references like "input.related_items"
        elif "." in collection_expr:
            # This could be a reference to a field containing an array or JSON
            # For now, assume it's a table reference
            if collection_expr.startswith("input."):
                # Could be input.related_items - would need schema knowledge
                raise NotImplementedError(
                    f"Input field references not yet supported: {collection_expr}"
                )
            else:
                # Assume it's a table reference like "crm.tb_orders"
                return f"""        SELECT * FROM {collection_expr}"""

        # Handle direct table references
        elif collection_expr.count(".") == 1 and not collection_expr.startswith("("):
            # Looks like a table reference: "schema.table"
            return f"""        SELECT * FROM {collection_expr}"""

        else:
            # Try to treat it as a simple table name
            # This is a fallback - ideally should be more strict
            return f"""        SELECT * FROM {entity.schema}.{collection_expr}"""

    def _compile_loop_body(
        self, steps: list[ActionStep], entity: EntityDefinition, context: dict, iterator_var: str
    ) -> str:
        """
        Compile the steps to execute inside the FOR loop

        Args:
            steps: Steps to execute for each iteration
            entity: Entity definition
            context: Compilation context
            iterator_var: Name of the iterator variable

        Returns:
            Compiled PL/pgSQL for loop body
        """
        if not steps:
            return ""

        # Update context to include iterator variable
        loop_context = context.copy()
        loop_context["iterator_var"] = iterator_var

        compiled_steps = []
        for step in steps:
            compiler = self.step_compiler_registry.get(step.type)
            if not compiler:
                raise ValueError(f"No compiler registered for step type: {step.type}")

            compiled_step = compiler.compile(step, entity, loop_context)
            compiled_steps.append(compiled_step)

        return "\n\n".join(compiled_steps)
