"""
App Wrapper Generator (Action Compilation)
Generates app.* API wrapper functions
"""

import importlib.resources as resources

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from core.ast_models import Action, Entity
from generators.fraiseql.mutation_annotator import MutationAnnotator


class AppWrapperGenerator:
    """Generates app.* wrapper functions for GraphQL/REST API"""

    def __init__(self, templates_dir: str = "templates/sql"):
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def _load_template(self, template_name: str):
        """Load template with fallback to package resources"""
        try:
            return self.env.get_template(template_name)
        except TemplateNotFound:
            # Try to load from package resources
            try:
                template_files = resources.files("templates.sql")
                template_path = template_files / template_name
                from jinja2 import Template

                return Template(template_path.read_text())
            except Exception:
                raise TemplateNotFound(
                    f"Template '{template_name}' not found in filesystem or package resources"
                )

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

        # All actions need composite types for consistent JSONB → Typed conversion
        needs_composite_type = True

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

        template = self._load_template("app_wrapper.sql.j2")
        function_sql = template.render(**context)

        # Add FraiseQL annotation (Team D) - IN SAME FILE as function
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

    def _generate_action_description(self, action: Action) -> str:
        """
        Generate human-readable description from action steps

        Args:
            action: Action with steps to analyze

        Returns:
            Description string based on action steps
        """
        if not action.steps:
            # Fallback to basic description
            action_type = self._detect_action_type(action.name)
            if action_type == "create":
                return "Creates a new record"
            elif action_type == "update":
                return "Updates an existing record"
            elif action_type == "delete":
                return "Deletes an existing record"
            else:
                return f"Performs {action.name.replace('_', ' ')} operation"

        # Analyze steps to generate description
        operations = []
        validations = []

        for step in action.steps:
            if step.type == "validate" and step.expression is not None:
                validations.append(step.expression)
            elif step.type == "insert":
                operations.append(f"creates new {step.entity}")
            elif step.type == "update":
                operations.append(f"updates {step.entity}")
            elif step.type == "delete":
                operations.append(f"deletes {step.entity}")
            elif step.type == "notify":
                operations.append("sends notification")

        # Build smart description based on action name and operations
        action_name_words = action.name.replace("_", " ").split()

        if operations and action_name_words:
            # Use action name to create a more meaningful description
            verb = action_name_words[0]
            noun = " ".join(action_name_words[1:]) if len(action_name_words) > 1 else "record"

            # Handle verb conjugation
            if verb == "qualify":
                return f"Qualifies a {noun}"
            elif verb in ["create", "update", "delete"]:
                return f"{verb.capitalize()}s a {noun}"

        # Build description from operations
        description_parts = []

        if operations:
            description_parts.append(f"{' and '.join(operations)}")

        if validations:
            description_parts.append("with validation")

        return ". ".join(description_parts).capitalize()
