# Migrating TypeScript/Prisma Projects to SpecQL

## Overview

This guide helps you migrate existing TypeScript/Prisma projects to SpecQL, enabling multi-language code generation from a single source of truth.

## Why Migrate to SpecQL?

- **Single Source of Truth**: Define your data models once in SpecQL YAML
- **Multi-Language Generation**: Generate code for TypeScript, Java, Rust, and more
- **Type Safety**: Maintain type safety across all generated code
- **Round-Trip Compatibility**: Convert existing Prisma schemas to SpecQL and back
- **Performance**: Fast parsing and generation (100+ entities/second)

## Migration Process

### Step 1: Reverse Engineer Your Prisma Schema

First, convert your existing Prisma schema to SpecQL YAML:

```bash
# Install SpecQL (if not already installed)
pip install specql

# Reverse engineer your Prisma schema
uv run specql reverse-engineer-prisma \
  --source ./prisma/schema.prisma \
  --output ./entities/
```

**What happens:**
- Your `schema.prisma` file is parsed
- Models are converted to SpecQL YAML format
- Generated files are saved in `./entities/` directory

### Step 2: Review Generated YAML

Examine the generated SpecQL YAML files:

**Before (Prisma):**
```prisma
model User {
  id          Int      @id @default(autoincrement())
  email       String   @unique
  name        String?
  profile     Profile?
  posts       Post[]
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model Profile {
  id       Int    @id @default(autoincrement())
  bio      String?
  userId   Int    @unique
  user     User   @relation(fields: [userId], references: [id])
}

model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  published Boolean  @default(false)
  authorId  Int
  author    User     @relation(fields: [authorId], references: [id])
  tags      Tag[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Tag {
  id    Int    @id @default(autoincrement())
  name  String @unique
  posts Post[]
}
```

**After (SpecQL YAML):**
```yaml
# entities/User.yaml
entity: User
schema: public
fields:
  email: text!
  name: text
  profile: reference Profile
  posts: reference! Post[]
  createdAt: datetime
  updatedAt: datetime

# entities/Profile.yaml
entity: Profile
schema: public
fields:
  bio: text
  user: reference! User

# entities/Post.yaml
entity: Post
schema: public
fields:
  title: text!
  content: text
  published: boolean
  author: reference! User
  tags: reference! Tag[]
  createdAt: datetime
  updatedAt: datetime

# entities/Tag.yaml
entity: Tag
schema: public
fields:
  name: text!
  posts: reference! Post[]
```

**Key Changes:**
- Audit fields (`id`, `createdAt`, `updatedAt`) are auto-generated
- Field types use SpecQL syntax: `text`, `integer`, `boolean`, `datetime`, `reference`
- Required fields marked with `!`
- Relationships use `reference` type
- Arrays denoted with `[]`

### Step 3: Customize SpecQL YAML

Edit the generated YAML to match your domain needs:

```yaml
# Add validation rules, defaults, and business logic
entity: User
schema: public
fields:
  email: text!
  name: text
  profile: reference Profile
  posts: reference! Post[]
actions:
  - name: createUser
    steps:
      - type: validate
        expression: "email is valid"
      - type: insert
        entity: User
        fields:
          email: $email
          name: $name
```

### Step 4: Generate Code in Multiple Languages

Generate code for all your target languages:

```bash
# Generate Prisma schema (for TypeScript projects)
uv run specql generate typescript entities/ --output-dir=generated/ts

# Generate Java entities (Spring Boot)
uv run specql generate java entities/ --output-dir=generated/java

# Generate Rust models (Diesel)
uv run specql generate rust entities/ --output-dir=generated/rust

# Generate database migrations
uv run specql generate sql entities/ --output-dir=generated/migrations
```

### Step 5: Update Your Application Code

Replace direct Prisma client usage with generated types:

**Before:**
```typescript
// Direct Prisma usage
const user = await prisma.user.create({
  data: {
    email: 'user@example.com',
    name: 'John Doe'
  }
});
```

**After:**
```typescript
// Using generated SpecQL types
import { User } from './generated/types/User';

const userData: User = {
  email: 'user@example.com',
  name: 'John Doe'
};

const user = await prisma.user.create({
  data: userData
});
```

## Advanced Migration Scenarios

### Handling Complex Relationships

**Many-to-Many with Junction Tables:**
```yaml
entity: Post
schema: public
fields:
  title: text!
  tags: reference! Tag[]

entity: Tag
schema: public
fields:
  name: text!
  posts: reference! Post[]
```

**Self-Referential Relationships:**
```yaml
entity: Employee
schema: public
fields:
  name: text!
  manager: reference Employee
  reports: reference! Employee[]
```

### Custom Field Types

**Enums:**
```yaml
entity: Order
schema: public
fields:
  status: enum!
  priority: enum
enum_values:
  - pending
  - processing
  - shipped
  - delivered
```

**Rich Types (JSON):**
```yaml
entity: Product
schema: public
fields:
  metadata: rich  # Stored as JSON
  specifications: rich
```

### Migration Validation

Validate your migration with round-trip testing:

```bash
# Test that SpecQL → Prisma → SpecQL preserves data
uv run specql validate-round-trip entities/
```

## Performance Considerations

- **Parsing**: 100+ entities/second
- **Generation**: 100+ entities/second
- **Round-trip**: 50+ entities/second
- Memory usage scales linearly with entity count

## Troubleshooting

### Common Issues

**"Field type not recognized"**
- Check SpecQL type mapping: `text`, `integer`, `boolean`, `datetime`, `reference`
- Use `rich` for complex/custom types

**"Relationship not found"**
- Ensure referenced entities exist in the same generation batch
- Check entity naming matches exactly

**"Validation errors"**
- Run `uv run specql validate entities/` to check YAML syntax
- Ensure required fields are marked with `!`

### Getting Help

- Check the [SpecQL documentation](https://specql.dev)
- File issues on [GitHub](https://github.com/specql/specql)
- Join the [Discord community](https://discord.gg/specql)

## Migration Checklist

- [ ] Back up existing Prisma schema
- [ ] Run reverse engineering: `specql reverse-engineer-prisma`
- [ ] Review generated YAML files
- [ ] Customize YAML with business logic
- [ ] Generate code for target languages
- [ ] Update application code to use generated types
- [ ] Run tests to ensure compatibility
- [ ] Validate round-trip conversion
- [ ] Deploy with confidence!

## Benefits After Migration

1. **Consistency**: Single source of truth for all languages
2. **Productivity**: Generate boilerplate code automatically
3. **Type Safety**: Compile-time guarantees across languages
4. **Maintainability**: Change models once, regenerate everywhere
5. **Future-Proof**: Easy to add new languages as needed

---

*Happy migrating! 🎉*