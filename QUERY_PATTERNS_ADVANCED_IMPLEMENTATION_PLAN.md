# SpecQL Advanced Query Patterns - Implementation Plan

**Created**: 2025-11-10
**Status**: Phase 2 Extension (v1.1+)
**Total Duration**: 8-10 weeks (2-2.5 months)
**Prerequisites**: Core Query Pattern Library (Phases 0-12) completed

---

## Executive Summary

This plan extends the Query Pattern Library with **4 advanced pattern categories** that address enterprise-grade requirements: temporal data management, internationalization, business metrics, and security. These patterns build on the foundational infrastructure from the core implementation.

**Advanced Pattern Categories**:
1. **Temporal Patterns** - Time-series, SCD Type 2, audit trails
2. **Localization Patterns** - Multi-language views with fallback logic
3. **Metric Patterns** - KPI calculations and business intelligence
4. **Security Patterns** - Row-level security and permission filtering

---

## Phase 13: Temporal Patterns (Week 17-18)

**Objective**: Enable time-series queries, historical tracking, and slowly changing dimensions

### Pattern Categories

#### 1. **Snapshot Pattern** - Point-in-time queries
#### 2. **Audit Trail Pattern** - Historical change tracking
#### 3. **SCD Type 2 Pattern** - Slowly changing dimensions
#### 4. **Temporal Range Pattern** - Effective date range queries

---

### TDD Cycle 1: Snapshot Pattern

#### 🔴 RED: Test Point-in-Time Snapshot

```bash
uv run pytest tests/unit/patterns/temporal/test_snapshot.py::test_contract_snapshot_at_date -v
# Expected: FAILED (snapshot pattern not implemented)
```

**Test Spec**:
```python
def test_contract_snapshot_at_date():
    """Test: Retrieve contract state as of specific date"""
    config = {
        "name": "v_contract_snapshot",
        "pattern": "temporal/snapshot",
        "config": {
            "entity": "Contract",
            "effective_date_field": "effective_date",
            "end_date_field": "superseded_date",
            "snapshot_mode": "point_in_time"
        }
    }

    sql = generate_pattern(config)

    # Validate SQL structure
    assert "tsrange" in sql or "BETWEEN" in sql
    assert "effective_date" in sql
    assert "LEAD(" in sql or "LAG(" in sql  # Window functions
```

#### 🟢 GREEN: Implement Snapshot Pattern

```yaml
# stdlib/queries/temporal/snapshot.yaml
pattern: temporal/snapshot
description: Point-in-time snapshot with temporal validity
category: temporal
complexity: medium

parameters:
  entity:
    type: entity_reference
    required: true
    description: Entity to snapshot

  effective_date_field:
    type: string
    required: true
    description: When the version became effective

  end_date_field:
    type: string
    required: false
    description: When the version was superseded (NULL = current)

  snapshot_mode:
    type: enum
    enum: [point_in_time, full_history, current_only]
    default: point_in_time
    description: Snapshot retrieval mode

  include_validity_range:
    type: boolean
    default: true
    description: Include tsrange column for validity period

examples:
  - name: Contract Version History
    description: Track contract changes over time
    config:
      entity: Contract
      effective_date_field: effective_date
      end_date_field: superseded_date
      snapshot_mode: full_history
```

**Template**:
```jinja2
{# stdlib/queries/temporal/snapshot.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description Point-in-time snapshot of {{ entity.name }} with temporal validity
-- @fraiseql:pattern temporal/snapshot

CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ entity.pk_field }},
    {{ entity.alias }}.*,

    {% if include_validity_range %}
    -- Temporal validity range
    tsrange(
        {{ effective_date_field }},
        LEAD({{ effective_date_field }}) OVER (
            PARTITION BY {{ entity.pk_field }}
            ORDER BY {{ effective_date_field }}
        ),
        '[)'  -- Inclusive start, exclusive end
    ) AS valid_period,
    {% endif %}

    -- Convenience flags
    {{ end_date_field }} IS NULL AS is_current,
    {{ effective_date_field }} AS version_effective_date,
    LEAD({{ effective_date_field }}) OVER (
        PARTITION BY {{ entity.pk_field }}
        ORDER BY {{ effective_date_field }}
    ) AS version_superseded_date

FROM {{ entity.schema }}.{{ entity.table }} {{ entity.alias }}
WHERE {{ entity.alias }}.deleted_at IS NULL
{% if snapshot_mode == 'current_only' %}
  AND {{ end_date_field }} IS NULL
{% endif %}
ORDER BY {{ entity.pk_field }}, {{ effective_date_field }} DESC;

-- Temporal index for point-in-time queries
CREATE INDEX IF NOT EXISTS idx_{{ name }}_temporal
    ON {{ schema }}.{{ name }} USING GIST ({{ entity.pk_field }}, valid_period);

-- Index for current version lookup
CREATE INDEX IF NOT EXISTS idx_{{ name }}_current
    ON {{ schema }}.{{ name }}({{ entity.pk_field }})
    WHERE is_current = true;

COMMENT ON VIEW {{ schema }}.{{ name }} IS
    'Temporal snapshot of {{ entity.name }} with validity ranges. Query as of date: WHERE valid_period @> ''2024-01-15''::date';
```

**Usage Examples**:
```sql
-- Get contract state as of 2024-01-15
SELECT *
FROM v_contract_snapshot
WHERE valid_period @> '2024-01-15'::date;

-- Get all historical versions of contract
SELECT *
FROM v_contract_snapshot
WHERE pk_contract = 123
ORDER BY version_effective_date DESC;

-- Get only current versions
SELECT *
FROM v_contract_snapshot
WHERE is_current = true;
```

#### 🔧 REFACTOR: Temporal Utilities

```python
# src/patterns/temporal/temporal_utils.py
from typing import Dict, Optional
from datetime import date

class TemporalQueryBuilder:
    """Utilities for building temporal queries"""

    def build_validity_range(
        self,
        start_field: str,
        end_field: Optional[str] = None,
        range_type: str = '[)'
    ) -> str:
        """Generate tsrange expression"""
        if end_field:
            return f"tsrange({start_field}, {end_field}, '{range_type}')"
        else:
            # Use LEAD for auto-computed end dates
            return f"""tsrange(
                {start_field},
                LEAD({start_field}) OVER (PARTITION BY pk ORDER BY {start_field}),
                '{range_type}'
            )"""

    def build_point_in_time_filter(
        self,
        validity_field: str,
        target_date: str = "CURRENT_DATE"
    ) -> str:
        """Generate point-in-time filter"""
        return f"{validity_field} @> {target_date}::date"

    def build_temporal_join(
        self,
        left_table: str,
        right_table: str,
        left_validity: str,
        right_validity: str,
        join_type: str = "INNER"
    ) -> str:
        """Generate temporal join condition"""
        return f"""
        {join_type} JOIN {right_table}
            ON {left_table}.fk = {right_table}.pk
            AND {left_validity} && {right_validity}  -- Overlapping ranges
        """
```

#### ✅ QA: Validate Snapshot Pattern

```bash
# Unit tests
uv run pytest tests/unit/patterns/temporal/test_snapshot.py -v

# Integration test with real database
uv run pytest tests/integration/patterns/temporal/test_snapshot_queries.py -v

# Performance test: Point-in-time query on 10k versions
uv run pytest tests/performance/patterns/temporal/test_snapshot_performance.py -v
```

---

### TDD Cycle 2: Audit Trail Pattern

#### 🔴 RED: Test Audit Trail Generation

```bash
uv run pytest tests/unit/patterns/temporal/test_audit_trail.py -v
```

