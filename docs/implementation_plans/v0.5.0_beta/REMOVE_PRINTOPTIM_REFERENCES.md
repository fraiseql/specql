# Remove PrintOptim References - Implementation Plan

**Document Version**: 1.0
**Created**: 2025-11-16
**Security Level**: CRITICAL - Prevents proprietary information leak
**Status**: Ready for execution
**Complexity**: Medium | Systematic cleanup with verification

---

## Executive Summary

This plan systematically removes all 349 occurrences of "PrintOptim" across 154 files in the SpecQL codebase before public release. PrintOptim is a proprietary production SaaS application that should not be publicly disclosed.

**Current Status**:
- ❌ 349 PrintOptim references found
- ❌ 154 files containing references
- ❌ 4 directories with PrintOptim in path
- ❌ Public marketing materials mention PrintOptim

**Expected Outcomes**:
- 0 PrintOptim references in codebase
- All proprietary information removed
- Generic "production reference" terminology used
- Safe for public GitHub repository
- Safe for PyPI publication

**Security Level**: CRITICAL - This must be completed before:
1. Publishing v0.5.0-beta to PyPI
2. Making repository public
3. Any marketing/social media posts

---

## Audit Summary

### References Found

| Category | Files | Occurrences | Risk Level |
|----------|-------|-------------|------------|
| **Directories** | 4 dirs | N/A | High - Visible in GitHub |
| **Stdlib YAML** | 36 files | 36 | Low - Metadata comments |
| **Documentation** | 15 files | ~100 | High - Public-facing |
| **Implementation Plans** | 13 files | ~2,000 lines | Medium - Planning docs |
| **Test Files** | 8 files | 26 | Low - Internal |
| **Templates** | 3 files | 4 | Low - Comments only |
| **Source Code** | 2 files | 2 | Low - Docstrings |
| **Examples** | 2 files | 4 | Medium - Examples visible |
| **user_journey_test/** | 156 files | 156 | High - Duplicate tree |
| **Total** | **154 files** | **349** | **CRITICAL** |

---

## PHASE 1: Delete Directories (Zero Risk)

**Objective**: Remove empty and backup directories containing PrintOptim references

**Estimated Time**: 5 minutes

### Directory 1: Empty Entities Directory

**Path**: `/home/lionel/code/specql/entities/printoptim/`

**Status**: Empty subdirectories (catalog/, common/, management/, tenant/)

**Size**: 20KB (directory structure only)

**Risk**: Zero - Directory is empty

#### Steps

**1. Verify directory is empty**
```bash
cd /home/lionel/code/specql
find entities/printoptim/ -type f
```

**Expected**: No output (no files)

**2. Delete directory**
```bash
rm -rf entities/printoptim/
```

**3. Verify deletion**
```bash
ls entities/printoptim 2>&1
```

**Expected**: "No such file or directory"

**Success Criteria**:
- [ ] Directory deleted
- [ ] No files lost (directory was empty)
- [ ] `git status` shows deletion

---

### Directory 2: Migration Working Directory

**Path**: `/home/lionel/code/specql/printoptim_migration/`

**Status**: 25 subdirectories, 1 file (analysis/state_minus_1/STRUCTURE.txt)

**Size**: 128KB

**Risk**: Low - Working directory with legacy analysis

#### Steps

**1. Check contents**
```bash
find printoptim_migration/ -type f
```

**Expected**: Only `analysis/state_minus_1/STRUCTURE.txt`

**2. Archive if needed** (optional)
```bash
# If you want to keep a backup outside repo
mkdir -p ~/archives/specql_cleanup_$(date +%Y%m%d)/
mv printoptim_migration/ ~/archives/specql_cleanup_$(date +%Y%m%d)/
```

**3. Delete from repository**
```bash
rm -rf printoptim_migration/
```

**4. Verify deletion**
```bash
ls printoptim_migration 2>&1
```

**Expected**: "No such file or directory"

**Success Criteria**:
- [ ] Directory removed from SpecQL repo
- [ ] Optional archive created (if desired)
- [ ] `git status` shows deletion

---

### Directory 3: Backup Internal

**Path**: `/home/lionel/code/specql/backup_internal/`

**Status**: 17MB of historical documentation

**Size**: 17MB (6,462 lines of markdown)

**Risk**: Medium - Contains detailed migration plans

**Files**:
- `PRINTOPTIM_MIGRATION_DETAILED_PLAN.md`
- `PRINTOPTIM_MIGRATION_AGENT_PLAN.md`
- `PRINTOPTIM_MIGRATION_AGENT_PROMPT.md`
- `PRINTOPTIM_REVERSE_ENGINEERING_AGENT_PROMPT.md`
- `docs/migration/printoptim_to_specql.md`
- `docs/migration/printoptim_to_patterns.md`

#### Steps

**1. Review contents**
```bash
ls -lh backup_internal/
du -sh backup_internal/
```

**2. Archive outside repository** (RECOMMENDED)
```bash
# Create archive directory
mkdir -p ~/private_archives/specql_backups/

# Move entire backup_internal
mv backup_internal/ ~/private_archives/specql_backups/backup_internal_$(date +%Y%m%d)/
```

**Alternative: Delete if no longer needed**
```bash
rm -rf backup_internal/
```

**3. Verify removal from repo**
```bash
ls backup_internal 2>&1
```

**Expected**: "No such file or directory"

**Success Criteria**:
- [ ] backup_internal/ removed from SpecQL repo
- [ ] Archive created in ~/private_archives/ (recommended)
- [ ] No proprietary information in public repo

---

### Directory 4: Generated Site Documentation

**Path**: `/home/lionel/code/specql/site/migration/printoptim_to_specql/`

**Status**: Generated MkDocs HTML (22KB index.html)

**Risk**: High - Would be visible in published docs

#### Steps

**1. Check if directory exists**
```bash
ls -la site/migration/printoptim_to_specql/
```

**2. Delete directory**
```bash
rm -rf site/migration/printoptim_to_specql/
```

**3. Verify deletion**
```bash
ls site/migration/printoptim_to_specql 2>&1
```

**Expected**: "No such file or directory"

**Note**: This will be regenerated from source if migration docs still exist. We'll handle source docs in Phase 3.

**Success Criteria**:
- [ ] Generated docs removed
- [ ] Site will regenerate without PrintOptim after source cleanup

---

### Directory 5: user_journey_test (Duplicate Tree)

**Path**: `/home/lionel/code/specql/user_journey_test/`

**Status**: Complete duplicate of SpecQL codebase causing pytest conflicts

**Size**: Unknown (complete copy)

**Risk**: High - Duplicate references, causes test failures

#### Steps

**1. Check size and contents**
```bash
du -sh user_journey_test/
ls user_journey_test/
```

**2. Archive if needed**
```bash
# Only if directory has unique value
mv user_journey_test/ ~/archives/specql_cleanup_$(date +%Y%m%d)/
```

**3. Delete from repository** (RECOMMENDED)
```bash
rm -rf user_journey_test/
```

**4. Verify pytest collection works**
```bash
uv run pytest --collect-only 2>&1 | grep "ERROR collecting"
```

**Expected**: No output (no collection errors)

**Success Criteria**:
- [ ] user_journey_test/ removed
- [ ] pytest collection works without errors
- [ ] No duplicate conftest.py conflicts

---

### Phase 1 Verification

**Run after all directory deletions**:

```bash
# Check git status
git status

# Expected deleted directories:
# deleted:    entities/printoptim/
# deleted:    printoptim_migration/
# deleted:    backup_internal/
# deleted:    site/migration/printoptim_to_specql/
# deleted:    user_journey_test/

# Count remaining references
grep -ri "printoptim" . --exclude-dir=.git --exclude-dir=node_modules \
  --exclude-dir=__pycache__ | wc -l

# Expected: Significantly fewer than 349 (directories removed)
```

**Phase 1 Success Criteria**:
- [ ] All 5 directories deleted
- [ ] Backups archived in ~/private_archives/ or ~/archives/
- [ ] Git status shows deletions
- [ ] pytest collection works
- [ ] Reference count reduced

---

## PHASE 2: Global Find/Replace (Low Risk)

**Objective**: Automated replacement of PrintOptim references in comments and metadata

**Estimated Time**: 10 minutes

### Replace 1: Stdlib YAML Files (36 files)

**Pattern Found**:
```yaml
# PrintOptim production system and generalized for universal reuse.
# PrintOptim pattern
```

**Files Affected**: All stdlib YAML files
- `stdlib/tech/*.yaml` (4 files)
- `stdlib/commerce/*.yaml` (6 files)
- `stdlib/time/*.yaml` (1 file)
- `stdlib/org/*.yaml` (2 files)
- `stdlib/crm/*.yaml` (3 files)
- `stdlib/i18n/*.yaml` (7 files)
- `stdlib/geo/*.yaml` (13 files)
- `stdlib/common/*.yaml` (2 files)

#### Steps

**1. Preview changes**
```bash
cd /home/lionel/code/specql

# Show all lines that will change
grep -r "PrintOptim" stdlib/ --include="*.yaml"
```

**2. Execute replacement**
```bash
# Replace "PrintOptim production system" → "production reference implementation"
find stdlib/ -name "*.yaml" -type f -exec sed -i \
  's/PrintOptim production system/production reference implementation/g' {} \;

# Replace remaining "PrintOptim" → "Reference Application"
find stdlib/ -name "*.yaml" -type f -exec sed -i \
  's/PrintOptim/Reference Application/g' {} \;
```

**3. Verify changes**
```bash
# Check no PrintOptim references remain in stdlib
grep -r "PrintOptim" stdlib/ --include="*.yaml"
```

**Expected**: No output (all references replaced)

**4. Spot check files**
```bash
# Check a few files manually
head -20 stdlib/tech/allocation.yaml
head -20 stdlib/commerce/contract.yaml
head -20 stdlib/i18n/language.yaml
```

**Expected**: Comments now say "production reference implementation" or "Reference Application"

**Success Criteria**:
- [ ] 36 stdlib files updated
- [ ] Zero PrintOptim references in stdlib/
- [ ] YAML files still valid (no syntax errors)
- [ ] Metadata updated to generic terms

---

### Replace 2: Template Comments (3 files)

**Pattern Found**:
```sql
-- Based on printoptim_backend implementation
-- Based on printoptim_backend pattern
```

**Files Affected**:
- `templates/sql/utilities/safe_slug.sql.jinja2`
- `templates/sql/hierarchy/recalculate_tree_path.sql.jinja2`
- `templates/sql/000_types.sql.jinja2`

#### Steps

**1. Preview changes**
```bash
grep -n "printoptim" templates/sql/ -ri --include="*.jinja2"
```

**2. Execute replacement**
```bash
# Case-insensitive replacement
find templates/sql/ -name "*.jinja2" -type f -exec sed -i \
  's/printoptim_backend/production reference/gi' {} \;
```

**3. Verify changes**
```bash
grep -n "printoptim" templates/sql/ -ri --include="*.jinja2"
```

**Expected**: No output

**4. Verify template syntax**
```bash
# Check files still render properly
cat templates/sql/utilities/safe_slug.sql.jinja2 | head -10
cat templates/sql/hierarchy/recalculate_tree_path.sql.jinja2 | head -10
cat templates/sql/000_types.sql.jinja2 | head -10
```

**Expected**: Comments updated, template syntax intact

**Success Criteria**:
- [ ] 3 template files updated
- [ ] Comments now reference "production reference"
- [ ] Template syntax valid
- [ ] No PrintOptim references in templates/

---

### Replace 3: Example Files (2 files)

**Pattern Found**:
```yaml
# (PrintOptim pattern)
# PrintOptim pattern for wildcard evolution
```

**Files Affected**:
- `entities/examples/invoice_wildcard_pattern.yaml`
- `entities/examples/contract_cross_schema.yaml`

#### Steps

**1. Preview changes**
```bash
grep -n "PrintOptim" entities/examples/*.yaml
```

**2. Execute replacement**
```bash
find entities/examples/ -name "*.yaml" -type f -exec sed -i \
  's/PrintOptim pattern/Production pattern/gi' {} \;

find entities/examples/ -name "*.yaml" -type f -exec sed -i \
  's/PrintOptim/Reference Application/gi' {} \;
```

**3. Verify changes**
```bash
grep -n "PrintOptim" entities/examples/ -i
```

**Expected**: No output

**4. Verify YAML syntax**
```bash
python -c "import yaml; yaml.safe_load(open('entities/examples/invoice_wildcard_pattern.yaml'))"
python -c "import yaml; yaml.safe_load(open('entities/examples/contract_cross_schema.yaml'))"
```

**Expected**: No syntax errors

**Success Criteria**:
- [ ] 2 example files updated
- [ ] Comments now reference "Production pattern"
- [ ] YAML syntax valid
- [ ] Examples still demonstrate intended features

---

### Phase 2 Verification

```bash
# Count references after automated replacements
grep -ri "printoptim" . --exclude-dir=.git --exclude-dir=node_modules \
  --exclude-dir=__pycache__ --exclude-dir=site | wc -l

# Expected: Much fewer (stdlib, templates, examples cleaned)

# Check specific directories
grep -r "printoptim" stdlib/ -i
grep -r "printoptim" templates/ -i
grep -r "printoptim" entities/examples/ -i

# Expected: All should return no output
```

**Phase 2 Success Criteria**:
- [ ] Stdlib cleaned (36 files)
- [ ] Templates cleaned (3 files)
- [ ] Examples cleaned (2 files)
- [ ] All YAML/SQL syntax valid
- [ ] Generic terminology used

---

## PHASE 3: Documentation Updates (Medium Risk)

**Objective**: Remove or update PrintOptim references in public-facing documentation

**Estimated Time**: 1-2 hours

### Doc Update 1: Marketing Content (HIGH PRIORITY)

**Risk**: HIGH - Public-facing marketing materials

#### File: docs/marketing/SOCIAL_MEDIA_CONTENT.md

**References** (3 occurrences):
- Line 274: LinkedIn post mentions "PrintOptim (production SaaS)"
- Context: Example social media content

**Changes Required**:

```bash
cd /home/lionel/code/specql
```

**Edit the file**:
```markdown
# BEFORE (Line 274):
I'm using SpecQL to migrate PrintOptim (production SaaS)...

# AFTER:
I'm using SpecQL to migrate a production SaaS application...
```

**Script**:
```bash
sed -i 's/PrintOptim (production SaaS)/a production SaaS application/g' \
  docs/marketing/SOCIAL_MEDIA_CONTENT.md
```

**Verify**:
```bash
grep -n "PrintOptim" docs/marketing/SOCIAL_MEDIA_CONTENT.md -i
```

**Expected**: No output

---

#### File: docs/marketing/SHOW_HN_CONTENT.md

**References** (2 occurrences):
- Line 311: "Yes! It's used in production at PrintOptim (SaaS app)."
- Line 356: "Share real-world use case from PrintOptim"

**Changes Required**:

```bash
# Line 311
sed -i 's/at PrintOptim (SaaS app)/in a production SaaS application/g' \
  docs/marketing/SHOW_HN_CONTENT.md

# Line 356
sed -i 's/from PrintOptim/from our reference implementation/g' \
  docs/marketing/SHOW_HN_CONTENT.md
```

**Verify**:
```bash
grep -n "PrintOptim" docs/marketing/SHOW_HN_CONTENT.md -i
```

**Expected**: No output

**Success Criteria**:
- [ ] SOCIAL_MEDIA_CONTENT.md cleaned
- [ ] SHOW_HN_CONTENT.md cleaned
- [ ] Marketing materials safe for public release
- [ ] No proprietary application names disclosed

---

### Doc Update 2: Implementation Plans (CONSIDER DELETION)

**Risk**: MEDIUM - Planning documents, may contain detailed proprietary info

**Files Affected** (13 files):
1. `docs/implementation_plans/PRINTOPTIM_SPECQL_MIGRATION_COMPREHENSIVE_PLAN.md` (1,986 lines)
2. `docs/implementation_plans/v0.5.0_beta/SPECQL_V050_BETA_RELEASE_BLOCKERS.md`
3. `docs/implementation_plans/v0.5.0_beta/README.md`
4. `docs/implementation_plans/v0.5.0_beta/WEEK_04_EXTENDED.md`
5. `docs/implementation_plans/v0.5.0_beta/WEEK_01_EXTENDED_2.md`
6. `docs/implementation_plans/v0.5.0_beta/WEEK_05_MARKETING_CONTENT.md`
7. `docs/implementation_plans/v0.5.0_beta/WEEK_01_EXTENDED.md`
8. `docs/implementation_plans/plpgsql_enhancement/WEEK_PLPGSQL_03_04_INTEGRATION_TESTS.md`
9. `docs/implementation_plans/plpgsql_enhancement/README.md`
10. `docs/implementation_plans/plpgsql_enhancement/PLPGSQL_MATURITY_ASSESSMENT.md`
11. `docs/implementation_plans/plpgsql_enhancement/WEEK_PLPGSQL_07_DOCUMENTATION.md`
12. `docs/08_troubleshooting/FAQ.md`

#### Strategy A: Delete Migration Plan (RECOMMENDED)

**Rationale**: The comprehensive migration plan is a working document, not needed for public release

```bash
# Delete the main migration plan
rm docs/implementation_plans/PRINTOPTIM_SPECQL_MIGRATION_COMPREHENSIVE_PLAN.md

# Update git
git add docs/implementation_plans/PRINTOPTIM_SPECQL_MIGRATION_COMPREHENSIVE_PLAN.md
```

#### Strategy B: Sanitize Migration Plan (Alternative)

**If you want to keep it as a generic example**:

```bash
# Global replace in the file
sed -i 's/PrintOptim/Reference Application/g' \
  docs/implementation_plans/PRINTOPTIM_SPECQL_MIGRATION_COMPREHENSIVE_PLAN.md

# Rename file
mv docs/implementation_plans/PRINTOPTIM_SPECQL_MIGRATION_COMPREHENSIVE_PLAN.md \
   docs/implementation_plans/REFERENCE_APP_MIGRATION_PLAN.md
```

#### Update Other Implementation Plans

**For the remaining 12 files** (1 occurrence each):

**Option 1: Global replace**
```bash
# Replace PrintOptim in all implementation plan files
find docs/implementation_plans/ -name "*.md" -type f -exec sed -i \
  's/PrintOptim/Reference Application/g' {} \;

# Also update FAQ
sed -i 's/PrintOptim/Reference Application/g' \
  docs/08_troubleshooting/FAQ.md
```

**Option 2: Manual review and edit**
```bash
# List all files with references
grep -l "PrintOptim" docs/implementation_plans/**/*.md -i
grep -l "PrintOptim" docs/08_troubleshooting/*.md -i

# Review each one
for file in $(grep -l "PrintOptim" docs/**/*.md -i); do
    echo "=== $file ==="
    grep -n "PrintOptim" "$file" -i
    echo ""
