# Naming Conventions & Registry - Phased Implementation Plan

**Timeline**: 7-10 days (Week 1.5, before Team T)
**TDD Discipline**: RED → GREEN → REFACTOR → QA for each phase

---

## 📅 Implementation Timeline

| Phase | Focus | Duration | Critical Path |
|-------|-------|----------|---------------|
| **Phase 1** | Domain Registry Schema | Day 1-2 | ✅ Foundation |
| **Phase 2** | DomainRegistry Class | Day 2-3 | ✅ Core |
| **Phase 3** | NamingConventions Module | Day 3-5 | ✅ Core |
| **Phase 4** | Generator Integration | Day 5-6 | Integration |
| **Phase 5** | CLI Commands | Day 6-7 | User Interface |
| **Phase 6** | Migration & Validation | Day 7-8 | Quality |
| **Phase 7** | Documentation & Examples | Day 8-10 | Polish |

---

## 🔴 Phase 1: Domain Registry Schema (Day 1-2)

**Objective**: Create domain registry YAML schema and initial data

### RED: Write Failing Test

```python
# tests/unit/registry/test_domain_registry.py

import pytest
from pathlib import Path
import yaml

def test_domain_registry_file_exists():
    """Domain registry YAML should exist"""
    registry_path = Path("registry/domain_registry.yaml")
    assert registry_path.exists(), "registry/domain_registry.yaml not found"

def test_domain_registry_has_version():
    """Registry should have version field"""
    with open("registry/domain_registry.yaml") as f:
        registry = yaml.safe_load(f)

    assert 'version' in registry
    assert registry['version'] == "1.0.0"

def test_domain_registry_has_schema_layers():
    """Registry should define schema layers"""
    with open("registry/domain_registry.yaml") as f:
        registry = yaml.safe_load(f)

    assert 'schema_layers' in registry
    assert '01' in registry['schema_layers']
    assert registry['schema_layers']['01'] == 'write_side'

def test_domain_registry_has_domains():
    """Registry should define domains"""
    with open("registry/domain_registry.yaml") as f:
        registry = yaml.safe_load(f)

    assert 'domains' in registry
    assert '2' in registry['domains']  # CRM domain
    assert registry['domains']['2']['name'] == 'crm'

def test_crm_domain_has_subdomains():
    """CRM domain should have subdomains"""
    with open("registry/domain_registry.yaml") as f:
        registry = yaml.safe_load(f)

    crm = registry['domains']['2']
    assert 'subdomains' in crm
    assert '3' in crm['subdomains']  # customer subdomain
    assert crm['subdomains']['3']['name'] == 'customer'
```

### GREEN: Minimal Implementation

```bash
# Create registry directory
mkdir -p registry
```

```yaml
# registry/domain_registry.yaml

version: "1.0.0"
last_updated: "2025-11-08"

schema_layers:
  "01": write_side
  "02": read_side
  "03": analytics

domains:
  "1":
    name: core
    description: "Core infrastructure"
    subdomains:
      "1":
        name: i18n
        description: "Internationalization"
        next_entity_sequence: 1

  "2":
    name: crm
    description: "Customer relationship management"
    aliases: ["management"]
    subdomains:
      "1":
        name: core
        description: "Core organization"
        next_entity_sequence: 1
      "3":
        name: customer
        description: "Customer contacts"
        next_entity_sequence: 1

  "3":
    name: catalog
    description: "Product catalog"
    subdomains:
      "2":
        name: manufacturer
        description: "Manufacturers"
        next_entity_sequence: 1

  "4":
    name: projects
    description: "Project management"
    aliases: ["tenant"]
    subdomains:
      "1":
        name: core
        description: "Core project entities"
        next_entity_sequence: 1

validation:
  enforce_uniqueness: true
  allow_manual_override: true
```

### REFACTOR: Complete Registry

Add all subdomains based on PrintOptim Backend reference:

