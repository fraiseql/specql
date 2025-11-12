# Hierarchical View Organization - REVISED Implementation Plan

**Date**: 2025-11-12 (REVISED)
**Status**: Planning
**Complexity**: Complex - Phased TDD Approach Required

## Executive Summary

Currently, SpecQL generates all table views (tv_*) into a single monolithic file `200_table_views.sql`. The goal is to implement hierarchical organization matching the reference system in `printoptim_specql`, where views are organized into individual files with hex-based prefixes.

**CRITICAL CORRECTION**: Read-side entity sequencing is **INDEPENDENT** from write-side. The 7th digit (entity sequence) is not derived from write-side codes but assigned independently per schema layer.

**Current State**: All tv_* tables → `200_table_views.sql` (single file)
**Target State**: Individual tv_* files organized hierarchically with independent read-side sequencing

---

## Hex Code Format: `0SDDSSEV`

Each position has specific meaning:

| Position | Name | Meaning | Example |
|----------|------|---------|---------|
| 1 | X | Schema file prefix | `0` (always) |
| 2 | S | Schema layer | `1` = write_side, `2` = read_side |
| 3-4 | DD | Domain code | `14` = dimensions |
| 5-6 | SS | Subdomain code | `41` = geo |
| 7 | E | Entity sequence (layer-specific) | `3` = 3rd entity |
| 8 | V | View/file number | `0` = first file |

### Example Breakdown

**Write-Side**: `014112_tb_location.sql`
```
0  1  41  1  2
│  │  │   │  └─ File 2 for this entity
│  │  │   └──── Entity 1 in subdomain
│  │  └──────── Subdomain 41 (geo)
│  └─────────── Write-side (1)
└────────────── Schema (0)
```

**Read-Side**: `024130_tv_location.sql`
```
0  2  41  3  0
│  │  │   │  └─ File 0 (first file)
│  │  │   └──── Entity 3 (INDEPENDENT from write-side!)
│  │  └──────── Subdomain 41 (same)
│  └─────────── Read-side (2)
└────────────── Schema (0)
```

**KEY INSIGHT**: Entity `1` on write-side ≠ Entity `1` on read-side!

---

## Gap Analysis

### 1. Current Implementation

**File Output** (`src/cli/orchestrator.py:424-437`):
```python
# Generate tv_ tables if requested
if include_tv and entity_defs:
    tv_sql = self.schema_orchestrator.generate_table_views(entity_defs)
    if tv_sql:
        migration = MigrationFile(
            number=200,
            name="table_views",
            content=tv_sql,
            path=output_path / "200_table_views.sql",  # ❌ Single file
        )
        result.migrations.append(migration)
```

**Key Characteristics**:
- ✅ Topological dependency resolution working
- ✅ FraiseQL annotations included
- ✅ Trinity pattern applied
- ❌ No per-entity file splitting
- ❌ No hierarchical directory structure
- ❌ No hex code assignment for read-side
- ❌ No independent entity sequencing for read-side

---

### 2. Target Implementation (Reference System)

**File Structure Example**:
```
0_schema/
├── 01_write_side/
│   └── 014_dim/
│       └── 0141_geo/
│           └── 01411_location/
│               ├── 014111_tb_location_info.sql    # Entity 1, File 1
│               └── 014112_tb_location.sql         # Entity 1, File 2
│
└── 02_query_side/
    └── 024_dim/
        └── 0241_geo/
            ├── 024111_v_count_allocations.sql     # Entity 1, File 1
            ├── 024122_v_location.sql              # Entity 2, File 2
            ├── 024130_tv_location.sql             # Entity 3, File 0 ← tv_!
            └── 024141_v_flat_location.sql         # Entity 4, File 1
```

**Pattern Analysis**:
- Write-side has 2 files for location (014111, 014112)
- Read-side has 4 different entities/views (024111, 024122, 024130, 024141)
- **Entity numbering is independent per schema layer**
- tv_location is entity 3 on read-side, not related to entity 1 on write-side

---

### 3. Registry Code Assignment System