done
```

#### Verification

```bash
# Check no PrintOptim in docs
grep -r "PrintOptim" docs/ -i --include="*.md"

# Expected: No output (or only in files you chose to keep)
```

**Success Criteria**:
- [ ] Main migration plan removed OR sanitized
- [ ] All implementation plans cleaned
- [ ] FAQ updated
- [ ] No proprietary information in docs/

---

### Doc Update 3: Migration Documentation Source

**Files** (if not already deleted in backup_internal):
- Check if any migration docs remain in `docs/migration/` or `docs/guides/`

```bash
# Search for migration docs
find docs/ -name "*migration*.md" -o -name "*printoptim*.md"

# Check each one
grep -l "PrintOptim" docs/**/*.md -i
```

**Action**: Remove or update any remaining migration documentation

**Success Criteria**:
- [ ] No migration docs reference PrintOptim
- [ ] Source files cleaned (not just generated site/)

---

### Phase 3 Verification

```bash
# Comprehensive documentation check
grep -r "printoptim" docs/ -i --include="*.md" | wc -l

# Expected: 0

# Check marketing specifically
grep -r "printoptim" docs/marketing/ -i

# Expected: No output

# Check implementation plans
grep -r "printoptim" docs/implementation_plans/ -i

# Expected: No output (or only in files you chose to keep)
```

**Phase 3 Success Criteria**:
- [ ] Marketing content cleaned
- [ ] Show HN content safe
- [ ] Implementation plans cleaned or deleted
- [ ] No proprietary app names in public docs
- [ ] Migration docs removed

---

## PHASE 4: Test File Updates (Low Risk)

**Objective**: Update test files that reference PrintOptim (mostly comments and class names)

**Estimated Time**: 30 minutes

### Test Update 1: Unit Tests (5 files)

#### File: tests/unit/numbering/test_numbering_parser.py

**Reference**: Line comment "Test case from PrintOptim: ColorMode entity"

**Fix**:
```bash
sed -i 's/from PrintOptim/from production reference/g' \
  tests/unit/numbering/test_numbering_parser.py
