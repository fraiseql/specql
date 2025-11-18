# Pattern Test Fix Cheatsheet - Quick Reference

**Current Status**: 57/66 passing (86%)
**Remaining**: 9 tests (2-3 days to 100%)

---

## 🚨 The 9 Failing Tests (Quick Fix List)

### Priority 1: Pattern Registration (3 tests - 15 minutes)
**File**: `src/generators/schema/pattern_applier.py`

```python
# Add imports
from src.patterns.validation.recursive_dependency_validator import RecursiveDependencyValidator
from src.patterns.validation.template_inheritance import TemplateInheritance

# Add to PATTERN_APPLIERS dict
PATTERN_APPLIERS = {
    # ... existing patterns ...
    "validation_recursive_dependency_validator": RecursiveDependencyValidator,
    "validation_template_inheritance": TemplateInheritance,
    "recursive_dependency_validator": RecursiveDependencyValidator,  # alias
    "template_inheritance": TemplateInheritance,  # alias
}
```

**Fixes**:
- `test_inherited_fields_handled`
- `test_no_override_constraint`
- `test_inheritance_depth_limit`

**Test**: `uv run pytest tests/unit/patterns/validation/test_template_inheritance.py -k "inherited_fields or no_override or depth_limit" -v`

---

### Priority 2: FraiseQL Metadata (1 test - 10 minutes)
**File**: `src/generators/comment_generator.py`

```python
def generate_table_comment(self, entity: EntityDefinition) -> str:
    """Generate comment for table."""
    parts = [entity.description or f"{entity.name} entity."]

    parts.append("\n@fraiseql:type")
    parts.append("trinity: true")

    # ADD THIS:
    for pattern in entity.patterns:
        pattern_type = pattern.get("type", "")
        if pattern_type:
            parts.append(f"@fraiseql:pattern:{pattern_type}")

    return "\n".join(parts)
```

**Fixes**: `test_fraiseql_metadata_includes_pattern`

**Test**: `uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_fraiseql_metadata_includes_pattern -v`

---

### Priority 3: Config Parsing (1 test - 10 minutes)
**File**: `src/patterns/validation/recursive_dependency_validator.py`

**Line ~46-60**: Fix null handling in `_parse_config`

```python
@classmethod
def _parse_config(cls, params: dict) -> DependencyConfig:
    """Parse pattern parameters."""
    dependency_entity = params.get("dependency_entity")
    parent_field = params.get("parent_field")

    # FIX: Safe null check
    has_dependency = dependency_entity is not None and dependency_entity != ""
    has_parent = parent_field is not None and parent_field != ""

    if not has_dependency and not has_parent:
        raise ValueError(
            "Recursive dependency validator requires either 'dependency_entity' or 'parent_field'"
        )

    if has_dependency and has_parent:
        raise ValueError("Cannot specify both 'dependency_entity' and 'parent_field'")

    # FIX: Default allow_cycles to False
    allow_cycles = params.get("allow_cycles", False)
    check_circular = not allow_cycles

    return DependencyConfig(
        dependency_entity=dependency_entity,
        parent_field=parent_field,
        max_depth=params.get("max_depth", 10),
        check_circular=check_circular,
    )
```

**Fixes**: `test_allow_cycles_configurable`

**Test**: `uv run pytest tests/unit/patterns/validation/test_recursive_dependency_validator.py::TestRecursiveDependencyValidator::test_allow_cycles_configurable -v`

---

### Priority 4: Null Handling (1 test - 15 minutes)
**File**: `src/patterns/validation/template_inheritance.py`

**Find**: `_generate_resolution_function` method

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
  v_template_id uuid;
BEGIN
  -- Get entity's template reference
  SELECT {config.template_field}
  INTO v_template_id
  FROM {entity.schema}.tb_{entity.name.lower()}
  WHERE id = entity_id;

  -- ADD THIS: Handle null template
  IF v_template_id IS NULL THEN
    RETURN '{{}}'::jsonb;
  END IF;

  -- Continue with recursive resolution...
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

**Fixes**: `test_inheritance_with_null_template_reference`

**Test**: `uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inheritance_with_null_template_reference -v`

---

### Priority 5: Field Naming (1 test - 20 minutes)
**File**: `src/patterns/validation/template_inheritance.py`

**Issue**: Custom field name not used from params

**Find**: `apply` method
```python
@classmethod
def apply(cls, entity: EntityDefinition, params: dict) -> None:
    """Apply template inheritance pattern."""
    config = cls._parse_config(params)

    # FIX: Get custom field name from params
    template_field = params.get("template_field", config.template_field)

    # Add field with custom name
    if template_field not in entity.fields:
        entity.fields[template_field] = FieldDefinition(
            name=template_field,
            type_name="text",
            nullable=True
        )

    # Update config to use custom field name
    config.template_field = template_field

    # Generate functions with correct field name
    functions = cls._generate_validation_functions(entity, config)
    entity.functions.extend(functions)
```

**Fixes**: `test_custom_template_field_name`

**Test**: `uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_custom_template_field_name -v`

---

### Priority 6: Trigger Generation (1 test - 30 minutes)
**File**: `src/patterns/validation/template_inheritance.py`

**Add new method**:
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

**Update `_generate_validation_functions`**:
```python
@classmethod
def _generate_validation_functions(cls, entity: EntityDefinition, config: TemplateConfig) -> list[str]:
    functions = []
    functions.append(cls._generate_resolution_function(entity, config))
    functions.append(cls._generate_depth_validation_function(entity, config))
    functions.append(cls._generate_circular_check_function(entity, config))
    functions.append(cls._generate_validation_trigger(entity, config))  # ADD THIS
    return functions
```

