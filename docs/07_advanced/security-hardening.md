# Security Hardening Guide

> **Production-grade security for SpecQL applications—defense in depth**

## Overview

SpecQL generates secure code by default, but production deployments require additional hardening:

- ✅ **Multi-Tenancy Isolation** - Row-Level Security (RLS)
- ✅ **SQL Injection Prevention** - Parameterized queries
- ✅ **Authentication & Authorization** - JWT + RBAC
- ✅ **Input Validation** - Rich types + constraints
- ✅ **Audit Logging** - Complete change tracking
- ✅ **Encryption** - At-rest and in-transit

**Security layers**: Database → Application → API → Frontend

---

## Quick Security Checklist

### Essential (Required for Production)

- [ ] Enable Row-Level Security (RLS) on all multi-tenant tables
- [ ] Configure SSL/TLS for database connections
- [ ] Use prepared statements (SpecQL default)
- [ ] Validate all inputs with rich types
- [ ] Enable audit logging
- [ ] Set up backup encryption
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets

### Recommended

- [ ] Implement API rate limiting
- [ ] Enable two-factor authentication (2FA)
- [ ] Set up intrusion detection
- [ ] Configure automated security scanning
- [ ] Implement least-privilege access
- [ ] Enable query logging
- [ ] Set up security monitoring

---

## Multi-Tenancy Security

### Row-Level Security (RLS)

**SpecQL auto-generates RLS policies** for multi-tenant schemas:

```yaml
# Domain registry
schemas:
  crm:
    tier: multi_tenant  # Auto-enables RLS
```

**Generated Security**:
```sql
-- Auto-added tenant_id column
CREATE TABLE crm.tb_contact (
    pk_contact INTEGER PRIMARY KEY,
    tenant_id UUID NOT NULL,  -- Automatic
    ...
);

-- Enable RLS
ALTER TABLE crm.tb_contact ENABLE ROW LEVEL SECURITY;

-- Isolation policy: Users only see their tenant's data
CREATE POLICY tenant_isolation ON crm.tb_contact
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Insert policy: New rows must use current tenant
CREATE POLICY tenant_insert ON crm.tb_contact
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Update policy: Can only update own tenant's data
CREATE POLICY tenant_update ON crm.tb_contact
    FOR UPDATE
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Delete policy: Can only delete own tenant's data
CREATE POLICY tenant_delete ON crm.tb_contact
    FOR DELETE
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

---

### Setting Tenant Context

**Before executing queries**, set tenant context:

```sql
-- Set tenant for session
SET app.current_tenant_id = '550e8400-e29b-41d4-a716-446655440000';