```

---

#### File: tests/unit/schema/test_wildcard_generation.py

**References**: Class name `TestWildcardPrintOptimPattern` (4 occurrences)

**Fix**:
```bash
sed -i 's/PrintOptim/Production/g' \
  tests/unit/schema/test_wildcard_generation.py
```

**Verify**: Class renamed to `TestWildcardProductionPattern`

---

#### File: tests/unit/core/test_table_views_wildcard.py

**References**: Class name `TestWildcardPrintOptimPattern` (4 occurrences)

**Fix**:
```bash
sed -i 's/PrintOptim/Production/g' \
  tests/unit/core/test_table_views_wildcard.py
```

---

#### File: tests/unit/registry/test_naming_conventions.py

**Reference**: Comment about PrintOptim migration

**Fix**:
```bash
sed -i 's/PrintOptim/Reference Application/g' \
  tests/unit/registry/test_naming_conventions.py
```

---

#### File: tests/unit/patterns/aggregation/test_boolean_flags.py

**Reference**: Comment "9-flag PrintOptim example"

**Fix**:
```bash
sed -i 's/PrintOptim/production/g' \
  tests/unit/patterns/aggregation/test_boolean_flags.py
```

---

### Test Update 2: Integration Tests (3 files)

#### File: tests/integration/test_hex_hierarchical_generation.py

**Reference**: 1 occurrence

**Fix**:
```bash
sed -i 's/PrintOptim/Reference Application/g' \
  tests/integration/test_hex_hierarchical_generation.py
