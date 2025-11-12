"""Compiler for subquery steps"""


from src.core.ast_models import ActionStep, EntityDefinition

from src.generators.actions.step_compilers.base import StepCompiler


class SubqueryStepCompiler(StepCompiler):
    """Compiles subquery steps to PL/pgSQL SELECT INTO statements"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Generate subquery SELECT INTO statement

        Returns:
            PL/pgSQL SELECT INTO statement for subquery result
        """
        query = step.subquery_query
        result_var = step.subquery_result_variable

        # For subqueries that return single values
        return f"SELECT ({query}) INTO {result_var};"