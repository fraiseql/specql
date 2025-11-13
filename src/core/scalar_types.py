"""
Scalar Rich Type Registry

Defines all 49 built-in scalar types with:
- PostgreSQL type mapping
- FraiseQL scalar name
- Validation patterns (regex, ranges)
- Metadata for UI generation (future)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PostgreSQLType(Enum):
    """PostgreSQL native types"""

    TEXT = "TEXT"
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    NUMERIC = "NUMERIC"
    DATE = "DATE"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    TIME = "TIME"
    INTERVAL = "INTERVAL"
    INET = "INET"
    MACADDR = "MACADDR"
    UUID = "UUID"
    JSONB = "JSONB"
    POINT = "POINT"
    BOOLEAN = "BOOLEAN"


@dataclass
class ScalarTypeDef:
    """Definition of a scalar rich type"""

    # Core identity
    name: str  # "email", "phoneNumber", "money"
    postgres_type: PostgreSQLType  # PostgreSQL type
    fraiseql_scalar_name: str  # GraphQL scalar name

    validation_pattern: str | None = None  # Regex for CHECK constraint
    min_value: float | None = None
    max_value: float | None = None
    postgres_precision: tuple | None = None  # For NUMERIC(19,4)

    # Metadata
    description: str = ""
    example: str = ""

    # UI hints (future frontend generation)
    input_type: str = "text"  # HTML input type
    placeholder: str | None = None

    def get_postgres_type_with_precision(self) -> str:
        """Get PostgreSQL type with precision if applicable"""
        base = self.postgres_type.value
        if self.postgres_precision:
            return f"{base}({','.join(map(str, self.postgres_precision))})"
        return base


@dataclass
class CompositeFieldDef:
    """Definition of a field within a composite type"""

    name: str
    type_name: str
    nullable: bool = True
    description: str = ""


@dataclass
class CompositeTypeDef:
    """Definition of a composite type (stored as JSONB)"""

    name: str
    fields: dict[str, CompositeFieldDef]
    description: str = ""
    example: str = ""

    @property
    def fraiseql_type_name(self) -> str:
        """Get GraphQL object type name"""
        return self.name

    def get_jsonb_schema(self) -> dict[str, Any]:
        """Get JSON schema for validation (for Team B)"""
        properties = {}
        required = []

        for field_name, field_def in self.fields.items():
            field_schema = {"type": "string"}  # Default to string
            if field_def.type_name in ["integer", "bigint"]:
                field_schema = {"type": "integer"}
            elif field_def.type_name in ["float", "money", "percentage"]:
                field_schema = {"type": "number"}
            elif field_def.type_name == "boolean":
                field_schema = {"type": "boolean"}

            if not field_def.nullable:
                required.append(field_name)

            properties[field_name] = field_schema

        schema = {"type": "object", "properties": properties}

        if required:
            schema["required"] = required

        return schema


# Type aliases for backward compatibility and stdlib support
SCALAR_TYPE_ALIASES = {
    "phone": "phoneNumber",  # stdlib uses 'phone', registry has 'phoneNumber'
}

# Registry of all built-in scalar types
SCALAR_TYPES: dict[str, ScalarTypeDef] = {
    # String-based types
    "email": ScalarTypeDef(
        name="email",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Email",
        validation_pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Valid email address (RFC 5322 simplified)",
        example="user@example.com",
        input_type="email",
        placeholder="user@example.com",
    ),
    "phoneNumber": ScalarTypeDef(
        name="phoneNumber",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="PhoneNumber",
        validation_pattern=r"^\+[1-9]\d{1,14}$",  # E.164 format
        description="International phone number (E.164 format)",
        example="+14155551234",
        input_type="tel",
        placeholder="+1 (415) 555-1234",
    ),
    "url": ScalarTypeDef(
        name="url",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Url",
        validation_pattern=r"^https?://[^\s/$.?#].[^\s]*$",
        description="Valid HTTP or HTTPS URL",
        example="https://example.com",
        input_type="url",
        placeholder="https://example.com",
    ),
    "slug": ScalarTypeDef(
        name="slug",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Slug",
        validation_pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-friendly identifier (lowercase with hyphens, validated format)",
        example="my-article-slug",
        placeholder="my-article-slug",
    ),
    "markdown": ScalarTypeDef(
        name="markdown",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Markdown",
        description="Markdown formatted text",
        example="# Heading\n\nParagraph with **bold**",
        input_type="textarea",
        placeholder="Enter markdown...",
    ),
    "html": ScalarTypeDef(
        name="html",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Html",
        description="HTML content (sanitized on input)",
        example="<p>Hello <strong>world</strong></p>",
        input_type="textarea",
        placeholder="<p>Enter HTML...</p>",
    ),
    # Network types
    "ipAddress": ScalarTypeDef(
        name="ipAddress",
        postgres_type=PostgreSQLType.INET,
        fraiseql_scalar_name="IpAddress",
        description="IPv4 or IPv6 address",
        example="192.168.1.1",
        input_type="text",
        placeholder="192.168.1.1",
    ),
    "macAddress": ScalarTypeDef(
        name="macAddress",
        postgres_type=PostgreSQLType.MACADDR,
        fraiseql_scalar_name="MacAddress",
        description="MAC address",
        example="08:00:2b:01:02:03",
        input_type="text",
        placeholder="08:00:2b:01:02:03",
    ),
    # Numeric types
    "money": ScalarTypeDef(
        name="money",
        postgres_type=PostgreSQLType.NUMERIC,
        postgres_precision=(19, 4),
        fraiseql_scalar_name="Money",
        min_value=0.0,
        description="Monetary amount (no currency, use MoneyAmount composite for currency)",
        example="1234.56",
        input_type="number",
        placeholder="0.00",
    ),
    "percentage": ScalarTypeDef(
        name="percentage",
        postgres_type=PostgreSQLType.NUMERIC,
        postgres_precision=(5, 2),
        fraiseql_scalar_name="Percentage",
        min_value=0.0,
        max_value=100.0,
        description="Percentage value (0-100)",
        example="75.5",
        input_type="number",
        placeholder="0.00",
    ),
    # Date/Time types
    "date": ScalarTypeDef(
        name="date",
        postgres_type=PostgreSQLType.DATE,
        fraiseql_scalar_name="Date",
        description="Calendar date (no time)",
        example="2025-11-08",
        input_type="date",
    ),
    "datetime": ScalarTypeDef(
        name="datetime",
        postgres_type=PostgreSQLType.TIMESTAMPTZ,
        fraiseql_scalar_name="DateTime",
        description="Timestamp with timezone",
        example="2025-11-08T14:30:00Z",
        input_type="datetime-local",
    ),
    "time": ScalarTypeDef(
        name="time",
        postgres_type=PostgreSQLType.TIME,
        fraiseql_scalar_name="Time",
        description="Time of day (no date)",
        example="14:30:00",
        input_type="time",
    ),
    "duration": ScalarTypeDef(
        name="duration",
        postgres_type=PostgreSQLType.INTERVAL,
        fraiseql_scalar_name="Duration",
        description="Time duration (interval)",
        example="2 hours 30 minutes",
        input_type="text",
        placeholder="2 hours 30 minutes",
    ),
    # Geographic types
    "coordinates": ScalarTypeDef(
        name="coordinates",
        postgres_type=PostgreSQLType.POINT,
        fraiseql_scalar_name="Coordinates",
        description="Geographic coordinates (lat, lng)",
        example="(37.7749, -122.4194)",
        input_type="text",
        placeholder="(37.7749, -122.4194)",
    ),
    "latitude": ScalarTypeDef(
        name="latitude",
        postgres_type=PostgreSQLType.NUMERIC,
        postgres_precision=(10, 8),
        fraiseql_scalar_name="Latitude",
        min_value=-90.0,
        max_value=90.0,
        description="Latitude (-90 to 90)",
        example="37.7749",
        input_type="number",
        placeholder="37.7749",
    ),
    "longitude": ScalarTypeDef(
        name="longitude",
        postgres_type=PostgreSQLType.NUMERIC,
        postgres_precision=(11, 8),
        fraiseql_scalar_name="Longitude",
        min_value=-180.0,
        max_value=180.0,
        description="Longitude (-180 to 180)",
        example="-122.4194",
        input_type="number",
        placeholder="-122.4194",
    ),
    # Media types
    "image": ScalarTypeDef(
        name="image",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Image",
        description="Image URL or path",
        example="https://example.com/image.jpg",
        input_type="url",
        placeholder="https://example.com/image.jpg",
    ),
    "file": ScalarTypeDef(
        name="file",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="File",
        description="File URL or path",
        example="https://example.com/document.pdf",
        input_type="url",
        placeholder="https://example.com/document.pdf",
    ),
    "color": ScalarTypeDef(
        name="color",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Color",
        validation_pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code",
        example="#FF5733",
        input_type="color",
        placeholder="#FF5733",
    ),
    "hex": ScalarTypeDef(
        name="hex",
        postgres_type=PostgreSQLType.INTEGER,
        fraiseql_scalar_name="Hex",
        validation_pattern=r"^(?:0[xX])?[0-9A-Fa-f]{1,2}$",  # 0x prefix optional, 1-2 hex digits (0-FF)
        min_value=0,
        max_value=255,  # FF in hex
        description="Hexadecimal number (0-FF, with optional 0x prefix)",
        example="FF",
        input_type="text",
        placeholder="0F",
    ),
    # Identifier types
    "uuid": ScalarTypeDef(
        name="uuid",
        postgres_type=PostgreSQLType.UUID,
        fraiseql_scalar_name="UUID",
        description="UUID v4",
        example="550e8400-e29b-41d4-a716-446655440000",
        input_type="text",
        placeholder="550e8400-e29b-41d4-a716-446655440000",
    ),
    # i18n types
    "languageCode": ScalarTypeDef(
        name="languageCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="LanguageCode",
        validation_pattern=r"^[a-z]{2}$",  # ISO 639-1: exactly 2 lowercase letters
        description="ISO 639-1 two-letter language code",
        example="en",
        input_type="text",
        placeholder="en",
    ),
    "localeCode": ScalarTypeDef(
        name="localeCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="LocaleCode",
        validation_pattern=r"^[a-z]{2}(-[A-Z]{2})?$",  # BCP 47: language or language-REGION
        description="BCP 47 locale code for regional formatting",
        example="en-US",
        input_type="text",
        placeholder="en-US",
    ),
    "timezone": ScalarTypeDef(
        name="timezone",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Timezone",
        validation_pattern=r"^[A-Z][a-zA-Z_]+(/[A-Z][a-zA-Z_]+){1,2}$",  # IANA format
        description="IANA timezone database identifier",
        example="America/New_York",
        input_type="text",
        placeholder="America/New_York",
    ),
    # Business/financial types
    "currencyCode": ScalarTypeDef(
        name="currencyCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="CurrencyCode",
        validation_pattern=r"^[A-Z]{3}$",  # ISO 4217: exactly 3 uppercase letters
        description="ISO 4217 currency code",
        example="USD",
        input_type="text",
        placeholder="USD",
    ),
    "countryCode": ScalarTypeDef(
        name="countryCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="CountryCode",
        validation_pattern=r"^[A-Z]{2}$",  # ISO 3166-1 alpha-2: exactly 2 uppercase letters
        description="ISO 3166-1 alpha-2 country code",
        example="US",
        input_type="text",
        placeholder="US",
    ),
    # Technical types
    "mimeType": ScalarTypeDef(
        name="mimeType",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="MimeType",
        validation_pattern=r"^[a-zA-Z][a-zA-Z0-9][a-zA-Z0-9\!\#\$\&\-\^]*\/[a-zA-Z0-9][a-zA-Z0-9\!\#\$\&\-\^]*$",
        description="MIME type (e.g., application/json, image/png)",
        example="application/json",
        input_type="text",
        placeholder="application/json",
    ),
    "semanticVersion": ScalarTypeDef(
        name="semanticVersion",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="SemanticVersion",
        validation_pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
        description="Semantic versioning (semver) format",
        example="1.2.3",
        input_type="text",
        placeholder="1.0.0",
    ),
    # Financial/stocks types
    "stockSymbol": ScalarTypeDef(
        name="stockSymbol",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="StockSymbol",
        validation_pattern=r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$",  # Stock ticker format (e.g., AAPL, BRK.A)
        description="Stock ticker symbol (1-5 uppercase letters, optional class suffix)",
        example="AAPL",
        input_type="text",
        placeholder="AAPL",
    ),
    "isin": ScalarTypeDef(
        name="isin",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="ISIN",
        validation_pattern=r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",  # ISIN format: 2 letters + 9 alphanum + 1 digit
        description="International Securities Identification Number (12 characters)",
        example="US0378331005",
        input_type="text",
        placeholder="US0378331005",
    ),
    "cusip": ScalarTypeDef(
        name="cusip",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="CUSIP",
        validation_pattern=r"^[0-9]{6}[0-9A-Z]{2}[0-9]$",  # CUSIP format: 6 digits + 2 alphanum + 1 digit
        description="Committee on Uniform Security Identification Procedures (9 characters, primarily US)",
        example="037833100",
        input_type="text",
        placeholder="037833100",
    ),
    "sedol": ScalarTypeDef(
        name="sedol",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="SEDOL",
        validation_pattern=r"^[0-9A-Z]{6}[0-9]$",  # SEDOL format: 6 alphanum + 1 check digit
        description="Stock Exchange Daily Official List (7 characters, UK-based)",
        example="B02LC96",
        input_type="text",
        placeholder="B02LC96",
    ),
    "lei": ScalarTypeDef(
        name="lei",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="LEI",
        validation_pattern=r"^[0-9A-Z]{18}[0-9]{2}$",  # LEI format: 18 alphanum + 2 check digits
        description="Legal Entity Identifier (20 characters, global standard)",
        example="54930084UKLVMY22DS16",
        input_type="text",
        placeholder="54930084UKLVMY22DS16",
    ),
    "mic": ScalarTypeDef(
        name="mic",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="MIC",
        validation_pattern=r"^[A-Z0-9]{4}$",  # MIC format: 4 characters
        description="Market Identifier Code (ISO 10383, identifies trading venues)",
        example="XNYS",
        input_type="text",
        placeholder="XNYS",
    ),
    "exchangeCode": ScalarTypeDef(
        name="exchangeCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="ExchangeCode",
        validation_pattern=r"^[A-Z]{2,6}$",  # Exchange codes (NYSE, NASDAQ, LSE, etc.)
        description="Stock exchange code (2-6 uppercase letters)",
        example="NYSE",
        input_type="text",
        placeholder="NYSE",
    ),
    # NOTE: forexPair and cryptoPair removed in favor of ref(TradingPair) entities
    # This provides better normalization and flexibility for financial data
    "exchangeRate": ScalarTypeDef(
        name="exchangeRate",
        postgres_type=PostgreSQLType.NUMERIC,
        postgres_precision=(19, 8),  # High precision for exchange rates
        fraiseql_scalar_name="ExchangeRate",
        min_value=0.0,
        description="Currency exchange rate (high precision decimal)",
        example="1.23456789",
        input_type="number",
        placeholder="1.23456789",
    ),
    # Logistics/shipping types
    "trackingNumber": ScalarTypeDef(
        name="trackingNumber",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="TrackingNumber",
        validation_pattern=r"^[A-Z0-9]{8,30}$",  # Generic tracking number format
        description="Shipping tracking number (8-30 alphanumeric characters)",
        example="1Z999AA1234567890",
        input_type="text",
        placeholder="1Z999AA1234567890",
    ),
    "containerNumber": ScalarTypeDef(
        name="containerNumber",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="ContainerNumber",
        validation_pattern=r"^[A-Z]{3}[UJZ]\d{6}\d$",  # ISO 6346 container number format
        description="Shipping container number (ISO 6346 format: 3 letters + U/J/Z + 6 digits + check digit)",
        example="MSKU1234567",
        input_type="text",
        placeholder="MSKU1234567",
    ),
    "licensePlate": ScalarTypeDef(
        name="licensePlate",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="LicensePlate",
        validation_pattern=r"^[A-Z0-9\s\-]{1,20}$",  # International license plate format (letters, numbers, spaces, hyphens)
        description="Vehicle license plate number (international format: alphanumeric with spaces/hyphens)",
        example="ABC-123",
        input_type="text",
        placeholder="ABC-123",
    ),
    "vin": ScalarTypeDef(
        name="vin",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="VIN",
        validation_pattern=r"^[A-HJ-NPR-Z0-9]{17}$",  # VIN format: 17 characters, no I,O,Q
        description="Vehicle Identification Number (17 characters, ISO 3779/3780)",
        example="1HGCM82633A123456",
        input_type="text",
        placeholder="1HGCM82633A123456",
    ),
    "flightNumber": ScalarTypeDef(
        name="flightNumber",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="FlightNumber",
        validation_pattern=r"^[A-Z]{2,3}\d{1,4}[A-Z]?$",  # Airline code + number + optional suffix
        description="Flight number (IATA airline code + 1-4 digits + optional letter)",
        example="AA1234",
        input_type="text",
        placeholder="AA1234",
    ),
    "portCode": ScalarTypeDef(
        name="portCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="PortCode",
        validation_pattern=r"^[A-Z]{5}$",  # UN/LOCODE format: 5 letters
        description="Port/terminal code (UN/LOCODE: 5 letters)",
        example="USNYC",
        input_type="text",
        placeholder="USNYC",
    ),
    "postalCode": ScalarTypeDef(
        name="postalCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="PostalCode",
        validation_pattern=r"^[A-Z0-9\s\-]{3,12}$",  # International postal code format
        description="Postal/ZIP code (international format: alphanumeric with spaces/hyphens)",
        example="12345",
        input_type="text",
        placeholder="12345",
    ),
    # Airport codes (separate from port codes)
    "airportCode": ScalarTypeDef(
        name="airportCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="AirportCode",
        validation_pattern=r"^[A-Z]{3}$",  # IATA airport code: 3 letters
        description="Airport code (IATA format: 3 uppercase letters)",
        example="JFK",
        input_type="text",
        placeholder="JFK",
    ),
    # Domain names and web identifiers
    "domainName": ScalarTypeDef(
        name="domainName",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="DomainName",
        validation_pattern=r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$",
        description="Domain name (RFC compliant)",
        example="example.com",
        input_type="text",
        placeholder="example.com",
    ),
    # API keys and tokens
    "apiKey": ScalarTypeDef(
        name="apiKey",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="ApiKey",
        validation_pattern=r"^[A-Za-z0-9_\-]{20,128}$",  # API key format
        description="API key or access token (alphanumeric with hyphens/underscores)",
        example="sk-1234567890abcdef",
        input_type="password",
        placeholder="sk-...",
    ),
    # Hash values
    "hashSHA256": ScalarTypeDef(
        name="hashSHA256",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="HashSHA256",
        validation_pattern=r"^[a-f0-9]{64}$",  # SHA256 hex format
        description="SHA256 hash (64 hexadecimal characters)",
        example="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
        input_type="text",
        placeholder="a665a459...",
    ),
    # IBAN (International Bank Account Number)
    "iban": ScalarTypeDef(
        name="iban",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="IBAN",
        validation_pattern=r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$",  # IBAN format
        description="International Bank Account Number (ISO 13616)",
        example="GB29 NWBK 6016 1331 9268 19",
        input_type="text",
        placeholder="GB29 NWBK 6016 1331 9268 19",
    ),
    # SWIFT/BIC codes
    "swiftCode": ScalarTypeDef(
        name="swiftCode",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="SwiftCode",
        validation_pattern=r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$",  # SWIFT/BIC format
        description="SWIFT/BIC bank identifier code (8 or 11 characters)",
        example="CHASUS33",
        input_type="text",
        placeholder="CHASUS33",
    ),
    # NOTE: "boolean" is a BASIC type, not a scalar type
    # It is handled by _parse_basic_field() in the parser
    # Structured types
    "json": ScalarTypeDef(
        name="json",
        postgres_type=PostgreSQLType.JSONB,
        fraiseql_scalar_name="JSON",
        description="JSON object or array",
        example='{"key": "value"}',
        input_type="textarea",
        placeholder='{"key": "value"}',
    ),
}


# Registry of all built-in composite types (stored as JSONB)
COMPOSITE_TYPES: dict[str, CompositeTypeDef] = {
    "SimpleAddress": CompositeTypeDef(
        name="SimpleAddress",
        description="Basic address information",
        example='{"street": "123 Main St", "city": "Anytown", "state": "CA", "zipCode": "12345"}',
        fields={
            "street": CompositeFieldDef(
                "street", "text", nullable=False, description="Street address"
            ),
            "city": CompositeFieldDef("city", "text", nullable=False, description="City name"),
            "state": CompositeFieldDef(
                "state", "text", nullable=False, description="State or province"
            ),
            "zipCode": CompositeFieldDef(
                "zipCode", "text", nullable=False, description="Postal code"
            ),
            "country": CompositeFieldDef(
                "country", "text", nullable=True, description="Country (defaults to US)"
            ),
        },
    ),
    "MoneyAmount": CompositeTypeDef(
        name="MoneyAmount",
        description="Monetary amount with currency",
        example='{"amount": 99.99, "currency": "USD"}',
        fields={
            "amount": CompositeFieldDef(
                "amount", "money", nullable=False, description="Monetary amount"
            ),
            "currency": CompositeFieldDef(
                "currency", "text", nullable=False, description="Currency code (ISO 4217)"
            ),
        },
    ),
    "PersonName": CompositeTypeDef(
        name="PersonName",
        description="Person's full name",
        example='{"firstName": "John", "lastName": "Doe", "middleName": "Q"}',
        fields={
            "firstName": CompositeFieldDef(
                "firstName", "text", nullable=False, description="First name"
            ),
            "lastName": CompositeFieldDef(
                "lastName", "text", nullable=False, description="Last name"
            ),
            "middleName": CompositeFieldDef(
                "middleName", "text", nullable=True, description="Middle name or initial"
            ),
            "title": CompositeFieldDef(
                "title", "text", nullable=True, description="Title (Mr, Mrs, Dr, etc.)"
            ),
            "suffix": CompositeFieldDef(
                "suffix", "text", nullable=True, description="Suffix (Jr, Sr, III, etc.)"
            ),
        },
    ),
    "ContactInfo": CompositeTypeDef(
        name="ContactInfo",
        description="Contact information",
        example='{"email": "john@example.com", "phone": "+14155551234", "website": "https://example.com"}',
        fields={
            "email": CompositeFieldDef(
                "email", "email", nullable=True, description="Email address"
            ),
            "phone": CompositeFieldDef(
                "phone", "phoneNumber", nullable=True, description="Phone number"
            ),
            "website": CompositeFieldDef(
                "website", "url", nullable=True, description="Website URL"
            ),
        },
    ),
    "Coordinates": CompositeTypeDef(
        name="Coordinates",
        description="Geographic coordinates",
        example='{"latitude": 37.7749, "longitude": -122.4194}',
        fields={
            "latitude": CompositeFieldDef(
                "latitude", "latitude", nullable=False, description="Latitude (-90 to 90)"
            ),
            "longitude": CompositeFieldDef(
                "longitude", "longitude", nullable=False, description="Longitude (-180 to 180)"
            ),
        },
    ),
    "TimeRange": CompositeTypeDef(
        name="TimeRange",
        description="Time range with start and end",
        example='{"start": "09:00:00", "end": "17:00:00"}',
        fields={
            "start": CompositeFieldDef("start", "time", nullable=False, description="Start time"),
            "end": CompositeFieldDef("end", "time", nullable=False, description="End time"),
        },
    ),
    "DateRange": CompositeTypeDef(
        name="DateRange",
        description="Date range with start and end",
        example='{"start": "2025-01-01", "end": "2025-12-31"}',
        fields={
            "start": CompositeFieldDef("start", "date", nullable=False, description="Start date"),
            "end": CompositeFieldDef("end", "date", nullable=False, description="End date"),
        },
    ),
    "PhoneNumber": CompositeTypeDef(
        name="PhoneNumber",
        description="Phone number with country code",
        example='{"countryCode": "+1", "number": "4155551234"}',
        fields={
            "countryCode": CompositeFieldDef(
                "countryCode", "text", nullable=False, description="Country code"
            ),
            "number": CompositeFieldDef(
                "number", "text", nullable=False, description="Phone number"
            ),
        },
    ),
    "EmailAddress": CompositeTypeDef(
        name="EmailAddress",
        description="Email address with display name",
        example='{"address": "john@example.com", "displayName": "John Doe"}',
        fields={
            "address": CompositeFieldDef(
                "address", "email", nullable=False, description="Email address"
            ),
            "displayName": CompositeFieldDef(
                "displayName", "text", nullable=True, description="Display name"
            ),
        },
    ),
    "URL": CompositeTypeDef(
        name="URL",
        description="URL with components",
        example='{"protocol": "https", "host": "example.com", "path": "/page", "query": "q=search"}',
        fields={
            "protocol": CompositeFieldDef(
                "protocol", "text", nullable=False, description="Protocol (http, https)"
            ),
            "host": CompositeFieldDef("host", "text", nullable=False, description="Host/domain"),
            "path": CompositeFieldDef("path", "text", nullable=True, description="Path component"),
            "query": CompositeFieldDef("query", "text", nullable=True, description="Query string"),
            "fragment": CompositeFieldDef(
                "fragment", "text", nullable=True, description="Fragment/hash"
            ),
        },
    ),
    "Color": CompositeTypeDef(
        name="Color",
        description="Color in RGB or HSL format",
        example='{"red": 255, "green": 128, "blue": 0, "alpha": 1.0}',
        fields={
            "red": CompositeFieldDef(
                "red", "integer", nullable=False, description="Red component (0-255)"
            ),
            "green": CompositeFieldDef(
                "green", "integer", nullable=False, description="Green component (0-255)"
            ),
            "blue": CompositeFieldDef(
                "blue", "integer", nullable=False, description="Blue component (0-255)"
            ),
            "alpha": CompositeFieldDef(
                "alpha", "float", nullable=True, description="Alpha/transparency (0.0-1.0)"
            ),
        },
    ),
    "Dimensions": CompositeTypeDef(
        name="Dimensions",
        description="Physical dimensions",
        example='{"width": 10.5, "height": 8.0, "depth": 2.0, "unit": "inches"}',
        fields={
            "width": CompositeFieldDef(
                "width", "float", nullable=False, description="Width measurement"
            ),
            "height": CompositeFieldDef(
                "height", "float", nullable=False, description="Height measurement"
            ),
            "depth": CompositeFieldDef(
                "depth", "float", nullable=True, description="Depth measurement"
            ),
            "unit": CompositeFieldDef(
                "unit", "text", nullable=False, description="Unit of measurement"
            ),
        },
    ),
    "BusinessHours": CompositeTypeDef(
        name="BusinessHours",
        description="Business hours for each day of the week",
        example='{"monday": {"start": "09:00", "end": "17:00"}, "tuesday": {"start": "09:00", "end": "17:00"}}',
        fields={
            "monday": CompositeFieldDef(
                "monday", "TimeRange", nullable=True, description="Monday hours"
            ),
            "tuesday": CompositeFieldDef(
                "tuesday", "TimeRange", nullable=True, description="Tuesday hours"
            ),
            "wednesday": CompositeFieldDef(
                "wednesday", "TimeRange", nullable=True, description="Wednesday hours"
            ),
            "thursday": CompositeFieldDef(
                "thursday", "TimeRange", nullable=True, description="Thursday hours"
            ),
            "friday": CompositeFieldDef(
                "friday", "TimeRange", nullable=True, description="Friday hours"
            ),
            "saturday": CompositeFieldDef(
                "saturday", "TimeRange", nullable=True, description="Saturday hours"
            ),
            "sunday": CompositeFieldDef(
                "sunday", "TimeRange", nullable=True, description="Sunday hours"
            ),
        },
    ),
    # Additional composite types for completeness
    "Contact": CompositeTypeDef(
        name="Contact",
        description="Contact information (embedded, no FK to User)",
        fields={
            "name": CompositeFieldDef("name", "text", nullable=False, description="Full name"),
            "email": CompositeFieldDef(
                "email", "email", nullable=True, description="Email address"
            ),
            "phone": CompositeFieldDef(
                "phone", "phoneNumber", nullable=True, description="Primary phone number"
            ),
            "alternate_phone": CompositeFieldDef(
                "alternate_phone",
                "phoneNumber",
                nullable=True,
                description="Secondary phone number",
            ),
            "relationship": CompositeFieldDef(
                "relationship", "text", nullable=True, description="Relationship to primary contact"
            ),
            "company": CompositeFieldDef(
                "company", "text", nullable=True, description="Company name"
            ),
            "job_title": CompositeFieldDef(
                "job_title", "text", nullable=True, description="Job title"
            ),
            "notes": CompositeFieldDef(
                "notes", "markdown", nullable=True, description="Additional notes"
            ),
        },
        example='{"name": "Jane Smith", "email": "jane.smith@example.com", "phone": "+14155551234", "relationship": "Manager", "company": "Acme Corp", "job_title": "VP of Operations"}',
    ),
    "Company": CompositeTypeDef(
        name="Company",
        description="Company information with nested address",
        fields={
            "name": CompositeFieldDef("name", "text", nullable=False, description="Company name"),
            "legal_name": CompositeFieldDef(
                "legal_name", "text", nullable=True, description="Legal entity name"
            ),
            "tax_id": CompositeFieldDef(
                "tax_id", "text", nullable=True, description="Tax identification number"
            ),
            "website": CompositeFieldDef(
                "website", "url", nullable=True, description="Company website"
            ),
            "industry": CompositeFieldDef(
                "industry", "text", nullable=True, description="Industry sector"
            ),
            "employee_count": CompositeFieldDef(
                "employee_count", "integer", nullable=True, description="Number of employees"
            ),
            # NESTED COMPOSITE!
            "address": CompositeFieldDef(
                "address", "SimpleAddress", nullable=True, description="Company address"
            ),
            "phone": CompositeFieldDef(
                "phone", "phoneNumber", nullable=True, description="Main phone number"
            ),
        },
        example='{"name": "Acme Corporation", "legal_name": "Acme Corp Inc.", "tax_id": "12-3456789", "website": "https://acme.com", "industry": "Manufacturing", "employee_count": 500, "address": {"street": "123 Business St", "city": "Business City", "state": "CA", "zipCode": "12345", "country": "USA"}, "phone": "+14155550000"}',
    ),
    "GeoLocation": CompositeTypeDef(
        name="GeoLocation",
        description="Rich geographic location with accuracy and timestamp",
        fields={
            "latitude": CompositeFieldDef(
                "latitude", "latitude", nullable=False, description="Latitude (-90 to 90)"
            ),
            "longitude": CompositeFieldDef(
                "longitude", "longitude", nullable=False, description="Longitude (-180 to 180)"
            ),
            "altitude": CompositeFieldDef(
                "altitude", "integer", nullable=True, description="Altitude in meters"
            ),
            "accuracy": CompositeFieldDef(
                "accuracy", "integer", nullable=True, description="Accuracy in meters"
            ),
            "heading": CompositeFieldDef(
                "heading", "integer", nullable=True, description="Heading in degrees (0-359)"
            ),
            "speed": CompositeFieldDef("speed", "float", nullable=True, description="Speed in m/s"),
            "timestamp": CompositeFieldDef(
                "timestamp", "datetime", nullable=False, description="Location timestamp"
            ),
        },
        example='{"latitude": 37.7749, "longitude": -122.4194, "altitude": 15, "accuracy": 5, "heading": 90, "speed": 2.5, "timestamp": "2025-11-08T14:30:00Z"}',
    ),
    "CurrencyExchange": CompositeTypeDef(
        name="CurrencyExchange",
        description="Currency exchange rate information",
        fields={
            "baseCurrency": CompositeFieldDef(
                "baseCurrency", "currencyCode", nullable=False, description="Base currency code"
            ),
            "quoteCurrency": CompositeFieldDef(
                "quoteCurrency", "currencyCode", nullable=False, description="Quote currency code"
            ),
            "rate": CompositeFieldDef(
                "rate", "exchangeRate", nullable=False, description="Exchange rate (base to quote)"
            ),
            "timestamp": CompositeFieldDef(
                "timestamp", "datetime", nullable=False, description="Rate timestamp"
            ),
            "source": CompositeFieldDef(
                "source", "text", nullable=True, description="Data source/provider"
            ),
        },
        example='{"baseCurrency": "USD", "quoteCurrency": "EUR", "rate": 0.85, "timestamp": "2025-11-08T14:30:00Z", "source": "ECB"}',
    ),
}


def get_scalar_type(type_name: str) -> ScalarTypeDef | None:
    """Get scalar type definition by name (resolving aliases)"""
    # Check direct match first
    if type_name in SCALAR_TYPES:
        return SCALAR_TYPES[type_name]

    # Check aliases
    if type_name in SCALAR_TYPE_ALIASES:
        alias_target = SCALAR_TYPE_ALIASES[type_name]
        return SCALAR_TYPES.get(alias_target)

    return None


def is_scalar_type(type_name: str) -> bool:
    """Check if type name is a registered scalar type (including aliases)"""
    return type_name in SCALAR_TYPES or type_name in SCALAR_TYPE_ALIASES


def get_composite_type(type_name: str) -> CompositeTypeDef | None:
    """Get composite type definition by name"""
    return COMPOSITE_TYPES.get(type_name)


def is_composite_type(type_name: str) -> bool:
    """Check if type name is a registered composite type"""
    return type_name in COMPOSITE_TYPES


def is_rich_type(type_name: str) -> bool:
    """Check if type name is any rich type (scalar or composite)"""
    return is_scalar_type(type_name) or is_composite_type(type_name)
