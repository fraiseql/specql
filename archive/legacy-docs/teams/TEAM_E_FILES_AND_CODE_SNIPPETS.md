# Team E: Detailed File and Code Snippet Analysis

---

## 1. Existing Implementation: CLI Foundation

### 1.1 Main CLI Entry Point
**File**: `/home/lionel/code/printoptim_backend_poc/src/cli/generate.py`
**Size**: 139 lines, 4,684 bytes
**Status**: FUNCTIONAL for `entities` command

**Key Code Snippets**:

```python
# Entry point called by: specql = "src.cli.generate:main"
def main():
    """Entry point for specql generate command"""
    cli()

# Click command group
@click.group()
def cli():
    """SpecQL Generator CLI"""
    pass

# Main command: generate entities
@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="migrations", help="Output directory for migrations")
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation migration")
@click.option("--include-tv", is_flag=True, help="Generate tv_ table views after entities")
def entities(entity_files, output_dir, foundation_only, include_tv):
    """Generate SQL migrations from SpecQL entity files"""
```

**Integration with Other Teams**:
- Uses `SpecQLParser` from Team A (src/core/specql_parser.py)
- Uses `SchemaOrchestrator` from Team B (src/generators/schema_orchestrator.py)
- Converts between EntityDefinition (Team A) and Entity (Team B) types

**Known TODO**: Line 20
```python
action = Action(
    name=action_def.name, steps=action_def.steps, impact=None
)  # TODO: Convert impact dict to ActionImpact
```

### 1.2 CLI Directory Structure
```
src/cli/
├── __init__.py              # Empty
├── generate.py              # 139 lines - entities command
├── validate.py              # MISSING (declared in pyproject.toml)
├── migrate.py               # MISSING (declared in pyproject.toml)
├── orchestrator.py          # MISSING (Team E internal)
├── migration_manager.py     # MISSING (Team E internal)
└── commands/                # MISSING directory
    ├── __init__.py
    ├── deduplication.py     # MISSING
    ├── split_entities.py    # MISSING
    └── validate_paths.py    # MISSING
```

### 1.3 pyproject.toml Entry Points Configuration

```toml
[project.scripts]
specql = "src.cli.generate:main"
specql-validate = "src.cli.validate:main"  # Points to missing file
specql-migrate = "src.cli.migrate:main"    # Points to missing file
```

---

## 2. Team B Integration: SchemaOrchestrator

### 2.1 SchemaOrchestrator Class
**File**: `/home/lionel/code/printoptim_backend_poc/src/generators/schema_orchestrator.py`
**Size**: 203 lines
**Status**: FUNCTIONAL

**Key Methods Available to Team E**:

```python
class SchemaOrchestrator:
    """Orchestrates complete schema generation: tables + types + indexes + constraints"""

    def __init__(self, naming_conventions: NamingConventions = None) -> None:
        # Creates generators for all schema components
        self.app_gen = AppSchemaGenerator()
        self.table_gen = TableGenerator(schema_registry)
        self.type_gen = CompositeTypeGenerator()
        self.helper_gen = TrinityHelperGenerator(schema_registry)
        self.core_gen = CoreLogicGenerator(schema_registry)

    def generate_complete_schema(self, entity: Entity) -> str:
        """
        Generate complete schema for entity: tables + types + indexes + functions

        Returns:
            Complete SQL schema as string
        """
        # Generates in order:
        # 1. App schema foundation
        # 2. Schema creation
        # 3. Common types
        # 4. Entity table (Trinity pattern)
        # 5. Input types for actions
        # 6. Indexes
        # 7. Foreign keys
        # 8. Core logic functions
        # 9. FraiseQL mutation annotations
        # 10. Trinity helper functions

    def generate_table_views(self, entities: List[EntityDefinition]) -> str:
        """Generate tv_ tables for all entities in dependency order"""

        resolver = TableViewDependencyResolver(entities)
        generation_order = resolver.get_generation_order()

        # Generates in order with FraiseQL annotations

    def generate_app_foundation_only(self) -> str:
        """Generate only the app schema foundation (for base migrations)"""
        return self.app_gen.generate_app_foundation()

    def generate_schema_summary(self, entity: Entity) -> Dict:
        """Generate summary of what will be created for this entity"""
        return {
            "entity": entity.name,
            "table": f"{entity.schema}.tb_{entity.name.lower()}",
            "types": [...],
            "indexes": [...],
            "constraints": [...]
        }
```

