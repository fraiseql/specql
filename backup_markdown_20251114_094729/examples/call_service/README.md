# Call Service Examples

This directory contains comprehensive examples demonstrating the `call_service` functionality in SpecQL, including external API integration, retry logic, callbacks, and error handling.

## Overview

The `call_service` step allows actions to asynchronously call external services (like payment processors, email services, etc.) while maintaining transactional consistency and providing robust error handling.

## Key Features Demonstrated

### 1. Asynchronous Payment Processing
The `place_order` action shows how to:
- Create an order record
- Queue a payment job asynchronously
- Handle success/failure callbacks
- Update order status based on payment outcome

### 2. Retry Configuration
- `max_retries: 3` - Retry failed payments up to 3 times
- `timeout: 30` - 30-second timeout per attempt
- Automatic backoff and retry logic

### 3. Callback Handling
Success and failure callbacks update the order status:
```yaml
on_success:
  - update: Order SET status = 'paid', paid_at = now() WHERE id = $job.entity_pk
on_failure:
  - update: Order SET status = 'payment_failed' WHERE id = $job.entity_pk
```

### 4. Synchronous Processing
The `process_payment_sync` action demonstrates synchronous calls with immediate responses.

## Generated Code

When you generate code from these entities, you'll get:

### SQL Functions
```sql
-- Asynchronous order placement with payment processing
CREATE OR REPLACE FUNCTION commerce.place_order(...) RETURNS app.mutation_result

-- Synchronous payment processing
CREATE OR REPLACE FUNCTION commerce.process_payment_sync(...) RETURNS app.mutation_result
```

### Job Queue Integration
- Jobs are automatically queued in `jobs.tb_job_run`
- Retry logic with exponential backoff
- Comprehensive observability views

### Frontend Integration
Generated TypeScript types and Apollo hooks handle the async nature of payment processing.

## Usage

### Generate Code
```bash
# Generate SQL migrations
python -m src.cli.generate entities examples/call_service/entities/*.yaml --output-dir db/migrations

# Generate frontend code
python -m src.cli.generate entities examples/call_service/entities/*.yaml \
  --output-frontend frontend/generated \
  --with-impacts
```

### Run Tests
```bash
# Test the call_service functionality
uv run pytest tests/integration/actions/test_call_service_action.py -v
```

## Service Registry Configuration

For these examples to work, configure the service registry:

```yaml
# registry/service_registry.yaml
services:
  stripe:
    base_url: https://api.stripe.com/v1
    auth_type: bearer_token
    timeout: 30
    retry_policy:
      max_attempts: 3
      backoff: exponential
    operations:
      create_charge:
        method: POST
        path: /charges
        input_schema:
          amount: integer
          currency: string
          customer_email: string
        output_schema:
          charge_id: string
          status: string
      create_refund:
        method: POST
        path: /refunds
        input_schema:
          charge_id: string
          amount: integer
```

## Error Handling Patterns

### Retryable vs Non-Retryable Errors
- Network timeouts → Retry
- Invalid payment details → Don't retry
- Insufficient funds → Don't retry
- Service unavailable → Retry with backoff

### Callback Error Handling
Callbacks run in separate transactions and should be idempotent.

## Monitoring

Use the generated observability views to monitor payment processing:

```sql
-- Check payment job health
SELECT * FROM jobs.v_job_queue_health WHERE service_name = 'stripe';

-- Monitor success rates
SELECT * FROM jobs.v_service_reliability WHERE service_name = 'stripe';

-- View retry patterns
SELECT * FROM jobs.v_job_retry_patterns WHERE service_name = 'stripe';
```

## Best Practices

1. **Idempotency**: Always design operations to be idempotent
2. **Timeouts**: Set reasonable timeouts for external calls
3. **Retry Logic**: Use appropriate retry counts based on operation criticality
4. **Error Handling**: Handle both temporary and permanent failures
5. **Monitoring**: Monitor job queues and success rates
6. **Testing**: Test both success and failure scenarios

## Frontend Integration

The generated frontend code handles the async nature of call_service operations:

```typescript
// Generated hook for place_order
const usePlaceOrder = () => {
  return useMutation<
    { placeOrder: MutationResult<PlaceOrderResult> },
    PlaceOrderInput
  >(PLACE_ORDER_MUTATION, {
    update: (cache, { data }) => {
      // Handle async payment processing
      if (data?.placeOrder.success) {
        // Order created, payment processing started
        const jobId = data.placeOrder.job_id;
        // Poll for payment status or use subscriptions
      }
    },
  });
};
```

This example demonstrates production-ready patterns for integrating external services with transactional consistency.</content>
</xai:function_call="bash">
<parameter name="command">cd /home/lionel/code/specql && python -m src.cli.generate entities examples/call_service/entities/order.yaml --output-dir /tmp/call_service_test