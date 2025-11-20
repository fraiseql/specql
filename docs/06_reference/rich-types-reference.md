# Rich Types Quick Reference

> **Quick lookup for all 49 scalar types + 15 composite types in SpecQL**

For detailed examples and use cases, see [Rich Types Guide](../03_core-concepts/rich-types.md).

---

## Contact & Communication

| Type | Format | Example | Validation |
|------|--------|---------|------------|
| `email` | RFC 5322 | `user@example.com` | Email format |
| `phoneNumber` | E.164 | `+14155552671` | International phone |
| `url` | RFC 3986 | `https://example.com` | Valid URL |
| `domainName` | DNS | `example.com` | Domain format |

---

## Financial & Monetary

| Type | Format | Example | PostgreSQL Type |
|------|--------|---------|-----------------|
| `money` | Decimal | `1234.56` | `NUMERIC(19,4)` |
| `percentage` | 0-100 | `15.5` | `NUMERIC(5,2)` |
| `currencyCode` | ISO 4217 | `USD`, `EUR` | `TEXT(3)` |
| `taxId` | Various | `12-3456789` | `TEXT` validated |
| `iban` | ISO 13616 | `GB82WEST12345698765432` | IBAN format |
| `bic` | ISO 9362 | `DEUTDEFF` | BIC/SWIFT code |

---

## Geographic & Location

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| `coordinates` | Lat,Lng | `(37.7749, -122.4194)` | PostgreSQL POINT |
| `latitude` | -90 to 90 | `37.7749` | Decimal degrees |
| `longitude` | -180 to 180 | `-122.4194` | Decimal degrees |
| `countryCode` | ISO 3166-1 | `US`, `GB` | 2-letter code |
| `postalCode` | Various | `94102`, `SW1A 1AA` | Country-specific |
| `timezone` | IANA | `America/New_York` | Timezone identifier |

---

## Identifiers & Codes

| Type | Format | Example | Use Case |
|------|--------|---------|----------|
| `uuid` | UUID v4 | `550e8400-e29b-41d4...` | Unique identifiers |
| `slug` | URL-safe | `my-blog-post` | URL segments |
| `sku` | Custom | `PROD-12345` | Product codes |
| `isbn` | ISBN-10/13 | `978-0-596-52068-7` | Book identifiers |
| `ean` | EAN-13 | `5901234123457` | Barcodes |
| `upc` | UPC-A | `012345678905` | Product codes |
| `gtin` | GTIN-14 | `10012345678902` | Trade items |

---

## Temporal & Time

| Type | Format | Example | PostgreSQL Type |
|------|--------|---------|-----------------|
| `date` | ISO 8601 | `2025-01-15` | `DATE` |
| `datetime` | ISO 8601 | `2025-01-15T10:30:00Z` | `TIMESTAMP` |
| `time` | HH:MM:SS | `14:30:00` | `TIME` |
| `duration` | ISO 8601 | `PT1H30M` | `INTERVAL` |
| `year` | YYYY | `2025` | `INTEGER` |

---

## Content & Text

| Type | Format | Example | Storage |
|------|--------|---------|---------|
| `text` | Plain text | `Hello world` | `TEXT` |
| `text(N)` | Max length | `text(100)` | `TEXT` + check |
| `markdown` | Markdown | `# Title` | `TEXT` |
| `html` | HTML | `<p>Text</p>` | `TEXT` |
| `json` | JSON | `{"key": "value"}` | `JSON` |
| `jsonb` | JSON Binary | `{"key": "value"}` | `JSONB` |

---

## Numeric Types

| Type | Format | Range | Example |
|------|--------|-------|---------|
| `integer` | Whole number | -2B to 2B | `42` |
| `integer(min)` | With min | min to 2B | `integer(0)` |
| `integer(min, max)` | With range | min to max | `integer(0, 100)` |
| `decimal` | Decimal | Unlimited | `123.456` |
| `decimal(p, s)` | Precision | Custom | `decimal(10, 2)` |
| `bigint` | Large int | -9Q to 9Q | `9223372036854775807` |
| `smallint` | Small int | -32K to 32K | `100` |
| `float` | Floating | IEEE 754 | `3.14159` |

---

## Network & Technical

| Type | Format | Example | Validation |
|------|--------|---------|------------|
| `ipAddress` | IPv4/IPv6 | `192.168.1.1` | IP format |
| `ipv4Address` | IPv4 | `192.168.1.1` | IPv4 only |
| `ipv6Address` | IPv6 | `2001:0db8::1` | IPv6 only |
| `macAddress` | MAC | `00:1B:44:11:3A:B7` | MAC format |
| `cidr` | CIDR | `192.168.1.0/24` | Network range |

---

## Security & Hashing

| Type | Format | Example | Use Case |
|------|--------|---------|----------|
| `apiKey` | Base64/Hex | `sk_live_...` | API authentication |
| `hashSHA256` | SHA-256 | `64 hex chars` | Password hashes |
| `hashMD5` | MD5 | `32 hex chars` | Checksums |
| `jwt` | JWT | `eyJ...` | Auth tokens |

---

## Business & Financial

| Type | Format | Example | Standard |
|------|--------|---------|----------|
| `stockSymbol` | Ticker | `AAPL`, `GOOGL` | Stock tickers |
| `isin` | ISO 6166 | `US0378331005` | Securities |
| `lei` | ISO 17442 | `20 chars` | Legal entities |
| `mic` | ISO 10383 | `XNAS` | Market identifiers |
| `cusip` | CUSIP | `037833100` | North American securities |
| `sedol` | SEDOL | `B0WNLY7` | UK securities |

---

## Logistics & Transport