**Test Case**: Track all changes to contract records

#### 🟢 GREEN: Implement Audit Trail Pattern

```yaml
# stdlib/queries/temporal/audit_trail.yaml
pattern: temporal/audit_trail
description: Complete audit trail of entity changes
category: temporal
complexity: high

parameters:
  entity:
    type: entity_reference
    required: true

  audit_table:
    type: string
    required: true
    description: Audit table name (e.g., tb_contract_audit)

  change_columns:
    type: array
    items: string
    required: false
    description: Columns to track (default: all)

  include_user_info:
    type: boolean
    default: true
    description: Include user who made change

  include_diff:
    type: boolean
    default: true
    description: Include before/after diff

  retention_period:
    type: string
    default: "7 years"
    description: Audit retention period
```

**Template**:
```jinja2
{# stdlib/queries/temporal/audit_trail.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description Complete audit trail for {{ entity.name }}
-- @fraiseql:pattern temporal/audit_trail

CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
WITH audit_with_changes AS (
    SELECT
        audit.audit_id,
        audit.{{ entity.pk_field }},
        audit.operation,  -- INSERT, UPDATE, DELETE
        audit.changed_at,
        audit.changed_by,

        {% if include_user_info %}
        u.data->>'email' AS changed_by_email,
        u.data->>'name' AS changed_by_name,
        {% endif %}

        {% if include_diff %}
        -- Compute changed fields
        CASE
            WHEN audit.operation = 'UPDATE' THEN
                (
                    SELECT jsonb_object_agg(key, jsonb_build_object(
                        'old', audit.old_values->key,
                        'new', audit.new_values->key
                    ))
                    FROM jsonb_each(audit.new_values) AS new_fields(key, value)
                    WHERE audit.old_values->key IS DISTINCT FROM audit.new_values->key
                )
            WHEN audit.operation = 'INSERT' THEN
                audit.new_values
            WHEN audit.operation = 'DELETE' THEN
                audit.old_values
        END AS changes,
        {% endif %}

        -- Full snapshots
        audit.old_values AS previous_state,
        audit.new_values AS current_state,

        -- Metadata
        audit.transaction_id,
        audit.application_name,
        audit.client_addr

    FROM {{ schema }}.{{ audit_table }} audit
    {% if include_user_info %}
    LEFT JOIN app.tb_user u ON u.id = audit.changed_by
    {% endif %}
    WHERE audit.changed_at >= CURRENT_DATE - INTERVAL '{{ retention_period }}'
)
SELECT
    *,
    -- Time since previous change
    changed_at - LAG(changed_at) OVER (
        PARTITION BY {{ entity.pk_field }}
        ORDER BY changed_at
    ) AS time_since_last_change,

    -- Change sequence number
    ROW_NUMBER() OVER (
        PARTITION BY {{ entity.pk_field }}
        ORDER BY changed_at
    ) AS change_sequence

FROM audit_with_changes
ORDER BY {{ entity.pk_field }}, changed_at DESC;

-- Index for entity lookup
CREATE INDEX IF NOT EXISTS idx_{{ name }}_entity
    ON {{ schema }}.{{ name }}({{ entity.pk_field }}, changed_at DESC);

-- Index for user audit
CREATE INDEX IF NOT EXISTS idx_{{ name }}_user
    ON {{ schema }}.{{ name }}(changed_by, changed_at DESC);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_{{ name }}_time
    ON {{ schema }}.{{ name }}(changed_at DESC);
```

**Audit Table Schema** (Auto-generated):
```sql
-- Auto-create audit table if it doesn't exist
CREATE TABLE IF NOT EXISTS {{ schema }}.{{ audit_table }} (
    audit_id BIGSERIAL PRIMARY KEY,
    {{ entity.pk_field }} INTEGER NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by UUID,
    transaction_id BIGINT DEFAULT txid_current(),
    application_name TEXT DEFAULT CURRENT_SETTING('application_name'),
    client_addr INET DEFAULT INET_CLIENT_ADDR(),
    old_values JSONB,
    new_values JSONB
);

-- Audit trigger function
CREATE OR REPLACE FUNCTION {{ schema }}.{{ entity.table }}_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO {{ schema }}.{{ audit_table }} (
            {{ entity.pk_field }}, operation, changed_by, new_values
        ) VALUES (
            NEW.{{ entity.pk_field }},
            'INSERT',
            NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
            to_jsonb(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO {{ schema }}.{{ audit_table }} (
            {{ entity.pk_field }}, operation, changed_by, old_values, new_values
        ) VALUES (
            NEW.{{ entity.pk_field }},
            'UPDATE',
            NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
            to_jsonb(OLD),
            to_jsonb(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO {{ schema }}.{{ audit_table }} (
            {{ entity.pk_field }}, operation, changed_by, old_values
        ) VALUES (
            OLD.{{ entity.pk_field }},
            'DELETE',
            NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
            to_jsonb(OLD)
        );
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Attach trigger
CREATE TRIGGER trg_{{ entity.table }}_audit
AFTER INSERT OR UPDATE OR DELETE ON {{ schema }}.{{ entity.table }}
FOR EACH ROW EXECUTE FUNCTION {{ schema }}.{{ entity.table }}_audit_trigger();
```

**Usage Examples**:
```sql
-- Get all changes to contract #123
SELECT *
FROM v_contract_audit_trail
WHERE pk_contract = 123
ORDER BY changed_at DESC;

-- Find who changed contract status
SELECT
    changed_by_email,
    changed_at,
    changes->'status'->>'old' AS old_status,
    changes->'status'->>'new' AS new_status
FROM v_contract_audit_trail
WHERE pk_contract = 123
  AND changes ? 'status'
ORDER BY changed_at DESC;

-- Audit report: Changes in last 30 days
SELECT
    changed_by_email,
    operation,
    COUNT(*) AS change_count,
    jsonb_object_keys(changes) AS changed_fields
FROM v_contract_audit_trail
WHERE changed_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY changed_by_email, operation, changed_fields
ORDER BY change_count DESC;
```

#### 🔧 REFACTOR: Audit Utilities

```python
# src/patterns/temporal/audit_generator.py
class AuditTrailGenerator:
    """Generate audit infrastructure"""

    def generate_audit_table(self, entity: Dict) -> str:
        """Generate audit table DDL"""
        pass

    def generate_audit_trigger(self, entity: Dict) -> str:
        """Generate audit trigger function"""
        pass

    def generate_audit_view(self, entity: Dict, config: Dict) -> str:
        """Generate audit trail view"""
        pass

    def generate_retention_policy(self, retention_period: str) -> str:
        """Generate audit data retention policy"""
        return f"""
        -- Automated audit cleanup
        CREATE OR REPLACE FUNCTION cleanup_old_audit_records()
        RETURNS void AS $$
        BEGIN
            DELETE FROM {{ audit_table }}
            WHERE changed_at < CURRENT_DATE - INTERVAL '{retention_period}';
        END;
        $$ LANGUAGE plpgsql;

        -- Schedule cleanup (requires pg_cron)
        SELECT cron.schedule('cleanup_audit', '0 2 * * 0', 'SELECT cleanup_old_audit_records()');
        """
```

#### ✅ QA: Validate Audit Trail

```bash
# Unit tests
uv run pytest tests/unit/patterns/temporal/test_audit_trail.py -v

# Integration test: Verify audit capture
uv run pytest tests/integration/patterns/temporal/test_audit_capture.py -v

# Compliance test: GDPR/SOC2 requirements
uv run pytest tests/compliance/test_audit_trail_compliance.py -v
```

