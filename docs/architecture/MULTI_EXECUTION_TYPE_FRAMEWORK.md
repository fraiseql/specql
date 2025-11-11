# Multi-Execution-Type Framework Architecture

## Overview

The SpecQL Multi-Execution-Type Framework extends the `call_service` functionality to support multiple execution environments beyond HTTP APIs. This framework transforms SpecQL from a simple HTTP job dispatcher into a universal execution engine while maintaining backward compatibility.

## Core Architecture

### Execution Types

The framework supports four execution types:

1. **HTTP** - REST API calls (existing, enhanced)
2. **Shell** - Local shell script execution
3. **Docker** - Containerized job execution
4. **Serverless** - Cloud function invocation

### Key Components

#### 1. Job Runner Interface (`JobRunner`)

All execution types implement the `JobRunner` abstract interface:

```python
class JobRunner(ABC):
    async def validate_config(self, config: dict[str, Any]) -> bool
    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult
    async def cancel(self, job_id: str) -> bool
    def get_resource_requirements(self, config: dict[str, Any]) -> ResourceRequirements
```

#### 2. Runner Registry (`RunnerRegistry`)

Singleton registry that maps execution types to runner implementations:

```python
registry = RunnerRegistry.get_instance()
registry.register(ExecutionType.HTTP, HTTPRunner)
runner_class = registry.get_runner(ExecutionType.HTTP)
```

#### 3. Service Registry Extensions

Extended service registry with execution-type-specific configuration:

```yaml
services:
  - name: data_processor
    type: script
    execution_type: shell
    runner_config:
      allowed_commands: ["/usr/bin/python", "/usr/bin/node"]
    security_policy:
      resource_limits:
        memory_mb: 512
        cpu_cores: 1.0
```

#### 4. Database Schema Extensions

Extended `jobs.tb_job_run` table includes:

- `execution_type TEXT` - Execution environment
- `runner_config JSONB` - Runner-specific configuration
- `resource_usage JSONB` - Runtime metrics
- `security_context JSONB` - Security audit trail

#### 5. Compiler Integration

`CallServiceStepCompiler` automatically detects execution type from service registry and generates appropriate SQL.

## Execution Flow

1. **SpecQL Compilation**: `call_service` step compiled to job queue INSERT
2. **Type Detection**: Service registry lookup determines execution type
3. **Configuration**: Runner-specific config retrieved and validated
4. **Job Creation**: Job record created with execution metadata
5. **Runner Selection**: Appropriate runner instantiated from registry
6. **Execution**: Job executed in target environment
7. **Result Processing**: Output data stored, success/failure handled

## Security Architecture

### Defense in Depth

1. **Configuration Validation**: All runner configs validated at startup
2. **Command Allowlists**: Shell/Docker runners restrict executable commands
3. **Resource Limits**: CPU, memory, disk quotas enforced per job
4. **Network Isolation**: Container execution with network restrictions
5. **Audit Logging**: All execution attempts logged with security context

### Security Contexts

Each job includes security context with:
- Tenant isolation references
- User identity tracking
- Resource limit specifications
- Command/image allowlists
- Audit trail metadata

## Observability

### Performance Monitoring

- `v_execution_performance_by_type` - Performance metrics by execution type
- `v_resource_usage_by_runner` - Resource consumption tracking
- `v_runner_failure_patterns` - Failure analysis and alerting

### Metrics Tracked

- Execution duration by type
- Resource usage (CPU, memory, disk)
- Success/failure rates
- Queue depth and throughput

## Backward Compatibility

### Zero Breaking Changes

- Existing HTTP services work without modification
- `execution_type` defaults to 'http' for legacy services
- New columns have appropriate defaults
- API contracts unchanged

### Migration Path

- Legacy services automatically classified as HTTP
- Gradual migration with configuration updates
- Backward compatibility maintained throughout rollout

## Extensibility

### Plugin Architecture

New execution types can be added by:
1. Implementing `JobRunner` interface
2. Registering with `RunnerRegistry`
3. Adding execution type enum value
4. Updating service registry schema

### Example: Custom Runner

```python
class CustomRunner(JobRunner):
    async def execute(self, job: JobRecord, context: ExecutionContext) -> JobResult:
        # Custom execution logic
        pass

# Register runner
registry.register(ExecutionType.CUSTOM, CustomRunner)
```

## Performance Characteristics

### Overhead Targets

- **Runner Selection**: < 1ms
- **Configuration Validation**: < 5ms
- **Job Setup**: < 10ms
- **Total Overhead**: < 100ms per job

### Scalability

- **Concurrent Jobs**: 1000+ jobs/minute
- **Memory Usage**: < 256MB per runner instance
- **Horizontal Scaling**: Multi-worker support

## Error Handling

### Failure Modes

1. **Configuration Errors**: Invalid runner config detected at startup
2. **Execution Failures**: Job-specific errors with detailed logging
3. **Resource Exhaustion**: Automatic cleanup and alerting
4. **Network Issues**: Retry logic with exponential backoff

### Recovery Patterns

- **Circuit Breakers**: Failed runners temporarily disabled
- **Dead Letter Queues**: Unrecoverable jobs quarantined
- **Graceful Degradation**: Fallback to simpler execution types

## Integration Points

### Frontend Integration

- TypeScript types for job monitoring
- Apollo hooks for execution status queries
- Execution-type-specific UI components

### Monitoring Integration

- Prometheus metrics export
- Grafana dashboard templates
- Alert manager integration

## Deployment Considerations

### Environment-Specific Configuration

- Development: Relaxed security for development speed
- Staging: Production-like security with test data
- Production: Full security controls and monitoring

### Rollout Strategy

1. **Phase 1**: HTTP runner (backward compatibility validation)
2. **Phase 2**: Shell runner (secure script execution)
3. **Phase 3**: Docker runner (containerized workloads)
4. **Phase 4**: Serverless runner (cloud integrations)

## Future Extensions

### Planned Enhancements

- **Kubernetes Runner**: Native Kubernetes job execution
- **WebAssembly Runner**: WASM module execution
- **Plugin Marketplace**: Community-contributed runners
- **Advanced Scheduling**: Job dependencies and workflows

### Research Areas

- **Performance Optimization**: JIT compilation for hot paths
- **Security Hardening**: eBPF-based security policies
- **Multi-Cloud Support**: Unified interface across cloud providers
- **AI/ML Integration**: Model execution and inference