```yaml
domains:
  "1":
    name: core
    description: "Core infrastructure (i18n, auth, events)"
    subdomains:
      "1":
        name: i18n
        description: "Internationalization & translations"
        next_entity_sequence: 1
      "2":
        name: auth
        description: "Authentication & authorization"
        next_entity_sequence: 1
      "3":
        name: events
        description: "Event system & audit logging"
        next_entity_sequence: 1
      "4":
        name: workflow
        description: "Workflow engine"
        next_entity_sequence: 1

  "2":
    name: crm
    description: "Customer relationship management & organizational structure"
    aliases: ["management"]
    subdomains:
      "1":
        name: core
        description: "Core organization entities (organization, user)"
        next_entity_sequence: 1
      "2":
        name: sales
        description: "Sales process entities (opportunity, quote)"
        next_entity_sequence: 1
      "3":
        name: customer
        description: "Customer contact entities (contact, company)"
        next_entity_sequence: 1
      "4":
        name: support
        description: "Customer support entities (ticket, case)"
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
        next_entity_sequence: 1
      "3":
        name: product
        description: "Product entities & SKUs"
        next_entity_sequence: 1
      "4":
        name: generic
        description: "Generic product data"
        next_entity_sequence: 1
      "5":
        name: financing
        description: "Financing & pricing"
        next_entity_sequence: 1

  "4":
    name: projects
    description: "Project management & tenant-specific entities"
    aliases: ["tenant", "dim"]
    subdomains:
      "1":
        name: core
        description: "Core project entities (task, project)"
        next_entity_sequence: 1
      "2":
        name: location
        description: "Geographic entities (location, address)"
        next_entity_sequence: 1
      "3":
        name: network
        description: "Network configuration"
        next_entity_sequence: 1
      "4":
        name: contract
        description: "Contract management"
        next_entity_sequence: 1
      "5":
        name: machine
        description: "Machine/equipment tracking"
        next_entity_sequence: 1

reserved_codes:
  - "000000"
  - "999999"
```

### QA: Verify

```bash
# Run tests
uv run pytest tests/unit/registry/test_domain_registry.py -v

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('registry/domain_registry.yaml'))"

# Check for duplicate codes
python -c "
import yaml
with open('registry/domain_registry.yaml') as f:
    registry = yaml.safe_load(f)

# Check domain codes unique
assert len(set(registry['domains'].keys())) == len(registry['domains'])
print('✓ All domain codes unique')
"
```

---

## 🟢 Phase 2: DomainRegistry Class (Day 2-3)

**Objective**: Implement DomainRegistry class for loading/managing registry

### RED: Write Failing Test

```python
# tests/unit/registry/test_domain_registry_class.py

from src.generators.schema.naming_conventions import DomainRegistry

def test_load_registry():
    """Should load registry from YAML"""
    registry = DomainRegistry("registry/domain_registry.yaml")

    assert registry.registry is not None
    assert 'domains' in registry.registry

def test_get_entity_not_found():
    """Should return None for unregistered entity"""
    registry = DomainRegistry()

    entity = registry.get_entity("NonExistent")
    assert entity is None

def test_get_domain_by_code():
    """Should get domain by code"""
    registry = DomainRegistry()

    domain = registry.get_domain("2")
    assert domain is not None
    assert domain.domain_name == "crm"

def test_get_domain_by_name():
    """Should get domain by name"""
    registry = DomainRegistry()

    domain = registry.get_domain("crm")
    assert domain is not None
    assert domain.domain_code == "2"

def test_get_domain_by_alias():
    """Should get domain by alias"""
    registry = DomainRegistry()

    domain = registry.get_domain("management")  # alias for crm
    assert domain is not None
    assert domain.domain_name == "crm"

def test_is_code_available():
    """Should check if code is available"""
    registry = DomainRegistry()

    # Reserved code
    assert not registry.is_code_available("000000")

    # Unassigned code
    assert registry.is_code_available("012399")
```

### GREEN: Minimal Implementation

