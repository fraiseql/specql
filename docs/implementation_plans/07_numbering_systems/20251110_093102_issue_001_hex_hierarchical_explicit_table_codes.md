# Implementation Plan: Fix Hex Hierarchical Generation with Explicit table_code Fields

**GitHub Issue**: #1
**Status**: 📋 Planning Complete
**Priority**: HIGH - Blocks migration of existing codebases
**Estimated Effort**: 4-6 hours

---

## 🎯 Issue Summary

**Problem**: When using `use_registry=True` with explicit `table_code` fields, the registry's uniqueness validation incorrectly rejects legitimate explicit table codes during generation, even though the user is intentionally providing pre-existing codes from a legacy system (PrintOptim with 74 entities).

**Root Cause**: Line 363 in `naming_conventions.py:get_table_code()` calls `validate_table_code()` which checks `is_code_available()`, causing false conflicts when multiple entities are processed in the same generation run.

**User Impact**:
- Blocks hex hierarchical generation for migrations
- Forces workaround using flat structure
- Affects anyone migrating from systems with existing numbering schemes

---

## 🔍 Current Flow Analysis (COMPLETED ✅)

### File Structure
- `src/generators/schema/naming_conventions.py:360-372` - `get_table_code()` method
- `src/generators/schema/naming_conventions.py:479-543` - `validate_table_code()` method
- `src/core/specql_parser.py:128-130` - Organization parsing

### Current Logic

**`get_table_code()` Priority 1 (line 361-364)**: Manual specification
```python
if entity.organization and entity.organization.table_code:
    table_code = entity.organization.table_code
    self.validate_table_code(table_code, entity)  # ← Problem!
    return table_code
```

**`validate_table_code()` (lines 535-542)**: Uniqueness check
```python
# Uniqueness check (skip if entity already has this code in registry)
registry_entry = self.registry.get_entity(entity.name)
if registry_entry and registry_entry.table_code == table_code:
    return

if not self.registry.is_code_available(table_code):
    raise ValueError(f"Table code {table_code} already assigned to another entity")
```

### Why This Fails

**Scenario:**
1. User provides `table_code: "013211"` for Manufacturer
2. User provides `table_code: "013212"` for ManufacturerRange
3. First entity processes fine, registers code
4. Second entity fails uniqueness check despite being a different, legitimate code

**Problem**: The validation treats explicit codes the same as auto-derived codes, but they have different semantics:
- **Explicit codes**: User-provided, from legacy system, trusted
- **Auto-derived codes**: Framework-generated, must be unique

---

## ✅ Solution Design

### Option 1: Skip Uniqueness Validation for Explicit Codes (RECOMMENDED)

**Rationale:**
- Users providing explicit table codes know what they're doing (migration scenario)
- Explicit codes are "trusted" - they come from existing systems
- Only auto-derived codes need uniqueness validation
- Maintains backward compatibility

**Changes Required:**

1. **`naming_conventions.py:get_table_code()` (line 363)**
   - Modify `validate_table_code()` call to skip uniqueness check
   - Only validate format and domain consistency
   - Trust explicit codes completely

2. **`naming_conventions.py:validate_table_code()` (new parameter)**
   - Add `skip_uniqueness: bool = False` parameter
   - When `skip_uniqueness=True`, skip lines 535-542
   - Still validate format and domain consistency

---

### Option 2: Support Top-Level `table_code` Field (BONUS)

**Rationale:**
- More intuitive YAML syntax
- Reduces nesting for simple cases
- Matches user expectations

**Change Required:**

**`specql_parser.py:128-131`** - Add support for top-level `table_code`:

```python
# Current: Only supports organization: { table_code: "..." }
if "organization" in data:
    entity.organization = self._parse_organization(data["organization"])
# NEW: Support top-level table_code field
elif "table_code" in data:
    entity.organization = Organization(
        table_code=data["table_code"],
        domain_name=data.get("domain_name")
    )
```

**User Experience:**

```yaml
# Before (nested - still works)
entity: Manufacturer
organization:
  table_code: "013211"

# After (top-level - more intuitive)
entity: Manufacturer
table_code: "013211"
```

---

## 🔧 Implementation Tasks

### Phase 1: Core Fix (Option 1) - HIGH PRIORITY

#### TASK 1.1: Modify `get_table_code()` validation

