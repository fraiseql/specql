# Your First Action

> **Add business logic to your SpecQL entities in 10 minutes**

## What You'll Learn

In this tutorial, you'll add a business logic action to qualify leads in a CRM system:
- Validate business rules
- Update entity state
- Send notifications
- All in declarative YAML

**Result**: 6 lines of YAML → 200+ lines of PL/pgSQL + GraphQL mutation

---

## Prerequisites

Complete [Your First Entity](first-entity.md) first. You should have:
- ✅ Contact entity created
- ✅ SpecQL installed
- ✅ Basic YAML knowledge

---

## Step 1: Understand the Business Logic (2 minutes)

**Scenario**: Qualify a lead in our CRM

**Business Rules**:
1. Only contacts with status='lead' can be qualified
2. When qualified, status changes to 'qualified'
3. Customer receives notification email
4. Audit trail is automatically maintained

**Current state**: Manual SQL or application code
**Goal**: Declarative SpecQL action

---

## Step 2: Add the Action (3 minutes)

Edit `entities/contact.yaml`:

```yaml
entity: Contact
schema: crm

fields:
  email: email!
  first_name: text!
  last_name: text!
  phone: phoneNumber
  company: ref(Company)!
  status: enum(lead, qualified, customer) = 'lead'

# Add this actions section
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead', error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: lead_qualified, to: $email
```

**That's it!** Just 6 lines for complete business logic.

---

## Step 3: Generate Code (1 minute)

```bash
specql generate entities/contact.yaml --output generated/
```

**Output**:
```
✅ Generating functions...
   entities/contact.yaml → generated/functions/qualify_lead.sql

✅ Generating GraphQL mutations...
   qualifyLead mutation added to schema

✨ Generated 247 lines from 6 lines of YAML
```

---

## Step 4: Review Generated Code (2 minutes)

### Generated PL/pgSQL Function

**File**: `generated/functions/qualify_lead.sql`

```sql
-- Core business logic function
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID
) RETURNS crm.contact AS $$
DECLARE
    v_contact crm.tb_contact%ROWTYPE;
    v_result crm.contact;
BEGIN
    -- Fetch and lock contact
    SELECT * INTO v_contact
    FROM crm.tb_contact
    WHERE id = p_contact_id
    FOR UPDATE;

    -- Validation: status must be 'lead'
    IF v_contact.status != 'lead' THEN
        RAISE EXCEPTION
            SQLSTATE '23514'
            USING MESSAGE = 'not_a_lead';
    END IF;

    -- Update status
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = NOW(),
        updated_by = current_setting('app.current_user_id', true)::UUID
    WHERE pk_contact = v_contact.pk_contact;

    -- Send notification
    PERFORM pg_notify('lead_qualified', json_build_object(
        'contact_id', v_contact.id,
        'email', v_contact.email
    )::text);

    -- Return updated contact
    SELECT * INTO v_result
    FROM crm.tb_contact
    WHERE pk_contact = v_contact.pk_contact;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- GraphQL wrapper function
CREATE OR REPLACE FUNCTION app.qualify_lead(
    contact_id UUID
) RETURNS app.mutation_result AS $$
DECLARE
    v_result app.mutation_result;
    v_contact crm.contact;
BEGIN
    -- Call core function
    v_contact := crm.qualify_lead(contact_id);

    -- Build success response
    v_result.status := 'success';
    v_result.code := 'lead_qualified';
    v_result.data := row_to_json(v_contact);
    v_result._meta := json_build_object(
        'impacts', json_build_array(
            json_build_object(
                'entity', 'Contact',
                'operation', 'update',
                'ids', array[v_contact.id]
            )
        )
    );

    RETURN v_result;
EXCEPTION
    WHEN SQLSTATE '23514' THEN
        v_result.status := 'error';
        v_result.code := SQLERRM;
        v_result.message := 'Only leads can be qualified';
        RETURN v_result;
    WHEN OTHERS THEN
        v_result.status := 'error';
        v_result.code := 'internal_error';
        v_result.message := SQLERRM;
        RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- FraiseQL annotation
COMMENT ON FUNCTION app.qualify_lead IS $$
@fraiseql:mutation
@fraiseql:entity Contact
@fraiseql:operation update
@fraiseql:impacts [{"entity":"Contact","operation":"update"}]
$$;
```

