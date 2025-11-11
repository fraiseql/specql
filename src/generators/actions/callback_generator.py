"""Callback Function Generator

Generates PL/pgSQL callback functions for call_service success/failure handling.

Example generated function:
    CREATE FUNCTION crm.order_stripe_create_charge_success(
        _job_run_id UUID,
        _output_data JSONB
    ) RETURNS void AS $$
    DECLARE
        _job RECORD;
    BEGIN
        SELECT * INTO _job
        FROM jobs.tb_job_run
        WHERE id = _job_run_id;

        -- Execute callback steps here
        UPDATE crm.tb_order
        SET payment_status = 'paid'
        WHERE pk_order = _job.entity_pk;
    END;
    $$ LANGUAGE plpgsql;
"""

from typing import List

from src.core.ast_models import ActionStep
from src.generators.actions.action_context import ActionContext


class CallbackGenerator:
    """Generates callback functions for call_service steps"""

    def __init__(self, step: ActionStep, context: ActionContext):
        self.step = step
        self.context = context

    def generate_success_callback(self) -> str:
        """Generate on_success callback function"""
        if not self.step.on_success:
            return ""

        callback_name = self._callback_function_name("success")
        steps_sql = self._compile_callback_steps(self.step.on_success)

        return f"""
CREATE FUNCTION {callback_name}(
    _job_run_id UUID,
    _output_data JSONB
) RETURNS void AS $$
DECLARE
    _job RECORD;
BEGIN
    SELECT * INTO _job
    FROM jobs.tb_job_run
    WHERE id = _job_run_id;

    {steps_sql}
END;
$$ LANGUAGE plpgsql;
"""

    def generate_failure_callback(self) -> str:
        """Generate on_failure callback function"""
        if not self.step.on_failure:
            return ""

        callback_name = self._callback_function_name("failure")
        steps_sql = self._compile_callback_steps(self.step.on_failure)

        return f"""
CREATE FUNCTION {callback_name}(
    _job_run_id UUID,
    _error_message TEXT
) RETURNS void AS $$
DECLARE
    _job RECORD;
BEGIN
    SELECT * INTO _job
    FROM jobs.tb_job_run
    WHERE id = _job_run_id;

    {steps_sql}
END;
$$ LANGUAGE plpgsql;
"""

    def _callback_function_name(self, callback_type: str) -> str:
        """Generate callback function name"""
        return f"{self.context.entity_schema}.{self.context.entity_name.lower()}_{self.step.service}_{self.step.operation}_{callback_type}"

    def _compile_callback_steps(self, steps: List[ActionStep]) -> str:
        """Compile callback steps to PL/pgSQL"""
        if not steps:
            return "-- No callback steps"

        compiled_steps = []

        for i, step in enumerate(steps):
            compiled_step = self._compile_single_callback_step(step)
            if compiled_step:
                compiled_steps.append(f"-- Step {i + 1}: {step.type}")
                compiled_steps.append(compiled_step)

        return "\n\n".join(compiled_steps)

    def _compile_single_callback_step(self, step: ActionStep) -> str:
        """Compile a single callback step"""
        if step.type == "update":
            return self._compile_update_step(step)
        elif step.type == "insert":
            return self._compile_insert_step(step)
        elif step.type == "delete":
            return self._compile_delete_step(step)
        else:
            # For unsupported step types, raise error
            raise ValueError(f"Unsupported callback step type: {step.type}")

    def _compile_update_step(self, step: ActionStep) -> str:
        """Compile update step for callback"""
        entity_name = step.entity or self.context.entity_name
        table_name = f"{self.context.entity_schema}.tb_{entity_name.lower()}"

        # Build SET clause
        set_parts = []
        if step.fields:
            for field, value in step.fields.items():
                if isinstance(value, str) and value.startswith("$"):
                    # Handle variable references
                    set_parts.append(f"{field} = {self._resolve_variable(value)}")
                else:
                    set_parts.append(f"{field} = '{value}'")

        set_clause = ", ".join(set_parts)

        # Build WHERE clause
        where_clause = self._compile_where_clause(step.where_clause)

        return f"""
UPDATE {table_name}
SET {set_clause}
WHERE {where_clause};
"""

    def _compile_insert_step(self, step: ActionStep) -> str:
        """Compile insert step for callback"""
        # Simplified implementation - would need full insert compiler
        return "-- TODO: Implement insert step in callback"

    def _compile_delete_step(self, step: ActionStep) -> str:
        """Compile delete step for callback"""
        # Simplified implementation - would need full delete compiler
        return "-- TODO: Implement delete step in callback"

    def _compile_where_clause(self, where_clause: str | None) -> str:
        """Compile WHERE clause with variable resolution"""
        if not where_clause:
            # Default to entity primary key = _job.entity_pk
            return f"pk_{self.context.entity_name.lower()} = _job.entity_pk"

        # Handle $job.entity_pk references
        if "$job.entity_pk" in where_clause:
            return where_clause.replace("$job.entity_pk", "_job.entity_pk")

        return where_clause

    def _resolve_variable(self, var_ref: str) -> str:
        """Resolve variable references in callbacks"""
        if var_ref == "$job.entity_pk":
            return "_job.entity_pk"
        elif var_ref == "$job.output_data":
            return "_output_data"
        else:
            # For other variables, return as-is for now
            return var_ref
