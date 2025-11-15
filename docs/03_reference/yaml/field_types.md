# Field Types Reference

**Complete guide to SpecQL field types** - Every available type with examples and constraints

This reference documents all field types supported by SpecQL, their PostgreSQL mappings, and usage examples.

## 📊 Basic Types

### Text Fields

#### `text`
Variable-length string with unlimited length.

```yaml
fields:
  name: text
  description: text
  notes: text
```

**PostgreSQL**: `TEXT`
**Default**: `NULL`
**Constraints**: None

#### `varchar(n)`
Fixed maximum length string.

```yaml
fields:
  code: varchar(10)      # Max 10 characters
  short_name: varchar(50) # Max 50 characters
```

**PostgreSQL**: `VARCHAR(n)`
**Default**: `NULL`
**Constraints**: Length <= n

### Numeric Types

#### `integer`
Whole numbers, positive or negative.

```yaml
fields:
  count: integer
  quantity: integer
  user_id: integer
```

**PostgreSQL**: `INTEGER`
**Range**: -2,147,483,648 to +2,147,483,647
**Default**: `NULL`

#### `bigint`
Large whole numbers.

```yaml
fields:
  large_count: bigint
  timestamp_ms: bigint  # Milliseconds since epoch
```

**PostgreSQL**: `BIGINT`
**Range**: -9,223,372,036,854,775,808 to +9,223,372,036,854,775,807
**Default**: `NULL`

#### `smallint`
Small whole numbers.

```yaml
fields:
  priority: smallint     # 1-5 scale
  rating: smallint       # 1-10 scale
```

**PostgreSQL**: `SMALLINT`
**Range**: -32,768 to +32,767
**Default**: `NULL`

#### `decimal`
Fixed precision decimal numbers.

```yaml
fields:
  price: decimal         # DECIMAL(10,2)
  weight: decimal(8,3)   # DECIMAL(8,3) - 8 total digits, 3 after decimal
  percentage: decimal(5,2) # DECIMAL(5,2) - 0.00 to 999.99
```

**PostgreSQL**: `DECIMAL(precision,scale)`
**Default**: `DECIMAL(10,2)`
**Constraints**: precision 1-1000, scale 0-precision

### Boolean Type

#### `boolean`
True/false values.

```yaml
fields:
  is_active: boolean
  has_discount: boolean
  email_verified: boolean
```

**PostgreSQL**: `BOOLEAN`
**Values**: `true`, `false`, `NULL`
**Default**: `NULL`

## 📅 Date and Time Types

#### `date`
Date without time.

```yaml
fields:
  birth_date: date
  hire_date: date
  due_date: date
```

**PostgreSQL**: `DATE`
**Format**: `YYYY-MM-DD`
**Default**: `NULL`

#### `time`
Time without date.

```yaml
fields:
  start_time: time
  end_time: time
  meeting_time: time
```

**PostgreSQL**: `TIME`
**Format**: `HH:MM:SS`
**Default**: `NULL`

#### `timestamp`
Date and time with timezone.

```yaml
fields:
  created_at: timestamp
  updated_at: timestamp
  published_at: timestamp
```

**PostgreSQL**: `TIMESTAMPTZ`
**Format**: `YYYY-MM-DD HH:MM:SS+TZ`
**Default**: `NULL`

## 🔑 Identifier Types

#### `uuid`
Universally unique identifier.

```yaml
fields:
  id: uuid              # Primary key
  external_id: uuid     # External references
  session_id: uuid      # Session tracking
```

**PostgreSQL**: `UUID`
**Format**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
**Default**: `NULL` (but auto-generated for primary keys)

#### `serial`
Auto-incrementing integer.

```yaml
fields:
  legacy_id: serial     # Auto-incrementing ID
  sequence: serial      # Sequential numbering
```

**PostgreSQL**: `SERIAL` (INTEGER + SEQUENCE)
**Range**: 1 to 2,147,483,647
**Default**: Auto-incremented

#### `bigserial`
Auto-incrementing large integer.

```yaml
fields:
  global_id: bigserial  # Large auto-incrementing ID
```

**PostgreSQL**: `BIGSERIAL` (BIGINT + SEQUENCE)
**Range**: 1 to 9,223,372,036,854,775,807
**Default**: Auto-incremented

## 📋 Choice Types

#### `enum(values...)`
Predefined set of values.

```yaml
fields:
  status: enum(active, inactive, suspended)
  priority: enum(low, medium, high, urgent)
  category: enum(personal, work, family, other)
  role: enum(user, moderator, admin, super_admin)
```

