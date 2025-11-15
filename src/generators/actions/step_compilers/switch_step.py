"""Compiler for switch steps"""

from src.core.ast_models import ActionStep, EntityDefinition
from src.generators.actions.compilation_context import CompilationContext
from src.generators.actions.step_compilers.base import StepCompiler
from src.generators.actions.switch_optimizer import SwitchOptimizer


class SwitchStepCompiler(StepCompiler):
    """Compiles switch steps to PL/pgSQL CASE WHEN or IF/ELSIF"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: CompilationContext) -> str:
        """
        Compile switch to CASE WHEN or IF/ELSIF chain

        Returns:
            PL/pgSQL code for the switch statement
        """
        # Validate switch structure
        SwitchOptimizer.validate_switch_cases(step.cases)

        if SwitchOptimizer.detect_simple_switch(step.cases, step.switch_expression):
            # Use CASE expression for simple value matching
            return self._compile_as_case_expression(step, context)
        else:
            # Use IF/ELSIF for complex conditions
            return self._compile_as_if_chain(step, context)

    def _compile_as_case_expression(self, step: ActionStep, context: CompilationContext) -> str:
        """Compile to CASE WHEN expression"""
        lines = [f"CASE {step.switch_expression}"]

        for case in step.cases:
            when_value = case.when_value
            then_body = self._compile_steps(case.then_steps, context)
            lines.append(f"  WHEN {when_value} THEN")
            if then_body.strip():
                lines.append(f"    {then_body}")

        if step.default_steps:
            default_body = self._compile_steps(step.default_steps, context)
            lines.append("  ELSE")
            if default_body.strip():
                lines.append(f"    {default_body}")

        lines.append("END CASE;")
        return "\n".join(lines)

    def _compile_as_if_chain(self, step: ActionStep, context: CompilationContext) -> str:
        """Compile to IF/ELSIF/ELSE chain"""
        lines = []

        for i, case in enumerate(step.cases):
            keyword = "IF" if i == 0 else "ELSIF"
            condition = case.when_condition or case.when_value
            then_body = self._compile_steps(case.then_steps, context)

            lines.append(f"{keyword} {condition} THEN")
            if then_body.strip():
                lines.append(f"  {then_body}")

        if step.default_steps:
            default_body = self._compile_steps(step.default_steps, context)
            lines.append("ELSE")
            if default_body.strip():
                lines.append(f"  {default_body}")

        lines.append("END IF;")
        return "\n".join(lines)

    def _compile_steps(self, steps: list[ActionStep], context: CompilationContext) -> str:
        """Compile a list of steps (helper method)"""
        if not steps:
            return ""

        # This is a simplified version - in practice we'd need the full orchestrator
        # For now, just handle basic cases
        compiled_steps = []
        for step in steps:
            if step.type == "query":
                compiled_steps.append(f"EXECUTE '{step.expression}';")
            elif step.type == "return":
                compiled_steps.append(f"RETURN {step.expression};")
            elif step.type == "reject":
                compiled_steps.append(f"RAISE EXCEPTION '{step.error}';")
            # Add other step types as needed

        return "\n".join(compiled_steps)