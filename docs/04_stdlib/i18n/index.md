# Internationalization (i18n) Entities: Global Reach Made Easy

> **Production-proven localization and multi-language support**

## Overview

The SpecQL stdlib **internationalization (i18n) module** provides comprehensive support for building global applications with:
- **Multi-currency**: ISO 4217 currency codes and symbols
- **Multi-language**: ISO 639 language codes
- **Localization**: BCP 47 locale definitions with formatting rules
- **Geographic data**: ISO 3166 countries and continents
- **Translation support**: Built-in translation infrastructure

These entities are extracted from production systems serving international markets across 50+ countries.

## Quick Start

```yaml
# Import pre-built i18n entities
import:
  - stdlib/i18n/currency
  - stdlib/i18n/language
  - stdlib/i18n/locale
  - stdlib/i18n/country

# Use them in your entities
entity: Product
fields:
  name: text
  price_amount: money
  price_currency: ref(Currency)  # Multi-currency support!

translations:
  enabled: true
  fields: [name, description]  # Auto-translate these fields
```

**Result**: Instant international support with zero configuration.

---

## Core Entities

### 1. Currency

**Purpose**: ISO 4217 currency reference data

**Schema**: `common` (shared across tenants)

**Standard**: [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html)

**Use Cases**:
- E-commerce pricing
- International invoicing
- Financial reporting
- Currency conversion
- Multi-currency contracts

#### Fields

```yaml
entity: Currency
fields:
  # ISO standard fields
  code:
    type: text
    nullable: false
    description: "ISO 4217 alphabetic currency code (3 uppercase letters)"
    # Examples: USD, EUR, GBP, JPY

  symbol:
    type: text
    description: "Currency symbol: $, €, £, ¥, etc."

  # Translated fields
  translations:
    enabled: true
    fields: [name]  # "Euro", "US Dollar", "British Pound"
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_currency
  - update_currency
  - delete_currency

  # Management
  - activate_currency
  - deactivate_currency
  - update_symbol
  - get_exchange_rate
```

#### Example: Multi-Currency Pricing

```yaml
import:
  - stdlib/i18n/currency
  - stdlib/commerce/price

# Product with multiple currency prices
entity: ProductPrice
fields:
  product: ref(Product)
  amount: money
  currency: ref(Currency)

# Create prices in different currencies
action: create_product_price
inputs:
  product_id: {identifier: "laptop-pro"}
  amount: 999.00
  currency: {code: "USD"}

action: create_product_price
inputs:
  product_id: {identifier: "laptop-pro"}
  amount: 899.00
  currency: {code: "EUR"}

action: create_product_price
inputs:
  product_id: {identifier: "laptop-pro"}
  amount: 799.00
  currency: {code: "GBP"}
```

**Generated SQL**:
```sql
-- Currency reference table
CREATE TABLE common.tb_currency (
  pk_currency INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  code TEXT NOT NULL,  -- ISO 4217
  symbol TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Unique constraint on currency code
CREATE UNIQUE INDEX idx_tb_currency_code
  ON common.tb_currency (code)
  WHERE deleted_at IS NULL;

-- Translation table (auto-generated from translations: enabled)
CREATE TABLE common.tb_currency_translation (
  pk_currency_translation INTEGER PRIMARY KEY,
  fk_currency INTEGER NOT NULL REFERENCES common.tb_currency(pk_currency),
  fk_language INTEGER NOT NULL REFERENCES common.tb_language(pk_language),

  name TEXT,  -- Translated currency name

  UNIQUE(fk_currency, fk_language)
);
```

#### Standard Currencies Pre-Loaded

```yaml
# Common currencies (examples)
currencies:
  - code: USD, symbol: "$",  name: "US Dollar"
  - code: EUR, symbol: "€",  name: "Euro"
  - code: GBP, symbol: "£",  name: "British Pound"
  - code: JPY, symbol: "¥",  name: "Japanese Yen"
  - code: CNY, symbol: "¥",  name: "Chinese Yuan"
  - code: CAD, symbol: "$",  name: "Canadian Dollar"
  - code: AUD, symbol: "$",  name: "Australian Dollar"
  - code: CHF, symbol: "Fr", name: "Swiss Franc"
  - code: INR, symbol: "₹",  name: "Indian Rupee"
  - code: BRL, symbol: "R$", name: "Brazilian Real"
```

---

### 2. Language

