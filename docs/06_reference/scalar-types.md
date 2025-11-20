# SpecQL Scalar Types Reference

**Complete technical reference for all 49 validated scalar types** 🔢

## Overview

SpecQL provides 49 built-in scalar types that automatically generate PostgreSQL CHECK constraints, ensuring data quality at the database level. Each type includes validation patterns, GraphQL mappings, and frontend input hints.

**Generated for each type:**
- PostgreSQL column definition with appropriate type
- CHECK constraint with regex/range validation
- GraphQL scalar type mapping
- TypeScript input type hints
- Example values and validation rules

## Contact Types

### email
**PostgreSQL**: `TEXT CHECK (email ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$')`
**GraphQL**: `Email`
**Validation**: RFC 5322 simplified email format
**Examples**: `user@example.com`, `test.email+tag@domain.co.uk`

```yaml
fields:
  email: email!              # NOT NULL email
  backup_email: email        # Optional email
```

### phoneNumber
**PostgreSQL**: `TEXT CHECK (phone ~ '^\\+[1-9]\\d{1,14}$')`
**GraphQL**: `PhoneNumber`
**Validation**: E.164 international phone format
**Examples**: `+14155551234`, `+447700900000`

```yaml
fields:
  phone: phoneNumber
  mobile: phoneNumber
```

## Web Types

### url
**PostgreSQL**: `TEXT CHECK (url ~ '^https?://[^\\s/$.?#].[^\\s]*$')`
**GraphQL**: `Url`
**Validation**: HTTP/HTTPS URL format
**Examples**: `https://example.com`, `http://localhost:3000/api`

```yaml
fields:
  website: url
  api_endpoint: url
```

### domainName
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `DomainName`
**Validation**: RFC compliant domain name

**Generated SQL**:
```sql
-- Domain name validation pattern
CHECK (domain ~ '^(?:&#91;a-zA-Z0-9&#93;(?:&#91;a-zA-Z0-9-&#93;{0,61}&#91;a-zA-Z0-9&#93;)?\.)+&#91;a-zA-Z&#93;{2,}$')
```

**Examples**: `example.com`, `sub.domain.co.uk`

```yaml
fields:
  domain: domainName!
```

### slug
**PostgreSQL**: `TEXT CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$')`
**GraphQL**: `Slug`
**Validation**: URL-friendly string (lowercase, numbers, hyphens)
**Examples**: `my-article`, `user-profile-123`

```yaml
fields:
  slug: slug!
```

## Content Types

### markdown
**PostgreSQL**: `TEXT`
**GraphQL**: `Markdown`
**Validation**: None (accepts any text)
**Notes**: Intended for Markdown content

```yaml
fields:
  content: markdown
  description: markdown
```

### html
**PostgreSQL**: `TEXT`
**GraphQL**: `Html`
**Validation**: None (accepts any text)
**Notes**: Intended for HTML content

```yaml
fields:
  html_content: html
  template: html
```

### text
**PostgreSQL**: `TEXT`
**GraphQL**: `String`
**Validation**: None (accepts any text)
**Notes**: General-purpose text field

```yaml
fields:
  name: text!
  description: text
```

## Financial Types

### money
**PostgreSQL**: `NUMERIC(19,4) CHECK (money >= -999999999999999.9999 AND money <= 999999999999999.9999)`
**GraphQL**: `Money`
**Validation**: 19 digits total, 4 decimal places
**Examples**: `123.45`, `-999.99`

```yaml
fields:
  price: money!
  budget: money
```

### percentage
**PostgreSQL**: `NUMERIC(5,2) CHECK (percentage >= 0 AND percentage <= 100)`
**GraphQL**: `Percentage`
**Validation**: 0-100 range, 2 decimal places
**Examples**: `85.50`, `0.00`, `100.00`

```yaml
fields:
  completion_rate: percentage
  tax_rate: percentage
```

### currencyCode
**PostgreSQL**: `TEXT CHECK (currency ~ '^[A-Z]{3}$')`
**GraphQL**: `CurrencyCode`
**Validation**: ISO 4217 3-letter currency code
**Examples**: `USD`, `EUR`, `GBP`, `JPY`

```yaml
fields:
  currency: currencyCode!
```

## Temporal Types

### date
**PostgreSQL**: `DATE`
**GraphQL**: `Date`
**Validation**: ISO date format (YYYY-MM-DD)
**Examples**: `2023-12-25`, `1990-01-01`

