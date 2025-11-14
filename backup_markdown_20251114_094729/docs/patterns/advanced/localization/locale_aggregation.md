# Localization Locale Aggregation Pattern

**Category**: Localization Patterns
**Use Case**: Aggregate data grouped by translated field values
**Complexity**: Medium
**Enterprise Feature**: ✅ Yes

## Overview

The locale aggregation pattern enables grouping and counting data by translated field values, essential for:

- Localized reporting and analytics
- Multi-language dashboard metrics
- International sales reports
- Localized category analysis

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity` | entity_reference | ✅ | - | Entity to aggregate |
| `group_by_field` | string | ✅ | - | Translatable field to group by |
| `aggregations` | array | ✅ | - | Aggregation functions to apply |
| `translation_table` | string | ✅ | - | Translation table name |
| `fallback_locale` | string | ❌ | en_US | Fallback locale |

## Generated SQL Features

- ✅ Localized GROUP BY with fallback logic
- ✅ Multiple aggregation functions per group
- ✅ Automatic translation joins
- ✅ Locale-aware result metadata

## Examples

### Example 1: Product Count by Localized Category

```yaml
views:
  - name: v_product_count_by_category_localized
    pattern: localization/locale_aggregation
    config:
      entity: Product
      group_by_field: category
      translation_table: tl_product_category
      aggregations:
        - metric: product_count
          function: COUNT
          field: "*"  # Count rows
        - metric: total_value
          function: SUM
          field: price
        - metric: avg_price
          function: AVG
          field: price
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_product_count_by_category_localized AS
SELECT
    -- Localized group-by field
    COALESCE(
        current_locale.category,
        fallback_locale.category
    ) AS category,

    -- Aggregations
    COUNT(p.*) AS product_count,
    SUM(p.price) AS total_value,
    AVG(p.price) AS avg_price,

    -- Metadata
    CURRENT_SETTING('app.current_locale')::text AS locale

FROM tenant.tb_product p
INNER JOIN tenant.tl_product_category fallback_locale
    ON fallback_locale.fk_category = p.fk_category
    AND fallback_locale.locale = 'en_US'
LEFT JOIN tenant.tl_product_category current_locale
    ON current_locale.fk_category = p.fk_category
    AND current_locale.locale = CURRENT_SETTING('app.current_locale')::text
WHERE p.deleted_at IS NULL
GROUP BY
    COALESCE(current_locale.category, fallback_locale.category),
    CURRENT_SETTING('app.current_locale')::text;
```

## Usage Examples

### Localized Analytics

```sql
-- Set locale for analysis
SET app.current_locale = 'fr_FR';

-- Get product counts by localized category
SELECT
    category,
    product_count,
    total_value,
    ROUND(avg_price, 2) AS avg_price
FROM v_product_count_by_category_localized
ORDER BY product_count DESC;

-- Compare across locales
SELECT
    locale,
    category,
    product_count
FROM v_product_count_by_category_localized
WHERE locale IN ('en_US', 'fr_FR', 'de_DE')
ORDER BY locale, product_count DESC;
```

### Multi-locale Reporting

```sql
-- Sales by category in all supported locales
WITH localized_counts AS (
    SELECT
        category,
        product_count,
        locale
    FROM v_product_count_by_category_localized
)
SELECT
    category,
    SUM(CASE WHEN locale = 'en_US' THEN product_count END) AS en_count,
    SUM(CASE WHEN locale = 'fr_FR' THEN product_count END) AS fr_count,
    SUM(CASE WHEN locale = 'de_DE' THEN product_count END) AS de_count
FROM localized_counts
GROUP BY category
ORDER BY en_count DESC;
```

## Translation Table Schema

For category translations:

```sql
CREATE TABLE tenant.tl_product_category (
    pk_translation BIGSERIAL PRIMARY KEY,
    fk_category INTEGER NOT NULL REFERENCES tenant.tb_category(pk_category),
    locale TEXT NOT NULL,
    name TEXT NOT NULL,  -- Translated category name
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    UNIQUE(fk_category, locale)
);
```

## When to Use

✅ **Use when**:
- Need aggregated reports in multiple languages
- Building international dashboards
- Localized analytics and BI reports
- Multi-language customer segmentation

❌ **Don't use when**:
- Single language analytics only
- No translated grouping fields
- Real-time aggregation requirements (consider materialized views)

## Performance Considerations

- **Grouping**: Localized GROUP BY may be less efficient than direct field grouping
- **Joins**: Multiple LEFT JOINs for locale fallback
- **Materialized Views**: Consider for frequently accessed aggregations
- **Indexing**: Ensure translation tables have proper indexes

## Advanced Usage

### Dynamic Locale Selection

```sql
-- Create view for each locale dynamically
DO $$
DECLARE
    locale_code TEXT;
BEGIN
    FOR locale_code IN SELECT DISTINCT locale FROM tenant.tl_product_category
    LOOP
        EXECUTE format('
            CREATE OR REPLACE VIEW v_product_count_by_category_%I AS
            SELECT
                COALESCE(tl.name, tl_en.name) AS category,
                COUNT(p.*) AS product_count,
                SUM(p.price) AS total_value
            FROM tenant.tb_product p
            LEFT JOIN tenant.tl_product_category tl
                ON tl.fk_category = p.fk_category AND tl.locale = %L
            INNER JOIN tenant.tl_product_category tl_en
                ON tl_en.fk_category = p.fk_category AND tl_en.locale = ''en_US''
            WHERE p.deleted_at IS NULL
            GROUP BY COALESCE(tl.name, tl_en.name)
        ', locale_code, locale_code);
    END LOOP;
END $$;
```

### Cross-locale Analysis

```sql
-- Find categories that exist in some locales but not others
WITH category_coverage AS (
    SELECT
        c.pk_category,
        c.name_en,
        COUNT(DISTINCT tl.locale) AS locale_count,
        array_agg(DISTINCT tl.locale ORDER BY tl.locale) AS available_locales
    FROM tenant.tb_category c
    CROSS JOIN (SELECT DISTINCT locale FROM tenant.tl_product_category) all_locales
    LEFT JOIN tenant.tl_product_category tl
        ON tl.fk_category = c.pk_category AND tl.locale = all_locales.locale
    GROUP BY c.pk_category, c.name_en
)
SELECT *
FROM category_coverage
WHERE locale_count < (SELECT COUNT(DISTINCT locale) FROM tenant.tl_product_category)
ORDER BY locale_count ASC;
```

## Related Patterns

- **Translated View**: Individual entity localization
- **KPI Calculator**: Business metrics with localization
- **Aggregation Patterns**: Non-localized aggregation patterns