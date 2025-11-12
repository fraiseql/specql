"""Compiler for while steps"""

from src.core.ast_models import ActionStep
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.loop_optimizer import LoopOptimizer
from src.generators.actions.step_compilers.base import StepCompiler


class WhileStepCompiler(StepCompiler):
    """Compiles while steps to PL/pgSQL WHILE loops"""

    def compile(self, step: ActionStep, context: CompilationContext) -> str:
        """
        Generate WHILE LOOP statement

        Returns:
            WHILE condition LOOP ... END LOOP;
        """
        # Check for potential infinite loops
        if LoopOptimizer.detect_infinite_loops(step):
            # Could add warning or optimization here
            pass

        # Enter loop context
        context.enter_loop("while", [])

        try:
            condition = step.while_condition
            body = self._compile_steps(step.loop_body, context)

            return f"""WHILE {condition} LOOP
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