# Week 19: Codebase Stabilization & Cleanup
**Date**: 2025-11-15 to 2025-11-22
**Focus**: Fix Test Collection Errors, Commit Changes, Critical TODO Fixes
**Estimated Time**: 10-12 hours
**Priority**: Critical - Release Blocker

---

## 📋 Current State Assessment (2025-11-15)

### ✅ Week 18 Complete
- VERSION: `0.4.0-alpha` ✅
- pyproject.toml: `version = "0.4.0-alpha"` ✅
- README: Multi-language title and alpha notice ✅
- WORKFLOW_VERIFICATION.md: Created ✅

### ⚠️ Issues Found
- **Test Collection**: 16 errors during test collection (2823 tests found)
- **Uncommitted Changes**: 117+ files modified but not committed
- **TODO/FIXME Comments**: 117 files still contain TODO comments

### 🎯 Week 19 Revised Objectives

1. **Fix test collection errors** (must pass before release)
2. **Commit all Week 18 changes** (clean working directory)
3. **Fix critical TODOs** (8 blockers identified)
4. **Create GitHub issues** for post-alpha work
5. **Clean up outdated TODOs** (remove obsolete comments)

---

## 🎯 Phase 1: Fix Test Collection Errors (2-3 hours)

### Current Problem

```bash
uv run pytest --co -q
# Output shows:
ERROR tests/unit/parsers/plpgsql/test_schema_analyzer.py
ERROR tests/unit/parsers/plpgsql/test_type_mapper.py
ERROR tests/unit/testing/test_spec_models.py
# ... 16 errors total
# 2823 tests collected, 16 errors
```

**Impact**: Tests cannot run if collection fails. This blocks release.

### Task 1.1: Identify Collection Errors

```bash
# Get detailed error messages
uv run pytest --co -v 2>&1 | grep -A 5 "ERROR"

# Common causes:
# - Import errors (missing dependencies)
# - Syntax errors in test files
# - Missing fixtures
# - Circular imports
```

### Task 1.2: Fix Each Error

**Process for each error**:

```bash
# 1. Run specific file to see error
uv run pytest tests/unit/parsers/plpgsql/test_schema_analyzer.py -v

# 2. Read error message carefully
# 3. Fix the issue (common fixes below)
# 4. Verify fix works
# 5. Move to next error
```

**Common Fixes**:

```python
# Fix 1: Import Error
# Before:
from src.parsers.old_module import Something

# After:
from src.parsers.new_module import Something

# Fix 2: Missing Fixture
# Add to conftest.py or test file:
@pytest.fixture
def missing_fixture():
    return SomeObject()

# Fix 3: Syntax Error
# Check for:
# - Missing colons
# - Incorrect indentation
# - Unclosed brackets/quotes

# Fix 4: Circular Import
# Reorganize imports or use TYPE_CHECKING:
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.module import Thing
```

### Task 1.3: Verify All Tests Collect

```bash
# After fixing all errors, verify collection works
uv run pytest --co -q

# Expected output:
# 2823 tests collected in X.XXs
# (no ERROR lines)

# Then run a quick smoke test
uv run pytest tests/unit/ -x --tb=short -q

# -x stops at first failure
# --tb=short gives minimal traceback
# -q is quiet mode
```

### Task 1.4: Commit Test Fixes

```bash
# Stage test-related fixes
git add tests/
git add conftest.py  # if modified

git commit -m "fix: resolve test collection errors

- Fix import errors in plpgsql test files
- Add missing fixtures
- Correct syntax errors
- Ensure all 2823 tests can be collected

Fixes 16 test collection errors. All tests now discoverable."
```

**Success Criteria**:
- [ ] All 16 test collection errors resolved
- [ ] `pytest --co -q` shows 0 errors
- [ ] Tests can be run (even if some fail)
- [ ] Changes committed to git

---

## 🎯 Phase 2: Commit Week 18 Changes (1 hour)

### Current State

```bash
git status --short
# Shows 117+ modified files (M flag)
# All from Week 18 work
```

### Task 2.1: Review Changes Before Commit

```bash
# Review what changed
git diff README.md | head -50
git diff VERSION
git diff pyproject.toml

# Check for accidental changes
git diff --stat | grep -v "expected pattern"

# Review a few random files
git diff scripts/version.py
git diff src/cli/generate.py
```