**Current Registry** (`registry/domain_registry.yaml`):
```yaml
domains:
  '2':
    name: crm
    subdomains:
      '03':
        name: customer
        entities:
          Contact:
            table_code: '012036'  # Write-side only!
            entity_code: CNT
```

**What's Missing**:
- ❌ No read-side entity tracking
- ❌ No independent read-side sequence management
- ❌ No view file tracking (v_, tv_, mv_)
- ❌ No read-side path information

**What's Needed**:
```yaml
domains:
  '2':
    name: crm
    multi_tenant: true
    subdomains:
      '03':
        name: customer

        # WRITE-SIDE (01_write_side)
        next_write_entity: 37
        write_entities:
          Contact:
            entity_number: 36           # 7th digit
            files:
              - code: '0120361'         # 01-2-03-36-1
                type: tb_
                name: tb_contact
                path: 01_write_side/012_crm/0123_customer/01236_contact/0120361_tb_contact.sql

        # READ-SIDE (02_query_side) - INDEPENDENT SEQUENCING!
        next_read_entity: 15
        read_entities:
          v_contact_list:
            entity_number: 12           # Different from write-side!
            files:
              - code: '0220121'         # 02-2-03-12-1
                type: v_
                name: v_contact_list
                path: 02_query_side/022_crm/0223_customer/0220121_v_contact_list.sql

          tv_contact:
            entity_number: 13           # Next entity on read-side
            files:
              - code: '0220130'         # 02-2-03-13-0 (first file)
                type: tv_
                name: tv_contact
                depends_on: [tv_company]
                path: 02_query_side/022_crm/0223_customer/0220130_tv_contact.sql
```

---

### 4. Missing Components (REVISED)

#### 4.1 Independent Read-Side Sequence Management

**Current**: Only write-side sequence tracking
**Needed**: Separate sequence counters for read-side

**Key Difference**:
- Write-side: Tracks entities in tb_* tables
- Read-side: Tracks ALL views (v_*, tv_*, mv_*) as separate entities
- **No derivation** - assign next available number

**Implementation Needed**:
```python
class DomainRegistry:
    def assign_read_entity_code(
        self,
        domain: str,
        subdomain: str,
        view_name: str,
        view_type: str  # 'v_', 'tv_', 'mv_'
    ) -> str:
        """
        Assign next read-side entity code.

        Example:
          domain = "crm" (code: 2)
          subdomain = "customer" (code: 03)
          view_name = "tv_contact"

        Returns:
          "0220130" (02-2-03-13-0)
          Where 13 is next_read_entity in this subdomain
        """
```

#### 4.2 Directory Hierarchy Generator

**Required Logic**:
```python
def get_tv_output_path(
    domain_code: str,
    subdomain_code: str,
    entity_code: str,
    domain_name: str,
    subdomain_name: str,
    view_name: str
) -> Path:
    """
    Generate hierarchical path for read-side file.

    Example:
      domain_code = "2"
      subdomain_code = "03"
      entity_code = "0220130"
      domain_name = "crm"
      subdomain_name = "customer"
      view_name = "tv_contact"

    Returns:
      0_schema/02_query_side/022_crm/0223_customer/0220130_tv_contact.sql
    """
    # Parse entity code
    # 0220130 → schema=0, layer=2, domain=2, subdomain=03, entity=13, file=0

    layer = "02_query_side"
    domain_path = f"0{domain_code}{subdomain_code[0]}_{domain_name}"
    subdomain_path = f"0{domain_code}{subdomain_code}_{subdomain_name}"
    filename = f"{entity_code}_{view_name}.sql"

    return Path("0_schema") / layer / domain_path / subdomain_path / filename
```

#### 4.3 File Splitting Logic (Unchanged)

**Each File Contains**:
```sql
-- 0220130_tv_contact.sql
CREATE TABLE crm.tv_contact (...);
ALTER TABLE ONLY crm.tv_contact ADD CONSTRAINT ...;
CREATE INDEX idx_tv_contact_tenant ON crm.tv_contact ...;
COMMENT ON TABLE crm.tv_contact IS '...';
COMMENT ON COLUMN crm.tv_contact.id IS '...';
CREATE FUNCTION crm.refresh_tv_contact() ...;
CREATE TRIGGER trg_tv_contact_cache_invalidation ...;
```