```python
# src/generators/schema/naming_conventions.py

from pathlib import Path
import yaml
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class DomainInfo:
    domain_code: str
    domain_name: str
    description: str
    subdomains: Dict
    aliases: list

class DomainRegistry:
    def __init__(self, registry_path: str = "registry/domain_registry.yaml"):
        self.registry_path = Path(registry_path)
        self.registry: Dict = {}
        self.entities_index: Dict = {}
        self.load()

    def load(self):
        """Load registry from YAML"""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Domain registry not found: {self.registry_path}")

        with open(self.registry_path, 'r') as f:
            self.registry = yaml.safe_load(f)

        self._build_entity_index()

    def _build_entity_index(self):
        """Build index of all registered entities"""
        # Implementation from overview
        pass

    def get_entity(self, entity_name: str) -> Optional[dict]:
        """Get entity from registry"""
        return self.entities_index.get(entity_name.lower())

    def get_domain(self, domain_identifier: str) -> Optional[DomainInfo]:
        """Get domain by code, name, or alias"""
        # Try by code
        if domain_identifier in self.registry.get('domains', {}):
            domain_data = self.registry['domains'][domain_identifier]
            return DomainInfo(
                domain_code=domain_identifier,
                domain_name=domain_data['name'],
                description=domain_data['description'],
                subdomains=domain_data.get('subdomains', {}),
                aliases=domain_data.get('aliases', [])
            )

        # Try by name or alias
        for code, domain_data in self.registry.get('domains', {}).items():
            if domain_data['name'] == domain_identifier:
                return self.get_domain(code)
            if domain_identifier in domain_data.get('aliases', []):
                return self.get_domain(code)

        return None

    def is_code_available(self, table_code: str) -> bool:
        """Check if code is available"""
        reserved = self.registry.get('reserved_codes', [])
        if table_code in reserved:
            return False

        for entity in self.entities_index.values():
            if entity.get('table_code') == table_code:
                return False

        return True
```

### REFACTOR: Complete Implementation

Add remaining methods:
- `get_next_entity_sequence()`
- `register_entity()`
- `save()`
- Proper `_build_entity_index()` implementation

### QA: Verify

```bash
uv run pytest tests/unit/registry/test_domain_registry_class.py -v
```

---

## 🔵 Phase 3: NamingConventions Module (Day 3-5)

**Objective**: Implement core naming conventions functions

### Phase 3.1: derive_entity_code() (Half Day)

#### RED
```python
def test_derive_entity_code_contact():
    nc = NamingConventions()
    assert nc.derive_entity_code("Contact") == "CON"

def test_derive_entity_code_manufacturer():
    nc = NamingConventions()
    assert nc.derive_entity_code("Manufacturer") == "MNF"
```

#### GREEN
```python
def derive_entity_code(self, entity_name: str) -> str:
    name_upper = entity_name.upper()
    consonants = [c for c in name_upper if c.isalpha() and c not in 'AEIOUY']
    return (''.join(consonants) + name_upper)[:3]
```

#### REFACTOR
Improve algorithm for edge cases

#### QA
```bash
uv run pytest tests/unit/schema/test_naming_conventions.py::test_derive_entity_code -v
```

### Phase 3.2: validate_table_code() (Half Day)

#### RED
```python
def test_validate_format():
    nc = NamingConventions()
    entity = Entity(name="Contact", schema="crm")

    nc.validate_table_code("012321", entity)  # Valid

    with pytest.raises(ValueError):
        nc.validate_table_code("123", entity)  # Too short
```

#### GREEN
```python
def validate_table_code(self, table_code: str, entity: Entity):
    if not re.match(r'^\d{6}$', table_code):
        raise ValueError(f"Invalid format: {table_code}")
```

#### REFACTOR
Add all validation checks (schema layer, domain, uniqueness)

#### QA
Run validation tests

### Phase 3.3: derive_table_code() (Day)

#### RED
```python
def test_derive_table_code_crm_contact():
    nc = NamingConventions()
    entity = Entity(name="Contact", schema="crm")

    code = nc.derive_table_code(entity)

    # Should start with 012 (write_side + crm)
    assert code.startswith("012")
    assert len(code) == 6
```

#### GREEN
Implement basic derivation logic

#### REFACTOR
Add subdomain inference, handle edge cases

#### QA
Test with multiple entities

### Phase 3.4: generate_file_path() (Half Day)

#### RED
```python
def test_generate_file_path():
    nc = NamingConventions()
    entity = Entity(name="Contact", schema="crm")

    path = nc.generate_file_path(entity, "012321", "table")

    assert "01_write_side" in path
    assert "012_crm" in path
    assert "012321_tb_contact.sql" in path
```

