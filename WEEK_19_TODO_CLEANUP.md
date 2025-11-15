# Week 19: TODO/FIXME Cleanup Campaign
**Date**: 2025-11-22 to 2025-11-29
**Focus**: Critical TODO Fixes, GitHub Issue Creation, and Code Cleanup
**Estimated Time**: 10-12 hours
**Priority**: Critical - Release Blocker

---

## 📋 Overview

**Current State**: 393 TODO/FIXME lines across 117 files
**Target State**: 8 critical TODOs fixed, 85 converted to issues, 25 removed, 13 clarified

This week focuses on cleaning up the codebase to prepare for public alpha release by:
1. Fixing critical TODOs that block core functionality
2. Creating GitHub issues for important enhancements
3. Removing outdated debug/TODO comments
4. Clarifying deferred TODOs for post-alpha work

**Reference**: See ALPHA_RELEASE_TODO_CLEANUP_PLAN.md for complete categorization

---

## 🎯 Phase 1: Fix Critical TODOs (3-4 hours)

These 8 TODOs block core functionality and **must** be fixed before alpha release.

### Critical TODO #1: Multiple Actions Per Entity
**File**: `src/generators/actions/action_orchestrator.py`
**Line**: ~75
**Current Issue**: Only supports single action per entity
**Impact**: Limits entities to one operation (can't have both create and update)

**Fix Strategy**:
```python
# Current (broken):
def compile_action(entity, action):
    # Only handles one action
    return single_action

# Target (fixed):
def compile_actions(entity, actions):
    # Handle multiple actions per entity
    compiled = []
    for action in actions:
        compiled.append(compile_single_action(entity, action))
    return compiled
```

**Testing**:
```bash
# Test with entity that has multiple actions
uv run pytest tests/unit/generators/test_action_orchestrator.py::TestMultipleActions -v
```

**Success Criteria**:
- [ ] Function supports list of actions
- [ ] Each action compiled independently
- [ ] Tests pass for multi-action entities
- [ ] No regression in single-action cases

---

### Critical TODO #2: Schema Lookup for Table Names
**File**: `src/generators/actions/step_compilers/insert_compiler.py`
**Line**: ~53
**Current Issue**: Hardcoded schema assumptions
**Impact**: Breaks for multi-schema databases

**Fix Strategy**:
```python
# Current (broken):
table_name = f"{entity.name}_table"

# Target (fixed):
schema = entity.schema or "public"
table_name = f"{schema}.{entity.table_name or entity.name.lower()}"
```

**Testing**:
```bash
uv run pytest tests/unit/generators/actions/test_insert_compiler.py::TestSchemaLookup -v
```

**Success Criteria**:
- [ ] Respects entity.schema attribute
- [ ] Falls back to "public" if no schema
- [ ] Fully qualified table names (schema.table)
- [ ] Tests pass for multi-schema scenarios

---

### Critical TODO #3: Cross-Schema Support
**File**: `src/generators/actions/impact_metadata_compiler.py`
**Line**: ~126
**Current Issue**: Impact analysis doesn't track cross-schema references
**Impact**: Incorrect dependency graph for multi-schema databases

**Fix Strategy**:
```python
# Add schema to impact tracking
class ActionImpact:
    table_name: str
    schema: str  # NEW

    @property
    def qualified_name(self):
        return f"{self.schema}.{self.table_name}"
```

**Testing**:
```bash
uv run pytest tests/unit/generators/actions/test_impact_metadata_compiler.py::TestCrossSchema -v
```

**Success Criteria**:
- [ ] Impact includes schema information
- [ ] Cross-schema references tracked
- [ ] Dependency graph correct for multi-schema
- [ ] Tests pass

---

### Critical TODO #4: Table Impact Analysis
**File**: `src/parsers/plpgsql/function_analyzer.py`
**Line**: ~64
**Current Issue**: Doesn't detect all table references in functions
**Impact**: Incomplete reverse engineering of PL/pgSQL

**Fix Strategy**:
```python
def analyze_table_impacts(function_ast):
    impacts = []

    # Detect INSERT INTO
    for insert in find_nodes(ast, "INSERT"):
        impacts.append(TableImpact("insert", insert.table))

    # Detect UPDATE
    for update in find_nodes(ast, "UPDATE"):
        impacts.append(TableImpact("update", update.table))

    # Detect SELECT FROM
    for select in find_nodes(ast, "SELECT"):
        for table in select.from_tables:
            impacts.append(TableImpact("read", table))

    return impacts
```

**Testing**:
```bash
uv run pytest tests/unit/parsers/plpgsql/test_function_analyzer.py::TestTableImpact -v
```

**Success Criteria**:
- [ ] Detects INSERT impacts
- [ ] Detects UPDATE impacts
- [ ] Detects SELECT impacts (reads)
- [ ] Detects DELETE impacts
- [ ] Tests pass with complex functions

---

### Critical TODO #5: DELETE Statement Parsing
**File**: `src/parsers/plpgsql/function_analyzer.py`
**Line**: ~214
**Current Issue**: DELETE statements not parsed correctly
**Impact**: Reverse engineering misses delete operations

**Fix Strategy**:
```python
def parse_delete_statement(node):
    return DeleteAction(
        table=node.relation.relname,
        where_clause=parse_where(node.whereClause),
        returning=parse_returning(node.returningList) if node.returningList else None
    )
```

**Testing**:
```bash
uv run pytest tests/unit/parsers/plpgsql/test_function_analyzer.py::TestDeleteParsing -v
```

**Success Criteria**:
- [ ] DELETE statements parsed
- [ ] WHERE clause captured
- [ ] RETURNING clause supported
- [ ] Tests pass

---

### Critical TODO #6: Convert Impact Dict to ActionImpact
**File**: `src/cli/generate.py`
**Line**: ~48
**Current Issue**: Type inconsistency between dict and ActionImpact object
**Impact**: CLI crashes when displaying impact metadata

**Fix Strategy**:
```python
# Current (broken):
impact = {"table": "users", "type": "insert"}  # dict

# Target (fixed):
from src.domain.models import ActionImpact
impact = ActionImpact(
    table_name="users",
    impact_type="insert",
    schema="public"
)
```

**Testing**:
```bash
uv run pytest tests/unit/cli/test_generate.py::TestImpactDisplay -v
```

**Success Criteria**:
- [ ] Impact metadata uses ActionImpact objects
- [ ] CLI displays impacts correctly
- [ ] Type checking passes (mypy)
- [ ] Tests pass

---

### Critical TODO #7: Remove Hardcoded API Key
**File**: `src/cicd/llm_recommendations.py`
**Line**: ~35
**Current Issue**: Placeholder API key in code
**Impact**: Security risk if committed with real key

**Fix Strategy**:
```python
# Current (WRONG):
api_key = "sk-placeholder-key-here"  # TODO: Remove before release

# Target (FIXED):
import os
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable required for LLM recommendations. "
        "Set it or disable LLM features."
    )
```

**Testing**:
```bash
# Test with env var
OPENAI_API_KEY=test uv run pytest tests/unit/cicd/test_llm_recommendations.py -v

# Test without env var (should raise)
uv run pytest tests/unit/cicd/test_llm_recommendations.py::TestMissingKey -v
```

**Success Criteria**:
- [ ] No hardcoded API keys in code
- [ ] Uses environment variable
- [ ] Clear error if env var missing
- [ ] Tests pass
- [ ] Security scan clean (bandit)

---

### Critical TODO #8: General Critical Scan
```bash
# Scan for any other critical issues
git grep -n "TODO.*CRITICAL\|FIXME.*URGENT\|XXX.*BLOCKER" src/

# Review and fix any additional critical items found
```

**Success Criteria**:
- [ ] All CRITICAL/URGENT/BLOCKER TODOs addressed
- [ ] No critical issues remaining in src/

---

## 🎯 Phase 2: Create GitHub Issues for Important TODOs (3-4 hours)

**Strategy**: Convert 85 important (but non-blocking) TODOs into GitHub issues, then update code with issue references.

### Task 2.1: Set Up Issue Creation Script

Create `scripts/create_todo_issues.sh`:

```bash
#!/bin/bash
# Batch create GitHub issues for TODO comments

# Function to create issue and return issue number
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"

    gh issue create \
        --title "$title" \
        --body "$body" \
        --label "$labels" \
        --json number \
        --jq '.number'
}

# Example: Action/Step Compilation Enhancements (15 items)
echo "Creating issues for action compilation enhancements..."

# TODO from step_compilers/json_build_step.py:42
ISSUE_NUM=$(create_issue \
    "Enhancement: Support nested JSON_BUILD_OBJECT in step compiler" \
    "**Location**: \`src/generators/actions/step_compilers/json_build_step.py:42\`

**Current TODO**:
\`\`\`python
# TODO: Support nested JSON_BUILD_OBJECT for complex structures
\`\`\`

**Description**:
Currently only supports flat JSON objects. Need to support nested structures like:
\`\`\`sql
JSON_BUILD_OBJECT(
    'user', JSON_BUILD_OBJECT('name', name, 'email', email),
    'address', JSON_BUILD_OBJECT('city', city, 'zip', zip)
)
\`\`\`

**Priority**: Medium
**Component**: Code Generation - PostgreSQL
**Milestone**: Post-Alpha" \
    "enhancement,post-alpha,code-generation")

echo "Created issue #$ISSUE_NUM for nested JSON_BUILD_OBJECT"

# ... repeat for other TODOs ...
```

### Task 2.2: Categorize TODOs by Component

Based on ALPHA_RELEASE_TODO_CLEANUP_PLAN.md, create issues for these categories:

#### A. Action/Step Compilation (15 issues)
- Nested JSON_BUILD_OBJECT support
- CTE optimization
- Subquery performance
- Switch statement fallthrough
- Aggregate edge cases
- ... (see cleanup plan for full list)

#### B. Java/Spring Boot Generation (8 issues)
- Lombok builder customization
- JPA cascade type inference
- Repository custom query support
- Service layer transaction handling
- ... (see cleanup plan)

#### C. Rust/Diesel Generation (5 issues)
- Diesel migration generation
- Actix-web middleware integration
- Error handling patterns
- Async/await support
- ... (see cleanup plan)

#### D. TypeScript/Prisma Generation (3 issues)
- Prisma relation field naming
- TypeScript strict mode compatibility
- Zod schema generation
- ... (see cleanup plan)

#### E. Parser Improvements (10 issues)
- PL/pgSQL RECORD type handling
- Spring Boot annotation parsing
- Rust macro expansion
- ... (see cleanup plan)

#### F. CLI Enhancements (12 issues)
- Interactive mode improvements
- Progress bar for large projects
- Colored output configuration
- ... (see cleanup plan)

#### G. CI/CD Pipeline Generation (8 issues)
- Jenkins pipeline support
- Azure DevOps integration
- GitHub Actions matrix builds
- ... (see cleanup plan)

#### H. Infrastructure & Performance (8 issues)
- Pulumi TypeScript generation
- Terraform module composition
- Pattern library indexing
- ... (see cleanup plan)

#### I. Testing & Integration (8 issues)
- pgTAP assertion library
- pytest fixture generation
- Integration test templates
- ... (see cleanup plan)

### Task 2.3: Update Code with Issue References

After creating issues, update TODO comments:

```python
# Before:
# TODO: Support nested JSON_BUILD_OBJECT for complex structures

# After:
# TODO(#42): Support nested JSON_BUILD_OBJECT (post-alpha enhancement)
# See issue #42 for details and discussion
```

**Automation Script** (`scripts/update_todo_references.sh`):
```bash
#!/bin/bash
# Update TODO comments with issue numbers

# Example: Update specific TODO with issue number
update_todo() {
    local file="$1"
    local line="$2"
    local issue_num="$3"
    local old_comment="$4"
    local new_comment="$5"

    sed -i "${line}s|${old_comment}|${new_comment} (post-alpha) - See issue #${issue_num}|" "$file"
}

# Usage:
# update_todo "src/file.py" 42 123 "TODO: Old text" "TODO(#123): Old text"
```

### Task 2.4: Verify Issue Creation

```bash
# List all created issues
gh issue list --label "post-alpha" --limit 100

# Verify count
gh issue list --label "post-alpha" --json number | jq 'length'
# Expected: ~85 issues

# Check issue quality (sample review)
gh issue view 42
gh issue view 50
gh issue view 75
```

**Success Criteria**:
- [ ] ~85 GitHub issues created
- [ ] Each issue has clear title and description
- [ ] Issues labeled appropriately (enhancement, post-alpha, component)
- [ ] TODO comments updated with issue references
- [ ] Verification complete

---

## 🎯 Phase 3: Remove Outdated TODOs (1-2 hours)

**Target**: Remove 25 outdated TODO/debug comments

### Task 3.1: Remove Debug Print Statements

```bash
# Find debug print statements (18 items identified)
git grep -n "print(.*#.*debug\|print(.*DEBUG\|# DEBUG:" src/

# Review each and remove if in production code
# Example:
# Before:
print(f"DEBUG: Processing entity {entity.name}")  # TODO: Remove

# After:
# (removed entirely, or use proper logging)
```

**Replacement Pattern** (if logging needed):
```python
# Before:
print(f"DEBUG: Processing entity {entity.name}")

# After:
logger.debug("Processing entity: %s", entity.name)
```

### Task 3.2: Remove Obsolete TODOs

```bash
# Find TODOs mentioning completed features
git grep -n "TODO.*already implemented\|TODO.*done\|TODO.*completed\|TODO.*fixed" src/

# Review and remove these comments
```

**Example**:
```python
# Before:
# TODO: Add Trinity pattern support - already implemented in v0.3.0
def generate_table(entity):
    ...

# After:
def generate_table(entity):
    """Generate table with Trinity pattern (pk_*, id, identifier)."""
    ...
```

### Task 3.3: Clean Up Commented-Out Code

```bash
# Find large blocks of commented code
git grep -n "# def.*\|# class.*\|#.*DEPRECATED" src/ | head -50

# Review and remove dead code
# Exception: Keep if it's valuable reference for alternative approach
```

### Task 3.4: Commit Cleanup

```bash
git add -A
git commit -m "chore: remove outdated TODO comments and debug statements

- Remove 18 debug print statements from production code
- Remove 7 obsolete TODO comments for completed features
- Clean up commented-out deprecated code
- Improves code clarity for alpha release"
```

**Success Criteria**:
- [ ] All debug print statements removed/replaced
- [ ] Obsolete TODOs removed
- [ ] Dead code cleaned up
- [ ] Changes committed
- [ ] Tests still pass

---

## 🎯 Phase 4: Clarify Deferred TODOs (1 hour)

**Target**: Update 13 deferred TODOs with clear post-alpha marking

### Task 4.1: Update Deferred TODO Format

**Standard Format**:
```python
# FUTURE(#123): Brief description of future enhancement (post-alpha)
# Context: Why this is deferred and what it would enable
# See issue #123 for detailed discussion
```

**Example**:
```python
# Before:
# TODO: Add caching layer for better performance

# After:
# FUTURE(#67): Add Redis caching layer for pattern library queries (post-alpha)
# Context: Would improve search performance 10x for large pattern sets
# See issue #67 for implementation approach and benchmarks
```

### Task 4.2: Update Deferred TODOs

Update these 13 identified deferred TODOs:
1. Pattern library caching (#67)
2. Incremental code generation (#68)
3. Parallel compilation (#69)
4. Hot reload for dev server (#70)
5. Plugin architecture (#71)
6. Custom type mappers (#72)
7. Schema migration diffing (#73)
8. Multi-tenant code generation (#74)
9. GraphQL federation support (#75)
10. Real-time preview (#76)
11. Cloud deployment automation (#77)
12. A/B testing support (#78)
13. Monitoring integration (#79)

### Task 4.3: Commit Clarifications

```bash
git add -A
git commit -m "chore: clarify deferred TODOs with issue references

- Update 13 deferred TODOs to FUTURE(#N) format
- Add context for why each is post-alpha
- Link to GitHub issues for detailed discussion
- Improves clarity on roadmap priorities"
```

**Success Criteria**:
- [ ] All 13 deferred TODOs updated
- [ ] Each has issue reference
- [ ] Clear post-alpha marking
- [ ] Changes committed

---

## 🎯 Phase 5: Final TODO Audit (1 hour)

### Task 5.1: Count Remaining TODOs

```bash
# Count TODO/FIXME comments
git grep -c "TODO\|FIXME\|XXX\|HACK" | wc -l

# Target: <50 files (down from 117)

# Count total lines
git grep "TODO\|FIXME\|XXX\|HACK" | wc -l

# Target: <100 lines (down from 393)
```

### Task 5.2: Categorize Remaining TODOs

```bash
# Critical (should be 0)
git grep -n "TODO.*CRITICAL\|FIXME.*URGENT" src/

# Important with issue refs (should have #N)
git grep -n "TODO(#\|FUTURE(#" src/ | wc -l

# Deferred without issues (investigate)
git grep -n "TODO\|FIXME" src/ | grep -v "TODO(#\|FUTURE(#"
```

### Task 5.3: Document Final State

Create `TODO_CLEANUP_RESULTS.md`:

```markdown
# TODO Cleanup Results - Week 19

**Date Completed**: 2025-11-29
**Starting State**: 393 TODO lines across 117 files
**Final State**: X TODO lines across Y files

## Changes Made

### Critical TODOs Fixed (8 items)
- ✅ Multiple actions per entity support
- ✅ Schema lookup for table names
- ✅ Cross-schema impact tracking
- ✅ Table impact analysis in PL/pgSQL
- ✅ DELETE statement parsing
- ✅ Impact dict to ActionImpact conversion
- ✅ Hardcoded API key removed
- ✅ Additional critical items addressed

### GitHub Issues Created (85 items)
- Created issues #42-#126 for post-alpha enhancements
- All important TODOs now have issue references
- Labeled appropriately by component and priority

### Outdated Comments Removed (25 items)
- Removed 18 debug print statements
- Removed 7 obsolete TODO comments
- Cleaned up deprecated code blocks

### Deferred TODOs Clarified (13 items)
- Updated to FUTURE(#N) format
- Added context and issue references
- Clear post-alpha marking

## Final TODO Breakdown

- Critical TODOs: 0 (down from 8) ✅
- Important TODOs with issues: ~85 (all tracked)
- Deferred TODOs: ~13 (all clarified)
- Remaining valid TODOs: ~X

## Quality Metrics

- Test coverage maintained: 96%+
- All tests passing: ✅
- Code quality checks passing: ✅
- Security scan clean: ✅

## Conclusion

Codebase is clean and ready for alpha release. All blocking TODOs resolved,
all important enhancements tracked in GitHub issues, and all remaining TODOs
properly documented and justified.
```

### Task 5.4: Final Quality Checks

```bash
# Run full test suite
uv run pytest --tb=short

# Run code quality
uv run ruff check src/ tests/
uv run mypy src/

# Security scan
uv run bandit -r src/ -ll

# All should pass ✅
```

**Success Criteria**:
- [ ] Remaining TODOs < 100 lines
- [ ] No critical TODOs remain
- [ ] All important TODOs have issue refs
- [ ] Cleanup results documented
- [ ] All quality checks pass

---

## 📊 Week 19 Success Criteria

### Critical TODO Fixes
- [ ] All 8 critical TODOs fixed
- [ ] Tests pass for all fixes
- [ ] No critical issues remaining

### GitHub Issues
- [ ] ~85 issues created for enhancements
- [ ] All issues properly labeled
- [ ] Code updated with issue references

### Code Cleanup
- [ ] 25 outdated TODOs removed
- [ ] Debug statements removed
- [ ] Dead code cleaned up

### Deferred TODOs
- [ ] 13 deferred TODOs clarified
- [ ] FUTURE(#N) format used
- [ ] Issue references added

### Quality
- [ ] Tests pass (pytest)
- [ ] Code quality passes (ruff, mypy)
- [ ] Security scan clean (bandit)
- [ ] Coverage maintained (96%+)

### Documentation
- [ ] TODO_CLEANUP_RESULTS.md created
- [ ] All changes committed
- [ ] Clean working directory

---

## 📝 Deliverables

1. **Fixed critical code** (8 TODO fixes with tests)
2. **GitHub issues** (~85 enhancement issues)
3. **Clean codebase** (25 outdated TODOs removed)
4. **Clarified TODOs** (13 deferred with issue refs)
5. **TODO_CLEANUP_RESULTS.md** (final state documentation)
6. **Git commits** (organized by category)

---

## ⏭️ Next Week Preview

**Week 20**: Git Tag, Repository Public, Community Setup
- Create v0.4.0-alpha git tag
- Make repository public
- Configure repository settings (topics, issues)
- Create community welcome issues
- Post-release verification
- Estimated time: 2-3 hours

---

## 🚨 Blockers & Risks

### Potential Blockers
1. **Critical TODO fixes break tests** - Must fix properly
2. **GitHub API rate limits** - May need to batch issue creation
3. **Merge conflicts** - Keep commits small and focused

### Risk Mitigation
- Test after each critical fix
- Use GitHub CLI with authentication
- Commit frequently in logical groups
- Create issues in batches of 20-30

---

## 📞 Questions & Clarifications

For detailed TODO categorization, see:
- ALPHA_RELEASE_TODO_CLEANUP_PLAN.md (complete breakdown)
- ALPHA_RELEASE_CHECKLIST.md (high-level overview)

If stuck on a critical TODO fix:
1. Review the file context and dependencies
2. Check existing tests for similar patterns
3. Run tests frequently during development
4. Ask for help if uncertain about approach

---

**Week 19 Status**: 🟡 Ready to Start (pending Week 18 completion)
**Next Action**: Fix critical TODO #1 (Multiple actions per entity)
**Estimated Completion**: 2025-11-29