#### 4.4 Migration File Management

**Orchestrator Changes**:
```python
# AFTER
if include_tv:
    tv_migrations = self.schema_orchestrator.generate_table_view_migrations(
        entity_defs, registry
    )
    for migration in tv_migrations:  # Multiple files
        result.migrations.append(migration)
```

---

## Implementation Plan (REVISED)

### Phase 1: Registry Enhancement for Independent Read-Side Sequencing

**Objective**: Extend registry to support independent read-side entity tracking

#### TDD Cycle:

1. **RED**: Write failing tests
   ```python
   # tests/unit/registry/test_read_side_sequencing.py
   def test_independent_read_entity_assignment():
       """Should assign read-side entity codes independently"""
       registry = DomainRegistry()

       # Write-side has entity 36
       registry.assign_write_entity_code("crm", "customer", "Contact")
       # Returns: 0120361

       # Read-side should start fresh
       code1 = registry.assign_read_entity_code("crm", "customer", "tv_contact")
       code2 = registry.assign_read_entity_code("crm", "customer", "v_contact_summary")

       # Should be sequential on read-side, NOT related to write-side
       assert code1 == "0220130"  # Entity 13 (not 36!)
       assert code2 == "0220140"  # Entity 14

   def test_read_entity_sequence_per_subdomain():
       """Should track read entity sequences per subdomain"""
       registry = DomainRegistry()

       # Different subdomains have independent sequences
       crm_code = registry.assign_read_entity_code("crm", "customer", "tv_contact")
       catalog_code = registry.assign_read_entity_code("catalog", "product", "tv_product")

       # Both can be entity 1 in their respective subdomains
       assert crm_code.endswith("10")    # Entity 1, file 0
       assert catalog_code.endswith("10") # Entity 1, file 0

   def test_file_sequence_within_entity():
       """Should track file sequences within same read entity"""
       registry = DomainRegistry()

       # First file for tv_contact entity
       code1 = registry.assign_read_file_code("crm", "customer", "tv_contact", file_num=0)
       assert code1 == "0220130"  # Entity 13, file 0

       # Additional view file for same logical entity
       code2 = registry.assign_read_file_code("crm", "customer", "tv_contact", file_num=1)
       assert code2 == "0220131"  # Entity 13, file 1
   ```

2. **GREEN**: Minimal implementation
   - Add `next_read_entity` to subdomain tracking
   - Add `read_entities` dictionary separate from `write_entities`
   - Implement `assign_read_entity_code()`
   - Update YAML schema

3. **REFACTOR**: Clean up and optimize
   - Extract code formatting helpers
   - Add validation for code ranges
   - Improve error messages

4. **QA**: Verify phase completion
   - [ ] All tests pass
   - [ ] Read-side sequencing independent from write-side
   - [ ] File sequences increment correctly per entity
   - [ ] YAML schema documented

**Files to Modify**:
- `src/generators/schema/naming_conventions.py` (DomainRegistry class)
- `registry/domain_registry.yaml` (schema extension)
- `tests/unit/registry/test_read_side_sequencing.py` (new)

**Success Criteria**:
- Registry assigns read codes independently
- Sequences don't conflict with write-side
- YAML persistence works for both layers

---

### Phase 2: Path Generation Logic

**Objective**: Generate hierarchical paths for read-side files

#### TDD Cycle:

