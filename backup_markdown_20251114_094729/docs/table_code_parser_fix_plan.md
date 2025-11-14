# SpecQL Parser table_code Field Fix - Implementation Plan

**Objective**: Fix the SpecQL parser to properly extract and use `table_code` from YAML entity definitions.

**Date**: 2025-11-10
**Status**: ✅ COMPLETED
**Priority**: HIGH
**Estimated Time**: 30-45 minutes (Actual: ~25 minutes)
**Complexity**: Low (single function, minimal changes)
**Location**: `../printoptim_backend_poc`

---

## 🔍 Problem Analysis

### Current State

The SpecQL system has **full support** for table codes in the data model, but there's a **critical gap** in the conversion pipeline:

```
YAML file → EntityDefinition → Entity (conversion) → SQL Generation
   ✅          ✅                 ❌                    ✅
```

**What Works:**
1. ✅ Parser reads `organization.table_code` from YAML
2. ✅ `EntityDefinition.organization.table_code` stores the value
3. ✅ `Entity.table_code` field exists and is used throughout codebase
4. ✅ SQL templates reference `entity.table_code`

**What's Broken:**
❌ The conversion function `convert_entity_definition_to_entity()` doesn't extract `table_code` from `organization` and set it on the `Entity` object

### Impact

**Current Behavior:**
- `Entity.table_code` is always `None`
- SQL comments don't include table codes: `-- [Table: None]`
- Migration tracking doesn't work with explicit codes
- Registry system auto-generates codes, ignoring YAML values

**Affected Features:**
1. SQL table comments (missing table codes)
2. Migration file naming
3. Table code registry
4. Documentation generation
5. Cross-reference tooling

---

## 📁 Files Involved

### Primary File (Needs Fix)

**File**: `../printoptim_backend_poc/src/cli/generate.py`
- **Function**: `convert_entity_definition_to_entity()` (lines 18-39)
- **Change Type**: Add 4 lines to extract table_code from organization
- **Risk Level**: LOW (isolated function, well-tested)

### Related Files (Context Only - No Changes)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `src/core/specql_parser.py` | 437-441 | Parses organization.table_code | ✅ Working |
| `src/core/ast_models.py` | 574-579 | Organization class definition | ✅ Working |
| `src/core/ast_models.py` | 463-502 | Entity class definition | ✅ Working |
| `templates/sql/table.sql.j2` | 7 | Uses entity.table_code | ✅ Working |
| `src/migration/orchestrator.py` | 243 | Uses table_code for files | ✅ Working |

---

## 🎯 Detailed Implementation Plan

### Phase 1: Verify Current Behavior (10 minutes)

#### Step 1.1: Review Current Code

**Objective**: Understand the exact current implementation

**File**: `../printoptim_backend_poc/src/cli/generate.py`

**Current Code** (lines 18-39):
```python
def convert_entity_definition_to_entity(entity_def: EntityDefinition) -> Entity:
    """Convert EntityDefinition to Entity for backward compatibility"""

    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name, steps=action_def.steps, impact=None
        )
        actions.append(action)

    # Create Entity
    entity = Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        description=entity_def.description,
        fields=entity_def.fields,
        actions=actions,
        agents=entity_def.agents,
        organization=entity_def.organization,  # ✅ Organization passed
        # ❌ BUT: entity.table_code is NOT set!
    )

    return entity
```

**Problem Identified**:
- Line 35: `organization=entity_def.organization` passes the full organization object
- Missing: Extraction of `table_code` from organization to set `Entity.table_code`

#### Step 1.2: Test Current Behavior

**Create Test YAML** (`test_entity.yaml`):
```yaml
entity: TestEntity
schema: tenant

organization:
  table_code: "012321"
  domain_name: "CRM"

fields:
  name: text
```

**Test Command**:
```bash
cd ../printoptim_backend_poc
python -m src.cli.generate test_entity.yaml --output test_output/
```

**Expected Current Behavior**:
- ❌ SQL comment: `-- [Table: None]` (should be `-- [Table: 012321]`)
- ❌ `entity.table_code` is `None` in generated code

**Verification**:
```bash
grep "Table:" test_output/*.sql
# Should show: -- [Table: None]
```

---

### Phase 2: Implement Fix (15 minutes)

#### Step 2.1: Update Conversion Function

**Objective**: Extract `table_code` from `organization` and set it on `Entity`

