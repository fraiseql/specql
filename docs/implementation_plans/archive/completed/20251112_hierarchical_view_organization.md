# Hierarchical View Organization - Gap Analysis & Implementation Plan

**Date**: 2025-11-12
**Status**: Planning
**Complexity**: Complex - Phased TDD Approach Required

## Executive Summary

Currently, SpecQL generates all table views (tv_*) into a single monolithic file `200_table_views.sql`. The goal is to implement hierarchical organization matching the reference system in `printoptim_specql`, where views are organized into individual files with hex-based prefixes matching the write-side (01_write_side) numbering system.

**Current State**: All tv_* tables → `200_table_views.sql` (single file)
**Target State**: Individual tv_* files organized hierarchically with hex prefixes matching table codes

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

**Generation Logic** (`src/generators/schema_orchestrator.py:219-258`):
```python
def generate_table_views(self, entities: list[EntityDefinition]) -> str:
    # Resolves dependencies topologically
    # Generates all tv_ tables + refresh functions
    # Returns concatenated SQL string  # ❌ Monolithic output
    return "\n\n".join(parts)
```

**Key Characteristics**:
- ✅ Topological dependency resolution working
- ✅ FraiseQL annotations included
- ✅ Trinity pattern applied
- ❌ No per-entity file splitting
- ❌ No hierarchical directory structure
- ❌ No hex prefix assignment for tv_ files
- ❌ No registry integration for tv_ codes

---

### 2. Target Implementation (Reference System)

**File Structure Example**:
```
0_schema/
├── 01_write_side/
│   └── 014_dim/
│       └── 0141_geo/
│           └── 01411_location/
│               ├── 014111_tb_location_info.sql
│               └── 014112_tb_location.sql        # Table code: 014112
│
├── 02_query_side/                                 # READ SIDE
│   └── 024_dim/                                   # Same domain structure
│       └── 0241_geo/                              # Same subdomain
│           ├── 02411_v_count_allocations_by_location.sql
│           ├── 02412_v_location.sql
│           ├── 02413_tv_location.sql             # Table view! Code: 02413
│           └── 02414_v_flat_location_for_rust_tree.sql
```

**Hex Prefix Pattern** (from tb_location.sql):
```sql
COMMENT ON TABLE tenant.tb_location IS
  '[Table: 014112 | Write-Side.Dimensions.Geography.Location] ...';
```

**Breakdown**:
- `01` = Schema layer (write_side)
- `4` = Domain code (dim = dimensions)
- `11` = Subdomain code (geo)
- `2` = Entity sequence (location is 2nd entity in geo)

**For tv_location.sql** (`02_query_side/024_dim/0241_geo/02413_tv_location.sql`):
- `02` = Schema layer (read_side) ← **KEY DIFFERENCE**
- `4` = Domain code (dim)
- `13` = File sequence within subdomain/entity group

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
            table_code: '012036'  # Write-side code only!
            entity_code: CNT
```

**What's Missing for TV_**:
- ❌ No read_side (02_*) code assignments
- ❌ No file sequence tracking per entity
- ❌ No tv_file_code field in entity registry
- ❌ No view-specific metadata

**What's Needed**:
```yaml
# Proposed structure
domains:
  '2':
    name: crm
    subdomains:
      '03':
        name: customer
        entities:
          Contact:
            table_code: '012036'        # Write-side
            tv_code: '02236'            # Read-side base code
            next_tv_file_sequence: 4    # For additional views
            entity_code: CNT
            tv_files:                   # Track all tv_ files
              - code: '022361'          # tv_contact.sql
                type: table_view
                name: tv_contact
              - code: '022362'          # Additional view
                type: regular_view
                name: v_contact_summary
```

---

### 4. Missing Components

#### 4.1 Code Derivation Logic

**Current**: Only write-side (01) codes exist
**Needed**: Derive read-side (02) codes from write-side codes

**Derivation Rule**:
```
Write-side code: 012036 (Contact table)
  01 = write_side
  2  = domain (crm)
  03 = subdomain (customer)
  6  = entity sequence

Read-side tv_ code: 022361
  02 = read_side (schema layer change)
  2  = domain (same)
  36 = subdomain code (03) + entity sequence (6)
  1  = first tv_ file for this entity
