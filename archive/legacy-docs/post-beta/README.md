# Post-Beta Implementation Plan
## 8-Week Roadmap to 100% Test Coverage

**Current Status**: 1401/1508 tests passing (92.9%)
**Target**: 1508/1508 tests passing (100%)
**Timeline**: 8 weeks (40 work days)

---

## 📚 How to Use This Guide

This plan is designed for **junior engineers** to complete all 104 skipped tests. Each week has:

- ✅ Clear objectives
- 📋 Step-by-step instructions
- 🧪 Test commands to run
- 💡 Code examples
- 🎯 Success criteria

### Weekly Plans

1. [Week 1: Database Integration](./week1_database_integration.md) - **8 tests** (HIGH PRIORITY)
2. [Week 2: Rich Type Comments](./week2_rich_type_comments.md) - **13 tests** (HIGH PRIORITY)
3. [Week 3: Rich Type Indexes](./week3_rich_type_indexes.md) - **12 tests** (HIGH PRIORITY)
4. [Week 4: Schema Polish](./week4_schema_polish.md) - **19 tests** (MEDIUM PRIORITY)
5. [Week 5: FraiseQL GraphQL](./week5_fraiseql_graphql.md) - **7 tests** (MEDIUM PRIORITY)
6. [Week 6: Template Validation](./week6_template_validation.md) - **16 tests** (MEDIUM PRIORITY)
7. [Week 7: Dependency Validation](./week7_dependency_validation.md) - **6 tests** (LOW PRIORITY)
8. [Week 8: Reverse Engineering](./week8_reverse_engineering.md) - **30 tests** (LOW PRIORITY)

---

## 🎯 Weekly Progress Tracker

| Week | Focus Area | Tests | Status | Guide |
|------|-----------|-------|--------|-------|
| 1 | Database Integration | 8 | ✅ Guide Complete | [week1_database_integration.md](./week1_database_integration.md) |
| 2 | Rich Type Comments | 13 | ✅ Guide Complete | [week2_rich_type_comments.md](./week2_rich_type_comments.md) |
| 3 | Rich Type Indexes | 12 | ✅ Guide Complete | [week3_rich_type_indexes.md](./week3_rich_type_indexes.md) |
| 4 | Schema Polish | 19 | ✅ Guide Complete | [week4_schema_polish.md](./week4_schema_polish.md) |
| 5 | FraiseQL GraphQL | 7 | ✅ Guide Complete | [week5_fraiseql_graphql.md](./week5_fraiseql_graphql.md) |
| 8 | Reverse Engineering | 30 | ✅ Guide Complete | [week8_reverse_engineering.md](./week8_reverse_engineering.md) |

**Documentation Status**: 100% Complete (all 81 skipped tests documented) 🎉

---

## 🚦 Getting Started

### Prerequisites

Before starting Week 1, ensure you have:

1. **Development environment set up**:
   ```bash
   git clone https://github.com/your-org/specql.git
   cd specql
   uv sync
   ```

2. **Tests running**:
   ```bash
   uv run pytest --tb=short
   # Should see: 1401 passed, 104 skipped, 3 xfailed
   ```

3. **Understand the codebase**:
   - Read `CLAUDE.md` (project overview)
   - Read `GETTING_STARTED.md` (quick start)
   - Review `docs/architecture/` (technical design)

### Daily Workflow

Each day follows the **TDD cycle**:

1. **🔴 RED Phase**: Write/understand failing tests
2. **🟢 GREEN Phase**: Make tests pass (minimal implementation)
3. **🔧 REFACTOR Phase**: Clean up and optimize
4. **✅ QA Phase**: Verify everything works

### How to Track Progress

Run tests and save output:
```bash
# At start of week
uv run pytest --tb=no -q > week_N_start.txt

# At end of week
uv run pytest --tb=no -q > week_N_end.txt

# Compare
diff week_N_start.txt week_N_end.txt
```

---

## 💡 Tips for Junior Engineers

### Understanding Skipped Tests

Tests are skipped for three reasons:

1. **Post-beta enhancements** (100 tests): Features intentionally deferred
   ```python
   pytestmark = pytest.mark.skip(reason="deferred to post-beta")
   ```

2. **Database requirements** (8 tests): Need PostgreSQL running
   ```python
   @pytest.mark.skip(reason="Requires actual database connection")
   ```

3. **Future features** (3 tests): Not yet implemented
   ```python
   @pytest.mark.skip(reason="future enhancement")
   ```

### How to Unskip a Test