**File**: `../printoptim_backend_poc/src/cli/generate.py`

**Change Location**: After line 27, before line 30

**New Code to Add**:
```python
def convert_entity_definition_to_entity(entity_def: EntityDefinition) -> Entity:
    """Convert EntityDefinition to Entity for backward compatibility"""

    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name, steps=action_def.steps, impact=None
        )
        actions.append(action)

    # ✅ NEW: Extract table_code from organization if present
    table_code = None
    if entity_def.organization and entity_def.organization.table_code:
        table_code = entity_def.organization.table_code

    # Create Entity
    entity = Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        table_code=table_code,  # ✅ NEW: Set table_code
        description=entity_def.description,
        fields=entity_def.fields,
        actions=actions,
        agents=entity_def.agents,
        organization=entity_def.organization,
    )

    return entity
```

**Lines Added**: 4 (extraction logic + parameter)
**Lines Modified**: 1 (add table_code parameter)

#### Step 2.2: Verify No Breaking Changes

**Check Entity Constructor**:
```bash
cd ../printoptim_backend_poc
grep -A 20 "class Entity:" src/core/ast_models.py | grep "table_code"
```

**Expected Output**:
```python
table_code: str | None = None
```

This confirms `table_code` is an optional parameter with default `None`, so adding it won't break existing code.

---

### Phase 3: Testing (15 minutes)

#### Step 3.1: Unit Test

**Create**: `../printoptim_backend_poc/tests/test_table_code_conversion.py`

```python
"""Test table_code extraction from organization to entity"""
import pytest
from src.core.ast_models import EntityDefinition, Organization, Entity
from src.cli.generate import convert_entity_definition_to_entity


def test_table_code_extracted_from_organization():
    """Test that table_code is properly extracted from organization"""
    # Create EntityDefinition with organization.table_code
    org = Organization(table_code="012321", domain_name="CRM")
    entity_def = EntityDefinition(
        name="TestEntity",
        schema="tenant",
        description="Test entity",
        fields={},
        actions=[],
        agents=[],
        organization=org
    )

    # Convert to Entity
    entity = convert_entity_definition_to_entity(entity_def)

    # Verify table_code was extracted
    assert entity.table_code == "012321", \
        f"Expected table_code='012321', got '{entity.table_code}'"
    assert entity.organization is not None
    assert entity.organization.table_code == "012321"


def test_table_code_none_when_no_organization():
    """Test that table_code is None when organization is missing"""
    entity_def = EntityDefinition(
        name="TestEntity",
        schema="tenant",
        description="Test entity",
        fields={},
        actions=[],
        agents=[],
        organization=None
    )

    entity = convert_entity_definition_to_entity(entity_def)

    assert entity.table_code is None
    assert entity.organization is None


def test_table_code_none_when_organization_has_no_code():
    """Test that table_code is None when organization exists but has no table_code"""
    org = Organization(table_code=None, domain_name="CRM")
    entity_def = EntityDefinition(
        name="TestEntity",
        schema="tenant",
        description="Test entity",
        fields={},
        actions=[],
        agents=[],
        organization=org
    )

    entity = convert_entity_definition_to_entity(entity_def)

    assert entity.table_code is None
    assert entity.organization is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Run Test**:
```bash
cd ../printoptim_backend_poc
pytest tests/test_table_code_conversion.py -v
```

**Expected Output**:
```
test_table_code_extracted_from_organization PASSED
test_table_code_none_when_no_organization PASSED
test_table_code_none_when_organization_has_no_code PASSED
```

#### Step 3.2: Integration Test

**Test YAML** (`test_machine.yaml`):
```yaml
entity: Machine
schema: tenant

organization:
  table_code: "014511"
  domain_name: "Dimensions"

description: |
  [014511 | Write-Side.Dimensions.Material.Machine]
  Represents a physical printing device.

fields:
  code:
    type: text
    nullable: false
    description: "Machine identifier code"

  serial_number:
    type: text
    description: "Manufacturer serial number"