**PostgreSQL**: `TEXT` with CHECK constraint
**Validation**: Must be one of the specified values
**Default**: `NULL`

## 📦 Complex Types

#### `json`
JSON data storage.

```yaml
fields:
  settings: json        # User preferences
  metadata: json        # Flexible metadata
  config: json          # Configuration objects
```

**PostgreSQL**: `JSONB`
**Indexing**: Can be indexed with GIN indexes
**Default**: `NULL`

#### `jsonb`
Binary JSON data (same as json in SpecQL).

```yaml
fields:
  data: jsonb           # Same as json
```

**PostgreSQL**: `JSONB`
**Advantages**: Faster operations, better indexing than JSON
**Default**: `NULL`

## 📍 Spatial Types (with PostGIS)

#### `geometry`
Geometric shapes and points.

```yaml
fields:
  location: geometry    # Points, polygons, etc.
  area: geometry        # Geographic areas
```

**PostgreSQL**: `GEOMETRY` (requires PostGIS)
**Types**: POINT, LINESTRING, POLYGON, etc.
**Default**: `NULL`

#### `geography`
Geographic coordinates.

```yaml
fields:
  coordinates: geography # Geographic points
```

**PostgreSQL**: `GEOGRAPHY` (requires PostGIS)
**CRS**: WGS84 (SRID 4326)
**Default**: `NULL`

## 💰 Financial Types

#### `money`
Monetary values with currency support.

```yaml
fields:
  price: money          # Amount with currency
  salary: money         # Compensation
```

**PostgreSQL**: Custom type or DECIMAL
**Format**: `{"amount": 123.45, "currency": "USD"}`
**Default**: `NULL`

## 📏 Measurement Types

#### `weight`
Weight measurements.

```yaml
fields:
  package_weight: weight # Weight with units
```

**PostgreSQL**: Custom type or DECIMAL + TEXT
**Units**: kg, lbs, g, oz
**Default**: `NULL`

#### `dimensions`
Physical dimensions.

```yaml
fields:
  size: dimensions      # Length x Width x Height
```

**PostgreSQL**: Custom type or JSON
**Format**: `{"length": 10, "width": 5, "height": 2, "unit": "cm"}`
**Default**: `NULL`

#### `volume`
Volume measurements.

```yaml
fields:
  capacity: volume      # Volume with units
```

**PostgreSQL**: Custom type or DECIMAL + TEXT
**Units**: liters, gallons, ml, etc.
**Default**: `NULL`

## 📞 Contact Types

#### `email`
Email addresses with validation.

```yaml
fields:
  user_email: email
  contact_email: email
  backup_email: email
```

**PostgreSQL**: `TEXT` with CHECK constraint
**Validation**: RFC-compliant email format
**Default**: `NULL`

#### `phone`
Phone numbers with formatting.

```yaml
fields:
  mobile: phone
  office: phone
  fax: phone
```

**PostgreSQL**: `TEXT` with CHECK constraint
**Validation**: International phone number format
**Default**: `NULL`

#### `url`
Web URLs with validation.

```yaml
fields:
  website: url
  avatar_url: url
  api_endpoint: url
```

**PostgreSQL**: `TEXT` with CHECK constraint
**Validation**: HTTP/HTTPS URL format
**Default**: `NULL`

## 🏷️ Address Types

#### `address`
Complete address structure.

```yaml
fields:
  home_address: address
  billing_address: address
  shipping_address: address
```

**PostgreSQL**: `JSONB`
**Structure**:
```json
{
  "street": "123 Main St",
  "city": "Anytown",
  "state": "CA",
  "zip_code": "12345",
  "country": "USA"
}
```
**Default**: `NULL`

#### `postal_code`
Postal/ZIP codes.

```yaml
fields:
  zip_code: postal_code
  postal_code: postal_code
```

**PostgreSQL**: `TEXT` with CHECK constraint
**Validation**: Country-specific formats
**Default**: `NULL`

## 📊 Field Options

All field types support these options:

### Basic Options

```yaml
fields:
  name: text
    nullable: false          # Cannot be NULL
    unique: true            # Unique constraint
    index: true             # Create index
    default: "Unknown"      # Default value
```

### String Options

```yaml
fields:
  code: varchar(10)
    min_length: 3           # Minimum length
    max_length: 10          # Maximum length (redundant for varchar)
    pattern: "^[A-Z0-9]+$"  # Regular expression pattern
```

### Numeric Options

