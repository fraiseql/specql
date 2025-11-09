# Team D: Detailed Execution Timeline - 3 Phases

**Team**: FraiseQL Metadata & Integration
**Status**: Ready to Execute
**Total Duration**: 3-4 days (spread across Week 5 & Week 7)
**Last Updated**: 2025-11-09

---

## 📅 Timeline Overview

```
Week 5          Week 6          Week 7
Day 1           [Gap]           Day 1    Day 2    Day 3
┌─────┐                        ┌─────┬─────┬─────┐
│  P1 │         Wait           │ P2  │ P2  │ P3  │
└─────┘                        └─────┴─────┴─────┘
1-2h                           8h    8h    4-6h

P1 = Phase 1: Rich Types Verification
P2 = Phase 2: tv_ Table Annotations
P3 = Phase 3: Mutation Annotations (optional)
```

**Total Effort**:
- Phase 1: 1-2 hours
- Phase 2: 2-3 days (16 hours)
- Phase 3: 4-6 hours (optional)
- **Grand Total**: 21-26 hours (3-4 work days)

---

## 🎯 PHASE 1: Rich Types FraiseQL Verification

**Timeline**: Week 5, Day 1
**Duration**: 1-2 hours
**Priority**: ⚡ **CRITICAL** (blocks understanding of FraiseQL integration)

---

### **Day Plan: Week 5, Day 1**

#### **Morning Block (9:00 AM - 11:00 AM)** - 2 hours max

---

### **Hour 1: RED Phase (9:00 - 9:30 AM)** - 30 minutes

**Objective**: Write failing integration tests

**Tasks**:
1. **[5 min]** Create test directory structure
   ```bash
   mkdir -p tests/integration/fraiseql
   touch tests/integration/fraiseql/__init__.py
   ```

2. **[10 min]** Create test fixture entity
   ```bash
   # Create entities/examples/contact_with_rich_types.yaml
   cat > entities/examples/contact_with_rich_types.yaml <<'EOF'
   entity: Contact
   schema: crm

   fields:
     email: email!
     website: url
     phone: phoneNumber

   actions: []
   EOF
   ```

3. **[15 min]** Write first failing test
   ```bash
   # Create tests/integration/fraiseql/test_rich_type_autodiscovery.py
   # Write test_email_field_has_check_constraint
   # Write test_email_field_has_comment
   ```

**Milestone**: Tests written, should fail with ImportError

**Verification**:
```bash
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v
# Expected: FAILED or ImportError
```

---

### **Hour 1: GREEN Phase (9:30 - 10:00 AM)** - 30 minutes

**Objective**: Create minimal compatibility checker

**Tasks**:
1. **[5 min]** Create package structure
   ```bash
   mkdir -p src/generators/fraiseql
   touch src/generators/fraiseql/__init__.py
   ```

2. **[20 min]** Implement compatibility_checker.py
   - Create CompatibilityChecker class
   - Implement check_all_types_compatible()
   - Implement get_incompatible_types()
   - Implement get_compatibility_report()

3. **[5 min]** Run tests
   ```bash
   uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v
   # Expected: PASSED (all tests pass)
   ```

**Milestone**: Tests pass, FraiseQL autodiscovery confirmed

---

### **Hour 2: REFACTOR Phase (10:00 - 10:30 AM)** - 30 minutes

**Objective**: Add documentation

**Tasks**:
1. **[20 min]** Write docs/fraiseql/RICH_TYPES_INTEGRATION.md
   - Overview section
   - How It Works (3 steps)
   - Rich Type Mappings table
   - Benefits section
   - Testing instructions

2. **[10 min]** Add unit tests for compatibility checker
   ```bash
   # Create tests/unit/fraiseql/test_compatibility_checker.py
   # Write test_check_all_types_compatible
   # Write test_get_compatibility_report
   ```

**Milestone**: Documentation complete

---

### **Hour 2: QA Phase (10:30 - 11:00 AM)** - 30 minutes

**Objective**: Full verification

**Tasks**:
1. **[10 min]** Run all tests
   ```bash
   uv run pytest tests/integration/fraiseql/ -v
   uv run pytest tests/unit/fraiseql/ -v
   ```

2. **[10 min]** Code quality checks
   ```bash
   uv run ruff check src/generators/fraiseql/
   uv run mypy src/generators/fraiseql/
   ```

3. **[5 min]** Generate schema and verify
   ```bash
   # Generate test schema
   uv run python -m src.cli.orchestrator generate entities/examples/contact_with_rich_types.yaml

   # Check output has comments
   grep -A 5 "COMMENT ON COLUMN" generated/migration.sql
   ```

4. **[5 min]** Git commit
   ```bash
   git add src/generators/fraiseql/ tests/ entities/examples/ docs/fraiseql/RICH_TYPES_INTEGRATION.md
   git commit -m "feat(Team D Phase 1): Rich Types FraiseQL Verification Complete"
   ```