```yaml
fields:
  birth_date: date
  hire_date: date
```

### datetime
**PostgreSQL**: `TIMESTAMPTZ`
**GraphQL**: `DateTime`
**Validation**: ISO timestamp with timezone
**Examples**: `2023-12-25T10:30:00Z`, `2023-12-25T10:30:00+02:00`

```yaml
fields:
  created_at: datetime!
  updated_at: datetime!
```

### time
**PostgreSQL**: `TIME`
**GraphQL**: `Time`
**Validation**: HH:MM:SS format
**Examples**: `14:30:00`, `09:15:30`

```yaml
fields:
  meeting_time: time
  opening_hours: time
```

### duration
**PostgreSQL**: `INTERVAL`
**GraphQL**: `Duration`
**Validation**: PostgreSQL interval format
**Examples**: `1 day`, `2 hours 30 minutes`, `P1DT2H30M`

```yaml
fields:
  processing_time: duration
  warranty_period: duration
```

## Geographic Types

### coordinates
**PostgreSQL**: `POINT` (PostGIS)
**GraphQL**: `Coordinates`
**Validation**: Geographic point (-180 to 180, -90 to 90)
**Examples**: `(2.3522, 48.8566)`, `(-74.0060, 40.7128)`

```yaml
fields:
  location: coordinates
```

### latitude
**PostgreSQL**: `NUMERIC(9,6) CHECK (latitude >= -90 AND latitude <= 90)`
**GraphQL**: `Latitude`
**Validation**: -90 to 90 degrees
**Examples**: `48.8566`, `-33.8688`

```yaml
fields:
  lat: latitude!
```

### longitude
**PostgreSQL**: `NUMERIC(9,6) CHECK (longitude >= -180 AND longitude <= 180)`
**GraphQL**: `Longitude`
**Validation**: -180 to 180 degrees
**Examples**: `2.3522`, `-74.0060`

```yaml
fields:
  lng: longitude!
```

## Technical Types

### ipAddress
**PostgreSQL**: `INET`
**GraphQL**: `IPAddress`
**Validation**: IPv4 or IPv6 address
**Examples**: `192.168.1.1`, `2001:db8::1`

```yaml
fields:
  server_ip: ipAddress
```

### macAddress
**PostgreSQL**: `MACADDR`
**GraphQL**: `MacAddress`
**Validation**: MAC address format
**Examples**: `08:00:27:5a:c8:32`, `08-00-27-5A-C8-32`

```yaml
fields:
  device_mac: macAddress
```

### uuid
**PostgreSQL**: `UUID`
**GraphQL**: `UUID`
**Validation**: UUID format (auto-generated by default)
**Examples**: `550e8400-e29b-41d4-a716-446655440000`

```yaml
fields:
  api_key: uuid!
```

## Business Types

### stockSymbol
**PostgreSQL**: `TEXT CHECK (symbol ~ '^[A-Z]{1,5}$')`
**GraphQL**: `StockSymbol`
**Validation**: 1-5 uppercase letters
**Examples**: `AAPL`, `GOOGL`, `TSLA`

```yaml
fields:
  ticker: stockSymbol!
```

### isin
**PostgreSQL**: `TEXT CHECK (isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$')`
**GraphQL**: `ISIN`
**Validation**: ISO 6166 ISIN format
**Examples**: `US0378331005` (Apple), `US5949181045` (Microsoft)

```yaml
fields:
  isin_code: isin!
```

### lei
**PostgreSQL**: `TEXT CHECK (lei ~ '^[A-Z0-9]{18}[0-9]{2}$')`
**GraphQL**: `LEI`
**Validation**: Legal Entity Identifier format
**Examples**: `54930084UKLVMY22DS16`

```yaml
fields:
  lei_code: lei
```

### mic
**PostgreSQL**: `TEXT CHECK (mic ~ '^[A-Z0-9]{4}$')`
**GraphQL**: `MIC`
**Validation**: ISO 10383 Market Identifier Code
**Examples**: `XNAS` (NASDAQ), `XLON` (London Stock Exchange)

```yaml
fields:
  market_code: mic!
```

## Logistics Types

### trackingNumber
**PostgreSQL**: `TEXT CHECK (tracking ~ '^[A-Z0-9]{8,30}$')`
**GraphQL**: `TrackingNumber`
**Validation**: 8-30 alphanumeric characters
**Examples**: `1Z999AA1234567890`, `9400111899223344556677`