```yaml
fields:
  age: integer
    min: 0                  # Minimum value
    max: 150                # Maximum value
    default: 0
```

### Decimal Options

```yaml
fields:
  price: decimal
    precision: 10           # Total digits
    scale: 2               # Digits after decimal
    min: 0                 # Minimum value
    max: 99999999.99       # Maximum value
```

### Enum Options

```yaml
fields:
  status: enum(active, inactive, suspended)
    default: "active"       # Default enum value
```

### JSON Options

```yaml
fields:
  settings: json
    schema: user_settings   # JSON schema validation
```

## 🔗 Reference Types

### Single References

```yaml
fields:
  author: ref(User)         # Reference to User entity
  category: ref(Category)   # Reference to Category entity
```

**PostgreSQL**: Foreign key to referenced table's primary key
**Validation**: Referenced record must exist
**Indexing**: Automatically indexed

### List References (Many-to-Many)

```yaml
fields:
  tags: ref(Tag)[]          # Many-to-many with Tag
  projects: ref(Project)[]  # Many-to-many with Project
```

**PostgreSQL**: Junction table created automatically
**Structure**: `entity1_entity2` table with foreign keys
**Indexing**: Composite indexes on both foreign keys

## 📋 Field Validation

### Built-in Validations

SpecQL automatically adds validations based on field types:

- **email**: RFC-compliant email format
- **phone**: International phone number format
- **url**: HTTP/HTTPS URL format
- **uuid**: Valid UUID format
- **enum**: Must be one of specified values
- **varchar(n)**: Length <= n
- **decimal(p,s)**: Precision and scale constraints

### Custom Validations

Add custom validation rules:

```yaml
fields:
  password: text
    min_length: 8
    pattern: "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).+$"  # Strong password
    nullable: false

  age: integer
    min: 0
    max: 150

  score: decimal(5,2)
    min: 0.00
    max: 100.00
```

## 📊 Database Mapping Summary

| SpecQL Type | PostgreSQL Type | Notes |
|-------------|-----------------|-------|
| `text` | `TEXT` | Unlimited length |
| `varchar(n)` | `VARCHAR(n)` | Fixed max length |
| `integer` | `INTEGER` | 32-bit signed |
| `bigint` | `BIGINT` | 64-bit signed |
| `smallint` | `SMALLINT` | 16-bit signed |
| `decimal` | `DECIMAL(10,2)` | Default precision |
| `decimal(p,s)` | `DECIMAL(p,s)` | Custom precision |
| `boolean` | `BOOLEAN` | True/false/null |
| `date` | `DATE` | Date only |
| `time` | `TIME` | Time only |
| `timestamp` | `TIMESTAMPTZ` | Date/time with timezone |
| `uuid` | `UUID` | Universally unique identifier |
| `serial` | `SERIAL` | Auto-incrementing integer |
| `bigserial` | `BIGSERIAL` | Auto-incrementing bigint |
| `enum(...)` | `TEXT + CHECK` | Constrained to specified values |
| `json` | `JSONB` | JSON data storage |
| `email` | `TEXT + CHECK` | Email format validation |
| `phone` | `TEXT + CHECK` | Phone format validation |
| `url` | `TEXT + CHECK` | URL format validation |

## 🚀 Best Practices

### Type Selection

1. **Use specific types**: Prefer `email`, `phone`, `url` over `text` for validation
2. **Consider storage**: Use `varchar(n)` when you know maximum length
3. **Use decimals for money**: Avoid floating point for financial calculations
4. **Use timestamps**: Always use `timestamp` for dates/times
5. **Use UUIDs for security**: Prefer `uuid` over `serial` for external APIs

### Constraints and Validation

1. **Validate at the source**: Use field-level validations to prevent bad data
2. **Use appropriate defaults**: Set sensible defaults for required fields
3. **Index selectively**: Only index fields that are frequently queried
4. **Use enums for consistency**: Prefer enums over free-form text for controlled values

### Performance Considerations

1. **Index foreign keys**: Always index reference fields
2. **Use appropriate sizes**: Choose integer sizes based on expected ranges
3. **Consider JSON indexing**: Use GIN indexes for JSON field queries
4. **Batch operations**: Use appropriate types for bulk operations

## 📚 Related Topics

- **[Entity Definition](../../02_guides/database/entities.md)** - How to define entities
- **[Complete YAML Reference](complete_reference.md)** - All YAML options
- **[Database Fields Guide](../../02_guides/database/fields.md)** - Field definitions