**Milestone**: Phase 1 complete! ✅

---

### **Phase 1 Deliverables**:

**Files Created** (8 files):
- ✅ src/generators/fraiseql/__init__.py
- ✅ src/generators/fraiseql/compatibility_checker.py
- ✅ tests/unit/fraiseql/test_compatibility_checker.py
- ✅ tests/integration/fraiseql/test_rich_type_autodiscovery.py
- ✅ tests/integration/fraiseql/__init__.py
- ✅ tests/unit/fraiseql/__init__.py
- ✅ docs/fraiseql/RICH_TYPES_INTEGRATION.md
- ✅ entities/examples/contact_with_rich_types.yaml

**Lines of Code**: ~805 lines

**Acceptance Criteria**:
- ✅ All integration tests pass
- ✅ Compatibility checker confirms 100% compatibility
- ✅ No manual annotations needed
- ✅ Documentation complete
- ✅ Code quality checks pass

---

## 🎯 PHASE 2: tv_ Table FraiseQL Annotations

**Timeline**: Week 7, Days 1-2
**Duration**: 2-3 days (16 hours)
**Priority**: 🟡 **HIGH** (core CQRS functionality)

---

### **Day 1 Plan: Week 7, Day 1 (8 hours)**

---

#### **Morning Session: RED Phase (9:00 AM - 12:00 PM)** - 3 hours

**Objective**: Write comprehensive unit tests

**Hour 1 (9:00 - 10:00 AM): Basic Annotation Tests**

**Tasks**:
1. **[10 min]** Create test file structure
   ```bash
   touch tests/unit/fraiseql/test_table_view_annotator.py
   ```

2. **[50 min]** Write basic annotation tests
   - TestTableAnnotation class
     - test_generates_table_annotation
     - test_skips_annotation_if_no_table_views
   - TestInternalColumnAnnotations class
     - test_marks_primary_key_as_internal
     - test_marks_foreign_keys_as_internal
     - test_marks_refreshed_at_as_internal

**Hour 2 (10:00 - 11:00 AM): Filter Column Tests**

**Tasks**:
1. **[50 min]** Write filter column tests
   - TestFilterColumnAnnotations class
     - test_annotates_tenant_id_as_filter
     - test_annotates_uuid_foreign_keys_as_filters
     - test_annotates_extra_filter_columns
     - test_hierarchical_path_annotation

2. **[10 min]** Run tests (should fail)
   ```bash
   uv run pytest tests/unit/fraiseql/test_table_view_annotator.py -v
   # Expected: ImportError (TableViewAnnotator doesn't exist)
   ```

**Hour 3 (11:00 AM - 12:00 PM): Data Column & SQL Mapping Tests**

**Tasks**:
1. **[30 min]** Write data column tests
   - TestDataColumnAnnotation class
     - test_annotates_data_column_with_expand
   - TestSQLTypeMapping class
     - test_maps_sql_types_to_graphql

2. **[20 min]** Create test fixture entity
   ```bash
   cat > entities/examples/review_with_table_views.yaml <<'EOF'
   entity: Review
   schema: library

   fields:
     rating: integer!
     comment: text
     author: ref(User)
     book: ref(Book)

   table_views:
     include_relations:
       - author:
           fields: [name, email]
       - book:
           fields: [title, isbn]
     extra_filter_columns:
       - rating
       - created_at

   actions: []
   EOF
   ```

3. **[10 min]** Run all tests
   ```bash
   uv run pytest tests/unit/fraiseql/test_table_view_annotator.py -v
   # Expected: All FAILED (no implementation yet)
   ```

**Milestone**: Comprehensive test suite written (should have ~10-12 tests)

---

#### **Lunch Break (12:00 PM - 1:00 PM)** - 1 hour

---

#### **Afternoon Session: GREEN Phase (1:00 PM - 5:00 PM)** - 4 hours

**Objective**: Implement TableViewAnnotator

**Hour 4 (1:00 - 2:00 PM): Core Implementation**

**Tasks**:
1. **[10 min]** Create implementation file
   ```bash
   touch src/generators/fraiseql/table_view_annotator.py
   ```

2. **[50 min]** Implement core class structure
   - TableViewAnnotator class
   - __init__ method
   - generate_annotations method
   - _annotate_table method

3. **[5 min]** Run tests (some should pass now)
   ```bash
   uv run pytest tests/unit/fraiseql/test_table_view_annotator.py::TestTableAnnotation -v
   # Expected: 2/2 PASSED
   ```

**Hour 5 (2:00 - 3:00 PM): Internal Columns Implementation**

**Tasks**:
1. **[45 min]** Implement _annotate_internal_columns method
   - Mark pk_* as internal
   - Mark fk_* as internal
   - Mark refreshed_at as internal
   - Helper: _extract_ref_entity

