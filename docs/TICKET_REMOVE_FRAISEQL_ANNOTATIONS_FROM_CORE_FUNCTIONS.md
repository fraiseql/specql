# Ticket: Remove FraiseQL Annotations from Core Layer Functions

**Priority**: Low
**Type**: Documentation Cleanup
**Status**: Open
**Created**: 2025-11-09
**Estimated Effort**: 10-15 minutes

---

## 📋 Summary

Core layer functions (e.g., `crm.create_contact`, `projects.assign_task`) currently have `@fraiseql:mutation` annotations in their comments. These annotations should be removed because:

1. **Only app layer functions are exposed to GraphQL** - FraiseQL introspects `app.*` functions, not `schema.*` functions
2. **Core functions are internal** - They are called by app layer functions, not exposed to GraphQL API
3. **Annotations are misleading** - Having `@fraiseql:mutation` on internal functions suggests they're GraphQL-exposed

---

## 🎯 Objective

Remove all `@fraiseql:mutation` annotations from core layer functions while keeping clear documentation about their purpose.

---

## 📍 Affected Files

### **File 1: `db/schema/30_functions/create_contact.sql`**

**Location**: Lines 139-146

**Current Code:**
```sql
COMMENT ON FUNCTION crm.create_contact IS
  '@fraiseql:mutation
   name=createContact
   input=CreateContactInput
   success_type=CreateContactSuccess
   error_type=CreateContactError
   primary_entity=Contact
   metadata_mapping={}';
```

**Should Be:**
```sql
COMMENT ON FUNCTION crm.create_contact IS
'Core business logic for creating Contact records.

Handles:
- Input validation
- Trinity pattern FK resolution (UUID → INTEGER)
- INSERT operation
- Audit logging via app.log_and_return_mutation

Called by: app.create_contact (GraphQL-exposed mutation)
Returns: app.mutation_result';
```

---

### **File 2: `db/schema/30_functions/qualify_lead.sql`**

**Expected Issue**: Likely has similar `@fraiseql:mutation` annotation

**Recommended Fix:**
```sql
COMMENT ON FUNCTION crm.qualify_lead IS
'Core business logic for qualifying a lead as a customer.

Validates:
- Contact exists
- Contact has status = "lead"

Performs:
- Status update to "qualified"
- Audit logging

Called by: app.qualify_lead (GraphQL-exposed mutation)
Returns: app.mutation_result';
```

---

### **Other Files to Check:**

Scan all files in `db/schema/30_functions/` for `@fraiseql:mutation` annotations:

```bash
grep -r "@fraiseql:mutation" db/schema/30_functions/
```

Any core layer function with this annotation should be updated.

---

## ✅ Acceptance Criteria

- [ ] All `@fraiseql:mutation` annotations removed from core layer functions
- [ ] Core functions have clear, descriptive comments explaining:
  - What the function does
  - What it validates
  - What operations it performs
  - Which app layer function calls it
  - What it returns
- [ ] No `@fraiseql:*` annotations remain on internal/core functions
- [ ] Documentation clearly distinguishes:
  - **App layer** (`app.*`): GraphQL-exposed, has `@fraiseql:mutation`
  - **Core layer** (`schema.*`): Internal business logic, NO annotations

---

## 📚 Context: App Layer vs Core Layer

### **App Layer Functions** (`app.*`)

**Purpose**: API entry points (GraphQL/REST)

**Responsibilities**:
- Accept JSONB input
- Convert JSONB → Typed Composite
- Delegate to core business logic
- Handle unexpected errors

**Comment Format**:
```sql
COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';
```

**Key**: ✅ **MUST have** `@fraiseql:mutation` annotation (GraphQL-exposed)

---

### **Core Layer Functions** (`schema.*`)

**Purpose**: Business logic implementation

**Responsibilities**:
- Business rule validation
- Trinity pattern FK resolution
- Data manipulation (INSERT/UPDATE/DELETE)
- Audit logging

**Comment Format**:
```sql
COMMENT ON FUNCTION crm.create_contact IS
'Core business logic for creating Contact records.

Validates input, resolves foreign keys, performs INSERT,
and logs to audit table.

Called by: app.create_contact
Returns: app.mutation_result';
```

**Key**: ❌ **MUST NOT have** `@fraiseql:*` annotations (internal only)

---

## 🔧 Implementation Steps

### **Step 1: Identify Affected Functions**

```bash
cd /home/lionel/code/printoptim_backend_poc

# Find all @fraiseql:mutation annotations in core functions
grep -r "@fraiseql:mutation" db/schema/30_functions/

# Expected output:
# db/schema/30_functions/create_contact.sql:COMMENT ON FUNCTION crm.create_contact IS '@fraiseql:mutation...'
# db/schema/30_functions/qualify_lead.sql:COMMENT ON FUNCTION crm.qualify_lead IS '@fraiseql:mutation...'
```

---

### **Step 2: Update Each Function Comment**

For each affected file:

1. Open file
2. Find `COMMENT ON FUNCTION schema.*` statement
3. Remove `@fraiseql:mutation` annotation
4. Replace with descriptive comment (see templates above)
5. Save file

---

### **Step 3: Verify Changes**

```bash
# Ensure no @fraiseql annotations remain in core functions
grep -r "@fraiseql" db/schema/30_functions/

# Expected: No results (or only in app layer functions if mixed)

# Verify app layer functions still have annotations
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep "app\."

# Expected: Only app.* functions
```

