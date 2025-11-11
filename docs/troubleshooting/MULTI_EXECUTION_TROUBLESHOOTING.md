# Multi-Execution Troubleshooting Guide

This guide helps diagnose and resolve common issues with the SpecQL multi-execution framework.

## Quick Diagnosis

### Check System Status

```bash
# Overall system health
specql health-check

# Runner status
specql runner-status

# Queue status
specql queue-status
```

### Common Symptoms and Solutions

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Jobs stuck in `pending` | Runner not registered | Check runner registration |
| Jobs failing immediately | Configuration error | Validate service registry |
| High memory usage | Resource limits too high | Reduce memory limits |
| Slow execution | Network timeouts | Check network connectivity |
| Authentication failures | Invalid credentials | Verify API keys/tokens |

## Job Execution Issues

### Jobs Not Starting

**Problem**: Jobs remain in `pending` status indefinitely.

**Diagnosis**:
```sql
-- Check pending jobs
SELECT
    identifier,
    service_name,
    execution_type,
    created_at,
    error_message
FROM jobs.tb_job_run
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 10;
```

**Common Causes**:

1. **Runner Not Registered**
   ```bash
   # Check registered runners
   specql list-runners

   # Expected output includes: http, shell, docker, serverless
   ```

   **Solution**: Ensure runner is imported and registered:
   ```python
   # In src/runners/__init__.py
   from src.runners.shell_runner import ShellScriptRunner
   _registry.register(ExecutionType.SHELL, ShellScriptRunner)
   ```

2. **Invalid Execution Type**
   ```yaml
   # Wrong: execution_type: "Shell"
   # Correct: execution_type: "shell"
   ```

3. **Service Registry Error**
   ```bash
   # Validate service registry
   specql validate-config registry/service_registry.yaml
   ```

### Jobs Failing Immediately

**Problem**: Jobs transition from `pending` to `failed` within seconds.

**Diagnosis**:
```sql
-- Check recent failures
SELECT
    identifier,
    service_name,
    execution_type,
    error_message,
    created_at,
    updated_at
FROM jobs.tb_job_run
WHERE status = 'failed'
    AND created_at > now() - interval '1 hour'
ORDER BY created_at DESC;
```

**Common Causes**:

1. **Configuration Validation Failure**
   ```
   Error: HTTP runner requires 'base_url' in config
   ```

   **Solution**: Add missing configuration:
   ```yaml
   runner_config:
     base_url: "https://api.example.com"
   ```

2. **Security Policy Violation**
   ```
   Error: Command '/usr/bin/rm' is not allowed
   ```

   **Solution**: Add command to allowlist:
   ```yaml
   security_policy:
     allowed_commands:
       - "/usr/bin/rm"
   ```

3. **Resource Limits Exceeded**
   ```
   Error: Memory limit exceeded: 2048MB requested, 512MB allowed
   ```

   **Solution**: Reduce resource requirements or increase limits.

### HTTP Execution Issues

#### Connection Timeouts

**Problem**: HTTP requests timing out.

**Diagnosis**:
```bash
# Test connectivity
curl -v https://api.example.com/health

# Check network from application
specql test-connectivity --url https://api.example.com
```

**Solutions**:

1. **Increase Timeout**
   ```yaml
   runner_config:
     timeout: 60  # seconds
   ```

2. **Check Network Configuration**
   ```bash
   # Firewall rules
   sudo iptables -L

   # DNS resolution
   nslookup api.example.com
   ```

3. **Retry Configuration**
   ```yaml
   runner_config:
     retry_config:
       max_retries: 3
       backoff_factor: 2.0
   ```

#### Authentication Failures

**Problem**: HTTP 401/403 errors.

**Diagnosis**:
```bash
# Test authentication manually
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/test
```

**Solutions**:

1. **Check Token Validity**
   ```bash
   # Verify environment variable
   echo $API_TOKEN

   # Check token expiration
   specql validate-token --service stripe
   ```

2. **Correct Auth Configuration**
   ```yaml
   runner_config:
     auth_type: "bearer"
     auth_config:
       token_env_var: "API_TOKEN"  # Correct variable name
   ```

### Shell Execution Issues

#### Command Not Found

**Problem**: `command not found` errors.

**Diagnosis**:
```bash
# Check if command exists
which python
ls -la /usr/bin/python

# Check PATH
echo $PATH
```

**Solutions**:

1. **Use Absolute Paths**
   ```yaml
   security_policy:
     allowed_commands:
       - "/usr/bin/python"  # Absolute path required
   ```

2. **Check Working Directory**
   ```yaml
   runner_config:
     working_directory: "/app/scripts"
   ```

#### Permission Denied

**Problem**: `Permission denied` errors.