2. **[15 min]** Run tests
   ```bash
   uv run pytest tests/unit/fraiseql/test_table_view_annotator.py::TestInternalColumnAnnotations -v
   # Expected: 3/3 PASSED
   ```

**Hour 6 (3:00 - 4:00 PM): Filter Columns Implementation**

**Tasks**:
1. **[50 min]** Implement _annotate_filter_columns method
   - Annotate tenant_id
   - Annotate UUID FK filters
   - Annotate extra filter columns
   - Handle hierarchical path
   - Helper: _map_sql_type_to_graphql

2. **[10 min]** Run tests
   ```bash
   uv run pytest tests/unit/fraiseql/test_table_view_annotator.py::TestFilterColumnAnnotations -v
   # Expected: 4/4 PASSED
   ```

**Hour 7 (4:00 - 5:00 PM): Data Column & Final Tests**

**Tasks**:
1. **[15 min]** Implement _annotate_data_column method

2. **[10 min]** Run all unit tests
   ```bash
   uv run pytest tests/unit/fraiseql/test_table_view_annotator.py -v
   # Expected: ALL PASSED (12/12)
   ```

3. **[20 min]** Update package exports
   ```python
   # src/generators/fraiseql/__init__.py
   from .compatibility_checker import CompatibilityChecker
   from .table_view_annotator import TableViewAnnotator

   __all__ = ["CompatibilityChecker", "TableViewAnnotator"]
   ```

4. **[15 min]** Quick manual test
   ```bash
   # Test in Python REPL
   from src.core.ast_models import EntityAST, TableViewConfig
   from src.generators.fraiseql.table_view_annotator import TableViewAnnotator

   entity = EntityAST(name="Review", schema="library", fields=[], actions=[], table_views=TableViewConfig(include_relations=["author"]))
   annotator = TableViewAnnotator(entity)
   print(annotator.generate_annotations())
   ```

**Milestone**: Core implementation complete, all unit tests passing!

---

#### **End of Day 1 Summary**:
- ✅ 12 unit tests written
- ✅ TableViewAnnotator implemented (300 lines)
- ✅ All unit tests passing
- ⏳ Integration pending (Day 2)

---

### **Day 2 Plan: Week 7, Day 2 (8 hours)**

---

#### **Morning Session: REFACTOR Phase (9:00 AM - 12:00 PM)** - 3 hours

**Objective**: Integration with orchestrator + integration tests

**Hour 1 (9:00 - 10:00 AM): Orchestrator Integration**

**Tasks**:
1. **[30 min]** Update schema_orchestrator.py
   ```python
   # Add import
   from src.generators.fraiseql.table_view_annotator import TableViewAnnotator

   # Add to generate_migration method
   if entity.table_views:
       annotator = TableViewAnnotator(entity)
       annotations = annotator.generate_annotations()
       if annotations:
           parts.append(
               f"-- FraiseQL Annotations: {entity.schema}.tv_{entity.name.lower()}\n"
               + annotations
           )
   ```

2. **[20 min]** Test integration manually
   ```bash
   # Generate complete schema with tv_ + annotations
   uv run python -m src.cli.orchestrator generate entities/examples/review_with_table_views.yaml

   # Verify annotations present
   grep -A 10 "FraiseQL Annotations" generated/migration.sql
   grep "@fraiseql:table" generated/migration.sql
   grep "@fraiseql:filter" generated/migration.sql
   grep "@fraiseql:jsonb expand=true" generated/migration.sql
   ```

3. **[10 min]** Commit integration
   ```bash
   git add src/generators/schema_orchestrator.py
   git commit -m "integrate: Team D table view annotator with schema orchestrator"
   ```

**Hour 2 (10:00 - 11:00 AM): Integration Tests**

**Tasks**:
1. **[40 min]** Write integration test
   ```bash
   # Create tests/integration/fraiseql/test_tv_annotations_e2e.py

   # Tests:
   # - test_migration_includes_fraiseql_annotations
   # - test_annotations_apply_to_database
   # - test_filter_column_comments_exist
   # - test_internal_columns_marked
   # - test_data_column_has_expand_annotation
   ```

2. **[20 min]** Run integration tests
   ```bash
   uv run pytest tests/integration/fraiseql/test_tv_annotations_e2e.py -v
   # Expected: ALL PASSED (5/5)
   ```

**Hour 3 (11:00 AM - 12:00 PM): Documentation**

**Tasks**:
1. **[40 min]** Write docs/fraiseql/TV_ANNOTATIONS.md
   - Overview section
   - Annotation patterns (4 types)
   - Implementation by day
   - Complete example
   - Acceptance criteria

