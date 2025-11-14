# Security Best Practices

This guide covers the security features and best practices for actions in the PrintOptim backend.

## Multi-Tenant Isolation

All data access is automatically isolated by tenant:

```sql
-- Generated functions automatically include tenant filtering
SELECT * FROM crm.tb_contact
WHERE tenant_id = auth_tenant_id  -- Automatic
  AND id = input_data.contact_id
```

### Trinity Pattern Security

The Trinity pattern ensures secure data access:

- **UUID external IDs**: Public-facing identifiers
- **INTEGER internal PKs**: Database-optimized foreign keys
- **Tenant isolation**: All queries filtered by `tenant_id`

## SQL Injection Protection

### Automatic Protection

All generated SQL uses parameterized queries:

```sql
-- ✅ Safe: Parameters are escaped
EXECUTE format('SELECT * FROM %I WHERE id = $1', table_name) USING entity_id;
```

### Input Validation

- **Type coercion**: All inputs validated against schemas
- **Enum validation**: Only allowed values accepted
- **Pattern matching**: Email, phone, URL formats enforced

## Audit Logging

Every mutation is automatically logged:

```sql
-- All changes recorded in app.tb_mutation_audit_log
INSERT INTO app.tb_mutation_audit_log (
    tenant_id, user_id, entity_type, entity_id,
    operation, status, updated_fields, message,
    object_data, extra_metadata, error_context
) VALUES (
    auth_tenant_id, auth_user_id, 'contact', contact_id,
    'UPDATE', 'success', ARRAY['status'], 'Contact updated',
    row_to_json(updated_contact), NULL, NULL
);
```

### Audit Trail Features

- **Complete history**: All changes tracked
- **User attribution**: Who made each change
- **Timestamp tracking**: When changes occurred
- **Failure logging**: Failed operations recorded
- **Data snapshots**: Before/after state preserved

## Authentication & Authorization

### JWT Context

All functions receive authenticated context:

```sql
CREATE FUNCTION crm.create_contact(
    auth_tenant_id UUID,  -- From JWT
    auth_user_id UUID,    -- From JWT
    input_data app.type_create_contact_input,
    input_payload JSONB
) RETURNS app.mutation_result
```

### Permission Checks

- **Tenant membership**: Users can only access their organization's data
- **Entity ownership**: References validated for tenant ownership
- **Field-level security**: Sensitive fields protected

## Input Sanitization

### Composite Types

Type-safe input using PostgreSQL composite types:

```sql
-- Generated composite type
CREATE TYPE app.type_create_contact_input AS (
    email TEXT,
    status TEXT,
    company_id UUID
);

-- Function signature enforces structure
CREATE FUNCTION crm.create_contact(
    input_data app.type_create_contact_input  -- Type-safe
) RETURNS app.mutation_result
```

### JSONB Validation

Additional validation on JSONB payloads:

- **Schema validation**: Structure enforced
- **Type checking**: Data types validated
- **Required fields**: Mandatory fields checked

## Error Handling

### Structured Error Responses

Errors return actionable information:

```json
{
  "id": null,
  "updated_fields": ["email"],
  "status": "failed:validation",
  "message": "Email is required",
  "object_data": null,
  "extra_metadata": {
    "code": "validation:required_field",
    "user_action": "Provide a value for email",
    "field": "email",
    "entity": "Contact"
  }
}
```

### Error Codes

Standardized error codes for client handling:

- `validation:*` - Input validation failures
- `constraint:*` - Database constraint violations
- `security:*` - Permission/security issues
- `reference:*` - Foreign key/reference errors

## Performance Security

### Query Optimization

Generated queries are optimized:

- **Indexes**: Automatic index creation
- **Trinity resolution**: Efficient FK lookups
- **Pagination**: Built-in result limiting
- **Timeout protection**: Query timeouts enforced

### Resource Limits

- **Connection pooling**: Database connections managed
- **Query limits**: Result set size restrictions
- **Execution timeouts**: Long-running query prevention

## Best Practices

### Writing Secure Actions

1. **Validate inputs early**:
   ```yaml
   actions:
     - name: create_contact
       steps:
         - validate: email IS NOT NULL, error: missing_email
         - validate: email MATCHES email_pattern, error: invalid_email
   ```

2. **Use references for relationships**:
   ```yaml
   fields:
     company: ref(Company)  # Enforces tenant isolation
   ```

3. **Handle sensitive data appropriately**:
   ```yaml
   # Audit logging captures all changes automatically
   - update: Contact SET status = 'qualified'  # Logged
   ```

### Monitoring & Alerting

- **Failed authentication attempts**: Logged and monitored
- **Unusual query patterns**: Detected and alerted
- **Audit log analysis**: Security event detection
- **Performance anomalies**: Slow query alerting

## Compliance

### Data Protection

- **GDPR compliance**: Right to erasure, data portability
- **Audit trails**: Complete change history
- **Data retention**: Configurable retention policies
- **Access logging**: All data access tracked

### Industry Standards

- **SOC 2**: Security controls and monitoring
- **ISO 27001**: Information security management
- **PCI DSS**: Payment data protection (when applicable)

## Implementation Details

### Security Headers

All API responses include security headers:

- `X-Tenant-ID`: Confirms tenant isolation
- `X-Request-ID`: Request tracing
- `X-Content-Type-Options: nosniff`

### Encryption

- **Data at rest**: Encrypted storage
- **Data in transit**: TLS 1.3 required
- **Secrets management**: Secure key storage

### Network Security

- **VPC isolation**: Database in private network
- **Firewall rules**: Minimal required access
- **DDoS protection**: Rate limiting and filtering

## Troubleshooting

### Common Security Issues

1. **Tenant data leakage**:
   - Check tenant_id filters in queries
   - Verify FK resolution includes tenant context

2. **SQL injection attempts**:
   - All queries use parameterized statements
   - Input validation prevents malicious data

3. **Unauthorized access**:
   - JWT validation required for all requests
   - Tenant membership verified

4. **Audit gaps**:
   - All mutations automatically logged
   - Custom actions include manual audit calls

## Contact

For security concerns or questions:
- **Security Team**: security@printoptim.com
- **DevOps**: devops@printoptim.com
- **CTO**: cto@printoptim.com