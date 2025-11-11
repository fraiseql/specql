# Multi-Execution Security Guidelines

This document outlines security best practices for the SpecQL multi-execution framework.

## Security Principles

### Defense in Depth

The framework implements multiple layers of security:

1. **Configuration Validation**: All configs validated at startup
2. **Runtime Controls**: Execution environment restrictions
3. **Resource Limits**: CPU, memory, disk, and network quotas
4. **Audit Logging**: Comprehensive execution tracking
5. **Access Controls**: Command, image, and domain allowlists

### Principle of Least Privilege

- **Minimal Permissions**: Grant only necessary permissions
- **Allowlists**: Restrict to approved commands, images, domains
- **Resource Limits**: Prevent resource exhaustion attacks
- **Network Isolation**: Limit network access where possible

## Execution Type Security

### HTTP Execution Security

#### Authentication Best Practices

```yaml
# Secure authentication configuration
runner_config:
  auth_type: "bearer"
  auth_config:
    token_env_var: "API_SECRET_KEY"  # Never hardcode secrets

# OR use API key authentication
runner_config:
  auth_type: "api_key"
  auth_config:
    api_key_env_var: "API_KEY"
    header_name: "X-API-Key"
```

#### Domain Restrictions

```yaml
security_policy:
  allowed_domains:
    - "api.stripe.com"
    - "api.github.com"
  # Never allow:
  # - localhost or private IPs in production
  # - internal services without proper authentication
```

#### Request Size Limits

```yaml
security_policy:
  max_request_size: 1048576  # 1MB limit
  rate_limit_per_minute: 100  # Prevent abuse
```

### Shell Execution Security

#### Command Allowlisting

```yaml
security_policy:
  allowed_commands:
    - "/usr/bin/python"
    - "/usr/bin/node"
    - "/usr/bin/bash"
    # NEVER allow:
    # - /bin/sh, /bin/bash without restrictions
    # - /usr/bin/sudo
    # - /usr/bin/rm, /bin/rm
    # - /usr/bin/wget, /usr/bin/curl
```

#### Working Directory Restrictions

```yaml
security_policy:
  working_directory_restrictions:
    - "/app/scripts"      # Application scripts
    - "/tmp/processing"   # Temporary processing
  # Prevent access to:
  # - /etc, /var, /usr
  # - User home directories
  # - System configuration files
```

#### Resource Limits

```yaml
security_policy:
  resource_limits:
    cpu_cores: 1.0        # Prevent CPU exhaustion
    memory_mb: 512        # Memory limits
    disk_mb: 1024         # Disk usage limits
    cpu_seconds: 300      # CPU time limits
```

#### Environment Sanitization

```yaml
# Safe environment variables only
runner_config:
  environment:
    PYTHONPATH: "/app"
    LOG_LEVEL: "INFO"
    # Avoid:
    # - PATH manipulation
    # - LD_LIBRARY_PATH
    # - Any user-controlled variables
```

### Docker Execution Security

#### Image Allowlisting

```yaml
security_policy:
  allowed_images:
    - "python:3.11-slim"
    - "node:18-alpine"
    # NEVER allow:
    # - Images with latest tag
    # - Untrusted registry images
    # - Images with root user
```

#### Volume Mount Security

```yaml
runner_config:
  volumes:
    - host_path: "/data/input"
      container_path: "/input"
      mode: "ro"  # Read-only where possible

security_policy:
  volume_restrictions:
    allowed_host_paths:
      - "/data"
      - "/tmp"
    max_volumes: 3
```

#### Container Isolation

```yaml
runner_config:
  network_mode: "none"    # No network access
  user: "appuser"         # Non-root user
  read_only: true         # Read-only filesystem
  tmpfs:                  # Temporary writable directories
    - "/tmp"
```

#### Resource Constraints

```yaml
security_policy:
  resource_limits:
    cpu_cores: 2.0
    memory_mb: 2048
    disk_mb: 5120
  # Enable OOM killer protection
  oom_kill_disable: false
```

### Serverless Execution Security

#### Function Permissions

```yaml
runner_config:
  auth_config:
    # AWS IAM role with minimal permissions
    role_arn: "arn:aws:iam::123456789012:role/LambdaExecutionRole"
    # GCP service account with specific permissions
    service_account_key_env_var: "GCP_SA_KEY"
```

#### Runtime Security

```yaml
security_policy:
  allowed_providers: ["aws", "gcp"]  # Restrict providers
  allowed_regions: ["us-east-1", "us-west-2"]  # Restrict regions
  resource_limits:
    memory_mb: 1024      # Function memory
    timeout_seconds: 300 # Execution timeout
```

#### Cost Controls

```yaml
security_policy:
  cost_limits:
    max_invocations_per_hour: 1000
    max_cost_per_hour: 5.0  # USD per hour
```

## Common Security Vulnerabilities

### Command Injection

**Vulnerable Pattern:**
```yaml
# DON'T DO THIS
input:
  command: "process_file"
  filename: "$user_input"  # User controls filename
```

**Secure Pattern:**
```yaml
# DO THIS
security_policy:
  allowed_commands: ["/usr/bin/python"]
  working_directory_restrictions: ["/app/processing"]

input:
  script: "process_file.py"
  input_file: "$validated_path"  # Server-side validation
```

### Path Traversal

**Vulnerable Pattern:**
```yaml
volumes:
  - host_path: "/data"
    container_path: "/data"
# User can access ../../../etc/passwd
```

**Secure Pattern:**
```yaml
security_policy:
  volume_restrictions:
    allowed_host_paths: ["/data/approved"]
    path_validation: "strict"  # Prevent .. in paths
```

### Resource Exhaustion

**Vulnerable Pattern:**
```yaml
# No resource limits
security_policy: {}
```