2. **[20 min]** Add code comments and docstrings
   - Add module docstring to table_view_annotator.py
   - Add detailed method docstrings
   - Add inline comments for complex logic

**Milestone**: Integration complete, documentation written

---

#### **Lunch Break (12:00 PM - 1:00 PM)** - 1 hour

---

#### **Afternoon Session: QA Phase (1:00 PM - 5:00 PM)** - 4 hours

**Objective**: Comprehensive testing and quality assurance

**Hour 4 (1:00 - 2:00 PM): Test Suite Execution**

**Tasks**:
1. **[20 min]** Run all unit tests
   ```bash
   uv run pytest tests/unit/fraiseql/ -v --tb=short
   # Target: ALL PASSED
   ```

2. **[20 min]** Run all integration tests
   ```bash
   uv run pytest tests/integration/fraiseql/ -v --tb=short
   # Target: ALL PASSED
   ```

3. **[20 min]** Run with coverage
   ```bash
   uv run pytest tests/unit/fraiseql/ tests/integration/fraiseql/ \
     --cov=src/generators/fraiseql \
     --cov-report=term-missing \
     --cov-report=html
   # Target: ≥ 90% coverage
   ```

**Hour 5 (2:00 - 3:00 PM): Code Quality Checks**

**Tasks**:
1. **[15 min]** Linting
   ```bash
   uv run ruff check src/generators/fraiseql/
   # Fix any issues
   uv run ruff check src/generators/fraiseql/ --fix
   ```

2. **[15 min]** Type checking
   ```bash
   uv run mypy src/generators/fraiseql/
   # Fix any type issues
   ```

3. **[15 min]** Format code
   ```bash
   uv run ruff format src/generators/fraiseql/
   uv run ruff format tests/unit/fraiseql/
   uv run ruff format tests/integration/fraiseql/
   ```

4. **[15 min]** Security check
   ```bash
   uv run bandit -r src/generators/fraiseql/
   ```

**Hour 6 (3:00 - 4:00 PM): Database Testing**

**Tasks**:
1. **[20 min]** Apply to real database
   ```bash
   # Create test database
   createdb test_specql_teamd

   # Generate migration
   uv run python -m src.cli.orchestrator generate entities/examples/review_with_table_views.yaml -o generated/teamd_phase2.sql

   # Apply migration
   psql test_specql_teamd < generated/teamd_phase2.sql
   ```

2. **[20 min]** Verify in database
   ```bash
   # Check table exists
   psql test_specql_teamd -c "\d+ library.tv_review"

   # Check table comment
   psql test_specql_teamd -c "SELECT obj_description('library.tv_review'::regclass);"

   # Check column comments
   psql test_specql_teamd -c "
     SELECT
       attname,
       col_description('library.tv_review'::regclass, attnum)
     FROM pg_attribute
     WHERE attrelid = 'library.tv_review'::regclass
       AND attnum > 0
     ORDER BY attnum;
   "
   ```

3. **[20 min]** Verify annotations
   ```bash
   # Check for @fraiseql annotations
   psql test_specql_teamd -c "
     SELECT obj_description('library.tv_review'::regclass);
   " | grep "@fraiseql"

   # Should see:
   # - @fraiseql:table
   # - @fraiseql:field internal=true (multiple)
   # - @fraiseql:filter (multiple)
   # - @fraiseql:jsonb expand=true
   ```

**Hour 7 (4:00 - 5:00 PM): Final Review & Commit**

**Tasks**:
1. **[15 min]** Review all changes
   ```bash
   git status
   git diff --cached
   ```

2. **[10 min]** Run final test suite
   ```bash
   make test  # or uv run pytest
   ```

3. **[10 min]** Clean up database
   ```bash
   dropdb test_specql_teamd
   ```

4. **[25 min]** Create comprehensive commit
   ```bash
   git add .
   git commit -m "feat(Team D Phase 2): tv_ Table FraiseQL Annotations Complete

   - TableViewAnnotator implementation (300 lines)
   - Comprehensive unit tests (12 tests)
   - Integration tests with database verification
   - Complete documentation
   - Schema orchestrator integration
   - 90%+ test coverage

   Annotations generated:
   - @fraiseql:table for tv_ tables
   - @fraiseql:field internal=true for pk_*, fk_*
   - @fraiseql:filter for UUID columns and extra filters
   - @fraiseql:jsonb expand=true for data column

   Ready for FraiseQL introspection!"
   ```

**Milestone**: Phase 2 complete! ✅

---

### **Phase 2 Deliverables**:

**Files Created** (5 files):
- ✅ src/generators/fraiseql/table_view_annotator.py (300 lines)
- ✅ tests/unit/fraiseql/test_table_view_annotator.py (350 lines)
- ✅ tests/integration/fraiseql/test_tv_annotations_e2e.py (150 lines)
- ✅ docs/fraiseql/TV_ANNOTATIONS.md (200 lines)
- ✅ entities/examples/review_with_table_views.yaml (30 lines)

