# Trinity Pattern: Triple Identity System

> **Status**: 🚧 Documentation in Progress
>
> This page provides a brief overview. Comprehensive documentation coming soon!

## Overview

The **Trinity Pattern** is SpecQL's core convention for entity identification. Every entity table has three identity columns, each optimized for different use cases.

## The Three Identities

```sql
CREATE TABLE crm.tb_contact (
    -- Trinity Pattern: 3 ways to reference
    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT UNIQUE NOT NULL,

    -- Business fields...
);
```

### 1. `pk_{entity}` - Database Primary Key (INTEGER)

**Use for**: Internal database operations, foreign keys, joins

**Why**: INTEGER primary keys provide:
- Fastest join performance (3-5x faster than UUID)
- Smallest index size
- Optimal query planner efficiency
- Sequential allocation

**Example**:
```sql
-- Foreign key references use pk_*
CREATE TABLE crm.tb_order (
    pk_order INTEGER PRIMARY KEY,
    fk_contact INTEGER NOT NULL,
    FOREIGN KEY (fk_contact) REFERENCES crm.tb_contact(pk_contact)
);

-- Fast joins
SELECT * FROM crm.tb_order o
JOIN crm.tb_contact c ON o.fk_contact = c.pk_contact;
```

### 2. `id` - External UUID

**Use for**: External APIs, GraphQL, REST endpoints, client-server communication

**Why**: UUID provides:
- Security (non-sequential, hard to guess)
- Portability (globally unique, safe for distributed systems)
- API stability (internal IDs never exposed)
- Prevents enumeration attacks

**Example**:
```graphql
# GraphQL uses UUIDs
query {
  contact(id: "550e8400-e29b-41d4-a716-446655440000") {
    email
    firstName
  }
}
```

```typescript
// TypeScript uses UUIDs
const contact = await getContact("550e8400-e29b-41d4-a716-446655440000");
```

### 3. `identifier` - Human-Readable Text

**Use for**: URLs, user-facing IDs, debugging, logging, customer support

**Why**: TEXT identifiers provide:
- Human-readable references
- SEO-friendly URLs
- Easier debugging and logging
- Customer-friendly support references
- Business context (e.g., `CONTACT-ACME-2024-001`)

**Example**:
```
# URL
https://app.example.com/contacts/CONTACT-ACME-12345

# Customer support
"Please reference ticket CONTACT-ACME-12345 in your reply"

# Logs
[INFO] Processing contact CONTACT-ACME-12345
```

## Quick Comparison

| Identity | Type | Use Case | Example | Benefits |
|----------|------|----------|---------|----------|
| `pk_contact` | INTEGER | DB joins, FKs | `42` | Performance, efficiency |
| `id` | UUID | API, GraphQL | `550e8400-...` | Security, portability |
| `identifier` | TEXT | URLs, UX | `CONTACT-ACME-001` | Readability, UX |

## Conversion Helpers

SpecQL auto-generates helper functions to convert between identities:

```sql
-- UUID → INTEGER (for internal queries)
SELECT crm.contact_pk('550e8400-e29b-41d4-a716-446655440000');
-- Returns: 42

-- INTEGER → UUID (for API responses)
SELECT crm.contact_id(42);
-- Returns: '550e8400-e29b-41d4-a716-446655440000'

-- TEXT → INTEGER (for URL handling)
SELECT crm.contact_pk_by_identifier('CONTACT-ACME-001');
-- Returns: 42
```

## Benefits of Trinity Pattern

### 1. Performance + Security
- Use INTEGER joins internally (fast)
- Expose UUIDs externally (secure)
- Best of both worlds

### 2. Developer Experience
- Readable identifiers in logs and URLs
- UUIDs for API stability
- Clear separation of concerns

### 3. Future-Proof
- Can migrate between systems using UUIDs
- Can optimize queries using INTEGER keys
- Can enhance UX with readable identifiers

## Coming Soon

Full documentation will cover:
- [ ] Identifier generation strategies
- [ ] Custom identifier formats
- [ ] Multi-tenant identifier patterns
- [ ] Migration from single-identity systems
- [ ] Performance benchmarks
- [ ] Advanced helper functions
- [ ] Integration with ORMs

## Related Documentation

- [Business YAML](business-yaml.md) - How trinity pattern is defined in YAML
- [Actions](actions.md) - How to reference entities in actions
- [Performance Tuning](../07_advanced/performance-tuning.md) - Performance implications

## Real-World Example

```yaml
entity: Contact
schema: crm
fields:
  email: email!
  company: ref(Company)!
```

Generates:

```sql
CREATE TABLE crm.tb_contact (
    -- Trinity Pattern (auto-generated)
    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT UNIQUE NOT NULL,

    -- Business fields
    email TEXT NOT NULL,
    fk_company INTEGER NOT NULL,  -- Uses INTEGER FK

    -- Foreign key
    CONSTRAINT fk_contact_company
        FOREIGN KEY (fk_company)
        REFERENCES crm.tb_company(pk_company)  -- References INTEGER PK
);

-- Helper functions (auto-generated)
CREATE FUNCTION crm.contact_pk(p_id UUID) RETURNS INTEGER AS $$
    SELECT pk_contact FROM crm.tb_contact WHERE id = p_id;
$$ LANGUAGE SQL STABLE;

CREATE FUNCTION crm.contact_id(p_pk INTEGER) RETURNS UUID AS $$
    SELECT id FROM crm.tb_contact WHERE pk_contact = p_pk;
$$ LANGUAGE SQL STABLE;

CREATE FUNCTION crm.contact_identifier(p_pk INTEGER) RETURNS TEXT AS $$
    SELECT identifier FROM crm.tb_contact WHERE pk_contact = p_pk;
$$ LANGUAGE SQL STABLE;
```

## Questions?

If you need more details:
- Check [Business YAML](business-yaml.md) for YAML definition
- Review [First Entity](../01_getting-started/first-entity.md) for examples
- See [Performance Tuning](../07_advanced/performance-tuning.md) for optimization
- Open an issue on GitHub

---

*Last Updated*: 2025-11-20
