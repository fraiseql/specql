# Simple Blog System Example

**What You'll Build**: A complete blog platform with posts, authors, comments, and tags.

**Time**: 20 minutes
**Complexity**: Beginner

## System Overview

Our blog will have:
- **Authors**: Users who write blog posts
- **Posts**: Blog articles with content
- **Comments**: Reader comments on posts
- **Tags**: Categories and keywords for posts

## Architecture

```
Author (1) ──< (N) Post
   │              │
   │              │
   └──< (N) Comment <──┘
Post (N) ──< (N) PostTag >── (N) Tag
```

## Step 1: Create Author Entity

Create `entities/blog/author.yaml`:

```yaml
entity: Author
schema: blog
description: A blog author/user

fields:
  # Identity
  username: text
  email: email
  display_name: text
  bio: text

  # Status
  status: enum(active, inactive)

indexes:
  - fields: [username]
    unique: true
  - fields: [email]
    unique: true

actions:
  - name: deactivate_author
    description: Deactivate an author account
    requires: caller.can_manage_authors
    steps:
      - update: Author SET status = 'inactive'
      - log: "Author deactivated"
```

## Step 2: Create Post Entity

Create `entities/blog/post.yaml`:

```yaml
entity: Post
schema: blog
description: A blog post/article

fields:
  # Content
  title: text
  slug: text
  content: text
  excerpt: text

  # Metadata
  published_at: timestamp
  status: enum(draft, published, archived)

  # Relationships
  author: ref(Author)

indexes:
  - fields: [slug]
    unique: true
  - fields: [status, published_at]
  - fields: [author_id, status]

actions:
  - name: publish_post
    description: Publish a draft post
    requires: caller.can_publish_posts
    steps:
      - validate: status = 'draft'
        error: "post_not_draft"
      - update: Post SET status = 'published', published_at = NOW()
      - notify: subscribers
      - log: "Post published"

  - name: archive_post
    description: Archive a published post
    requires: caller.can_manage_posts
    steps:
      - validate: status = 'published'
        error: "post_not_published"
      - update: Post SET status = 'archived'
      - log: "Post archived"
```

## Step 3: Create Comment Entity

Create `entities/blog/comment.yaml`:

```yaml
entity: Comment
schema: blog
description: A comment on a blog post

fields:
  # Content
  content: text

  # Relationships
  post: ref(Post)
  author: ref(Author)

  # Status
  status: enum(pending, approved, rejected)

indexes:
  - fields: [post_id, status]
  - fields: [author_id, created_at]

actions:
  - name: approve_comment
    description: Approve a pending comment
    requires: caller.can_moderate_comments
    steps:
      - validate: status = 'pending'
        error: "comment_not_pending"
      - update: Comment SET status = 'approved'
      - notify: comment_author
      - log: "Comment approved"

  - name: reject_comment
    description: Reject a pending comment
    requires: caller.can_moderate_comments
    steps:
      - validate: status = 'pending'
        error: "comment_not_pending"
      - update: Comment SET status = 'rejected'
      - log: "Comment rejected"
```

## Step 4: Create Tag Entity

Create `entities/blog/tag.yaml`:

```yaml
entity: Tag
schema: blog
description: A tag/category for blog posts

fields:
  # Identity
  name: text
  slug: text
  description: text

indexes:
  - fields: [slug]
    unique: true
  - fields: [name]
```

## Step 5: Create PostTag Entity

Create `entities/blog/post_tag.yaml`:

```yaml
entity: PostTag
schema: blog
description: Many-to-many relationship between posts and tags

fields:
  # Relationships
  post: ref(Post)
  tag: ref(Tag)

indexes:
  - fields: [post_id, tag_id]
    unique: true
  - fields: [tag_id, post_id]
```

## Step 6: Generate the Complete System

```bash
# Create output directory
mkdir -p output/blog

# Generate all entities
specql generate entities/blog/*.yaml --output output/blog

# You should see generation for all 5 entities
```

## Step 7: Inspect Generated Code

### PostgreSQL Schema
```bash
# Check the generated tables
cat output/blog/postgresql/blog/01_tables.sql

# You'll see:
# - blog.tb_author (authors)
# - blog.tb_post (posts)
# - blog.tb_comment (comments)
# - blog.tb_tag (tags)
# - blog.tb_post_tag (post-tag relationships)
# - Foreign key relationships
# - Indexes and constraints
```

