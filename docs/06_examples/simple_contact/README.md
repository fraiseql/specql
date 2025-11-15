# Simple Contact Example

**Your first SpecQL entity** - A complete contact management system in minutes

This example demonstrates the core SpecQL concepts with a simple contact entity that includes validation, business logic, and GraphQL API generation.

## 🎯 What You'll Learn

- Basic entity definition
- Field types and validation
- Business logic with actions
- GraphQL API generation
- TypeScript integration

## 📋 Example Overview

**Business Requirements**:
- Store contact information (email, name, phone)
- Track lead status (lead → qualified → customer)
- Validate email format
- Require first name
- Business rule: only leads can be qualified

## 📝 Entity Definition

**File**: `entities/contact.yaml`

```yaml
# Simple Contact Entity
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: text
  first_name: text
  last_name: text
  status: enum(lead, qualified, customer)
  phone: text

actions:
  # Lead qualification - core business logic
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")

  # Contact creation with validation
  - name: create_contact
    steps:
      - validate: email MATCHES email_pattern
        error: "invalid_email"
      - validate: first_name IS NOT NULL
        error: "first_name_required"
      - insert: Contact

  # Status update with business rules
  - name: update_status
    requires: caller.can_edit_contact
    steps:
      - validate: status IN ('lead', 'qualified', 'customer')
        error: "invalid_status"
      - validate: status != 'customer' OR notes IS NOT NULL
        error: "notes_required_for_customer"
      - update: Contact SET status = $status
```

## 🔧 Generate the Code

```bash
# Generate from the entity
specql generate entities/contact.yaml

# Or generate with frontend code
specql generate entities/contact.yaml --with-impacts --output-frontend=src/generated
```

## 🗄️ Generated Database Schema

**Table**: `crm.tb_contact`

```sql
-- Trinity Pattern automatically applied
CREATE TABLE IF NOT EXISTS crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT,

    -- Your business fields
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    status TEXT CHECK (status IN ('lead', 'qualified', 'customer')),
    phone TEXT,

    -- Audit fields (automatic)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID,

    UNIQUE(id),
    UNIQUE(identifier)
);

-- Performance indexes (automatic)
CREATE INDEX IF NOT EXISTS idx_tb_contact_status
    ON crm.tb_contact(status) WHERE deleted_at IS NULL;
```

## 🚀 Generated Business Logic

**Function**: `crm.qualify_lead`

```sql
CREATE OR REPLACE FUNCTION crm.qualify_lead(
    p_contact_id UUID,
    p_caller_id UUID DEFAULT NULL
)
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_pk INTEGER;
    v_status TEXT;
    v_email TEXT;
BEGIN
    -- Trinity resolution: UUID → INTEGER
    SELECT pk_contact, status, email INTO v_contact_pk, v_status, v_email
    FROM crm.tb_contact
    WHERE id = p_contact_id AND deleted_at IS NULL;

    -- Business validation
    IF v_status != 'lead' THEN
        RETURN app.error('not_a_lead', 'Contact is not a lead');
    END IF;

    -- Business logic
    UPDATE crm.tb_contact
    SET status = 'qualified',
        updated_at = NOW(),
        updated_by = p_caller_id
    WHERE pk_contact = v_contact_pk;

    -- Notification (placeholder)
    RAISE NOTICE 'Notification: Contact % qualified - email: %', p_contact_id, v_email;

    -- Success response
    RETURN app.success('Contact qualified', jsonb_build_object(
        'id', p_contact_id,
        'status', 'qualified'
    ));
END;
$$;
```

## 🌐 Generated GraphQL API

**GraphQL Mutation**:

```graphql
mutation QualifyLead($contactId: UUID!) {
  qualifyLead(contactId: $contactId) {
    success
    message
    object
    errors {
      code
      message
    }
  }
}
```

**Usage**:

```javascript
const result = await client.mutate({
  mutation: QUALIFY_LEAD,
  variables: { contactId: "550e8400-e29b-41d4-a716-446655440000" }
});

if (result.data.qualifyLead.success) {
  console.log("Contact qualified!");
}
```

## 📱 Generated TypeScript

**Types**:

```typescript
export interface Contact {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  status: 'lead' | 'qualified' | 'customer';
  phone?: string;
}

export interface QualifyLeadVariables {
  contactId: string;
}

export interface QualifyLeadResponse {
  success: boolean;
  message: string;
  object: {
    id: string;
    status: string;
  };
  errors?: Array<{
    code: string;
    message: string;
  }>;
}
```

**React Hook**:

```typescript
import { useQualifyLead } from '../generated/hooks';

function ContactCard({ contact }: { contact: Contact }) {
  const [qualifyLead] = useQualifyLead();

  const handleQualify = async () => {
    const result = await qualifyLead({
      variables: { contactId: contact.id }
    });

    if (result.data?.success) {
      console.log('Contact qualified!');
    }
  };

  return (
    <div>
      <h3>{contact.firstName} {contact.lastName}</h3>
      <p>Status: {contact.status}</p>
      {contact.status === 'lead' && (
        <button onClick={handleQualify}>
          Qualify Lead
        </button>
      )}
    </div>
  );
}
```

## 🧪 Generated Tests

**pgTAP Test**:

```sql
-- Test qualify_lead function
SELECT * FROM crm.qualify_lead('550e8400-e29b-41d4-a716-446655440000'::UUID);

-- Verify status change
SELECT status FROM crm.tb_contact
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- Test validation (should fail)
SELECT * FROM crm.qualify_lead('550e8400-e29b-41d4-a716-446655440001'::UUID);
-- Expected: error 'not_a_lead'
```

**pytest Test**:

```python
def test_qualify_lead_success(db_session):
    # Create test contact
    contact = ContactFactory(status='lead')

    # Call the function
    result = qualify_lead(contact.id)

    # Assertions
    assert result['success'] is True
    assert result['object']['status'] == 'qualified'

    # Verify database
    contact.refresh()
    assert contact.status == 'qualified'

def test_qualify_lead_validation(db_session):
    # Create qualified contact
    contact = ContactFactory(status='qualified')

    # Should fail
    result = qualify_lead(contact.id)

    assert result['success'] is False
    assert result['errors'][0]['code'] == 'not_a_lead'
```

## 🚀 Deploy and Test

```bash
# 1. Create database
createdb contact_example

# 2. Apply migrations
psql -d contact_example -f migrations/**/*.sql

# 3. Test the API
psql -d contact_example -c "
  -- Create a test contact
  INSERT INTO crm.tb_contact (email, first_name, status)
  VALUES ('john@example.com', 'John', 'lead');

  -- Get the ID
  SELECT id FROM crm.tb_contact WHERE email = 'john@example.com';
"

# 4. Test qualification
psql -d contact_example -c "
  SELECT * FROM app.qualify_lead('YOUR_CONTACT_ID_HERE');
"
```

## 🎯 Key Concepts Demonstrated

### 1. Entity Definition
- **entity**: Business object name
- **schema**: Database organization
- **description**: Documentation

### 2. Field Types
- **text**: Basic string fields
- **enum**: Restricted value sets
- **Validation**: Automatic constraints

### 3. Business Logic
- **Actions**: Named operations
- **Validation**: Business rules
- **Updates**: Data manipulation
- **Authorization**: Permission checks

### 4. Trinity Pattern
- **pk_contact**: Database JOINs
- **id**: API identifiers
- **identifier**: Human-readable codes

### 5. Error Handling
- **Structured errors**: Code + message
- **Validation failures**: Clear feedback
- **Business rules**: Enforced constraints

## 🔄 Extend the Example

### Add More Fields

```yaml
fields:
  # ... existing fields ...
  company: text
  title: text
  notes: text
  last_contacted: timestamp
```

### Add More Actions

```yaml
actions:
  # ... existing actions ...

  - name: mark_contacted
    steps:
      - update: Contact SET last_contacted = NOW()

  - name: convert_to_customer
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'qualified'
        error: "not_qualified"
      - update: Contact SET status = 'customer'
```

### Add Relationships

```yaml
# Create company entity first
entity: Company
schema: crm
fields:
  name: text
  website: url

# Then update contact
entity: Contact
schema: crm
fields:
  # ... existing fields ...
  company: ref(Company)  # Foreign key reference
```

## 📚 Next Steps

- **[E-commerce System](../ECOMMERCE_SYSTEM.md)** - Complex business logic
- **[CRM System](../CRM_SYSTEM_COMPLETE.md)** - Complete business application
- **[Custom Patterns](../../../../02_guides/patterns/)** - Reusable patterns
- **[Multi-Language](../../../../05_vision/multi_language.md)** - Java/Rust/Go support

## 💡 Pro Tips

1. **Start Simple**: Begin with basic fields and actions
2. **Validate Early**: Add validation before complex logic
3. **Use Enums**: Restrict values for data integrity
4. **Test Thoroughly**: Generated tests catch issues fast
5. **Iterate Quickly**: YAML changes deploy instantly

---

**Simple Contact**: The foundation of SpecQL mastery.