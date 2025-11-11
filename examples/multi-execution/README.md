# Multi-Execution Examples

This directory contains example SpecQL entities demonstrating each execution type in the multi-execution framework.

## Examples by Execution Type

### HTTP Execution
**Use Case**: REST API integrations, webhooks, external service calls
- [Payment Processing](http/) - Stripe payment integration
- [Email Service](http/) - SendGrid email delivery
- [File Storage](http/) - AWS S3 file operations

### Shell Execution
**Use Case**: Data processing, file manipulation, system automation
- [Data Processing](shell/) - CSV processing and transformation
- [Image Processing](shell/) - Image resizing and optimization
- [Report Generation](shell/) - PDF report creation

### Docker Execution
**Use Case**: Isolated processing, custom runtimes, ML inference
- [ML Prediction](docker/) - TensorFlow model inference
- [Video Processing](docker/) - FFmpeg video transcoding
- [Document Conversion](docker/) - LibreOffice document processing

### Serverless Execution
**Use Case**: Cloud functions, event processing, scalable workloads
- [Image Resizing](serverless/) - AWS Lambda image processing
- [Data Analysis](serverless/) - Google Cloud Functions analytics
- [Notification Service](serverless/) - Azure Functions notifications

## Service Registry Configuration

Each example includes the corresponding service registry configuration in `registry/service_registry.yaml`.

## Running the Examples

1. **Install Dependencies**
   ```bash
   pip install specql
   ```

2. **Configure Services**
   ```bash
   # Copy service registry
   cp examples/multi-execution/registry/service_registry.yaml registry/

   # Set environment variables
   export STRIPE_API_KEY="sk_test_..."
   export SENDGRID_API_KEY="SG...."
   ```

3. **Run Schema Generation**
   ```bash
   specql generate-schema examples/multi-execution/entities/
   ```

4. **Execute Jobs**
   ```bash
   # Process a payment
   specql execute-job --entity payment --action process_payment

   # Generate a report
   specql execute-job --entity report --action generate_pdf

   # Run ML prediction
   specql execute-job --entity prediction --action classify_image
   ```

## Common Patterns

### Error Handling
```yaml
actions:
  - call_service:
      service: payment_processor
      operation: charge_card
      input: { amount: "$order.total" }
      on_failure:
        - call_service:
            service: notification_service
            operation: send_alert
            input: { message: "Payment failed for order $order.id" }
```

### Sequential Processing
```yaml
actions:
  - call_service:
      service: data_validator
      operation: validate
      input: { data: "$input.raw_data" }
      on_success:
        - call_service:
            service: data_processor
            operation: transform
            input: { data: "$validation.result" }
            on_success:
              - call_service:
                  service: data_storage
                  operation: save
                  input: { data: "$transform.result" }
```

### Parallel Processing
```yaml
actions:
  - parallel:
      - call_service:
          service: email_service
          operation: send_receipt
          input: { order: "$order" }
      - call_service:
          service: inventory_service
          operation: update_stock
          input: { items: "$order.items" }
      - call_service:
          service: analytics_service
          operation: track_purchase
          input: { order: "$order" }
```

## Security Considerations

All examples include security policies:

- **Command Allowlists**: Restricted to approved executables
- **Image Allowlists**: Limited to trusted Docker images
- **Resource Limits**: CPU, memory, and time constraints
- **Network Controls**: Restricted external access

## Monitoring

Monitor execution with the included observability views:

```sql
-- Check execution performance
SELECT * FROM jobs.v_execution_performance_by_type;

-- Monitor resource usage
SELECT * FROM jobs.v_resource_usage_by_runner;

-- Track failure patterns
SELECT * FROM jobs.v_runner_failure_patterns;
```

## Customization

Adapt these examples to your needs:

1. **Modify Service Configurations** in `registry/service_registry.yaml`
2. **Update Entity Definitions** to match your data models
3. **Adjust Security Policies** based on your requirements
4. **Add Custom Runners** by implementing the `JobRunner` interface

## Support

- **Documentation**: See `docs/` directory for detailed guides
- **Troubleshooting**: Check `docs/troubleshooting/MULTI_EXECUTION_TROUBLESHOOTING.md`
- **Migration**: See `docs/guides/MULTI_EXECUTION_MIGRATION.md` for upgrading existing services