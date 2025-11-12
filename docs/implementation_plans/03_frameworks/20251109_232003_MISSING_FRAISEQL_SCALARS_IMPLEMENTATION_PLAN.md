# Missing FraiseQL Scalars - Complete Implementation Plan

**Project**: printoptim_backend_poc
**Target**: FraiseQL scalar library
**Status**: Ready for Implementation
**Date**: 2025-11-09

---

## Executive Summary

This document provides a comprehensive implementation plan for all scalar types needed by the printoptim_backend_poc project but currently missing from FraiseQL's scalar library.

### Current State Analysis

**FraiseQL Scalars Currently Implemented** ✅:
- ✅ `cidr` - CIDR network notation
- ✅ `coordinates` - Geographic coordinates
- ✅ `date` - ISO 8601 date
- ✅ `daterange` - PostgreSQL date range
- ✅ `datetime` - ISO 8601 datetime with timezone
- ✅ `email_address` - Email validation
- ✅ `hostname` - DNS hostname (RFC 1123)
- ✅ `ip_address` - IPv4/IPv6 addresses
- ✅ `json` - JSON object
- ✅ `language_code` - ISO 639-1 language codes (NEW - Issue #127)
- ✅ `locale_code` - BCP 47 locale codes (NEW - Issue #127)
- ✅ `ltree` - PostgreSQL ltree path
- ✅ `mac_address` - MAC address
- ✅ `port` - Network port (1-65535)
- ✅ `timezone` - IANA timezone identifiers (NEW - Issue #127)
- ✅ `uuid` - RFC 4122 UUID

**Total Implemented**: 16 scalars

---

## Scalars Needed by printoptim_backend_poc

Based on analysis of entity YAML files and documentation:

### Category 1: String Validation Types
1. ❌ **PhoneNumber** - E.164 phone number format
2. ❌ **URL** - HTTP/HTTPS URL validation
3. ❌ **Slug** - URL-friendly identifier (kebab-case)
4. ❌ **Color** - Hex color code (#RRGGBB)

### Category 2: Text Formatting Types
5. ❌ **Markdown** - Markdown formatted text
6. ❌ **HTML** - HTML content

### Category 3: Numeric/Financial Types
7. ❌ **Money** - Monetary values with precision
8. ❌ **Percentage** - Percentage values (0-100)
9. ❌ **ExchangeRate** - Currency exchange rates

### Category 4: Geographic Types
10. ❌ **Latitude** - Latitude value (-90 to 90)
11. ❌ **Longitude** - Longitude value (-180 to 180)

### Category 5: Media/File Types
12. ❌ **Image** - Image URL/path
13. ❌ **File** - File URL/path

### Category 6: Time Types
14. ❌ **Time** - Time of day (HH:MM:SS)
15. ❌ **Duration** - Time duration/interval

**Total Needed**: 15 new scalars

---

## Implementation Priority

### Priority 1: High-Impact Scalars (Immediate Need)
**Timeline**: Week 1
**Rationale**: Used in core entities (Contact, TradingInstrument)

1. **PhoneNumber** - Contact management
2. **URL** - Contact/Company websites
3. **Money** - Trading instruments, financial data
4. **ExchangeRate** - Trading instruments
5. **Image** - Contact avatars, product images

**Estimated Time**: 8-10 hours

---

### Priority 2: Medium-Impact Scalars (Near-Term)
**Timeline**: Week 2
**Rationale**: Enhance functionality, common use cases

6. **Percentage** - Discounts, rates, analytics
7. **Slug** - URL-friendly identifiers for entities
8. **Markdown** - Rich text content (notes, descriptions)
9. **Color** - UI theming, branding

**Estimated Time**: 6-8 hours

---

### Priority 3: Low-Impact Scalars (Future Enhancement)
**Timeline**: Week 3-4
**Rationale**: Nice-to-have, specialized use cases

10. **HTML** - Rich text content (alternative to Markdown)
11. **Latitude** - Geographic data (unless using Coordinates)
12. **Longitude** - Geographic data (unless using Coordinates)
13. **Time** - Scheduling, time-based features
14. **Duration** - Time intervals, task durations
15. **File** - Document attachments, file uploads

**Estimated Time**: 8-10 hours

---

## Detailed Implementation Specifications

### 1. PhoneNumber Scalar

**File**: `src/fraiseql/types/scalars/phone_number.py`

**Validation**: E.164 international phone number format
- **Format**: `+[country][number]`
- **Length**: 7-15 digits (including country code)
- **Regex**: `^\+?[1-9]\d{1,14}$`
- **Examples**: `+14155552671`, `+33123456789`, `+81312345678`

**PostgreSQL Type**: `TEXT`
**GraphQL Scalar**: `PhoneNumber`

**Key Features**:
- Accepts optional + prefix
- No country code required (but recommended)
- No formatting characters (spaces, hyphens, parentheses)
- Stores normalized format

**Implementation Template**:
```python
"""Phone number scalar type for E.164 validation."""

import re
from typing import Any

from graphql import GraphQLError, GraphQLScalarType
from graphql.language import StringValueNode

from fraiseql.types.definitions import ScalarMarker

# E.164 international phone number format
# +[country][number] - 7 to 15 digits total
_PHONE_NUMBER_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")


def serialize_phone_number(value: Any) -> str | None:
    """Serialize phone number to string."""
    if value is None:
        return None

    value_str = str(value).strip()

    if not _PHONE_NUMBER_REGEX.match(value_str):
        raise GraphQLError(
            f"Invalid phone number: {value}. Must be E.164 format (e.g., '+14155552671')"
        )

    return value_str


def parse_phone_number_value(value: Any) -> str:
    """Parse phone number from variable value."""
    if not isinstance(value, str):
        raise GraphQLError(f"Phone number must be a string, got {type(value).__name__}")

    value_str = value.strip()

    if not _PHONE_NUMBER_REGEX.match(value_str):
        raise GraphQLError(
            f"Invalid phone number: {value}. Must be E.164 format (e.g., '+14155552671')"
        )

    return value_str


def parse_phone_number_literal(ast: Any, _variables: dict[str, Any] | None = None) -> str:
    """Parse phone number from AST literal."""
    if not isinstance(ast, StringValueNode):
        raise GraphQLError("Phone number must be a string")

    return parse_phone_number_value(ast.value)


PhoneNumberScalar = GraphQLScalarType(
    name="PhoneNumber",
    description=(
        "E.164 international phone number format. "
        "Format: +[country][number] (7-15 digits). "
        "Examples: +14155552671, +33123456789. "
        "See: https://en.wikipedia.org/wiki/E.164"
    ),
    serialize=serialize_phone_number,
    parse_value=parse_phone_number_value,
    parse_literal=parse_phone_number_literal,
)


class PhoneNumberField(str, ScalarMarker):
    """E.164 international phone number format.

    This scalar validates phone numbers following E.164 standard:
    - Optional + prefix
    - Country code followed by number
    - 7-15 digits total
    - No formatting characters (spaces, hyphens, parentheses)

    Example:
        >>> from fraiseql.types import PhoneNumber
        >>>
        >>> @fraiseql.type
        ... class Contact:
        ...     phone: PhoneNumber
        ...     mobile: PhoneNumber | None
    """

    __slots__ = ()

    def __new__(cls, value: str) -> "PhoneNumberField":
        """Create a new PhoneNumberField instance with validation."""
        value_str = value.strip()
        if not _PHONE_NUMBER_REGEX.match(value_str):
            raise ValueError(
                f"Invalid phone number: {value}. Must be E.164 format (e.g., '+14155552671')"
            )
        return super().__new__(cls, value_str)
```

---

### 2. URL Scalar

**File**: `src/fraiseql/types/scalars/url.py`

**Validation**: HTTP/HTTPS URL format
- **Schemes**: `http://`, `https://`
- **Components**: scheme, domain, optional path/query/fragment
- **Regex**: `^https?://[^\s/$.?#].[^\s]*$`
- **Examples**: `https://example.com`, `http://api.example.com/v1/users?limit=10`

**PostgreSQL Type**: `TEXT`
**GraphQL Scalar**: `URL`

**Key Features**:
- Validates HTTP/HTTPS schemes only
- Allows paths, query strings, fragments
- Case-insensitive domain
- International domain names supported

**Implementation Template**:
```python
"""URL scalar type for HTTP/HTTPS URL validation."""

import re
from typing import Any

from graphql import GraphQLError, GraphQLScalarType
from graphql.language import StringValueNode

from fraiseql.types.definitions import ScalarMarker

# HTTP/HTTPS URL regex
# Supports: scheme, domain, path, query, fragment
_URL_REGEX = re.compile(
    r"^https?://"  # HTTP or HTTPS scheme
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP address
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",  # path
    re.IGNORECASE
)


def serialize_url(value: Any) -> str | None:
    """Serialize URL to string."""
    if value is None:
        return None

    value_str = str(value).strip()

    if not _URL_REGEX.match(value_str):
        raise GraphQLError(
            f"Invalid URL: {value}. Must be HTTP or HTTPS URL (e.g., 'https://example.com')"
        )

    return value_str


def parse_url_value(value: Any) -> str:
    """Parse URL from variable value."""
    if not isinstance(value, str):
        raise GraphQLError(f"URL must be a string, got {type(value).__name__}")

    value_str = value.strip()

    if not _URL_REGEX.match(value_str):
        raise GraphQLError(
            f"Invalid URL: {value}. Must be HTTP or HTTPS URL (e.g., 'https://example.com')"
        )

    return value_str


def parse_url_literal(ast: Any, _variables: dict[str, Any] | None = None) -> str:
    """Parse URL from AST literal."""
    if not isinstance(ast, StringValueNode):
        raise GraphQLError("URL must be a string")

    return parse_url_value(ast.value)


URLScalar = GraphQLScalarType(
    name="URL",
    description=(
        "HTTP or HTTPS URL. "
        "Must include scheme (http:// or https://). "
        "Examples: https://example.com, http://api.example.com/v1/users. "
        "See: https://tools.ietf.org/html/rfc3986"
    ),
    serialize=serialize_url,
    parse_value=parse_url_value,
    parse_literal=parse_url_literal,
)


class URLField(str, ScalarMarker):
    """HTTP or HTTPS URL.

    This scalar validates URLs with HTTP or HTTPS schemes:
    - Must start with http:// or https://
    - Valid domain name or IP address
    - Optional port, path, query, fragment
    - Case-insensitive domain

    Example:
        >>> from fraiseql.types import URL
        >>>
        >>> @fraiseql.type
        ... class Company:
        ...     website: URL
        ...     api_endpoint: URL | None
    """

    __slots__ = ()

    def __new__(cls, value: str) -> "URLField":
        """Create a new URLField instance with validation."""
        value_str = value.strip()
        if not _URL_REGEX.match(value_str):
            raise ValueError(
                f"Invalid URL: {value}. Must be HTTP or HTTPS URL (e.g., 'https://example.com')"
            )
        return super().__new__(cls, value_str)
```

---

### 3. Money Scalar

**File**: `src/fraiseql/types/scalars/money.py`

**Validation**: Decimal monetary value
- **Format**: Decimal number with up to 4 decimal places
- **Range**: -999,999,999,999,999.9999 to 999,999,999,999,999.9999
- **Precision**: 19 digits, 4 decimal places
- **Examples**: `19.99`, `1234.5678`, `-99.99`, `0.01`

**PostgreSQL Type**: `NUMERIC(19,4)`
**GraphQL Scalar**: `Money`

**Key Features**:
- Currency-agnostic (store currency separately)
- High precision for financial calculations
- Supports negative values
- Stores as PostgreSQL NUMERIC (no floating-point errors)

**Implementation Template**:
```python
"""Money scalar type for monetary values."""

from decimal import Decimal, InvalidOperation
from typing import Any

from graphql import GraphQLError, GraphQLScalarType
from graphql.language import FloatValueNode, IntValueNode, StringValueNode

from fraiseql.types.definitions import ScalarMarker


def serialize_money(value: Any) -> str | None:
    """Serialize money to string."""
    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise GraphQLError(f"Invalid money value: {value}. Must be a decimal number") from e

    # Validate precision (19 digits, 4 decimal places)
    if decimal_value.as_tuple().exponent < -4:
        raise GraphQLError(
            f"Invalid money value: {value}. Maximum 4 decimal places allowed"
        )

    # Validate range
    max_value = Decimal("999999999999999.9999")
    min_value = Decimal("-999999999999999.9999")
    if decimal_value > max_value or decimal_value < min_value:
        raise GraphQLError(
            f"Invalid money value: {value}. Must be between {min_value} and {max_value}"
        )

    return str(decimal_value)


def parse_money_value(value: Any) -> Decimal:
    """Parse money from variable value."""
    if isinstance(value, Decimal):
        return value

    if not isinstance(value, (str, int, float)):
        raise GraphQLError(f"Money must be a number, got {type(value).__name__}")

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise GraphQLError(f"Invalid money value: {value}. Must be a decimal number") from e

    # Validate precision
    if decimal_value.as_tuple().exponent < -4:
        raise GraphQLError(
            f"Invalid money value: {value}. Maximum 4 decimal places allowed"
        )

    return decimal_value


def parse_money_literal(ast: Any, _variables: dict[str, Any] | None = None) -> Decimal:
    """Parse money from AST literal."""
    if isinstance(ast, (IntValueNode, FloatValueNode, StringValueNode)):
        return parse_money_value(ast.value)

    raise GraphQLError("Money must be a number")


MoneyScalar = GraphQLScalarType(
    name="Money",
    description=(
        "Monetary value with high precision. "
        "Stored as NUMERIC(19,4) - up to 4 decimal places. "
        "Currency-agnostic (store currency code separately). "
        "Examples: 19.99, 1234.5678, -99.99"
    ),
    serialize=serialize_money,
    parse_value=parse_money_value,
    parse_literal=parse_money_literal,
)


class MoneyField(Decimal, ScalarMarker):
    """Monetary value with high precision.

    This scalar represents monetary values:
    - High precision: NUMERIC(19,4)
    - No floating-point errors
    - Supports negative values
    - Currency-agnostic

    Example:
        >>> from fraiseql.types import Money
        >>>
        >>> @fraiseql.type
        ... class Product:
        ...     price: Money
        ...     cost: Money | None
        ...     currency: str  # Store currency separately
    """

    __slots__ = ()

    def __new__(cls, value: Any) -> "MoneyField":
        """Create a new MoneyField instance with validation."""
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid money value: {value}. Must be a decimal number") from e

        if decimal_value.as_tuple().exponent < -4:
            raise ValueError(
                f"Invalid money value: {value}. Maximum 4 decimal places allowed"
            )

        return super().__new__(cls, decimal_value)
```

---

### 4. ExchangeRate Scalar

**File**: `src/fraiseql/types/scalars/exchange_rate.py`

**Validation**: Decimal exchange rate value
- **Format**: Decimal number with up to 8 decimal places
- **Range**: Must be positive (> 0)
- **Precision**: 20 digits, 8 decimal places
- **Examples**: `1.2345`, `0.85`, `120.456789`, `0.00000123`

**PostgreSQL Type**: `NUMERIC(20,8)`
**GraphQL Scalar**: `ExchangeRate`

**Key Features**:
- High precision for crypto exchange rates
- Positive values only
- Supports very small rates (e.g., 0.00000123)

**Implementation Template**:
```python
"""Exchange rate scalar type for currency conversion rates."""

from decimal import Decimal, InvalidOperation
from typing import Any

from graphql import GraphQLError, GraphQLScalarType
from graphql.language import FloatValueNode, IntValueNode, StringValueNode

from fraiseql.types.definitions import ScalarMarker


def serialize_exchange_rate(value: Any) -> str | None:
    """Serialize exchange rate to string."""
    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise GraphQLError(f"Invalid exchange rate: {value}. Must be a decimal number") from e

    # Must be positive
    if decimal_value <= 0:
        raise GraphQLError(
            f"Invalid exchange rate: {value}. Must be positive (> 0)"
        )

    # Validate precision (20 digits, 8 decimal places)
    if decimal_value.as_tuple().exponent < -8:
        raise GraphQLError(
            f"Invalid exchange rate: {value}. Maximum 8 decimal places allowed"
        )

    return str(decimal_value)


def parse_exchange_rate_value(value: Any) -> Decimal:
    """Parse exchange rate from variable value."""
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, (str, int, float)):
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as e:
            raise GraphQLError(f"Invalid exchange rate: {value}. Must be a decimal number") from e
    else:
        raise GraphQLError(f"Exchange rate must be a number, got {type(value).__name__}")

    if decimal_value <= 0:
        raise GraphQLError(
            f"Invalid exchange rate: {value}. Must be positive (> 0)"
        )

    if decimal_value.as_tuple().exponent < -8:
        raise GraphQLError(
            f"Invalid exchange rate: {value}. Maximum 8 decimal places allowed"
        )

    return decimal_value


def parse_exchange_rate_literal(ast: Any, _variables: dict[str, Any] | None = None) -> Decimal:
    """Parse exchange rate from AST literal."""
    if isinstance(ast, (IntValueNode, FloatValueNode, StringValueNode)):
        return parse_exchange_rate_value(ast.value)

    raise GraphQLError("Exchange rate must be a number")


ExchangeRateScalar = GraphQLScalarType(
    name="ExchangeRate",
    description=(
        "Currency exchange rate with high precision. "
        "Stored as NUMERIC(20,8) - up to 8 decimal places. "
        "Must be positive. Supports very small rates for crypto. "
        "Examples: 1.2345, 0.85, 0.00000123"
    ),
    serialize=serialize_exchange_rate,
    parse_value=parse_exchange_rate_value,
    parse_literal=parse_exchange_rate_literal,
)


class ExchangeRateField(Decimal, ScalarMarker):
    """Currency exchange rate with high precision.

    This scalar represents exchange rates between currencies:
    - High precision: NUMERIC(20,8)
    - Must be positive (> 0)
    - Supports very small rates (crypto)
    - No floating-point errors

    Example:
        >>> from fraiseql.types import ExchangeRate
        >>>
        >>> @fraiseql.type
        ... class TradingInstrument:
        ...     exchange_rate: ExchangeRate
        ...     base_currency: str
        ...     quote_currency: str
    """

    __slots__ = ()

    def __new__(cls, value: Any) -> "ExchangeRateField":
        """Create a new ExchangeRateField instance with validation."""
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid exchange rate: {value}. Must be a decimal number") from e

        if decimal_value <= 0:
            raise ValueError(
                f"Invalid exchange rate: {value}. Must be positive (> 0)"
            )

        if decimal_value.as_tuple().exponent < -8:
            raise ValueError(
                f"Invalid exchange rate: {value}. Maximum 8 decimal places allowed"
            )

        return super().__new__(cls, decimal_value)
```

---

### 5. Image Scalar

**File**: `src/fraiseql/types/scalars/image.py`

**Validation**: Image URL or file path
- **Formats**: URL (http/https) or file path
- **Extensions**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.bmp`, `.ico`
- **Examples**: `https://example.com/avatar.png`, `/uploads/image.jpg`, `data:image/png;base64,...`

**PostgreSQL Type**: `TEXT`
**GraphQL Scalar**: `Image`

**Key Features**:
- Validates URL format or file path
- Validates image file extensions
- Supports data URLs (base64)
- Case-insensitive extension checking

**Implementation Template**:
```python
"""Image scalar type for image URL/path validation."""

import re
from typing import Any

from graphql import GraphQLError, GraphQLScalarType
from graphql.language import StringValueNode

from fraiseql.types.definitions import ScalarMarker

# Image file extensions
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"}

# URL or file path pattern
_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
_DATA_URL_PATTERN = re.compile(r"^data:image/[a-z]+;base64,", re.IGNORECASE)


def _is_valid_image(value: str) -> bool:
    """Check if value is a valid image URL or path."""
    value_lower = value.lower()

    # Data URL (base64 encoded image)
    if _DATA_URL_PATTERN.match(value_lower):
        return True

    # HTTP/HTTPS URL
    if _URL_PATTERN.match(value_lower):
        # Check if ends with image extension or has extension in path
        return any(ext in value_lower for ext in _IMAGE_EXTENSIONS)

    # File path
    return any(value_lower.endswith(ext) for ext in _IMAGE_EXTENSIONS)


def serialize_image(value: Any) -> str | None:
    """Serialize image to string."""
    if value is None:
        return None

    value_str = str(value).strip()

    if not _is_valid_image(value_str):
        raise GraphQLError(
            f"Invalid image: {value}. Must be URL or path with image extension "
            f"(jpg, jpeg, png, gif, webp, svg, bmp, ico)"
        )

    return value_str


def parse_image_value(value: Any) -> str:
    """Parse image from variable value."""
    if not isinstance(value, str):
        raise GraphQLError(f"Image must be a string, got {type(value).__name__}")

    value_str = value.strip()

    if not _is_valid_image(value_str):
        raise GraphQLError(
            f"Invalid image: {value}. Must be URL or path with image extension "
            f"(jpg, jpeg, png, gif, webp, svg, bmp, ico)"
        )

    return value_str


def parse_image_literal(ast: Any, _variables: dict[str, Any] | None = None) -> str:
    """Parse image from AST literal."""
    if not isinstance(ast, StringValueNode):
        raise GraphQLError("Image must be a string")

    return parse_image_value(ast.value)


ImageScalar = GraphQLScalarType(
    name="Image",
    description=(
        "Image URL or file path. "
        "Supports: http/https URLs, file paths, data URLs (base64). "
        "Valid extensions: jpg, jpeg, png, gif, webp, svg, bmp, ico. "
        "Examples: https://example.com/avatar.png, /uploads/image.jpg"
    ),
    serialize=serialize_image,
    parse_value=parse_image_value,
    parse_literal=parse_image_literal,
)


class ImageField(str, ScalarMarker):
    """Image URL or file path.

    This scalar validates image URLs or file paths:
    - HTTP/HTTPS URLs with image extensions
    - File paths ending with image extensions
    - Data URLs (base64 encoded images)
    - Supported formats: jpg, jpeg, png, gif, webp, svg, bmp, ico

    Example:
        >>> from fraiseql.types import Image
        >>>
        >>> @fraiseql.type
        ... class User:
        ...     avatar: Image | None
        ...     cover_photo: Image | None
    """

    __slots__ = ()

    def __new__(cls, value: str) -> "ImageField":
        """Create a new ImageField instance with validation."""
        value_str = value.strip()
        if not _is_valid_image(value_str):
            raise ValueError(
                f"Invalid image: {value}. Must be URL or path with image extension "
                f"(jpg, jpeg, png, gif, webp, svg, bmp, ico)"
            )
        return super().__new__(cls, value_str)
```

---

## Quick Reference: All 15 Missing Scalars

| # | Scalar | PostgreSQL Type | GraphQL Name | Priority | Complexity | Time |
|---|--------|-----------------|--------------|----------|------------|------|
| 1 | PhoneNumber | TEXT | PhoneNumber | P1 | Low | 1.5h |
| 2 | URL | TEXT | URL | P1 | Low | 1.5h |
| 3 | Money | NUMERIC(19,4) | Money | P1 | Medium | 2h |
| 4 | ExchangeRate | NUMERIC(20,8) | ExchangeRate | P1 | Medium | 2h |
| 5 | Image | TEXT | Image | P1 | Low | 1.5h |
| 6 | Percentage | NUMERIC(5,2) | Percentage | P2 | Low | 1.5h |
| 7 | Slug | TEXT | Slug | P2 | Low | 1.5h |
| 8 | Markdown | TEXT | Markdown | P2 | Low | 1h |
| 9 | Color | TEXT | Color | P2 | Low | 1h |
| 10 | HTML | TEXT | HTML | P3 | Low | 1h |
| 11 | Latitude | NUMERIC(10,8) | Latitude | P3 | Low | 1.5h |
| 12 | Longitude | NUMERIC(11,8) | Longitude | P3 | Low | 1.5h |
| 13 | Time | TIME | Time | P3 | Low | 1.5h |
| 14 | Duration | INTERVAL | Duration | P3 | Medium | 2h |
| 15 | File | TEXT | File | P3 | Low | 1.5h |

**Total Estimated Time**: 22-24 hours (distributed across 3 weeks)

---

## Implementation Strategy

### Batched Implementation Approach

#### Batch 1: Priority 1 Scalars (Week 1)
**Scalars**: PhoneNumber, URL, Money, ExchangeRate, Image
**Time**: 8-10 hours
**Order**:
1. PhoneNumber (1.5h) - Simplest, good warm-up
2. URL (1.5h) - Similar pattern to PhoneNumber
3. Image (1.5h) - Builds on URL validation
4. Money (2h) - Decimal handling, more complex
5. ExchangeRate (2h) - Similar to Money

**Deliverables**:
- 5 scalar implementation files
- 5 test files with 100% coverage
- Module exports updated
- Integration tests passing

#### Batch 2: Priority 2 Scalars (Week 2)
**Scalars**: Percentage, Slug, Markdown, Color
**Time**: 6-8 hours
**Order**:
1. Color (1h) - Simple regex validation
2. Slug (1.5h) - Regex + normalization
3. Markdown (1h) - Minimal validation
4. Percentage (1.5h) - Decimal with range constraints

**Deliverables**:
- 4 scalar implementation files
- 4 test files with 100% coverage
- Module exports updated
- Integration tests passing

#### Batch 3: Priority 3 Scalars (Week 3-4)
**Scalars**: HTML, Latitude, Longitude, Time, Duration, File
**Time**: 8-10 hours
**Order**:
1. HTML (1h) - Minimal validation
2. File (1.5h) - Similar to Image
3. Time (1.5h) - PostgreSQL TIME type
4. Latitude (1.5h) - Decimal with range
5. Longitude (1.5h) - Decimal with range
6. Duration (2h) - PostgreSQL INTERVAL type

**Deliverables**:
- 6 scalar implementation files
- 6 test files with 100% coverage
- Module exports updated
- Integration tests passing
- Complete documentation

---

## File Structure

```
fraiseql/
├── src/fraiseql/types/scalars/
│   ├── __init__.py                    # UPDATE: Add new exports
│   ├── color.py                       # NEW
│   ├── duration.py                    # NEW
│   ├── exchange_rate.py               # NEW
│   ├── file.py                        # NEW
│   ├── html.py                        # NEW
│   ├── image.py                       # NEW
│   ├── latitude.py                    # NEW
│   ├── longitude.py                   # NEW
│   ├── markdown.py                    # NEW
│   ├── money.py                       # NEW
│   ├── percentage.py                  # NEW
│   ├── phone_number.py                # NEW
│   ├── slug.py                        # NEW
│   ├── time.py                        # NEW
│   └── url.py                         # NEW
│
├── src/fraiseql/types/__init__.py     # UPDATE: Add new exports
│
└── tests/unit/core/type_system/
    ├── test_color_scalar.py           # NEW
    ├── test_duration_scalar.py        # NEW
    ├── test_exchange_rate_scalar.py   # NEW
    ├── test_file_scalar.py            # NEW
    ├── test_html_scalar.py            # NEW
    ├── test_image_scalar.py           # NEW
    ├── test_latitude_scalar.py        # NEW
    ├── test_longitude_scalar.py       # NEW
    ├── test_markdown_scalar.py        # NEW
    ├── test_money_scalar.py           # NEW
    ├── test_percentage_scalar.py      # NEW
    ├── test_phone_number_scalar.py    # NEW
    ├── test_slug_scalar.py            # NEW
    ├── test_time_scalar.py            # NEW
    └── test_url_scalar.py             # NEW
```

---

## Testing Strategy

### Test Template Structure

Each scalar test file follows the pattern established by `test_hostname_scalar.py`:

```python
"""Tests for [Scalar] scalar type validation."""

import pytest
from graphql import GraphQLError
from graphql.language import IntValueNode, StringValueNode

from fraiseql.types.scalars.[scalar_module] import (
    [Scalar]Field,
    parse_[scalar]_literal,
    parse_[scalar]_value,
    serialize_[scalar],
)


@pytest.mark.unit
class Test[Scalar]Serialization:
    """Test [scalar] serialization."""

    def test_serialize_valid_[scalar]s(self):
        """Test serializing valid [scalar]s."""
        # Valid examples

    def test_serialize_none(self):
        """Test serializing None returns None."""
        assert serialize_[scalar](None) is None

    def test_serialize_invalid_[scalar](self):
        """Test serializing invalid [scalar]s raises error."""
        # Invalid examples with pytest.raises


class Test[Scalar]Parsing:
    """Test [scalar] parsing from variables."""

    def test_parse_valid_[scalar](self):
        """Test parsing valid [scalar]s."""
        # Valid examples

    def test_parse_invalid_[scalar](self):
        """Test parsing invalid [scalar]s raises error."""
        # Invalid examples

    def test_parse_invalid_type(self):
        """Test parsing non-string types raises error."""
        # Type validation


class Test[Scalar]Field:
    """Test [Scalar]Field class."""

    def test_create_valid_[scalar]_field(self):
        """Test creating [Scalar]Field with valid values."""
        # Constructor tests

    def test_create_invalid_[scalar]_field(self):
        """Test creating [Scalar]Field with invalid values raises error."""
        # Invalid constructor tests


class Test[Scalar]LiteralParsing:
    """Test parsing [scalar] from GraphQL literals."""

    def test_parse_valid_literal(self):
        """Test parsing valid [scalar] literals."""
        # AST node tests

    def test_parse_invalid_literal_format(self):
        """Test parsing invalid [scalar] format literals."""
        # Invalid AST tests

    def test_parse_non_string_literal(self):
        """Test parsing non-string literals."""
        # Type validation for AST
```

### Test Execution Commands

```bash
# Run specific scalar tests
uv run pytest tests/unit/core/type_system/test_phone_number_scalar.py -v
uv run pytest tests/unit/core/type_system/test_money_scalar.py -v

# Run all new scalar tests
uv run pytest tests/unit/core/type_system/ -k "phone_number or url or money or exchange_rate or image" -v

# Run complete test suite
uv run pytest --tb=short

# Code quality
uv run ruff check
uv run mypy
```

---

## Module Export Updates

### `src/fraiseql/types/scalars/__init__.py`

**Add to imports**:
```python
from .color import ColorScalar
from .duration import DurationScalar
from .exchange_rate import ExchangeRateScalar
from .file import FileScalar
from .html import HTMLScalar
from .image import ImageScalar
from .latitude import LatitudeScalar
from .longitude import LongitudeScalar
from .markdown import MarkdownScalar
from .money import MoneyScalar
from .percentage import PercentageScalar
from .phone_number import PhoneNumberScalar
from .slug import SlugScalar
from .time import TimeScalar
from .url import URLScalar
```

**Add to `__all__`** (alphabetically):
```python
__all__ = [
    "CIDRScalar",
    "ColorScalar",           # NEW
    "CoordinateScalar",
    "DateRangeScalar",
    "DateScalar",
    "DateTimeScalar",
    "DurationScalar",        # NEW
    "ExchangeRateScalar",    # NEW
    "FileScalar",            # NEW
    "HostnameScalar",
    "HTMLScalar",            # NEW
    "ImageScalar",           # NEW
    "IpAddressScalar",
    "JSONScalar",
    "LanguageCodeScalar",
    "LatitudeScalar",        # NEW
    "LocaleCodeScalar",
    "LongitudeScalar",       # NEW
    "LTreeScalar",
    "MacAddressScalar",
    "MarkdownScalar",        # NEW
    "MoneyScalar",           # NEW
    "PercentageScalar",      # NEW
    "PhoneNumberScalar",     # NEW
    "PortScalar",
    "SlugScalar",            # NEW
    "SubnetMaskScalar",
    "TimeScalar",            # NEW
    "TimezoneScalar",
    "URLScalar",             # NEW
    "UUIDScalar",
]
```

### `src/fraiseql/types/__init__.py`

**Add to imports**:
```python
from .scalars.color import ColorField as Color
from .scalars.duration import DurationField as Duration
from .scalars.exchange_rate import ExchangeRateField as ExchangeRate
from .scalars.file import FileField as File
from .scalars.html import HTMLField as HTML
from .scalars.image import ImageField as Image
from .scalars.latitude import LatitudeField as Latitude
from .scalars.longitude import LongitudeField as Longitude
from .scalars.markdown import MarkdownField as Markdown
from .scalars.money import MoneyField as Money
from .scalars.percentage import PercentageField as Percentage
from .scalars.phone_number import PhoneNumberField as PhoneNumber
from .scalars.slug import SlugField as Slug
from .scalars.time import TimeField as Time
from .scalars.url import URLField as URL
```

**Add to `__all__`** (alphabetically):
```python
__all__ = [
    "CIDR",
    "Color",              # NEW
    "Connection",
    "Coordinate",
    "Date",
    "DateRange",
    "DateRangeValidatable",
    "DateRangeValidationMixin",
    "DateTime",
    "Duration",           # NEW
    "Edge",
    "EmailAddress",
    "Error",
    "ExchangeRate",       # NEW
    "File",               # NEW
    "HTML",               # NEW
    "Hostname",
    "Image",              # NEW
    "IpAddress",
    "JSON",
    "LanguageCode",
    "Latitude",           # NEW
    "LocaleCode",
    "Longitude",          # NEW
    "LTree",
    "MacAddress",
    "Markdown",           # NEW
    "Money",              # NEW
    "PageInfo",
    "PaginatedResponse",
    "Percentage",         # NEW
    "PhoneNumber",        # NEW
    "Port",
    "Slug",               # NEW
    "Time",               # NEW
    "Timezone",
    "URL",                # NEW
    "convert_scalar_to_graphql",
    "create_connection",
    "date_range_validator",
    "fraise_input",
    "fraise_type",
    "get_date_range_validation_errors",
    "input",
    "type",
    "validate_date_range",
]
```

---

## Quality Assurance Checklist

### Per-Scalar Checklist

For each scalar implementation:

- [ ] Scalar file created with pattern compliance
- [ ] Test file created with 100% coverage
- [ ] Serialization tests pass (valid, invalid, None)
- [ ] Parsing tests pass (valid, invalid, type errors)
- [ ] Field marker tests pass (constructor validation)
- [ ] Literal parsing tests pass (AST nodes)
- [ ] Exports added to `scalars/__init__.py`
- [ ] Exports added to `types/__init__.py`
- [ ] Linting passes: `uv run ruff check`
- [ ] Type checking passes: `uv run mypy`
- [ ] Integration test created and passing
- [ ] Documentation complete with examples

### Batch Completion Checklist

After each batch:

- [ ] All scalar tests pass: `uv run pytest tests/unit/core/type_system/ -k "[batch_pattern]"`
- [ ] No regressions: `uv run pytest --tb=short`
- [ ] Code coverage maintained: `uv run pytest --cov=src`
- [ ] Linting clean: `uv run ruff check`
- [ ] Type checking clean: `uv run mypy`
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Usage examples added
- [ ] Git commit with clear message

---

## Integration Testing

### Integration Test Template

**File**: `tests/integration/test_[batch]_scalars_integration.py`

```python
"""Integration tests for [batch] scalars."""

import pytest
from fraiseql.types import (
    type,
    input,
    PhoneNumber,
    URL,
    Money,
    # ... other scalars in batch
)


def test_scalars_in_type_definition():
    """Test scalars work in @fraiseql.type definitions."""

    @type(sql_source="app.contacts")
    class Contact:
        id: int
        name: str
        phone: PhoneNumber
        website: URL | None

    # Should create without errors
    contact = Contact(
        id=1,
        name="John Doe",
        phone=PhoneNumber("+14155552671"),
        website=URL("https://example.com")
    )

    assert contact.phone == "+14155552671"
    assert contact.website == "https://example.com"


def test_scalars_in_input_definition():
    """Test scalars work in @fraiseql.input definitions."""

    @input
    class CreateContactInput:
        name: str
        phone: PhoneNumber
        website: URL | None

    # Should validate on construction
    input_data = CreateContactInput(
        name="Jane Doe",
        phone=PhoneNumber("+14155552672"),
        website=None
    )

    assert input_data.phone == "+14155552672"


def test_scalar_validation_errors():
    """Test scalars raise validation errors."""

    with pytest.raises(ValueError, match="Invalid phone number"):
        PhoneNumber("not-a-phone")

    with pytest.raises(ValueError, match="Invalid URL"):
        URL("not-a-url")
```

---

## Usage Examples

### Contact Management (Priority 1 Scalars)

```python
from fraiseql.types import type, input, PhoneNumber, URL, Image

@type(sql_source="crm.contacts")
class Contact:
    id: int
    name: str
    email: EmailAddress
    phone: PhoneNumber
    website: URL | None
    avatar: Image | None

@input
class CreateContactInput:
    name: str
    email: EmailAddress
    phone: PhoneNumber
    website: URL | None
    avatar: Image | None
```

### Trading Instruments (Priority 1 Scalars)

```python
from fraiseql.types import type, Money, ExchangeRate

@type(sql_source="trading.instruments")
class TradingInstrument:
    id: int
    base_currency: str
    quote_currency: str
    exchange_rate: ExchangeRate
    volume_24h: Money
    last_updated: DateTime
```

### Product Catalog (Priority 2 Scalars)

```python
from fraiseql.types import type, Money, Percentage, Markdown, Slug, Color

@type(sql_source="catalog.products")
class Product:
    id: int
    name: str
    slug: Slug
    description: Markdown
    price: Money
    discount_percentage: Percentage | None
    brand_color: Color | None
```

### Event Scheduling (Priority 3 Scalars)

```python
from fraiseql.types import type, Date, Time, Duration

@type(sql_source="calendar.events")
class Event:
    id: int
    title: str
    event_date: Date
    start_time: Time
    duration: Duration
    timezone: Timezone
```

---

## Success Criteria

### Functional Success

✅ **All 15 Scalars Implemented**:
- PhoneNumber, URL, Money, ExchangeRate, Image
- Percentage, Slug, Markdown, Color
- HTML, Latitude, Longitude, Time, Duration, File

✅ **Quality Standards Met**:
- 100% test coverage for all scalars
- All tests passing
- Zero regressions
- Linting clean
- Type checking clean

✅ **Integration Success**:
- Works with `@fraiseql.type` and `@fraiseql.input`
- PostgreSQL integration working
- GraphQL schema generation working
- Documentation complete

### Business Impact

✅ **printoptim_backend_poc Ready**:
- Contact management fully supported
- Trading instruments fully supported
- All entity YAML files can use rich types
- Type-safe API development enabled

✅ **FraiseQL Library Enhanced**:
- 15 new universal scalars
- Comprehensive coverage of common use cases
- Ready for other projects to use
- Well-documented with examples

---

## Next Steps

### Phase 1: Batch 1 Implementation (This Week)

1. Create GitHub issues for Batch 1 scalars
2. Implement scalars in order: PhoneNumber → URL → Image → Money → ExchangeRate
3. Run tests after each scalar
4. Create integration tests
5. Update documentation

### Phase 2: Batch 2 Implementation (Next Week)

1. Create GitHub issues for Batch 2 scalars
2. Implement scalars in order: Color → Slug → Markdown → Percentage
3. Run tests after each scalar
4. Create integration tests
5. Update documentation

### Phase 3: Batch 3 Implementation (Weeks 3-4)

1. Create GitHub issues for Batch 3 scalars
2. Implement scalars in order: HTML → File → Time → Latitude → Longitude → Duration
3. Run tests after each scalar
4. Create integration tests
5. Update documentation
6. Final integration verification
7. Release notes

---

## References

- **FraiseQL Scalar Patterns**: `/home/lionel/code/fraiseql/src/fraiseql/types/scalars/`
- **Test Patterns**: `/home/lionel/code/fraiseql/tests/unit/core/type_system/test_hostname_scalar.py`
- **printoptim_backend_poc Entities**: `/home/lionel/code/printoptim_backend_poc/entities/`
- **Rich Types Spec**: `/home/lionel/code/printoptim_backend_poc/docs/teams/TEAM_A_RICH_TYPES_IMPLEMENTATION.md`
- **i18n Scalars Implementation**: `/home/lionel/code/fraiseql/docs/implementation-plans/I18N_SCALARS_IMPLEMENTATION_PLAN.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**Status**: Ready for Implementation
**Total Estimated Time**: 22-24 hours (3-4 weeks at current pace)