---

### TDD Cycle 3: SCD Type 2 Pattern

#### 🔴 RED: Test Slowly Changing Dimension

```bash
uv run pytest tests/unit/patterns/temporal/test_scd_type2.py -v
```

**Test Case**: Customer address changes over time

#### 🟢 GREEN: Implement SCD Type 2 Pattern

```yaml
# stdlib/queries/temporal/scd_type2.yaml
pattern: temporal/scd_type2
description: Slowly Changing Dimension Type 2 (full history)
category: temporal
complexity: medium

parameters:
  entity:
    type: entity_reference
    required: true

  effective_date_field:
    type: string
    default: effective_date

  end_date_field:
    type: string
    default: end_date

  is_current_field:
    type: string
    default: is_current

  version_number_field:
    type: string
    default: version_number

  surrogate_key_field:
    type: string
    required: false
    description: Surrogate key for SCD (default: auto-generate)
```

**Template**:
```jinja2
{# stdlib/queries/temporal/scd_type2.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description SCD Type 2 view for {{ entity.name }}
-- @fraiseql:pattern temporal/scd_type2

CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    -- Surrogate key (unique per version)
    {% if surrogate_key_field %}
    {{ surrogate_key_field }},
    {% else %}
    ROW_NUMBER() OVER (ORDER BY {{ entity.pk_field }}, {{ effective_date_field }}) AS surrogate_key,
    {% endif %}

    -- Natural key (same across versions)
    {{ entity.pk_field }} AS natural_key,

    -- All entity attributes
    {{ entity.alias }}.*,

    -- SCD Type 2 metadata
    {{ effective_date_field }},
    {{ end_date_field }},
    {{ is_current_field }},

    -- Version tracking
    ROW_NUMBER() OVER (
        PARTITION BY {{ entity.pk_field }}
        ORDER BY {{ effective_date_field }}
    ) AS {{ version_number_field }},

    -- Validity range
    tsrange({{ effective_date_field }}, {{ end_date_field }}, '[)') AS valid_period

FROM {{ entity.schema }}.{{ entity.table }} {{ entity.alias }}
WHERE {{ entity.alias }}.deleted_at IS NULL;

-- Unique constraint on current version
CREATE UNIQUE INDEX IF NOT EXISTS idx_{{ name }}_current_unique
    ON {{ schema }}.{{ name }}({{ entity.pk_field }})
    WHERE {{ is_current_field }} = true;

-- Temporal index
CREATE INDEX IF NOT EXISTS idx_{{ name }}_temporal_lookup
    ON {{ schema }}.{{ name }} USING GIST ({{ entity.pk_field }}, valid_period);
```

**SCD Type 2 Trigger** (Auto-generate on base table):
```sql
-- Auto-manage SCD Type 2 on UPDATE
CREATE OR REPLACE FUNCTION {{ schema }}.{{ entity.table }}_scd_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Close old version
    UPDATE {{ schema }}.{{ entity.table }}
    SET
        {{ end_date_field }} = CURRENT_DATE,
        {{ is_current_field }} = false
    WHERE {{ entity.pk_field }} = OLD.{{ entity.pk_field }}
      AND {{ is_current_field }} = true;

    -- Insert new version
    INSERT INTO {{ schema }}.{{ entity.table }} (
        {{ entity.pk_field }},
        -- ... all fields
        {{ effective_date_field }},
        {{ end_date_field }},
        {{ is_current_field }}
    ) VALUES (
        NEW.{{ entity.pk_field }},
        -- ... all new values
        CURRENT_DATE,
        NULL,
        true
    );

    RETURN NULL;  -- Prevent original UPDATE
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_{{ entity.table }}_scd
BEFORE UPDATE ON {{ schema }}.{{ entity.table }}
FOR EACH ROW
WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE FUNCTION {{ schema }}.{{ entity.table }}_scd_trigger();
```

#### 🔧 REFACTOR: SCD Utilities

```python
# src/patterns/temporal/scd_utils.py
class SCDType2Manager:
    """Manage SCD Type 2 lifecycle"""

    def create_new_version(self, natural_key: int, new_data: Dict) -> int:
        """Create new version, close old one"""
        pass

    def get_current_version(self, natural_key: int) -> Dict:
        """Get current active version"""
        pass

    def get_version_at_date(self, natural_key: int, as_of_date: date) -> Dict:
        """Get version effective at specific date"""
        pass

    def get_all_versions(self, natural_key: int) -> List[Dict]:
        """Get complete version history"""
        pass
```

#### ✅ QA: Validate SCD Type 2

```bash
uv run pytest tests/unit/patterns/temporal/test_scd_type2.py -v
uv run pytest tests/integration/patterns/temporal/test_scd_versioning.py -v
```

---

### TDD Cycle 4: Temporal Range Pattern

#### 🔴 RED: Test Date Range Queries

```bash
uv run pytest tests/unit/patterns/temporal/test_temporal_range.py -v
```

**Test Case**: Contracts effective during specific period

#### 🟢 GREEN: Implement Temporal Range Pattern

```yaml
# stdlib/queries/temporal/temporal_range.yaml
pattern: temporal/temporal_range
description: Queries over temporal ranges (effective dates, validity periods)
category: temporal
complexity: low

parameters:
  entity:
    type: entity_reference
    required: true

  start_date_field:
    type: string
    required: true

  end_date_field:
    type: string
    required: false
    description: NULL means ongoing/infinite

  filter_mode:
    type: enum
    enum: [current, future, historical, custom_range]
    default: current

  custom_date_range:
    type: object
    required: false
    properties:
      start: string
      end: string
```

**Template**:
```jinja2
{# stdlib/queries/temporal/temporal_range.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description Temporal range filtered {{ entity.name }}
-- @fraiseql:pattern temporal/temporal_range

CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ entity.alias }}.*,

    -- Computed validity range
    {% if end_date_field %}
    daterange({{ start_date_field }}, {{ end_date_field }}, '[)') AS validity_range,
    {% else %}
    daterange({{ start_date_field }}, NULL, '[)') AS validity_range,  -- Infinite end
    {% endif %}

    -- Convenience flags
    CASE
        WHEN {{ start_date_field }} <= CURRENT_DATE
            AND ({{ end_date_field }} IS NULL OR {{ end_date_field }} >= CURRENT_DATE)
        THEN true
        ELSE false
    END AS is_currently_valid,

    CASE
        WHEN {{ start_date_field }} > CURRENT_DATE THEN true
        ELSE false
    END AS is_future,

    CASE
        WHEN {{ end_date_field }} IS NOT NULL AND {{ end_date_field }} < CURRENT_DATE
        THEN true
        ELSE false
    END AS is_historical

FROM {{ entity.schema }}.{{ entity.table }} {{ entity.alias }}
WHERE {{ entity.alias }}.deleted_at IS NULL
{% if filter_mode == 'current' %}
  AND {{ start_date_field }} <= CURRENT_DATE
  AND ({{ end_date_field }} IS NULL OR {{ end_date_field }} >= CURRENT_DATE)
{% elif filter_mode == 'future' %}
  AND {{ start_date_field }} > CURRENT_DATE
{% elif filter_mode == 'historical' %}
  AND {{ end_date_field }} IS NOT NULL
  AND {{ end_date_field }} < CURRENT_DATE
{% elif filter_mode == 'custom_range' %}
  AND daterange({{ start_date_field }}, {{ end_date_field }}, '[)') &&
      daterange('{{ custom_date_range.start }}'::date, '{{ custom_date_range.end }}'::date, '[)')
{% endif %};

-- Temporal range index (GiST for range operations)
CREATE INDEX IF NOT EXISTS idx_{{ name }}_validity_range
    ON {{ schema }}.{{ name }} USING GIST (validity_range);
```

