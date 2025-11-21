# Rich Types in stdlib

stdlib entities use FraiseQL rich scalar types for better type safety and validation.

## Geographic Types

### coordinates

**Maps to**: PostgreSQL `POINT`
**Format**: `(latitude, longitude)`
**Used in**: PublicAddress, Location

**Example**:
```yaml
coordinates:
  type: coordinates
  nullable: true
  description: "Geographic coordinates"
```

**Generated SQL**:
```sql
coordinates POINT
```

**GraphQL**:
```graphql
type Coordinates {
  lat: Float!
  lng: Float!
}
```

## Contact Types

### email

**Maps to**: TEXT with email validation
**Format**: RFC 5322
**Used in**: Contact

### phone

**Maps to**: TEXT with E.164 validation
**Format**: `+[country][number]` (e.g., `+33612345678`)
**Used in**: Contact

## Web Types

### url

**Maps to**: TEXT with URL validation
**Format**: Valid URL (http/https)
**Used in**: Organization

## Financial Types

### money

**Maps to**: NUMERIC(19,4)
**Used in**: Price

## Complete List

See FraiseQL documentation for all available rich types.
