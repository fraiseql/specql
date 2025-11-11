# Multi-Execution-Type Configuration Reference

This guide explains how to configure each execution type in the SpecQL multi-execution framework.

## Service Registry Configuration

All execution types are configured in `registry/service_registry.yaml`. Each service can specify:

- `execution_type`: The execution environment (http, shell, docker, serverless)
- `runner_config`: Execution-type-specific configuration
- `security_policy`: Security controls and resource limits

## HTTP Execution Type

### Overview
HTTP execution calls REST APIs with authentication and retry logic.

### Configuration Schema

```yaml
services:
  - name: stripe_payment
    type: payment
    category: financial
    execution_type: http  # Default, can be omitted
    runner_config:
      base_url: "https://api.stripe.com/v1"
      auth_type: "bearer"  # bearer, basic, api_key, none
      auth_config:
        token_env_var: "STRIPE_SECRET_KEY"  # For bearer auth
        # OR for basic auth:
        username_env_var: "STRIPE_USERNAME"
        password_env_var: "STRIPE_PASSWORD"
        # OR for API key auth:
        api_key_env_var: "STRIPE_API_KEY"
        header_name: "Authorization"
      headers:
        Content-Type: "application/json"
        X-API-Version: "2023-10-16"
      timeout: 30  # seconds
      retry_config:
        max_retries: 3
        backoff_factor: 2.0
        retry_status_codes: [429, 500, 502, 503, 504]
    security_policy:
      allowed_domains: ["api.stripe.com"]
      max_request_size: 1048576  # 1MB
      rate_limit_per_minute: 100
```

### Runner Config Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `base_url` | string | Yes | Base URL for API endpoints |
| `auth_type` | string | No | Authentication type: bearer, basic, api_key, none |
| `auth_config` | object | No | Authentication configuration |
| `headers` | object | No | Default headers for all requests |
| `timeout` | number | No | Request timeout in seconds (default: 300) |
| `retry_config` | object | No | Retry configuration |

### Security Policy Fields

| Field | Type | Description |
|-------|------|-------------|
| `allowed_domains` | array | List of allowed domains for requests |
| `max_request_size` | number | Maximum request body size in bytes |
| `rate_limit_per_minute` | number | Requests per minute limit |

### Example Usage

```yaml
# SpecQL entity
actions:
  - call_service:
      service: stripe_payment
      operation: create_charge
      input:
        amount: "$order.total_cents"
        currency: "usd"
        source: "$payment.token"
```

## Shell Execution Type

### Overview
Shell execution runs local commands with comprehensive security controls.

### Configuration Schema

```yaml
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
      shell: "/bin/bash"  # Default shell
      timeout: 600  # 10 minutes
    security_policy:
      allowed_commands:
        - "/usr/bin/python"
        - "/usr/bin/node"
        - "/usr/bin/bash"
        - "/usr/bin/cat"
        - "/usr/bin/grep"
      resource_limits:
        cpu_cores: 1.0
        memory_mb: 512
        disk_mb: 1024
        cpu_seconds: 300
      working_directory_restrictions:
        - "/app/scripts"
        - "/tmp/processing"
      network_access: "none"  # none, localhost, all
      file_access: "read_write"  # none, read, read_write
```

### Runner Config Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `working_directory` | string | No | Working directory for command execution |
| `environment` | object | No | Environment variables |
| `shell` | string | No | Shell to use (default: /bin/bash) |
| `timeout` | number | No | Execution timeout in seconds (default: 600) |

### Security Policy Fields

| Field | Type | Description |
|-------|------|-------------|
| `allowed_commands` | array | Absolute paths of allowed executables |
| `resource_limits` | object | CPU, memory, disk limits |
| `working_directory_restrictions` | array | Allowed working directories |
| `network_access` | string | Network access level |
| `file_access` | string | File system access level |

### Example Usage

