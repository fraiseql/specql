# Error Codes Reference

Complete reference for all error codes used in SpecQL, including validation errors, constraint violations, security issues, and business logic failures.

## Overview

SpecQL uses structured error codes following a `category: subcategory` naming convention. Each error includes a user-friendly message, suggested action, and severity level.

## Error Code Categories

### Validation Errors (`validation:*`)

Errors related to input validation and business rule enforcement.

| Error Code | Description | User Action | Severity |
|------------|-------------|-------------|----------|
| `validation:required_field` | A required field was not provided | Provide a value for the missing field | error |
| `validation:reference_not_found` | Referenced entity does not exist | Verify the referenced record exists and belongs to your organization | error |
| `validation:invalid_enum` | Field value not in allowed enum values | Choose a valid value from the allowed options | error |
| `validation:expression_failed` | Custom validation expression failed | Check your input data and try again | error |
| `validation:duplicate_found` | Duplicate record detected | Use different values or update the existing record | error |
| `validation:invalid_state_transition` | Invalid state machine transition | Check current state and allowed transitions | error |
| `validation:guard_failed` | Business rule guard condition failed | Address the specific business rule requirement | error |
| `validation:record_not_found` | Entity record not found | Verify the record ID and try again | error |
| `validation:dependencies_exist` | Cannot delete due to existing dependencies | Remove dependent records first or use soft delete | error |
| `validation:invalid_amount` | Invalid monetary amount | Provide a valid positive amount | error |
| `validation:invalid_email_format` | Email address format is invalid | Provide a properly formatted email address | error |
| `validation:password_too_short` | Password does not meet minimum length | Use a longer password (minimum 8 characters) | error |
| `validation:username_format_invalid` | Username contains invalid characters | Use only letters, numbers, underscores, and hyphens | error |

### Constraint Errors (`constraint:*`)

Database constraint violations and data integrity issues.

| Error Code | Description | User Action | Severity |
|------------|-------------|-------------|----------|
| `constraint:unique_violation` | Unique constraint violated | Use a different value for the unique field | error |
| `constraint:check_violation` | Check constraint failed | Ensure data meets the required conditions | error |
| `constraint:foreign_key_violation` | Foreign key constraint violated | Ensure referenced records exist | error |
| `constraint:not_null_violation` | NOT NULL constraint violated | Provide a value for the required field | error |

### Security Errors (`security:*`)

Authentication, authorization, and access control issues.

| Error Code | Description | User Action | Severity |
|------------|-------------|-------------|----------|
| `security:permission_denied` | User lacks required permission | Contact your administrator for access | error |
| `security:tenant_isolation` | Attempted cross-tenant access | Contact support if you believe this is an error | critical |
| `security:authentication_required` | User must be authenticated | Log in to perform this action | error |
| `security:token_expired` | Authentication token has expired | Log in again to refresh your session | error |
| `security:insufficient_scope` | Token lacks required scope | Request a token with appropriate permissions | error |

### Business Logic Errors (`business:*`)

Application-specific business rule violations.

| Error Code | Description | User Action | Severity |
|------------|-------------|-------------|----------|
| `business:insufficient_funds` | Account has insufficient funds | Add funds to your account or reduce the amount | error |
| `business:insufficient_inventory` | Product is out of stock | Choose a different product or wait for restock | error |
| `business:order_already_processed` | Order has already been processed | Check order status or contact support | error |
| `business:invalid_order_state` | Operation not allowed in current order state | Check order status and available actions | error |
| `business:contract_already_exists` | Contract with same details exists | Review existing contracts or modify details | error |
| `business:budget_exceeded` | Transaction exceeds budget limit | Reduce amount or request budget increase | error |
| `business:approval_required` | Transaction requires approval | Submit for approval or contact approver | warning |

### System Errors (`system:*`)

Infrastructure and system-level issues.

