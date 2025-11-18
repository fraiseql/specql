# Junior Engineer Guides - Complete Package

**Created**: 2025-11-18
**Purpose**: Help junior engineers fix all skipped/failing pattern tests
**Target**: 47 skipped + 6 failed → 100% passing (53 tests fixed)

---

## 📦 What's Included

### Quick Start (Start Here! ⭐)
- **[QUICK_START_FIRST_TEST_FIX.md](QUICK_START_FIRST_TEST_FIX.md)** (9KB)
  - Fix your first test in 30 minutes
  - Build confidence with immediate success
  - Learn the basic workflow
  - **Start here if you're new!**

### Main Index
- **[JUNIOR_GUIDES_INDEX.md](JUNIOR_GUIDES_INDEX.md)** (14KB)
  - Overview of all guides
  - Progress tracking
  - Success metrics
  - Learning resources

### Weekly Guides

#### Week 1: Foundation (Already Complete ✅)
- **[WEEK_01_JUNIOR_GUIDE.md](WEEK_01_JUNIOR_GUIDE.md)** (31KB)
  - Dependency management
  - Test infrastructure
  - Pattern testing basics
  - Computed columns (already working!)

#### Week 2: SCD Type 2 (6 Failing Tests)
- **[WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md](WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md)** (22KB)
  - Slowly Changing Dimensions
  - Version tracking
  - History tables
  - Point-in-time queries
  - **Fixes**: 6 failing tests → passing

#### Week 3: Temporal Patterns (18 Skipped Tests)
- **[WEEK_03_JUNIOR_GUIDE_TEMPORAL_PATTERNS.md](WEEK_03_JUNIOR_GUIDE_TEMPORAL_PATTERNS.md)** (22KB)
  - Non-overlapping date ranges
  - DATERANGE type
  - GIST indexes
  - EXCLUSION constraints
  - **Fixes**: 18 skipped tests → passing

#### Week 4: Validation Patterns (29 Skipped Tests)
- **[WEEK_04_JUNIOR_GUIDE_VALIDATION_PATTERNS.md](WEEK_04_JUNIOR_GUIDE_VALIDATION_PATTERNS.md)** (22KB)
  - Recursive dependency validation
  - Template inheritance
  - Recursive CTEs
  - JSONB operations
  - **Fixes**: 29 skipped tests → passing

---

## 🎯 How to Use These Guides

### For Complete Beginners

**Day 1**: Quick Start
```bash
# 1. Read quick start guide
cat QUICK_START_FIRST_TEST_FIX.md

# 2. Fix your first test (30 minutes)
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified -v

# 3. Celebrate! 🎉
```

**Day 2-7**: Follow Week 1 Guide (if needed)
```bash
cat WEEK_01_JUNIOR_GUIDE.md
# Complete dependency setup and test infrastructure
```

**Week 2**: SCD Type 2 Pattern
```bash
cat WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md
# Fix 6 failing tests
```

**Week 3**: Temporal Patterns
```bash
cat WEEK_03_JUNIOR_GUIDE_TEMPORAL_PATTERNS.md
# Fix 18 skipped tests
```

**Week 4**: Validation Patterns
```bash
cat WEEK_04_JUNIOR_GUIDE_VALIDATION_PATTERNS.md
# Fix 29 skipped tests
```

### For Experienced Developers

Skip to relevant week based on what needs fixing:
- **SCD Type 2 failing?** → Week 2 guide
- **Temporal tests skipped?** → Week 3 guide
- **Validation tests skipped?** → Week 4 guide

---

## 📊 Test Status Overview

### Current State
```bash
uv run pytest tests/unit/patterns/ -v --tb=no

Results:
✅ 15 passed   (computed columns, aggregate views)
❌ 6 failed    (SCD Type 2)
⏸️ 47 skipped  (18 temporal + 29 validation)
──────────────────────────────────
Total: 68 tests
Complete: 22% (15/68)
```

### After Week 2
```bash
✅ 21 passed   (+6 from SCD Type 2)
❌ 0 failed    (all fixed!)
⏸️ 47 skipped  (still need Week 3-4)
──────────────────────────────────
Complete: 31% (21/68)
```

### After Week 3
```bash
✅ 39 passed   (+18 from temporal patterns)
❌ 0 failed
⏸️ 29 skipped  (only validation left!)
──────────────────────────────────
Complete: 57% (39/68)
```

### After Week 4 (Final Goal)
```bash
✅ 68 passed   (+29 from validation patterns)
❌ 0 failed
⏸️ 0 skipped   (ALL DONE! 🎉)
──────────────────────────────────
Complete: 100% (68/68)
```