**Files Modified** (2 files):
- ✅ src/generators/schema_orchestrator.py (+15 lines)
- ✅ src/generators/fraiseql/__init__.py (+2 lines)

**Total Lines**: ~1,047 lines

**Acceptance Criteria**:
- ✅ Table annotations generated with @fraiseql:table
- ✅ Internal columns marked internal=true
- ✅ Filter columns annotated with type/index/performance
- ✅ JSONB data column annotated with expand=true
- ✅ All unit tests pass (12/12)
- ✅ All integration tests pass (5/5)
- ✅ Code quality checks pass (ruff, mypy, bandit)
- ✅ Test coverage ≥ 90%
- ✅ Annotations apply correctly to PostgreSQL
- ✅ Documentation complete

---

## 🎯 PHASE 3: Mutation Impact Annotations (OPTIONAL)

**Timeline**: Week 7, Day 3
**Duration**: 4-6 hours
**Priority**: 🟢 **LOW** (optional enhancement)

---

### **Day Plan: Week 7, Day 3 (Half Day)**

---

#### **Morning Session (9:00 AM - 1:00 PM)** - 4 hours

**Note**: This phase is OPTIONAL. If time is constrained or Phase 2 took longer, skip this phase. Core functionality (Phases 1-2) works without it.

---

### **Hour 1: RED Phase (9:00 - 10:00 AM)** - 1 hour

**Objective**: Write failing tests for mutation annotations

**Tasks**:
1. **[10 min]** Create test file
   ```bash
   touch tests/unit/fraiseql/test_mutation_annotator.py
   ```

2. **[40 min]** Write unit tests
   - TestMutationAnnotation class
     - test_generates_mutation_annotation
     - test_includes_metadata_mapping
     - test_camel_case_conversion
     - test_handles_actions_without_impact

3. **[10 min]** Run tests
   ```bash
   uv run pytest tests/unit/fraiseql/test_mutation_annotator.py -v
   # Expected: FAILED (MutationAnnotator doesn't exist)
   ```

**Milestone**: Test suite ready for mutation annotations

---

### **Hour 2: GREEN Phase (10:00 - 11:00 AM)** - 1 hour

**Objective**: Implement MutationAnnotator

**Tasks**:
1. **[10 min]** Create implementation file
   ```bash
   touch src/generators/fraiseql/mutation_annotator.py
   ```

2. **[40 min]** Implement MutationAnnotator class
   - __init__ method
   - generate_mutation_annotation method
   - _to_camel_case helper
   - _build_metadata_mapping helper

3. **[10 min]** Run tests
   ```bash
   uv run pytest tests/unit/fraiseql/test_mutation_annotator.py -v
   # Expected: ALL PASSED (4/4)
   ```

**Milestone**: Basic implementation complete

---

### **Hour 3: REFACTOR Phase (11:00 AM - 12:00 PM)** - 1 hour

**Objective**: Integration and documentation

**Tasks**:
1. **[20 min]** Update schema_orchestrator.py
   ```python
   from src.generators.fraiseql.mutation_annotator import MutationAnnotator

   # Add after action compilation
   if entity.actions:
       for action in entity.actions:
           annotator = MutationAnnotator(entity.schema, entity.name)
           annotation = annotator.generate_mutation_annotation(action)
           if annotation:
               mutation_annotations.append(annotation)
   ```

2. **[20 min]** Write integration test
   ```bash
   # Create tests/integration/fraiseql/test_mutation_annotations_e2e.py
   # Test end-to-end mutation annotation generation
   ```

3. **[20 min]** Write docs/fraiseql/MUTATION_ANNOTATIONS.md
   - Quick overview
   - Example annotation
   - Integration with Team C

**Milestone**: Integration complete, basic docs written

---

### **Hour 4: QA Phase (12:00 - 1:00 PM)** - 1 hour

**Objective**: Testing and commit

**Tasks**:
1. **[20 min]** Run all tests
   ```bash
   uv run pytest tests/unit/fraiseql/ tests/integration/fraiseql/ -v
   # Target: ALL PASSED
   ```

2. **[10 min]** Code quality
   ```bash
   uv run ruff check src/generators/fraiseql/
   uv run mypy src/generators/fraiseql/
   ```

3. **[15 min]** Manual verification
   ```bash
   # Generate schema with actions
   uv run python -m src.cli.orchestrator generate entities/examples/contact_with_actions.yaml

   # Check for mutation annotations
   grep -A 10 "@fraiseql:mutation" generated/migration.sql
   ```