```yaml
fields:
  tracking_code: trackingNumber
```

### containerNumber
**PostgreSQL**: `TEXT CHECK (container ~ '^[A-Z]{3}[UJZ][0-9]{7}$')`
**GraphQL**: `ContainerNumber`
**Validation**: ISO 6346 container number format
**Examples**: `MSKU1234567`, `OOLU1234560`

```yaml
fields:
  container_id: containerNumber!
```

### vin
**PostgreSQL**: `TEXT CHECK (vin ~ '^[A-HJ-NPR-Z0-9]{17}$')`
**GraphQL**: `VIN`
**Validation**: Vehicle Identification Number format
**Examples**: `1HGCM82633A123456`

```yaml
fields:
  vehicle_vin: vin!
```

## Security Types

### apiKey
**PostgreSQL**: `TEXT CHECK (api_key ~ '^[A-Za-z0-9]{32,128}$')`
**GraphQL**: `ApiKey`
**Validation**: 32-128 alphanumeric characters
**Examples**: `sk_test_4eC39HqLyjWDarjtT1zdp7dc`

```yaml
fields:
  api_key: apiKey!
```

### hashSHA256
**PostgreSQL**: `TEXT CHECK (hash ~ '^[a-f0-9]{64}$')`
**GraphQL**: `HashSHA256`
**Validation**: 64 hexadecimal characters (SHA-256 hash)
**Examples**: `a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3`

```yaml
fields:
  password_hash: hashSHA256!
```

## Media Types

### image
**PostgreSQL**: `TEXT`
**GraphQL**: `ImageUrl`
**Validation**: None (intended for image URLs)
**Notes**: Use with `url` type for validation

```yaml
fields:
  avatar_url: image
  logo_url: image
```

### video
**PostgreSQL**: `TEXT`
**GraphQL**: `VideoUrl`
**Validation**: None (intended for video URLs)

```yaml
fields:
  video_url: video
```

### audio
**PostgreSQL**: `TEXT`
**GraphQL**: `AudioUrl`
**Validation**: None (intended for audio URLs)

```yaml
fields:
  audio_url: audio
```

## Numeric Types

### integer
**PostgreSQL**: `INTEGER`
**GraphQL**: `Int`
**Validation**: -2147483648 to 2147483647
**Examples**: `42`, `-100`, `0`

```yaml
fields:
  count: integer!
  quantity: integer
```

### bigint
**PostgreSQL**: `BIGINT`
**GraphQL**: `BigInt`
**Validation**: -9223372036854775808 to 9223372036854775807
**Examples**: `9223372036854775807`

```yaml
fields:
  large_number: bigint
```

### decimal
**PostgreSQL**: `NUMERIC(10,2)`
**GraphQL**: `Decimal`
**Validation**: 10 digits total, 2 decimal places
**Examples**: `123.45`, `-999.99`

```yaml
fields:
  amount: decimal
```

### numeric
**PostgreSQL**: `NUMERIC`
**GraphQL**: `Numeric`
**Validation**: Arbitrary precision decimal
**Examples**: `123.456789`, `-999.999999`

```yaml
fields:
  precise_value: numeric
```

## Boolean and Binary Types

### boolean
**PostgreSQL**: `BOOLEAN`
**GraphQL**: `Boolean`
**Validation**: true/false
**Examples**: `true`, `false`

```yaml
fields:
  active: boolean = true
  verified: boolean!
```

### bytea
**PostgreSQL**: `BYTEA`
**GraphQL**: `ByteArray`
**Validation**: Binary data
**Notes**: For files, images, encrypted data

```yaml
fields:
  file_data: bytea
  encrypted_content: bytea
```

## JSON Types

### json
**PostgreSQL**: `JSONB`
**GraphQL**: `JSONObject`
**Validation**: Valid JSON structure
**Examples**: `{"key": "value"}`, `[1, 2, 3]`

```yaml
fields:
  metadata: json
  settings: json
```

### jsonb
**PostgreSQL**: `JSONB`
**GraphQL**: `JSONObject`
**Validation**: Valid JSON structure (same as json)
**Notes**: JSONB is the recommended JSON type in PostgreSQL

```yaml
fields:
  configuration: jsonb
  user_preferences: jsonb
```

## Identifier Types

