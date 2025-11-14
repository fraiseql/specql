# Temporal Audit Trail Pattern

**Category**: Temporal Patterns
**Use Case**: Complete change history tracking with before/after values
**Complexity**: High
**Enterprise Feature**: ✅ Yes

## Overview

The audit trail pattern provides comprehensive change tracking for entities, capturing every INSERT, UPDATE, and DELETE operation with full before/after snapshots. Essential for:

- Regulatory compliance (GDPR, SOC2, HIPAA)
- Forensic analysis and debugging
- Change history reporting
- Data integrity verification

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entity` | entity_reference | ✅ | - | Entity to audit |
| `audit_table` | string | ✅ | - | Audit table name (e.g., tb_contract_audit) |
| `change_columns` | array | ❌ | all | Columns to track (default: all) |
| `include_user_info` | boolean | ❌ | true | Include user who made change |
| `include_diff` | boolean | ❌ | true | Include before/after diff |
| `retention_period` | string | ❌ | "7 years" | Audit retention period |

## Generated SQL Features

- ✅ Automatic audit triggers on INSERT/UPDATE/DELETE
- ✅ JSONB snapshots of old/new values
- ✅ User context tracking via settings
- ✅ Transaction metadata capture
- ✅ Configurable retention policies
- ✅ Change diff computation

## Examples

### Example 1: Contract Audit Trail

```yaml
views:
  - name: v_contract_audit_trail
    pattern: temporal/audit_trail
    config:
      entity: Contract
      audit_table: tb_contract_audit
      include_user_info: true
      include_diff: true
      retention_period: "10 years"
```

**Generated SQL**:
```sql
-- Audit table (auto-created)
CREATE TABLE IF NOT EXISTS tenant.tb_contract_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    pk_contract INTEGER NOT NULL,
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
CREATE OR REPLACE FUNCTION tenant.tb_contract_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO tenant.tb_contract_audit (
            pk_contract, operation, changed_by, new_values
        ) VALUES (
            NEW.pk_contract,
            'INSERT',
            NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
            to_jsonb(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO tenant.tb_contract_audit (
            pk_contract, operation, changed_by, old_values, new_values
        ) VALUES (
            NEW.pk_contract,
            'UPDATE',
            NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
            to_jsonb(OLD),
            to_jsonb(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO tenant.tb_contract_audit (
            pk_contract, operation, changed_by, old_values
        ) VALUES (
            OLD.pk_contract,
            'DELETE',
            NULLIF(CURRENT_SETTING('app.current_user_id', true), '')::uuid,
            to_jsonb(OLD)
        );
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Attach trigger
CREATE TRIGGER trg_tb_contract_audit
AFTER INSERT OR UPDATE OR DELETE ON tenant.tb_contract
FOR EACH ROW EXECUTE FUNCTION tenant.tb_contract_audit_trigger();

-- Audit view
CREATE OR REPLACE VIEW tenant.v_contract_audit_trail AS
WITH audit_with_changes AS (
    SELECT
        audit.audit_id,
        audit.pk_contract,
        audit.operation,
        audit.changed_at,
        audit.changed_by,

        u.data->>'email' AS changed_by_email,
        u.data->>'name' AS changed_by_name,

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
            WHEN audit.operation = 'INSERT' THEN audit.new_values
            WHEN audit.operation = 'DELETE' THEN audit.old_values
        END AS changes,

        -- Full snapshots
        audit.old_values AS previous_state,
        audit.new_values AS current_state,

        -- Metadata
        audit.transaction_id,
        audit.application_name,
        audit.client_addr

    FROM tenant.tb_contract_audit audit
    LEFT JOIN app.tb_user u ON u.id = audit.changed_by
    WHERE audit.changed_at >= CURRENT_DATE - INTERVAL '10 years'
)
SELECT
    *,
    -- Time since previous change
    changed_at - LAG(changed_at) OVER (
        PARTITION BY pk_contract
        ORDER BY changed_at
    ) AS time_since_last_change,

    -- Change sequence number
    ROW_NUMBER() OVER (
        PARTITION BY pk_contract
        ORDER BY changed_at
    ) AS change_sequence

FROM audit_with_changes
ORDER BY pk_contract, changed_at DESC;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_v_contract_audit_trail_entity
    ON tenant.v_contract_audit_trail(pk_contract, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_v_contract_audit_trail_user
    ON tenant.v_contract_audit_trail(changed_by, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_v_contract_audit_trail_time
    ON tenant.v_contract_audit_trail(changed_at DESC);
```

## Usage Examples

### Change History Queries

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
```

### Audit Reporting

```sql
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

-- Detect unusual activity
SELECT
    pk_contract,
    changed_by_email,
    COUNT(*) AS changes_in_hour
FROM v_contract_audit_trail
WHERE changed_at >= CURRENT_DATE - INTERVAL '1 hour'
GROUP BY pk_contract, changed_by_email
HAVING COUNT(*) > 10  -- More than 10 changes per hour
ORDER BY changes_in_hour DESC;
```

### Compliance Queries

```sql
-- GDPR: Data access history for user
SELECT
    changed_at,
    changed_by_email,
    operation,
    CASE
        WHEN operation = 'SELECT' THEN 'Data accessed'
        WHEN operation = 'UPDATE' THEN 'Data modified'
        ELSE operation
    END AS activity
FROM v_contract_audit_trail
WHERE pk_contract IN (
    SELECT pk_contract
    FROM tenant.tb_contract
    WHERE customer_id = ?
)
  AND changed_at >= ?  -- Since consent given
ORDER BY changed_at DESC;
```

## When to Use

✅ **Use when**:
- Regulatory compliance requirements
- Need complete change history
- Forensic analysis needed
- Data integrity verification
- User activity monitoring

❌ **Don't use when**:
- Entity rarely changes (use simple versioning)
- Performance is critical (audit tables add overhead)
- Only need current state (use snapshot pattern)

## Performance Considerations

- **Partitioning**: Date-based partitioning for large audit tables
- **Retention**: Automated cleanup of old audit records
- **Indexing**: Composite indexes on (entity_id, changed_at)
- **Archival**: Move old audit data to separate tables
- **Compression**: Enable table compression for storage efficiency

## Security Considerations

- **Access Control**: Audit views should have restricted permissions
- **Data Masking**: Sensitive fields in audit data may need masking
- **Encryption**: Consider encrypting audit tables at rest
- **Monitoring**: Alert on unusual audit activity patterns

## Related Patterns

- **Snapshot**: Point-in-time views without full change history
- **SCD Type 2**: Automated version management
- **Data Masking**: Hide sensitive data in audit trails