# FraiseQL i18n Scalar Types

**Status**: Implemented (FraiseQL Issue #127)
**Version**: FraiseQL 0.x+
**Date**: 2025-11-09

---

## Overview

FraiseQL now provides three specialized scalar types for internationalization (i18n) and localization support:

1. **`LanguageCode`** - ISO 639-1 two-letter language codes
2. **`LocaleCode`** - BCP 47 locale format (language-REGION)
3. **`Timezone`** - IANA timezone database identifiers

These scalars provide type-safe validation for multi-language, multi-region applications and are essential for any global SaaS platform.

---

## Quick Reference

### Import

```python
from fraiseql.types import LanguageCode, LocaleCode, Timezone
```

### Usage Examples

```python
from fraiseql.types import type, input, LanguageCode, LocaleCode, Timezone

@type(sql_source="app.users")
class User:
    id: int
    name: str
    email: EmailAddress
    preferred_language: LanguageCode  # e.g., "en", "fr", "de"
    locale: LocaleCode                 # e.g., "en-US", "fr-FR"
    timezone: Timezone                 # e.g., "America/New_York"

@input
class UpdateUserPreferencesInput:
    preferred_language: LanguageCode | None
    locale: LocaleCode | None
    timezone: Timezone | None
```

---

## LanguageCode

**ISO 639-1 two-letter language codes**

### Validation Rules

- **Format**: Exactly 2 lowercase letters (a-z)
- **Case-insensitive**: Input normalized to lowercase
- **Standard**: ISO 639-1
- **Examples**: `en`, `fr`, `de`, `es`, `ja`, `zh`, `ar`, `ru`, `pt`, `it`

### Python Usage

```python
from fraiseql.types import LanguageCode

# Valid
lang = LanguageCode("en")      # "en"
lang = LanguageCode("FR")      # "fr" (normalized)
lang = LanguageCode("de")      # "de"

# Invalid - raises ValueError
LanguageCode("eng")           # Too long
LanguageCode("e")             # Too short
LanguageCode("en-US")         # Use LocaleCode instead
LanguageCode("english")       # Must be 2 letters
```

### GraphQL Schema

```graphql
"""ISO 639-1 two-letter language code."""
scalar LanguageCode

type User {
  preferredLanguage: LanguageCode
  fallbackLanguage: LanguageCode
}

input UserPreferencesInput {
  language: LanguageCode
}
```

### PostgreSQL Integration

```sql
CREATE TABLE app.users (
    id UUID PRIMARY KEY,
    preferred_language TEXT
        CHECK (preferred_language ~ '^[a-z]{2}$'),

    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON COLUMN app.users.preferred_language IS
    'ISO 639-1 two-letter language code (e.g., en, fr, de)';
```

### Use Cases

- **Content Translation**: Specify which language to serve content in
- **UI Localization**: User interface language preference
- **Content Filtering**: Filter articles/products by language
- **SEO**: Language metadata for search engines

---

## LocaleCode

**BCP 47 locale format for regional/cultural preferences**

### Validation Rules

- **Format**: `language` OR `language-REGION`
  - Language: 2 lowercase letters (ISO 639-1)
  - Region: 2 uppercase letters (ISO 3166-1 alpha-2)
- **Case-sensitive**: Must match exact format (lowercase-UPPERCASE)
- **Standard**: BCP 47
- **Examples**: `en-US`, `en-GB`, `fr-FR`, `fr-CA`, `de-DE`, `es-ES`, `ja-JP`, `zh-CN`, `pt-BR`

### Python Usage

```python
from fraiseql.types import LocaleCode

# Valid
locale = LocaleCode("en-US")   # "en-US"
locale = LocaleCode("fr-FR")   # "fr-FR"
locale = LocaleCode("en")      # "en" (language-only accepted)

# Invalid - raises ValueError
LocaleCode("EN-us")           # Wrong case (must be lowercase-UPPERCASE)
LocaleCode("en_US")           # Underscore not allowed (use hyphen)
LocaleCode("en-USA")          # Region must be 2 letters
LocaleCode("eng-US")          # Language must be 2 letters
```

### GraphQL Schema

```graphql
"""BCP 47 locale code (language-REGION format)."""
scalar LocaleCode

type User {
  locale: LocaleCode!           # For formatting preferences
  preferredLanguage: LanguageCode  # For content translation
}

input UpdateLocaleInput {
  locale: LocaleCode!
}
```

### PostgreSQL Integration

```sql
CREATE TABLE app.users (
    id UUID PRIMARY KEY,
    locale TEXT
        CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$'),

    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON COLUMN app.users.locale IS
    'BCP 47 locale code for formatting (e.g., en-US, fr-FR)';
```

### Use Cases

- **Number Formatting**: Display prices correctly ($1,234.56 vs 1.234,56 €)
- **Date Formatting**: Regional date formats (MM/DD/YYYY vs DD/MM/YYYY)
- **Currency Display**: Currency symbols and placement
- **Measurement Units**: Imperial vs Metric
- **Address Formats**: Regional address field ordering

### LanguageCode vs LocaleCode

| Aspect | LanguageCode | LocaleCode |
|--------|--------------|------------|
| **Purpose** | Content translation | Formatting preferences |
| **Format** | `en` | `en-US`, `en-GB` |
| **Example** | UI language | Date/number format |
| **Granularity** | Language only | Language + Region |

**Example**:
```python
# Canadian user who speaks French but prefers English UI
class User:
    preferred_language: LanguageCode = "en"  # Show UI in English
    locale: LocaleCode = "fr-CA"              # Format dates/numbers Canadian French style
```

---

## Timezone

**IANA timezone database identifiers for timezone-aware applications**

### Validation Rules

- **Format**: `Region/City` or `Region/City/Locality`
  - Each component starts with uppercase letter
  - Can contain letters (a-z, A-Z) and underscores
- **Case-sensitive**: Exact capitalization required
- **Standard**: IANA Timezone Database (tz database)
- **Examples**:
  - Two-part: `America/New_York`, `Europe/Paris`, `Asia/Tokyo`, `Pacific/Auckland`
  - Three-part: `America/Argentina/Buenos_Aires`, `America/Indiana/Indianapolis`

### Python Usage

```python
from fraiseql.types import Timezone

# Valid
tz = Timezone("America/New_York")              # "America/New_York"
tz = Timezone("Europe/Paris")                  # "Europe/Paris"
tz = Timezone("Asia/Tokyo")                    # "Asia/Tokyo"
tz = Timezone("America/Argentina/Buenos_Aires") # "America/Argentina/Buenos_Aires"

# Invalid - raises ValueError
Timezone("EST")                    # Abbreviations not supported
Timezone("UTC+5")                  # Offsets not supported
Timezone("GMT-8")                  # Offsets not supported
Timezone("america/new_york")       # Wrong capitalization
Timezone("NewYork")                # Must have Region/City format
```

### GraphQL Schema

```graphql
"""IANA timezone database identifier."""
scalar Timezone

type User {
  timezone: Timezone!
}

input ScheduleEventInput {
  startTime: DateTime!
  timezone: Timezone!  # For display in user's local time
}
```

### PostgreSQL Integration

```sql
CREATE TABLE app.users (
    id UUID PRIMARY KEY,
    timezone TEXT
        CHECK (timezone ~ '^[A-Z][a-zA-Z_]+(/[A-Z][a-zA-Z_]+){1,2}$'),

    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON COLUMN app.users.timezone IS
    'IANA timezone identifier (e.g., America/New_York, Europe/Paris)';
```

### Use Cases

- **Timestamp Display**: Show all times in user's local timezone
- **Scheduling**: Event scheduling with correct DST handling
- **Email Notifications**: Send emails at appropriate local times
- **Reporting**: Generate reports in user's timezone
- **Meeting Coordination**: Schedule meetings across timezones

### Why IANA Timezones (Not UTC Offsets)

❌ **UTC Offset** (`UTC+5`, `GMT-8`):
- Breaks during Daylight Saving Time transitions
- Static offset doesn't adjust seasonally
- Ambiguous (which regions use UTC+5?)

✅ **IANA Timezone** (`America/New_York`):
- Automatically handles DST transitions
- Historical accuracy for past dates
- Future-proof for DST rule changes
- Clear geographic meaning

**Example**:
```python
# BAD: UTC offset breaks with DST
# New York is UTC-5 in winter, UTC-4 in summer
user_offset = "UTC-5"  # Wrong half the year!

# GOOD: IANA timezone handles DST automatically
user_timezone = Timezone("America/New_York")  # Always correct
```

---

## Integration Patterns

### Multi-tenant SaaS Platform

```python
from fraiseql.types import type, LanguageCode, LocaleCode, Timezone, EmailAddress

@type(sql_source="app.users")
class User:
    id: UUID
    email: EmailAddress
    name: str

    # i18n preferences
    preferred_language: LanguageCode   # UI language
    locale: LocaleCode                 # Formatting preferences
    timezone: Timezone                 # Timestamp display

    created_at: DateTime

# GraphQL output
"""
type User {
  id: UUID!
  email: EmailAddress!
  name: String!
  preferredLanguage: LanguageCode!
  locale: LocaleCode!
  timezone: Timezone!
  createdAt: DateTime!
}
"""
```

### Content Management System

```python
@type(sql_source="app.articles")
class Article:
    id: int
    title: str
    content: str
    language: LanguageCode    # Content language (for SEO/filtering)
    published_at: DateTime

@input
class CreateArticleInput:
    title: str
    content: str
    language: LanguageCode    # Required: which language is this content in?
```

### Event Scheduling Platform

```python
@type(sql_source="app.events")
class Event:
    id: UUID
    title: str
    description: str
    start_time: DateTime
    end_time: DateTime
    timezone: Timezone        # Event timezone (handles DST correctly)

@input
class CreateEventInput:
    title: str
    description: str
    start_time: DateTime
    end_time: DateTime
    timezone: Timezone        # Required: event timezone

# Example: Schedule event in New York
mutation {
  createEvent(input: {
    title: "Product Launch"
    description: "Q1 2025 Product Launch Event"
    startTime: "2025-03-15T14:00:00Z"
    timezone: "America/New_York"  # 2:00 PM EST/EDT (auto-adjusts)
  }) {
    id
    startTime
    timezone
  }
}
```

### E-commerce Platform

```python
@type(sql_source="app.customers")
class Customer:
    id: UUID
    email: EmailAddress
    name: str

    # Formatting preferences
    locale: LocaleCode        # For price/date formatting
    timezone: Timezone        # For order confirmation emails

    created_at: DateTime

# Display price correctly based on locale
# en-US: $1,234.56
# fr-FR: 1 234,56 €
# de-DE: 1.234,56 €
```

### User Preferences Update

```python
@input
class UpdateUserPreferencesInput:
    preferred_language: LanguageCode | None
    locale: LocaleCode | None
    timezone: Timezone | None

mutation UpdatePreferences {
  updateUserPreferences(input: {
    preferredLanguage: "fr"
    locale: "fr-CA"
    timezone: "America/Toronto"
  }) {
    id
    preferredLanguage
    locale
    timezone
  }
}
```

---

## Complete Database Schema Example

```sql
-- Multi-tenant SaaS users table with full i18n support
CREATE TABLE app.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,

    -- i18n preferences with validation
    preferred_language TEXT NOT NULL DEFAULT 'en'
        CHECK (preferred_language ~ '^[a-z]{2}$'),

    locale TEXT NOT NULL DEFAULT 'en-US'
        CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$'),

    timezone TEXT NOT NULL DEFAULT 'America/New_York'
        CHECK (timezone ~ '^[A-Z][a-zA-Z_]+(/[A-Z][a-zA-Z_]+){1,2}$'),

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add helpful column comments
COMMENT ON COLUMN app.users.preferred_language IS
    'ISO 639-1 two-letter language code for UI translation (e.g., en, fr, de)';

COMMENT ON COLUMN app.users.locale IS
    'BCP 47 locale code for date/number/currency formatting (e.g., en-US, fr-FR)';

COMMENT ON COLUMN app.users.timezone IS
    'IANA timezone identifier for timestamp display (e.g., America/New_York, Europe/Paris)';

-- Index for common queries
CREATE INDEX idx_users_language ON app.users(preferred_language);
CREATE INDEX idx_users_locale ON app.users(locale);

-- Example data
INSERT INTO app.users (email, name, preferred_language, locale, timezone) VALUES
    ('john@example.com', 'John Doe', 'en', 'en-US', 'America/New_York'),
    ('marie@example.fr', 'Marie Dubois', 'fr', 'fr-FR', 'Europe/Paris'),
    ('hans@example.de', 'Hans Schmidt', 'de', 'de-DE', 'Europe/Berlin'),
    ('yuki@example.jp', 'Yuki Tanaka', 'ja', 'ja-JP', 'Asia/Tokyo');
```

---

## Validation Examples

### Valid Values

```python
# LanguageCode - ISO 639-1
✅ LanguageCode("en")       # English
✅ LanguageCode("FR")       # French (normalized to "fr")
✅ LanguageCode("de")       # German
✅ LanguageCode("ja")       # Japanese
✅ LanguageCode("zh")       # Chinese
✅ LanguageCode("ar")       # Arabic

# LocaleCode - BCP 47
✅ LocaleCode("en-US")      # English (United States)
✅ LocaleCode("en-GB")      # English (United Kingdom)
✅ LocaleCode("fr-FR")      # French (France)
✅ LocaleCode("fr-CA")      # French (Canada)
✅ LocaleCode("en")         # English (language-only)

# Timezone - IANA
✅ Timezone("America/New_York")
✅ Timezone("Europe/Paris")
✅ Timezone("Asia/Tokyo")
✅ Timezone("Pacific/Auckland")
✅ Timezone("America/Argentina/Buenos_Aires")
```

### Invalid Values

```python
# LanguageCode - Invalid
❌ LanguageCode("eng")        # Too long (must be 2 letters)
❌ LanguageCode("e")          # Too short
❌ LanguageCode("en-US")      # Use LocaleCode for this
❌ LanguageCode("english")    # Must be 2 letters
❌ LanguageCode("e1")         # No numbers allowed

# LocaleCode - Invalid
❌ LocaleCode("EN-us")        # Wrong case (must be lowercase-UPPERCASE)
❌ LocaleCode("en_US")        # Use hyphen, not underscore
❌ LocaleCode("en-USA")       # Region must be 2 letters
❌ LocaleCode("eng-US")       # Language must be 2 letters

# Timezone - Invalid
❌ Timezone("EST")            # Abbreviations not supported
❌ Timezone("UTC+5")          # Offsets not supported
❌ Timezone("GMT-8")          # Offsets not supported
❌ Timezone("america/new_york") # Wrong capitalization
❌ Timezone("NewYork")        # Must have slash (Region/City)
```

---

## Error Messages

### GraphQL Errors

```graphql
# Invalid LanguageCode
mutation {
  updateUser(input: { language: "eng" })
}
# Error: "Invalid language code: eng. Must be ISO 639-1 two-letter code (e.g., 'en', 'fr', 'de')"

# Invalid LocaleCode
mutation {
  updateUser(input: { locale: "en_US" })
}
# Error: "Invalid locale code: en_US. Must be BCP 47 format (e.g., 'en-US', 'fr-FR', 'de-DE')"

# Invalid Timezone
mutation {
  updateUser(input: { timezone: "EST" })
}
# Error: "Invalid timezone: EST. Must be IANA timezone identifier (e.g., 'America/New_York', 'Europe/Paris')"
```

### Python Errors

```python
from fraiseql.types import LanguageCode, LocaleCode, Timezone

# ValueError with clear message
try:
    LanguageCode("english")
except ValueError as e:
    print(e)
    # "Invalid language code: english. Must be ISO 639-1 two-letter code (e.g., 'en', 'fr', 'de')"

try:
    LocaleCode("en_US")
except ValueError as e:
    print(e)
    # "Invalid locale code: en_US. Must be BCP 47 format (e.g., 'en-US', 'fr-FR', 'de-DE')"

try:
    Timezone("EST")
except ValueError as e:
    print(e)
    # "Invalid timezone: EST. Must be IANA timezone identifier (e.g., 'America/New_York', 'Europe/Paris')"
```

---

## Benefits

### 1. Type Safety
- Prevent invalid language/locale/timezone values at API boundary
- Catch errors before database insert
- Better developer experience with IDE autocomplete

### 2. Self-Documenting
- GraphQL schema shows valid formats and examples
- Clear scalar descriptions
- Reference links to standards

### 3. Early Validation
- Validate at GraphQL layer (before business logic)
- Consistent error messages
- Prevents storage of malformed data

### 4. PostgreSQL Optimization
- CHECK constraints enable query optimization
- Indexed text columns with guaranteed format
- Database-level validation as backup layer

### 5. Universal Utility
- Every global application needs these types
- Common pattern across all multi-language/multi-region apps
- Reusable in any FraiseQL project

---

## Best Practices

### 1. Use Appropriate Scalar for Context

```python
class User:
    # For content translation
    preferred_language: LanguageCode  # "en", "fr", "de"

    # For formatting preferences
    locale: LocaleCode                # "en-US", "fr-FR", "de-DE"

    # For timestamp display
    timezone: Timezone                # "America/New_York"
```

### 2. Provide Sensible Defaults

```sql
-- Set defaults based on your primary market
CREATE TABLE app.users (
    preferred_language TEXT DEFAULT 'en',
    locale TEXT DEFAULT 'en-US',
    timezone TEXT DEFAULT 'America/New_York'
);
```

### 3. Allow Flexibility

```python
@input
class UpdateUserPreferencesInput:
    # Make all optional for partial updates
    preferred_language: LanguageCode | None
    locale: LocaleCode | None
    timezone: Timezone | None
```

### 4. Combine with Other i18n Tools

```python
# Example: Full i18n user profile
class User:
    # Identity
    id: UUID
    email: EmailAddress

    # i18n preferences
    preferred_language: LanguageCode   # UI language
    locale: LocaleCode                 # Formatting
    timezone: Timezone                 # Timestamps

    # Optional: Fallback languages
    fallback_languages: list[LanguageCode] | None
```

### 5. Document Business Logic

```python
# Clear documentation helps other developers
@type(sql_source="app.users")
class User:
    """User with full i18n support.

    - preferred_language: Language for UI/content translation
    - locale: Regional formatting for dates/numbers/currency
    - timezone: Display all timestamps in user's local time

    Example: French Canadian user
    - preferred_language: "fr"
    - locale: "fr-CA"
    - timezone: "America/Toronto"
    """
    preferred_language: LanguageCode
    locale: LocaleCode
    timezone: Timezone
```

---

## Common Timezones Reference

### United States
- `America/New_York` - Eastern Time
- `America/Chicago` - Central Time
- `America/Denver` - Mountain Time
- `America/Los_Angeles` - Pacific Time
- `America/Phoenix` - Arizona (no DST)
- `Pacific/Honolulu` - Hawaii

### Europe
- `Europe/London` - UK
- `Europe/Paris` - France, Spain (CET)
- `Europe/Berlin` - Germany (CET)
- `Europe/Rome` - Italy (CET)
- `Europe/Moscow` - Russia (MSK)

### Asia
- `Asia/Tokyo` - Japan
- `Asia/Shanghai` - China
- `Asia/Hong_Kong` - Hong Kong
- `Asia/Singapore` - Singapore
- `Asia/Dubai` - UAE
- `Asia/Kolkata` - India

### Oceania
- `Australia/Sydney` - Eastern Australia
- `Australia/Melbourne` - Eastern Australia
- `Pacific/Auckland` - New Zealand

### Latin America
- `America/Sao_Paulo` - Brazil
- `America/Argentina/Buenos_Aires` - Argentina
- `America/Mexico_City` - Mexico

---

## References

- **ISO 639-1 Language Codes**: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
- **BCP 47 Locale Format**: https://tools.ietf.org/html/bcp47
- **IANA Timezone Database**: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
- **Full Timezone List**: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
- **FraiseQL Documentation**: https://github.com/fraiseql/fraiseql
- **Implementation Plan**: `/home/lionel/code/fraiseql/docs/implementation-plans/I18N_SCALARS_IMPLEMENTATION_PLAN.md`

---

## Migration Guide

### Adding i18n Support to Existing Project

#### Step 1: Update Database Schema

```sql
-- Add columns to existing users table
ALTER TABLE app.users
    ADD COLUMN preferred_language TEXT DEFAULT 'en'
        CHECK (preferred_language ~ '^[a-z]{2}$'),
    ADD COLUMN locale TEXT DEFAULT 'en-US'
        CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$'),
    ADD COLUMN timezone TEXT DEFAULT 'America/New_York'
        CHECK (timezone ~ '^[A-Z][a-zA-Z_]+(/[A-Z][a-zA-Z_]+){1,2}$');

-- Add column comments
COMMENT ON COLUMN app.users.preferred_language IS
    'ISO 639-1 two-letter language code (e.g., en, fr, de)';
COMMENT ON COLUMN app.users.locale IS
    'BCP 47 locale code for formatting (e.g., en-US, fr-FR)';
COMMENT ON COLUMN app.users.timezone IS
    'IANA timezone identifier (e.g., America/New_York, Europe/Paris)';
```

#### Step 2: Update FraiseQL Types

```python
from fraiseql.types import type, LanguageCode, LocaleCode, Timezone

@type(sql_source="app.users")
class User:
    id: UUID
    email: EmailAddress
    name: str

    # NEW: i18n fields
    preferred_language: LanguageCode
    locale: LocaleCode
    timezone: Timezone
```

#### Step 3: Add Update Mutation

```python
@input
class UpdateUserPreferencesInput:
    preferred_language: LanguageCode | None
    locale: LocaleCode | None
    timezone: Timezone | None

# Mutation resolver will automatically validate
```

#### Step 4: Populate Defaults

```sql
-- Set defaults for existing users based on IP geolocation or account settings
UPDATE app.users SET
    preferred_language = 'en',
    locale = 'en-US',
    timezone = 'America/New_York'
WHERE preferred_language IS NULL;
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**Related Issue**: [FraiseQL #127](https://github.com/fraiseql/fraiseql/issues/127)