**Usage Examples**:
```sql
-- Current contracts
SELECT * FROM v_contract_current;

-- Contracts active during Q1 2024
SELECT *
FROM v_contract_temporal
WHERE validity_range && daterange('2024-01-01', '2024-04-01');

-- Contracts that became effective in 2024
SELECT *
FROM v_contract_temporal
WHERE EXTRACT(YEAR FROM start_date) = 2024;
```

#### ✅ QA: Validate Temporal Range

```bash
uv run pytest tests/integration/patterns/temporal/test_temporal_range.py -v
```

---

### Deliverables: Phase 13 (Temporal Patterns)

- ✅ **Snapshot pattern** - Point-in-time queries
- ✅ **Audit trail pattern** - Complete change history
- ✅ **SCD Type 2 pattern** - Slowly changing dimensions
- ✅ **Temporal range pattern** - Date range filtering
- ✅ **Temporal utilities** - Query builder, SCD manager
- ✅ **Documentation** - Pattern reference, examples
- ✅ **Tests** - Unit, integration, performance

**Pattern Count**: 4 temporal patterns
**Test Coverage**: 95%+
**Documentation**: Complete with examples

---

## Phase 14: Localization Patterns (Week 19)

**Objective**: Multi-language views with translation fallback logic

### Prerequisites Check

```bash
# Check if SpecQL already handles localization
grep -r "tl_" src/generators/schema/table_view_generator.py
grep -r "translatable" stdlib/**/*.yaml
```

**Decision Point**:
- ✅ If NO localization support found → Proceed with this phase
- ❌ If localization auto-generated → Skip this phase

---

### TDD Cycle 1: Translated View Pattern

#### 🔴 RED: Test Translation Fallback

```bash
uv run pytest tests/unit/patterns/localization/test_translated_view.py -v
# Expected: FAILED (localization pattern not implemented)
```

**Test Spec**:
```python
def test_translated_view_with_fallback():
    """Test: Generate localized view with fallback logic"""
    config = {
        "name": "v_product_localized",
        "pattern": "localization/translated_view",
        "config": {
            "entity": "Product",
            "translatable_fields": ["name", "description", "specifications"],
            "fallback_locale": "en_US",
            "translation_table": "tl_product"
        }
    }

    sql = generate_pattern(config)

    # Validate COALESCE fallback logic
    assert "COALESCE" in sql
    assert "tl_product" in sql
    assert "en_US" in sql
```

#### 🟢 GREEN: Implement Translated View Pattern

```yaml
# stdlib/queries/localization/translated_view.yaml
pattern: localization/translated_view
description: Multi-language view with translation fallback
category: localization
complexity: medium

parameters:
  entity:
    type: entity_reference
    required: true
    description: Entity to localize

  translatable_fields:
    type: array
    items: string
    required: true
    description: Fields that have translations

  translation_table:
    type: string
    required: true
    description: Translation table name (tl_*)

  fallback_locale:
    type: string
    default: en_US
    description: Fallback locale when translation missing

  current_locale_source:
    type: string
    default: "CURRENT_SETTING('app.current_locale')"
    description: How to determine user's locale

  include_all_locales:
    type: boolean
    default: false
    description: Include all translations as JSONB object

examples:
  - name: Product with French/English fallback
    config:
      entity: Product
      translatable_fields: [name, description]
      fallback_locale: en_US
```

**Template**:
```jinja2
{# stdlib/queries/localization/translated_view.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description Localized {{ entity.name }} with {{ fallback_locale }} fallback
-- @fraiseql:pattern localization/translated_view

CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ entity.alias }}.{{ entity.pk_field }},

    -- Non-translatable fields (passthrough)
    {% for field in entity.fields %}
    {% if field.name not in translatable_fields %}
    {{ entity.alias }}.{{ field.name }},
    {% endif %}
    {% endfor %}

    -- Translatable fields with fallback
    {% for field in translatable_fields %}
    COALESCE(
        current_locale.{{ field }},  -- Prefer current locale
        fallback_locale.{{ field }}  -- Fall back to default
    ) AS {{ field }},
    {% endfor %}

    {% if include_all_locales %}
    -- All translations as JSONB object
    (
        SELECT jsonb_object_agg(tl.locale, jsonb_build_object(
            {% for field in translatable_fields %}
            '{{ field }}', tl.{{ field }}{% if not loop.last %},{% endif %}
            {% endfor %}
        ))
        FROM {{ entity.schema }}.{{ translation_table }} tl
        WHERE tl.{{ entity.fk_field }} = {{ entity.alias }}.{{ entity.pk_field }}
          AND tl.deleted_at IS NULL
    ) AS all_translations,
    {% endif %}

    -- Metadata
    {{ current_locale_source }}::text AS current_locale,
    '{{ fallback_locale }}' AS fallback_locale,
    current_locale.locale IS NOT NULL AS has_translation_for_locale

FROM {{ entity.schema }}.{{ entity.table }} {{ entity.alias }}

-- Join base locale (fallback)
INNER JOIN {{ entity.schema }}.{{ translation_table }} fallback_locale
    ON fallback_locale.{{ entity.fk_field }} = {{ entity.alias }}.{{ entity.pk_field }}
    AND fallback_locale.locale = '{{ fallback_locale }}'
    AND fallback_locale.deleted_at IS NULL

-- Join current locale (preferred)
LEFT JOIN {{ entity.schema }}.{{ translation_table }} current_locale
    ON current_locale.{{ entity.fk_field }} = {{ entity.alias }}.{{ entity.pk_field }}
    AND current_locale.locale = {{ current_locale_source }}::text
    AND current_locale.deleted_at IS NULL

WHERE {{ entity.alias }}.deleted_at IS NULL;

-- Index for locale lookup
CREATE INDEX IF NOT EXISTS idx_{{ translation_table }}_locale
    ON {{ entity.schema }}.{{ translation_table }}({{ entity.fk_field }}, locale);

COMMENT ON VIEW {{ schema }}.{{ name }} IS
    'Localized {{ entity.name }} with automatic fallback to {{ fallback_locale }}. Set locale via SET app.current_locale = ''fr_FR'';';
```

**Usage Examples**:
```sql
-- Set user locale
SET app.current_locale = 'fr_FR';

-- Query localized products
SELECT pk_product, name, description
FROM v_product_localized;
-- Returns French translations if available, English otherwise

-- Check translation coverage
SELECT
    current_locale,
    has_translation_for_locale,
    COUNT(*) AS product_count
FROM v_product_localized
GROUP BY current_locale, has_translation_for_locale;

-- Get all translations for a product
SELECT pk_product, all_translations
FROM v_product_localized
WHERE pk_product = 123;
-- Returns: {"en_US": {"name": "Product", ...}, "fr_FR": {"name": "Produit", ...}}
```

#### 🔧 REFACTOR: Localization Utilities

```python
# src/patterns/localization/translation_utils.py
class TranslationManager:
    """Manage translation views and fallback logic"""

    def __init__(self, default_locale: str = "en_US"):
        self.default_locale = default_locale

    def generate_coalesce_fallback(
        self,
        field: str,
        locales: List[str]
    ) -> str:
        """Generate COALESCE chain for locale fallback"""
        coalesce_args = [f"{locale}_table.{field}" for locale in locales]
        return f"COALESCE({', '.join(coalesce_args)})"

    def detect_missing_translations(
        self,
        entity: str,
        target_locale: str
    ) -> List[int]:
        """Find records missing translations"""
        pass

    def generate_translation_coverage_report(self) -> Dict:
        """Generate translation coverage metrics"""
        pass
```