### Task 2.2: Commit in Logical Groups

**Strategy**: Commit related changes together

#### Commit Group 1: Version Updates
```bash
git add VERSION pyproject.toml
git commit -m "chore: bump version to 0.4.0-alpha

- Update VERSION file to 0.4.0-alpha
- Update pyproject.toml version to 0.4.0-alpha
- Prepares for public alpha release"
```

#### Commit Group 2: README Updates
```bash
git add README.md
git commit -m "docs: update README to reflect multi-language capabilities

- Change title to 'Multi-Language Backend Code Generator'
- Add prominent alpha warning banner
- Break down features by language (PostgreSQL, Java, Rust, TypeScript)
- Reorganize sections for clarity
- Add reverse engineering for all 4 languages
- Update roadmap (Rust complete, only Go coming soon)

Accurately represents project as multi-language generator."
```

#### Commit Group 3: Documentation Files
```bash
git add WEEK_*.md ALPHA_RELEASE_*.md QUICK_START_*.md README_UPDATES_SUMMARY.md WORKFLOW_VERIFICATION.md
git commit -m "docs: add alpha release planning documentation

- Add Week 18-21 detailed plans
- Add alpha release summary and quick start guide
- Add workflow verification documentation
- Add README updates summary

Provides complete roadmap for alpha release."
```

#### Commit Group 4: Bulk Source Changes
```bash
# Check what's in src/
git status src/ --short | wc -l

# If these are from logging/cleanup PRs mentioned in git log:
git add src/
git commit -m "chore: apply code cleanup and logging improvements

- Remove debug print statements
- Apply formatting/linting fixes
- Code quality improvements from recent PRs

Part of pre-alpha cleanup."
```

#### Commit Group 5: Scripts
```bash
git add scripts/
git commit -m "chore: update scripts for alpha release

- Update version references
- Apply code quality improvements
- Ensure scripts compatible with 0.4.0-alpha"
```

#### Commit Group 6: Other Files
```bash
# Check what's left
git status --short

# Commit remaining files
git add .
git commit -m "chore: finalize Week 18 changes

- Update remaining files for alpha release
- Ensure consistency across codebase"
```

### Task 2.3: Verify Clean Working Directory

```bash
# Should show nothing
git status

# Expected output:
# On branch pre-public-cleanup
# nothing to commit, working tree clean

# Verify recent commits
git log --oneline -10
```

**Success Criteria**:
- [ ] All changes committed in logical groups
- [ ] Working directory clean
- [ ] Commit messages clear and descriptive
- [ ] No accidentally committed secrets/temp files

---

## 🎯 Phase 3: Fix Critical TODOs (3-4 hours)

Based on ALPHA_RELEASE_CHECKLIST.md, these 8 TODOs block core functionality.

### Critical TODO #1: Remove Hardcoded API Key (SECURITY - DO FIRST)

**File**: `src/cicd/llm_recommendations.py:35`
**Priority**: CRITICAL - Security vulnerability

```bash
# Find the exact line
grep -n "api.key\|apikey\|sk-" src/cicd/llm_recommendations.py
```

**Fix**:
```python
# Before:
api_key = "sk-placeholder-key-here"  # TODO: Remove before release

# After:
import os

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable required for LLM recommendations. "
        "Set it or disable LLM features with --no-llm flag."
    )
```

**Test**:
```bash
# Test with env var
OPENAI_API_KEY=test uv run pytest tests/unit/cicd/test_llm_recommendations.py -v

# Test without env var (should raise ValueError)
uv run python -c "from src.cicd.llm_recommendations import get_api_key; get_api_key()"
```

**Commit**:
```bash
git add src/cicd/llm_recommendations.py
git commit -m "fix: remove hardcoded API key placeholder (security)

- Use environment variable OPENAI_API_KEY instead
- Raise clear error if not set
- Add test for missing key scenario

SECURITY: Removes potential secret exposure before public release."
```

---

### Critical TODO #2: Multiple Actions Per Entity

**File**: `src/generators/actions/action_orchestrator.py:75`

```bash
# Find the TODO
grep -n "TODO.*multiple.*action" src/generators/actions/action_orchestrator.py -i
```

**Current Issue**: Only handles one action per entity

