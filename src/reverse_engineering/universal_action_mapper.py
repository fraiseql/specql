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
        }

    def _get_rust_parser(self) -> object | None:
        """Lazy import to avoid circular dependencies"""
        try:
            from src.reverse_engineering.rust_action_parser import RustActionParser

            return RustActionParser()
        except ImportError:
            logger.warning("Rust parser not available")
            return None

    def _get_python_parser(self) -> object | None:
        """Lazy import to avoid circular dependencies"""
        try:
            from src.reverse_engineering.python_action_parser import PythonActionParser

            return PythonActionParser()
        except ImportError:
            logger.warning("Python parser not available")
            return None

    def _get_java_parser(self) -> object | None:
        """Lazy import to avoid circular dependencies"""
        try:
            from src.reverse_engineering.java_action_parser import JavaActionParser

            return JavaActionParser()
        except ImportError:
            logger.warning("Java parser not available")
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
