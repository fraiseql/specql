# Week 18: Alpha Release Preparation
**Date**: 2025-11-15 to 2025-11-22
**Focus**: Version Updates, README Enhancement, and Workflow Verification
**Estimated Time**: 4-6 hours
**Priority**: Critical - Release Blocker

---

## 📋 Objectives

Prepare the repository infrastructure for public alpha release by:
1. Correcting version files to 0.4.0-alpha
2. Adding prominent alpha notice to README
3. Verifying GitHub Actions workflows are production-ready
4. Running comprehensive quality checks

---

## 🎯 Phase 1: Version Correction (30 minutes)

### Task 1.1: Update VERSION File
**File**: `VERSION`
**Current**: `0.4.0`
**Target**: `0.4.0-alpha`

```bash
# Update VERSION file
echo "0.4.0-alpha" > VERSION

# Verify
cat VERSION
```

**Rationale**: The VERSION file must include the "-alpha" suffix to match the CHANGELOG and indicate pre-release status.

### Task 1.2: Update pyproject.toml
**File**: `pyproject.toml`
**Line**: ~3
**Current**: `version = "0.4.0"`
**Target**: `version = "0.4.0-alpha"`

```bash
# Edit pyproject.toml (line 3)
# Before: version = "0.4.0"
# After:  version = "0.4.0-alpha"
```

**Rationale**: Package version must match VERSION file and CHANGELOG for consistency checks in GitHub Actions.

### Task 1.3: Verify Version Consistency
```bash
# Check all version references
grep -r "0\.4\.0" --include="*.toml" --include="VERSION" --include="*.md" .

# Expected matches:
# - VERSION: 0.4.0-alpha
# - pyproject.toml: version = "0.4.0-alpha"
# - CHANGELOG.md: ## [0.4.0-alpha] - 2025-11-15
```

### Task 1.4: Commit Version Updates
```bash
git add VERSION pyproject.toml
git commit -m "chore: update version to 0.4.0-alpha

- Update VERSION file to 0.4.0-alpha
- Update pyproject.toml version to 0.4.0-alpha
- Ensures consistency with CHANGELOG.md
- Prepares for public alpha release"
```

**Success Criteria**:
- [ ] VERSION file contains exactly `0.4.0-alpha`
- [ ] pyproject.toml version is `0.4.0-alpha`
- [ ] Changes committed to git

---

## 🎯 Phase 2: README Alpha Notice (45 minutes)

### Task 2.1: Add Alpha Warning Banner
**File**: `README.md`
**Location**: Immediately after title, before first paragraph

```markdown
# SpecQL - Multi-Language Backend Code Generator

> **🚧 ALPHA RELEASE (v0.4.0-alpha)**: SpecQL is in active development. APIs may change.
> Production use is not recommended yet. [Report issues](https://github.com/fraiseql/specql/issues).

**20 lines YAML → 2000+ lines production code in 4 languages (100x leverage)**

Generate production-ready backends from single YAML spec:
**PostgreSQL** · **Java/Spring Boot** · **Rust/Diesel** · **TypeScript/Prisma**
```

**Rationale**: Users must immediately see alpha status AND understand this is multi-language code generation, not just PostgreSQL.

### Task 2.2: Update Status Section
**File**: `README.md`
**Location**: Bottom of file (or create if missing)

Add/update this section:

```markdown
---

## Current Status

**Release**: 🚧 **Alpha (v0.4.0-alpha)** - Multi-language backend generation
**Languages**: PostgreSQL + Java + Rust + TypeScript
**Test Coverage**: 96%+ across 371 Python files
**Stability**: Pre-release - APIs subject to change

### Supported Technologies
- **PostgreSQL**: 14+ with Trinity pattern (pk_*, id, identifier)
- **Java**: 17+ (Spring Boot 3.x, JPA/Hibernate, Lombok)
- **Rust**: 1.70+ (Diesel 2.x, Actix-web)
- **TypeScript**: 4.9+ (Prisma Client, type-safe interfaces)

### Known Limitations
- Frontend generation not yet implemented
- Infrastructure as Code partial (Terraform/Pulumi in progress)
- Not published to PyPI (install from source only)
- Discord and GitHub Discussions not yet available
```

### Task 2.3: Update Installation Section
Ensure installation instructions reflect alpha status:

```markdown
## Installation

### From Source (Required for Alpha)

```bash
git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
uv pip install -e .
```

### Verify Installation

```bash
specql --version  # Should show: 0.4.0-alpha
specql generate entities/examples/**/*.yaml
```

**Note**: SpecQL is not yet published to PyPI. Source installation is required.
```

### Task 2.4: Add Community Section
**File**: `README.md`
**Location**: Near bottom, before license