```

**Implementation Needed**:
- Function to derive tv_code from table_code
- Registry updates when tv_ is generated
- File sequence management

#### 4.2 Directory Hierarchy Generator

**Current**: Flat file output
**Needed**: Hierarchical directory creation matching domain/subdomain structure

**Required Logic**:
```python
def get_tv_output_path(entity: Entity, registry: DomainRegistry) -> Path:
    """
    Generate hierarchical path for tv_ file.

    Example:
      entity.name = "Location"
      domain = "dim" (code: 4)
      subdomain = "geo" (code: 41)
      tv_code = "02413"

    Returns:
      0_schema/02_query_side/024_dim/0241_geo/02413_tv_location.sql
    """
```

#### 4.3 File Splitting Logic

**Current**: Single concatenated string
**Needed**: Individual files with:
- Table DDL
- Indexes
- Refresh function
- FraiseQL annotations
- Triggers

**Each File Contains** (per reference):
```sql
-- 02413_tv_location.sql
CREATE TABLE public.tv_location (...);
ALTER TABLE ONLY public.tv_location ADD CONSTRAINT ...;
CREATE INDEX idx_tv_location_organization ON public.tv_location ...;
COMMENT ON TABLE public.tv_location IS '...';
COMMENT ON COLUMN public.tv_location.id IS '...';
CREATE TRIGGER trg_tv_location_cache_invalidation ...;
```

#### 4.4 Migration File Management

**Current**: Single MigrationFile object
**Needed**: Multiple MigrationFile objects, one per entity

**Orchestrator Changes**:
```python
# BEFORE
if include_tv:
    tv_sql = self.schema_orchestrator.generate_table_views(entity_defs)
    migration = MigrationFile(...)  # Single file
    result.migrations.append(migration)

# AFTER
if include_tv:
    tv_migrations = self.schema_orchestrator.generate_table_view_migrations(
        entity_defs, registry
    )
    for migration in tv_migrations:  # Multiple files
        result.migrations.append(migration)
