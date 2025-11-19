# Internationalization (i18n) Entities: Multi-Language & Localization

> **7 standards-based entities for global applications—ISO 3166, ISO 639, BCP 47, ISO 4217 compliant**

## Overview

SpecQL's i18n stdlib provides **production-ready internationalization** with full standards compliance. These entities handle countries, languages, currencies, and locales for building truly global applications.

**Standards-Based**:
- **ISO 3166**: Country codes (alpha-2, alpha-3, numeric)
- **ISO 639**: Language codes (2-letter, 3-letter)
- **BCP 47**: Locale identifiers (en-US, fr-FR, etc.)
- **ISO 4217**: Currency codes (USD, EUR, JPY, etc.)

**Features**:
- Multi-language translations built-in
- Currency with symbols and formatting
- Country/continent hierarchies
- Locale preferences per country

**Origin**: Extracted from PrintOptim production system (international platform)

---

## Entities Overview

| Entity | Standard | Purpose | Examples |
|--------|----------|---------|----------|
| **Country** | ISO 3166-1 | Countries worldwide | US, FR, GB, DE |
| **Continent** | - | Geographic continents | Europe, Asia, Americas |
| **Language** | ISO 639 | Languages | en, fr, es, de, ja |
| **Locale** | BCP 47 | Locale identifiers | en-US, fr-FR, es-MX |
| **Currency** | ISO 4217 | Money and symbols | USD ($), EUR (€), JPY (¥) |
| **CountryLocale** | - | Country-specific locales | US → en-US, FR → fr-FR |

---

## Country Entity

### Purpose

**ISO 3166-1 compliant country reference** with:
- Alpha-2 codes (US, FR, GB)
- Continent classification
- Multi-language names
- Administrative hierarchies

### Schema Location

**Shared**: `common` schema

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | text | Yes | Country name (English) |
| `iso_code` | text | **Yes** | ISO 3166-1 alpha-2 (2 uppercase letters) |
| `continent` | ref(Continent) | Yes | Geographic continent |

**Validation**:
```sql
CONSTRAINT check_iso_code CHECK (iso_code ~ '^[A-Z]{2}$')
```

### Translation Support

```yaml
translations:
  enabled: true
  fields: [name, abbreviation, short_name, official_name]
```

**Result**: Country names in multiple languages.

### Pre-built Actions

```yaml
# CRUD
- create_country
- update_country
- delete_country

# Business Logic
- activate_country
- deactivate_country
- update_iso_code
- change_continent
```

### Usage Example

```yaml
from: stdlib/i18n/country.yaml
from: stdlib/i18n/continent.yaml

# Seed country data
action: seed_countries
  steps:
    - insert: Country VALUES (
        name: 'United States',
        iso_code: 'US',
        continent: ref(Continent[name='North America'])
      )
    - insert: Country VALUES (
        name: 'France',
        iso_code: 'FR',
        continent: ref(Continent[name='Europe'])
      )
    - insert: Country VALUES (
        name: 'Japan',
        iso_code: 'JP',
        continent: ref(Continent[name='Asia'])
      )
```

**Translations**:

```sql
-- French translations
INSERT INTO common.tb_country_i18n (country, lang, name, official_name)
VALUES
  (country_pk('US'), 'fr', 'États-Unis', 'États-Unis d''Amérique'),
  (country_pk('FR'), 'fr', 'France', 'République Française'),
  (country_pk('JP'), 'fr', 'Japon', 'Japon');

-- Spanish translations
INSERT INTO common.tb_country_i18n (country, lang, name, official_name)
VALUES
  (country_pk('US'), 'es', 'Estados Unidos', 'Estados Unidos de América'),
  (country_pk('FR'), 'es', 'Francia', 'República Francesa'),
  (country_pk('JP'), 'es', 'Japón', 'Japón');
```

---

## Language Entity

### Purpose

**ISO 639 compliant language reference** with:
- ISO 639-1 codes (2-letter: en, fr, es)
- ISO 639-2 codes (3-letter: eng, fra, spa)
- Multi-language names

### Schema Location

**Shared**: `common` schema

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | text | Yes | Language name (in English) |
| `iso_code_2` | text | Yes | ISO 639-1 (2-letter code) |
| `iso_code_3` | text | No | ISO 639-2 (3-letter code) |

**Validation**:
```sql
CONSTRAINT check_iso_code_2 CHECK (iso_code_2 ~ '^[a-z]{2}$')
CONSTRAINT check_iso_code_3 CHECK (iso_code_3 IS NULL OR iso_code_3 ~ '^[a-z]{3}$')
```

