# GraphQL Integration with FraiseQL

**PostgreSQL comments become GraphQL schemas automatically** 🔄

## Overview

SpecQL generates GraphQL APIs automatically through FraiseQL - a convention that turns PostgreSQL comments into GraphQL schemas. No schema duplication, no manual GraphQL type definitions.

**What you get:**
- ✅ GraphQL schema auto-generated from PostgreSQL
- ✅ Mutations from PL/pgSQL functions
- ✅ Types from database tables
- ✅ Descriptions from comments
- ✅ Frontend hooks auto-generated

## How It Works

### The FraiseQL Convention

FraiseQL reads PostgreSQL comments and converts them to GraphQL:

```sql
-- PostgreSQL with comments
COMMENT ON TABLE crm.tb_contact IS 'Customer contact information';
COMMENT ON COLUMN crm.tb_contact.email IS 'Primary email address (unique)';
COMMENT ON FUNCTION crm.create_contact(text, text, text) IS
  'Create a new contact @fraiseql:mutation';

-- Becomes GraphQL automatically
type Contact {
  """Customer contact information"""
  id: UUID!
  email: String  # "Primary email address (unique)"
}

type Mutation {
  createContact(email: String!, firstName: String!, lastName: String!): MutationResult
    @fraiseql(type: "crm.create_contact")
}
```

### SpecQL Generates FraiseQL-Ready Code

```yaml
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email:
    type: email
    description: "Primary email address (unique)"

actions:
  - name: create_contact
    description: "Create a new contact"
```

**Generates:**
```sql
-- Table with FraiseQL comments
COMMENT ON TABLE crm.tb_contact IS 'Customer contact information';
COMMENT ON COLUMN crm.tb_contact.email IS 'Primary email address (unique)';

-- Function with FraiseQL annotation
COMMENT ON FUNCTION crm.create_contact(text, text, text) IS
  'Create a new contact @fraiseql:mutation';
```

## Quick Start

### 1. Create Entity with GraphQL Intent

```yaml
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  first_name: text!
  last_name: text!
  email: email!
  phone: phone

actions:
  - name: create_contact
    description: "Create a new contact"
  - name: update_contact
    description: "Update existing contact"
  - name: delete_contact
    description: "Soft delete contact"
```

### 2. Generate Everything

```bash
specql generate entities/contact.yaml
```

### 3. Deploy and Query

```bash
# Deploy to database
cd db/schema
confiture migrate up

# Your GraphQL API is ready!
# FraiseQL automatically discovers all functions and types
```

### 4. Use from Frontend

```typescript
// Generated Apollo hooks
const [createContact, { loading }] = useCreateContactMutation();
const { data: contacts } = useContactsQuery();

// Use like any GraphQL API
await createContact({
  variables: {
    email: 'john@example.com',
    firstName: 'John',
    lastName: 'Doe'
  }
});
```

## FraiseQL Annotations

### Function Annotations

```sql
-- Basic mutation
COMMENT ON FUNCTION crm.create_contact(text, text, text) IS
  'Create a new contact @fraiseql:mutation';

-- Query with custom name
COMMENT ON FUNCTION crm.get_contacts() IS
  'Get all contacts @fraiseql:query(name: "contacts")';

-- Mutation with custom impact
COMMENT ON FUNCTION crm.update_contact(uuid, text) IS
  'Update contact @fraiseql:mutation @fraiseql:impact(contact_updated)';
```

### Field Annotations

```sql
-- Custom GraphQL type
COMMENT ON COLUMN crm.tb_contact.email IS
  'Email address @fraiseql:type EmailScalar';

-- Required field
COMMENT ON COLUMN crm.tb_contact.first_name IS
  'First name @fraiseql:required';

-- Custom resolver
COMMENT ON COLUMN crm.tb_contact.full_name IS
  'Full name @fraiseql:resolver contactFullName';
```

### Type Annotations

```sql
-- Custom GraphQL type name
COMMENT ON TABLE crm.tb_contact IS
  'Customer contact @fraiseql:type Customer';

-- Interface implementation
COMMENT ON TABLE crm.tb_contact IS
  'Contact info @fraiseql:implements Person';
```

## Generated GraphQL Schema

### Automatic Type Generation

```graphql
# From SpecQL entity
type Contact {
  """Customer contact information"""
  id: UUID!
  pkContact: Int!
  identifier: String!

  # Fields with descriptions
  firstName: String!  # "First name"
  lastName: String!   # "Last name"
  email: Email!       # "Email address"
  phone: Phone        # "Phone number"

  # Audit fields
  createdAt: DateTime!
  updatedAt: DateTime!
  deletedAt: DateTime
}

# Automatic input types
input ContactInput {
  firstName: String!
  lastName: String!
  email: Email!
  phone: Phone
}

# Automatic filter types
input ContactFilter {
  email: Email
  createdAt: DateRange
  # ... more filters
}
```

