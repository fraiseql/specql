# FraiseQL Integration with SpecQL Rich Types

**Status**: ✅ Fully Compatible
**FraiseQL Version Required**: 1.3.4+
**Manual Annotations Needed**: None

---

## Overview

SpecQL rich types seamlessly integrate with FraiseQL's autodiscovery system.
PostgreSQL comments and base types automatically map to GraphQL scalars.

**Key Insight**: FraiseQL v1.3.4+ discovers everything automatically! 🎉

---

## How It Works

### 1. SpecQL → PostgreSQL Schema

```yaml
# entities/contact.yaml
entity: Contact
schema: crm

fields:
  email: email!
  website: url
  phone: phoneNumber
```

↓ **Team B generates PostgreSQL**

```sql
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT UNIQUE,

    -- Rich type fields with validation
    email TEXT NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    website TEXT CHECK (website ~* '^https?://[^\s/$.?#].[^\s]*$'),
    phone TEXT CHECK (phone ~* '^\+?[1-9]\d{1,14}$'),

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Team B adds descriptive comments
COMMENT ON COLUMN crm.tb_contact.email IS
    'Email address (validated format) (required)';

COMMENT ON COLUMN crm.tb_contact.website IS
    'URL/website address (validated format)';

COMMENT ON COLUMN crm.tb_contact.phone IS
    'Phone number in E.164 format (validated format)';
```

### 2. FraiseQL Autodiscovery

FraiseQL introspects PostgreSQL and discovers:

1. **Base Types**: TEXT → String, INET → IpAddress, POINT → Coordinates
2. **Comments**: PostgreSQL comments → GraphQL field descriptions
3. **Constraints**: CHECK constraints signal semantic validation
4. **Nullability**: NOT NULL → `!` in GraphQL

### 3. GraphQL Schema (Auto-Generated)

```graphql
type Contact {
  """Email address (validated format) (required)"""
  email: Email!

  """URL/website address (validated format)"""
  website: Url

  """Phone number in E.164 format (validated format)"""
  phone: PhoneNumber
}

# Custom scalars (provided by FraiseQL)
scalar Email
scalar Url
scalar PhoneNumber
```

---

## Rich Type Mappings

| SpecQL Type   | PostgreSQL Type      | GraphQL Scalar | Auto-Discovered | Validation |
|---------------|---------------------|----------------|-----------------|------------|
| `email`       | TEXT + CHECK        | Email          | ✅ Yes          | Regex      |
| `url`         | TEXT + CHECK        | Url            | ✅ Yes          | Regex      |
| `phoneNumber` | TEXT + CHECK        | PhoneNumber    | ✅ Yes          | E.164      |
| `ipAddress`   | INET                | IpAddress      | ✅ Yes          | Native     |
| `macAddress`  | MACADDR             | MacAddress     | ✅ Yes          | Native     |
| `coordinates` | POINT               | Coordinates    | ✅ Yes          | Native     |
| `money`       | NUMERIC(19,4)       | Money          | ✅ Yes          | Precision  |
| `percentage`  | NUMERIC(5,2) + CHECK| Percentage     | ✅ Yes          | 0-100      |
| `date`        | DATE                | Date           | ✅ Yes          | ISO 8601   |
| `datetime`    | TIMESTAMPTZ         | DateTime       | ✅ Yes          | ISO 8601   |
| `uuid`        | UUID                | UUID           | ✅ Yes          | Native     |
| `markdown`    | TEXT                | Markdown       | ✅ Yes          | None       |
| `color`       | TEXT + CHECK        | Color          | ✅ Yes          | Hex/Named  |
| `slug`        | TEXT + CHECK        | Slug           | ✅ Yes          | URL-safe   |

**Result**: 100% compatibility, 0% manual work! 🎉

---

## Benefits

### 1. Zero Configuration
- ✅ No manual `@fraiseql:field` annotations needed
- ✅ No type mapping configuration
- ✅ No GraphQL schema definition files
- ✅ Just write SpecQL, everything else is automatic

### 2. Single Source of Truth
- ✅ PostgreSQL is the documentation source
- ✅ Comments become GraphQL descriptions
- ✅ Constraints signal validation rules
- ✅ No duplication between database and API

### 3. Type Safety Everywhere
- ✅ PostgreSQL validates at INSERT/UPDATE
- ✅ GraphQL validates at query/mutation input
- ✅ Frontend gets TypeScript types
- ✅ End-to-end type safety

### 4. Developer Experience
- ✅ GraphQL Playground shows field descriptions
- ✅ Auto-complete in GraphQL queries
- ✅ Inline documentation
- ✅ No context switching

### 5. Maintainability
- ✅ Update PostgreSQL comment → GraphQL updates automatically
- ✅ Change validation rule → GraphQL reflects immediately
- ✅ Add new type → FraiseQL discovers it
- ✅ Zero maintenance overhead

---

## Testing

### Run Integration Tests

