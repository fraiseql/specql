# Week 5: Final Polish - Fix Remaining 9 Tests (86% → 100%)

**Goal**: Fix final 9 validation pattern tests to reach 100% completion
**Time**: 2-3 days
**Current Status**: 57/66 passing (86%)
**Target**: 66/66 passing (100%)
**Difficulty**: ⭐⭐ Medium (minor polish issues)

---

## 🎯 What You'll Fix

**Current Status**:
```bash
uv run pytest tests/unit/patterns/validation/ -v --tb=short

Results:
✅ 13 PASSED
❌ 9 FAILED (minor integration issues)
```

**After This Guide**:
```bash
✅ 22 PASSED (100% validation patterns complete!)
❌ 0 FAILED
```

---

## 📊 The 9 Failing Tests (Grouped by Issue)

### Issue Group 1: Pattern Registration (3 tests)
**Root Cause**: Pattern classes not registered in pattern applier

**Failing Tests**:
1. `test_inherited_fields_handled` - ValueError: Pattern class 'TemplateInheritance' not found
2. `test_no_override_constraint` - ValueError: Pattern class 'TemplateInheritance' not found
3. `test_inheritance_depth_limit` - ValueError: Pattern class 'TemplateInheritance' not found

**Fix**: Register pattern classes in pattern applier

---

### Issue Group 2: FraiseQL Metadata (1 test)
**Root Cause**: Pattern annotation missing from table comments

**Failing Test**:
4. `test_fraiseql_metadata_includes_pattern` - Missing `@fraiseql:pattern:template_inheritance`

**Fix**: Add pattern metadata to comment generator

---

### Issue Group 3: Field Naming (1 test)
**Root Cause**: Custom field name not applied

**Failing Test**:
5. `test_custom_template_field_name` - Expected `parent_template_id`, got `template_id`

**Fix**: Apply custom field name from pattern params

---

### Issue Group 4: Trigger Generation (1 test)
**Root Cause**: Triggers not generated for template inheritance

**Failing Test**:
6. `test_inheritance_resolution_trigger` - Missing `CREATE TRIGGER`

**Fix**: Add trigger generation to pattern implementation

---

### Issue Group 5: Index Generation (1 test)
**Root Cause**: Indexes not created for template fields

**Failing Test**:
7. `test_template_inheritance_indexes` - Missing index on template field

**Fix**: Add index generation for template reference fields

---

### Issue Group 6: Null Handling (1 test)
**Root Cause**: Null template reference not handled

**Failing Test**:
8. `test_inheritance_with_null_template_reference` - Null handling error

**Fix**: Add null checks in template resolution functions

---

### Issue Group 7: Configuration Parsing (1 test)
**Root Cause**: `allow_cycles` parameter not parsed correctly

**Failing Test**:
9. `test_allow_cycles_configurable` - AttributeError: 'NoneType' object has no attribute 'lower'

**Fix**: Fix parameter parsing in recursive dependency validator

---

## 🔧 Day 1: Pattern Registration (3 tests)

### Problem
Pattern classes exist but aren't registered in the pattern applier, causing "Pattern class not found" errors.

### Solution: Register Validation Patterns

**File**: `src/generators/schema/pattern_applier.py`

**Step 1**: Find the pattern registry
```bash
grep -n "PATTERN_APPLIERS" src/generators/schema/pattern_applier.py
```

**Step 2**: Add imports at top of file
```python
# Existing imports
from src.patterns.temporal.scd_type2_helper import SCDType2Helper
from src.patterns.schema.computed_column import ComputedColumnPattern
from src.patterns.temporal.non_overlapping_daterange import NonOverlappingDateRangePattern

# ADD THESE:
from src.patterns.validation.recursive_dependency_validator import RecursiveDependencyValidator
from src.patterns.validation.template_inheritance import TemplateInheritance
```

