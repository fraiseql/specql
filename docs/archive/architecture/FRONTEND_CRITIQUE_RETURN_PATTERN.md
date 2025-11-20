# Frontend Developer Critique: Return Value Pattern

## The Proposed Pattern

```json
{
  "success": true,
  "affected_entities": [
    {
      "entity": "Contact",
      "id": "uuid-1",
      "modified_fields": {"status": "qualified", "updated_at": "..."}
    },
    {
      "entity": "Notification",
      "id": "uuid-2",
      "operation": "insert",
      "modified_fields": {"message": "Done", "created_at": "..."}
    }
  ]
}
```

## Critical Issues from Frontend Perspective

### ❌ Issue 1: Type Safety is Destroyed

**Problem:** The `modified_fields` object is completely dynamic. TypeScript can't help you.

```typescript
// What the frontend gets:
interface AffectedEntity {
  entity: string;  // Just a string! Not a type!
  id: string;
  modified_fields: Record<string, any>;  // Any! Type safety gone!
}

// What the frontend dev has to write:
const contact = affectedEntities.find(e => e.entity === 'Contact');
if (contact) {
  // No autocomplete here ↓
  const status = contact.modified_fields['status'];  // string? number? who knows!
  const email = contact.modified_fields['email'];    // Might not exist!
}
```

**What they want:**
```typescript
// Fully typed response
interface QualifyLeadResponse {
  contact: Contact;  // Real type!
  createdNotifications: Notification[];
}

// Beautiful autocomplete and type checking
const { contact, createdNotifications } = result.data.qualifyLead;
contact.status  // ✅ TypeScript knows this is ContactStatus enum
contact.email   // ✅ TypeScript knows this is string
```

### ❌ Issue 2: Apollo/Relay Cache Updates are MANUAL

**Problem:** Apollo Client and Relay have sophisticated cache management that works automatically with standard GraphQL responses. Our pattern breaks this.

```typescript
// With our pattern - MANUAL HELL:
const { data } = await qualifyLead({ variables: { contactId } });

// Frontend dev has to manually update cache for EVERY entity type:
data.affectedEntities.forEach(entity => {
  switch(entity.entity) {
    case 'Contact':
      // Manual cache write
      cache.writeFragment({
        id: cache.identify({ __typename: 'Contact', id: entity.id }),
        fragment: gql`fragment ContactFields on Contact {
          ${Object.keys(entity.modified_fields).join(' ')}
        }`,
        data: entity.modified_fields
      });
      break;
    case 'Notification':
      // More manual cache writes...
      // This is tedious and error-prone!
      break;
  }
});
```

**What they want (Apollo does it automatically):**
```typescript
const { data } = await qualifyLead({ variables: { contactId } });
// ✨ Cache is automatically updated! No extra code!
```

This works because Apollo uses `__typename` + `id` to automatically normalize and update the cache when you return full objects.

### ❌ Issue 3: Partial Data Problem

**Problem:** Frontend only gets modified fields. What about fields that are displayed but weren't modified?

**Scenario:**
```tsx
// Frontend is displaying:
function ContactCard({ contact }) {
  return (
    <div>
      <h2>{contact.email}</h2>           {/* Not modified */}
      <p>Status: {contact.status}</p>     {/* Modified */}
      <p>Company: {contact.company.name}</p>  {/* Not modified */}
    </div>
  );
}
```

**After mutation with our pattern:**
```json
{
  "entity": "Contact",
  "id": "uuid-1",
  "modified_fields": {"status": "qualified", "updated_at": "..."}
}
```

Frontend only has `status` and `updated_at`. Where is:
- ❌ `email` (needed for display)
- ❌ `company.name` (needed for display)

**Options (all bad):**
1. **Refetch entire Contact** - Extra roundtrip! Defeats the purpose!
2. **Merge with cache** - Hope cache isn't stale
3. **Partial UI update** - Half the component updates, half shows old data (janky UX)

**What they want:**
```graphql
mutation QualifyLead($contactId: UUID!) {
  qualifyLead(contactId: $contactId) {
    contact {
      id
      email        # Get EVERYTHING needed for UI
      status       # in ONE response
      company {
        id
        name
      }
    }
  }
}
```

One roundtrip, complete data, UI fully updates.

### ❌ Issue 4: Optimistic UI is Nearly Impossible

