"""
Write-side path generation

Generates hierarchical file paths for write-side tables based on table codes.
Implements PathGenerator protocol for use with HierarchicalFileWriter.
"""

from pathlib import Path

from src.generators.schema.hierarchical_file_writer import FileSpec, PathGenerator
from src.generators.schema.naming_conventions import NamingConventions


class WriteSidePathGenerator(PathGenerator):
    """
    Generates hierarchical paths for write-side files

    Path structure:
    0_schema/01_write_side/0{D}{D}_{domain}/0{D}{D}{S}_{subdomain}/{D}{D}{S}{E}_{entity}/{table_code}_{filename}.sql

    Where:
    - D: domain code (1 digit)
    - S: subdomain code (1 digit from table code)
    - E: entity sequence (1 digit from table code)

    Example:
        generate_path(FileSpec(code="012361", name="tb_contact", layer="write_side"))
        → 0_schema/01_write_side/012_crm/0123_customer/01236_contact/012361_tb_contact.sql
    """

    # Schema layer constants
    SCHEMA_LAYER_WRITE = "01"
    SCHEMA_LAYER_PREFIX = "0_schema"
    WRITE_SIDE_DIR = "01_write_side"

    def __init__(self, base_dir: str = "generated"):
        """
        Initialize with base directory

        Args:
            base_dir: Base directory for generated files (default: "generated")
        """
        self.base_dir = Path(base_dir)
        self.naming = NamingConventions()

    def generate_path(self, file_spec: FileSpec) -> Path:
        """
        Generate hierarchical path from file specification

        Args:
            file_spec: File specification with write-side code

        Returns:
            Path object for the file location

        Raises:
            ValueError: If file spec is not for write-side or code format is invalid
        """
        if file_spec.layer != "write_side":
            raise ValueError(f"WriteSidePathGenerator can only handle write_side files, got {file_spec.layer}")

        # Accept 6-digit codes only
        if len(file_spec.code) != 6:
            raise ValueError(f"Write-side code must be 6 digits, got: {file_spec.code}")

        # Parse code using the numbering parser
        from src.numbering.numbering_parser import NumberingParser
        parser = NumberingParser()
        components = parser.parse_table_code_detailed(file_spec.code)

        schema_layer = components.schema_layer
        domain_code = components.domain_code
        subdomain_code = components.subdomain_code  # Now 1 digit
        entity_sequence = components.entity_sequence

        # Validate schema layer
        if schema_layer != "01":
            raise ValueError(f"Invalid schema layer '{schema_layer}' for write-side code (expected '01')")

        # Get domain info from registry
        domain_info = self.naming.registry.get_domain(domain_code)
        if not domain_info:
            raise ValueError(f"Unknown domain code: {domain_code}")

        # Get subdomain info
        subdomain_info = self.naming.registry.get_subdomain(domain_code, subdomain_code)
        if not subdomain_info:
            raise ValueError(f"Unknown subdomain code: {subdomain_code} in domain {domain_code}")

        # Build path components
        domain_name = domain_info.domain_name
        subdomain_name = subdomain_info.subdomain_name

        # Domain directory: {schema_layer}{domain_code}_{domain_name}
        domain_dir = f"{schema_layer}{domain_code}_{domain_name}"

        # Subdomain directory
        subdomain_dir_code = f"{schema_layer}{domain_code}{subdomain_code}"
        subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"

        # Entity directory: {subdomain_dir_code}{entity_sequence}_{entity_name}
        # For write-side, we need to infer entity name from file_spec.name
        # file_spec.name can be like "tb_contact", "fn_contact_create_contact", "tb_contact_audit"
        if file_spec.name.startswith("tb_"):
            # Table or audit file: "tb_contact" -> entity_name = "contact"
            entity_name = file_spec.name[3:]  # Remove "tb_" prefix
            # Handle audit files: "tb_contact_audit" -> "contact"
            if entity_name.endswith("_audit"):
                entity_name = entity_name[:-6]  # Remove "_audit" suffix
        elif file_spec.name.startswith("fn_"):
            # Function file: "fn_contact_create_contact" -> entity_name = "contact"
            # Remove "fn_" prefix and action name
            name_parts = file_spec.name[3:].split("_")  # Split on underscores
            entity_name = name_parts[0]  # First part is entity name
        else:
            raise ValueError(f"Write-side file name should start with 'tb_' or 'fn_', got: {file_spec.name}")

        # Convert to snake_case for directory name
        from src.generators.naming_utils import camel_to_snake
        entity_snake = camel_to_snake(entity_name)

        entity_dir_code = f"{subdomain_dir_code}{entity_sequence}"
        entity_dir = f"{entity_dir_code}_{entity_snake}"

        # File name: {table_code}_{filename}.sql
        filename = f"{file_spec.code}_{file_spec.name}.sql"

        # Combine path
        return self.base_dir / self.SCHEMA_LAYER_PREFIX / self.WRITE_SIDE_DIR / domain_dir / subdomain_dir / entity_dir / filename