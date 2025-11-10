# Repository Cleanup & Organization Plan

**Project**: printoptim_backend_poc
**Task**: Clean and organize repository structure
**Complexity**: Simple | **Direct Execution**
**Document Created**: 2025-11-10

---

## Executive Summary

Organize repository for production readiness by removing temporary files, consolidating documentation, and establishing clear directory structure. Current state has accumulated development artifacts (test outputs, temporary scripts, excessive docs) that should be cleaned up.

**Estimated Time**: 2-3 hours

---

## Current State Issues

### 1. Temporary Directories (4)
```
test_confiture/         # Confiture test output
test_hierarchical/      # Hierarchical test output
test_output/           # General test output
tmp_cli_test/          # CLI test artifacts
```
**Action**: Delete or add to .gitignore

### 2. Root-Level Scripts (2)
```
scripts/dev/compare_with_original.py   # Development comparison script
scripts/dev/generate_sql.py           # Development generation script
```
**Action**: Move to `scripts/` or `dev/` directory

### 3. Python Cache (140 directories)
```
__pycache__/ directories throughout
```
**Action**: Verify .gitignore, clean from git if tracked

### 4. Documentation Sprawl (125 files)
```
docs/
├── teams/           # 60+ team-specific planning docs
├── implementation-plans/  # 15+ phased plans
├── fraiseql/        # 8+ FraiseQL docs
├── architecture/    # 10+ architecture docs
├── analysis/        # Various analysis docs
└── *.md (root)      # 10+ loose docs
```
**Action**: Archive completed work, consolidate active docs

### 5. Test Organization
```
tests/
├── archived/        # ✅ Good - archived tests
├── integration/     # ✅ Good structure
├── unit/           # ✅ Good structure
├── pytest/         # ❓ Separate pytest tests?
└── schema/         # ❓ Schema fixtures?
```
**Action**: Verify test organization, document purpose

---

## PHASE 1: Remove Temporary Files

**Objective**: Clean up development artifacts

**Estimated Time**: 15 minutes

### Actions

1. **Remove test output directories**:
```bash
# Verify these are generated outputs
ls -la test_confiture/ test_hierarchical/ test_output/ tmp_cli_test/

# Remove if safe
rm -rf test_confiture/ test_hierarchical/ test_output/ tmp_cli_test/
```

2. **Update .gitignore**:
```bash
# Add to .gitignore if not already present
cat >> .gitignore <<EOF

# Test outputs
test_*/
tmp_*/
*_output/

# Development artifacts
scripts/dev/compare_with_original.py
scripts/dev/generate_sql.py
EOF
```

3. **Clean Python cache** (if tracked):
```bash
# Check if __pycache__ is tracked
git ls-files | grep __pycache__

# If found, remove from git
find . -type d -name "__pycache__" -exec git rm -r --cached {} +
```

**Checklist**:
- [ ] Test output directories removed
- [ ] .gitignore updated
- [ ] Python cache cleaned from git (if needed)
- [ ] No temporary files in git

---

## PHASE 2: Organize Root-Level Files

**Objective**: Clean up project root

**Estimated Time**: 30 minutes

### Actions

1. **Create development scripts directory**:
```bash
mkdir -p scripts/dev
```

2. **Move development scripts**:
```bash
# Move scripts to dev directory
mv scripts/dev/compare_with_original.py scripts/dev/
mv scripts/dev/generate_sql.py scripts/dev/

# Update any references in documentation
grep -r "scripts/dev/compare_with_original.py" docs/
grep -r "scripts/dev/generate_sql.py" docs/
```

3. **Verify root directory is clean**:
```bash
# Should only have:
# - pyproject.toml
# - README.md
# - GETTING_STARTED.md
# - uv.lock
# - Configuration files (.gitignore, confiture.yaml, etc.)

ls -1 *.py *.sql 2>/dev/null  # Should be empty
```

**Directory Structure** (root level):
```
printoptim_backend_poc/
├── .claude/
├── db/
├── docs/
├── entities/
├── migrations/
├── registry/
├── scripts/
│   └── dev/              # ← Development scripts
├── src/
├── stdlib/
├── templates/
├── tests/
├── pyproject.toml
├── README.md
├── GETTING_STARTED.md
└── uv.lock
```

**Checklist**:
- [ ] scripts/dev/ created
- [ ] Development scripts moved
- [ ] Root directory clean
- [ ] Documentation updated

---

## PHASE 3: Consolidate Documentation

**Objective**: Organize 125+ documentation files into clear structure

**Estimated Time**: 1 hour

### Current Structure (125 files)
```
docs/
├── teams/              # 60+ files (Team A-E planning & status)
├── implementation-plans/  # 15+ files (phased plans)
├── fraiseql/           # 8+ files (FraiseQL specs)
├── architecture/       # 10+ files (architecture docs)
├── analysis/           # Various analysis
└── *.md (loose)        # 10+ root-level docs
```