```

**Generate SQL**:
```bash
cd ../printoptim_backend_poc
python -m src.cli.generate test_machine.yaml --output test_output/
```

**Verify SQL Output**:
```bash
grep "Table:" test_output/001_machine.sql
```

**Expected Output**:
```sql
-- [Table: 014511 | Machine]
COMMENT ON TABLE tenant.tb_machine IS '[Table: 014511] Represents a physical printing device.';
```

#### Step 3.3: Regression Testing

**Run Full Test Suite**:
```bash
cd ../printoptim_backend_poc
pytest tests/ -v
```

**Expected**: All existing tests should pass (no breaking changes)

---

### Phase 4: Documentation (5 minutes)

#### Step 4.1: Update Function Docstring

**File**: `../printoptim_backend_poc/src/cli/generate.py`

**Updated Docstring**:
```python
def convert_entity_definition_to_entity(entity_def: EntityDefinition) -> Entity:
    """Convert EntityDefinition to Entity for backward compatibility

    This function bridges the gap between the parsed EntityDefinition
    (from SpecQL YAML) and the Entity object used by code generators.

    Key conversions:
    - ActionDefinition → Action
    - organization.table_code → entity.table_code (for numbering system)

    Args:
        entity_def: Parsed entity definition from SpecQL YAML

    Returns:
        Entity object ready for code generation

    Note:
        If entity_def.organization.table_code is present, it will be
        extracted and set as entity.table_code for use in SQL comments,
        migration naming, and the table numbering registry.
    """
```

#### Step 4.2: Update CHANGELOG

**File**: `../printoptim_backend_poc/CHANGELOG.md`

**Add Entry**:
```markdown
## [Unreleased]

### Fixed
- **SpecQL Parser**: Extract `table_code` from `organization` field in YAML
  - `convert_entity_definition_to_entity()` now properly sets `Entity.table_code`
  - SQL table comments now include explicit table codes from YAML
  - Migration file naming respects explicit table codes
  - Fixes issue where YAML `organization.table_code` was parsed but not used
  - Related files: `src/cli/generate.py`
```

---

## 🔄 Execution Checklist

### Pre-Implementation
- [ ] Backup current `src/cli/generate.py`
- [ ] Review current code (lines 18-39)
- [ ] Create test YAML file
- [ ] Test current behavior (verify table_code is None)

### Implementation
- [ ] Add table_code extraction logic (4 lines)
- [ ] Add table_code parameter to Entity constructor
- [ ] Save changes

### Testing
- [ ] Create unit test file
- [ ] Run unit tests (3 test cases)
- [ ] Create integration test YAML
- [ ] Generate SQL and verify table_code in comments
- [ ] Run full regression test suite
- [ ] Verify no breaking changes

### Documentation
- [ ] Update function docstring
- [ ] Update CHANGELOG.md
- [ ] Document change in commit message

### Deployment
- [ ] Create git commit with detailed message
- [ ] Run final validation
- [ ] Merge to main branch

---

## 📊 Expected Results

### Before Fix
```yaml
# Input YAML
organization:
  table_code: "012321"
```
```python
# Parsed Entity
entity.table_code = None  # ❌ Lost during conversion
entity.organization.table_code = "012321"  # ✓ But not used
```
```sql
-- Generated SQL
-- [Table: None]  ❌
COMMENT ON TABLE tenant.tb_contact IS '[Table: None] ...';  ❌
```

### After Fix
```yaml
# Input YAML
organization:
  table_code: "012321"
```
```python
# Parsed Entity
entity.table_code = "012321"  # ✅ Properly extracted
entity.organization.table_code = "012321"  # ✓ Also preserved
```
```sql
-- Generated SQL
-- [Table: 012321]  ✅
COMMENT ON TABLE tenant.tb_contact IS '[Table: 012321] ...';  ✅
```

---

## 🚨 Edge Cases & Considerations

### 1. Backward Compatibility

**Issue**: Existing YAML files without `organization` field

**Solution**: Code already handles this with `if entity_def.organization` check
```python
table_code = None
if entity_def.organization and entity_def.organization.table_code:
    table_code = entity_def.organization.table_code
```

**Result**: ✅ No breaking changes for existing files

### 2. Auto-Generated Table Codes

**Issue**: System has registry that auto-generates codes when `use_registry=True`

**Current Behavior**: Auto-generation ignores YAML values

**After Fix**: Explicit YAML codes take precedence
- If YAML has `organization.table_code`: Use it
- If YAML has no code: Auto-generate (existing behavior)

**No Conflict**: This is the desired behavior (explicit beats implicit)

### 3. Invalid Table Codes

**Issue**: What if YAML has invalid table_code (not 6 digits)?

**Current Validation**: None in parser

**Recommendation**: Add validation in future PR
```python
# Future enhancement (separate PR)
if table_code and not re.match(r'^\d{6}$', table_code):
    logger.warning(f"Invalid table_code format: {table_code}")
