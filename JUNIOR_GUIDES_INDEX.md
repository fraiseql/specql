# SpecQL Junior Engineer Guides - Complete Index

**Goal**: Take all skipped/failing pattern tests from ⚠️ 47 skipped/6 failed → ✅ 100% passing
**Target Audience**: Junior engineers
**Total Time**: 3-4 weeks (part-time)

---

## 📚 Guide Overview

| Guide | Tests Fixed | Difficulty | Time | Status |
|-------|-------------|------------|------|--------|
| [Week 1: Foundation](#week-1-foundation) | Infrastructure | ⭐ Easy | 7 days | ✅ Complete |
| [Week 2: SCD Type 2](#week-2-scd-type-2) | 6 failing | ⭐⭐ Medium | 3-4 days | ✅ Complete |
| [Week 3: Temporal Patterns](#week-3-temporal-patterns) | 8 skipped | ⭐⭐ Medium | 5-6 days | ✅ Complete |
| [Week 4: Validation Patterns](#week-4-validation-patterns) | 13 passing | ⭐⭐⭐ Hard | 5-6 days | ✅ Complete |
| [Week 5: Final Polish](#week-5-final-polish) | 9 failing | ⭐⭐ Medium | 2-3 days | 📝 Ready |

**Total Impact**: 66 tests from 22% → 100% passing

---

## Week 1: Foundation

**File**: [`WEEK_01_JUNIOR_GUIDE.md`](WEEK_01_JUNIOR_GUIDE.md)

### What You'll Learn
- Dependency management (core vs optional)
- Pytest markers for optional features
- Pattern test infrastructure
- Writing effective tests

### Key Topics
1. **Days 1-2**: Dependency organization (`pyproject.toml`, optional dependencies)
2. **Day 3**: Test infrastructure (fixtures, conftest.py)
3. **Days 4-7**: Pattern testing basics (computed columns example)

### Prerequisites
- Basic Python
- pytest basics
- SQL fundamentals

### Completion Criteria
- [ ] All dependencies organized
- [ ] Pytest markers working
- [ ] Pattern test structure created
- [ ] Computed column tests passing (already ✅ done!)

---

## Week 2: SCD Type 2

**File**: [`WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md`](WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md)

### What You'll Learn
- Slowly Changing Dimensions (version tracking)
- History tables and time-travel queries
- Unique constraints with `WHERE` clauses
- Point-in-time queries

### Current Status
```bash
uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py -v

Results:
✅ 2 PASSED
❌ 6 FAILED ← We fix these!
```

### Failing Tests
1. ❌ `test_no_tracked_fields_specified`
2. ❌ `test_history_table_created`
3. ❌ `test_version_field_added`
4. ❌ `test_cascade_delete_handling`
5. ❌ `test_bulk_update_support`
6. ❌ `test_performance_indexes_optimized`

### Implementation Plan
- **Day 1**: Fix entity model (add `tracked_fields`, `natural_key_fields` attributes)
- **Day 2**: Implement pattern applier (add version fields, configure entity)
- **Day 3**: Generate DDL (constraints, history table)
- **Day 4**: Fix remaining tests (cascades, bulk updates, indexes)

### Key Code Locations
- `src/core/ast_models.py` - Add SCD Type 2 attributes to `EntityDefinition`
- `src/patterns/temporal/scd_type2_helper.py` - Create pattern implementation
- `src/generators/schema/pattern_applier.py` - Register pattern
- `src/generators/schema/table_generator.py` - Generate version tracking DDL

### Success Criteria
- [ ] All 8 SCD Type 2 tests passing
- [ ] Version fields added automatically
- [ ] Unique constraint on current version
- [ ] History table created (if configured)
- [ ] Helper functions generated

---

## Week 3: Temporal Patterns

**File**: [`WEEK_03_JUNIOR_GUIDE_TEMPORAL_PATTERNS.md`](WEEK_03_JUNIOR_GUIDE_TEMPORAL_PATTERNS.md)

### What You'll Learn
- PostgreSQL `DATERANGE` type
- GIST indexes for range queries
- EXCLUSION constraints
- Computed columns (`GENERATED ALWAYS AS`)

### Current Status
```bash
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py -v

Results:
⏸️ 18 SKIPPED ← We implement these!
```

### Real-World Use Case
**Machine allocation**: Prevent double-booking machines for different products

```
Machine 001:
  ❌ Jan 1-10: Product A
  ❌ Jan 5-15: Product B  ← BLOCKED by EXCLUDE constraint!
  ✅ Jan 10-20: Product C  ← OK (adjacent, not overlapping)
```

### Implementation Plan
- **Day 1**: Learn PostgreSQL range types (hands-on experimentation)
- **Day 2**: Implement pattern class (`NonOverlappingDateRangePattern`)
- **Day 3**: Update table generator (computed columns, indexes)
- **Day 4**: Debug and test
- **Day 5**: Advanced features (multiple scopes, warning mode)
- **Day 6**: Integration testing with real database

### Key PostgreSQL Features
```sql
-- Computed daterange column
date_range DATERANGE
  GENERATED ALWAYS AS (daterange(start_date, end_date, '[)')) STORED

-- GIST index
CREATE INDEX idx_allocations_daterange
ON allocations USING gist(date_range);

-- Exclusion constraint (prevents overlaps)
ALTER TABLE allocations
ADD CONSTRAINT no_overlap
EXCLUDE USING gist (machine_id WITH =, date_range WITH &&);
```

### Key Code Locations
- `src/patterns/temporal/non_overlapping_daterange.py` - Create pattern implementation
- `src/core/ast_models.py` - Add computed column support to `FieldDefinition`
- `src/generators/schema/table_generator.py` - Generate computed column DDL
- `src/generators/schema/index_generator.py` - Generate GIST indexes

### Success Criteria
- [ ] All 18 temporal tests passing
- [ ] Computed daterange column generated
- [ ] GIST index created
- [ ] EXCLUSION constraint in strict mode
- [ ] Warning trigger in warning mode
- [ ] Integration test with real PostgreSQL

---

## Week 4: Validation Patterns

**File**: [`WEEK_04_JUNIOR_GUIDE_VALIDATION_PATTERNS.md`](WEEK_04_JUNIOR_GUIDE_VALIDATION_PATTERNS.md)

### What You'll Learn
- Recursive CTEs (tree/graph traversal)
- Dependency validation (REQUIRES, CONFLICTS_WITH)
- Template inheritance with JSONB merging
- Circular dependency detection

### Current Status
```bash
uv run pytest tests/unit/patterns/validation/ -v | grep SKIPPED

Results:
⏸️ 29 SKIPPED ← We implement these!
  - Recursive dependencies: ~17 tests
  - Template inheritance: ~12 tests
```

### Part 1: Recursive Dependency Validator

**Real-World Use Case**: Product feature dependencies

```
User selects: [Bluetooth]
System checks:
  ❌ Missing: WiFi (required by Bluetooth)
  ❌ Missing: Power Management (required by WiFi)
```

**Implementation**: Recursive CTE to traverse dependency graph

```sql
WITH RECURSIVE dependency_tree AS (
    -- BASE: Direct dependencies
    SELECT feature_id, requires_feature_id, 1 as depth
    FROM feature_dependencies
    WHERE feature_id = 'bluetooth'

    UNION ALL

    -- RECURSIVE: Dependencies of dependencies
    SELECT fd.feature_id, fd.requires_feature_id, dt.depth + 1
    FROM feature_dependencies fd
    JOIN dependency_tree dt ON dt.requires_feature_id = fd.feature_id
    WHERE dt.depth < 10
)
SELECT * FROM dependency_tree;
```

### Part 2: Template Inheritance

**Real-World Use Case**: Configuration template hierarchy

```
Generic Product Template
  ↓ (inherits)
Electronics Template (adds voltage, wattage)
  ↓ (inherits)
Laptop Template (adds screen_size, battery_life)
```

**Implementation**: Recursive hierarchy traversal with JSONB merging

### Implementation Plan
- **Days 1-2**: Recursive dependency validator
  - Generate validation functions
  - Implement recursive CTE
  - Add conflict detection
- **Day 3**: Integration testing
- **Days 4-5**: Template inheritance
  - Generate resolution functions
  - Implement JSONB merging
  - Add template chain debugging

### Key Code Locations
- `src/patterns/validation/recursive_dependency_validator.py` - Dependency validation
- `src/patterns/validation/template_inheritance.py` - Template resolution
- Both patterns generate PL/pgSQL functions (not schema changes)

### Success Criteria
- [ ] All 29 validation tests passing
- [ ] Recursive dependency validation working
- [ ] Conflict detection working
- [ ] Circular dependency detection
- [ ] Template inheritance resolution
- [ ] JSONB merging correct

---

## Week 5: Final Polish

**File**: [`WEEK_05_FINAL_POLISH_GUIDE.md`](WEEK_05_FINAL_POLISH_GUIDE.md)

### What You'll Fix
- Pattern registration issues (3 tests)
- FraiseQL metadata annotations (1 test)
- Custom field naming (1 test)
- Trigger generation (1 test)
- Index generation (1 test)
- Null handling in template resolution (1 test)
- Configuration parameter parsing (1 test)

### Current Status
```bash
uv run pytest tests/unit/patterns/validation/ -v

Results:
✅ 13 PASSED
❌ 9 FAILED ← We fix these!
```

### The 9 Failing Tests (Grouped by Root Cause)

**Issue Group 1: Pattern Registration** (3 tests)
- Missing pattern class registration in applier
- Fix: Register `RecursiveDependencyValidator` and `TemplateInheritance`

**Issue Group 2: FraiseQL Metadata** (1 test)
- Missing `@fraiseql:pattern:*` annotations
- Fix: Add pattern metadata to comment generator

**Issue Group 3: Field Naming** (1 test)
- Custom field names not applied
- Fix: Use `template_field` param from config

**Issue Group 4: Trigger Generation** (1 test)
- No validation triggers generated
- Fix: Add trigger generation to pattern

**Issue Group 5: Index Generation** (1 test)
- Template fields not indexed
- Fix: Generate indexes for reference fields

**Issue Group 6: Null Handling** (1 test)
- Null template references crash
- Fix: Add null checks in SQL functions

**Issue Group 7: Config Parsing** (1 test)
- `allow_cycles` parameter causes error
- Fix: Safe null parameter parsing

### Implementation Plan
- **Day 1**: Pattern registration (3 tests) + FraiseQL metadata (1 test)
- **Day 2**: Field naming (1 test) + Trigger generation (1 test)
- **Day 3**: Index generation (1 test) + Null handling (1 test) + Config parsing (1 test)

### Key Code Locations
- `src/generators/schema/pattern_applier.py` - Register validation patterns
- `src/generators/comment_generator.py` - Add pattern annotations
- `src/patterns/validation/template_inheritance.py` - Fix field names, triggers, indexes, null handling
- `src/patterns/validation/recursive_dependency_validator.py` - Fix config parsing

### Success Criteria
- [ ] All 9 failing tests fixed
- [ ] 66/66 pattern tests passing (100%!)
- [ ] Pattern registration complete
- [ ] FraiseQL discovery working
- [ ] All edge cases handled

---

## 🎯 Overall Success Metrics

### Before
```bash
uv run pytest tests/unit/patterns/ --tb=no -q

Results:
✅ 15 passed (computed columns, aggregate views)
❌ 6 failed (SCD Type 2)
⏸️ 47 skipped (temporal + validation patterns)
───────────────────────────────────
Total: 68 tests, 78% incomplete
```

### After (Target)
```bash
uv run pytest tests/unit/patterns/ --tb=no -q

Results:
✅ 68 passed (ALL TESTS!)
❌ 0 failed
⏸️ 0 skipped
───────────────────────────────────
Total: 68 tests, 100% complete 🎉
```

---

## 🛠️ Development Workflow

### Daily Workflow

1. **Start of Day**: Check test status
   ```bash
   uv run pytest tests/unit/patterns/ -v | grep -E "(PASSED|FAILED|SKIPPED)"
   ```

2. **Pick a Test**: Start with simplest failing/skipped test
   ```bash
   uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_version_field_added -v -s
   ```

3. **Understand the Test**: Read test code, understand what it expects

4. **Implement**: Make minimal changes to pass the test

5. **Verify**: Run test again
   ```bash
   # Should now pass!
   uv run pytest tests/unit/patterns/schema/test_scd_type2_helper.py::TestSCDType2Helper::test_version_field_added -v
   ```

6. **Commit**: Small, focused commits
   ```bash
   git add src/patterns/temporal/scd_type2_helper.py
   git commit -m "feat: add version fields to SCD Type 2 pattern"
   ```

7. **Run All Tests**: Ensure no regressions
   ```bash
   uv run pytest tests/unit/patterns/ -v
   ```

### When Stuck

1. **Add Debug Output**:
   ```python
   print(f"Entity patterns: {entity.patterns}")
   print(f"Generated DDL:\n{ddl}")
   ```

2. **Check Example Code**: Look at computed column pattern (already working)

3. **Test Incrementally**: Break complex test into smaller assertions

4. **Ask Questions**: Document what you tried, what happened, what you expected

---

## 📊 Progress Tracking

### Week 2 Checklist
- [ ] Day 1: Entity model updated
- [ ] Day 2: Pattern applier implemented
- [ ] Day 3: DDL generation working
- [ ] Day 4: All 8 SCD Type 2 tests passing ✅

### Week 3 Checklist
- [ ] Day 1: Understand PostgreSQL ranges
- [ ] Day 2: Pattern class implemented
- [ ] Day 3: Table generator updated
- [ ] Day 4: Basic tests passing
- [ ] Day 5: Advanced features working
- [ ] Day 6: Integration test passing ✅

### Week 4 Checklist
- [ ] Days 1-2: Recursive dependency validator
- [ ] Day 3: Integration tests passing
- [ ] Days 4-5: Template inheritance
- [ ] All 29 validation tests passing ✅

---

## 🎓 Learning Resources

### PostgreSQL Documentation
- [Range Types](https://www.postgresql.org/docs/current/rangetypes.html)
- [GIST Indexes](https://www.postgresql.org/docs/current/gist.html)
- [Exclusion Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION)
- [Recursive CTEs](https://www.postgresql.org/docs/current/queries-with.html)
- [JSONB Functions](https://www.postgresql.org/docs/current/functions-json.html)

### SQL Practice
```bash
# Start test database
docker run -d --name postgres-test -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:16

# Connect and experiment
psql -h localhost -U postgres

# Try examples from guides
CREATE TABLE test_table (...);
```

### Python/Pytest Resources
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html)

---

## 🚀 Getting Started

### Prerequisites Check
```bash
# Python 3.11+
python --version

# uv package manager
uv --version

# PostgreSQL (for integration tests)
psql --version

# Clone repo
git clone <repo-url>
cd specql
```

### Setup
```bash
# Install dependencies
uv pip install -e ".[dev,all]"

# Run tests to see current status
uv run pytest tests/unit/patterns/ -v

# Start with Week 1 (if not done)
cat WEEK_01_JUNIOR_GUIDE.md
```

### Your First Test Fix

1. **Read** `WEEK_02_JUNIOR_GUIDE_SCD_TYPE2.md`
2. **Pick** first failing test: `test_no_tracked_fields_specified`
3. **Understand** what it expects (version tracking fields)
4. **Implement** the fix (add attributes to `EntityDefinition`)
5. **Verify** test passes
6. **Celebrate** 🎉 and move to next test!

---

## 💡 Tips for Success

### 1. Start Small
Don't try to implement entire pattern at once. Fix one test at a time.

### 2. Read Tests First
Tests tell you EXACTLY what to implement. They're the specification!

### 3. Use Debug Prints
When stuck, print everything:
```python
print(f"DEBUG: entity.fields = {entity.fields}")
print(f"DEBUG: generated DDL = {ddl}")
```

### 4. Test Incrementally
Run tests after every change. Fast feedback loop = faster learning.

### 5. Commit Often
Small commits = easy to undo if something breaks.

### 6. Ask Questions
Document your debugging process. It helps others help you.

### 7. Take Breaks
Complex patterns (especially recursive CTEs) are mentally demanding. Break them into pieces.

---

## 🎉 Completion Rewards

### After Week 2 (SCD Type 2)
You understand:
- ✅ Version tracking patterns
- ✅ History tables
- ✅ Time-travel queries
- ✅ Unique constraints with conditions

### After Week 3 (Temporal Patterns)
You understand:
- ✅ PostgreSQL range types
- ✅ GIST indexes
- ✅ Exclusion constraints
- ✅ Computed columns

### After Week 4 (Validation Patterns)
You understand:
- ✅ Recursive CTEs
- ✅ Graph traversal in SQL
- ✅ JSONB operations
- ✅ Complex validation logic

### Final Achievement
- ✅ 68/68 pattern tests passing (100%)
- ✅ Production-ready pattern implementation
- ✅ Advanced PostgreSQL skills
- ✅ Complex code generation mastery

**You'll be a PostgreSQL and code generation expert! 🚀**

---

## 📞 Support

If stuck:
1. Re-read the relevant guide section
2. Check the "Common Mistakes" section
3. Add debug output and investigate
4. Document what you tried (helps get better help)
5. Ask for help (include: what you tried, what happened, what you expected)

---

**Good luck! You've got this! 💪**

**Remember**: Every expert was once a beginner. These guides break complex topics into manageable pieces. Take your time, test incrementally, and celebrate small wins! 🎉
