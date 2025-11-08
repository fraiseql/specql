"""
Call Step Compiler

Compiles 'call' steps to PL/pgSQL function calls.

Example SpecQL:
    - call: send_notification(owner_email, "Contact qualified")

Generated PL/pgSQL:
    -- Call: send_notification
    PERFORM app.send_notification(
        p_email := owner_email,
        p_message := 'Contact qualified'
    );
"""

from src.core.ast_models import ActionStep, EntityDefinition


class CallStepCompiler:
    """Compiles call steps to PL/pgSQL function calls"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile call step to PL/pgSQL

        Args:
            step: ActionStep with type='call'
            entity: EntityDefinition for table/schema context
            context: Compilation context (variables, etc.)

        Returns:
            PL/pgSQL code for function call
        """
        if step.type != "call":
            raise ValueError(f"Expected call step, got {step.type}")

        function_name = step.function_name
        if not function_name:
            raise ValueError("Call step must have a function_name")

        # Get arguments
        args_dict = step.arguments or {}

        # Build argument list
        arg_sql = self._build_arguments(args_dict, entity, context)

        return f"""
    -- Call: {function_name}
    PERFORM app.{function_name}({arg_sql});
"""

    def _build_arguments(self, args_dict: dict, entity: EntityDefinition, context: dict) -> str:
        """
        Build argument list for PERFORM call

        Example:
            {"email": "owner_email", "message": "'Contact qualified'"}
            → "p_email := owner_email, p_message := 'Contact qualified'"
        """
        if not args_dict:
            return ""

        arg_parts = []
        for param_name, arg_value in args_dict.items():
            # If it's a quoted string, keep as is
            if isinstance(arg_value, str) and (
                (arg_value.startswith('"') and arg_value.endswith('"'))
                or (arg_value.startswith("'") and arg_value.endswith("'"))
            ):
                arg_parts.append(f"p_{param_name} := {arg_value}")
            else:
                # Assume it's a variable reference or value
                arg_parts.append(f"p_{param_name} := {arg_value}")

        return ", ".join(arg_parts)