| Error Code | Description | User Action | Severity |
|------------|-------------|-------------|----------|
| `system:database_unavailable` | Database connection failed | Try again later or contact support | critical |
| `system:external_service_unavailable` | External service is down | Try again later or contact support | warning |
| `system:rate_limit_exceeded` | Too many requests in time window | Wait before making more requests | warning |
| `system:maintenance_mode` | System is in maintenance mode | Try again later | info |
| `system:feature_disabled` | Requested feature is disabled | Contact support to enable the feature | info |

### Batch Operation Errors (`batch:*`)

Errors specific to bulk operations and data processing.

| Error Code | Description | User Action | Severity |
|------------|-------------|-------------|----------|
| `batch:partial_failure` | Some items in batch failed | Check individual item errors and retry failed items | warning |
| `batch:validation_failed` | Batch validation failed | Fix validation errors and resubmit | error |
| `batch:size_limit_exceeded` | Batch size exceeds limit | Reduce batch size and try again | error |
| `batch:timeout` | Batch operation timed out | Reduce batch size or contact support | error |
| `batch:concurrency_limit` | Too many concurrent batches | Wait for other batches to complete | warning |

### Integration Errors (`integration:*`)

Errors from external service integrations.

| Error Code | Description | User Action | Severity |
|------------|-------------|-------------|----------|
| `integration:payment_failed` | Payment processing failed | Check payment details and try again | error |
| `integration:shipping_unavailable` | Shipping service unavailable | Try again later or choose different shipping | warning |
| `integration:email_delivery_failed` | Email delivery failed | Check email address or try again | warning |
| `integration:api_rate_limited` | External API rate limit exceeded | Wait before retrying | warning |
| `integration:webhook_failed` | Webhook delivery failed | Check webhook configuration | warning |

## Error Response Format

All SpecQL errors follow a consistent JSON structure:

```json
{
  "status": "error",
  "code": "validation:required_field",
  "message": "Email is required",
  "user_action": "Provide a value for email",
  "severity": "error",
  "context": {
    "field": "email",
    "entity": "User",
    "operation": "create_user"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-12345"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always "error" for error responses |
| `code` | string | Structured error code (category:subcategory) |
| `message` | string | Human-readable error message |
| `user_action` | string | Suggested action to resolve the error |
| `severity` | enum | Error severity: `info`, `warning`, `error`, `critical` |
| `context` | object | Additional context about the error |
| `timestamp` | string | ISO 8601 timestamp when error occurred |
| `request_id` | string | Unique request identifier for tracing |

## Error Handling Patterns

### Client-Side Error Handling

```javascript
// JavaScript/TypeScript error handling
try {
  const result = await api.createUser(userData);
  // Success handling
} catch (error) {
  switch (error.code) {
    case 'validation:required_field':
      showFieldError(error.context.field, error.message);
      break;
    case 'validation:duplicate_found':
      showDuplicateError(error.context.field);
      break;
    case 'security:permission_denied':
      showPermissionError();
      break;
    default:
      showGenericError(error.message);
  }
}
```

### Server-Side Error Handling

```python
# Python error handling
def handle_api_error(error):
    if error['code'].startswith('validation:'):
        return jsonify({
            'field': error['context'].get('field'),
            'message': error['message'],
            'action': error['user_action']
        }), 400

    elif error['code'].startswith('security:'):
        return jsonify({
            'message': 'Authentication or authorization error',
            'action': 'Please log in or contact support'
        }), 403

    else:
        # Log unexpected errors
        logger.error(f"Unexpected error: {error}")
        return jsonify({
            'message': 'An unexpected error occurred',
            'action': 'Please try again or contact support'
        }), 500
```

### Batch Operation Error Handling

```python
# Handling partial batch failures
def process_batch_results(results):
    successful = []
    failed = []

    for item in results:
        if item['status'] == 'success':
            successful.append(item)
        else:
            failed.append({
                'item': item,
                'error': item['error'],
                'retryable': is_retryable_error(item['error']['code'])
            })

    return {
        'successful_count': len(successful),
        'failed_count': len(failed),
        'failed_items': failed,
        'can_retry': any(item['retryable'] for item in failed)
    }
