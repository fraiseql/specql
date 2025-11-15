# SpecQL v0.4.0-alpha Release Checklist

**Date Created**: 2025-11-15
**Total TODO/FIXME Comments**: 393 lines across 159 files
**Estimated Time**: 8-12 hours
**Status**: Ready for Execution

---

## 📊 Current State Summary

### TODO Comment Analysis
- **Total Files with TODOs**: 159
- **Total TODO Lines**: 393
- **Critical TODOs**: 8 (must fix before release)
- **Important TODOs**: 85 (create GitHub issues)
- **Outdated TODOs**: 25 (remove)
- **Deferred TODOs**: 13 (keep with clear post-alpha marking)

### Repository Status
- **Current Branch**: pre-public-cleanup
- **GitHub Actions**: 4 workflows configured
- **Version Files**: Need update to 0.4.0-alpha
- **Repository Visibility**: Currently private

---

## 🎯 High Priority Tasks (Do First)

### Phase 1: Verify Infrastructure (30-45 minutes)
- [ ] **Verify GitHub Actions Workflows**
  - Review `.github/workflows/tests.yml`, `code-quality.yml`, `version-check.yml`, `release.yml`
  - Ensure all workflows are production-ready with proper triggers and permissions

- [ ] **Test Workflows Locally**
  ```bash
  uv run pytest --tb=short
  uv run ruff check src/ tests/
  uv run ruff format --check src/ tests/
  uv run mypy src/
  ```

