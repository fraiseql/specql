"""Compiler for declare steps"""

from typing import Any

from src.core.ast_models import ActionStep, EntityDefinition
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.step_compilers.base import StepCompiler
from src.generators.actions.type_mapper import TypeMapper


class DeclareStepCompiler(StepCompiler):
    """Compiles declare steps to PL/pgSQL DECLARE block"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: CompilationContext) -> str:
        """
        Generate DECLARE statement(s)

        Returns:
            DECLARE block entries (not full block, added to function DECLARE section)
        """
        if step.variable_name:
            # Single declaration
            context.add_variable(step.variable_name, step.variable_type or "text")
            default = ""
            if step.default_value is not None:
                default = f" := {self._format_value(step.default_value)}"

            pg_type = TypeMapper.to_postgres(step.variable_type or "text")
            return f"{step.variable_name} {pg_type}{default};"

        elif step.declarations:
            # Multiple declarations
            lines = []
            for decl in step.declarations:
                context.add_variable(decl.name, decl.type)
                default = ""
                if decl.default_value is not None:
                    default = f" := {self._format_value(decl.default_value)}"

                pg_type = TypeMapper.to_postgres(decl.type)
                lines.append(f"{decl.name} {pg_type}{default};")

            return "\n".join(lines)

        return ""

    def _format_value(self, value: Any) -> str:
        """Format a value for SQL"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        else:
            return str(value)