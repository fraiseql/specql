# GraphQL Integration Guide

> **Integrate SpecQL-generated GraphQL with your frontend—FraiseQL auto-discovery and Apollo Client**

## Overview

SpecQL generates **FraiseQL-compatible GraphQL** automatically:
- ✅ Auto-generated queries and mutations
- ✅ Type-safe TypeScript interfaces
- ✅ Apollo Client hooks
- ✅ Optimistic UI support via impact metadata
- ✅ Auto-discovery from SQL comments

**Zero GraphQL schema writing required.**

---

## Quick Start

### Step 1: Generate GraphQL Schema

```bash
specql generate entities/*.yaml --with-frontend --output generated/
```

**Output**:
```
generated/
├── graphql/
│   └── schema.graphql
└── typescript/
    ├── types/
    │   ├── contact.ts
    │   └── company.ts
    └── hooks/
        ├── useQualifyLead.ts
        └── useCreateContact.ts
```

### Step 2: Set Up Apollo Client

```typescript
// apollo-client.ts
import { ApolloClient, InMemoryCache, HttpLink } from '@apollo/client';

const client = new ApolloClient({
  link: new HttpLink({
    uri: 'http://localhost:5000/graphql',  // Your FraiseQL endpoint
  }),
  cache: new InMemoryCache(),
});

export default client;
```

### Step 3: Use Generated Hooks

```typescript
import { useQualifyLead } from './generated/hooks/useQualifyLead';

function ContactCard({ contact }) {
  const [qualifyLead, { loading }] = useQualifyLead();

  const handleQualify = async () => {
    const result = await qualifyLead({
      variables: { contactId: contact.id }
    });

    if (result.data.qualifyLead.status === 'success') {
      toast.success('Lead qualified!');
    } else {
      toast.error(result.data.qualifyLead.message);
    }
  };

  return (
    <button onClick={handleQualify} disabled={loading}>
      Qualify Lead
    </button>
  );
}
```

---

## Generated GraphQL Schema

### Queries

**From entity**:
```yaml
entity: Contact
schema: crm
fields:
  email: email!
  first_name: text!
```

**Generated GraphQL**:
```graphql
type Contact {
  id: ID!
  identifier: String!
  email: String!
  firstName: String!
  company: Company!
  createdAt: DateTime!
}

type Query {
  contact(id: ID!): Contact
  contacts(
    limit: Int
    offset: Int
    where: ContactFilter
    orderBy: ContactOrderBy
  ): [Contact!]!
}

input ContactFilter {
  email: StringFilter
  firstName: StringFilter
  status: ContactStatusFilter
}
```

### Mutations

