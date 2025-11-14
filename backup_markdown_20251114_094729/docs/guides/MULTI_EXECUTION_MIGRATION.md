# Migration Guide: HTTP-Only to Multi-Execution

This guide helps migrate existing SpecQL applications from HTTP-only `call_service` to multi-execution support.

## Migration Overview

### What Changes

The multi-execution framework extends SpecQL without breaking existing functionality:

- **Zero Breaking Changes**: Existing HTTP services continue working
- **Backward Compatibility**: All current APIs and behaviors preserved
- **Gradual Adoption**: Migrate services incrementally
- **Enhanced Capabilities**: Add shell, Docker, and serverless execution

### Migration Phases

1. **Phase 1**: Infrastructure preparation (no code changes)
2. **Phase 2**: Service registry enhancement (configuration only)
3. **Phase 3**: New execution types adoption (optional)
4. **Phase 4**: Advanced features (optional)

## Phase 1: Infrastructure Preparation

### Step 1: Update SpecQL Version

```bash
# Update to multi-execution enabled version
pip install specql>=2.0.0

# Verify installation
specql --version
```

### Step 2: Database Schema Migration

```bash
# Run schema migration (adds new columns with defaults)
specql migrate-schema

# Verify schema changes
specql validate-schema
```

**What Changes**:
- Adds `execution_type` column (defaults to 'http')
- Adds `runner_config` JSONB column
- Adds `resource_usage` JSONB column
- Adds `security_context` JSONB column
- Creates new indexes and observability views

### Step 3: Service Registry Validation

```bash
# Validate existing service registry
specql validate-config registry/service_registry.yaml

# Check for deprecated patterns
specql migration-check registry/service_registry.yaml
```

## Phase 2: Service Registry Enhancement

### Automatic Migration

Existing services automatically work with default HTTP execution:

```yaml
# Before (still works)
services:
  - name: stripe_api
    type: payment
    category: financial
    operations:
      - name: create_charge
        input_schema: { amount: integer }
        output_schema: { id: string }

# After (explicit, equivalent)
services:
  - name: stripe_api
    type: payment
    category: financial
    execution_type: http  # Explicit default
    operations:
      - name: create_charge
        input_schema: { amount: integer }
        output_schema: { id: string }
```

### Enhanced HTTP Configuration

Add explicit configuration for better control:

```yaml
services:
  - name: stripe_api
    type: payment
    category: financial
    execution_type: http
    runner_config:
      base_url: "https://api.stripe.com/v1"
      auth_type: "bearer"
      auth_config:
        token_env_var: "STRIPE_SECRET_KEY"
      timeout: 30
      retry_config:
        max_retries: 3
        backoff_factor: 2.0
    security_policy:
      allowed_domains: ["api.stripe.com"]
      max_request_size: 1048576
      rate_limit_per_minute: 100
    operations:
      - name: create_charge
        input_schema: { amount: integer }
        output_schema: { id: string }
```

### Migration Checklist

- [ ] Schema migration completed
- [ ] Service registry validates successfully
- [ ] Existing jobs still process correctly
- [ ] No application code changes required

## Phase 3: New Execution Types Adoption

### Adding Shell Script Execution

**Use Case**: Data processing, file manipulation, system automation

```yaml
# Add shell service
services:
  - name: data_processor
    type: script
    category: automation
    execution_type: shell
    runner_config:
      working_directory: "/app/scripts"
      environment:
        PYTHONPATH: "/app"
        LOG_LEVEL: "INFO"
    security_policy:
      allowed_commands:
        - "/usr/bin/python"
        - "/usr/bin/node"
        - "/usr/bin/bash"
        - "/usr/bin/cat"
      resource_limits:
        cpu_cores: 1.0
        memory_mb: 512
        disk_mb: 1024
    operations:
      - name: process_data
        input_schema:
          input_file: string
          output_file: string
        output_schema:
          status: string
          records_processed: integer
```

**SpecQL Usage**:

```yaml
# Existing HTTP call
actions:
  - call_service:
      service: stripe_api
      operation: create_charge
      input:
        amount: "$order.total"

# New shell execution
actions:
  - call_service:
      service: data_processor
      operation: process_data
      input:
        input_file: "$upload.path"
        output_file: "$result.path"
```

### Adding Docker Container Execution

**Use Case**: Isolated processing, custom runtimes, ML inference