1. **RED**: Write failing tests
   ```python
   # tests/unit/generators/test_read_side_path_generator.py
   def test_generate_tv_path_from_code():
       """Should generate path from read-side code"""
       registry = DomainRegistry()

       # Given a read-side code
       code = "0220130"  # 02-2-03-13-0
       view_name = "tv_contact"

       path_gen = ReadSidePathGenerator(registry)
       path = path_gen.generate_path(code, view_name)

       expected = Path("0_schema/02_query_side/022_crm/0223_customer/0220130_tv_contact.sql")
       assert path == expected

   def test_parse_read_side_code():
       """Should parse read-side code components"""
       parser = ReadSideCodeParser()

       components = parser.parse("0220130")
       assert components.schema_prefix == "0"
       assert components.layer == "2"
       assert components.domain == "2"
       assert components.subdomain == "03"
       assert components.entity == "13"
       assert components.file_num == "0"

   def test_domain_subdomain_path_formatting():
       """Should format domain and subdomain paths correctly"""
       registry = DomainRegistry()

       # Domain path: 0{domain_code}{subdomain_first_digit}_{domain_name}
       domain_path = registry.format_domain_path("2", "03", "crm")
       assert domain_path == "022_crm"

       # Subdomain path: 0{domain_code}{subdomain_code}_{subdomain_name}
       subdomain_path = registry.format_subdomain_path("2", "03", "customer")
       assert subdomain_path == "0223_customer"
   ```

2. **GREEN**: Implement path generator
   - Create `ReadSidePathGenerator` class
   - Create `ReadSideCodeParser` helper
   - Implement directory hierarchy logic
   - Add path formatting methods to DomainRegistry

3. **REFACTOR**: Pattern compliance
   - Match existing generator patterns
   - Extract reusable path utilities
   - Add comprehensive docstrings

4. **QA**: Integration verification
   - [ ] Paths match reference structure exactly
   - [ ] Directories created as needed
   - [ ] Code parsing accurate
   - [ ] Domain/subdomain paths formatted correctly

**Files to Create**:
- `src/generators/schema/read_side_path_generator.py` (new)
- `src/generators/schema/code_parser.py` (new)
- `tests/unit/generators/test_read_side_path_generator.py` (new)

**Success Criteria**:
- Paths match `0_schema/02_query_side/0{D}{S}_{domain}/0{D}{SS}_{subdomain}/{code}_{view}.sql`
- Parent directories auto-created
- Code parsing tested

---

### Phase 3: File Splitting & Content Structuring

**Objective**: Split monolithic tv_ output into individual entity files

#### TDD Cycle:

1. **RED**: Write failing tests
   ```python
   # tests/unit/generators/test_tv_file_generator.py
   def test_generate_individual_tv_files():
       """Should generate separate file per tv_ entity"""
       entities = [create_contact_entity(), create_company_entity()]
       registry = DomainRegistry()

       generator = TableViewFileGenerator(entities, registry)
       files = generator.generate_files()

       assert len(files) == 2
       assert files[0].code == "0220120"  # tv_company
       assert files[0].name == "tv_company"
       assert files[0].content.startswith("CREATE TABLE")

       assert files[1].code == "0220130"  # tv_contact
       assert files[1].name == "tv_contact"

   def test_tv_file_structure():
       """Should include all components in file"""
       entity = create_contact_entity()
       registry = DomainRegistry()

       generator = TableViewFileGenerator([entity], registry)
       file = generator.generate_files()[0]

       # Check all components present
       assert "CREATE TABLE" in file.content
       assert "CREATE INDEX" in file.content
       assert "CREATE FUNCTION" in file.content  # refresh function
       assert "COMMENT ON TABLE" in file.content
       assert "CREATE TRIGGER" in file.content   # cache invalidation

   def test_dependency_order_preserved():
       """Should maintain topological order"""
       company = create_company_entity()
       contact = create_contact_entity()  # depends on company

       generator = TableViewFileGenerator([contact, company], registry)
       files = generator.generate_files()

       # Company first, contact second
       assert files[0].name == "tv_company"
       assert files[1].name == "tv_contact"
   ```

2. **GREEN**: Implement file generator
   - Refactor `generate_table_views()` to return list of file objects
   - Create `TableViewFile` dataclass
   - Extract per-entity content generation
   - Maintain dependency ordering

3. **REFACTOR**: Clean separation
   - Split TableViewGenerator responsibilities
   - Extract content formatting
   - Improve modularity

4. **QA**: Content verification
   - [ ] Each file contains complete tv_ definition
   - [ ] Dependency order maintained
   - [ ] All SQL components included
   - [ ] FraiseQL annotations present