**Diagnosis**:
```bash
# Check file permissions
ls -la /path/to/script.py

# Check execution permissions
stat /usr/bin/python
```

**Solutions**:

1. **Fix File Permissions**
   ```bash
   chmod +x /path/to/script.py
   ```

2. **Check User Context**
   ```yaml
   runner_config:
     user: "appuser"  # Non-root user
   ```

#### Resource Limit Exceeded

**Problem**: Jobs killed due to resource limits.

**Diagnosis**:
```sql
-- Check resource usage
SELECT
    identifier,
    resource_usage
FROM jobs.tb_job_run
WHERE status = 'failed'
    AND error_message LIKE '%resource%'
ORDER BY created_at DESC;
```

**Solutions**:

1. **Increase Limits**
   ```yaml
   security_policy:
     resource_limits:
       memory_mb: 1024  # Increase memory
       cpu_seconds: 600  # Increase CPU time
   ```

2. **Optimize Code**
   - Reduce memory usage
   - Add early exits
   - Use streaming for large data

### Docker Execution Issues

#### Image Pull Failures

**Problem**: `image not found` or pull errors.

**Diagnosis**:
```bash
# Check Docker daemon
docker ps

# Test image pull manually
docker pull python:3.11-slim

# Check registry access
docker login registry.example.com
```

**Solutions**:

1. **Verify Image Name**
   ```yaml
   runner_config:
     image: "python:3.11-slim"  # Correct image name
   ```

2. **Check Image Allowlist**
   ```yaml
   security_policy:
     allowed_images:
       - "python:3.11-slim"
   ```

3. **Registry Authentication**
   ```yaml
   runner_config:
     registry_auth:
       username_env_var: "DOCKER_USERNAME"
       password_env_var: "DOCKER_PASSWORD"
   ```

#### Container Startup Failures

**Problem**: Containers fail to start.

**Diagnosis**:
```bash
# Check container logs
docker logs <container_id>

# Test container manually
docker run --rm python:3.11-slim python --version
```

**Solutions**:

1. **Check Command Syntax**
   ```yaml
   runner_config:
     command: ["python", "script.py"]  # Correct array format
   ```

2. **Verify Working Directory**
   ```yaml
   runner_config:
     working_dir: "/app"  # Directory exists in container
   ```

3. **Check Volume Mounts**
   ```yaml
   runner_config:
     volumes:
       - host_path: "/data"
         container_path: "/data"
         mode: "ro"
   ```

### Serverless Execution Issues

#### Function Not Found

**Problem**: `Function not found` errors.

**Diagnosis**:
```bash
# AWS Lambda
aws lambda list-functions --region us-east-1

# GCP Functions
gcloud functions list --region us-central1
```

**Solutions**:

1. **Verify Function Name**
   ```yaml
   runner_config:
     function_name: "my-function"  # Exact function name
   ```

2. **Check Region**
   ```yaml
   runner_config:
     region: "us-east-1"  # Correct region
   ```

3. **Validate Permissions**
   ```bash
   # AWS IAM permissions
   aws sts get-caller-identity

   # GCP service account
   gcloud auth list
   ```

#### Timeout Errors

**Problem**: Functions timing out.

**Solutions**:

1. **Increase Timeout**
   ```yaml
   runner_config:
     timeout: 300  # 5 minutes
   ```

2. **Optimize Function Code**
   - Reduce execution time
   - Use async processing
   - Implement early returns

## Observability Issues

### Missing Metrics

**Problem**: No data in observability views.

**Diagnosis**:
```sql
-- Check if views exist
SELECT table_name
FROM information_schema.views
WHERE table_name LIKE 'v_execution_%';

-- Check data volume
SELECT count(*) FROM jobs.tb_job_run;
```

**Solutions**:

1. **Run Schema Migration**
   ```bash
   specql migrate-schema
   ```

2. **Check View Definitions**
   ```sql
   -- Recreate views if needed
   DROP VIEW IF EXISTS jobs.v_execution_performance_by_type;
   -- Rerun schema generation
   ```

### Performance Issues

**Problem**: Slow query performance.

**Diagnosis**:
```sql
-- Check index usage
EXPLAIN ANALYZE
SELECT * FROM jobs.v_execution_performance_by_type
WHERE execution_type = 'http';

-- Check table statistics
ANALYZE jobs.tb_job_run;
```

**Solutions**:

1. **Rebuild Indexes**
   ```sql
   REINDEX INDEX jobs.idx_tb_job_run_execution_type;
   ```

2. **Update Statistics**
   ```sql
   VACUUM ANALYZE jobs.tb_job_run;
   ```

## Configuration Issues

### YAML Syntax Errors

**Problem**: Configuration parsing failures.