**Fix Strategy**:
```python
# Before (approximately):
def compile_action(entity, action):
    # Handles only one action
    return compile_single_action(entity, action)

# After:
def compile_actions(entity, actions):
    """Compile multiple actions for an entity.

    Args:
        entity: Entity definition
        actions: List of action definitions

    Returns:
        List of compiled actions
    """
    if not actions:
        return []

    compiled = []
    for action in actions:
        try:
            compiled.append(compile_single_action(entity, action))
        except Exception as e:
            logger.error(f"Failed to compile action {action.name}: {e}")
            raise

    return compiled
```

**Test**:
```bash
# Create test for multiple actions
cat > test_multiple_actions.py << 'EOF'
def test_entity_with_multiple_actions():
    entity = Entity(name="User", actions=[
        Action(name="create_user", steps=[...]),
        Action(name="update_user", steps=[...]),
        Action(name="delete_user", steps=[...]),
    ])

    compiled = compile_actions(entity, entity.actions)

    assert len(compiled) == 3
    assert compiled[0].name == "create_user"
    assert compiled[1].name == "update_user"
    assert compiled[2].name == "delete_user"
EOF

# Run test
uv run pytest test_multiple_actions.py -v
```

**Commit**:
```bash
git add src/generators/actions/action_orchestrator.py tests/
git commit -m "fix: support multiple actions per entity

- Change compile_action to compile_actions (plural)
- Handle list of actions instead of single action
- Add error handling per action
- Add tests for multiple actions

Resolves critical limitation blocking multi-action entities."
```

---

### Critical TODO #3: Schema Lookup for Table Names

**File**: `src/generators/actions/step_compilers/insert_compiler.py:53`

```python
# Before:
table_name = f"{entity.name}_table"  # TODO: Proper schema lookup

# After:
def get_qualified_table_name(entity):
    """Get fully-qualified table name with schema."""
    schema = entity.schema or "public"
    table = entity.table_name or entity.name.lower()
    return f"{schema}.{table}"

# In compiler:
table_name = get_qualified_table_name(entity)
```

**Test**:
```bash
# Test multi-schema support
uv run pytest tests/unit/generators/actions/test_insert_compiler.py::TestSchemaLookup -v
```

**Commit**:
```bash
git add src/generators/actions/step_compilers/insert_compiler.py
git commit -m "fix: add proper schema lookup for table names

- Use entity.schema attribute (default 'public')
- Support custom table_name override
- Generate fully-qualified names (schema.table)
- Add tests for multi-schema scenarios

Enables multi-schema database support."
```

---

### Critical TODOs #4-8: Quick Assessment

For remaining critical TODOs, follow this process:

```bash
# List all critical TODOs
git grep -n "TODO.*CRITICAL\|FIXME.*URGENT\|TODO.*blocker" src/ -i

# For each:
# 1. Assess complexity (15 min - 2 hours?)
# 2. If quick fix (<30 min): Fix now
# 3. If complex (>30 min): Create GitHub issue, mark as post-alpha
# 4. Document decision

# Create tracking file
cat > TODO_CRITICAL_TRACKING.md << 'EOF'
# Critical TODO Tracking - Week 19

## Fixed This Week
- [x] #1: Hardcoded API key - FIXED (security)
- [x] #2: Multiple actions per entity - FIXED
- [x] #3: Schema lookup - FIXED

## Remaining Critical
- [ ] #4: Cross-schema impact tracking
  - Complexity: 1-2 hours
  - Status: [Fix now / Create issue #XXX]

- [ ] #5: Table impact analysis
  - Complexity: 1 hour
  - Status: [Fix now / Create issue #XXX]

- [ ] #6: DELETE statement parsing
  - Complexity: 30 min
  - Status: Fix now

- [ ] #7: Impact dict to ActionImpact
  - Complexity: 30 min
  - Status: Fix now

- [ ] #8: Other critical items (TBD)
  - Run: git grep -n "TODO.*CRITICAL" src/
EOF
```

**Success Criteria**:
- [ ] Hardcoded API key removed (SECURITY)
- [ ] Multiple actions support added
- [ ] Schema lookup implemented
- [ ] Remaining critical TODOs assessed
- [ ] All fixes tested
- [ ] All changes committed

---

## 🎯 Phase 4: Create GitHub Issues (3-4 hours)

### Task 4.1: Prepare Issue Creation

