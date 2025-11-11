# Naming Conventions & Registry System - Implementation Plan

**Status**: Planning Phase
**Timeline**: Week 1.5 (7-10 days, before Team T starts)
**Priority**: **CRITICAL** - Blocks testing infrastructure
**Team Size**: 1-2 developers

---

## 🎯 Mission

**Implement automatic table code assignment, validation, and registry management with subdomain/entity organization for efficient DDL file hierarchy.**

This system provides:
1. **Automatic table code derivation** - No manual numbering required
2. **Validation and uniqueness checks** - Prevent conflicts
3. **Central registry** - Single source of truth for all entity codes
4. **Hierarchical file organization** - Efficient DDL file structure
5. **Subdomain management** - Logical grouping of related entities

---

## 🚨 Why This is Critical

### Current Problem
```yaml
# contact.yaml
entity: Contact
schema: crm
# Missing: organization.table_code
```

**Current behavior**:
- Falls back to `entity.name[:3].upper()` → `"CON"` (3 chars, not 6-digit code)
- Breaks UUID encoding for testing (needs 6-digit code)
- No validation, no uniqueness checks
- No organization structure for DDL files

### After Implementation
```yaml
# Option 1: Manual (explicit control)
entity: Contact
schema: crm
organization:
  table_code: "012321"  # Validated, checked for uniqueness
  subdomain: "customer"

# Option 2: Automatic (lightweight)
entity: Contact
schema: crm
# Auto-assigned: 012321 (based on schema + subdomain + entity)
```

**New behavior**:
- ✅ Automatic table code assignment following SSDGGE pattern
- ✅ Validation of format, uniqueness, schema consistency
- ✅ Central registry tracks all assignments
- ✅ Hierarchical DDL organization: `01_write_side/012_crm/0123_customer/01232_contact/`
- ✅ UUID encoding works: `01232122-3201-0001-0001-000000000001`

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  SpecQL YAML                                                 │
│  - Entity name: "Contact"                                   │
│  - Schema: "crm"                                            │
│  - Subdomain: "customer" (optional)                         │
│  - Manual table_code (optional)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Domain Registry (YAML/JSON)                                │
│  - Domains defined: core, management, catalog, crm, etc.   │
│  - Subdomains defined: customer, product, inventory, etc.  │
│  - Entity assignments tracked                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  NamingConventions Module                                   │
│  ├─ derive_table_code()     - Auto-generate if missing     │
│  ├─ validate_table_code()   - Check format & consistency   │
│  ├─ check_uniqueness()      - Prevent duplicates           │
│  ├─ assign_subdomain()      - Infer or assign subdomain    │
│  └─ generate_file_path()    - Hierarchical DDL path        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Entity with Complete Metadata                              │
│  - table_code: "012321"                                     │
│  - entity_code: "CON"                                       │
│  - subdomain: "customer"                                    │
│  - file_path: "01_write_side/012_crm/0123_customer/..."   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Table Code Format (SSDGGE)

### Existing Format (from numbering_parser.py)
```
SSDGGE (6 digits)
│││││└─ E: File sequence (1-9)
││││└── E: Entity code (0-9) - UNUSED, merge with Group
│││└─── G: Entity group (0-9)
││└──── D: Domain code (1-9)
└└───── SS: Schema layer (01=write_side, 02=read_side, 03=analytics)
```

### **PROPOSED: Refined Format (SSDSSE)**
```
SSDSSE (6 digits)
│││││└─ E: Entity sequence (0-9)
││││└── S: Subdomain code (0-9)
│││└─── S: Subdomain code (0-9) - TWO DIGITS for subdomain
││└──── D: Domain code (1-9)
└└───── SS: Schema layer (01=write_side, 02=read_side, 03=analytics)

Example Breakdown:
012321
││││││
││││└└─ 21: Entity sequence #21 in subdomain
│││└─── 3: Subdomain "customer" (crm has subdomains: 1=core, 2=sales, 3=customer, 4=support)
││└──── 2: Domain "crm" (2=crm/management)
└└───── 01: Schema layer "write_side"

Result: Table in write_side, crm domain, customer subdomain, entity #21
Path: 01_write_side/012_crm/0123_customer/01232_contact_group/012321_tb_contact.sql
```