```

## Common Error Scenarios

### User Registration

```json
// Missing required field
{
  "status": "error",
  "code": "validation:required_field",
  "message": "Email is required",
  "user_action": "Provide a value for email",
  "severity": "error",
  "context": {"field": "email", "entity": "User"}
}

// Duplicate email
{
  "status": "error",
  "code": "validation:duplicate_found",
  "message": "A User with this email already exists",
  "user_action": "Use a different email or update the existing record",
  "severity": "error",
  "context": {"field": "email", "entity": "User"}
}
```

### Order Processing

```json
// Insufficient inventory
{
  "status": "error",
  "code": "business:insufficient_inventory",
  "message": "Product Wireless Headphones is out of stock",
  "user_action": "Choose a different product or wait for restock",
  "severity": "error",
  "context": {"product_id": "prod-123", "available": 0, "requested": 2}
}

// Invalid state transition
{
  "status": "error",
  "code": "validation:invalid_state_transition",
  "message": "Cannot ship order in 'pending' status",
  "user_action": "Order must be confirmed before shipping",
  "severity": "error",
  "context": {"current_state": "pending", "target_state": "shipped", "order_id": "ord-456"}
}
```

### Permission Errors

```json
// Insufficient permissions
{
  "status": "error",
  "code": "security:permission_denied",
  "message": "You don't have permission to create contracts",
  "user_action": "Contact your administrator for access",
  "severity": "error",
  "context": {"action": "create_contract", "user_role": "user"}
}

// Cross-tenant access
{
  "status": "error",
  "code": "security:tenant_isolation",
  "message": "Cannot access Contract from another organization",
  "user_action": "Contact support if you believe this is an error",
  "severity": "critical",
  "context": {"entity": "Contract", "requested_tenant": "tenant-2", "user_tenant": "tenant-1"}
}
```

## Error Monitoring and Alerting

### Log Aggregation

```sql
-- Query error patterns
SELECT
    code,
    COUNT(*) as error_count,
    COUNT(DISTINCT request_id) as affected_requests,
    MAX(timestamp) as last_occurrence
FROM error_logs
WHERE timestamp > now() - interval '24 hours'
GROUP BY code
ORDER BY error_count DESC;

-- User impact analysis
SELECT
    user_id,
    COUNT(*) as errors_per_user,
    array_agg(DISTINCT code) as error_types
FROM error_logs
WHERE severity = 'error'
  AND timestamp > now() - interval '7 days'
GROUP BY user_id
HAVING COUNT(*) > 5
ORDER BY errors_per_user DESC;
```

### Alert Configuration

```yaml
# Prometheus alerting rules
groups:
  - name: specql_errors
    rules:
      - alert: HighErrorRate
        expr: rate(error_total{code=~"validation:*"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High validation error rate detected"

      - alert: CriticalErrors
        expr: rate(error_total{severity="critical"}[1m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical error occurred"

      - alert: PermissionErrors
        expr: rate(error_total{code="security:permission_denied"}[10m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High permission denial rate"
```

## Best Practices

### Error Prevention
- Validate input data client-side before API calls
- Use enum types to prevent invalid values
- Implement proper foreign key relationships
- Add database constraints for data integrity

### Error Communication
- Use user-friendly error messages
- Provide actionable guidance in error responses
- Include relevant context without exposing sensitive data
- Use consistent error codes across the application

### Error Monitoring
- Log all errors with sufficient context
- Set up alerts for error rate thresholds
- Monitor error patterns for systemic issues
- Track error resolution times

### Error Recovery
- Implement retry logic for transient errors
- Provide fallback options for failed operations
- Allow users to recover from validation errors
- Implement circuit breakers for external service failures

---

**See Also:**
- [Pattern Library API](pattern-library-api.md)
- [YAML Schema Reference](yaml-schema.md)
- [Troubleshooting Guide](../troubleshooting/)
- [Security Best Practices](../best-practices/security.md)