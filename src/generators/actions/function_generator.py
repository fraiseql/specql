"""
Function Generator for Action Compiler

Generates complete PL/pgSQL function signatures, declarations, and scaffolding.
"""

from src.core.ast_models import ActionDefinition, EntityDefinition
from src.generators.actions.action_context import ActionContext
from src.generators.actions.function_scaffolding import FunctionScaffoldingGenerator


class FunctionGenerator:
    """Generates PL/pgSQL function components for actions"""

    def __init__(self):
        """Initialize with scaffolding generator"""
        self.scaffolding_gen = FunctionScaffoldingGenerator()

    def generate_signature(self, context: ActionContext) -> str:
        """
        Generate function signature from action context

        Args:
            context: ActionContext with function details

        Returns:
            Function signature string
        """
        # Create minimal action and entity for scaffolding
        action = ActionDefinition(name=context.function_name.split(".")[-1], steps=[])
        entity = EntityDefinition(
            name=context.entity_name,
            schema=context.entity_schema,
            fields={},  # Will be filled as needed
        )

        scaffolding = self.scaffolding_gen.generate(action, entity)
        sig = scaffolding.signature

        # Build parameter list
        params = []
        for param in sig.parameters:
            param_def = f"{param['name']} {param['type']}"
            if "default" in param:
                param_def += f" DEFAULT {param['default']}"
            params.append(param_def)

        params_str = ", ".join(params)

        return f"CREATE OR REPLACE FUNCTION {sig.function_name}({params_str}) RETURNS {sig.returns}"

    def generate_declare_block(self, context: ActionContext) -> str:
        """
        Generate DECLARE block with proper variable types

        Args:
            context: ActionContext with function details

        Returns:
            DECLARE block content
        """
        # Create minimal action and entity for scaffolding
        action = ActionDefinition(name=context.function_name.split(".")[-1], steps=[])
        entity = EntityDefinition(
            name=context.entity_name,
            schema=context.entity_schema,
            fields={},  # Will be filled as needed
        )

        scaffolding = self.scaffolding_gen.generate(action, entity)

        # Build variable declarations
        vars_str = "\n    ".join(scaffolding.variables)

        # Add impact metadata variable if needed
        if context.has_impact_metadata:
            vars_str += (
                "\n    v_meta mutation_metadata.mutation_impact_metadata;  -- Impact metadata"
            )

        return f"DECLARE\n    {vars_str}"

    def generate_trinity_resolution(self, context: ActionContext) -> str:
        """
        Generate Trinity resolution code

        Args:
            context: ActionContext with entity details

        Returns:
            Trinity resolution assignment
        """
        entity_lower = context.entity_name.lower()
        schema = context.entity_schema

        return f"v_pk := {schema}.{entity_lower}_pk(p_{entity_lower}_id);"
