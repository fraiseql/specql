# Handoff: Final 2 Pattern Tests (97% → 100%)

**Date**: 2025-11-18
**Status**: Implementation complete, needs debugging
**Progress**: 64/66 tests passing (97%)
**Remaining**: 2 tests (trigger + index generation)
**Time**: 2-4 hours estimated

---

## 📊 Current Status

### Test Results
```bash
uv run pytest tests/unit/patterns/validation/ -v

Results:
✅ 20 PASSED
❌ 2 FAILED
──────────────────────────────────────────
Validation: 91% (20/22)
Overall: 97% (64/66)
```

### Failing Tests
1. `test_inheritance_resolution_trigger` - Trigger SQL not in DDL output
2. `test_template_inheritance_indexes` - Index SQL not in DDL output

---

## ✅ What's Been Completed

### 1. Week 5 Phase 1-2 (20 Tests Fixed)
- ✅ Pattern registration (3 tests)
- ✅ FraiseQL metadata (1 test)
- ✅ Field naming (1 test)
- ✅ Configuration parsing (1 test)
- ✅ Null handling (1 test)
- **Total**: 7 tests fixed

### 2. Custom DDL Collection Implementation
**File**: `src/generators/schema/pattern_applier.py`
**Lines**: 111-119

**What was added**:
```python
# Collect custom DDL if pattern added any (triggers, indexes, etc.)
additional_sql = ""
if hasattr(entity, "_custom_ddl") and entity._custom_ddl:
    additional_sql = "\n\n".join(entity._custom_ddl)
    # Clear _custom_ddl to prevent duplication on re-application
    entity._custom_ddl = []

# Functions are added to entity.functions and rendered separately via template
return entity, additional_sql
```

**Purpose**: Collect triggers, indexes, and other custom DDL from patterns and return as `additional_sql`

**Status**: ✅ Implemented (both registered and fallback paths)

### 3. Index Generation Method
**File**: `src/patterns/validation/template_inheritance.py`
**Lines**: 269-280

**What was added**:
```python
@classmethod
def _generate_template_index(cls, entity: EntityDefinition, config: TemplateConfig) -> str:
    """Generate index for template field lookups."""
    table_name = f"tb_{entity.name.lower()}"
    idx_name = f"idx_{entity.name.lower()}_{config.template_field}"

    return f"""
-- Index for template lookups
CREATE INDEX {idx_name}
ON {entity.schema}.{table_name}({config.template_field})
WHERE {config.template_field} IS NOT NULL;
"""
```

**Purpose**: Generate partial index for template field lookups

**Status**: ✅ Implemented

### 4. Integration in Pattern Apply
**File**: `src/patterns/validation/template_inheritance.py`
**Lines**: 41-51

**What was added**:
```python
# Add trigger and index as custom DDL
if not hasattr(entity, "_custom_ddl"):
    entity._custom_ddl = []

# Add validation trigger
trigger_sql = cls._generate_validation_trigger(entity, config)
entity._custom_ddl.append(trigger_sql)

# Add template field index (ensures it's in DDL output)
index_sql = cls._generate_template_index(entity, config)
entity._custom_ddl.append(index_sql)
```

**Purpose**: Add both trigger and index to custom DDL list

**Status**: ✅ Implemented

---

## ❌ What's Not Working

### Symptom
Custom DDL (triggers and indexes) are generated and added to `entity._custom_ddl`, but they don't appear in the final DDL output.

### Expected Behavior
```sql
-- (table creation)
-- (functions)
-- (TRIGGER should appear here)
-- (INDEX should appear here)
-- (comments)
```

### Actual Behavior
```sql
-- (table creation)
-- (functions)
-- (comments)
-- ❌ No trigger
-- ❌ No index
```

---

## 🔍 Debugging Steps

### Step 1: Verify Pattern is Being Applied
Add debug output to `TemplateInheritancePattern.apply()`:

```python
@classmethod
def apply(cls, entity: EntityDefinition, params: dict) -> None:
    """Apply template inheritance pattern."""
    print(f"[DEBUG] TemplateInheritancePattern.apply() called for entity: {entity.name}")
    config = cls._parse_config(params, entity.name)

    # ... existing code ...

    # Add trigger and index as custom DDL
    if not hasattr(entity, "_custom_ddl"):
        entity._custom_ddl = []

    print(f"[DEBUG] Adding trigger to _custom_ddl")
    trigger_sql = cls._generate_validation_trigger(entity, config)
    entity._custom_ddl.append(trigger_sql)

    print(f"[DEBUG] Adding index to _custom_ddl")
    index_sql = cls._generate_template_index(entity, config)
    entity._custom_ddl.append(index_sql)

    print(f"[DEBUG] _custom_ddl now has {len(entity._custom_ddl)} items")
```

**Run test**:
```bash
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inheritance_resolution_trigger -v -s
```

**Expected**: See debug messages showing pattern.apply() is called and _custom_ddl is populated

---

### Step 2: Verify Pattern Applier Receives Custom DDL
Add debug output to `PatternApplier._apply_python_pattern()`:

```python
# After pattern_class.apply(entity, pattern.params)
print(f"[DEBUG] After apply(), entity has _custom_ddl: {hasattr(entity, '_custom_ddl')}")
if hasattr(entity, "_custom_ddl"):
    print(f"[DEBUG] _custom_ddl length: {len(entity._custom_ddl)}")
    if entity._custom_ddl:
        print(f"[DEBUG] First item preview: {entity._custom_ddl[0][:100]}")
```

**Expected**: See _custom_ddl with 2 items (trigger + index)

---

### Step 3: Check Entity Type Compatibility
The pattern uses `EntityDefinition` but table generator might use `Entity`:

```python
# In test or pattern
print(f"[DEBUG] Entity type: {type(entity)}")
print(f"[DEBUG] Entity class: {entity.__class__.__name__}")
```

**Possible Issue**: Type mismatch between EntityDefinition (pattern) and Entity (table generator)

**Solution**: Check if Entity has _custom_ddl attribute properly set

---

### Step 4: Trace DDL Flow
Add debug in `TableGenerator.generate_table_ddl()`:

```python
def generate_table_ddl(self, entity) -> str:
    # Apply patterns to entity first
    entity, additional_sql = self._apply_patterns_to_entity(entity)

    print(f"[DEBUG] After apply_patterns:")
    print(f"[DEBUG] - additional_sql length: {len(additional_sql) if additional_sql else 0}")
    print(f"[DEBUG] - additional_sql preview: {additional_sql[:200] if additional_sql else 'None'}")

    # ... rest of method ...

    # Combine table SQL with pattern-generated SQL
    if additional_sql:
        print(f"[DEBUG] Appending {len(additional_sql)} chars of additional SQL")
        return table_sql + "\n\n" + additional_sql
    else:
        print(f"[DEBUG] No additional SQL to append")
        return table_sql
```

**Expected**: See additional_sql with trigger and index content

---

## 🎯 Most Likely Issues

### Issue #1: Entity Type Mismatch
**Symptom**: Pattern modifies EntityDefinition but table generator uses Entity
**Check**:
```python
# In pattern
print(f"Type: {type(entity)}, Has _custom_ddl: {hasattr(entity, '_custom_ddl')}")
```
**Fix**: Ensure both use same entity instance

### Issue #2: Pattern Not Being Called
**Symptom**: No debug output from pattern.apply()
**Check**: Pattern type matching in PATTERN_APPLIERS
**Fix**: Verify `"validation_template_inheritance"` is registered

### Issue #3: Custom DDL Cleared Too Early
**Symptom**: _custom_ddl populated but empty when checked
**Check**: Timing of `entity._custom_ddl = []` clearing
**Fix**: Only clear after collecting, not before

### Issue #4: Wrong Code Path
**Symptom**: Fallback path used instead of registered path
**Check**: Which return statement is hit in _apply_python_pattern()
**Fix**: Ensure pattern_class found in PATTERN_APPLIERS

---

## 📋 Verification Checklist

After debugging and fixing:

- [ ] Add debug prints to pattern.apply()
- [ ] Run test with `-s` flag to see output
- [ ] Verify _custom_ddl is populated (should have 2 items)
- [ ] Verify pattern applier receives _custom_ddl
- [ ] Verify additional_sql is not empty
- [ ] Verify table generator appends additional_sql
- [ ] Run both failing tests:
  ```bash
  uv run pytest tests/unit/patterns/validation/test_template_inheritance.py -k "trigger or indexes" -v
  ```
- [ ] Both tests should pass ✅
- [ ] Run all validation tests:
  ```bash
  uv run pytest tests/unit/patterns/validation/ -v
  ```
- [ ] Should see 22/22 passing ✅
- [ ] Run all pattern tests:
  ```bash
  uv run pytest tests/unit/patterns/ -v
  ```
- [ ] Should see 66/66 passing ✅
- [ ] Remove debug prints
- [ ] Commit final fix

---

## 📚 Resources

### Documentation
- **Phased Plan**: `WEEK_05_FINAL_2_TESTS_PHASED_PLAN.md` (detailed implementation guide)
- **Quick Fix**: `PATTERN_FIX_CHEATSHEET.md` (priority-ordered fixes)
- **Progress**: `PATTERN_TESTS_PROGRESS.md` (current status)

### Key Files
- Pattern Applier: `src/generators/schema/pattern_applier.py`
- Template Pattern: `src/patterns/validation/template_inheritance.py`
- Table Generator: `src/generators/table_generator.py`
- Tests: `tests/unit/patterns/validation/test_template_inheritance.py`

### Test Commands
```bash
# Single failing test
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inheritance_resolution_trigger -v -s

# Both failing tests
uv run pytest tests/unit/patterns/validation/test_template_inheritance.py -k "trigger or indexes" -v

# All validation tests
uv run pytest tests/unit/patterns/validation/ -v

# All pattern tests
uv run pytest tests/unit/patterns/ -v
```

---

## 🎯 Success Criteria

### Tests Pass
```bash
uv run pytest tests/unit/patterns/ -v

Expected:
============================== 66 passed in 12.34s ===============================
✅ 100% PATTERN TESTS PASSING!
```

### DDL Contains Triggers and Indexes
```sql
-- In generated DDL for Product entity:

CREATE TRIGGER trg_validate_template_product
  BEFORE INSERT OR UPDATE ON catalog.tb_product
  FOR EACH ROW
  EXECUTE FUNCTION catalog.trg_validate_template_product_func();

CREATE INDEX idx_product_template_id
ON catalog.tb_product(template_id)
WHERE template_id IS NOT NULL;
```

---

## 💾 Final Commit

After tests pass:
```bash
git add src/generators/schema/pattern_applier.py src/patterns/validation/template_inheritance.py
git commit -m "fix: complete custom DDL rendering for validation patterns (100%)

Debug findings:
- [Document what was found during debugging]

Solution:
- [Document the actual fix applied]

Results:
- ✅ test_inheritance_resolution_trigger passing
- ✅ test_template_inheritance_indexes passing
- ✅ 22/22 validation tests passing
- ✅ 66/66 pattern tests passing (100%)

🎉 Pattern testing complete! 🎉"
```

---

## ⏱️ Time Estimate

- **Debugging**: 1-2 hours
- **Fix Implementation**: 30 minutes
- **Testing & Verification**: 30 minutes
- **Clean up & Commit**: 30 minutes
- **Total**: 2-4 hours

---

## 🎉 Completion Message

When all 66 tests pass:

```bash
uv run pytest tests/unit/patterns/ -v

============================== 66 passed in 12.34s ===============================

🎉🎉🎉 CONGRATULATIONS! 🎉🎉🎉

✅ 100% Pattern Test Coverage Complete!
✅ From 15 passing to 66 passing (+51 tests)
✅ From 22% to 100% completion
✅ Production-ready pattern system

You are now a PostgreSQL + code generation expert! 🚀
```

---

**Current State**: Ready for debugging
**Next Step**: Follow debugging steps above
**Goal**: 66/66 tests passing (100%)

**You've got this! 💪**
