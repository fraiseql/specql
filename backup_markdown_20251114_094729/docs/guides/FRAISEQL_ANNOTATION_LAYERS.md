# FraiseQL Annotation Layers Guide

**Purpose**: Comprehensive guide on when to annotate vs. when not to annotate functions for FraiseQL GraphQL auto-discovery.

---

## 🎯 Core Principle

**FraiseQL introspects ONLY the GraphQL API layer**, not internal business logic.

---

## 🏗️ Two-Layer Architecture

### **Layer 1: App Layer** (`app.*` functions)
- **Purpose**: GraphQL API entry points
- **Annotation**: ✅ `@fraiseql:mutation` REQUIRED
- **Discovery**: ✅ Exposed to GraphQL schema
- **Example**: `app.create_contact()`

### **Layer 2: Core Layer** (`schema.*` functions)
- **Purpose**: Internal business logic
- **Annotation**: ❌ NO `@fraiseql:mutation`
- **Discovery**: ❌ Hidden from GraphQL
- **Example**: `crm.create_contact()`

---

## 📋 Annotation Rules

### ✅ **WHEN TO ANNOTATE**

#### **App Layer Functions** (`app.*`)
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

**Why**: These are the GraphQL API endpoints that users call.

#### **Composite Types** (`app.type_*`)
```sql
COMMENT ON TYPE app.type_create_contact_input IS
'@fraiseql:composite
name: CreateContactInput
tier: 1
storage: composite';
```

**Why**: FraiseQL needs to know about input/output types.

#### **Table Columns** (for field mapping)
```sql
COMMENT ON COLUMN crm.tb_contact.email IS
'@fraiseql:field name=email,type=String!';
```

**Why**: Maps PostgreSQL columns to GraphQL fields.

### ❌ **WHEN NOT TO ANNOTATE**

#### **Core Layer Functions** (`crm.*`, `projects.*`, etc.)
```sql
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

**Why**: These are internal implementation details, not API endpoints.

#### **Helper Functions** (Trinity utilities)
```sql
COMMENT ON FUNCTION crm.contact_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_contact.';
```

**Why**: Utilities don't need GraphQL exposure.

---

## 🔍 How FraiseQL Discovers Schema

### **Discovery Process**

1. **Scans** all `COMMENT ON FUNCTION` statements
2. **Finds** functions with `@fraiseql:mutation`
3. **Extracts** GraphQL schema from annotations
4. **Ignores** functions without annotations

### **Result**

- **Annotated functions** → GraphQL mutations
- **Non-annotated functions** → Hidden from GraphQL

---

## 📝 Implementation Examples

### **Complete Mutation Pair**

```sql
-- ============================================================================
-- MUTATION: create_contact
-- Entity: Contact
-- Pattern: App Wrapper + Core Logic + FraiseQL Metadata
-- ============================================================================

-- ============================================================================
-- APP WRAPPER: create_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_contact(
    auth_tenant_id UUID,
    auth_user_id UUID,
    input_payload JSONB
) RETURNS app.mutation_result AS $$
BEGIN
    -- Delegate to core business logic
    RETURN crm.create_contact(auth_tenant_id, input_data, input_payload, auth_user_id);
END;
$$ LANGUAGE plpgsql;

-- ✅ ANNOTATED: GraphQL API endpoint
COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';

-- ============================================================================
-- CORE LOGIC: crm.create_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION crm.create_contact(
    auth_tenant_id UUID,
    input_data app.type_create_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result AS $$
BEGIN
    -- Business logic implementation
    INSERT INTO crm.tb_contact (...) VALUES (...);
    RETURN app.log_and_return_mutation(...);
END;
$$ LANGUAGE plpgsql;

-- ❌ NOT ANNOTATED: Internal business logic
COMMENT ON FUNCTION crm.create_contact IS
'Core business logic for creating Contact records.

Validation:
- Validates company_id exists (if provided)
- Checks tenant_id context

Operations:
- Trinity FK resolution (UUID → INTEGER)
- Inserts new contact record
- Logs audit trail

Called by: app.create_contact (GraphQL mutation)
Returns: app.mutation_result';
```

---

## 🚨 Common Mistakes

### ❌ **Mistake: Annotating Core Functions**

```sql
-- WRONG: Core function should not have @fraiseql:mutation
COMMENT ON FUNCTION crm.create_contact IS
'@fraiseql:mutation
 name=createContact
 ...';
```

**Problem**: FraiseQL will try to expose internal functions as GraphQL mutations.

### ❌ **Mistake: Missing App Layer Annotations**

```sql
-- WRONG: App function missing @fraiseql:mutation
COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.';
```

**Problem**: GraphQL mutation won't be discovered.

### ❌ **Mistake: Wrong Function Names**

```sql
-- WRONG: Annotated wrong function
COMMENT ON FUNCTION crm.create_contact IS
'@fraiseql:mutation...';

-- App function not annotated
COMMENT ON FUNCTION app.create_contact IS
'Creates a contact.';
```

**Problem**: GraphQL API exposes internal function instead of API wrapper.

---

## 🔧 Troubleshooting

### **GraphQL Mutation Not Found**

**Symptoms**: Mutation doesn't appear in GraphQL schema.

**Checks**:
1. ✅ App function has `@fraiseql:mutation` annotation
2. ✅ Function name matches `app.*` pattern
3. ✅ Annotation syntax is correct
4. ✅ FraiseQL has scanned the database

### **Internal Functions Exposed**

**Symptoms**: Core business logic functions appear as GraphQL mutations.

**Checks**:
1. ❌ Core functions have NO `@fraiseql:mutation` annotations
2. ✅ Only app functions have annotations
3. ✅ Annotations are on `app.*` functions only

### **Validation**

```bash
# Check for incorrectly annotated core functions
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep -v "app\."

# Should return NO results

# Check that app functions are annotated
grep -r "@fraiseql:mutation" db/schema/30_functions/ | grep "app\."

# Should return app.* functions
```

---

## 📚 Related Documentation

- `docs/TICKET_REMOVE_FRAISEQL_ANNOTATIONS_FROM_CORE_FUNCTIONS.md` - Original issue
- `docs/teams/TEAM_D_PHASED_IMPLEMENTATION_PLAN.md` - Team D implementation
- `src/generators/fraiseql/mutation_annotator.py` - Implementation code

---

## 🎯 Key Takeaways

1. **App layer** = GraphQL API (annotate with `@fraiseql:mutation`)
2. **Core layer** = Business logic (NO annotations, descriptive comments)
3. **FraiseQL discovers only annotated functions**
4. **Separation ensures clean GraphQL schema**

**Result**: GraphQL API exposes only the intended public interface, not internal implementation details.</content>
</xai:function_call: write>
<parameter name="filePath">docs/guides/FRAISEQL_ANNOTATION_LAYERS.md