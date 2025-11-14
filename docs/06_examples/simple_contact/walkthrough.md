# Simple Contact Walkthrough

**Step-by-step guide** - From YAML to working application

This walkthrough shows exactly how to implement the simple contact example from start to finish.

## 🏁 Step 1: Setup

```bash
# Create project directory
mkdir specql-contact-example
cd specql-contact-example

# Create entities directory
mkdir entities
```

## 📝 Step 2: Create Entity

Create `entities/contact.yaml`:

```yaml
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
  - name: qualify_lead
    requires: caller.can_edit_contact
    steps:
      - validate: status = 'lead'
        error: "not_a_lead"
      - update: Contact SET status = 'qualified'
      - notify: owner(email, "Contact qualified")

  - name: create_contact
    steps:
      - validate: email MATCHES email_pattern
        error: "invalid_email"
      - validate: first_name IS NOT NULL
        error: "first_name_required"
      - insert: Contact
```

## 🔧 Step 3: Generate Code

```bash
# Generate database schema and functions
specql generate entities/contact.yaml

# View what was generated
ls -la migrations/
```

**Expected output structure**:
```
migrations/
├── 01_write_side/
│   └── 012_crm/
│       └── 0123_customer/
│           └── 01236_contact/
│               ├── 012361_tb_contact.sql
│               ├── 012362_fn_qualify_lead.sql
│               ├── 012363_fn_create_contact.sql
│               └── 012364_fn_update_status.sql
└── 02_query_side/
    └── 022_crm/
        └── 0223_customer/
            └── 0220310_tv_contact.sql
```

## 🗄️ Step 4: Setup Database

```bash
# Create database
createdb contact_example

# Apply migrations
psql -d contact_example -f migrations/**/*.sql

# Verify tables created
psql -d contact_example -c "\dt crm.*"
```

**Expected output**:
```
              List of relations
 Schema |    Name     | Type  |  Owner
--------|-------------|-------|---------
 crm    | tb_contact  | table | lionel
```

## 🧪 Step 5: Test Business Logic

```bash
# Connect to database
psql -d contact_example
```

**Inside psql**:

```sql
-- Create a test contact
INSERT INTO crm.tb_contact (email, first_name, status)
VALUES ('john@example.com', 'John', 'lead');

-- Get the contact ID
SELECT id, email, first_name, status FROM crm.tb_contact;

-- Test qualification (should succeed)
SELECT * FROM app.qualify_lead('YOUR_CONTACT_ID_HERE');

-- Check status changed
SELECT id, email, status, updated_at FROM crm.tb_contact;

-- Test validation (create contact with invalid email)
SELECT * FROM app.create_contact('{"email": "invalid-email", "first_name": "Jane"}'::jsonb);

-- Test validation (create contact without first name)
SELECT * FROM app.create_contact('{"email": "jane@example.com"}'::jsonb);
```

## 🌐 Step 6: Generate GraphQL API

```bash
# Generate with GraphQL support
specql generate entities/contact.yaml --with-impacts --output-frontend=src/generated

# View generated files
ls -la src/generated/
```

**Generated files**:
```
src/generated/
├── types.ts          # TypeScript types
├── hooks.ts          # React Apollo hooks
├── mutations.ts      # GraphQL mutations
├── queries.ts        # GraphQL queries
└── fragments.ts      # GraphQL fragments
```

## ⚛️ Step 7: Use in React Application

**Install dependencies**:
```bash
npm install @apollo/client graphql
```

**Setup Apollo Client** (`src/apollo.ts`):
```typescript
import { ApolloClient, InMemoryCache } from '@apollo/client';

export const client = new ApolloClient({
  uri: 'http://localhost:4000/graphql', // Your GraphQL endpoint
  cache: new InMemoryCache()
});
```

**Create Contact Component** (`src/ContactCard.tsx`):
```typescript
import React from 'react';
import { useQualifyLead } from './generated/hooks';

interface Contact {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  status: 'lead' | 'qualified' | 'customer';
  phone?: string;
}

interface ContactCardProps {
  contact: Contact;
}

export function ContactCard({ contact }: ContactCardProps) {
  const [qualifyLead, { loading }] = useQualifyLead();

  const handleQualify = async () => {
    try {
      const result = await qualifyLead({
        variables: { contactId: contact.id }
      });

      if (result.data?.qualifyLead.success) {
        alert('Contact qualified successfully!');
        // Refetch data or update local state
      } else {
        alert('Failed to qualify contact');
      }
    } catch (error) {
      console.error('Error qualifying contact:', error);
    }
  };

  return (
    <div className="contact-card">
      <h3>{contact.firstName} {contact.lastName}</h3>
      <p>Email: {contact.email}</p>
      <p>Status: <strong>{contact.status}</strong></p>
      {contact.phone && <p>Phone: {contact.phone}</p>}

      {contact.status === 'lead' && (
        <button
          onClick={handleQualify}
          disabled={loading}
        >
          {loading ? 'Qualifying...' : 'Qualify Lead'}
        </button>
      )}
    </div>
  );
}
```

