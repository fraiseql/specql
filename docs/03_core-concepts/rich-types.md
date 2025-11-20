# Rich Types: 49 Built-in Validations for Production Data

> **SpecQL's rich type system: Automatic validation, proper PostgreSQL types, and GraphQL scalars**

## Overview

SpecQL includes **49 scalar types + 15 composite types** that automatically generate:
- PostgreSQL CHECK constraints with regex validation
- Range validation for numeric types
- Proper data types and precision
- GraphQL scalar mappings
- Frontend input type hints

No validation code needed in your application—it's all built into the database.

## Why Rich Types Matter

### Traditional Approach (Error-Prone)

```python
# Manual validation everywhere
def create_user(email, age):
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError("Invalid email")
    if not isinstance(age, int) or age < 0 or age > 150:
        raise ValueError("Invalid age")
    # ... then duplicate in frontend, GraphQL, etc
```

### SpecQL Approach (Automatic)

```yaml
entity: User
fields:
  email: email!      # Auto-validates email format
  age: integer(0, 150)  # Auto-validates range
```

**Result**: Validation happens at the database level, automatically enforced everywhere.

## Quick Reference

| Category | Types | Use Case |
|----------|-------|----------|
| **Contact** | `email`, `phoneNumber` | User contact information |
| **Web** | `url`, `domainName`, `slug` | Web addresses and identifiers |
| **Content** | `markdown`, `html`, `text` | Rich text content |
| **Financial** | `money`, `percentage`, `currencyCode` | Monetary values |
| **Temporal** | `date`, `datetime`, `time`, `duration` | Time-based data |
| **Geographic** | `coordinates`, `latitude`, `longitude` | Location data |
| **Technical** | `ipAddress`, `macAddress`, `uuid` | Network and system identifiers |
| **Business** | `stockSymbol`, `isin`, `lei`, `mic` | Financial instruments |
| **Logistics** | `trackingNumber`, `containerNumber`, `vin` | Shipping and transport |
| **Security** | `apiKey`, `hashSHA256` | Authentication and hashing |

## Contact Types

### email
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `Email`
**Validation**: RFC 5322 simplified email format

```yaml
fields:
  email: email!  # NOT NULL + email validation
```

**Generated SQL**:
```sql
email TEXT NOT NULL CHECK (email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
```

**Examples**: `user@example.com`, `test.email+tag@domain.co.uk`

### phoneNumber
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `PhoneNumber`
**Validation**: E.164 international format

```yaml
fields:
  phone: phoneNumber  # Optional phone number
```

**Generated SQL**:
```sql
phone TEXT CHECK (phone ~ '^\+[1-9]\d{1,14}$')
```

**Examples**: `+14155551234`, `+447700900000`

## Web Types

### url
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `Url`
**Validation**: HTTP/HTTPS URL format

```yaml
fields:
  website: url
```

**Generated SQL**:
```sql
website TEXT CHECK (website ~ '^https?://[^\s/$.?#].[^\s]*$')
```

**Examples**: `https://example.com`, `http://localhost:3000/api`

### domainName
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `DomainName`
**Validation**: RFC compliant domain name

```yaml
fields:
  domain: domainName!
```

**Generated SQL**:
```sql
-- Domain name validation (RFC compliant regex)
domain TEXT NOT NULL CHECK (
  domain ~ '^(?:subdomain\.)*domain\.tld$'
)
-- Actual pattern validates: alphanumeric subdomains (max 63 chars each)
-- separated by dots, ending with 2+ letter TLD
```

## Financial Types

### money
**PostgreSQL**: `NUMERIC(19,4)` with precision
**GraphQL**: `Money`
**Validation**: High-precision decimal for currency

```yaml
fields:
  price: money!
  budget: money
```

**Generated SQL**:
```sql
price NUMERIC(19,4) NOT NULL,
budget NUMERIC(19,4)
```

**Examples**: `1234.56`, `999999999.9999`

### percentage
**PostgreSQL**: `NUMERIC(5,2)` with range validation
**GraphQL**: `Percentage`
**Validation**: 0-100 with 2 decimal places

```yaml
fields:
  tax_rate: percentage!
  discount: percentage
```

**Generated SQL**:
```sql
tax_rate NUMERIC(5,2) NOT NULL CHECK (tax_rate >= 0 AND tax_rate <= 100),
discount NUMERIC(5,2) CHECK (discount >= 0 AND discount <= 100)
```

## Geographic Types

### coordinates
**PostgreSQL**: `POINT` with GIST spatial index
**GraphQL**: `Coordinates`
**Validation**: Geographic coordinate pair

```yaml
fields:
  location: coordinates
```

**Generated SQL**:
```sql
location POINT,
-- Auto-generated spatial index
CREATE INDEX idx_table_location ON table USING GIST(location);
```

**Examples**: `(37.7749, -122.4194)`, `(-33.8688, 151.2093)`

### latitude & longitude
**PostgreSQL**: `NUMERIC` with range validation
**GraphQL**: `Latitude` / `Longitude`
**Validation**: Proper geographic ranges

```yaml
fields:
  lat: latitude
  lng: longitude
```

