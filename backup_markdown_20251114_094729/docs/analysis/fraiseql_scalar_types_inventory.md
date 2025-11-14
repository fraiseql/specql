# FraiseQL Scalar Types Inventory

Complete list of 50 scalar types that need to be added to the FraiseQL library for comprehensive enterprise-grade GraphQL support.

## Categories Overview

| Category | Count | Description |
|----------|-------|-------------|
| i18n Types | 3 | Internationalization support |
| Financial Types | 11 | Financial and business data |
| Geographic Types | 6 | Location and coordinate data |
| Network Types | 6 | Network and technical identifiers |
| Logistics Types | 6 | Shipping and transportation |
| Content Types | 5 | Email, URLs, media validation |
| Data Types | 4 | Identifiers and technical data |
| Date/Time Types | 4 | Temporal data handling |
| Structured Types | 3 | Content formatting |
| **Total** | **50** | Complete enterprise coverage |

## Complete Scalar Type Inventory

### i18n Types
- **LanguageCode** (languageCode): ISO 639-1 two-letter language code - PostgreSQL: TEXT
- **LocaleCode** (localeCode): BCP 47 locale code for regional formatting - PostgreSQL: TEXT
- **Timezone** (timezone): IANA timezone database identifier - PostgreSQL: TEXT

### Financial Types
- **CurrencyCode** (currencyCode): ISO 4217 currency code - PostgreSQL: TEXT
- **Money** (money): Monetary amount (no currency, use MoneyAmount composite for currency) - PostgreSQL: NUMERIC
- **Percentage** (percentage): Percentage value (0-100) - PostgreSQL: NUMERIC
- **StockSymbol** (stockSymbol): Stock ticker symbol (1-5 uppercase letters, optional class suffix) - PostgreSQL: TEXT
- **ISIN** (isin): International Securities Identification Number (12 characters) - PostgreSQL: TEXT
- **CUSIP** (cusip): Committee on Uniform Security Identification Procedures (9 characters, primarily US) - PostgreSQL: TEXT
- **SEDOL** (sedol): Stock Exchange Daily Official List (7 characters, UK-based) - PostgreSQL: TEXT
- **LEI** (lei): Legal Entity Identifier (20 characters, global standard) - PostgreSQL: TEXT
- **MIC** (mic): Market Identifier Code (ISO 10383, identifies trading venues) - PostgreSQL: TEXT
- **ExchangeCode** (exchangeCode): Stock exchange code (2-6 uppercase letters) - PostgreSQL: TEXT
- **ExchangeRate** (exchangeRate): Currency exchange rate (high precision decimal) - PostgreSQL: NUMERIC

### Geographic Types
- **Coordinates** (coordinates): Geographic coordinates (lat, lng) - PostgreSQL: POINT
- **Latitude** (latitude): Latitude (-90 to 90) - PostgreSQL: NUMERIC
- **Longitude** (longitude): Longitude (-180 to 180) - PostgreSQL: NUMERIC
- **AirportCode** (airportCode): Airport code (IATA format: 3 uppercase letters) - PostgreSQL: TEXT
- **PortCode** (portCode): Port/terminal code (UN/LOCODE: 5 letters) - PostgreSQL: TEXT
- **PostalCode** (postalCode): Postal/ZIP code (international format: alphanumeric with spaces/hyphens) - PostgreSQL: TEXT

### Network Types
- **IpAddress** (ipAddress): IPv4 or IPv6 address - PostgreSQL: INET
- **MacAddress** (macAddress): MAC address - PostgreSQL: MACADDR
- **DomainName** (domainName): Domain name (RFC compliant) - PostgreSQL: TEXT
- **ApiKey** (apiKey): API key or access token (alphanumeric with hyphens/underscores) - PostgreSQL: TEXT
- **HashSHA256** (hashSHA256): SHA256 hash (64 hexadecimal characters) - PostgreSQL: TEXT
- **SemanticVersion** (semanticVersion): Semantic versioning (semver) format - PostgreSQL: TEXT