### hierarchical
**PostgreSQL**: `TEXT`
**GraphQL**: `HierarchicalIdentifier`
**Validation**: None (intended for hierarchical paths)
**Examples**: `root.parent.child`, `1.2.3.4`

```yaml
fields:
  path: hierarchical
  category_path: hierarchical
```

## Type Mapping Table

| SpecQL Type | PostgreSQL Type | GraphQL Type | Validation |
|-------------|-----------------|--------------|------------|
| `email` | `TEXT` | `Email` | RFC 5322 email |
| `phoneNumber` | `TEXT` | `PhoneNumber` | E.164 phone |
| `url` | `TEXT` | `Url` | HTTP/HTTPS URL |
| `domainName` | `TEXT` | `DomainName` | RFC domain |
| `slug` | `TEXT` | `Slug` | URL-friendly |
| `markdown` | `TEXT` | `Markdown` | None |
| `html` | `TEXT` | `Html` | None |
| `text` | `TEXT` | `String` | None |
| `money` | `NUMERIC(19,4)` | `Money` | 19 digits, 4 decimals |
| `percentage` | `NUMERIC(5,2)` | `Percentage` | 0-100, 2 decimals |
| `currencyCode` | `TEXT` | `CurrencyCode` | ISO 4217 |
| `date` | `DATE` | `Date` | ISO date |
| `datetime` | `TIMESTAMPTZ` | `DateTime` | ISO timestamp |
| `time` | `TIME` | `Time` | HH:MM:SS |
| `duration` | `INTERVAL` | `Duration` | PostgreSQL interval |
| `coordinates` | `POINT` | `Coordinates` | Geographic point |
| `latitude` | `NUMERIC(9,6)` | `Latitude` | -90 to 90 |
| `longitude` | `NUMERIC(9,6)` | `Longitude` | -180 to 180 |
| `ipAddress` | `INET` | `IPAddress` | IPv4/IPv6 |
| `macAddress` | `MACADDR` | `MacAddress` | MAC address |
| `uuid` | `UUID` | `UUID` | UUID format |
| `stockSymbol` | `TEXT` | `StockSymbol` | 1-5 uppercase |
| `isin` | `TEXT` | `ISIN` | ISO 6166 |
| `lei` | `TEXT` | `LEI` | Legal Entity ID |
| `mic` | `TEXT` | `MIC` | Market ID Code |
| `trackingNumber` | `TEXT` | `TrackingNumber` | 8-30 alphanumeric |
| `containerNumber` | `TEXT` | `ContainerNumber` | ISO 6346 |
| `vin` | `TEXT` | `VIN` | Vehicle ID |
| `apiKey` | `TEXT` | `ApiKey` | 32-128 alphanumeric |
| `hashSHA256` | `TEXT` | `HashSHA256` | 64 hex chars |
| `image` | `TEXT` | `ImageUrl` | None |
| `video` | `TEXT` | `VideoUrl` | None |
| `audio` | `TEXT` | `AudioUrl` | None |
| `integer` | `INTEGER` | `Int` | 32-bit integer |
| `bigint` | `BIGINT` | `BigInt` | 64-bit integer |
| `decimal` | `NUMERIC(10,2)` | `Decimal` | 10 digits, 2 decimals |
| `numeric` | `NUMERIC` | `Numeric` | Arbitrary precision |
| `boolean` | `BOOLEAN` | `Boolean` | true/false |
| `bytea` | `BYTEA` | `ByteArray` | Binary data |
| `json` | `JSONB` | `JSONObject` | JSON structure |
| `jsonb` | `JSONB` | `JSONObject` | JSON structure |
| `hierarchical` | `TEXT` | `HierarchicalIdentifier` | None |

## Validation Patterns

### Regex Patterns Used

```sql
-- Email validation
CHECK (email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$')

-- Phone (E.164)
CHECK (phone ~ '^\+[1-9]\d{1,14}$')

-- URL
CHECK (url ~ '^https?://[^\s/$.?#].[^\s]*$')

-- Domain
CHECK (domain ~ '^(?:&#91;a-zA-Z0-9&#93;(?:&#91;a-zA-Z0-9-&#93;{0,61}&#91;a-zA-Z0-9&#93;)?\.)+&#91;a-zA-Z&#93;{2,}$')

-- Slug
CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$')

-- Currency code
CHECK (currency ~ '^[A-Z]{3}$')

-- ISIN
CHECK (isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$')

-- LEI
CHECK (lei ~ '^[A-Z0-9]{18}[0-9]{2}$')

-- MIC
CHECK (mic ~ '^[A-Z0-9]{4}$')

-- Container number
CHECK (container ~ '^[A-Z]{3}[UJZ][0-9]{7}$')

-- VIN
CHECK (vin ~ '^[A-HJ-NPR-Z0-9]{17}$')

-- API key
CHECK (api_key ~ '^[A-Za-z0-9]{32,128}$')

-- SHA256 hash
CHECK (hash ~ '^[a-f0-9]{64}$')
```

