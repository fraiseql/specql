# SpecQL Quick Reference

## Entity Structure

```yaml
entity: Contact                    # PascalCase, unique
schema: crm                        # snake_case, registered
description: "Customer contacts"   # Optional

fields:                            # Required
  email: text                      # Required field
  first_name: text
  last_name: text
  company: ref(Company)            # Foreign key
  status: enum(lead, qualified, customer)
  notes: text?                     # Nullable field
  metadata: json                   # JSON data

organization:                      # Optional, for migrations
  table_code: "012311"             # 6-char hex, unique
  domain: "CRM"
  subdomain: "Customer"

actions:                           # Optional
  - name: qualify_lead
    description: "Qualify a lead"
    impacts:
      write: [Contact]
      read: [Company]
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

## Field Types

### Scalar Types
| Type | SQL | Use Case | Example |
|------|-----|----------|---------|
| `text` | TEXT | Free-form text | `name: text` |
| `integer` | INTEGER | Whole numbers | `quantity: integer` |
| `decimal` | NUMERIC | Money, precise | `price: decimal` |
| `boolean` | BOOLEAN | True/false | `active: boolean` |
| `timestamp` | TIMESTAMP TZ | Date-time | `created_at: timestamp` |
| `date` | DATE | Date only | `birthday: date` |
| `json` | JSONB | Structured data | `metadata: json` |

### Rich Types
| Type | SQL | Structure | Example |
|------|-----|-----------|---------|
| `email` | app.email | `{address, display_name}` | `contact_email: email` |
| `phone` | app.phone | `{country_code, number, extension}` | `mobile: phone` |
| `money` | app.money | `{amount, currency}` | `total: money` |
| `dimensions` | app.dimensions | `{length, width, height, unit}` | `size: dimensions` |
| `contact_info` | app.contact_info | `{email, phone, address}` | `primary_contact: contact_info` |

### Relational Types
| Type | SQL | Use Case | Example |
|------|-----|----------|---------|
| `ref(Entity)` | INTEGER FK | Foreign key | `company: ref(Company)` |
| `enum(v1, v2, ...)` | TEXT CHECK | Fixed values | `status: enum(active, inactive)` |
| `list(Type)` | Type[] | Multiple values | `tags: list(text)` |

### Modifiers
| Modifier | Meaning | Example |
|----------|---------|---------|
| `?` | Nullable | `middle_name: text?` |
| None | Required | `email: text` |

## Actions

### Step Types
| Step | Purpose | Example |
|------|---------|---------|
| `validate` | Check preconditions | `validate: status = 'draft'` |
| `insert` | Create record | `insert: AuditLog SET action = 'created'` |
| `update` | Modify record | `update: Contact SET status = 'qualified'` |
| `soft_delete` | Mark deleted | `soft_delete: Contact` |
| `call` | Invoke action | `call: crm.send_email(contact_id: :id)` |
| `notify` | Send event | `notify: contact_created WITH {id: :id}` |
| `if` | Conditional | `if: amount > 1000 then: [...]` |
| `foreach` | Loop | `foreach: item IN order_lines do: [...]` |

### Variables
| Variable | Meaning | Example |
|----------|---------|---------|
| `:param` | Input parameter | `:contact_id` |
| `:item.field` | Loop item field | `:line.product_id` |
| `CURRENT_USER` | Current user UUID | `created_by = CURRENT_USER` |

## CLI Commands

### Generate
```bash
# Basic generation
specql generate entities/**/*.yaml

# With options
specql generate entities/**/*.yaml \
  --with-impacts \
  --output-frontend=src/generated \
  --output-format hierarchical
```

### Validate
```bash
# Check syntax
specql validate entities/**/*.yaml

# With impact checking
specql validate entities/**/*.yaml --check-impacts
```

### Check Codes
```bash
# Verify table code uniqueness
specql check-codes entities/**/*.yaml
```

## Common Patterns

### Basic Entity
```yaml
entity: Contact
schema: crm
fields:
  email: text
  name: text
```

### With Relationships
```yaml
entity: Order
schema: commerce
fields:
  customer: ref(Customer)
  status: enum(draft, confirmed, shipped)
  total: money
```

### With Actions
```yaml
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

### Multi-Tenant
```yaml
# registry/domain_registry.yaml
domains:
  crm:
    type: multi_tenant  # Adds tenant_id automatically
```

### Hierarchical
```yaml
entity: Category
schema: catalog
hierarchical: true
fields:
  name: text
  parent: ref(Category)?
```

## Auto-Generated Features

### Trinity Pattern (Always Added)
- `id` - INTEGER PRIMARY KEY
- `pk_<entity>` - UUID unique identifier
- `identifier` - TEXT human-readable slug

### Audit Fields (Always Added)
- `created_at`, `updated_at` - TIMESTAMP WITH TIME ZONE
- `created_by`, `updated_by` - UUID user references
- `deleted_at`, `deleted_by` - Soft delete fields

### Indexes (Auto-Generated)
- Foreign keys: `idx_tb_<entity>_<field>`
- Enums: `idx_tb_<entity>_<field>`
- JSON: GIN indexes
- Tenant ID: `idx_tb_<entity>_tenant_id`

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Tables | `tb_<entity>` | `tb_contact` |
| Views | `tv_<entity>` | `tv_contact` |
| Foreign Keys | `fk_tb_<entity>_<field>` | `fk_tb_contact_company` |
| Indexes | `idx_tb_<entity>_<field>` | `idx_tb_contact_email` |
| Functions | `<schema>.<action>` | `crm.qualify_lead` |
| Wrappers | `app.<action>` | `app.qualify_lead` |

## Migration Mapping

| SQL Type | SpecQL Type | Notes |
|----------|-------------|-------|
| `TEXT`, `VARCHAR` | `text` | |
| `INTEGER` | `integer` | |
| `NUMERIC` | `decimal` | |
| `BOOLEAN` | `boolean` | |
| `TIMESTAMP` | `timestamp` | |
| `JSONB` | `json` | |
| `TEXT[]` | `list(text)` | |
| `INTEGER REFERENCES` | `ref(Entity)` | Drop `_id` suffix |
| `TEXT CHECK (...)` | `enum(...)` | Extract values |
| `NULL` | `field?` | Add `?` suffix |

## Quick Commands

```bash
# Validate all entities
specql validate entities/**/*.yaml

# Generate schema
specql generate entities/**/*.yaml

# Check table codes
specql check-codes entities/**/*.yaml

# Compare with existing
specql diff entities/contact.yaml --compare db/schema/10_tables/contact.sql

# Generate docs
specql docs entities/**/*.yaml
```

## Common Errors

| Error | Quick Fix |
|-------|-----------|
| `Unknown field type 'string'` | Use `text` instead |
| `Missing 'entity' key` | Use `entity:` not `import:` |
| `Table code already assigned` | `specql check-codes` to find duplicates |
| `Referenced entity not found` | Create referenced entity first |
| `Circular reference` | Make one reference nullable with `?` |

## Resources

- **YAML Reference**: `docs/reference/yaml-reference.md`
- **CLI Reference**: `docs/reference/cli-reference.md`
- **Migration Guide**: `docs/guides/migration-guide.md`
- **Troubleshooting**: `docs/guides/troubleshooting.md`
- **Examples**: `examples/entities/`