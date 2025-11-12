# Confiture Integration Pattern Correction

**Date**: 2025-11-09
**Issue**: Implementation plans did not account for "one file per mutation" pattern
**Status**: ✅ **CORRECTED**

---

## 🚨 Problem Identified

The Team E implementation plan specified generating SQL in a way that **bundled all mutations together**, which contradicts the established **App/Core two-layer pattern** from the existing PrintOptim backend.

### What Was Wrong ❌

**Original Plan** (from `TEAM_E_IMPLEMENTATION_PLAN.md`):

```python
@dataclass
class SchemaOutput:
    """Split output for Confiture directory structure"""
    tables_sql: str        # → db/schema/10_tables/
    functions_sql: str     # → db/schema/30_functions/  ❌ ALL ACTIONS BUNDLED!
    metadata_sql: str      # → db/schema/40_metadata/
```

**File Structure**:
```
30_functions/
└── contact_actions.sql    # ❌ Contains ALL mutations for Contact
```

**Problem**: All mutations for an entity were bundled into one file, making it:
- Hard to version control (large diffs)
- Difficult to review (multiple mutations in one PR)
- Impossible to track which specific mutations changed
- Against the established pattern from PrintOptim backend

---

## ✅ Corrected Pattern

### Correct Implementation

**New Plan** (corrected):

```python
@dataclass
class MutationFunctionPair:
    """One mutation = 2 functions (app wrapper + core logic)"""
    action_name: str
    app_wrapper_sql: str      # app.{action_name}()
    core_logic_sql: str       # core.{action_name}()

@dataclass
class SchemaOutput:
    """Split output for Confiture directory structure"""
    table_sql: str                           # → db/schema/10_tables/{entity}.sql
    helpers_sql: str                         # → db/schema/20_helpers/{entity}_helpers.sql
    mutations: List[MutationFunctionPair]    # → db/schema/30_functions/{action_name}.sql (ONE FILE EACH!)
    table_metadata_sql: str                  # → db/schema/40_metadata/{entity}_table_metadata.sql
    mutations_metadata_sql: str              # → db/schema/40_metadata/{entity}_mutations_metadata.sql
```

**File Structure**:
```
db/schema/
├── 10_tables/
│   └── contact.sql               # Table definition
├── 20_helpers/
│   └── contact_helpers.sql       # Trinity helpers (contact_pk, contact_id, etc.)
├── 30_functions/                 # ✅ ONE FILE PER MUTATION
│   ├── create_contact.sql        # app.create_contact() + core.create_contact()
│   ├── update_contact.sql        # app.update_contact() + core.update_contact()
│   └── qualify_lead.sql          # app.qualify_lead() + core.qualify_lead()
└── 40_metadata/
    ├── contact_table_metadata.sql
    └── contact_mutations_metadata.sql
```

---

## 📝 Files Updated

### 1. `/docs/teams/TEAM_E_IMPLEMENTATION_PLAN.md`

**Changes**:
- ✅ Updated directory structure to show 5 layers (00, 10, 20, 30, 40)
- ✅ Added `20_helpers/` layer for utility functions
- ✅ Clarified that `30_functions/` has **ONE FILE PER MUTATION**
- ✅ Updated `SchemaOutput` dataclass specification
- ✅ Added `MutationFunctionPair` dataclass
- ✅ Updated orchestrator logic to write one file per mutation
- ✅ Updated `confiture.yaml` example with 5 layers
- ✅ Updated file structure section with detailed examples

### 2. `/.claude/CLAUDE.md`

**Changes**:
- ✅ Added **CRITICAL FILE PATTERN** warning to Team E section
- ✅ Referenced new architecture document

### 3. `/docs/architecture/ONE_FILE_PER_MUTATION_PATTERN.md` (NEW)

**Content**:
- ✅ Detailed specification of the pattern
- ✅ Complete file structure examples
- ✅ Example SQL file content
- ✅ Anti-patterns (what NOT to do)
- ✅ Implementation requirements for SchemaOrchestrator
- ✅ Implementation requirements for CLIOrchestrator
- ✅ Benefits and rationale
- ✅ Migration steps from current implementation

---

## 🎯 Key Takeaways

### Pattern Requirements

**MUST DO** ✅:
1. Each mutation gets its own SQL file
2. Each file contains exactly 2 functions:
   - `app.{action_name}()` - App wrapper (JSONB → typed input, delegates)
   - `core.{action_name}()` - Core logic (business rules, validation, audit)
