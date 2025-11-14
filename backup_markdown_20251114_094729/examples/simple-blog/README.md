# Simple Blog Example

**A complete blog platform built with SpecQL** 📝

From YAML to production PostgreSQL + GraphQL in minutes.

## Overview

This example demonstrates a simple blog with:
- **Posts** with rich markdown content
- **Authors** with profiles
- **Comments** on posts
- **Tags** for categorization

**What you get:**
- ✅ PostgreSQL tables with proper relationships
- ✅ CRUD operations for all entities
- ✅ GraphQL API with FraiseQL auto-discovery
- ✅ Rich types (markdown, email, slug)
- ✅ Audit trails and data validation

## Quick Start

### 1. Generate the Schema

```bash
# From project root
cd examples/simple-blog

# Generate all entities
specql generate entities/*.yaml
```

### 2. Deploy to Database

```bash
# Create database
createdb blog_example

# Run migrations
cd db/schema
confiture migrate up
```

### 3. Test the API

```sql
-- Create an author
SELECT blog.create_author(
  email => 'author@example.com',
  first_name => 'John',
  last_name => 'Writer',
  bio => 'Tech blogger and author'
);

-- Create a post
SELECT blog.create_post(
  title => 'My First Blog Post',
  slug => 'my-first-blog-post',
  content => '# Hello World\nThis is my first post!',
  author_id => (SELECT id FROM blog.tb_author WHERE email = 'author@example.com' LIMIT 1),
  published => true
);

-- Add a comment
SELECT blog.create_comment(
  post_id => (SELECT id FROM blog.tb_post WHERE slug = 'my-first-blog-post' LIMIT 1),
  author_name => 'Anonymous Reader',
  author_email => 'reader@example.com',
  content => 'Great post! Looking forward to more.'
);
```

## Entities

### Author (`author.yaml`)

Blog post authors with profiles:

```yaml
entity: Author
schema: blog
description: "Blog post author"

fields:
  email: email!          # Rich type with validation
  first_name: text!
  last_name: text!
  bio: markdown          # Rich markdown content
  website: url           # URL validation
  avatar_url: image      # Image URL

actions:
  - name: create_author
  - name: update_author
  - name: get_author
```

**Generated:**
- `blog.tb_author` table
- Email validation and uniqueness
- Helper functions (`author_pk()`, `author_id()`)
- CRUD operations with validation

### Post (`post.yaml`)

Blog posts with rich content:

```yaml
entity: Post
schema: blog
description: "Blog post with rich content"

fields:
  title: text!
  slug: slug!            # URL-friendly identifier
  content: markdown!     # Rich markdown content
  excerpt: text          # Short summary
  published: boolean = false
  published_at: datetime

  # Relationships
  author: ref(Author)!   # Required author

  # Metadata
  reading_time: integer  # Estimated reading time
  word_count: integer    # Word count

actions:
  - name: create_post
  - name: update_post
  - name: publish_post
  - name: unpublish_post
```

**Features:**
- Slug generation for SEO-friendly URLs
- Publication workflow
- Author relationship
- Content metadata

### Comment (`comment.yaml`)

Comments on blog posts:

```yaml
entity: Comment
schema: blog
description: "Comment on a blog post"

fields:
  author_name: text!
  author_email: email
  content: markdown!
  approved: boolean = false

  # Relationships
  post: ref(Post)!

actions:
  - name: create_comment
  - name: approve_comment
  - name: reject_comment
```

**Features:**
- Optional email for anonymous comments
- Approval workflow
- Post relationship

### Tag (`tag.yaml`)

Content tags for categorization:

```yaml
entity: Tag
schema: blog
description: "Content tag for categorization"

fields:
  name: text!
  slug: slug!
  description: text
  color: text          # Hex color code

actions:
  - name: create_tag
  - name: update_tag
```

**Features:**
- SEO-friendly slugs
- Optional color coding
- Simple CRUD operations

## Generated Database Schema

### Tables

```sql
-- Authors
CREATE TABLE blog.tb_author (
  pk_author INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  email TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  bio TEXT,
  website TEXT,
  avatar_url TEXT,
  -- Audit fields...
);

-- Posts
CREATE TABLE blog.tb_post (
  pk_post INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  slug TEXT NOT NULL,
  content TEXT NOT NULL,
  excerpt TEXT,
  published BOOLEAN DEFAULT false,
  published_at TIMESTAMPTZ,
  fk_author INTEGER NOT NULL,
  reading_time INTEGER,
  word_count INTEGER,
  -- Audit fields...
);

-- Comments
CREATE TABLE blog.tb_comment (
  pk_comment INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  author_name TEXT NOT NULL,
  author_email TEXT,
  content TEXT NOT NULL,
  approved BOOLEAN DEFAULT false,
  fk_post INTEGER NOT NULL,
  -- Audit fields...
);

-- Tags
CREATE TABLE blog.tb_tag (
  pk_tag INTEGER PRIMARY KEY,
  id UUID DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  description TEXT,
  color TEXT,
  -- Audit fields...
);
```

### Constraints & Validation

```sql
-- Email validation
ALTER TABLE blog.tb_author
ADD CONSTRAINT author_email_check
CHECK (email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');

-- Slug validation
ALTER TABLE blog.tb_post
ADD CONSTRAINT post_slug_check
CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$');

-- Foreign key constraints
ALTER TABLE blog.tb_post
ADD CONSTRAINT tb_post_fk_author_fkey
FOREIGN KEY (fk_author) REFERENCES blog.tb_author(pk_author);

-- Unique constraints
ALTER TABLE blog.tb_author ADD CONSTRAINT tb_author_email_key UNIQUE (email);
ALTER TABLE blog.tb_post ADD CONSTRAINT tb_post_slug_key UNIQUE (slug);
```

