"""
Insert Step Compiler

Compiles 'insert' steps to PL/pgSQL INSERT statements with Trinity Pattern and audit fields.

Example SpecQL:
    - insert: Notification(contact_id = $contact_id, message = "Lead qualified")

Generated PL/pgSQL:
    -- Insert Notification
    INSERT INTO core.tb_notification (
        fk_contact,
        message,
        created_at,    -- AUTO: Audit field
        created_by     -- AUTO: Audit field
    ) VALUES (
        v_pk,
        'Lead qualified',
        now(),
        p_caller_id
    ) RETURNING pk_notification INTO v_notification_pk;
"""

from typing import Any

from src.core.ast_models import ActionStep, EntityDefinition


class InsertStepCompiler:
    """Compiles insert steps to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile insert step to PL/pgSQL INSERT

        Args:
            step: ActionStep with type='insert'
            entity: Target entity for insertion
            context: Compilation context

        Returns:
            PL/pgSQL INSERT statement with Trinity Pattern and audit fields
        """
        if step.type != "insert":
            raise ValueError(f"Expected insert step, got {step.type}")

        target_entity = step.entity
        if not target_entity:
            raise ValueError("Insert step must specify target entity")
        fields = step.fields or {}

        entity_lower = target_entity.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"  # TODO: lookup schema
        pk_column = f"pk_{entity_lower}"

        # Build column list and value list
        columns = []
        values = []

        for field_name, field_value in fields.items():
            # Handle FK references (convert to fk_*)
            if field_name.endswith("_id"):
                col_name = f"fk_{field_name[:-3]}"  # contact_id → fk_contact
            else:
                col_name = field_name

            columns.append(col_name)
            values.append(self._format_value(field_value))

        # Add audit fields (AUTO)
        columns.extend(["created_at", "created_by"])
        values.extend(["now()", "p_caller_id"])

        columns_str = ", ".join(columns)
        values_str = ", ".join(values)

        # Generate variable for returned PK
        pk_var = f"v_{entity_lower}_pk"

        return f"""
    -- Insert {target_entity}
    INSERT INTO {table_name} (
        {columns_str}
    ) VALUES (
        {values_str}
    ) RETURNING {pk_column} INTO {pk_var};
"""

    def _format_value(self, value: Any) -> str:
        """Format value for SQL"""
        if isinstance(value, str):
            if value.startswith("$"):
                # Variable reference
                return f"v_{value[1:]}"
            else:
                # String literal
                return f"'{value}'"
        else:
            return str(value)