### Mutation Generation

```graphql
type Mutation {
  # From actions
  createContact(input: ContactInput!): MutationResult!
  updateContact(id: UUID!, input: ContactUpdate!): MutationResult!
  deleteContact(id: UUID!): MutationResult!

  # Automatic CRUD mutations
  createContactManual(email: Email!, firstName: String!, lastName: String!): MutationResult!
  updateContactManual(id: UUID!, email: Email, firstName: String): MutationResult!
}

type MutationResult {
  success: Boolean!
  message: String!
  object: Contact  # The created/updated object
  errors: [ValidationError!]  # Validation failures
}
```

### Query Generation

```graphql
type Query {
  # Single object
  contact(id: UUID!): Contact

  # List with filtering
  contacts(
    filter: ContactFilter
    orderBy: ContactOrderBy
    limit: Int
    offset: Int
  ): ContactConnection!

  # Aggregations
  contactsCount(filter: ContactFilter): Int!
}

type ContactConnection {
  edges: [ContactEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type ContactEdge {
  node: Contact!
  cursor: String!
}
```

## Rich Type Integration

### Scalar Types

SpecQL's 49 rich types map to GraphQL scalars:

```yaml
fields:
  email: email!      # GraphQL: Email!
  phone: phone       # GraphQL: Phone
  money: money       # GraphQL: Money
  percentage: percentage  # GraphQL: Percentage
  coordinates: coordinates  # GraphQL: Coordinates
  url: url           # GraphQL: URL
```

### Validation at GraphQL Level

```graphql
scalar Email  # Validates email format
scalar Phone  # Validates E.164 format
scalar Money  # Validates decimal precision
scalar Percentage  # Validates 0-100 range

# Usage in schema
input ContactInput {
  email: Email!      # Rejected if not valid email
  phone: Phone       # Rejected if not E.164 format
  budget: Money      # Rejected if invalid decimal
}
```

## Frontend Integration

### Apollo Hooks Generation

SpecQL can generate TypeScript Apollo hooks:

```bash
# Generate with frontend code
specql generate entities/*.yaml --with-impacts
```

**Generated hooks:**
```typescript
// Apollo React hooks
export const useCreateContactMutation = () => { /* ... */ }
export const useUpdateContactMutation = () => { /* ... */ }
export const useContactsQuery = () => { /* ... */ }
export const useContactQuery = () => { /* ... */ }

// TypeScript types
export interface Contact {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  createdAt: Date;
}

export interface CreateContactInput {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
}
```

### React Component Example

```tsx
import {
  useContactsQuery,
  useCreateContactMutation,
  Contact
} from './generated/graphql';

function ContactManager() {
  const { data, loading } = useContactsQuery();
  const [createContact] = useCreateContactMutation();

  const handleCreate = async (input: CreateContactInput) => {
    await createContact({
      variables: { input },
      refetchQueries: ['contacts']  // Automatic cache update
    });
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {data?.contacts.edges.map(({ node }) => (
        <ContactCard key={node.id} contact={node} />
      ))}
    </div>
  );
}
```

## Advanced Patterns

### Complex Mutations

```yaml
actions:
  - name: create_opportunity
    description: "Create opportunity with contact and organization"
    steps:
      - validate: contact_email IS NOT NULL
      - insert: Contact
      - insert: Opportunity
      - notify: sales_team "New opportunity created"
```

**Generated GraphQL:**
```graphql
type Mutation {
  createOpportunity(
    contactEmail: Email!
    contactFirstName: String!
    organizationName: String!
    opportunityName: String!
    amount: Money
  ): MutationResult!
}
```

### Relationships and Nested Queries

```yaml
entity: Contact
fields:
  organization: ref(Organization)

entity: Organization
fields:
  name: text!
  contacts: ref(Contact, many: true)  # Reverse relationship
```

**Generated GraphQL:**
```graphql
type Contact {
  id: UUID!
  firstName: String!
  organization: Organization
}

type Organization {
  id: UUID!
  name: String!
  contacts(filter: ContactFilter, limit: Int): [Contact!]!
}
```

### Custom Resolvers

For complex business logic:

```yaml
actions:
  - name: get_contact_summary
    description: "Get contact with computed fields @fraiseql:query"
    steps:
      - select: Contact WITH organization, last_order
      - compute: total_orders = COUNT(orders)
      - compute: lifetime_value = SUM(order_amounts)
```

## Error Handling

### Validation Errors

```graphql
mutation CreateContact($input: ContactInput!) {
  createContact(input: $input) {
    success
    message
    object {
      id
      firstName
      lastName
      email
    }
    errors {
      field
      message
      code  # EMAIL_INVALID, REQUIRED_FIELD, etc.
    }
  }
}
```

