import pytest
from src.core.scalar_types import SCALAR_TYPES, get_scalar_type, is_scalar_type


def test_scalar_types_registry_complete():
    """Ensure all 50 scalar types are registered (22 original + 3 i18n + 4 business + 5 finance + 6 logistics + 1 postal + 9 additional)"""
    assert len(SCALAR_TYPES) >= 50

    required_types = [
        "email",
        "phoneNumber",
        "url",
        "slug",
        "markdown",
        "html",
        "ipAddress",
        "macAddress",
        "money",
        "percentage",
        "date",
        "datetime",
        "time",
        "duration",
        "coordinates",
        "latitude",
        "longitude",
        "image",
        "file",
        "color",
        "uuid",
        "json",
        # i18n types
        "languageCode",
        "localeCode",
        "timezone",
        # business/financial types
        "currencyCode",
        "countryCode",
        # technical types
        "mimeType",
        "semanticVersion",
        # financial/stocks types
        "stockSymbol",
        "isin",
        "cusip",
        "sedol",
        "lei",
        "mic",
        "exchangeCode",
        "exchangeRate",
        # logistics/shipping types
        "trackingNumber",
        "containerNumber",
        "licensePlate",
        "vin",
        "flightNumber",
        "portCode",
        "postalCode",
        # Note: "boolean" is NOT a scalar type - it's a basic type
        # handled by _parse_basic_field() in the parser
    ]

    for type_name in required_types:
        assert type_name in SCALAR_TYPES, f"Missing scalar type: {type_name}"


def test_email_scalar_definition():
    """Test email scalar type definition"""
    email = get_scalar_type("email")

    assert email is not None
    assert email.name == "email"
    assert email.postgres_type.value == "TEXT"
    assert email.fraiseql_scalar_name == "Email"
    assert email.validation_pattern is not None
    assert "@" in email.validation_pattern
    assert email.input_type == "email"


def test_money_scalar_with_precision():
    """Test money scalar type with NUMERIC precision"""
    money = get_scalar_type("money")

    assert money is not None
    assert money.postgres_type.value == "NUMERIC"
    assert money.postgres_precision == (19, 4)
    assert money.get_postgres_type_with_precision() == "NUMERIC(19,4)"
    assert money.min_value == 0.0


def test_latitude_range_validation():
    """Test latitude has min/max range"""
    lat = get_scalar_type("latitude")

    assert lat is not None
    assert lat.min_value == -90.0
    assert lat.max_value == 90.0


def test_is_scalar_type_helper():
    """Test is_scalar_type helper function"""
    assert is_scalar_type("email") is True
    assert is_scalar_type("money") is True
    assert is_scalar_type("not_a_type") is False


def test_phone_number_validation_pattern():
    """Test phone number has E.164 validation pattern"""
    phone = get_scalar_type("phoneNumber")

    assert phone is not None
    assert phone.validation_pattern is not None
    assert phone.validation_pattern.startswith("^")
    assert phone.validation_pattern.endswith("$")
    assert "+" in phone.validation_pattern


def test_color_hex_validation():
    """Test color type has hex validation pattern"""
    color = get_scalar_type("color")

    assert color is not None
    assert color.validation_pattern is not None
    assert "#[0-9A-Fa-f]{6}" in color.validation_pattern


def test_uuid_type_mapping():
    """Test UUID type maps to PostgreSQL UUID"""
    uuid_type = get_scalar_type("uuid")

    assert uuid_type is not None
    assert uuid_type.postgres_type.value == "UUID"
    assert uuid_type.fraiseql_scalar_name == "UUID"


def test_json_type_mapping():
    """Test JSON type maps to PostgreSQL JSONB"""
    json_type = get_scalar_type("json")

    assert json_type is not None
    assert json_type.postgres_type.value == "JSONB"
    assert json_type.fraiseql_scalar_name == "JSON"