```

---

## Implementation Plan

### Phase 1: Registry Enhancement for Read-Side Codes

**Objective**: Extend domain registry to support tv_ code assignment and tracking

#### TDD Cycle:

1. **RED**: Write failing tests
   ```python
   # tests/unit/registry/test_tv_code_assignment.py
   def test_derive_tv_code_from_table_code():
       """Should derive read-side code from write-side code"""
       registry = DomainRegistry()
       tv_code = registry.derive_tv_code("012036")
       assert tv_code == "022360"  # Base code, sequence 0

   def test_assign_tv_file_code():
       """Should assign sequential file codes for tv_ files"""
       registry = DomainRegistry()
       code1 = registry.assign_tv_file_code("Contact", "table_view")
       code2 = registry.assign_tv_file_code("Contact", "regular_view")
       assert code1 == "022361"
       assert code2 == "022362"
   ```

2. **GREEN**: Minimal implementation
   - Add `derive_tv_code()` to DomainRegistry
   - Add `assign_tv_file_code()` with sequence tracking
   - Update YAML schema to support tv_code and tv_files

3. **REFACTOR**: Clean up and optimize
   - Extract code derivation logic
   - Add validation for code ranges
   - Improve error messages

4. **QA**: Verify phase completion
   - [ ] All tests pass
   - [ ] Registry can derive tv_ codes
   - [ ] File sequences increment correctly
   - [ ] YAML schema documented

**Files to Modify**:
- `src/generators/schema/naming_conventions.py` (DomainRegistry class)
- `registry/domain_registry.yaml` (schema extension)
- `tests/unit/registry/test_tv_code_assignment.py` (new)

**Success Criteria**:
- Registry can derive tv_code from table_code
- Registry tracks file sequences per entity
- YAML persistence works

---

### Phase 2: Path Generation Logic

**Objective**: Generate hierarchical paths matching reference structure

#### TDD Cycle:

1. **RED**: Write failing tests
   ```python
   # tests/unit/generators/test_tv_path_generator.py
   def test_generate_tv_path():
       """Should generate hierarchical path for tv_ file"""
       entity = create_test_entity("Location", domain="dim", subdomain="geo")
       registry = DomainRegistry()

       path_gen = TableViewPathGenerator(registry)
       path = path_gen.generate_path(entity, tv_code="02413")

       expected = Path("0_schema/02_query_side/024_dim/0241_geo/02413_tv_location.sql")
       assert path == expected

   def test_create_directories():
       """Should create parent directories if they don't exist"""
       path_gen = TableViewPathGenerator(registry)
       path = path_gen.generate_path(entity, tv_code="02413")

       assert path.parent.exists()
   ```

2. **GREEN**: Implement path generator
   - Create `TableViewPathGenerator` class
   - Implement directory hierarchy logic
   - Add path formatting for domain/subdomain codes

3. **REFACTOR**: Pattern compliance
   - Match existing generator patterns
   - Extract reusable path utilities
   - Add docstrings

4. **QA**: Integration verification
   - [ ] Paths match reference structure
   - [ ] Directories created as needed
   - [ ] Path formatting correct

**Files to Create**:
- `src/generators/schema/table_view_path_generator.py` (new)
- `tests/unit/generators/test_tv_path_generator.py` (new)

**Success Criteria**:
- Paths match `02_query_side/0{D}{SS}_{domain}/{0D}{SS}_{subdomain}/{code}_tv_{entity}.sql`
- Parent directories auto-created
- Path generation tested

---

### Phase 3: File Splitting & Content Structuring

**Objective**: Split monolithic tv_ output into individual entity files

#### TDD Cycle:

1. **RED**: Write failing tests
   ```python
   # tests/unit/generators/test_tv_file_splitter.py
   def test_split_tv_content():
       """Should split tv_ content into separate files"""
       entities = [create_contact_entity(), create_company_entity()]
       generator = TableViewFileGenerator(entities, registry)

       files = generator.generate_files()
       assert len(files) == 2
       assert files[0].name == "tv_contact"
       assert "CREATE TABLE" in files[0].content
       assert "CREATE TRIGGER" in files[0].content

   def test_dependency_order_preserved():
       """Should maintain topological order in file list"""
       entities = [company, contact]  # contact depends on company
       files = generator.generate_files()

       assert files[0].name == "tv_company"  # Company first
       assert files[1].name == "tv_contact"  # Contact second
   ```

2. **GREEN**: Implement file splitter
   - Refactor `generate_table_views()` to return list of files
   - Extract per-entity content generation
   - Maintain dependency ordering

3. **REFACTOR**: Clean separation of concerns
   - Split TableViewGenerator into concerns
   - Extract file content formatting
   - Improve modularity

4. **QA**: Content verification
   - [ ] Each file contains complete tv_ definition
   - [ ] Dependency order maintained
   - [ ] FraiseQL annotations included

**Files to Modify**:
- `src/generators/schema_orchestrator.py` (refactor generate_table_views)
- `src/generators/schema/table_view_generator.py` (add file-level generation)
- `tests/unit/schema/test_table_view_file_generation.py` (new)

**Success Criteria**:
- One file per entity
- Complete SQL per file (table + indexes + refresh + annotations)
- Topological order preserved

---

### Phase 4: Orchestrator Integration

**Objective**: Update CLI orchestrator to output hierarchical tv_ files

#### TDD Cycle:

1. **RED**: Write failing integration test
   ```python
   # tests/integration/test_hierarchical_tv_generation.py
   def test_generate_hierarchical_tv_files(tmp_path):
       """Should generate tv_ files in hierarchical structure"""
       orchestrator = CLIOrchestrator()
       result = orchestrator.generate(
           entity_files=["entities/contact.yaml"],
           output_path=tmp_path,
           include_tv=True
       )

       # Check file exists at correct path
       expected_path = tmp_path / "0_schema/02_query_side/022_crm/0223_customer/022361_tv_contact.sql"
       assert expected_path.exists()

       # Check content
       content = expected_path.read_text()
       assert "CREATE TABLE crm.tv_contact" in content

   def test_multiple_entities_correct_paths():
       """Should generate multiple entities in correct subdomain paths"""
       # Test cross-subdomain organization
   ```

2. **GREEN**: Update orchestrator
   - Replace single-file logic with multi-file logic
   - Integrate TableViewPathGenerator
   - Update MigrationFile creation loop

3. **REFACTOR**: Code quality
   - Extract orchestration helpers
   - Improve error handling
   - Add progress reporting per file

4. **QA**: Full pipeline test
   - [ ] CLI command works end-to-end
   - [ ] Files created in correct locations
   - [ ] Registry updated with tv_ codes
   - [ ] All tests pass

**Files to Modify**:
- `src/cli/orchestrator.py` (lines 424-437)
- `tests/integration/test_hierarchical_tv_generation.py` (new)

**Success Criteria**:
- `specql generate --include-tv` creates hierarchical structure
- Registry automatically updated
- Backward compatibility maintained (optional single-file mode?)

---

### Phase 5: Registry Persistence & Migration

**Objective**: Auto-update registry when tv_ files are generated

#### TDD Cycle:

1. **RED**: Write registry update tests
   ```python
   # tests/unit/registry/test_tv_registry_persistence.py
   def test_registry_updated_after_tv_generation():
       """Should persist tv_code to registry after generation"""
       registry = DomainRegistry()
       generator = TableViewOrchestrator(registry)

       generator.generate_table_view_file(contact_entity)

       # Check registry was updated
       entity_entry = registry.get_entity("Contact")
       assert entity_entry.tv_code == "022361"
       assert entity_entry.tv_files[0]["code"] == "022361"

   def test_registry_yaml_updated():
       """Should write updates to YAML file"""
       # Verify YAML file contains new tv_code
   ```

2. **GREEN**: Implement persistence
   - Add `save()` method to DomainRegistry
   - Auto-save after tv_ code assignment
   - Update YAML preserving structure

3. **REFACTOR**: Robustness
   - Add backup before writing
   - Validate YAML after save
   - Add rollback on error

4. **QA**: Persistence verification
   - [ ] Registry YAML updated after generation
   - [ ] tv_code persisted correctly
   - [ ] File sequences tracked
   - [ ] No data loss

**Files to Modify**:
- `src/generators/schema/naming_conventions.py` (add save())
- `tests/unit/registry/test_tv_registry_persistence.py` (new)

**Success Criteria**:
- Registry automatically updated after tv_ generation
- YAML file reflects tv_ codes
- Idempotent regeneration works

---

### Phase 6: Documentation & Migration Guide

**Objective**: Document new system and provide migration path

#### TDD Cycle:

1. **RED**: Write documentation tests (linting, completeness)
   ```python
   def test_documentation_complete():
       """Should have docs for hierarchical tv_ organization"""
       assert Path("docs/architecture/HIERARCHICAL_TV_ORGANIZATION.md").exists()

   def test_migration_guide_exists():
       """Should provide migration guide from 200_table_views.sql"""
   ```

2. **GREEN**: Create documentation
   - Architecture overview
   - Code derivation rules
   - Migration guide from single-file

3. **REFACTOR**: Documentation quality
   - Add diagrams
   - Include examples
   - Cross-reference related docs

4. **QA**: Review
   - [ ] Docs accurate
   - [ ] Examples tested
   - [ ] Migration guide validated

**Files to Create**:
- `docs/architecture/HIERARCHICAL_TV_ORGANIZATION.md`
- `docs/guides/MIGRATION_SINGLE_TO_HIERARCHICAL_TV.md`

**Success Criteria**:
- Complete documentation
- Migration guide tested
- Examples working

---

## Technical Decisions

### Decision 1: Code Derivation Algorithm

**Question**: How to derive tv_code from table_code?

**Options**:
1. **Sequential**: tv_code = table_code + 1000 (e.g., 012036 → 022037)
2. **Layer-based**: Replace first 2 digits (01 → 02), keep rest (012036 → 022036)
3. **Independent**: Assign tv_codes independently from table_codes

**Chosen**: **Option 2 - Layer-based derivation**

**Reasoning**:
- Maintains domain/subdomain/entity alignment
- Easy to understand mapping (write ↔ read)
- Matches reference structure pattern
- Preserves entity grouping in file system

**Confidence**: 9/10

---

### Decision 2: File Organization Granularity

**Question**: One file per entity or split by component (DDL, refresh, annotations)?

**Options**:
1. **Single file**: All components in one file (table + refresh + annotations)
2. **Split by component**: Separate files for DDL, functions, annotations
3. **Hybrid**: DDL + indexes in one file, refresh in another

**Chosen**: **Option 1 - Single file per entity**

**Reasoning**:
- Matches reference structure (see `02413_tv_location.sql`)
- Simpler to manage and understand
- Atomic updates (all or nothing)
- Easier dependency tracking

**Confidence**: 10/10

---

### Decision 3: Registry Schema Extension

**Question**: How to track tv_ files in registry?

**Options**:
1. **Flat**: Add `tv_code` field only
2. **List**: Add `tv_files` array with metadata
3. **Nested**: Create separate `read_side` section in registry

**Chosen**: **Option 2 - List with metadata**

**Reasoning**:
- Supports multiple views per entity (tv_*, v_*, mv_*)
- Tracks file types (table_view, regular_view, materialized_view)
- Extensible for future view types
- Maintains backward compatibility

**Confidence**: 8/10

---

## Risk Assessment

### Risk 1: Registry Merge Conflicts

**Impact**: High
**Probability**: Medium

**Mitigation**:
- Document YAML structure clearly
- Add validation on load
- Consider version control best practices doc

---

### Risk 2: Breaking Changes for Existing Users

**Impact**: High
**Probability**: High

**Mitigation**:
- Add `--tv-output-mode=single|hierarchical` flag
- Default to `single` for backward compatibility
- Deprecation notice for single-file mode
- Provide migration tool

---

### Risk 3: Path Generation Edge Cases

**Impact**: Medium
**Probability**: Medium

**Mitigation**:
- Comprehensive path generation tests
- Handle special characters in entity names
- Validate generated paths
- Document naming limitations

---

## Success Criteria

### Phase Completion
- [ ] Phase 1: Registry can assign and track tv_ codes
- [ ] Phase 2: Paths generated match reference structure
- [ ] Phase 3: Files split correctly with complete content
- [ ] Phase 4: CLI generates hierarchical structure
- [ ] Phase 5: Registry persisted after generation
- [ ] Phase 6: Documentation complete

### Overall Success
- [ ] `specql generate --include-tv` creates hierarchical structure
- [ ] Paths match: `02_query_side/0{D}{SS}_{domain}/{0D}{SS}_{subdomain}/{code}_tv_{entity}.sql`
- [ ] Registry tracks all tv_ files with codes
- [ ] Backward compatibility maintained
- [ ] All tests pass (unit + integration)
- [ ] Documentation complete
- [ ] Migration guide validated

---

## Dependencies

### External Dependencies
- Domain registry YAML schema (registry/domain_registry.yaml)
- Reference structure (../printoptim_specql/reference_sql)
- Existing TableViewGenerator logic

### Internal Dependencies
- DomainRegistry class (naming_conventions.py)
- TableViewGenerator (table_view_generator.py)
- CLIOrchestrator (orchestrator.py)
- MigrationFile model

---

## Timeline Estimate

**Phase 1**: Registry Enhancement - 4-6 hours
**Phase 2**: Path Generation - 3-4 hours
**Phase 3**: File Splitting - 4-6 hours
**Phase 4**: Orchestrator Integration - 3-4 hours
**Phase 5**: Registry Persistence - 2-3 hours
**Phase 6**: Documentation - 2-3 hours

**Total Estimate**: 18-26 hours (2-3 working days)

---

## Open Questions

1. Should we support custom path templates in specql.yaml?
2. How to handle view dependencies that cross domains?
3. Should refresh functions be in separate files?
4. Migration tool for existing 200_table_views.sql files?
5. Naming convention for non-tv_ views (v_, mv_)?

---

**Next Steps**:
1. Review this plan with stakeholders
2. Begin Phase 1: Registry Enhancement
3. Set up test fixtures for reference structure validation
4. Create feature branch: `feature/hierarchical-tv-organization`

---

*Phased TDD Development Methodology*
*Focus: Discipline • Quality • Predictable Progress*
