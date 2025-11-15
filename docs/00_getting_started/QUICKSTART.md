# SpecQL Quickstart Guide

**Time**: 10 minutes
**Goal**: Generate your first multi-language backend from YAML

By the end of this guide, you'll have:
- ✅ Installed SpecQL
- ✅ Created a SpecQL entity definition
- ✅ Generated PostgreSQL schema
- ✅ Generated Java/Spring Boot code
- ✅ Tested the generated code

## See It In Action

![Quick Start Demo](../demos/quickstart_demo.gif)

---

## Prerequisites

Before starting, ensure you have:
- [ ] Python 3.11 or higher installed
- [ ] `uv` package manager installed ([get it here](https://github.com/astral-sh/uv))
- [ ] Basic understanding of YAML
- [ ] (Optional) PostgreSQL for testing schemas

Check your Python version:
```bash
python --version  # Should show 3.11+
```

---

## Step 1: Install SpecQL (3 minutes)

### 1.1 Install uv (if not already installed)

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows** (PowerShell):
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Verify installation:
```bash
uv --version  # Should show: uv 0.x.x
```

### 1.2 Clone SpecQL

```bash
# Choose a location for SpecQL
cd ~/code  # or wherever you keep projects

# Clone the repository
git clone https://github.com/fraiseql/specql.git
cd specql
```

### 1.3 Install Dependencies

```bash
# This installs all Python dependencies
uv sync

# Install SpecQL in editable mode
uv pip install -e .
```

### 1.4 Verify Installation

```bash
# Check SpecQL CLI is available
specql --help
# Should show list of commands

# Test generation with dry run
specql generate entities/examples/contact_lightweight.yaml --dry-run
# Should show generation output without errors
```

**✅ Checkpoint**: If you see generation output without errors, SpecQL is installed correctly!

**❌ Troubleshooting**:
- If `specql` command not found, make sure uv's bin directory is in your PATH
- On macOS/Linux: Add `export PATH="$HOME/.local/bin:$PATH"` to your `.bashrc` or `.zshrc`
- On Windows: Add `%USERPROFILE%\.local\bin` to your PATH environment variable
- If generation fails, check that Python 3.11+ is installed: `python --version`

---

## Step 2: Create Your First Entity (2 minutes)

Let's create a simple blog post entity.

### 2.1 Create Project Structure

```bash
# Create a new directory for your project
mkdir ~/my-specql-project
cd ~/my-specql-project

# Create entities directory
mkdir -p entities/blog
```

### 2.2 Create Entity YAML

Create file: `entities/blog/post.yaml`

```yaml
# entities/blog/post.yaml
entity: Post
schema: blog
description: A blog post with author and publication date

fields:
  # Basic fields
  title: text
  slug: text
  content: text
  excerpt: text

  # Metadata
  published_at: timestamp
  author_name: text
  view_count: integer

  # Status
  status: enum(draft, published, archived)

  # Auto-managed fields (created_at, updated_at added automatically)

indexes:
  - fields: [slug]
    unique: true
  - fields: [status, published_at]
  - fields: [author_name]

actions:
  - name: publish
    description: Publish a draft post
    requires: caller.can_publish
    steps:
      - validate: status = 'draft'
        error: "post_already_published"
      - update: Post SET status = 'published', published_at = NOW()
      - notify: subscribers
```

### 2.3 Understand the YAML

Let's break down what we just wrote:

- **entity**: The name of your entity (becomes table name `tb_post`)
- **schema**: PostgreSQL schema name (namespace)
- **fields**: Column definitions with types
  - `text`: String/varchar
  - `timestamp`: Date and time
  - `integer`: Whole number
  - `enum(...)`: Predefined choices
- **indexes**: Database indexes for performance
  - `unique: true`: Ensures no duplicates
- **actions**: Business logic functions
  - `validate`: Check conditions before proceeding
  - `update`: Modify data
  - `notify`: Trigger notifications

**✅ Checkpoint**: You now have a SpecQL entity definition!

---

## Step 3: Generate PostgreSQL Schema (2 minutes)

### 3.1 Generate SQL

```bash
# Generate PostgreSQL schema from your YAML
specql generate entities/blog/post.yaml --output output/postgresql

# You should see:
# ✓ Parsing entities/blog/post.yaml
# ✓ Generating PostgreSQL schema
# ✓ Writing output/postgresql/blog/01_tables.sql
# ✓ Writing output/postgresql/blog/02_functions.sql
# ✓ Generated 450 lines of SQL
```

### 3.2 Inspect Generated Files

```bash
# Look at the generated table
cat output/postgresql/blog/01_tables.sql

# You'll see:
# - CREATE SCHEMA blog;
# - CREATE TABLE blog.tb_post (
#     pk_post SERIAL PRIMARY KEY,
#     id UUID DEFAULT gen_random_uuid(),
#     identifier TEXT,  -- slug
#     title TEXT NOT NULL,
#     content TEXT,
#     ...
#   );
# - Indexes
# - Constraints
```

### 3.3 Test the Schema (Optional)

If you have PostgreSQL installed:

```bash
# Create a test database
createdb specql_test

# Apply the schema
psql specql_test < output/postgresql/blog/01_tables.sql
psql specql_test < output/postgresql/blog/02_functions.sql

# Test inserting data
psql specql_test -c "
INSERT INTO blog.tb_post (title, slug, content, status)
VALUES ('My First Post', 'first-post', 'Hello World!', 'draft');"

# Test calling the publish action
psql specql_test -c "
SELECT blog.fn_post_publish(1, 'user@example.com');"

# Query the data
psql specql_test -c "SELECT * FROM blog.tv_post;"
```

**✅ Checkpoint**: If you can query `blog.tv_post`, your schema works!

---

## Step 4: Generate Java/Spring Boot Code (2 minutes)

### 4.1 Generate Java

```bash
specql generate entities/blog/post.yaml --target java --output output/java

# You should see:
# ✓ Generating Java/Spring Boot code
# ✓ Writing output/java/com/example/blog/Post.java
# ✓ Writing output/java/com/example/blog/PostRepository.java
# ✓ Writing output/java/com/example/blog/PostService.java
# ✓ Writing output/java/com/example/blog/PostController.java
# ✓ Generated 380 lines of Java
```

### 4.2 Inspect Generated Java

```bash
# Look at the JPA entity
cat output/java/com/example/blog/Post.java
```

You'll see:
```java
package com.example.blog;

import lombok.Data;
import javax.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Data
@Entity
@Table(name = "tb_post", schema = "blog")
public class Post {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "pk_post")
    private Long pkPost;

    @Column(name = "id", unique = true)
    private UUID id = UUID.randomUUID();

    @Column(name = "title", nullable = false)
    private String title;

    @Column(name = "slug", unique = true)
    private String slug;

    // ... more fields

    @Enumerated(EnumType.STRING)
    @Column(name = "status")
    private PostStatus status;

    // Timestamps
    @Column(name = "created_at")
    private Instant createdAt;

    @Column(name = "updated_at")
    private Instant updatedAt;
}
```

**✅ Checkpoint**: You now have production-ready Java code!

---

## Step 5: Generate Rust/Diesel Code (1 minute)

```bash
specql generate entities/blog/post.yaml --target rust --output output/rust

# You'll get:
# - Diesel schema definitions
# - Rust model structs
# - Query builders
# - Actix-web handlers
```

---

## Step 6: Generate TypeScript/Prisma (1 minute)

```bash
specql generate entities/blog/post.yaml --target typescript --output output/typescript

# You'll get:
# - Prisma schema
# - TypeScript interfaces
# - Type-safe client
```

---

## What You Just Did

In 10 minutes, you:
1. ✅ Installed SpecQL
2. ✅ Wrote 50 lines of YAML
3. ✅ Generated 2000+ lines of production code across 4 languages:
   - PostgreSQL schema with business logic
   - Java/Spring Boot application
   - Rust/Diesel backend
   - TypeScript/Prisma client

**Code leverage**: 40x (50 YAML → 2000+ code)

---

## Next Steps

### Learn More
- [Complete Tutorial](../01_tutorials/GETTING_STARTED_TUTORIAL.md) - Build a full CRM system
- [YAML Reference](../03_reference/yaml/complete_reference.md) - All field types and options
- [CLI Reference](../03_reference/cli/command_reference.md) - All command options

- [CRM Example](../06_examples/CRM_SYSTEM_COMPLETE.md) - Contact management system
- [E-commerce Example](../06_examples/ECOMMERCE_SYSTEM.md) - Product catalog
- [Blog Example](../06_examples/SIMPLE_BLOG.md) - Content management
- [User Authentication](../06_examples/USER_AUTHENTICATION.md) - Auth system
- [Multi-Tenant SaaS](../06_examples/MULTI_TENANT_SAAS.md) - Enterprise platform

- [Java Migration Guide](../guides/JAVA_MIGRATION_GUIDE.md) - Migrate Java projects
- [Rust Migration Guide](../guides/RUST_MIGRATION_GUIDE.md) - Migrate Rust projects
- [TypeScript Migration Guide](../guides/TYPESCRIPT_MIGRATION_GUIDE.md) - Migrate TypeScript projects

---

**Congratulations!** You're now ready to use SpecQL in your projects. 🎉