def test_geographic_types_precision():
    """Test geographic types have appropriate precision"""
    lat = get_scalar_type("latitude")
    lng = get_scalar_type("longitude")

    assert lat.postgres_precision == (10, 8)
    assert lng.postgres_precision == (11, 8)

    assert lat.get_postgres_type_with_precision() == "NUMERIC(10,8)"
    assert lng.get_postgres_type_with_precision() == "NUMERIC(11,8)"


def test_percentage_range():
    """Test percentage has 0-100 range"""
    pct = get_scalar_type("percentage")

    assert pct is not None
    assert pct.min_value == 0.0
    assert pct.max_value == 100.0
    assert pct.postgres_precision == (5, 2)


def test_network_types():
    """Test network types map correctly"""
    ip = get_scalar_type("ipAddress")
    mac = get_scalar_type("macAddress")

    assert ip.postgres_type.value == "INET"
    assert mac.postgres_type.value == "MACADDR"


def test_datetime_types():
    """Test date/time types map correctly"""
    date = get_scalar_type("date")
    datetime = get_scalar_type("datetime")
    time = get_scalar_type("time")
    duration = get_scalar_type("duration")

    assert date.postgres_type.value == "DATE"
    assert datetime.postgres_type.value == "TIMESTAMPTZ"
    assert time.postgres_type.value == "TIME"
    assert duration.postgres_type.value == "INTERVAL"


def test_i18n_scalar_types():
    """Test i18n scalar types are properly defined"""
    language_code = get_scalar_type("languageCode")
    locale_code = get_scalar_type("localeCode")
    timezone = get_scalar_type("timezone")

    # All should exist
    assert language_code is not None
    assert locale_code is not None
    assert timezone is not None

    # All should map to TEXT in PostgreSQL
    assert language_code.postgres_type.value == "TEXT"
    assert locale_code.postgres_type.value == "TEXT"
    assert timezone.postgres_type.value == "TEXT"

    # Should map to correct FraiseQL scalars
    assert language_code.fraiseql_scalar_name == "LanguageCode"
    assert locale_code.fraiseql_scalar_name == "LocaleCode"
    assert timezone.fraiseql_scalar_name == "Timezone"


def test_language_code_validation():
    """Test language code validation pattern"""
    language_code = get_scalar_type("languageCode")

    assert language_code.validation_pattern == r"^[a-z]{2}$"
    assert language_code.description == "ISO 639-1 two-letter language code"
    assert language_code.example == "en"
    assert language_code.input_type == "text"
    assert language_code.placeholder == "en"


def test_locale_code_validation():
    """Test locale code validation pattern"""
    locale_code = get_scalar_type("localeCode")

    assert locale_code.validation_pattern == r"^[a-z]{2}(-[A-Z]{2})?$"
    assert locale_code.description == "BCP 47 locale code for regional formatting"
    assert locale_code.example == "en-US"
    assert locale_code.input_type == "text"
    assert locale_code.placeholder == "en-US"


def test_timezone_validation():
    """Test timezone validation pattern"""
    timezone = get_scalar_type("timezone")

    assert timezone.validation_pattern == r"^[A-Z][a-zA-Z_]+(/[A-Z][a-zA-Z_]+){1,2}$"
    assert timezone.description == "IANA timezone database identifier"
    assert timezone.example == "America/New_York"
    assert timezone.input_type == "text"
    assert timezone.placeholder == "America/New_York"


def test_business_scalar_types():
    """Test business/financial scalar types are properly defined"""
    currency_code = get_scalar_type("currencyCode")
    country_code = get_scalar_type("countryCode")
    mime_type = get_scalar_type("mimeType")
    semantic_version = get_scalar_type("semanticVersion")

    # All should exist
    assert currency_code is not None
    assert country_code is not None
    assert mime_type is not None
    assert semantic_version is not None

    # All should map to TEXT in PostgreSQL
    assert currency_code.postgres_type.value == "TEXT"
    assert country_code.postgres_type.value == "TEXT"
    assert mime_type.postgres_type.value == "TEXT"
    assert semantic_version.postgres_type.value == "TEXT"

    # Should map to correct FraiseQL scalars
    assert currency_code.fraiseql_scalar_name == "CurrencyCode"
    assert country_code.fraiseql_scalar_name == "CountryCode"
    assert mime_type.fraiseql_scalar_name == "MimeType"
    assert semantic_version.fraiseql_scalar_name == "SemanticVersion"


