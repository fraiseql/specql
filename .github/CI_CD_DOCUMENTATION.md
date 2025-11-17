# SpecQL CI/CD Documentation

## Overview

SpecQL uses GitHub Actions for continuous integration and deployment. This document describes all workflows and their purposes.

## Workflows

### 1. Main CI Pipeline (`ci.yml`)

**Triggers**: Push to `main`, `develop`, `claude/**` branches; PRs to `main`, `develop`

**Jobs**:

#### Test Matrix
- Runs tests on Python 3.11 and 3.12
- Uses PostgreSQL 16 service for integration tests
- Separates unit and integration tests
- Uploads JUnit test results as artifacts
- **Database**: `postgresql://postgres:postgres@localhost:5432/specql_test`

#### Code Quality (Lint)
- **Ruff**: Linting for code quality and style issues
- **Ruff Format**: Code formatting validation
- **Black**: Additional formatting checks
- **MyPy**: Type checking (soft-fail for now)

#### Coverage
- Runs full test suite with coverage tracking
- Uploads to Codecov for trend analysis
- Generates HTML coverage report as artifact
- Minimum coverage: Not enforced yet (monitoring phase)

#### Security Scan
- **Bandit**: Python security linter
- **Safety**: Dependency vulnerability scanner
- Both set to `continue-on-error: true` (monitoring phase)

#### Build Distribution
- Builds Python package (wheel + sdist)
- Validates package with `twine check`
- Uploads distribution artifacts

#### Documentation Check
- Validates markdown links
- Lints YAML files with yamllint
- Soft-fail to not block PRs

**Status**: ✅ **Active and required for PRs**

---

### 2. Version Check (`version-check.yml`)

**Triggers**: PRs to `main`

**Purpose**: Ensures version bumps are valid before merging

**Checks**:
1. Version file changed (or intentionally skipped for docs/tests)
2. Valid semver format (MAJOR.MINOR.PATCH)
3. Version incremented (not decremented)
4. `VERSION` file synced with `pyproject.toml`

**How to bump version**:
```bash
# Automated (recommended)
make version-patch  # 0.5.0 -> 0.5.1
make version-minor  # 0.5.0 -> 0.6.0
make version-major  # 0.5.0 -> 1.0.0

# Manual
python scripts/version.py bump [patch|minor|major]
```

**Status**: ✅ **Active and required for PRs to main**

---

### 3. Release Pipeline (`release.yml`)

**Triggers**: Push of tags matching `v*.*.*` (e.g., `v0.5.0`)

**Process**:
1. Checkout code and setup Python 3.11
2. Install dependencies with `uv`
3. Run full test suite:
   - **Stable releases**: Tests MUST pass
   - **Pre-releases** (beta/alpha/rc): Tests can fail
4. Verify version consistency between tag and `VERSION` file
5. Extract changelog from `CHANGELOG.md`
6. Create GitHub Release with changelog
7. Build distribution packages
8. Publish to PyPI using trusted publishing

**PyPI Publishing**:
- Uses PyPI Trusted Publishing (OIDC)
- No API tokens required
- Requires `id-token: write` permission
- Automatically publishes to https://pypi.org/project/specql-generator/

**How to create a release**:
```bash
# 1. Bump version and update CHANGELOG
make version-minor  # or patch/major

# 2. Edit CHANGELOG.md to add release notes
vim CHANGELOG.md

# 3. Commit changes
git add VERSION CHANGELOG.md pyproject.toml
git commit -m "chore: prepare release v0.6.0"

# 4. Create and push tag
git tag v0.6.0
git push origin v0.6.0
```

**Status**: ✅ **Active for tagged releases**

---

### 4. CodeQL Security Analysis (`codeql.yml`)

**Triggers**:
- Push to `main`, `develop`
- PRs to `main`, `develop`
- Weekly schedule (Mondays at 00:00 UTC)

**Purpose**: Advanced security and code quality analysis