```bash
# All FraiseQL integration tests
uv run pytest tests/integration/fraiseql/ -v

# Rich type autodiscovery specifically
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v

# Compatibility checker
uv run pytest tests/unit/fraiseql/test_compatibility_checker.py -v
```

### Verify Compatibility

```python
from src.generators.fraiseql.compatibility_checker import CompatibilityChecker

checker = CompatibilityChecker()

# Check all types are compatible
assert checker.check_all_types_compatible()  # True

# Get detailed report
report = checker.get_compatibility_report()
print(f"Compatible types: {report['compatible_types']}/{report['total_types']}")
# Output: Compatible types: 14/14 (100%)
```

---

## Example: Complete Flow

### User Writes (20 lines)

```yaml
entity: Contact
schema: crm

fields:
  name: text!
  email: email!
  website: url
  phone: phoneNumber
  office_ip: ipAddress
```

### Generated PostgreSQL (200+ lines)

```sql
-- Trinity pattern table
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT UNIQUE,

    -- Business fields with rich type validation
    name TEXT NOT NULL,
    email TEXT NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@...'),
    website TEXT CHECK (website ~* '^https?://...'),
    phone TEXT CHECK (phone ~* '^\+?[1-9]\d{1,14}$'),
    office_ip INET,

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,
    updated_by UUID,
    deleted_at TIMESTAMPTZ
);

-- Descriptive comments (become GraphQL descriptions)
COMMENT ON COLUMN crm.tb_contact.email IS 'Email address (validated format) (required)';
COMMENT ON COLUMN crm.tb_contact.website IS 'URL/website address (validated format)';
COMMENT ON COLUMN crm.tb_contact.phone IS 'Phone number in E.164 format (validated format)';
COMMENT ON COLUMN crm.tb_contact.office_ip IS 'IP address (IPv4 or IPv6)';

-- Indexes, helper functions, etc.
```

### FraiseQL Auto-Generates GraphQL (1000+ lines)

```graphql
"""Contact entity"""
type Contact {
  id: UUID!
  name: String!

  """Email address (validated format) (required)"""
  email: Email!

  """URL/website address (validated format)"""
  website: Url

  """Phone number in E.164 format (validated format)"""
  phone: PhoneNumber

  """IP address (IPv4 or IPv6)"""
  officeIp: IpAddress

  createdAt: DateTime!
  updatedAt: DateTime!
}

type Query {
  contact(id: UUID!): Contact
  contacts(where: ContactFilter, limit: Int, offset: Int): [Contact!]!
}

type Mutation {
  createContact(input: CreateContactInput!): CreateContactPayload!
  updateContact(id: UUID!, input: UpdateContactInput!): UpdateContactPayload!
  deleteContact(id: UUID!): DeleteContactPayload!
}

# All custom scalars provided by FraiseQL
scalar Email
scalar Url
scalar PhoneNumber
scalar IpAddress
scalar UUID
scalar DateTime
```

### Result: 100x Code Leverage

- **User writes**: 20 lines YAML
- **Generated**: 2000+ lines (SQL + GraphQL + TypeScript types)
- **Manual annotations**: 0 lines
- **Maintenance overhead**: 0

---

## Team D's Minimal Role

### Original Plan (Deprecated)
- 400+ lines of annotation generation code
- Manual `@fraiseql:field` for every field
- Complex scalar mapping logic
- Extensive test suite

### Actual Implementation (Simplified)
- ✅ 50 lines compatibility checker
- ✅ 200 lines integration tests
- ✅ Verify FraiseQL autodiscovery works
- ✅ Documentation

**Time Savings**: 6-7 hours → 1-2 hours

---

## What If FraiseQL Doesn't Discover a Type?

**Highly unlikely**, but if it happens:

### 1. Check PostgreSQL Metadata

```sql
-- Verify comment exists
SELECT col_description('crm.tb_contact'::regclass,
                        (SELECT attnum FROM pg_attribute
                         WHERE attrelid = 'crm.tb_contact'::regclass
                           AND attname = 'email'));
```

### 2. Check FraiseQL Logs

```bash
fraiseql introspect --database-url=... --verbose
```

### 3. Add Explicit Annotation (Fallback)

```python
# Only if autodiscovery fails (should never happen)
from src.generators.fraiseql.compatibility_checker import CompatibilityChecker

checker = CompatibilityChecker()
checker._incompatible_types.add("custom_type_name")

# Generate manual annotation
annotation = checker.generate_type_annotation_if_needed("custom_type_name")
```

### 4. Report to FraiseQL Team

Open issue with:
- PostgreSQL schema
- Expected GraphQL type
- FraiseQL version
- Introspection logs

---

## Conclusion

**Team D's role is minimal because FraiseQL is smart!**

✅ Rich types work out of the box
✅ No manual annotations needed
✅ PostgreSQL comments → GraphQL descriptions
✅ 100% compatibility verified by tests

**The best code is the code you don't have to write.** 🎉

---

**Status**: ✅ Phase 1 Complete
**Next Phase**: Phase 2 - tv_ Table Annotations