**Step 3**: Register patterns in PATTERN_APPLIERS dict
```python
PATTERN_APPLIERS = {
    # Existing patterns
    "schema_computed_column": ComputedColumnPattern,
    "temporal_scd_type2_helper": SCDType2Helper,
    "temporal_non_overlapping_daterange": NonOverlappingDateRangePattern,

    # ADD THESE:
    "validation_recursive_dependency_validator": RecursiveDependencyValidator,
    "validation_template_inheritance": TemplateInheritance,

    # Aliases for backward compatibility
    "recursive_dependency_validator": RecursiveDependencyValidator,
    "template_inheritance": TemplateInheritance,
}
```

**Step 4**: Test the fix
```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inherited_fields_handled -v
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_no_override_constraint -v
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inheritance_depth_limit -v
```

**Expected**: All 3 tests should pass ✅

---

## 🏷️ Day 1 (Afternoon): FraiseQL Metadata (1 test)

### Problem
Pattern annotations missing from table comments, breaking FraiseQL discovery.

### Solution: Add Pattern Metadata to Comments

**File**: `src/generators/comment_generator.py`

**Step 1**: Find the table comment generation
```bash
grep -n "def generate_table_comment" src/generators/comment_generator.py
```

**Step 2**: Locate where patterns are added to comments
```python
# Look for existing pattern comment generation
def generate_table_comment(self, entity: EntityDefinition) -> str:
    """Generate comment for table."""
    parts = [entity.description or f"{entity.name} entity."]

    # Trinity pattern annotation
    parts.append("\n@fraiseql:type")
    parts.append("trinity: true")

    # ADD PATTERN ANNOTATIONS HERE
    for pattern in entity.patterns:
        pattern_type = pattern.get("type", "")
        parts.append(f"@fraiseql:pattern:{pattern_type}")

    return "\n".join(parts)
```

**Step 3**: Test the fix
```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_fraiseql_metadata_includes_pattern -v
```

**Expected**: Test passes with pattern annotation present ✅

---

## 📝 Day 2: Field Naming (1 test)

### Problem
Custom template field name not applied from pattern params.

### Solution: Apply Custom Field Name

**File**: `src/patterns/validation/template_inheritance.py`

**Step 1**: Find the apply method
```bash
grep -n "def apply" src/patterns/validation/template_inheritance.py
```

**Step 2**: Check template_field parameter handling
```python
@classmethod
def apply(cls, entity: EntityDefinition, params: dict) -> None:
    """Apply template inheritance pattern."""
    config = cls._parse_config(params)

    # Use custom field name if provided
    template_field = params.get("template_field", "template_id")

    # Add template field to entity
    if template_field not in entity.fields:
        entity.fields[template_field] = FieldDefinition(
            name=template_field,
            type_name="text",
            nullable=True
        )
```

**Step 3**: Update function generation to use custom field name
```python
@classmethod
def _generate_resolution_function(cls, entity: EntityDefinition, config: TemplateConfig) -> str:
    """Generate template resolution function."""
    func_name = f"resolve_template_{entity.name.lower()}"
    template_field = config.template_field  # Use from config

    return f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(entity_id uuid)
RETURNS jsonb
AS $$
  WITH RECURSIVE template_chain AS (
    SELECT
      1 as depth,
      e.{template_field} as template_id,  -- Use custom field name
      e.config_data
    FROM {entity.schema}.tb_{entity.name.lower()} e
    WHERE e.id = entity_id
    ...
  )
$$;
"""
```

**Step 4**: Test the fix
```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_custom_template_field_name -v
```

**Expected**: Test passes with `parent_template_id` field ✅

---

## 🔔 Day 2 (Afternoon): Trigger Generation (1 test)

### Problem
No triggers generated for template inheritance validation.

### Solution: Add Trigger Generation

**File**: `src/patterns/validation/template_inheritance.py`

**Step 1**: Add trigger generation method
```python
@classmethod
def _generate_validation_trigger(cls, entity: EntityDefinition, config: TemplateConfig) -> str:
    """Generate trigger to validate template changes."""
    trigger_name = f"trg_validate_template_{entity.name.lower()}"
    func_name = f"validate_template_depth_{entity.name.lower()}"

    return f"""
-- Validation trigger function
CREATE OR REPLACE FUNCTION {entity.schema}.{trigger_name}_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Validate template depth on insert/update
  IF NEW.{config.template_field} IS NOT NULL THEN
    PERFORM {entity.schema}.{func_name}(NEW.id);
  END IF;
  RETURN NEW;
END;
$$;

-- Trigger
CREATE TRIGGER {trigger_name}
  BEFORE INSERT OR UPDATE ON {entity.schema}.tb_{entity.name.lower()}
  FOR EACH ROW
  EXECUTE FUNCTION {entity.schema}.{trigger_name}_func();
"""
```