```

---

#### File: tests/integration/test_issue_6_subdomain_parsing.py

**References**: 2 occurrences

**Fix**:
```bash
sed -i 's/PrintOptim/Reference Application/g' \
  tests/integration/test_issue_6_subdomain_parsing.py
```

---

#### File: tests/integration/test_cross_schema_composition.py.skip

**References**: 5 occurrences (test classes and methods)

**Note**: File is .skip (disabled)

**Fix**:
```bash
sed -i 's/PrintOptim/Production/g' \
  tests/integration/test_cross_schema_composition.py.skip
```

---

### Test Update 3: Documentation Tests (2 files)

#### File: tests/docs/test_migration_examples.py

**References**: 6 occurrences (test paths)

**Strategy**: Update or disable tests if migration docs are removed

**Fix**:
```bash
# If migration docs removed, skip these tests
sed -i '1i import pytest' tests/docs/test_migration_examples.py
sed -i 's/def test_/@pytest.mark.skip("Migration docs removed")\ndef test_/g' \
  tests/docs/test_migration_examples.py
```

**Alternative**: Update test to reference new docs

---

#### File: tests/docs/test_documentation_coverage.py

**References**: 2 occurrences

**Fix**:
```bash
sed -i 's/PrintOptim/Reference Application/g' \
  tests/docs/test_documentation_coverage.py