def test_currency_code_validation():
    """Test currency code validation pattern"""
    currency_code = get_scalar_type("currencyCode")

    assert currency_code.validation_pattern == r"^[A-Z]{3}$"
    assert currency_code.description == "ISO 4217 currency code"
    assert currency_code.example == "USD"
    assert currency_code.input_type == "text"
    assert currency_code.placeholder == "USD"


def test_country_code_validation():
    """Test country code validation pattern"""
    country_code = get_scalar_type("countryCode")

    assert country_code.validation_pattern == r"^[A-Z]{2}$"
    assert country_code.description == "ISO 3166-1 alpha-2 country code"
    assert country_code.example == "US"
    assert country_code.input_type == "text"
    assert country_code.placeholder == "US"


def test_mime_type_validation():
    """Test MIME type validation pattern"""
    mime_type = get_scalar_type("mimeType")

    assert (
        mime_type.validation_pattern
        == r"^[a-zA-Z][a-zA-Z0-9][a-zA-Z0-9\!\#\$\&\-\^]*\/[a-zA-Z0-9][a-zA-Z0-9\!\#\$\&\-\^]*$"
    )
    assert mime_type.description == "MIME type (e.g., application/json, image/png)"
    assert mime_type.example == "application/json"
    assert mime_type.input_type == "text"
    assert mime_type.placeholder == "application/json"


def test_semantic_version_validation():
    """Test semantic version validation pattern"""
    semantic_version = get_scalar_type("semanticVersion")

    # Check that the pattern exists and is complex (semver is complex)
    assert semantic_version.validation_pattern is not None
    assert len(semantic_version.validation_pattern) > 50  # Semver regex is long
    assert semantic_version.description == "Semantic versioning (semver) format"
    assert semantic_version.example == "1.2.3"
    assert semantic_version.input_type == "text"
    assert semantic_version.placeholder == "1.0.0"


def test_finance_scalar_types():
    """Test financial/stocks scalar types are properly defined"""
    stock_symbol = get_scalar_type("stockSymbol")
    isin = get_scalar_type("isin")
    cusip = get_scalar_type("cusip")
    exchange_code = get_scalar_type("exchangeCode")

    # All should exist
    assert stock_symbol is not None
    assert isin is not None
    assert cusip is not None
    assert exchange_code is not None

    # All should map to TEXT in PostgreSQL
    assert stock_symbol.postgres_type.value == "TEXT"
    assert isin.postgres_type.value == "TEXT"
    assert cusip.postgres_type.value == "TEXT"
    assert exchange_code.postgres_type.value == "TEXT"

    # Should map to correct FraiseQL scalars
    assert stock_symbol.fraiseql_scalar_name == "StockSymbol"
    assert isin.fraiseql_scalar_name == "ISIN"
    assert cusip.fraiseql_scalar_name == "CUSIP"
    assert exchange_code.fraiseql_scalar_name == "ExchangeCode"


def test_stock_symbol_validation():
    """Test stock symbol validation pattern"""
    stock_symbol = get_scalar_type("stockSymbol")

    assert stock_symbol.validation_pattern == r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$"
    assert (
        stock_symbol.description
        == "Stock ticker symbol (1-5 uppercase letters, optional class suffix)"
    )
    assert stock_symbol.example == "AAPL"
    assert stock_symbol.input_type == "text"
    assert stock_symbol.placeholder == "AAPL"


