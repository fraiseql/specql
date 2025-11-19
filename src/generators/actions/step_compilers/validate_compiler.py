"""
Validate Step Compiler

Compiles 'validate' steps to PL/pgSQL validation logic.

Example SpecQL:
    - validate: status = 'lead'
      error: "not_a_lead"

Generated PL/pgSQL:
    -- Validate: status = 'lead'
    SELECT status INTO v_status
    FROM crm.tb_contact
    WHERE pk_contact = v_pk;

    IF v_status != 'lead' THEN
        v_result.status := 'error';
        v_result.message := 'not_a_lead';
        RETURN v_result;
    END IF;
"""

from src.core.ast_models import ActionStep, EntityDefinition
from src.core.scalar_types import get_scalar_type


class ValidateStepCompiler:
    """Compiles validate steps to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile validate step to PL/pgSQL

        Args:
            step: ActionStep with type='validate'
            entity: EntityDefinition for table/schema context
            context: Compilation context (variables, etc.)

        Returns:
            PL/pgSQL code for validation
        """
        if step.type != "validate":
            raise ValueError(f"Expected validate step, got {step.type}")

        expression = step.expression
        if not expression:
            raise ValueError("Validate step must have an expression")
        error_code = step.error or "validation_failed"

        # Check if this is a scalar type validation
        scalar_validation = self._is_scalar_validation(expression, entity)
        if scalar_validation:
            return self._compile_scalar_validation(scalar_validation, error_code, entity)

        # Parse expression to extract field references
        fields_to_fetch = self._extract_fields(expression, entity)

        # Generate SELECT to fetch field values
        select_sql = self._generate_select(fields_to_fetch, entity)

        # Generate IF check for validation
        check_sql = self._generate_check(expression, error_code, entity)

        return f"""
    -- Validate: {expression}
{select_sql}

{check_sql}
"""

    def _extract_fields(self, expression: str, entity: EntityDefinition) -> list[str]:
        """
        Extract field names from validation expression

        Example:
            "status = 'lead' AND email IS NOT NULL"
            → ["status", "email"]
        """
        import re

        # Get all field names from entity
        field_names = list(entity.fields.keys())

        # Find which fields are referenced in expression
        fields_in_expr = []
        for field_name in field_names:
            # Match whole word only (avoid partial matches)
            if re.search(rf"\b{field_name}\b", expression):
                fields_in_expr.append(field_name)

        return fields_in_expr

    def _generate_select(self, fields: list[str], entity: EntityDefinition) -> str:
        """
        Generate SELECT statement to fetch field values

        Example:
            SELECT status, email INTO v_status, v_email
            FROM crm.tb_contact
            WHERE pk_contact = v_pk;
        """
        if not fields:
            return ""

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"
        pk_column = f"pk_{entity_lower}"

        # Build SELECT list with INTO clause
        select_list = ", ".join(fields)
        into_list = ", ".join(f"v_{field}" for field in fields)

        return f"""    SELECT {select_list} INTO {into_list}
    FROM {table_name}
    WHERE {pk_column} = v_pk;"""

    def _generate_check(self, expression: str, error_code: str, entity: EntityDefinition) -> str:
        """
        Generate IF check for validation

        Example:
            IF NOT (v_status = 'lead') THEN
                v_result.status := 'error';
                v_result.message := 'not_a_lead';
                RETURN v_result;
            END IF;
        """
        # Replace field names with v_field variables
        check_expr = self._replace_fields_with_vars(expression, entity)

        return f"""    IF NOT ({check_expr}) THEN
        v_result.status := 'error';
        v_result.message := '{error_code}';
        RETURN v_result;
    END IF;"""

    def _replace_fields_with_vars(self, expression: str, entity: EntityDefinition) -> str:
        """
        Replace field names with v_field variables

        Example:
            "status = 'lead'" → "v_status = 'lead'"
        """
        # Replace field names with v_ prefix
        field_names = set(entity.fields.keys())

        for field_name in field_names:
            # Replace whole word matches only
            import re

            expression = re.sub(rf"\b{re.escape(field_name)}\b", f"v_{field_name}", expression)

        return expression

    def _is_scalar_validation(
        self, expression: str, entity: EntityDefinition
    ) -> tuple[str, str] | None:
        """
        Check if expression is a scalar type validation

        Returns:
            (field_name, validation_type) or None

        Examples:
            "email is valid" → ("email", "email")
            "phone is valid" → ("phone", "phone")
        """
        import re

        # Pattern: "field_name is valid"
        match = re.match(r"^(\w+)\s+is\s+valid$", expression.strip(), re.IGNORECASE)
        if not match:
            return None

        field_name = match.group(1)
        if field_name not in entity.fields:
            return None

        field_def = entity.fields[field_name]
        if not field_def.scalar_def:
            return None

        return (field_name, field_def.type_name)

    def _compile_scalar_validation(
        self, scalar_validation: tuple[str, str], error_code: str, entity: EntityDefinition
    ) -> str:
        """
        Compile scalar type validation

        Args:
            scalar_validation: (field_name, scalar_type)
            error_code: Error code for validation failure
            entity: Entity definition

        Returns:
            PL/pgSQL validation code
        """
        field_name, scalar_type = scalar_validation
        scalar_def = get_scalar_type(scalar_type)

        if not scalar_def:
            raise ValueError(f"Unknown scalar type: {scalar_type}")

        entity_lower = entity.name.lower()
        table_name = f"{entity.schema}.tb_{entity_lower}"
        pk_column = f"pk_{entity_lower}"

        # Generate validation logic based on scalar type
        validation_checks = []

        # Pattern validation
        if scalar_def.validation_pattern:
            pattern = scalar_def.validation_pattern
            validation_checks.append(f"NOT (v_{field_name} ~ '{pattern}')")

        # Min/Max validation for numeric types
        if scalar_def.min_value is not None:
            validation_checks.append(f"v_{field_name} < {scalar_def.min_value}")

        if scalar_def.max_value is not None:
            validation_checks.append(f"v_{field_name} > {scalar_def.max_value}")

        # Length validation for strings
        if scalar_def.postgres_precision and len(scalar_def.postgres_precision) >= 2:
            max_length = scalar_def.postgres_precision[1]
            validation_checks.append(f"length(v_{field_name}) > {max_length}")

        if not validation_checks:
            # No specific validations, just check if field is not null for required fields
            if not entity.fields[field_name].nullable:
                validation_checks.append(f"v_{field_name} IS NULL")

        if not validation_checks:
            # Fallback: assume valid if we reach here
            return f"""
    -- Validate scalar: {field_name} is valid
    SELECT {field_name} INTO v_{field_name}
    FROM {table_name}
    WHERE {pk_column} = v_pk;

    -- No specific validation rules for {scalar_type}
"""

        # Combine all validation checks
        combined_check = " OR ".join(validation_checks)

        return f"""
    -- Validate scalar: {field_name} is valid ({scalar_type})
    SELECT {field_name} INTO v_{field_name}
    FROM {table_name}
    WHERE {pk_column} = v_pk;

    IF ({combined_check}) THEN
        v_result.status := 'error';
        v_result.message := '{error_code}';
        RETURN v_result;
    END IF;
"""
