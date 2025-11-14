# FraiseQL Annotations Reference

**Complete guide to PostgreSQL comments that generate GraphQL APIs** 📝

## Overview

FraiseQL is SpecQL's convention for turning PostgreSQL comments into GraphQL schemas. By adding specially-formatted comments to database objects, FraiseQL automatically generates:

- ✅ GraphQL type definitions
- ✅ Query and mutation operations
- ✅ Field resolvers and relationships
- ✅ Input types and validation
- ✅ Schema documentation

**Annotation format:**
```sql
COMMENT ON [OBJECT] [name] IS '[description]
@[namespace]:[directive]
[additional metadata]';
```

## Function Annotations

### @fraiseql:mutation

Marks a PostgreSQL function as a GraphQL mutation:

```sql
COMMENT ON FUNCTION crm.create_contact(UUID, TEXT, TEXT, TEXT) IS
  'Create a new contact record
@fraiseql:mutation
@fraiseql:impact contact_created';
```

**Generated GraphQL:**
```graphql
type Mutation {
  createContact(
    tenantId: UUID!
    email: String!
    firstName: String!
    lastName: String!
  ): MutationResult!
}
```

**Parameters:**
- Function parameters become GraphQL input fields
- Parameter names are converted to camelCase
- Parameter types map to GraphQL scalars
- NOT NULL parameters become required (!) fields

### @fraiseql:query

Marks a function as a GraphQL query:

```sql
COMMENT ON FUNCTION crm.get_contacts(UUID) IS
  'Retrieve all contacts for a tenant
@fraiseql:query(name: "contacts")
@fraiseql:type ContactConnection';
```

**Generated GraphQL:**
```graphql
type Query {
  contacts(tenantId: UUID!): ContactConnection!
}

type ContactConnection {
  edges: [ContactEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}
```

**Parameters:**
- `name`: Custom GraphQL field name (defaults to function name)
- `type`: Return type (defaults to inferred from PostgreSQL type)

### @fraiseql:impact

Defines mutation side effects for cache invalidation:

```sql
COMMENT ON FUNCTION crm.update_contact(UUID, TEXT) IS
  'Update contact information
@fraiseql:mutation
@fraiseql:impact contact_updated, contact_list_stale';
```

**Usage:**
- Comma-separated list of impact identifiers
- Used by Apollo Client for cache management
- Triggers refetch of related queries

## Table Annotations

### @fraiseql:type

Defines the GraphQL type name for a table:

```sql
COMMENT ON TABLE crm.tb_contact IS
  'Customer contact information
@fraiseql:type Contact
trinity: true';
```

**Generated GraphQL:**
```graphql
type Contact {
  id: UUID!
  pkContact: Int!
  # ... other fields from column comments
}
```

**Parameters:**
- Type name (required) - GraphQL type identifier
- `trinity: true` - Enables Trinity pattern field generation

### Table Metadata

Additional table-level metadata:

```sql
COMMENT ON TABLE crm.tb_contact IS
  'Customer contact information
@fraiseql:type Contact
trinity: true
implements: Person
description: "A person or organization contact"';
```

**Supported metadata:**
- `implements`: Interface implementation
- `description`: Extended description
- `deprecated`: Deprecation notice

## Column Annotations

### @fraiseql:field

Customizes GraphQL field generation:

```sql
COMMENT ON COLUMN crm.tb_contact.email IS
  'Primary email address for contact
@fraiseql:field
name: emailAddress
type: Email!
required: true
description: "Valid email address"';
```

**Generated GraphQL:**
```graphql
type Contact {
  emailAddress: Email!  # "Valid email address"
}
```

**Parameters:**
- `name`: Custom field name (defaults to column name in camelCase)
- `type`: GraphQL type override
- `required`: Force field as non-nullable
- `description`: Field documentation

### @fraiseql:resolver

Specifies custom field resolver:

```sql
COMMENT ON COLUMN crm.tb_contact.full_name IS
  'Computed full name
@fraiseql:field
resolver: contactFullNameResolver
type: String!';
```

**Usage:**
- References a custom resolver function
- Overrides default column value resolution
- Enables computed fields and relationships

## Type Mapping

### PostgreSQL → GraphQL Type Conversion

| PostgreSQL Type | GraphQL Type | Notes |
|----------------|--------------|-------|
| `TEXT` | `String` | Variable length text |
| `INTEGER` | `Int` | 32-bit integer |
| `BIGINT` | `BigInt` | 64-bit integer |
| `NUMERIC` | `Decimal` | Arbitrary precision |
| `BOOLEAN` | `Boolean` | True/false |
| `UUID` | `UUID` | UUID scalar |
| `TIMESTAMPTZ` | `DateTime` | ISO timestamp |
| `DATE` | `Date` | ISO date |
| `TIME` | `Time` | HH:MM:SS |
| `JSONB` | `JSONObject` | JSON object |
| `POINT` | `Coordinates` | Geographic point |

