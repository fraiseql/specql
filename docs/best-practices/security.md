# Security Best Practices

Comprehensive guide to implementing secure SpecQL applications, covering authentication, authorization, data protection, and compliance requirements.

## Overview

Security in SpecQL applications involves multiple layers: authentication, authorization, data protection, audit logging, and compliance. This guide covers best practices for each area.

## Authentication & Authorization

### User Authentication

**Use Strong Authentication Patterns:**

```yaml
# Secure user entity with proper authentication fields
entity: User
schema: auth
fields:
  email:
    type: text
    required: true
    unique: true
    description: "User's email address"

  password_hash:
    type: text
    required: true
    description: "BCrypt hash of user password"

  password_salt:
    type: text
    required: true
    description: "Salt used for password hashing"

  email_verified:
    type: boolean
    default: false
    description: "Whether email has been verified"

  failed_login_attempts:
    type: integer
    default: 0
    description: "Number of consecutive failed login attempts"

  locked_until:
    type: timestamptz
    description: "Account lockout timestamp"

  last_login_at:
    type: timestamptz
    description: "Last successful login timestamp"

  mfa_enabled:
    type: boolean
    default: false
    description: "Multi-factor authentication enabled"

  mfa_secret:
    type: text
    description: "TOTP secret for MFA"
```

**Implement Account Security:**

```yaml
actions:
  - name: authenticate_user
    pattern: validation/validation_chain
    config:
      validations:
        - name: check_account_lock
          condition: "locked_until IS NULL OR locked_until < now()"
          message: "Account is temporarily locked due to failed login attempts"

        - name: verify_password
          condition: "crypt(input_data.password, password_hash) = password_hash"
          message: "Invalid email or password"

        - name: check_mfa_if_enabled
          condition: "NOT mfa_enabled OR verify_totp(mfa_secret, input_data.mfa_code)"
          message: "Invalid multi-factor authentication code"

  - name: record_failed_login
    pattern: crud/update
    config:
      set:
        failed_login_attempts: "failed_login_attempts + 1"
        locked_until: "CASE WHEN failed_login_attempts >= 5 THEN now() + interval '15 minutes' ELSE NULL END"

  - name: record_successful_login
    pattern: crud/update
    config:
      set:
        failed_login_attempts: 0
        locked_until: null
        last_login_at: now()
```

### Role-Based Access Control (RBAC)

**Define Roles and Permissions:**

```yaml
entity: Role
schema: auth
fields:
  name:
    type: text
    required: true
    unique: true
    description: "Role name (e.g., admin, user, manager)"

  description:
    type: text
    description: "Role description"

  permissions:
    type: jsonb
    default: "[]"
    description: "Array of permission strings"

entity: UserRole
schema: auth
fields:
  user_id:
    type: ref(User)
    required: true

  role_id:
    type: ref(Role)
    required: true

  granted_at:
    type: timestamptz
    default: now()

  granted_by:
    type: ref(User)
    description: "User who granted this role"

  expires_at:
    type: timestamptz
    description: "Optional role expiration"
```

**Permission Checking:**

```yaml
actions:
  - name: check_permission
    pattern: validation/validation_chain
    config:
      validations:
        - name: has_required_permission
          condition: |
            EXISTS (
              SELECT 1 FROM auth.user_roles ur
              JOIN auth.roles r ON ur.role_id = r.id
              WHERE ur.user_id = caller.id
                AND ur.expires_at IS NULL OR ur.expires_at > now()
                AND r.permissions ? input_data.required_permission
            )
          message: "Insufficient permissions for this action"
```

### Multi-Tenant Isolation

**Implement Tenant Isolation:**

```yaml
entity: Organization
schema: tenant
fields:
  name:
    type: text
    required: true
    description: "Organization name"

  domain:
    type: text
    unique: true
    description: "Organization domain for email validation"

  subscription_tier:
    type: enum[free,pro,enterprise]
    default: free

  settings:
    type: jsonb
    default: "{}"
    description: "Organization-specific settings"

# Add tenant_id to all entities
entity: User
schema: app
fields:
  tenant_id:
    type: ref(Organization)
    required: true
    indexed: true
    description: "Tenant organization"

  # ... other user fields

constraints:
  - name: tenant_isolation
    type: check
    condition: "tenant_id IS NOT NULL"
    error_message: "All records must belong to a tenant"
```