### Generated GraphQL Mutation

**File**: `generated/graphql/schema.graphql`

```graphql
extend type Mutation {
  qualifyLead(contactId: ID!): MutationResult!
}

type MutationResult {
  status: MutationStatus!
  code: String!
  message: String
  data: Contact
  _meta: MutationMeta
}

enum MutationStatus {
  SUCCESS
  ERROR
}
```

### Generated TypeScript Hook

**File**: `generated/hooks/useQualifyLead.ts`

```typescript
export function useQualifyLead() {
  return useMutation<QualifyLeadResult, QualifyLeadVariables>(
    gql`
      mutation QualifyLead($contactId: ID!) {
        qualifyLead(contactId: $contactId) {
          status
          code
          message
          data {
            id
            email
            firstName
            lastName
            status
          }
        }
      }
    `
  );
}
```

---

## Step 5: Use in Frontend (2 minutes)

```typescript
import { useQualifyLead } from './generated/hooks';

function ContactCard({ contact }) {
  const [qualifyLead, { loading }] = useQualifyLead();

  const handleQualify = async () => {
    const result = await qualifyLead({
      variables: { contactId: contact.id }
    });

    if (result.data.qualifyLead.status === 'success') {
      toast.success('Lead qualified!');
      // Apollo cache automatically updated via impacts
    } else {
      toast.error(result.data.qualifyLead.message);
    }
  };

  if (contact.status !== 'lead') {
    return null; // Only show for leads
  }

  return (
    <button onClick={handleQualify} disabled={loading}>
      {loading ? 'Qualifying...' : 'Qualify Lead'}
    </button>
  );
}
```

---

## What Just Happened?

### From 6 Lines of YAML...

```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead', error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: lead_qualified, to: $email
```

### To 200+ Lines of Production Code

1. **PL/pgSQL Functions** (120+ lines)
   - Core business logic
   - GraphQL wrapper
   - Error handling
   - Transaction safety
   - Audit trail updates

2. **GraphQL Schema** (40+ lines)
   - Mutation definition
   - Input types
   - Result types
   - FraiseQL annotations

3. **TypeScript Hooks** (40+ lines)
   - Apollo Client hook
   - Type definitions
   - Cache updates

**Ratio**: 6 lines → 200+ lines = **33x leverage**

---

## Adding More Complex Logic

### Example: Multi-Step Workflow

```yaml
actions:
  - name: approve_and_notify_lead
    steps:
      # Validation
      - validate: status = 'qualified', error: "not_qualified"
      - validate: company.credit_check = true, error: "credit_check_failed"

      # Conditional logic
      - if: total_value > 10000
        then:
          - call: require_manager_approval
          - update: Contact SET requires_approval = true
        else:
          - update: Contact SET status = 'customer'

      # Create related records
      - insert: CustomerAccount VALUES (
          contact_id: $contact_id,
          tier: 'standard',
          credit_limit: 5000
        )

      # Notifications
      - notify: customer_approved, to: $email
      - notify: sales_team_alert, to: 'sales@company.com'
```

---

## Action Step Types

### Validate

```yaml
- validate: <condition>
  error: <error_code>
  message: <optional_message>
```

### Update

```yaml
- update: <Entity>
  SET <field> = <value>, ...
  WHERE <condition>
```

### Insert

```yaml
- insert: <Entity> VALUES (
    <field>: <value>,
    ...
  )
```

### If/Then/Else

```yaml
- if: <condition>
  then:
    - <steps>
  else:
    - <steps>
```

### Call Function

```yaml
- call: <function_name>
  args: {<param>: <value>, ...}
  result: $<variable>
```