**Files to Modify**:
- `src/generators/schema_orchestrator.py` (refactor generate_table_views)
- `src/generators/schema/table_view_generator.py` (add file-level generation)
- `src/generators/schema/table_view_file.py` (new dataclass)
- `tests/unit/schema/test_tv_file_generator.py` (new)

**Success Criteria**:
- One file per tv_ entity
- Complete SQL per file
- Topological order preserved
- Clean abstractions

---

### Phase 4: Orchestrator Integration with Registry Assignment

**Objective**: Update CLI orchestrator to assign codes and output hierarchical files

#### TDD Cycle:

1. **RED**: Write failing integration test
   ```python
   # tests/integration/test_hierarchical_tv_generation.py
   def test_generate_hierarchical_tv_with_code_assignment(tmp_path):
       """Should generate tv_ files with assigned codes"""
       # Setup: Contact entity defined in YAML
       orchestrator = CLIOrchestrator()
       registry = DomainRegistry()

       result = orchestrator.generate(
           entity_files=["entities/contact.yaml"],
           output_path=tmp_path,
           include_tv=True,
           registry=registry
       )

       # Check registry was updated with read-side code
       contact_entry = registry.get_read_entity("crm", "customer", "tv_contact")
       assert contact_entry is not None
       assert contact_entry.code == "0220130"

       # Check file exists at correct path
       expected_path = tmp_path / "0_schema/02_query_side/022_crm/0223_customer/0220130_tv_contact.sql"
       assert expected_path.exists()

       # Check content
       content = expected_path.read_text()
       assert "CREATE TABLE crm.tv_contact" in content
       assert "COMMENT ON TABLE crm.tv_contact IS" in content

   def test_multiple_tv_entities_sequential_codes(tmp_path):
       """Should assign sequential codes to multiple tv_ entities"""
       orchestrator = CLIOrchestrator()
       registry = DomainRegistry()

       result = orchestrator.generate(
           entity_files=["entities/company.yaml", "entities/contact.yaml"],
           output_path=tmp_path,
           include_tv=True,
           registry=registry
       )

       # Check sequential assignment
       company = registry.get_read_entity("crm", "customer", "tv_company")
       contact = registry.get_read_entity("crm", "customer", "tv_contact")

       assert company.code == "0220120"  # Entity 12
       assert contact.code == "0220130"  # Entity 13

       # Check both files exist
       assert (tmp_path / "0_schema/02_query_side/022_crm/0223_customer/0220120_tv_company.sql").exists()
       assert (tmp_path / "0_schema/02_query_side/022_crm/0223_customer/0220130_tv_contact.sql").exists()

   def test_registry_yaml_persisted(tmp_path):
       """Should persist assigned codes to registry YAML"""
       orchestrator = CLIOrchestrator()
       registry = DomainRegistry("registry/domain_registry.yaml")

       orchestrator.generate(
           entity_files=["entities/contact.yaml"],
           include_tv=True,
           registry=registry
       )

       # Reload registry from disk
       registry_reloaded = DomainRegistry("registry/domain_registry.yaml")
       contact = registry_reloaded.get_read_entity("crm", "customer", "tv_contact")

       assert contact.code == "0220130"
   ```

2. **GREEN**: Update orchestrator
   - Replace single-file logic with multi-file logic
   - Integrate ReadSidePathGenerator
   - Assign read-side codes before generation
   - Update MigrationFile creation loop
   - Persist registry after assignment

3. **REFACTOR**: Code quality
   - Extract orchestration helpers
   - Improve error handling
   - Add progress reporting per file
   - Transaction-like registry updates (rollback on error)

4. **QA**: Full pipeline test
   - [ ] CLI command works end-to-end
   - [ ] Files created in correct locations
   - [ ] Registry updated with read-side codes
   - [ ] Registry persisted to YAML
   - [ ] All tests pass

**Files to Modify**:
- `src/cli/orchestrator.py` (lines 424-437 + registry integration)
- `src/generators/schema/naming_conventions.py` (add save() method)
- `tests/integration/test_hierarchical_tv_generation.py` (new)