### Proposed Structure
```
docs/
├── README.md           # Documentation index
├── architecture/       # Active architecture docs
├── guides/            # User guides (NEW)
│   ├── getting-started.md
│   ├── rich-types.md
│   └── stdlib-usage.md
├── reference/         # API reference (NEW)
│   ├── scalar-types.md
│   └── fraiseql/
├── development/       # Development docs (NEW)
│   ├── testing.md
│   └── contributing.md
└── archive/          # Completed planning docs (NEW)
    ├── teams/         # All Team A-E docs
    └── plans/         # Completed implementation plans
```

### Actions

1. **Create new structure**:
```bash
mkdir -p docs/guides
mkdir -p docs/reference
mkdir -p docs/development
mkdir -p docs/archive/teams
mkdir -p docs/archive/plans
```

2. **Archive team planning docs** (completed work):
```bash
# Move all Team A-E docs to archive
mv docs/teams/* docs/archive/teams/

# Move completed implementation plans
mv docs/implementation-plans/TEAM_* docs/archive/plans/
```

3. **Keep active implementation plans**:
```bash
# Keep these in docs/implementation-plans/:
# - STDLIB_INTEGRATION_PHASED_PLAN.md
# - TEST_SUITE_FIX_PHASED_PLAN.md
# - Any other active/future plans
```

4. **Create documentation index**:
```bash
cat > docs/README.md <<'EOF'
# SpecQL Documentation

## Quick Links

- [Getting Started](../GETTING_STARTED.md)
- [Architecture Overview](architecture/)
- [Rich Types Guide](guides/rich-types.md)
- [stdlib Usage](guides/stdlib-usage.md)

## Documentation Structure

- **architecture/** - System architecture and design decisions
- **guides/** - User guides and tutorials
- **reference/** - API and type reference documentation
- **development/** - Development, testing, and contribution guides
- **implementation-plans/** - Active implementation plans
- **archive/** - Completed planning documents and historical records

## For Developers

- [Testing Guide](development/testing.md)
- [Contributing Guidelines](development/contributing.md)
- [Implementation Plans](implementation-plans/)

## Archive

Historical planning documents and completed team work:
- [Team Planning Archive](archive/teams/)
- [Completed Plans](archive/plans/)
EOF
```

5. **Consolidate FraiseQL docs**:
```bash
# Move to reference
mv docs/fraiseql docs/reference/
```

6. **Create essential guides**:
```bash
# Extract key info from existing docs into user guides
# - Rich types guide (from various rich type docs)
# - stdlib usage guide (from INTEGRATION_NOTES.md)
# - Testing guide (from test fix plans)
```

**Checklist**:
- [ ] New directory structure created
- [ ] Team docs archived
- [ ] Completed plans archived
- [ ] Active plans identified and kept
- [ ] docs/README.md created
- [ ] User guides created
- [ ] Reference docs organized

---

## PHASE 4: Clean Up Tests Directory

**Objective**: Verify and document test organization

**Estimated Time**: 30 minutes

### Current Structure
```
tests/
├── archived/           # Archived tests (good)
├── conftest.py         # Pytest configuration
├── fixtures/           # Test fixtures
├── integration/        # Integration tests
├── pytest/            # Separate pytest tests?
├── schema/            # Schema fixtures?
└── unit/              # Unit tests
```

### Actions

1. **Verify pytest/ directory purpose**:
```bash
# Check what's in pytest/
ls -la tests/pytest/

# Check if these are integration tests or special tests
head -20 tests/pytest/test_contact_integration.py
```

2. **Consolidate or document**:
- **Option A**: Move to integration/ if they're integration tests
- **Option B**: Document purpose in tests/README.md if they serve special purpose

3. **Verify schema/ directory**:
```bash
# Check schema directory
ls -la tests/schema/

# Likely fixtures - move to fixtures/ if appropriate
```

4. **Create tests/README.md**:
```bash
cat > tests/README.md <<'EOF'
# SpecQL Test Suite

## Structure

- **unit/** - Unit tests for individual components
- **integration/** - Integration tests with database/full stack
- **fixtures/** - Shared test fixtures and mock data
- **archived/** - Deprecated tests kept for reference

## Running Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Specific test file
uv run pytest tests/unit/core/test_scalar_types.py -v
```

## Test Coverage

- 906/910 tests passing (99.6%)
- 4 skipped (database-dependent)
- Target: 100% effective coverage
EOF
```

**Checklist**:
- [ ] pytest/ directory purpose verified
- [ ] schema/ directory organized
- [ ] tests/README.md created
- [ ] Test organization documented

---

## PHASE 5: Update Configuration Files

**Objective**: Ensure configuration files reflect clean structure

**Estimated Time**: 15 minutes

### Actions

1. **Update .gitignore**:
```bash
cat >> .gitignore <<'EOF'

# Test outputs and temporary directories
test_*/
tmp_*/
*_output/
*.db-journal
*.db-wal

