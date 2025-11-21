# Rich Types Overview
## **Best explanation extracted from docs/guides/rich-types-guide.md**

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

---

**Source**: docs/guides/rich-types-guide.md
**Quality**: Good - clear categories, concrete examples, shows generated SQL
**Use in**: 03_core-concepts/rich-types.md</content>
</xai:function_call
