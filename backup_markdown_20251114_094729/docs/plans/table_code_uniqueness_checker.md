# CLI Command: Table Code Uniqueness Checker - COMPLEX

**Complexity**: Complex | **Phased TDD Approach**

## Executive Summary

Add a new CLI command `specql check-codes` that validates the uniqueness of user-defined `table_code` fields across multiple SpecQL YAML files. This is critical for large migrations (like PrintOptim with 74+ entities) where explicit table codes are used and developers need to ensure no collisions exist before generation.

## Background

With the recent fix for Issue #1, SpecQL now supports explicit `table_code` fields that skip validation. This is essential for migrations from external systems, but it creates a new problem: users can accidentally use duplicate codes across different YAML files, leading to database conflicts.

**User Need**: Before running `specql generate`, users need a way to verify that all their explicit table codes are unique.

## PHASES

### Phase 1: Core Uniqueness Detection

**Objective**: Implement basic duplicate detection logic that scans YAML files and reports collisions.

#### TDD Cycle:

1. **RED**: Write failing test for duplicate detection
   - Test file: `tests/unit/cli/test_check_codes.py`
   - Expected failure: Test expects duplicate codes to be detected
   - Test case: Two entities with same `table_code: "013211"`

2. **GREEN**: Implement minimal code to pass
   - Files to create:
     - `src/cli/commands/check_codes.py` - Core uniqueness checker
     - Add function `check_table_code_uniqueness(entity_files: List[Path]) -> Dict[str, List[str]]`
   - Minimal implementation:
     - Parse each YAML file
     - Extract `table_code` field (both top-level and `organization.table_code`)
     - Build dict: `{code: [entity_names]}`
     - Return codes with len > 1

3. **REFACTOR**: Clean up and optimize
   - Use SpecQL parser instead of raw YAML parsing
   - Add proper error handling for malformed files
   - Extract reusable functions

4. **QA**: Verify phase completion
   - [ ] Basic duplicate detection works
   - [ ] Handles both `table_code` formats (top-level and nested)
   - [ ] Returns structured results
   - [ ] No false positives

---

### Phase 2: CLI Integration

**Objective**: Add `specql check-codes` command with proper argument parsing and output formatting.

#### TDD Cycle:

1. **RED**: Write failing test for CLI command
   - Test file: `tests/unit/cli/test_check_codes.py`
   - Expected failure: CLI command doesn't exist yet
   - Test case: Run `specql check-codes entities/*.yaml`

2. **GREEN**: Implement CLI command
   - Files to modify:
     - `src/cli/commands/check_codes.py` - Add Click command
     - `src/cli/main.py` - Register new command (if not auto-discovered)
   - Minimal implementation:
     ```python
     @click.command()
     @click.argument('entity_files', nargs=-1, type=click.Path(exists=True))
     def check_codes(entity_files):
         """Check uniqueness of table codes across entities"""
         # Call core function from Phase 1
         # Print results
     ```

3. **REFACTOR**: Improve user experience
   - Add colored output (green = OK, red = duplicates)
   - Add `--format` option (text, json, csv)
   - Add glob pattern support (`entities/**/*.yaml`)
   - Add progress indicator for large file sets

4. **QA**: Verify phase completion
   - [ ] Command runs successfully
   - [ ] Accepts multiple file patterns
   - [ ] Output is clear and actionable
   - [ ] Exit code: 0 (no duplicates), 1 (duplicates found)

---

### Phase 3: Registry Integration (Optional but Recommended)

**Objective**: Check for collisions between explicit codes and registry-assigned codes.

#### TDD Cycle:

1. **RED**: Write failing test for registry collision detection
   - Test file: `tests/unit/cli/test_check_codes.py`
   - Expected failure: Doesn't check registry yet
   - Test case: Explicit code `013029` collides with Manufacturer in registry

2. **GREEN**: Implement registry checking
   - Files to modify:
     - `src/cli/commands/check_codes.py` - Add `--check-registry` flag
   - Minimal implementation:
     - Load `DomainRegistry`
     - Check if explicit codes are already assigned in registry
     - Report potential collisions

