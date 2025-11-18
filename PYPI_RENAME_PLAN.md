# PyPI Package Rename Implementation Plan
## From `specql-generator` → `specql`

**Date**: 2025-11-17
**Current Version**: 0.5.0
**Status**: READY TO EXECUTE
**Impact**: MINIMAL (package published <1 hour ago)

---

## Executive Summary

Rename the PyPI package from `specql-generator` to `specql` to:
- Simplify installation (`pip install specql`)
- Align package name with CLI command (`specql`)
- Improve branding and professionalism
- Enable future expansion beyond "generator"

**Timeline**: 30-45 minutes
**Risk Level**: LOW (package is brand new)

---

## Phase 1: Prepare New Package

### Step 1.1: Update pyproject.toml
```toml
# Change package name
[project]
name = "specql"  # Was: specql-generator
version = "0.5.0"
```

**Files to modify**: `pyproject.toml`

### Step 1.2: Verify CLI Entry Point
```toml
# Ensure CLI command remains "specql"
[project.scripts]
specql = "src.cli.confiture_extensions:specql"
```

**No changes needed** - already correct!

### Step 1.3: Update README Installation Instructions
```bash
# Update all references:
# OLD: pip install specql-generator
# NEW: pip install specql
```

**Files to check**:
- `README.md`
- `docs/GETTING_STARTED.md` (if exists)
- Any documentation files

---

## Phase 2: Build and Publish New Package

### Step 2.1: Clean Build Environment
```bash
# Remove old build artifacts
rm -rf dist/ build/ src/*.egg-info

# Verify clean state
git status
```

### Step 2.2: Build New Package
```bash
# Build with new name
uv run python -m build

# Verify package name in dist/
ls -lh dist/
# Expected:
# - specql-0.5.0-py3-none-any.whl
# - specql-0.5.0.tar.gz
```

### Step 2.3: Verify Package Quality
```bash
# Check package integrity
uv run twine check dist/*

# Expected: PASSED (warnings about long_description are OK)
```

### Step 2.4: Test Install Locally
```bash
# Create test environment
python -m venv /tmp/test-specql
source /tmp/test-specql/bin/activate

# Test install from wheel
pip install dist/specql-0.5.0-py3-none-any.whl

# Verify CLI works
specql --version
# Expected: Show version info

# Verify import works
python -c "import src.core.specql_parser; print('OK')"

# Cleanup
deactivate
rm -rf /tmp/test-specql
```

### Step 2.5: Publish to PyPI
```bash
# Upload to PyPI
uv run twine upload dist/*

# Expected output:
# View at: https://pypi.org/project/specql/0.5.0/
```

### Step 2.6: Verify Publication
```bash
# Check PyPI
curl -s https://pypi.org/pypi/specql/json | jq -r '.info.version'
# Expected: 0.5.0

# Test installation from PyPI
pip install specql==0.5.0
specql --version
```

---

## Phase 3: Deprecate Old Package

### Step 3.1: Create Deprecation Package

Create `pyproject.toml.deprecated` for `specql-generator`:

```toml
[project]
name = "specql-generator"
version = "0.5.1"  # Bump version to signal deprecation
description = "DEPRECATED: Use 'specql' instead"
authors = [
    {name = "Lionel Hamayon", email = "lionel.hamayon@evolution-digitale.fr"}
]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "specql>=0.5.0",  # Depend on new package
]

[project.scripts]
specql = "src.cli.confiture_extensions:specql"
```

### Step 3.2: Create Deprecation Warning

Create `src/__init__.py` with warning:

```python
"""
DEPRECATION WARNING
===================

The 'specql-generator' package has been renamed to 'specql'.

Please update your installation:
    pip uninstall specql-generator
    pip install specql

The 'specql-generator' package will not receive future updates.
"""

import warnings

warnings.warn(
    "The 'specql-generator' package is deprecated. "
    "Please use 'specql' instead: pip install specql",
    DeprecationWarning,
    stacklevel=2
)
```

### Step 3.3: Build and Publish Deprecation Package
```bash
# Temporarily restore old name for deprecation release
cp pyproject.toml pyproject.toml.new
cp pyproject.toml.deprecated pyproject.toml

# Clean and rebuild
rm -rf dist/ build/ src/*.egg-info
uv run python -m build

# Publish deprecation version
uv run twine upload dist/*

# Restore new package config
mv pyproject.toml.new pyproject.toml
```