---

## 📁 Hierarchical File Organization

### Current (PrintOptim Backend Reference)
```
db/0_schema/01_write_side/013_catalog/
├── 0131_classification/
│   ├── 01311_generic_model/
│   │   └── 013111_tb_generic_model.sql
│   └── 01312_model_category/
│       └── 013121_tb_model_category.sql
├── 0132_manufacturer/
│   ├── 01321_manufacturer/
│   │   └── 013211_tb_manufacturer.sql
│   └── 01322_manufacturer_range/
│       └── 013221_tb_manufacturer_range.sql
└── 0133_financing/
    └── 01331_financing_type/
        └── 013311_tb_financing_type.sql
```

**Pattern**:
- `SS_schema_layer/` (e.g., `01_write_side/`)
- `SSD_domain/` (e.g., `013_catalog/`)
- `SSDS_subdomain/` (e.g., `0132_manufacturer/`)
- `SSDSE_entity_group/` (e.g., `01321_manufacturer/`)
- `SSDSEF_file.sql` (e.g., `013211_tb_manufacturer.sql`)

### Proposed (SpecQL)
```
generated/
├── migrations/
│   ├── 01_write_side/
│   │   ├── 012_crm/
│   │   │   ├── 0123_customer/
│   │   │   │   ├── 01232_contact_group/
│   │   │   │   │   ├── 012321_tb_contact.sql
│   │   │   │   │   ├── 012321_app_create_contact.sql
│   │   │   │   │   └── 012321_fraiseql_comments.sql
│   │   │   │   └── 01233_company_group/
│   │   │   │       └── 012331_tb_company.sql
│   │   │   ├── 0124_sales/
│   │   │   │   └── 01241_opportunity/
│   │   │   │       └── 012411_tb_opportunity.sql
│   │   │   └── manifest.json  # Execution order
│   │   └── 013_catalog/
│   │       ├── 0132_manufacturer/
│   │       │   └── 01321_manufacturer/
│   │       │       └── 013211_tb_manufacturer.sql
│   │       └── 0133_product/
│   │           └── 01331_product/
│   │               └── 013311_tb_product.sql
│   └── manifest.json  # Global execution order
```

---

## 📦 Component 1: Domain Registry

**File**: `registry/domain_registry.yaml`

### Registry Structure
```yaml
# Domain Registry - Central source of truth for numbering
version: "1.0.0"
last_updated: "2025-11-08"

# Schema layers (fixed)
schema_layers:
  "01": write_side
  "02": read_side
  "03": analytics

# Domains (can be extended)
domains:
  "1":
    name: core
    description: "Core infrastructure (i18n, auth, events)"
    subdomains:
      "1":
        name: i18n
        description: "Internationalization"
        next_entity_sequence: 1
      "2":
        name: auth
        description: "Authentication & authorization"
        next_entity_sequence: 1
      "3":
        name: events
        description: "Event system"
        next_entity_sequence: 1

  "2":
    name: crm
    description: "Customer relationship management & organizational structure"
    aliases: ["management"]  # Also known as management
    subdomains:
      "1":
        name: core
        description: "Core organization entities"
        next_entity_sequence: 1
      "2":
        name: sales
        description: "Sales-related entities"
        next_entity_sequence: 1
      "3":
        name: customer
        description: "Customer contact entities"
        next_entity_sequence: 1
        entities:
          contact:
            table_code: "012321"
            entity_code: "CON"
            assigned_at: "2025-11-08"
          company:
            table_code: "012331"
            entity_code: "COM"
            assigned_at: "2025-11-08"
      "4":
        name: support
        description: "Customer support entities"
        next_entity_sequence: 1

  "3":
    name: catalog
    description: "Product catalog & manufacturer data"
    subdomains:
      "1":
        name: classification
        description: "Product classification & categories"
        next_entity_sequence: 1
      "2":
        name: manufacturer
        description: "Manufacturer-related entities"
        next_entity_sequence: 2  # manufacturer is 01321, next would be 01322
        entities:
          manufacturer:
            table_code: "013211"
            entity_code: "MAN"
            assigned_at: "2025-11-08"
      "3":
        name: product
        description: "Product entities"
        next_entity_sequence: 1
      "4":
        name: generic
        description: "Generic product data"
        next_entity_sequence: 1

  "4":
    name: projects
    description: "Project management entities"
    aliases: ["tenant"]
    subdomains:
      "1":
        name: core
        description: "Core project entities"
        next_entity_sequence: 1
        entities:
          task:
            table_code: "014111"
            entity_code: "TSK"
            assigned_at: "2025-11-08"

# Reserved codes (cannot be auto-assigned)
reserved_codes:
  - "000000"  # Invalid
  - "999999"  # Reserved for future use

# Validation rules
validation:
  enforce_uniqueness: true
  allow_manual_override: true
  require_subdomain: false  # Optional for simple entities
```