3. **REFACTOR**: Smart collision detection
   - Distinguish between:
     - **Hard collisions**: Same code, different entity name
     - **Soft warnings**: Same code, same entity name (OK - re-generation)
   - Add `--ignore-registry` option to skip registry checks

4. **QA**: Verify phase completion
   - [ ] Registry collisions detected
   - [ ] Hard vs soft collisions distinguished
   - [ ] Clear warnings for each collision type
   - [ ] Works with and without registry

---

### Phase 4: Detailed Reporting

**Objective**: Provide comprehensive reports with file locations, entity details, and suggested fixes.

#### TDD Cycle:

1. **RED**: Write failing test for detailed reports
   - Test file: `tests/unit/cli/test_check_codes.py`
   - Expected failure: Report doesn't include file paths
   - Test case: Verify report contains YAML file paths for each duplicate

2. **GREEN**: Implement detailed reporting
   - Files to modify:
     - `src/cli/commands/check_codes.py` - Enhance result structure
   - Minimal implementation:
     - Store `(entity_name, file_path, line_number)` for each code
     - Report format:
       ```
       ❌ Duplicate code: 013211
         - Contact (entities/crm/contact.yaml:3)
         - Company (entities/crm/company.yaml:3)
       ```

3. **REFACTOR**: Enhanced reporting
   - Add summary section:
     ```
     📊 Summary:
       Total files scanned: 74
       Unique codes found: 72
       Duplicate codes: 2
       Registry collisions: 1
     ```
   - Add `--fix` option that suggests new codes (use registry auto-derivation)
   - Add `--export` option to save report to file

4. **QA**: Verify phase completion
   - [ ] Reports include all necessary context
   - [ ] File paths and line numbers accurate
   - [ ] Summary is helpful
   - [ ] Fix suggestions are actionable

---

### Phase 5: Integration Testing & Documentation

**Objective**: End-to-end testing with real-world scenarios and complete documentation.

#### TDD Cycle:

1. **RED**: Write failing integration test
   - Test file: `tests/integration/test_check_codes_integration.py`
   - Expected failure: Full PrintOptim scenario not tested
   - Test case: 74 entities with 2 duplicates, verify exact output

2. **GREEN**: Ensure integration works
   - Files to test:
     - Create fixture directory with realistic entity files
     - Test all command flags in combination
   - Validate:
     - Large file sets (100+ entities)
     - Edge cases (no table_code, malformed YAML, etc.)

3. **REFACTOR**: Polish and performance
   - Optimize for large codebases (parallel file parsing)
   - Add caching for repeated checks
   - Memory efficiency for 1000+ entities

4. **QA**: Verify phase completion
   - [ ] Integration tests pass
   - [ ] Performance acceptable (< 5s for 100 entities)
   - [ ] Documentation complete
   - [ ] Help text clear (`specql check-codes --help`)

---

## Technical Design

### Core Data Structures

```python
@dataclass
class TableCodeOccurrence:
    """Single occurrence of a table code"""
    entity_name: str
    file_path: Path
    line_number: int
    code: str
    schema: str

@dataclass
class DuplicateReport:
    """Report of duplicate table codes"""
    code: str
    occurrences: List[TableCodeOccurrence]
    collision_type: str  # "duplicate", "registry_collision"

@dataclass
class CheckResult:
    """Overall check result"""
    total_files: int
    total_codes: int
    duplicates: List[DuplicateReport]
    success: bool
```

### CLI Command Structure

