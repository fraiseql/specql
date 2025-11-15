"""
TypeScript parser for SpecQL reverse engineering.

Parses TypeScript interface and type definitions.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional

from src.core.universal_ast import UniversalEntity, UniversalField, FieldType

logger = logging.getLogger(__name__)


class TypeScriptParser:
    """Parser for TypeScript files."""

    def __init__(self):
        self.type_mapping = {
            "string": FieldType.TEXT,
            "number": FieldType.INTEGER,
            "boolean": FieldType.BOOLEAN,
            "Date": FieldType.DATETIME,
            "any": FieldType.RICH,
            "unknown": FieldType.RICH,
            "null": FieldType.RICH,
            "undefined": FieldType.RICH,
        }

        # Pre-compile regex patterns for better performance
        self.interface_pattern = re.compile(
            r"interface\s+(\w+)(?:\s+extends\s+([^{]+))?\s*\{", re.DOTALL
        )
        self.type_pattern = re.compile(r"type\s+(\w+)\s*=\s*\{([^}]+)\}", re.DOTALL)

    def parse_file(self, file_path: str) -> List[UniversalEntity]:
        """Parse a TypeScript file."""
        ts_file = Path(file_path)
        if not ts_file.exists():
            raise FileNotFoundError(f"TypeScript file not found: {file_path}")

        content = ts_file.read_text()
        return self.parse_content(content, file_path)

    def parse_content(
        self, content: str, source_file: str = "unknown"
    ) -> List[UniversalEntity]:
        """Parse TypeScript content."""
        entities = []

        # Parse interfaces
        interface_entities = self._parse_interfaces(content)
        entities.extend(interface_entities)

        # Parse type aliases (basic support)
        type_entities = self._parse_type_aliases(content)
        entities.extend(type_entities)

        # Parse enums
        enum_entities = self._parse_enums(content)
        entities.extend(enum_entities)

        logger.info(f"Parsed {len(entities)} entities from {source_file}")
        return entities

    def _parse_interfaces(self, content: str) -> List[UniversalEntity]:
        """Parse TypeScript interfaces."""
        entities = []

        # Find all interface definitions
        interface_starts = list(self.interface_pattern.finditer(content))

        for match in interface_starts:
            interface_name = match.group(1)
            match.group(2) or ""
            start_pos = match.end()

            # Find the matching closing brace
            brace_count = 1
            end_pos = start_pos
            while end_pos < len(content) and brace_count > 0:
                if content[end_pos] == "{":
                    brace_count += 1
                elif content[end_pos] == "}":
                    brace_count -= 1
                end_pos += 1

            interface_body = content[
                start_pos : end_pos - 1
            ]  # Exclude the closing brace

            try:
                fields = self._parse_interface_fields(interface_body)

                if fields:
                    entity = UniversalEntity(
                        name=interface_name,
                        schema="public",
                        fields=fields,
                        actions=[],
                        description=f"TypeScript interface {interface_name}",
                    )
                    entities.append(entity)

            except Exception as e:
                logger.warning(f"Failed to parse interface {interface_name}: {e}")
                continue

        return entities

    def _parse_interface_fields(self, interface_body: str) -> List[UniversalField]:
        """Parse fields from interface body."""
        fields = []

        # Split into lines and parse each field
        lines = [line.strip() for line in interface_body.split("\n") if line.strip()]
        lines = [
            line
            for line in lines
            if not line.startswith("//") and not line.startswith("/*")
        ]

        for line in lines:
            # Remove trailing comma and semicolon
            line = line.rstrip(",;")

            # Skip empty lines and method declarations
            if not line or "(" in line or ")" in line:
                continue

            field = self._parse_field_line(line)
            if field:
                fields.append(field)

        return fields

    def _parse_field_line(self, line: str) -> Optional[UniversalField]:
        """Parse a single field line from interface."""
        # Handle optional fields (field?: type)
        optional_match = re.match(r"(\w+)\?\s*:\s*(.+)", line)
        if optional_match:
            field_name = optional_match.group(1)
            field_type = optional_match.group(2).strip()
            is_optional = True
        else:
            # Regular fields (field: type)
            field_match = re.match(r"(\w+)\s*:\s*(.+)", line)
            if not field_match:
                return None

            field_name = field_match.group(1)
            field_type = field_match.group(2).strip()
            is_optional = False

        # Clean up the type (remove comments, etc.)
        field_type = re.sub(r"\s*//.*$", "", field_type).strip()
        # Remove trailing semicolon
        field_type = field_type.rstrip(";").strip()

        # Map TypeScript type to SpecQL FieldType
        specql_type = self._map_typescript_type(field_type)

        field = UniversalField(
            name=field_name, type=specql_type, required=not is_optional
        )

        # Handle reference types
        if field_type.startswith("I") and field_type[1].isupper():
            # Likely an interface reference (e.g., IUser, IPost)
            field.references = field_type

        return field

    def _map_typescript_type(self, ts_type: str) -> FieldType:
        """Map TypeScript type to SpecQL FieldType."""
        # Handle array types
        if ts_type.endswith("[]"):
            return FieldType.LIST

        # Handle union types (take first type)
        if "|" in ts_type:
            first_type = ts_type.split("|")[0].strip()
            return self._map_typescript_type(first_type)

        # Handle generic types
        if "<" in ts_type:
            base_type = ts_type.split("<")[0]
            return self.type_mapping.get(base_type, FieldType.RICH)

        # Handle intersection types (&)
        if "&" in ts_type:
            return FieldType.RICH  # Intersection types are complex

        # Direct type mapping
        return self.type_mapping.get(ts_type, FieldType.RICH)

    def _parse_type_aliases(self, content: str) -> List[UniversalEntity]:
        """Parse basic TypeScript type aliases."""
        entities = []

        # Match type alias definitions (basic support)
        matches = self.type_pattern.findall(content)

        for type_name, type_body in matches:
            try:
                fields = self._parse_interface_fields(type_body)

                if fields:
                    entity = UniversalEntity(
                        name=type_name,
                        schema="public",
                        fields=fields,
                        actions=[],
                        description=f"TypeScript type {type_name}",
                    )
                    entities.append(entity)

            except Exception as e:
                logger.warning(f"Failed to parse type alias {type_name}: {e}")
                continue

        return entities

    def _parse_enums(self, content: str) -> List[UniversalEntity]:
        """Parse TypeScript enums."""
        entities = []

        # Match enum definitions
        enum_pattern = r"enum\s+(\w+)\s*\{([^}]+)\}"
        matches = re.findall(enum_pattern, content, re.DOTALL)

        for enum_name, enum_body in matches:
            try:
                # Parse enum values
                values = []
                lines = [
                    line.strip().rstrip(",")
                    for line in enum_body.split("\n")
                    if line.strip()
                ]

                for line in lines:
                    if "=" in line:
                        # Has explicit value
                        name, value = line.split("=", 1)
                        name = name.strip()
                        values.append(f"{name}={value.strip()}")
                    else:
                        # Auto-assigned value
                        values.append(line.strip())

                if values:
                    entity = UniversalEntity(
                        name=enum_name,
                        schema="public",
                        fields=[],  # Enums don't have fields, but we can store values in description
                        actions=[],
                        description=f"TypeScript enum {enum_name}: {', '.join(values)}",
                    )
                    entities.append(entity)

            except Exception as e:
                logger.warning(f"Failed to parse enum {enum_name}: {e}")
                continue

        return entities

    def parse_project(self, project_dir: str) -> List[UniversalEntity]:
        """Parse a TypeScript project directory."""
        entities = []
        project_path = Path(project_dir)

        if not project_path.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

        # Find all .ts and .tsx files
        ts_files = list(project_path.glob("**/*.ts")) + list(
            project_path.glob("**/*.tsx")
        )

        for ts_file in ts_files:
            try:
                file_entities = self.parse_file(str(ts_file))
                entities.extend(file_entities)
            except Exception as e:
                logger.warning(f"Failed to parse {ts_file}: {e}")
                continue

        logger.info(
            f"Parsed {len(entities)} entities from {len(ts_files)} TypeScript files"
        )
        return entities