**Success Criteria**:
- `specql generate --include-tv` creates hierarchical structure
- Registry automatically assigns and persists codes
- Idempotent regeneration works (same codes on re-run)
- Backward compatibility option available

---

### Phase 5: Registry Schema Migration & Validation

**Objective**: Migrate existing registry to new schema and add validation

#### TDD Cycle:

1. **RED**: Write migration and validation tests
   ```python
   # tests/unit/registry/test_registry_migration.py
   def test_migrate_old_schema_to_new():
       """Should migrate old registry schema to new format"""
       old_yaml = """
       domains:
         '2':
           name: crm
           subdomains:
             '03':
               name: customer
               next_entity_sequence: 37
               entities:
                 Contact:
                   table_code: '0120361'
                   entity_code: CNT
       """

       migrator = RegistryMigrator()
       new_registry = migrator.migrate(old_yaml)

       # Check new structure
       assert "write_entities" in new_registry['domains']['2']['subdomains']['03']
       assert "read_entities" in new_registry['domains']['2']['subdomains']['03']
       assert new_registry['domains']['2']['subdomains']['03']['next_write_entity'] == 37
       assert new_registry['domains']['2']['subdomains']['03']['next_read_entity'] == 1

   def test_validate_registry_schema():
       """Should validate registry has correct schema"""
       validator = RegistryValidator()

       # Valid registry
       valid_registry = load_test_registry("valid_registry.yaml")
       assert validator.validate(valid_registry) == True

       # Invalid: missing read_entities
       invalid_registry = load_test_registry("invalid_registry.yaml")
       errors = validator.validate(invalid_registry)
       assert "missing read_entities" in errors

   def test_detect_code_conflicts():
       """Should detect conflicting codes"""
       registry = DomainRegistry()

       # Assign same code twice (should error)
       registry.assign_read_entity_code("crm", "customer", "tv_contact")

       with pytest.raises(CodeConflictError):
           # Manually set conflicting code
           registry.force_assign_code("0220130", "crm", "customer", "tv_other")
   ```

2. **GREEN**: Implement migration and validation
   - Create `RegistryMigrator` class
   - Create `RegistryValidator` class
   - Add migration CLI command
   - Add validation to DomainRegistry.__init__()

3. **REFACTOR**: Robustness
   - Add backup before migration
   - Comprehensive validation rules
   - Clear error messages

4. **QA**: Migration verification
   - [ ] Old registries migrate successfully
   - [ ] Validation catches errors
   - [ ] Backup created before migration
   - [ ] No data loss

**Files to Create**:
- `src/registry/migrator.py` (new)
- `src/registry/validator.py` (new)
- `src/cli/commands/migrate_registry.py` (new)
- `tests/unit/registry/test_registry_migration.py` (new)

**Success Criteria**:
- Existing registries migrate without data loss
- Validation prevents invalid states
- Migration is idempotent

---

### Phase 6: Documentation & Examples

**Objective**: Document new system and provide examples

#### TDD Cycle:

1. **RED**: Documentation tests
   ```python
   def test_documentation_complete():
       """Should have complete documentation"""
       assert Path("docs/architecture/READ_SIDE_ORGANIZATION.md").exists()
       assert Path("docs/guides/REGISTRY_SCHEMA.md").exists()

   def test_examples_valid():
       """Should have working examples"""
       examples = Path("docs/examples/read_side_codes")
       assert (examples / "crm_customer_example.yaml").exists()

       # Examples should parse correctly
       registry = DomainRegistry(str(examples / "crm_customer_example.yaml"))
       assert registry is not None
   ```

2. **GREEN**: Create documentation
   - Architecture overview
   - Registry schema reference
   - Code format specification
   - Migration guide
   - Examples for common scenarios

3. **REFACTOR**: Documentation quality
   - Add diagrams
   - Include working examples
   - Cross-reference related docs

4. **QA**: Review
   - [ ] Docs accurate
   - [ ] Examples tested
   - [ ] Migration guide validated