**Purpose**: ISO 639 language reference data

**Schema**: `common` (shared across tenants)

**Standard**: [ISO 639-1](https://www.iso.org/iso-639-language-codes.html) / [ISO 639-2](https://www.loc.gov/standards/iso639-2/)

**Use Cases**:
- Content translation
- User interface localization
- Document management
- Customer communication
- Multi-language support

#### Fields

```yaml
entity: Language
fields:
  name: text          # "English", "French", "German"

  iso_code:
    type: text
    nullable: false
    description: "ISO 639-1 alpha-2 language code (2 lowercase letters)"
    # Examples: en, fr, de, es, zh, ar
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_language
  - update_language
  - delete_language

  # Management
  - activate_language
  - deactivate_language
  - update_iso_code
```

#### Example: Multi-Language Content

```yaml
import:
  - stdlib/i18n/language

entity: BlogPost
fields:
  title: text
  content: text
  author: ref(User)

translations:
  enabled: true
  fields: [title, content]  # Auto-create translation tables

# Create blog post
action: create_blog_post
inputs:
  title: "Getting Started with SpecQL"
  content: "SpecQL is a powerful code generator..."
  author: {identifier: "john-doe"}

# Add French translation
action: add_translation
inputs:
  entity: BlogPost
  entity_id: {identifier: "blog-post-123"}
  language: {iso_code: "fr"}
  translations:
    title: "Démarrer avec SpecQL"
    content: "SpecQL est un générateur de code puissant..."

# Add German translation
action: add_translation
inputs:
  entity: BlogPost
  entity_id: {identifier: "blog-post-123"}
  language: {iso_code: "de"}
  translations:
    title: "Erste Schritte mit SpecQL"
    content: "SpecQL ist ein leistungsstarker Code-Generator..."
```

**Generated SQL**:
```sql
-- Language reference table
CREATE TABLE common.tb_language (
  pk_language INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  name TEXT NOT NULL,
  iso_code TEXT NOT NULL,  -- ISO 639-1

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Unique constraint on language code
CREATE UNIQUE INDEX idx_tb_language_iso_code
  ON common.tb_language (iso_code)
  WHERE deleted_at IS NULL;

-- Auto-generated translation table for BlogPost
CREATE TABLE tenant.tb_blog_post_translation (
  pk_blog_post_translation INTEGER PRIMARY KEY,
  fk_blog_post INTEGER NOT NULL REFERENCES tenant.tb_blog_post(pk_blog_post),
  fk_language INTEGER NOT NULL REFERENCES common.tb_language(pk_language),

  title TEXT,
  content TEXT,

  tenant_id UUID NOT NULL,

  UNIQUE(fk_blog_post, fk_language, tenant_id)
);

-- Translation lookup function (auto-generated)
CREATE FUNCTION tenant.get_blog_post_translation(
  p_blog_post_id UUID,
  p_language_code TEXT
) RETURNS TABLE(
  title TEXT,
  content TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    bt.title,
    bt.content
  FROM tenant.tb_blog_post_translation bt
  JOIN common.tb_language l ON bt.fk_language = l.pk_language
  WHERE bt.fk_blog_post = (
          SELECT pk_blog_post FROM tenant.tb_blog_post WHERE id = p_blog_post_id
        )
    AND l.iso_code = p_language_code;
END;
$$ LANGUAGE plpgsql;
```

#### Standard Languages Pre-Loaded

```yaml
# Common languages (examples)
languages:
  - iso_code: en, name: "English"
  - iso_code: es, name: "Spanish"
  - iso_code: fr, name: "French"
  - iso_code: de, name: "German"
  - iso_code: it, name: "Italian"
  - iso_code: pt, name: "Portuguese"
  - iso_code: zh, name: "Chinese"
  - iso_code: ja, name: "Japanese"
  - iso_code: ar, name: "Arabic"
  - iso_code: ru, name: "Russian"
  - iso_code: hi, name: "Hindi"
  - iso_code: ko, name: "Korean"
```

---

### 3. Locale

**Purpose**: BCP 47 locale definitions with formatting rules

**Schema**: `common` (shared across tenants)

**Standard**: [BCP 47](https://www.rfc-editor.org/rfc/rfc5646.html)

**Use Cases**:
- Regional number formatting
- Date/time formatting
- Currency display
- Right-to-left (RTL) languages
- User preferences

#### Fields

```yaml
entity: Locale
fields:
  # Identification
  code: text     # "en-US", "fr-CA", "de-DE", "ar-SA"
  name: text     # "English (United States)"
  flag: text     # Emoji flag or country code

  # Number formatting
  numeric_pattern: text        # "#,##0.##"
  decimal_separator: text      # "." (US) or "," (EU)
  grouping_separator: text     # "," (US) or " " (FR)
  currency_pattern: text       # "$#,##0.00" or "#,##0.00 €"

  # Status
  is_default: boolean          # Default locale for the system
  is_active: boolean           # Currently enabled
  is_rtl: boolean             # Right-to-left script (Arabic, Hebrew)

  # Reference
  language: ref(Language)      # Base language
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_locale
  - update_locale
  - delete_locale

  # Management
  - activate_locale
  - deactivate_locale
  - update_formatting
  - change_language
  - set_as_default
```

#### Example: Locale-Aware Formatting

```yaml
import:
  - stdlib/i18n/locale
  - stdlib/i18n/currency

# Format number based on locale
action: format_number
inputs:
  number: 1234567.89
  locale: {code: "en-US"}
output:
  formatted: "1,234,567.89"  # US format

action: format_number
inputs:
  number: 1234567.89
  locale: {code: "de-DE"}
output:
  formatted: "1.234.567,89"  # German format

# Format currency
action: format_currency
inputs:
  amount: 99.99
  currency: {code: "USD"}
  locale: {code: "en-US"}
output:
  formatted: "$99.99"

action: format_currency
inputs:
  amount: 99.99
  currency: {code: "EUR"}
  locale: {code: "fr-FR"}
output:
  formatted: "99,99 €"
```

**Generated SQL**:
```sql
-- Locale table
CREATE TABLE common.tb_locale (
  pk_locale INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  code TEXT NOT NULL,  -- BCP 47 locale code
  name TEXT NOT NULL,
  flag TEXT,

  numeric_pattern TEXT,
  decimal_separator TEXT DEFAULT '.',
  grouping_separator TEXT DEFAULT ',',
  currency_pattern TEXT,

  is_default BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  is_rtl BOOLEAN DEFAULT FALSE,

  fk_language INTEGER NOT NULL REFERENCES common.tb_language(pk_language),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Unique constraint on locale code
CREATE UNIQUE INDEX idx_tb_locale_code
  ON common.tb_locale (code)
  WHERE deleted_at IS NULL;

-- Only one default locale allowed
CREATE UNIQUE INDEX idx_tb_locale_default
  ON common.tb_locale (is_default)
  WHERE is_default = TRUE AND deleted_at IS NULL;

-- Number formatting function (auto-generated)
CREATE FUNCTION common.format_number(
  p_number NUMERIC,
  p_locale_code TEXT
) RETURNS TEXT AS $$
DECLARE
  v_decimal_separator TEXT;
  v_grouping_separator TEXT;
  v_numeric_pattern TEXT;
BEGIN
  SELECT
    decimal_separator,
    grouping_separator,
    numeric_pattern
  INTO
    v_decimal_separator,
    v_grouping_separator,
    v_numeric_pattern
  FROM common.tb_locale
  WHERE code = p_locale_code
    AND deleted_at IS NULL;

  -- Apply formatting based on locale
  -- (Implementation details omitted for brevity)
  RETURN formatted_result;
END;
$$ LANGUAGE plpgsql;
```

#### Standard Locales Pre-Loaded

```yaml
# Common locales (examples)
locales:
  # English variants
  - code: en-US, name: "English (United States)", decimal_separator: ".", grouping_separator: ","
  - code: en-GB, name: "English (United Kingdom)", decimal_separator: ".", grouping_separator: ","
  - code: en-CA, name: "English (Canada)", decimal_separator: ".", grouping_separator: ","

  # French variants
  - code: fr-FR, name: "French (France)", decimal_separator: ",", grouping_separator: " "
  - code: fr-CA, name: "French (Canada)", decimal_separator: ",", grouping_separator: " "

  # German
  - code: de-DE, name: "German (Germany)", decimal_separator: ",", grouping_separator: "."

  # Spanish
  - code: es-ES, name: "Spanish (Spain)", decimal_separator: ",", grouping_separator: "."
  - code: es-MX, name: "Spanish (Mexico)", decimal_separator: ".", grouping_separator: ","

  # RTL languages
  - code: ar-SA, name: "Arabic (Saudi Arabia)", is_rtl: true
  - code: he-IL, name: "Hebrew (Israel)", is_rtl: true
```

---

### 4. Country

**Purpose**: ISO 3166 country reference data

**Schema**: `common` (shared across tenants)

**Standard**: [ISO 3166-1](https://www.iso.org/iso-3166-country-codes.html)

**Use Cases**:
- Address validation
- Shipping restrictions
- Tax calculations
- Regional settings
- Geographic reporting

#### Fields

```yaml
entity: Country
fields:
  name: text

  iso_code:
    type: text
    nullable: false
    description: "ISO 3166-1 alpha-2 country code (2 uppercase letters)"
    # Examples: US, FR, GB, DE, JP

  continent: ref(Continent)

translations:
  enabled: true
  fields: [name, abbreviation, short_name, official_name]
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_country
  - update_country
  - delete_country

  # Management
  - activate_country
  - deactivate_country
  - update_iso_code
  - change_continent
```

#### Example: Country-Specific Logic

```yaml
import:
  - stdlib/i18n/country
  - stdlib/geo/public_address

# Validate shipping to country
action: check_shipping_availability
inputs:
  country_iso: text
steps:
  - query: |
      SELECT iso_code FROM Country
      WHERE iso_code = :country_iso
        AND iso_code NOT IN ('IR', 'KP', 'SY')  -- Restricted countries

  - if: query_result IS NULL
    then:
      - error: "Shipping not available to this country"

# Calculate tax based on country
action: calculate_sales_tax
inputs:
  amount: money
  country_iso: text
steps:
  - query: |
      SELECT tax_rate FROM CountryTaxRate
      WHERE country_iso = :country_iso

  - return:
      tax_amount: :amount * :tax_rate
      total_amount: :amount + (:amount * :tax_rate)
```

**Generated SQL**:
```sql
-- Country reference table
CREATE TABLE common.tb_country (
  pk_country INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  name TEXT NOT NULL,
  iso_code TEXT NOT NULL,  -- ISO 3166-1 alpha-2

  fk_continent INTEGER REFERENCES common.tb_continent(pk_continent),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Unique constraint on country code
CREATE UNIQUE INDEX idx_tb_country_iso_code
  ON common.tb_country (iso_code)
  WHERE deleted_at IS NULL;

-- Country translation table
CREATE TABLE common.tb_country_translation (
  pk_country_translation INTEGER PRIMARY KEY,
  fk_country INTEGER NOT NULL REFERENCES common.tb_country(pk_country),
  fk_language INTEGER NOT NULL REFERENCES common.tb_language(pk_language),

  name TEXT,
  abbreviation TEXT,
  short_name TEXT,
  official_name TEXT,

  UNIQUE(fk_country, fk_language)
);
```

---

### 5. Continent

**Purpose**: Continental grouping for countries

**Schema**: `common` (shared across tenants)

**Use Cases**:
- Geographic reporting
- Regional filtering
- Market segmentation

#### Fields

```yaml
entity: Continent
fields:
  name: text  # Africa, Antarctica, Asia, Europe, North America, Oceania, South America
  code: text  # AF, AN, AS, EU, NA, OC, SA

translations:
  enabled: true
  fields: [name]
```

---

## Complete Integration Example

### Global E-Commerce Platform

```yaml
# Import i18n foundation
import:
  - stdlib/i18n/currency
  - stdlib/i18n/language
  - stdlib/i18n/locale
  - stdlib/i18n/country
  - stdlib/i18n/continent
  - stdlib/commerce/price
  - stdlib/crm/contact

# Multi-language product catalog
entity: Product
fields:
  sku: text
  base_price: money
  base_currency: ref(Currency)

translations:
  enabled: true
  fields: [name, description, marketing_text]

# User preferences
entity: UserPreferences
fields:
  user: ref(User)
  preferred_language: ref(Language)
  preferred_locale: ref(Locale)
  preferred_currency: ref(Currency)

# Multi-currency pricing
entity: ProductPrice
fields:
  product: ref(Product)
  currency: ref(Currency)
  amount: money
  effective_date: date

# Localized checkout
actions:
  - name: get_product_for_user
    inputs:
      product_id: uuid
      user_id: uuid
    steps:
      # Get user preferences
      - query: |
          SELECT
            up.preferred_language,
            up.preferred_locale,
            up.preferred_currency
          FROM UserPreferences up
          WHERE up.user = :user_id

      # Get translated product info
      - query: |
          SELECT
            pt.name,
            pt.description
          FROM Product_Translation pt
          WHERE pt.product = :product_id
            AND pt.language = :preferred_language

      # Get price in user's currency
      - query: |
          SELECT pp.amount
          FROM ProductPrice pp
          WHERE pp.product = :product_id
            AND pp.currency = :preferred_currency
            AND pp.effective_date <= CURRENT_DATE

      # Format price according to locale
      - call: common.format_currency(
          :amount,
          :preferred_currency,
          :preferred_locale
        )

      - return:
          product_name: :translated_name
          product_description: :translated_description
          price_formatted: :formatted_price
```

**Generated Code**: 2000+ lines of PostgreSQL with:
- Multi-currency support
- Translation tables for all entities
- Locale-aware formatting functions
- Country/language validation
- Foreign key constraints
- Translation lookup optimization

---

## Best Practices

### ✅ DO

1. **Use ISO standards consistently**
   ```yaml
   # Good: ISO codes
   currency: {code: "USD"}  # ISO 4217
   language: {iso_code: "en"}  # ISO 639-1
   country: {iso_code: "US"}  # ISO 3166-1
   ```

2. **Enable translations for user-facing content**
   ```yaml
   entity: Product
   translations:
     enabled: true
     fields: [name, description, tags]
   ```

3. **Store amounts with currency references**
   ```yaml
   # Good: Amount + currency
   fields:
     amount: money
     currency: ref(Currency)
   ```

4. **Use locales for formatting, languages for content**
   ```yaml
   # Language: For content translation
   content_language: ref(Language)  # "en", "fr", "de"

   # Locale: For formatting numbers/dates
   display_locale: ref(Locale)  # "en-US", "fr-CA", "de-DE"
   ```

### ❌ DON'T

1. **Don't hardcode currency symbols**
   ```yaml
   # ❌ Bad: Hardcoded
   fields:
     price: "$99.99"

   # ✅ Good: Use Currency entity
   fields:
     amount: money
     currency: ref(Currency)  # Auto-includes symbol
   ```

2. **Don't store translations in main entity**
   ```yaml
   # ❌ Bad: Separate columns
   entity: Product
   fields:
     name_en: text
     name_fr: text
     name_de: text

   # ✅ Good: Use translation infrastructure
   entity: Product
   fields:
     name: text  # Default language
   translations:
     enabled: true
     fields: [name]
   ```

3. **Don't mix locale and language**
   ```yaml
   # ❌ Bad: Using locale for content language
   SELECT * FROM Product_Translation
   WHERE locale = 'en-US'  # Wrong! Use language

   # ✅ Good: Use language for content
   SELECT * FROM Product_Translation
   WHERE language = 'en'
   ```

---

## Performance Considerations

### Translation Queries

For high-traffic multi-language sites, add composite indexes:

```sql
-- Auto-generated by SpecQL
CREATE INDEX idx_product_translation_lookup
  ON tenant.tb_product_translation (
    fk_product,
    fk_language
  )
  WHERE deleted_at IS NULL;
```

### Currency Lookups

Common currency queries benefit from indexes:

```sql
-- Auto-generated by SpecQL
CREATE INDEX idx_tb_currency_code
  ON common.tb_currency (code)
  WHERE deleted_at IS NULL;
```

---

## Reference

### Complete Entity List

| Entity | Schema | Standard | Key Features |
|--------|--------|----------|--------------|
| **Currency** | common | ISO 4217 | Currency codes, symbols |
| **Language** | common | ISO 639-1/2 | Language codes |
| **Locale** | common | BCP 47 | Formatting rules, RTL support |
| **Country** | common | ISO 3166-1 | Country codes, continents |
| **Continent** | common | - | Continental grouping |
| **CountryLocale** | common | - | Country-locale mapping |

### Related Documentation

- [Commerce Entities](../commerce/index.md) - Multi-currency pricing
- [Geographic Entities](../geo/index.md) - International addresses
- [Rich Types Reference](../../03_core-concepts/rich-types.md) - money type details

---

## Next Steps

1. **Try it**: Import i18n entities in your project
2. **Translate it**: Enable translations on your entities
3. **Localize it**: Add locale-aware formatting
4. **Deploy it**: Generate PostgreSQL schema with i18n support

**Ready to go global? Import and launch worldwide!** 🌍
