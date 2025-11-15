"""
Partial Update Step Compiler

Compiles 'update' steps to PL/pgSQL UPDATE statements with CASE expressions
for partial updates (PATCH semantics). Only updates fields present in input payload.

Example SpecQL:
    - update: Contact
      partial_updates: true
      track_updated_fields: true

Generated PL/pgSQL:
    -- Partial update Contact
    UPDATE crm.tb_contact
    SET
        first_name = CASE WHEN input_payload ? 'first_name'
                         THEN input_data.first_name
                         ELSE first_name END,
        last_name = CASE WHEN input_payload ? 'last_name'
                        THEN input_data.last_name
                        ELSE last_name END,
        updated_at = NOW(),
        updated_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- Track updated fields
    IF input_payload ? 'first_name' THEN
        v_updated_fields := v_updated_fields || ARRAY['first_name'];
    END IF;
"""

from src.core.ast_models import ActionStep, EntityDefinition


class PartialUpdateCompiler:
    """Compiles update steps with CASE expressions for partial updates"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile partial update step to PL/pgSQL with CASE expressions

        Args:
            step: ActionStep with type='update'
            entity: EntityDefinition
            context: Compilation context

        Returns:
            PL/pgSQL UPDATE statement with CASE expressions for partial updates
        """
        if step.type != "update":
            raise ValueError(f"Expected update step, got {step.type}")

        # Get configuration from step fields
        step.fields.get("partial_updates", True) if step.fields else True
        track_updated_fields = (
            step.fields.get("track_updated_fields", False) if step.fields else False
        )

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"

        # Generate CASE expressions for each field
        set_clauses = []
        tracking_code = ""

        for field_name, field_def in entity.fields.items():
            # Skip system fields that shouldn't be updated directly
            if field_name in ["id", "tenant_id", "created_at", "created_by"]:
                continue

            case_expr = self._generate_case_expression(field_name, field_def)
            set_clauses.append(case_expr)

            # Generate field tracking if requested
            if track_updated_fields:
                tracking_code += self._generate_field_tracking(field_name)

        # Add audit fields
        set_clauses.extend(["updated_at = NOW()", "updated_by = auth_user_id"])

        set_clause = ",\n        ".join(set_clauses)

        # Build WHERE clause
        where_clause = f"WHERE id = v_{entity_lower}_id AND tenant_id = auth_tenant_id"

        update_sql = f"""
    -- Partial update {entity.name}
    UPDATE {table_name}
    SET
        {set_clause}
    {where_clause};
"""

        # Add field tracking if requested
        if track_updated_fields and tracking_code:
            update_sql += f"\n{tracking_code}"

        return update_sql

    def _generate_case_expression(self, field_name: str, field_def) -> str:
        """
        Generate CASE expression for a field

        Args:
            field_name: Name of the field
            field_def: Field definition

        Returns:
            CASE expression string
        """
        return f"""{field_name} = CASE WHEN input_payload ? '{field_name}'
                         THEN input_data.{field_name}
                         ELSE {field_name} END"""

    def _generate_field_tracking(self, field_name: str) -> str:
        """
        Generate code to track which fields were updated

        Args:
            field_name: Name of the field

        Returns:
            PL/pgSQL code for field tracking
        """
        return f"""
    IF input_payload ? '{field_name}' THEN
        v_updated_fields := v_updated_fields || ARRAY['{field_name}'];
    END IF;"""
