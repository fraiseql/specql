"""
Conditional Compiler - Transform conditional logic to PL/pgSQL control flow
"""

from dataclasses import dataclass
from typing import List

from src.core.ast_models import ActionStep, Entity


@dataclass
class ConditionalCompiler:
    """Compiles conditional logic (if/then/else, switch) to PL/pgSQL"""

    def compile(self, step: ActionStep, entity: Entity) -> str:
        """Compile conditional step"""
        if step.type == "if":
            return self._compile_if(step, entity)
        elif step.type == "switch":
            return self._compile_switch(step, entity)
        return ""

    def _compile_if(self, step: ActionStep, entity: Entity) -> str:
        """Compile if/then/else"""
        condition = step.condition or ""
        then_body = self._compile_steps(step.then_steps or [], entity)
        else_body = self._compile_steps(step.else_steps or [], entity) if step.else_steps else ""

        sql = f"""
    IF ({condition}) THEN
        {then_body}
"""
        if else_body:
            sql += f"""
    ELSE
        {else_body}
"""
        sql += """
    END IF;
"""
        return sql

    def _compile_switch(self, step: ActionStep, entity: Entity) -> str:
        """Compile switch/case"""
        expression = step.expression or ""
        cases = step.cases or {}

        case_clauses = []
        for value, case_steps in cases.items():
            body = self._compile_steps(case_steps, entity)
            case_clauses.append(f"""
        WHEN '{value}' THEN
            {body}
""")

        return f"""
    CASE {expression}
        {"".join(case_clauses)}
    END CASE;
"""

    def _compile_steps(self, steps: List[ActionStep], entity: Entity) -> str:
        """Compile list of steps (recursive)"""
        # For now, return a simple placeholder - will be enhanced when integrated
        if not steps:
            return "-- No steps"

        compiled = []
        for step in steps:
            if step.type == "update":
                # Simple update compilation for testing
                fields_sql = ", ".join(f"{k} = '{v}'" for k, v in (step.fields or {}).items())
                compiled.append(
                    f"UPDATE {entity.schema}.tb_{entity.name.lower()} SET {fields_sql} WHERE pk_{entity.name.lower()} = v_pk;"
                )
            elif step.type == "insert":
                # Simple insert compilation for testing
                fields_sql = ", ".join(f"{k} = '{v}'" for k, v in (step.fields or {}).items())
                compiled.append(
                    f"INSERT INTO {entity.schema}.tb_{step.entity or entity.name}_lightweight ({fields_sql});"
                )
            else:
                compiled.append(f"-- Unknown step type: {step.type}")

        return "\n        ".join(compiled)
