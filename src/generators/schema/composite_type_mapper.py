"""
Composite Type Mapper

Maps Team A's composite type definitions to:
- JSONB columns
- PL/pgSQL validation functions
- GIN indexes
"""

from dataclasses import dataclass

from src.core.ast_models import FieldDefinition
from src.core.scalar_types import CompositeTypeDef, get_composite_type

from .index_strategy import generate_gin_index


@dataclass
class CompositeDDL:
    """DDL output for a composite field"""

    column_name: str
    postgres_type: str = "JSONB"
    nullable: bool = True
    validation_function: str | None = None
    check_constraint: str | None = None
    comment: str | None = None
    jsonb_schema: dict | None = None


class CompositeTypeMapper:
    """Maps composite types to PostgreSQL JSONB with validation"""

    def map_field(self, field: FieldDefinition) -> CompositeDDL:
        """
        Map composite field to JSONB with validation

        Args:
            field: FieldDefinition with composite type

        Returns:
            CompositeDDL with validation function name
        """
        if not field.is_composite():
            raise ValueError(f"Field {field.name} is not a composite type")

        # Get composite definition from registry if not set on field
        composite_def = field.composite_def
        if composite_def is None:
            composite_def = get_composite_type(field.type_name)
            if composite_def is None:
                raise ValueError(f"Composite type {field.type_name} not found in registry")

        # Generate validation function name (convert camelCase to snake_case)
        def camel_to_snake(name):
            import re

            return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

        validation_function = f"validate_{camel_to_snake(composite_def.name)}"

        # Generate CHECK constraint that calls validation function
        check_constraint = f"{validation_function}({field.name})"

        return CompositeDDL(
            column_name=field.name,
            postgres_type="JSONB",
            nullable=field.nullable,
            validation_function=validation_function,
            check_constraint=check_constraint,
            comment=composite_def.description,
            jsonb_schema=composite_def.get_jsonb_schema(),
        )

    def generate_validation_function(self, composite_def: CompositeTypeDef) -> str:
        """
        Generate PL/pgSQL validation function for composite type

        Example output:
            CREATE OR REPLACE FUNCTION validate_simple_address(data JSONB)
            RETURNS BOOLEAN AS $$
            BEGIN
                -- Check required fields
                IF NOT (data ? 'street' AND data ? 'city' AND data ? 'country_code') THEN
                    RETURN FALSE;
                END IF;

                -- Validate country_code format
                IF data->>'country_code' !~ '^[A-Z]{2}$' THEN
                    RETURN FALSE;
                END IF;

                RETURN TRUE;
            END;
            $$ LANGUAGE plpgsql IMMUTABLE;
        """

        def camel_to_snake(name):
            import re

            return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

        func_name = f"validate_{camel_to_snake(composite_def.name)}"

        validations = []

        # Required fields check
        required_fields = [
            f"'{field_name}'"
            for field_name, field_def in composite_def.fields.items()
            if not field_def.nullable
        ]

        if required_fields:
            fields_check = " AND ".join([f"data ? {f}" for f in required_fields])
            validations.append(
                f"""
    -- Check required fields
    IF NOT ({fields_check}) THEN
        RETURN FALSE;
    END IF;"""
            )

        # Field-level validations (basic type checking for now)
        for field_name, field_def in composite_def.fields.items():
            # Add basic validations based on type_name
            if field_def.type_name == "text":
                # For text fields, ensure they are strings if present
                validations.append(
                    f"""
    -- Validate {field_name} is text
    IF data ? '{field_name}' AND jsonb_typeof(data->'{field_name}') != 'string' THEN
        RETURN FALSE;
    END IF;"""
                )
            elif field_def.type_name in ["integer", "bigint"]:
                validations.append(
                    f"""
    -- Validate {field_name} is number
    IF data ? '{field_name}' AND jsonb_typeof(data->'{field_name}') != 'number' THEN
        RETURN FALSE;
    END IF;"""
                )
            elif field_def.type_name == "boolean":
                validations.append(
                    f"""
    -- Validate {field_name} is boolean
    IF data ? '{field_name}' AND jsonb_typeof(data->'{field_name}') != 'boolean' THEN
        RETURN FALSE;
    END IF;"""
                )

        return f"""
CREATE OR REPLACE FUNCTION {func_name}(data JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Return TRUE if data is NULL
    IF data IS NULL THEN
        RETURN TRUE;
    END IF;
{"".join(validations)}
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
"""

    def generate_field_ddl(self, composite_ddl: CompositeDDL) -> str:
        """
        Generate complete field DDL with validation CHECK

        Example output:
            shipping_address JSONB CHECK (validate_simple_address(shipping_address))
        """
        parts = [composite_ddl.column_name, composite_ddl.postgres_type]

        if not composite_ddl.nullable:
            parts.append("NOT NULL")

        if composite_ddl.check_constraint:
            parts.append(f"CHECK ({composite_ddl.check_constraint})")

        return " ".join(parts)

    def generate_gin_index(self, schema: str, table: str, composite_ddl: CompositeDDL) -> str:
        """
        Generate GIN index for JSONB queryability with partial index support

        Example output:
            CREATE INDEX idx_order_shipping_address
            ON crm.tb_order USING GIN (shipping_address)
            WHERE deleted_at IS NULL;
        """
        index_name = f"idx_{table}_{composite_ddl.column_name}"
        table_name = f"{schema}.{table}"

        return generate_gin_index(table_name, index_name, [composite_ddl.column_name])
