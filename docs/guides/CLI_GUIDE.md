# SpecQL CLI Guide

## Overview

The SpecQL CLI transforms YAML business logic definitions into production-ready PostgreSQL schemas. With intelligent defaults and framework-aware generation, it eliminates complex wrapper scripts and delivers GraphQL-ready output out of the box.

## Quick Start

```bash
# Generate production-ready schema (FraiseQL defaults)
specql generate entities/**/*.yaml

# Development mode (flat structure)
specql generate entities/**/*.yaml --dev

# Specific framework
specql generate entities/**/*.yaml --framework django
```

## Framework-Aware Defaults

SpecQL adapts its output based on your target framework. Each framework has production-ready defaults optimized for its ecosystem.

### FraiseQL Framework (Default)

**Best for**: Full-stack PostgreSQL + GraphQL applications

**Defaults**:
- Table views (tv_*) for GraphQL queries
- Trinity pattern (pk_*, id, identifier)
- Audit fields (created_at, updated_at, deleted_at)
- FraiseQL GraphQL annotations
- Helper functions for type-safe access
- Hierarchical output structure
- Registry-based table codes

**Example Output**:
```
migrations/
├── 000_app_foundation.sql
└── 01_write_side/
    ├── 011_crm/
    │   └── 011001_contact/
    │       ├── 011001_tb_contact.sql
    │       ├── 011001_tv_contact.sql
    │       └── 011001_fn_contact_create.sql
    └── 013_catalog/
        └── 013001_product/
            ├── 013001_tb_product.sql
            ├── 013001_tv_product.sql
            └── 013001_fn_product_update.sql
```

### Django Framework

**Best for**: Django ORM applications

**Defaults**:
- No table views (ORM handles queries)
- Single primary key (id)
- Audit fields (auto timestamps)
- Flat output structure
- Confiture-compatible paths

**Example Output**:
```
db/schema/
├── 10_tables/contact.sql
├── 20_helpers/contact_helpers.sql
└── 30_functions/create_contact.sql
```

### Rails Framework

**Best for**: Ruby on Rails applications

**Defaults**:
- No table views (ActiveRecord handles queries)
- Single primary key (id)
- Audit fields (timestamps)
- Flat output structure
- Rails migration patterns

### Prisma Framework

**Best for**: Prisma ORM applications

**Defaults**:
- No table views (Prisma client handles queries)
- Single primary key (id)
- Audit fields (Prisma timestamps)
- Flat output structure
- Prisma schema patterns

## Output Formats

### Hierarchical Format (Default)

**When to use**: Production deployments, large codebases, team collaboration

**Structure**:
```
migrations/
├── 000_app_foundation.sql
└── 01_write_side/
    ├── 011_crm/
    │   ├── 011001_contact/
    │   │   ├── 011001_tb_contact.sql
    │   │   ├── 011001_tv_contact.sql
    │   │   └── 011001_fn_contact_*.sql
    │   └── 011002_company/
    └── 013_catalog/
        └── 013001_product/
```

**Benefits**:
- Organized by domain/subdomain/entity
- Registry-based hexadecimal codes
- Clear migration ordering
- Team collaboration friendly

### Flat Format (--dev)

**When to use**: Development, small projects, Confiture integration

**Structure**:
```
db/schema/
├── 00_foundation/
├── 10_tables/
│   ├── contact.sql
│   └── company.sql
├── 20_helpers/
│   ├── contact_helpers.sql
│   └── company_helpers.sql
└── 30_functions/
    ├── create_contact.sql
    ├── update_contact.sql
    └── create_company.sql
```

**Benefits**:
- Simple directory structure
- Fast iteration during development
- Confiture-compatible
- Easy to understand

## Command Reference

### specql generate

Generate PostgreSQL schema from SpecQL YAML files.