**File**: `src/generators/schema/naming_conventions.py:360-364`
**Action**: Remove uniqueness check for explicit codes

**Change**:
```python
# Priority 1: Manual specification (TRUSTED - no uniqueness validation)
if entity.organization and entity.organization.table_code:
    table_code = entity.organization.table_code
    # Validate format & domain consistency only (not uniqueness)
    self.validate_table_code(table_code, entity, skip_uniqueness=True)
    return table_code
```

**TDD Cycle**:
1. **RED**: Write test `test_explicit_table_code_skips_uniqueness_validation()`
2. **GREEN**: Add `skip_uniqueness=True` parameter to call
3. **REFACTOR**: Clean up comments
4. **QA**: Run all schema tests

---

#### TASK 1.2: Add `skip_uniqueness` parameter to `validate_table_code()`

**File**: `src/generators/schema/naming_conventions.py:479`
**Action**: Add optional parameter, conditionally skip uniqueness check

**Change**:
```python
def validate_table_code(
    self,
    table_code: str,
    entity: Entity,
    skip_uniqueness: bool = False
):
    """
    Validate table code format and consistency

    Args:
        table_code: 6-character hexadecimal code to validate
        entity: Entity being validated
        skip_uniqueness: If True, skip uniqueness validation (for explicit codes)

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

    # Uniqueness check (SKIP for explicit codes)
    if not skip_uniqueness:
        registry_entry = self.registry.get_entity(entity.name)
        if registry_entry and registry_entry.table_code == table_code:
            return

        if not self.registry.is_code_available(table_code):
            raise ValueError(f"Table code {table_code} already assigned to another entity")
```

**TDD Cycle**:
1. **RED**: Write test `test_validate_table_code_with_skip_uniqueness()`
2. **GREEN**: Implement `skip_uniqueness` logic
3. **REFACTOR**: Ensure backward compatibility (default `skip_uniqueness=False`)
4. **QA**: Run all naming convention tests

---

### Phase 2: Parser Enhancement (Option 2) - MEDIUM PRIORITY

#### TASK 2.1: Add top-level `table_code` support to parser

**File**: `src/core/specql_parser.py:128-131`
**Action**: Support both `organization.table_code` AND top-level `table_code`

**Change**:
```python
# Parse organization
if "organization" in data:
    entity.organization = self._parse_organization(data["organization"])
elif "table_code" in data:
    # Support top-level table_code (more intuitive for simple cases)
    entity.organization = Organization(
        table_code=data["table_code"],
        domain_name=data.get("domain_name", None)
    )
```

**TDD Cycle**:
1. **RED**: Write test `test_parse_top_level_table_code()`
2. **GREEN**: Add `elif` clause for top-level `table_code`
3. **REFACTOR**: Ensure nested format still takes priority
4. **QA**: Run all parser tests

---

### Phase 3: Testing - MEDIUM PRIORITY

#### TASK 3.1: Unit tests for explicit table_code handling

**File**: `tests/unit/schema/test_naming_conventions.py`

**Tests to add**:

```python
def test_explicit_table_code_skips_uniqueness_validation():
    """Explicit table codes should skip uniqueness validation"""
    registry = DomainRegistry()
    registry.load_from_yaml("registry/domain_registry.yaml")

    conventions = NamingConventions(registry)

    # Create entity with explicit table code
    entity1 = Entity(name="Manufacturer", schema="catalog")
    entity1.organization = Organization(table_code="013211")

    # First entity should succeed
    code1 = conventions.get_table_code(entity1)
    assert code1 == "013211"

    # Create second entity with different explicit code
    entity2 = Entity(name="ManufacturerRange", schema="catalog")
    entity2.organization = Organization(table_code="013212")

    # Second entity should also succeed (no conflict)
    code2 = conventions.get_table_code(entity2)
    assert code2 == "013212"


def test_explicit_table_code_validates_format():
    """Explicit table codes should still validate format"""
    registry = DomainRegistry()
    registry.load_from_yaml("registry/domain_registry.yaml")

    conventions = NamingConventions(registry)

    # Invalid format should raise error
    entity = Entity(name="Test", schema="catalog")
    entity.organization = Organization(table_code="INVALID")

    with pytest.raises(ValueError, match="Invalid table code format"):
        conventions.get_table_code(entity)


def test_explicit_table_code_validates_domain_consistency():
    """Explicit table codes should validate domain consistency"""
    registry = DomainRegistry()
    registry.load_from_yaml("registry/domain_registry.yaml")

    conventions = NamingConventions(registry)

    # Domain mismatch should raise error
    entity = Entity(name="Contact", schema="crm")
    entity.organization = Organization(table_code="013211")  # catalog domain

    with pytest.raises(ValueError, match="doesn't match entity schema"):
        conventions.get_table_code(entity)


def test_auto_derived_codes_still_validate_uniqueness():
    """Auto-derived codes should still check uniqueness"""
    registry = DomainRegistry()
    registry.load_from_yaml("registry/domain_registry.yaml")

    conventions = NamingConventions(registry)

    # Auto-derive code for entity 1
    entity1 = Entity(name="TestEntity", schema="catalog")
    code1 = conventions.get_table_code(entity1)

    # Register entity 1
    registry.register_entity_code(
        entity_name="TestEntity",
        table_code=code1,
        domain_code="3",
        subdomain_code="00"
    )

    # Auto-derive code for entity 2 in same domain/subdomain
    entity2 = Entity(name="TestEntity2", schema="catalog")
    code2 = conventions.get_table_code(entity2)

    # Codes should be different (uniqueness enforced)
    assert code1 != code2
```