---

## 🎓 What You'll Learn

### PostgreSQL Skills
- ✅ Range types (DATERANGE, TSRANGE)
- ✅ GIST indexes for range queries
- ✅ EXCLUSION constraints
- ✅ Computed columns (GENERATED ALWAYS AS)
- ✅ Recursive CTEs (WITH RECURSIVE)
- ✅ JSONB operations
- ✅ Triggers and functions
- ✅ Partial indexes (WHERE clause)

### Python Skills
- ✅ Dataclasses
- ✅ Type hints (Optional, List, Dict)
- ✅ Pattern implementation
- ✅ Code generation
- ✅ AST manipulation

### Testing Skills
- ✅ pytest basics
- ✅ Fixtures
- ✅ Parametrized tests
- ✅ Test-driven development
- ✅ Debugging test failures

### Software Engineering
- ✅ Design patterns
- ✅ Code organization
- ✅ Documentation
- ✅ Git workflow
- ✅ Incremental development

---

## 📚 Guide Features

### Each Guide Includes

1. **Clear Learning Objectives**
   - What you'll accomplish
   - What you'll learn
   - Prerequisites

2. **Real-World Examples**
   - Concrete use cases
   - Business scenarios
   - Practical applications

3. **Step-by-Step Instructions**
   - Copy-paste friendly code
   - Command-line examples
   - Expected outputs

4. **Concept Explanations**
   - Why things work this way
   - SQL fundamentals
   - PostgreSQL features

5. **Common Mistakes Section**
   - What goes wrong
   - How to fix it
   - How to avoid it

6. **Troubleshooting Guide**
   - Debug strategies
   - Error messages explained
   - Solutions provided

7. **Success Criteria**
   - Checkboxes to track progress
   - Clear completion goals
   - Verification commands

---

## 🛠️ Required Tools

### Software
```bash
# Python 3.11+
python --version  # Should be 3.11 or higher

# uv package manager
uv --version

# PostgreSQL (for integration tests)
psql --version

# Git
git --version
```

### Installation
```bash
# Clone repository
git clone <repo-url>
cd specql

# Install dependencies
uv pip install -e ".[dev,all]"

# Verify installation
uv run pytest tests/unit/patterns/ --collect-only
```

### Optional but Helpful
```bash
# VS Code (great for searching/editing)
code --version

# Docker (for test databases)
docker --version

# pytest-watch (auto-run tests)
uv pip install pytest-watch
```

---

## 🚀 Quick Reference Commands

### Running Tests
```bash
# All pattern tests
uv run pytest tests/unit/patterns/ -v

# Specific pattern
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py -v

# Single test
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_no_tracked_fields_specified -v

# With debug output
uv run pytest <test-path> -v -s

# Show test names only
uv run pytest tests/unit/patterns/ --collect-only -q
```

### Finding Code
```bash
# Find class definition
grep -r "class EntityDefinition" src/

# Find function
grep -r "def apply_pattern" src/

# Find pattern registration
grep -r "PATTERN_APPLIERS" src/
```

### Git Workflow
```bash
# Check status
git status

# See changes
git diff

# Stage changes
git add <file>

# Commit
git commit -m "feat: descriptive message"

# Push
git push
```

---

## 📈 Progress Tracking

### Weekly Checklist

#### Week 2: SCD Type 2
- [ ] Day 1: Entity model updated
- [ ] Day 2: Pattern applier implemented
- [ ] Day 3: DDL generation working
- [ ] Day 4: All 8 tests passing
- [ ] Week complete: 6 failing → 6 passing ✅

#### Week 3: Temporal Patterns
- [ ] Day 1: PostgreSQL ranges understood
- [ ] Day 2: Pattern class created
- [ ] Day 3: Table generator updated
- [ ] Day 4: Tests debugging
- [ ] Day 5: Advanced features
- [ ] Day 6: Integration testing
- [ ] Week complete: 18 skipped → 18 passing ✅

#### Week 4: Validation Patterns
- [ ] Days 1-2: Recursive dependencies
- [ ] Day 3: Integration tests
- [ ] Days 4-5: Template inheritance
- [ ] Week complete: 29 skipped → 29 passing ✅

### Overall Progress
- [ ] Quick start test fixed
- [ ] Week 1 foundation (if needed)
- [ ] Week 2 complete (6 tests)
- [ ] Week 3 complete (18 tests)
- [ ] Week 4 complete (29 tests)
- [ ] All 68 pattern tests passing 🎉

---

## 💡 Tips for Success

### 1. Start with Quick Start
Don't dive into complex guides first. Build confidence with quick win!