---

## 📦 Component 2: Naming Conventions Module

**File**: `src/generators/schema/naming_conventions.py`

### Core Functions

```python
"""
Naming Conventions & Table Code Management
Provides automatic table code derivation, validation, and registry integration
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import yaml
import re

from src.core.ast_models import Entity, Organization
from src.numbering.numbering_parser import NumberingParser, TableCodeComponents


@dataclass
class DomainInfo:
    """Domain information from registry"""
    domain_code: str
    domain_name: str
    description: str
    subdomains: Dict[str, 'SubdomainInfo']
    aliases: List[str]


@dataclass
class SubdomainInfo:
    """Subdomain information from registry"""
    subdomain_code: str
    subdomain_name: str
    description: str
    next_entity_sequence: int
    entities: Dict[str, 'EntityRegistryEntry']


@dataclass
class EntityRegistryEntry:
    """Entity entry in registry"""
    entity_name: str
    table_code: str
    entity_code: str
    assigned_at: str
    subdomain: str
    domain: str


class DomainRegistry:
    """Load and manage domain registry"""

    def __init__(self, registry_path: str = "registry/domain_registry.yaml"):
        self.registry_path = Path(registry_path)
        self.registry: Dict = {}
        self.entities_index: Dict[str, EntityRegistryEntry] = {}
        self.load()

    def load(self):
        """Load registry from YAML"""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Domain registry not found: {self.registry_path}")

        with open(self.registry_path, 'r') as f:
            self.registry = yaml.safe_load(f)

        # Build entity index for quick lookup
        self._build_entity_index()

    def _build_entity_index(self):
        """Build index of all registered entities"""
        for domain_code, domain in self.registry.get('domains', {}).items():
            domain_name = domain['name']
            for subdomain_code, subdomain in domain.get('subdomains', {}).items():
                subdomain_name = subdomain['name']
                for entity_name, entity_data in subdomain.get('entities', {}).items():
                    self.entities_index[entity_name.lower()] = EntityRegistryEntry(
                        entity_name=entity_name,
                        table_code=entity_data['table_code'],
                        entity_code=entity_data['entity_code'],
                        assigned_at=entity_data['assigned_at'],
                        subdomain=subdomain_name,
                        domain=domain_name
                    )

    def get_entity(self, entity_name: str) -> Optional[EntityRegistryEntry]:
        """Get entity from registry by name"""
        return self.entities_index.get(entity_name.lower())

    def get_domain(self, domain_identifier: str) -> Optional[DomainInfo]:
        """Get domain by code or name"""
        # Try by code first
        if domain_identifier in self.registry.get('domains', {}):
            domain_data = self.registry['domains'][domain_identifier]
            return DomainInfo(
                domain_code=domain_identifier,
                domain_name=domain_data['name'],
                description=domain_data['description'],
                subdomains={},  # TODO: populate
                aliases=domain_data.get('aliases', [])
            )

        # Try by name or alias
        for code, domain_data in self.registry.get('domains', {}).items():
            if domain_data['name'] == domain_identifier:
                return self.get_domain(code)
            if domain_identifier in domain_data.get('aliases', []):
                return self.get_domain(code)

        return None

    def get_next_entity_sequence(self, domain_code: str, subdomain_code: str) -> int:
        """Get next available entity sequence number for subdomain"""
        try:
            return self.registry['domains'][domain_code]['subdomains'][subdomain_code]['next_entity_sequence']
        except KeyError:
            raise ValueError(f"Subdomain {subdomain_code} not found in domain {domain_code}")

    def register_entity(
        self,
        entity_name: str,
        table_code: str,
        entity_code: str,
        domain_code: str,
        subdomain_code: str
    ):
        """Register new entity in registry and save"""
        from datetime import datetime

        # Add to in-memory registry
        if 'domains' not in self.registry:
            self.registry['domains'] = {}
        if domain_code not in self.registry['domains']:
            raise ValueError(f"Domain {domain_code} not found")
        if subdomain_code not in self.registry['domains'][domain_code]['subdomains']:
            raise ValueError(f"Subdomain {subdomain_code} not found in domain {domain_code}")

        subdomain = self.registry['domains'][domain_code]['subdomains'][subdomain_code]

        if 'entities' not in subdomain:
            subdomain['entities'] = {}

        subdomain['entities'][entity_name] = {
            'table_code': table_code,
            'entity_code': entity_code,
            'assigned_at': datetime.now().isoformat()
        }

        # Increment next_entity_sequence
        subdomain['next_entity_sequence'] += 1

        # Update last_updated
        self.registry['last_updated'] = datetime.now().isoformat()

        # Save to file
        self.save()

        # Rebuild index
        self._build_entity_index()

    def save(self):
        """Save registry to YAML"""
        with open(self.registry_path, 'w') as f:
            yaml.dump(self.registry, f, default_flow_style=False, sort_keys=False)

    def is_code_available(self, table_code: str) -> bool:
        """Check if table code is available (not already assigned)"""
        reserved = self.registry.get('reserved_codes', [])
        if table_code in reserved:
            return False

        # Check if any entity has this code
        for entity in self.entities_index.values():
            if entity.table_code == table_code:
                return False

        return True


class NamingConventions:
    """
    Naming conventions and table code management
    Provides automatic derivation, validation, and registry integration
    """

    def __init__(self, registry_path: str = "registry/domain_registry.yaml"):
        self.registry = DomainRegistry(registry_path)
        self.parser = NumberingParser()

    def get_table_code(self, entity: Entity) -> str:
        """
        Get table code for entity (manual or auto-derived)

        Priority:
        1. Manual specification in YAML (organization.table_code)
        2. Registry lookup (if entity previously registered)
        3. Automatic derivation

        Returns:
            6-digit table code string
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
        return self.derive_table_code(entity)

    def derive_table_code(
        self,
        entity: Entity,
        schema_layer: str = "01",  # Default: write_side
        subdomain: Optional[str] = None
    ) -> str:
        """
        Automatically derive table code from entity

        Args:
            entity: Entity AST model
            schema_layer: Schema layer code (01=write_side, 02=read_side, 03=analytics)
            subdomain: Subdomain name (if None, will try to infer)

        Returns:
            6-digit table code (SSDSSE format)
        """
        # Get domain code
        domain_info = self.registry.get_domain(entity.schema)
        if not domain_info:
            raise ValueError(f"Unknown domain/schema: {entity.schema}")

        domain_code = domain_info.domain_code

        # Get or infer subdomain
        if subdomain is None:
            subdomain = self._infer_subdomain(entity, domain_info)

        # Find subdomain code
        subdomain_code = None
        subdomain_info = None
        for code, subdom in domain_info.subdomains.items():
            if subdom['name'] == subdomain:
                subdomain_code = code
                subdomain_info = subdom
                break

        if not subdomain_code:
            raise ValueError(f"Subdomain '{subdomain}' not found in domain '{domain_info.domain_name}'")

        # Get next entity sequence
        entity_sequence = self.registry.get_next_entity_sequence(domain_code, subdomain_code)

        # Build table code: SSDSSE
        table_code = f"{schema_layer}{domain_code}{subdomain_code}{entity_sequence:02d}1"

        # Validate uniqueness
        if not self.registry.is_code_available(table_code):
            raise ValueError(f"Table code {table_code} already assigned")

        return table_code

    def _infer_subdomain(self, entity: Entity, domain_info: DomainInfo) -> str:
        """
        Infer subdomain from entity name/characteristics

        Heuristics:
        - CRM: contact/company → customer, opportunity → sales
        - Catalog: manufacturer/model → manufacturer, product → product
        - If unclear, use 'core' subdomain
        """
        entity_name_lower = entity.name.lower()

        # CRM heuristics
        if domain_info.domain_name in ['crm', 'management']:
            if entity_name_lower in ['contact', 'company', 'person']:
                return 'customer'
            elif entity_name_lower in ['opportunity', 'deal', 'quote']:
                return 'sales'
            elif entity_name_lower in ['ticket', 'case']:
                return 'support'
            else:
                return 'core'

        # Catalog heuristics
        elif domain_info.domain_name == 'catalog':
            if entity_name_lower in ['manufacturer', 'manufacturer_range', 'brand']:
                return 'manufacturer'
            elif entity_name_lower in ['product', 'sku', 'item']:
                return 'product'
            elif entity_name_lower in ['category', 'generic_model']:
                return 'classification'
            else:
                return 'core'

        # Default: core subdomain
        return 'core'

    def validate_table_code(self, table_code: str, entity: Entity):
        """
        Validate table code format and consistency

        Checks:
        - Format: exactly 6 digits
        - Schema layer exists
        - Domain code exists and matches entity.schema
        - Code is unique (not already assigned)
        """
        # Format check
        if not re.match(r'^\d{6}$', table_code):
            raise ValueError(f"Invalid table code format: {table_code}. Must be 6 digits.")

        # Parse components
        components = self.parser.parse_table_code_detailed(table_code)

        # Schema layer check
        if components.schema_layer not in self.registry.registry.get('schema_layers', {}):
            raise ValueError(f"Invalid schema layer: {components.schema_layer}")

        # Domain code check
        if components.domain_code not in self.registry.registry.get('domains', {}):
            raise ValueError(f"Invalid domain code: {components.domain_code}")

        # Domain consistency check
        domain_info = self.registry.registry['domains'][components.domain_code]
        if entity.schema != domain_info['name'] and entity.schema not in domain_info.get('aliases', []):
            raise ValueError(
                f"Table code domain '{domain_info['name']}' doesn't match entity schema '{entity.schema}'"
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
        - Take uppercase consonants first
        - If < 3, add uppercase vowels
        - If still < 3, pad with uppercase letters from start

        Examples:
        - Contact → CON (C, N, T)
        - Manufacturer → MNF (M, N, F)
        - Task → TSK (T, S, K)
        """
        name_upper = entity_name.upper()
        consonants = [c for c in name_upper if c.isalpha() and c not in 'AEIOUY']
        vowels = [c for c in name_upper if c in 'AEIOUY']

        code = ''

        # Start with consonants
        code += ''.join(consonants[:3])

        # Add vowels if needed
        if len(code) < 3:
            code += ''.join(vowels[:3 - len(code)])

        # Pad with letters from start if still < 3
        if len(code) < 3:
            all_letters = [c for c in name_upper if c.isalpha()]
            code += ''.join(all_letters[:3])

        return code[:3].upper()

    def generate_file_path(
        self,
        entity: Entity,
        table_code: str,
        file_type: str = "table"
    ) -> str:
        """
        Generate hierarchical file path for entity

        Args:
            entity: Entity AST model
            table_code: 6-digit table code
            file_type: Type of file ('table', 'function', 'comment', 'test')

        Returns:
            Complete file path following hierarchy

        Example:
            generate_file_path(contact_entity, "012321", "table")
            → "generated/migrations/01_write_side/012_crm/0123_customer/01232_contact_group/012321_tb_contact.sql"
        """
        components = self.parser.parse_table_code_detailed(table_code)

        # Schema layer directory
        schema_layer_name = self.registry.registry['schema_layers'].get(
            components.schema_layer,
            f"schema_{components.schema_layer}"
        )
        schema_dir = f"{components.schema_layer}_{schema_layer_name}"

        # Domain directory
        domain_info = self.registry.registry['domains'].get(components.domain_code, {})
        domain_name = domain_info.get('name', f"domain_{components.domain_code}")
        domain_dir = f"{components.full_domain}_{domain_name}"

        # Subdomain directory
        subdomain_code = components.subdomain_code  # Single digit
        subdomain_info = domain_info.get('subdomains', {}).get(subdomain_code, {})
        subdomain_name = subdomain_info.get('name', f"subdomain_{subdomain_code}")
        subdomain_dir = f"{components.full_domain}{subdomain_code}_{subdomain_name}"

        # Entity group directory
        entity_lower = entity.name.lower()
        entity_group_code = f"{components.full_domain}{subdomain_code}{components.entity_sequence}"
        entity_group_dir = f"{entity_group_code}_{entity_lower}_group"

        # File name
        file_extensions = {
            'table': 'sql',
            'function': 'sql',
            'comment': 'sql',
            'test': 'sql',
            'yaml': 'yaml'
        }
        ext = file_extensions.get(file_type, 'sql')

        file_prefixes = {
            'table': f'tb_{entity_lower}',
            'function': f'fn_{entity_lower}',
            'comment': f'comments_{entity_lower}',
            'test': f'test_{entity_lower}',
            'yaml': entity_lower
        }
        filename = file_prefixes.get(file_type, entity_lower)

        # Complete path
        return f"generated/migrations/{schema_dir}/{domain_dir}/{subdomain_dir}/{entity_group_dir}/{table_code}_{filename}.{ext}"

    def register_entity_auto(self, entity: Entity, table_code: str):
        """
        Automatically register entity in registry after generation

        Args:
            entity: Entity AST model
            table_code: Assigned table code
        """
        components = self.parser.parse_table_code_detailed(table_code)
        entity_code = self.derive_entity_code(entity.name)
        self.registry.register_entity(
            entity_name=entity.name,
            table_code=table_code,
            entity_code=entity_code,
            domain_code=components.domain_code,
            subdomain_code=components.subdomain_code
        )
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/schema/test_naming_conventions.py

def test_derive_entity_code():
    nc = NamingConventions()
    assert nc.derive_entity_code("Contact") == "CON"
    assert nc.derive_entity_code("Manufacturer") == "MNF"
    assert nc.derive_entity_code("Task") == "TSK"

def test_derive_table_code_crm_contact():
    nc = NamingConventions()
    entity = Entity(name="Contact", schema="crm")

    table_code = nc.derive_table_code(entity)

    # Should be: 01 (write_side) + 2 (crm) + 3 (customer subdomain) + 01 (first entity) + 1 (file seq)
    assert table_code == "012311"  # Depends on registry state

def test_validate_table_code_format():
    nc = NamingConventions()
    entity = Entity(name="Contact", schema="crm")

    # Valid
    nc.validate_table_code("012321", entity)

    # Invalid format
    with pytest.raises(ValueError, match="Must be 6 digits"):
        nc.validate_table_code("123", entity)

def test_validate_table_code_uniqueness():
    nc = NamingConventions()
    entity1 = Entity(name="Contact", schema="crm")
    entity2 = Entity(name="Company", schema="crm")

    # Assign code to entity1
    code = "012321"
    nc.register_entity_auto(entity1, code)

    # Try to use same code for entity2
    with pytest.raises(ValueError, match="already assigned"):
        nc.validate_table_code(code, entity2)
```

---

**Continue to Phase Implementation Details...**

*Due to length, I'll create this as a separate detailed document. Would you like me to continue with the full phased implementation plan (RED/GREEN/REFACTOR/QA cycles for each phase)?*