### Translation Support

```yaml
translations:
  enabled: true
  fields: [name]
```

**Result**: Language names in their own language (endonyms).

### Usage Example

```yaml
from: stdlib/i18n/language.yaml

# Seed major languages
action: seed_languages
  steps:
    - insert: Language VALUES (name: 'English', iso_code_2: 'en', iso_code_3: 'eng')
    - insert: Language VALUES (name: 'French', iso_code_2: 'fr', iso_code_3: 'fra')
    - insert: Language VALUES (name: 'Spanish', iso_code_2: 'es', iso_code_3: 'spa')
    - insert: Language VALUES (name: 'German', iso_code_2: 'de', iso_code_3: 'deu')
    - insert: Language VALUES (name: 'Japanese', iso_code_2: 'ja', iso_code_3: 'jpn')
    - insert: Language VALUES (name: 'Chinese', iso_code_2: 'zh', iso_code_3: 'zho')
```

**Endonym Translations**:

```sql
-- Languages in their own language
INSERT INTO common.tb_language_i18n (language, lang, name)
VALUES
  (language_pk('en'), 'en', 'English'),
  (language_pk('fr'), 'fr', 'Français'),
  (language_pk('es'), 'es', 'Español'),
  (language_pk('de'), 'de', 'Deutsch'),
  (language_pk('ja'), 'ja', '日本語'),
  (language_pk('zh'), 'zh', '中文');
```

---

## Currency Entity

### Purpose

**ISO 4217 compliant currency reference** with:
- 3-letter currency codes (USD, EUR, GBP)
- Currency symbols ($, €, £)
- Multi-language names

### Schema Location

**Shared**: `common` schema

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | text | **Yes** | ISO 4217 alphabetic code (3 uppercase) |
| `symbol` | text | No | Currency symbol |

**Validation**:
```sql
CONSTRAINT check_currency_code CHECK (code ~ '^[A-Z]{3}$')
```

### Translation Support

```yaml
translations:
  enabled: true
  fields: [name]
```

**Result**: Currency names in multiple languages.

### Pre-built Actions

```yaml
# CRUD
- create_currency
- update_currency
- delete_currency

# Business Logic
- activate_currency
- deactivate_currency
- update_symbol
- get_exchange_rate
```

### Usage Example

```yaml
from: stdlib/i18n/currency.yaml

# Seed major currencies
action: seed_currencies
  steps:
    - insert: Currency VALUES (code: 'USD', symbol: '$')
    - insert: Currency VALUES (code: 'EUR', symbol: '€')
    - insert: Currency VALUES (code: 'GBP', symbol: '£')
    - insert: Currency VALUES (code: 'JPY', symbol: '¥')
    - insert: Currency VALUES (code: 'CNY', symbol: '¥')
    - insert: Currency VALUES (code: 'CHF', symbol: 'Fr')
```

**Translations**:

```sql
-- Currency names in multiple languages
INSERT INTO common.tb_currency_i18n (currency, lang, name)
VALUES
  (currency_pk('USD'), 'en', 'US Dollar'),
  (currency_pk('USD'), 'fr', 'Dollar Américain'),
  (currency_pk('USD'), 'es', 'Dólar Estadounidense'),

  (currency_pk('EUR'), 'en', 'Euro'),
  (currency_pk('EUR'), 'fr', 'Euro'),
  (currency_pk('EUR'), 'es', 'Euro'),

  (currency_pk('JPY'), 'en', 'Japanese Yen'),
  (currency_pk('JPY'), 'fr', 'Yen Japonais'),
  (currency_pk('JPY'), 'ja', '日本円');
```

---

## Locale Entity

### Purpose

**BCP 47 compliant locale identifiers** with:
- Language-region combinations (en-US, fr-FR)
- Script variants (zh-Hans, zh-Hant)
- Formatting preferences

### Schema Location

**Shared**: `common` schema

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | text | **Yes** | BCP 47 locale code |
| `language` | ref(Language) | Yes | ISO 639 language |

**Validation**:
```sql
-- BCP 47 pattern: language-region (en-US) or language-script-region (zh-Hans-CN)
CONSTRAINT check_locale_code CHECK (code ~ '^[a-z]{2}(-[A-Z][a-z]{3})?-[A-Z]{2}$')
```

### Usage Example