### 2. One Test at a Time
Don't try to fix multiple tests simultaneously. Focus = faster progress.

### 3. Read Tests First
Tests are the specification. They tell you exactly what to implement.

### 4. Use Debug Prints
When stuck, print everything. See what's actually happening.

### 5. Commit Often
Small commits = easy to undo if something breaks.

### 6. Take Breaks
Complex patterns are mentally demanding. Break them into sessions.

### 7. Ask Questions
Document your attempts. Makes it easier to get help.

---

## 🆘 Getting Help

### When Stuck

1. **Check the "Common Mistakes" section** in relevant guide
2. **Check the "Troubleshooting" section** in relevant guide
3. **Add debug output** to see what's happening
4. **Search for similar tests** that are passing
5. **Document what you tried** and ask for help

### Help Template
```markdown
**Test**: test_no_tracked_fields_specified
**Guide**: WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md
**Section**: Day 1, Step 4

**What I'm trying to do**:
Add tracked_fields attribute to EntityDefinition

**What I tried**:
1. Added `tracked_fields: Optional[list[str]] = None` to class
2. Imported Optional from typing

**What happened**:
Still getting AttributeError

**Debug output**:
[paste relevant output]

**Question**:
Did I add the attribute in the right place? Should it be inside the dataclass?
```

---

## 🎉 Celebration Milestones

### First Test Passing
🎉 **Milestone 1**: You fixed your first test!
- You understand the workflow
- You can read test failures
- You know how to implement fixes

### Week 2 Complete
🎉 **Milestone 2**: SCD Type 2 pattern complete!
- You understand version tracking
- You can generate complex DDL
- 6 tests fixed!

### Week 3 Complete
🎉 **Milestone 3**: Temporal patterns complete!
- You mastered PostgreSQL ranges
- You understand GIST indexes
- 18 more tests fixed!

### Week 4 Complete
🎉 **Milestone 4**: Validation patterns complete!
- You mastered recursive CTEs
- You understand complex SQL
- 29 more tests fixed!

### All Tests Passing
🎉🎉🎉 **FINAL MILESTONE**: 100% test coverage!
- 68/68 tests passing
- Production-ready patterns
- You're now a PostgreSQL + code generation expert!

---

## 📞 Support Resources

### Documentation
- PostgreSQL Docs: https://www.postgresql.org/docs/current/
- pytest Docs: https://docs.pytest.org/
- Python Docs: https://docs.python.org/3/

### In-Repository Help
- `README.md` - Project overview
- `docs/architecture/` - Design decisions
- `tests/unit/patterns/README.md` - Pattern testing guide
- These guides!

---

## 🎯 Final Goal

```bash
uv run pytest tests/unit/patterns/ -v

# Target output:
============================== 68 passed in 15.23s ==============================

✅ All pattern tests passing!
✅ Production-ready implementation!
✅ You're now an expert!
```

---

## 📝 Document Index

| Document | Size | Purpose | Start Here? |
|----------|------|---------|-------------|
| **QUICK_START_FIRST_TEST_FIX.md** | 9KB | Fix first test in 30 min | ⭐ YES |
| **JUNIOR_GUIDES_INDEX.md** | 14KB | Overview and navigation | Second |
| **WEEK_01_JUNIOR_GUIDE.md** | 31KB | Foundation (if needed) | Optional |
| **WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md** | 22KB | Fix 6 failing tests | Required |
| **WEEK_03_JUNIOR_GUIDE_TEMPORAL_PATTERNS.md** | 22KB | Fix 18 skipped tests | Required |
| **WEEK_04_JUNIOR_GUIDE_VALIDATION_PATTERNS.md** | 22KB | Fix 29 skipped tests | Required |

**Total**: 140KB of detailed, beginner-friendly guides

---

## 🚀 Getting Started NOW

```bash
# 1. Read quick start (5 minutes)
cat QUICK_START_FIRST_TEST_FIX.md

# 2. Run current test status
uv run pytest tests/unit/patterns/ -v --tb=no

# 3. Fix your first test (30 minutes)
#    Follow QUICK_START_FIRST_TEST_FIX.md step-by-step

# 4. Read Week 2 guide
cat WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md

# 5. Fix remaining SCD Type 2 tests (3-4 days)

# 6. Continue with Weeks 3-4

# 7. Celebrate 100% test coverage! 🎉
```

---

**Good luck! You've got everything you need to succeed! 💪**

**Remember**: Every expert was once a beginner. These guides break down complex topics into manageable steps. Take your time, test incrementally, and celebrate every small win! 🎉

---

**Questions?** Re-read the relevant guide section or check the troubleshooting section first. You've got this! 🚀