```

---

### Automated Batch Update (All Test Files)

**Global replace across all test files**:

```bash
# Replace in all test files
find tests/ -name "*.py" -type f -exec sed -i \
  's/PrintOptim/Production/g' {} \;

find tests/ -name "*.py" -type f -exec sed -i \
  's/printoptim/production/g' {} \;
```

**Verify**: Run test collection

```bash
uv run pytest --collect-only 2>&1 | grep -i "printoptim"
```

**Expected**: No output (no PrintOptim in test names or collection)

---

### Run Test Suite

**After all test updates**:

```bash
# Run all tests to ensure nothing broke
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v -k "not skip"

# Check for failures
uv run pytest --tb=short -q
```

**Success Criteria**:
- [ ] All test files updated
- [ ] Test classes renamed
- [ ] Comments updated
- [ ] Tests still pass (or skipped if docs removed)
- [ ] No PrintOptim in test collection output

---

## PHASE 5: Source Code Updates (Low Risk)

**Objective**: Update source code docstrings and comments

**Estimated Time**: 10 minutes

### Source Update 1: Migration Analyzer

**File**: `src/patterns/migration_analyzer.py`

**Reference**: Line 2 docstring

```python
# BEFORE:
"""Migration Analyzer for PrintOptim to SpecQL Patterns"""

