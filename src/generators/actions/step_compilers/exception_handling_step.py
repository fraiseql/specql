"""Compiler for exception_handling steps"""

from src.core.ast_models import ActionStep
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.exception_optimizer import ExceptionOptimizer
from src.generators.actions.step_compilers.base import StepCompiler


class ExceptionHandlingStepCompiler(StepCompiler):
    """Compiles exception_handling steps to PL/pgSQL BEGIN/EXCEPTION blocks"""

    def compile(self, step: ActionStep, context: CompilationContext) -> str:
        """
        Generate BEGIN ... EXCEPTION WHEN ... END block

        Returns:
            BEGIN ... EXCEPTION WHEN ... END;
        """
        # Optimize exception handlers
        optimized_handlers = ExceptionOptimizer.optimize_exception_handlers(step.catch_handlers)

        # Enter exception context
        context.enter_exception_handler()

        try:
            try_body = self._compile_steps(step.try_steps, context)
            finally_body = self._compile_steps(step.finally_steps, context) if step.finally_steps else ""

            # Build exception handlers
            exception_blocks = []
            for handler in optimized_handlers:
                when_condition = ExceptionOptimizer.map_specql_to_postgres_exceptions(handler.when_condition)
                handler_body = self._compile_steps(handler.then_steps, context)
                exception_blocks.append(f"""WHEN {when_condition} THEN
    {handler_body}""")

            exception_block = "\n".join(exception_blocks)

            finally_clause = f"FINALLY\n    {finally_body}" if finally_body else ""
            return f"""BEGIN
    {try_body}
EXCEPTION
    {exception_block}
{finally_clause}
END;"""
        finally:
            # Always exit exception context
            context.exit_exception_handler()

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