**Step 2**: Add trigger to generated functions
```python
@classmethod
def _generate_validation_functions(cls, entity: EntityDefinition, config: TemplateConfig) -> list[str]:
    """Generate all validation functions."""
    functions = []

    # Existing functions
    functions.append(cls._generate_resolution_function(entity, config))
    functions.append(cls._generate_depth_validation_function(entity, config))
    functions.append(cls._generate_circular_check_function(entity, config))

    # ADD TRIGGER
    functions.append(cls._generate_validation_trigger(entity, config))

    return functions
```

**Step 3**: Test the fix
```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inheritance_resolution_trigger -v
```

**Expected**: Test passes with trigger present ✅

---

## 📇 Day 3: Index Generation (1 test)

### Problem
No indexes created for template reference fields.

### Solution: Add Index Generation

**File**: `src/patterns/validation/template_inheritance.py`

**Step 1**: Add index metadata to template field
```python
@classmethod
def apply(cls, entity: EntityDefinition, params: dict) -> None:
    """Apply template inheritance pattern."""
    config = cls._parse_config(params)
    template_field = params.get("template_field", "template_id")

    # Add template field with index metadata
    if template_field not in entity.fields:
        field_def = FieldDefinition(
            name=template_field,
            type_name="text",
            nullable=True
        )
        # Mark for indexing
        field_def.indexed = True  # Add this attribute
        entity.fields[template_field] = field_def
```

**Step 2**: Verify index generator picks up the field
```bash
# Check how indexes are generated
grep -rn "indexed" src/generators/schema/index_generator.py
```

**Alternative**: Generate index explicitly in pattern
```python
@classmethod
def _generate_template_index(cls, entity: EntityDefinition, config: TemplateConfig) -> str:
    """Generate index for template field."""
    idx_name = f"idx_tb_{entity.name.lower()}_{config.template_field}"

    return f"""
-- Index for template lookups
CREATE INDEX {idx_name}
ON {entity.schema}.tb_{entity.name.lower()}({config.template_field})
WHERE {config.template_field} IS NOT NULL;
"""
```

**Step 3**: Add to validation functions
```python
functions.append(cls._generate_template_index(entity, config))
```

**Step 4**: Test the fix
```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_template_inheritance_indexes -v
```

**Expected**: Test passes with index present ✅

---

## 🔒 Day 3 (Afternoon): Null Handling (1 test)

### Problem
Template resolution fails when template reference is null.

### Solution: Add Null Checks

**File**: `src/patterns/validation/template_inheritance.py`

**Step 1**: Find resolution function
```python
@classmethod
def _generate_resolution_function(cls, entity: EntityDefinition, config: TemplateConfig) -> str:
    """Generate template resolution function."""
    func_name = f"resolve_template_{entity.name.lower()}"

    return f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(entity_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
  v_resolved_config jsonb;
  v_template_id uuid;  -- ADD THIS
BEGIN
  -- Get entity's template reference
  SELECT {config.template_field}
  INTO v_template_id
  FROM {entity.schema}.tb_{entity.name.lower()}
  WHERE id = entity_id;

  -- Handle null template (no inheritance)
  IF v_template_id IS NULL THEN
    RETURN '{{}}'::jsonb;
  END IF;

  -- Continue with recursive resolution
  WITH RECURSIVE template_chain AS (
    ...
  )
  SELECT ...
  INTO v_resolved_config
  FROM template_chain;

  RETURN COALESCE(v_resolved_config, '{{}}'::jsonb);
END;
$$;
"""
```

**Step 2**: Test the fix
```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inheritance_with_null_template_reference -v
```

**Expected**: Test passes with null handling ✅

---

