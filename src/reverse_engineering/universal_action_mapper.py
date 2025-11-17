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
            # TODO: Import Java parser when Engineer B completes it
            # from src.reverse_engineering.java_action_parser import JavaActionParser
            # return JavaActionParser()
            logger.warning("Java parser not yet implemented by Engineer B")
            return None
        except ImportError:
            logger.warning("Java parser not available")
            return None

    def convert_file(self, file_path: Path, language: str, **kwargs: object) -> str:
        """Convert source file to SpecQL YAML"""
        parser = self.parsers.get(language)
        if not parser:
            raise ValueError(f"Unsupported language: {language}")

        # Extract actions using appropriate parser
        actions = parser.extract_actions(file_path)  # type: ignore

        # Convert to SpecQL YAML
        return self._generate_yaml(file_path, actions, language)

    def convert_code(self, code: str, language: str, **kwargs: object) -> str:
        """Convert source code string to SpecQL YAML"""
        parser = self.parsers.get(language)
        if not parser:
            raise ValueError(f"Unsupported language: {language}")

        # Extract actions using appropriate parser
        if hasattr(parser, "extract_actions_from_code"):
            actions = parser.extract_actions_from_code(code)  # type: ignore
        else:
            # Fallback for parsers that don't have extract_actions_from_code
            raise NotImplementedError(
                f"Parser for {language} doesn't support code string conversion"
            )

        # Convert to SpecQL YAML
        return self._generate_yaml_from_code(actions, language)

    def _generate_yaml(self, file_path: Path, actions: list[dict[str, Any]], language: str) -> str:
        """Generate SpecQL YAML from actions"""
        # Group actions by entity (inferred from file path and action names)
        entity_name = self._infer_entity_name(file_path, actions)

        specql_dict = {
            "entity": entity_name,
            "description": f"Actions extracted from {language} file {file_path.name}",
            "actions": actions,
            "_metadata": {
                "source_file": str(file_path),
                "source_language": language,
                "extraction_method": "action_parser",
                "total_actions": len(actions),
            },
        }

        return yaml.dump(specql_dict, default_flow_style=False, sort_keys=False)

    def _generate_yaml_from_code(self, actions: list[dict[str, Any]], language: str) -> str:
        """Generate SpecQL YAML from actions (when no file path available)"""
        # Group actions by entity (inferred from action names)
        entity_name = self._infer_entity_name_from_actions(actions)

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