**Queries**:
- Security-extended: Deep security vulnerability detection
- Security-and-quality: Best practices and quality issues

**Analysis**: Python codebase

**Results**: Posted to GitHub Security tab

**Status**: ✅ **Active - results in Security tab**

---

### 5. Stale Issues/PRs (`stale.yml`)

**Triggers**: Daily at 01:00 UTC

**Purpose**: Automatic cleanup of inactive issues and PRs

**Configuration**:

**Issues**:
- Marked stale after 60 days
- Closed 7 days after stale
- Exempt labels: `enhancement`, `bug`, `documentation`, `help-wanted`, `good-first-issue`, `priority:high`

**Pull Requests**:
- Marked stale after 30 days
- Closed 14 days after stale
- Exempt labels: `priority:high`, `work-in-progress`, `blocked`

**Status**: ✅ **Active for maintenance**

---

### 6. Pull Request Labeler (`labeler.yml`)

**Triggers**: PR opened, synchronized, or reopened

**Purpose**: Automatic label assignment based on changed files

**Labels Applied**:
- `documentation` - Docs or markdown changes
- `testing` - Test file changes
- `team-a:parser` - Parser changes
- `team-b:schema` - Schema generator changes
- `team-c:actions` - Action compiler changes
- `team-d:fraiseql` - FraiseQL metadata changes
- `team-e:cli` - CLI changes
- `registry` - Registry changes
- `ci-cd` - CI/CD changes
- `dependencies` - Dependency updates
- `configuration` - Config file changes
- `examples` - Example changes
- `templates` - Template changes
- `database` - Database/migration changes

**Status**: ✅ **Active for PRs**

---

### 7. Dependabot (`dependabot.yml`)

**Triggers**: Weekly on Mondays at 09:00 UTC

**Purpose**: Automated dependency updates

**Ecosystems**:
1. **Python (`pip`)**: Dependencies in `pyproject.toml`
2. **GitHub Actions**: Workflow action versions

**Configuration**:
- Max 10 PRs for Python deps
- Max 5 PRs for GitHub Actions
- Auto-labels: `dependencies`, `python`/`github-actions`
- Commit prefix: `chore` (Python), `ci` (Actions)

**Status**: ✅ **Active for dependency management**

---

## CI/CD Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Events                           │
└───────┬─────────────────────────────────────────────────────┘
        │
        ├──► Push/PR ──────► ci.yml (Main CI Pipeline)
        │                      ├─ Tests (Python 3.11, 3.12)
        │                      ├─ Code Quality (Ruff, Black, MyPy)
        │                      ├─ Coverage (Codecov)
        │                      ├─ Security (Bandit, Safety)
        │                      ├─ Build (Package distribution)
        │                      └─ Docs Check (Links, YAML)
        │
        ├──► PR to main ──────► version-check.yml
        │                      └─ Validate version bump
        │
        ├──► Tag push ────────► release.yml
        │                      ├─ Run tests
        │                      ├─ Build package
        │                      ├─ Create GitHub Release
        │                      └─ Publish to PyPI
        │
        ├──► Schedule ────────► codeql.yml (Weekly security scan)
        │                      └─ CodeQL analysis
        │
        ├──► Schedule ────────► stale.yml (Daily cleanup)
        │                      └─ Close stale issues/PRs
        │
        ├──► PR events ───────► labeler.yml
        │                      └─ Auto-label based on files
        │
        └──► Schedule ────────► dependabot.yml (Weekly updates)
                               └─ Dependency update PRs
```

---

## Required Secrets

### GitHub Repository Secrets

1. **`GITHUB_TOKEN`** (Automatic)
   - Provided by GitHub Actions
   - Used for: Creating releases, commenting, labeling

2. **PyPI Trusted Publishing** (Configuration needed)
   - No secret required
   - Setup: https://docs.pypi.org/trusted-publishers/
   - Configure in PyPI project settings

### Optional Secrets

1. **`CODECOV_TOKEN`** (Optional)
   - For private repos or better reliability
   - Get from: https://codecov.io

---

## Branch Protection Rules

### Recommended for `main` branch:

```yaml
Required status checks:
  - Test (Python 3.11)
  - Test (Python 3.12)
  - Code Quality
  - Coverage
  - Build Distribution

