# Rich Types Guide

**SpecQL Rich Types: 50 Validated Scalar Types for Production-Ready Data**

Rich types automatically generate PostgreSQL CHECK constraints, ensuring data quality at the database level. No validation code needed in your application.

## Overview

SpecQL includes 50 built-in scalar types that automatically generate:
- PostgreSQL CHECK constraints with regex validation
- Range validation for numeric types
- Proper data types and precision
- GraphQL scalar mappings
- Frontend input type hints

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
domain TEXT NOT NULL CHECK (domain ~ '^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
```

**Examples**: `example.com`, `sub.domain.co.uk`

### slug
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `Slug`
**Validation**: URL-safe identifier

```yaml
fields:
  slug: slug!
```

**Generated SQL**:
```sql
slug TEXT NOT NULL CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$')
```

**Examples**: `my-article`, `user-profile-123`

## Content Types

### markdown
**PostgreSQL**: `TEXT`
**GraphQL**: `Markdown`
**Validation**: Basic markdown structure check

```yaml
fields:
  content: markdown
```

**Examples**: Standard markdown content with headers, links, lists

### html
**PostgreSQL**: `TEXT`
**GraphQL**: `Html`
**Validation**: Basic HTML structure check

```yaml
fields:
  description: html
```

**Examples**: HTML content with tags and attributes

## Financial Types

### money
**PostgreSQL**: `NUMERIC(19,4)` with range validation
**GraphQL**: `Money`
**Validation**: -999999999999999.9999 to 999999999999999.9999

```yaml
fields:
  price: money!
```

**Generated SQL**:
```sql
price NUMERIC(19,4) NOT NULL CHECK (price >= -999999999999999.9999 AND price <= 999999999999999.9999)
```

**Examples**: `99.99`, `1234567.8901`, `-50.00`

### percentage
**PostgreSQL**: `NUMERIC(5,2)` with range validation
**GraphQL**: `Percentage`
**Validation**: 0.00 to 100.00

```yaml
fields:
  score: percentage
```

**Generated SQL**:
```sql
score NUMERIC(5,2) CHECK (score >= 0.00 AND score <= 100.00)
```

**Examples**: `85.50`, `100.00`, `0.01`

### currencyCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `CurrencyCode`
**Validation**: ISO 4217 currency codes

```yaml
fields:
  currency: currencyCode!
```

**Generated SQL**:
```sql
currency TEXT NOT NULL CHECK (currency ~ '^[A-Z]{3}$')
```

**Examples**: `USD`, `EUR`, `GBP`, `JPY`

## Temporal Types

### date
**PostgreSQL**: `DATE`
**GraphQL**: `Date`
**Validation**: ISO date format

```yaml
fields:
  birth_date: date
```

**Examples**: `2025-01-15`, `1990-12-31`

### datetime
**PostgreSQL**: `TIMESTAMPTZ`
**GraphQL**: `DateTime`
**Validation**: ISO timestamp with timezone

```yaml
fields:
  created_at: datetime!
```

**Examples**: `2025-01-15T14:30:00Z`, `2025-01-15T09:30:00-05:00`

### time
**PostgreSQL**: `TIME`
**GraphQL**: `Time`
**Validation**: HH:MM:SS format

```yaml
fields:
  meeting_time: time
```

**Examples**: `14:30:00`, `09:15:30`

### duration
**PostgreSQL**: `INTERVAL`
**GraphQL**: `Duration`
**Validation**: PostgreSQL interval format

```yaml
fields:
  duration: duration
```

**Examples**: `1 hour 30 minutes`, `2 days`, `PT1H30M`

## Geographic Types

### coordinates
**PostgreSQL**: `POINT` with spatial index
**GraphQL**: `Coordinates`
**Validation**: Latitude/Longitude pair

```yaml
fields:
  location: coordinates
```

**Generated SQL**:
```sql
location POINT
-- Plus automatic GIST spatial index
CREATE INDEX idx_tb_entity_location ON schema.tb_entity USING GIST(location);
```

**Examples**: `(37.7749, -122.4194)`, `(-33.8688, 151.2093)`

### latitude
**PostgreSQL**: `NUMERIC(9,6)` with range validation
**GraphQL**: `Latitude`
**Validation**: -90.000000 to 90.000000

```yaml
fields:
  lat: latitude!
```

**Generated SQL**:
```sql
lat NUMERIC(9,6) NOT NULL CHECK (lat >= -90.000000 AND lat <= 90.000000)
```

### longitude
**PostgreSQL**: `NUMERIC(9,6)` with range validation
**GraphQL**: `Longitude`
**Validation**: -180.000000 to 180.000000

```yaml
fields:
  lng: longitude!
```

**Generated SQL**:
```sql
lng NUMERIC(9,6) NOT NULL CHECK (lng >= -180.000000 AND lng <= 180.000000)
```

## Technical Types

### ipAddress
**PostgreSQL**: `INET`
**GraphQL**: `IpAddress`
**Validation**: IPv4 or IPv6 address

```yaml
fields:
  ip: ipAddress
```

**Examples**: `192.168.1.1`, `2001:db8::1`

### macAddress
**PostgreSQL**: `MACADDR`
**GraphQL**: `MacAddress`
**Validation**: MAC address format

```yaml
fields:
  mac: macAddress
```

**Examples**: `00:1B:44:11:3A:B7`, `00-1B-44-11-3A-B7`

### uuid
**PostgreSQL**: `UUID`
**GraphQL**: `UUID`
**Validation**: UUID format

```yaml
fields:
  api_key: uuid!
```

**Examples**: `550e8400-e29b-41d4-a716-446655440000`

## Internationalization Types

### languageCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `LanguageCode`
**Validation**: ISO 639 language codes

```yaml
fields:
  language: languageCode
```

**Generated SQL**:
```sql
language TEXT CHECK (language ~ '^[a-z]{2,3}(?:-[A-Z]{2})?$')
```

**Examples**: `en`, `fr`, `zh-CN`, `pt-BR`

### localeCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `LocaleCode`
**Validation**: BCP 47 locale format

```yaml
fields:
  locale: localeCode
```

**Generated SQL**:
```sql
locale TEXT CHECK (locale ~ '^[a-z]{2,3}(?:-[A-Z]{2})?(?:-[a-z]{2,8})*$')
```

**Examples**: `en-US`, `fr-CA`, `zh-Hans-CN`

### timezone
**PostgreSQL**: `TEXT` with validation
**GraphQL**: `Timezone`
**Validation**: IANA timezone names

```yaml
fields:
  tz: timezone!
```

**Examples**: `America/New_York`, `Europe/London`, `Asia/Tokyo`

### countryCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `CountryCode`
**Validation**: ISO 3166-1 alpha-2

```yaml
fields:
  country: countryCode
```

**Generated SQL**:
```sql
country TEXT CHECK (country ~ '^[A-Z]{2}$')
```

**Examples**: `US`, `GB`, `CA`, `JP`

## Financial Instrument Types

### stockSymbol
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `StockSymbol`
**Validation**: Stock ticker format

```yaml
fields:
  symbol: stockSymbol!
```

**Generated SQL**:
```sql
symbol TEXT NOT NULL CHECK (symbol ~ '^[A-Z]{1,5}(\.[A-Z]{1,2})?$')
```

**Examples**: `AAPL`, `GOOGL`, `BRK.A`

### isin
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `ISIN`
**Validation**: ISO 6166 ISIN format

```yaml
fields:
  isin: isin
```

**Generated SQL**:
```sql
isin TEXT CHECK (isin ~ '^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
```

**Examples**: `US0378331005`, `GB0002634946`

### cusip
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `CUSIP`
**Validation**: CUSIP format

```yaml
fields:
  cusip: cusip
```

**Generated SQL**:
```sql
cusip TEXT CHECK (cusip ~ '^[0-9]{6}[0-9A-Z]{2}[0-9]$')
```

**Examples**: `037833100`, `172967424`

### sedol
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `SEDOL`
**Validation**: SEDOL format

```yaml
fields:
  sedol: sedol
```

**Generated SQL**:
```sql
sedol TEXT CHECK (sedol ~ '^[0-9A-Z]{6}[0-9]$')
```

**Examples**: `B02LC96`, `0263494`

### lei
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `LEI`
**Validation**: LEI format

```yaml
fields:
  lei: lei
```

**Generated SQL**:
```sql
lei TEXT CHECK (lei ~ '^[0-9A-Z]{18}[0-9]{2}$')
```

**Examples**: `54930084UKLVMY22DS16`

### mic
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `MIC`
**Validation**: ISO 10383 MIC format

```yaml
fields:
  mic: mic
```

**Generated SQL**:
```sql
mic TEXT CHECK (mic ~ '^[A-Z0-9]{4}$')
```

**Examples**: `XNYS`, `XLON`

### exchangeCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `ExchangeCode`
**Validation**: Exchange code format

```yaml
fields:
  exchange: exchangeCode
```

**Generated SQL**:
```sql
exchange TEXT CHECK (exchange ~ '^[A-Z]{2,6}$')
```

**Examples**: `NYSE`, `NASDAQ`, `LSE`

### exchangeRate
**PostgreSQL**: `NUMERIC(19,8)` with range validation
**GraphQL**: `ExchangeRate`
**Validation**: High precision decimal

```yaml
fields:
  rate: exchangeRate!
```

**Generated SQL**:
```sql
rate NUMERIC(19,8) NOT NULL CHECK (rate >= 0.0)
```

## Logistics Types

### trackingNumber
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `TrackingNumber`
**Validation**: Generic tracking number format

```yaml
fields:
  tracking: trackingNumber
```

**Generated SQL**:
```sql
tracking TEXT CHECK (tracking ~ '^[A-Z0-9]{8,30}$')
```

**Examples**: `1Z999AA1234567890`, `9400111899223344`

### containerNumber
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `ContainerNumber`
**Validation**: ISO 6346 container number

```yaml
fields:
  container: containerNumber
```

**Generated SQL**:
```sql
container TEXT CHECK (container ~ '^[A-Z]{3}[UJZ]\d{6}\d$')
```

**Examples**: `MSKU1234567`, `CSQU3054383`

### licensePlate
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `LicensePlate`
**Validation**: International license plate format

```yaml
fields:
  plate: licensePlate
```

**Generated SQL**:
```sql
plate TEXT CHECK (plate ~ '^[A-Z0-9\s\-]{1,20}$')
```

**Examples**: `ABC-123`, `CA 123456`

### vin
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `VIN`
**Validation**: Vehicle Identification Number

```yaml
fields:
  vin: vin
```

**Generated SQL**:
```sql
vin TEXT CHECK (vin ~ '^[A-HJ-NPR-Z0-9]{17}$')
```

**Examples**: `1HGCM82633A123456`

### flightNumber
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `FlightNumber`
**Validation**: Airline code + number format

```yaml
fields:
  flight: flightNumber
```

**Generated SQL**:
```sql
flight TEXT CHECK (flight ~ '^[A-Z]{2,3}\d{1,4}[A-Z]?$')
```

**Examples**: `AA1234`, `BAW123`, `DL1234A`

### portCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `PortCode`
**Validation**: UN/LOCODE format

```yaml
fields:
  port: portCode
```

**Generated SQL**:
```sql
port TEXT CHECK (port ~ '^[A-Z]{5}$')
```

**Examples**: `USNYC`, `NLRTM`, `HKHKG`

### postalCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `PostalCode`
**Validation**: International postal code format

```yaml
fields:
  zip: postalCode
```

**Generated SQL**:
```sql
zip TEXT CHECK (zip ~ '^[A-Z0-9\s\-]{3,12}$')
```

**Examples**: `12345`, `SW1A 1AA`, `90210-1234`

### airportCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `AirportCode`
**Validation**: IATA airport code

```yaml
fields:
  airport: airportCode
```

**Generated SQL**:
```sql
airport TEXT CHECK (airport ~ '^[A-Z]{3}$')
```

**Examples**: `JFK`, `LAX`, `LHR`, `NRT`

## Security Types

### apiKey
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `ApiKey`
**Validation**: API key format

```yaml
fields:
  api_key: apiKey
```

**Generated SQL**:
```sql
api_key TEXT CHECK (api_key ~ '^[A-Za-z0-9_\-]{20,128}$')
```

**Examples**: `sk-1234567890abcdef`, `pk_live_1234567890abcdef`

### hashSHA256
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `HashSHA256`
**Validation**: SHA256 hex format

```yaml
fields:
  password_hash: hashSHA256
```

**Generated SQL**:
```sql
password_hash TEXT CHECK (password_hash ~ '^[a-f0-9]{64}$')
```

**Examples**: `a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3`

## Banking Types

### iban
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `IBAN`
**Validation**: IBAN format

```yaml
fields:
  iban: iban
```

**Generated SQL**:
```sql
iban TEXT CHECK (iban ~ '^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$')
```

**Examples**: `GB29 NWBK 6016 1331 9268 19`

### swiftCode
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `SwiftCode`
**Validation**: SWIFT/BIC format

```yaml
fields:
  swift: swiftCode
```

**Generated SQL**:
```sql
swift TEXT CHECK (swift ~ '^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$')
```

**Examples**: `CHASUS33`, `DEUTDEFF`

## Special Types

### json
**PostgreSQL**: `JSONB`
**GraphQL**: `JSON`
**Validation**: Valid JSON structure

```yaml
fields:
  metadata: json
```

**Examples**: `{"key": "value"}`, `[1, 2, 3]`, `{"nested": {"object": true}}`

### image
**PostgreSQL**: `TEXT`
**GraphQL**: `Image`
**Validation**: Image file extension

```yaml
fields:
  avatar: image
```

**Generated SQL**:
```sql
avatar TEXT CHECK (avatar ~ '\.(jpg|jpeg|png|gif|webp|svg)$'i)
```

### file
**PostgreSQL**: `TEXT`
**GraphQL**: `File`
**Validation**: Generic file path

```yaml
fields:
  attachment: file
```

### color
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `Color`
**Validation**: Hex color format

```yaml
fields:
  theme_color: color
```

**Generated SQL**:
```sql
theme_color TEXT CHECK (theme_color ~ '^#[0-9A-Fa-f]{6}$')
```

**Examples**: `#FF0000`, `#00FF00`, `#0000FF`

### mimeType
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `MimeType`
**Validation**: MIME type format

```yaml
fields:
  content_type: mimeType
```

**Generated SQL**:
```sql
content_type TEXT CHECK (content_type ~ '^[a-zA-Z][a-zA-Z0-9\-+]*\/[a-zA-Z0-9\-+]*$')
```

**Examples**: `application/json`, `text/html`, `image/png`

### semanticVersion
**PostgreSQL**: `TEXT` with regex validation
**GraphQL**: `SemanticVersion`
**Validation**: SemVer format

```yaml
fields:
  version: semanticVersion!
```

**Generated SQL**:
```sql
version TEXT NOT NULL CHECK (version ~ '^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$')
```

**Examples**: `1.0.0`, `2.1.3-alpha`, `3.0.0-beta.1`

## Usage Patterns

### Basic Entity with Rich Types

```yaml
entity: User
schema: public
description: "User account with rich type validation"

fields:
  # Contact information
  email: email!
  phone: phoneNumber

  # Profile data
  username: slug!
  bio: markdown
  website: url

  # Financial data
  salary: money
  completion_rate: percentage

  # Geographic data
  home_coordinates: coordinates

  # Technical data
  api_key: apiKey
  last_login_ip: ipAddress

  # Internationalization
  language: languageCode
  timezone: timezone!
  country: countryCode
```

### E-commerce Product

```yaml
entity: Product
schema: commerce
description: "Product with comprehensive rich types"

fields:
  name: text!
  description: html
  price: money!
  currency: currencyCode!
  discount_percentage: percentage
  weight_kg: float
  dimensions: json  # {"width": 10, "height": 5, "depth": 2}
  color: color
  image_url: url
  sku: text!
  barcode: text
```

### Financial Instrument

```yaml
entity: Stock
schema: finance
description: "Stock with financial instrument types"

fields:
  symbol: stockSymbol!
  isin: isin
  cusip: cusip
  exchange: mic!
  currency: currencyCode!
  last_price: money
  market_cap: money
  pe_ratio: float
```

## Error Messages

Rich types provide clear validation error messages:

- **email**: "Email must be in valid format (user@domain.com)"
- **phoneNumber**: "Phone number must be in E.164 format (+1234567890)"
- **url**: "URL must be a valid HTTP or HTTPS address"
- **money**: "Amount must be between -999999999999999.9999 and 999999999999999.9999"
- **percentage**: "Percentage must be between 0.00 and 100.00"
- **coordinates**: "Coordinates must be valid latitude/longitude pair"

## Custom Validation

For custom validation beyond built-in types, use actions with validate steps:

```yaml
actions:
  - name: create_user
    steps:
      - validate: age >= 18 AND age <= 120
      - validate: LENGTH(password) >= 8
      - validate: email NOT IN (SELECT email FROM banned_emails)
      - insert: User
```

## Performance Considerations

- **Indexes**: Rich types automatically create appropriate indexes (spatial for coordinates, etc.)
- **Constraints**: CHECK constraints are fast but add overhead on INSERT/UPDATE
- **Storage**: Some types use higher precision (NUMERIC) for accuracy
- **Validation**: Regex validation is performed at database level

## Migration from Basic Types

When upgrading from basic types to rich types:

```yaml
# Before
fields:
  email: text!
  phone: text
  price: float

# After
fields:
  email: email!      # Now validated
  phone: phoneNumber # Now validated
  price: money       # Now properly typed with precision
```

The migration automatically adds CHECK constraints to existing data. Run validation first:

```bash
specql validate entities/*.yaml
```

---

**Next**: Learn about [Actions](actions-guide.md) or explore [Stdlib Entities](stdlib-usage.md)