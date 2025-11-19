# SpecQL v0.6.0 Quality Plan - Quick Reference Card

**Target Release**: Late January 2026 | **Current Phase**: Week 1 | **Confidence**: 85%

---

## 📅 5-Week Timeline at a Glance

```
Week 1: Test Infrastructure + Pattern Tests ██████░░░░░░░░░░░░░░░ 30%
Week 2: Pattern Implementation + CLI Polish ░░░░░░██████░░░░░░░░░░ 50%
Week 3: PrintOptim Validation + Performance ░░░░░░░░░░░░██████░░░░ 70%
Week 4: Security + Documentation             ░░░░░░░░░░░░░░░░██████ 90%
Week 5: Release                              ░░░░░░░░░░░░░░░░░░░░██ 100%
```

---

## 🎯 Daily Quick Commands

### **Check Overall Status**
```bash
# Run all tests
make test
# or: uv run pytest

# Check coverage
make test-coverage
# or: uv run pytest --cov=src --cov-report=term

# Lint & type check
make lint
# or: uv run ruff check src/ && uv run mypy src/
```

### **Test Specific Areas**
```bash
# Core tests only
uv run pytest tests/unit/core tests/unit/generators tests/unit/schema

# Pattern tests only
uv run pytest tests/unit/patterns -v

# CLI tests only
uv run pytest tests/unit/cli -v

# Integration tests
uv run pytest tests/integration -v

# Benchmarks
uv run pytest tests/benchmark -v
```

### **Check Dependencies**
```bash
# With core only
uv pip install -e ".[dev]"
uv run pytest  # Should skip optional feature tests

# With all features
uv pip install -e ".[all]"
uv run pytest  # Should run all tests
```

---

## 📊 Key Metrics Dashboard

| Metric | Current | Target | Command |
|--------|---------|--------|---------|
| **Tests** | 384 | 544+ | `pytest --collect-only \| grep collected` |
| **Coverage** | 87% | 95%+ | `pytest --cov=src --cov-report=term` |
| **Errors** | 60 | 0 | `pytest --collect-only 2>&1 \| grep ERROR` |
| **Pass Rate** | 100% (core) | 100% (all) | `pytest -q \| tail -1` |
| **Patterns** | 4/6 impl, 0 tested | 6/6, 112 tests | `pytest tests/unit/patterns -v` |

---

## 🚦 Quality Gates (Go/No-Go)

### **Week 1 Gate**: Test Infrastructure
```bash
# Must pass before Week 2:
uv run pytest --collect-only 2>&1 | grep -c "ERROR"
# Expected: 0

uv run pytest tests/unit/patterns --collect-only | grep -c "collected"
# Expected: 112 tests collected
```

### **Week 2 Gate**: Pattern Implementation
```bash
# Must pass before Week 3:
uv run pytest tests/unit/patterns -v
# Expected: 112 passed

find stdlib/actions stdlib/schema -name "*.yaml" | wc -l
# Expected: 16+ patterns (6 new ones)
```

### **Week 3 Gate**: PrintOptim Validation
```bash
# Must pass before Week 4:
specql generate entities/printoptim/*.yaml --output-schema=db/schema/printoptim/
./scripts/compare_schemas.sh original_printoptim generated_printoptim
# Expected: 95%+ automation
```

### **Week 4 Gate**: Performance & Security
```bash
# Must pass before Week 5:
uv run pytest tests/benchmark -v
# Expected: All benchmarks pass

bandit -r src/ -ll && pip-audit
# Expected: 0 vulnerabilities
```

### **Week 5 Gate**: Release Ready
```bash
# Must pass before release:
uv run pytest --cov=src
uv run ruff check src/
uv run mypy src/ --strict
mkdocs build --strict
uv build
# Expected: All clean ✅
```

---

## 🔍 Common Issues & Quick Fixes

### **Issue: Test Collection Errors**
```bash
# Symptom: ModuleNotFoundError: No module named 'pglast'
# Fix: Install optional dependencies
uv pip install -e ".[all]"

# Or mark tests to skip gracefully
# Add to conftest.py (see WEEK_01_IMPLEMENTATION_GUIDE.md)
```

### **Issue: Low Test Coverage**
```bash
# Find uncovered lines
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Focus on red/yellow files first
```

### **Issue: Slow Tests**
```bash
# Find slowest tests
uv run pytest --durations=10

# Profile specific test
uv run pytest tests/unit/patterns/test_something.py --profile
```

### **Issue: Failing Benchmark**
```bash
# Run specific benchmark with verbose output
uv run pytest tests/benchmark/test_schema_gen.py -v -s

# Profile to find bottleneck
uv run pytest tests/benchmark/test_schema_gen.py --profile
```

---

## 📝 Daily Checklist

