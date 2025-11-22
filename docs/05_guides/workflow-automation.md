# Workflow Automation: Migrate & Sync

> **Automate your database schema workflows with SpecQL's migrate and sync commands for continuous development**

## What You'll Learn

This guide covers SpecQL's workflow automation commands that streamline database development:

- ✅ **`workflow migrate`** - Convert existing schemas to SpecQL entities
- ✅ **`workflow sync`** - Keep generated code in sync with entity changes
- ✅ **Automation patterns** - Integrate into CI/CD pipelines
- ✅ **Best practices** - For team development and production deployments

## Prerequisites

- ✅ SpecQL CLI installed
- ✅ Existing database schema or code to migrate
- ✅ Basic understanding of SpecQL entities

## Command Overview

### `workflow migrate`

**Purpose**: Convert existing database schemas or ORM models into SpecQL entity definitions

**Supported Sources**:
- SQL DDL files (PostgreSQL, MySQL, etc.)
- Django models (`models.py`)
- TypeScript interfaces
- Rust structs
- Prisma schemas

**Output**: YAML entity files + generated SQL

### `workflow sync`

**Purpose**: Automatically regenerate code when entity files change

**Features**:
- Incremental regeneration (only changed files)
- Pattern detection integration
- Watch mode for continuous development
- CI/CD integration

## Scenario 1: Migrating a Legacy Database

### Step 1: Export Your Schema

First, extract your existing schema to SQL files:

```bash
# PostgreSQL
pg_dump --schema-only --no-owner mydb > schema.sql

# MySQL
mysqldump --no-data mydb > schema.sql

# Or export specific tables
pg_dump --schema-only --table=users --table=products mydb > schema.sql
```

### Step 2: Run Migration

Convert SQL to SpecQL entities:

```bash
# Basic migration
specql workflow migrate schema.sql --reverse-from=sql -o ./entities

# With validation
specql workflow migrate schema.sql --reverse-from=sql -o ./entities --validate

# Dry run to preview
specql workflow migrate schema.sql --reverse-from=sql -o ./entities --dry-run
```

**What happens**:
1. Parses SQL DDL statements
2. Extracts table definitions, columns, constraints
3. Generates SpecQL YAML entities
4. Validates entity syntax
5. Generates new SQL from entities (verification)

### Step 3: Review Generated Entities

Check the generated YAML files:

```bash
# List generated entities
ls -la entities/

# Review a specific entity
cat entities/user.yaml
```

Example generated entity:

```yaml
entity: User
schema: public
description: "User account"

fields:
  email: text!
  username: text!
  created_at: timestamp
  updated_at: timestamp

# Auto-detected patterns
patterns:
  - audit-trail
```

### Step 4: Customize and Regenerate

Modify entities as needed, then regenerate:

```bash
# Add validation rules
echo "
validation:
  - field: email
    rules:
      - format: email
" >> entities/user.yaml

# Regenerate SQL
specql generate entities/*.yaml -o ./sql
```

## Scenario 2: Migrating Django Models

### Step 1: Export Models

```bash
# Copy your models.py files
cp myapp/models.py ./django_models/
```

### Step 2: Migrate to SpecQL

```bash
# Migrate Django models
specql workflow migrate django_models/ --reverse-from=python -o ./entities

# Target specific files
specql workflow migrate myapp/models.py --reverse-from=python -o ./entities
```

**Django-specific features**:
- Recognizes `models.Model` inheritance
- Maps Django field types to SpecQL types
- Preserves `related_name` and relationship metadata
- Handles custom model methods

## Scenario 3: Continuous Development with Sync

### Step 1: Initial Setup

```bash
# Create entities directory
mkdir entities

# Create initial entity
cat > entities/product.yaml << 'EOF'
entity: Product
schema: ecommerce
fields:
  name: text!
  price: decimal
EOF

# Generate initial schema
specql generate entities/ -o ./sql
```

### Step 2: Enable Sync Monitoring

```bash
# Start sync in watch mode (regenerates on changes)
specql workflow sync entities/ --watch --output ./sql

# Or run once for CI/CD
specql workflow sync entities/ --output ./sql
```

### Step 3: Make Changes

Edit your entity files, and sync will automatically regenerate:

```bash
# Add a new field
echo "  description: text" >> entities/product.yaml

# Add validation
cat >> entities/product.yaml << 'EOF'
validation:
  - field: price
    rules:
      - min: 0
EOF
```

The sync command detects changes and regenerates only the modified files.

## Advanced Automation Patterns

### CI/CD Integration

#### GitHub Actions Example

