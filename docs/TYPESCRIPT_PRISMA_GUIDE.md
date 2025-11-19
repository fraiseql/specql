# TypeScript & Prisma Reverse Engineering

SpecQL can reverse engineer TypeScript/Prisma projects to generate SpecQL YAML entities and actions.

## Supported Frameworks

### Prisma Schema
- Model definitions with fields, types, and attributes
- Relations (one-to-one, one-to-many, many-to-many)
- Enums with string values
- Indexes and unique constraints
- Default values and column mappings

### Express
- `router.get()`, `router.post()`, `router.put()`, `router.patch()`, `router.delete()`
- Route parameter extraction (`/users/:id`)
- Prisma database operations

### Fastify
- `fastify.get()`, `fastify.post()`, `fastify.put()`, `fastify.patch()`, `fastify.delete()`
- Route parameter extraction
- Async/await handlers

### Next.js Pages Router
- `pages/api/**/*.ts` files
- `NextApiRequest`/`NextApiResponse` handlers
- Method-based routing (`req.method === 'POST'`)

### Next.js App Router
- `app/api/**/route.ts` files
- `GET`, `POST`, `PUT`, `PATCH`, `DELETE` named exports
- Server Actions with `'use server'` directive

## Example Workflow

### Input: Prisma Schema

**prisma/schema.prisma**:
```prisma
enum ContactStatus {
  LEAD
  QUALIFIED
  CUSTOMER
}

model Contact {
  id        Int           @id @default(autoincrement())
  email     String        @unique
  status    ContactStatus @default(LEAD)
  companyId Int?
  company   Company?      @relation(fields: [companyId], references: [id])

  deletedAt DateTime? @map("deleted_at")
  createdAt DateTime  @default(now()) @map("created_at")
  updatedAt DateTime  @updatedAt @map("updated_at")

  @@map("contacts")
}

model Company {
  id      Int       @id @default(autoincrement())
  name    String
  contacts Contact[]

  @@map("companies")
}
```

### Input: Express Routes

**src/routes/contacts.ts**:
```typescript
import express from 'express';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const router = express.Router();

router.post('/contacts', async (req, res) => {
  const contact = await prisma.contact.create({
    data: {
      email: req.body.email,
      status: 'LEAD'
    }
  });
  res.json(contact);
});

router.get('/contacts/:id', async (req, res) => {
  const contact = await prisma.contact.findUnique({
    where: { id: parseInt(req.params.id) }
  });
  res.json(contact);
});

export default router;
```

### Input: Next.js App Router

**app/api/contacts/route.ts**:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(request: NextRequest) {
  const contacts = await prisma.contact.findMany();
  return NextResponse.json(contacts);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const contact = await prisma.contact.create({
    data: body
  });
  return NextResponse.json(contact, { status: 201 });
}
```

### Input: Next.js Server Actions

**app/actions/contactActions.ts**:
```typescript
'use server';

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function createContact(formData: FormData) {
  const email = formData.get('email') as string;

  const contact = await prisma.contact.create({
    data: { email, status: 'LEAD' }
  });

  return contact;
}

export async function updateContactStatus(id: number, status: string) {
  const contact = await prisma.contact.update({
    where: { id },
    data: { status }
  });

  return contact;
}
```

### Output: SpecQL YAML

```yaml
entity: Contact
schema: public
description: Extracted from TypeScript/Prisma project
fields:
  email: text
  status: enum(LEAD, QUALIFIED, CUSTOMER)
  companyId: integer
  deletedAt: timestamp
  createdAt: timestamp
  updatedAt: timestamp
relations:
  - name: company
    type: belongs_to
    entity: Company
indexes:
  - fields: [email]
unique_constraints:
  - fields: [email]
actions:
  - name: create_contact
    type: create
    entity: Contact
    description: Create Contact via express route
    steps:
      - insert: Contact
  - name: read_contact
    type: read
    entity: Contact
    description: Read Contact via express route
    steps:
      - select: Contact
  - name: read_contacts
    type: read
    entity: Contact
    description: Read Contacts via Next.js App Router
    steps:
      - select: Contact
  - name: create_contact_app
    type: create
    entity: Contact
    description: Create Contact via Next.js App Router
    steps:
      - insert: Contact
  - name: create_contact_action
    type: create
    entity: Contact
    description: Create Contact via Server Action
    steps:
      - insert: Contact
  - name: update_contact_status
    type: update
    entity: Contact
    description: Update Contact Status via Server Action
    steps:
      - update: Contact

---

entity: Company
schema: public
description: Extracted from Prisma schema
fields:
  name: text
relations:
  - name: contacts
    type: has_many
    entity: Contact
```

## Usage

### Command Line

```bash
# Reverse engineer Prisma schema
specql reverse prisma/schema.prisma

# Reverse engineer TypeScript routes
specql reverse src/routes/contacts.ts

# Reverse engineer Next.js API routes
specql reverse app/api/contacts/route.ts

# Reverse engineer entire project
specql reverse . --language typescript
```

### Programmatic API

```python
from src.reverse_engineering.universal_action_mapper import UniversalActionMapper

mapper = UniversalActionMapper()

# Convert Prisma schema
with open('prisma/schema.prisma') as f:
    schema = f.read()
contact_yaml = mapper.convert_code(schema, 'typescript')

# Convert Express routes
with open('src/routes/contacts.ts') as f:
    routes = f.read()
actions_yaml = mapper.convert_code(routes, 'typescript')

print(contact_yaml + actions_yaml)
```

## Supported Patterns

TypeScript reverse engineering detects these universal patterns:

- **State Machine**: Status fields with transitions
- **Soft Delete**: `deleted_at` timestamp fields
- **Audit Trail**: Created/updated timestamp fields
- **Multi-tenant**: Tenant isolation patterns
- **Hierarchical**: Parent-child relationships
- **Versioning**: Version fields and optimistic locking
- **Event Sourcing**: Event-based state changes
- **Sharding**: Data partitioning patterns
- **Cache Invalidation**: Cache management patterns
- **Rate Limiting**: Request throttling patterns

## Limitations

- Complex TypeScript types (unions, generics) are simplified
- Dynamic route generation is not supported
- Middleware and authentication logic is not extracted
- Only Prisma ORM is currently supported for database operations
- Server Action form validation is not analyzed

## Contributing

To add support for additional TypeScript frameworks:

1. Extend `TypeScriptParser` with new extraction methods
2. Add corresponding test cases
3. Update this documentation
4. Submit a pull request

Supported addition candidates:
- NestJS controllers and decorators
- Koa.js routes
- SvelteKit API routes
- Remix routes
- tRPC procedures