#### ✅ QA: Validate Translated Views

```bash
# Unit tests
uv run pytest tests/unit/patterns/localization/test_translated_view.py -v

# Integration test: Multi-locale queries
uv run pytest tests/integration/patterns/localization/test_locale_fallback.py -v

# Coverage report
uv run pytest tests/integration/patterns/localization/test_translation_coverage.py -v
```

---

### TDD Cycle 2: Locale-Aware Aggregation

#### 🔴 RED: Test Localized Aggregations

```bash
uv run pytest tests/unit/patterns/localization/test_locale_aggregation.py -v
```

**Test Case**: Count products by translated category name

#### 🟢 GREEN: Implement Locale-Aware Aggregation

```yaml
# stdlib/queries/localization/locale_aggregation.yaml
pattern: localization/locale_aggregation
description: Aggregations grouped by translated fields
category: localization
complexity: medium

parameters:
  entity:
    type: entity_reference
    required: true

  group_by_field:
    type: string
    required: true
    description: Translatable field to group by

  aggregations:
    type: array
    items:
      metric: string
      function: enum[COUNT, SUM, AVG, MAX, MIN]
    required: true
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    -- Localized group-by field
    COALESCE(
        current_locale.{{ group_by_field }},
        fallback_locale.{{ group_by_field }}
    ) AS {{ group_by_field }},

    -- Aggregations
    {% for agg in aggregations %}
    {{ agg.function }}({{ entity.alias }}.{{ agg.field }}) AS {{ agg.metric }},
    {% endfor %}

    -- Metadata
    {{ current_locale_source }}::text AS locale

FROM {{ entity.schema }}.{{ entity.table }} {{ entity.alias }}
INNER JOIN {{ translation_table }} fallback_locale
    ON fallback_locale.{{ entity.fk_field }} = {{ entity.alias }}.{{ entity.pk_field }}
    AND fallback_locale.locale = '{{ fallback_locale }}'
LEFT JOIN {{ translation_table }} current_locale
    ON current_locale.{{ entity.fk_field }} = {{ entity.alias }}.{{ entity.pk_field }}
    AND current_locale.locale = {{ current_locale_source }}::text
WHERE {{ entity.alias }}.deleted_at IS NULL
GROUP BY
    COALESCE(current_locale.{{ group_by_field }}, fallback_locale.{{ group_by_field }}),
    {{ current_locale_source }}::text;
```

#### ✅ QA: Validate Locale Aggregation

```bash
uv run pytest tests/integration/patterns/localization/test_locale_aggregation.py -v
```

---

### Deliverables: Phase 14 (Localization Patterns)

- ✅ **Translated view pattern** - Multi-language with fallback
- ✅ **Locale-aware aggregation** - Grouping by translated fields
- ✅ **Translation utilities** - Coverage reports, missing detection
- ✅ **Documentation** - Pattern reference, i18n best practices
- ✅ **Tests** - Multi-locale integration tests

**Pattern Count**: 2 localization patterns
**Locales Supported**: Any (configurable)
**Fallback Strategy**: Cascade (current → fallback → NULL)

---

## Phase 15: Metric Patterns (Week 20-21)

**Objective**: Business KPI calculations and dashboard metrics

### TDD Cycle 1: KPI Calculator Pattern

#### 🔴 RED: Test KPI Calculation

```bash
uv run pytest tests/unit/patterns/metrics/test_kpi_calculator.py -v
```

**Test Case**: Machine utilization rate (active days / total days)

#### 🟢 GREEN: Implement KPI Calculator Pattern

```yaml
# stdlib/queries/metrics/kpi_calculator.yaml
pattern: metrics/kpi_calculator
description: Business KPI calculations with formulas
category: metrics
complexity: high

parameters:
  base_entity:
    type: entity_reference
    required: true
    description: Entity to calculate KPIs for

  time_window:
    type: string
    default: "30 days"
    description: Time window for calculations

  metrics:
    type: array
    required: true
    items:
      name: string
      formula: string  # SQL expression
      format: enum[percentage, currency, integer, decimal]
      thresholds:
        type: object
        properties:
          warning: number
          critical: number

  refresh_strategy:
    type: enum
    enum: [real_time, materialized, scheduled]
    default: real_time

examples:
  - name: Machine Utilization Metrics
    description: Track machine uptime and utilization
    config:
      base_entity: Machine
      time_window: 30 days
      metrics:
        - name: utilization_rate
          formula: "COUNT(DISTINCT active_date) / 30.0"
          format: percentage
          thresholds: {warning: 0.5, critical: 0.3}
```

**Template**:
```jinja2
{# stdlib/queries/metrics/kpi_calculator.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description KPI dashboard for {{ base_entity.name }}
-- @fraiseql:pattern metrics/kpi_calculator

{% if refresh_strategy == 'materialized' %}
CREATE MATERIALIZED VIEW {{ schema }}.{{ name }} AS
{% else %}
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
{% endif %}

WITH base_data AS (
    -- Gather raw data for calculations
    SELECT
        {{ base_entity.pk_field }},
        {{ base_entity.alias }}.*,

        -- Time-windowed aggregations
        {% for metric in metrics %}
        {% if metric.requires_aggregation %}
        {{ metric.aggregation_source }} AS {{ metric.name }}_source,
        {% endif %}
        {% endfor %}

        -- Reference date range
        CURRENT_DATE - INTERVAL '{{ time_window }}' AS window_start,
        CURRENT_DATE AS window_end

    FROM {{ base_entity.schema }}.{{ base_entity.table }} {{ base_entity.alias }}
    {% for join in metric_joins %}
    LEFT JOIN {{ join.table }} {{ join.alias }}
        ON {{ join.condition }}
        AND {{ join.alias }}.date_field BETWEEN CURRENT_DATE - INTERVAL '{{ time_window }}' AND CURRENT_DATE
    {% endfor %}
    WHERE {{ base_entity.alias }}.deleted_at IS NULL
    GROUP BY {{ base_entity.pk_field }}
),
calculated_metrics AS (
    SELECT
        {{ base_entity.pk_field }},

        -- Calculate KPIs
        {% for metric in metrics %}
        {{ metric.formula }} AS {{ metric.name }},
        {% endfor %}

        window_start,
        window_end

    FROM base_data
)
SELECT
    cm.*,

    -- Format metrics
    {% for metric in metrics %}
    {% if metric.format == 'percentage' %}
    ROUND((cm.{{ metric.name }} * 100)::numeric, 2) AS {{ metric.name }}_pct,
    {% elif metric.format == 'currency' %}
    TO_CHAR(cm.{{ metric.name }}, 'FM$999,999,999.00') AS {{ metric.name }}_formatted,
    {% endif %}
    {% endfor %}

    -- Threshold status
    {% for metric in metrics %}
    {% if metric.thresholds %}
    CASE
        WHEN cm.{{ metric.name }} < {{ metric.thresholds.critical }} THEN 'CRITICAL'
        WHEN cm.{{ metric.name }} < {{ metric.thresholds.warning }} THEN 'WARNING'
        ELSE 'OK'
    END AS {{ metric.name }}_status,
    {% endif %}
    {% endfor %}

    -- Metadata
    NOW() AS calculated_at,
    '{{ time_window }}' AS time_window

FROM calculated_metrics cm;

{% if refresh_strategy == 'materialized' %}
-- Refresh function
CREATE OR REPLACE FUNCTION {{ schema }}.refresh_{{ name }}()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY {{ schema }}.{{ name }};
END;
$$ LANGUAGE plpgsql;
{% endif %}

-- Index for entity lookup
CREATE INDEX IF NOT EXISTS idx_{{ name }}_entity
    ON {{ schema }}.{{ name }}({{ base_entity.pk_field }});

COMMENT ON {% if refresh_strategy == 'materialized' %}MATERIALIZED VIEW{% else %}VIEW{% endif %} {{ schema }}.{{ name }} IS
    'KPI metrics for {{ base_entity.name }} over {{ time_window }} window. {% if refresh_strategy == 'materialized' %}Refresh: SELECT refresh_{{ name }}();{% endif %}';
```

