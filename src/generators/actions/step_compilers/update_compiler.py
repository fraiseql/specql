"""
Update Step Compiler

Compiles 'update' steps to PL/pgSQL UPDATE statements with audit fields.

Example SpecQL:
    - update: Contact SET status = 'qualified', qualified_at = now()

Generated PL/pgSQL:
    -- Update Contact
    UPDATE crm.tb_contact
    SET status = 'qualified',
        qualified_at = now(),
        updated_at = now(),        -- AUTO: Audit field
        updated_by = p_caller_id   -- AUTO: Audit field
    WHERE pk_contact = v_pk;
"""

from src.core.ast_models import ActionStep, EntityDefinition


class UpdateStepCompiler:
    """Compiles update steps to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile update step to PL/pgSQL

        Args:
            step: ActionStep with type='update'
            entity: EntityDefinition
            context: Compilation context

        Returns:
            PL/pgSQL UPDATE statement with audit fields
        """
        if step.type != "update":
            raise ValueError(f"Expected update step, got {step.type}")

        # Parse UPDATE statement
        # Format: "update: Entity SET field = value, field2 = value2 WHERE condition"
        update_spec = step.fields.get("raw_set", "") if step.fields else ""
        where_clause = step.where_clause

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"
        pk_column = f"pk_{entity_lower}"

        # Parse SET clause
        set_assignments = self._parse_set_clause(update_spec)

        # Add audit fields (AUTO)
        set_assignments.append("updated_at = now()")
        set_assignments.append("updated_by = p_caller_id")

        set_clause = ",\n        ".join(set_assignments)

        # Build WHERE clause
        if where_clause:
            where_sql = f"WHERE {pk_column} = v_pk AND ({where_clause})"
        else:
            where_sql = f"WHERE {pk_column} = v_pk"

        return f"""
    -- Update {entity.name}
    UPDATE {table_name}
    SET {set_clause}
    {where_sql};
"""

    def _parse_set_clause(self, set_spec: str) -> list[str]:
        """
        Parse SET clause into individual assignments

        Example:
            "status = 'qualified', qualified_at = now()"
            → ["status = 'qualified'", "qualified_at = now()"]
        """
        # Simple comma split (TODO: handle commas in strings)
        assignments = [a.strip() for a in set_spec.split(",")]
        return assignments
