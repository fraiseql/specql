# src/adapters/postgresql_adapter.py
"""
PostgreSQL Adapter

Converts Universal AST entities into PostgreSQL + PL/pgSQL code.
"""

from typing import List, Dict, Optional

from src.adapters.base_adapter import FrameworkAdapter, GeneratedCode, FrameworkConventions
from src.core.universal_ast import UniversalEntity, UniversalAction, UniversalField, FieldType


class PostgreSQLAdapter(FrameworkAdapter):
    """Adapter for PostgreSQL + PL/pgSQL"""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate PostgreSQL table DDL"""
        ddl = self._generate_basic_ddl(entity)

        return [
            GeneratedCode(
                file_path=f"db/schema/10_tables/{entity.name.lower()}.sql",
                content=ddl,
                language="sql",
            )
        ]

    def generate_action(
        self, action: UniversalAction, entity: UniversalEntity
    ) -> List[GeneratedCode]:
        """Generate PL/pgSQL function"""
        plpgsql = self._generate_basic_plpgsql(action, entity)

        return [
            GeneratedCode(
                file_path=f"db/schema/06_functions/{entity.schema}/{action.name}.sql",
                content=plpgsql,
                language="sql",
            )
        ]

    def generate_relationship(self, field: UniversalField, entity: UniversalEntity) -> str:
        """Generate PostgreSQL foreign key relationship"""
        if field.type == FieldType.REFERENCE:
            ref_entity = field.references
            return f"REFERENCES tb_{ref_entity.lower()}(pk_{ref_entity.lower()})"
        return ""

    def get_conventions(self) -> FrameworkConventions:
        return FrameworkConventions(
            naming_case="snake_case",
            primary_key_name="pk_{entity}",
            foreign_key_pattern="fk_{entity}",
            timestamp_fields=["created_at", "updated_at", "deleted_at"],
            supports_multi_tenancy=True,
        )

    def get_framework_name(self) -> str:
        return "postgresql"

    def _generate_basic_ddl(self, entity: UniversalEntity) -> str:
        """Generate basic PostgreSQL DDL for an entity"""
        lines = []

        # Table name
        table_name = f"tb_{entity.name.lower()}"
        lines.append(f"CREATE TABLE {table_name} (")

        # Trinity pattern fields
        lines.append(f"    pk_{entity.name.lower()} SERIAL PRIMARY KEY,")
        lines.append("    id UUID NOT NULL DEFAULT gen_random_uuid(),")
        lines.append("    identifier VARCHAR(255) NOT NULL,")

        # Multi-tenancy
        if entity.is_multi_tenant:
            lines.append("    tenant_id UUID NOT NULL,")

        # Business fields
        for field in entity.fields:
            pg_type = self._map_field_to_postgres_type(field)
            nullable = "NOT NULL" if field.required else ""
            default = f"DEFAULT {field.default}" if field.default else ""
            constraint = self.generate_relationship(field, entity)

            field_def = f"    {field.name} {pg_type}"
            if nullable:
                field_def += f" {nullable}"
            if default:
                field_def += f" {default}"
            if constraint:
                field_def += f" {constraint}"

            lines.append(field_def + ",")

        # Audit fields
        lines.append("    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),")
        lines.append("    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),")
        lines.append("    deleted_at TIMESTAMPTZ NULL")

        lines.append(");")

        # Indexes
        if entity.is_multi_tenant:
            lines.append(f"CREATE INDEX idx_{table_name}_tenant ON {table_name}(tenant_id);")

        for field in entity.fields:
            if field.type == FieldType.REFERENCE:
                lines.append(
                    f"CREATE INDEX idx_{table_name}_{field.name} ON {table_name}({field.name});"
                )
            elif field.type == FieldType.ENUM:
                lines.append(
                    f"CREATE INDEX idx_{table_name}_{field.name} ON {table_name}({field.name});"
                )

        return "\n".join(lines)

    def _generate_basic_plpgsql(self, action: UniversalAction, entity: UniversalEntity) -> str:
        """Generate basic PL/pgSQL function for an action"""
        function_name = f"{entity.schema}.{action.name}"
        lines = []

        lines.append(f"CREATE OR REPLACE FUNCTION {function_name}()")
        lines.append("RETURNS JSONB")
        lines.append("LANGUAGE plpgsql")
        lines.append("AS $$")
        lines.append("DECLARE")
        lines.append("    result JSONB;")
        lines.append("BEGIN")

        # Generate function body based on steps
        for step in action.steps:
            if step.type.value == "validate":
                lines.append(f"    -- Validate: {step.expression}")
                # Basic validation - would need more sophisticated expression parsing
                lines.append(f"    IF NOT ({step.expression}) THEN")
                lines.append(f"        RAISE EXCEPTION 'Validation failed: {step.expression}';")
                lines.append("    END IF;")
            elif step.type.value == "update":
                lines.append(f"    -- Update {step.entity}")
                if step.fields:
                    set_clause = ", ".join([f"{k} = {repr(v)}" for k, v in step.fields.items()])
                    lines.append(f"    UPDATE tb_{step.entity.lower()} SET {set_clause};")
            elif step.type.value == "insert":
                lines.append(f"    -- Insert into {step.entity}")
                # Simplified insert logic

        # Return success
        lines.append("    result := jsonb_build_object(")
        lines.append("        'success', true,")
        lines.append("        'message', 'Action completed successfully'")
        lines.append("    );")
        lines.append("    RETURN result;")
        lines.append("END;")
        lines.append("$$;")

        return "\n".join(lines)

    def _map_field_to_postgres_type(self, field: UniversalField) -> str:
        """Map UniversalField type to PostgreSQL type"""
        if field.type == FieldType.TEXT:
            return "TEXT"
        elif field.type == FieldType.INTEGER:
            return "INTEGER"
        elif field.type == FieldType.BOOLEAN:
            return "BOOLEAN"
        elif field.type == FieldType.DATETIME:
            return "TIMESTAMPTZ"
        elif field.type == FieldType.REFERENCE:
            return "INTEGER"  # FK to pk_* column
        elif field.type == FieldType.ENUM:
            return "TEXT"  # Enums stored as TEXT
        elif field.type == FieldType.RICH:
            return "JSONB"  # Rich types as JSONB
        else:
            return "TEXT"
