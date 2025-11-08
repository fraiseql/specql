"""
Delete Step Compiler

Compiles 'delete' steps to PL/pgSQL soft delete (sets deleted_at).

Example SpecQL:
    - delete: Contact WHERE status = 'inactive'

Generated PL/pgSQL:
    -- Soft delete Contact
    UPDATE crm.tb_contact
    SET deleted_at = now(),
        deleted_by = p_caller_id
    WHERE pk_contact = v_pk AND (status = 'inactive');
"""

from src.core.ast_models import ActionStep, EntityDefinition


class DeleteStepCompiler:
    """Compiles delete steps to PL/pgSQL soft delete"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile delete step to PL/pgSQL soft delete

        Note: We use UPDATE to set deleted_at, not actual DELETE.
        This preserves audit trail.
        """
        if step.type != "delete":
            raise ValueError(f"Expected delete step, got {step.type}")

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"
        pk_column = f"pk_{entity_lower}"

        where_clause = step.where_clause or ""

        # Build WHERE clause
        if where_clause:
            where_sql = f"WHERE {pk_column} = v_pk AND ({where_clause})"
        else:
            where_sql = f"WHERE {pk_column} = v_pk"

        return f"""
    -- Soft delete {entity.name}
    UPDATE {table_name}
    SET deleted_at = now(),
        deleted_by = p_caller_id
    {where_sql};
"""
