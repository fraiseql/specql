"""
Numbering System Parser
Parses 7-digit decimal table codes into hierarchical components
"""

import re
from dataclasses import dataclass


@dataclass
class TableCodeComponents:
    """Structured representation of parsed table code components"""

    schema_layer: str  # 2 digits: schema type (01=write_side, etc.)
    domain_code: str  # 1 digit: domain (0-9)
    subdomain_code: str  # 2 digits: subdomain (00-99)
    entity_sequence: str  # 1 digit: entity sequence (0-9)
    file_sequence: str  # 1 digit: file sequence (0-9)

    @property
    def full_domain(self) -> str:
        """Full domain code: schema_layer + domain_code"""
        return f"{self.schema_layer}{self.domain_code}"

    @property
    def full_group(self) -> str:
        """Full group code: full_domain + subdomain_code"""
        return f"{self.full_domain}{self.subdomain_code}"

    @property
    def full_entity(self) -> str:
        """Full entity code: full_group + entity_sequence"""
        return f"{self.full_group}{self.entity_sequence}"

    @property
    def table_code(self) -> str:
        """Reconstruct the full 7-digit decimal table code"""
        return f"{self.schema_layer}{self.domain_code}{self.subdomain_code}{self.entity_sequence}{self.file_sequence}"


class NumberingParser:
    """Parse and validate materialized numbering codes"""

    # Schema layer mappings
    SCHEMA_LAYERS = {"01": "write_side", "02": "read_side", "03": "analytics"}

    # Domain code mappings
    DOMAIN_CODES = {"1": "core", "2": "management", "3": "catalog", "4": "tenant"}

    def parse_table_code(self, table_code: str) -> dict[str, str]:
        """Parse 7-character hexadecimal table code into hierarchical components"""
        components = self.parse_table_code_detailed(table_code)

        return {
            "schema_layer": components.schema_layer,
            "domain_code": components.domain_code,
            "entity_group": components.subdomain_code,  # Use correct single-digit subdomain
            "entity_code": components.entity_sequence,  # Use correct field name
            "file_sequence": components.file_sequence,
            "full_domain": components.full_domain,
            "full_group": components.full_group,
            "full_entity": components.full_entity,
        }

    def parse_table_code_detailed(self, table_code: str) -> TableCodeComponents:
        """
        Parse 7-digit decimal table code into structured components

        Args:
            table_code: 7-digit decimal string (or 6-digit for backward compat)

        Returns:
            TableCodeComponents: Structured representation of the code

        Raises:
            ValueError: If table_code is invalid
        """
        if not table_code:
            raise ValueError("table_code is required")

        if not isinstance(table_code, str):
            raise ValueError(f"table_code must be a string, got {type(table_code)}")

        # Accept 6 or 7 decimal digits (backward compatibility)
        if len(table_code) == 6:
            # 6-digit code (SSDSSE): assume file_sequence = "1" for backward compat
            # Format: SS (layer) + D (domain) + SS (subdomain) + E (entity)
            if not re.match(r"^[0-9]{6}$", table_code):
                raise ValueError(
                    f"Invalid table_code: {table_code}. "
                    f"Must be 6 or 7 decimal digits (0-9)."
                )
            return TableCodeComponents(
                schema_layer=table_code[0:2],  # First 2 digits
                domain_code=table_code[2],      # 3rd digit
                subdomain_code=table_code[3:5], # 4th-5th digits
                entity_sequence=table_code[5],  # 6th digit
                file_sequence="1",              # Default file sequence
            )
        elif len(table_code) == 7:
            # 7-digit code (SSDSSEX): parse normally
            # Format: SS (layer) + D (domain) + SS (subdomain) + E (entity) + X (file)
            if not re.match(r"^[0-9]{7}$", table_code):
                raise ValueError(
                    f"Invalid table_code: {table_code}. "
                    f"Must be exactly 7 decimal digits (0-9)."
                )
            return TableCodeComponents(
                schema_layer=table_code[0:2],   # First 2 digits
                domain_code=table_code[2],       # 3rd digit
                subdomain_code=table_code[3:5],  # 4th-5th digits
                entity_sequence=table_code[5],   # 6th digit
                file_sequence=table_code[6],     # 7th digit
            )
        else:
            raise ValueError(
                f"Invalid table_code: {table_code}. "
                f"Must be 6 or 7 decimal digits (0-9), got {len(table_code)}."
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
        from src.generators.naming_utils import camel_to_snake

        components = self.parse_table_code_detailed(table_code)

        schema_name = self.SCHEMA_LAYERS.get(
            components.schema_layer, f"schema_{components.schema_layer}"
        )
        domain_name = self.DOMAIN_CODES.get(
            components.domain_code, f"domain_{components.domain_code}"
        )

        entity_snake = camel_to_snake(entity_name)

        return f"{components.schema_layer}_{schema_name}/{components.full_domain}_{domain_name}/{components.full_group}_{entity_snake}/{components.full_entity}_{entity_snake}"

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
        from src.generators.naming_utils import camel_to_snake

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
        entity_snake = camel_to_snake(entity_name)
        if file_type == "table":
            filename = f"tb_{entity_snake}"
        else:
            filename = f"{entity_snake}_{file_type}"

        return f"{dir_path}/{table_code}_{filename}.{ext}"