**Diagnosis**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('registry/service_registry.yaml'))"

# Check indentation
specql validate-config registry/service_registry.yaml
```

**Common Issues**:

1. **Incorrect Indentation**
   ```yaml
   # Wrong
   services:
     - name: test
     execution_type: http

   # Correct
   services:
     - name: test
       execution_type: http
   ```

2. **Invalid Execution Type**
   ```yaml
   # Wrong: execution_type: "HTTP"
   # Correct: execution_type: "http"
   ```

### Environment Variable Issues

**Problem**: Environment variables not resolved.

**Diagnosis**:
```bash
# Check environment variables
env | grep API_

# Test variable resolution
specql test-vars --config registry/service_registry.yaml
```

**Solutions**:

1. **Export Variables**
   ```bash
   export API_TOKEN="your-token"
   ```

2. **Check Variable Names**
   ```yaml
   auth_config:
     token_env_var: "API_TOKEN"  # Exact variable name
   ```

## Security Issues

### Allowlist Violations

**Problem**: Commands/images blocked by security policies.

**Diagnosis**:
```sql
-- Check security violations
SELECT
    identifier,
    service_name,
    error_message
FROM jobs.tb_job_run
WHERE error_message LIKE '%not allowed%'
ORDER BY created_at DESC;
```

**Solutions**:

1. **Update Allowlists**
   ```yaml
   security_policy:
     allowed_commands:
       - "/usr/bin/python"
       - "/usr/bin/node"  # Add missing commands
   ```

2. **Review Security Policies**
   ```bash
   specql security-audit --service problematic_service
   ```

### Resource Exhaustion

**Problem**: System running out of resources.

**Diagnosis**:
```bash
# Check system resources
top
df -h
free -h

# Check container resources
docker stats
```

**Solutions**:

1. **Reduce Resource Limits**
   ```yaml
   security_policy:
     resource_limits:
       memory_mb: 256  # Reduce memory allocation
   ```

2. **Implement Circuit Breakers**
   ```yaml
   security_policy:
     circuit_breaker:
       failure_threshold: 5
       recovery_timeout: 300
   ```

## Advanced Debugging

### Enable Debug Logging

```bash
# Enable verbose logging
export SPECQL_LOG_LEVEL=DEBUG

# Run with debug output
specql process-jobs --verbose
```

### Job Execution Tracing

```sql
-- Trace complete job lifecycle
SELECT
    id,
    identifier,
    status,
    execution_type,
    created_at,
    started_at,
    completed_at,
    error_message,
    resource_usage,
    security_context
FROM jobs.tb_job_run
WHERE identifier = 'job-identifier'
ORDER BY created_at;
```

### Runner-Specific Debugging

```python
# Debug HTTP runner
from src.runners.http_runner import HTTPRunner
import logging
logging.basicConfig(level=logging.DEBUG)

runner = HTTPRunner()
# Add debug breakpoints
```

### Network Debugging

```bash
# HTTP traffic capture
tcpdump -i eth0 port 443

# DNS debugging
dig api.example.com

# SSL certificate validation
openssl s_client -connect api.example.com:443
```

## Common Error Patterns

### Pattern 1: Intermittent Failures

**Symptoms**: Jobs succeed sometimes, fail others.

**Likely Causes**:
- Network timeouts
- Resource contention
- External service rate limits

**Solutions**:
- Implement retry logic
- Add exponential backoff
- Monitor external service health

### Pattern 2: All Jobs Failing

**Symptoms**: Complete service outage.

**Likely Causes**:
- Configuration corruption
- Runner registration failure
- Database connectivity issues

**Solutions**:
- Check configuration syntax
- Verify runner imports
- Test database connections

### Pattern 3: Performance Degradation

**Symptoms**: Jobs taking longer over time.

**Likely Causes**:
- Resource leaks
- Database index fragmentation
- External service slowdown

**Solutions**:
- Monitor resource usage
- Rebuild database indexes
- Implement performance budgets

## Getting Help

### Community Resources

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check docs/ directory for updates
- **Examples**: Review examples/ directory for patterns

### Diagnostic Commands

```bash
# Comprehensive system diagnostic
specql diagnose --full

# Generate support bundle
specql support-bundle --output support.tar.gz

# Check version compatibility
specql version-check
```

### Emergency Procedures

1. **Stop Job Processing**
   ```bash
   specql emergency-stop
   ```

2. **Switch to Safe Mode**
   ```bash
   specql safe-mode --enable
   ```

3. **Rollback Configuration**
   ```bash
   git checkout HEAD~1 registry/service_registry.yaml
   ```

Remember: When in doubt, check the logs first. Most issues reveal themselves through detailed error messages and execution traces.