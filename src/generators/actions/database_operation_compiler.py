"""
Database Operation Compiler - Transform database operations to PL/pgSQL
"""

from dataclasses import dataclass
from typing import Any

from src.core.ast_models import ActionStep, Entity
from src.utils.safe_slug import safe_slug, safe_table_name


class ObjectBuilder:
    """Builds GraphQL-compatible object responses with relationships"""

    def build_object_query(
        self, entity: Entity, include_relations: list[str] | None = None
    ) -> str:
        """Build SELECT query for full object with relationships"""
        fields = []
        joins = []
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        pk_column = f"pk_{safe_slug(entity.name)}"

        # __typename (for Apollo cache)
        fields.append(f"'__typename', '{entity.name}'")

        # ID field
        fields.append(f"'id', c.{pk_column}")

        # Primary fields
        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref":
                # Handle relationship
                if include_relations and field_name in include_relations:
                    target = field_def.reference_entity or field_name
                    fields.append(
                        f"'{field_name}', {self._build_relation_object(field_name, target)}"
                    )
                    joins.append(self._build_join(field_name, target, entity))
                else:
                    # Just include ID
                    fields.append(f"'{field_name}Id', c.fk_{field_name}")
            else:
                # Regular field
                camel_name = self._to_camel(field_name)
                fields.append(f"'{camel_name}', c.{field_name}")

        # Build query
        join_sql = "\n    ".join(joins) if joins else ""

        fields_sql = ",\n            ".join(fields)
        return f"""
    -- Return full {entity.name} object
    v_result.object_data := (
        SELECT jsonb_build_object(
            {fields_sql}
        )
        FROM {table_name} c
        {join_sql}
        WHERE c.{pk_column} = v_pk
    );
"""

    def _to_camel(self, snake: str) -> str:
        """Convert snake_case to camelCase"""
        parts = snake.split("_")
        return parts[0] + "".join(word.capitalize() for word in parts[1:])

    def _build_relation_object(self, field_name: str, target_entity: str) -> str:
        """Build JSON object for relationship"""
        return f"""jsonb_build_object(
            '__typename', '{target_entity}',
            'id', co.pk_{target_entity.lower()}
        )"""

    def _build_join(self, field_name: str, target_entity: str, entity: Entity) -> str:
        """Build JOIN clause for relationship"""
        return f"""LEFT JOIN management.tb_{target_entity.lower()} co ON co.pk_{target_entity.lower()} = c.fk_{field_name}"""


@dataclass
class DatabaseOperationCompiler:
    """Compiles database operation steps to PL/pgSQL"""

    def __init__(self) -> None:
        """Initialize with helper components"""
        self.object_builder = ObjectBuilder()

    def compile_insert(self, step: ActionStep, entity: Entity) -> str:
        """Generate INSERT statement with RETURNING"""
        table = f"{entity.schema}.{safe_table_name(entity.name)}"
        pk_column = f"pk_{safe_slug(entity.name)}"

        # Get field columns (exclude Trinity pattern fields - auto-generated)
        field_cols = []
        field_vals = []

        for field_name, field_def in entity.fields.items():
            col_name = (
                f"fk_{field_name}" if field_def.type_name == "ref" else field_name
            )
            field_cols.append(col_name)

            if field_def.type_name == "ref":
                # Resolve ref to pk
                target = field_def.reference_entity or field_name
                field_vals.append(
                    f"{entity.schema}.{target.lower()}_pk(p_{field_name}_id)"
                )
            else:
                field_vals.append(f"p_{field_name}")

        # Add audit fields
        field_cols.extend(["created_at", "created_by"])
        field_vals.extend(["now()", "p_caller_id"])

        return f"""
    -- Insert {entity.name}
    INSERT INTO {table} (
        {", ".join(field_cols)}
    ) VALUES (
        {", ".join(field_vals)}
    ) RETURNING {pk_column} INTO v_pk;
"""

    def compile_update(self, step: ActionStep, entity: Entity) -> str:
        """Generate UPDATE statement with auto-audit fields"""
        set_clauses = []
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        pk_column = f"pk_{safe_slug(entity.name)}"

        # User-specified fields
        for field_name, value in (step.fields or {}).items():
            set_clauses.append(f"{field_name} = {self._format_value(value)}")

        # Auto-audit fields
        set_clauses.extend(["updated_at = now()", "updated_by = p_caller_id"])

        return f"""
    -- Update {entity.name}
    UPDATE {table_name}
    SET {", ".join(set_clauses)}
    WHERE {pk_column} = v_pk;
    """

    def generate_object_return(
        self, step: ActionStep, entity: Entity, impact: Any | None = None
    ) -> str:
        """Generate full object return with relationships"""
        include_relations = None
        if (
            impact
            and hasattr(impact, "primary")
            and hasattr(impact.primary, "include_relations")
        ):
            relations = getattr(impact.primary, "include_relations", None)
            if isinstance(relations, list):
                include_relations = relations

        return self.object_builder.build_object_query(entity, include_relations)

    def _format_value(self, value: str) -> str:
        """Format value for SQL SET clause"""
        # If it's a string literal, escape and wrap in quotes
        if isinstance(value, str):
            # FIXED: proper escaping to prevent SQL injection
            from src.generators.sql_utils import SQLUtils

            escaped = SQLUtils.escape_string_literal(value)
            return f"'{escaped}'"
        return str(value)