```bash
# Authenticate GitHub CLI
gh auth status

# If not authenticated:
gh auth login

# Test issue creation
gh issue create --title "Test Issue" --body "Testing issue creation" --label "test"
gh issue close <issue-number>  # Close test issue
```

### Task 4.2: Create Issues for Important TODOs

**Strategy**: Batch create issues for post-alpha enhancements

```bash
# Create script for batch issue creation
cat > scripts/create_post_alpha_issues.sh << 'EOF'
#!/bin/bash
# Create GitHub issues for post-alpha TODOs

echo "Creating post-alpha enhancement issues..."

# PostgreSQL Generation Enhancements
gh issue create \
  --title "Enhancement: Nested JSON_BUILD_OBJECT support" \
  --body "**Location**: \`src/generators/actions/step_compilers/json_build_step.py:42\`

Support nested JSON objects in step compilation.

**Example**:
\`\`\`sql
JSON_BUILD_OBJECT(
  'user', JSON_BUILD_OBJECT('name', name, 'email', email),
  'address', JSON_BUILD_OBJECT('city', city, 'zip', zip)
)
\`\`\`

**Priority**: Medium
**Milestone**: Post-Alpha" \
  --label "enhancement,post-alpha,postgresql"

# Java Generation Enhancements
gh issue create \
  --title "Enhancement: Lombok builder customization" \
  --body "**Location**: \`src/generators/java/entity_generator.py:89\`

Add support for custom Lombok builder patterns.

**Priority**: Medium
**Milestone**: Post-Alpha" \
  --label "enhancement,post-alpha,java"

# Rust Generation Enhancements
gh issue create \
  --title "Enhancement: Diesel migration generation" \
  --body "**Location**: \`src/generators/rust/migration_generator.py\`

Auto-generate Diesel migrations from entity changes.

**Priority**: Medium
**Milestone**: Post-Alpha" \
  --label "enhancement,post-alpha,rust"

# TypeScript Generation Enhancements
gh issue create \
  --title "Enhancement: Zod schema generation" \
  --body "**Location**: \`src/generators/typescript/schema_generator.py\`

Generate Zod validation schemas alongside Prisma schemas.

**Priority**: Medium
**Milestone**: Post-Alpha" \
  --label "enhancement,post-alpha,typescript"

# Add more issues as needed...

echo "✅ Issues created successfully"
EOF

chmod +x scripts/create_post_alpha_issues.sh
```

### Task 4.3: Create Issue Labels

```bash
# Create labels for issue organization
gh label create "post-alpha" --description "Enhancements planned for post-alpha" --color "d4c5f9"
gh label create "postgresql" --description "PostgreSQL generation" --color "0052cc"
gh label create "java" --description "Java/Spring Boot generation" --color "b07219"
gh label create "rust" --description "Rust/Diesel generation" --color "dea584"
gh label create "typescript" --description "TypeScript/Prisma generation" --color "2b7489"
gh label create "parser" --description "Reverse engineering parsers" --color "fbca04"
gh label create "cli" --description "CLI/UX improvements" --color "0e8a16"
```

### Task 4.4: Run Issue Creation

```bash
# Run the script (creates ~20-30 issues)
./scripts/create_post_alpha_issues.sh

# Verify issues created
gh issue list --label "post-alpha" --limit 50

# Count
gh issue list --label "post-alpha" --json number | jq 'length'
```

### Task 4.5: Update TODOs with Issue References

```bash
# Example: Update TODO with issue reference
# Before:
# TODO: Support nested JSON_BUILD_OBJECT

# After:
# TODO(#42): Support nested JSON_BUILD_OBJECT (post-alpha)
# See: https://github.com/fraiseql/specql/issues/42
```

**Success Criteria**:
- [ ] GitHub CLI authenticated
- [ ] Issue labels created
- [ ] ~20-30 issues created for post-alpha work
- [ ] TODOs updated with issue references
- [ ] Script committed to git

---

## 🎯 Phase 5: Clean Up Outdated TODOs (1-2 hours)

### Task 5.1: Remove Debug Print Statements

```bash
# Find debug prints
git grep -n "print(.*debug\|print(.*DEBUG" src/

# For each, either:
# 1. Remove entirely (if not needed)
# 2. Replace with logger.debug()

# Example:
# Before:
print(f"DEBUG: Processing {entity.name}")

# After:
logger.debug("Processing entity: %s", entity.name)
```