```python
# src/cli/commands/check_codes.py

@click.command("check-codes")
@click.argument('entity_files', nargs=-1, type=click.Path())
@click.option('--check-registry/--no-check-registry', default=True,
              help='Check for collisions with registry codes')
@click.option('--format', type=click.Choice(['text', 'json', 'csv']),
              default='text', help='Output format')
@click.option('--export', type=click.Path(), help='Export report to file')
@click.option('--fix', is_flag=True, help='Suggest fixes for duplicates')
def check_codes(entity_files, check_registry, format, export, fix):
    """
    Check uniqueness of table codes across entity files.

    Examples:
        specql check-codes entities/*.yaml
        specql check-codes entities/**/*.yaml --format json
        specql check-codes entities/ --check-registry --fix
    """
    # Implementation from phases 1-4
```

### Output Examples

#### Success Case
```
✅ Table code uniqueness check PASSED

📊 Summary:
  Total files scanned: 74
  Unique codes found: 74
  Duplicate codes: 0
  Registry collisions: 0

All table codes are unique! 🎉
```

#### Failure Case
```
❌ Table code uniqueness check FAILED

🔴 Duplicate Codes:

  Code: 013211
    - Contact (entities/crm/contact.yaml:3)
    - Company (entities/crm/company.yaml:4)

  Code: 014511
    - Machine (entities/projects/machine.yaml:2)
    - Device (entities/projects/device.yaml:2)

⚠️  Registry Collisions:

  Code: 013029 (Manufacturer)
    - Used in: NewEntity (entities/catalog/new_entity.yaml:3)
    - Registry: Manufacturer (catalog.manufacturer.MNF)
    - Warning: Code already assigned in registry

📊 Summary:
  Total files scanned: 74
  Unique codes found: 72
  Duplicate codes: 2
  Registry collisions: 1

❌ Fix duplicates before running 'specql generate'

Exit code: 1
```

---

## Implementation Files

### New Files
- `src/cli/commands/check_codes.py` - Main command implementation
- `tests/unit/cli/test_check_codes.py` - Unit tests
- `tests/integration/test_check_codes_integration.py` - Integration tests
- `tests/fixtures/check_codes/` - Test fixtures with sample entities

### Modified Files
- `src/cli/main.py` - Register new command (if needed)
- `docs/cli/CHECK_CODES.md` - Command documentation

---

## Success Criteria

- [ ] All tests pass (unit + integration)
- [ ] Command detects 100% of duplicate codes
- [ ] Registry collision detection accurate
- [ ] Performance: < 5s for 100 entities
- [ ] Clear, actionable output
- [ ] Documentation complete with examples
- [ ] Exit codes correct (0 = success, 1 = duplicates)
- [ ] Works with glob patterns (`**/*.yaml`)

---

## Open Questions

1. **Should we check for "similar" codes?** (e.g., `013211` vs `013212` - potential typo)
2. **Should we validate code format?** (6-digit hex) or assume SpecQL parser handles this?
3. **Should we support auto-fixing?** (e.g., `--fix` flag that modifies YAML files)
4. **Should we integrate with `specql validate`?** Or keep as separate command?

---

## Dependencies

- SpecQL parser (`src/core/specql_parser.py`) - Already supports `table_code` parsing
- Domain Registry (`src/generators/schema/naming_conventions.py`) - For registry collision checks
- Click CLI framework - Already used throughout SpecQL

---

## Estimated Effort

- **Phase 1**: 2-3 hours (core logic)
- **Phase 2**: 1-2 hours (CLI integration)
- **Phase 3**: 2-3 hours (registry checking)
- **Phase 4**: 2-3 hours (reporting)
- **Phase 5**: 2-3 hours (integration + docs)

**Total**: 9-14 hours (1-2 days of focused work)

---

## Notes for Implementation

1. **Reuse existing parsers**: Don't parse YAML directly - use `SpecQLParser` from `src/core/specql_parser.py`
2. **Follow SpecQL CLI patterns**: Look at `src/cli/commands/validate.py` for similar structure
3. **Test with real PrintOptim data**: The 74-entity PrintOptim migration is the perfect test case
4. **Consider performance**: Use generator patterns for large file sets
5. **Clear error messages**: Users should know exactly which files to fix

---

**Last Updated**: 2025-11-10
**Status**: Ready for implementation
**Related Issues**: #1 (Explicit table_code support)
