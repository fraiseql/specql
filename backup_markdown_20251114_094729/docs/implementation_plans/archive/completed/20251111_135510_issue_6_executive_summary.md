# Issue #6 Executive Summary: Subdomain Parsing Bug

**Issue**: [#6 - Hierarchical generator incorrectly parses table_code subdomain](https://github.com/evoludigit/specql/issues/6)
**Priority**: HIGH - Blocks production migration
**Complexity**: MEDIUM - Requires 6 phased cycles
**Estimated Time**: 9-15 hours
**Risk**: LOW - No SQL generation changes

---

## The Problem in 30 Seconds

The hierarchical generator extracts **2 digits** for subdomain instead of **1 digit** from table codes, creating wrong directory structures:

```
❌ Current (WRONG):
  01311_subdomain_11/
  01312_subdomain_12/
  01313_subdomain_13/

✅ Expected (CORRECT):
  0131_classification/
    01311_colormode_group/
    01312_duplexmode_group/
    01313_machinefunction_group/
```

---

## Root Cause

**File**: `src/generators/schema/naming_conventions.py:688`

```python
# WRONG: Takes 2 digits for subdomain
subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]
# For "013111" → subdomain_code = "11" ❌

# CORRECT: Should take single digit
subdomain_code = components.subdomain_code  # "1" ✅
```

**Table Code Format**: `XYZWWF`
- `XY` = Schema layer (2 digits)
- `Z` = Domain (1 digit)
- `W` = **Subdomain (1 digit)** ← THE BUG
- `W` = Entity sequence (1 digit)
- `F` = File sequence (1 digit)

---

## Impact

### ✅ What Works
- SQL generation is **perfect** (no functional issues)
- All database schema, constraints, functions correct
- Files are generated successfully

### ❌ What's Broken
- Directory names are generic (`subdomain_11` instead of `classification`)
- Directory codes wrong (5 digits `01311` instead of 4 digits `0131`)
- Same-subdomain entities split across multiple directories
- Doesn't match reference backend structure (PrintOptim migration blocker)

---

## Solution Overview

### Fix 3 Files (6 Phases)

1. **`src/numbering/numbering_parser.py`**
   - Add `subdomain_code` field (single digit)
   - Add `entity_sequence` field

2. **`src/generators/schema/naming_conventions.py`**
   - Fix `generate_file_path()` to use `subdomain_code`
   - Fix `register_entity_auto()` to use correct subdomain
   - Look up subdomain names from registry

3. **Tests**
   - Add unit tests for parser
   - Add unit tests for path generation
   - Add integration tests for PrintOptim scenario

---

## 7 Implementation Phases

### Phase 1: Fix Parser (1-2 hours)
- Add `subdomain_code` field to `TableCodeComponents`
- Add `entity_sequence` field

### Phase 2: Fix Path Generation (2-3 hours)
- Update `generate_file_path()` to use single-digit subdomain
- Build 4-digit subdomain directory codes
- Look up subdomain names from registry

### Phase 3: Fix Registration (1-2 hours)
- Update `register_entity_auto()` to use correct subdomain
- Add subdomain validation
- Handle 2-digit registry codes (padding)

### Phase 4: Integration Tests (2-3 hours)
- Test PrintOptim scenario (74 entities)
- Test same-subdomain grouping
- Test cross-subdomain separation

### Phase 4.5: Snake_case & Remove _group (2-3 hours) **NEW**
- Add `camel_to_snake()` utility function
- Convert entity names to snake_case (ColorMode → color_mode)
- Remove `_group` suffix from directories
- Update all tests and documentation

### Phase 5: Backward Compatibility (1-2 hours)
- Add deprecation warnings
- Ensure old code still works
- Document migration path

### Phase 6: Documentation (2-3 hours)
- Update architecture docs
- Add migration guide
- Update README examples

---

## TDD Approach

Each phase follows **RED → GREEN → REFACTOR → QA**:

1. **RED**: Write failing test showing expected behavior
2. **GREEN**: Minimal code to make test pass
3. **REFACTOR**: Clean up and improve
4. **QA**: Run full test suite to ensure no regressions

---

## Testing Strategy

### Unit Tests
```bash
uv run pytest tests/unit/numbering/ -v
uv run pytest tests/unit/registry/ -v
```

### Integration Tests
```bash
uv run pytest tests/integration/test_issue_6_subdomain_parsing.py -v
```

### Regression Tests
```bash
uv run pytest --tb=short  # Full suite
```

---

## Risk Mitigation

### Low Risk Factors ✅
- No SQL changes (database schema unaffected)
- Only affects directory structure
- Backward compatibility maintained
- Comprehensive test coverage

### Potential Issues ⚠️
- External scripts referencing old paths may break
- Users with v0.2.0 output need to regenerate

### Mitigation Plan 📋
- Clear migration guide
- Deprecation warnings
- Version bump to v0.2.1
- Announcement in CHANGELOG

---

## Success Criteria

**Must Have**:
- [ ] All tests pass (`make test`)
- [ ] PrintOptim 74-entity migration works
- [ ] Directory structure matches reference backend
- [ ] No `subdomain_XX` generic names
- [ ] Backward compatibility maintained

**Nice to Have**:
- [ ] Migration guide published
- [ ] Documentation updated
- [ ] CLI help text improved

---

## Example Output

### Before Fix (v0.2.0)
```
generated/
  01_write_side/
    013_catalog/
      01311_subdomain_11/        ❌ Wrong code
        013111_colormode_group/
      01312_subdomain_12/        ❌ Duplicate subdomain
        013121_duplexmode_group/
      01321_subdomain_21/        ❌ Generic name
        013211_manufacturer_group/
```

### After Fix (v0.2.1)
```
generated/
  01_write_side/
    013_catalog/
      0131_classification/       ✅ Correct code, meaningful name
        01311_color_mode/        ✅ Snake_case, no _group
        01312_duplex_mode/       ✅ Same subdomain, shared directory
        01313_machine_function/  ✅ Consistent naming
      0132_manufacturer/         ✅ Registry name
        01321_manufacturer/      ✅ No _group suffix
        01323_model/
```

---

## Files Changed

1. `src/numbering/numbering_parser.py` (~20 lines)
2. `src/generators/schema/naming_conventions.py` (~30 lines)
3. `tests/unit/numbering/test_numbering_parser.py` (new tests)
4. `tests/unit/registry/test_naming_conventions.py` (new tests)
5. `tests/integration/test_issue_6_subdomain_parsing.py` (new file)
6. `docs/architecture/NUMBERING_SYSTEMS_VERIFICATION.md` (update)
7. `docs/migration/issue_6_subdomain_fix.md` (new)
8. `README.md` (update examples)

---

## Next Steps

1. **Review** this plan with team
2. **Start Phase 1** - Fix parser
3. **Follow TDD** - RED → GREEN → REFACTOR → QA for each phase
4. **Document** as you go
5. **Test continuously** - Run suite after each phase

---

## Questions?

- **Will this break existing databases?** NO - SQL is unchanged
- **Do I need to migrate?** Only if using `--output-format hierarchical`
- **What about Confiture format?** No impact - already flat structure
- **When will this be fixed?** Target: v0.2.1 release

---

**Status**: Ready for Implementation
**Blocking**: No blockers
**Dependencies**: None

---

*Full implementation plan: [`docs/implementation_plans/issue_6_subdomain_parsing_fix.md`](./issue_6_subdomain_parsing_fix.md)*
*Last Updated: 2025-11-11*
