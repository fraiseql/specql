"""
Mutation Annotator (Team D)
Generates FraiseQL annotations for PL/pgSQL mutation functions

Purpose:
- Tell FraiseQL how to expose mutation functions as GraphQL mutations
- Include impact metadata for frontend cache invalidation
- Map PostgreSQL function parameters to GraphQL input types
"""

from typing import Any

from src.core.ast_models import Action, ActionImpact


class MutationAnnotator:
    """Generate FraiseQL annotations for mutation functions"""

    def __init__(self, schema: str, entity_name: str):
        self.schema = schema
        self.entity_name = entity_name

    def generate_mutation_annotation(self, action: Action) -> str:
        """
        Generate descriptive comment for core layer functions (NO @fraiseql:mutation!)

        Core layer functions are internal business logic and should NOT be exposed
        to GraphQL. Only app.* functions get @fraiseql:mutation annotations.

        Args:
            action: The parsed action definition

        Returns:
            SQL COMMENT statement with descriptive comment (no FraiseQL annotation)
        """
        function_name = f"{self.schema}.{action.name}"

        # Get action description with core layer context
        description = self._get_core_action_description(action)

        comment_lines = [
            f"COMMENT ON FUNCTION {function_name} IS",
            f"'{description}';",
        ]

        return "\n".join(comment_lines)

    def generate_app_mutation_annotation(self, action: Action) -> str:
        """
        Generate @fraiseql:mutation annotation for app.* wrapper functions

        Uses YAML format with description for app layer functions.

        Args:
            action: The parsed action definition

        Returns:
            SQL COMMENT statement with descriptive @fraiseql:mutation annotation
        """
        function_name = f"app.{action.name}"
        graphql_name = self._to_camel_case(action.name)
        pascal_name = graphql_name[0].upper() + graphql_name[1:] if graphql_name else ""

        # Get action description
        description = self._get_action_description(action)

        annotation_lines = [
            f"COMMENT ON FUNCTION {function_name} IS",
            f"'{description}",
            "",
            "@fraiseql:mutation",
            f"name: {graphql_name}",
            f"input_type: app.type_{action.name}_input",
            f"success_type: {pascal_name}Success",
            f"failure_type: {pascal_name}Error';",
        ]

        return "\n".join(annotation_lines)

    def _get_action_description(self, action: Action) -> str:
        """
        Get human-readable description for app layer action

        Args:
            action: The action to describe

        Returns:
            Description string for app layer functions
        """
        action_type = self._detect_action_type(action.name)
        entity_name = self.entity_name

        if action_type == "create":
            return f"Creates a new {entity_name} record.\nValidates input and delegates to core business logic."
        elif action_type == "update":
            return f"Updates an existing {entity_name} record.\nValidates input and delegates to core business logic."
        elif action_type == "delete":
            return f"Deletes an existing {entity_name} record.\nValidates permissions and delegates to core business logic."
        else:
            return f"Performs {action.name.replace('_', ' ')} operation on {entity_name}.\nValidates input and delegates to core business logic."

    def _get_core_action_description(self, action: Action) -> str:
        """
        Get descriptive comment for core layer functions (NO FraiseQL annotations!)

        Core layer functions contain internal business logic and are called by
        app layer functions. They should have descriptive comments but no
        @fraiseql:mutation annotations.

        Args:
            action: The action to describe

        Returns:
            Descriptive comment for core layer functions
        """
        action_type = self._detect_action_type(action.name)
        entity_name = self.entity_name

        # Build validation list (simplified for now)
        validations = ["Input validation", "Permission checks"]

        # Determine operation type
        operation = self._get_operation_type(action_type)

        description_lines = [
            f"Core business logic for {action.name.replace('_', ' ')}.",
            "",
            "Validation:",
        ]

        # Add validation items
        for validation in validations:
            description_lines.append(f"- {validation}")

        description_lines.extend(
            [
                "",
                "Operations:",
                "- Trinity FK resolution (UUID → INTEGER)",
                f"- {operation} operation on {self.schema}.tb_{entity_name.lower()}",
                "- Audit logging via app.log_and_return_mutation",
                "",
                f"Called by: app.{action.name} (GraphQL mutation)",
                "Returns: app.mutation_result (success/failure status)",
            ]
        )

        return "\n".join(description_lines)

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

    def _get_operation_type(self, action_type: str) -> str:
        """
        Get SQL operation type from action type

        Args:
            action_type: The detected action type

        Returns:
            SQL operation: 'INSERT', 'UPDATE', 'DELETE', or 'OPERATION'
        """
        if action_type == "create":
            return "INSERT"
        elif action_type == "update":
            return "UPDATE"
        elif action_type == "delete":
            return "DELETE"
        else:
            return "OPERATION"

    def _build_metadata_mapping(self, impact: ActionImpact | None = None) -> str:
        """
        Build metadata mapping JSON for cache invalidation

        Args:
            impact: Action impact metadata

        Returns:
            JSON string with metadata mapping
        """
        if not impact:
            return "{}"

        # For now, include basic impact metadata
        # In a full implementation, this would include detailed cache invalidation rules
        mapping: dict[str, Any] = {"_meta": "MutationImpactMetadata"}

        # Add primary entity impact
        if impact.primary:
            mapping["primary_impact"] = {
                "entity": impact.primary.entity,
                "operation": impact.primary.operation,
                "fields": impact.primary.fields,
            }

        # Add side effects if any
        if impact.side_effects:
            mapping["side_effects"] = [
                {"entity": side.entity, "operation": side.operation, "fields": side.fields}
                for side in impact.side_effects
            ]

        # Convert to JSON-like string (Python dict representation)
        return str(mapping).replace("'", '"')

    def _to_camel_case(self, snake_str: str) -> str:
        """
        Convert snake_case to camelCase

        Args:
            snake_str: String in snake_case format

        Returns:
            String in camelCase format
        """
        components = snake_str.split("_")
        return components[0] + "".join(x.capitalize() for x in components[1:])