# Development scripts (now in scripts/dev/)
/scripts/dev/compare_with_original.py
/scripts/dev/generate_sql.py

# Editor directories
.vscode/
.idea/

# macOS
.DS_Store

# Database files (keep in migrations/)
/*.db
/*.sql
EOF
```

2. **Verify pyproject.toml**:
```bash
# Check that tool configurations are up to date
# - pytest paths
# - ruff exclude patterns
# - mypy exclude patterns
```

3. **Update README.md** (if needed):
```bash
# Update any references to:
# - Old doc locations
# - Development scripts (now in scripts/dev/)
# - Test structure
```

**Checklist**:
- [ ] .gitignore updated
- [ ] pyproject.toml verified
- [ ] README.md updated
- [ ] All configs reference correct paths

---

## PHASE 6: Final Verification

**Objective**: Ensure repository is clean and organized

**Estimated Time**: 15 minutes

### Actions

1. **Run tests**:
```bash
uv run pytest --tb=short -q
# Should still have 906/910 passing
```

2. **Check git status**:
```bash
git status
# Should see clean organization changes
```

3. **Verify structure**:
```bash
tree -L 2 -d
# Should show clean, organized structure
```

4. **Check for untracked files**:
```bash
git status --short | grep "^??"
# Should only see intentional untracked files
```

5. **Create cleanup commit**:
```bash
git add -A
git commit -m "chore: Clean up and organize repository structure

- Remove temporary test output directories
- Move development scripts to scripts/dev/
- Archive completed team planning docs
- Consolidate documentation into clear structure
- Update .gitignore for cleaner working directory
- Add documentation indexes and guides

New structure:
- docs/guides/ - User guides
- docs/reference/ - API reference
- docs/development/ - Development docs
- docs/archive/ - Completed planning docs
- scripts/dev/ - Development scripts

All 906/910 tests still passing.

🎉 Repository is now production-ready!
"
```

**Checklist**:
- [ ] All tests passing
- [ ] Git status clean
- [ ] Directory structure verified
- [ ] Documentation organized
- [ ] Changes committed

---

## Success Criteria

### Before
```
- 125+ scattered documentation files
- Temporary test directories in root
- Development scripts in root
- No clear doc structure
- 140 __pycache__ directories
```

### After
```
✅ Clean root directory (configs only)
✅ Organized documentation (guides, reference, archive)
✅ Development scripts in scripts/dev/
✅ No temporary files
✅ Clear .gitignore
✅ Documentation index
✅ 906/910 tests still passing
✅ Production-ready structure
```

---

## Recommended Directory Structure (Final)

```
printoptim_backend_poc/
├── .claude/
│   └── CLAUDE.md
├── db/
│   └── schema/
│       ├── 00_foundation/
│       ├── 10_tables/
│       ├── 20_helpers/
│       └── 30_functions/
├── docs/
│   ├── README.md              # Documentation index
│   ├── architecture/          # Active architecture
│   ├── guides/               # User guides
│   ├── reference/            # API reference
│   ├── development/          # Dev guides
│   ├── implementation-plans/ # Active plans
│   └── archive/             # Completed work
│       ├── teams/
│       └── plans/
├── entities/                 # YAML entity definitions
├── migrations/               # Confiture migrations
├── registry/
│   └── domain_registry.yaml
├── scripts/
│   └── dev/                 # Development scripts
├── src/
│   ├── cli/
│   ├── core/
│   ├── generators/
│   ├── numbering/
│   ├── testing/
│   └── utils/
├── stdlib/                  # Standard library entities
├── templates/               # Jinja2 templates
├── tests/
│   ├── README.md
│   ├── conftest.py
│   ├── fixtures/
│   ├── integration/
│   ├── unit/
│   └── archived/
├── .gitignore
├── confiture.yaml
├── pyproject.toml
├── README.md
├── GETTING_STARTED.md
└── uv.lock
```

---

## Quick Commands Reference

```bash
# Phase 1: Remove temporary files
rm -rf test_* tmp_*

# Phase 2: Organize root
mkdir -p scripts/dev
mv scripts/dev/compare_with_original.py scripts/dev/generate_sql.py scripts/dev/

# Phase 3: Consolidate docs
mkdir -p docs/{guides,reference,development,archive/{teams,plans}}
mv docs/teams/* docs/archive/teams/
mv docs/implementation-plans/TEAM_* docs/archive/plans/

# Phase 4: Clean tests
# (Manual verification)

# Phase 5: Update configs
# (Edit .gitignore)

# Phase 6: Commit
git add -A
git commit -m "chore: Clean up and organize repository structure"
```

---

**Total Estimated Time**: 2-3 hours
**Complexity**: Simple - straightforward file organization
**Risk**: Low - all changes are organizational, no code changes

---

**Document Version**: 1.0
**Last Updated**: 2025-11-10
**Status**: Ready for execution
