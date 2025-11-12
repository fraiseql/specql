"""
Numbering System Parser
Parses 6-digit decimal table codes into hierarchical components
"""

import re
from dataclasses import dataclass


@dataclass
class TableCodeComponents:
    """Structured representation of parsed table code components"""

    schema_layer: str  # 2 digits: schema type (01=write_side, etc.)
    domain_code: str  # 1 digit: domain (0-9)
    subdomain_code: str  # 1 digit: subdomain (0-9)
    entity_sequence: str  # 1 digit: entity sequence (0-9)
    file_sequence: str  # 1 digit: file sequence (0-9)

    @property
    def full_domain(self) -> str:
        """Full domain code: schema_layer + domain_code"""
        return f"{self.schema_layer}{self.domain_code}"

    @property
    def full_group(self) -> str:
        """Full group code: full_domain + subdomain_code (4 digits: SS+D+S)"""
        return f"{self.full_domain}{self.subdomain_code}"

    @property
    def full_entity(self) -> str:
        """Full entity code: full_group + entity_sequence (5 digits: SS+D+S+E)"""
        return f"{self.full_group}{self.entity_sequence}"

    @property
    def table_code(self) -> str:
        """Reconstruct the full 6-digit decimal table code"""
        return f"{self.schema_layer}{self.domain_code}{self.subdomain_code}{self.entity_sequence}{self.file_sequence}"


class NumberingParser:
    """Parse and validate materialized numbering codes"""

    # Schema layer mappings
    SCHEMA_LAYERS = {"01": "write_side", "02": "read_side", "03": "analytics"}

    # Domain code mappings
    DOMAIN_CODES = {"1": "core", "2": "management", "3": "catalog", "4": "tenant"}

    def parse_table_code(self, table_code: str) -> dict[str, str]:
        """Parse 6-digit decimal table code into hierarchical components"""
        components = self.parse_table_code_detailed(table_code)

        return {
            "schema_layer": components.schema_layer,
            "domain_code": components.domain_code,
            "subdomain_code": components.subdomain_code,  # 1-digit subdomain
            "entity_sequence": components.entity_sequence,
            "file_sequence": components.file_sequence,
            "full_domain": components.full_domain,
            "full_group": components.full_group,
            "full_entity": components.full_entity,
        }

    def parse_table_code_detailed(self, table_code: str) -> TableCodeComponents:
        """
        Parse 6-digit decimal table code into structured components

        Format: SDSEX (Schema + Domain + Subdomain + Entity + FileSequence)
        - SS (2 digits): Schema layer (01=write_side, 02=read_side, 03=functions)
        - D (1 digit): Domain (0-9)
        - S (1 digit): Subdomain (0-9)
        - E (1 digit): Entity sequence (0-9)
        - X (1 digit): File sequence (0-9)

        Args:
            table_code: 6-digit decimal string

        Returns:
            TableCodeComponents: Structured representation of the code

        Raises:
            ValueError: If table_code is invalid
        """
        if not table_code:
            raise ValueError("table_code is required")

        if not isinstance(table_code, str):
            raise ValueError(f"table_code must be a string, got {type(table_code)}")

        # Require exactly 6 hexadecimal digits
        if not re.match(r"^[0-9a-fA-F]{6}$", table_code):
            raise ValueError(
                f"Invalid table_code: {table_code}. "
                f"Must be exactly 6 hexadecimal digits (0-9, a-f, A-F), got {len(table_code)}."
            )

        return TableCodeComponents(
            schema_layer=table_code[0:2],   # First 2 digits: SS
            domain_code=table_code[2],       # 3rd digit: D
            subdomain_code=table_code[3],    # 4th digit: S (1 digit)
            entity_sequence=table_code[4],   # 5th digit: E
            file_sequence=table_code[5],     # 6th digit: X
        )

    def generate_directory_path(self, table_code: str, entity_name: str) -> str:
        """
        Generate hierarchical directory path from table code and entity name

        Directory structure follows SDSEX format:
        - Layer 1: SS_schema/ (2 digits)
        - Layer 2: SSD_domain/ (3 digits)
        - Layer 3: SSDS_subdomain/ (4 digits)
        - Layer 4: SSDSE_entity/ (5 digits)

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

        # Build progressive directory structure
        schema_dir = f"{components.schema_layer}_{schema_name}"
        domain_dir = f"{components.full_domain}_{domain_name}"
        subdomain_dir = f"{components.full_group}_{entity_snake}"  # SSDS_subdomain
        entity_dir = f"{components.full_entity}_{entity_snake}"    # SSDSE_entity

        return f"{schema_dir}/{domain_dir}/{subdomain_dir}/{entity_dir}"

    def generate_file_path(self, table_code: str, entity_name: str, file_type: str) -> str:
        """
        Generate file path with proper naming convention

        File is placed in the entity directory (5 digits) with 6-digit filename.

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
            filename = f"{table_code}_tb_{entity_snake}"
        elif file_type == "view":
            filename = f"{table_code}_v_{entity_snake}"
        elif file_type == "function":
            filename = f"{table_code}_fn_{entity_snake}"
        else:
            filename = f"{table_code}_{entity_snake}_{file_type}"

        return f"{dir_path}/{filename}.{ext}"
