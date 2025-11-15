"""
Read-side path generation

Generates hierarchical file paths for read-side views based on codes.
Implements PathGenerator protocol for use with HierarchicalFileWriter.
"""

from pathlib import Path

from src.generators.schema.code_parser import ReadSideCodeParser
from src.generators.schema.hierarchical_file_writer import FileSpec, PathGenerator


class ReadSidePathGenerator(PathGenerator):
    """
    Generates hierarchical paths for read-side files

    Path structure:
    0_schema/02_query_side/02{D}_{domain}/02{D}{S}_{subdomain}/02{D}{S}{E}_{entity}/{code}_{view}.sql

    Where:
    - D: domain code (1 digit)
    - S: subdomain code (1 digit)
    - E: entity sequence (1 digit)

    Example:
        generate_path(FileSpec(code="022310", name="v_contact", layer="read_side"))
        → 0_schema/02_query_side/022_crm/0223_customer/02232_contact/022310_v_contact.sql
    """

    # Schema layer constants
    SCHEMA_LAYER_READ = "02"
    SCHEMA_LAYER_PREFIX = "0_schema"
    QUERY_SIDE_DIR = "02_query_side"

    def __init__(self, base_dir: str = "generated"):
        """
        Initialize with base directory

        Args:
            base_dir: Base directory for generated files (default: "generated")
        """
        self.base_dir = Path(base_dir)
        self.parser = ReadSideCodeParser()

    def generate_path(self, file_spec: FileSpec) -> Path:
        """
        Generate hierarchical path from file specification

        Args:
            file_spec: File specification with read-side code

        Returns:
            Path object for the file location

        Raises:
            ValueError: If file spec is not for read-side or code format is invalid

        Example:
            generate_path(FileSpec(code="0220310", name="tv_contact", layer="read_side"))
            → 0_schema/02_query_side/022_crm/0223_customer/0220310_tv_contact.sql
        """
        if file_spec.layer != "read_side":
            raise ValueError(f"ReadSidePathGenerator can only handle read_side files, got {file_spec.layer}")

        code = file_spec.code
        view_name = file_spec.name

        if not view_name:
            raise ValueError("view_name cannot be empty")

        # Accept 6-digit codes only
        if len(code) != 6:
            raise ValueError(f"Read-side code must be 6 digits, got: {code}")

        # Parse the code
        components = self.parser.parse(code)

        # Validate layer
        if components.schema_layer != "02":
            raise ValueError(f"Invalid schema layer '{components.schema_layer}' for read-side code (expected '02')")

        # Build path components
        domain_name = self._get_domain_name(components.domain)
        if not domain_name:
            raise ValueError(f"Unknown domain code: {components.domain}")

        subdomain_name = self._get_subdomain_name(components.domain, components.subdomain)
        if not subdomain_name:
            raise ValueError(f"Unknown subdomain code: {components.subdomain} in domain {components.domain}")

        # Domain directory: 02{domain}_{domain_name}
        domain_dir = f"02{components.domain}_{domain_name}"

        # Subdomain directory: 02{domain}{subdomain}_{subdomain_name}
        subdomain_dir = f"02{components.domain}{components.subdomain}_{subdomain_name}"

        # Entity directory: 02{domain}{subdomain}{entity}_{entity_name}
        # For read-side, infer entity name from view_name (e.g., "v_contact" -> "contact")
        if view_name.startswith("v_"):
            entity_name = view_name[2:]  # Remove "v_" prefix
        elif view_name.startswith("tv_"):
            entity_name = view_name[3:]  # Remove "tv_" prefix
        else:
            raise ValueError(f"Read-side view name should start with 'v_' or 'tv_', got: {view_name}")

        # Convert to snake_case for directory name
        from src.generators.naming_utils import camel_to_snake
        entity_snake = camel_to_snake(entity_name)

        entity_dir = f"02{components.domain}{components.subdomain}{components.entity}_{entity_snake}"

        # File name
        filename = f"{code}_{view_name}.sql"

        # Combine path (now includes entity directory)
        return self.base_dir / self.SCHEMA_LAYER_PREFIX / self.QUERY_SIDE_DIR / domain_dir / subdomain_dir / entity_dir / filename

    def format_domain_path(self, domain_code: str, subdomain_code: str, domain_name: str) -> str:
        """
        Format domain directory path

        Args:
            domain_code: Domain code (e.g., "2")
            subdomain_code: Subdomain code (e.g., "03")
            domain_name: Domain name (e.g., "crm")

        Returns:
            Domain directory name (e.g., "022_crm")
        """
        return f"0{domain_code}{domain_code}_{domain_name}"

    def format_subdomain_path(self, domain_code: str, subdomain_code: str, subdomain_name: str) -> str:
        """
        Format subdomain directory path

        Args:
            domain_code: Domain code (e.g., "2")
            subdomain_code: Subdomain code (e.g., "03")
            subdomain_name: Subdomain name (e.g., "customer")

        Returns:
            Subdomain directory name (e.g., "0223_customer")
        """
        return f"0{domain_code}{domain_code}{subdomain_code[1]}_{subdomain_name}"

    def _get_domain_name(self, domain_code: str) -> str:
        """Get domain name from domain code"""
        domain_map = {
            "1": "core",
            "2": "crm",
            "3": "catalog",
            "4": "projects",
            "5": "analytics",
            "6": "finance"
        }
        return domain_map.get(domain_code, f"domain_{domain_code}")

    def _get_subdomain_name(self, domain_code: str, subdomain_code: str) -> str:
        """Get subdomain name from domain and subdomain codes"""
        # This is a simplified mapping - in a real implementation,
        # this would come from the registry
        subdomain_map = {
            ("2", "1"): "core",
            ("2", "2"): "sales",
            ("2", "3"): "customer",
            ("2", "4"): "support",
            ("2", "5"): "marketing",
            ("3", "1"): "classification",
            ("3", "2"): "manufacturer",
            ("3", "3"): "financing",
            ("3", "4"): "generic",
            ("4", "1"): "core",
            ("4", "2"): "location",
            ("4", "3"): "network",
            ("4", "4"): "contract",
            ("4", "5"): "machine",
            ("4", "6"): "allocation",
        }

        return subdomain_map.get((domain_code, subdomain_code), f"subdomain_{subdomain_code}")