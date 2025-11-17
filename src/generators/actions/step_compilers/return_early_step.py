"""Compiler for return_early steps"""

from src.core.ast_models import ActionStep, EntityDefinition
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.step_compilers.base import StepCompiler


class ReturnEarlyStepCompiler(StepCompiler):
    """Compiles return_early steps to PL/pgSQL RETURN statement"""

    def compile(
        self, step: ActionStep, entity: EntityDefinition, context: CompilationContext
    ) -> str:
        """
        Compile early return to RETURN statement

        Returns:
            PL/pgSQL RETURN statement
        """
        return_value = step.return_value

        if return_value is None:
            return "RETURN;"

        # For actions, always return mutation_result format
        return self._build_mutation_result(return_value)

    def _build_mutation_result(self, value: dict) -> str:
        """Build mutation_result return value"""
        return f"""RETURN ROW(
    {value.get("success", "false")}::BOOLEAN,
    {value.get("message", "''")}::TEXT,
    '{{}}'::JSONB,
    '{{}}'::JSONB
)::app.mutation_result;"""
