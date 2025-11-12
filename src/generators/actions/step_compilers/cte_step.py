"""Compiler for CTE steps"""

from src.core.ast_models import ActionStep, EntityDefinition
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.step_compilers.base import StepCompiler


class CTEStepCompiler(StepCompiler):
    """Compiles CTE steps to SQL WITH clauses"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: CompilationContext) -> str:
        """
        Generate CTE definition

        Returns:
            CTE definition (will be collected and added to WITH clause)
        """
        context.add_cte(step.cte_name, step.cte_query or "", step.cte_materialized)

        # Return empty string (CTEs are added at query level, not inline)
        return ""

    def get_cte_clause(self, context: CompilationContext) -> str:
        """Build the WITH clause from collected CTEs"""
        return context.get_with_clause()