### Step 3.4: Add PyPI Deprecation Notice

On PyPI, update the `specql-generator` project description:

1. Go to: https://pypi.org/manage/project/specql-generator/
2. Edit project description
3. Add prominent deprecation notice:

```markdown
⚠️ **DEPRECATED** ⚠️

This package has been renamed to `specql`.

Please update your installation:
```bash
pip uninstall specql-generator
pip install specql
```

Future updates will only be published to the `specql` package.
```

---

## Phase 4: Update Documentation & Git

### Step 4.1: Update All Documentation
```bash
# Files to update:
- README.md (installation instructions)
- CHANGELOG.md (add rename notice)
- docs/ (any documentation)
- .github/workflows/release.yml (comments, if any)
```

**Search and replace**:
```bash
# Find all references
rg "specql-generator" --type md
rg "specql_generator" --type md

# Replace with: specql
```

### Step 4.2: Update CHANGELOG.md
```markdown
## [0.5.0] - 2025-11-17

### Changed
- **BREAKING**: Renamed PyPI package from `specql-generator` to `specql`
  - Old: `pip install specql-generator`
  - New: `pip install specql`
  - Migration: `pip uninstall specql-generator && pip install specql`
  - The `specql-generator` package is deprecated and will not receive updates
```

### Step 4.3: Commit Changes
```bash
# Stage changes
git add pyproject.toml README.md CHANGELOG.md

# Commit
git commit -m "refactor: rename PyPI package from specql-generator to specql

BREAKING CHANGE: The PyPI package name has been changed from
'specql-generator' to 'specql' for better branding and simplicity.

Migration instructions:
  pip uninstall specql-generator
  pip install specql

The old 'specql-generator' package (v0.5.1) is deprecated and will
forward to 'specql', but will not receive future updates.

Rationale:
- Simpler installation command
- Aligns with CLI command name (specql)
- Enables future expansion beyond code generation
- Better branding and professionalism

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to main
git push origin main
```

---

## Phase 5: Update GitHub Release

### Step 5.1: Create New GitHub Release

Since the package name changed, optionally create a new GitHub release to highlight this:

**Option A**: Edit existing v0.5.0 release
```bash
gh release edit v0.5.0 --notes-file - <<'EOF'
## [0.5.0] - 2025-11-17

⚠️ **IMPORTANT: Package Renamed**

The PyPI package has been renamed from `specql-generator` to `specql`.

**New Installation:**
```bash
pip install specql
```

**Migration from old package:**
```bash
pip uninstall specql-generator
pip install specql
```

[Rest of release notes...]
EOF
```

**Option B**: Create v0.5.0 patch release (v0.5.0.post1)
- Not recommended for this case

**Recommended**: Option A (edit existing release)

---

## Phase 6: Update Workflow for Future Releases

### Step 6.1: Verify Workflow Compatibility

Check `.github/workflows/release.yml`:
```yaml
# No changes needed - workflow uses pyproject.toml name
# Build and publish steps will automatically use new name
```

**Action**: No changes required ✓

### Step 6.2: Test Workflow (Optional)

Create a test tag to verify:
```bash
# Create test tag
git tag -a v0.5.0-test -m "Test release workflow with new package name"
git push origin v0.5.0-test

# Watch workflow
gh run watch

# Delete test tag after verification
git tag -d v0.5.0-test
git push origin :refs/tags/v0.5.0-test
```

**Action**: Optional - only if you want to test before next real release

---

## Phase 7: Communication & Monitoring

### Step 7.1: Announcement Channels

If you have users (unlikely given <1 hour since release), announce:

- **GitHub Discussions** (if enabled)
- **Project README** (already updated)
- **Twitter/Social Media** (if applicable)

**Message Template**:
```
🎉 SpecQL v0.5.0 is now available!

📦 New Package Name: The PyPI package is now simply "specql"

Installation:
  pip install specql

The old specql-generator package is deprecated.

Learn more: https://github.com/fraiseql/specql
```

### Step 7.2: Monitor for Issues

Monitor for 48 hours:
- GitHub Issues for installation problems
- PyPI download stats: https://pypistats.org/packages/specql
- Old package downloads: https://pypistats.org/packages/specql-generator

**Action Items**:
- [ ] Check issues daily for 2 days
- [ ] Monitor download stats weekly

---

## Rollback Plan (If Needed)

**Scenario**: Critical issue discovered with new package name