```yaml
from: stdlib/i18n/locale.yaml
from: stdlib/i18n/language.yaml

# Seed common locales
action: seed_locales
  steps:
    - insert: Locale VALUES (
        code: 'en-US',
        language: ref(Language[iso_code_2='en'])
      )
    - insert: Locale VALUES (
        code: 'en-GB',
        language: ref(Language[iso_code_2='en'])
      )
    - insert: Locale VALUES (
        code: 'fr-FR',
        language: ref(Language[iso_code_2='fr'])
      )
    - insert: Locale VALUES (
        code: 'es-MX',
        language: ref(Language[iso_code_2='es'])
      )
    - insert: Locale VALUES (
        code: 'zh-Hans-CN',  # Simplified Chinese
        language: ref(Language[iso_code_2='zh'])
      )
```

---

## CountryLocale Entity

### Purpose

**Map countries to their default/supported locales**:
- US → en-US
- FR → fr-FR
- CH → de-CH, fr-CH, it-CH

### Fields

| Field | References | Description |
|-------|------------|-------------|
| `country` | Country | ISO 3166 country |
| `locale` | Locale | BCP 47 locale |
| `is_default` | boolean | Primary locale for country |

### Usage Example

```yaml
from: stdlib/i18n/country_locale.yaml

# Map countries to locales
action: seed_country_locales
  steps:
    # US: English only
    - insert: CountryLocale VALUES (
        country: ref(Country[iso_code='US']),
        locale: ref(Locale[code='en-US']),
        is_default: true
      )

    # Switzerland: Multi-language
    - insert: CountryLocale VALUES (
        country: ref(Country[iso_code='CH']),
        locale: ref(Locale[code='de-CH']),
        is_default: true  # German is primary
      )
    - insert: CountryLocale VALUES (
        country: ref(Country[iso_code='CH']),
        locale: ref(Locale[code='fr-CH']),
        is_default: false
      )
    - insert: CountryLocale VALUES (
        country: ref(Country[iso_code='CH']),
        locale: ref(Locale[code='it-CH']),
        is_default: false
      )
```

---

## Continent Entity

### Purpose

Geographic continent classification for countries.

### Usage Example

```yaml
from: stdlib/i18n/continent.yaml

# Seed continents
action: seed_continents
  steps:
    - insert: Continent VALUES (name: 'Africa')
    - insert: Continent VALUES (name: 'Antarctica')
    - insert: Continent VALUES (name: 'Asia')
    - insert: Continent VALUES (name: 'Europe')
    - insert: Continent VALUES (name: 'North America')
    - insert: Continent VALUES (name: 'Oceania')
    - insert: Continent VALUES (name: 'South America')
```

---

## Complete i18n Example

### Scenario: Global E-Commerce Platform

```yaml
# File: entities/global_store.yaml

# Import i18n entities
from: stdlib/i18n/country.yaml
from: stdlib/i18n/language.yaml
from: stdlib/i18n/currency.yaml
from: stdlib/i18n/locale.yaml
from: stdlib/i18n/country_locale.yaml

# Import other entities
from: stdlib/crm/contact.yaml
from: stdlib/commerce/price.yaml
from: stdlib/commerce/order.yaml

# Extend Contact with localization
extend: Contact
  custom_fields:
    preferred_language: ref(Language)
    preferred_currency: ref(Currency)
    country: ref(Country)
    locale: ref(Locale)

# Extend Order with multi-currency
extend: Order
  custom_fields:
    currency: ref(Currency)
    exchange_rate: decimal(10,4)
    total_in_usd: money  # Normalized for reporting

# Custom actions
action: set_user_locale
  entity: Contact
  steps:
    # Auto-detect locale from country
    - query: SELECT locale FROM CountryLocale
      WHERE country = $contact_country AND is_default = true
      result: $default_locale

    - update: Contact
      SET locale = $default_locale,
          language = locale.language,
          currency = country.default_currency

action: create_localized_order
  entity: Order
  steps:
    # Get customer preferences
    - query: SELECT preferred_currency, locale FROM Contact WHERE id = $customer_id
      result: $prefs

    # Create order with customer currency
    - insert: Order
      VALUES (
        customer: $customer_id,
        currency: $prefs.preferred_currency,
        locale: $prefs.locale
      )

    # Calculate prices in customer currency
    - foreach: cart_items
      - call: convert_price(
          amount: $item.price,
          from_currency: 'USD',
          to_currency: $prefs.preferred_currency
        )
        result: $localized_price

action: format_localized_amount
  input:
    amount: money
    currency: ref(Currency)
    locale: ref(Locale)
  steps:
    # Return formatted string based on locale
    # en-US: $1,234.56
    # fr-FR: 1 234,56 €
    # de-DE: 1.234,56 €
    - call: number_format($amount, $locale.decimal_separator, $locale.thousands_separator)
    - return: $currency.symbol + ' ' + $formatted
```