### **Every Morning**
- [ ] Pull latest changes: `git pull origin main`
- [ ] Install dependencies: `uv pip install -e ".[all]"`
- [ ] Run tests: `make test`
- [ ] Check status: Review metrics vs. targets

### **During Development**
- [ ] Write test first (TDD)
- [ ] Run relevant tests: `pytest tests/unit/[area]`
- [ ] Check coverage: `pytest --cov=src/[module]`
- [ ] Commit often: Small, focused commits

### **Before Committing**
- [ ] Run full test suite: `make test`
- [ ] Lint: `make lint`
- [ ] Update docs if needed
- [ ] Write clear commit message

### **End of Day**
- [ ] Update todo list
- [ ] Note blockers/questions
- [ ] Push changes: `git push`
- [ ] Update status (if weekly report due)

---

## 🎯 This Week's Focus (Week 1)

### **Days 1-3: Test Infrastructure**
**Goal**: Fix 60 collection errors → 0
```bash
# Daily check:
uv run pytest --collect-only 2>&1 | grep -c "ERROR"
# Target: 60 → 40 → 20 → 0
```

### **Days 4-7: Pattern Tests**
**Goal**: Write 112 pattern tests
```bash
# Daily check:
uv run pytest tests/unit/patterns --collect-only | grep "collected"
# Target: 0 → 20 → 52 → 84 → 112
```

**Specific Tasks**:
- Day 1: Dependency reorganization
- Day 2: Pytest markers & graceful degradation
- Day 3: Coverage analysis
- Day 4: Pattern test infrastructure
- Day 5: Temporal pattern tests (20 tests)
- Day 6: Validation pattern tests (24 tests)
- Day 7: Schema pattern tests (20 tests)

---

## 🆘 When Stuck

### **Technical Blockers**
1. Check relevant guide:
   - Implementation details: `WEEK_01_IMPLEMENTATION_GUIDE.md`
   - Strategy/context: `QUALITY_EXCELLENCE_PLAN.md`
   - Metrics/gates: `SUCCESS_METRICS.md`

2. Search codebase for examples:
   ```bash
   # Find similar tests
   grep -r "pattern_test_example" tests/

   # Find similar implementations
   grep -r "PatternGenerator" src/
   ```

3. Run specific test in debug mode:
   ```bash
   uv run pytest tests/unit/path/to/test.py::TestClass::test_method -vv -s
   ```

### **Scope Creep**
- **Reminder**: Focus on v0.6.0 scope only
- **6 patterns**: Don't add new ones
- **Documentation**: Complete existing, don't expand
- **Performance**: Meet targets, don't over-optimize

### **Time Pressure**
- **Don't skip tests**: Tests prevent rework later
- **Don't skip documentation**: Users need docs
- **Don't skip quality gates**: Blocks downstream work
- **Do reduce scope**: Cut nice-to-haves if needed

---

## 📞 Communication

### **Daily Standup Format** (15 min)
```
Yesterday: [What I completed]
Today: [What I'm working on]
Blockers: [What's blocking me]
Metrics: [Key metric update]
```

### **Weekly Status Report** (see SUCCESS_METRICS.md for full template)
- Tests: X/544 passing
- Coverage: X%
- Patterns: X/6 complete
- Risks: [Any red flags]

### **Quality Gate Review**
- Run pre-gate checklist
- Present metrics vs. targets
- Go/no-go decision
- Document decision rationale

---

## 🎓 Key Principles

1. **Test-First (TDD)**: Write failing test → Implement → Refactor → Verify
2. **Quality Gates**: Don't proceed if gate fails
3. **Metrics-Driven**: Track daily progress vs. targets
4. **One Thing at a Time**: Complete current phase before next
5. **Document as You Go**: Don't defer documentation

---

## 🔗 Full Documentation Links

- **QUALITY_ROADMAP_SUMMARY.md**: Executive overview (this is your start)
- **QUALITY_EXCELLENCE_PLAN.md**: Strategic 6-phase plan
- **WEEK_01_IMPLEMENTATION_GUIDE.md**: Tactical day-by-day guide for Week 1
- **SUCCESS_METRICS.md**: Complete metrics and quality gates
- **QUICK_REFERENCE.md**: This card (daily use)

---

## ✅ Today's Checklist (Template)

**Date**: ___________ | **Day**: Week 1, Day ___

**Today's Goal**: ___________________________________

**Tasks**:
- [ ] Task 1: _______________
- [ ] Task 2: _______________
- [ ] Task 3: _______________

**Tests**:
- [ ] Tests written: ___
- [ ] Tests passing: ___
- [ ] Coverage: ___%

**Blockers**:
- _______________

**Notes**:
- _______________

---

**Print this card** | **Pin to wall** | **Reference daily**

Last Updated: 2025-11-18