-- Now all queries are automatically filtered
SELECT * FROM crm.tb_contact;  -- Only returns current tenant's contacts
```

**Application code**:
```python
def execute_with_tenant(tenant_id: str, query: str):
    """Execute query with tenant context"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Set tenant context
    cursor.execute("SET app.current_tenant_id = %s", (tenant_id,))

    # Execute query (RLS auto-filters)
    cursor.execute(query)

    return cursor.fetchall()
```

---

### Superuser Bypass

**IMPORTANT**: Superusers bypass RLS policies!

```sql
-- ❌ BAD: Application uses superuser (bypasses RLS)
DATABASE_URL=postgresql://postgres:password@localhost/myapp

-- ✅ GOOD: Application uses restricted user
DATABASE_URL=postgresql://app_user:password@localhost/myapp
```

**Create restricted user**:
```sql
-- Create application user (not superuser)
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';

-- Grant minimal permissions
GRANT CONNECT ON DATABASE myapp TO app_user;
GRANT USAGE ON SCHEMA crm TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA crm TO app_user;

-- RLS policies will apply to app_user
```

---

## SQL Injection Prevention

### Parameterized Queries (Default)

**SpecQL auto-generates parameterized queries**—SQL injection impossible:

```sql
-- ✅ Generated code uses parameters
CREATE FUNCTION app.qualify_lead(p_contact_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
    v_contact crm.tb_contact%ROWTYPE;
BEGIN
    -- Safe: Uses parameter, not string concatenation
    SELECT * INTO v_contact
    FROM crm.tb_contact
    WHERE id = p_contact_id;  -- ← Parameter binding
    ...
END;
$$ LANGUAGE plpgsql;
```

---

### Expression Safety

**SpecQL expressions are compiled safely**:

```yaml
actions:
  - name: search_contacts
    params:
      search_term: text!
    steps:
      # ✅ Safe: SpecQL compiles to parameterized query
      - query: Contact WHERE email LIKE '%' || $search_term || '%'
        result: $contacts
```

**Generated SQL**:
```sql
-- Safe parameterized query
SELECT * FROM crm.tb_contact
WHERE email LIKE '%' || $1 || '%';  -- $1 is parameter
```

---

### Dangerous Patterns to Avoid

**Never use dynamic SQL** in custom functions:

```sql
-- ❌ VULNERABLE: String concatenation (SQL injection risk)
CREATE FUNCTION unsafe_search(p_email TEXT)
RETURNS SETOF crm.tb_contact AS $$
BEGIN
    RETURN QUERY EXECUTE 'SELECT * FROM crm.tb_contact WHERE email = ''' || p_email || '''';
    -- SQL injection possible!
END;
$$ LANGUAGE plpgsql;

-- ✅ SAFE: Use parameters
CREATE FUNCTION safe_search(p_email TEXT)
RETURNS SETOF crm.tb_contact AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM crm.tb_contact WHERE email = p_email;
    -- Parameters prevent injection
END;
$$ LANGUAGE plpgsql;
```

---

## Input Validation

### Rich Types (First Line of Defense)

**SpecQL rich types enforce validation** at the database level:

```yaml
entity: Contact
fields:
  email: email!           # Must be valid email
  phone: phoneNumber      # Must be E.164 format
  website: url            # Must be valid URL
  age: integer(18, 120)!  # Must be 18-120
```

**Generated constraints**:
```sql
CREATE TABLE crm.tb_contact (
    email TEXT NOT NULL
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),

    phone TEXT
        CHECK (phone ~ '^\+[1-9]\d{1,14}$'),

    website TEXT
        CHECK (website ~ '^https?://[^\s/$.?#].[^\s]*$'),

    age INTEGER NOT NULL
        CHECK (age >= 18 AND age <= 120)
);
```

**Attempts to insert invalid data fail**:
```sql
-- ❌ Invalid email
INSERT INTO crm.tb_contact (email, ...)
VALUES ('not-an-email', ...);
-- ERROR: violates check constraint "chk_contact_email"

-- ❌ Invalid age
INSERT INTO crm.tb_contact (email, age, ...)
VALUES ('user@example.com', 15, ...);
-- ERROR: violates check constraint "chk_contact_age"
```

---

### Custom Validation

**Add business logic validation**:

```yaml
actions:
  - name: create_order
    params:
      customer_id: uuid!
      items: list(OrderItemInput)!
      total_amount: money!
    steps:
      # Validate customer exists
      - validate: exists(Customer WHERE id = $customer_id)
        error: "customer_not_found"

      # Validate items not empty
      - validate: array_length($items, 1) > 0
        error: "order_must_have_items"

      # Validate total matches item sum
      - validate: $total_amount = sum($items.unit_price * $items.quantity)
        error: "total_amount_mismatch"

      # Create order
      - insert: Order VALUES (...)
```

---

## Authentication & Authorization

### JWT Authentication

**Validate JWT tokens in database**:

```sql
-- Create JWT validation function
CREATE FUNCTION core.verify_jwt(p_token TEXT)
RETURNS TABLE(user_id UUID, tenant_id UUID, roles TEXT[]) AS $$
DECLARE
    v_payload JSONB;
BEGIN
    -- Verify JWT signature (using pg_jwt extension or external service)
    v_payload := verify_jwt_signature(p_token, 'your-secret-key');

    -- Extract claims
    RETURN QUERY
    SELECT
        (v_payload->>'user_id')::UUID,
        (v_payload->>'tenant_id')::UUID,
        ARRAY(SELECT jsonb_array_elements_text(v_payload->'roles'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Set context from JWT**:
```sql
-- Set user/tenant context
CREATE FUNCTION core.set_context_from_jwt(p_token TEXT)
RETURNS VOID AS $$
DECLARE
    v_user_id UUID;
    v_tenant_id UUID;
    v_roles TEXT[];
BEGIN
    SELECT user_id, tenant_id, roles
    INTO v_user_id, v_tenant_id, v_roles
    FROM core.verify_jwt(p_token);

    -- Set session variables
    PERFORM set_config('app.current_user_id', v_user_id::TEXT, TRUE);
    PERFORM set_config('app.current_tenant_id', v_tenant_id::TEXT, TRUE);
    PERFORM set_config('app.current_roles', array_to_string(v_roles, ','), TRUE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

### Role-Based Access Control (RBAC)

**Define roles and permissions**:

```yaml
entity: User
fields:
  email: email!
  roles: list(enum(admin, manager, user))!

actions:
  - name: delete_contact
    requires_role: [admin]  # Only admins can delete
    steps:
      - delete: Contact WHERE id = $contact_id
```

**Generated permission check**:
```sql
CREATE FUNCTION app.delete_contact(p_contact_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
    v_user_roles TEXT;
BEGIN
    -- Check user has required role
    v_user_roles := current_setting('app.current_roles', TRUE);

    IF NOT ('admin' = ANY(string_to_array(v_user_roles, ','))) THEN
        RAISE EXCEPTION
            SQLSTATE '42501'
            USING MESSAGE = 'insufficient_permissions';
    END IF;

    -- Proceed with deletion
    ...
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## Audit Logging

### Automatic Audit Trail

**SpecQL audit_trail pattern** tracks all changes:

```yaml
entity: Contact
patterns:
  - audit_trail  # Adds created_at, updated_at, created_by, updated_by

fields:
  email: email!
```

**Generated audit fields**:
```sql
CREATE TABLE crm.tb_contact (
    ...,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- Auto-update trigger
CREATE TRIGGER trg_tb_contact_audit
    BEFORE UPDATE ON crm.tb_contact
    FOR EACH ROW
    EXECUTE FUNCTION core.update_audit_fields();
```

---

### Change History Tracking

**Use versioning pattern for complete history**:

```yaml
entity: Order
patterns:
  - audit_trail
  - versioning  # Creates history table

fields:
  total_amount: money!
  status: enum(pending, shipped, delivered)!
```

**Generated history table**:
```sql
CREATE TABLE sales.tb_order_history (
    history_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    pk_order INTEGER NOT NULL,
    version INTEGER NOT NULL,
    snapshot JSONB NOT NULL,  -- Complete row state
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by UUID,
    change_type TEXT,  -- 'insert', 'update', 'delete'

    CONSTRAINT fk_order_history
        FOREIGN KEY (pk_order)
        REFERENCES sales.tb_order(pk_order)
);
```

**Query change history**:
```sql
-- Get all changes to an order
SELECT
    version,
    snapshot->>'total_amount' as total_amount,
    snapshot->>'status' as status,
    changed_at,
    changed_by
FROM sales.tb_order_history
WHERE pk_order = order_pk('550e8400-...')
ORDER BY version DESC;
```

---

### Security Event Logging

**Log security-sensitive operations**:

```sql
CREATE TABLE core.security_events (
    event_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    event_type TEXT NOT NULL,  -- 'login', 'logout', 'permission_denied', etc.
    user_id UUID,
    tenant_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    occurred_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_security_events_user ON core.security_events(user_id);
CREATE INDEX idx_security_events_type ON core.security_events(event_type);
CREATE INDEX idx_security_events_time ON core.security_events(occurred_at);
```

**Log events in actions**:
```sql
-- Log failed login attempt
INSERT INTO core.security_events (event_type, details, ip_address)
VALUES (
    'login_failed',
    json_build_object('email', p_email, 'reason', 'invalid_password'),
    inet_client_addr()
);
```

---

## Encryption

### At-Rest Encryption

**Enable PostgreSQL encryption**:

```bash
# postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'

# Require SSL for connections
hostssl  all  all  0.0.0.0/0  md5
```

**Encrypt sensitive columns** (using pgcrypto):

```sql
CREATE EXTENSION pgcrypto;

-- Encrypt sensitive data
CREATE TABLE crm.tb_contact (
    ...,
    ssn_encrypted BYTEA,  -- Encrypted SSN
    credit_card_encrypted BYTEA  -- Encrypted credit card
);

-- Encrypt on insert
INSERT INTO crm.tb_contact (email, ssn_encrypted)
VALUES (
    'user@example.com',
    pgp_sym_encrypt('123-45-6789', current_setting('app.encryption_key'))
);

-- Decrypt on select
SELECT
    email,
    pgp_sym_decrypt(ssn_encrypted, current_setting('app.encryption_key')) as ssn
FROM crm.tb_contact;
```

---

### In-Transit Encryption

**Enforce TLS/SSL connections**:

```python
# Application connection string
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"

# Verify server certificate
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=verify-full&sslrootcert=/path/to/ca.crt"
```

---

## API Security

### Rate Limiting

**Implement at application or API gateway level**:

```yaml
# Rate limiting pattern (per user)
entity: ApiKey
patterns:
  - rate_limiting:
      max_requests: 1000
      window_minutes: 60

fields:
  key: apiKey!
  user: ref(User)!
```

**Check rate limit before action**:
```sql
CREATE FUNCTION app.check_rate_limit(p_api_key TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    v_key crm.tb_api_key%ROWTYPE;
BEGIN
    SELECT * INTO v_key
    FROM crm.tb_api_key
    WHERE key = p_api_key;

    -- Check if within rate limit
    IF v_key.request_count >= 1000 AND
       v_key.window_start > NOW() - INTERVAL '60 minutes' THEN
        RETURN FALSE;  -- Rate limit exceeded
    END IF;

    -- Update counters
    UPDATE crm.tb_api_key
    SET
        request_count = CASE
            WHEN window_start < NOW() - INTERVAL '60 minutes'
            THEN 1
            ELSE request_count + 1
        END,
        window_start = CASE
            WHEN window_start < NOW() - INTERVAL '60 minutes'
            THEN NOW()
            ELSE window_start
        END
    WHERE pk_api_key = v_key.pk_api_key;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

---

### CORS Configuration

**GraphQL server CORS settings**:

```javascript
// server.js
const corsOptions = {
  origin: [
    'https://yourdomain.com',
    'https://app.yourdomain.com'
  ],
  credentials: true,
  maxAge: 86400  // 24 hours
};

app.use(cors(corsOptions));
```

---

## Database Security

### Firewall Rules

**Restrict database access**:

```sql
-- postgresql.conf: pg_hba.conf
# TYPE  DATABASE  USER       ADDRESS         METHOD

# Allow localhost
host    all       all        127.0.0.1/32    md5

# Allow application servers only
host    all       app_user   10.0.1.0/24     md5

# Deny all other connections
host    all       all        0.0.0.0/0       reject
```

---

### Least Privilege

**Grant minimal permissions**:

```sql
-- Read-only role for analytics
CREATE ROLE analytics_user WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE myapp TO analytics_user;
GRANT USAGE ON SCHEMA crm TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA crm TO analytics_user;

-- Read-write role for application
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE myapp TO app_user;
GRANT USAGE ON SCHEMA crm TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA crm TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA crm TO app_user;

-- No superuser access for application
```

---

### Secrets Management

**Never hardcode secrets**:

```yaml
# ❌ BAD: Secrets in code
database:
  host: localhost
  password: "my_password_123"

# ✅ GOOD: Environment variables
database:
  host: ${DATABASE_HOST}
  password: ${DATABASE_PASSWORD}
```

**Use secret management tools**:
- **HashiCorp Vault** - Enterprise secret management
- **AWS Secrets Manager** - AWS-native
- **Azure Key Vault** - Azure-native
- **Google Secret Manager** - GCP-native

---

## Security Monitoring

### Enable Query Logging

```sql
-- postgresql.conf
log_statement = 'all'
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

---

### Intrusion Detection

**Monitor for suspicious patterns**:

```sql
-- Alert on multiple failed login attempts
CREATE VIEW core.failed_logins AS
SELECT
    details->>'email' as email,
    COUNT(*) as attempt_count,
    MAX(occurred_at) as last_attempt
FROM core.security_events
WHERE event_type = 'login_failed'
  AND occurred_at > NOW() - INTERVAL '1 hour'
GROUP BY details->>'email'
HAVING COUNT(*) >= 5;
```

---

## Best Practices Summary

### ✅ DO

1. **Enable RLS** on all multi-tenant tables
2. **Use prepared statements** (SpecQL default)
3. **Validate inputs** with rich types
4. **Encrypt sensitive data** (at-rest and in-transit)
5. **Audit all changes** (audit_trail pattern)
6. **Use least privilege** for database users
7. **Implement rate limiting** on APIs
8. **Monitor security events** continuously
9. **Rotate secrets** regularly
10. **Keep PostgreSQL updated**

---

### ❌ DON'T

1. **Don't use superuser** for application
2. **Don't hardcode secrets** in code
3. **Don't skip input validation**
4. **Don't disable SSL/TLS**
5. **Don't expose database** to public internet
6. **Don't ignore security logs**
7. **Don't use weak passwords**
8. **Don't trust client input**

---

## Security Checklist for Production

### Pre-Deployment

- [ ] RLS enabled on all multi-tenant tables
- [ ] SSL/TLS configured for database
- [ ] Application uses non-superuser role
- [ ] All secrets in environment variables
- [ ] Input validation on all fields
- [ ] Audit logging enabled
- [ ] Firewall rules configured
- [ ] Rate limiting implemented
- [ ] CORS properly configured
- [ ] Security monitoring set up

### Post-Deployment

- [ ] Regular security audits
- [ ] Penetration testing performed
- [ ] Backup encryption verified
- [ ] Access logs reviewed
- [ ] Incident response plan documented
- [ ] Security patches applied
- [ ] Password rotation scheduled

---

## Next Steps

### Learn More

- **[Monitoring Guide](monitoring.md)** - Security event monitoring
- **[Deployment Guide](deployment.md)** - Secure deployment
- **[Testing Guide](testing.md)** - Security testing

### Tools

- **pg_audit** - PostgreSQL audit logging
- **pgcrypto** - Encryption extension
- **PostgREST** - Secure REST API
- **OWASP ZAP** - Security scanner

---

## Summary

You've learned:
- ✅ Multi-tenancy isolation with RLS
- ✅ SQL injection prevention
- ✅ Input validation strategies
- ✅ Authentication and authorization
- ✅ Audit logging patterns
- ✅ Encryption at-rest and in-transit
- ✅ API and database security

**Key Takeaway**: Defense in depth—layer security at database, application, API, and frontend levels.

**Next**: Monitor your secure application with [Monitoring Guide](monitoring.md) →

---

**Security is not optional—harden every layer.**