**Current Usage in generate.py**:
```python
# Line 72-103
orchestrator = SchemaOrchestrator()

# Generate app foundation
foundation_sql = orchestrator.generate_app_foundation_only()

# Generate complete schema for each entity
migration_sql = orchestrator.generate_complete_schema(entity)

# Generate table views if requested
tv_sql = orchestrator.generate_table_views(all_entity_defs)
```

---

## 3. Team A Integration: Parser

### 3.1 SpecQLParser
**File**: `/home/lionel/code/printoptim_backend_poc/src/core/specql_parser.py`
**Status**: COMPLETE (✅ Team A Done)

**Key Method Used by Team E**:
```python
from src.core.specql_parser import SpecQLParser

parser = SpecQLParser()
entity_def = parser.parse(yaml_content)  # Returns EntityDefinition

# convert_entity_definition_to_entity() in generate.py converts to Entity type
def convert_entity_definition_to_entity(entity_def: EntityDefinition) -> Entity:
    """Convert EntityDefinition to Entity for orchestrator compatibility"""
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name,
            steps=action_def.steps,
            impact=None  # TODO: Convert impact dict to ActionImpact
        )
        actions.append(action)

    return Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        description=entity_def.description,
        fields=entity_def.fields,
        actions=actions,
        agents=entity_def.agents,
        organization=entity_def.organization,
    )
```

---

## 4. Team D Integration: FraiseQL Metadata

### 4.1 Mutation Annotator
**File**: `/home/lionel/code/printoptim_backend_poc/src/generators/fraiseql/mutation_annotator.py`
**Size**: ~100 lines
**Status**: FUNCTIONAL

**Used by SchemaOrchestrator**:
```python
# From schema_orchestrator.py lines 104-116
if entity.actions:
    for action in entity.actions:
        annotator = MutationAnnotator(entity.schema, entity.name)
        annotation = annotator.generate_mutation_annotation(action)
        if annotation:
            mutation_annotations.append(annotation)

if mutation_annotations:
    parts.append(
        "-- FraiseQL Mutation Annotations (Team D)\n" + "\n\n".join(mutation_annotations)
    )
```

### 4.2 Table View Annotator
**File**: `/home/lionel/code/printoptim_backend_poc/src/generators/fraiseql/table_view_annotator.py`
**Size**: ~200 lines
**Status**: FUNCTIONAL

**Used by SchemaOrchestrator for tv_ tables**:
```python
# From schema_orchestrator.py lines 153-161
if entity.table_views:
    annotator = TableViewAnnotator(entity)
    annotations = annotator.generate_annotations()
    if annotations:
        parts.append(
            f"-- FraiseQL Annotations: {entity.schema}.tv_{entity.name.lower()}\n"
            + annotations
        )
```

---

## 5. Team E TODO: What's Missing to Implement

### 5.1 Missing Files Summary

| Priority | File | Lines | Purpose |
|----------|------|-------|---------|
| **HIGH** | `src/cli/validate.py` | 150 | Validation command |
| **HIGH** | `src/cli/orchestrator.py` | 200 | CLI orchestration wrapper |
| **HIGH** | `tests/unit/cli/__init__.py` | 5 | Test package |
| **HIGH** | `tests/unit/cli/test_generate_command.py` | 200+ | Generate command tests |
| **HIGH** | `tests/unit/cli/test_cli_orchestrator.py` | 200+ | Orchestrator tests |
| **MEDIUM** | `src/cli/migrate.py` | 200 | Migration execution |
| **MEDIUM** | `src/cli/migration_manager.py` | 150 | Migration state tracking |
| **MEDIUM** | `src/generators/frontend/__init__.py` | 10 | Package init |
| **MEDIUM** | `src/generators/frontend/mutation_impacts_generator.py` | 150 | JSON generator |
| **MEDIUM** | `src/generators/frontend/typescript_types_generator.py` | 200 | TypeScript types |
| **LOW** | `src/cli/commands/__init__.py` | 10 | Commands package |
| **LOW** | `src/cli/commands/deduplication.py` | 100 | Dedup commands |
| **LOW** | `src/cli/commands/split_entities.py` | 120 | Split entity commands |
| **LOW** | `src/generators/frontend/apollo_hooks_generator.py` | 250 | React hooks |
| **LOW** | `src/generators/frontend/mutation_docs_generator.py` | 150 | Markdown docs |