```yaml
# SpecQL entity
actions:
  - call_service:
      service: data_processor
      operation: process_batch
      input:
        script: "process_data.py"
        input_file: "$batch.input_path"
        output_file: "$batch.output_path"
```

## Docker Execution Type

### Overview
Docker execution runs jobs in containers with image allowlisting and volume mounting.

### Configuration Schema

```yaml
services:
  - name: ml_processor
    type: container
    category: compute
    execution_type: docker
    runner_config:
      image: "python:3.11-slim"
      command: ["python", "ml_predict.py"]
      working_dir: "/app"
      environment:
        MODEL_PATH: "/models"
        LOG_LEVEL: "INFO"
      volumes:
        - host_path: "/data/models"
          container_path: "/models"
          mode: "ro"  # read-only
        - host_path: "/tmp/processing"
          container_path: "/tmp"
          mode: "rw"  # read-write
      network_mode: "none"  # none, bridge, host
      restart_policy: "no"  # no, on-failure, always
      timeout: 1800  # 30 minutes
    security_policy:
      allowed_images:
        - "python:3.11-slim"
        - "tensorflow/tensorflow:2.13.0"
        - "pytorch/pytorch:2.0.1"
      resource_limits:
        cpu_cores: 2.0
        memory_mb: 2048
        disk_mb: 5120
      volume_restrictions:
        allowed_host_paths:
          - "/data"
          - "/tmp"
        max_volumes: 5
      network_isolation: true
```

### Runner Config Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | string | Yes | Docker image to use |
| `command` | array | No | Command to run in container |
| `working_dir` | string | No | Working directory in container |
| `environment` | object | No | Environment variables |
| `volumes` | array | No | Volume mounts |
| `network_mode` | string | No | Docker network mode |
| `restart_policy` | string | No | Container restart policy |
| `timeout` | number | No | Execution timeout in seconds |

### Security Policy Fields

| Field | Type | Description |
|-------|------|-------------|
| `allowed_images` | array | Allowed Docker images |
| `resource_limits` | object | Container resource limits |
| `volume_restrictions` | object | Volume mount restrictions |
| `network_isolation` | boolean | Enable network isolation |

### Example Usage

```yaml
# SpecQL entity
actions:
  - call_service:
      service: ml_processor
      operation: predict
      input:
        model_version: "v2.1"
        input_data: "$request.data"
        output_path: "$result.prediction_path"
```

## Serverless Execution Type

### Overview
Serverless execution invokes cloud functions with async result handling.

### Configuration Schema

```yaml
services:
  - name: image_resizer
    type: function
    category: media
    execution_type: serverless
    runner_config:
      provider: "aws"  # aws, gcp, azure
      function_name: "image-resize-service"
      region: "us-east-1"
      runtime: "nodejs18.x"
      memory_mb: 1024
      timeout: 900  # 15 minutes
      environment:
        BUCKET_NAME: "processed-images"
      auth_config:
        role_arn: "arn:aws:iam::123456789012:role/LambdaExecutionRole"
        # OR for GCP:
        service_account_key_env_var: "GCP_SERVICE_ACCOUNT_KEY"
    security_policy:
      allowed_providers: ["aws", "gcp"]
      allowed_regions: ["us-east-1", "us-west-2", "eu-west-1"]
      resource_limits:
        memory_mb: 3072  # Max 3GB
        timeout_seconds: 900  # Max 15 minutes
      cost_limits:
        max_invocations_per_hour: 1000
        max_cost_per_hour: 10.0  # USD
```

### Runner Config Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Cloud provider: aws, gcp, azure |
| `function_name` | string | Yes | Function name |
| `region` | string | No | Cloud region |
| `runtime` | string | No | Runtime environment |
| `memory_mb` | number | No | Memory allocation |
| `timeout` | number | No | Function timeout |
| `environment` | object | No | Environment variables |
| `auth_config` | object | No | Authentication configuration |

### Security Policy Fields

