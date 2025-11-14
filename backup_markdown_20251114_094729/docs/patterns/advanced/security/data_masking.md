# Security Data Masking Pattern

**Category**: Security Patterns
**Use Case**: Dynamic data masking based on user roles and permissions
**Complexity**: Medium
**Enterprise Feature**: ✅ Yes

## Overview

The data masking pattern automatically masks sensitive data fields based on user roles and permissions, showing different data to different users. Essential for:

- PII (Personally Identifiable Information) protection
- GDPR and privacy compliance
- Role-based data visibility
- Secure data sharing across teams

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_entity` | entity_reference | ✅ | - | Entity containing sensitive data |
| `masked_fields` | array | ✅ | - | Fields to mask with rules |
| `user_context_source` | string | ❌ | CURRENT_SETTING | How to get current user |

## Generated SQL Features

- ✅ Role-based field masking (redact, partial, hash, null)
- ✅ Partial masking with configurable patterns
- ✅ Automatic role detection
- ✅ Multiple masking strategies per field

## Examples

### Example 1: Contact PII Protection

```yaml
views:
  - name: v_contact_masked
    pattern: security/data_masking
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

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_contact_masked AS
SELECT
    c.pk_contact,

    -- Non-sensitive fields (passthrough)
    c.first_name,
    c.last_name,
    c.company,

    -- Masked fields
    CASE
        -- Unmasked for specific roles
        WHEN EXISTS (
            SELECT 1 FROM app.tb_user_role ur
            WHERE ur.user_id = CURRENT_SETTING('app.current_user_id')::uuid
              AND ur.role IN ('admin', 'hr_manager')
        ) THEN c.email
        -- Partial masking
        ELSE
            SUBSTRING(c.email, 1, 2) ||
            REPEAT('*', GREATEST(0, LENGTH(c.email) - 2 - 0)) ||
            SUBSTRING(c.email, LENGTH(c.email) - 0 + 1)
    END AS email,

    CASE
        WHEN EXISTS (
            SELECT 1 FROM app.tb_user_role ur
            WHERE ur.user_id = CURRENT_SETTING('app.current_user_id')::uuid
              AND ur.role IN ('admin', 'hr_manager')
        ) THEN c.phone
        ELSE
            REPEAT('*', GREATEST(0, LENGTH(c.phone) - 0 - 4)) ||
            SUBSTRING(c.phone, LENGTH(c.phone) - 4 + 1)
    END AS phone,

    CASE
        WHEN EXISTS (
            SELECT 1 FROM app.tb_user_role ur
            WHERE ur.user_id = CURRENT_SETTING('app.current_user_id')::uuid
              AND ur.role IN ('admin')
        ) THEN c.ssn
        ELSE MD5(c.ssn)
    END AS ssn

FROM tenant.tb_contact c
WHERE c.deleted_at IS NULL;
```

## Masking Types

### Redact (Full Masking)
Completely hides the field:
```yaml
- field: secret_key
  mask_type: redact
```
**Output**: `[REDACTED]`

### Partial Masking
Shows only parts of the data:
```yaml
- field: credit_card
  mask_type: partial
  partial_config:
    show_first: 4    # Show first 4 digits
    show_last: 4     # Show last 4 digits
    mask_char: "*"   # Use * for masking
```
**Input**: `4111111111111111`
**Output**: `4111********1111`

### Hash (One-way)
Creates irreversible hash:
```yaml
- field: ssn
  mask_type: hash
```
**Output**: `a1b2c3d4e5f6...` (MD5 hash)

### Null (Complete Removal)
Replaces with NULL:
```yaml
- field: internal_notes
  mask_type: null
```
**Output**: `NULL`

## Usage Examples

### Role-Based Data Access

```sql
-- Regular user sees masked data
SET app.current_user_id = 'regular-user-id';
SELECT email, phone, ssn FROM v_contact_masked;
-- email: "jo********@example.com"
-- phone: "***-***-1234"
-- ssn: "a1b2c3d4..." (hashed)

-- Admin sees unmasked data
SET ROLE admin;
SELECT email, phone, ssn FROM v_contact_masked;
-- email: "john.doe@example.com"
-- phone: "555-123-1234"
-- ssn: "123-45-6789"
```

### Compliance Reporting

```sql
-- GDPR-compliant export (mask PII)
SELECT
    pk_contact,
    first_name,
    last_name,
    email,  -- Automatically masked
    phone   -- Automatically masked
FROM v_contact_masked
WHERE created_at >= '2020-01-01';

-- Generate masking audit report
SELECT
    CURRENT_SETTING('app.current_user_id')::text AS user_id,
    array_agg(role) AS user_roles,
    COUNT(*) AS records_accessed,
    NOW() AS access_time
