"""Compiler for json_build steps"""

from typing import Any

from src.core.ast_models import ActionStep, EntityDefinition
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.step_compilers.base import StepCompiler


class JsonBuildStepCompiler(StepCompiler):
    """Compiles json_build steps to PL/pgSQL JSON construction"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: CompilationContext) -> str:
        """
        Generate JSON construction statement

        Returns:
            Assignment statement that builds JSON
        """
        if not step.json_variable_name or not step.json_object:
            return ""

        # Build JSON construction
        json_expr = self._build_json_expression(step.json_object)
        return f"{step.json_variable_name} := {json_expr};"

    def _build_json_expression(self, obj: dict[str, Any]) -> str:
        """Build JSON expression from dictionary"""
        if not obj:
            return "'{}'::jsonb"

        # Build json_build_object call
        args = []
        for key, value in obj.items():
            args.append(f"'{key}'")
            args.append(self._format_json_value(value))

        return f"json_build_object({', '.join(args)})"

    def _format_json_value(self, value: Any) -> str:
        """Format a value for JSON construction"""
        if isinstance(value, str):
            if value.startswith("$"):
                # Variable reference
                return value[1:]  # Remove $ prefix
            else:
                # String literal
                return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, dict):
            # Nested object
            return self._build_json_expression(value)
        elif isinstance(value, list):
            # Array
            return self._build_json_array(value)
        else:
            return str(value)

    def _build_json_array(self, arr: list[Any]) -> str:
        """Build JSON array expression"""
        if not arr:
            return "'[]'::jsonb"

        args = [self._format_json_value(item) for item in arr]
        return f"json_build_array({', '.join(args)})"