### Rich Type Mappings

SpecQL rich types map to specific GraphQL scalars:

```sql
-- Email type
COMMENT ON COLUMN crm.tb_contact.email IS 'Email address
@fraiseql:field
type: Email!';

-- Phone type
COMMENT ON COLUMN crm.tb_contact.phone IS 'Phone number
@fraiseql:field
type: Phone';

-- Money type
COMMENT ON COLUMN crm.tb_invoice.amount IS 'Invoice amount
@fraiseql:field
type: Money!';
```

## Relationship Annotations

### Foreign Key Relationships

```sql
COMMENT ON COLUMN crm.tb_contact.fk_organization IS
  'Reference to organization
@fraiseql:field
name: organization
type: Organization
resolver: organizationResolver';
```

**Generated GraphQL:**
```graphql
type Contact {
  organization: Organization
}
```

### Reverse Relationships

```sql
-- On the organization table
COMMENT ON TABLE crm.tb_organization IS
  'Organization information
@fraiseql:type Organization
relations:
  contacts: [Contact!] @reverse(fk_organization)';
```

## Input Type Generation

### Automatic Input Types

Mutations automatically generate input types:

```sql
COMMENT ON FUNCTION crm.create_contact(UUID, TEXT, TEXT, TEXT) IS
  'Create contact
@fraiseql:mutation';
```

**Generated:**
```graphql
input CreateContactInput {
  tenantId: UUID!
  email: String!
  firstName: String!
  lastName: String!
}

type Mutation {
  createContact(input: CreateContactInput!): MutationResult!
}
```

### Custom Input Types

```sql
COMMENT ON FUNCTION crm.update_contact(UUID, UUID, ContactUpdate) IS
  'Update contact
@fraiseql:mutation
@fraiseql:input ContactUpdate {
  email: String
  firstName: String
  lastName: String
}';
```

## Filter and Pagination

### Automatic Filters

Tables get automatic filter generation:

```sql
COMMENT ON TABLE crm.tb_contact IS
  'Contact information
@fraiseql:type Contact
filters: true';
```

**Generated:**
```graphql
input ContactFilter {
  email: String
  firstName: String
  lastName: String
  createdAt: DateRange
  # ... other fields
}

type Query {
  contacts(filter: ContactFilter, limit: Int, offset: Int): [Contact!]!
}
```

### Custom Filters

```sql
COMMENT ON TABLE crm.tb_contact IS
  'Contact information
@fraiseql:type Contact
filters:
  - name: activeContacts
    fields: [status, createdAt]
  - name: emailSearch
    fields: [email]';
```

## Validation Annotations

### Field Validation

```sql
COMMENT ON COLUMN crm.tb_contact.email IS
  'Email address
@fraiseql:field
validation:
  required: true
  format: email
  maxLength: 254';
```

**Generated GraphQL:**
```graphql
input CreateContactInput {
  email: Email! @validation(format: "email", maxLength: 254)
}
```

### Custom Validators

```sql
COMMENT ON FUNCTION crm.validate_contact(UUID, TEXT) IS
  'Custom validation function
@fraiseql:validator(name: "contactExists")';
```

## Enum Annotations

### Enum Type Definition

```sql
COMMENT ON TABLE crm.tb_contact IS
  'Contact information
@fraiseql:type Contact
enums:
  status: [lead, qualified, customer]
  priority: [low, medium, high]';
```

**Generated:**
```graphql
enum ContactStatus {
  LEAD
  QUALIFIED
  CUSTOMER
}

enum ContactPriority {
  LOW
  MEDIUM
  HIGH
}

type Contact {
  status: ContactStatus!
  priority: ContactPriority
}
```

## Interface and Union Types

### Interface Implementation

```sql
COMMENT ON TABLE crm.tb_contact IS
  'Contact information
@fraiseql:type Contact
implements: Person';

COMMENT ON TABLE crm.tb_organization IS
  'Organization information
@fraiseql:type Organization
implements: Person';
```

**Generated:**
```graphql
interface Person {
  id: UUID!
  name: String!
}

type Contact implements Person {
  id: UUID!
  name: String!
  email: Email!
}

type Organization implements Person {
  id: UUID!
  name: String!
  taxId: String
}
```

### Union Types

```sql
COMMENT ON COLUMN crm.tb_message.recipient IS
  'Message recipient
@fraiseql:field
type: Contact | Organization
resolver: recipientResolver';
```

## Subscription Annotations

### Real-time Subscriptions

```sql
COMMENT ON FUNCTION crm.contact_created(UUID) IS
  'Contact creation event
@fraiseql:subscription
@fraiseql:trigger contact_created';
```