| Field | Type | Description |
|-------|------|-------------|
| `allowed_providers` | array | Allowed cloud providers |
| `allowed_regions` | array | Allowed regions |
| `resource_limits` | object | Function resource limits |
| `cost_limits` | object | Cost control limits |

### Example Usage

```yaml
# SpecQL entity
actions:
  - call_service:
      service: image_resizer
      operation: resize
      input:
        image_url: "$upload.image_url"
        width: 800
        height: 600
        format: "webp"
```

## Common Configuration Patterns

### Environment Variable References

All configuration values can reference environment variables:

```yaml
runner_config:
  base_url: "${API_BASE_URL}"
  auth_config:
    token_env_var: "${API_TOKEN}"
```

### Conditional Configuration

Use environment-specific configurations:

```yaml
# Development
development:
  services:
    - name: test_api
      execution_type: http
      runner_config:
        base_url: "http://localhost:3000"

# Production
production:
  services:
    - name: test_api
      execution_type: http
      runner_config:
        base_url: "https://api.production.com"
```

### Resource Limit Patterns

Common resource limit patterns:

```yaml
# Light processing
security_policy:
  resource_limits:
    cpu_cores: 0.5
    memory_mb: 256
    timeout_seconds: 60

# Heavy computation
security_policy:
  resource_limits:
    cpu_cores: 4.0
    memory_mb: 8192
    timeout_seconds: 3600

# I/O intensive
security_policy:
  resource_limits:
    cpu_cores: 1.0
    memory_mb: 1024
    disk_mb: 10240
    timeout_seconds: 1800
```

## Validation and Error Handling

### Configuration Validation

Configurations are validated at startup:

```bash
# Validate service registry
specql validate-config registry/service_registry.yaml

# Check for security policy violations
specql security-check registry/service_registry.yaml
```

### Common Validation Errors

- **Missing required fields**: `base_url` required for HTTP
- **Invalid paths**: Commands must be absolute paths
- **Security violations**: Disallowed commands or images
- **Resource limits**: Exceeded maximum allowed values

### Runtime Error Handling

Jobs include detailed error information:

```sql
-- Check job status and errors
SELECT
    identifier,
    status,
    error_message,
    resource_usage
FROM jobs.tb_job_run
WHERE id = 'job-uuid';
```

## Migration from HTTP-Only

### Automatic Migration

Existing services automatically use HTTP execution:

```yaml
# Before (still works)
services:
  - name: legacy_api
    type: api
    operations: [...]

# After (explicit, but equivalent)
services:
  - name: legacy_api
    type: api
    execution_type: http  # Explicit default
    operations: [...]
```

### Gradual Enhancement

Add execution types incrementally:

```yaml
# Phase 1: Keep HTTP
services:
  - name: api_service
    execution_type: http
    # ... existing config

# Phase 2: Add shell processing
services:
  - name: shell_processor
    execution_type: shell
    runner_config:
      allowed_commands: ["/usr/bin/python"]
    security_policy:
      resource_limits:
        memory_mb: 512
```

## Best Practices

### Security First

1. **Principle of Least Privilege**: Minimal allowed commands/images
2. **Resource Limits**: Always set appropriate limits
3. **Network Isolation**: Use restrictive network policies
4. **Audit Logging**: Enable comprehensive logging

### Performance Optimization

1. **Right-sizing**: Match resource limits to workload
2. **Connection Pooling**: Reuse connections where possible
3. **Caching**: Cache expensive operations
4. **Async Processing**: Use async execution for long-running jobs

### Monitoring and Alerting

1. **Key Metrics**: Track success rates, latency, resource usage
2. **Error Patterns**: Monitor for security violations
3. **Cost Tracking**: Monitor cloud costs for serverless
4. **Performance Alerts**: Alert on performance degradation

### Configuration Management

1. **Environment Separation**: Different configs for dev/staging/prod
2. **Version Control**: Keep configs in version control
3. **Validation**: Validate configs in CI/CD pipeline
4. **Documentation**: Document all configuration options