**Tenant-Scoped Queries:**

```yaml
actions:
  - name: get_users
    pattern: crud/read
    requires: "caller.tenant_id = tenant_id"  # Only see users in same tenant
    config:
      filters:
        - condition: "tenant_id = caller.tenant_id"
```

## Data Protection

### Encryption at Rest

**Encrypt Sensitive Fields:**

```yaml
entity: PaymentMethod
schema: billing
fields:
  user_id:
    type: ref(User)
    required: true

  type:
    type: enum[credit_card,bank_account]
    required: true

  # Encrypted fields
  encrypted_data:
    type: text
    required: true
    description: "Encrypted payment details"

  encryption_key_version:
    type: text
    required: true
    description: "Version of encryption key used"

  last_four:
    type: text
    description: "Last 4 digits for display (not encrypted)"

  expiry_month:
    type: integer
    description: "Expiry month (not encrypted)"

  expiry_year:
    type: integer
    description: "Expiry year (not encrypted)"
```

**Encryption Functions:**

```sql
-- Custom encryption functions
CREATE OR REPLACE FUNCTION encrypt_payment_data(plaintext text, key_version text)
RETURNS text AS $$
  -- Use pgcrypto or external KMS for encryption
  SELECT encrypt(plaintext::bytea, key_version::bytea, 'aes')::text;
$$ LANGUAGE sql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_payment_data(ciphertext text, key_version text)
RETURNS text AS $$
  -- Use pgcrypto or external KMS for decryption
  SELECT decrypt(ciphertext::bytea, key_version::bytea, 'aes')::text;
$$ LANGUAGE sql SECURITY DEFINER;
```

### Data Sanitization

**Input Validation and Sanitization:**

```yaml
actions:
  - name: create_post
    pattern: validation/validation_chain
    config:
      validations:
        - name: sanitize_html
          condition: "input_data.content = sanitize_html(input_data.content)"
          message: "Content contains invalid HTML"

        - name: check_sql_injection
          condition: "NOT input_data.content ~* '(;|--|xp_|sp_|exec|union|select|insert|update|delete)'"
          message: "Content contains potentially dangerous SQL patterns"

        - name: validate_urls
          condition: "validate_embedded_urls(input_data.content)"
          message: "Content contains invalid or malicious URLs"
```

### Audit Logging

**Comprehensive Audit Trail:**

```yaml
entity: AuditLog
schema: audit
fields:
  entity_type:
    type: text
    required: true
    description: "Type of entity being audited"

  entity_id:
    type: uuid
    required: true
    description: "ID of the audited entity"

  action:
    type: enum[create,update,delete,read]
    required: true
    description: "Action performed"

  user_id:
    type: ref(User)
    description: "User who performed the action"

  tenant_id:
    type: ref(Organization)
    description: "Tenant context"

  timestamp:
    type: timestamptz
    default: now()
    indexed: true

  ip_address:
    type: text
    description: "Client IP address"

  user_agent:
    type: text
    description: "Client user agent"

  old_values:
    type: jsonb
    description: "Previous values (for updates)"

  new_values:
    type: jsonb
    description: "New values (for creates/updates)"

  metadata:
    type: jsonb
    default: "{}"
    description: "Additional audit metadata"
```

**Automatic Audit Logging:**

```yaml
hooks:
  after_create:
    - name: audit_create
      action: create_audit_log
      config:
        action: create
        new_values: input_data

  after_update:
    - name: audit_update
      action: create_audit_log
      config:
        action: update
        old_values: old_record
        new_values: input_data

  after_delete:
    - name: audit_delete
      action: create_audit_log
      config:
        action: delete
        old_values: old_record
```

## API Security

