# Pre-Public Release Cleanup Prompt

**Purpose**: Clean and audit the SpecQL repository before making it public.

**Target Audience**: AI Assistant (Claude Code) or Developer performing final review

---

## 🎯 Objective

Perform a comprehensive audit and cleanup of the SpecQL repository to ensure it's ready for public release. Remove any sensitive information, improve documentation, and ensure professional presentation.

---

## 📋 Security & Privacy Audit

### 1. Scan for Sensitive Information

**Task**: Search the entire codebase for potentially sensitive data.

```bash
# Search for common sensitive patterns
rg -i "password|secret|api_key|token|private_key|credentials" --type yaml --type py --type md
rg -i "TODO|FIXME|XXX|HACK" --type py --type md
rg "@evolution-digitale\.fr" --type-not sql  # Check for personal emails
rg "lionel|hamayon" -i --type-not sql --type-not md  # Personal references
```

**Check**:
- [ ] No hardcoded passwords, API keys, or secrets
- [ ] No internal company references (except in author fields)
- [ ] No personal email addresses in code (README/LICENSE are OK)
- [ ] No database connection strings with credentials
- [ ] No internal URLs or hostnames
- [ ] No proprietary business logic or client-specific code

### 2. Review Git History

**Task**: Check git history for accidentally committed secrets.

```bash
# Review recent commits
git log --all --pretty=format:"%h %s" --since="6 months ago"

# Check for large files that shouldn't be in repo
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {print substr($0,6)}' | sort -n -k2 | tail -20
```

**Check**:
- [ ] No commits with sensitive data in history
- [ ] No large binary files or databases accidentally committed
- [ ] All commit messages are professional and appropriate
- [ ] No internal issue tracker references that shouldn't be public

### 3. Environment & Configuration Files

**Task**: Verify no sensitive config files are tracked.

```bash
# Check for environment files
find . -name "*.env*" -o -name "*.config.local.*" -o -name "credentials.*"
```

**Check**:
- [ ] `.env` files are in `.gitignore`
- [ ] No example configs contain real credentials
- [ ] All config files use placeholder values
- [ ] `.gitignore` is comprehensive

---

## 🧹 Code Quality Cleanup

### 4. Remove Dead Code & TODOs

**Task**: Clean up experimental code and incomplete features.

```bash
# Find TODO comments
rg "TODO|FIXME|XXX|HACK|NOTE:" --type py

# Find unused imports
ruff check --select F401 src/ tests/

# Find unused variables
ruff check --select F841 src/ tests/
```

**Actions**:
- [ ] Resolve or remove all TODO/FIXME comments
- [ ] Remove commented-out code blocks
- [ ] Delete unused imports and variables
- [ ] Remove experimental/prototype code
- [ ] Archive or delete incomplete features

### 5. Test Coverage & Quality

**Task**: Ensure comprehensive test coverage.

```bash
# Run full test suite
make test

# Generate coverage report
make coverage

# Check for skipped/xfail tests
rg "@pytest\.(skip|xfail)" tests/
```

**Check**:
- [ ] All tests passing
- [ ] Test coverage > 80% (or document why not)
- [ ] No permanently skipped tests without good reason
- [ ] Integration tests work with example data
- [ ] No hardcoded test credentials

### 6. Code Style Consistency

**Task**: Ensure consistent code formatting.

```bash
# Format all code
make format

# Run linting
make lint

# Type checking
make typecheck
```

**Check**:
- [ ] All code properly formatted (black)
- [ ] No linting errors (ruff)
- [ ] Type hints present and passing (mypy)
- [ ] Consistent naming conventions throughout

---

## 📚 Documentation Audit

### 7. README & Getting Started

**Task**: Review and improve main documentation.

**Check README.md**:
- [ ] Clear project description and value proposition
- [ ] Accurate feature list (no vaporware)
- [ ] Working installation instructions
- [ ] Quick start example that actually works
- [ ] Link to comprehensive documentation
- [ ] Clear licensing information
- [ ] Contributing guidelines (if accepting contributions)
- [ ] Support/contact information
- [ ] No internal references or assumptions

