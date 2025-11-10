# Security Permission Filter Pattern

**Category**: Security Patterns
**Use Case**: Row-level security with configurable permission checks
**Complexity**: High
**Enterprise Feature**: ✅ Yes

## Overview

The permission filter pattern implements row-level security (RLS) with flexible permission checks based on user context, organizational hierarchy, and role-based access. Essential for:

- Multi-tenant applications
- Regulatory compliance (GDPR, HIPAA, SOC2)
- Organizational data isolation
- Role-based access control

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_entity` | entity_reference | ✅ | - | Entity to secure |
| `permission_checks` | array | ✅ | - | Permission check definitions |
| `user_context_source` | string | ❌ | CURRENT_SETTING | How to get current user |
| `deny_by_default` | boolean | ❌ | true | Deny access unless permitted |
| `enable_rls` | boolean | ❌ | false | Enable PostgreSQL RLS |

## Generated SQL Features

- ✅ Multiple permission check types (ownership, organizational, role-based, custom)
- ✅ Automatic user context detection
- ✅ Hierarchical organization permissions
- ✅ PostgreSQL RLS integration
- ✅ Configurable security policies

## Examples

### Example 1: Contract Access Control

```yaml
views:
  - name: v_contract_accessible
    pattern: security/permission_filter
    config:
      base_entity: Contract
      permission_checks:
        - type: ownership
          field: created_by
        - type: organizational_hierarchy
          field: organization_id
        - type: role_based
          allowed_roles: [admin, contract_manager]
      user_context_source: "CURRENT_SETTING('app.current_user_id')"
      deny_by_default: true
```

**Generated SQL**:
```sql
CREATE OR REPLACE VIEW tenant.v_contract_accessible AS
SELECT c.*
FROM tenant.tb_contract c

-- Join organizational hierarchy for permission check
LEFT JOIN tenant.tb_organizational_unit user_ou
    ON user_ou.deleted_at IS NULL
LEFT JOIN tenant.tb_user current_user
    ON current_user.id = CURRENT_SETTING('app.current_user_id')::uuid
    AND current_user.deleted_at IS NULL

WHERE c.deleted_at IS NULL
AND (
    -- Ownership check
    c.created_by = CURRENT_SETTING('app.current_user_id')::uuid

    OR
    -- Organizational hierarchy check
    c.organization_id IN (
        SELECT ou.pk_organizational_unit
        FROM tenant.tb_organizational_unit ou
        WHERE ou.path <@ current_user.organizational_unit_path
          AND ou.deleted_at IS NULL
    )

    OR
    -- Role-based check
    EXISTS (
        SELECT 1
        FROM app.tb_user_role ur
        WHERE ur.user_id = CURRENT_SETTING('app.current_user_id')::uuid
          AND ur.role IN ('admin', 'contract_manager')
          AND ur.deleted_at IS NULL
    )
);

COMMENT ON VIEW tenant.v_contract_accessible IS
    'Permission-filtered view of Contract. Access controlled by: ownership, organizational_hierarchy, role_based';
```

## Permission Check Types

### Ownership Check
Grants access to records created by the current user:
```yaml
- type: ownership
  field: created_by  # Field containing user ID
```

### Organizational Hierarchy Check
Uses tree paths for hierarchical permissions:
```yaml
- type: organizational_hierarchy
  field: organization_id  # Field containing org ID
```
**Requires**: Organization table with `path` column (ltree type)

### Role-Based Check
Grants access based on user roles:
```yaml
- type: role_based
  allowed_roles: [admin, manager, auditor]
```

### Custom Check
Arbitrary SQL permission logic:
```yaml
- type: custom
  custom_condition: "c.department_id IN (SELECT department_id FROM user_departments WHERE user_id = CURRENT_USER_ID)"
```

## Usage Examples

### Basic Access Control

```sql
-- Set user context
SET app.current_user_id = 'a1b2c3d4-5678-9abc-def0-123456789abc';

-- Query contracts (automatically filtered)
SELECT * FROM v_contract_accessible;

-- Admin sees all contracts
SET ROLE admin;
SELECT * FROM v_contract_accessible;  -- No filtering applied
```

### Permission Analysis

```sql
-- Check what contracts a user can access
SELECT
    CURRENT_SETTING('app.current_user_id')::text AS user_id,
    COUNT(*) AS accessible_contracts
FROM v_contract_accessible;

