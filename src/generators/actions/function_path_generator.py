"""
Function path generation for write-side functions

Generates hierarchical file paths for function files based on 6-digit codes.
Functions use layer 03 and follow the same hierarchy as tables.
"""

from pathlib import Path
from src.generators.schema.hierarchical_file_writer import FileSpec, PathGenerator
from src.generators.schema.naming_conventions import NamingConventions


class FunctionPathGenerator(PathGenerator):
    """
    Generates hierarchical paths for function files (layer 03)

    Path structure:
    0_schema/03_functions/03{D}_{domain}/03{D}{S}_{subdomain}/03{D}{S}{E}_{entity}/{code}_{fn_name}.sql

    Where:
    - D: domain code (1 digit)
    - S: subdomain code (1 digit)
    - E: entity sequence (1 digit)

    Example:
        generate_path(FileSpec(code="032361", name="fn_contact_create", layer="functions"))
        → 0_schema/03_functions/032_crm/0323_customer/03232_contact/032361_fn_contact_create.sql
    """

    # Schema layer constants
    SCHEMA_LAYER_FUNCTIONS = "03"
    SCHEMA_LAYER_PREFIX = "0_schema"
    FUNCTIONS_DIR = "03_functions"

    def __init__(self, base_dir: str = "generated"):
        """Initialize with base directory"""
        self.base_dir = Path(base_dir)
        self.naming = NamingConventions()

    def generate_path(self, file_spec: FileSpec) -> Path:
        """
        Generate hierarchical path from file specification

        Args:
            file_spec: File specification with function code (6 digits)

        Returns:
            Path object for the file location

        Raises:
            ValueError: If code format is invalid or not layer 03
        """
        if len(file_spec.code) != 6:
            raise ValueError(f"Function code must be 6 digits, got: {file_spec.code}")

        # Parse function code (same structure as table code but layer 03)
        schema_layer = file_spec.code[:2]
        domain_code = file_spec.code[2]
        subdomain_code = file_spec.code[3]  # 1 digit
        entity_sequence = file_spec.code[4]
        file_spec.code[5]

        # Validate schema layer
        if schema_layer != "03":
            raise ValueError(
                f"Invalid schema layer '{schema_layer}' for function code (expected '03')"
            )

        # Get domain and subdomain info from registry
        domain_info = self.naming.registry.get_domain(domain_code)
        if not domain_info:
            raise ValueError(f"Unknown domain code: {domain_code}")

        subdomain_info = self.naming.registry.get_subdomain(domain_code, subdomain_code)
        if not subdomain_info:
            raise ValueError(f"Unknown subdomain code: {subdomain_code} in domain {domain_code}")

        # Build path components
        domain_name = domain_info.domain_name
        subdomain_name = subdomain_info.subdomain_name

        # Domain directory: 03{domain_code}_{domain_name}
        domain_dir = f"{schema_layer}{domain_code}_{domain_name}"

        # Subdomain directory: 03{domain_code}{subdomain_code}_{subdomain_name}
        subdomain_dir = f"{schema_layer}{domain_code}{subdomain_code}_{subdomain_name}"

        # Entity directory: infer from file_spec.name
        # file_spec.name format: "fn_contact_create_contact" or "fn_contact_create"
        if file_spec.name.startswith("fn_"):
            name_parts = file_spec.name[3:].split("_")
            entity_name = name_parts[0]  # First part is entity name
        else:
            raise ValueError(f"Function file name should start with 'fn_', got: {file_spec.name}")

        from src.generators.naming_utils import camel_to_snake
        entity_snake = camel_to_snake(entity_name)

        entity_dir_code = f"{schema_layer}{domain_code}{subdomain_code}{entity_sequence}"
        entity_dir = f"{entity_dir_code}_{entity_snake}"

        # File name: {code}_{fn_name}.sql
        filename = f"{file_spec.code}_{file_spec.name}.sql"

        # Combine path
        return (
            self.base_dir
            / self.SCHEMA_LAYER_PREFIX
            / self.FUNCTIONS_DIR
            / domain_dir
            / subdomain_dir
            / entity_dir
            / filename
        )