3. File name matches action name (e.g., `qualify_lead.sql`)
4. Utility functions (Trinity helpers) in separate `20_helpers/` directory

**MUST NOT DO** ❌:
1. Bundle multiple mutations in one file
2. Mix helper functions with mutation functions
3. Separate app wrapper and core logic into different files

### Benefits

| Benefit | Impact |
|---------|--------|
| **Modularity** | Each mutation is independent |
| **Version Control** | Git diffs focus on single mutations |
| **Code Review** | Reviewers see complete mutation in one place |
| **Testing** | Can test mutations in isolation |
| **Debugging** | Easy to locate specific mutation code |
| **Refactoring** | Safe to refactor one mutation without risk |

---

## 🔧 Implementation Impact

### Components Affected

1. **`SchemaOrchestrator.generate_split_schema()`**
   - Must iterate over actions
   - Generate separate `app_wrapper_sql` + `core_logic_sql` for each
   - Return `List[MutationFunctionPair]` not single `functions_sql`

2. **`CLIOrchestrator.generate_from_files()`**
   - Must loop over mutations
   - Write one file per mutation
   - Create proper directory structure

3. **`AppWrapperGenerator`**
   - Already generates per-action (✅ no change needed)

4. **`CoreLogicGenerator`**
   - Already generates per-action (✅ no change needed)

5. **Tests**
   - Must verify correct file structure
   - Check that each mutation has its own file
   - Verify 2 functions per file

---

## 📊 Before vs After

### Before (WRONG ❌)

**Entity: Contact with 3 actions (create, update, qualify_lead)**

Generated Files:
```
30_functions/
└── contact_actions.sql    # 6 functions bundled together
```

Problems:
- Hard to see what changed in version control
- Code review difficult (too much in one file)
- Can't track individual mutation history

### After (CORRECT ✅)

**Entity: Contact with 3 actions (create, update, qualify_lead)**

Generated Files:
```
20_helpers/
└── contact_helpers.sql           # 3 utility functions

30_functions/
├── create_contact.sql            # 2 functions
├── update_contact.sql            # 2 functions
└── qualify_lead.sql              # 2 functions
```

Benefits:
- Clear version history per mutation
- Easy code review (one mutation at a time)
- Individual mutation can be rolled back
- Helpers separated from business logic

---

## 🚀 Next Steps

### For Implementation

1. **Update `SchemaOrchestrator`**:
   - Modify `generate_split_schema()` to return `List[MutationFunctionPair]`
   - Iterate over actions, generate separate SQL for each

2. **Update `CLIOrchestrator`**:
   - Loop over mutations in `SchemaOutput.mutations`
   - Write one file per mutation to `30_functions/{action_name}.sql`

3. **Update Tests**:
   - Verify file count matches action count
   - Check each file has exactly 2 functions
   - Validate file naming convention

4. **Update Documentation**:
   - ✅ DONE: Implementation plans corrected
   - ✅ DONE: Architecture document created
   - ✅ DONE: CLAUDE.md updated

---

## 📚 References

- **Architecture Spec**: `/docs/architecture/ONE_FILE_PER_MUTATION_PATTERN.md`
- **App/Core Pattern**: `/docs/architecture/APP_CORE_FUNCTION_PATTERN.md`
- **Team E Plan**: `/docs/teams/TEAM_E_IMPLEMENTATION_PLAN.md`
- **PrintOptim Backend**: `../printoptim_backend/db/0_schema/03_functions/` (reference implementation)

---

## ✅ Verification Checklist

When implementing, verify:

- [ ] `generate_split_schema()` returns `List[MutationFunctionPair]`
- [ ] Each `MutationFunctionPair` has `app_wrapper_sql` + `core_logic_sql`
- [ ] Orchestrator writes one file per mutation
- [ ] File name matches action name exactly
- [ ] Each file has comment header with mutation info
- [ ] Helper functions in separate `20_helpers/` directory
- [ ] Confiture can build from 5-layer structure
- [ ] Tests verify correct file structure
- [ ] Git diff shows individual mutations clearly

---

**Status**: 📋 **DOCUMENTED** - Ready for implementation
**Priority**: 🔴 **CRITICAL** - Required for proper version control and modularity
**Owner**: Team E (CLI & Orchestration)