### Generated Functions

```sql
-- Auto-detect user locale from country
CREATE FUNCTION tenant.set_user_locale(contact_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
  user_country INTEGER;
  default_locale_id INTEGER;
  default_lang INTEGER;
  default_currency INTEGER;
BEGIN
  -- Get contact's country
  SELECT country INTO user_country
  FROM tenant.tb_contact WHERE id = contact_id;

  -- Find default locale for country
  SELECT locale, language, currency
  INTO default_locale_id, default_lang, default_currency
  FROM common.tb_country_locale cl
  INNER JOIN common.tb_locale l ON cl.locale = l.pk_locale
  WHERE cl.country = user_country AND cl.is_default = true
  LIMIT 1;

  -- Update contact preferences
  UPDATE tenant.tb_contact
  SET locale = default_locale_id,
      preferred_language = default_lang,
      preferred_currency = default_currency
  WHERE id = contact_id;

  RETURN app.success_result('Locale configured');
END;
$$ LANGUAGE plpgsql;
```

---

## Integration Examples

### i18n + CRM

```yaml
from: stdlib/crm/contact.yaml
from: stdlib/i18n/language.yaml
from: stdlib/i18n/country.yaml

extend: Contact
  custom_fields:
    preferred_language: ref(Language)
    country: ref(Country)

# Send emails in user's language
action: send_welcome_email
  entity: Contact
  steps:
    - call: get_translation('welcome_email', $contact.preferred_language)
      result: $email_template
    - notify: email($contact.email, $email_template)
```

---

### i18n + Commerce

```yaml
from: stdlib/commerce/price.yaml
from: stdlib/i18n/currency.yaml

extend: Price
  custom_fields:
    currency: ref(Currency)

# Multi-currency pricing
action: get_price_in_currency
  input:
    product_id: text
    currency_code: text
  steps:
    - query: SELECT amount FROM Price
      WHERE product = $product_id
        AND currency = currency_pk($currency_code)
      result: $price
    - return: $price
```

---

### i18n + Geo

```yaml
from: stdlib/geo/public_address.yaml
from: stdlib/i18n/country.yaml

# Country reference is built-in
extend: PublicAddress
  custom_fields:
    country: ref(Country)
```

---

## Performance: Caching

i18n entities are **reference data** (rarely changes):

```sql
-- Cache-friendly queries
SELECT code, symbol FROM common.tb_currency;  -- 170 rows, cache forever

SELECT iso_code, name FROM common.tb_country;  -- 250 rows, cache forever

SELECT code FROM common.tb_locale;  -- ~400 rows, cache 24 hours
```

**Best Practice**: Load once at application startup, cache in Redis/memory.

---

## Security: Read-Only

i18n entities are typically **read-only** in production:

```sql
-- Restrict writes
REVOKE INSERT, UPDATE, DELETE ON common.tb_country FROM app_user;
REVOKE INSERT, UPDATE, DELETE ON common.tb_currency FROM app_user;

GRANT SELECT ON common.tb_country TO app_user;
GRANT SELECT ON common.tb_currency TO app_user;
```

---

## Data Seeding

SpecQL provides **seed scripts** for all i18n entities:

```bash
# Seed all i18n data
specql seed stdlib/i18n/*.yaml --output db/seed/

# Generated seed files:
# - seed_countries.sql (250 countries)
# - seed_languages.sql (100+ languages)
# - seed_currencies.sql (170 currencies)
# - seed_locales.sql (400+ locales)
# - seed_continents.sql (7 continents)
```

**Source**: ISO official data (updated quarterly).

---

## Key Takeaways

1. **Standards-Compliant**: ISO 3166, 639, 4217, BCP 47
2. **Multi-Language**: Automatic translations for all entities
3. **Production-Ready**: Real-world data, tested in international platforms
4. **Composable**: Integrate with CRM, Commerce, Geo modules
5. **Cache-Friendly**: Reference data, perfect for edge caching

**Build global applications with proper i18n from day one.** 🌍

---

*Last updated: 2025-11-19*
