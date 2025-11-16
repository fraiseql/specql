# Fix: CLI Confirmation Prompt Issue

**Issue ID**: CLI-PROMPT-001
**Priority**: CRITICAL
**Estimated Time**: 30 minutes
**Status**: Ready to fix

---

## Problem Statement

All SpecQL CLI commands (including the newly implemented `generate-tests`) are displaying an unexpected confirmation prompt:

```bash
$ specql generate-tests --help
False [y/N]: Aborted!
```

This affects:
- ✅ `generate-tests` command (newly implemented - working but blocked by prompt)
- ✅ `reverse-tests` command (blocked by prompt)
- ✅ ALL other CLI commands (blocked by prompt)

### Impact

- **Severity**: CRITICAL - Completely blocks all CLI usage
- **User Experience**: Commands appear broken
- **Scope**: Affects 100% of CLI functionality
- **Root Cause**: Identified

---

## Root Cause Analysis

### Investigation Results

Through systematic tracing, the issue was identified:

**File**: `/home/lionel/code/specql/src/cli/templates.py`
**Line**: 277
**Problem**: `@click.confirmation_option()` decorator on template deletion command

```python
# Line 275-280 in templates.py
@templates.command()
@click.argument("template_id")
@click.confirmation_option(prompt="Are you sure you want to delete this template?")
def delete(template_id):
    """Delete a template"""
    config = get_config()
```

### Why This Breaks Everything

1. **Import Chain**:
   ```
   confiture_extensions.py (line 893)
     → imports templates.py
       → @click.confirmation_option() decorator is evaluated at import time
         → Creates a GLOBAL confirmation option
           → Affects ALL commands in the CLI group
   ```

2. **Click Behavior**:
   - `@click.confirmation_option()` is designed for individual commands
   - When used incorrectly, it can leak into parent groups
   - The decorator is being evaluated during module import, not command execution

3. **Why It Shows "False [y/N]"**:
   - The confirmation option is receiving boolean `False` instead of proper context
   - This happens because it's being triggered at the wrong time

### Evidence

Trace output shows:
```
=== confirmation_option called ===
Args: ()
Kwargs: {'prompt': 'Are you sure you want to delete this template?'}

Call stack:
  confiture_extensions.py:893 in <module>
    from src.cli.templates import templates
  templates.py:277 in <module>
    @click.confirmation_option(prompt="Are you sure you want to delete this template?")
```

---

## Solution

### Fix Strategy

Replace `@click.confirmation_option()` with explicit confirmation inside the function.

### Why This Works

1. **No import-time side effects** - Confirmation only happens when command runs
2. **Proper context** - Function receives correct Click context
3. **Standard pattern** - Matches other SpecQL commands (see `generate` command)
4. **No global pollution** - Isolated to specific command

---

## Implementation

### Step 1: Update templates.py (5 minutes)

**File**: `src/cli/templates.py`

**Change**: Line 275-280

```python
# BEFORE (BROKEN):
@templates.command()
@click.argument("template_id")
@click.confirmation_option(prompt="Are you sure you want to delete this template?")
def delete(template_id):
    """Delete a template"""
    config = get_config()
```

```python
# AFTER (FIXED):
@templates.command()
@click.argument("template_id")
def delete(template_id):
    """Delete a template"""
    # Ask for confirmation before deletion
    if not click.confirm("Are you sure you want to delete this template?", default=False):
        click.echo("❌ Deletion cancelled")
        return 0

    config = get_config()
```

### Step 2: Verify Fix (10 minutes)

```bash
# Test 1: Help should work without prompts
uv run specql --help
# Expected: Help text displays, no prompts

# Test 2: generate-tests help should work
uv run specql generate-tests --help
# Expected: Help text for generate-tests, no prompts

# Test 3: reverse-tests help should work
uv run specql reverse-tests --help
# Expected: Help text for reverse-tests, no prompts

# Test 4: Template delete still prompts (but only when running delete)
uv run specql templates delete dummy-id
# Expected: Shows confirmation prompt "Are you sure..."

# Test 5: Template delete with cancellation
echo "n" | uv run specql templates delete dummy-id
# Expected: Shows "Deletion cancelled", exits cleanly
```

### Step 3: Test generate-tests End-to-End (10 minutes)

```bash
# Test the actual functionality now that prompt is fixed
uv run specql generate-tests docs/06_examples/simple_contact/contact.yaml --preview -v

# Expected output:
# 📄 Processing contact.yaml...
#    Entity: Contact
#    Schema: crm
#    📋 Would generate 4 test file(s):
#       • tests/test_contact_structure.sql
#       • tests/test_contact_crud.sql
#       • tests/test_contact_actions.sql
#       • tests/test_contact_integration.py
# 🔍 Preview mode - no files were written
```

