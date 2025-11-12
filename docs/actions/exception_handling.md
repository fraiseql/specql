# exception_handling - Try/Catch Exception Handling

Handle runtime errors and exceptions with try/catch/finally blocks.

## Syntax

```yaml
- exception_handling:
    try:
      - step1
      - step2
    catch:
      - when: 'exception_type'
        then:
          - error_handling_step1
          - error_handling_step2
      - when: 'another_exception'
        then:
          - different_handling
    finally:
      - cleanup_step1
      - cleanup_step2
```

## Parameters

- `try`: Steps to execute that might raise exceptions
- `catch`: Array of exception handlers with conditions and responses
- `finally`: Steps to execute regardless of whether an exception occurred

## Exception Types

Common exception types that map to PostgreSQL:

- `payment_failed` → `RAISE_EXCEPTION`
- `network_error` → `CONNECTION_EXCEPTION`
- `database_error` → `INTEGRITY_CONSTRAINT_VIOLATION`
- `parse_error` → `INVALID_TEXT_REPRESENTATION`
- `validation_error` → `CHECK_VIOLATION`
- `OTHERS` → Catch any unhandled exceptions

## Examples

### Basic Error Handling

```yaml
entity: Transaction
actions:
  - name: process_payment
    steps:
      - exception_handling:
          try:
            - call_service:
                service: payment_gateway
                operation: charge
                input: {amount: $amount, card: $card_token}
            - update: Transaction SET status = 'completed'
          catch:
            - when: 'payment_failed'
              then:
                - update: Transaction SET status = 'failed'
                - reject: "Payment processing failed"
            - when: 'network_error'
              then:
                - update: Transaction SET status = 'retry'
                - call_function: schedule_retry
          finally:
            - call_function: cleanup_resources
```

### Multiple Exception Handlers

```yaml
entity: FileProcessor
actions:
  - name: import_data
    steps:
      - exception_handling:
          try:
            - call_function:
                function: parse_file
            - call_function: validate_data
            - call_function: save_records
          catch:
            - when: 'parse_error'
              then:
                - call_function:
                    function: log_error
                - reject: invalid_format
            - when: 'validation_error'
              then:
                - call_function:
                    function: log_error
                - reject: invalid_data
            - when: 'database_error'
              then:
                - call_function:
                    function: log_error
                - call_function:
                    function: rollback_transaction
            - when: 'OTHERS'
              then:
                - call_function:
                    function: log_error
                - reject: system_error
```

## Notes

- Exception handlers are checked in order
- `OTHERS` should be last to catch any unhandled exceptions
- The `finally` block executes regardless of exceptions
- Variables declared in try/catch are accessible in finally
- Use `reject` to return error responses from catch blocks