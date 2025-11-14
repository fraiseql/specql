"""
Spring Boot to SpecQL Converter

Converts Spring Boot components to SpecQL actions and entities.
Maps Spring MVC endpoints to SpecQL actions.
"""

from typing import List, Dict, Any, Optional
from src.reverse_engineering.java.spring_visitor import SpringComponent, SpringMethod
from src.core.ast_models import Action, ActionStep, ActionImpact, EntityImpact


class SpringToSpecQLConverter:
    """Convert Spring Boot components to SpecQL"""

    def __init__(self):
        self.http_method_mapping = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "DELETE": "delete",
            "PATCH": "update",
        }

    def convert_component(self, component: SpringComponent) -> List[Action]:
        """
        Convert Spring component to SpecQL actions

        Args:
            component: Parsed Spring component

        Returns:
            List of SpecQL actions
        """
        actions = []

        if component.component_type in ("controller", "rest_controller"):
            # Convert controller methods to actions
            for method in component.methods:
                action = self._convert_controller_method(component, method)
                if action:
                    actions.append(action)

        elif component.component_type == "service":
            # Convert service methods to actions
            for method in component.methods:
                action = self._convert_service_method(component, method)
                if action:
                    actions.append(action)

        elif component.component_type == "repository":
            # Convert repository methods to actions
            for method in component.methods:
                action = self._convert_repository_method(component, method)
                if action:
                    actions.append(action)

        elif component.component_type == "configuration":
            # Convert configuration @Bean methods to actions
            for method in component.methods:
                action = self._convert_configuration_method(component, method)
                if action:
                    actions.append(action)

        return actions

    def _convert_controller_method(
        self, component: SpringComponent, method: SpringMethod
    ) -> Optional[Action]:
        """Convert controller method to SpecQL action"""
        if not method.http_method:
            return None

        # Generate action name
        action_name = self._generate_action_name(method, component.base_path)

        # Map HTTP method to SpecQL action type
        action_type = self.http_method_mapping.get(method.http_method, "custom")

        # Create action steps based on method signature
        steps = self._create_action_steps(method, action_type)

        # Create action
        action = Action(
            name=action_name,
            steps=steps,
            impact=self._create_action_impact(method, action_type),
        )

        return action

    def _convert_service_method(
        self, component: SpringComponent, method: SpringMethod
    ) -> Optional[Action]:
        """Convert service method to SpecQL action"""
        # Service methods become internal actions
        method_name = method.name.lower() if method.name else "unknown"
        action_name = f"{component.class_name.lower()}_{method_name}"

        # Create action steps
        steps = self._create_service_action_steps(method)

        # Create a minimal EntityImpact for internal actions
        internal_impact = EntityImpact(entity="internal", operation="INTERNAL")

        action = Action(
            name=action_name, steps=steps, impact=ActionImpact(primary=internal_impact)
        )

        return action

    def _generate_action_name(
        self, method: SpringMethod, base_path: Optional[str]
    ) -> str:
        """Generate SpecQL action name from HTTP method and path"""
        # Start with base path
        full_path = base_path or ""

        # Append method path if present
        if method.path:
            method_path = method.path.strip("/")
            if method_path:
                if full_path:
                    full_path = f"{full_path}/{method_path}"
                else:
                    full_path = method_path

        # Clean path for action name
        path = full_path.strip("/")
        if not path:
            # Root endpoint
            http_method = (
                method.http_method.lower() if method.http_method else "unknown"
            )
            return f"{http_method}_root"

        # Convert path to snake_case action name, keep {param} as is
        path_parts = path.replace("/", "_")
        http_method = method.http_method.lower() if method.http_method else "unknown"
        action_name = f"{http_method}_{path_parts}"

        return action_name

    def _create_action_steps(
        self, method: SpringMethod, action_type: str
    ) -> List[ActionStep]:
        """Create action steps for controller method"""
        steps = []

        # Primary step based on HTTP method
        if action_type == "read":
            step = ActionStep(
                type="select",
                entity=self._infer_table_from_path(method.path),
                where_clause=str(self._extract_path_parameters(method.path))
                if self._extract_path_parameters(method.path)
                else None,
            )
        elif action_type == "create":
            step = ActionStep(
                type="insert",
                entity=self._infer_table_from_path(method.path),
                fields=self._extract_request_body_parameters(method),
            )
        elif action_type == "update":
            step = ActionStep(
                type="update",
                entity=self._infer_table_from_path(method.path),
                fields=self._extract_request_body_parameters(method),
                where_clause=str(self._extract_path_parameters(method.path))
                if self._extract_path_parameters(method.path)
                else None,
            )
        elif action_type == "delete":
            step = ActionStep(
                type="delete",
                entity=self._infer_table_from_path(method.path),
                where_clause=str(self._extract_path_parameters(method.path))
                if self._extract_path_parameters(method.path)
                else None,
            )
        else:
            # Custom action
            step = ActionStep(
                type="call",
                function_name=f"{method.name}",
                arguments=self._extract_method_parameters(method),
            )

        steps.append(step)
        return steps

    def _create_service_action_steps(self, method: SpringMethod) -> List[ActionStep]:
        """Create action steps for service method"""
        # Service methods typically call stored procedures or perform business logic
        step = ActionStep(
            type="call",
            function_name=f"{method.name}",
            arguments=self._extract_method_parameters(method),
        )

        return [step]

    def _convert_repository_method(
        self, component: SpringComponent, method: SpringMethod
    ) -> Optional[Action]:
        """Convert repository method to SpecQL action"""
        method_name = method.name.lower() if method.name else "unknown"
        action_name = f"{component.class_name.lower()}_{method_name}"

        # Determine action type based on method name
        action_type = self._get_repository_action_type(method.name)

        # Create action steps
        steps = self._create_repository_action_steps(method, action_type, component)

        action = Action(
            name=action_name,
            steps=steps,
            impact=ActionImpact(
                primary=EntityImpact(
                    entity=self._infer_entity_from_repository(component),
                    operation=action_type.upper(),
                )
            ),
        )

        return action

    def _get_repository_action_type(self, method_name: str) -> str:
        """Determine action type from repository method name"""
        if method_name.startswith("find") or method_name.startswith("get"):
            return "read"
        elif method_name.startswith("save"):
            return "create"
        elif method_name.startswith("delete"):
            return "delete"
        elif method_name.startswith("exists"):
            return "read"
        elif method_name.startswith("count"):
            return "read"
        else:
            return "custom"

    def _create_repository_action_steps(
        self, method: SpringMethod, action_type: str, component: SpringComponent
    ) -> List[ActionStep]:
        """Create action steps for repository method"""
        entity_name = self._infer_entity_from_repository(component)

        if action_type == "read":
            step = ActionStep(
                type="select",
                entity=entity_name,
                where_clause=self._extract_query_conditions(method.name),
            )
        elif action_type == "create":
            step = ActionStep(
                type="insert",
                entity=entity_name,
                fields=self._extract_method_parameters(method),
            )
        elif action_type == "delete":
            step = ActionStep(
                type="delete",
                entity=entity_name,
                where_clause=self._extract_query_conditions(method.name),
            )
        else:
            step = ActionStep(
                type="call",
                function_name=method.name,
                arguments=self._extract_method_parameters(method),
            )

        return [step]

    def _infer_entity_from_repository(self, component: SpringComponent) -> str:
        """Infer entity name from repository class name"""
        # Repository classes typically end with 'Repository'
        repo_name = component.class_name
        if repo_name.endswith("Repository"):
            entity_name = repo_name[:-10]  # Remove 'Repository'
        else:
            entity_name = repo_name

        return entity_name.lower()

    def _infer_entity_from_method(self, method: SpringMethod) -> str:
        """Infer entity from method return type or parameters"""
        # Try to extract from return type
        return_type = method.return_type
        if return_type:
            if "List<" in return_type:
                # List<Entity> -> Entity
                start = return_type.find("<") + 1
                end = return_type.find(">")
                if start > 0 and end > start:
                    entity = return_type[start:end]
                    return entity.lower()
            elif return_type not in ["void", "boolean", "int", "long"]:
                # Direct entity return type
                return return_type.lower()

        # Try to extract from method name (findByField -> entity)
        # For repository methods, we can't easily infer the entity without more context
        # This would need to be passed from the component level

        return "unknown"

    def _extract_query_conditions(self, method_name: str) -> Optional[str]:
        """Extract query conditions from method name like findByName"""
        if "By" in method_name:
            parts = method_name.split("By", 1)
            if len(parts) > 1:
                condition_part = parts[1]
                # Simple conversion: Name -> name = ?
                return f"{condition_part.lower()} = ?"
        return None

    def _convert_configuration_method(
        self, component: SpringComponent, method: SpringMethod
    ) -> Optional[Action]:
        """Convert @Bean method to SpecQL action"""
        action_name = f"{component.class_name.lower()}_{method.name}"

        # @Bean methods create configuration objects
        steps = [
            ActionStep(
                type="call",
                function_name=f"{method.name}",
                arguments=self._extract_method_parameters(method),
            )
        ]

        # Configuration methods are internal
        internal_impact = EntityImpact(entity="configuration", operation="CONFIG")

        action = Action(
            name=action_name, steps=steps, impact=ActionImpact(primary=internal_impact)
        )

        return action

    def _create_action_impact(
        self, method: SpringMethod, action_type: str
    ) -> ActionImpact:
        """Create action impact metadata"""
        entity_name = (
            self._infer_table_from_path(method.path) if method.path else "unknown"
        )
        operation = action_type.upper()

        primary_impact = EntityImpact(entity=entity_name, operation=operation)

        return ActionImpact(primary=primary_impact)

    def _infer_table_from_path(self, path: Optional[str]) -> str:
        """Infer table name from URL path"""
        if not path:
            return "unknown"

        # Extract resource name from path
        # e.g., /api/users/{id} -> users
        path_parts = path.strip("/").split("/")
        for part in reversed(path_parts):
            if not part.startswith("{") and part != "api":
                # Keep plural form for table names
                return part.lower()

        return "unknown"

        # Extract resource name from path
        # e.g., /api/users/{id} -> users
        path_parts = path.strip("/").split("/")
        for part in reversed(path_parts):
            if not part.startswith("{") and part != "api":
                return self._plural_to_singular(part)

        return "unknown"

    def _plural_to_singular(self, word: str) -> str:
        """Convert plural to singular (basic implementation)"""
        if word.endswith("ies"):
            return word[:-3] + "y"
        elif word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    def _extract_path_parameters(self, path: Optional[str]) -> Optional[Dict[str, Any]]:
        """Extract path parameters from URL path"""
        if not path:
            return None

        # Find {param} patterns
        import re

        param_pattern = r"\{([^}]+)\}"
        params = re.findall(param_pattern, path)

        if not params:
            return None

        # Create condition for path parameters
        conditions = {}
        for param in params:
            conditions[param] = f"${param}"

        return conditions

    def _extract_request_body_parameters(
        self, method: SpringMethod
    ) -> Optional[Dict[str, Any]]:
        """Extract parameters that would come from request body"""
        # Look for @RequestBody annotated parameters
        body_params = {}
        for param in method.parameters:
            if "RequestBody" in param.get("annotations", []):
                body_params[param["name"]] = f"${param['name']}"

        return body_params if body_params else None

    def _extract_method_parameters(self, method: SpringMethod) -> Dict[str, Any]:
        """Extract all method parameters"""
        params = {}
        for param in method.parameters:
            params[param["name"]] = f"${param['name']}"
        return params