**Create Contact Form** (`src/ContactForm.tsx`):
```typescript
import React, { useState } from 'react';
import { useCreateContact } from './generated/hooks';

export function ContactForm() {
  const [formData, setFormData] = useState({
    email: '',
    firstName: '',
    lastName: '',
    phone: ''
  });

  const [createContact, { loading }] = useCreateContact();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const result = await createContact({
        variables: {
          email: formData.email,
          firstName: formData.firstName,
          lastName: formData.lastName,
          phone: formData.phone || undefined
        }
      });

      if (result.data?.createContact.success) {
        alert('Contact created successfully!');
        setFormData({ email: '', firstName: '', lastName: '', phone: '' });
      } else {
        alert('Failed to create contact');
      }
    } catch (error) {
      console.error('Error creating contact:', error);
    }
  };

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
  };

  return (
    <form onSubmit={handleSubmit} className="contact-form">
      <div>
        <label>Email:</label>
        <input
          type="email"
          value={formData.email}
          onChange={handleChange('email')}
          required
        />
      </div>

      <div>
        <label>First Name:</label>
        <input
          type="text"
          value={formData.firstName}
          onChange={handleChange('firstName')}
          required
        />
      </div>

      <div>
        <label>Last Name:</label>
        <input
          type="text"
          value={formData.lastName}
          onChange={handleChange('lastName')}
        />
      </div>

      <div>
        <label>Phone:</label>
        <input
          type="tel"
          value={formData.phone}
          onChange={handleChange('phone')}
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Creating...' : 'Create Contact'}
      </button>
    </form>
  );
}
```

## 🎯 Step 8: Complete Application

**App Component** (`src/App.tsx`):
```typescript
import React from 'react';
import { ApolloProvider } from '@apollo/client';
import { client } from './apollo';
import { ContactForm } from './ContactForm';
import { ContactList } from './ContactList';

function App() {
  return (
    <ApolloProvider client={client}>
      <div className="app">
        <h1>Contact Manager</h1>
        <ContactForm />
        <ContactList />
      </div>
    </ApolloProvider>
  );
}

export default App;
```

**Contact List Component** (`src/ContactList.tsx`):
```typescript
import React from 'react';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import { ContactCard } from './ContactCard';

const GET_CONTACTS = gql`
  query GetContacts {
    contacts {
      id
      email
      firstName
      lastName
      status
      phone
    }
  }
`;

export function ContactList() {
  const { loading, error, data } = useQuery(GET_CONTACTS);

  if (loading) return <p>Loading contacts...</p>;
  if (error) return <p>Error loading contacts: {error.message}</p>;

  return (
    <div className="contact-list">
      <h2>Contacts</h2>
      {data.contacts.map((contact: any) => (
        <ContactCard key={contact.id} contact={contact} />
      ))}
    </div>
  );
}
```

## 🚀 Step 9: Run the Application

```bash
# Start your GraphQL server (implementation depends on your backend)
npm start

# Or if using Next.js
npm run dev
```

## 🧪 Step 10: Run Tests

```bash
# Generate tests
specql generate entities/contact.yaml --with-tests

# Run pgTAP tests
psql -d contact_example -f tests/**/*.sql

# Run pytest tests
pytest tests/
```

## 🎉 Success!

You've built a complete contact management system with:

✅ **Database Schema**: PostgreSQL tables with Trinity pattern
✅ **Business Logic**: PL/pgSQL functions with validation
✅ **GraphQL API**: Type-safe mutations and queries
✅ **React Frontend**: TypeScript components with Apollo hooks
✅ **Tests**: Comprehensive test coverage
✅ **Type Safety**: End-to-end TypeScript integration

**From 25 lines of YAML to a production-ready application!**

## 🔄 What Next?

- **Add more fields** to the contact entity
- **Create related entities** (Company, Address)
- **Add more actions** (update, delete, search)
- **Implement authentication** and authorization
- **Add real email notifications**
- **Deploy to production**

The same SpecQL approach scales to complex enterprise applications with hundreds of entities and thousands of lines of generated code.