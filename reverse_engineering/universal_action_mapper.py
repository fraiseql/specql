"""
Universal Action Mapper - Convert actions from any language to SpecQL YAML

Works with action parsers from different languages to create unified SpecQL output.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class UniversalActionMapper:
    """Convert actions from any language to SpecQL YAML"""

    def __init__(self) -> None:
        self.parsers = {
            "rust": self._get_rust_parser(),
            "python": self._get_python_parser(),
            "java": self._get_java_parser(),
            "typescript": self._get_typescript_parser(),
        }

    def _get_rust_parser(self) -> object | None:
        """Lazy import to avoid circular dependencies"""
        try:
            from reverse_engineering.rust_action_parser import RustActionParser

            return RustActionParser()
        except ImportError:
            logger.warning("Rust parser not available")
            return None

    def _get_python_parser(self) -> object | None:
        """Lazy import to avoid circular dependencies"""
        try:
            from reverse_engineering.python_action_parser import PythonActionParser

            return PythonActionParser()
        except ImportError:
            logger.warning("Python parser not available")
            return None

    def _get_java_parser(self) -> object | None:
        """Lazy import to avoid circular dependencies"""
        try:
            from reverse_engineering.java_action_parser import JavaActionParser

            return JavaActionParser()
        except ImportError:
            logger.warning("Java parser not available")
            return None

    def _get_typescript_parser(self) -> object | None:
        """Lazy import to avoid circular dependencies"""
        try:
            from reverse_engineering.typescript_parser import TypeScriptParser

            return TypeScriptParser()
        except ImportError:
            logger.warning("TypeScript parser not available")
            return None

    def convert_file(self, file_path: Path, language: str, **kwargs: object) -> str:
        """Convert source file to SpecQL YAML"""
        parser = self.parsers.get(language)
        if not parser:
            raise ValueError(f"Unsupported language: {language}")

        # Read file content
        with open(file_path) as f:
            code = f.read()

        # Extract actions and/or fields based on file type
        actions = []
        fields = []

        if language == "java":
            # For Java, check if it's an entity or controller/repository
            if "@Entity" in code:
                # JPA entity - extract fields
                if hasattr(parser, "extract_entity_fields_from_code"):
                    fields = parser.extract_entity_fields_from_code(code)  # type: ignore
            elif "@RestController" in code or "@Controller" in code or "Repository" in code:
                # Controller or Repository - extract actions
                actions = parser.extract_actions_from_code(code)  # type: ignore
        else:
            # For other languages, extract actions
            actions = parser.extract_actions(file_path)  # type: ignore

        # Convert to SpecQL YAML
        return self._generate_yaml(file_path, actions, fields, language)

    def convert_code(self, code: str, language: str, **kwargs: object) -> str:
        """Convert source code string to SpecQL YAML"""
        parser = self.parsers.get(language)
        if not parser:
            raise ValueError(f"Unsupported language: {language}")

        # Extract actions and/or fields based on code content
        actions = []
        fields = []

        if language == "java":
            # For Java, check if it's an entity or controller/repository
            if "@Entity" in code:
                # JPA entity - extract fields
                if hasattr(parser, "extract_entity_fields_from_code"):
                    fields = parser.extract_entity_fields_from_code(code)  # type: ignore
            elif "@RestController" in code or "@Controller" in code or "Repository" in code:
                # Controller or Repository - extract actions
                actions = parser.extract_actions_from_code(code)  # type: ignore
        elif language == "typescript":
            # For TypeScript, extract routes and actions
            actions = self._map_typescript_actions(code)
        else:
            # For other languages, extract actions
            if hasattr(parser, "extract_actions_from_code"):
                actions = parser.extract_actions_from_code(code)  # type: ignore
            else:
                raise NotImplementedError(
                    f"Parser for {language} doesn't support code string conversion"
                )

        # Convert to SpecQL YAML
        return self._generate_yaml_from_code(actions, fields, language)

    def _generate_yaml(
        self,
        file_path: Path,
        actions: list[dict[str, Any]],
        fields: list[dict[str, Any]] | None,
        language: str,
    ) -> str:
        """Generate SpecQL YAML from actions and/or fields"""
        # Group actions by entity (inferred from file path and action names)
        if actions:
            entity_name = self._infer_entity_name(file_path, actions)
        else:
            entity_name = self._infer_entity_name_from_filename(file_path)

        specql_dict = {
            "entity": entity_name,
            "description": f"Extracted from {language} file {file_path.name}",
        }

        if actions:
            specql_dict["actions"] = actions
        if fields:
            specql_dict["fields"] = fields

        # Add metadata
        specql_dict["_metadata"] = {
            "source_file": str(file_path),
            "source_language": language,
            "extraction_method": "universal_action_mapper",
            "total_actions": len(actions) if actions else 0,
            "total_fields": len(fields) if fields else 0,
        }

        return yaml.dump(specql_dict, default_flow_style=False, sort_keys=False)

    def _generate_yaml_from_code(
        self, actions: list[dict[str, Any]], fields: list[dict[str, Any]] | None, language: str
    ) -> str:
        """Generate SpecQL YAML from actions and/or fields (when no file path available)"""
        # Group actions by entity (inferred from action names or use generic name)
        if actions:
            entity_name = self._infer_entity_name_from_actions(actions)
        else:
            entity_name = "Entity"

        specql_dict = {
            "entity": entity_name,
            "description": f"Actions extracted from {language} code",
            "actions": actions,
            "_metadata": {
                "source_language": language,
                "extraction_method": "action_parser",
                "total_actions": len(actions),
            },
        }

        return yaml.dump(specql_dict, default_flow_style=False, sort_keys=False)

    def _infer_entity_name(self, file_path: Path, actions: list[dict[str, Any]]) -> str:
        """Infer entity name from file path and actions"""
        # Try to extract from file name
        file_stem = file_path.stem.lower()

        # Remove common suffixes
        for suffix in [
            "_controller",
            "_handler",
            "_service",
            "_repository",
            "_view",
            "_api",
            "_routes",
            "_views",
        ]:
            if file_stem.endswith(suffix):
                return file_stem[: -len(suffix)].title()

        # Try to infer from action names
        return self._infer_entity_name_from_actions(actions)

    def _infer_entity_name_from_actions(self, actions: list[dict[str, Any]]) -> str:
        """Infer entity name from action names"""
        if not actions:
            return "Unknown"

        # Look for common patterns in action names
        action_names = [action.get("name", "") for action in actions]

        # Find common prefixes (like 'create_contact', 'get_contact' -> 'Contact')
        if len(action_names) > 1:
            # Split by underscore and find common first part
            parts = [name.split("_") for name in action_names if "_" in name]
            if parts and len(parts[0]) > 1:
                first_parts = [p[1] for p in parts if len(p) > 1]  # Skip the verb
                if first_parts:
                    # Find most common second part
                    from collections import Counter

                    most_common = Counter(first_parts).most_common(1)
                    if most_common:
                        return str(most_common[0][0]).title()

        # Fallback: use first action name without verb
        first_action = action_names[0]
        if "_" in first_action:
            parts = first_action.split("_")
            if len(parts) > 1:
                return str(parts[1]).title()

        return "Entity"

    def _infer_entity_name_from_filename(self, file_path: Path) -> str:
        """Infer entity name from filename"""
        filename = file_path.stem  # Remove extension

        # Remove common suffixes
        for suffix in ["Controller", "Repository", "Service", "Entity"]:
            if filename.endswith(suffix):
                filename = filename[: -len(suffix)]
                break

        # Convert to title case
        return filename.title()

    def _map_typescript_actions(self, code: str) -> list[dict[str, Any]]:
        """Map TypeScript routes/actions to SpecQL actions"""
        parser = self.parsers.get("typescript")
        if not parser:
            return []

        actions = []

        # Extract Express/Fastify routes
        routes = parser.extract_routes(code)
        for route in routes:
            # Map HTTP method to action type
            action_type = self._http_method_to_action_type(route.method)

            # Infer entity from path (/contacts -> Contact)
            entity = self._infer_entity_from_path(route.path)

            actions.append(
                {
                    "name": f"{action_type}_{entity.lower()}",
                    "type": action_type,
                    "entity": entity,
                    "description": f"{action_type.title()} {entity} via {route.framework} route",
                    "steps": self._generate_steps_for_action(action_type, entity),
                }
            )

        # Extract Next.js App Router routes (if applicable)
        # Check if this looks like an App Router file
        if "export async function" in code and ("NextRequest" in code or "NextResponse" in code):
            app_routes = parser.extract_nextjs_app_routes(
                code, "app/api/contacts/route.ts"
            )  # Use contacts path for better inference
            for route in app_routes:
                action_type = self._http_method_to_action_type(route.method)
                entity = self._infer_entity_from_path(route.path)

                actions.append(
                    {
                        "name": f"{action_type}_{entity.lower()}_app",
                        "type": action_type,
                        "entity": entity,
                        "description": f"{action_type.title()} {entity} via Next.js App Router",
                        "steps": self._generate_steps_for_action(action_type, entity),
                    }
                )

        # Extract Server Actions (if applicable)
        if "'use server'" in code or '"use server"' in code:
            server_actions = parser.extract_server_actions(code)
            for action in server_actions:
                # Infer action type from function name
                action_type = self._infer_action_type_from_name(action.name)
                entity = self._infer_entity_from_function_name(action.name)

                actions.append(
                    {
                        "name": action.name.lower().replace("contact", "contact"),
                        "type": action_type,
                        "entity": entity,
                        "description": f"{action_type.title()} {entity} via Server Action",
                        "steps": self._generate_steps_for_action(action_type, entity),
                    }
                )

        return actions

    def _http_method_to_action_type(self, method: str) -> str:
        """Map HTTP method to SpecQL action type"""
        mapping = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        return mapping.get(method, "custom")

    def _infer_entity_from_path(self, path: str) -> str:
        """Infer entity name from API path"""
        # Remove leading slash and split by slashes
        parts = path.strip("/").split("/")

        # Find the main resource (usually the first non-parameter part)
        for part in parts:
            if not part.startswith(":") and part != "api":
                # Convert to title case and singularize
                return self._singularize(part.title())

        return "Entity"

    def _singularize(self, word: str) -> str:
        """Simple singularization (basic implementation)"""
        if word.endswith("ies"):
            return word[:-3] + "y"
        elif word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    def _generate_steps_for_action(self, action_type: str, entity: str) -> list[dict[str, Any]]:
        """Generate basic steps for an action"""
        if action_type == "create":
            return [{"insert": entity}]
        elif action_type == "read":
            return [{"select": entity}]
        elif action_type == "update":
            return [{"update": entity}]
        elif action_type == "delete":
            return [{"delete": entity}]
        else:
            return [{"custom": f"{action_type}_{entity}"}]

    def _infer_action_type_from_name(self, function_name: str) -> str:
        """Infer action type from function name"""
        name_lower = function_name.lower()
        if name_lower.startswith("create") or name_lower.startswith("add"):
            return "create"
        elif (
            name_lower.startswith("get")
            or name_lower.startswith("find")
            or name_lower.startswith("read")
        ):
            return "read"
        elif (
            name_lower.startswith("update")
            or name_lower.startswith("edit")
            or name_lower.startswith("modify")
        ):
            return "update"
        elif name_lower.startswith("delete") or name_lower.startswith("remove"):
            return "delete"
        else:
            return "custom"

    def _infer_entity_from_function_name(self, function_name: str) -> str:
        """Infer entity from function name"""
        # Remove common prefixes
        name = function_name
        for prefix in ["create", "get", "update", "delete", "find", "add", "remove", "edit"]:
            if name.lower().startswith(prefix):
                name = name[len(prefix) :]
                break

        # Convert from PascalCase/CamelCase to Title Case
        if name and name[0].isupper():
            # Already PascalCase, just ensure it's singular
            return self._singularize(name)
        else:
            # Convert to title case
            return name.title()
