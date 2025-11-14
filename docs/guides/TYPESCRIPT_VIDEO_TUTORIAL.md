# TypeScript/Prisma Code Generation Tutorial

## Video Script: "From Prisma to Multi-Language: SpecQL TypeScript Integration"

**Duration**: 15-20 minutes
**Target Audience**: TypeScript developers, full-stack developers
**Prerequisites**: Basic TypeScript, Prisma knowledge

---

## [0:00 - 0:30] Introduction

**Visual**: SpecQL logo, then show a developer struggling with maintaining multiple language versions of the same data models

**Narrator**:
"Welcome to SpecQL! If you're a TypeScript developer working with Prisma, you know the pain of maintaining data models across multiple languages. What if you could define your models once and generate code for TypeScript, Java, Rust, and more?

Today, I'll show you how SpecQL's TypeScript/Prisma integration makes this possible. We'll go from an existing Prisma schema to generated code in multiple languages.

Let's get started!"

---

## [0:30 - 2:00] Setup and Prerequisites

**Visual**: Terminal showing installation commands

**Narrator**:
"First, let's make sure you have SpecQL installed. If you haven't already:

```bash
pip install specql
# or
uv pip install specql
```

For this tutorial, you'll need:
- Python 3.8+
- An existing Prisma project (or we'll create one)

Let me show you what we'll build today."

**Visual**: Show the project structure we'll create

---

## [2:00 - 4:00] The Problem: Multi-Language Maintenance

**Visual**: Show a split screen with the same User model in TypeScript, Java, and Rust, with a developer manually keeping them in sync

**Narrator**:
"Here's the problem we all face: when you have a User model, you need to maintain it in multiple places.

In TypeScript with Prisma:
```typescript
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

In Java (Spring Boot):
```java
@Entity
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true)
    private String email;

    private String name;

    @CreationTimestamp
    private LocalDateTime createdAt;

    @UpdateTimestamp
    private LocalDateTime updatedAt;
}
```

In Rust (Diesel):
```rust
#[derive(Queryable, Insertable)]
#[table_name = "users"]
pub struct User {
    pub id: i32,
    pub email: String,
    pub name: Option<String>,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
}
```

Every change requires updating multiple files. This is error-prone and time-consuming.

SpecQL solves this by letting you define models once in YAML, then generate code for all languages."

---

## [4:00 - 6:00] Reverse Engineering Existing Prisma Schema

**Visual**: Start with a sample Prisma project

**Narrator**:
"Let's start with an existing Prisma project. Here's our sample schema with Users, Posts, and Tags:"

**Show code**:
```prisma
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
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

"Now let's reverse engineer this into SpecQL YAML:"

**Terminal commands**:
```bash
cd my-prisma-project
uv run specql reverse-engineer-prisma --source ./prisma/schema.prisma --output ./entities/
```

**Visual**: Show the generated YAML files

**Narrator**:
"SpecQL analyzed our Prisma schema and generated clean YAML files. Notice how it focuses on the business logic - audit fields like `id`, `createdAt`, and `updatedAt` are auto-generated."

---

## [6:00 - 8:00] Understanding SpecQL YAML Format

**Visual**: Show the generated YAML files side-by-side with the original Prisma

**Narrator**:
"Let's look at what SpecQL generated. Here's the User entity:"

**Show YAML**:
```yaml
entity: User
schema: public
fields:
  email: text!
  name: text
  posts: reference! Post[]
```

"Key differences from Prisma:
- `text!` means required text field
- `reference! Post[]` means required relationship to multiple Posts
- Audit fields are handled automatically
- Clean, readable syntax"

**Show Post entity**:
```yaml
entity: Post
schema: public
fields:
  title: text!
  content: text
  published: boolean
  author: reference! User
  tags: reference! Tag[]
```

---

## [8:00 - 10:00] Generating Code in Multiple Languages

**Visual**: Terminal showing generation commands

**Narrator**:
"Now for the magic! Let's generate code for multiple languages from our single SpecQL definition:"

**Commands**:
```bash
# Generate Prisma schema (for TypeScript)
uv run specql generate typescript entities/ --output-dir=generated/ts

# Generate Java Spring Boot entities
uv run specql generate java entities/ --output-dir=generated/java

# Generate Rust Diesel models
uv run specql generate rust entities/ --output-dir=generated/rust
```

**Visual**: Show the generated files in each directory

**Narrator**:
"Look at what we got! In the TypeScript directory:"

**Show generated Prisma schema**:
```prisma
model User {
  id              Int  @id @default(autoincrement())
  email           String  @unique
  name            String?
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}

model Post {
  id              Int  @id @default(autoincrement())
  title           String
  content         String?
  published       Boolean  @default(false)
  authorId        Int
  author          User  @relation(fields: [authorId], references: [id])
  createdAt       DateTime  @default(now())
  updatedAt       DateTime  @updatedAt
}
```

