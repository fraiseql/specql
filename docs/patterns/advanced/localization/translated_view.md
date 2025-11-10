# Localization Translated View Pattern

**Category**: Localization Patterns
**Use Case**: Multi-language entity views with automatic fallback
**Complexity**: Medium
**Enterprise Feature**: ✅ Yes

## Overview

The translated view pattern provides seamless multi-language support for entities, automatically falling back to default locales when translations are missing. Essential for:

- International product catalogs
- Multi-language content management
- Global customer support
- Localized reporting and analytics

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity` | entity_reference | ✅ | - | Entity to localize |
| `translatable_fields` | array | ✅ | - | Fields that have translations |
| `translation_table` | string | ✅ | - | Translation table name (tl_*) |
| `fallback_locale` | string | ❌ | en_US | Fallback locale when translation missing |
| `current_locale_source` | string | ❌ | CURRENT_SETTING | How to determine user's locale |
| `include_all_locales` | boolean | ❌ | false | Include all translations as JSONB |

## Generated SQL Features

- ✅ `COALESCE` fallback logic for missing translations
- ✅ Automatic locale detection via session settings
- ✅ JSONB aggregation of all translations
- ✅ Translation coverage metadata
- ✅ Efficient locale-based indexing

## Examples

### Example 1: Product Catalog with French/English Fallback

```yaml
views:
  - name: v_product_localized
    pattern: localization/translated_view
    config:
      entity: Product
      translatable_fields: [name, description, specifications]
      translation_table: tl_product
      fallback_locale: en_US
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_product_localized AS
SELECT
    p.pk_product,

    -- Non-translatable fields (passthrough)
    p.price,
    p.category,
    p.created_at,

    -- Translatable fields with fallback
    COALESCE(
        current_locale.name,  -- Prefer current locale
        fallback_locale.name  -- Fall back to default
    ) AS name,

    COALESCE(
        current_locale.description,
        fallback_locale.description
    ) AS description,

    COALESCE(
        current_locale.specifications,
        fallback_locale.specifications
    ) AS specifications,

    -- All translations as JSONB object
    (
        SELECT jsonb_object_agg(tl.locale, jsonb_build_object(
            'name', tl.name,
            'description', tl.description,
            'specifications', tl.specifications
        ))
        FROM tenant.tl_product tl
        WHERE tl.fk_product = p.pk_product
          AND tl.deleted_at IS NULL
    ) AS all_translations,

    -- Metadata
    CURRENT_SETTING('app.current_locale')::text AS current_locale,
    'en_US' AS fallback_locale,
    current_locale.locale IS NOT NULL AS has_translation_for_locale

FROM tenant.tb_product p

-- Join base locale (fallback)
INNER JOIN tenant.tl_product fallback_locale
    ON fallback_locale.fk_product = p.pk_product
    AND fallback_locale.locale = 'en_US'
    AND fallback_locale.deleted_at IS NULL

-- Join current locale (preferred)
LEFT JOIN tenant.tl_product current_locale
    ON current_locale.fk_product = p.pk_product
    AND current_locale.locale = CURRENT_SETTING('app.current_locale')::text
    AND current_locale.deleted_at IS NULL

WHERE p.deleted_at IS NULL;

-- Index for locale lookup
CREATE INDEX IF NOT EXISTS idx_tl_product_locale
    ON tenant.tl_product(fk_product, locale);
```

## Usage Examples

### Basic Localized Queries

```sql
-- Set user locale
SET app.current_locale = 'fr_FR';

-- Query localized products (returns French if available, English otherwise)
SELECT pk_product, name, description, price
FROM v_product_localized;

-- Check translation coverage
SELECT
    current_locale,
    has_translation_for_locale,
    COUNT(*) AS product_count
FROM v_product_localized
GROUP BY current_locale, has_translation_for_locale;
```

### Translation Management

```sql
-- Get all translations for a product
SELECT pk_product, all_translations
FROM v_product_localized
WHERE pk_product = 123;

-- Returns:
-- {
--   "en_US": {"name": "Wireless Headphones", "description": "..."},
--   "fr_FR": {"name": "Écouteurs Sans Fil", "description": "..."},
--   "de_DE": {"name": "Drahtlose Kopfhörer", "description": "..."}
-- }
```

### Analytics with Localization

```sql
-- Product count by localized category
SELECT
    category,
    COUNT(*) AS product_count
FROM v_product_localized
GROUP BY category
ORDER BY product_count DESC;

-- Translation coverage report
SELECT
    locale,
    COUNT(*) AS translated_products,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM v_product_localized), 2) AS coverage_pct
FROM (
    SELECT jsonb_object_keys(all_translations) AS locale
    FROM v_product_localized
    WHERE all_translations IS NOT NULL
) translations
GROUP BY locale
ORDER BY coverage_pct DESC;
```

## Translation Table Schema

The pattern expects translation tables with this structure:

```sql
CREATE TABLE tenant.tl_product (
    pk_translation BIGSERIAL PRIMARY KEY,
    fk_product INTEGER NOT NULL REFERENCES tenant.tb_product(pk_product),
    locale TEXT NOT NULL,  -- e.g., 'en_US', 'fr_FR', 'de_DE'
    name TEXT,
    description TEXT,
    specifications JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    UNIQUE(fk_product, locale)
);
```

## When to Use

✅ **Use when**:
- Building international applications
- Content needs multiple language versions
- Users expect localized interfaces
- Global customer base requirements

❌ **Don't use when**:
- Application is single-language only
- Translation overhead not justified
- Content changes frequently (consider caching strategies)

## Performance Considerations

- **Indexing**: Composite indexes on (fk_entity, locale) for fast lookups
- **Caching**: Consider materialized views for frequently accessed locales
- **Fallback Logic**: COALESCE adds minimal overhead
- **JSONB Aggregation**: Expensive for large translation sets

## Locale Detection Strategies

### Session Setting (Default)
```sql
SET app.current_locale = 'fr_FR';
```

### Application Logic
```sql
-- In application code
current_locale = get_user_preference(user_id) or 'en_US'
execute("SET app.current_locale = %s", current_locale)
```

### Database Function
```yaml
current_locale_source: "get_current_locale()"
```

## Translation Workflow

1. **Content Creation**: Create base entity in default locale
2. **Translation**: Add translations to tl_* tables
3. **Query**: Use localized view - automatic fallback
4. **Maintenance**: Update translations as content changes

## Related Patterns

- **Locale Aggregation**: Group and count by translated fields
- **Data Masking**: Combine with localization for regional compliance