### Step 4: Run Full Test Suite (5 minutes)

```bash
# Ensure no regressions
uv run pytest tests/cli/ -v

# Specifically test CLI commands
uv run pytest tests/cli/test_generate_tests_command.py -v
uv run pytest tests/cli/test_reverse_tests_command.py -v

# All should pass now
```

---

## Verification Checklist

After applying the fix:

- [ ] `specql --help` works without prompts
- [ ] `specql generate-tests --help` works without prompts
- [ ] `specql generate-tests entities/contact.yaml --preview` works
- [ ] `specql reverse-tests --help` works without prompts
- [ ] `specql templates delete` still shows confirmation (when actually running)
- [ ] All CLI tests pass
- [ ] No regression in existing functionality

---

## Alternative Approaches Considered

### Option 1: Remove confirmation entirely
**Pros**: Simpler
**Cons**: Less safe for destructive operations
**Verdict**: ❌ Not recommended

### Option 2: Use `--yes` flag
**Pros**: Scriptable
**Cons**: Requires additional implementation
**Verdict**: ⚠️ Future enhancement, not needed now

### Option 3: Use Click's built-in confirm (SELECTED)
**Pros**: Standard pattern, no global side effects
**Cons**: None
**Verdict**: ✅ Best solution

---

## Risk Assessment

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Break template deletion | Low | Low | Test template delete command |
| Miss other uses of confirmation_option | Low | Medium | Search codebase for all uses |
| Regression in other commands | Very Low | Low | Run full test suite |

### Mitigation Steps

1. **Search for all uses**:
```bash
grep -rn "confirmation_option" src/
# Verify only templates.py uses it
```

2. **Test template functionality**:
```bash
# Create template, then delete it
uv run specql templates list
uv run specql templates delete <id>
# Should prompt, then delete
```

---

## Time Estimate Breakdown

| Task | Time | Status |
|------|------|--------|
| Code change (1 line → 5 lines) | 5 min | Ready |
| Verification tests | 10 min | Ready |
| End-to-end testing | 10 min | Ready |
| Test suite | 5 min | Ready |
| **Total** | **30 min** | **Ready** |

---

## Git Commit

After fix and verification:

```bash
git add src/cli/templates.py
git commit -m "fix: remove global confirmation prompt blocking all CLI commands

Issue: @click.confirmation_option() decorator on templates delete command
was being evaluated at import time, creating a global confirmation that
blocked all CLI commands with 'False [y/N]: Aborted!' prompt.

Solution: Replace decorator with explicit click.confirm() call inside
the delete function. This isolates confirmation to the specific command
and eliminates import-time side effects.

Changes:
- src/cli/templates.py: Replace @click.confirmation_option() decorator
  with explicit confirmation inside delete() function

Testing:
- All CLI commands now work without unexpected prompts
- generate-tests --help works correctly
- reverse-tests --help works correctly
- template delete still prompts for confirmation (when actually run)
- All CLI tests passing

Fixes: CLI-PROMPT-001
Related: generate-tests implementation (Week 1)
"
```

---

## Success Criteria

✅ **Fix is successful when**:

1. Running `specql --help` shows help without prompts
2. Running `specql generate-tests --help` shows help without prompts
3. Running `specql generate-tests entities/contact.yaml --preview` executes without prompts
4. Running `specql templates delete <id>` DOES show confirmation prompt
5. All existing tests pass
6. New generate-tests command works end-to-end

---

## Post-Fix Actions

1. **Update Week 1 completion status** - Mark CLI commands as fully functional
2. **Continue with Week 1 tasks** - Now unblocked
3. **Document this as a lesson learned** - Add to testing checklist:
   - ⚠️ Avoid `@click.confirmation_option()` - use explicit `click.confirm()` instead
   - ⚠️ Test CLI imports don't have side effects

---

## Appendix: Full Investigation Log

### Trace Commands Used

```bash
# Initial discovery
uv run specql generate-tests --help

# Confirmation this affects all commands
uv run specql --help
uv run specql generate --help

# Source investigation
grep -rn "click.confirm\|confirmation" src/cli/

# Deep trace (found root cause)
python3 << 'EOF'
import click
old_confirm = click.confirmation_option
def tracked(*args, **kwargs):
    import traceback
    print("=== confirmation_option called ===")
    traceback.print_stack()
    return old_confirm(*args, **kwargs)
click.confirmation_option = tracked
from src.cli.confiture_extensions import specql
EOF
```

### Root Cause Found

Line 277 of templates.py: `@click.confirmation_option(prompt="Are you sure you want to delete this template?")`

This decorator is evaluated at module import time (when confiture_extensions.py imports templates.py), creating a global confirmation that affects all commands.

---

**READY TO FIX** - This is a simple, well-understood issue with a clear solution.