-- Compare access across roles
WITH user_permissions AS (
    SELECT
        ur.user_id,
        array_agg(ur.role) AS roles,
        COUNT(c.*) AS contract_count
    FROM app.tb_user_role ur
    CROSS JOIN tenant.v_contract_accessible c  -- Will be filtered per user
    GROUP BY ur.user_id
)
SELECT * FROM user_permissions;
```

### Audit Access Patterns

```sql
-- Log access attempts (requires audit triggers)
CREATE TABLE audit.access_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    table_name TEXT,
    record_id BIGINT,
    action TEXT,
    accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to log view access
CREATE OR REPLACE FUNCTION audit.log_contract_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.access_log (user_id, table_name, record_id, action)
    VALUES (
        CURRENT_SETTING('app.current_user_id')::uuid,
        'v_contract_accessible',
        NEW.pk_contract,
        'SELECT'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_contract_access_audit
AFTER SELECT ON tenant.v_contract_accessible
FOR EACH ROW EXECUTE FUNCTION audit.log_contract_access();
```

## PostgreSQL RLS Integration

### Enable RLS on Base Table

```yaml
views:
  - name: v_contract_secure
    pattern: security/permission_filter
    config:
      base_entity: Contract
      permission_checks: [...]
      enable_rls: true
```

**Generated RLS Policy**:
```sql
ALTER TABLE tenant.tb_contract ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_contract_access
ON tenant.tb_contract
FOR SELECT
USING (
    pk_contract IN (
        SELECT pk_contract
        FROM tenant.v_contract_accessible
    )
);
```

### RLS vs View-based Security

| Approach | Performance | Flexibility | Maintenance |
|----------|-------------|-------------|-------------|
| **RLS** | Better (direct table access) | Limited | Complex |
| **View** | Good (indexed views) | High | Simple |

## When to Use

✅ **Use when**:
- Multi-tenant data isolation required
- Regulatory compliance needs
- Complex organizational hierarchies
- Role-based access control

❌ **Don't use when**:
- Single-user application
- No sensitive data
- Simple table-level permissions sufficient

## Performance Considerations

- **View Complexity**: Multiple JOINs can impact performance
- **Indexing**: Ensure permission-related fields are indexed
- **Materialized Views**: Consider for frequently accessed filtered data
- **RLS Overhead**: Minimal for simple policies, higher for complex ones

## Security Best Practices

### Defense in Depth
1. **Application Layer**: Initial permission checks
2. **Database Layer**: RLS or view-based filtering
3. **Audit Layer**: Log all access attempts

### Secure User Context
```sql
-- Use secure session variables
SET app.current_user_id = 'user-uuid';  -- Set by application only
SET app.user_roles = 'admin,manager';   -- Comma-separated roles
SET app.org_path = 'org1.dept2.team3';  -- Organizational hierarchy
```

### Permission Testing
```sql
-- Test permission isolation
DO $$
DECLARE
    test_user_id UUID := 'test-user-id';
    visible_count INT;
BEGIN
    -- Set test user
    PERFORM set_config('app.current_user_id', test_user_id::text, false);

    -- Count visible records
    SELECT COUNT(*) INTO visible_count FROM v_contract_accessible;

    -- Assert user can only see their records
    ASSERT visible_count <= 5, 'User should see limited records';

    RAISE NOTICE 'Permission test passed: % records visible', visible_count;
END $$;
```

## Advanced Security Patterns

### Attribute-Based Access Control (ABAC)

```yaml
permission_checks:
  - type: custom
    custom_condition: |
      (c.confidentiality_level <=
       (SELECT clearance_level FROM user_clearance
        WHERE user_id = CURRENT_SETTING('app.current_user_id')::uuid))
```

### Time-Based Permissions

```yaml
permission_checks:
  - type: custom
    custom_condition: |
      (c.access_expires_at IS NULL OR c.access_expires_at > NOW())
      AND EXTRACT(HOUR FROM NOW()) BETWEEN 9 AND 17  -- Business hours only
```

### Geographic Restrictions

```yaml
permission_checks:
  - type: custom
    custom_condition: |
      c.country_code = (SELECT country FROM user_location
                       WHERE user_id = CURRENT_SETTING('app.current_user_id')::uuid)
```

## Related Patterns

- **Data Masking**: Hide sensitive fields based on permissions
- **Audit Trail**: Track who accessed what data
- **Organizational Hierarchy**: Tree-based permission structures