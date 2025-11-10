# Team E: Next Actions Summary

**Date**: November 9, 2025
**Current Status**: 70% Complete (Phase 3.2 Done)
**Next Phase**: 3.3 - FraiseQL Annotation Cleanup

---

## 🎯 Quick Summary

**Good News**: Team E is **70% done** - way ahead of original schedule!
- ✅ Confiture integration working
- ✅ Directory structure created
- ✅ CLI commands functional

**Important Discovery**: Found ticket requiring FraiseQL annotation cleanup
- Core layer functions shouldn't have `@fraiseql:mutation` annotations
- Only app layer functions should have them
- ~4 hours of work

**Remaining Work**: 40 hours (5 days)
- Annotation cleanup: 4h
- Documentation: 6h
- Frontend codegen: 20h
- Polish: 10h

---

## 🚀 Immediate Next Steps (This Week)

### **Action 1: Fix FraiseQL Annotations** (4 hours - HIGH PRIORITY)

**Problem**: Core functions have `@fraiseql:mutation` when they shouldn't

**Example of Issue**:
```sql
-- ❌ WRONG: Core function with GraphQL annotation
COMMENT ON FUNCTION crm.create_contact IS
  '@fraiseql:mutation
   name=createContact
   ...';  -- This suggests it's GraphQL-exposed, but it's internal!

-- ✅ CORRECT: Core function with descriptive comment
COMMENT ON FUNCTION crm.create_contact IS
'Core business logic for creating Contact records.
...
Called by: app.create_contact (GraphQL mutation)';
```

**What to Do**:

1. **Update Code Generator** (2h)
   ```bash
   # Edit the file that generates mutation comments
   vim src/generators/fraiseql/mutation_annotator.py

   # Make it generate TWO different comments:
   # - app.* functions: @fraiseql:mutation annotation ✅
   # - schema.* functions: descriptive comment only ✅
   ```

2. **Regenerate SQL** (1h)
   ```bash
   # Regenerate all entities with fixed logic
   python -m src.cli.generate entities/examples/*.yaml

   # Verify changes
   git diff db/schema/30_functions/
   ```

3. **Manual Cleanup** (30min)
   ```bash
   # Find any remaining issues
   grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep -v "app\."

   # Manually fix each file if needed
   ```

4. **Verify** (30min)
   ```bash
   # Test 1: Core functions should NOT have annotations
   grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep -v "app\."
   # Expected: No results

   # Test 2: App functions SHOULD have annotations
   grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep "app\."
   # Expected: All app.* functions

   # Test 3: Run tests
   uv run pytest tests/ -v
   ```

**Reference**: `docs/TICKET_REMOVE_FRAISEQL_ANNOTATIONS_FROM_CORE_FUNCTIONS.md`

---

### **Action 2: Update Documentation** (6 hours)

**Files to Update**:

1. **`.claude/CLAUDE.md`** (1h)
   - Update Team D section
   - Add annotation layer rules
   - Examples of app vs. core layer

2. **`README.md`** (1h)
   - Add FraiseQL annotation section
   - Explain two-layer architecture

3. **`docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md`** (1h)
   - Add annotation separation notes
   - Update examples

4. **Create new guide** (3h)
   ```bash
   # Create comprehensive guide
   vim docs/guides/FRAISEQL_ANNOTATION_LAYERS.md

   # Contents:
   # - When to use @fraiseql:mutation (app layer only!)
   # - When NOT to use it (core layer)
   # - Examples of both patterns
   # - Troubleshooting guide
   ```

---

## 📅 This Week's Schedule

**Monday (Today)**: Annotation Cleanup - Code
- Update `mutation_annotator.py` (2h)
- Regenerate SQL files (1h)
- Manual cleanup (30min)
- Testing (30min)

**Tuesday**: Annotation Cleanup - Verification
- Comprehensive testing (2h)
- Fix any issues found (2h)

**Wednesday**: Documentation
- Update `.claude/CLAUDE.md` (1h)
- Update `README.md` (1h)
- Update Team D docs (1h)
- Start annotation layers guide (3h)

**Thursday**: Documentation + Buffer
- Finish annotation layers guide
- Integration testing
- Fix any discovered issues

**Friday**: Wrap Up Week
- Final testing
- Document known issues
- Prepare for Week 2 (frontend codegen)

---

## 📊 Progress Tracking

### Current State (70%)
```
✅ Phase 1: Cleanup & Confiture Integration (DONE)
✅ Phase 2: Dual-Mode Output (DONE)
✅ Phase 3.1: Confiture Integration - Install (DONE)
✅ Phase 3.2: Confiture Integration - Structure (DONE)
🔄 Phase 3.3: FraiseQL Annotation Cleanup (IN PROGRESS)
⏸️  Phase 3.4: Documentation Updates (NEXT)
⏸️  Phase 4: Frontend Code Generation (WEEK 2)
```

