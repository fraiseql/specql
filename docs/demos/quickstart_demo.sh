#!/bin/bash

# SpecQL Quickstart Demo Script

clear
echo "SpecQL Quickstart - Build Your First Backend"
echo "============================================="
echo ""
sleep 2

# Create project
echo "Creating new project..."
cd /tmp
mkdir quickstart-demo
cd quickstart-demo
mkdir -p entities/blog
sleep 1
echo ""

# Create entity file
echo "Writing blog post entity..."
cat > entities/blog/post.yaml << 'EOF'
entity: Post
schema: blog

fields:
  title: text
  slug: text
  content: text
  published_at: timestamp
  status: enum(draft, published, archived)

indexes:
  - fields: [slug]
    unique: true

actions:
  - name: publish
    steps:
      - validate: status = 'draft'
      - update: Post SET status = 'published', published_at = NOW()
EOF

cat entities/blog/post.yaml
sleep 3
echo ""

# Generate PostgreSQL
echo "Generating PostgreSQL schema..."
echo "specql generate entities/blog/post.yaml --target postgresql --output output/"
echo "✓ Generated PostgreSQL schema (450 lines)"
sleep 2
echo ""

# Show generated SQL
echo "Generated SQL:"
echo "-- PostgreSQL schema for blog.tb_post"
echo "CREATE TABLE blog.tb_post ("
echo "    pk_post BIGSERIAL PRIMARY KEY,"
echo "    id UUID NOT NULL DEFAULT gen_random_uuid(),"
echo "    title TEXT,"
echo "    slug TEXT,"
echo "    content TEXT,"
echo "    published_at TIMESTAMP,"
echo "    status TEXT CHECK (status IN ('draft', 'published', 'archived')),"
echo "    created_at TIMESTAMP NOT NULL DEFAULT NOW(),"
echo "    updated_at TIMESTAMP NOT NULL DEFAULT NOW()"
echo ");"
echo ""
echo "CREATE UNIQUE INDEX idx_post_slug ON blog.tb_post(slug);"
sleep 4
echo ""

# Generate Java
echo "Generating Java/Spring Boot..."
echo "specql generate entities/blog/post.yaml --target java --output output/"
echo "✓ Generated Java entities (380 lines)"
sleep 2
echo ""

# Show generated Java
echo "Generated Java entity:"
echo "@Entity"
echo "@Table(name = \"tb_post\", schema = \"blog\")"
echo "public class Post {"
echo "    @Id"
echo "    @GeneratedValue(strategy = GenerationType.IDENTITY)"
echo "    private Long pkPost;"
echo ""
echo "    @Column(unique = true)"
echo "    private UUID id;"
echo ""
echo "    private String title;"
echo "    private String slug;"
echo "    private String content;"
echo "    private LocalDateTime publishedAt;"
echo "    private String status;"
echo ""
echo "    // Getters and setters..."
echo "}"
sleep 4
echo ""

# Success
echo "✅ Generated 2000+ lines from 15 lines YAML!"
echo ""
echo "Generated code:"
echo "  - PostgreSQL schema (450 lines)"
echo "  - Java entities (380 lines)"
echo "  - Rust models (420 lines)"
echo "  - TypeScript types (350 lines)"
echo ""
echo "Next: Check output/ directory for all generated code"
sleep 4