def test_isin_validation():
    """Test ISIN validation pattern"""
    isin = get_scalar_type("isin")

    assert isin.validation_pattern == r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$"
    assert isin.description == "International Securities Identification Number (12 characters)"
    assert isin.example == "US0378331005"
    assert isin.input_type == "text"
    assert isin.placeholder == "US0378331005"


def test_cusip_validation():
    """Test CUSIP validation pattern"""
    cusip = get_scalar_type("cusip")

    assert cusip.validation_pattern == r"^[0-9]{6}[0-9A-Z]{2}[0-9]$"
    assert (
        cusip.description
        == "Committee on Uniform Security Identification Procedures (9 characters, primarily US)"
    )
    assert cusip.example == "037833100"
    assert cusip.input_type == "text"
    assert cusip.placeholder == "037833100"


def test_exchange_code_validation():
    """Test exchange code validation pattern"""
    exchange_code = get_scalar_type("exchangeCode")

    assert exchange_code.validation_pattern == r"^[A-Z]{2,6}$"
    assert exchange_code.description == "Stock exchange code (2-6 uppercase letters)"
    assert exchange_code.example == "NYSE"
    assert exchange_code.input_type == "text"
    assert exchange_code.placeholder == "NYSE"


def test_sedol_validation():
    """Test SEDOL validation pattern"""
    sedol = get_scalar_type("sedol")

    assert sedol.validation_pattern == r"^[0-9A-Z]{6}[0-9]$"
    assert sedol.description == "Stock Exchange Daily Official List (7 characters, UK-based)"
    assert sedol.example == "B02LC96"
    assert sedol.input_type == "text"
    assert sedol.placeholder == "B02LC96"


def test_lei_validation():
    """Test LEI validation pattern"""
    lei = get_scalar_type("lei")

    assert lei.validation_pattern == r"^[0-9A-Z]{18}[0-9]{2}$"
    assert lei.description == "Legal Entity Identifier (20 characters, global standard)"
    assert lei.example == "54930084UKLVMY22DS16"
    assert lei.input_type == "text"
    assert lei.placeholder == "54930084UKLVMY22DS16"


def test_mic_validation():
    """Test MIC validation pattern"""
    mic = get_scalar_type("mic")

    assert mic.validation_pattern == r"^[A-Z0-9]{4}$"
    assert mic.description == "Market Identifier Code (ISO 10383, identifies trading venues)"
    assert mic.example == "XNYS"
    assert mic.input_type == "text"
    assert mic.placeholder == "XNYS"


def test_logistics_scalar_types():
    """Test logistics/shipping scalar types are properly defined"""
    tracking_number = get_scalar_type("trackingNumber")
    container_number = get_scalar_type("containerNumber")
    license_plate = get_scalar_type("licensePlate")
    vin = get_scalar_type("vin")
    flight_number = get_scalar_type("flightNumber")
    port_code = get_scalar_type("portCode")
    postal_code = get_scalar_type("postalCode")

    # All should exist
    assert tracking_number is not None
    assert container_number is not None
    assert license_plate is not None
    assert vin is not None
    assert flight_number is not None
    assert port_code is not None
    assert postal_code is not None

    # All should map to TEXT in PostgreSQL
    assert tracking_number.postgres_type.value == "TEXT"
    assert container_number.postgres_type.value == "TEXT"
    assert license_plate.postgres_type.value == "TEXT"
    assert vin.postgres_type.value == "TEXT"
    assert flight_number.postgres_type.value == "TEXT"
    assert port_code.postgres_type.value == "TEXT"
    assert postal_code.postgres_type.value == "TEXT"

    # Should map to correct FraiseQL scalars
    assert tracking_number.fraiseql_scalar_name == "TrackingNumber"
    assert container_number.fraiseql_scalar_name == "ContainerNumber"
    assert license_plate.fraiseql_scalar_name == "LicensePlate"
    assert vin.fraiseql_scalar_name == "VIN"
    assert flight_number.fraiseql_scalar_name == "FlightNumber"
    assert port_code.fraiseql_scalar_name == "PortCode"
    assert postal_code.fraiseql_scalar_name == "PostalCode"