### Target State (95%)
```
✅ Phase 1: Cleanup & Confiture Integration
✅ Phase 2: Dual-Mode Output
✅ Phase 3: Confiture Integration (all sub-phases)
✅ Phase 4: Frontend Code Generation
✅ Final QA & Polish
```

---

## 🎯 Success Criteria for This Week

**By Friday, should have**:
- [ ] No core functions with `@fraiseql:mutation` annotations
- [ ] All app functions still have annotations
- [ ] `mutation_annotator.py` updated to handle both layers correctly
- [ ] All documentation updated
- [ ] New annotation layers guide created
- [ ] All tests passing
- [ ] Team E at **80% complete** (ready for frontend codegen next week)

---

## 🔍 How to Verify Everything Works

### **Test 1: Annotation Separation**
```bash
# Should find ZERO core functions with annotations
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep "crm\.\|projects\.\|catalog\." | wc -l
# Expected: 0

# Should find ALL app functions with annotations
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep "app\." | wc -l
# Expected: Number of actions across all entities
```

### **Test 2: Code Quality**
```bash
# Run all tests
uv run pytest tests/ -v

# Type checking
uv run mypy src/generators/fraiseql/

# Linting
uv run ruff check src/generators/fraiseql/
```

### **Test 3: End-to-End**
```bash
# Generate from SpecQL
python -m src.cli.generate entities/examples/contact_lightweight.yaml

# Check output structure
ls -R db/schema/

# Verify no regressions
git diff db/schema/ | grep "@fraiseql:mutation"
```

---

## 📚 Key Reference Documents

**Created Today**:
1. `TEAM_E_REVISED_PLAN_POST_CONFITURE_V2.md` - Complete updated plan
2. `CLEANUP_OPPORTUNITY_POST_CONFITURE.md` - What to remove/simplify
3. `EXECUTIVE_SUMMARY_CONFITURE_INTEGRATION.md` - ROI analysis
4. `TEAM_E_NEXT_ACTIONS.md` - This document

**Existing References**:
1. `docs/TICKET_REMOVE_FRAISEQL_ANNOTATIONS_FROM_CORE_FUNCTIONS.md` - The issue to fix
2. `docs/teams/TEAM_E_CURRENT_STATE.md` - Team E status (update to 70%)
3. `docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md` - Team D (needs update)

---

## 💡 Pro Tips

### **For Annotation Cleanup**:
- Don't manually edit every file - fix the generator, then regenerate
- Test on one entity first (Contact) before regenerating all
- Keep a backup before regenerating: `cp -r db/schema db/schema.backup`

### **For Documentation**:
- Use concrete examples (actual SQL from generated files)
- Include "before/after" comparisons
- Add troubleshooting section ("Why am I seeing X?")

### **For Testing**:
- Test the unhappy paths too (what if annotation is malformed?)
- Verify FraiseQL introspection works (if you have FraiseQL available)
- Check that generated GraphQL schema only includes app layer functions

---

## 🚨 Potential Issues & Solutions

### **Issue 1**: Regenerating overwrites manual changes
**Solution**: Make all changes in generators, not in generated SQL

### **Issue 2**: Some core functions need different annotations
**Solution**: Use conditional logic in `mutation_annotator.py` based on schema name

### **Issue 3**: Tests fail after annotation changes
**Solution**: Tests shouldn't depend on specific comment formats - if they do, update tests

### **Issue 4**: FraiseQL introspects core functions
**Solution**: This is the whole point of the fix! After cleanup, FraiseQL should only find app layer

---

## ✅ Quick Checklist for Today

**Morning** (4h):
- [ ] Read the ticket: `docs/TICKET_REMOVE_FRAISEQL_ANNOTATIONS_FROM_CORE_FUNCTIONS.md`
- [ ] Open `src/generators/fraiseql/mutation_annotator.py`
- [ ] Implement two-comment logic (app vs. core)
- [ ] Test on Contact entity first

**Afternoon** (4h):
- [ ] Regenerate all entities
- [ ] Manual cleanup if needed
- [ ] Run tests
- [ ] Commit changes
- [ ] Update status: Team E → 75% complete

---

**Status**: 🟢 READY TO START
**Priority**: HIGH (blocking FraiseQL integration correctness)
**Estimated Time**: 4 hours for annotation fix, 6 hours for docs
**Next Review**: Tomorrow EOD (verify annotation cleanup complete)

---

*Last Updated*: November 9, 2025
*For*: Team E Development
*Created By*: Claude Code