**Files to Create**:
- `docs/architecture/READ_SIDE_ORGANIZATION.md`
- `docs/guides/REGISTRY_SCHEMA.md`
- `docs/guides/CODE_FORMAT_SPECIFICATION.md`
- `docs/examples/read_side_codes/crm_customer_example.yaml`

**Success Criteria**:
- Complete documentation
- Working examples
- Migration guide tested

---

## Technical Decisions (REVISED)

### Decision 1: Independent Read-Side Sequencing

**Question**: How to assign read-side entity codes?

**Options**:
1. **Derive from write-side**: Map write entity → read entity (1:1)
2. **Independent sequencing**: Assign codes independently on read-side
3. **Hybrid**: Start from write-side but allow gaps

**Chosen**: **Option 2 - Independent sequencing**

**Reasoning**:
- Reference system shows independent numbering
- Read-side can have multiple views per write entity (v_*, tv_*, mv_*)
- Read-side can have views not tied to specific write entities
- Simpler mental model: each layer has its own sequence
- Matches actual reference structure

**Evidence from reference**:
```
Write: 014111, 014112 (location has 2 files)
Read:  024111, 024122, 024130, 024141 (4 different entities)
```

**Confidence**: 10/10

---

### Decision 2: Registry Schema Structure

**Question**: How to organize write vs read entities in registry?

**Options**:
1. **Flat**: Mix write and read in same `entities` dict
2. **Separate**: `write_entities` and `read_entities` dicts
3. **Nested layers**: Separate top-level sections for each layer

**Chosen**: **Option 2 - Separate dicts per subdomain**

**Reasoning**:
- Clear separation of concerns
- Independent sequence tracking
- Easier to understand
- Maintains subdomain grouping
- Allows different metadata per layer

**Structure**:
```yaml
subdomains:
  '03':
    next_write_entity: 37
    write_entities: {...}
    next_read_entity: 15
    read_entities: {...}
```

**Confidence**: 9/10

---

### Decision 3: Code Assignment Timing

**Question**: When to assign read-side codes?

**Options**:
1. **On demand**: Assign during generation
2. **Pre-assigned**: Assign during entity definition
3. **Hybrid**: Check registry, assign if missing

**Chosen**: **Option 3 - Hybrid (check registry first)**

**Reasoning**:
- Idempotent generation (same code on re-run)
- Supports manual code assignment
- Allows code reuse after deletion
- Registry is source of truth

**Implementation**:
```python
def get_or_assign_read_code(entity_name: str) -> str:
    existing = registry.get_read_entity(domain, subdomain, entity_name)
    if existing:
        return existing.code
    return registry.assign_read_entity_code(domain, subdomain, entity_name)
```

**Confidence**: 9/10

---

### Decision 4: File Organization Granularity

**Question**: One file per entity or split by component?

**Options**:
1. **Single file**: All components together
2. **Split by component**: Separate files for DDL, functions, annotations
3. **Hybrid**: DDL + indexes together, functions separate

**Chosen**: **Option 1 - Single file per entity**

**Reasoning**:
- Matches reference structure (024130_tv_location.sql has everything)
- Atomic updates
- Simpler to manage
- Easier dependency tracking

**Confidence**: 10/10

---

## Risk Assessment (REVISED)

### Risk 1: Registry Conflicts During Concurrent Development

**Impact**: High
**Probability**: Medium

**Scenario**: Multiple developers generate views simultaneously

**Mitigation**:
- Add advisory locks during code assignment
- Validation on registry load
- Clear error messages for conflicts
- Document merge conflict resolution

---

### Risk 2: Code Exhaustion in Subdomains

**Impact**: Medium
**Probability**: Low

**Scenario**: Subdomain has >9 entities (single digit limit)

**Mitigation**:
- Document limit clearly (max 9 entities per subdomain per layer)
- Add validation to prevent overflow
- Guide for subdomain restructuring
- Consider hexadecimal (0-F) if needed

**Note**: Reference uses single digit (0-9), so this is a real constraint

---

### Risk 3: Migration Errors for Existing Registries

**Impact**: High
**Probability**: Medium