**Problem:** Frontend can't predict the response structure to show optimistic updates.

```typescript
// With our pattern - how do you predict this?
const [qualifyLead] = useMutation(QUALIFY_LEAD, {
  optimisticResponse: {
    qualifyLead: {
      affectedEntities: [
        {
          entity: 'Contact',
          id: contactId,
          modified_fields: {
            status: 'qualified',  // Ok, we can predict this
            updated_at: ???,      // Don't know the timestamp
            // What other fields will be here?
          }
        },
        {
          entity: 'Notification',  // Wait, will a notification be created?
          id: ???,                  // Don't know the ID
          modified_fields: ???      // Don't know what's in it
        }
      ]
    }
  }
});
```

**What they want:**
```typescript
const [qualifyLead] = useMutation(QUALIFY_LEAD, {
  optimisticResponse: {
    qualifyLead: {
      contact: {
        __typename: 'Contact',
        id: contactId,
        status: 'qualified',  // Can predict this
        ...currentContact     // Merge with current data
      },
      createdNotifications: []  // Know structure even if empty
    }
  }
});
```

Predictable structure = good optimistic UI = smooth UX.

### ❌ Issue 5: Breaks GraphQL Conventions

**Problem:** Apollo and Relay expect specific response shapes. Our pattern breaks their assumptions.

**Apollo/Relay expect:**
```graphql
type Contact {
  __typename: String!  # For cache normalization
  id: ID!              # For cache key
  status: String!      # Fields at top level
  email: String!
}
```

**Our pattern gives:**
```json
{
  "entity": "Contact",      // Not __typename!
  "id": "...",
  "modified_fields": {      // Fields nested, not at top level!
    "status": "qualified"
  }
}
```

Apollo's cache key: `Contact:uuid-1`
Our structure: Doesn't match! Cache key must be constructed manually.

### ❌ Issue 6: Relationship Data Missing

**Problem:** Relationships aren't included unless they were modified.

```yaml
# SpecQL action:
- update: Contact SET status = 'qualified'
```

```json
// Response:
{
  "entity": "Contact",
  "modified_fields": {"status": "qualified"}
}
```

Frontend needs to display `contact.company.name`. It's not in the response!

**Options:**
1. Make separate query for company (2 roundtrips total)
2. Hope it's in Apollo cache (might be stale)
3. Refetch entire contact (defeats purpose)

**What they want:**
```graphql
mutation QualifyLead {
  qualifyLead(contactId: $id) {
    contact {
      id
      status
      company {  # Can request relationships!
        id
        name
      }
    }
  }
}
```

### ❌ Issue 7: Array of Heterogeneous Types

**Problem:** `affected_entities` array can contain different entity types. GraphQL doesn't handle this elegantly without unions.

```json
{
  "affected_entities": [
    {"entity": "Contact", ...},      // Different type
    {"entity": "Notification", ...}, // Different type
    {"entity": "Task", ...}          // Different type
  ]
}
```

**Frontend has to:**
```typescript
data.affectedEntities.forEach(entity => {
  switch(entity.entity) {  // Manual type discrimination
    case 'Contact':
      // Handle Contact
      break;
    case 'Notification':
      // Handle Notification
      break;
    // ... more cases
  }
});
```

**What they want (if using unions):**
```graphql
mutation QualifyLead {
  qualifyLead(contactId: $id) {
    affectedEntities {
      __typename  # GraphQL's type discriminator
      ... on Contact {
        id
        status
      }
      ... on Notification {
        id
        message
      }
    }
  }
}
```

TypeScript discriminated unions work automatically with `__typename`.

### ❌ Issue 8: Error Handling is Unclear

**Problem:** What if step 2 succeeds but step 3 fails?

```json
{
  "success": false,  // or true? Partial success?
  "affected_entities": [
    {"entity": "Contact", ...}  // This succeeded
    // Notification creation failed - is it in array or not?
  ],
  "errors": ???  // Where do errors go?
}
```

**What they want:**
```graphql
type QualifyLeadPayload {
  contact: Contact       # Null if failed
  createdNotifications: [Notification!]!  # Empty if failed
  errors: [MutationError!]!  # Always present
}

type MutationError {
  code: String!
  message: String!
  field: String
  path: [String!]
}
```

Clear, typed error structure.