def test_tracking_number_validation():
    """Test tracking number validation pattern"""
    tracking_number = get_scalar_type("trackingNumber")

    assert tracking_number.validation_pattern == r"^[A-Z0-9]{8,30}$"
    assert tracking_number.description == "Shipping tracking number (8-30 alphanumeric characters)"
    assert tracking_number.example == "1Z999AA1234567890"
    assert tracking_number.input_type == "text"
    assert tracking_number.placeholder == "1Z999AA1234567890"


def test_container_number_validation():
    """Test container number validation pattern"""
    container_number = get_scalar_type("containerNumber")

    assert container_number.validation_pattern == r"^[A-Z]{3}[UJZ]\d{6}\d$"
    assert (
        container_number.description
        == "Shipping container number (ISO 6346 format: 3 letters + U/J/Z + 6 digits + check digit)"
    )
    assert container_number.example == "MSKU1234567"
    assert container_number.input_type == "text"
    assert container_number.placeholder == "MSKU1234567"


def test_license_plate_validation():
    """Test license plate validation pattern"""
    license_plate = get_scalar_type("licensePlate")

    assert license_plate.validation_pattern == r"^[A-Z0-9\s\-]{1,20}$"
    assert (
        license_plate.description
        == "Vehicle license plate number (international format: alphanumeric with spaces/hyphens)"
    )
    assert license_plate.example == "ABC-123"
    assert license_plate.input_type == "text"
    assert license_plate.placeholder == "ABC-123"


def test_vin_validation():
    """Test VIN validation pattern"""
    vin = get_scalar_type("vin")

    assert vin.validation_pattern == r"^[A-HJ-NPR-Z0-9]{17}$"
    assert vin.description == "Vehicle Identification Number (17 characters, ISO 3779/3780)"
    assert vin.example == "1HGCM82633A123456"
    assert vin.input_type == "text"
    assert vin.placeholder == "1HGCM82633A123456"


def test_flight_number_validation():
    """Test flight number validation pattern"""
    flight_number = get_scalar_type("flightNumber")

    assert flight_number.validation_pattern == r"^[A-Z]{2,3}\d{1,4}[A-Z]?$"
    assert (
        flight_number.description
        == "Flight number (IATA airline code + 1-4 digits + optional letter)"
    )
    assert flight_number.example == "AA1234"
    assert flight_number.input_type == "text"
    assert flight_number.placeholder == "AA1234"


def test_port_code_validation():
    """Test port code validation pattern"""
    port_code = get_scalar_type("portCode")

    assert port_code.validation_pattern == r"^[A-Z]{5}$"
    assert port_code.description == "Port/terminal code (UN/LOCODE: 5 letters)"
    assert port_code.example == "USNYC"
    assert port_code.input_type == "text"
    assert port_code.placeholder == "USNYC"


def test_postal_code_validation():
    """Test postal code validation pattern"""
    postal_code = get_scalar_type("postalCode")

    assert postal_code.validation_pattern == r"^[A-Z0-9\s\-]{3,12}$"
    assert (
        postal_code.description
        == "Postal/ZIP code (international format: alphanumeric with spaces/hyphens)"
    )
    assert postal_code.example == "12345"
    assert postal_code.input_type == "text"
    assert postal_code.placeholder == "12345"


