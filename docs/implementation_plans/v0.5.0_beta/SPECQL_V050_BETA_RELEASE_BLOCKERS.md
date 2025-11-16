# SpecQL v0.5.0-beta Release Blockers - Implementation Plan

**Document Version**: 1.0
**Created**: 2025-11-16
**Target Release Date**: 2025-11-18 (2 days)
**Status**: Ready for execution
**Complexity**: Simple | Direct execution with validation

---

## Executive Summary

This plan addresses critical blockers preventing SpecQL v0.5.0-beta from being published to PyPI and used for the PrintOptim migration project. All issues are straightforward fixes that can be completed in 2-3 hours total.

**Current Status**:
- ✅ Code committed to GitHub (v0.5.0-beta features complete)
- ❌ Missing dependency (faker)
- ❌ 4 linting errors (unused imports)
- ❌ pytest collection conflict
- ❌ Not tested end-to-end
- ❌ Not published to PyPI

**Expected Outcomes**:
- 100% test passing rate
- Zero linting errors
- Clean PyPI package ready for `pip install specql-generator`
- Ready for immediate use in PrintOptim migration

---

## Current State Analysis

### Blockers Identified

#### 1. Missing `faker` Dependency
**Severity**: Critical - Tests cannot import

**Error**:
```
ModuleNotFoundError: No module named 'faker'
```

**Affected Files**:
- `src/testing/seed/field_generators.py:6`
- `tests/unit/testing/test_field_generators.py`
- `tests/unit/testing/test_seed_generator.py`

**Root Cause**: `faker` used for test data generation but not in `pyproject.toml`

**Impact**: Test suite fails to collect, blocking validation

---

#### 2. Linting Errors (4 issues)
**Severity**: Medium - CI/CD will fail

**Errors**:
```
src/cli/generate_tests.py:12:26: F401 [*] `typing.Optional` imported but unused
src/cli/generate_tests.py:68:33: F841 [*] Local variable `parse_error` is assigned to but never used
tests/cli/test_dry_run.py:3:8: F401 [*] `pytest` imported but unused
tests/cli/test_generate_tests_command.py:5:21: F401 [*] `pathlib.Path` imported but unused
tests/cli/test_generate_tests_command.py:46:29: F811 [*] Redefinition of unused `Path` from line 5
```

**Root Cause**: Refactoring left unused imports

**Impact**: Pre-commit hooks fail, CI/CD blocked

---

#### 3. pytest Conftest Conflict
**Severity**: High - Test collection fails

**Error**:
```
ValueError: Plugin already registered under a different name:
/home/lionel/code/specql/user_journey_test/specql/tests/conftest.py=<module 'tests.conftest' from '/home/lionel/code/specql/tests/conftest.py'>
```

**Root Cause**: `user_journey_test/` directory contains duplicate `conftest.py`

**Impact**: Cannot run test suite, blocking validation

---

#### 4. Validation Testing Gap
**Severity**: Medium - No end-to-end validation

**Gap**: `generate-tests` command not tested manually on real entity

**Impact**: Cannot guarantee command works for end users

---

### Release Checklist Status

From `RELEASE_CHECKLIST.md`:

| Item | Status | Blocker? |
|------|--------|----------|
| All tests passing | ❌ | **YES** |
| Test coverage >90% | ✅ | No |
| No linting errors | ❌ | **YES** |
| No type errors | ⚠️ Unchecked | Maybe |
| Documentation complete | ✅ | No |
| Examples tested | ❌ | **YES** |
| Demo GIFs created | ✅ | No |
| Version numbers updated | ✅ | No |
| CHANGELOG updated | ✅ | No |
| `generate-tests` works | ❌ | **YES** |
| `reverse-tests` works | ⚠️ Unchecked | No |
| Git tag created | ❌ | **YES** |
| PyPI published | ❌ | **YES** |

**Blockers**: 7 items preventing release

---

## Implementation Plan

### Fix 1: Add faker Dependency

**Objective**: Add faker to dependencies and verify imports work

**Estimated Time**: 5 minutes

#### Steps

**1. Add faker to pyproject.toml**
```bash
cd /home/lionel/code/specql
uv add faker
```

**Expected**: Updates `pyproject.toml` and `uv.lock`

**2. Verify import works**
```bash
uv run python -c "from faker import Faker; print(Faker().name())"
```

**Expected output**: Random name like "John Smith"