```yaml
services:
  - name: ml_processor
    type: container
    category: compute
    execution_type: docker
    runner_config:
      image: "python:3.11-slim"
      command: ["python", "predict.py"]
      working_dir: "/app"
      volumes:
        - host_path: "/models"
          container_path: "/models"
          mode: "ro"
    security_policy:
      allowed_images: ["python:3.11-slim"]
      resource_limits:
        cpu_cores: 2.0
        memory_mb: 2048
        disk_mb: 5120
    operations:
      - name: predict
        input_schema:
          model_version: string
          input_data: object
        output_schema:
          prediction: object
          confidence: number
```

### Adding Serverless Execution

**Use Case**: Cloud functions, event processing, scalable workloads

```yaml
services:
  - name: image_resizer
    type: function
    category: media
    execution_type: serverless
    runner_config:
      provider: "aws"
      function_name: "image-resize-service"
      region: "us-east-1"
      memory_mb: 1024
      timeout: 300
    security_policy:
      allowed_providers: ["aws"]
      allowed_regions: ["us-east-1", "us-west-2"]
      resource_limits:
        memory_mb: 3072
        timeout_seconds: 900
      cost_limits:
        max_invocations_per_hour: 1000
        max_cost_per_hour: 5.0
    operations:
      - name: resize
        input_schema:
          image_url: string
          width: integer
          height: integer
        output_schema:
          resized_url: string
          original_size: integer
          new_size: integer
```

## Phase 4: Advanced Features

### Multi-Step Workflows

Combine different execution types in workflows:

```yaml
# Complex workflow
actions:
  # 1. HTTP API call to get data
  - call_service:
      service: api_service
      operation: fetch_data
      input: { query: "$request.query" }
      on_success:
        # 2. Shell processing
        - call_service:
            service: data_processor
            operation: transform
            input: { data: "$api_response.data" }
            on_success:
              # 3. Docker ML processing
              - call_service:
                  service: ml_processor
                  operation: analyze
                  input: { dataset: "$processed.data" }
```

### Conditional Execution

Use execution types based on conditions:

```yaml
actions:
  - if:
      condition: "$input.use_gpu"
      then:
        # GPU-accelerated processing
        - call_service:
            service: gpu_processor
            operation: process
      else:
        # CPU processing
        - call_service:
            service: cpu_processor
            operation: process
```

### Error Handling and Fallbacks

Implement resilient patterns:

```yaml
actions:
  - call_service:
      service: primary_api
      operation: process
      input: { data: "$input.data" }
      on_failure:
        # Fallback to secondary service
        - call_service:
            service: backup_api
            operation: process
            input: { data: "$input.data" }
```

## Environment-Specific Migration

### Development Environment

```yaml
# Relaxed security for development
development:
  services:
    - name: test_processor
      execution_type: shell
      security_policy:
        allowed_commands: ["/usr/bin/python", "/usr/bin/bash"]
        resource_limits:
          memory_mb: 2048  # Higher limits for debugging
```

### Production Environment

```yaml
# Strict security for production
production:
  services:
    - name: prod_processor
      execution_type: shell
      security_policy:
        allowed_commands: ["/usr/bin/python"]  # Minimal commands
        resource_limits:
          memory_mb: 512  # Conservative limits
```

## Testing Migration

### Unit Tests

Update existing tests to work with new framework:

```python
# Before
def test_call_service_http():
    # Test HTTP API call
    pass

# After (still works)
def test_call_service_http():
    # Test HTTP API call (unchanged)
    pass

# New tests
def test_call_service_shell():
    # Test shell execution
    pass

def test_call_service_docker():
    # Test Docker execution
    pass
```

### Integration Tests

Test end-to-end workflows:

```python
def test_multi_execution_workflow():
    """Test workflow with multiple execution types"""
    # 1. HTTP API call
    # 2. Shell processing
    # 3. Docker analysis
    # 4. Result storage
    pass
```

### Load Testing

Verify performance under load:

```bash
# Load test HTTP execution
specql load-test --service http_service --concurrency 100

# Load test shell execution
specql load-test --service shell_service --concurrency 50

# Compare performance
specql benchmark --services http_service shell_service docker_service
```

## Monitoring and Observability

### New Metrics

Monitor execution-type-specific metrics:

```sql
-- Performance by execution type
SELECT
    execution_type,
    avg(duration_seconds) as avg_duration,
    count(*) as total_jobs,
    count(*) filter (where status = 'completed')::float / count(*) as success_rate
FROM jobs.tb_job_run
WHERE created_at > now() - interval '1 hour'
GROUP BY execution_type;

-- Resource usage tracking
SELECT
    execution_type,
    avg((resource_usage->>'cpu_usage_percent')::numeric) as avg_cpu,
    avg((resource_usage->>'memory_mb')::numeric) as avg_memory
FROM jobs.tb_job_run
WHERE resource_usage IS NOT NULL
GROUP BY execution_type;
```