4. **[15 min]** Commit
   ```bash
   git add .
   git commit -m "feat(Team D Phase 3): Mutation Impact Annotations Complete (Optional)

   - MutationAnnotator implementation
   - Unit and integration tests
   - Schema orchestrator integration
   - Documentation

   This phase is optional and adds mutation metadata for frontend cache invalidation."
   ```

**Milestone**: Phase 3 complete! ✅

---

### **Phase 3 Deliverables**:

**Files Created** (4 files):
- ✅ src/generators/fraiseql/mutation_annotator.py (150 lines)
- ✅ tests/unit/fraiseql/test_mutation_annotator.py (100 lines)
- ✅ tests/integration/fraiseql/test_mutation_annotations_e2e.py (100 lines)
- ✅ docs/fraiseql/MUTATION_ANNOTATIONS.md (100 lines)

**Files Modified** (2 files):
- ✅ src/generators/schema_orchestrator.py (+10 lines)
- ✅ src/generators/fraiseql/__init__.py (+1 line)

**Total Lines**: ~461 lines

**Acceptance Criteria**:
- ✅ Mutation annotations generated
- ✅ metadata_mapping includes _meta field
- ✅ Integration with action compiler works
- ✅ All tests pass
- ✅ Code quality checks pass
- ✅ Documentation complete

---

## 📊 Complete Timeline Summary

### **Week 5**

| Day | Phase | Duration | Tasks | Deliverables |
|-----|-------|----------|-------|--------------|
| **Day 1** | Phase 1 | 1-2h | Rich Types Verification | 8 files, 805 lines |

**Outcome**: ✅ FraiseQL autodiscovery confirmed working

---

### **Week 6**

| Week | Status | Notes |
|------|--------|-------|
| **Week 6** | ⏸️ **PAUSE** | Gap between phases, work on other teams or projects |

---

### **Week 7**

| Day | Phase | Duration | Tasks | Deliverables |
|-----|-------|----------|-------|--------------|
| **Day 1** | Phase 2 (Part 1) | 8h | RED + GREEN phases | TableViewAnnotator implemented, tests passing |
| **Day 2** | Phase 2 (Part 2) | 8h | REFACTOR + QA | Integration complete, docs written, QA verified |
| **Day 3** | Phase 3 (Optional) | 4-6h | All phases | Mutation annotations complete |

**Outcome**: ✅ Complete FraiseQL integration ready for production

---

## 📋 Daily Checklists

### **Week 5, Day 1 Checklist** (Phase 1)

#### Morning (9:00 - 11:00 AM)

**RED Phase** (30 min):
- [ ] Create test directories
- [ ] Create contact_with_rich_types.yaml fixture
- [ ] Write test_email_field_has_check_constraint
- [ ] Write test_email_field_has_comment
- [ ] Run tests (should fail)

**GREEN Phase** (30 min):
- [ ] Create fraiseql package
- [ ] Implement CompatibilityChecker class
- [ ] Run tests (should pass)

**REFACTOR Phase** (30 min):
- [ ] Write RICH_TYPES_INTEGRATION.md
- [ ] Add unit tests for CompatibilityChecker
- [ ] Run all tests

**QA Phase** (30 min):
- [ ] Run all fraiseql tests
- [ ] Run ruff and mypy
- [ ] Generate sample schema
- [ ] Verify comments in output
- [ ] Git commit

**End of Day**:
- [ ] Phase 1 complete
- [ ] 8 files created
- [ ] All tests passing
- [ ] Documentation written

---

### **Week 7, Day 1 Checklist** (Phase 2 - Part 1)

#### Morning (9:00 AM - 12:00 PM)

**RED Phase** (3 hours):
- [ ] Create test_table_view_annotator.py
- [ ] Write TestTableAnnotation tests (2 tests)
- [ ] Write TestInternalColumnAnnotations tests (3 tests)
- [ ] Write TestFilterColumnAnnotations tests (4 tests)
- [ ] Write TestDataColumnAnnotation tests (1 test)
- [ ] Write TestSQLTypeMapping tests (1 test)
- [ ] Create review_with_table_views.yaml fixture
- [ ] Run tests (all should fail)

#### Afternoon (1:00 PM - 5:00 PM)

**GREEN Phase** (4 hours):
- [ ] Create table_view_annotator.py
- [ ] Implement TableViewAnnotator class
- [ ] Implement generate_annotations method
- [ ] Implement _annotate_table method
- [ ] Implement _annotate_internal_columns method
- [ ] Implement _annotate_filter_columns method
- [ ] Implement _annotate_data_column method
- [ ] Implement helper methods
- [ ] Run unit tests (all should pass)
- [ ] Update __init__.py exports
- [ ] Manual REPL test

**End of Day**:
- [ ] 12 unit tests written
- [ ] TableViewAnnotator implemented (300 lines)
- [ ] All unit tests passing

---

### **Week 7, Day 2 Checklist** (Phase 2 - Part 2)

