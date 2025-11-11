"""
App Wrapper Generator (Team C)
Generates app.* API wrapper functions
"""

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Action, Entity
from src.generators.fraiseql.mutation_annotator import MutationAnnotator


class AppWrapperGenerator:
    """Generates app.* wrapper functions for GraphQL/REST API"""

    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_app_wrapper(self, entity: Entity, action: Action) -> str:
        """
        Generate app wrapper function for action

        Args:
            entity: Entity containing the action
            action: Action to generate wrapper for

        Returns:
            SQL for app wrapper function with FraiseQL comments
        """
        action_type = self._detect_action_type(action.name)
        composite_type_name = f"app.type_{action.name}_input"
        graphql_name = self._to_camel_case(action.name)
        input_type_name = self._to_pascal_case(action.name) + "Input"

        # For delete actions, we might not need a composite type
        needs_composite_type = action_type != "delete"

        context = {
            "app_function_name": action.name,
            "composite_type_name": composite_type_name,
            "core_schema": entity.schema,
            "core_function_name": action.name,
            "graphql_name": graphql_name,
            "input_type_name": input_type_name,
            "action_type": action_type,
            "needs_composite_type": needs_composite_type,
        }

        template = self.env.get_template("app_wrapper.sql.j2")
        function_sql = template.render(**context)

        # Add FraiseQL annotation - IN SAME FILE as function
        annotator = MutationAnnotator("app", entity.name)
        annotation_sql = annotator.generate_app_mutation_annotation(action)

        return f"{function_sql}\n\n{annotation_sql}"

    def _detect_action_type(self, action_name: str) -> str:
        """
        Detect action type from action name

        Args:
            action_name: Name of the action

        Returns:
            Action type: 'create', 'update', 'delete', or 'custom'
        """
        if action_name.startswith("create_"):
            return "create"
        elif action_name.startswith("update_"):
            return "update"
        elif action_name.startswith("delete_"):
            return "delete"
        else:
            return "custom"

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split("_")
        return components[0] + "".join(x.capitalize() for x in components[1:])

    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase"""
        components = snake_str.split("_")
        return "".join(x.capitalize() for x in components)