**Example: Machine Utilization KPIs**:
```yaml
views:
  - name: v_machine_utilization_metrics
    pattern: metrics/kpi_calculator
    config:
      base_entity: Machine
      time_window: 30 days
      metrics:
        - name: utilization_rate
          formula: |
            COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.status = 'active') / 30.0
          format: percentage
          thresholds:
            warning: 0.5
            critical: 0.3

        - name: downtime_hours
          formula: |
            COALESCE(SUM(EXTRACT(EPOCH FROM (m.downtime_end - m.downtime_start)) / 3600), 0)
          format: decimal
          thresholds:
            warning: 24
            critical: 48

        - name: maintenance_cost
          formula: |
            COALESCE(SUM(mc.cost), 0)
          format: currency

        - name: print_volume
          formula: |
            COALESCE(SUM(r.page_count), 0)
          format: integer
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_machine_utilization_metrics AS
WITH base_data AS (
    SELECT
        m.pk_machine,
        m.*,
        COUNT(DISTINCT a.allocation_date) FILTER (WHERE a.status = 'active') AS active_days,
        SUM(EXTRACT(EPOCH FROM (m.downtime_end - m.downtime_start)) / 3600) AS total_downtime_hours,
        SUM(mc.cost) AS total_maintenance_cost,
        SUM(r.page_count) AS total_print_volume
    FROM tenant.tb_machine m
    LEFT JOIN tenant.tb_allocation a
        ON a.fk_machine = m.pk_machine
        AND a.allocation_date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
    LEFT JOIN tenant.tb_maintenance_cost mc
        ON mc.fk_machine = m.pk_machine
        AND mc.date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
    LEFT JOIN tenant.tb_reading r
        ON r.fk_machine = m.pk_machine
        AND r.reading_date BETWEEN CURRENT_DATE - INTERVAL '30 days' AND CURRENT_DATE
    WHERE m.deleted_at IS NULL
    GROUP BY m.pk_machine
),
calculated_metrics AS (
    SELECT
        pk_machine,
        active_days / 30.0 AS utilization_rate,
        COALESCE(total_downtime_hours, 0) AS downtime_hours,
        COALESCE(total_maintenance_cost, 0) AS maintenance_cost,
        COALESCE(total_print_volume, 0) AS print_volume
    FROM base_data
)
SELECT
    cm.*,

    -- Formatted metrics
    ROUND((cm.utilization_rate * 100)::numeric, 2) AS utilization_rate_pct,
    TO_CHAR(cm.maintenance_cost, 'FM$999,999,999.00') AS maintenance_cost_formatted,

    -- Threshold status
    CASE
        WHEN cm.utilization_rate < 0.3 THEN 'CRITICAL'
        WHEN cm.utilization_rate < 0.5 THEN 'WARNING'
        ELSE 'OK'
    END AS utilization_rate_status,

    CASE
        WHEN cm.downtime_hours > 48 THEN 'CRITICAL'
        WHEN cm.downtime_hours > 24 THEN 'WARNING'
        ELSE 'OK'
    END AS downtime_hours_status,

    NOW() AS calculated_at,
    '30 days' AS time_window

FROM calculated_metrics cm;
```

**Usage**:
```sql
-- Dashboard query
SELECT
    pk_machine,
    utilization_rate_pct,
    utilization_rate_status,
    downtime_hours,
    maintenance_cost_formatted,
    print_volume
FROM v_machine_utilization_metrics
WHERE utilization_rate_status IN ('WARNING', 'CRITICAL')
ORDER BY utilization_rate ASC;

-- Alert query
SELECT pk_machine, utilization_rate_pct
FROM v_machine_utilization_metrics
WHERE utilization_rate_status = 'CRITICAL';
```

#### 🔧 REFACTOR: Metric Utilities

```python
# src/patterns/metrics/kpi_builder.py
class KPIBuilder:
    """Build KPI calculation views"""

    def parse_formula(self, formula: str) -> Dict:
        """Parse SQL formula into AST"""
        pass

    def detect_required_joins(self, formula: str) -> List[str]:
        """Detect which tables need to be joined"""
        pass

    def generate_threshold_checks(self, metric: Dict) -> str:
        """Generate CASE statement for threshold status"""
        thresholds = metric.get('thresholds', {})
        return f"""
        CASE
            WHEN {metric['name']} < {thresholds.get('critical', 0)} THEN 'CRITICAL'
            WHEN {metric['name']} < {thresholds.get('warning', 0)} THEN 'WARNING'
            ELSE 'OK'
        END AS {metric['name']}_status
        """

    def generate_formatter(self, metric: Dict) -> str:
        """Generate formatting expression"""
        formats = {
            'percentage': f"ROUND(({metric['name']} * 100)::numeric, 2)",
            'currency': f"TO_CHAR({metric['name']}, 'FM$999,999,999.00')",
            'integer': f"ROUND({metric['name']})::integer",
            'decimal': f"ROUND({metric['name']}::numeric, 2)"
        }
        return formats.get(metric.get('format', 'decimal'))
```

#### ✅ QA: Validate KPI Calculator

```bash
uv run pytest tests/unit/patterns/metrics/test_kpi_calculator.py -v
uv run pytest tests/integration/patterns/metrics/test_kpi_accuracy.py -v
```

---

### TDD Cycle 2: Trend Analysis Pattern

#### 🔴 RED: Test Trend Detection

```bash
uv run pytest tests/unit/patterns/metrics/test_trend_analysis.py -v
```

**Test Case**: Detect upward/downward trends in metrics

#### 🟢 GREEN: Implement Trend Analysis Pattern

```yaml
# stdlib/queries/metrics/trend_analysis.yaml
pattern: metrics/trend_analysis
description: Time-series trend analysis with moving averages
category: metrics
complexity: high

parameters:
  base_metric_view:
    type: string
    required: true
    description: View containing base metrics

  trend_metrics:
    type: array
    required: true
    items:
      metric: string
      periods: array  # [7, 30, 90] days
      smoothing: enum[simple, weighted, exponential]

  trend_detection:
    enabled: boolean
    sensitivity: enum[low, medium, high]
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
WITH historical_data AS (
    SELECT
        date_trunc('day', calculated_at) AS metric_date,
        {% for metric in trend_metrics %}
        AVG({{ metric.metric }}) AS {{ metric.metric }}_daily_avg,
        {% endfor %}
    FROM {{ base_metric_view }}
    WHERE calculated_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY date_trunc('day', calculated_at)
),
moving_averages AS (
    SELECT
        metric_date,
        {% for metric in trend_metrics %}
        {% for period in metric.periods %}
        AVG({{ metric.metric }}_daily_avg) OVER (
            ORDER BY metric_date
            ROWS BETWEEN {{ period - 1 }} PRECEDING AND CURRENT ROW
        ) AS {{ metric.metric }}_ma{{ period }},
        {% endfor %}
        {% endfor %}
    FROM historical_data
)
SELECT
    *,

    -- Trend detection
    {% for metric in trend_metrics %}
    CASE
        WHEN {{ metric.metric }}_ma7 > {{ metric.metric }}_ma30 * 1.1 THEN 'INCREASING'
        WHEN {{ metric.metric }}_ma7 < {{ metric.metric }}_ma30 * 0.9 THEN 'DECREASING'
        ELSE 'STABLE'
    END AS {{ metric.metric }}_trend
    {% endfor %}

FROM moving_averages
ORDER BY metric_date DESC;
```

