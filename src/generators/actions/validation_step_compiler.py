"""
Validation Step Compiler - Transform validation steps to PL/pgSQL
"""

import re
from dataclasses import dataclass

from src.core.ast_models import ActionStep, Entity
from src.core.scalar_types import get_scalar_type


class ExpressionParser:
    """Parses and transforms SpecQL expressions to PostgreSQL SQL"""

    def __init__(self, entity: Entity):
        self.entity = entity

    def parse(self, expr: str, in_exists_where: bool = False) -> str:
        """Parse SpecQL expression to SQL"""
        if self._is_pattern_match(expr):
            return self._parse_pattern_match(expr)

        if self._is_exists_query(expr):
            return self._parse_exists_query(expr)

        if self._is_rich_type_validation(expr):
            return self._parse_rich_type_validation(expr)

        if self._is_comparison(expr):
            return self._parse_comparison(expr, in_exists_where)

        return self._replace_identifiers(expr, in_exists_where)

    def _is_pattern_match(self, expr: str) -> bool:
        """Check if expression is a pattern match"""
        return "MATCHES" in expr

    def _is_exists_query(self, expr: str) -> bool:
        """Check if expression is an EXISTS query"""
        return "EXISTS" in expr

    def _is_comparison(self, expr: str) -> bool:
        """Check if expression is a comparison"""
        return any(op in expr for op in ["=", "!=", "<", ">", "<=", ">=", "IS", "LIKE"])

    def _is_rich_type_validation(self, expr: str) -> bool:
        """Check if expression is a rich type validation request"""
        return expr.strip().startswith("VALIDATE ")

    def _parse_pattern_match(self, expr: str) -> str:
        """Transform MATCHES to PostgreSQL regex operator"""
        match = re.match(r"(\w+)\s+MATCHES\s+['\"]?(\w+)['\"]?", expr)
        if match:
            field, pattern_name = match.groups()
            pattern = self._get_pattern(pattern_name)
            return f"{field} ~ '{pattern}'"
        return expr

    def _parse_exists_query(self, expr: str) -> str:
        """Transform EXISTS query to PostgreSQL"""
        match = re.match(r"(NOT\s+)?EXISTS\s+(\w+)\s+WHERE\s+(.+)", expr)
        if match:
            not_clause, entity_name, where = match.groups()
            not_clause = not_clause or ""

            table = f"{self.entity.schema}.tb_{entity_name.lower()}"
            where_sql = self.parse(where, in_exists_where=True)

            return f"{not_clause}EXISTS (SELECT 1 FROM {table} WHERE {where_sql})"

        return expr

    def _parse_comparison(self, expr: str, in_exists_where: bool) -> str:
        """Parse comparison expression"""
        return self._replace_identifiers(expr, in_exists_where)

    def _parse_rich_type_validation(self, expr: str) -> str:
        """Parse VALIDATE field_name expression"""
        match = re.match(r"VALIDATE\s+(\w+)", expr.strip())
        if match:
            field_name = match.group(1)
            validation = self._get_rich_type_validation(field_name)
            if validation:
                return validation
            else:
                raise ValueError(f"No validation defined for rich type field: {field_name}")
        return expr

    def _replace_identifiers(self, expr: str, in_exists_where: bool) -> str:
        """Replace field references with appropriate identifiers"""
        # Replace "input.field" with "p_field"
        expr = re.sub(r"input\.(\w+)", r"p_\1", expr)

        # Replace bare field names with parameters (only outside EXISTS WHERE clauses)
        if not in_exists_where:
            for field_name in self.entity.fields.keys():
                expr = re.sub(rf"\b{field_name}\b", f"p_{field_name}", expr)

        return expr

    def _get_pattern(self, pattern_name: str) -> str:
        """Get regex pattern by name from rich type definitions"""
        # Handle legacy pattern names for backward compatibility
        legacy_patterns = {
            "email_pattern": "email",
            "phone_pattern": "phoneNumber",
        }

        # Map legacy names to rich type names
        rich_type_name = legacy_patterns.get(pattern_name, pattern_name)

        # Get pattern from scalar types registry
        scalar_def = get_scalar_type(rich_type_name)
        if scalar_def and scalar_def.validation_pattern:
            return scalar_def.validation_pattern

        # Fallback for unknown patterns
        return ".*"

    def _get_rich_type_validation(self, field_name: str) -> str | None:
        """
        Get validation expression for a rich type field

        Args:
            field_name: Name of the field to validate

        Returns:
            SQL validation expression or None if no validation needed
        """
        field_def = self.entity.fields.get(field_name)
        if not field_def:
            return None

        # Get the scalar type definition
        scalar_def = get_scalar_type(field_def.type_name)
        if not scalar_def:
            return None

        validations = []

        # Add regex validation if pattern exists
        if scalar_def.validation_pattern:
            validations.append(f"p_{field_name} ~ '{scalar_def.validation_pattern}'")

        # Add range validation for numeric types
        if scalar_def.min_value is not None:
            validations.append(f"p_{field_name} >= {scalar_def.min_value}")

        if scalar_def.max_value is not None:
            validations.append(f"p_{field_name} <= {scalar_def.max_value}")

        # Combine validations with AND
        if validations:
            return " AND ".join(validations)

        return None


@dataclass
class ValidationStepCompiler:
    """Compiles validation steps to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: Entity) -> str:
        """Generate validation SQL from step"""
        expression = step.expression or ""
        error_code = step.error or ""

        # Transform expression to SQL
        parser = ExpressionParser(entity)
        sql_expr = parser.parse(expression)

        return f"""
    -- Validation: {expression}
    IF NOT ({sql_expr}) THEN
        v_result.status := 'error';
        v_result.message := '{error_code}';
        v_result.object_data := '{{}}'::jsonb;
        RETURN v_result;
    END IF;
"""