# AFTER:
"""Migration Analyzer for existing codebases to SpecQL Patterns"""
```

**Fix**:
```bash
sed -i 's/PrintOptim to SpecQL/existing codebases to SpecQL/g' \
  src/patterns/migration_analyzer.py
```

---

### Source Update 2: Comparison Script

**File**: `scripts/dev/compare_with_original.py`

**References**:
- Line 3: Docstring
- Line 10: Path to `../printoptim_backend/`

**Decision**: DELETE or UPDATE

**Option A: Delete** (if script not needed)
```bash
rm scripts/dev/compare_with_original.py
```

**Option B: Update** (if script useful for other purposes)
```bash
sed -i 's/printoptim_backend/reference_implementation/g' \
  scripts/dev/compare_with_original.py

# Update path
sed -i 's|../printoptim_backend/|../reference_app/|g' \
  scripts/dev/compare_with_original.py
```

**Recommended**: Delete (script is dev-only and specific to PrintOptim)

---

### Verify Source Code Clean

```bash
# Check all Python source files
grep -r "printoptim" src/ -i --include="*.py"
grep -r "printoptim" scripts/ -i --include="*.py"

# Expected: No output
```

**Success Criteria**:
- [ ] migration_analyzer.py updated
- [ ] compare_with_original.py deleted or updated
- [ ] No PrintOptim in source code
- [ ] Code still runs correctly

---

## PHASE 6: Final Verification & Commit

**Objective**: Comprehensive verification that all PrintOptim references are removed

**Estimated Time**: 30 minutes

### Verification 1: Comprehensive Search

```bash
cd /home/lionel/code/specql

