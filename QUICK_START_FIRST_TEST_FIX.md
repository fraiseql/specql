# Quick Start: Fix Your First Test in 30 Minutes

**Goal**: Get your first test passing to build confidence
**Time**: 30 minutes
**Test**: `test_no_tracked_fields_specified` (SCD Type 2)
**Difficulty**: ⭐ Beginner-friendly

---

## 🎯 What You'll Fix

**Current Status**:
```bash
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified -v

# Result:
# ❌ FAILED - AttributeError: 'EntityDefinition' object has no attribute 'tracked_fields'
```

**After Fix**:
```bash
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified -v

# Result:
# ✅ PASSED - Test now passes!
```

---

## 📝 Step-by-Step (Copy-Paste Friendly)

### Step 1: Understand the Error (2 minutes)

**Run the test**:
```bash
cd /home/lionel/code/specql
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified -v
```

**Error message**:
```
AttributeError: 'EntityDefinition' object has no attribute 'tracked_fields'
```

**Translation**: The `EntityDefinition` class is missing the `tracked_fields` attribute that the test expects.

---

### Step 2: Look at the Test Code (3 minutes)

**Open test file**:
```bash
cat tests/unit/patterns/schema/test_scd_type2_helper.py | grep -A 20 "def test_no_tracked_fields_specified"
```

**What the test does**:
```python
def test_no_tracked_fields_specified(self):
    """Pattern should work without explicitly specifying tracked fields."""
    entity_def = EntityDefinition(
        name="Product",
        schema="catalog",
        fields={"name": FieldDefinition(name="name", type_name="text")},
        patterns=[{
            "type": "temporal_scd_type2_helper",
            "params": {"natural_key": ["product_code"]}
            # NOTE: No 'tracked_fields' specified! Should default to all fields.
        }],
        tracked_fields=None  # ← This line fails! Attribute doesn't exist!
    )
```

**Key insight**: Test tries to create `EntityDefinition` with `tracked_fields=None`, but that attribute doesn't exist in the class yet.

---

### Step 3: Find the EntityDefinition Class (2 minutes)

**Locate the file**:
```bash
grep -r "class EntityDefinition" src/
# Result: src/core/ast_models.py
```

**View current definition**:
```bash
cat src/core/ast_models.py | grep -A 20 "class EntityDefinition"
```

**Current code** (simplified):
```python
@dataclass
class EntityDefinition:
    name: str
    schema: str
    fields: dict[str, FieldDefinition]
    actions: list[ActionDefinition] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)
    # ... other existing fields ...
    # ❌ Missing: tracked_fields attribute!
```

---

### Step 4: Add the Missing Attribute (5 minutes)

**Edit the file**:
```bash
# Open in your editor (vim, nano, VS Code, etc.)
vim src/core/ast_models.py
# OR
code src/core/ast_models.py
```

**Find the `EntityDefinition` class** (search for `class EntityDefinition`).

**Add these lines** after the existing attributes:
```python
@dataclass
class EntityDefinition:
    name: str
    schema: str
    fields: dict[str, FieldDefinition]
    actions: list[ActionDefinition] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)

    # ... existing attributes ...

    # NEW: Add these attributes for SCD Type 2 support
    tracked_fields: Optional[list[str]] = None
    natural_key_fields: list[str] = field(default_factory=list)
    version_tracking_enabled: bool = False
```

**Full context** (what it should look like):
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EntityDefinition:
    """Represents a parsed entity (table/view) from SpecQL YAML."""

    name: str
    schema: str
    fields: dict[str, FieldDefinition]
    actions: list[ActionDefinition] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)

    # Existing attributes (don't change these)
    table_name: Optional[str] = None
    primary_key_field: str = "pk_id"
    # ... other existing attributes ...

    # NEW: SCD Type 2 attributes (ADD THESE)
    tracked_fields: Optional[list[str]] = None
    natural_key_fields: list[str] = field(default_factory=list)
    version_tracking_enabled: bool = False
```

**Save the file** (`:wq` in vim, `Ctrl+S` in VS Code).

---

### Step 5: Add Import if Missing (1 minute)

**Check if `Optional` is imported**:
```bash
head -20 src/core/ast_models.py | grep Optional
```

**If NOT found**, add it to imports at top of file:
```python
from typing import Optional  # Add this if missing
```

---

### Step 6: Run the Test Again (2 minutes)

```bash
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified -v
```

**Expected result**:
```
tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified PASSED [100%]