**From action**:
```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

**Generated GraphQL**:
```graphql
type Mutation {
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

type MutationMeta {
  impacts: [Impact!]!
}

type Impact {
  entity: String!
  operation: Operation!
  ids: [ID!]
}

enum Operation {
  INSERT
  UPDATE
  DELETE
}
```

---

## Impact Metadata for Optimistic UI

### What Are Impacts?

Impacts tell the frontend **what data changed** so Apollo cache can update automatically.

**Example**:
```yaml
actions:
  - name: qualify_lead
    impacts:
      - entity: Contact
        operation: update
        filters: {id: $contact_id}
```

**Generated Response**:
```json
{
  "status": "success",
  "code": "lead_qualified",
  "data": {
    "id": "123",
    "status": "qualified"
  },
  "_meta": {
    "impacts": [
      {
        "entity": "Contact",
        "operation": "UPDATE",
        "ids": ["123"]
      }
    ]
  }
}
```

### Optimistic UI with Impacts

```typescript
const [qualifyLead] = useMutation(QUALIFY_LEAD, {
  optimisticResponse: (vars) => ({
    qualifyLead: {
      status: 'SUCCESS',
      code: 'lead_qualified',
      data: {
        __typename: 'Contact',
        id: vars.contactId,
        status: 'qualified',  // Optimistic update
      },
      _meta: {
        impacts: [
          { entity: 'Contact', operation: 'UPDATE', ids: [vars.contactId] }
        ]
      }
    }
  }),
  update: (cache, { data }) => {
    // Apollo automatically updates cache using impacts
    if (data.qualifyLead._meta) {
      data.qualifyLead._meta.impacts.forEach(impact => {
        if (impact.operation === 'UPDATE') {
          cache.modify({
            id: cache.identify({ __typename: impact.entity, id: impact.ids[0] }),
            fields: {
              status: () => data.qualifyLead.data.status
            }
          });
        }
      });
    }
  }
});
```

---

## Type-Safe Frontend Integration

### Generated TypeScript Types

```typescript
// generated/types/contact.ts
export interface Contact {
  id: string;
  identifier: string;
  email: string;
  firstName: string;
  lastName: string;
  company: Company;
  status: ContactStatus;
}

export enum ContactStatus {
  Lead = 'lead',
  Qualified = 'qualified',
  Customer = 'customer',
}

export interface QualifyLeadInput {
  contactId: string;
}

export interface QualifyLeadResult {
  status: 'success' | 'error';
  code: string;
  message?: string;
  data?: Contact;
  _meta?: {
    impacts: Impact[];
  };
}
```

### Using Types in React

```typescript
import { Contact, ContactStatus, QualifyLeadResult } from './generated/types';

interface Props {
  contact: Contact;
}

function ContactCard({ contact }: Props) {
  const isLead = contact.status === ContactStatus.Lead;

  const handleQualify = async () => {
    const result: QualifyLeadResult = await qualifyLead({
      variables: { contactId: contact.id }
    });

    if (result.status === 'success') {
      // TypeScript knows result.data is Contact
      console.log(result.data.status);
    }
  };

  return (
    <div>
      <h3>{contact.firstName} {contact.lastName}</h3>
      {isLead && <button onClick={handleQualify}>Qualify</button>}
    </div>
  );
}
```

---

## FraiseQL Auto-Discovery

### SQL Comment Annotations

SpecQL adds FraiseQL annotations automatically:

```sql
-- Generated by SpecQL
COMMENT ON FUNCTION app.qualify_lead IS $$
@fraiseql:mutation
@fraiseql:entity Contact
@fraiseql:operation update
@fraiseql:impacts [{"entity":"Contact","operation":"update"}]
$$;
```

**FraiseQL reads these comments** to auto-generate GraphQL schema—no manual configuration.

---

## Apollo Client Integration Patterns

### Pattern 1: Query with Variables

```typescript
const GET_CONTACTS = gql`
  query GetContacts($status: ContactStatus) {
    contacts(where: { status: { eq: $status } }) {
      id
      email
      firstName
      lastName
      status
    }
  }
`;

function ContactList() {
  const { data, loading } = useQuery(GET_CONTACTS, {
    variables: { status: 'lead' }
  });

  if (loading) return <Spinner />;

  return (
    <ul>
      {data.contacts.map(contact => (
        <li key={contact.id}>{contact.email}</li>
      ))}
    </ul>
  );
}
```

### Pattern 2: Mutation with Refetch

```typescript
const [createContact] = useMutation(CREATE_CONTACT, {
  refetchQueries: [{ query: GET_CONTACTS }],
  awaitRefetchQueries: true,
});
```

### Pattern 3: Cache Updates

```typescript
const [deleteContact] = useMutation(DELETE_CONTACT, {
  update(cache, { data }) {
    if (data.deleteContact.status === 'success') {
      const contactId = data.deleteContact.data.id;

      cache.evict({ id: `Contact:${contactId}` });
      cache.gc();
    }
  }
});
```

---

## Real-Time Updates (Optional)

### WebSocket Subscriptions

```graphql
type Subscription {
  contactUpdated(id: ID!): Contact!
}
```

```typescript
const CONTACT_SUBSCRIPTION = gql`
  subscription OnContactUpdated($id: ID!) {
    contactUpdated(id: $id) {
      id
      status
      updatedAt
    }
  }
`;

function useRealtimeContact(contactId: string) {
  useSubscription(CONTACT_SUBSCRIPTION, {
    variables: { id: contactId },
    onSubscriptionData: ({ client, subscriptionData }) => {
      // Update cache
      client.cache.writeFragment({
        id: `Contact:${contactId}`,
        fragment: gql`fragment UpdatedContact on Contact { status updatedAt }`,
        data: subscriptionData.data.contactUpdated,
      });
    }
  });
}
```

---

## Best Practices

### ✅ Use Generated Hooks

```typescript
// Good: Use generated hook
import { useQualifyLead } from './generated/hooks';
const [qualifyLead, { loading }] = useQualifyLead();

// Bad: Manual GraphQL
const [qualifyLead] = useMutation(gql`...`);
```

### ✅ Handle Errors Properly

```typescript
const result = await mutation();

if (result.data.mutation.status === 'error') {
  // Business logic error
  handleBusinessError(result.data.mutation.code);
} else {
  // Success
  handleSuccess(result.data.mutation.data);
}
```

### ✅ Use Optimistic UI for Better UX

```typescript
useMutation(MUTATION, {
  optimisticResponse: { /* ... */ },
  update: (cache) => { /* Update cache immediately */ }
});
```

---

## Next Steps

- **Tutorial**: [Your First Action](your-first-action.md)
- **Reference**: [CLI Commands](../06_reference/cli-commands.md)
- **Guide**: [Actions](actions.md)

---

**GraphQL integration with SpecQL is automatic, type-safe, and optimized for modern frontends.**