```bash
specql generate [OPTIONS] ENTITY_FILES...

# Examples
specql generate entities/**/*.yaml
specql generate entities/contact.yaml entities/company.yaml
specql generate entities/catalog/*.yaml --framework django
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--framework` | `fraiseql` | Target framework (fraiseql, django, rails, prisma) |
| `--output` | `migrations/` | Output directory |
| `--use-registry` | `True` | Use hexadecimal registry for table codes |
| `--format` | `hierarchical` | Output format (hierarchical, confiture) |
| `--dev` | `False` | Development mode (flat structure) |
| `--no-tv` | `False` | Skip table view generation |
| `--foundation-only` | `False` | Generate only app foundation |
| `--verbose` | `False` | Show detailed progress |
| `--dry-run` | `False` | Show what would be generated |

#### Framework-Specific Options

| Framework | Default Behavior | Override Options |
|-----------|------------------|------------------|
| **FraiseQL** | tv_*, Trinity, audit, helpers | `--no-tv` |
| **Django** | models, admin, migrations | `--include-tv` |
| **Rails** | models, migrations | `--include-tv` |
| **Prisma** | schema, client | `--include-tv` |

### specql list-frameworks

List all available frameworks with descriptions.

```bash
specql list-frameworks
```

### specql universal

Generate code for multiple frameworks simultaneously.

```bash
specql universal [OPTIONS] ENTITY_FILES...

# Examples
specql universal entities/**/*.yaml --backends postgresql,django
specql universal entities/contact.yaml --backends postgresql
```

## Common Usage Patterns

### Production Deployment (FraiseQL)

```bash
# Generate for production
specql generate entities/**/*.yaml

# Review generated structure
tree migrations/

# Apply foundation
psql -f migrations/000_app_foundation.sql

# Apply entity migrations in order
find migrations/01_write_side -name "*.sql" | sort | xargs -I {} psql -f {}
```

### Development Workflow

```bash
# Quick development iteration
specql generate entities/**/*.yaml --dev

# Apply to development database
psql -f db/schema/00_foundation/000_app_foundation.sql
for file in db/schema/10_tables/*.sql; do psql -f "$file"; done
for file in db/schema/30_functions/*.sql; do psql -f "$file"; done
```

### Multi-Framework Development

```bash
# Generate for both PostgreSQL and Django
specql universal entities/**/*.yaml --backends postgresql,django

# PostgreSQL output in: generated/postgresql/
# Django output in: generated/django/
```

### Large Project Organization

```bash
# Generate by domain
specql generate entities/crm/*.yaml --output migrations/crm
specql generate entities/catalog/*.yaml --output migrations/catalog

# Or use glob patterns
specql generate entities/crm/**/*.yaml entities/shared/**/*.yaml
```

## Generated Artifacts

### For Each Entity

SpecQL generates comprehensive SQL artifacts:

1. **Table Definition** (`tb_*`)
   - Trinity pattern: `id`, `pk_*`, `identifier`
   - Audit fields: `created_at`, `updated_at`, `deleted_at`
   - Foreign key constraints
   - Indexes and performance optimizations

2. **Table View** (`tv_*`) - FraiseQL only
   - GraphQL-friendly query interface
   - Automatic JOIN resolution
   - FraiseQL annotations for GraphQL schema

3. **Helper Functions**
   - `get_by_id(entity_id)`
   - `get_by_identifier(identifier)`
   - `exists_by_id(entity_id)`

4. **CRUD Functions**
   - `create_entity(data)`
   - `update_entity(entity_id, data)`
   - `delete_entity(entity_id)`

5. **Business Actions**
   - Custom functions from YAML actions
   - Impact tracking for GraphQL cache updates
   - Audit logging

### Foundation Artifacts

1. **App Schema** (`app.*`)
   - Mutation result types
   - Audit logging infrastructure
   - Cascade helper functions

2. **Extensions**
   - PostgreSQL extensions (uuid-ossp, etc.)
   - Custom types and domains

## Framework Comparison