## ⚙️ Day 3 (Final): Configuration Parsing (1 test)

### Problem
`allow_cycles` parameter causes AttributeError during parsing.

### Solution: Fix Parameter Parsing

**File**: `src/patterns/validation/recursive_dependency_validator.py`

**Step 1**: Find the _parse_config method (line 46)

**Current Code**:
```python
@classmethod
def _parse_config(cls, params: dict) -> DependencyConfig:
    """Parse pattern parameters."""
    dependency_entity = params.get("dependency_entity")
    parent_field = params.get("parent_field")

    # This line causes the error if parent_field is None
    if not dependency_entity and not parent_field:
        raise ValueError(...)
```

**Step 2**: Fix the null handling
```python
@classmethod
def _parse_config(cls, params: dict) -> DependencyConfig:
    """Parse pattern parameters."""
    dependency_entity = params.get("dependency_entity")
    parent_field = params.get("parent_field")

    # Safe null check
    has_dependency_entity = dependency_entity is not None and dependency_entity != ""
    has_parent_field = parent_field is not None and parent_field != ""

    if not has_dependency_entity and not has_parent_field:
        raise ValueError(
            "Recursive dependency validator requires either 'dependency_entity' or 'parent_field'"
        )

    if has_dependency_entity and has_parent_field:
        raise ValueError("Cannot specify both 'dependency_entity' and 'parent_field'")

    # Fix allow_cycles handling
    allow_cycles = params.get("allow_cycles", False)  # Default to False (check for cycles)
    check_circular = not allow_cycles

    return DependencyConfig(
        dependency_entity=dependency_entity,
        parent_field=parent_field,
        max_depth=params.get("max_depth", 10),
        check_circular=check_circular,
    )
```

**Step 3**: Test the fix
```bash
uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::TestRecursiveDependencyValidator::test_allow_cycles_configurable -v
```

**Expected**: Test passes without AttributeError ✅

---

## ✅ Final Verification

### Run All Validation Tests
```bash
uv run pytest tests/unit/patterns/validation/ -v --tb=short
```

**Expected Output**:
```
============================== 22 passed in 3.45s ===============================
✅ 100% validation patterns complete!
```

### Run ALL Pattern Tests
```bash
uv run pytest tests/unit/patterns/ -v --tb=short
```

**Expected Output**:
```
============================== 66 passed in 12.34s ==============================
✅ 100% PATTERN TESTS PASSING! 🎉
```

---

## 🎯 Success Criteria

- [x] Issue Group 1: Pattern registration (3 tests) ✅
- [x] Issue Group 2: FraiseQL metadata (1 test) ✅
- [x] Issue Group 3: Field naming (1 test) ✅
- [x] Issue Group 4: Trigger generation (1 test) ✅
- [x] Issue Group 5: Index generation (1 test) ✅
- [x] Issue Group 6: Null handling (1 test) ✅
- [x] Issue Group 7: Configuration parsing (1 test) ✅

**Final Status**: 66/66 tests passing (100% complete!) 🎉

---

## 📝 Commit Strategy

**Day 1**:
```bash
git add src/generators/schema/pattern_applier.py
git commit -m "fix: register validation patterns in pattern applier

- Add RecursiveDependencyValidator registration
- Add TemplateInheritance registration
- Add backward compatibility aliases

Fixes 3 tests:
- test_inherited_fields_handled
- test_no_override_constraint
- test_inheritance_depth_limit"
```

**Day 2**:
```bash
git add src/generators/comment_generator.py src/patterns/validation/template_inheritance.py
git commit -m "fix: add pattern metadata and custom field names

- Add @fraiseql:pattern annotations to comments
- Support custom template_field parameter
- Generate triggers for validation

Fixes 3 tests:
- test_fraiseql_metadata_includes_pattern
- test_custom_template_field_name
- test_inheritance_resolution_trigger"
```

**Day 3**:
```bash
git add src/patterns/validation/template_inheritance.py src/patterns/validation/recursive_dependency_validator.py
git commit -m "fix: add indexes, null handling, and fix config parsing

- Generate indexes for template fields
- Add null checks in resolution functions
- Fix allow_cycles parameter parsing

Fixes 3 tests:
- test_template_inheritance_indexes
- test_inheritance_with_null_template_reference
- test_allow_cycles_configurable"
```