#### ✅ QA: Validate Trend Analysis

```bash
uv run pytest tests/integration/patterns/metrics/test_trend_analysis.py -v
```

---

### Deliverables: Phase 15 (Metric Patterns)

- ✅ **KPI calculator pattern** - Business metrics with thresholds
- ✅ **Trend analysis pattern** - Moving averages, trend detection
- ✅ **Metric utilities** - Formula parser, threshold checker
- ✅ **Documentation** - KPI best practices, dashboard examples
- ✅ **Tests** - Accuracy validation, performance benchmarks

**Pattern Count**: 2 metric patterns
**KPI Support**: Unlimited formulas
**Threshold Alerting**: Built-in

---

## Phase 16: Security Patterns (Week 22-23)

**Objective**: Row-level security, permission filtering, data masking

### TDD Cycle 1: Permission Filter Pattern

#### 🔴 RED: Test Permission Filtering

```bash
uv run pytest tests/unit/patterns/security/test_permission_filter.py -v
```

**Test Case**: User can only see contracts from their organization

#### 🟢 GREEN: Implement Permission Filter Pattern

```yaml
# stdlib/queries/security/permission_filter.yaml
pattern: security/permission_filter
description: Row-level permission filtering based on user context
category: security
complexity: high

parameters:
  base_entity:
    type: entity_reference
    required: true

  permission_checks:
    type: array
    required: true
    items:
      type: enum[ownership, organizational_hierarchy, role_based, custom]
      field: string  # Field to check
      allowed_roles: array  # For role_based
      custom_condition: string  # For custom

  user_context_source:
    type: string
    default: "CURRENT_SETTING('app.current_user_id')"

  deny_by_default:
    type: boolean
    default: true
    description: Deny access unless explicitly permitted

examples:
  - name: Contract Access Control
    description: Users see contracts they own or from their org
    config:
      base_entity: Contract
      permission_checks:
        - type: ownership
          field: created_by
        - type: organizational_hierarchy
          field: organization_id
        - type: role_based
          allowed_roles: [admin, contract_manager]
```

**Template**:
```jinja2
{# stdlib/queries/security/permission_filter.sql.jinja2 #}
-- @fraiseql:view
-- @fraiseql:description Permission-filtered {{ entity.name }}
-- @fraiseql:pattern security/permission_filter
-- @fraiseql:security row_level

CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT {{ entity.alias }}.*
FROM {{ entity.schema }}.{{ entity.table }} {{ entity.alias }}

{% for check in permission_checks %}
{% if check.type == 'organizational_hierarchy' %}
-- Join organizational hierarchy for permission check
LEFT JOIN tenant.tb_organizational_unit user_ou
    ON user_ou.deleted_at IS NULL
LEFT JOIN tenant.tb_user current_user
    ON current_user.id = {{ user_context_source }}::uuid
    AND current_user.deleted_at IS NULL
{% endif %}
{% endfor %}

WHERE {{ entity.alias }}.deleted_at IS NULL

{% if deny_by_default %}
AND (
{% else %}
OR (
{% endif %}

    {% for check in permission_checks %}

    {% if check.type == 'ownership' %}
    -- Ownership check
    {{ entity.alias }}.{{ check.field }} = {{ user_context_source }}::uuid

    {% elif check.type == 'organizational_hierarchy' %}
    -- Organizational hierarchy check
    {{ entity.alias }}.{{ check.field }} IN (
        SELECT ou.pk_organizational_unit
        FROM tenant.tb_organizational_unit ou
        WHERE ou.path <@ current_user.organizational_unit_path
          AND ou.deleted_at IS NULL
    )

    {% elif check.type == 'role_based' %}
    -- Role-based check
    EXISTS (
        SELECT 1
        FROM app.tb_user_role ur
        WHERE ur.user_id = {{ user_context_source }}::uuid
          AND ur.role IN ({{ check.allowed_roles|map('quote')|join(', ') }})
          AND ur.deleted_at IS NULL
    )

    {% elif check.type == 'custom' %}
    -- Custom permission logic
    ({{ check.custom_condition }})

    {% endif %}

    {% if not loop.last %}OR{% endif %}

    {% endfor %}
);

-- Enable RLS on base table (optional)
{% if enable_rls %}
ALTER TABLE {{ entity.schema }}.{{ entity.table }} ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_{{ entity.table }}_access
ON {{ entity.schema }}.{{ entity.table }}
FOR SELECT
USING (
    {{ entity.pk_field }} IN (
        SELECT {{ entity.pk_field }}
        FROM {{ schema }}.{{ name }}
    )
);
{% endif %}

COMMENT ON VIEW {{ schema }}.{{ name }} IS
    'Permission-filtered view of {{ entity.name }}. Access controlled by: {{ permission_checks|map(attribute='type')|join(', ') }}';
```

**Usage**:
```sql
-- Set user context
SET app.current_user_id = 'a1b2c3d4-...';

-- Query contracts (automatically filtered)
SELECT * FROM v_contract_accessible;
-- Only returns contracts user has permission to see

-- Admin override (if has admin role)
SELECT * FROM v_contract_accessible;
-- Returns all contracts
```

#### 🔧 REFACTOR: Security Utilities

```python
# src/patterns/security/permission_checker.py
class PermissionChecker:
    """Validate permission configurations"""

    def validate_permission_checks(self, checks: List[Dict]) -> ValidationResult:
        """Ensure permission checks are secure"""
        errors = []

        # Check for common security mistakes
        if not checks:
            errors.append("At least one permission check required")

        for check in checks:
            if check['type'] == 'custom':
                if 'OR 1=1' in check['custom_condition']:
                    errors.append("Insecure custom condition detected")

        return ValidationResult(errors=errors)

    def generate_rls_policy(self, entity: Dict, checks: List[Dict]) -> str:
        """Generate PostgreSQL RLS policy"""
        pass
```

#### ✅ QA: Validate Permission Filters

```bash
# Security tests
uv run pytest tests/unit/patterns/security/test_permission_filter.py -v
uv run pytest tests/integration/patterns/security/test_access_control.py -v

# Security audit
uv run pytest tests/security/test_permission_bypass.py -v
```

---

### TDD Cycle 2: Data Masking Pattern

#### 🔴 RED: Test Sensitive Data Masking

```bash
uv run pytest tests/unit/patterns/security/test_data_masking.py -v
```

**Test Case**: Mask email addresses for non-admin users

#### 🟢 GREEN: Implement Data Masking Pattern

```yaml
# stdlib/queries/security/data_masking.yaml
pattern: security/data_masking
description: Mask sensitive data based on user role
category: security
complexity: medium

parameters:
  base_entity:
    type: entity_reference
    required: true

  masked_fields:
    type: array
    required: true
    items:
      field: string
      mask_type: enum[redact, partial, hash, null]
      unmasked_roles: array  # Roles that see unmasked data
      partial_config:  # For partial masking
        show_first: integer
        show_last: integer
        mask_char: string

examples:
  - name: Contact with Masked PII
    config:
      base_entity: Contact
      masked_fields:
        - field: email
          mask_type: partial
          unmasked_roles: [admin, hr_manager]
          partial_config:
            show_first: 2
            show_last: 0
            mask_char: "*"
        - field: phone
          mask_type: partial
          partial_config:
            show_first: 0
            show_last: 4
        - field: ssn
          mask_type: hash
          unmasked_roles: [admin]
```