### Logistics Types
- **TrackingNumber** (trackingNumber): Shipping tracking number (8-30 alphanumeric characters) - PostgreSQL: TEXT
- **ContainerNumber** (containerNumber): Shipping container number (ISO 6346 format: 3 letters + U/J/Z + 6 digits + check digit) - PostgreSQL: TEXT
- **LicensePlate** (licensePlate): Vehicle license plate number (international format: alphanumeric with spaces/hyphens) - PostgreSQL: TEXT
- **VIN** (vin): Vehicle Identification Number (17 characters, ISO 3779/3780) - PostgreSQL: TEXT
- **FlightNumber** (flightNumber): Flight number (IATA airline code + 1-4 digits + optional letter) - PostgreSQL: TEXT
- **IBAN** (iban): International Bank Account Number (ISO 13616) - PostgreSQL: TEXT

### Content Types
- **Email** (email): Valid email address (RFC 5322 simplified) - PostgreSQL: TEXT
- **PhoneNumber** (phoneNumber): International phone number (E.164 format) - PostgreSQL: TEXT
- **Url** (url): Valid HTTP or HTTPS URL - PostgreSQL: TEXT
- **Image** (image): Image URL or path - PostgreSQL: TEXT
- **File** (file): File URL or path - PostgreSQL: TEXT

### Data Types
- **UUID** (uuid): UUID v4 - PostgreSQL: UUID
- **Color** (color): Hex color code - PostgreSQL: TEXT
- **Slug** (slug): URL-friendly slug (lowercase, hyphens) - PostgreSQL: TEXT
- **MimeType** (mimeType): MIME type (e.g., application/json, image/png) - PostgreSQL: TEXT

### Date/Time Types
- **Date** (date): Calendar date (no time) - PostgreSQL: DATE
- **DateTime** (datetime): Timestamp with timezone - PostgreSQL: TIMESTAMPTZ
- **Time** (time): Time of day (no date) - PostgreSQL: TIME
- **Duration** (duration): Time duration (interval) - PostgreSQL: INTERVAL

### Structured Types
- **Markdown** (markdown): Markdown formatted text - PostgreSQL: TEXT
- **Html** (html): HTML content (sanitized on input) - PostgreSQL: TEXT
- **JSON** (json): JSON object or array - PostgreSQL: JSONB

## Implementation Requirements

Each scalar type needs:

### GraphQL Implementation
- GraphQL scalar definition with validation
- Serialization and parsing functions
- Error handling for invalid values

### PostgreSQL Integration
- Appropriate PostgreSQL type mapping
- CHECK constraints for validation
- Index optimization support

### Python Type System
- Type markers for static typing
- Field classes with validation
- Integration with dataclasses/Pydantic

### Testing
- Unit tests for validation logic
- GraphQL serialization/parsing tests
- PostgreSQL constraint tests
- Edge case handling

## Use Cases by Category

### Enterprise Applications
- **Financial**: Trading platforms, banking, fintech
- **Logistics**: Shipping, supply chain, e-commerce
- **Global SaaS**: Multi-tenant with i18n support

### Content Management
- **Media**: Image/file validation, content types
- **Publishing**: Markdown/HTML content, slugs
- **Communication**: Email, phone number validation

### Technical Platforms
- **APIs**: Key/token validation, versioning
- **Infrastructure**: Network identifiers, geographic data
- **Security**: Hash validation, UUID handling

## Implementation Priority

### High Priority (Foundation)
1. i18n Types - Universal need for global apps
2. Content Types - Email, URL, phone validation
3. Date/Time Types - Temporal data handling
4. Data Types - UUID, JSON support

### Medium Priority (Business Logic)
5. Financial Types - Enterprise financial applications
6. Geographic Types - Location-based services
7. Network Types - Technical infrastructure

### Lower Priority (Specialized)
8. Logistics Types - Shipping/e-commerce platforms
9. Structured Types - Content management systems

## Migration Impact

This represents a **10x expansion** of FraiseQL's scalar capabilities, requiring:
- Systematic implementation following existing patterns
- Comprehensive test coverage
- Documentation updates
- Performance validation
- Backward compatibility maintenance

## References

- ISO Standards: 639-1 (languages), 4217 (currencies), 6346 (containers)
- IETF Standards: BCP 47 (locales), RFC 5322 (email)
- IANA: Timezone database
- PostgreSQL: Native types and constraints