**Final**:
```bash
git add PATTERN_TESTS_PROGRESS.md
git commit -m "feat: 100% pattern test completion! 🎉

All 66 pattern tests passing:
- ✅ 14 Computed Column tests
- ✅ 14 Aggregate View tests
- ✅ 8 SCD Type 2 tests
- ✅ 8 Non-Overlapping Daterange tests
- ✅ 22 Validation Pattern tests

Progress: 22% → 86% → 100%

This completes the pattern testing initiative!"
```

---

## 🎉 What You Learned

### PostgreSQL Advanced Features
- ✅ Recursive CTEs with cycle detection
- ✅ Template/hierarchy traversal
- ✅ JSONB configuration merging
- ✅ Trigger-based validation
- ✅ Partial indexes with WHERE clauses

### Code Generation Patterns
- ✅ Pattern registration systems
- ✅ Metadata annotation generation
- ✅ Dynamic function generation
- ✅ Null-safe SQL generation

### Testing & Debugging
- ✅ Reading error messages effectively
- ✅ Isolating root causes
- ✅ Fixing integration issues
- ✅ Comprehensive test verification

---

## 💡 Common Mistakes

### Mistake 1: Forgetting Pattern Registration
**Error**: `ValueError: Python pattern class 'X' not found`
**Fix**: Always register new patterns in `PATTERN_APPLIERS` dict

### Mistake 2: Missing Null Checks
**Error**: SQL functions fail on null references
**Fix**: Always add `IF x IS NULL THEN RETURN ...` checks

### Mistake 3: Hard-coded Field Names
**Error**: Custom field names ignored
**Fix**: Use `config.template_field` from params

### Mistake 4: Missing Metadata Annotations
**Error**: FraiseQL discovery fails
**Fix**: Add `@fraiseql:pattern:X` to table comments

---

## 🆘 Troubleshooting

### Issue: Import Errors After Registration
```
ImportError: cannot import name 'TemplateInheritance'
```

**Fix**: Verify pattern class exists and is named correctly
```bash
grep -rn "class TemplateInheritance" src/patterns/
```

### Issue: Tests Still Failing After Fix
```
AssertionError: pattern annotation not found
```

**Debug**: Print generated DDL
```python
# In test
print(ddl)  # See what's actually generated
```

### Issue: Circular Import
```
ImportError: circular import detected
```

**Fix**: Move import inside function or use TYPE_CHECKING
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.patterns.validation.template_inheritance import TemplateInheritance
```

---

## 🚀 Final Commands

```bash
# Day 1: Pattern registration + metadata (4 tests)
uv run pytest tests/unit/patterns/validation/ -k "inherited_fields or no_override or depth_limit or fraiseql_metadata" -v

# Day 2: Field naming + triggers (2 tests)
uv run pytest tests/unit/patterns/validation/ -k "custom_template or resolution_trigger" -v

# Day 3: Indexes + null + config (3 tests)
uv run pytest tests/unit/patterns/validation/ -k "indexes or null_template or allow_cycles" -v

# Final: All validation tests
uv run pytest tests/unit/patterns/validation/ -v

# Victory: ALL pattern tests
uv run pytest tests/unit/patterns/ -v
```

---

## 🎊 Completion Celebration

When all tests pass:

```bash
uv run pytest tests/unit/patterns/ -v | tail -20

# You should see:
============================== 66 passed in X.XXs ===============================

🎉 CONGRATULATIONS! 🎉
✅ 100% Pattern Test Coverage Complete!
✅ From 15 passing to 66 passing (+51 tests)
✅ From 22% to 100% completion
✅ Production-ready pattern implementation

You are now a PostgreSQL + code generation expert!
```

---

**Total Time**: 2-3 days
**Total Tests Fixed**: 9 tests (final polish)
**Overall Achievement**: 22% → 100% pattern test coverage
**Skills Mastered**: Advanced PostgreSQL, code generation, pattern systems

**You did it! 🚀**