#### Morning (9:00 AM - 12:00 PM)

**REFACTOR Phase** (3 hours):
- [ ] Update schema_orchestrator.py
- [ ] Test orchestrator integration manually
- [ ] Commit orchestrator integration
- [ ] Write test_tv_annotations_e2e.py (5 tests)
- [ ] Run integration tests (all should pass)
- [ ] Write TV_ANNOTATIONS.md documentation
- [ ] Add docstrings to table_view_annotator.py

#### Afternoon (1:00 PM - 5:00 PM)

**QA Phase** (4 hours):
- [ ] Run all unit tests
- [ ] Run all integration tests
- [ ] Generate coverage report (≥90%)
- [ ] Run ruff linter (fix issues)
- [ ] Run mypy type checker (fix issues)
- [ ] Format all code
- [ ] Run bandit security check
- [ ] Apply migration to test database
- [ ] Verify table structure in DB
- [ ] Verify column comments in DB
- [ ] Verify @fraiseql annotations
- [ ] Review all changes
- [ ] Run final test suite
- [ ] Clean up test database
- [ ] Create comprehensive commit
- [ ] **Phase 2 complete!**

**End of Day**:
- [ ] Phase 2 complete
- [ ] 5 new files created
- [ ] 2 files modified
- [ ] All tests passing
- [ ] ≥90% coverage
- [ ] Code quality verified
- [ ] Database verification complete

---

### **Week 7, Day 3 Checklist** (Phase 3 - Optional)

#### Morning (9:00 AM - 1:00 PM)

**RED Phase** (1 hour):
- [ ] Create test_mutation_annotator.py
- [ ] Write TestMutationAnnotation tests (4 tests)
- [ ] Run tests (should fail)

**GREEN Phase** (1 hour):
- [ ] Create mutation_annotator.py
- [ ] Implement MutationAnnotator class
- [ ] Implement generate_mutation_annotation method
- [ ] Implement helper methods
- [ ] Run tests (should pass)

**REFACTOR Phase** (1 hour):
- [ ] Update schema_orchestrator.py
- [ ] Write test_mutation_annotations_e2e.py
- [ ] Write MUTATION_ANNOTATIONS.md

**QA Phase** (1 hour):
- [ ] Run all tests
- [ ] Code quality checks
- [ ] Manual verification
- [ ] Git commit
- [ ] **Phase 3 complete!**

**End of Day**:
- [ ] Phase 3 complete (optional)
- [ ] 4 new files created
- [ ] 2 files modified
- [ ] All tests passing

---

## 🎯 Success Metrics

### **Phase 1 Success Criteria**:
- ✅ Tests execute in < 5 seconds
- ✅ 100% test pass rate
- ✅ Zero manual annotations required
- ✅ CompatibilityChecker confirms 100% compatibility
- ✅ Documentation reviewed and approved

### **Phase 2 Success Criteria**:
- ✅ All 12 unit tests pass
- ✅ All 5 integration tests pass
- ✅ Test coverage ≥ 90%
- ✅ Zero linting errors
- ✅ Zero type errors
- ✅ Annotations visible in database
- ✅ FraiseQL can introspect (manual verification)

### **Phase 3 Success Criteria** (Optional):
- ✅ All 4 unit tests pass
- ✅ Integration test passes
- ✅ Annotations generated for all actions
- ✅ Documentation complete

---

## 🚨 Risk Management & Contingencies

### **Phase 1 Risks**:

**Risk**: FraiseQL autodiscovery doesn't work
- **Likelihood**: Very Low
- **Impact**: High
- **Mitigation**: Test immediately in Phase 1
- **Contingency**: Add manual annotations in compatibility_checker (adds 2-3 hours)

**Risk**: PostgreSQL comments not generated by Team B
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**: Verify Team B output has comments
- **Contingency**: Coordinate with Team B to add comments (1 hour)

---

### **Phase 2 Risks**:

**Risk**: Complex SQL type mapping edge cases
- **Likelihood**: Medium
- **Impact**: Low
- **Mitigation**: Comprehensive test coverage
- **Contingency**: Add specialized type handlers (adds 1-2 hours)

**Risk**: Integration with schema_orchestrator breaks existing functionality
- **Likelihood**: Low
- **Impact**: High
- **Mitigation**: Run full test suite after integration
- **Contingency**: Isolate Team D code in separate section (1 hour)

**Risk**: FraiseQL cannot parse generated annotations
- **Likelihood**: Low
- **Impact**: High
- **Mitigation**: Manual FraiseQL introspection test in QA phase
- **Contingency**: Adjust annotation format based on FraiseQL docs (2-3 hours)

---

### **Phase 3 Risks**:

**Risk**: Time constraint - cannot complete Phase 3
- **Likelihood**: Medium
- **Impact**: Low (Phase 3 is optional)
- **Mitigation**: Clear prioritization, Phase 3 is optional
- **Contingency**: Defer Phase 3 entirely (saves 4-6 hours)

