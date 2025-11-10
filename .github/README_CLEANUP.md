# Pre-Public Cleanup Resources

This directory contains guides and tools to prepare SpecQL for public release.

## 📚 Documents

### 1. **PRE_PUBLIC_CLEANUP.md** (Comprehensive Checklist)
   - **Use**: Human-guided manual cleanup
   - **Format**: Detailed 18-section checklist
   - **Covers**: Security, code quality, docs, legal, testing
   - **Time**: 4-8 hours for thorough review

### 2. **AI_CLEANUP_PROMPT.md** (Claude Code Prompt)
   - **Use**: AI-assisted automated cleanup
   - **Format**: Structured prompt for Claude
   - **Covers**: Same as manual checklist but AI-optimized
   - **Time**: 1-2 hours with AI assistance

### 3. **VERSIONING_QUICK_REF.md** (Version Management)
   - **Use**: Quick reference for versioning commands
   - **Format**: Command cheatsheet
   - **Covers**: SemVer, releases, version bumping

### 4. **RELEASE_CHECKLIST.md** (Release Process)
   - **Use**: Step-by-step release guide
   - **Format**: Sequential checklist
   - **Covers**: Pre-release, version bump, commit, tag, push

## 🔧 Scripts

### `../scripts/pre_public_check.sh` (Automated Checks)
   - **Use**: Automated verification before public release
   - **Run**: `bash scripts/pre_public_check.sh`
   - **Checks**:
     - Security: Scans for secrets, sensitive data
     - Tests: Runs full test suite
     - Linting: Checks code style
     - Type checking: Runs mypy
     - Documentation: Verifies required files
     - Version: Checks consistency
     - Git: Checks for uncommitted changes
     - Cleanup: Scans for unwanted files

## 🚀 Recommended Workflow

### Option A: Human-Led Cleanup
```bash
# 1. Read the checklist
cat .github/PRE_PUBLIC_CLEANUP.md

# 2. Create cleanup branch
git checkout -b pre-public-cleanup

# 3. Work through checklist sections
# ... make changes ...

# 4. Run automated checks
bash scripts/pre_public_check.sh

# 5. Create PR
gh pr create --title "Pre-public release cleanup"
```

### Option B: AI-Assisted Cleanup
```bash
# 1. Open Claude Code

# 2. Copy and send this prompt:
cat .github/AI_CLEANUP_PROMPT.md

# 3. Review AI's findings and changes

# 4. Run automated checks
bash scripts/pre_public_check.sh

# 5. Create PR for human review
```

### Option C: Hybrid Approach (Recommended)
```bash
# 1. Run automated checks to get baseline
bash scripts/pre_public_check.sh

# 2. Use AI for initial pass
# Send AI_CLEANUP_PROMPT.md to Claude

# 3. Manually review critical sections
# Focus on: Security, Legal, Documentation

# 4. Run checks again
bash scripts/pre_public_check.sh

# 5. Final human review
cat .github/PRE_PUBLIC_CLEANUP.md
```

## ⚠️ Critical Sections (Manual Review Required)

Even with AI assistance, these MUST have human review:

1. **Security Audit** - Check for secrets, credentials
2. **Git History** - Review for sensitive commits
3. **License Compliance** - Legal review
4. **Documentation Accuracy** - Verify claims are true
5. **Fresh Install Test** - Actually test the README

## 📊 Success Metrics

Before making repository public:

- [ ] `scripts/pre_public_check.sh` passes with 0 errors
- [ ] Manual security audit completed
- [ ] Fresh installation tested
- [ ] At least one other person reviewed changes
- [ ] Version bumped appropriately (consider v1.0.0)
- [ ] CHANGELOG.md updated
- [ ] All PR reviews approved

## 🎯 Timeline

| Phase | Duration | Type |
|-------|----------|------|
| Automated checks | 5-10 min | Script |
| AI-assisted cleanup | 1-2 hours | AI + Human |
| Manual review | 2-4 hours | Human |
| Testing | 1-2 hours | Human |
| PR review | 1-2 days | Human |
| **Total** | **3-5 days** | **Mixed** |

## 🔗 Related Documentation

- **VERSION** - Current version number
- **CHANGELOG.md** - Release history
- **docs/VERSIONING.md** - Detailed versioning guide
- **README.md** - Main project documentation

---

## Quick Commands

```bash
# Show current version
make version

# Run automated checks
bash scripts/pre_public_check.sh

# Run all quality checks
make test && make lint && make typecheck

# Create cleanup branch
git checkout -b pre-public-cleanup

# Bump to v1.0.0 for public launch
python scripts/version.py set 1.0.0
```

---

**When in doubt, review manually. Security is paramount.**

**Last Updated**: 2025-11-10
