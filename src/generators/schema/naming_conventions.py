"""
Naming Conventions & Table Code Management

Provides automatic table code derivation, validation, and registry integration
for SpecQL entities following the SSDSSE (6-digit) numbering system.

Table Code Format: SSDSSE
- SS: Schema layer (01=write_side, 02=read_side, 03=analytics)
- D:  Domain code (1-9)
- SS: Subdomain code (00-99)
- E:  Entity sequence + file sequence

Example: 012321
  01 = write_side
  2  = crm domain
  32 = customer subdomain (3) + entity #2
  1  = first file
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from src.core.ast_models import Entity
from src.numbering.numbering_parser import NumberingParser

# ============================================================================
# Data Models
# ============================================================================


@dataclass
class EntityRegistryEntry:
    """Entity entry in registry"""

    entity_name: str
    table_code: str
    entity_code: str  # 3-char code (e.g., "CON" for Contact)
    assigned_at: str
    subdomain: str
    domain: str


@dataclass
class SubdomainInfo:
    """Subdomain information from registry"""

    subdomain_code: str
    subdomain_name: str
    description: str
    next_entity_sequence: int
    entities: dict[str, dict]


@dataclass
class DomainInfo:
    """Domain information from registry"""

    domain_code: str
    domain_name: str
    description: str
    subdomains: dict[str, SubdomainInfo]
    aliases: list[str]
    multi_tenant: bool


# ============================================================================
# Domain Registry
# ============================================================================


class DomainRegistry:
    """
    Load and manage domain registry

    Responsibilities:
    - Load registry from YAML
    - Index entities for fast lookup
    - Track assigned table codes
    - Manage entity registration
    - Save registry updates
    """

    def __init__(self, registry_path: str = "registry/domain_registry.yaml"):
        self.registry_path = Path(registry_path)
        self.registry: dict = {}
        self.entities_index: dict[str, EntityRegistryEntry] = {}
        self.load()

    def load(self):
        """Load registry from YAML file"""
        if not self.registry_path.exists():
            raise FileNotFoundError(
                f"Domain registry not found: {self.registry_path}\n"
                f"Create it by copying registry/domain_registry.yaml.example"
            )

        with open(self.registry_path) as f:
            self.registry = yaml.safe_load(f)

        # Build entity index for quick lookup
        self._build_entity_index()

    def _build_entity_index(self):
        """Build index of all registered entities for O(1) lookup"""
        self.entities_index = {}

        for domain_code, domain in self.registry.get("domains", {}).items():
            domain_name = domain["name"]

            for subdomain_code, subdomain in domain.get("subdomains", {}).items():
                subdomain_name = subdomain["name"]

                # Handle case where entities might be None or {}
                entities = subdomain.get("entities") or {}

                for entity_name, entity_data in entities.items():
                    self.entities_index[entity_name.lower()] = EntityRegistryEntry(
                        entity_name=entity_name,
                        table_code=entity_data["table_code"],
                        entity_code=entity_data["entity_code"],
                        assigned_at=entity_data["assigned_at"],
                        subdomain=subdomain_name,
                        domain=domain_name,
                    )

    def get_entity(self, entity_name: str) -> EntityRegistryEntry | None:
        """
        Get entity from registry by name

        Args:
            entity_name: Entity name (case-insensitive)

        Returns:
            EntityRegistryEntry if found, None otherwise
        """
        return self.entities_index.get(entity_name.lower())

    def get_domain(self, domain_identifier: str) -> DomainInfo | None:
        """
        Get domain by code, name, or alias

        Args:
            domain_identifier: Domain code ("2"), name ("crm"), or alias ("management")

        Returns:
            DomainInfo if found, None otherwise
        """
        # Try by code first
        if domain_identifier in self.registry.get("domains", {}):
            return self._build_domain_info(domain_identifier)

        # Try by name or alias
        for code, domain_data in self.registry.get("domains", {}).items():
            if domain_data["name"] == domain_identifier:
                return self._build_domain_info(code)
            if domain_identifier in domain_data.get("aliases", []):
                return self._build_domain_info(code)

        return None

    def _build_domain_info(self, domain_code: str) -> DomainInfo:
        """Build DomainInfo from registry data"""
        domain_data = self.registry["domains"][domain_code]

        # Build subdomain info
        subdomains = {}
        for subdomain_code, subdomain_data in domain_data.get("subdomains", {}).items():
            subdomains[subdomain_code] = SubdomainInfo(
                subdomain_code=subdomain_code,
                subdomain_name=subdomain_data["name"],
                description=subdomain_data["description"],
                next_entity_sequence=subdomain_data["next_entity_sequence"],
                entities=subdomain_data.get("entities", {}),
            )

        return DomainInfo(
            domain_code=domain_code,
            domain_name=domain_data["name"],
            description=domain_data["description"],
            subdomains=subdomains,
            aliases=domain_data.get("aliases", []),
            multi_tenant=domain_data.get("multi_tenant", False),
        )

    def get_subdomain(self, domain_code: str, subdomain_identifier: str) -> SubdomainInfo | None:
        """
        Get subdomain by code or name

        Args:
            domain_code: Domain code
            subdomain_identifier: Subdomain code ("03") or name ("customer")

        Returns:
            SubdomainInfo if found, None otherwise
        """
        domain_info = self._build_domain_info(domain_code)

        # Try by code
        if subdomain_identifier in domain_info.subdomains:
            return domain_info.subdomains[subdomain_identifier]

        # Try by name
        for code, subdomain in domain_info.subdomains.items():
            if subdomain.subdomain_name == subdomain_identifier:
                return subdomain

        return None

    def get_next_entity_sequence(self, domain_code: str, subdomain_code: str) -> int:
        """
        Get next available entity sequence number for subdomain

        Args:
            domain_code: Domain code (e.g., "2" for crm)
            subdomain_code: Subdomain code (e.g., "03" for customer)

        Returns:
            Next entity sequence number

        Raises:
            ValueError: If domain or subdomain not found
        """
        try:
            return self.registry["domains"][domain_code]["subdomains"][subdomain_code][
                "next_entity_sequence"
            ]
        except KeyError:
            raise ValueError(f"Subdomain {subdomain_code} not found in domain {domain_code}")

    def is_code_available(self, table_code: str) -> bool:
        """
        Check if table code is available (not already assigned)

        Args:
            table_code: 6-digit table code to check

        Returns:
            True if available, False if already assigned or reserved
        """
        # Check reserved codes
        reserved = self.registry.get("reserved_codes", [])
        if table_code in reserved:
            return False

        # Check if any entity has this code
        for entity in self.entities_index.values():
            if entity.table_code == table_code:
                return False

        return True

    def register_entity(
        self,
        entity_name: str,
        table_code: str,
        entity_code: str,
        domain_code: str,
        subdomain_code: str,
    ):
        """
        Register new entity in registry and save to file

        Args:
            entity_name: Name of the entity
            table_code: 6-digit table code
            entity_code: 3-character entity code
            domain_code: Domain code
            subdomain_code: Subdomain code

        Raises:
            ValueError: If domain or subdomain not found
        """
        # Validate domain and subdomain exist
        if domain_code not in self.registry.get("domains", {}):
            raise ValueError(f"Domain {domain_code} not found in registry")

        if subdomain_code not in self.registry["domains"][domain_code].get("subdomains", {}):
            raise ValueError(f"Subdomain {subdomain_code} not found in domain {domain_code}")

        # Add to in-memory registry
        subdomain = self.registry["domains"][domain_code]["subdomains"][subdomain_code]

        # Handle case where entities is None
        if subdomain.get("entities") is None:
            subdomain["entities"] = {}
        elif "entities" not in subdomain:
            subdomain["entities"] = {}

        subdomain["entities"][entity_name] = {
            "table_code": table_code,
            "entity_code": entity_code,
            "assigned_at": datetime.now().isoformat(),
        }

        # Increment next_entity_sequence
        subdomain["next_entity_sequence"] += 1

        # Update last_updated
        self.registry["last_updated"] = datetime.now().isoformat()

        # Save to file
        self.save()

        # Rebuild index
        self._build_entity_index()

    def save(self):
        """Save registry to YAML file"""
        with open(self.registry_path, "w") as f:
            yaml.dump(
                self.registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True
            )


# ============================================================================
# Naming Conventions
# ============================================================================


class NamingConventions:
    """
    Naming conventions and table code management

    Provides:
    - Automatic table code derivation
    - Validation of manual table codes
    - Entity code generation (3-char codes)
    - Subdomain inference
    - File path generation
    - Registry integration
    """

    def __init__(self, registry_path: str = "registry/domain_registry.yaml"):
        self.registry = DomainRegistry(registry_path)
        self.parser = NumberingParser()

    def get_table_code(self, entity: Entity, schema_layer: str = "01") -> str:
        """
        Get table code for entity (manual or auto-derived)

        Priority:
        1. Manual specification in YAML (organization.table_code)
        2. Registry lookup (if entity previously registered)
        3. Automatic derivation

        Args:
            entity: Entity AST model
            schema_layer: Schema layer code (default: "01" = write_side)

        Returns:
            6-digit table code string

        Raises:
            ValueError: If table code is invalid or cannot be derived
        """
        # Priority 1: Manual specification
        if entity.organization and entity.organization.table_code:
            table_code = entity.organization.table_code
            self.validate_table_code(table_code, entity)
            return table_code

        # Priority 2: Registry lookup
        registry_entry = self.registry.get_entity(entity.name)
        if registry_entry:
            return registry_entry.table_code

        # Priority 3: Automatic derivation
        return self.derive_table_code(entity, schema_layer=schema_layer)

    def derive_table_code(
        self, entity: Entity, schema_layer: str = "01", subdomain: str | None = None
    ) -> str:
        """
        Automatically derive table code from entity

        Table Code Format: SSDSSE
        - SS: Schema layer (01=write_side, 02=read_side, 03=analytics)
        - D:  Domain code (1-9)
        - SS: Subdomain code (00-99)
        - E:  Entity sequence (1-9) + file sequence (1)

        Args:
            entity: Entity AST model
            schema_layer: Schema layer code (default: "01")
            subdomain: Subdomain name (if None, will try to infer)

        Returns:
            6-digit table code (e.g., "012321")

        Raises:
            ValueError: If domain unknown or subdomain cannot be determined
        """
        # Get domain code
        domain_info = self.registry.get_domain(entity.schema)
        if not domain_info:
            raise ValueError(
                f"Unknown domain/schema: {entity.schema}\n"
                f"Available domains: {list(self.registry.registry.get('domains', {}).keys())}"
            )

        domain_code = domain_info.domain_code

        # Get or infer subdomain
        if subdomain is None:
            subdomain = self._infer_subdomain(entity, domain_info)

        # Find subdomain code
        subdomain_info = self.registry.get_subdomain(domain_code, subdomain)
        if not subdomain_info:
            raise ValueError(
                f"Subdomain '{subdomain}' not found in domain '{domain_info.domain_name}'\n"
                f"Available subdomains: {[s.subdomain_name for s in domain_info.subdomains.values()]}"
            )

        subdomain_code = subdomain_info.subdomain_code

        # Get next entity sequence
        entity_sequence = self.registry.get_next_entity_sequence(domain_code, subdomain_code)

        # Build table code: SSDSSE (6 digits total)
        # Format: schema_layer (2) + domain (1) + subdomain (2) + entity_seq (1)
        # Note: subdomain_code is already 2 digits (e.g., "03")
        # We need just the entity sequence digit, so take last digit of entity_sequence
        table_code = f"{schema_layer}{domain_code}{subdomain_code}{entity_sequence % 10}"

        # Validate uniqueness
        if not self.registry.is_code_available(table_code):
            raise ValueError(
                f"Table code {table_code} already assigned. "
                f"This is unexpected - registry may be corrupted."
            )

        return table_code

    def _infer_subdomain(self, entity: Entity, domain_info: DomainInfo) -> str:
        """
        Infer subdomain from entity name/characteristics

        Uses heuristics defined in registry (subdomain_inference section)

        Args:
            entity: Entity AST model
            domain_info: Domain information

        Returns:
            Inferred subdomain name (defaults to 'core' if unclear)
        """
        entity_name_lower = entity.name.lower()

        # Load inference rules from registry
        inference_rules = self.registry.registry.get("subdomain_inference", {})
        domain_rules = inference_rules.get(domain_info.domain_name, {})

        # Try to match patterns
        for subdomain_name, rules in domain_rules.items():
            patterns = rules.get("patterns", [])
            for pattern in patterns:
                if pattern in entity_name_lower:
                    return subdomain_name

        # Default: use 'core' subdomain
        # Check if 'core' exists in this domain
        for subdomain in domain_info.subdomains.values():
            if subdomain.subdomain_name == "core":
                return "core"

        # Fallback: first subdomain
        if domain_info.subdomains:
            return list(domain_info.subdomains.values())[0].subdomain_name

        raise ValueError(
            f"Cannot infer subdomain for entity '{entity.name}' in domain '{domain_info.domain_name}'"
        )

    def validate_table_code(self, table_code: str, entity: Entity):
        """
        Validate table code format and consistency

        Checks:
        - Format: exactly 6 hexadecimal characters (case-insensitive)
        - Schema layer exists
        - Domain code exists and matches entity.schema
        - Code is unique (not already assigned)

        Args:
            table_code: 6-character hexadecimal code to validate
            entity: Entity being validated

        Raises:
            ValueError: If validation fails
        """
        # Normalize to uppercase for consistency
        table_code = table_code.upper()

        # Format check: 6 hexadecimal characters
        if not re.match(r"^[0-9A-F]{6}$", table_code):
            raise ValueError(
                f"Invalid table code format: {table_code}. "
                f"Must be exactly 6 hexadecimal characters (0-9, A-F)."
            )

        # Parse components
        components = self.parser.parse_table_code_detailed(table_code)

        # Schema layer check
        schema_layers = self.registry.registry.get("schema_layers", {})
        if components.schema_layer not in schema_layers:
            raise ValueError(
                f"Invalid schema layer: {components.schema_layer}\n"
                f"Valid schema layers: {list(schema_layers.keys())}"
            )

        # Domain code check
        domains = self.registry.registry.get("domains", {})
        if components.domain_code not in domains:
            raise ValueError(
                f"Invalid domain code: {components.domain_code}\n"
                f"Valid domain codes: {list(domains.keys())}"
            )

        # Domain consistency check
        domain_info = domains[components.domain_code]
        if entity.schema != domain_info["name"] and entity.schema not in domain_info.get(
            "aliases", []
        ):
            raise ValueError(
                f"Table code domain '{domain_info['name']}' doesn't match "
                f"entity schema '{entity.schema}'"
            )

        # Uniqueness check (skip if entity already has this code in registry)
        registry_entry = self.registry.get_entity(entity.name)
        if registry_entry and registry_entry.table_code == table_code:
            # Entity already registered with this code - OK
            return

        if not self.registry.is_code_available(table_code):
            raise ValueError(f"Table code {table_code} already assigned to another entity")

    def derive_entity_code(self, entity_name: str) -> str:
        """
        Derive 3-character entity code from entity name

        Rules:
        1. Take first letter
        2. Take consonants (skip vowels and Y)
        3. If still < 3, add vowels
        4. If still < 3, pad with remaining letters

        Examples:
        - Contact → CON (C, N, T)
        - Manufacturer → MNF (M, N, F)
        - Task → TSK (T, S, K)
        - User → USR (U, S, R)

        Args:
            entity_name: Entity name

        Returns:
            3-character uppercase code
        """
        name_upper = entity_name.upper()

        # Build code starting with first letter
        code = name_upper[0] if len(name_upper) > 0 else ""

        # Extract consonants (excluding Y and first letter)
        consonants = [c for c in name_upper[1:] if c.isalpha() and c not in "AEIOUY"]

        # Add consonants
        for c in consonants:
            if len(code) >= 3:
                break
            code += c

        # Add vowels if needed
        if len(code) < 3:
            vowels = [c for c in name_upper[1:] if c in "AEIOUY"]
            for v in vowels:
                if len(code) >= 3:
                    break
                code += v

        # Pad with any remaining letters if still < 3
        if len(code) < 3:
            for c in name_upper[1:]:
                if len(code) >= 3:
                    break
                if c.isalpha() and c not in code:
                    code += c

        return code[:3].upper()

    def derive_function_code(self, table_code: str) -> str:
        """
        Derive function code from table code by changing schema layer to 03

        Args:
            table_code: Base table code (e.g., "012031")

        Returns:
            Function code with layer 03 (e.g., "032031")

        Example:
            table_code="012031" (write_side table) → "032031" (function)
        """
        if len(table_code) != 6:
            raise ValueError(f"Invalid table code format: {table_code}")

        # Replace schema layer (first 2 digits) with "03" (functions)
        return f"03{table_code[2:]}"

    def derive_view_code(self, table_code: str) -> str:
        """
        Derive view code from table code by changing schema layer to 02

        Args:
            table_code: Base table code (e.g., "012031")

        Returns:
            View code with layer 02 (e.g., "022031")

        Example:
            table_code="012031" (write_side table) → "022031" (read_side view)
        """
        if len(table_code) != 6:
            raise ValueError(f"Invalid table code format: {table_code}")

        # Replace schema layer (first 2 digits) with "02" (views)
        return f"02{table_code[2:]}"

    def generate_file_path(
        self,
        entity: Entity,
        table_code: str,
        file_type: str = "table",
        base_dir: str = "generated/migrations",
    ) -> str:
        """
        Generate hierarchical file path for entity

        Hierarchy:
        base_dir/
          SS_schema_layer/
            SSD_domain/
              SSDS_subdomain/
                SSDSE_entity_group/
                  SSDSEF_filename.ext

        Args:
            entity: Entity AST model
            table_code: 6-digit table code
            file_type: Type of file ('table', 'function', 'comment', 'test')
            base_dir: Base directory for generated files

        Returns:
            Complete file path

        Example:
            generate_file_path(contact, "012311", "table")
            → "generated/migrations/01_write_side/012_crm/0123_customer/01231_contact_group/012311_tb_contact.sql"
        """
        components = self.parser.parse_table_code_detailed(table_code)

        # Schema layer directory
        schema_layer_name = self.registry.registry["schema_layers"].get(
            components.schema_layer, f"schema_{components.schema_layer}"
        )
        schema_dir = f"{components.schema_layer}_{schema_layer_name}"

        # Domain directory
        domain_data = self.registry.registry["domains"].get(components.domain_code, {})
        domain_name = domain_data.get("name", f"domain_{components.domain_code}")
        domain_dir = f"{components.full_domain}_{domain_name}"

        # Subdomain directory (2 digits)
        subdomain_code = f"{components.entity_group}{components.entity_code}"[:2]
        subdomain_data = domain_data.get("subdomains", {}).get(subdomain_code, {})
        subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code}")
        subdomain_dir = f"{components.full_domain}{subdomain_code}_{subdomain_name}"

        # Entity group directory
        entity_lower = entity.name.lower()
        entity_group_code = f"{components.full_domain}{subdomain_code}{components.entity_code}"
        entity_group_dir = f"{entity_group_code}_{entity_lower}_group"

        # File name
        file_extensions = {
            "table": "sql",
            "function": "sql",
            "comment": "sql",
            "test": "sql",
            "yaml": "yaml",
            "json": "json",
        }
        ext = file_extensions.get(file_type, "sql")

        file_prefixes = {
            "table": f"tb_{entity_lower}",
            "function": f"fn_{entity_lower}",
            "comment": f"comments_{entity_lower}",
            "test": f"test_{entity_lower}",
            "yaml": entity_lower,
            "json": entity_lower,
        }
        filename = file_prefixes.get(file_type, entity_lower)

        # Complete path
        return str(
            Path(base_dir)
            / schema_dir
            / domain_dir
            / subdomain_dir
            / entity_group_dir
            / f"{table_code}_{filename}.{ext}"
        )

    def register_entity_auto(self, entity: Entity, table_code: str):
        """
        Automatically register entity in registry after generation

        Args:
            entity: Entity AST model
            table_code: Assigned table code

        Raises:
            ValueError: If table code is invalid
        """
        components = self.parser.parse_table_code_detailed(table_code)
        entity_code = self.derive_entity_code(entity.name)

        # Subdomain code is 2 digits
        subdomain_code = f"{components.entity_group}{components.entity_code}"[:2]

        self.registry.register_entity(
            entity_name=entity.name,
            table_code=table_code,
            entity_code=entity_code,
            domain_code=components.domain_code,
            subdomain_code=subdomain_code,
        )

    def get_all_entities(self) -> list[EntityRegistryEntry]:
        """
        Get all registered entities

        Returns:
            List of all registered entities
        """
        return list(self.registry.entities_index.values())

    def get_entities_by_domain(self, domain_name: str) -> list[EntityRegistryEntry]:
        """
        Get all entities in a domain

        Args:
            domain_name: Domain name (e.g., "crm", "catalog")

        Returns:
            List of entities in the domain
        """
        return [
            entry for entry in self.registry.entities_index.values() if entry.domain == domain_name
        ]

    def get_entities_by_subdomain(
        self, domain_name: str, subdomain_name: str
    ) -> list[EntityRegistryEntry]:
        """
        Get all entities in a subdomain

        Args:
            domain_name: Domain name
            subdomain_name: Subdomain name

        Returns:
            List of entities in the subdomain
        """
        return [
            entry
            for entry in self.registry.entities_index.values()
            if entry.domain == domain_name and entry.subdomain == subdomain_name
        ]