Require branches to be up to date: true
Require review from Code Owners: true
Require linear history: true
```

### Recommended for `develop` branch:

```yaml
Required status checks:
  - Test (Python 3.11)
  - Code Quality

Require branches to be up to date: false
```

---

## Local Testing

### Run tests locally:
```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Specific team tests
make teamA-test  # Parser
make teamB-test  # Schema
make teamC-test  # Actions
make teamD-test  # FraiseQL
make teamE-test  # CLI
```

### Run code quality checks:
```bash
# Linting
make lint

# Formatting
make format

# Type checking
make typecheck

# Coverage
make coverage
```

### Test build:
```bash
# Build package locally
uv pip install build
uv run python -m build

# Check package
uv pip install twine
uv run twine check dist/*
```

---

## Troubleshooting

### CI Tests Failing

1. **Database connection issues**:
   - Check PostgreSQL service health
   - Verify `DATABASE_URL` environment variable
   - Ensure port 5432 is accessible

2. **Dependency issues**:
   - Clear cache: Delete `.venv` and `~/.cache/uv`
   - Reinstall: `uv pip install -e ".[dev]"`

3. **Import errors**:
   - Ensure package is installed in editable mode
   - Check `PYTHONPATH` includes project root

### Version Check Failing

1. **Version mismatch**:
   ```bash
   python scripts/version.py bump patch
   ```

2. **Invalid format**:
   - Must be `MAJOR.MINOR.PATCH`
   - No `v` prefix in VERSION file

### Release Failing

1. **Tag format**:
   - Must be `v*.*.*` (e.g., `v0.5.0`)
   - Must match VERSION file

2. **PyPI publishing**:
   - Verify Trusted Publishing is configured
   - Check permissions: `id-token: write`

### CodeQL False Positives

- Review in Security tab
- Dismiss false positives with justification
- Update queries if needed

---

## Monitoring & Metrics

### Where to find results:

1. **Test Results**: Actions tab → CI workflow → Test job
2. **Coverage**: Codecov.io dashboard
3. **Security**: Security tab → Code scanning alerts
4. **Dependencies**: Dependabot tab
5. **Releases**: Releases section
6. **PyPI**: https://pypi.org/project/specql-generator/

### Key Metrics:

- ✅ **Test Pass Rate**: 100% (1105/1105 passing)
- ✅ **Python Support**: 3.11, 3.12
- ✅ **Coverage**: Tracked via Codecov
- ✅ **Security**: CodeQL weekly scans
- ✅ **Dependencies**: Auto-updated weekly

---

## Contributing

When contributing, ensure:

1. ✅ All tests pass locally (`make test`)
2. ✅ Code is formatted (`make format`)
3. ✅ Linting passes (`make lint`)
4. ✅ Version bumped if needed (`make version-patch`)
5. ✅ CHANGELOG.md updated
6. ✅ CI checks pass on PR

---

## Maintenance

### Weekly Tasks:
- ✅ Review Dependabot PRs
- ✅ Check CodeQL alerts
- ✅ Monitor test reliability

### Monthly Tasks:
- ✅ Review stale issues/PRs
- ✅ Update documentation
- ✅ Security audit

### Release Tasks:
- ✅ Update CHANGELOG
- ✅ Run full test suite
- ✅ Create release tag
- ✅ Verify PyPI publication

---

## Contact

For CI/CD issues:
- GitHub Issues: https://github.com/fraiseql/specql/issues
- Label: `ci-cd`

---

**Last Updated**: 2025-11-17
**CI/CD Version**: 1.0
**Status**: ✅ Production Ready