# Search ALL files (excluding git)
grep -ri "printoptim" . --exclude-dir=.git --exclude-dir=node_modules \
  --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=site \
  --exclude="*.pyc"

# Expected: NO OUTPUT (zero references)
```

**If any references remain**: Go back to appropriate phase and clean them

---

### Verification 2: Specific File Types

```bash
# Python files
grep -r "printoptim" . -i --include="*.py" --exclude-dir=.git

# YAML files
grep -r "printoptim" . -i --include="*.yaml" --exclude-dir=.git

# SQL files
grep -r "printoptim" . -i --include="*.sql" --exclude-dir=.git

# Markdown files
grep -r "printoptim" . -i --include="*.md" --exclude-dir=.git

# Jinja templates
grep -r "printoptim" . -i --include="*.jinja2" --exclude-dir=.git

# All expected: NO OUTPUT
```

---

### Verification 3: Directory Check

```bash
# Check deleted directories don't exist
ls entities/printoptim 2>&1 | grep "No such file"
ls printoptim_migration 2>&1 | grep "No such file"
ls backup_internal 2>&1 | grep "No such file"
ls user_journey_test 2>&1 | grep "No such file"
ls site/migration/printoptim_to_specql 2>&1 | grep "No such file"

# All expected: "No such file or directory"
```

---

### Verification 4: Test Suite

```bash
# Ensure tests still work
uv run pytest --collect-only 2>&1 | grep -i "error\|printoptim"

# Expected: No errors, no printoptim references

# Run quick test subset
uv run pytest tests/unit/cli/ -v
uv run pytest tests/unit/core/ -v

# Expected: All pass
```

---

### Verification 5: Git Status Review

```bash
git status

# Review all changes
git diff --stat

# Check specific files
git diff docs/marketing/SOCIAL_MEDIA_CONTENT.md
git diff stdlib/tech/allocation.yaml
git diff tests/unit/schema/test_wildcard_generation.py
```

**Expected changes**:
- Deleted: 5 directories
- Modified: ~60 files (comments, class names, metadata)
- No unexpected changes

---

### Verification 6: Documentation Build

**If using MkDocs or similar**:

```bash
# Rebuild documentation
mkdocs build

# Check for broken links
mkdocs build --strict

# Expected: No errors, no PrintOptim in generated site
```

---

### Verification 7: Package Build Test

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build package
uv build

# Check package contents don't include PrintOptim
tar -tzf dist/specql-generator-*.tar.gz | grep -i printoptim

# Expected: No output (no printoptim files in package)

# Check wheel
unzip -l dist/specql_generator-*.whl | grep -i printoptim

# Expected: No output
```

---

### Final Cleanup Checklist

**Before committing, verify**:

- [ ] **Search Results**: Zero occurrences of "printoptim" (case-insensitive)
- [ ] **Directories**: All 5 PrintOptim directories deleted
- [ ] **Stdlib**: 36 YAML files updated with generic terms
- [ ] **Templates**: 3 Jinja files updated
- [ ] **Examples**: 2 YAML files updated
- [ ] **Marketing**: SOCIAL_MEDIA_CONTENT.md and SHOW_HN_CONTENT.md cleaned
- [ ] **Docs**: Implementation plans deleted or sanitized
- [ ] **Tests**: 8 test files updated, all passing
- [ ] **Source**: 2 source files updated
- [ ] **Test Suite**: Runs without errors
- [ ] **Package Build**: Succeeds without PrintOptim references
- [ ] **Git Status**: Only expected changes
- [ ] **Private Archives**: Backups saved in ~/private_archives/ (if needed)

---

### Commit Changes

```bash
# Stage all changes
git add .

# Review staged changes
git status
git diff --cached --stat

# Create commit
git commit -m "security: remove all PrintOptim references from codebase

CRITICAL: Remove proprietary application references before public release

Changes:
- Deleted 5 directories (entities/printoptim, printoptim_migration,
  backup_internal, user_journey_test, site/migration/printoptim_to_specql)
- Updated 41 stdlib YAML files: replace PrintOptim → Reference Application
- Updated 3 template files: replace printoptim_backend → production reference
- Updated 2 example files: replace PrintOptim pattern → Production pattern
- Cleaned marketing content (SOCIAL_MEDIA_CONTENT.md, SHOW_HN_CONTENT.md)
- Removed/sanitized implementation plans referencing PrintOptim
- Updated 8 test files: renamed classes, updated comments
- Updated 2 source files: cleaned docstrings
- Removed migration documentation

Verification:
✅ Zero occurrences of 'printoptim' in codebase
✅ All tests passing
✅ Package builds successfully
✅ No proprietary information disclosed

This commit must be included before:
- Publishing v0.5.0-beta to PyPI
- Making repository public
- Any marketing/social media posts

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin pre-public-cleanup
```