1. **Find the test file**:
   ```bash
   # Example: tests/unit/schema/test_comment_generation.py
   ```

2. **Remove the skip marker**:
   ```python
   # Before:
   pytestmark = pytest.mark.skip(reason="deferred to post-beta")

   # After:
   # pytestmark = pytest.mark.skip(reason="deferred to post-beta")  # REMOVED
   ```

3. **Run the test**:
   ```bash
   uv run pytest tests/unit/schema/test_comment_generation.py -v
   ```

4. **Make it pass**!

### Where to Add Code

Follow the **Team structure**:

- **Team A (Parser)**: `src/core/` - YAML parsing
- **Team B (Schema)**: `src/generators/schema/` - DDL generation
- **Team C (Actions)**: `src/generators/actions/` - PL/pgSQL functions
- **Team D (FraiseQL)**: `src/generators/fraiseql/` - GraphQL metadata
- **Team E (CLI)**: `src/cli/` - Command-line interface

### Getting Help

1. **Read the test**: Tests are documentation!
   ```python
   def test_email_field_generates_descriptive_comment(table_generator):
       """Test: email type generates descriptive COMMENT"""
       field = FieldDefinition(name="email", type_name="email")
       # ... shows exactly what the code should do
   ```

2. **Look at similar code**: Find working examples
   ```bash
   grep -r "generate_comment" src/
   ```

3. **Run related tests**: See what already works
   ```bash
   uv run pytest tests/unit/schema/ -v -k comment
   ```

---

## 🎓 Learning Resources

### TDD (Test-Driven Development)

Read our methodology: `~/.claude/CLAUDE.md` (Phased TDD section)

**Key principles**:
- RED: Test fails (defines what we want)
- GREEN: Test passes (implement feature)
- REFACTOR: Clean up (improve code)
- QA: Verify (integration testing)

### SpecQL Architecture

Essential docs:
- `docs/architecture/SPECQL_BUSINESS_LOGIC_REFINED.md` - Full DSL spec
- `docs/architecture/INTEGRATION_PROPOSAL.md` - Framework conventions
- `START_HERE.md` - Handoff document

### Python Testing

```bash
# Run specific test
uv run pytest tests/unit/schema/test_comment_generation.py::test_email_field_generates_descriptive_comment -v

# Run with debugging
uv run pytest tests/unit/schema/test_comment_generation.py -v --pdb

# Run with print output
uv run pytest tests/unit/schema/test_comment_generation.py -v -s
```

---

## ⚠️ Common Pitfalls

### 1. Skip Marker Location

```python
# ❌ Wrong: Skip at test function level
def test_something():
    pytest.skip("reason")

# ✅ Right: Skip at module level
pytestmark = pytest.mark.skip(reason="reason")

# Or at function level with decorator
@pytest.mark.skip(reason="reason")
def test_something():
    pass
```

### 2. Test Isolation

```python
# ❌ Wrong: Tests depend on each other
def test_first():
    global data
    data = "something"

def test_second():
    assert data == "something"  # Depends on test_first!

# ✅ Right: Each test independent
@pytest.fixture
def data():
    return "something"

def test_first(data):
    assert data == "something"

def test_second(data):
    assert data == "something"
```

### 3. Import Errors

```python
# ❌ Wrong: Relative imports
from ..generators import TableGenerator

# ✅ Right: Absolute imports
from src.generators.table_generator import TableGenerator
```

---

## 📊 Success Metrics

### Weekly Goals

Each week, you should:
- ✅ Complete all tests for that week
- ✅ No regressions (previous tests still pass)
- ✅ Code reviewed and cleaned up
- ✅ Ready to move to next week

### Measuring Progress

```bash
# Quick progress check
uv run pytest --tb=no -q | grep -E "(passed|skipped)"

# Expected progression:
# Week 1: 1409 passed, 96 skipped
# Week 2: 1422 passed, 83 skipped
# Week 3: 1434 passed, 71 skipped
# Week 4: 1453 passed, 52 skipped
# Week 5: 1460 passed, 45 skipped
# Week 6: 1476 passed, 29 skipped
# Week 7: 1482 passed, 23 skipped
# Week 8: 1508 passed, 0 skipped ✅
```

---

## 🚀 Let's Get Started!

Ready to begin? Start with:

**👉 [Week 1: Database Integration](./week1_database_integration.md)**

This is the **highest priority** week. Database integration is critical infrastructure that other features depend on.

Good luck! 🎉

---

**Questions?** Check existing code, read tests, and experiment! That's how you learn.
