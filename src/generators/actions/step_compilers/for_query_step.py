"""Compiler for for_query steps"""

from src.core.ast_models import ActionStep
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.loop_optimizer import LoopOptimizer
from src.generators.actions.step_compilers.base import StepCompiler


class ForQueryStepCompiler(StepCompiler):
    """Compiles for_query steps to PL/pgSQL FOR loops"""

    def compile(self, step: ActionStep, context: CompilationContext) -> str:
        """
        Generate FOR record IN query LOOP statement

        Returns:
            FOR alias IN query LOOP ... END LOOP;
        """
        # Validate cursor usage
        LoopOptimizer.validate_cursor_usage(step)

        # Enter loop context with record variable
        record_var = step.for_query_alias or "rec"
        context.enter_loop("for_query", [record_var])

        try:
            query = step.for_query_sql
            alias = record_var
            body = self._compile_steps(step.for_query_body, context)

            return f"""FOR {alias} IN {query} LOOP
    {body}
END LOOP;"""
        finally:
            # Always exit loop context
            context.exit_loop()

    def _compile_steps(self, steps: list[ActionStep], context: CompilationContext) -> str:
        """Compile a list of steps into PL/pgSQL"""
        compiled = []
        for step in steps:
            compiler = self._get_compiler_for_step(step.type)
            if compiler:
                compiled.append(compiler.compile(step, context))
        return "\n    ".join(compiled)

    def _get_compiler_for_step(self, step_type: str):
        """Get the appropriate compiler for a step type"""
        # For now, return a simple mock compiler
        # In real implementation, this would use the full compiler registry
        class MockCompiler:
            def compile(self, step, context):
                return f"-- {step_type} step"
        return MockCompiler()