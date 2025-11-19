"""
PostgreSQL Function Generator (Team B)
Generates CRUD and action functions from Entity AST
"""

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Entity
from src.generators.app_wrapper_generator import AppWrapperGenerator
from src.generators.core_logic_generator import CoreLogicGenerator


class FunctionGenerator:
    """Generates PostgreSQL functions for CRUD operations and SpecQL actions"""

    def __init__(self, schema_registry, templates_dir: str = "templates/sql"):
        """
        Initialize with schema registry and Jinja2 templates

        Args:
            schema_registry: SchemaRegistry instance for multi-tenant detection
            templates_dir: Path to SQL templates directory
        """
        self.templates_dir = templates_dir
        self.schema_registry = schema_registry

        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )

        # Initialize sub-generators with schema_registry
        self.app_gen = AppWrapperGenerator(templates_dir)
        self.core_gen = CoreLogicGenerator(schema_registry, templates_dir)

    def generate_action_functions(self, entity: Entity) -> str:
        """
        Generate functions for SpecQL actions using App/Core pattern

        Args:
            entity: Parsed Entity AST

        Returns:
            SQL with action functions
        """
        functions = []

        for action in entity.actions:
            # Use App/Core pattern for all actions
            app_wrapper = self.app_gen.generate_app_wrapper(entity, action)
            functions.append(app_wrapper)

            # Core layer - for now, only support CRUD actions
            core_logic = None
            if action.name.startswith("create"):
                core_logic = self.core_gen.generate_core_create_function(entity)
            elif action.name.startswith("update"):
                core_logic = self.core_gen.generate_core_update_function(entity)
            elif action.name.startswith("delete"):
                core_logic = self.core_gen.generate_core_delete_function(entity)
            # TODO: Add support for custom actions in core layer

            if core_logic:
                functions.append(core_logic)

        return "\n\n".join(functions)