### Range Validations

```sql
-- Money range
CHECK (money >= -999999999999999.9999 AND money <= 999999999999999.9999)

-- Percentage range
CHECK (percentage >= 0 AND percentage <= 100)

-- Latitude range
CHECK (latitude >= -90 AND latitude <= 90)

-- Longitude range
CHECK (longitude >= -180 AND longitude <= 180)

-- Integer range
CHECK (integer >= -2147483648 AND integer <= 2147483647)

-- BigInt range
CHECK (bigint >= -9223372036854775808 AND bigint <= 9223372036854775807)
```

## Frontend Type Hints

Each scalar type provides TypeScript input type hints for better developer experience:

```typescript
// Generated from SpecQL types
interface ContactInput {
  email: string;        // email type
  phone?: string;       // phoneNumber type
  website?: string;     // url type
  score: number;        // percentage type (0-100)
  budget: number;       // money type
  coordinates: { lat: number; lng: number }; // coordinates type
  createdAt: Date;      // datetime type
  active: boolean;      // boolean type
}
```

## Custom Validation

For complex validation beyond built-in types:

```yaml
fields:
  custom_field:
    type: text
    validation: "^[A-Z][a-z]+$"  # Custom regex
    description: "Must start with capital letter"
```

## Migration from Generic Types

### Before (Generic Types)
```yaml
fields:
  email: text          # No validation
  phone: text          # No validation
  price: numeric       # No range limits
  percentage: numeric  # No 0-100 limit
```

### After (Rich Types)
```yaml
fields:
  email: email!        # Automatic email validation
  phone: phone         # Automatic E.164 validation
  price: money         # Automatic precision and range
  percentage: percentage # Automatic 0-100 validation
```

## Performance Considerations

- **Rich types add CHECK constraints**: Minimal performance impact
- **Text validations use regex**: Efficient for most use cases
- **Numeric ranges use simple comparisons**: Very fast
- **JSON types use JSONB**: Indexed and searchable
- **Geographic types require PostGIS**: Enable for coordinate support

## Best Practices

### 1. Use Semantic Types
```yaml
# ✅ Use specific types
email: email!
phone: phone
website: url
price: money

# ❌ Don't use generic types
email: text
phone: text
website: text
price: numeric
```

### 2. Leverage Validation
```yaml
# ✅ Database-level validation
score: percentage    # Automatically 0-100
currency: currencyCode # Automatically 3-letter code

# ❌ Application-level validation needed
score: numeric      # Need to validate 0-100 in app
currency: text      # Need to validate format in app
```

### 3. Consider Storage Size
```yaml
# ✅ Appropriate precision
price: money        # NUMERIC(19,4) - suitable for most currencies
percentage: percentage # NUMERIC(5,2) - 2 decimal places

# ❌ Over-precision
price: numeric      # Arbitrary precision - wasteful
percentage: decimal # NUMERIC(10,2) - unnecessary precision
```

## Troubleshooting

### Validation Errors
```
ERROR: new row for relation "contact" violates check constraint "contact_email_check"
DETAIL: Failing row contains (email) = (invalid-email)

# Fix: Use valid email format
email: 'user@example.com'
```

### Type Mismatches
```
ERROR: column "price" is of type numeric but expression is of type text

# Fix: Use numeric value
price: 123.45  # Not "123.45"
```

### PostGIS Required
```
ERROR: type "point" does not exist

# Fix: Install PostGIS extension
CREATE EXTENSION postgis;
```

## Next Steps

- **Read YAML Syntax**: Complete DSL reference in `yaml-syntax.md`
- **Check Rich Types Guide**: Usage examples in `../03_core-concepts/rich-types.md`
- **Browse Examples**: See types in action in `examples/`
- **Generate Schema**: Run `specql generate` to see generated constraints

---

**49 types, 49 validations, zero boilerplate.** ✅