**Generated:**
```graphql
type Subscription {
  contactCreated(tenantId: UUID!): Contact!
}
```

## Authentication and Authorization

### Permission Annotations

```sql
COMMENT ON FUNCTION crm.create_contact(UUID, TEXT, TEXT, TEXT) IS
  'Create contact
@fraiseql:mutation
@fraiseql:auth roles: [admin, manager]';

COMMENT ON TABLE crm.tb_contact IS
  'Contact information
@fraiseql:type Contact
@fraiseql:auth read: [user, admin]
@fraiseql:auth write: [admin]';
```

## Deprecation

### Deprecated Fields

```sql
COMMENT ON COLUMN crm.tb_contact.old_field IS
  'Deprecated field
@fraiseql:field
deprecated: "Use newField instead"
reason: "Field renamed for consistency"';
```

**Generated:**
```graphql
type Contact {
  oldField: String @deprecated(reason: "Use newField instead")
  newField: String
}
```

## Advanced Patterns

### Computed Fields

```sql
COMMENT ON COLUMN crm.tb_contact.full_name IS
  'Computed full name
@fraiseql:field
type: String!
computed: true
resolver: fullNameResolver';
```

### Batch Resolvers

```sql
COMMENT ON COLUMN crm.tb_contact.organization IS
  'Organization relationship
@fraiseql:field
type: Organization
batch: true
resolver: organizationBatchResolver';
```

### Custom Scalars

```sql
COMMENT ON COLUMN crm.tb_contact.custom_field IS
  'Custom scalar field
@fraiseql:field
type: MyCustomScalar
scalar: true';
```

## Error Handling

### Error Type Annotations

```sql
COMMENT ON FUNCTION crm.create_contact(UUID, TEXT, TEXT, TEXT) IS
  'Create contact
@fraiseql:mutation
@fraiseql:errors {
  EMAIL_EXISTS: "Email address already in use"
  INVALID_EMAIL: "Email format is invalid"
}';
```

**Generated:**
```graphql
type MutationResult {
  success: Boolean!
  message: String!
  object: Contact
  errors: [ValidationError!]
}

type ValidationError {
  field: String!
  code: String!
  message: String!
}
```

## Schema Organization

### Module Grouping

```sql
COMMENT ON SCHEMA crm IS
  'Customer relationship management
@fraiseql:module
name: CRM
description: "Contact and organization management"';
```

### Versioning

```sql
COMMENT ON FUNCTION crm.create_contact(UUID, TEXT, TEXT, TEXT) IS
  'Create contact
@fraiseql:mutation
@fraiseql:version 1.0
@fraiseql:breaking false';
```

## Performance Optimization

### Caching Hints

```sql
COMMENT ON FUNCTION crm.get_contacts(UUID) IS
  'Get contacts
@fraiseql:query
@fraiseql:cache {
  ttl: 300
  scope: tenant
}';
```

### Query Complexity

```sql
COMMENT ON FUNCTION crm.get_contacts(UUID, ContactFilter, Int, Int) IS
  'Get contacts with filtering
@fraiseql:query
@fraiseql:complexity {
  base: 10
  multiplier: 2
}';
```

## Testing Annotations

### Test Data Generation

```sql
COMMENT ON FUNCTION test.create_test_contact(TEXT, TEXT, TEXT) IS
  'Create test contact
@fraiseql:test
@fraiseql:fixture name: "testContact"';
```

## Complete Example

### Full Entity with Annotations

```sql
-- Table with type definition
COMMENT ON TABLE crm.tb_contact IS
  'Customer contact information
@fraiseql:type Contact
trinity: true
implements: Person
filters: true
description: "A person contact with organization affiliation"';

-- Columns with field definitions
COMMENT ON COLUMN crm.tb_contact.id IS
  'Public UUID identifier
@fraiseql:field
name: id
type: UUID!
required: true';

COMMENT ON COLUMN crm.tb_contact.email IS
  'Primary email address
@fraiseql:field
name: email
type: Email!
required: true
validation:
  format: email
  maxLength: 254';

COMMENT ON COLUMN crm.tb_contact.first_name IS
  'First name
@fraiseql:field
name: firstName
type: String!
required: true';

COMMENT ON COLUMN crm.tb_contact.organization IS
  'Organization relationship
@fraiseql:field
name: organization
type: Organization
resolver: organizationResolver';

-- Functions with operation definitions
COMMENT ON FUNCTION crm.create_contact(UUID, TEXT, TEXT, TEXT) IS
  'Create a new contact
@fraiseql:mutation
@fraiseql:impact contact_created
@fraiseql:auth roles: [admin, manager]';

COMMENT ON FUNCTION crm.get_contacts(UUID, ContactFilter, Int, Int) IS
  'Retrieve contacts with filtering
@fraiseql:query(name: "contacts")
@fraiseql:type ContactConnection
@fraiseql:auth roles: [user, admin]';

COMMENT ON FUNCTION crm.update_contact(UUID, UUID, TEXT, TEXT, TEXT) IS
  'Update contact information
@fraiseql:mutation
@fraiseql:impact contact_updated
@fraiseql:auth roles: [admin]';
```

