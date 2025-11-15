# Multi-Language Tutorial

**Generate code in multiple languages** - PostgreSQL, Java, Rust, TypeScript from one YAML

This tutorial shows how SpecQL generates production-ready code across multiple programming languages from a single entity definition.

## 🎯 What You'll Learn

- Generate PostgreSQL schemas, functions, and views
- Generate Java Spring Boot applications
- Generate Rust Diesel models and handlers
- Generate TypeScript Prisma clients
- Cross-language consistency and type safety

## 📋 Prerequisites

- [ ] Completed [Relationships Tutorial](RELATIONSHIPS_TUTORIAL.md)
- [ ] SpecQL installed with all targets
- [ ] Development environments for target languages

## 🏗️ Step 1: Define Multi-Language Entity

Create a comprehensive entity that will generate well in all languages:

```yaml
# entities/blog/post.yaml
entity: Post
schema: blog
description: "Blog post with full multi-language support"

fields:
  title: text
  slug: text
  content: text
  excerpt: text
  published_at: timestamp
  author_id: integer
  status: enum(draft, published, archived)
  tags: json
  view_count: integer

relationships:
  - name: author
    entity: User
    type: many-to-one
    local_field: author_id
    foreign_field: pk_user

indexes:
  - fields: [slug]
    unique: true
  - fields: [status, published_at]
  - fields: [author_id]

actions:
  - name: publish
    description: "Publish a draft post"
    steps:
      - validate: status = 'draft'
        error: "post_not_draft"
      - update: Post SET status = 'published', published_at = NOW()
      - notify: post_published

  - name: increment_views
    description: "Increment view counter"
    steps:
      - update: Post SET view_count = COALESCE(view_count, 0) + 1
```

## 🗄️ Step 2: Generate PostgreSQL Schema

Generate the database foundation:

```bash
# Generate PostgreSQL only
specql generate entities/blog/post.yaml --target postgresql --output generated/postgresql

# Includes:
# - Table DDL with constraints
# - Business logic functions
# - Query views
# - Performance indexes
```

**Generated table:**
```sql
CREATE TABLE blog.tb_post (
    pk_post SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid(),
    identifier TEXT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    content TEXT,
    excerpt TEXT,
    published_at TIMESTAMPTZ,
    author_id INTEGER,
    status TEXT CHECK (status IN ('draft', 'published', 'archived')),
    tags JSONB,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## ☕ Step 3: Generate Java Spring Boot

Generate complete Java application:

```bash
specql generate entities/blog/post.yaml --target java --output generated/java
```

**Generated files:**
```
generated/java/
├── com/example/blog/
│   ├── Post.java              # JPA Entity
│   ├── PostRepository.java    # Data access
│   ├── PostService.java       # Business logic
│   └── PostController.java    # REST API
└── application.properties     # Configuration
```

**JPA Entity:**
```java
@Entity
@Table(name = "tb_post", schema = "blog")
@Data
public class Post {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "pk_post")
    private Long pkPost;

    @Column(name = "id", unique = true)
    private UUID id;

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "status")
    @Enumerated(EnumType.STRING)
    private PostStatus status;

    @Column(name = "tags", columnDefinition = "jsonb")
    @Type(type = "jsonb")
    private List<String> tags;
}
```

## 🦀 Step 4: Generate Rust Diesel

Generate Rust application with Actix-web:

```bash
specql generate entities/blog/post.yaml --target rust --output generated/rust
```

**Generated files:**
```
generated/rust/
├── Cargo.toml
├── src/
│   ├── models.rs           # Diesel models
│   ├── schema.rs           # Database schema
│   ├── handlers.rs         # HTTP handlers
│   └── main.rs            # Application entry
└── diesel.toml            # Diesel configuration
```

**Diesel Model:**
```rust
#[derive(Queryable, Identifiable)]
#[table_name = "tb_post"]
pub struct Post {
    pub pk_post: i32,
    pub id: Uuid,
    pub identifier: Option<String>,
    pub title: String,
    pub slug: String,
    pub content: Option<String>,
    pub status: PostStatus,
    pub tags: serde_json::Value,
    pub view_count: i32,
}