**Secure Pattern:**
```yaml
security_policy:
  resource_limits:
    cpu_cores: 1.0
    memory_mb: 512
    disk_mb: 1024
  # Circuit breaker for repeated failures
  circuit_breaker:
    failure_threshold: 5
    recovery_timeout: 300
```

### Information Disclosure

**Vulnerable Pattern:**
```yaml
# Exposing internal details in errors
error_message: "Failed to connect to database: $internal_error"
```

**Secure Pattern:**
```yaml
# Generic error messages
error_message: "Service temporarily unavailable"
# Log details internally only
logging:
  internal_errors: true
  user_safe_messages: true
```

## Security Monitoring

### Audit Logging

All executions are logged with:

```sql
-- Audit trail query
SELECT
    created_at,
    service_name,
    execution_type,
    triggered_by,
    security_context,
    resource_usage,
    CASE WHEN status = 'completed' THEN 'SUCCESS' ELSE 'FAILURE' END as result
FROM jobs.tb_job_run
WHERE created_at > now() - interval '24 hours'
ORDER BY created_at DESC;
```

### Security Alerts

Monitor for:

- **Allowlist Violations**: Commands/images not in allowlists
- **Resource Limit Exceedance**: Jobs hitting resource limits
- **Authentication Failures**: Repeated auth failures
- **Suspicious Patterns**: Unusual execution patterns

### Compliance Checks

```bash
# Security compliance validation
specql security-check registry/service_registry.yaml

# Audit log analysis
specql audit-report --since "2024-01-01" --service "critical_service"
```

## Environment-Specific Security

### Development Environment

```yaml
# Relaxed for development productivity
security_policy:
  allowed_commands: ["/usr/bin/python", "/usr/bin/node", "/usr/bin/bash"]
  resource_limits:
    memory_mb: 2048  # Higher limits for debugging
  network_access: "all"  # Full network for external APIs
```

### Production Environment

```yaml
# Strict security controls
security_policy:
  allowed_commands: ["/usr/bin/python"]  # Minimal commands
  resource_limits:
    memory_mb: 512   # Conservative limits
  network_access: "restricted"  # Limited network access
  audit_logging: "comprehensive"
```

### Staging Environment

```yaml
# Production-like security with some flexibility
security_policy:
  allowed_commands: ["/usr/bin/python", "/usr/bin/node"]
  resource_limits:
    memory_mb: 1024
  network_access: "restricted"
  audit_logging: "comprehensive"
```

## Security Testing

### Unit Tests

```python
def test_shell_runner_blocks_disallowed_commands():
    """Verify command allowlist enforcement"""
    runner = ShellScriptRunner()

    job = JobRecord(
        id="test-job",
        service_name="test",
        operation="run",
        input_data={"command": "rm", "args": ["-rf", "/"]},
        timeout_seconds=30,
        attempts=0,
        max_attempts=3
    )

    context = ExecutionContext(
        security_context={
            "allowed_commands": ["/usr/bin/echo"]  # rm not allowed
        }
    )

    result = await runner.execute(job, context)
    assert result.success == False
    assert "not allowed" in result.error_message
```

### Integration Tests

```python
def test_end_to_end_security():
    """Test complete security pipeline"""
    # 1. Configuration validation
    # 2. Runtime execution
    # 3. Resource limit enforcement
    # 4. Audit logging verification
    pass
```

### Penetration Testing

Regular security assessments should include:

- **Input Validation**: Test for injection attacks
- **Resource Limits**: Attempt resource exhaustion
- **Network Isolation**: Test network access controls
- **Authentication**: Test credential handling

## Incident Response

### Security Incident Process

1. **Detection**: Monitor alerts and logs
2. **Containment**: Disable affected services
3. **Investigation**: Analyze audit logs and system state
4. **Recovery**: Restore from clean backups
5. **Lessons Learned**: Update security policies

### Emergency Controls

```bash
# Emergency disable all shell execution
specql emergency-disable --execution-type shell

# Emergency resource limit reduction
specql emergency-limits --memory-mb 256 --cpu-cores 0.5

# Emergency audit mode
specql emergency-audit --enable
```

## Compliance Considerations

### Industry Standards

- **SOC 2**: Access controls, audit logging
- **PCI DSS**: Secure payment processing
- **HIPAA**: Protected health information handling
- **GDPR**: Data protection and privacy

### Regulatory Requirements

```yaml
# GDPR compliance
security_policy:
  data_processing:
    retention_days: 2555  # 7 years
    encryption: "aes256"
    audit_trail: true

# PCI compliance
security_policy:
  payment_processing:
    network_isolation: true
    key_management: "hsm"
    audit_logging: "comprehensive"
```

## Security Checklist

### Pre-Deployment

- [ ] All configurations validated
- [ ] Security policies reviewed
- [ ] Resource limits appropriate
- [ ] Allowlists comprehensive
- [ ] Audit logging enabled
- [ ] Authentication configured
- [ ] Network isolation tested

### Post-Deployment

- [ ] Security monitoring active
- [ ] Alert thresholds set
- [ ] Incident response plan ready
- [ ] Regular security assessments scheduled
- [ ] Compliance requirements met
- [ ] Documentation updated

### Ongoing Maintenance

- [ ] Security patches applied
- [ ] Configurations reviewed quarterly
- [ ] Access controls audited
- [ ] Security training completed
- [ ] Threat intelligence monitored
- [ ] Incident response tested

## Conclusion

Security is not a one-time implementation but an ongoing process. The multi-execution framework provides comprehensive security controls, but their effectiveness depends on proper configuration and monitoring. Always apply the principle of least privilege, implement defense in depth, and maintain vigilant monitoring of your execution environments.