**Risk**: Action impact metadata format changes
- **Likelihood**: Low
- **Impact**: Medium
- **Mitigation**: Follow established patterns from Team C
- **Contingency**: Adjust format, update tests (1-2 hours)

---

## 📈 Progress Tracking

### **Daily Stand-up Template**:

```markdown
## Team D Daily Stand-up - [Date]

### Yesterday:
- [x] Completed X
- [x] Completed Y
- [ ] Blocked on Z

### Today:
- [ ] Plan to complete A
- [ ] Plan to complete B

### Blockers:
- None / [Describe blocker]

### On Track:
- ✅ Yes, on schedule
- ⚠️ At risk (reason)
- 🔴 Behind schedule (reason)
```

---

### **Phase Completion Report Template**:

```markdown
## Phase [N] Completion Report

**Date**: [Date]
**Duration**: [Actual hours] (Planned: [X] hours)
**Status**: ✅ Complete / ⚠️ Partial / 🔴 Blocked

### Deliverables:
- [x] File 1 created
- [x] File 2 created
- [x] Tests written (X/X passing)
- [x] Documentation complete

### Metrics:
- Test coverage: [X]%
- Lines of code: [X]
- Tests passing: [X]/[X]

### Issues Encountered:
- [None / List issues]

### Lessons Learned:
- [Key takeaways]

### Next Steps:
- [Next phase / tasks]
```

---

## 🎓 Learning Opportunities

### **Phase 1 Learning**:
- FraiseQL autodiscovery capabilities
- PostgreSQL comment introspection
- Integration testing strategies

### **Phase 2 Learning**:
- Complex annotation generation
- SQL type mapping
- Database metadata patterns
- CQRS read-layer optimization

### **Phase 3 Learning**:
- Mutation impact tracking
- Frontend cache invalidation patterns
- GraphQL metadata best practices

---

## 📚 Reference Materials

### **Quick Links**:
- Phase 1 Plan: `docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md` (lines 39-353)
- Phase 2 Plan: `docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md` (lines 355-1729)
- Phase 3 Plan: `docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md` (lines 1731-1872)

### **Documentation**:
- FraiseQL Integration: `docs/fraiseql/RICH_TYPES_INTEGRATION.md`
- tv_ Annotations: `docs/fraiseql/TV_ANNOTATIONS.md`
- Mutation Annotations: `docs/fraiseql/MUTATION_ANNOTATIONS.md`

### **Test Examples**:
- Rich types: `entities/examples/contact_with_rich_types.yaml`
- Table views: `entities/examples/review_with_table_views.yaml`

---

## 🎯 Final Checklist (All Phases Complete)

### **Implementation**:
- [ ] Phase 1: compatibility_checker.py
- [ ] Phase 2: table_view_annotator.py
- [ ] Phase 3: mutation_annotator.py (optional)

### **Tests**:
- [ ] Phase 1: Unit + integration tests passing
- [ ] Phase 2: Unit + integration tests passing (≥90% coverage)
- [ ] Phase 3: Unit + integration tests passing (optional)

### **Documentation**:
- [ ] Phase 1: RICH_TYPES_INTEGRATION.md
- [ ] Phase 2: TV_ANNOTATIONS.md
- [ ] Phase 3: MUTATION_ANNOTATIONS.md (optional)

### **Integration**:
- [ ] schema_orchestrator.py updated
- [ ] All generators exported in __init__.py
- [ ] No breaking changes to existing code

### **Quality**:
- [ ] All tests passing
- [ ] Code coverage ≥ 90%
- [ ] Ruff linting clean
- [ ] Mypy type checking clean
- [ ] Bandit security check clean
- [ ] Database verification complete

### **Git**:
- [ ] Phase 1 committed
- [ ] Phase 2 committed
- [ ] Phase 3 committed (if completed)
- [ ] All commit messages descriptive

---

## 🚀 Ready to Execute!

**Total Timeline**: 3-4 days across Week 5 and Week 7

**Estimated Completion**:
- Phase 1: 1-2 hours
- Phase 2: 2 days
- Phase 3: Half day (optional)

**Success Rate**: High (clear plan, comprehensive tests, well-documented)

**Risk Level**: Low (incremental phases, optional Phase 3, comprehensive QA)

---

**Team D is ready to execute this detailed timeline!** 🎉

Each phase has:
- ✅ Hour-by-hour breakdown
- ✅ Clear tasks and milestones
- ✅ Test-first approach (TDD)
- ✅ Quality gates at each step
- ✅ Comprehensive checklists
- ✅ Risk mitigation strategies
- ✅ Progress tracking templates

**Follow this timeline for predictable, high-quality delivery!**