| Type | Format | Example | Use Case |
|------|--------|---------|----------|
| `trackingNumber` | Various | `1Z999AA10123456784` | Shipment tracking |
| `containerNumber` | ISO 6346 | `CSQU3054383` | Shipping containers |
| `vin` | ISO 3779 | `1HGBH41JXMN109186` | Vehicle identification |
| `flightNumber` | IATA | `AA123`, `DL1234` | Flight codes |
| `airportCode` | IATA | `SFO`, `JFK` | Airport identifiers |

---

## Composite Types

### address
Complete postal address with validation:
```yaml
fields:
  shipping_address: address!
```

**Structure**:
```json
{
  "street": "123 Main St",
  "city": "San Francisco",
  "state": "CA",
  "postalCode": "94102",
  "country": "US"
}
```

### money (composite)
Amount + currency:
```yaml
fields:
  price: money!
```

**Structure**:
```json
{
  "amount": "1234.56",
  "currency": "USD"
}
```

### dimensions
Physical dimensions:
```yaml
fields:
  package_size: dimensions!
```

**Structure**:
```json
{
  "length": 10.5,
  "width": 8.0,
  "height": 3.0,
  "unit": "cm"
}
```

### contactInfo
Complete contact information:
```yaml
fields:
  contact_details: contactInfo!
```

**Structure**:
```json
{
  "email": "user@example.com",
  "phone": "+14155552671",
  "address": {...}
}
```

### i18nText
Internationalized text:
```yaml
fields:
  description: i18nText!
```

**Structure**:
```json
{
  "en": "Hello",
  "es": "Hola",
  "fr": "Bonjour"
}
```

---

## Usage Patterns

### Required vs Optional

```yaml
fields:
  email: email!         # Required (NOT NULL)
  phone: phoneNumber    # Optional (NULL allowed)
```

### With Defaults

```yaml
fields:
  status: enum(active, inactive) = 'active'
  count: integer(0) = 0
  is_verified: boolean = false
```

### Range Constraints

```yaml
fields:
  age: integer(18, 120)!        # Age between 18-120
  score: decimal(0, 100)!       # Percentage 0-100
  rating: integer(1, 5)!        # Star rating 1-5
```

### Length Constraints

```yaml
fields:
  name: text(100)!              # Max 100 characters
  bio: text(50, 500)            # Min 50, max 500
  code: text(6, 6)!             # Exactly 6 characters
```

### Lists/Arrays

```yaml
fields:
  tags: list(text)              # Array of strings
  categories: list(ref(Category))  # Array of references
  scores: list(integer(0, 100))    # Array of integers 0-100
```

---

## Generated SQL Examples

### email
```sql
email TEXT NOT NULL
  CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
```

### phoneNumber
```sql
phone TEXT
  CHECK (phone ~ '^\+[1-9]\d{1,14}$')
```

### money
```sql
price NUMERIC(19, 4) NOT NULL
  CHECK (price >= 0)
```

### integer with range
```sql
age INTEGER NOT NULL
  CHECK (age >= 18 AND age <= 120)
```

### text with length
```sql
name TEXT NOT NULL
  CHECK (char_length(name) <= 100)
```

### url
```sql
website TEXT
  CHECK (website ~ '^https?://[^\s/$.?#].[^\s]*$')
```

---

## GraphQL Scalar Mappings

| SpecQL Type | GraphQL Scalar |
|-------------|----------------|
| `email` | `Email` |
| `phoneNumber` | `PhoneNumber` |
| `url` | `URL` |
| `datetime` | `DateTime` |
| `date` | `Date` |
| `time` | `Time` |
| `money` | `Money` |
| `uuid` | `UUID` |
| `json` | `JSON` |
| `jsonb` | `JSON` |

---

## Frontend Input Type Hints

| SpecQL Type | HTML Input Type | Pattern |
|-------------|-----------------|---------|
| `email` | `email` | - |
| `phoneNumber` | `tel` | - |
| `url` | `url` | - |
| `date` | `date` | - |
| `datetime` | `datetime-local` | - |
| `time` | `time` | - |
| `integer` | `number` | `step="1"` |
| `decimal` | `number` | `step="0.01"` |
| `money` | `number` | `step="0.01"` |
| `percentage` | `number` | `min="0" max="100"` |

---

## Common Validation Rules

### Email
- **Pattern**: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- **Max length**: 254 characters
- **Case**: Case-insensitive

### Phone Number
- **Format**: E.164 (`+[country][number]`)
- **Pattern**: `^\+[1-9]\d{1,14}$`
- **Example**: `+14155552671`

### URL
- **Pattern**: `^https?://[^\s/$.?#].[^\s]*$`
- **Schemes**: `http`, `https`
- **Max length**: 2048 characters

### Postal Code
- **US**: `^\d{5}(-\d{4})?$` (ZIP or ZIP+4)
- **UK**: `^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$`
- **CA**: `^[A-Z]\d[A-Z] ?\d[A-Z]\d$`

---

## Performance Considerations

### Indexed Types

These types automatically get indexes:
- `email` - Unique index
- `uuid` - Unique index
- Foreign keys (`ref()`) - Index on FK column

### Storage Optimization

| Type | Storage Size | Notes |
|------|--------------|-------|
| `integer` | 4 bytes | Good default |
| `bigint` | 8 bytes | Use only if needed |
| `smallint` | 2 bytes | For small ranges |
| `text` | Variable | Compressed automatically |
| `jsonb` | Variable | Binary, indexable |
| `json` | Variable | Text, not indexable |

---

## Next Steps

- **Full Guide**: [Rich Types](../03_core-concepts/rich-types.md) - Detailed examples
- **Tutorial**: [Your First Entity](../01_getting-started/first-entity.md) - Use rich types
- **Reference**: [YAML Syntax](yaml-syntax.md) - Complete syntax

---

**Use rich types to move validation to the database—enforce data integrity automatically.**