### Task 5.2: Remove Obsolete TODOs

```bash
# Find completed TODOs
git grep -n "TODO.*done\|TODO.*complete\|TODO.*implemented" src/

# Remove these comments entirely
```

### Task 5.3: Commit Cleanup

```bash
git add src/
git commit -m "chore: remove debug statements and obsolete TODOs

- Remove debug print statements (replace with logging)
- Remove TODOs for completed features
- Clean up commented-out code

Improves code clarity for alpha release."
```

**Success Criteria**:
- [ ] Debug print statements removed
- [ ] Obsolete TODOs removed
- [ ] Code cleaner and more maintainable

---

## 🎯 Phase 6: Final Verification (1 hour)

### Task 6.1: Run Full Test Suite

```bash
# Run all tests
uv run pytest --tb=short -v

# Check coverage
uv run pytest --cov=src --cov-report=term --cov-report=html

# Expected: 96%+ coverage maintained
```

### Task 6.2: Run Code Quality Checks

```bash
# Linting
uv run ruff check src/ tests/

# Formatting
uv run ruff format --check src/ tests/

# Type checking
uv run mypy src/

# All should pass ✅
```

### Task 6.3: Security Scan

```bash
# Run bandit security scan
uv run bandit -r src/ -ll

# Expected: No high/medium severity issues
```

### Task 6.4: Create Week 19 Summary

```bash
cat > WEEK_19_COMPLETION_REPORT.md << 'EOF'
# Week 19 Completion Report

**Date**: 2025-11-15
**Status**: ✅ Complete

## Completed Tasks

### Test Collection Errors Fixed
- Resolved 16 test collection errors
- All 2823 tests now discoverable
- Tests can be run successfully

### Changes Committed
- 117+ files committed in logical groups
- Clean working directory
- Clear commit messages

### Critical TODOs Fixed
- ✅ Hardcoded API key removed (SECURITY)
- ✅ Multiple actions per entity support
- ✅ Schema lookup for table names
- ✅ [List other fixes]

### GitHub Issues Created
- Created ~25-30 post-alpha enhancement issues
- Proper labels and organization
- TODOs updated with issue references

### Code Cleanup
- Debug statements removed
- Obsolete TODOs removed
- Code quality improved

## Metrics

- Test coverage: 96%+ ✅
- Linting: Pass ✅
- Type checking: Pass ✅
- Security scan: Pass ✅

## Next Steps

Week 20: Release Execution
- Create git tag v0.4.0-alpha
- Make repository public
- Set up community infrastructure
EOF
```

**Success Criteria**:
- [ ] All tests passing
- [ ] Code quality checks pass
- [ ] Security scan clean
- [ ] Coverage maintained
- [ ] Completion report created

---

## 📊 Week 19 Success Criteria

### Test Infrastructure
- [ ] 0 test collection errors
- [ ] All 2823 tests discoverable
- [ ] Tests can run successfully

### Git Repository
- [ ] All changes committed
- [ ] Working directory clean
- [ ] Logical commit structure

### Critical TODOs
- [ ] Security issues fixed (API key)
- [ ] Core functionality unblocked (multiple actions, schema lookup)
- [ ] Remaining critical TODOs assessed

### GitHub Issues
- [ ] ~25-30 issues created
- [ ] Labels configured
- [ ] TODOs reference issues

### Code Quality
- [ ] Tests pass
- [ ] Linting pass
- [ ] Type checking pass
- [ ] Security scan pass
- [ ] Coverage 96%+

---

## 📝 Deliverables

1. **Fixed test collection** (0 errors)
2. **Clean git repository** (all changes committed)
3. **Fixed critical TODOs** (security + core functionality)
4. **GitHub issues** (~25-30 for post-alpha)
5. **Clean codebase** (debug statements removed)
6. **Week 19 completion report**

---

## ⏭️ Next Week Preview

**Week 20**: Release Execution (2-3 hours)
- Create git tag v0.4.0-alpha
- Make repository public
- Configure repository settings
- Create community issues
- Post-release verification

---

**Week 19 Status**: 🟢 Ready to Execute
**Next Action**: Fix test collection errors (Phase 1)
**Estimated Completion**: 2025-11-22