**TDD Cycle**:
1. **RED**: Run tests (should fail)
2. **GREEN**: Implement Phase 1 fixes
3. **REFACTOR**: Clean up test assertions
4. **QA**: All tests pass

---

#### TASK 3.2: Parser tests for top-level table_code

**File**: `tests/unit/core/test_specql_parser.py`

**Tests to add**:

```python
def test_parse_top_level_table_code():
    """Parser should support top-level table_code field"""
    yaml_content = """
entity: Manufacturer
schema: catalog
table_code: "013211"
description: Test entity

fields:
  name: text
"""
    parser = SpecQLParser()
    entity = parser.parse_entity(yaml_content)

    assert entity.name == "Manufacturer"
    assert entity.organization is not None
    assert entity.organization.table_code == "013211"


def test_parse_nested_table_code_takes_priority():
    """Nested organization.table_code should take priority over top-level"""
    yaml_content = """
entity: Manufacturer
schema: catalog
table_code: "013211"
organization:
  table_code: "013999"
  domain_name: catalog

fields:
  name: text
"""
    parser = SpecQLParser()
    entity = parser.parse_entity(yaml_content)

    # Nested format should win
    assert entity.organization.table_code == "013999"


def test_parse_table_code_without_domain_name():
    """Top-level table_code without domain_name should work"""
    yaml_content = """
entity: Manufacturer
schema: catalog
table_code: "013211"

fields:
  name: text
"""
    parser = SpecQLParser()
    entity = parser.parse_entity(yaml_content)

    assert entity.organization.table_code == "013211"
    assert entity.organization.domain_name is None
```

**TDD Cycle**:
1. **RED**: Run tests (should fail)
2. **GREEN**: Implement Phase 2 parser changes
3. **REFACTOR**: Handle edge cases
4. **QA**: All parser tests pass

---

#### TASK 3.3: Integration test with PrintOptim scenario

**File**: `tests/integration/test_hex_hierarchical_generation.py` (NEW)

**Test**: Generate 2+ entities with explicit table_codes in same run