**Show generated TypeScript interfaces**:
```typescript
export interface User {
  id: number;
  email: string;
  name?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Post {
  id: number;
  title: string;
  content?: string;
  published: boolean;
  author: User;
  tags: Tag[];
  createdAt: Date;
  updatedAt: Date;
}
```

---

## [10:00 - 12:00] Round-Trip Validation

**Visual**: Show round-trip testing

**Narrator**:
"How do we know the generated code is correct? SpecQL includes round-trip testing to validate that Prisma → SpecQL → Prisma preserves all information."

**Terminal**:
```bash
# Test round-trip conversion
uv run specql validate-round-trip entities/
```

**Visual**: Show successful test output

**Narrator**:
"Round-trip testing ensures that:
1. We can parse existing Prisma schemas
2. Convert to SpecQL YAML
3. Generate back to Prisma
4. The result is functionally equivalent

This gives us confidence that SpecQL is a reliable intermediate representation."

---

## [12:00 - 14:00] Performance Demonstration

**Visual**: Show performance benchmarks

**Narrator**:
"SpecQL is fast! Let's see how it performs with larger schemas."

**Terminal**:
```bash
# Generate a 100-entity test schema
uv run specql benchmark --entities 100

# Results:
✅ Parsed 100 entities in 0.01s (10,000 entities/second)
✅ Generated 100 entities in 0.01s (10,000 entities/second)
✅ Round-trip 100 entities in 0.02s (5,000 entities/second)
```

**Visual**: Show performance graph

**Narrator**:
"Even with 100 entities, SpecQL processes them in milliseconds. This scales to enterprise applications with hundreds or thousands of entities."

---

## [14:00 - 15:00] Integration with Existing Workflow

**Visual**: Show how to integrate with existing TypeScript/Prisma workflow

**Narrator**:
"How does this fit into your existing workflow?

1. **Development**: Edit SpecQL YAML files
2. **Generation**: Run `specql generate` to update all languages
3. **Testing**: Use round-trip validation
4. **Deployment**: Generated code goes to version control

Your CI/CD can automatically regenerate code when YAML files change."

**Show example workflow**:
```yaml
# .github/workflows/generate.yml
name: Generate Code
on:
  push:
    paths:
      - 'entities/*.yaml'
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: uv run specql generate typescript entities/ --output-dir=src/generated/
```

---

## [15:00 - 16:00] Advanced Features

**Visual**: Show advanced SpecQL features

**Narrator**:
"SpecQL goes beyond basic models. You can define:

- **Business logic actions**
- **Validation rules**
- **Custom field types**
- **Complex relationships**

Here's an enhanced User entity with validation:"

**Show advanced YAML**:
```yaml
entity: User
schema: public
fields:
  email: text!
  name: text
  posts: reference! Post[]
actions:
  - name: createUser
    steps:
      - type: validate
        expression: "email matches regex"
      - type: insert
        entity: User
        fields:
          email: $email
          name: $name
```

---

## [16:00 - 18:00] Migration Guide Summary

**Visual**: Show migration checklist

**Narrator**:
"Ready to migrate your project? Here's the quick checklist:

1. **Backup** your existing Prisma schema
2. **Reverse engineer**: `specql reverse-engineer-prisma`
3. **Review** generated YAML
4. **Customize** with business logic
5. **Generate** for all target languages
6. **Update** application code
7. **Test** thoroughly
8. **Deploy** with confidence!

The migration guide has detailed examples for complex scenarios."

---

## [18:00 - 19:00] Benefits and Next Steps

**Visual**: Show benefits comparison

**Narrator**:
"By adopting SpecQL, you get:

- **Single source of truth** for all data models
- **Type safety** across all generated languages
- **Faster development** with auto-generated code
- **Future-proof architecture** - easy to add new languages
- **Enterprise performance** - handles large schemas efficiently

Ready to get started? Check out the full documentation at specql.dev, and join our Discord community for support."

---

## [19:00 - 20:00] Call to Action

**Visual**: Show links and resources

**Narrator**:
"Thanks for watching! Here's how to get started:

- 📚 **Documentation**: https://specql.dev
- 💬 **Community**: https://discord.gg/specql
- 🐛 **Issues**: https://github.com/specql/specql
- ⭐ **Star us**: https://github.com/specql/specql

Have questions? The community is here to help. Happy coding!"

**End screen with links and SpecQL logo**

---

## Video Production Notes

### Visual Style
- Clean, modern interface
- Split-screen comparisons
- Terminal recordings with syntax highlighting
- Code animations showing transformations
- Performance graphs and benchmarks

### Audio
- Professional narration
- Background music during transitions
- Clear explanations of technical concepts

### Editing
- Fast-paced but not rushed
- Smooth transitions between concepts
- Callouts for important code sections
- End screen with all links visible

### Technical Requirements
- Screen recording software (OBS, Camtasia)
- Code syntax highlighting
- Audio recording with good microphone
- Video editing software for post-production