```markdown
## Community & Support

**Alpha Release**: SpecQL is in early alpha. We're building in public!

- 📖 [Documentation](docs/) - Complete guides and references
- 🐛 [Report Bugs](https://github.com/fraiseql/specql/issues) - Help us improve
- 💡 [Feature Requests](https://github.com/fraiseql/specql/issues) - Share your ideas
- 📦 [Examples](examples/) - Working code examples
- 📝 [Changelog](CHANGELOG.md) - See what's new

**Coming Soon**: Discord community and GitHub Discussions
```

### Task 2.5: Commit README Updates
```bash
git add README.md
git commit -m "docs: add alpha release notice and status to README

- Add prominent alpha warning banner at top
- Update status section with current metrics
- Clarify installation requires source (not PyPI)
- Add community section with GitHub issues links
- Document known limitations for alpha
- Prepares for public repository visibility"
```

**Success Criteria**:
- [ ] Alpha warning visible in first 5 lines of README
- [ ] Status section shows v0.4.0-alpha
- [ ] Known limitations documented
- [ ] Community links point to GitHub issues only
- [ ] Changes committed to git

---

## 🎯 Phase 3: Workflow Verification (1-2 hours)

### Task 3.1: Review Workflow Files
**Files to Review**:
- `.github/workflows/tests.yml`
- `.github/workflows/code-quality.yml`
- `.github/workflows/version-check.yml`
- `.github/workflows/release.yml`

**Checklist for Each Workflow**:
- [ ] Triggers are appropriate (push, pull_request, tags)
- [ ] Permissions are minimal and correct
- [ ] Python versions match project requirements (3.11+)
- [ ] Dependencies installation uses `uv sync`
- [ ] Error handling is robust
- [ ] Secrets are not hardcoded

### Task 3.2: Test Workflows Locally

#### Test Suite
```bash
# Run full test suite (as GitHub Actions will)
uv run pytest --tb=short

# Expected: All tests pass
# If failures occur, fix before proceeding
```

#### Code Quality Checks
```bash
# Linting
uv run ruff check src/ tests/

# Formatting
uv run ruff format --check src/ tests/

# Type checking
uv run mypy src/

# Expected: All checks pass
# Fix any issues before proceeding
```

#### Coverage Check
```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=term --cov-report=html

# Expected: 96%+ coverage maintained
# Review coverage report in htmlcov/index.html
```

### Task 3.3: Verify Version Check Workflow
**File**: `.github/workflows/version-check.yml`

This workflow is critical - it ensures VERSION, pyproject.toml, and git tags match.

**Manual Test**:
```bash
# Simulate what the workflow does
VERSION_FILE=$(cat VERSION)
PYPROJECT_VERSION=$(grep 'version = ' pyproject.toml | cut -d'"' -f2)

echo "VERSION file: $VERSION_FILE"
echo "pyproject.toml: $PYPROJECT_VERSION"

# Should both show: 0.4.0-alpha
```

### Task 3.4: Verify Release Workflow
**File**: `.github/workflows/release.yml`

**Key Points to Verify**:
1. **Line 45-50**: Version consistency check
   - Uses VERSION file and git tag
   - Will fail if mismatch occurs

2. **Line 52-68**: CHANGELOG extraction
   - Extracts content between `## [0.4.0-alpha]` and next `## [`
   - Uses this as GitHub release notes

3. **Line 74**: Pre-release detection
   - Automatically marks releases with `-alpha`, `-beta`, `-rc` as pre-releases
   - Perfect for v0.4.0-alpha!

**Manual Verification**:
```bash
# Check CHANGELOG format is correct
sed -n '/## \[0.4.0-alpha\]/,/## \[/p' CHANGELOG.md | head -20

# Should show:
# ## [0.4.0-alpha] - 2025-11-15
# ### 🎉 First Public Alpha Release
# ...
```

### Task 3.5: Document Workflow Status
Create a simple status file:

```bash
cat > WORKFLOW_VERIFICATION.md << 'EOF'
# GitHub Actions Workflow Verification
**Date**: 2025-11-15
**Status**: ✅ Verified and Production-Ready

## Workflow Status

### ✅ tests.yml
- Triggers: push, pull_request
- Python versions: 3.12, 3.13
- Status: Production-ready

### ✅ code-quality.yml
- Checks: ruff, mypy, security (bandit)
- Status: Production-ready

### ✅ version-check.yml
- Validates: VERSION, pyproject.toml, git tags
- Status: Production-ready

### ✅ release.yml
- Triggers: git tags matching v*
- Creates: GitHub releases with CHANGELOG
- Pre-release: Automatic for alpha/beta/rc
- Status: Production-ready

## Local Verification Results

### Test Suite
- Command: `uv run pytest --tb=short`
- Result: ✅ All tests pass
- Coverage: 96%+

### Code Quality
- Linting: ✅ Pass
- Formatting: ✅ Pass
- Type checking: ✅ Pass

### Version Consistency
- VERSION: 0.4.0-alpha
- pyproject.toml: 0.4.0-alpha
- CHANGELOG.md: 0.4.0-alpha
- Status: ✅ Consistent

## Conclusion
All GitHub Actions workflows are production-ready for v0.4.0-alpha release.
EOF
```