```yaml
# .github/workflows/schema-sync.yml
name: Schema Sync
on:
  push:
    paths:
      - 'entities/*.yaml'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install SpecQL
        run: pip install specql

      - name: Sync Schema
        run: specql workflow sync entities/ --output ./sql

      - name: Validate Generated SQL
        run: specql validate sql/*.sql

      - name: Commit Changes
        run: |
          git config --global user.name 'SpecQL Bot'
          git config --global user.email 'bot@specql.dev'
          git add sql/
          git commit -m "Auto-sync schema from entity changes" || echo "No changes to commit"
          git push
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: specql-sync
        name: SpecQL Schema Sync
        entry: specql workflow sync entities/ --output sql/
        language: system
        files: ^entities/.*\.yaml$
        pass_filenames: false
```

### Docker Development Environment

```dockerfile
# Dockerfile.dev
FROM python:3.11

RUN pip install specql

WORKDIR /app

# Start sync in watch mode
CMD ["specql", "workflow", "sync", "entities/", "--watch", "--output", "sql/"]
```

## Pattern Detection Integration

### Automatic Pattern Application

```bash
# Sync with pattern detection
specql workflow sync entities/ --include-patterns --output sql/

# Apply specific patterns
specql patterns apply audit-trail entities/user.yaml
specql patterns apply soft-delete entities/product.yaml
```

### Pattern Detection in CI

```yaml
# Detect and suggest patterns
- name: Check for Patterns
  run: |
    specql patterns detect entities/ --format=json > patterns.json
    if [ -s patterns.json ]; then
      echo "Suggested patterns found:"
      cat patterns.json
      echo "::warning::Consider applying detected patterns"
    fi
```

## Error Handling and Recovery

### Common Issues

#### Migration Errors

```bash
# Invalid SQL syntax
specql workflow migrate broken.sql --reverse-from=sql
# Error: Parse error at line 15: unexpected token

# Solution: Fix SQL or use --continue-on-error
specql workflow migrate broken.sql --continue-on-error --reverse-from=sql
```

#### Sync Conflicts

```bash
# Manual edits to generated files
specql workflow sync entities/
# Warning: sql/user.sql has been manually modified

# Force regeneration
specql workflow sync entities/ --force
```

#### Validation Failures

```bash
# Entity validation errors
specql workflow migrate models.py --validate
# Error: Field 'price' must have validation rules

# Fix and retry
specql validate entities/ --fix
```

## Best Practices

### Directory Structure

```
project/
├── entities/           # SpecQL YAML files
│   ├── user.yaml
│   ├── product.yaml
│   └── order.yaml
├── sql/               # Generated SQL
│   ├── 001_user.sql
│   ├── 002_product.sql
│   └── 003_order.sql
├── migrations/        # Database migrations
└── scripts/
    └── migrate.sh     # Migration scripts
```

### Version Control

```bash
# Commit entities and generated code together
git add entities/ sql/
git commit -m "Add product entity with pricing validation"

# Use .gitignore for generated files in development
echo "sql/*.sql" >> .gitignore
```

### Team Workflow

1. **Feature Branch**: Create feature branch
2. **Entity Changes**: Modify YAML files
3. **Sync**: Run `specql workflow sync` to regenerate
4. **Test**: Run tests against generated schema
5. **Review**: Code review includes entity changes
6. **Merge**: Merge with automatic schema sync

## Troubleshooting

### Migration Issues

**"No tables found in SQL file"**
- Check SQL file contains CREATE TABLE statements
- Use `--verbose` for detailed parsing info

**"Unsupported column type"**
- Some database-specific types may not be recognized
- Manually adjust the generated YAML

### Sync Issues

**"File has been modified"**
- Generated files were manually edited
- Use `--force` to overwrite or move manual changes to entities

**"Pattern detection failed"**
- Ensure UniversalPatternDetector is available
- Check entity YAML syntax

### Performance

**Large projects**: Use `--parallel` for sync operations
**Many files**: Use include/exclude patterns to limit scope

## Next Steps

- **[Pattern Detection Guide](pattern-detection.md)** - Advanced pattern usage
- **[Production Deployment](../05_guides/production-deploy.md)** - Deploying generated schemas
- **[Multi-Tenancy](../05_guides/multi-tenancy.md)** - SaaS applications

## Related Commands

- `specql generate` - Manual code generation
- `specql validate` - Entity validation
- `specql patterns detect` - Pattern analysis
- `specql reverse` - Individual file conversion

---

**Time to read: 10 minutes | Commands covered: 2 | Use cases: Migration, Sync, CI/CD**</content>
</xai:function_call name="todowrite">
<parameter name="todos">[{"status":"completed","id":"create-workflow-guide"}]