def test_additional_scalar_types():
    """Test additional technical/financial scalar types"""
    airport_code = get_scalar_type("airportCode")
    domain_name = get_scalar_type("domainName")
    api_key = get_scalar_type("apiKey")
    hash_sha256 = get_scalar_type("hashSHA256")
    iban = get_scalar_type("iban")
    swift_code = get_scalar_type("swiftCode")

    # All should exist
    assert airport_code is not None
    assert domain_name is not None
    assert api_key is not None
    assert hash_sha256 is not None
    assert iban is not None
    assert swift_code is not None

    # All should map to TEXT in PostgreSQL
    assert airport_code.postgres_type.value == "TEXT"
    assert domain_name.postgres_type.value == "TEXT"
    assert api_key.postgres_type.value == "TEXT"
    assert hash_sha256.postgres_type.value == "TEXT"
    assert iban.postgres_type.value == "TEXT"
    assert swift_code.postgres_type.value == "TEXT"

    # Should map to correct FraiseQL scalars
    assert airport_code.fraiseql_scalar_name == "AirportCode"
    assert domain_name.fraiseql_scalar_name == "DomainName"
    assert api_key.fraiseql_scalar_name == "ApiKey"
    assert hash_sha256.fraiseql_scalar_name == "HashSHA256"
    assert iban.fraiseql_scalar_name == "IBAN"
    assert swift_code.fraiseql_scalar_name == "SwiftCode"


def test_airport_code_validation():
    """Test airport code validation pattern"""
    airport_code = get_scalar_type("airportCode")

    assert airport_code.validation_pattern == r"^[A-Z]{3}$"
    assert airport_code.description == "Airport code (IATA format: 3 uppercase letters)"
    assert airport_code.example == "JFK"
    assert airport_code.input_type == "text"
    assert airport_code.placeholder == "JFK"


def test_domain_name_validation():
    """Test domain name validation pattern"""
    domain_name = get_scalar_type("domainName")

    assert (
        domain_name.validation_pattern
        == r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )
    assert domain_name.description == "Domain name (RFC compliant)"
    assert domain_name.example == "example.com"
    assert domain_name.input_type == "text"
    assert domain_name.placeholder == "example.com"


def test_api_key_validation():
    """Test API key validation pattern"""
    api_key = get_scalar_type("apiKey")

    assert api_key.validation_pattern == r"^[A-Za-z0-9_\-]{20,128}$"
    assert api_key.description == "API key or access token (alphanumeric with hyphens/underscores)"
    assert api_key.example == "sk-1234567890abcdef"
    assert api_key.input_type == "password"
    assert api_key.placeholder == "sk-..."


def test_hash_sha256_validation():
    """Test SHA256 hash validation pattern"""
    hash_sha256 = get_scalar_type("hashSHA256")

    assert hash_sha256.validation_pattern == r"^[a-f0-9]{64}$"
    assert hash_sha256.description == "SHA256 hash (64 hexadecimal characters)"
    assert hash_sha256.example == "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
    assert hash_sha256.input_type == "text"
    assert hash_sha256.placeholder == "a665a459..."


def test_iban_validation():
    """Test IBAN validation pattern"""
    iban = get_scalar_type("iban")

    assert iban.validation_pattern == r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$"
    assert iban.description == "International Bank Account Number (ISO 13616)"
    assert iban.example == "GB29 NWBK 6016 1331 9268 19"
    assert iban.input_type == "text"
    assert iban.placeholder == "GB29 NWBK 6016 1331 9268 19"


def test_swift_code_validation():
    """Test SWIFT code validation pattern"""
    swift_code = get_scalar_type("swiftCode")

    assert swift_code.validation_pattern == r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$"
    assert swift_code.description == "SWIFT/BIC bank identifier code (8 or 11 characters)"
    assert swift_code.example == "CHASUS33"
    assert swift_code.input_type == "text"
    assert swift_code.placeholder == "CHASUS33"


def test_exchange_rate_validation():
    """Test exchange rate validation"""
    exchange_rate = get_scalar_type("exchangeRate")

    assert exchange_rate.postgres_type.value == "NUMERIC"
    assert exchange_rate.postgres_precision == (19, 8)
    assert exchange_rate.min_value == 0.0
    assert exchange_rate.description == "Currency exchange rate (high precision decimal)"
    assert exchange_rate.example == "1.23456789"
    assert exchange_rate.input_type == "number"
    assert exchange_rate.placeholder == "1.23456789"
