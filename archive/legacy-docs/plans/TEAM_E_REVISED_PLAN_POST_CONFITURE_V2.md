# Team E Implementation Plan - Revised Post-Confiture v0.2.0 (v2)

**Date**: November 9, 2025
**Status**: 🟢 IN PROGRESS - Phase 3.2 Complete, Moving to Phase 3.3
**Previous Version**: TEAM_E_REVISED_PLAN_POST_CONFITURE.md
**Current Progress**: ~70% complete (Confiture integration working!)

---

## 🎉 Progress Update

### ✅ What Team E Has ALREADY Completed

**Phase 1**: Cleanup & Confiture Integration (DONE!)
- ✅ Confiture v0.2.0 installed (`fraiseql-confiture` dependency)
- ✅ Confiture directory structure created (`db/schema/`)
- ✅ `confiture_extensions.py` created (SpecQL CLI wrapper)
- ✅ Orchestrator updated for Confiture output
- ✅ Tests passing

**Phase 2**: Dual-Mode Output (DONE!)
- ✅ Confiture-compatible output format working
- ✅ Files written to `db/schema/10_tables/`, `30_functions/`, `40_metadata/`
- ✅ Registry integration functional (`use_registry` parameter)

**Phase 3.1-3.2**: Confiture Integration (DONE!)
- ✅ `db/schema/` directory structure created with all layers
- ✅ `confiture_extensions.py` provides SpecQL commands
- ✅ End-to-end workflow working: SpecQL → Confiture → SQL

**Current Files**:
```
src/cli/
├── confiture_extensions.py  ✅ (97 lines - SpecQL CLI wrapper)
├── orchestrator.py          ✅ (310 lines - Updated for Confiture)
├── generate.py              ✅ (139 lines - Original CLI still works)
├── validate.py              ✅ (84 lines - SpecQL validation)
├── docs.py                  ✅ (221 lines - Doc generation)
├── diff.py                  ✅ (149 lines - SpecQL diff)
└── migrate.py               ⚠️  (91 lines - Wrapper around Confiture)

db/schema/
├── 00_foundation/           ✅ (App foundation layer)
├── 10_tables/               ✅ (Team B DDL output)
├── 20_helpers/              ✅ (Trinity helper functions)
├── 30_functions/            ✅ (Team C actions output)
└── 40_metadata/             ✅ (Team D FraiseQL annotations)
```

---

## 🎯 What Remains: Phases 3.3 - 4

### **Phase 3.3: FraiseQL Annotation Cleanup** (NEW - From Ticket)

**Context**: Found ticket `docs/TICKET_REMOVE_FRAISEQL_ANNOTATIONS_FROM_CORE_FUNCTIONS.md`