**Generated GraphQL Schema:**
```graphql
interface Person {
  id: UUID!
  name: String!
}

type Contact implements Person {
  id: UUID!
  email: Email!
  firstName: String!
  organization: Organization
}

input ContactFilter {
  email: String
  firstName: String
}

type ContactConnection {
  edges: [ContactEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type Mutation {
  createContact(
    tenantId: UUID!
    email: Email!
    firstName: String!
    lastName: String!
  ): MutationResult!
    @auth(roles: [admin, manager])

  updateContact(
    tenantId: UUID!
    contactId: UUID!
    email: Email
    firstName: String
    lastName: String
  ): MutationResult!
    @auth(roles: [admin])
}

type Query {
  contacts(
    tenantId: UUID!
    filter: ContactFilter
    first: Int
    after: String
  ): ContactConnection!
    @auth(roles: [user, admin])
}
```

## Annotation Reference Table

| Annotation | Target | Purpose | Example |
|------------|--------|---------|---------|
| `@fraiseql:mutation` | Function | GraphQL mutation | `@fraiseql:mutation` |
| `@fraiseql:query` | Function | GraphQL query | `@fraiseql:query(name: "contacts")` |
| `@fraiseql:subscription` | Function | GraphQL subscription | `@fraiseql:subscription` |
| `@fraiseql:impact` | Function | Cache invalidation | `@fraiseql:impact contact_updated` |
| `@fraiseql:type` | Table | GraphQL type name | `@fraiseql:type Contact` |
| `@fraiseql:field` | Column | Field customization | `@fraiseql:field name: emailAddress` |
| `@fraiseql:resolver` | Column | Custom resolver | `@fraiseql:resolver contactResolver` |
| `@fraiseql:auth` | Any | Authorization | `@fraiseql:auth roles: [admin]` |
| `@fraiseql:validation` | Column | Field validation | `@fraiseql:validation required: true` |
| `@fraiseql:deprecated` | Any | Deprecation notice | `@fraiseql:deprecated reason: "Use newField"` |

## Best Practices

### 1. Consistent Naming

```sql
-- ✅ Good: camelCase for GraphQL
@fraiseql:field name: emailAddress

-- ❌ Bad: snake_case in GraphQL
@fraiseql:field name: email_address
```

### 2. Descriptive Comments

```sql
-- ✅ Good: Clear purpose and type
COMMENT ON FUNCTION crm.create_contact(...) IS
  'Create a new contact record with validation
@fraiseql:mutation
@fraiseql:impact contact_created';

-- ❌ Bad: Minimal information
COMMENT ON FUNCTION crm.create_contact(...) IS 'Create contact
@fraiseql:mutation';
```

### 3. Security First

```sql
-- ✅ Good: Explicit authorization
@fraiseql:auth roles: [admin, manager]

-- ❌ Bad: Implicit permissions
-- (No auth annotation)
```

### 4. Version Impact

```sql
-- ✅ Good: Mark breaking changes
@fraiseql:breaking true
@fraiseql:version 2.0

-- ❌ Bad: Silent breaking changes
```

## Troubleshooting

### Schema Not Generated

```sql
-- Check annotation syntax
COMMENT ON FUNCTION crm.create_contact(...) IS
  'Create contact
@fraiseql:mutation';  -- Must have @fraiseql:mutation

-- Verify function exists
SELECT proname FROM pg_proc WHERE proname = 'create_contact';
```

### Type Conflicts

```sql
-- Avoid GraphQL reserved words
@fraiseql:type MyType  -- ✅ Good
@fraiseql:type Type    -- ❌ Reserved word

-- Check for duplicates
SELECT * FROM pg_description
WHERE description LIKE '%@fraiseql:type%'
  AND description LIKE '%Contact%';
```

### Resolver Errors

```sql
-- Ensure resolver exists
@fraiseql:resolver contactResolver
-- Must have: function contactResolver(...) RETURNS ...

-- Check resolver signature
CREATE FUNCTION contactResolver(contact_id UUID) RETURNS JSONB AS $$
-- Implementation
$$ LANGUAGE sql;
```

## Next Steps

- **Read Generated Patterns**: See how annotations become code in `docs/reference/generated-patterns.md`
- **Check GraphQL Integration**: Usage examples in `docs/guides/graphql-integration.md`
- **Browse Examples**: See annotations in action in `examples/`
- **Generate Schema**: Run FraiseQL server to see live schema

---

**PostgreSQL comments → GraphQL schema. Automatically.** ✨