### Rate Limiting

**Implement Rate Limiting:**

```yaml
entity: RateLimit
schema: security
fields:
  identifier:
    type: text
    required: true
    description: "Rate limit key (IP, user, API key)"

  window_start:
    type: timestamptz
    required: true
    description: "Start of current rate limit window"

  request_count:
    type: integer
    default: 0
    description: "Number of requests in current window"

  limit_type:
    type: enum[ip,user,endpoint,global]
    required: true

  max_requests:
    type: integer
    required: true
    description: "Maximum requests allowed in window"
```

**Rate Limit Checking:**

```yaml
actions:
  - name: check_rate_limit
    pattern: validation/validation_chain
    config:
      validations:
        - name: within_limit
          condition: |
            NOT EXISTS (
              SELECT 1 FROM security.rate_limits
              WHERE identifier = input_data.identifier
                AND window_start > now() - interval '1 hour'
                AND request_count >= max_requests
            )
          message: "Rate limit exceeded. Please try again later."

  - name: record_request
    pattern: crud/update
    config:
      upsert: true
      set:
        request_count: "COALESCE(request_count, 0) + 1"
        window_start: "CASE WHEN window_start < now() - interval '1 hour' THEN date_trunc('hour', now()) ELSE window_start END"
```

### Input Validation

**Comprehensive Input Validation:**

```yaml
actions:
  - name: validate_user_input
    pattern: validation/validation_chain
    config:
      validations:
        - name: email_format
          field: email
          condition: "input_data.email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'"
          message: "Invalid email format"

        - name: password_strength
          field: password
          condition: "length(input_data.password) >= 8 AND input_data.password ~* '[A-Z]' AND input_data.password ~* '[a-z]' AND input_data.password ~* '[0-9]'"
          message: "Password must be at least 8 characters with uppercase, lowercase, and numbers"

        - name: no_script_tags
          field: bio
          condition: "NOT input_data.bio ~* '<script'"
          message: "Script tags are not allowed"

        - name: reasonable_length
          field: name
          condition: "length(input_data.name) BETWEEN 1 AND 100"
          message: "Name must be between 1 and 100 characters"
```

### CORS and CSRF Protection

**API Configuration:**

```yaml
# API security configuration
api:
  cors:
    allowed_origins: ["https://yourapp.com", "https://app.yourapp.com"]
    allowed_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: ["Content-Type", "Authorization", "X-Requested-With"]
    allow_credentials: true
    max_age: 86400

  csrf:
    enabled: true
    token_header: "X-CSRF-Token"
    cookie_name: "csrf_token"
    secure_cookie: true
    http_only: true
```

## Compliance

### GDPR Compliance

**Data Subject Rights:**

```yaml
actions:
  - name: gdpr_data_export
    pattern: crud/read
    requires: "caller.id = user_id OR caller.has_role('admin')"
    config:
      select: "*"  # Export all user data
      format: json
      include_related: true

  - name: gdpr_data_deletion
    pattern: multi_entity/coordinated_update
    requires: "caller.id = user_id OR caller.has_role('admin')"
    config:
      entities:
        - entity: User
          operation: update
          set:
            deleted_at: now()
            email: "deleted@example.com"
            personal_data: null
        - entity: UserSessions
          operation: delete
          where: "user_id = input_data.user_id"
        - entity: AuditLog
          operation: update
          set:
            user_id: null
            anonymized: true
          where: "user_id = input_data.user_id"

  - name: gdpr_consent_log
    pattern: crud/create
    config:
      fields: [user_id, consent_type, consent_given, ip_address, user_agent]
```

### Data Retention

**Automated Data Cleanup:**

```yaml
entity: DataRetentionPolicy
schema: compliance
fields:
  entity_type:
    type: text
    required: true

  retention_period_days:
    type: integer
    required: true

  deletion_action:
    type: enum[anonymize,delete,archive]
    default: delete

  last_cleanup:
    type: timestamptz
    description: "Last time cleanup was run"
```

**Retention Enforcement:**

