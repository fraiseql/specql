"""
Numbering System Parser
Parses 6-character hexadecimal table codes into hierarchical components
"""

import re
from dataclasses import dataclass


@dataclass
class TableCodeComponents:
    """Structured representation of parsed table code components"""

    schema_layer: str  # 2 hex chars: schema type (01=write_side, etc.)
    domain_code: str  # 1 hex char: domain (0-F)
    entity_group: str  # 1 hex char: entity group
    entity_code: str  # 1 hex char: entity code
    file_sequence: str  # 1 hex char: file sequence

    @property
    def full_domain(self) -> str:
        """Full domain code: schema_layer + domain_code"""
        return f"{self.schema_layer}{self.domain_code}"

    @property
    def full_group(self) -> str:
        """Full group code: full_domain + entity_group"""
        return f"{self.full_domain}{self.entity_group}"

    @property
    def full_entity(self) -> str:
        """Full entity code: full_group + entity_code"""
        return f"{self.full_group}{self.entity_code}"

    @property
    def table_code(self) -> str:
        """Reconstruct the full 6-character hexadecimal table code"""
        return f"{self.schema_layer}{self.domain_code}{self.entity_group}{self.entity_code}{self.file_sequence}".upper()


class NumberingParser:
    """Parse and validate materialized numbering codes"""

    # Schema layer mappings
    SCHEMA_LAYERS = {"01": "write_side", "02": "read_side", "03": "analytics"}

    # Domain code mappings
    DOMAIN_CODES = {"1": "core", "2": "management", "3": "catalog", "4": "tenant"}

    def parse_table_code(self, table_code: str) -> dict[str, str]:
        """Parse 6-character hexadecimal table code into hierarchical components"""
        components = self.parse_table_code_detailed(table_code)

        return {
            "schema_layer": components.schema_layer,
            "domain_code": components.domain_code,
            "entity_group": components.entity_group,
            "entity_code": components.entity_code,
            "file_sequence": components.file_sequence,
            "full_domain": components.full_domain,
            "full_group": components.full_group,
            "full_entity": components.full_entity,
        }

    def parse_table_code_detailed(self, table_code: str) -> TableCodeComponents:
        """
        Parse 6-character hexadecimal table code into structured components

        Args:
            table_code: 6-character hexadecimal string (case-insensitive)

        Returns:
            TableCodeComponents: Structured representation of the code

        Raises:
            ValueError: If table_code is invalid
        """
        if not table_code:
            raise ValueError("table_code is required")

        if not isinstance(table_code, str):
            raise ValueError(f"table_code must be a string, got {type(table_code)}")

        # Normalize to uppercase
        table_code = table_code.upper()

        # Accept hexadecimal characters (0-9, A-F)
        if not re.match(r"^[0-9A-F]{6}$", table_code):
            raise ValueError(
                f"Invalid table_code: {table_code}. "
                f"Must be exactly 6 hexadecimal characters (0-9, A-F)."
            )

        return TableCodeComponents(
            schema_layer=table_code[0:2],
            domain_code=table_code[2],
            entity_group=table_code[3],
            entity_code=table_code[4],
            file_sequence=table_code[5],
        )

    def generate_directory_path(self, table_code: str, entity_name: str) -> str:
        """
        Generate hierarchical directory path from table code and entity name

        Args:
            table_code: 6-digit table code
            entity_name: Name of the entity

        Returns:
            str: Hierarchical directory path
        """
        components = self.parse_table_code_detailed(table_code)

        schema_name = self.SCHEMA_LAYERS.get(
            components.schema_layer, f"schema_{components.schema_layer}"
        )
        domain_name = self.DOMAIN_CODES.get(
            components.domain_code, f"domain_{components.domain_code}"
        )

        return f"{components.schema_layer}_{schema_name}/{components.full_domain}_{domain_name}/{components.full_group}_{entity_name}/{components.full_entity}_{entity_name}"

    def generate_file_path(self, table_code: str, entity_name: str, file_type: str) -> str:
        """
        Generate file path with proper naming convention

        Args:
            table_code: 6-digit table code
            entity_name: Name of the entity
            file_type: Type of file ('table', 'function', 'view', 'yaml', 'json')

        Returns:
            str: Complete file path with extension
        """
        if not entity_name:
            raise ValueError("entity_name is required")

        if not file_type:
            raise ValueError("file_type is required")

        dir_path = self.generate_directory_path(table_code, entity_name)

        # Map file types to extensions
        extensions = {
            "table": "sql",
            "function": "sql",
            "view": "sql",
            "yaml": "yaml",
            "json": "json",
        }
        ext = extensions.get(file_type, "sql")

        # Generate filename based on type
        if file_type == "table":
            filename = f"tb_{entity_name}"
        else:
            filename = f"{entity_name}_{file_type}"

        return f"{dir_path}/{table_code}_{filename}.{ext}"