```

**For This PR**: Accept any string value (same as current system)

### 4. Duplicate Table Codes

**Issue**: Two entities with same table_code

**Current System**: Registry handles this (increments duplicate codes)

**After Fix**: No change in registry behavior

**Result**: ✅ Existing duplicate detection still works

### 5. Migration Impact

**Issue**: Existing migrations generated with table_code=None

**Impact**: None - migrations are immutable once created

**New Migrations**: Will include proper table codes

**Result**: ✅ No impact on existing migrations

---

## 🔧 Alternative Approaches (Not Recommended)

### Alternative 1: Remove Duplicate table_code Field

**Approach**: Remove `Entity.table_code` and always use `Entity.organization.table_code`

**Files to Change**: ~10 files
- `src/migration/orchestrator.py`
- `templates/sql/table.sql.j2`
- `src/naming/conventions.py`
- All template files referencing `entity.table_code`

**Pros**: Single source of truth

**Cons**:
- Larger change surface
- More risk of breaking changes
- Requires template updates
- Migration code complexity

**Verdict**: ❌ Not recommended (too invasive for the benefit)

### Alternative 2: Make organization.table_code the Primary Source

**Approach**: Deprecate `Entity.table_code`, update all references to use `entity.organization.table_code`

**Pros**: Clearer data model

**Cons**:
- Breaks all templates
- Requires null checks everywhere
- More verbose code

**Verdict**: ❌ Not recommended (worse developer experience)

### Alternative 3: Do Nothing

**Approach**: Keep current behavior, document limitation

**Pros**: No code changes

**Cons**:
- YAML table codes are ignored
- SQL comments don't have codes
- Migration naming doesn't work
- Defeats purpose of table_code implementation in printoptim_specql

**Verdict**: ❌ Not acceptable (breaks traceability feature)

---

## ✅ Success Criteria

1. ✅ `Entity.table_code` is populated from `organization.table_code`
2. ✅ SQL comments include table codes: `-- [Table: 012321]`
3. ✅ All unit tests pass
4. ✅ Integration test shows correct SQL output
5. ✅ No regression in existing test suite
6. ✅ Documentation updated
7. ✅ Change is backward compatible

---

## 📝 Commit Message Template

```
fix(parser): extract table_code from organization in entity conversion

The SpecQL parser correctly parsed organization.table_code from YAML,
but the conversion function didn't extract it to Entity.table_code.
This caused SQL comments to show [Table: None] instead of actual codes.

Changes:
- src/cli/generate.py: Extract table_code from organization in
  convert_entity_definition_to_entity()
- tests/test_table_code_conversion.py: Add unit tests for extraction

Impact:
- SQL table comments now include proper table codes
- Migration file naming respects explicit codes from YAML
- Table numbering registry uses YAML codes when present

Fixes: Table codes in printoptim_specql entities now properly flow
through to generated SQL and migrations.

Testing:
- 3 new unit tests (all passing)
- Integration test with sample YAML → SQL generation
- Full regression test suite (all passing)
- Backward compatible (no breaking changes)

Related: printoptim_specql commit 47fce65 (table code implementation)
```

---

## 🎯 Next Steps After Implementation

1. **Apply to printoptim_specql entities**: Regenerate SQL with proper table codes
2. **Update templates**: Enhance SQL comments to use table codes more extensively
3. **Add validation**: Validate table_code format (6 digits) in parser
4. **Registry integration**: Update registry to prefer YAML codes over auto-generated
5. **Documentation**: Update SpecQL spec to document organization.table_code field

---

## 📚 References

- **SpecQL Parser**: `../printoptim_backend_poc/src/core/specql_parser.py`
- **AST Models**: `../printoptim_backend_poc/src/core/ast_models.py`
- **Generation CLI**: `../printoptim_backend_poc/src/cli/generate.py`
- **SQL Templates**: `../printoptim_backend_poc/templates/sql/`
- **Entity YAML Examples**: `../printoptim_specql/entities/`

---

**Plan Version**: 1.0
**Last Updated**: 2025-11-10
**Author**: Claude Code
**Estimated Effort**: 30-45 minutes
**Risk Level**: LOW
**Priority**: HIGH