### Business Logic Functions
```bash
# Check the generated functions
cat output/blog/postgresql/blog/02_functions.sql

# You'll see functions like:
# - blog.fn_post_publish_post()
# - blog.fn_comment_approve_comment()
# - blog.fn_author_deactivate_author()
```

### Java/Spring Boot
```bash
# Check Java entities
ls output/blog/java/com/example/blog/

# You'll see:
# - Author.java, AuthorRepository.java, AuthorService.java
# - Post.java, PostRepository.java, PostService.java
# - Comment.java, CommentRepository.java, CommentService.java
# - Tag.java, TagRepository.java, TagService.java
# - PostTag.java, PostTagRepository.java, PostTagService.java
```

## Step 8: Test the Blog System

If you have PostgreSQL running:

```bash
# Create test database
createdb blog_test

# Apply schema
psql blog_test < output/blog/postgresql/blog/01_tables.sql
psql blog_test < output/blog/postgresql/blog/02_functions.sql

# Insert test data
psql blog_test << 'EOF'
-- Create an author
INSERT INTO blog.tb_author (username, email, display_name, status)
VALUES ('johndoe', 'john@example.com', 'John Doe', 'active');

-- Create a post
INSERT INTO blog.tb_post (title, slug, content, excerpt, author_id, status)
VALUES ('My First Blog Post', 'my-first-blog-post', 'This is the content...', 'This is an excerpt', 1, 'draft');

-- Create tags
INSERT INTO blog.tb_tag (name, slug, description)
VALUES ('Technology', 'technology', 'Tech-related posts');

INSERT INTO blog.tb_tag (name, slug, description)
VALUES ('Tutorial', 'tutorial', 'How-to guides');

-- Tag the post
INSERT INTO blog.tb_post_tag (post_id, tag_id) VALUES (1, 1);
INSERT INTO blog.tb_post_tag (post_id, tag_id) VALUES (1, 2);

-- Add a comment
INSERT INTO blog.tb_comment (content, post_id, author_id, status)
VALUES ('Great post!', 1, 1, 'pending');
EOF

# Query the data
psql blog_test -c "SELECT * FROM blog.tv_author;"
psql blog_test -c "SELECT * FROM blog.tv_post;"
psql blog_test -c "SELECT * FROM blog.tv_comment;"
psql blog_test -c "SELECT * FROM blog.tv_tag;"
psql blog_test -c "SELECT * FROM blog.tv_post_tag;"

# Test business logic
psql blog_test -c "SELECT blog.fn_post_publish_post(1, 'admin@example.com');"
psql blog_test -c "SELECT blog.fn_comment_approve_comment(1, 'admin@example.com');"
```

## Step 9: FraiseQL Integration

Add this to your FraiseQL configuration:

```yaml
# fraiseql-config.yaml
schemas:
  - name: blog
    entities:
      - entities/blog/author.yaml
      - entities/blog/post.yaml
      - entities/blog/comment.yaml
      - entities/blog/tag.yaml
      - entities/blog/post_tag.yaml

# This gives you instant GraphQL API:
# - query { posts(status: PUBLISHED) { title author { displayName } tags { name } comments { content } } }
# - mutation { publishPost(postId: 1) { success } }
# - mutation { approveComment(commentId: 1) { success } }
```

## Common Blog Patterns Used

### 1. Content Workflow
- **Draft** → **Published** → **Archived**
- Authors create drafts, editors publish, admins archive

### 2. Moderation System
- **Pending** → **Approved/Rejected**
- Comments require approval before being visible

### 3. Slug-based URLs
Unique slugs for SEO-friendly URLs:
```yaml
slug: text  # e.g., "my-first-blog-post"
```

### 4. Many-to-Many Relationships
Tags connected to posts via junction table:
```yaml
entity: PostTag
fields:
  post: ref(Post)
  tag: ref(Tag)
```

### 5. Audit Logging
All actions automatically log changes with timestamps and user context.

## Full Source Code

All YAML files for this example:
- [View Source](../../examples/simple-blog/)
- [View on GitHub](https://github.com/fraiseql/specql/tree/main/examples/simple-blog)

## Next Steps

- Add user authentication and permissions
- Implement rich text editing
- Add image/file uploads
- Create admin dashboard
- Add search and filtering
- Implement RSS feeds
- Set up comment notifications

This blog system demonstrates how SpecQL enables rapid development of content management systems with proper relationships, workflow management, and multi-language code generation.