**3. Run affected tests**
```bash
uv run pytest tests/unit/testing/test_field_generators.py -v
uv run pytest tests/unit/testing/test_seed_generator.py -v
```

**Expected**: Tests collect and run (may pass or fail, but no import errors)

**Success Criteria**:
- [ ] `faker` in `pyproject.toml` dependencies
- [ ] `uv.lock` updated
- [ ] No import errors when collecting tests
- [ ] Tests run (results don't matter yet)

---

### Fix 2: Clean Up Linting Errors

**Objective**: Remove all unused imports and variables

**Estimated Time**: 10 minutes

#### Error 1: Unused `Optional` import

**File**: `src/cli/generate_tests.py:12`

**Fix**:
```python
# Before
from typing import List, Optional

# After
from typing import List
```

#### Error 2: Unused `parse_error` variable

**File**: `src/cli/generate_tests.py:68`

**Fix**:
```python
# Before
except Exception as parse_error:
    # Try as dict
    entity_dict = yaml.safe_load(entity_content)

# After
except Exception:
    # Try as dict
    entity_dict = yaml.safe_load(entity_content)
```

#### Error 3: Unused `pytest` import

**File**: `tests/cli/test_dry_run.py:3`

**Fix**:
```python
# Before
import pytest
from click.testing import CliRunner

# After
from click.testing import CliRunner
```

#### Error 4 & 5: Duplicate `Path` import

**File**: `tests/cli/test_generate_tests_command.py:5 and :46`

**Fix**:
```python
# Before (lines 3-6)
import pytest
from click.testing import CliRunner
from pathlib import Path  # ← Remove this unused import
from src.cli.confiture_extensions import specql

# ... later in file ...
def test_generate_tests_function_basic(self):
    from src.cli.generate_tests import _generate_tests_core
    import tempfile
    from pathlib import Path  # ← Keep this one, it's used

# After (lines 3-6)
import pytest
from click.testing import CliRunner
from src.cli.confiture_extensions import specql

# ... later in file ...
def test_generate_tests_function_basic(self):
    from src.cli.generate_tests import _generate_tests_core
    import tempfile
    from pathlib import Path  # ← Only import here where used
```

#### Validation Steps

**1. Run ruff check**
```bash
uv run ruff check src/ tests/
```

**Expected**: All checks passed (no output)

**2. Run auto-fix to verify**
```bash
uv run ruff check --fix src/cli/generate_tests.py
uv run ruff check --fix tests/cli/test_dry_run.py
uv run ruff check --fix tests/cli/test_generate_tests_command.py
```

**Expected**: Files fixed automatically

**3. Verify tests still pass**
```bash
uv run pytest tests/cli/test_generate_tests_command.py -v
uv run pytest tests/cli/test_dry_run.py -v
```

**Expected**: All tests pass

**Success Criteria**:
- [ ] Zero linting errors from `ruff check`
- [ ] All affected tests still pass
- [ ] Code functionality unchanged

---

### Fix 3: Remove pytest Conftest Conflict

**Objective**: Remove or relocate conflicting test directory

**Estimated Time**: 5 minutes

#### Analysis

**Conflicting file**: `/home/lionel/code/specql/user_journey_test/specql/tests/conftest.py`

**Options**:
1. **Delete entire `user_journey_test/` directory** (if obsolete)
2. **Move to archive** (if historical value)
3. **Rename conftest.py** (if still needed)

**Recommended**: Option 1 (delete if obsolete) or Option 2 (archive if unsure)

#### Steps

**1. Check if directory is needed**
```bash
ls -la user_journey_test/
git log --oneline user_journey_test/ | head -5
```

**Expected**: Understand when it was created and if it's current

**2a. If obsolete - Delete**
```bash
rm -rf user_journey_test/
```

**2b. If unsure - Archive**
```bash
mkdir -p ../specql_archived/
mv user_journey_test/ ../specql_archived/user_journey_test_$(date +%Y%m%d)/
```

**3. Verify pytest collection works**
```bash
uv run pytest --collect-only 2>&1 | grep "ERROR collecting" || echo "✅ No collection errors"
```

**Expected**: "✅ No collection errors"

**4. Run quick test subset**
```bash
uv run pytest tests/unit/cli/ -v
```

**Expected**: Tests run successfully

**Success Criteria**:
- [ ] No pytest collection errors
- [ ] `user_journey_test/` removed or archived
- [ ] Tests collect and run normally

---

### Fix 4: Run Complete Test Suite

**Objective**: Validate all tests pass after fixes

**Estimated Time**: 15 minutes (test runtime ~90 seconds + analysis)

#### Steps

**1. Run full test suite**
```bash
uv run pytest --tb=short -v --maxfail=10
```

**Expected**: May have some failures, but should collect all tests

**2. Analyze failures**
```bash
uv run pytest --tb=short --maxfail=5 2>&1 | tee test_results.txt
```

**3. Fix critical failures** (if any)

**Common issues to check**:
- Database connection (if required)
- Missing test fixtures
- Outdated test expectations
- Environment-specific failures

**4. Run tests by category**
```bash
# Unit tests (should be fast and reliable)
uv run pytest tests/unit/ -v

# CLI tests
uv run pytest tests/cli/ -v

# Integration tests (may need database)
uv run pytest tests/integration/ -v --maxfail=3

# Performance tests (optional)
uv run pytest tests/performance/ -v -k "not slow"
```

**5. Achieve acceptable pass rate**

**Targets**:
- Unit tests: 100% pass
- CLI tests: 100% pass
- Integration tests: 90%+ pass (some may need database setup)
- Performance tests: Can skip for release

**Success Criteria**:
- [ ] Test suite collects without errors
- [ ] Unit tests: 100% pass
- [ ] CLI tests: 100% pass
- [ ] Integration tests: >90% pass or skipped
- [ ] No critical test failures

---

### Fix 5: Type Checking (Optional but Recommended)

**Objective**: Ensure no type errors

**Estimated Time**: 10 minutes

#### Steps

**1. Run mypy on core modules**
```bash
uv run mypy src/cli/generate_tests.py --ignore-missing-imports
uv run mypy src/testing/ --ignore-missing-imports
uv run mypy src/core/ --ignore-missing-imports
```

**Expected**: May have some errors, but should identify issues

**2. Fix critical type errors** (if any)

**Common issues**:
- Missing return type annotations
- Incorrect type hints
- Optional values not handled

**3. Run targeted mypy check**
```bash
uv run mypy src/cli/generate_tests.py src/cli/templates.py --ignore-missing-imports --check-untyped-defs
```

**Success Criteria**:
- [ ] No critical type errors in CLI modules
- [ ] Type checking passes on generate_tests.py
- [ ] Type checking passes on templates.py (if modified)

**Note**: Full mypy compliance not required for v0.5.0-beta release, but recommended for v1.0

---

### Fix 6: Manual End-to-End Testing

**Objective**: Validate `generate-tests` command works for real use case

**Estimated Time**: 20 minutes

#### Test Case 1: Simple Entity

**1. Create test entity**
```bash
mkdir -p /tmp/specql_test
cat > /tmp/specql_test/simple_user.yaml << 'EOF'
entity: User
schema: app
description: Simple user entity for testing

fields:
  email:
    type: email
    required: true
    unique: true

  username:
    type: text
    required: true
    unique: true

  is_active:
    type: boolean
    default: true

  created_at:
    type: timestamptz
    default: now()

actions:
  - name: create_user
    type: create

  - name: deactivate_user
    type: custom
    operation: update
    set:
      is_active: false
EOF
```

**2. Test preview mode**
```bash
cd /home/lionel/code/specql
uv run python -m src.cli.confiture_extensions generate-tests \
    /tmp/specql_test/simple_user.yaml \
    --preview
```

**Expected output**:
```
🧪 Generating tests for User entity...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Preview Mode - Files that would be generated:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 tests/test_user_structure.sql (pgTAP)
   • Test table exists
   • Test columns exist with correct types
   • Test primary key constraint
   • Test unique constraints (email, username)
   • Test default values
   (10 tests)

📄 tests/test_user_crud.sql (pgTAP)
   • Test insert user
   • Test insert duplicate email fails
   • Test insert duplicate username fails
   • Test select user
   • Test update user
   • Test delete user
   (15 tests)

📄 tests/test_user_actions.sql (pgTAP)
   • Test create_user action
   • Test deactivate_user action
   (8 tests)

📄 tests/test_user_integration.py (pytest)
   • test_create_user_happy_path
   • test_create_user_duplicate_email
   • test_create_user_duplicate_username
   • test_deactivate_user
   • test_full_user_lifecycle
   (12 tests)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary: 4 files, 45 tests, ~380 lines
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**3. Test actual generation**
```bash
uv run python -m src.cli.confiture_extensions generate-tests \
    /tmp/specql_test/simple_user.yaml \
    --output-dir /tmp/specql_test/generated_tests/ \
    --verbose
```

**Expected**: Creates 4 test files

**4. Validate generated files**
```bash
# Check files exist
ls -lh /tmp/specql_test/generated_tests/

# Validate SQL syntax
for sql_file in /tmp/specql_test/generated_tests/*.sql; do
    echo "Checking $sql_file..."
    # Check for basic pgTAP structure
    grep -q "SELECT plan(" "$sql_file" && echo "  ✅ Has plan()" || echo "  ❌ Missing plan()"
    grep -q "SELECT \* FROM finish()" "$sql_file" && echo "  ✅ Has finish()" || echo "  ❌ Missing finish()"
done

# Validate Python syntax
python -m py_compile /tmp/specql_test/generated_tests/test_user_integration.py && \
    echo "✅ Python test is valid" || echo "❌ Python syntax error"
```

**5. Test different modes**
```bash
# pgTAP only
uv run python -m src.cli.confiture_extensions generate-tests \
    /tmp/specql_test/simple_user.yaml \
    --type pgtap \
    --output-dir /tmp/specql_test/pgtap_only/ \
    --verbose

# pytest only
uv run python -m src.cli.confiture_extensions generate-tests \
    /tmp/specql_test/simple_user.yaml \
    --type pytest \
    --output-dir /tmp/specql_test/pytest_only/ \
    --verbose
```

**Expected**: Each mode creates appropriate subset of files

#### Test Case 2: Complex Entity (PrintOptim Locale)

**1. Use existing entity YAML**
```bash
# If PrintOptim migration has Locale entity
cp /home/lionel/code/printoptim_migration/specql_entities_accurate/catalog/locale.yaml \
   /tmp/specql_test/locale.yaml

# Or create complex test entity
cat > /tmp/specql_test/locale.yaml << 'EOF'
entity: Locale
schema: catalog
description: Language + region locale codes

fields:
  code:
    type: text
    required: true
    unique: true

  language:
    type: ref
    entity: Language
    required: true

  is_active:
    type: boolean
    default: true

actions:
  - name: create_locale
    type: create

  - name: activate_locale
    type: custom
    operation: update
    set:
      is_active: true

  - name: list_active_locales
    type: query
    filter:
      is_active: true
EOF
```

**2. Generate tests**
```bash
uv run python -m src.cli.confiture_extensions generate-tests \
    /tmp/specql_test/locale.yaml \
    --output-dir /tmp/specql_test/locale_tests/ \
    --type all \
    --verbose
```

**Expected**: More tests due to foreign keys and complex actions

**3. Validate complexity handled**
```bash
# Check for foreign key tests
grep -i "foreign key\|fk_\|references" /tmp/specql_test/locale_tests/*.sql

# Check for action tests
grep -i "activate_locale\|list_active" /tmp/specql_test/locale_tests/*.sql
```

**Success Criteria**:
- [ ] Simple entity generates successfully
- [ ] Preview mode shows expected output
- [ ] All 4 file types generated (structure, crud, actions, integration)
- [ ] Generated SQL is syntactically valid
- [ ] Generated Python is syntactically valid
- [ ] pgTAP-only mode works
- [ ] pytest-only mode works
- [ ] Complex entity with FKs generates successfully
- [ ] Generated tests handle foreign keys
- [ ] Generated tests handle custom actions

---

### Fix 7: Create Git Tag and Prepare Release

**Objective**: Tag v0.5.0-beta and prepare for PyPI publish

**Estimated Time**: 10 minutes

#### Steps

**1. Final validation**
```bash
# Ensure all tests pass
uv run pytest --tb=short -q

# Ensure no linting errors
uv run ruff check src/ tests/

# Ensure version is correct
grep "version = " pyproject.toml
# Expected: version = "0.5.0-beta"
```

**2. Commit any final fixes**
```bash
git status
git add .
git commit -m "fix: resolve v0.5.0-beta release blockers

- Add faker dependency
- Fix linting errors (unused imports)
- Remove pytest conftest conflict
- Validate generate-tests command end-to-end

All tests passing. Ready for PyPI release.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**3. Create git tag**
```bash
git tag -a v0.5.0-beta -m "SpecQL v0.5.0-beta: Automatic Test Generation

Major Features:
- Automatic test generation (pgTAP + pytest)
- 70+ tests per entity from YAML definitions
- Test reverse engineering capabilities
- Comprehensive coverage analysis

Changes:
- Generate-tests command with preview mode
- Support for pgTAP and pytest generation
- Test generation guides and examples
- Enhanced CLI with improved UX

Testing:
- 600+ tests passing
- End-to-end validation complete
- Manual testing on complex entities

🚀 Ready for production use in PrintOptim migration"
```

**4. Push tag to GitHub**
```bash
git push origin pre-public-cleanup
git push origin v0.5.0-beta
```

**5. Verify tag on GitHub**
```bash
# Check tags
git tag -l
git show v0.5.0-beta
```

**Success Criteria**:
- [ ] All changes committed
- [ ] Git tag v0.5.0-beta created
- [ ] Tag pushed to GitHub
- [ ] Tag visible in GitHub releases

---

### Fix 8: Publish to PyPI

**Objective**: Make SpecQL v0.5.0-beta installable via `pip install specql-generator`

**Estimated Time**: 15 minutes

#### Prerequisites

**1. Verify PyPI credentials**
```bash
# Check if ~/.pypirc exists
cat ~/.pypirc

# Or check for API token
echo $PYPI_API_TOKEN
```

**2. Verify package metadata**
```bash
cat pyproject.toml | grep -A 10 "\[project\]"
```

**Expected**:
```toml
[project]
name = "specql-generator"
version = "0.5.0-beta"
description = "Multi-language backend code generator from YAML specifications"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Lionel Martin", email = "your-email@example.com"}
]
```

#### Build and Publish Steps

**1. Clean previous builds**
```bash
rm -rf dist/ build/ *.egg-info
```

**2. Build package**
```bash
uv build
```

**Expected output**:
```
Building specql-generator
  Building sdist...
  Built specql-generator-0.5.0b0.tar.gz
  Building wheel...
  Built specql_generator-0.5.0b0-py3-none-any.whl
```

**Note**: PyPI normalizes `0.5.0-beta` to `0.5.0b0` (PEP 440 standard)

**3. Verify build**
```bash
ls -lh dist/
```

**Expected**: 2 files
- `specql-generator-0.5.0b0.tar.gz` (source distribution)
- `specql_generator-0.5.0b0-py3-none-any.whl` (wheel)

**4. Test package locally**
```bash
# Create test environment
python -m venv /tmp/test_specql_env
source /tmp/test_specql_env/bin/activate

# Install from local wheel
pip install dist/specql_generator-0.5.0b0-py3-none-any.whl

# Test installation
specql --help
python -c "from src.cli.generate_tests import generate_tests; print('✅ Import works')"

# Cleanup
deactivate
rm -rf /tmp/test_specql_env
```

**5. Publish to TestPyPI first** (recommended)
```bash
uv publish --repository testpypi
```

**Expected**: Prompts for TestPyPI credentials or uses token

**6. Test installation from TestPyPI**
```bash
pip install --index-url https://test.pypi.org/simple/ specql-generator==0.5.0b0
```

**7. Publish to production PyPI**
```bash
uv publish
```

**Expected**:
```
Uploading specql-generator-0.5.0b0.tar.gz
Uploading specql_generator-0.5.0b0-py3-none-any.whl
✅ Successfully published specql-generator 0.5.0b0
```

**8. Verify on PyPI**
```bash
# Check PyPI page
open https://pypi.org/project/specql-generator/

# Test installation
python -m venv /tmp/test_from_pypi
source /tmp/test_from_pypi/bin/activate
pip install specql-generator==0.5.0b0
specql --version
specql generate-tests --help
deactivate
```

**Success Criteria**:
- [ ] Package builds successfully
- [ ] Local installation works
- [ ] TestPyPI publish succeeds
- [ ] Production PyPI publish succeeds
- [ ] Package visible on PyPI
- [ ] `pip install specql-generator` works
- [ ] CLI commands accessible

---

### Fix 9: Create GitHub Release

**Objective**: Create official release on GitHub with changelog

**Estimated Time**: 10 minutes

#### Steps

**1. Navigate to GitHub releases**
```bash
# Open in browser
open https://github.com/fraiseql/specql/releases/new
```

**Or use GitHub CLI**:
```bash
# Install if needed
# brew install gh

# Create release
gh release create v0.5.0-beta \
    --title "SpecQL v0.5.0-beta: Automatic Test Generation" \
    --notes-file CHANGELOG_v0.5.0-beta.md \
    --prerelease
```

**2. Fill release form**

**Tag version**: `v0.5.0-beta`

**Release title**: `SpecQL v0.5.0-beta: Automatic Test Generation`

**Description**: Use content from `CHANGELOG_v0.5.0-beta.md`

**Attach binaries**: (optional) Include `dist/` files

**Mark as pre-release**: ✅ (since it's beta)

**3. Publish release**

**4. Verify release**
```bash
open https://github.com/fraiseql/specql/releases/tag/v0.5.0-beta
```

**Success Criteria**:
- [ ] GitHub release created
- [ ] Changelog visible
- [ ] Marked as pre-release
- [ ] Download links work

---

## Validation Checklist

After completing all fixes, validate:

### Core Functionality
- [ ] `uv add faker` completes successfully
- [ ] All imports work (no `ModuleNotFoundError`)
- [ ] `ruff check src/ tests/` returns zero errors
- [ ] `pytest --collect-only` succeeds without errors
- [ ] Unit tests: 100% pass
- [ ] CLI tests: 100% pass
- [ ] Integration tests: >90% pass

### Test Generation Command
- [ ] `specql generate-tests --help` works
- [ ] Preview mode shows expected output
- [ ] Generates all 4 file types (structure, crud, actions, integration)
- [ ] Generated SQL is syntactically valid
- [ ] Generated Python is syntactically valid
- [ ] Handles simple entities correctly
- [ ] Handles complex entities with FKs correctly
- [ ] `--type pgtap` mode works
- [ ] `--type pytest` mode works
- [ ] `--verbose` flag provides useful output

### Release Artifacts
- [ ] Git tag v0.5.0-beta exists
- [ ] Tag pushed to GitHub
- [ ] Package builds (`uv build` succeeds)
- [ ] Package installs locally
- [ ] Published to PyPI
- [ ] `pip install specql-generator==0.5.0b0` works
- [ ] GitHub release created
- [ ] Release marked as pre-release

### Documentation
- [ ] README accurate
- [ ] CHANGELOG complete
- [ ] Release checklist updated
- [ ] Test generation guide accurate
- [ ] All links work

---

## Timeline Estimate

| Task | Estimated Time | Dependencies |
|------|----------------|--------------|
| **Fix 1**: Add faker dependency | 5 min | None |
| **Fix 2**: Clean up linting | 10 min | None |
| **Fix 3**: Remove conftest conflict | 5 min | None |
| **Fix 4**: Run test suite | 15 min | Fix 1, 2, 3 |
| **Fix 5**: Type checking | 10 min | None (optional) |
| **Fix 6**: Manual E2E testing | 20 min | All above |
| **Fix 7**: Git tag | 10 min | All above |
| **Fix 8**: PyPI publish | 15 min | Fix 7 |
| **Fix 9**: GitHub release | 10 min | Fix 7, 8 |
| **Total** | **1.5-2 hours** | Sequential |

**Best Case**: 90 minutes (everything works first try)
**Realistic**: 2-3 hours (some debugging needed)
**Worst Case**: 4 hours (unexpected test failures)

---

## Risk Assessment

### Low Risk ✅

1. **faker dependency** - Standard package, well-tested
2. **Linting fixes** - Automated, can't break functionality
3. **Git tagging** - Easy to delete/recreate if needed
4. **Documentation** - Already complete

### Medium Risk ⚠️

1. **Conftest removal** - Could affect test discovery
   - **Mitigation**: Archive first, don't delete
   - **Rollback**: Restore from archive

2. **Test failures** - Some tests may fail after fixes
   - **Mitigation**: Fix progressively, not all-or-nothing
   - **Rollback**: Focus on unit tests first

3. **PyPI publish** - Can't unpublish once done
   - **Mitigation**: Test on TestPyPI first
   - **Fallback**: Publish v0.5.0-beta.1 if needed

### High Risk ❌

None identified - all fixes are low-impact and reversible

---

## Rollback Plan

If issues arise during execution:

### Rollback Steps

**1. Uncommitted changes**
```bash
git restore .
git clean -fd
```

**2. Committed changes**
```bash
git reset --hard HEAD~1
```

**3. Pushed commits**
```bash
git revert <commit-hash>
git push origin pre-public-cleanup
```

**4. Git tag**
```bash
git tag -d v0.5.0-beta
git push origin :refs/tags/v0.5.0-beta
```

**5. PyPI release**
- **Cannot unpublish** - Must publish v0.5.0-beta.1 with fixes
- Or yank version: `pip install twine && twine yank specql-generator 0.5.0b0`

**6. GitHub release**
```bash
gh release delete v0.5.0-beta
```

---

## Success Metrics

### Technical Metrics
- ✅ Test pass rate: 100% (unit), >90% (integration)
- ✅ Linting errors: 0
- ✅ Import errors: 0
- ✅ Package size: <5MB
- ✅ Install time: <30 seconds

### Quality Metrics
- ✅ Generate-tests works on 10+ test entities
- ✅ Generated tests are valid SQL/Python
- ✅ Documentation accurate
- ✅ Examples work

### Release Metrics
- ✅ PyPI package available
- ✅ GitHub release published
- ✅ Tag created and pushed
- ✅ Ready for PrintOptim migration

---

## Post-Release Actions

After successful release:

### Immediate (Same Day)
1. Test installation on clean machine
2. Update SpecQL documentation site (if exists)
3. Announce on social media (from marketing content)
4. Monitor PyPI download stats
5. Monitor GitHub issues for bug reports

### Week 1
1. Begin PrintOptim migration with v0.5.0-beta
2. Collect user feedback
3. Fix critical bugs if found (publish v0.5.0-beta.1)
4. Update documentation based on feedback

### Week 2-4
1. Plan v0.6.0 features based on PrintOptim learnings
2. Improve test generation based on real-world usage
3. Enhance documentation with PrintOptim case study
4. Consider v0.5.0 stable release (drop beta)

---

## Next Steps for Agent Execution

An agent executing this plan should:

1. **Execute fixes sequentially** - Each fix builds on previous
2. **Validate after each fix** - Don't proceed if something fails
3. **Document any deviations** - Note unexpected issues
4. **Capture error messages** - Save for troubleshooting
5. **Test incrementally** - Don't wait until end to test
6. **Update release checklist** - Mark items complete
7. **Create clean commit messages** - Follow existing patterns
8. **Test the published package** - Ensure end-users will succeed

**Ready to execute!** 🚀

---

## Appendix: Command Reference

### Quick Fix Commands
```bash
# All fixes in sequence
cd /home/lionel/code/specql

# Fix 1: faker
uv add faker

# Fix 2: linting
uv run ruff check --fix src/cli/generate_tests.py
uv run ruff check --fix tests/cli/test_dry_run.py
uv run ruff check --fix tests/cli/test_generate_tests_command.py

# Fix 3: conftest
rm -rf user_journey_test/  # or mv to archive

# Fix 4: tests
uv run pytest --tb=short -v

# Fix 5: type checking (optional)
uv run mypy src/cli/generate_tests.py --ignore-missing-imports

# Fix 6: manual testing
uv run python -m src.cli.confiture_extensions generate-tests \
    /tmp/specql_test/simple_user.yaml --preview

# Fix 7: git tag
git add .
git commit -m "fix: resolve v0.5.0-beta release blockers"
git tag -a v0.5.0-beta -m "SpecQL v0.5.0-beta: Automatic Test Generation"
git push origin pre-public-cleanup
git push origin v0.5.0-beta

# Fix 8: PyPI
uv build
uv publish

# Fix 9: GitHub release
gh release create v0.5.0-beta \
    --title "SpecQL v0.5.0-beta: Automatic Test Generation" \
    --notes-file CHANGELOG_v0.5.0-beta.md \
    --prerelease
```

### Validation Commands
```bash
# Quick validation
uv run ruff check src/ tests/
uv run pytest tests/unit/ tests/cli/ -v
uv run python -m src.cli.confiture_extensions generate-tests --help

# Full validation
uv run pytest --tb=short -v
uv run mypy src/cli/ --ignore-missing-imports
pip install dist/specql_generator-0.5.0b0-py3-none-any.whl
specql generate-tests --help
```

---

**Document Status**: Ready for execution
**Estimated Completion**: 2-3 hours
**Risk Level**: Low
**Next Action**: Execute Fix 1 (Add faker dependency)