**Issue**: Core layer functions (e.g., `crm.create_contact`) have `@fraiseql:mutation` annotations, but they shouldn't because:
- Only **app layer** functions (`app.*`) are exposed to GraphQL
- Core layer functions are **internal business logic**, called by app layer
- Annotations are misleading (suggest GraphQL exposure when they're internal)

**Correct Pattern**:
```sql
-- ✅ App layer (GraphQL-exposed) - KEEP @fraiseql:mutation
COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';

-- ✅ Core layer (Internal) - REMOVE @fraiseql:mutation
COMMENT ON FUNCTION crm.create_contact IS
'Core business logic for creating Contact records.

Validation:
- Validates company_id exists (if provided)
- Checks tenant_id context

Operations:
- Resolves company UUID → INTEGER (Trinity pattern)
- Inserts new contact record
- Logs audit trail

Called by: app.create_contact (GraphQL mutation)
Returns: app.mutation_result with success/failure status';
```

**Action Items**:

1. **Update Team D** (FraiseQL Metadata Generator)
   - `src/generators/fraiseql/mutation_annotator.py`
   - **ONLY** annotate `app.*` functions with `@fraiseql:mutation`
   - **SKIP** annotations for `schema.*` (core) functions
   - Add descriptive comments for core functions instead

2. **Update existing generated SQL** (10-15 min manual cleanup)
   ```bash
   # Find core functions with annotations
   grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep -v "app\."

   # Expected files to update:
   # - db/schema/30_functions/create_contact.sql (crm.create_contact)
   # - db/schema/30_functions/qualify_lead.sql (crm.qualify_lead)
   # - Any other core functions
   ```

3. **Update mutation_annotator.py logic**:
   ```python
   # src/generators/fraiseql/mutation_annotator.py

   def generate_mutation_comment(self, action: Action, entity: Entity) -> str:
       """Generate COMMENT for both app and core layer functions"""

       # App layer function (GraphQL-exposed)
       app_comment = f"""
   COMMENT ON FUNCTION app.{action.name} IS
   '{action.description}

   @fraiseql:mutation
   name: {to_camel_case(action.name)}
   input_type: app.type_{action.name}_input
   success_type: {to_pascal_case(action.name)}Success
   failure_type: {to_pascal_case(action.name)}Error';
   """

       # Core layer function (Internal - NO @fraiseql annotation!)
       core_comment = f"""
   COMMENT ON FUNCTION {entity.schema}.{action.name} IS
   'Core business logic for {action.description}.

   Validation:
   - {self._generate_validation_list(action)}

   Operations:
   - Trinity FK resolution (UUID → INTEGER)
   - {action.operation_type} operation
   - Audit logging

   Called by: app.{action.name} (GraphQL mutation)
   Returns: app.mutation_result';
   """

       return app_comment + "\n\n" + core_comment
   ```

**Testing**:
```bash
# After fix, verify no core functions have annotations
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep -v "app\."
# Expected: No results

# Verify app functions still have them
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep "app\."
# Expected: Only app.* functions
```

**Estimated Time**: 4 hours
- 1h: Update `mutation_annotator.py`
- 1h: Regenerate affected SQL files
- 1h: Manual cleanup of existing files
- 1h: Testing + verification

---

### **Phase 3.4: Documentation Updates** (1 day)

**Files to Update**:

1. **`.claude/CLAUDE.md`** - Team D section (FraiseQL Metadata)
   ```markdown
   ## Team D: FraiseQL Metadata Generator

   **IMPORTANT**: Only annotate **app layer** functions!

   **Annotation Rules**:
   - ✅ `app.*` functions → Add `@fraiseql:mutation` (GraphQL-exposed)
   - ❌ `schema.*` functions → NO annotations (internal business logic)
   - ✅ Composite types → Add `@fraiseql:composite` (FraiseQL introspects these)
   - ✅ Table columns → Add `@fraiseql:field` (for GraphQL field mapping)

   **Example**:
   ```sql
   -- ✅ App layer - HAS annotation
   COMMENT ON FUNCTION app.create_contact IS '@fraiseql:mutation...';

   -- ✅ Core layer - NO annotation, descriptive comment instead
   COMMENT ON FUNCTION crm.create_contact IS 'Core business logic...';
   ```
   ```

2. **`README.md`** - Update quick start to mention annotation separation
   ```markdown
   ### FraiseQL Integration

   **Two-Layer Architecture**:
   - **App Layer** (`app.*`): GraphQL API entry points with `@fraiseql:mutation`
   - **Core Layer** (`schema.*`): Internal business logic, NO annotations

   FraiseQL introspects **only** the app layer for GraphQL schema generation.
   ```

3. **`docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md`**
   - Add note about annotation layer separation
   - Update examples to show both layers

4. **New Guide**: `docs/guides/FRAISEQL_ANNOTATION_LAYERS.md`
   - Comprehensive guide on when to annotate vs. when not to
   - Examples of both app and core layer patterns
   - Troubleshooting guide

**Estimated Time**: 6 hours

---

### **Phase 4: Frontend Code Generation** (Already Planned, No Changes)

This phase was correctly planned in the original document. No changes needed.

**Estimated Time**: 12 hours (2 days)

---

## 📅 Revised Timeline (From Current State)

### **Week 1: Remaining Work** (Nov 9-15)

**Day 1**: FraiseQL Annotation Cleanup - Code (4h)
- Update `mutation_annotator.py`
- Regenerate affected SQL
- Test annotation separation

**Day 2**: FraiseQL Annotation Cleanup - Verification (4h)
- Manual cleanup of existing files
- Comprehensive testing
- Verify FraiseQL introspection works correctly (if available)

**Day 3**: Documentation Updates (6h)
- Update all Team D documentation
- Create annotation layers guide
- Update README and CLAUDE.md

**Day 4**: Buffer + Integration Testing (6h)
- Full end-to-end testing
- Verify no regressions
- Document known issues

**Total Week 1**: 20 hours (remaining work from 70% → 80%)

---

### **Week 2: Frontend Code Generation** (Nov 16-22)

**Day 5-6**: Mutation Impacts Generator (12h)
- `src/generators/frontend/mutation_impacts_generator.py`
- `src/generators/frontend/typescript_types_generator.py`
- `src/generators/frontend/apollo_hooks_generator.py`
- `src/generators/frontend/mutation_docs_generator.py`

**Day 7**: CLI Integration (4h)
- Add `--with-impacts` flag to `generate` command
- Add `--output-frontend` option
- Integration testing

**Day 8**: Polish & Final Testing (4h)
- Documentation
- Examples
- Final QA

**Total Week 2**: 20 hours (80% → 95%)

---

### **Grand Total Remaining**: 40 hours (5 days @ 8h/day)

**Previous Total**: 10 weeks (80 hours)
**Completed**: ~70% (56 hours)
**Remaining**: ~30% (40 hours - revised up due to annotation cleanup)

---

## 🎯 Updated Success Criteria

### Phase 3.3: FraiseQL Annotation Cleanup ✅
- [ ] `mutation_annotator.py` updated to skip core function annotations
- [ ] Existing SQL files cleaned up (no `@fraiseql:mutation` on core functions)
- [ ] App layer functions still have annotations
- [ ] Core layer functions have descriptive comments
- [ ] Tests passing
- [ ] FraiseQL introspection only finds app layer functions (verified if FraiseQL available)

### Phase 3.4: Documentation Updates ✅
- [ ] `.claude/CLAUDE.md` updated (Team D section)
- [ ] `README.md` updated (annotation section)
- [ ] `docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md` updated
- [ ] New guide: `docs/guides/FRAISEQL_ANNOTATION_LAYERS.md`

### Phase 4: Frontend Code Generation ✅
- [ ] `mutation-impacts.json` generator working
- [ ] TypeScript type definitions generator working
- [ ] Apollo/React hooks generator working
- [ ] Mutation documentation generator working
- [ ] `--with-impacts` flag working
- [ ] `--output-frontend` option working

---

## 📊 File Structure (Updated with Annotation Cleanup)

### Generated SQL Structure

```
db/schema/
├── 00_foundation/
│   └── app_foundation.sql              ✅ (App layer types, helper functions)
│
├── 10_tables/
│   └── contact.sql                     ✅ (Team B DDL)
│       -- CREATE TABLE crm.tb_contact
│       -- COMMENT ON TABLE: @fraiseql:type (correct!)
│       -- COMMENT ON COLUMN: @fraiseql:field (correct!)
│
├── 20_helpers/
│   └── contact_helpers.sql             ✅ (Trinity helper functions)
│       -- contact_pk(), contact_id(), etc.
│       -- NO @fraiseql annotations (utilities)
│
├── 30_functions/
│   └── contact.sql                     ⚠️  (Needs cleanup!)
│       -- App layer (GraphQL-exposed)
│       COMMENT ON FUNCTION app.create_contact IS
│         '@fraiseql:mutation...'       ✅ KEEP
│
│       -- Core layer (Internal)
│       COMMENT ON FUNCTION crm.create_contact IS
│         '@fraiseql:mutation...'       ❌ REMOVE! (This is the issue)
│
│       -- Should be:
│       COMMENT ON FUNCTION crm.create_contact IS
│         'Core business logic...'      ✅ CORRECT
│
└── 40_metadata/
    └── contact.sql                     ✅ (Team D FraiseQL annotations)
        -- COMMENT ON TABLE: Additional metadata
        -- COMMENT ON COLUMN: Additional field metadata
```

---

## 🔧 Annotation Cleanup Implementation

### **Step 1: Update mutation_annotator.py**

**File**: `src/generators/fraiseql/mutation_annotator.py`

**Changes**:

```python
# src/generators/fraiseql/mutation_annotator.py

class MutationAnnotator:
    """Generate FraiseQL annotations for mutations"""

    def annotate_mutation(self, action: Action, entity: Entity) -> str:
        """
        Generate COMMENT statements for both app and core layer functions

        IMPORTANT: Only app layer gets @fraiseql:mutation annotation!
        Core layer gets descriptive human-readable comment instead.
        """
        annotations = []

        # 1. App layer function (GraphQL-exposed) - WITH annotation
        app_comment = self._generate_app_layer_comment(action, entity)
        annotations.append(app_comment)

        # 2. Core layer function (Internal) - WITHOUT annotation
        core_comment = self._generate_core_layer_comment(action, entity)
        annotations.append(core_comment)

        return "\n\n".join(annotations)

    def _generate_app_layer_comment(self, action: Action, entity: Entity) -> str:
        """Generate @fraiseql:mutation annotation for app layer"""

        mutation_name = to_camel_case(action.name)
        success_type = f"{to_pascal_case(action.name)}Success"
        error_type = f"{to_pascal_case(action.name)}Error"

        return f"""COMMENT ON FUNCTION app.{action.name} IS
'{action.description or f"Performs {action.name} operation on {entity.name}"}.

@fraiseql:mutation
name: {mutation_name}
input_type: app.type_{action.name}_input
success_type: {success_type}
failure_type: {error_type}';"""

    def _generate_core_layer_comment(self, action: Action, entity: Entity) -> str:
        """Generate descriptive comment for core layer (NO @fraiseql annotation!)"""

        # Build validation list
        validations = self._extract_validations(action)
        validation_text = "\n".join(f"- {v}" for v in validations) if validations else "- Input validation"

        # Build operation description
        operation = self._get_operation_type(action)  # "INSERT", "UPDATE", "DELETE"

        return f"""COMMENT ON FUNCTION {entity.schema}.{action.name} IS
'Core business logic for {action.description or action.name}.

Validation:
{validation_text}

Operations:
- Trinity FK resolution (UUID → INTEGER)
- {operation} operation on {entity.schema}.tb_{entity.name.lower()}
- Audit logging via app.log_and_return_mutation

Called by: app.{action.name} (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';"""

    def _extract_validations(self, action: Action) -> List[str]:
        """Extract validation steps from action"""
        validations = []
        for step in action.steps:
            if step.get("validate"):
                validations.append(step["validate"])
        return validations

    def _get_operation_type(self, action: Action) -> str:
        """Determine operation type from action steps"""
        for step in action.steps:
            if "insert" in step:
                return "INSERT"
            elif "update" in step:
                return "UPDATE"
            elif "delete" in step:
                return "DELETE"
        return "OPERATION"
```

---

### **Step 2: Regenerate Affected SQL Files**

```bash
# Regenerate all entities to apply new annotation logic
python -m src.cli.generate entities/examples/*.yaml --output-dir db/schema

# Verify changes
git diff db/schema/30_functions/

# Expected changes:
# - App layer functions: Still have @fraiseql:mutation ✅
# - Core layer functions: @fraiseql:mutation removed, descriptive comment added ✅
```

---

### **Step 3: Manual Cleanup (If Needed)**

If any core functions still have old annotations:

```bash
# Find affected files
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep -v "app\." > /tmp/cleanup_list.txt

# For each file in cleanup_list.txt:
# 1. Open file
# 2. Find COMMENT ON FUNCTION schema.function_name
# 3. Replace @fraiseql:mutation block with descriptive comment
# 4. Save

# Example fix:
# Before:
COMMENT ON FUNCTION crm.create_contact IS
  '@fraiseql:mutation
   name=createContact
   input=CreateContactInput
   success_type=CreateContactSuccess
   error_type=CreateContactError';

# After:
COMMENT ON FUNCTION crm.create_contact IS
'Core business logic for creating Contact records.

Validation:
- Validates company_id exists (if provided)
- Checks tenant_id context

Operations:
- Resolves company UUID → INTEGER (Trinity pattern)
- Inserts new contact record
- Logs audit trail

Called by: app.create_contact (GraphQL mutation)
Returns: app.mutation_result';
```

---

### **Step 4: Verify Cleanup**

```bash
# Test 1: No core functions should have @fraiseql:mutation
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep -v "app\."
# Expected: No results ✅

# Test 2: App functions should still have annotations
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep "app\."
# Expected: All app.* functions listed ✅

# Test 3: Verify core functions have descriptive comments
grep -A 10 "COMMENT ON FUNCTION crm\." db/schema/30_functions/create_contact.sql
# Expected: Should see descriptive comment, NOT @fraiseql:mutation ✅

# Test 4: Run all tests
uv run pytest tests/ -v
# Expected: All tests pass ✅
```

---

## 🎯 Key Takeaways

### **What Changed from Original Plan**

1. **Added Phase 3.3**: FraiseQL Annotation Cleanup (from ticket)
   - Team D needs to differentiate app vs. core layer annotations
   - ~4 hours of work

2. **Team E Already 70% Done**!
   - Confiture integration working
   - Directory structure created
   - CLI commands functional

3. **Only 40 Hours Remaining** (down from 80)
   - Annotation cleanup: 4h
   - Documentation: 6h
   - Frontend codegen: 20h
   - Polish + buffer: 10h

---

## 📚 Related Tickets & Documentation

**Tickets**:
- `docs/TICKET_REMOVE_FRAISEQL_ANNOTATIONS_FROM_CORE_FUNCTIONS.md` ⚠️ (NEW - Must address)

**Implementation Plans**:
- `docs/implementation-plans/TEAM_E_REVISED_PLAN_POST_CONFITURE.md` (v1 - superseded by this)
- `docs/implementation-plans/CLEANUP_OPPORTUNITY_POST_CONFITURE.md` (cleanup guide)
- `docs/implementation-plans/EXECUTIVE_SUMMARY_CONFITURE_INTEGRATION.md` (ROI analysis)

**Team Docs**:
- `docs/teams/TEAM_E_CURRENT_STATE.md` (update status to 70%)
- `docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md` (update for annotation layers)

---

## ✅ Final Checklist

### Phase 3.3: FraiseQL Annotation Cleanup
- [ ] Update `mutation_annotator.py` to skip core annotations
- [ ] Regenerate SQL files with new logic
- [ ] Manual cleanup of existing files (if needed)
- [ ] Verify no core functions have `@fraiseql:mutation`
- [ ] Verify app functions still have annotations
- [ ] All tests passing

### Phase 3.4: Documentation
- [ ] Update `.claude/CLAUDE.md` (Team D)
- [ ] Update `README.md`
- [ ] Update Team D plan
- [ ] Create annotation layers guide

### Phase 4: Frontend Codegen
- [ ] Mutation impacts generator
- [ ] TypeScript types generator
- [ ] Apollo hooks generator
- [ ] Mutation docs generator
- [ ] CLI integration (`--with-impacts`, `--output-frontend`)
- [ ] Examples working

### Final QA
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Examples working
- [ ] Team E marked 95% complete

---

**Status**: 🟢 READY TO CONTINUE (Phase 3.3 - Annotation Cleanup)
**Current Progress**: 70% → Target: 95%
**Remaining Time**: 40 hours (5 days)
**Next Action**: Update `mutation_annotator.py` for annotation layer separation

---

*Last Updated*: November 9, 2025
*Version*: 2.0 (Reflects current state + annotation cleanup ticket)
*Author*: Claude Code