#[derive(Insertable)]
#[table_name = "tb_post"]
pub struct NewPost<'a> {
    pub id: Uuid,
    pub title: &'a str,
    pub slug: &'a str,
    pub status: PostStatus,
}
```

## 🔷 Step 5: Generate TypeScript Prisma

Generate TypeScript client with GraphQL:

```bash
specql generate entities/blog/post.yaml --target typescript --output generated/typescript
```

**Generated files:**
```
generated/typescript/
├── prisma/
│   └── schema.prisma        # Prisma schema
├── src/
│   ├── types.ts            # TypeScript types
│   ├── client.ts           # Prisma client
│   └── resolvers.ts        # GraphQL resolvers
└── package.json            # Dependencies
```

**Prisma Schema:**
```prisma
model Post {
  pkPost      Int      @id @default(autoincrement())
  id          String   @unique @default(uuid())
  identifier  String?
  title       String
  slug        String   @unique
  content     String?
  excerpt     String?
  publishedAt DateTime?
  authorId    Int?
  status      PostStatus
  tags        Json?
  viewCount   Int      @default(0)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  author      User?    @relation(fields: [authorId], references: [pkUser])
}
```

## 🚀 Step 6: All Languages at Once

Generate everything simultaneously:

```bash
# Generate all targets
specql generate entities/blog/post.yaml \
  --target postgresql \
  --target java \
  --target rust \
  --target typescript \
  --output generated/all
```

**Result:** Complete stack from one YAML file!

## 🧪 Step 7: Cross-Language Testing

Test that all generated code works together:

```bash
# 1. Apply PostgreSQL schema
psql mydb < generated/all/postgresql/blog/01_tables.sql

# 2. Test Java compilation
cd generated/all/java && mvn compile

# 3. Test Rust compilation
cd generated/all/rust && cargo check

# 4. Test TypeScript compilation
cd generated/all/typescript && npm run build
```

## 🎯 Step 8: Integration Benefits

### Type Safety Across Languages

```typescript
// TypeScript (generated)
interface Post {
  id: string;
  title: string;
  status: 'draft' | 'published' | 'archived';
  tags: string[] | null;
}

// Java (generated)
public enum PostStatus {
    DRAFT, PUBLISHED, ARCHIVED
}

// Rust (generated)
#[derive(Debug, Clone, PartialEq, FromSql, ToSql)]
pub enum PostStatus {
    Draft,
    Published,
    Archived,
}
```

### Consistent Business Logic

```sql
-- PostgreSQL function
CREATE FUNCTION blog.fn_post_publish(p_post_id UUID)
RETURNS mutation_result AS $$
BEGIN
    UPDATE blog.tb_post SET status = 'published'
    WHERE id = p_post_id AND status = 'draft';
    -- ... validation and error handling
END;
$$ LANGUAGE plpgsql;
```

```java
// Java service method
public MutationResult publishPost(UUID postId) {
    Post post = postRepository.findById(postId)
        .orElseThrow(() -> new EntityNotFoundException("Post not found"));

    if (post.getStatus() != PostStatus.DRAFT) {
        throw new BusinessException("Post is not a draft");
    }

    post.setStatus(PostStatus.PUBLISHED);
    postRepository.save(post);

    return MutationResult.success("Post published");
}
```

## 🔄 Next Steps

- **[Reverse Engineering Tutorial](REVERSE_ENGINEERING_TUTORIAL.md)** - Import existing code
- **[CRM Example](../06_examples/CRM_SYSTEM_COMPLETE.md)** - Real multi-language application
- **[E-commerce Example](../06_examples/ECOMMERCE_SYSTEM.md)** - Complex business logic

## 🆘 Common Issues

**Different field types across languages?**
- SpecQL normalizes types: `text` → String/VARCHAR, `integer` → int/i32/Int

**Business logic consistency?**
- Actions generate equivalent functions/methods in each language
- Validation rules are preserved across all targets

**Integration complexity?**
- Start with one language, then add others
- Use generated APIs for cross-service communication

---

**Congratulations!** You can now generate production applications in multiple languages from a single source of truth.