```python
"""Integration tests for hex hierarchical generation with explicit table codes"""
import pytest
from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator


def test_generate_multiple_entities_with_explicit_codes(tmp_path):
    """
    Test generating multiple entities with explicit table codes in same run

    Reproduces GitHub Issue #1 scenario:
    - PrintOptim migration with 74 entities
    - Each entity has pre-existing 6-digit hex code
    - Hex hierarchical generation should succeed
    """
    # Create test entity files
    manufacturer_yaml = tmp_path / "manufacturer.yaml"
    manufacturer_yaml.write_text("""
entity: Manufacturer
schema: catalog
table_code: "013211"
description: Printer/copier manufacturers

fields:
  name: text
  abbreviation: text
""")

    manufacturer_range_yaml = tmp_path / "manufacturer_range.yaml"
    manufacturer_range_yaml.write_text("""
entity: ManufacturerRange
schema: catalog
table_code: "013212"
description: Product ranges from manufacturers

fields:
  name: text
  manufacturer: ref(Manufacturer)
""")

    # Generate with registry + hierarchical output
    output_dir = tmp_path / "generated"
    orchestrator = CLIOrchestrator(
        use_registry=True,
        output_format="hierarchical"
    )

    result = orchestrator.generate_from_files(
        entity_files=[
            str(manufacturer_yaml),
            str(manufacturer_range_yaml)
        ],
        output_dir=str(output_dir)
    )

    # Both entities should generate successfully
    assert result.success
    assert len(result.generated_entities) == 2

    # Verify hierarchical structure created
    # Expected: 01_write_side/013_catalog/.../013211_tb_manufacturer.sql
    write_side_dir = output_dir / "01_write_side"
    assert write_side_dir.exists()

    catalog_dir = write_side_dir / "013_catalog"
    assert catalog_dir.exists()

    # Verify files exist (exact paths depend on subdomain structure)
    manufacturer_files = list(catalog_dir.rglob("*manufacturer*.sql"))
    assert len(manufacturer_files) > 0

    range_files = list(catalog_dir.rglob("*manufacturerrange*.sql"))
    assert len(range_files) > 0


def test_explicit_codes_allow_same_prefix():
    """
    Explicit table codes can share prefixes (different subdomains)

    Example:
    - 013211 = Catalog domain, manufacturer subdomain
    - 013311 = Catalog domain, parts subdomain

    These are both valid and should not conflict.
    """
    # TODO: Implement test
    pass


def test_auto_derived_codes_still_enforce_uniqueness():
    """
    Auto-derived codes (no explicit table_code) should still validate uniqueness

    This ensures the fix doesn't break normal auto-derivation behavior.
    """
    # TODO: Implement test
    pass
```

**TDD Cycle**:
1. **RED**: Run test (should fail with "Table code already assigned")
2. **GREEN**: Implement Phase 1 + 2 fixes
3. **REFACTOR**: Test with 10+ entities
4. **QA**: Full PrintOptim migration (74 entities)

---

## 📊 Success Criteria

### 1. ✅ Explicit table codes are trusted without uniqueness validation
- When `entity.organization.table_code` is set, skip `is_code_available()` check
- Format and domain consistency still validated
- No false conflicts between different explicit codes

### 2. ✅ Multiple entities with explicit codes can be generated in same run
- No "Table code already assigned" errors
- Registry doesn't block legitimate explicit codes
- Hex hierarchical structure created correctly

### 3. ✅ Top-level `table_code` field works in YAML (bonus)
- `table_code: "XXXXXX"` at entity root level
- Backward compatible with nested `organization.table_code`
- More intuitive user experience

### 4. ✅ PrintOptim migration use case succeeds
- Generate 74 entities with pre-existing codes
- Hex hierarchical folder structure created correctly
- File naming matches legacy system

### 5. ✅ All tests pass
- Unit tests for naming conventions ✅
- Parser tests for top-level field ✅
- Integration test with multi-entity generation ✅
- No regressions in existing functionality ✅

### 6. ✅ Auto-derived codes still work correctly
- Uniqueness validation still applies to auto-derived codes
- Registry tracking still functions
- No breaking changes to normal workflow

---

## 🎯 Implementation Priority

### HIGH PRIORITY (Blocking)
- **Phase 1**: Core Fix (Tasks 1.1, 1.2)
  - Solves the blocker immediately
  - Unblocks PrintOptim migration
  - ~2-3 hours

### MEDIUM PRIORITY (Enhancement)
- **Phase 2**: Parser Enhancement (Task 2.1)
  - Nice UX improvement
  - More intuitive YAML syntax
  - ~1 hour

- **Phase 3**: Testing (Tasks 3.1, 3.2, 3.3)
  - Ensures no regressions
  - Validates fix comprehensively
  - ~2-3 hours

---

## 📝 Testing Strategy (TDD)

### RED Phase: Write failing tests
```bash
# Test explicit table code handling
uv run pytest tests/unit/schema/test_naming_conventions.py::test_explicit_table_code_skips_uniqueness_validation -v
# Expected: FAILED (skip_uniqueness parameter doesn't exist yet)
```

### GREEN Phase: Implement minimal fix
```bash
# Add skip_uniqueness parameter
uv run pytest tests/unit/schema/test_naming_conventions.py::test_explicit_table_code_skips_uniqueness_validation -v
# Expected: PASSED (minimal implementation working)
```