#### GREEN
Implement path generation

#### REFACTOR
Use proper directory hierarchy

#### QA
Test multiple file types

---

## 🟡 Phase 4: Generator Integration (Day 5-6)

**Objective**: Integrate NamingConventions with Team B schema generator

### RED: Write Integration Test

```python
# tests/integration/schema/test_naming_conventions_integration.py

from src.core.specql_parser import SpecQLParser
from src.generators.table_generator import TableGenerator
from src.generators.schema.naming_conventions import NamingConventions

def test_generate_contact_with_auto_table_code():
    """Should auto-assign table code during generation"""
    yaml_content = """
    entity: Contact
    schema: crm
    fields:
      email: email!
    """

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    generator = TableGenerator()
    sql = generator.generate_table_ddl(entity)

    # Should have generated with auto table code
    assert "CREATE TABLE crm.tb_contact" in sql

    # Check registry was updated
    nc = NamingConventions()
    registry_entry = nc.registry.get_entity("Contact")
    assert registry_entry is not None
    assert len(registry_entry.table_code) == 6
```

### GREEN: Modify TableGenerator

```python
# src/generators/table_generator.py

from src.generators.schema.naming_conventions import NamingConventions

class TableGenerator:
    def __init__(self):
        self.naming = NamingConventions()

    def generate_table_ddl(self, entity: Entity) -> str:
        # Get table code (manual or auto)
        table_code = self.naming.get_table_code(entity)

        # Register in registry if new
        if not self.naming.registry.get_entity(entity.name):
            entity_code = self.naming.derive_entity_code(entity.name)
            components = self.naming.parser.parse_table_code_detailed(table_code)
            self.naming.registry.register_entity(
                entity.name,
                table_code,
                entity_code,
                components.domain_code,
                components.entity_group
            )

        # Continue with existing generation logic
        # ... existing code ...
```

### REFACTOR
- Add proper error handling
- Update all generators (Team C, D)
- Add file path organization

### QA
```bash
uv run pytest tests/integration/schema/test_naming_conventions_integration.py -v
make test-integration
```

---

## 🟣 Phase 5: CLI Commands (Day 6-7)

**Objective**: Add CLI commands for registry management

### RED: Write CLI Test

```python
# tests/integration/cli/test_registry_commands.py

from click.testing import CliRunner
from src.cli.registry import registry_cli

def test_registry_list():
    """Should list all registered entities"""
    runner = CliRunner()
    result = runner.invoke(registry_cli, ['list'])

    assert result.exit_code == 0
    assert 'Contact' in result.output
    assert '012321' in result.output

def test_registry_check_available():
    """Should check if code is available"""
    runner = CliRunner()
    result = runner.invoke(registry_cli, ['check', '012399'])

    assert result.exit_code == 0
    assert 'available' in result.output.lower()
```

### GREEN: Implement CLI

```python
# src/cli/registry.py

import click
from src.generators.schema.naming_conventions import NamingConventions

@click.group()
def registry_cli():
    """Registry management commands"""
    pass

@registry_cli.command()
def list():
    """List all registered entities"""
    nc = NamingConventions()

    click.echo("Registered Entities:")
    click.echo("-" * 60)

    for entity_name, entry in nc.registry.entities_index.items():
        click.echo(f"{entity_name:20} {entry.table_code:10} {entry.domain}/{entry.subdomain}")

@registry_cli.command()
@click.argument('table_code')
def check(table_code):
    """Check if table code is available"""
    nc = NamingConventions()

    if nc.registry.is_code_available(table_code):
        click.echo(f"✓ Code {table_code} is available")
    else:
        click.echo(f"✗ Code {table_code} is already assigned")

@registry_cli.command()
def manifest():
    """Generate execution manifest"""
    # Implementation using ManifestGenerator
    pass
```

### REFACTOR
Add more commands:
- `specql registry validate` - Validate registry consistency
- `specql registry export` - Export as JSON/CSV
- `specql registry stats` - Show statistics

### QA
```bash
uv run pytest tests/integration/cli/test_registry_commands.py -v
specql registry list
specql registry check 012399
```

---