**Success Criteria**:
- [ ] All 4 workflows reviewed and understood
- [ ] Local tests pass completely
- [ ] Code quality checks pass
- [ ] Version consistency verified
- [ ] CHANGELOG format validated
- [ ] Workflow verification documented

---

## 🎯 Phase 4: Pre-Release Quality Audit (1-2 hours)

### Task 4.1: Security Scan
```bash
# Run security checks
uv run bandit -r src/ -ll

# Expected: No high/medium severity issues
# Address any security findings before release
```

### Task 4.2: Check for Sensitive Data
```bash
# Scan git history for sensitive files
git log --all --full-history --source -- \
  '*secret*' '*password*' '*.env' '*credential*' '*key*' \
  '*token*' '*.pem' '*.key'

# Expected: No matches
# If matches found, review and ensure no secrets committed
```

### Task 4.3: Verify .gitignore Completeness
```bash
# Check .gitignore has critical patterns
cat .gitignore | grep -E "\.env|secret|credential|private|\.key|\.pem|token"

# Should include:
# .env
# *.env
# secrets/
# credentials/
# *.key
# *.pem
# Add any missing patterns
```

### Task 4.4: Check Debug/Print Statements
```bash
# Find debug print statements in production code
git grep -n "print(.*#.*debug" src/
git grep -n "print(.*DEBUG" src/
git grep -n "console.log" src/

# Review and remove/comment out debug statements
# Note: This will be more thoroughly addressed in Week 19 TODO cleanup
```

### Task 4.5: Run Integration Tests
```bash
# Run integration tests to ensure end-to-end works
uv run pytest tests/integration/ --tb=short -v

# Expected: All integration tests pass
# Fix any failures before release
```

### Task 4.6: Documentation Spell Check
```bash
# Quick documentation review
aspell check README.md
aspell check CHANGELOG.md

# Fix any obvious typos
# Don't spend too long on this - focus on critical docs
```

**Success Criteria**:
- [ ] Security scan shows no critical issues
- [ ] No sensitive data in git history
- [ ] .gitignore properly configured
- [ ] Debug statements identified (if any)
- [ ] Integration tests pass
- [ ] Critical documentation reviewed

---

## 📊 Week 18 Success Criteria

### Version & Documentation
- [ ] VERSION file updated to `0.4.0-alpha`
- [ ] pyproject.toml version updated to `0.4.0-alpha`
- [ ] README has prominent alpha warning
- [ ] README status section updated
- [ ] Known limitations documented

### GitHub Actions
- [ ] All 4 workflows reviewed and verified
- [ ] Local tests pass (pytest)
- [ ] Code quality checks pass (ruff, mypy)
- [ ] Coverage maintained at 96%+
- [ ] Workflow verification documented

### Quality & Security
- [ ] Security scan completed
- [ ] No sensitive data exposed
- [ ] .gitignore comprehensive
- [ ] Integration tests pass
- [ ] Critical docs spell-checked

### Git Commits
- [ ] Version updates committed
- [ ] README updates committed
- [ ] All changes on `pre-public-cleanup` branch
- [ ] No uncommitted changes remaining

---

## 📝 Deliverables

1. **Updated VERSION file** (0.4.0-alpha)
2. **Updated pyproject.toml** (version 0.4.0-alpha)
3. **Enhanced README.md** (alpha notice, status, community)
4. **WORKFLOW_VERIFICATION.md** (workflow status documentation)
5. **Quality audit results** (security, integration tests)
6. **Git commits** (all changes committed and clean working directory)

---

## ⏭️ Next Week Preview

**Week 19**: TODO/FIXME Cleanup Campaign
- Fix 8 critical TODOs blocking core functionality
- Create GitHub issues for 85 important TODOs
- Remove 25 outdated TODO comments
- Update 13 deferred TODOs with issue references
- Estimated time: 10-12 hours

---

## 🚨 Blockers & Risks

### Potential Blockers
1. **Tests failing locally** - Must fix before proceeding
2. **Type checking errors** - Address mypy issues
3. **Security vulnerabilities** - Must patch before public release

### Risk Mitigation
- Run all checks locally before committing
- Keep changes small and focused
- Test after each phase completion
- Don't proceed to Week 19 until all Week 18 criteria met

---

## 📞 Questions & Clarifications

If you encounter issues:
1. Check ALPHA_RELEASE_IMPLEMENTATION_PLAN.md for detailed guidance
2. Review existing completion reports for context
3. Test locally before making changes
4. Ask for help rather than guessing on critical steps

---

**Week 18 Status**: 🟡 Ready to Start
**Next Action**: Update VERSION file and pyproject.toml to 0.4.0-alpha
**Estimated Completion**: 2025-11-22