```sql
-- Automated cleanup function
CREATE OR REPLACE FUNCTION cleanup_expired_data() RETURNS void AS $$
DECLARE
  policy record;
BEGIN
  FOR policy IN SELECT * FROM compliance.data_retention_policies LOOP
    CASE policy.deletion_action
      WHEN 'delete' THEN
        EXECUTE format('DELETE FROM %I.%I WHERE created_at < now() - interval ''%s days''',
                      policy.schema_name, policy.table_name, policy.retention_period_days);
      WHEN 'anonymize' THEN
        EXECUTE format('UPDATE %I.%I SET personal_data = NULL WHERE created_at < now() - interval ''%s days''',
                      policy.schema_name, policy.table_name, policy.retention_period_days);
      WHEN 'archive' THEN
        -- Move to archive table
        EXECUTE format('INSERT INTO archive.%I SELECT * FROM %I.%I WHERE created_at < now() - interval ''%s days''',
                      policy.table_name, policy.schema_name, policy.table_name, policy.retention_period_days);
        EXECUTE format('DELETE FROM %I.%I WHERE created_at < now() - interval ''%s days''',
                      policy.schema_name, policy.table_name, policy.retention_period_days);
    END CASE;
  END LOOP;
END;
$$ LANGUAGE plpgsql;
```

## Security Monitoring

### Security Event Logging

**Security Event Tracking:**

```yaml
entity: SecurityEvent
schema: security
fields:
  event_type:
    type: enum[failed_login,permission_denied,suspicious_activity,security_breach]
    required: true

  severity:
    type: enum[low,medium,high,critical]
    required: true

  user_id:
    type: ref(User)
    description: "User associated with the event"

  ip_address:
    type: text
    required: true

  user_agent:
    type: text

  details:
    type: jsonb
    default: "{}"
    description: "Additional event details"

  timestamp:
    type: timestamptz
    default: now()
    indexed: true
```

### Intrusion Detection

**Suspicious Activity Detection:**

```yaml
actions:
  - name: detect_brute_force
    pattern: validation/validation_chain
    config:
      validations:
        - name: check_failed_attempts
          condition: |
            NOT EXISTS (
              SELECT 1 FROM security.failed_login_attempts
              WHERE ip_address = input_data.ip_address
                AND attempt_time > now() - interval '1 hour'
                AND attempt_count >= 10
            )
          message: "Too many failed attempts from this IP address"

  - name: detect_unusual_activity
    pattern: validation/validation_chain
    config:
      validations:
        - name: check_location_anomaly
          condition: "check_location_consistency(caller.id, input_data.ip_address)"
          message: "Login from unusual location detected"

        - name: check_time_anomaly
          condition: "check_login_time_pattern(caller.id, now())"
          message: "Login at unusual time detected"
```

## Best Practices Summary

### Authentication
- Use strong password hashing (bcrypt, scrypt)
- Implement account lockout after failed attempts
- Require multi-factor authentication for sensitive operations
- Use secure session management with proper expiration

### Authorization
- Implement role-based access control (RBAC)
- Use permission-based authorization
- Apply the principle of least privilege
- Regularly review and audit user permissions

### Data Protection
- Encrypt sensitive data at rest and in transit
- Implement proper input validation and sanitization
- Use parameterized queries to prevent SQL injection
- Implement comprehensive audit logging

### API Security
- Implement rate limiting and throttling
- Use proper CORS configuration
- Implement CSRF protection
- Validate all input data thoroughly

### Compliance
- Implement data retention policies
- Support data export and deletion requests
- Maintain comprehensive audit trails
- Regular security assessments and penetration testing

### Monitoring
- Log all security-relevant events
- Implement intrusion detection
- Set up alerts for suspicious activities
- Regular security monitoring and response

---

**See Also:**
- [Error Codes Reference](../reference/error-codes.md)
- [Entity Design Best Practices](entity-design.md)
- [Performance Best Practices](performance.md)
- [Troubleshooting: Security Issues](../troubleshooting/security-issues.md)