**Fixes**: `test_inheritance_resolution_trigger`

**Test**: `uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_inheritance_resolution_trigger -v`

---

### Priority 7: Index Generation (1 test - 30 minutes)
**File**: `src/patterns/validation/template_inheritance.py`

**Add new method**:
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

**Update `_generate_validation_functions`**:
```python
functions.append(cls._generate_template_index(entity, config))  # ADD THIS
```

**Fixes**: `test_template_inheritance_indexes`

**Test**: `uv run pytest tests/unit/patterns/validation/test_template_inheritance.py::TestTemplateInheritance::test_template_inheritance_indexes -v`

---

## ⚡ Quick Commands

### Run All 9 Failing Tests
```bash
uv run pytest tests/unit/patterns/validation/ -v | grep FAILED
```

### Fix and Test Priority Groups
```bash
# Priority 1-3 (Pattern registration, metadata, config) - 30 minutes
uv run pytest tests/unit/patterns/validation/ -k "inherited_fields or no_override or depth_limit or fraiseql_metadata or allow_cycles" -v

# Priority 4-5 (Null handling, field naming) - 35 minutes
uv run pytest tests/unit/patterns/validation/ -k "null_template or custom_template" -v

# Priority 6-7 (Triggers, indexes) - 60 minutes
uv run pytest tests/unit/patterns/validation/ -k "resolution_trigger or inheritance_indexes" -v
```

### Final Verification
```bash
# All validation tests
uv run pytest tests/unit/patterns/validation/ -v

# ALL pattern tests (target: 66/66)
uv run pytest tests/unit/patterns/ -v
```

---

## 📝 Commit Strategy

### After Priorities 1-3 (Quick Wins)
```bash
git add src/generators/schema/pattern_applier.py src/generators/comment_generator.py src/patterns/validation/recursive_dependency_validator.py
git commit -m "fix: pattern registration, metadata, and config parsing

- Register validation patterns in PATTERN_APPLIERS
- Add @fraiseql:pattern annotations to comments
- Fix allow_cycles parameter parsing with null checks

Fixes 5 tests:
- test_inherited_fields_handled
- test_no_override_constraint
- test_inheritance_depth_limit
- test_fraiseql_metadata_includes_pattern
- test_allow_cycles_configurable"
```

### After Priorities 4-5 (Null + Naming)
```bash
git add src/patterns/validation/template_inheritance.py
git commit -m "fix: null handling and custom field naming

- Add null checks in template resolution
- Support custom template_field parameter
- Use custom field name in SQL generation

Fixes 2 tests:
- test_inheritance_with_null_template_reference
- test_custom_template_field_name"
```

### After Priorities 6-7 (Triggers + Indexes)
```bash
git add src/patterns/validation/template_inheritance.py
git commit -m "fix: add validation triggers and template indexes

- Generate validation triggers for template changes
- Create indexes for template reference fields
- Optimize template lookups

Fixes 2 tests:
- test_inheritance_resolution_trigger
- test_template_inheritance_indexes"
```

### Final Commit
```bash
git add PATTERN_TESTS_PROGRESS.md
git commit -m "feat: 100% pattern test completion! 🎉

All 66 pattern tests passing:
- 14 Computed Column
- 14 Aggregate View
- 8 SCD Type 2
- 8 Non-Overlapping Daterange
- 22 Validation Patterns (all fixed!)

Progress: 22% → 86% → 100%
Time: 4-5 weeks from start
Result: Production-ready pattern system"
```

---

## 🎯 Time Estimates

| Priority | Issue | Tests | Time | Difficulty |
|----------|-------|-------|------|------------|
| 1 | Pattern registration | 3 | 15 min | ⭐ Easy |
| 2 | FraiseQL metadata | 1 | 10 min | ⭐ Easy |
| 3 | Config parsing | 1 | 10 min | ⭐ Easy |
| 4 | Null handling | 1 | 15 min | ⭐ Easy |
| 5 | Field naming | 1 | 20 min | ⭐⭐ Medium |
| 6 | Trigger generation | 1 | 30 min | ⭐⭐ Medium |
| 7 | Index generation | 1 | 30 min | ⭐⭐ Medium |

**Total**: ~2 hours of focused work

**Real-World**: 1 day (with testing, debugging, commits)

---

## 🔍 Debug Tips

### If Pattern Not Found Error
```python
# Check registration
import src.generators.schema.pattern_applier as pa
print(pa.PATTERN_APPLIERS.keys())
```

### If Metadata Missing
```python
# In test, print DDL
print(ddl)
# Search for @fraiseql:pattern
```

### If SQL Error
```python
# Print generated function
for func in entity.functions:
    print(func)
```

### If Test Still Fails
```bash
# Run with full output
uv run pytest <test-path> -v -s --tb=long
```

---

## ✅ Success Criteria

After all fixes:
```bash
uv run pytest tests/unit/patterns/ -v --tb=no

Expected:
============================== 66 passed in 12.34s ===============================

✅ 100% PATTERN TESTS PASSING!
```

---

## 🎉 Victory Commands

```bash
# Show final status
uv run pytest tests/unit/patterns/ -v --tb=no

# Generate final report
uv run pytest tests/unit/patterns/ --tb=no -q | tail -5

# Celebrate! 🎉
echo "🎉 100% Pattern Test Coverage Complete! 🎉"
```

---

**Total Time**: 1-2 days (including testing and polish)
**Total Fixes**: 9 tests
**Final Result**: 66/66 passing (100%) 🎉

**You're almost there! 💪**
