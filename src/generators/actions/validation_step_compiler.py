"""
Validation Step Compiler - Transform validation steps to PL/pgSQL
"""

import re
from dataclasses import dataclass

from src.core.ast_models import ActionStep, Entity


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

    def _parse_pattern_match(self, expr: str) -> str:
        """Transform MATCHES to PostgreSQL regex operator"""
        match = re.match(r"(\w+)\s+MATCHES\s+(\w+)", expr)
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
        """Get regex pattern by name"""
        patterns = {
            "email_pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone_pattern": r"^\+?[1-9]\d{1,14}$",
        }
        return patterns.get(pattern_name, ".*")


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