### Rollback Steps:
```bash
# 1. Revert pyproject.toml
git revert <commit-hash>
git push origin main

# 2. Publish fixed version to old name
# Update version to 0.5.2 with old name
uv run python -m build
uv run twine upload dist/*

# 3. Mark new package as yanked on PyPI
# Go to: https://pypi.org/manage/project/specql/release/0.5.0/
# Click "Yank release" with reason: "Reverting package rename"

# 4. Communicate rollback
# Update README, send announcement
```

**Probability**: VERY LOW (package name change is low-risk)

---

## Success Criteria

All tasks complete when:
- [x] New package `specql` published on PyPI
- [x] Old package `specql-generator` deprecated with warning
- [x] README and docs updated
- [x] Git history reflects change
- [x] GitHub release notes updated
- [x] Installation tested: `pip install specql` works
- [x] CLI verified: `specql --version` works
- [x] No installation errors reported

---

## Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|------------|
| 1 | Update pyproject.toml & docs | 5 min | 5 min |
| 2 | Build & publish new package | 10 min | 15 min |
| 3 | Create & publish deprecation | 10 min | 25 min |
| 4 | Update git & documentation | 5 min | 30 min |
| 5 | Update GitHub release | 5 min | 35 min |
| 6 | Test & verify | 10 min | 45 min |

**Total Estimated Time**: 45 minutes

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Name already taken | LOW | HIGH | Checked - `specql` is available ✓ |
| Breaking user installs | VERY LOW | MEDIUM | Package <1 hour old, zero users likely |
| Installation issues | LOW | MEDIUM | Test locally before publishing |
| Documentation gaps | LOW | LOW | Search for all references |
| Workflow breaks | VERY LOW | HIGH | Test with dry-run first |

**Overall Risk**: LOW

---

## Pre-Execution Checklist

Before starting, verify:
- [ ] `specql` name is still available on PyPI
- [ ] Working in clean git state (`git status`)
- [ ] Have PyPI credentials configured (`~/.pypirc`)
- [ ] Have `build` and `twine` installed
- [ ] No active users depending on `specql-generator` (check PyPI stats)
- [ ] Backup current state: `git tag backup-pre-rename`

---

## Post-Execution Checklist

After completion, verify:
- [ ] `pip install specql` works from fresh environment
- [ ] `specql --version` shows correct version
- [ ] PyPI page shows correct package: https://pypi.org/project/specql/
- [ ] Old package shows deprecation warning
- [ ] README has updated installation instructions
- [ ] CHANGELOG documents the change
- [ ] GitHub release notes updated
- [ ] All tests still pass: `uv run pytest`

---

## Notes

- **Package Name on PyPI ≠ Import Name**: The package name is `specql` but imports are still from `src.*` (this is fine and common)
- **CLI Command Unchanged**: `specql` command was already correct
- **Version Strategy**: Keep as 0.5.0 for new package, use 0.5.1 for deprecation notice on old package
- **Timing**: Execute during low-traffic hours (already met - package just published)

---

## Questions & Decisions

### Q: Should we yank the old 0.5.0 from specql-generator?
**A**: NO - Leave it for 30 days, then yank with message pointing to new package

### Q: Should we publish both names simultaneously?
**A**: NO - Only maintain `specql`, let `specql-generator` 0.5.1 be a wrapper with deprecation

### Q: What about existing GitHub stars/issues?
**A**: NO IMPACT - Repository stays the same, only PyPI package name changes

### Q: Should we bump to 0.6.0 instead of keeping 0.5.0?
**A**: NO - Keep 0.5.0 since it's the same code, just different package name

---

## Appendix: Commands Reference

```bash
# Quick reference for execution

# Phase 1: Update files
vim pyproject.toml  # Change name to "specql"
vim README.md       # Update pip install commands

# Phase 2: Build & Publish New
rm -rf dist/ build/ src/*.egg-info
uv run python -m build
uv run twine check dist/*
uv run twine upload dist/*

# Phase 3: Deprecate Old
# (Follow detailed steps in Phase 3)

# Phase 4: Git
git add pyproject.toml README.md CHANGELOG.md
git commit -m "refactor: rename PyPI package to specql"
git push origin main

# Phase 5: Test
pip install specql==0.5.0
specql --version
```

---

**END OF IMPLEMENTATION PLAN**

*This plan provides a complete, step-by-step guide to safely rename the PyPI package from `specql-generator` to `specql` with minimal disruption.*