| Feature | FraiseQL | Django | Rails | Prisma |
|---------|----------|--------|-------|--------|
| **Table Views** | ✅ Default | ❌ N/A | ❌ N/A | ❌ N/A |
| **Trinity Pattern** | ✅ Default | ❌ Single PK | ❌ Single PK | ❌ Single PK |
| **Audit Fields** | ✅ Default | ✅ Auto | ✅ Timestamps | ✅ Timestamps |
| **GraphQL Ready** | ✅ Full support | ❌ ORM | ❌ ORM | ❌ ORM |
| **Output Structure** | Hierarchical | Flat | Flat | Flat |
| **Registry Codes** | ✅ Hex codes | ❌ Sequential | ❌ Sequential | ❌ Sequential |

## Troubleshooting

### Common Issues

**"Subdomain XX not found in domain Y"**
- Registry issue with table codes
- Check entity organization in YAML
- Use `--dev` for development mode

**"Framework not supported"**
- Check available frameworks: `specql list-frameworks`
- Verify spelling: `fraiseql`, `django`, `rails`, `prisma`

**"No entities found"**
- Check file paths: `entities/**/*.yaml`
- Verify YAML syntax
- Ensure files have `.yaml` extension

### Performance Tips

**Large Projects (50+ entities)**:
- Use hierarchical output for organization
- Generate by domain: `specql generate entities/crm/*.yaml`
- Use `--verbose` for progress tracking

**Development Iteration**:
- Use `--dev` for fast flat structure
- Skip table views: `--no-tv` for faster generation
- Use specific entities: `specql generate entities/contact.yaml`

### Migration from 0.x

**Old behavior** (implicit defaults):
```bash
# Old way (confiture flat structure)
specql generate entities/**/*.yaml --use-registry=false
```

**New behavior** (explicit production defaults):
```bash
# New way (hierarchical production structure)
specql generate entities/**/*.yaml

# Keep old behavior
specql generate entities/**/*.yaml --dev
```

## Advanced Usage

### Custom Output Directories

```bash
# Custom migration directory
specql generate entities/**/*.yaml --output db/migrations/v2/

# Separate by environment
specql generate entities/**/*.yaml --output migrations/production/
specql generate entities/**/*.yaml --output migrations/staging/ --dev
```

### Selective Generation

```bash
# Only foundation
specql generate --foundation-only

# Specific entities
specql generate entities/user.yaml entities/post.yaml

# Exclude patterns
specql generate entities/**/*.yaml --exclude entities/test/**
```

### Integration with Build Tools

**Makefile**:
```makefile
.PHONY: schema
schema:
    specql generate entities/**/*.yaml

.PHONY: schema-dev
schema-dev:
    specql generate entities/**/*.yaml --dev

.PHONY: test-schema
test-schema:
    specql generate entities/**/*.yaml --output test/schema/
```

**Package.json**:
```json
{
  "scripts": {
    "schema": "specql generate entities/**/*.yaml",
    "schema:dev": "specql generate entities/**/*.yaml --dev",
    "schema:watch": "find entities -name '*.yaml' | entr specql generate entities/**/*.yaml --dev"
  }
}
```

## Best Practices

### Project Structure

```
project/
├── entities/
│   ├── crm/
│   │   ├── contact.yaml
│   │   └── company.yaml
│   ├── catalog/
│   │   ├── product.yaml
│   │   └── category.yaml
│   └── shared/
│       └── user.yaml
├── migrations/          # Generated (production)
├── db/
│   └── schema/          # Generated (development)
└── scripts/
    └── migrate.sh
```

### Development Workflow

1. **Start development** with `--dev` for fast iteration
2. **Generate production schema** with default settings
3. **Review generated files** before applying to database
4. **Use version control** for migration files
5. **Test migrations** on staging before production

### Framework Selection

- **FraiseQL**: Full-stack GraphQL applications
- **Django**: Python web applications with Django ORM
- **Rails**: Ruby web applications with ActiveRecord
- **Prisma**: TypeScript/Node.js applications with Prisma

Choose based on your application's technology stack and requirements.</content>
</xai:function_call">Write