FROM app.tb_user_role
WHERE user_id = CURRENT_SETTING('app.current_user_id')::uuid
GROUP BY user_id;
```

### Development vs Production

```sql
-- Development environment (show some data)
DO $$
BEGIN
    IF CURRENT_SETTING('app.environment') = 'development' THEN
        -- Show more data in dev
        SET app.masking_level = 'reduced';
    END IF;
END $$;

-- Production environment (strict masking)
-- Default strict masking applies
```

## Advanced Masking Patterns

### Contextual Masking

```yaml
masked_fields:
  - field: salary
    mask_type: custom
    custom_mask: |
      CASE
        WHEN department = 'HR' THEN salary  -- HR sees actual salaries
        WHEN salary > 100000 THEN 'High'    -- High earners masked as 'High'
        ELSE 'Standard Range'               -- Others get range
      END
```

### Time-Based Masking

```yaml
masked_fields:
  - field: medical_history
    mask_type: redact
    unmasked_roles: [doctor]
    time_restrictions:
      - after_hours: true  -- Only mask after business hours
```

### Geographic Masking

```yaml
masked_fields:
  - field: location_data
    mask_type: partial
    geographic_rules:
      - country: US
        mask_type: partial
        show_precision: state  # Show state, mask city
      - country: EU
        mask_type: redact      # Full masking for GDPR
```

## Performance Considerations

- **Function Overhead**: CASE statements add minimal overhead
- **Role Caching**: Consider caching user roles in session
- **Indexing**: Masked views may not be indexable
- **Materialized Views**: Use for frequently accessed masked data

## Security Best Practices

### Defense in Depth
1. **Application Layer**: Input validation and access control
2. **Database Layer**: View-based masking
3. **Audit Layer**: Log all masked data access

### Secure Masking Functions
```sql
-- Custom masking function for credit cards
CREATE OR REPLACE FUNCTION mask_credit_card(card_number TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Validate input format
    IF NOT card_number ~ '^\d{13,19}$' THEN
        RETURN '[INVALID CARD]';
    END IF;

    -- Apply masking
    RETURN LEFT(card_number, 4) || REPEAT('*', LENGTH(card_number) - 8) || RIGHT(card_number, 4);
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

### Masking Audit
```sql
-- Track masking access patterns
CREATE TABLE audit.masking_access (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    view_name TEXT,
    masking_level TEXT,
    record_count INT,
    accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to log masked data access
CREATE OR REPLACE FUNCTION audit.log_masking_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.masking_access (user_id, view_name, record_count)
    VALUES (
        CURRENT_SETTING('app.current_user_id')::uuid,
        TG_TABLE_NAME,
        (SELECT COUNT(*) FROM NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_masking_access_audit
AFTER SELECT ON tenant.v_contact_masked
EXECUTE FUNCTION audit.log_masking_access();
```

## Compliance Frameworks

### GDPR Compliance
```yaml
masked_fields:
  - field: email
    mask_type: partial
    gdpr_purpose: marketing
    retention_days: 2555  # 7 years
  - field: ip_address
    mask_type: hash
    gdpr_purpose: analytics
```

### HIPAA Compliance
```yaml
masked_fields:
  - field: medical_record_number
    mask_type: hash
    hipaa_protected: true
    unmasked_roles: [doctor, nurse]
  - field: diagnosis
    mask_type: redact
    hipaa_protected: true
    unmasked_roles: [patient]  # Patients can see their own data
```

### PCI DSS Compliance
```yaml
masked_fields:
  - field: credit_card_number
    mask_type: partial
    pci_scope: cardholder_data
    show_first: 6
    show_last: 4
  - field: cvv
    mask_type: null  # Never store or show
```

## When to Use

✅ **Use when**:
- Protecting PII and sensitive data
- Regulatory compliance requirements
- Multi-role data access patterns
- Secure data sharing

❌ **Don't use when**:
- All users need full data access
- No sensitive information present
- Performance critical (masking adds overhead)

## Integration with Other Patterns

### Combined with Permission Filters
```yaml
# First filter rows, then mask columns
views:
  - name: v_secure_contact_data
    pattern: security/permission_filter
    config:
      base_entity: Contact
      permission_checks: [...]
  - name: v_masked_contact_data
    pattern: security/data_masking
    config:
      base_entity: v_secure_contact_data  # Use filtered view as base
      masked_fields: [...]
```

### Audit Trail Integration
```yaml
# Mask sensitive data in audit logs
views:
  - name: v_audit_trail_masked
    pattern: security/data_masking
    config:
      base_entity: audit_trail_view
      masked_fields:
        - field: old_values
          mask_type: partial
        - field: new_values
          mask_type: partial
```

## Related Patterns

- **Permission Filter**: Row-level access control
- **Audit Trail**: Track access to masked data
- **Encryption**: Database-level encryption for stored data