============================== 1 passed in 0.23s ==============================
```

**🎉 SUCCESS! Your first test is passing!**

---

### Step 7: Commit Your Change (3 minutes)

```bash
# Check what changed
git diff src/core/ast_models.py

# Add the file
git add src/core/ast_models.py

# Commit with clear message
git commit -m "feat: add SCD Type 2 attributes to EntityDefinition

- Added tracked_fields: Optional[list[str]]
- Added natural_key_fields: list[str]
- Added version_tracking_enabled: bool

Fixes test_no_tracked_fields_specified"

# Push (optional)
# git push
```

---

## 🎓 What You Just Learned

1. ✅ **Reading error messages**: `AttributeError` means missing attribute
2. ✅ **Understanding tests**: Tests show what code SHOULD do
3. ✅ **Locating code**: Using `grep` to find class definitions
4. ✅ **Dataclasses**: Adding optional attributes with `Optional[Type]`
5. ✅ **Testing**: Running specific tests with pytest
6. ✅ **Git workflow**: Making small, focused commits

---

## 🚀 Next Steps

### Option A: Fix More SCD Type 2 Tests (Recommended)

Continue with the next failing test:
```bash
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_version_field_added -v
```

Follow the same process:
1. Understand the error
2. Look at test code
3. Implement what's missing
4. Run test again
5. Commit

**Full guide**: See `WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md`

### Option B: Check Overall Progress

```bash
# Run ALL SCD Type 2 tests
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py -v

# Expected now:
# ✅ 3 PASSED (was 2, now 3!)
# ❌ 5 FAILED (was 6, now 5!)
# Progress: +1 test fixed! 🎉
```

---

## 🔄 Repeat This Process

The same workflow applies to ALL failing/skipped tests:

1. **Run test** → See error
2. **Read test code** → Understand expectation
3. **Find relevant code** → Locate what needs changing
4. **Make minimal change** → Just enough to pass test
5. **Run test again** → Verify it passes
6. **Commit** → Save your progress
7. **Next test** → Repeat!

---

## 💡 Pro Tips

### Tip 1: Use VS Code Search
```
Ctrl+Shift+F (Windows/Linux) or Cmd+Shift+F (Mac)
Search for: "class EntityDefinition"
```

### Tip 2: Run Tests in Watch Mode
```bash
# Install pytest-watch
uv pip install pytest-watch

# Auto-run tests on file changes
ptw tests/unit/patterns/schema/test_scd_type2_helper.py -- -v
```

### Tip 3: Focus on One Test
```bash
# Use -k flag to match test name
uv run pytest tests/unit/patterns/ -k "test_no_tracked_fields" -v
```

### Tip 4: See Full Diff
```bash
# Show more context in git diff
git diff -U10 src/core/ast_models.py
```

---

## 🆘 Troubleshooting

### Issue: Import Error After Changes

**Error**:
```
ImportError: cannot import name 'Optional' from 'typing'
```

**Fix**: Add import at top of file:
```python
from typing import Optional, List, Dict
```

### Issue: Test Still Fails

**Debug**: Add print statement to see what's happening:
```python
# In test file, add:
print(f"Entity definition: {entity_def}")
print(f"Tracked fields: {entity_def.tracked_fields}")
```

**Run with** `-s` flag to see prints:
```bash
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified -v -s
```

### Issue: Syntax Error

**Error**:
```
SyntaxError: invalid syntax
```

**Fix**: Check for:
- Missing commas between fields
- Unmatched parentheses
- Incorrect indentation

**Run linter**:
```bash
uv run ruff check src/core/ast_models.py
```

---

## ✅ Success Checklist

- [x] Test error understood
- [x] Test code read and understood
- [x] `EntityDefinition` class located
- [x] Attributes added (`tracked_fields`, etc.)
- [x] Imports added (`Optional`)
- [x] Test runs and passes
- [x] Change committed to git

**Congratulations! You've fixed your first test! 🎉**

---

## 📈 Your Progress

| Before | After | Next Goal |
|--------|-------|-----------|
| 2 passing | 3 passing | 8 passing |
| 6 failing | 5 failing | 0 failing |
| +1 test | 🎯 | +5 more |

**Keep going! Each test gets easier!** 💪

---

## 🎯 Challenge

Can you fix the next test (`test_version_field_added`) in under 30 minutes?

**Hint**: It probably needs pattern applier implementation. Check `WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md` Day 2!

---

**Happy coding! 🚀**