---

## Security Checklist

**Before making repository public or publishing to PyPI**:

### Code Security
- [ ] Zero PrintOptim references in codebase
- [ ] No proprietary application names
- [ ] No customer/client names
- [ ] No internal URLs or server names
- [ ] No API keys or credentials (separate check)
- [ ] No private email addresses

### Documentation Security
- [ ] Marketing materials cleaned
- [ ] Show HN content safe for public
- [ ] No migration docs with proprietary details
- [ ] Examples use generic terminology
- [ ] README doesn't mention PrintOptim

### Git History
- [ ] Recent commits don't expose PrintOptim details
- [ ] Branch names don't include "printoptim"
- [ ] No sensitive info in commit messages

### Package/Distribution
- [ ] Built package doesn't include PrintOptim files
- [ ] PyPI description doesn't mention PrintOptim
- [ ] GitHub releases don't reference PrintOptim

### Final Scan
- [ ] `grep -ri "printoptim" . --exclude-dir=.git` returns ZERO results
- [ ] Package builds: `uv build` succeeds
- [ ] Tests pass: `uv run pytest --tb=short -q`
- [ ] No broken links in documentation

---

## Rollback Plan

**If issues arise during cleanup**:

### Undo Changes (Before Commit)
```bash
# Restore all changes
git restore .
git clean -fd

# Restore specific directories from git
git restore --source=HEAD --staged --worktree entities/printoptim/
git restore --source=HEAD --staged --worktree backup_internal/
```

### Undo Commit (After Commit)
```bash
# Undo last commit but keep changes
git reset --soft HEAD~1

# Undo last commit and discard changes
git reset --hard HEAD~1
```

### Restore from Archive
```bash
# If you archived backup_internal
cp -r ~/private_archives/specql_backups/backup_internal_*/ backup_internal/

# If you archived printoptim_migration
cp -r ~/archives/specql_cleanup_*/printoptim_migration/ .
```

---

## Timeline Estimate

| Phase | Task | Time |
|-------|------|------|
| **Phase 1** | Delete 5 directories | 5 min |
| **Phase 2** | Global find/replace (41 files) | 10 min |
| **Phase 3** | Documentation updates (15 files) | 1-2 hours |
| **Phase 4** | Test file updates (8 files) | 30 min |
| **Phase 5** | Source code updates (2 files) | 10 min |
| **Phase 6** | Verification & commit | 30 min |
| **Total** | | **2.5-3.5 hours** |

**Best Case**: 2.5 hours (minimal doc review)
**Realistic**: 3 hours (thorough review)
**Worst Case**: 4 hours (many manual doc edits)

---

## Post-Cleanup Actions

### Immediate (Same Day)
1. Run full test suite: `uv run pytest`
2. Build package: `uv build`
3. Verify package contents
4. Test local installation
5. Regenerate documentation site (if applicable)

### Before Public Release
1. Review all public-facing content
2. Double-check marketing materials
3. Test package installation from scratch
4. Review git commit history (last 20 commits)
5. Scan for any other proprietary references

### After Public Release
1. Monitor GitHub issues for any mentions
2. Check PyPI package description
3. Review initial user feedback
4. Update documentation if needed

---

## Summary

**Scope**: Remove 349 occurrences across 154 files
**Risk**: CRITICAL - Prevents proprietary information leak
**Time**: 2.5-3.5 hours
**Verification**: Zero "printoptim" references allowed

**Success Metrics**:
- ✅ `grep -ri "printoptim" . --exclude-dir=.git` returns 0 results
- ✅ All tests passing
- ✅ Package builds successfully
- ✅ Documentation safe for public
- ✅ Marketing materials safe for public
- ✅ No proprietary application names disclosed

**Next Actions**:
1. Execute this cleanup plan
2. Complete v0.5.0-beta release blockers
3. Publish to PyPI
4. Make repository public (if desired)

---

**Document Status**: Ready for execution
**Security Priority**: CRITICAL
**Must Complete Before**: PyPI publish, public repository, marketing
**Next Action**: Execute Phase 1 (Delete directories)
