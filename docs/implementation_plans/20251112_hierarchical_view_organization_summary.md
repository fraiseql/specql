# Hierarchical View Organization - Quick Summary

**Full Plan**: `20251112_hierarchical_view_organization.md`

---

## The Gap

**Current**: All tv_* tables → single `200_table_views.sql` file
**Target**: Hierarchical structure matching reference system

```
# CURRENT
output/
└── 200_table_views.sql                          # Everything in one file

# TARGET (matching ../printoptim_specql/reference_sql)
0_schema/
├── 01_write_side/
│   └── 014_dim/0141_geo/01411_location/
│       └── 014112_tb_location.sql               # Table code: 014112
└── 02_query_side/
    └── 024_dim/0241_geo/
        ├── 02411_v_count_allocations.sql
        ├── 02412_v_location.sql
        └── 02413_tv_location.sql                # TV code: 02413
```

---

## Key Missing Components

### 1. Read-Side Code Assignment
- **Current**: Only write-side codes (01*) in registry
- **Needed**: Read-side tv_ codes (02*) derived from write-side
- **Example**: `table_code: 014112` → `tv_code: 024130`

### 2. Hierarchical Path Generation
- **Current**: Flat file output
- **Needed**: `02_query_side/0{D}{SS}_{domain}/{0D}{SS}_{subdomain}/{code}_tv_{entity}.sql`

### 3. File Splitting
- **Current**: Monolithic concatenated string
- **Needed**: One file per entity with complete DDL + refresh + annotations

### 4. Registry Tracking
- **Current**: No tv_ file tracking
- **Needed**: Track tv_code, file sequences, and metadata per entity

---

## Implementation Phases

### Phase 1: Registry Enhancement (4-6 hours)
**Goal**: Support tv_ code derivation and tracking

**Changes**:
- Add `derive_tv_code()` to DomainRegistry
- Add `tv_code` and `tv_files` to YAML schema
- Track file sequences per entity

**Test**: `tests/unit/registry/test_tv_code_assignment.py`

---

### Phase 2: Path Generation (3-4 hours)
**Goal**: Generate hierarchical paths

**Changes**:
- Create `TableViewPathGenerator` class
- Implement domain/subdomain path logic
- Auto-create parent directories

**Test**: `tests/unit/generators/test_tv_path_generator.py`

---

### Phase 3: File Splitting (4-6 hours)
**Goal**: Split monolithic output into individual files

**Changes**:
- Refactor `generate_table_views()` to return list
- Extract per-entity content generation
- Maintain topological ordering

**Test**: `tests/unit/schema/test_table_view_file_generation.py`

---

### Phase 4: Orchestrator Integration (3-4 hours)
**Goal**: CLI outputs hierarchical structure

**Changes**:
- Update `src/cli/orchestrator.py:424-437`
- Replace single MigrationFile with multiple
- Integrate path generator

**Test**: `tests/integration/test_hierarchical_tv_generation.py`

---

### Phase 5: Registry Persistence (2-3 hours)
**Goal**: Auto-save tv_ codes to registry

**Changes**:
- Add `save()` to DomainRegistry
- Auto-update after tv_ generation
- Preserve YAML structure

**Test**: `tests/unit/registry/test_tv_registry_persistence.py`

---

### Phase 6: Documentation (2-3 hours)
**Goal**: Document system and migration path

**Deliverables**:
- Architecture overview
- Code derivation rules
- Migration guide from single-file

---

## Code Derivation Rule

**From write-side to read-side**:
```
Write-side: 014112 (tb_location)
  01 = write_side
  4  = domain (dimensions)
  11 = subdomain (geo)
  2  = entity sequence

Read-side: 024130 (tv_location, first file)
  02 = read_side (schema layer change)
  4  = domain (same)
  13 = file position in subdomain
  0  = base entity file
```

**Pattern**:
- Schema layer changes: `01` → `02`
- Domain/subdomain preserved
- Sequential file numbering within subdomain

---

## Key Decisions

### 1. Code Derivation
**Choice**: Layer-based derivation (01 → 02, keep domain/subdomain)
**Why**: Maintains alignment, easy to understand, matches reference

### 2. File Organization
**Choice**: Single file per entity (all components together)
**Why**: Matches reference, atomic updates, simpler management

### 3. Registry Schema
**Choice**: Add `tv_files` array with metadata
**Why**: Supports multiple views, tracks types, extensible

---

## Success Criteria

- ✅ `specql generate --include-tv` creates hierarchical structure
- ✅ Paths match: `02_query_side/0{D}{SS}_{domain}/.../{code}_tv_{entity}.sql`
- ✅ Registry tracks all tv_ codes and files
- ✅ Backward compatibility maintained
- ✅ All tests pass
- ✅ Documentation complete

---

## Timeline

**Total**: 18-26 hours (2-3 working days)

**Breakdown**:
- Phase 1: 4-6 hours
- Phase 2: 3-4 hours
- Phase 3: 4-6 hours
- Phase 4: 3-4 hours
- Phase 5: 2-3 hours
- Phase 6: 2-3 hours

---

## Files to Create/Modify

### New Files
- `src/generators/schema/table_view_path_generator.py`
- `tests/unit/registry/test_tv_code_assignment.py`
- `tests/unit/generators/test_tv_path_generator.py`
- `tests/unit/schema/test_table_view_file_generation.py`
- `tests/integration/test_hierarchical_tv_generation.py`
- `tests/unit/registry/test_tv_registry_persistence.py`
- `docs/architecture/HIERARCHICAL_TV_ORGANIZATION.md`
- `docs/guides/MIGRATION_SINGLE_TO_HIERARCHICAL_TV.md`

### Modified Files
- `src/generators/schema/naming_conventions.py` (DomainRegistry)
- `src/generators/schema_orchestrator.py` (generate_table_views)
- `src/generators/schema/table_view_generator.py` (file-level generation)
- `src/cli/orchestrator.py` (lines 424-437)
- `registry/domain_registry.yaml` (schema extension)

---

## Open Questions

1. Support custom path templates in specql.yaml?
2. How to handle view dependencies across domains?
3. Should refresh functions be in separate files?
4. Migration tool for existing 200_table_views.sql?
5. Naming convention for non-tv_ views (v_, mv_)?

---

## Next Steps

1. Review plan with stakeholders
2. Create feature branch: `feature/hierarchical-tv-organization`
3. Begin Phase 1: Registry Enhancement
4. Set up test fixtures from reference structure

---

**See full plan for detailed TDD cycles, code examples, and risk assessment**