---

### **Step 4: Regenerate SQL if Needed**

If using code generation:

```bash
# Regenerate SQL from YAML
python scripts/dev/generate_sql.py

# Verify changes are preserved
git diff db/schema/30_functions/
```

---

## 📝 Example: Before & After

### **Before (Incorrect)**

```sql
-- Core layer function (internal)
CREATE OR REPLACE FUNCTION crm.create_contact(...) RETURNS app.mutation_result AS $$
...
$$;

COMMENT ON FUNCTION crm.create_contact IS
  '@fraiseql:mutation
   name=createContact
   input=CreateContactInput
   success_type=CreateContactSuccess
   error_type=CreateContactError
   primary_entity=Contact
   metadata_mapping={}';
```

**Problems:**
- ❌ Has `@fraiseql:mutation` (suggests GraphQL exposure)
- ❌ No human-readable description
- ❌ Field names inconsistent (`input` instead of `input_type`)
- ❌ Misleading (this function is NOT exposed to GraphQL)

---

### **After (Correct)**

```sql
-- Core layer function (internal)
CREATE OR REPLACE FUNCTION crm.create_contact(...) RETURNS app.mutation_result AS $$
...
$$;

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

**Benefits:**
- ✅ Clear, descriptive documentation
- ✅ No misleading annotations
- ✅ Explains what the function does
- ✅ Documents relationship to app layer

---

## 🎯 Why This Matters

### **For FraiseQL Introspection**

FraiseQL introspects **app layer functions only**:
```python
# FraiseQL searches for functions with @fraiseql:mutation
functions = introspector.discover_functions(schema="app")

# Only app.create_contact is found (correct)
# crm.create_contact is NOT introspected (correct)
```

Having `@fraiseql:mutation` on core functions:
- ❌ Could confuse FraiseQL (if it searches all schemas)
- ❌ Misleads developers (suggests GraphQL exposure)
- ❌ Violates separation of concerns

---

### **For Code Clarity**

Clear separation:
- **App layer**: "This is exposed to GraphQL" (`@fraiseql:mutation` present)
- **Core layer**: "This is internal business logic" (NO annotations)

Developers can quickly understand:
- Which functions are public API (app layer)
- Which functions are internal (core layer)

---

## 📊 Related Files (No Changes Needed)

These files are **correct as-is**:

### **✅ App Layer Functions (Keep Annotations)**

```sql
-- File: db/schema/30_functions/create_contact.sql
COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';
```

**Status**: ✅ Correct (GraphQL-exposed, needs annotation)

---

### **✅ Composite Types (Keep Annotations)**

```sql
COMMENT ON TYPE app.type_create_contact_input IS
'Input parameters for Create Contact.

@fraiseql:composite
name: CreateContactInput
tier: 2';
```

**Status**: ✅ Correct (FraiseQL introspects composite types)

---

### **✅ Utility Functions (No Annotations)**

```sql
COMMENT ON FUNCTION app.log_and_return_mutation IS
'Logs mutation to audit table and returns standardized result.

Internal utility function used by all mutations.
Not exposed to GraphQL.';
```

**Status**: ✅ Correct (utility function, no annotation needed)

---

## 🚀 Testing After Changes

### **Test 1: Verify No Regressions**

```bash
# Run all tests
pytest tests/

# Expected: All tests pass (comments don't affect functionality)
```

---

### **Test 2: Verify FraiseQL Introspection (Future)**

When FraiseQL Phase 5 is implemented:

```python
# Test that only app layer functions are introspected
from fraiseql.introspection import PostgresIntrospector

introspector = PostgresIntrospector(connection)
functions = introspector.discover_functions(schema="app")

# Should find: app.create_contact, app.qualify_lead, etc.
# Should NOT find: crm.create_contact, crm.qualify_lead, etc.

assert "create_contact" in [f.function_name for f in functions]
```

---

## 📞 Questions?

**For SpecQL Team:**
- See: `/tmp/specql_comment_format_guide.md` (comment format specification)
- See: `/tmp/printoptim_backend_poc_comment_format_analysis.md` (full analysis)

**For PrintOptim Backend POC Team:**
- Slack: #specql-printoptim
- GitHub: Create issue if needed

---

## ✅ Checklist

- [ ] Identify all core functions with `@fraiseql:mutation` annotations
- [ ] Update `db/schema/30_functions/create_contact.sql`
- [ ] Update `db/schema/30_functions/qualify_lead.sql`
- [ ] Update any other affected core functions
- [ ] Verify no `@fraiseql` annotations remain on core functions
- [ ] Verify app layer functions still have annotations
- [ ] Run tests (if any)
- [ ] Commit changes with message: "docs: Remove @fraiseql annotations from core layer functions"

---

**Status**: Ready for implementation
**Assignee**: SpecQL/PrintOptim Backend Team
**Estimated Time**: 10-15 minutes

---

## 📚 References

- **Comment Format Guide**: `/tmp/specql_comment_format_guide.md`
- **Analysis Report**: `/tmp/printoptim_backend_poc_comment_format_analysis.md`
- **FraiseQL Boundaries**: `/home/lionel/code/fraiseql/docs/architecture/SPECQL_FRAISEQL_BOUNDARIES.md`