**TOTAL**: ~15 files, ~2,100+ lines

### 5.2 CLI Commands to Implement

Based on CLAUDE.md + TEAM_E_DATABASE_DECISIONS_PLAN.md:

**From CLAUDE.md**:
```bash
specql generate entities/contact.yaml                                      # PARTIAL ✅
specql generate entities/*.yaml --with-impacts --output-frontend=..  # TODO
specql validate entities/*.yaml --check-impacts                      # TODO
specql diff entities/contact.yaml                                    # TODO
specql docs entities/*.yaml --format=markdown --output=docs/       # TODO
specql validate-impacts --database-url=postgres://                  # TODO
```

**From TEAM_E_DATABASE_DECISIONS_PLAN.md**:
```bash
specql list-duplicates --entity=Location --schema=tenant            # TODO
specql recalculate-identifiers --entity=Contact --schema=crm       # TODO
specql list-split-entities                                          # TODO
specql validate-split-integrity --entity=Location --schema=tenant  # TODO
specql validate-paths --entity=Location --schema=tenant [--fix]    # TODO
```

---

## 6. Dependencies Already Available

### 6.1 Python Package Dependencies (in pyproject.toml)

```toml
dependencies = [
    "pyyaml>=6.0",              # YAML parsing ✅
    "jinja2>=3.1.2",            # Template rendering ✅
    "click>=8.1.0",             # CLI framework ✅
    "rich>=13.0.0",             # Terminal UI/formatting ✅
    "psycopg2-binary>=2.9.0",   # Database driver ✅
    "psycopg>=3.2.12",          # Async DB driver ✅
]
```

**All needed for Team E work are already installed!**

### 6.2 Internal Modules Available to Team E

```python
# Team A - Parser
from src.core.specql_parser import SpecQLParser
from src.core.ast_models import Entity, Action, EntityDefinition

# Team B - Schema Generation
from src.generators.schema_orchestrator import SchemaOrchestrator
from src.generators.table_generator import TableGenerator
from src.generators.trinity_helper_generator import TrinityHelperGenerator
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry

# Team C - Actions (if needed)
from src.generators.actions.action_compiler import ActionCompiler
from src.generators.actions.action_validator import ActionValidator

# Team D - FraiseQL
from src.generators.fraiseql.mutation_annotator import MutationAnnotator
from src.generators.fraiseql.table_view_annotator import TableViewAnnotator
```

---

## 7. Current Test Examples (For Comparison)

### 7.1 Unit Test Structure (from Team B)
**File**: `/home/lionel/code/printoptim_backend_poc/tests/unit/generators/test_schema_generator.py`

```python
import pytest
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator

@pytest.fixture
def parser():
    return SpecQLParser()

@pytest.fixture
def orchestrator():
    return SchemaOrchestrator()

def test_generate_complete_schema(parser, orchestrator):
    yaml_content = """
    entity: Contact
    schema: crm
    fields:
      email: text
      company: ref(Company)
    """

    entity_def = parser.parse(yaml_content)
    # Convert to Entity...
    sql = orchestrator.generate_complete_schema(entity)

    assert "CREATE TABLE crm.tb_contact" in sql
    assert "pk_contact" in sql
    assert "id UUID" in sql
```

### 7.2 Integration Test Structure (from Team B)
**File**: `/home/lionel/code/printoptim_backend_poc/tests/integration/test_team_b_integration.py`

```python
import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator

@pytest.mark.integration
def test_schema_orchestrator_end_to_end():
    parser = SpecQLParser()
    orchestrator = SchemaOrchestrator()

    # Test with actual file
    yaml_file = Path("entities/examples/contact_lightweight.yaml")
    yaml_content = yaml_file.read_text()

    entity_def = parser.parse(yaml_content)
    # Convert to Entity...
    sql = orchestrator.generate_complete_schema(entity)

    # Verify all components are present
    assert "CREATE TABLE" in sql
    assert "CREATE INDEX" in sql
    assert "CREATE OR REPLACE FUNCTION" in sql
```

