"""Compiler for call_function steps"""


from src.core.ast_models import ActionStep, EntityDefinition

from src.generators.actions.step_compilers.base import StepCompiler


class CallFunctionStepCompiler(StepCompiler):
    """Compiles call_function steps to PL/pgSQL function calls"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Generate function call statement

        Returns:
            PL/pgSQL function call statement
        """
        function_name = step.call_function_name
        arguments = step.call_function_arguments or {}
        return_var = step.call_function_return_variable

        # Build argument list
        arg_list = []
        for arg_name, arg_value in arguments.items():
            if isinstance(arg_value, str) and arg_value.startswith('$'):
                # Parameter reference
                arg_list.append(arg_value[1:])  # Remove $ prefix
            else:
                # Literal value
                if isinstance(arg_value, str):
                    arg_list.append(f"'{arg_value}'")
                else:
                    arg_list.append(str(arg_value))

        args_str = ", ".join(arg_list) if arg_list else ""

        # Generate function call
        if return_var:
            return f"SELECT {function_name}({args_str}) INTO {return_var};"
        else:
            return f"PERFORM {function_name}({args_str});"