**Test**:
```bash
# Follow your own README from scratch
# Can a new user actually get started?
```

### 8. Documentation Files

**Task**: Review all markdown files.

```bash
# Find all documentation
find . -name "*.md" -not -path "./.*" | sort
```

**Check each file**:
- [ ] Up-to-date and accurate
- [ ] No internal references
- [ ] Professional tone
- [ ] Proper grammar and spelling
- [ ] Working links (no broken references)
- [ ] Code examples actually work

**Files to review**:
- [ ] README.md
- [ ] GETTING_STARTED.md
- [ ] CHANGELOG.md
- [ ] LICENSE (if exists)
- [ ] CONTRIBUTING.md (if exists)
- [ ] docs/*.md

### 9. Code Comments & Docstrings

**Task**: Review inline documentation.

```bash
# Find files with few/no docstrings
find src/ -name "*.py" -exec sh -c 'grep -L "\"\"\"" "$1" && echo "$1"' _ {} \;
```

**Check**:
- [ ] Public APIs have docstrings
- [ ] Complex logic is explained
- [ ] No offensive or unprofessional comments
- [ ] No internal-only context required
- [ ] Comments add value (not just restating code)

---

## 🏗️ Repository Structure

### 10. File Organization

**Task**: Ensure clean repository structure.

```bash
# Check for common issues
ls -la  # Check for dotfiles that shouldn't be public
find . -name "*.pyc" -o -name "__pycache__" -o -name ".DS_Store"
```

**Check**:
- [ ] Logical directory structure
- [ ] No unnecessary files in root directory
- [ ] No build artifacts committed
- [ ] No IDE-specific files (except in .gitignore)
- [ ] Clear separation of source, tests, docs
- [ ] No empty directories (or they're intentional)

### 11. Dependencies & Requirements

**Task**: Review and minimize dependencies.

```bash
# Review dependencies
cat pyproject.toml | grep -A20 "dependencies"
```

**Check**:
- [ ] All dependencies are necessary
- [ ] Version pins are appropriate
- [ ] No internal/private packages
- [ ] License-compatible dependencies
- [ ] Known secure versions (no known CVEs)
- [ ] Optional dependencies properly marked

### 12. GitHub-Specific Files

**Task**: Ensure GitHub features are properly configured.

**Check**:
- [ ] `.github/workflows/*.yml` - All workflows functional
- [ ] `.github/ISSUE_TEMPLATE/` - If present, are they appropriate?
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` - If present, is it useful?
- [ ] `.github/CODEOWNERS` - Correct for public repo?
- [ ] `.github/dependabot.yml` - Configure security updates?

---

## ⚖️ Legal & Licensing

### 13. License Compliance

**Task**: Ensure proper licensing.

**Check**:
- [ ] LICENSE file exists and is appropriate (MIT recommended)
- [ ] Copyright notices are correct
- [ ] Third-party licenses are acknowledged
- [ ] No GPL code (if using permissive license)
- [ ] Author information is accurate

### 14. Attribution & Credits

**Task**: Proper attribution for external code.

**Check**:
- [ ] Third-party code is properly attributed
- [ ] Inspiration/references are acknowledged
- [ ] No plagiarized documentation
- [ ] Contributors are credited (if applicable)

---

## 🎨 Branding & Presentation

### 15. Project Identity

**Task**: Consistent branding and messaging.

**Check**:
- [ ] Project name is consistent everywhere
- [ ] Description/tagline is compelling and accurate
- [ ] Version numbers are correct and consistent
- [ ] Links to repository/documentation work
- [ ] No "under construction" or "coming soon" without dates

### 16. Visual Polish

**Task**: Professional appearance.

**Check**:
- [ ] README has badges (version, license, build status)
- [ ] Code examples are syntax-highlighted
- [ ] Screenshots/diagrams are clear and professional (if any)
- [ ] Consistent markdown formatting
- [ ] Proper emoji usage (not excessive)

---

## 🚀 Pre-Release Testing

### 17. Fresh Installation Test

**Task**: Verify clean install process.

```bash
# In a temporary directory
cd /tmp
git clone https://github.com/fraiseql/specql.git
cd specql

# Follow README exactly
# Does it work?
```

**Test**:
- [ ] Clone works without authentication issues
- [ ] Installation instructions are complete
- [ ] Quick start example runs successfully
- [ ] Tests pass on fresh install
- [ ] No missing dependencies

### 18. Cross-Platform Check

**Task**: Verify compatibility.

**Check**:
- [ ] Works on Linux (primary platform)
- [ ] Works on macOS (if claimed)
- [ ] Works on Windows (if claimed)
- [ ] Python version requirements are documented
- [ ] No platform-specific hardcoded paths

---

## 📊 Final Checklist

### Pre-Public Release Final Review

- [ ] **Security**: No secrets, credentials, or sensitive data
- [ ] **Code Quality**: Tests pass, linting clean, type-safe
- [ ] **Documentation**: Accurate, complete, professional
- [ ] **Structure**: Organized, clean, no cruft
- [ ] **Legal**: Proper license, attributions, compliance
- [ ] **Branding**: Consistent naming, professional presentation
- [ ] **Testing**: Fresh install works, examples run
- [ ] **Git History**: No sensitive commits, professional messages
- [ ] **Dependencies**: All public, properly licensed, secure
- [ ] **GitHub Config**: Workflows work, settings appropriate

---

## 🔧 Automated Checks Script

Save this as `scripts/pre_public_check.sh`:

```bash
#!/bin/bash
set -e

echo "🔍 Running Pre-Public Release Checks..."

# Security checks
echo "📋 Checking for sensitive patterns..."
if rg -i "password|secret|api_key|token" --type yaml --type py 2>/dev/null; then
    echo "⚠️  WARNING: Potential secrets found!"
fi

# Code quality
echo "🧪 Running tests..."
make test

echo "🎨 Checking code style..."
make lint
make typecheck

# Documentation
echo "📚 Checking documentation..."
if ! test -f README.md; then
    echo "❌ ERROR: README.md missing!"
    exit 1
fi

if ! test -f LICENSE; then
    echo "⚠️  WARNING: No LICENSE file!"
fi

# Version consistency
echo "🏷️  Checking version consistency..."
VERSION=$(cat VERSION)
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
if [ "$VERSION" != "$PYPROJECT_VERSION" ]; then
    echo "❌ ERROR: Version mismatch!"
    exit 1
fi

echo "✅ All automated checks passed!"
echo "📝 Review the manual checklist in .github/PRE_PUBLIC_CLEANUP.md"
```

---

## 📝 After Cleanup

Once all checks are complete:

1. **Create cleanup branch**:
   ```bash
   git checkout -b pre-public-cleanup
   ```

2. **Make all necessary changes**

3. **Test thoroughly**:
   ```bash
   bash scripts/pre_public_check.sh
   ```

4. **Create PR for review**:
   ```bash
   gh pr create --title "Pre-public release cleanup" --body "See .github/PRE_PUBLIC_CLEANUP.md"
   ```

5. **Final review by human maintainer**

6. **Merge and tag release**:
   ```bash
   git checkout main
   git merge pre-public-cleanup
   make version-major  # 0.1.0 -> 1.0.0 for public launch
   git tag -a v1.0.0 -m "Public release v1.0.0"
   git push origin main --tags
   ```

7. **Change repository visibility to Public** in GitHub settings

---

## 🎉 Ready for Public Release

After completing all steps, the repository is ready to be made public!

**Remember**: Once public, assume everything is permanent. Git history rewrites are difficult and disruptive.

---

**Last Updated**: 2025-11-10
**Maintained By**: FraiseQL Team
