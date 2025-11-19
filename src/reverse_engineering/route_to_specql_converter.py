"""
Convert extracted routes to SpecQL YAML

Maps HTTP routes to SpecQL actions
"""

from dataclasses import dataclass

import yaml


@dataclass
class SpecQLAction:
    """Represents a SpecQL action"""

    name: str
    steps: list[dict]


class RouteToSpecQLConverter:
    """Convert HTTP routes to SpecQL actions"""

    def convert_route(
        self, method: str, path: str, handler_name: str | None = None
    ) -> SpecQLAction:
        """
        Convert HTTP route to SpecQL action

        Rules:
        - POST /contacts -> create_contact (insert)
        - GET /contacts/:id -> get_contact (validate + return)
        - PUT /contacts/:id -> update_contact (validate + update)
        - DELETE /contacts/:id -> delete_contact (validate + soft delete)

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: Route path (/contacts/:id)
            handler_name: Optional handler function name

        Returns:
            SpecQLAction with generated name and steps
        """
        # Generate action name from path and method
        action_name = self._generate_action_name(method, path)

        # Generate steps based on method
        steps = self._generate_steps(method, path)

        return SpecQLAction(name=action_name, steps=steps)

    def _generate_action_name(self, method: str, path: str) -> str:
        """
        Generate action name from HTTP method and path

        Examples:
        - POST /contacts -> create_contact
        - GET /contacts/:id -> get_contact
        - PUT /contacts/:id -> update_contact
        - DELETE /contacts/:id -> delete_contact
        """
        # Extract entity from path
        entity = self._extract_entity(path).lower()

        # Map method to action prefix
        method_map = {
            "POST": "create",
            "GET": "get",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }

        prefix = method_map.get(method, "do")

        return f"{prefix}_{entity}"

    def _generate_steps(self, method: str, path: str) -> list[dict]:
        """
        Generate action steps based on HTTP method

        POST: validate required fields + insert
        GET: validate ID exists
        PUT: validate ID + update
        DELETE: validate ID + soft delete
        """
        has_id = ":id" in path or "{id}" in path

        steps = []

        if method == "POST":
            # Create: validate required fields + insert
            steps = [
                {"validate": "id IS NOT NULL", "error": "missing_id"},
                {"insert": self._extract_entity(path)},
            ]
        elif method == "GET":
            # Read: validate ID exists
            if has_id:
                steps = [{"validate": "id IS NOT NULL", "error": "missing_id"}]
        elif method in ["PUT", "PATCH"]:
            # Update: validate ID + update
            steps = [
                {"validate": "id IS NOT NULL", "error": "missing_id"},
                {"update": self._extract_entity(path), "fields": {}},
            ]
        elif method == "DELETE":
            # Delete: validate ID + soft delete
            steps = [
                {"validate": "id IS NOT NULL", "error": "missing_id"},
                {"update": self._extract_entity(path), "fields": {"deleted_at": "NOW()"}},
            ]

        return steps

    def _extract_entity(self, path: str) -> str:
        """
        Extract entity name from path

        /contacts -> Contact
        /api/users/:id -> User
        /categories/:id -> Category
        """
        parts = [p for p in path.split("/") if p and ":" not in p and p != "api"]

        if not parts:
            return "Entity"

        # Get last part, remove plural, capitalize
        entity = parts[-1]

        # Handle common plural forms
        if entity.endswith("ies"):
            entity = entity[:-3] + "y"  # categories -> category
        elif entity.endswith("s"):
            entity = entity[:-1]  # users -> user, contacts -> contact

        return entity.capitalize()

    def to_yaml(self, actions: list[SpecQLAction]) -> str:
        """Convert actions to YAML format"""
        data = {"actions": [{"name": action.name, "steps": action.steps} for action in actions]}

        return yaml.dump(data, default_flow_style=False, sort_keys=False)