---

## 8. Example Test Structure for Team E

### 8.1 Test File: test_generate_command.py (Should be created)

```python
# tests/unit/cli/test_generate_command.py
import pytest
from click.testing import CliRunner
from pathlib import Path
from src.cli.generate import cli

@pytest.fixture
def cli_runner():
    return CliRunner()

@pytest.fixture
def temp_migrations_dir(tmp_path):
    return tmp_path / "migrations"

def test_generate_entities_command(cli_runner, temp_migrations_dir):
    """Test: specql entities entities/examples/contact.yaml"""
    result = cli_runner.invoke(cli, [
        'entities',
        'entities/examples/contact_lightweight.yaml',
        '--output-dir', str(temp_migrations_dir)
    ])

    assert result.exit_code == 0
    assert (temp_migrations_dir / "000_app_foundation.sql").exists()
    assert (temp_migrations_dir / "100_contact.sql").exists()

def test_generate_with_table_views(cli_runner, temp_migrations_dir):
    """Test: specql entities ... --include-tv"""
    result = cli_runner.invoke(cli, [
        'entities',
        'entities/examples/contact_lightweight.yaml',
        '--output-dir', str(temp_migrations_dir),
        '--include-tv'
    ])

    assert result.exit_code == 0
    assert (temp_migrations_dir / "200_table_views.sql").exists()

def test_generate_foundation_only(cli_runner, temp_migrations_dir):
    """Test: specql entities --foundation-only"""
    result = cli_runner.invoke(cli, [
        'entities',
        '--foundation-only',
        '--output-dir', str(temp_migrations_dir)
    ])

    assert result.exit_code == 0
    assert (temp_migrations_dir / "000_app_foundation.sql").exists()
```

---

## 9. Example Entity Files Available for Testing

### 9.1 Contact (Simple)
**File**: `/home/lionel/code/printoptim_backend_poc/entities/examples/contact_lightweight.yaml`

```yaml
entity: Contact
schema: crm

fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

### 9.2 Manufacturer (Complex with Table Views)
**File**: `/home/lionel/code/printoptim_backend_poc/entities/examples/manufacturer.yaml`

```yaml
entity: Manufacturer
schema: catalog

fields:
  name: text
  status: enum(active, inactive)
  parent_id: ref(Manufacturer)

table_views:
  - name: tv_Manufacturer
    columns: [id, name, status]

actions:
  - name: create_manufacturer
    steps:
      - insert: Manufacturer(name, status)
```

---

## 10. Quick Implementation Checklist

### Phase 1: Immediate (Next Session)
- [ ] Create `tests/unit/cli/` directory
- [ ] Create `tests/unit/cli/__init__.py`
- [ ] Create `tests/unit/cli/test_generate_command.py` with basic tests
- [ ] Run tests: `make teamE-test` (should have some passing)

### Phase 2: CLI Foundation
- [ ] Extend `generate.py` with `--with-impacts` flag
- [ ] Create `src/cli/orchestrator.py` wrapper
- [ ] Create `src/cli/validate.py` command
- [ ] Update tests to cover new options

### Phase 3: Orchestration
- [ ] Create `src/cli/migration_manager.py`
- [ ] Implement migration versioning
- [ ] Add rollback capability

### Phase 4: Frontend (Lower Priority)
- [ ] Create `src/generators/frontend/` directory
- [ ] Implement generators one by one

### Phase 5: Management Commands (Low Priority)
- [ ] Create `src/cli/commands/` directory
- [ ] Implement dedup, split entity, path validation commands

---

## Summary

**Current State**:
- Team E is 5% complete (~1 file, 140 lines out of 3,200+ needed)
- Foundation is solid (Click, dependencies, examples)
- All teams A-D are complete and functional
- 100 tests show strong testing culture
- Comprehensive documentation exists

**Next Steps**:
1. Create test directory and basic tests
2. Extend existing generate.py with new options
3. Build out remaining CLI commands systematically
4. Frontend code generation (lower priority)

**Effort Estimate**: 2-3 weeks for complete Team E implementation following TDD methodology