### Business Logic Errors

```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
      - error: "Lead already qualified" WHEN status != 'lead'
```

## Performance Optimization

### Automatic Optimizations

- **N+1 Query Prevention**: FraiseQL analyzes dependencies
- **Batch Loading**: Related data loaded efficiently
- **Caching**: HTTP and Apollo cache integration
- **Persisted Queries**: For production deployments

### Custom Optimization

```yaml
actions:
  - name: get_contacts_with_stats
    description: "Contacts with computed statistics @fraiseql:query @fraiseql:batch"
    optimization: batch_load
```

## Testing GraphQL APIs

### Integration Tests

```typescript
describe('Contact GraphQL API', () => {
  test('create contact', async () => {
    const result = await graphqlClient.mutate({
      mutation: CREATE_CONTACT,
      variables: {
        input: {
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com'
        }
      }
    });

    expect(result.data.createContact.success).toBe(true);
    expect(result.data.createContact.object.email).toBe('john@example.com');
  });

  test('validation errors', async () => {
    const result = await graphqlClient.mutate({
      mutation: CREATE_CONTACT,
      variables: {
        input: {
          firstName: 'John',
          email: 'invalid-email'  // Invalid format
        }
      }
    });

    expect(result.data.createContact.success).toBe(false);
    expect(result.data.createContact.errors).toContainEqual({
      field: 'email',
      code: 'EMAIL_INVALID'
    });
  });
});
```

## Deployment

### Production Setup

```bash
# Generate schema
specql generate entities/*.yaml

# Deploy database
confiture migrate up

# Start FraiseQL server
fraiseql serve --schema postgres://... --port 4000

# Your GraphQL API is live at http://localhost:4000/graphql
```

### Schema Registry

```bash
# Register schema with Apollo Studio
fraiseql schema:push --endpoint http://localhost:4000/graphql

# Check for breaking changes
fraiseql schema:check
```

## Best Practices

### 1. Descriptive Comments

```yaml
entity: Contact
description: "Individual contact with organization affiliation"

fields:
  email:
    description: "Primary email address - must be unique per organization"
  phone:
    description: "Business phone number in E.164 format"
```

### 2. Consistent Naming

```yaml
actions:
  - name: create_contact     # ✅ Consistent naming
  - name: contact_create     # ❌ Inconsistent
```

### 3. Use Rich Types

```yaml
fields:
  email: email!      # ✅ Semantic validation
  email: text        # ❌ Generic, no validation
```

### 4. Document Business Logic

```yaml
actions:
  - name: qualify_lead
    description: "Convert marketing lead to sales qualified lead"
    steps:
      - validate: status = 'lead'
      - validate: email_verified = true
      - update: Contact SET status = 'qualified', qualified_at = now()
```

## Troubleshooting

### Schema Not Appearing

```bash
# Check function comments
COMMENT ON FUNCTION crm.create_contact(text, text, text) IS
  'Create contact @fraiseql:mutation';  # Must have @fraiseql:mutation

# Restart FraiseQL server after schema changes
fraiseql restart
```

### Type Conflicts

```yaml
# Avoid GraphQL reserved words
fields:
  type: text      # ❌ 'type' is reserved
  entity_type: text  # ✅ Use specific names
```

### Performance Issues

```bash
# Enable query analysis
fraiseql serve --analyze-queries

# Check slow queries
fraiseql query:analyze "query { contacts { id email } }"
```

## Migration from Manual GraphQL

### Before: Manual Schema

```graphql
# Manual type definitions
type Contact {
  id: ID!
  firstName: String!
  lastName: String!
  email: String!
}

type Mutation {
  createContact(input: ContactInput!): Contact!
}
```

```typescript
// Manual resolvers
const resolvers = {
  Mutation: {
    createContact: async (_, { input }) => {
      // Manual database calls
      const result = await db.query('INSERT INTO contacts ...');
      return result.rows[0];
    }
  }
};
```

### After: SpecQL + FraiseQL

```yaml
# Define once
entity: Contact
fields:
  first_name: text!
  last_name: text!
  email: email!

actions:
  - name: create_contact
```

**Everything else generated automatically!**

## Next Steps

- **Read Rich Types Guide**: Learn all scalar types in `docs/guides/rich-types-guide.md`
- **Check Actions Guide**: Understand business logic in `docs/guides/actions-guide.md`
- **Browse Examples**: See `examples/` for complete implementations
- **FraiseQL Docs**: Visit [fraiseql.dev](https://fraiseql.dev) for advanced features

---

**GraphQL APIs without the boilerplate. PostgreSQL comments become your schema.** ✨