### Notify

```yaml
- notify: <event_name>
  to: <email_address>
  data: {<key>: <value>, ...}
```

### Foreach Loop

```yaml
- foreach: <collection> as <item>
  do:
    - <steps>
```

**Full reference**: [Action Steps](../06_reference/action-steps.md)

---

## Testing Your Action

### Test in Database

```sql
-- Test success case
SELECT * FROM app.qualify_lead(
    '550e8400-e29b-41d4-a716-446655440000'
);
-- Should return status='success'

-- Test validation error
SELECT * FROM app.qualify_lead(
    '550e8400-e29b-41d4-a716-446655440001' -- Customer, not lead
);
-- Should return status='error', code='not_a_lead'
```

### Test in Frontend

```typescript
describe('qualify_lead', () => {
  it('should qualify a lead', async () => {
    const contact = await createTestContact({ status: 'lead' });

    const result = await qualifyLead({ contactId: contact.id });

    expect(result.data.qualifyLead.status).toBe('success');
    expect(result.data.qualifyLead.data.status).toBe('qualified');
  });

  it('should reject non-leads', async () => {
    const contact = await createTestContact({ status: 'customer' });

    const result = await qualifyLead({ contactId: contact.id });

    expect(result.data.qualifyLead.status).toBe('error');
    expect(result.data.qualifyLead.code).toBe('not_a_lead');
  });
});
```

---

## Common Patterns

### Pattern 1: State Machine

```yaml
actions:
  - name: transition_status
    params:
      new_status: enum(lead, qualified, customer)!
    steps:
      - validate: call(is_valid_transition, status, $new_status)
        error: "invalid_status_transition"
      - update: Contact SET status = $new_status
```

### Pattern 2: Idempotent Actions

```yaml
actions:
  - name: qualify_lead_safe
    steps:
      - if: status = 'lead'
        then:
          - update: Contact SET status = 'qualified'
        else:
          - return: "Already qualified or customer"
```

### Pattern 3: Batch Operations

```yaml
actions:
  - name: qualify_all_leads
    steps:
      - foreach: Contact WHERE status = 'lead' as contact
        do:
          - call: qualify_lead, args: {contact_id: $contact.id}
```

---

## Next Steps

### Learn More

- **[Actions Guide](../05_guides/actions.md)** - Complete actions documentation
- **[Error Handling](../05_guides/error-handling.md)** - Handle errors properly
- **[Action Steps Reference](../06_reference/action-steps.md)** - All step types

### Try These Examples

1. **Add validation**: Prevent qualifying leads without email
2. **Add conditions**: Different logic for high-value leads
3. **Add loops**: Qualify multiple leads at once
4. **Add external calls**: Integrate with external CRM API

### Advanced Topics

- **[Custom Patterns](../07_advanced/custom-patterns.md)** - Reusable logic
- **[Performance Tuning](../07_advanced/performance-tuning.md)** - Optimize actions
- **[Testing](../07_advanced/testing.md)** - Comprehensive testing

---

## Troubleshooting

### Error: "Action not found"

**Solution**: Regenerate code
```bash
specql generate entities/contact.yaml --output generated/
```

### Error: "Validation failed"

**Check**: Ensure contact has `status = 'lead'`
```sql
SELECT * FROM crm.tb_contact WHERE id = '...';
```

### Frontend shows stale data

**Solution**: Use impact metadata for cache updates
```typescript
update: (cache, { data }) => {
  if (data.qualifyLead._meta?.impacts) {
    // Apollo updates cache automatically
  }
}
```

---

## Summary

You've learned:
- ✅ How to define actions in YAML
- ✅ What code SpecQL generates automatically
- ✅ How to use actions in frontend
- ✅ Common action patterns

**Key Takeaway**: Actions give you 30x leverage—write business logic once in YAML, get complete implementation everywhere.

**Next**: Build more complex workflows with [Actions Guide](../05_guides/actions.md) →

---

**Welcome to declarative business logic—focus on what, not how.**