### Indexes

```sql
-- Primary key indexes (automatic)
CREATE UNIQUE INDEX idx_tb_author_id ON blog.tb_author(id);
CREATE UNIQUE INDEX idx_tb_post_id ON blog.tb_post(id);

-- Foreign key indexes (automatic)
CREATE INDEX idx_tb_post_fk_author ON blog.tb_post(fk_author);

-- Performance indexes
CREATE INDEX idx_tb_post_published ON blog.tb_post(published) WHERE deleted_at IS NULL;
CREATE INDEX idx_tb_post_slug ON blog.tb_post(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_tb_comment_fk_post ON blog.tb_comment(fk_post) WHERE deleted_at IS NULL;
CREATE INDEX idx_tb_comment_approved ON blog.tb_comment(approved) WHERE deleted_at IS NULL;
```

## GraphQL API

### Queries

```graphql
# Get published posts
query GetPosts {
  posts(filter: { published: true }, limit: 10) {
    edges {
      node {
        id
        title
        slug
        excerpt
        publishedAt
        author {
          id
          firstName
          lastName
          email
        }
      }
    }
  }
}

# Get post with comments
query GetPost($slug: String!) {
  posts(filter: { slug: { eq: $slug } }) {
    edges {
      node {
        id
        title
        content
        comments(filter: { approved: true }) {
          edges {
            node {
              id
              authorName
              content
              createdAt
            }
          }
        }
      }
    }
  }
}
```

### Mutations

```graphql
# Create a post
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    success
    message
    object {
      id
      title
      slug
      author {
        id
        firstName
        lastName
      }
    }
  }
}

# Add a comment
mutation AddComment($input: CreateCommentInput!) {
  createComment(input: $input) {
    success
    message
    object {
      id
      authorName
      content
      approved
    }
  }
}
```

## Business Logic Examples

### Publishing Workflow

```sql
-- Custom action: publish_post
CREATE FUNCTION blog.publish_post(post_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
  v_result app.mutation_result;
  v_pk INTEGER;
BEGIN
  -- Resolve UUID to pk
  v_pk := blog.post_pk(post_id::TEXT);

  -- Update post
  UPDATE blog.tb_post SET
    published = true,
    published_at = now()
  WHERE pk_post = v_pk;

  v_result.success := true;
  v_result.message := 'Post published successfully';

  RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

### Comment Moderation

```sql
-- Approve comment
CREATE FUNCTION blog.approve_comment(comment_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
  v_result app.mutation_result;
  v_pk INTEGER;
BEGIN
  v_pk := blog.comment_pk(comment_id::TEXT);

  UPDATE blog.tb_comment SET
    approved = true
  WHERE pk_comment = v_pk;

  v_result.success := true;
  v_result.message := 'Comment approved';

  RETURN v_result;
END;
$$ LANGUAGE plpgsql;
```

## Extending the Example

### Add Post-Tag Relationships

```yaml
# New entity: PostTag
entity: PostTag
schema: blog
description: "Many-to-many relationship between posts and tags"

fields:
  post: ref(Post)!
  tag: ref(Tag)!

actions:
  - name: tag_post
  - name: untag_post
```

### Add User Authentication

```yaml
# Extend Author entity
entity: Author
extends:
  from: stdlib/crm/contact  # Use stdlib contact
schema: blog

fields:
  # Add authentication
  password_hash: hashSHA256
  email_verified: boolean = false
  last_login: datetime

actions:
  - name: authenticate
  - name: change_password
```

### Add Analytics

```yaml
# New entity: PostView
entity: PostView
schema: blog
description: "Track post views for analytics"

fields:
  post: ref(Post)!
  viewer_ip: ipAddress
  user_agent: text
  viewed_at: datetime!

actions:
  - name: record_view
```

## File Structure

```
examples/simple-blog/
├── README.md                    # This file
├── entities/
│   ├── author.yaml             # Author entity
│   ├── post.yaml               # Post entity
│   ├── comment.yaml            # Comment entity
│   └── tag.yaml                # Tag entity
└── generated/                   # (After generation)
    └── db/schema/
        ├── 10_tables/
        │   ├── author.sql
        │   ├── post.sql
        │   ├── comment.sql
        │   └── tag.sql
        ├── 20_helpers/
        └── 30_functions/
```

## Learning Points

### Rich Types in Action
- `email` - Automatic email validation
- `markdown` - Rich content support
- `slug` - SEO-friendly URLs
- `url` - Website validation

### Relationships
- Foreign key constraints
- Helper functions for ID conversion
- Automatic JOIN optimization

### Business Logic
- Custom actions beyond CRUD
- Validation and error handling
- Workflow state management

### GraphQL Integration
- FraiseQL auto-discovery
- Type-safe API generation
- Automatic resolver creation

## Next Steps

- **Run the example**: Generate and deploy this blog
- **Extend it**: Add features like categories, drafts, or SEO
- **Check other examples**: See `examples/ecommerce/` or `examples/crm/`
- **Read guides**: Learn more in `docs/guides/`

---

**From YAML to blog platform in minutes.** 🚀