**Mitigation**:
- Automatic backup before migration
- Comprehensive migration tests
- Rollback capability
- Validation after migration
- Clear migration documentation

---

### Risk 4: Path Generation Edge Cases

**Impact**: Medium
**Probability**: Low

**Scenario**: Special characters, long names, edge cases

**Mitigation**:
- Sanitize entity names for filesystem
- Validate generated paths
- Document naming limitations
- Comprehensive path tests

---

## Success Criteria (REVISED)

### Phase Completion
- [ ] Phase 1: Registry supports independent read-side sequencing
- [ ] Phase 2: Paths generated from codes match reference
- [ ] Phase 3: Files split correctly with complete content
- [ ] Phase 4: CLI assigns codes and generates hierarchical structure
- [ ] Phase 5: Registry schema migrated and validated
- [ ] Phase 6: Documentation complete with examples

### Overall Success
- [ ] `specql generate --include-tv` creates hierarchical structure
- [ ] Paths match: `0_schema/02_query_side/0{D}{S}_{domain}/0{D}{SS}_{subdomain}/{code}_{view}.sql`
- [ ] Registry tracks read entities independently from write
- [ ] Codes assigned sequentially per subdomain
- [ ] Registry persists to YAML automatically
- [ ] Migration from old schema works
- [ ] All tests pass (unit + integration)
- [ ] Documentation complete with working examples

---

## Code Format Reference

### Format: `0SDDSSEV`

| Component | Positions | Values | Example | Meaning |
|-----------|-----------|--------|---------|---------|
| Schema prefix | 1 | `0` | `0` | Always 0 for schema |
| Layer | 2 | `1`=write, `2`=read | `2` | Read-side |
| Domain | 3-4 | `01-99` | `22` | CRM domain |
| Subdomain | 5-6 | `01-99` | `03` | Customer subdomain |
| Entity | 7 | `0-9` | `3` | 3rd entity in subdomain |
| File | 8 | `0-9` | `0` | First file for entity |

### Examples

| Code | Layer | Domain | Subdomain | Entity | File | Full Path |
|------|-------|--------|-----------|--------|------|-----------|
| `0120361` | Write (1) | CRM (2) | Customer (03) | 36 | 1 | `01_write_side/012_crm/0123_customer/01236_contact/0120361_tb_contact.sql` |
| `0220130` | Read (2) | CRM (2) | Customer (03) | 13 | 0 | `02_query_side/022_crm/0223_customer/0220130_tv_contact.sql` |
| `024130` | Read (2) | Dim (4) | Geo (41) | 3 | 0 | `02_query_side/024_dim/0241_geo/024130_tv_location.sql` |

### Path Pattern

```
0_schema/
└── 0{layer}_{layer_name}/
    └── 0{domain}{subdomain[0]}_{domain_name}/
        └── 0{domain}{subdomain}_{subdomain_name}/
            └── {full_code}_{entity_name}.sql
```

---

## Timeline Estimate (REVISED)

**Phase 1**: Independent Read Sequencing - 6-8 hours
**Phase 2**: Path Generation - 4-5 hours
**Phase 3**: File Splitting - 4-6 hours
**Phase 4**: Orchestrator + Registry - 5-7 hours
**Phase 5**: Migration & Validation - 4-5 hours
**Phase 6**: Documentation - 3-4 hours

**Total Estimate**: 26-35 hours (3-4 working days)

---

## Open Questions

1. Should entity sequence support hex (0-F) or stay decimal (0-9)?
2. How to handle subdomain with >9 entities?
3. Should we support custom code assignment in YAML?
4. Migration tool for existing 200_table_views.sql files?
5. How to handle view dependencies across domains?
6. Should refresh functions optionally be in separate files?

---

## Next Steps

1. **Review** this REVISED plan
2. **Create feature branch**: `feature/hierarchical-tv-organization`
3. **Begin Phase 1**: Registry enhancement with independent sequencing
4. **Set up test fixtures** from reference structure
5. **Create migration plan** for existing registry files

---

*Phased TDD Development Methodology*
*Focus: Discipline • Quality • Predictable Progress*