**Generated SQL**:
```sql
lat NUMERIC(10,8) CHECK (lat >= -90 AND lat <= 90),
lng NUMERIC(11,8) CHECK (lng >= -180 AND lng <= 180)
```

## Business Types

### stockSymbol
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `StockSymbol`
**Validation**: Stock ticker format

```yaml
fields:
  ticker: stockSymbol!
```

**Generated SQL**:
```sql
ticker TEXT NOT NULL CHECK (ticker ~ '^[A-Z]{1,5}(\.[A-Z]{1,2})?$')
```

**Examples**: `AAPL`, `BRK.A`, `GOOGL`

### isin
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `ISIN`
**Validation**: International Securities Identification Number

```yaml
fields:
  security_id: isin
```

**Generated SQL**:
```sql
security_id TEXT CHECK (security_id ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
```

**Examples**: `US0378331005` (Apple), `GB0002634946` (BAE Systems)

## Composite Types

SpecQL also supports **15 composite types** for complex data structures:

### PersonName
Structured name with title, first, middle, last, suffix:

```yaml
fields:
  full_name: PersonName!
```

**Generated SQL**:
```sql
full_name JSONB,
-- Validation via JSON schema
CONSTRAINT person_name_check CHECK (jsonb_matches_schema(...))
```

**Example Data**:
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "middleName": "Q",
  "title": "Mr",
  "suffix": "Jr"
}
```

### MoneyAmount
Currency-aware monetary values:

```yaml
fields:
  price: MoneyAmount!
```

**Example Data**:
```json
{
  "amount": 99.99,
  "currency": "USD"
}
```

### ContactInfo
Complete contact information:

```yaml
fields:
  contact: ContactInfo
```

**Example Data**:
```json
{
  "email": "john@example.com",
  "phone": "+14155551234",
  "website": "https://example.com"
}
```

## How Rich Types Work

### Automatic Validation
Every rich type generates appropriate PostgreSQL constraints:

```sql
-- Email validation
CHECK (email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

-- Range validation
CHECK (age >= 0 AND age <= 150)

-- Format validation
CHECK (phone ~ '^\+[1-9]\d{1,14}$')
```

### GraphQL Integration
Rich types map to custom GraphQL scalars:

```graphql
scalar Email
scalar PhoneNumber
scalar Money
scalar Coordinates

type User {
  email: Email!
  phone: PhoneNumber
  salary: Money
  location: Coordinates
}
```

### Frontend Hints
Types include HTML input type hints for better UX:

- `email` → `<input type="email">`
- `url` → `<input type="url">`
- `money` → `<input type="number" step="0.01">`

## Best Practices

### Choose Specific Types
```yaml
# ✅ Specific and validated
fields:
  email: email!
  website: url
  price: money!

# ❌ Generic and unvalidated
fields:
  email: text
  website: text
  price: numeric
```

### Use Enums for Business Values
```yaml
fields:
  status: enum(active, inactive, suspended)
  priority: enum(low, medium, high, urgent)
  category: enum(tech, sales, support, billing)
```

### Combine with Validation
```yaml
fields:
  age: integer(0, 150)      # Range validation
  score: integer(0, 100)    # Percentage-like but custom range
  discount: percentage      # Built-in 0-100 validation
```

## Performance Benefits

Rich types don't just validate—they optimize:

- **Indexes**: Spatial indexes for coordinates
- **Constraints**: Fast validation at database level
- **Types**: Proper PostgreSQL types for performance
- **Queries**: Optimized operators for rich types

## Migration from Plain Types

**Before** (manual validation):
```sql
CREATE TABLE users (
    email TEXT,
    age INTEGER,
    -- Manual constraints
    CONSTRAINT email_check CHECK (email LIKE '%@%'),
    CONSTRAINT age_check CHECK (age >= 0 AND age <= 150)
);
```

**After** (automatic):
```yaml
entity: User
fields:
  email: email!
  age: integer(0, 150)
```

**Result**: Same validation, better performance, GraphQL integration.

## All 49 Scalar Types

**Contact**: `email`, `phoneNumber`
**Web**: `url`, `domainName`, `slug`
**Content**: `markdown`, `html`
**Financial**: `money`, `percentage`, `currencyCode`, `exchangeRate`
**Temporal**: `date`, `datetime`, `time`, `duration`
**Geographic**: `coordinates`, `latitude`, `longitude`
**Technical**: `ipAddress`, `macAddress`, `uuid`
**Business**: `stockSymbol`, `isin`, `cusip`, `lei`, `mic`, `exchangeCode`
**Logistics**: `trackingNumber`, `containerNumber`, `vin`, `flightNumber`, `portCode`, `postalCode`, `airportCode`
**i18n**: `languageCode`, `localeCode`, `timezone`, `countryCode`
**Media**: `image`, `file`, `color`
**Security**: `apiKey`, `hashSHA256`
**Identifiers**: `semanticVersion`, `licensePlate`

## Next Steps

- [Learn about Actions](actions.md) - business logic with rich types
- [Create your first entity](../01_getting-started/first-entity.md) - use rich types in practice
- [See all types reference](../06_reference/rich-types-reference.md) - complete technical details

---

**Rich types eliminate an entire category of bugs: invalid data. Your database guarantees data quality automatically.**</content>
</xai:function_call