## 🔴 Phase 6: Migration & Validation (Day 7-8)

**Objective**: Migrate existing entities to registry, validate consistency

### RED: Write Migration Test

```python
def test_migrate_existing_entities():
    """Should migrate existing entities to registry"""
    from src.cli.migrate import migrate_existing_entities

    # Before: registry has 0 entities
    nc = NamingConventions()
    assert len(nc.registry.entities_index) == 0

    # Migrate
    migrated_count = migrate_existing_entities('entities/examples/')

    # After: registry has entities
    nc.load()  # Reload
    assert len(nc.registry.entities_index) > 0
    assert migrated_count > 0
```

### GREEN: Implement Migration

```python
# src/cli/migrate.py

def migrate_existing_entities(entities_dir: str) -> int:
    """Migrate existing SpecQL entities to registry"""
    from pathlib import Path
    from src.core.specql_parser import SpecQLParser
    from src.generators.schema.naming_conventions import NamingConventions

    parser = SpecQLParser()
    nc = NamingConventions()
    migrated = 0

    for yaml_file in Path(entities_dir).rglob('*.yaml'):
        entity = parser.parse(yaml_file.read_text())

        # Skip if already registered
        if nc.registry.get_entity(entity.name):
            continue

        # Get or derive table code
        if entity.organization and entity.organization.table_code:
            table_code = entity.organization.table_code
        else:
            table_code = nc.derive_table_code(entity)

        # Register
        entity_code = nc.derive_entity_code(entity.name)
        components = nc.parser.parse_table_code_detailed(table_code)
        nc.registry.register_entity(
            entity.name,
            table_code,
            entity_code,
            components.domain_code,
            components.entity_group
        )

        migrated += 1
        click.echo(f"✓ Migrated {entity.name} → {table_code}")

    return migrated
```

### REFACTOR
Add validation:
- Check for conflicts
- Validate subdomain assignments
- Detect potential duplicates

### QA
```bash
specql migrate entities/examples/
specql registry validate
```

---

## 📘 Phase 7: Documentation & Examples (Day 8-10)

**Objective**: Complete documentation and working examples

### Deliverables

1. **User Guide** (`docs/guides/naming-conventions.md`)
   - How to use manual table codes
   - How automatic derivation works
   - Registry management
   - Subdomain organization

2. **API Reference** (`docs/api/naming-conventions-api.md`)
   - All public functions
   - Parameters and return types
   - Examples

3. **Migration Guide** (`docs/guides/migration-to-registry.md`)
   - How to migrate existing projects
   - Troubleshooting
   - Best practices

4. **Examples**
   - Simple entity with auto code
   - Manual code specification
   - Complex multi-subdomain project

### QA
- All documentation reviewed
- Examples run successfully
- CLI help text clear
- README updated

---

## ✅ Success Criteria

### Must Have
- ✅ Registry YAML with all domains/subdomains
- ✅ DomainRegistry class loads and manages registry
- ✅ NamingConventions derives and validates codes
- ✅ Team B integration working
- ✅ Registry automatically updated on generation
- ✅ CLI commands for list/check/validate
- ✅ Existing entities migrated
- ✅ 50+ unit tests passing
- ✅ 10+ integration tests passing

### Should Have
- ✅ Hierarchical file organization
- ✅ Subdomain inference working
- ✅ Manifest generation
- ✅ Registry export/import
- ✅ Validation warnings for potential issues

### Nice to Have
- 🔄 Visual registry browser
- 🔄 Auto-detect subdomain from entity patterns
- 🔄 Registry version control integration
- 🔄 Conflict resolution UI

---

## 🚀 Getting Started

```bash
# Day 1: Start with Phase 1
mkdir -p registry tests/unit/registry
touch registry/domain_registry.yaml

# Create basic test
vim tests/unit/registry/test_domain_registry.py

# Run RED phase
uv run pytest tests/unit/registry/ -v
# Should fail - no registry yet

# Create registry (GREEN)
vim registry/domain_registry.yaml

# Tests should pass
uv run pytest tests/unit/registry/ -v
```

---

**Next Steps**: Once this is complete, Team T (Testing Infrastructure) can begin with confident table code generation for UUID encoding!
