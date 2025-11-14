# Team A: Scalar Rich Types

## Overview

Team A has implemented parsing for 23 scalar rich types that provide built-in validation and semantic meaning.

## Supported Scalar Types

### String-Based Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `email` | TEXT | Email | RFC 5322 regex | user@example.com |
| `phoneNumber` | TEXT | PhoneNumber | E.164 format | +14155551234 |
| `url` | TEXT | Url | URL regex | https://example.com |
| `slug` | TEXT | Slug | lowercase-hyphen | my-article |
| `markdown` | TEXT | Markdown | None | # Heading |
| `html` | TEXT | Html | None | `<p>Text</p>` |

### Numeric Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `money` | NUMERIC(19,4) | Money | >= 0 | 1234.56 |
| `percentage` | NUMERIC(5,2) | Percentage | 0-100 | 75.5 |

### Date/Time Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `date` | DATE | Date | None | 2025-11-08 |
| `datetime` | TIMESTAMPTZ | DateTime | None | 2025-11-08T14:30:00Z |
| `time` | TIME | Time | None | 14:30:00 |
| `duration` | INTERVAL | Duration | None | 2 hours 30 minutes |

### Geographic Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `coordinates` | POINT | Coordinates | None | (37.7749, -122.4194) |
| `latitude` | NUMERIC(10,8) | Latitude | -90 to 90 | 37.7749 |
| `longitude` | NUMERIC(11,8) | Longitude | -180 to 180 | -122.4194 |

### Network Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `ipAddress` | INET | IpAddress | None | 192.168.1.1 |
| `macAddress` | MACADDR | MacAddress | None | 08:00:2b:01:02:03 |

### Media Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `image` | TEXT | Image | None | https://example.com/image.jpg |
| `file` | TEXT | File | None | https://example.com/document.pdf |
| `color` | TEXT | Color | Hex color regex | #FF5733 |

### Identifier Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `uuid` | UUID | UUID | None | 550e8400-e29b-41d4-a716-446655440000 |

### Structured Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `json` | JSONB | JSON | None | {"key": "value"} |

### Boolean Types

| Type | PostgreSQL | FraiseQL | Validation | Example |
|------|-----------|----------|-----------|---------|
| `boolean` | BOOLEAN | Boolean | None | true |

## Usage in SpecQL

```yaml
entity: Contact
fields:
  email: email!
  phone: phoneNumber
  website: url
```

## AST Output

Team A generates FieldDefinition objects with:
- `tier: FieldTier.SCALAR`
- `scalar_def: ScalarTypeDef` (full metadata)
- `postgres_type: str` (for Team B)
- `fraiseql_type: str` (for Team D)
- `validation_pattern: Optional[str]` (for Team B CHECK constraints)

## Implementation Details

### Core Files
- `src/core/scalar_types.py` - Type registry and definitions
- `src/core/ast_models.py` - Extended AST with tier support
- `src/core/specql_parser.py` - Parser with scalar type recognition

### Test Coverage
- Unit tests for all 23 scalar types
- Parser integration tests
- End-to-end validation tests

## Phase 2: Composite Types ✅ COMPLETED

Team A has implemented 12 composite types that map to JSONB in PostgreSQL:

### Supported Composite Types

| Type | Description | Fields | Example |
|------|-------------|--------|---------|
| `SimpleAddress` | Basic address | street, city, state, zipCode, country | {"street": "123 Main St", "city": "Anytown"} |
| `MoneyAmount` | Currency + amount | amount, currency | {"amount": 99.99, "currency": "USD"} |
| `PersonName` | Full name | firstName, lastName, middleName, title, suffix | {"firstName": "John", "lastName": "Doe"} |
| `ContactInfo` | Contact details | email, phone, website | {"email": "john@example.com"} |
| `Coordinates` | Lat/lng pair | latitude, longitude | {"latitude": 37.7749, "longitude": -122.4194} |
| `TimeRange` | Start/end times | startTime, endTime | {"startTime": "09:00", "endTime": "17:00"} |
| `DateRange` | Start/end dates | startDate, endDate | {"startDate": "2025-01-01", "endDate": "2025-12-31"} |
| `PhoneNumber` | Phone with type | countryCode, number | {"countryCode": "1", "number": "4155551234"} |
| `EmailAddress` | Email with type | address, type | {"address": "john@example.com", "type": "work"} |
| `URL` | URL with type | protocol, host, path, query, fragment | {"protocol": "https", "host": "example.com"} |
| `Color` | RGB color | red, green, blue | {"red": 255, "green": 0, "blue": 0} |
| `Dimensions` | Size measurements | width, height, depth, unit | {"width": 10, "height": 5, "unit": "inches"} |
| `BusinessHours` | Weekly schedule | monday-sunday (TimeRange) | {"monday": {"startTime": "09:00", "endTime": "17:00"}} |

### Usage in SpecQL

```yaml
entity: Company
fields:
  headquarters: SimpleAddress!
  contact_info: ContactInfo
  business_hours: BusinessHours
```

### AST Output

Composite fields generate FieldDefinition objects with:
- `tier: FieldTier.COMPOSITE`
- `composite_def: CompositeTypeDef` (schema + examples)
- `postgres_type: "JSONB"`
- `fraiseql_type: str` (GraphQL object type name)
- `fraiseql_schema: dict` (JSON schema for validation)

## Phase 3: Entity References ✅ COMPLETED

Team A has implemented entity reference parsing with PostgreSQL UUID foreign keys:

### Reference Syntax

```yaml
entity: Order
fields:
  customer: ref(Customer)!          # Single entity reference
  supplier: ref(Supplier)           # Nullable reference
  backup_contacts: ref(Person)      # Array of references (future)
```

### Polymorphic References

```yaml
entity: Activity
fields:
  actor: ref(User|Admin|System)!    # Union of entity types
  subject: ref(Post|Comment|User)   # Nullable polymorphic
```

### AST Output

Reference fields generate FieldDefinition objects with:
- `tier: FieldTier.REFERENCE`
- `reference_entity: str` (target entity name)
- `postgres_type: "UUID"` (foreign key)
- `fraiseql_type: "ID"` (GraphQL ID type)
- `fraiseql_relation: "many-to-one"` (relationship type)

## Complete Type System

The implementation now supports all three tiers:

### Tier 1: Basic Types
- `text`, `integer`, `bigint`, `float`, `boolean`
- Maps to PostgreSQL primitives
- No additional validation

### Tier 1: Scalar Rich Types
- 22 specialized types with validation (email, money, etc.)
- Built-in regex patterns and constraints
- Maps to PostgreSQL TEXT/NUMERIC with CHECK constraints

### Tier 2: Composite Types
- 12 structured JSONB types
- Nested field validation schemas
- Maps to PostgreSQL JSONB

### Tier 3: Entity References
- UUID foreign keys to other entities
- Polymorphic reference support
- Maps to PostgreSQL UUID with FK constraints

## Integration Ready

The complete type system provides all metadata needed for:
- **Team B**: PostgreSQL DDL generation with proper types and constraints
- **Team D**: GraphQL schema generation with correct types and relations
- **Future**: Full validation and type safety across the stack