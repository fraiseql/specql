# Quick Start: Alpha Release Workflow

**TL;DR**: 3 weeks, 16-21 hours total, to go from current state to public v0.4.0-alpha

**SpecQL**: Multi-language backend code generator (PostgreSQL + Java + Rust + TypeScript)

---

## 🎯 Current State

```bash
# What's done ✅
✅ CHANGELOG.md (complete)
✅ GitHub Actions (4 workflows)
✅ Tests (96%+ coverage)
✅ Documentation (50+ files)

# What needs fixing ⚠️
⚠️ VERSION: "0.4.0" → "0.4.0-alpha"
⚠️ pyproject.toml: "0.4.0" → "0.4.0-alpha"

# What's missing ❌
❌ README alpha notice
❌ TODO cleanup (393 lines)
❌ Git tag (v0.4.0-alpha)
❌ Public repository
❌ Community setup
```

---

## 📅 3-Week Plan

### Week 18: Preparation (4-6h)
**File**: `WEEK_18_ALPHA_PREPARATION.md`

```bash
# Fix version files (30 min)
echo "0.4.0-alpha" > VERSION
# Edit pyproject.toml line 3: version = "0.4.0-alpha"
git commit -m "chore: update version to 0.4.0-alpha"

# Add README alpha notice (45 min)
# Add banner at top of README.md
git commit -m "docs: add alpha release notice to README"

# Verify workflows (1-2h)
uv run pytest --tb=short
uv run ruff check src/ tests/
uv run mypy src/

# Security audit (1-2h)
uv run bandit -r src/ -ll
git log --all --full-history '*secret*' '*password*' '*.env'
```

**Done when**: Version corrected, README updated, all tests pass

---

### Week 19: Cleanup (10-12h)
**File**: `WEEK_19_TODO_CLEANUP.md`

```bash
# Fix 8 critical TODOs (3-4h)
# 1. Multiple actions per entity
# 2. Schema lookup for table names
# 3. Cross-schema impact tracking
# 4. Table impact analysis
# 5. DELETE statement parsing
# 6. Impact dict conversion
# 7. Remove hardcoded API key
# 8. Additional critical items

# Create ~85 GitHub issues (3-4h)
# Use: scripts/create_todo_issues.sh
# Update code with issue references

# Remove outdated (1-2h)
# Remove 25 debug/obsolete TODOs

# Clarify deferred (1h)
# Update 13 TODOs to FUTURE(#N) format
```

**Done when**: Critical TODOs fixed, all enhancements tracked, codebase clean

---

### Week 20: Release (2-3h)
**File**: `WEEK_20_RELEASE_EXECUTION.md`

```bash
# Create git tag (15 min)
git tag -a v0.4.0-alpha -m "Release v0.4.0-alpha - First Public Alpha"
git push origin v0.4.0-alpha
# GitHub Actions auto-creates release

# Make public (30 min)
gh repo edit fraiseql/specql --visibility public
gh repo edit fraiseql/specql --add-topic "code-generation" # ... etc

# Community setup (45 min)
gh issue create --title "Welcome to SpecQL Alpha!" --pin
gh issue create --title "Bug Reports - v0.4.0-alpha"
gh issue create --title "Feature Requests & Roadmap"
# Create issue templates, labels

# Verify (30 min)
# Test clone, install, generation
# Document post-release report
```

**Done when**: Repository public, release created, community ready

---

## 🚀 Quick Commands

### Daily Checks (After Week 20)
```bash
# Check new issues
gh issue list --state open --limit 10

# Check bugs
gh issue list --label "bug" --state open

# Run tests
uv run pytest --tb=short
```

### Weekly Tasks
```bash
# Triage issues
gh issue list --state open | while read -r issue; do
  # Review, label, assign milestone
done

# Post community update
# Comment on pinned Welcome issue with weekly summary
```

---

## 📁 File Guide