### ❌ Issue 9: Performance - Forced to Over-fetch

**Problem:** Frontend dev, scared of missing data, does this:

```typescript
// Step 1: Mutation
const { data } = await qualifyLead({ variables: { contactId } });

// Step 2: Immediately refetch to get complete data
const { data: fullData } = await getContact({ variables: { id: contactId } });
```

**Two roundtrips instead of one!** The partial data problem forces this.

## What Real-World GraphQL APIs Do

### Pattern A: Action-Specific Payloads (Shopify, GitHub, Stripe)

```graphql
mutation QualifyLead($input: QualifyLeadInput!) {
  qualifyLead(input: $input) {
    # Primary entity - full object
    contact {
      id
      email
      status
      updatedAt
      company {
        id
        name
      }
    }

    # Side effects - full objects
    createdNotifications {
      id
      message
      createdAt
    }

    # Errors
    errors {
      code
      message
      field
    }
  }
}
```

**Pros:**
- ✅ Fully typed
- ✅ Apollo auto-cache
- ✅ Easy optimistic UI
- ✅ Complete data in one roundtrip
- ✅ Clear primary vs. side effects

**Cons:**
- Each mutation has unique shape (but that's OK! It matches business intent)

### Pattern B: Union Types (Relay)

```graphql
mutation QualifyLead($input: QualifyLeadInput!) {
  qualifyLead(input: $input) {
    entities {
      __typename
      ... on Contact {
        id
        status
        email
        company { id name }
      }
      ... on Notification {
        id
        message
        createdAt
      }
    }
  }
}
```

**Pros:**
- ✅ Typed (via unions)
- ✅ Apollo handles `__typename` automatically
- ✅ More flexible than bespoke shapes

**Cons:**
- Less clear what's primary vs. side effect

## Recommended Solution for This Project

### Generate Action-Specific Return Types

Instead of generic `affected_entities`, generate typed responses per action:

#### 1. Enhanced SpecQL to Declare Returns

```yaml
actions:
  - name: qualify_lead
    returns:
      primary: Contact  # Primary entity
      includes:         # Related data to include
        - company
      side_effects:     # Secondary entities affected
        - Notification
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - insert: Notification(user=Contact.owner, message='Lead qualified')
```

#### 2. Generated PL/pgSQL with Full Objects

```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS jsonb AS $$
DECLARE
    v_pk INTEGER;
    v_notification_ids UUID[];
BEGIN
    -- Trinity resolution
    v_pk := crm.contact_pk(p_contact_id);

    -- Validation
    IF (SELECT status FROM crm.tb_contact WHERE pk_contact = v_pk) != 'lead' THEN
        RAISE EXCEPTION 'validation_failed';
    END IF;

    -- Update
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = now(),
        updated_by = p_caller_id
    WHERE pk_contact = v_pk;

    -- Create notification
    INSERT INTO core.tb_notification (fk_user, message, created_at)
    SELECT fk_owner, 'Lead qualified', now()
    FROM crm.tb_contact WHERE pk_contact = v_pk
    RETURNING id INTO v_notification_ids;

    -- Return FULL objects (not just deltas!)
    RETURN jsonb_build_object(
        'contact', (
            SELECT jsonb_build_object(
                '__typename', 'Contact',
                'id', c.id,
                'email', c.email,
                'status', c.status,
                'updatedAt', c.updated_at,
                'company', jsonb_build_object(
                    '__typename', 'Company',
                    'id', co.id,
                    'name', co.name
                )
            )
            FROM crm.tb_contact c
            LEFT JOIN management.tb_company co ON co.pk_company = c.fk_company
            WHERE c.pk_contact = v_pk
        ),
        'createdNotifications', (
            SELECT COALESCE(jsonb_agg(
                jsonb_build_object(
                    '__typename', 'Notification',
                    'id', n.id,
                    'message', n.message,
                    'createdAt', n.created_at
                )
            ), '[]'::jsonb)
            FROM core.tb_notification n
            WHERE n.id = ANY(v_notification_ids)
        ),
        'errors', '[]'::jsonb
    );
END;
$$ LANGUAGE plpgsql;
```

#### 3. Generated GraphQL Schema

```graphql
input QualifyLeadInput {
  contactId: UUID!
}

type QualifyLeadPayload {
  contact: Contact!
  createdNotifications: [Notification!]!
  errors: [MutationError!]!
}

type Mutation {
  qualifyLead(input: QualifyLeadInput!): QualifyLeadPayload!
}
```

#### 4. Frontend TypeScript (Auto-generated)

```typescript
interface QualifyLeadPayload {
  contact: Contact;  // Fully typed!
  createdNotifications: Notification[];
  errors: MutationError[];
}

// Usage with perfect types:
const { data } = await qualifyLead({ variables: { contactId } });

data.qualifyLead.contact.status  // ✅ TypeScript knows this is ContactStatus
data.qualifyLead.contact.email   // ✅ TypeScript knows this is string
data.qualifyLead.createdNotifications[0].message  // ✅ Fully typed
```

#### 5. Apollo Cache - Automatic!

```typescript
const [qualifyLead] = useMutation(QUALIFY_LEAD);

await qualifyLead({ variables: { contactId } });

// ✨ Apollo automatically updates cache for:
// - Contact (from contact field)
// - Company (from contact.company)
// - Notifications (from createdNotifications)
//
// No manual cache writes needed!
```

#### 6. Optimistic UI - Easy!

```typescript
const [qualifyLead] = useMutation(QUALIFY_LEAD, {
  optimisticResponse: {
    __typename: 'Mutation',
    qualifyLead: {
      __typename: 'QualifyLeadPayload',
      contact: {
        __typename: 'Contact',
        id: contactId,
        status: 'qualified',  // Predictable!
        ...currentContactData
      },
      createdNotifications: [],  // Know structure
      errors: []
    }
  }
});
```

## Comparison Table

| Feature | Proposed Pattern (Delta) | Recommended Pattern (Full Objects) |
|---------|---------------------------|-------------------------------------|
| **Type Safety** | ❌ Lost (any) | ✅ Full TypeScript types |
| **Apollo Auto-Cache** | ❌ Manual writes needed | ✅ Automatic |
| **Optimistic UI** | ❌ Very difficult | ✅ Easy |
| **Data Completeness** | ❌ Partial (modified only) | ✅ Full objects |
| **Relationship Data** | ❌ Not included | ✅ Included |
| **GraphQL Conventions** | ❌ Breaks them | ✅ Follows them |
| **Error Handling** | ⚠️ Unclear | ✅ Clear typed errors |
| **Code Generation** | ✅ Generic | ⚠️ Per-action (but better DX) |
| **Network Efficiency** | ⚠️ Small responses, but often requires refetch | ✅ One roundtrip with complete data |

## Team C Responsibilities (Updated)

### What Team C Should Generate

1. **Action-Specific Return Structures** (not generic)
2. **Full Object Selection** (not just modified fields)
3. **Include Primary Entity + Related Data** (as specified in SpecQL)
4. **Include Side Effects** (secondary entities created/updated)
5. **Standard Error Structure**
6. **Proper `__typename` fields** (for Apollo/Relay)

### Example SpecQL Enhancement

```yaml
entity: Contact
schema: crm

fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead

    # NEW: Explicit return specification
    returns:
      primary: Contact
      include_relations:
        - company  # Automatically include company in response
      side_effects:
        - Notification  # Will be created during action

    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")
```

## Conclusion

**The proposed `affected_entities` pattern is database-centric, not frontend-centric.**

It optimizes for:
- ✅ Easy code generation
- ✅ Generic SQL patterns
- ✅ Minimal complexity in action compiler

But it causes pain for frontend developers:
- ❌ Type safety lost
- ❌ Manual cache management
- ❌ Partial data problems
- ❌ Extra queries/refetches needed
- ❌ Breaks GraphQL conventions
- ❌ Difficult optimistic UI

**Recommendation:**

Generate **action-specific response types** that return **full objects** (not deltas) for:
- Primary entity with requested relationships
- Side-effect entities (newly created/updated)
- Typed error structures

This is **more work for Team C** but provides **vastly better developer experience** and aligns with how GraphQL is actually used in production applications.

**Trade-off:** Less generic code generation, but that's OK because SpecQL is domain-specific anyway. Each action is unique, so unique response shapes make sense.

---

**Bottom Line:** Don't make frontend developers pay for backend convenience. Generate more code on the backend to give frontend devs the typed, complete, cache-friendly responses they expect from GraphQL.