### Alerting

Set up alerts for new failure patterns:

```yaml
# Alert configuration
alerts:
  - name: "High HTTP Error Rate"
    condition: "http_error_rate > 0.05"
    execution_type: "http"

  - name: "Shell Command Failures"
    condition: "shell_failures > 10"
    execution_type: "shell"

  - name: "Resource Limit Violations"
    condition: "resource_violations > 5"
    execution_type: "any"
```

## Rollback Procedures

### Emergency Rollback

If issues arise, rollback to HTTP-only mode:

```bash
# Disable new execution types
specql execution-types --disable shell docker serverless

# Revert to HTTP-only
specql rollback --to http-only

# Restore original service registry
git checkout HEAD~1 registry/service_registry.yaml
```

### Gradual Rollback

Phase out new execution types:

```yaml
# Temporarily disable problematic service
services:
  - name: problematic_service
    execution_type: http  # Fallback to HTTP
    # ... rest of config
```

## Best Practices

### Migration Strategy

1. **Start Small**: Migrate one service at a time
2. **Test Thoroughly**: Comprehensive testing before production
3. **Monitor Closely**: Watch for performance and error changes
4. **Have Rollback Plan**: Ready to revert if needed

### Configuration Management

1. **Version Control**: Keep service registries in Git
2. **Environment Separation**: Different configs per environment
3. **Validation**: Validate configs in CI/CD pipeline
4. **Documentation**: Document all execution type usage

### Security Considerations

1. **Principle of Least Privilege**: Minimal permissions
2. **Allowlists**: Restrict commands, images, domains
3. **Resource Limits**: Prevent resource exhaustion
4. **Audit Logging**: Enable comprehensive logging

### Performance Optimization

1. **Right-sizing**: Match resource limits to workload
2. **Caching**: Cache expensive operations
3. **Async Processing**: Use async for long-running jobs
4. **Load Balancing**: Distribute load across workers

## Common Migration Issues

### Issue 1: Schema Migration Failures

**Problem**: Database migration fails
**Solution**:
```bash
# Check database permissions
specql check-permissions

# Manual migration
psql -d your_database -f migrations/001_multi_execution.sql

# Verify migration
specql validate-schema
```

### Issue 2: Service Registry Validation Errors

**Problem**: Configuration validation fails
**Solution**:
```bash
# Detailed validation
specql validate-config registry/service_registry.yaml --verbose

# Fix common issues
# - Check YAML indentation
# - Verify environment variables exist
# - Confirm absolute command paths
```

### Issue 3: Performance Degradation

**Problem**: Jobs slower after migration
**Solution**:
```bash
# Profile execution
specql profile --service migrated_service

# Check resource limits
specql resource-check --service migrated_service

# Optimize configuration
# - Reduce resource limits
# - Enable caching
# - Use connection pooling
```

### Issue 4: Security Violations

**Problem**: Jobs failing due to security policies
**Solution**:
```bash
# Audit security violations
specql security-audit --service problematic_service

# Update allowlists
# - Add missing commands to allowed_commands
# - Add missing images to allowed_images
# - Adjust resource limits
```

## Support and Resources

### Getting Help

- **Documentation**: Check docs/ directory for guides
- **Examples**: Review examples/ directory for patterns
- **GitHub Issues**: Report migration issues
- **Community**: Join SpecQL community discussions

### Professional Services

For complex migrations, consider:
- **Migration Assessment**: Evaluate current architecture
- **Planning Workshop**: Design migration strategy
- **Implementation Support**: Assisted migration execution
- **Post-Migration Review**: Validate migration success

## Success Metrics

### Migration Completeness

- [ ] All services migrated or have migration plan
- [ ] Zero breaking changes to existing functionality
- [ ] All tests passing
- [ ] Performance meets or exceeds baseline

### Operational Readiness

- [ ] Monitoring and alerting configured
- [ ] Rollback procedures documented and tested
- [ ] Support team trained on new execution types
- [ ] Incident response plans updated

### Business Value

- [ ] New execution types delivering value
- [ ] Development velocity improved
- [ ] Operational costs optimized
- [ ] System reliability maintained

---

**Migration Checklist**

- [ ] Infrastructure preparation completed
- [ ] Schema migration successful
- [ ] Service registry enhanced
- [ ] New execution types tested
- [ ] Monitoring and alerting configured
- [ ] Rollback procedures ready
- [ ] Team trained and documentation updated
- [ ] Success metrics defined and tracked

**Next Steps**: Start with Phase 1 infrastructure preparation, then gradually adopt new execution types based on your needs and risk tolerance.