**Template**:
```jinja2
CREATE OR REPLACE VIEW {{ schema }}.{{ name }} AS
SELECT
    {{ entity.pk_field }},

    -- Non-sensitive fields (passthrough)
    {% for field in entity.fields if field.name not in masked_fields|map(attribute='field') %}
    {{ entity.alias }}.{{ field.name }},
    {% endfor %}

    -- Masked fields
    {% for masked in masked_fields %}
    CASE
        {% if masked.unmasked_roles %}
        -- Unmasked for specific roles
        WHEN EXISTS (
            SELECT 1 FROM app.tb_user_role ur
            WHERE ur.user_id = CURRENT_SETTING('app.current_user_id')::uuid
              AND ur.role IN ({{ masked.unmasked_roles|map('quote')|join(', ') }})
        ) THEN {{ entity.alias }}.{{ masked.field }}
        {% endif %}

        {% if masked.mask_type == 'redact' %}
        -- Full redaction
        ELSE '[REDACTED]'

        {% elif masked.mask_type == 'partial' %}
        -- Partial masking
        ELSE
            SUBSTRING({{ entity.alias }}.{{ masked.field }}, 1, {{ masked.partial_config.show_first }}) ||
            REPEAT('{{ masked.partial_config.mask_char }}', GREATEST(0, LENGTH({{ entity.alias }}.{{ masked.field }}) - {{ masked.partial_config.show_first }} - {{ masked.partial_config.show_last }})) ||
            SUBSTRING({{ entity.alias }}.{{ masked.field }}, LENGTH({{ entity.alias }}.{{ masked.field }}) - {{ masked.partial_config.show_last }} + 1)

        {% elif masked.mask_type == 'hash' %}
        -- Hash
        ELSE MD5({{ entity.alias }}.{{ masked.field }})

        {% elif masked.mask_type == 'null' %}
        -- NULL
        ELSE NULL

        {% endif %}
    END AS {{ masked.field }}
    {% if not loop.last %},{% endif %}
    {% endfor %}

FROM {{ entity.schema }}.{{ entity.table }} {{ entity.alias }}
WHERE {{ entity.alias }}.deleted_at IS NULL;
```

**Usage**:
```sql
-- Regular user sees masked data
SET app.current_user_id = 'user123';
SELECT email, phone FROM v_contact_masked;
-- email: "jo********@example.com"
-- phone: "***-***-1234"

-- Admin sees unmasked data
SET ROLE admin;
SELECT email, phone FROM v_contact_masked;
-- email: "john.doe@example.com"
-- phone: "555-123-1234"
```

#### ✅ QA: Validate Data Masking

```bash
uv run pytest tests/integration/patterns/security/test_data_masking.py -v
uv run pytest tests/compliance/test_gdpr_compliance.py -v
```

---

### Deliverables: Phase 16 (Security Patterns)

- ✅ **Permission filter pattern** - Row-level access control
- ✅ **Data masking pattern** - PII protection
- ✅ **Security utilities** - Permission validator, RLS generator
- ✅ **Documentation** - Security best practices, GDPR compliance
- ✅ **Tests** - Security audit, penetration testing

**Pattern Count**: 2 security patterns
**Compliance**: GDPR, SOC2 ready
**RLS Support**: Full PostgreSQL RLS integration

---

## Summary: Advanced Patterns Implementation

### Pattern Breakdown

| Phase | Category | Patterns | Week | Complexity | Enterprise Value |
|-------|----------|----------|------|------------|------------------|
| **13** | Temporal | 4 | 17-18 | High | Time-series, audit trails |
| **14** | Localization | 2 | 19 | Medium | Multi-language support |
| **15** | Metrics | 2 | 20-21 | High | KPIs, dashboards |
| **16** | Security | 2 | 22-23 | Very High | Access control, compliance |

**Total**: 10 advanced patterns across 4 categories

---

### Integration with Core Patterns

These advanced patterns build on the core infrastructure:

```
Core Patterns (Phase 0-12)
    ↓
Pattern Registry & Generator Pipeline
    ↓
    ├─→ Temporal Patterns (Phase 13)
    ├─→ Localization Patterns (Phase 14)
    ├─→ Metric Patterns (Phase 15)
    └─→ Security Patterns (Phase 16)
```

All advanced patterns use:
- Same YAML configuration format
- Same Jinja2 templating system
- Same test infrastructure
- Same documentation structure

---

### Success Metrics (Advanced Patterns)

#### Quantitative
- ✅ **10 advanced patterns** implemented
- ✅ **95%+ test coverage** for advanced patterns
- ✅ **< 100ms** generation time per pattern
- ✅ **50+ integration tests**
- ✅ **GDPR/SOC2 compliance** validated

#### Qualitative
- ✅ Enterprise-grade security features
- ✅ Multi-language support for global apps
- ✅ Business intelligence ready
- ✅ Audit trail compliance
- ✅ Production-validated KPIs

---

### Risk Mitigation (Advanced Patterns)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Security vulnerabilities | Medium | Critical | Comprehensive security testing, external audit |
| Performance degradation | Medium | High | Materialized view options, indexing strategies |
| Complex formula parsing | Medium | Medium | Formula validation, safe SQL injection prevention |
| Translation coverage gaps | Low | Low | Coverage reports, missing translation detection |
| KPI accuracy issues | Low | High | Validation against known results, unit tests |

---

### Timeline Summary (Advanced Patterns)

| Week | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| **17-18** | 13 | Temporal | Snapshot, audit trail, SCD Type 2, temporal range |
| **19** | 14 | Localization | Translated views, locale aggregation |
| **20-21** | 15 | Metrics | KPI calculator, trend analysis |
| **22-23** | 16 | Security | Permission filter, data masking |

**Total**: 7 weeks (1.75 months)

---

### Combined Project Timeline

**Core + Advanced Patterns**:
- **Weeks 1-16**: Core patterns (Phases 0-12)
- **Weeks 17-23**: Advanced patterns (Phases 13-16)
- **Total**: 23 weeks (~5.5 months)

**Pattern Library Size**:
- **Core patterns**: 49 (from PrintOptim)
- **Advanced patterns**: 10 (new)
- **Total**: 59 production-ready patterns

---

## Next Steps (Advanced Patterns)

### Prerequisites
1. ✅ Complete Phases 0-12 (Core patterns)
2. ✅ Verify pattern infrastructure stable
3. ✅ Check localization requirements (Phase 14 dependency)
4. ✅ Security review for permission patterns

### Immediate Actions
1. Review this advanced patterns plan
2. Prioritize pattern categories (all 4 or subset?)
3. Decide on security pattern scope (RLS integration?)
4. Schedule Phase 13 kickoff

### First Month (Phases 13-14)
1. Implement temporal patterns (snapshot, audit, SCD)
2. Verify localization needs, implement if required
3. Document temporal best practices
4. Create 10+ temporal pattern examples

---

**Created**: 2025-11-10
**Author**: Claude (Assistant)
**Status**: Ready for Implementation (after core patterns)
**Estimated Effort**: 7 weeks (1 developer full-time)
**Dependencies**: Core Query Pattern Library (Phases 0-12)
**Impact**: Very High - Enterprise-grade features for production systems 🚀