### Phase 2: Create Release Documentation (60 minutes)
- [ ] **Create CHANGELOG.md**
  - Use [Keep a Changelog](https://keepachangelog.com/) format
  - Include all features from completion reports (WEEK_12-17 reports)
  - Document known limitations and alpha status
  - Add installation instructions for alpha

### Phase 3: Fix Critical TODOs (2-3 hours)
These 8 TODOs block core functionality and must be fixed:

**Core Generator Issues:**
- [ ] `src/generators/actions/action_orchestrator.py:75` - Support multiple actions per entity
- [ ] `src/generators/actions/step_compilers/insert_compiler.py:53` - Schema lookup for table names
- [ ] `src/generators/actions/impact_metadata_compiler.py:126` - Cross-schema support

**Parser Issues:**
- [ ] `src/parsers/plpgsql/function_analyzer.py:64` - Table impact analysis
- [ ] `src/parsers/plpgsql/function_analyzer.py:214` - DELETE statement parsing

**CLI Issues:**
- [ ] `src/cli/generate.py:48` - Convert impact dict to ActionImpact

**Security Issues:**
- [ ] `src/cicd/llm_recommendations.py:35` - Remove hardcoded API key placeholder

---

## 🔧 Medium Priority Tasks (Do Next)

### Phase 4: Clean Up Codebase (3-4 hours)
- [ ] **Create GitHub Issues for Important TODOs** (85 items)
  - Action/step compilation enhancements (15 items)
  - Java/Spring Boot generation (8 items)
  - Rust/Diesel generation (5 items)
  - TypeScript/Prisma generation (3 items)
  - Parser improvements (10 items)
  - CLI enhancements (12 items)
  - CI/CD pipeline generation (8 items)
  - Infrastructure & performance (8 items)
  - Testing & integration (8 items)

- [ ] **Remove Outdated Comments** (25 items)
  - Debug print statements (18 items) - remove from production code
  - Outdated TODOs (7 items) - remove irrelevant comments

- [ ] **Update Deferred TODOs** (13 items)
  - Mark with clear post-alpha wording
  - Add issue references where applicable

### Phase 5: Version and Tag (30 minutes)
- [ ] **Update Version Files**
  ```bash
  # Update pyproject.toml
  version = "0.4.0-alpha"

  # Update VERSION file
  echo "0.4.0-alpha" > VERSION
  ```

- [ ] **Update README.md**
  - Add alpha notice at top
  - Update status section with current metrics
  - Add community links (GitHub issues only, no Discord yet)

- [ ] **Create Git Tag**
  ```bash
  git tag -a v0.4.0-alpha -m "Release v0.4.0-alpha - First Public Alpha"
  git push origin v0.4.0-alpha
  ```

---

## 🚀 High Priority Tasks (Do Last)

### Phase 6: Make Repository Public (15 minutes)
- [ ] **Pre-Publication Checklist**
  - Verify no sensitive information in git history
  - Check .gitignore is comprehensive
  - Ensure working directory is clean
  - Confirm all tests pass

- [ ] **Make Repository Public**
  ```bash
  gh repo edit fraiseql/specql --visibility public
  ```

- [ ] **Configure Repository**
  - Add topics: code-generation, postgresql, graphql, yaml, java, rust, typescript
  - Enable issues and discussions (if ready)

- [ ] **Verify Release Creation**
  - Confirm GitHub Actions created release automatically
  - Verify release is marked as pre-release
  - Check release notes extracted from CHANGELOG.md

### Phase 7: Community Setup (30 minutes)
- [ ] **Create Community Issues**
  - Welcome/Getting Started help issue
  - Bug reports template issue
  - Feature requests issue

- [ ] **Update Community Links**
  - Remove placeholder Discord/Discussion links
  - Add GitHub issues links for community engagement

---

## 📋 Post-Release Tasks (Optional)

### Phase 8: Development Setup (15 minutes)
- [ ] **Create Development Branch**
  ```bash
  git checkout -b develop
  git push -u origin develop
  ```

- [ ] **Document Release Postmortem**
  - Create `docs/releases/v0.4.0-alpha-postmortem.md`
  - Record timeline, successes, improvements needed

---

## ✅ Success Criteria

### Technical Requirements
- [ ] All GitHub Actions workflows passing
- [ ] CHANGELOG.md complete and accurate
- [ ] All critical TODOs fixed and tested
- [ ] Version updated to 0.4.0-alpha in all files
- [ ] Git tag v0.4.0-alpha created and pushed
- [ ] Repository visibility set to public
- [ ] GitHub release created automatically as pre-release

### Code Quality Requirements
- [ ] All tests passing (`uv run pytest`)
- [ ] Linting passing (`uv run ruff check`)
- [ ] Type checking passing (`uv run mypy`)
- [ ] No debug prints in production code
- [ ] No critical TODOs remaining
- [ ] All remaining TODOs clearly marked as deferred

### Community Requirements
- [ ] Repository topics configured for discoverability
- [ ] Initial community issues created
- [ ] README has clear alpha notice and community links
- [ ] No sensitive data exposed in public repository

---

## 📊 Progress Tracking

| Phase | Task | Status | Time Estimate | Actual Time |
|-------|------|--------|---------------|-------------|
| 1 | Verify GitHub Actions | ⏳ Pending | 30 min | |
| 2 | Create CHANGELOG.md | ⏳ Pending | 60 min | |
| 3 | Fix Critical TODOs | ⏳ Pending | 2-3 hours | |
| 4 | Clean Up Codebase | ⏳ Pending | 3-4 hours | |
| 5 | Version and Tag | ⏳ Pending | 30 min | |
| 6 | Make Repository Public | ⏳ Pending | 15 min | |
| 7 | Community Setup | ⏳ Pending | 30 min | |
| 8 | Post-Release Tasks | ⏳ Pending | 15 min | |

**Total Estimated Time**: 8-12 hours
**Total Actual Time**: TBD

---

## 🚨 Risk Mitigation

### Common Issues and Solutions

**GitHub Actions Failing:**
- Test locally first: `uv run pytest --tb=short`
- Check Python version matches CI (3.11+)
- Verify dependencies: `uv sync --frozen`

**Version Consistency Check Fails:**
- Ensure VERSION file and pyproject.toml match
- Both should show: `0.4.0-alpha`
- Re-tag if needed: `git tag -f v0.4.0-alpha`

**CHANGELOG Format Invalid:**
- Must have exact format: `## [0.4.0-alpha] - 2025-11-15`
- Workflow extracts content between version headers

**Too Many TODOs Overwhelming:**
- Focus on critical first (8 items)
- Batch create GitHub issues for important ones
- Remove obviously outdated comments quickly
- Leave non-critical TODOs for post-alpha

---

## 📞 Getting Help

1. **Check existing documentation**: ALPHA_RELEASE_IMPLEMENTATION_PLAN.md has detailed steps
2. **Review TODO cleanup plan**: ALPHA_RELEASE_TODO_CLEANUP_PLAN.md has categorized TODOs
3. **Test locally first**: Always verify changes work before pushing
4. **Use GitHub CLI docs**: `gh help` for repository management
5. **Ask for clarification**: Better to ask than guess on complex steps

---

**Next Action**: Start with Phase 1 - Verify GitHub Actions workflows are ready for production use.