| File | Purpose | When to Read |
|------|---------|--------------|
| `ALPHA_RELEASE_WEEKLY_SUMMARY.md` | High-level overview | Start here first |
| `WEEK_18_ALPHA_PREPARATION.md` | Detailed Week 18 plan | Before starting Week 18 |
| `WEEK_19_TODO_CLEANUP.md` | Detailed Week 19 plan | Before starting Week 19 |
| `WEEK_20_RELEASE_EXECUTION.md` | Detailed Week 20 plan | Before starting Week 20 |
| `WEEK_21_POST_ALPHA_ITERATION.md` | Post-release workflows | After Week 20 done |
| `ALPHA_RELEASE_IMPLEMENTATION_PLAN.md` | Original detailed plan | For deep dive |
| `ALPHA_RELEASE_CHECKLIST.md` | Quick checklist | For progress tracking |
| `ALPHA_RELEASE_TODO_CLEANUP_PLAN.md` | TODO categorization | Reference during Week 19 |

---

## ✅ Quick Checklist

### Pre-Flight Check
- [ ] Read `ALPHA_RELEASE_WEEKLY_SUMMARY.md`
- [ ] Understand 3-week plan
- [ ] Allocate time (5-7h/week for 3 weeks)
- [ ] Commit to schedule

### Week 18: Preparation
- [ ] VERSION → `0.4.0-alpha`
- [ ] pyproject.toml → `version = "0.4.0-alpha"`
- [ ] README alpha notice added
- [ ] All tests passing
- [ ] Security audit clean

### Week 19: Cleanup
- [ ] 8 critical TODOs fixed
- [ ] ~85 GitHub issues created
- [ ] 25 outdated TODOs removed
- [ ] 13 deferred TODOs clarified
- [ ] All tests still passing

### Week 20: Release
- [ ] Git tag v0.4.0-alpha created
- [ ] GitHub Release published (pre-release)
- [ ] Repository public
- [ ] 4 community issues created
- [ ] Post-release verified

### Week 21+: Iteration
- [ ] Daily issue monitoring
- [ ] Weekly community digest
- [ ] Triage workflow running
- [ ] Beta planning started

---

## 🆘 Emergency Contacts

### Common Issues

**Tests failing?**
```bash
uv run pytest -v  # See which tests fail
uv run pytest tests/path/to/test.py::test_name -v  # Run specific test
```

**Workflow failing?**
```bash
gh run list --limit 5  # See recent runs
gh run view <run-id>  # See logs
```

**Need to revert?**
```bash
git reset --hard HEAD~1  # Revert last commit (careful!)
git tag -d v0.4.0-alpha  # Delete local tag
git push --delete origin v0.4.0-alpha  # Delete remote tag
```

**Repository public but found issue?**
```bash
gh repo edit fraiseql/specql --visibility private  # Make private again
# Fix issue, then make public again
```

---

## 📊 Time Estimates

| Activity | Minimum | Expected | Maximum |
|----------|---------|----------|---------|
| Week 18 | 4h | 5h | 6h |
| Week 19 | 10h | 11h | 12h |
| Week 20 | 2h | 2.5h | 3h |
| **Total** | **16h** | **18.5h** | **21h** |

**Recommended pace**: 5-7 hours/week for 3 weeks

---

## 🎯 Success Indicators

You'll know you're done when:

✅ GitHub shows: https://github.com/fraiseql/specql (public)
✅ Latest release: v0.4.0-alpha (pre-release badge)
✅ README top: Alpha warning visible
✅ Issues tab: 4 pinned issues
✅ Stars: Starting to accumulate
✅ All tests: Passing (96%+ coverage)
✅ Your feeling: Proud and ready for feedback! 🎉

---

## 🚦 Getting Started NOW

```bash
# 1. Read the overview (5 min)
cat ALPHA_RELEASE_WEEKLY_SUMMARY.md

# 2. Read Week 18 plan (10 min)
cat WEEK_18_ALPHA_PREPARATION.md

# 3. Start with version fix (5 min)
echo "0.4.0-alpha" > VERSION
# Edit pyproject.toml: version = "0.4.0-alpha"

# 4. Commit
git add VERSION pyproject.toml
git commit -m "chore: update version to 0.4.0-alpha"

# 5. Continue with Week 18...
# See WEEK_18_ALPHA_PREPARATION.md for next steps
```

---

**Ready? Start with Week 18!** 🚀

See `WEEK_18_ALPHA_PREPARATION.md` for detailed instructions.

---

**Last Updated**: 2025-11-15
**Status**: Ready to Execute
**Next Action**: Fix version files (Week 18, Phase 1)