### REFACTOR Phase: Clean up and optimize
```bash
# Run broader schema tests
uv run pytest tests/unit/schema/ -v
# Expected: All passing, clean implementation
```

### QA Phase: Full validation
```bash
# Run complete test suite
uv run pytest --tb=short

# Test with actual PrintOptim entities
uv run python -m src.cli.orchestrator generate \
  entities/catalog/manufacturer.yaml \
  entities/catalog/manufacturer_range.yaml \
  --use-registry \
  --output-format=hierarchical
```

---

## 🔗 Files to Modify

### Phase 1: Core Fix
1. ✏️ `src/generators/schema/naming_conventions.py:363-364` - Modify validation call
2. ✏️ `src/generators/schema/naming_conventions.py:479` - Add `skip_uniqueness` parameter
3. ✏️ `src/generators/schema/naming_conventions.py:535-542` - Conditional uniqueness check

### Phase 2: Parser Enhancement
4. ✏️ `src/core/specql_parser.py:128-131` - Add top-level `table_code` support

### Phase 3: Testing
5. 📝 `tests/unit/schema/test_naming_conventions.py` - Add explicit code tests
6. 📝 `tests/unit/core/test_specql_parser.py` - Add parser tests
7. 📝 `tests/integration/test_hex_hierarchical_generation.py` - NEW file (integration tests)

---

## 🚀 Expected Impact

### Before Fix
```
❌ Failed to generate Manufacturer: Table code 013211 already assigned.
This is unexpected - registry may be corrupted.
```

### After Fix
```
✅ Generated Manufacturer → 01_write_side/013_catalog/0132_manufacturer/01321_manufacturer/013211_tb_manufacturer.sql
✅ Generated ManufacturerRange → 01_write_side/013_catalog/0132_manufacturer/01321_range/013212_tb_manufacturerrange.sql
✅ Generated 74 entities successfully
```

### Unblocks
- ✅ PrintOptim migration (74 entities with pre-existing codes)
- ✅ Any legacy system migration with existing numbering schemes
- ✅ Hex hierarchical generation for real-world use cases
- ✅ Multi-entity generation workflows

---

## 🔄 Backward Compatibility

### No Breaking Changes
- Default behavior unchanged (`skip_uniqueness=False`)
- Auto-derived codes still validate uniqueness
- Nested `organization.table_code` format still works
- Registry tracking still functions normally

### Additive Changes Only
- New parameter `skip_uniqueness` (optional, default=False)
- New top-level `table_code` field (optional, alternative to nested format)
- No changes to existing APIs or data structures

---

## 📚 Documentation Updates

### Files to Update
1. `docs/guides/migrations.md` - Add explicit table_code usage guide
2. `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Document top-level table_code field
3. `CHANGELOG.md` - Document bug fix and enhancement

### Examples to Add
```yaml
# Simple migration example
entity: LegacyEntity
schema: catalog
table_code: "013999"  # Preserved from legacy system

fields:
  name: text
```

---

## 🧪 Test Coverage Goals

- **Unit Tests**: 100% coverage of modified functions
- **Integration Tests**: Multi-entity generation scenarios
- **Edge Cases**:
  - Invalid format with explicit codes
  - Domain mismatch with explicit codes
  - Mixed explicit + auto-derived codes
  - Top-level vs nested table_code priority

---

## 🎓 Lessons Learned

### Design Principle Violated
**"Trust user-provided data over framework validation"**

When users explicitly provide configuration (like table codes), the framework should trust their intent rather than apply the same validation rules as auto-generated values.

### Future Consideration
Consider making this pattern more general:
- `skip_validation` flags for other user-provided values
- Clear distinction between "derived" vs "explicit" throughout codebase
- Documentation on when validation should be relaxed

---

## ✅ Definition of Done

- [ ] All Phase 1 tasks completed (core fix)
- [ ] All Phase 2 tasks completed (parser enhancement)
- [ ] All Phase 3 tasks completed (testing)
- [ ] All tests passing (unit + integration)
- [ ] PrintOptim migration verified (74 entities)
- [ ] No regressions in existing functionality
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] GitHub Issue #1 closed

---

**Last Updated**: 2025-11-10
**Estimated Completion**: 4-6 hours (phased implementation)
**Next Steps**: Begin Phase 1 (Core Fix) implementation
