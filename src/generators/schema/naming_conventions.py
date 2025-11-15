"""
Naming Conventions - Now uses Repository Pattern

BEFORE: Direct YAML access
AFTER: Uses DomainRepository abstraction
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from src.core.ast_models import Entity
from src.numbering.numbering_parser import NumberingParser
from src.domain.repositories.domain_repository import DomainRepository


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
class ReadEntityRegistryEntry:
    """Read-side entity entry in registry"""

    entity_name: str
    code: str  # 8-digit read-side code (e.g., "0220130")
    entity_number: int  # Entity sequence number (1-9)
    view_type: str  # 'v_', 'tv_', 'mv_'
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
    next_read_entity: int = 1  # Independent read-side sequence
    read_entities: dict[str, dict] = field(default_factory=dict)  # Read-side entities
    next_function_sequence: dict[str, int] = field(default_factory=dict)  # Per-entity function counter
    next_table_file_sequence: dict[str, int] = field(default_factory=dict)  # Per-entity table file counter


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
        self.read_entities_index: dict[str, ReadEntityRegistryEntry] = {}
        # Caches for performance
        self._domain_mapping_cache: dict[str, dict] | None = None
        self._subdomain_mapping_cache: dict[str, dict[str, dict]] = {}
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

        # Clear caches when reloading
        self._domain_mapping_cache = None
        self._subdomain_mapping_cache = {}

        # Build entity index for quick lookup
        self._build_entity_index()

    def _build_entity_index(self):
        """Build index of all registered entities for O(1) lookup"""
        self.entities_index = {}
        self.read_entities_index = {}

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

                # Build read entities index
                read_entities = subdomain.get("read_entities") or {}
                for entity_name, entity_data in read_entities.items():
                    self.read_entities_index[entity_name.lower()] = ReadEntityRegistryEntry(
                        entity_name=entity_name,
                        code=entity_data["code"],
                        entity_number=entity_data["entity_number"],
                        view_type=entity_data["view_type"],
                        assigned_at=entity_data["assigned_at"],
                        subdomain=subdomain_name,
                        domain=domain_name,
                    )

    def get_entity(self, entity_name: str) -> EntityRegistryEntry | None:
        """
        Get entity from registry by name (case-insensitive)

        Args:
            entity_name: Entity name (case-insensitive)

        Returns:
            EntityRegistryEntry if found, None otherwise
        """
        return self.entities_index.get(entity_name.lower())

    def get_read_entity(self, domain_name: str, subdomain_name: str, entity_name: str) -> ReadEntityRegistryEntry | None:
        """
        Get read-side entity from registry by domain, subdomain, and name

        Args:
            domain_name: Domain name
            subdomain_name: Subdomain name
            entity_name: Entity name (case-insensitive)

        Returns:
            ReadEntityRegistryEntry if found, None otherwise
        """
        entry = self.read_entities_index.get(entity_name.lower())
        if entry and entry.domain == domain_name and entry.subdomain == subdomain_name:
            return entry
        return None

    def assign_write_entity_code(self, domain_name: str, subdomain_name: str, entity_name: str) -> str:
        """
        Assign write-side entity code (for testing - simulates existing logic)

        Args:
            domain_name: Domain name
            subdomain_name: Subdomain name
            entity_name: Entity name

        Returns:
            Assigned write-side code
        """
        # Get domain and subdomain codes
        domain_info = self.get_domain(domain_name)
        if not domain_info:
            raise ValueError(f"Domain {domain_name} not found")

        subdomain_info = self.get_subdomain(domain_info.domain_code, subdomain_name)
        if not subdomain_info:
            raise ValueError(f"Subdomain {subdomain_name} not found in domain {domain_name}")

        # Get next sequence
        entity_sequence = subdomain_info.next_entity_sequence

        # Build write-side code: 01 + domain + subdomain + entity + file
        code = f"01{domain_info.domain_code}{subdomain_info.subdomain_code}{entity_sequence}1"

        # Register the entity
        self.register_entity(
            entity_name=entity_name,
            table_code=code,
            entity_code=self._derive_entity_code(entity_name),
            domain_code=domain_info.domain_code,
            subdomain_code=subdomain_info.subdomain_code,
        )

        return code

    def _derive_entity_code(self, entity_name: str) -> str:
        """Simple entity code derivation for testing"""
        return entity_name[:3].upper()

    def assign_read_entity_code(self, domain_name: str, subdomain_name: str, entity_name: str) -> str:
        """
        Assign read-side entity code independently from write-side

        Args:
            domain_name: Domain name
            subdomain_name: Subdomain name
            entity_name: Entity name (e.g., "tv_contact")

        Returns:
            Assigned 8-digit read-side code (e.g., "0220130")
        """
        # Get domain and subdomain codes
        domain_info = self.get_domain(domain_name)
        if not domain_info:
            raise ValueError(f"Domain {domain_name} not found")

        subdomain_info = self.get_subdomain(domain_info.domain_code, subdomain_name)
        if not subdomain_info:
            raise ValueError(f"Subdomain {subdomain_name} not found in domain {domain_name}")

        # Check if already assigned
        existing = self.get_read_entity(domain_name, subdomain_name, entity_name)
        if existing:
            return existing.code

        # Get next read-side entity sequence (independent from write-side)
        entity_number = subdomain_info.next_read_entity

        # Validate entity number range (0-9)
        if entity_number < 0 or entity_number > 9:
            raise ValueError(f"Entity number {entity_number} out of range (0-9) for subdomain {subdomain_name}")

        # Build read-side code: 02 + domain + subdomain + entity + file
        code = f"02{domain_info.domain_code}{subdomain_info.subdomain_code}{entity_number}0"

        # Register the read-side entity
        self._register_read_entity(
            entity_name=entity_name,
            code=code,
            entity_number=entity_number,
            view_type=self._determine_view_type(entity_name),
            domain_code=domain_info.domain_code,
            subdomain_code=subdomain_info.subdomain_code,
        )

        return code

    def _determine_view_type(self, entity_name: str) -> str:
        """Determine view type from entity name"""
        if entity_name.startswith("tv_"):
            return "tv_"
        elif entity_name.startswith("v_"):
            return "v_"
        elif entity_name.startswith("mv_"):
            return "mv_"
        else:
            return "v_"  # Default

    def _register_read_entity(
        self,
        entity_name: str,
        code: str,
        entity_number: int,
        view_type: str,
        domain_code: str,
        subdomain_code: str,
    ):
        """
        Register read-side entity in registry and save to file
        """
        # Add to in-memory registry
        subdomain = self.registry["domains"][domain_code]["subdomains"][subdomain_code]

        # Ensure read_entities exists
        if "read_entities" not in subdomain:
            subdomain["read_entities"] = {}

        subdomain["read_entities"][entity_name] = {
            "code": code,
            "entity_number": entity_number,
            "view_type": view_type,
            "assigned_at": datetime.now().isoformat(),
        }

        # Increment next_read_entity
        subdomain["next_read_entity"] = entity_number + 1

        # Update last_updated
        self.registry["last_updated"] = datetime.now().isoformat()

        # Save to file
        self.save()

        # Rebuild index
        self._build_entity_index()

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
                next_read_entity=subdomain_data.get("next_read_entity", 1),
                read_entities=subdomain_data.get("read_entities", {}),
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

    def load_domain_mapping(self) -> dict[str, dict]:
        """
        Load domain mapping from registry for fast lookups

        Returns:
            Dictionary mapping domain codes/names to domain info
        """
        if self._domain_mapping_cache is not None:
            return self._domain_mapping_cache

        mapping = {}

        for domain_code, domain_data in self.registry.get("domains", {}).items():
            domain_name = domain_data["name"]
            aliases = domain_data.get("aliases", [])

            # Map by code
            mapping[domain_code] = {
                "code": domain_code,
                "name": domain_name,
                "description": domain_data["description"],
                "aliases": aliases,
                "multi_tenant": domain_data.get("multi_tenant", False)
            }

            # Map by name
            mapping[domain_name] = mapping[domain_code]

            # Map by aliases
            for alias in aliases:
                mapping[alias] = mapping[domain_code]

        self._domain_mapping_cache = mapping
        return mapping

    def load_subdomain_mapping(self, domain_identifier: str) -> dict[str, dict]:
        """
        Load subdomain mapping for a specific domain from registry

        Args:
            domain_identifier: Domain code, name, or alias

        Returns:
            Dictionary mapping subdomain codes/names to subdomain info
        """
        if domain_identifier in self._subdomain_mapping_cache:
            return self._subdomain_mapping_cache[domain_identifier]

        # Get domain info
        domain_info = self.get_domain(domain_identifier)
        if not domain_info:
            return {}

        mapping = {}

        for subdomain_code, subdomain_data in domain_info.subdomains.items():
            subdomain_name = subdomain_data.subdomain_name

            mapping[subdomain_code] = {
                "code": subdomain_code,
                "name": subdomain_name,
                "description": subdomain_data.description,
                "next_entity_sequence": subdomain_data.next_entity_sequence,
                "next_read_entity": subdomain_data.next_read_entity
            }

            # Also map by name
            mapping[subdomain_name] = mapping[subdomain_code]

        self._subdomain_mapping_cache[domain_identifier] = mapping
        return mapping

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
            table_code: 7-digit table code to check

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

    def assign_read_file_code(self, domain_name: str, subdomain_name: str, entity_name: str, file_num: int) -> str:
        """
        Assign read-side file code for additional files within same entity

        Args:
            domain_name: Domain name
            subdomain_name: Subdomain name
            entity_name: Entity name
            file_num: File number (0, 1, 2, ...)

        Returns:
            Assigned 7-digit read-side code
        """
        # Get existing entity
        existing = self.get_read_entity(domain_name, subdomain_name, entity_name)
        if not existing:
            # First file - assign entity code
            return self.assign_read_entity_code(domain_name, subdomain_name, entity_name)

        # Additional file - use same entity number but different file number
        domain_info = self.get_domain(domain_name)
        if not domain_info:
            raise ValueError(f"Domain {domain_name} not found")

        subdomain_info = self.get_subdomain(domain_info.domain_code, subdomain_name)
        if not subdomain_info:
            raise ValueError(f"Subdomain {subdomain_name} not found in domain {domain_name}")

        # Validate file number range (0-9)
        if file_num < 0 or file_num > 9:
            raise ValueError(f"File number {file_num} out of range (0-9)")

        code = f"02{domain_info.domain_code}{subdomain_info.subdomain_code}{existing.entity_number}{file_num}"

        # Register additional file
        subdomain = self.registry["domains"][domain_info.domain_code]["subdomains"][subdomain_info.subdomain_code]
        entity_data = subdomain["read_entities"][entity_name]

        # Ensure files list exists
        if "files" not in entity_data:
            entity_data["files"] = []

        entity_data["files"].append({
            "code": code,
            "type": existing.view_type,
            "name": entity_name,
            "file_num": file_num,
        })

        # Save and rebuild
        self.save()
        self._build_entity_index()

        return code

    def validate_read_code_format(self, code: str) -> bool:
        """
        Validate read-side code format

        Args:
            code: 7-digit code to validate

        Returns:
            True if valid format
        """
        if len(code) != 7:
            return False

        # Format: 0SDSSEV
        # 0: always 0
        # S: schema layer (2 for read-side)
        # D: domain code (1 digit)
        # SS: subdomain code (2 digits)
        # E: entity number (1 digit)
        # V: file number (1 digit)

        try:
            schema_prefix = code[0]
            layer = code[1]
            domain = code[2]
            subdomain = code[3:5]
            entity = code[5]
            file_num = code[6]

            return (
                schema_prefix == "0" and
                layer == "2" and  # Read-side
                domain.isdigit() and len(domain) == 1 and
                subdomain.isdigit() and len(subdomain) == 2 and
                entity.isdigit() and len(entity) == 1 and
                file_num.isdigit() and len(file_num) == 1
            )
        except (IndexError, ValueError):
            return False

    def force_assign_read_code(self, code: str, domain_name: str, subdomain_name: str, entity_name: str):
        """
        Force assign a specific read-side code (for testing conflicts)

        Args:
            code: Code to assign
            domain_name: Domain name
            subdomain_name: Subdomain name
            entity_name: Entity name
        """
        domain_info = self.get_domain(domain_name)
        if not domain_info:
            raise ValueError(f"Domain {domain_name} not found")

        subdomain_info = self.get_subdomain(domain_info.domain_code, subdomain_name)
        if not subdomain_info:
            raise ValueError(f"Subdomain {subdomain_name} not found in domain {domain_name}")

        # Check for conflicts
        for existing_entity, existing_data in subdomain_info.read_entities.items():
            if existing_data.get("code") == code:
                raise ValueError(f"Code {code} already assigned to {existing_entity}")

        # Register
        entity_number = int(code[5])  # Extract entity number from 7-digit code (position 5)
        self._register_read_entity(
            entity_name=entity_name,
            code=code,
            entity_number=entity_number,
            view_type=self._determine_view_type(entity_name),
            domain_code=domain_info.domain_code,
            subdomain_code=subdomain_info.subdomain_code,
        )

    def assign_function_code(
        self,
        domain_name: str,
        subdomain_name: str,
        entity_name: str,
        action_name: str
    ) -> str:
        """
        Assign function code for an action

        Args:
            domain_name: Domain name
            subdomain_name: Subdomain name
            entity_name: Entity name
            action_name: Action name (e.g., "create_contact")

        Returns:
            7-digit function code (e.g., "0323611")
        """
        # Get entity info
        entity_entry = self.get_entity(entity_name)
        if not entity_entry:
            raise ValueError(f"Entity {entity_name} not registered")

        # Get base table code (7 digits)
        base_code = entity_entry.table_code

        # Get subdomain info
        domain_info = self.get_domain(domain_name)
        if not domain_info:
            raise ValueError(f"Domain {domain_name} not found")

        subdomain_info = self.get_subdomain(domain_info.domain_code, subdomain_name)
        if not subdomain_info:
            raise ValueError(f"Subdomain {subdomain_name} not found in domain {domain_name}")

        # Update registry dictionary directly
        subdomain_dict = self.registry["domains"][domain_info.domain_code]["subdomains"][subdomain_info.subdomain_code]

        # Ensure next_function_sequence exists
        if "next_function_sequence" not in subdomain_dict:
            subdomain_dict["next_function_sequence"] = {}

        entity_key = entity_name.lower()

        if entity_key not in subdomain_dict["next_function_sequence"]:
            subdomain_dict["next_function_sequence"][entity_key] = 1

        function_seq = subdomain_dict["next_function_sequence"][entity_key]

        # Build 7-digit function code: 03 + domain/subdomain/entity + function_seq
        function_code = f"03{base_code[2:6]}{function_seq}"

        # Increment sequence
        subdomain_dict["next_function_sequence"][entity_key] += 1

        # Update last_updated
        self.registry["last_updated"] = datetime.now().isoformat()

        # Save registry
        self.save()

        return function_code

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
    """Naming conventions for generated SQL"""

    def __init__(self, domain_repository: DomainRepository | None = None):
        # Use provided repository or get from config
        if domain_repository is None:
            from src.core.config import get_config
            config = get_config()
            domain_repository = config.get_domain_repository()

        self.domain_repository = domain_repository
        self.parser = NumberingParser()

    def get_table_code(self, domain: str, subdomain: str, entity: str) -> str:
        """Get 6-digit table code"""
        domain_obj = self.domain_repository.find_by_name(domain)
        if not domain_obj:
            raise ValueError(f"Domain {domain} not found")

        # Business logic now lives in domain entity
        return str(domain_obj.allocate_entity_code(subdomain, entity))

    def derive_table_code(
        self, entity: Entity, schema_layer: str = "01", subdomain: str | None = None
    ) -> str:
        """
        Automatically derive table code from entity

        Table Code Format: SDSEX (6 digits)
        - SS: Schema layer (01=write_side, 02=read_side, 03=analytics)
        - D:  Domain code (1-9)
        - S:  Subdomain code (0-9)
        - E:  Entity sequence (1-9)
        - X:  File sequence (1=main table, 2=audit, 3=info, etc.)

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

        # Build table code: SDSEX (6 digits total)
        # Format: schema_layer (2) + domain (1) + subdomain (1) + entity_seq (1) + file_seq (1)
        # Note: subdomain_code is now 1 digit (e.g., "3")
        table_code = f"{schema_layer}{domain_code}{subdomain_code}{entity_sequence % 10}1"

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

    def validate_table_code(self, table_code: str, entity: Entity, skip_uniqueness: bool = False):
        """
        Validate table code format and consistency

        Checks:
        - Format: exactly 6 decimal digits
        - Schema layer exists
        - Domain code exists and matches entity.schema
        - Code is unique (not already assigned) - unless skip_uniqueness=True

        Args:
            table_code: 6-digit decimal code to validate
            entity: Entity being validated
            skip_uniqueness: If True, skip uniqueness validation (for explicit codes)

        Raises:
            ValueError: If validation fails
        """
        # Format check: exactly 6 hexadecimal digits
        if not re.match(r"^[0-9a-fA-F]{6}$", table_code):
            raise ValueError(
                f"Invalid table code format: {table_code}. "
                f"Must be exactly 6 hexadecimal digits (0-9, a-f, A-F)."
            )

        # For explicit codes, trust the user - only check format
        if skip_uniqueness:
            return  # Skip all structural validation for external table codes

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

        # Uniqueness check
        if not skip_uniqueness:
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

    def derive_function_code(self, table_code: str, function_seq: int = 1) -> str:
        """
        Derive function code from table code by changing schema layer to 03

        Args:
            table_code: Base table code (6 digits, e.g., "012361")
            function_seq: Function sequence within entity (1-9, default: 1)

        Returns:
            6-digit function code (e.g., "032361", "032362")

        Examples:
            derive_function_code("012361", 1)  # First function → "032361"
            derive_function_code("012361", 2)  # Second function → "032362"
        """
        if len(table_code) != 6:
            raise ValueError(f"Table code must be 6 digits, got: {table_code}")

        # Validate function sequence
        if function_seq < 1 or function_seq > 9:
            raise ValueError(f"Function sequence must be 1-9, got: {function_seq}")

        # Build 6-digit function code: 03 + domain/subdomain/entity + function_seq
        return f"03{table_code[2:5]}{function_seq}"

    def derive_table_file_code(self, table_code: str, file_seq: int = 1) -> str:
        """
        Generate 6-digit code for additional table files (audit, info, node, etc.)

        Args:
            table_code: Base table code (6 digits, e.g., "012361")
            file_seq: File sequence within entity (1-9, default: 1)

        Returns:
            6-digit table file code

        Examples:
            derive_table_file_code("012361", 1)  # Main table → "012361"
            derive_table_file_code("012361", 2)  # Audit table → "012362"
            derive_table_file_code("012361", 3)  # Info table → "012363"
        """
        if len(table_code) != 6:
            raise ValueError(f"Table code must be 6 digits, got: {table_code}")

        # Validate file sequence
        if file_seq < 1 or file_seq > 9:
            raise ValueError(f"File sequence must be 1-9, got: {file_seq}")

        # Build 6-digit code: base_code + file_seq
        return f"{table_code[:5]}{file_seq}"

    def derive_view_code(self, table_code: str) -> str:
        """
        Derive view code from table code by changing schema layer to 02

        Args:
            table_code: Table code (6 digits, e.g., "012311")

        Returns:
            View code with layer 02 (6 digits, e.g., "022310")

        Example:
            table_code="012311" (write_side table) → "022310" (read_side view)
        """
        if len(table_code) != 6:
            raise ValueError(f"Table code must be 6 digits, got: {table_code}")

        # Replace schema layer (first 2 digits) with "02" (views)
        # Keep domain, subdomain, and entity info, add "0" as the view sequence
        return f"02{table_code[2:5]}0"

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
                SSDSE_entity/              ← No _group suffix, snake_case
                  SSDSEF_filename.ext

        Args:
            entity: Entity AST model
            table_code: 6-digit table code
            file_type: Type of file ('table', 'function', 'comment', 'test')
            base_dir: Base directory for generated files

        Returns:
            Complete file path with snake_case entity names

        Example:
            generate_file_path(ColorMode, "013111", "table")
            → "generated/01_write_side/013_catalog/0131_classification/01311_color_mode/013111_tb_color_mode.sql"
        """
        from src.generators.naming_utils import camel_to_snake

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

        # Subdomain directory - FIXED: use single-digit subdomain_code from table code
        # Table code format: SSDSSE (schema_layer + domain + subdomain + entity_sequence + file_sequence)
        # Subdomain is single digit in table code, but registry uses 2-digit codes with leading zero
        subdomain_code = components.subdomain_code  # Single digit (e.g., "1")
        subdomain_code_padded = subdomain_code.zfill(2)  # Padded to 2 digits (e.g., "01")

        # Look up subdomain name from registry
        subdomain_data = domain_data.get("subdomains", {}).get(subdomain_code_padded, {})
        subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code_padded}")

        # Build 4-digit subdomain directory code: schema_layer + domain + subdomain
        # Example: "0131" for schema 01, domain 3, subdomain 1
        subdomain_dir_code = f"{components.schema_layer}{components.domain_code}{subdomain_code}"
        subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"

        # Entity directory - CHANGED: snake_case, no _group suffix
        entity_snake = camel_to_snake(entity.name)  # ColorMode → color_mode
        entity_dir_code = f"{subdomain_dir_code}{components.entity_sequence}"
        entity_dir = f"{entity_dir_code}_{entity_snake}"  # 01311_color_mode (no _group)

        # File name - CHANGED: use snake_case
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
            "table": f"tb_{entity_snake}",  # tb_color_mode
            "function": f"fn_{entity_snake}",  # fn_color_mode
            "comment": f"comments_{entity_snake}",
            "test": f"test_{entity_snake}",
            "yaml": entity_snake,
            "json": entity_snake,
        }
        filename = file_prefixes.get(file_type, entity_snake)

        # Complete path
        return str(
            Path(base_dir)
            / schema_dir
            / domain_dir
            / subdomain_dir
            / entity_dir  # Changed: no _group, snake_case
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

        # FIXED: Use single-digit subdomain_code
        subdomain_code = components.subdomain_code  # ← Now correct

        # Registry uses 2-digit codes with leading zero
        subdomain_code_padded = subdomain_code.zfill(2)

        # Validate subdomain exists in registry
        domain_data = self.registry.registry["domains"].get(components.domain_code)
        if not domain_data:
            raise ValueError(f"Domain {components.domain_code} not found in registry")

        if subdomain_code_padded not in domain_data.get("subdomains", {}):
            raise ValueError(
                f"Subdomain {subdomain_code_padded} not found in domain {components.domain_code}. "
                f"Available: {list(domain_data.get('subdomains', {}).keys())}"
            )

        self.registry.register_entity(
            entity_name=entity.name,
            table_code=table_code,
            entity_code=entity_code,
            domain_code=components.domain_code,
            subdomain_code=subdomain_code_padded,
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
