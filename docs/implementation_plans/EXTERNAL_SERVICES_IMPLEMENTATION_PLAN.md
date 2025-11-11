# External Services Implementation Plan - SpecQL

**Feature**: External Service Integration (Job Queue Pattern)
**Complexity**: Complex | **Phased TDD Approach**
**Status**: Planning Phase
**Date**: 2025-11-11

---

## Executive Summary

SpecQL currently handles CRUD operations beautifully, but real applications need to call external services (email, payment, webhooks, etc.). This plan implements a **Job Queue Pattern** that allows users to declaratively call external services from SpecQL actions with built-in reliability, retries, observability, and multi-tenant isolation.

**Key Design Principles**:
1. **Async by default** - External calls don't block mutations
2. **Declarative** - Users write YAML, framework generates PL/pgSQL + job orchestration
3. **Observable** - Full audit trail of all service calls
4. **Reliable** - Automatic retries, idempotency, error handling
5. **Type-safe** - Service registry validates inputs/outputs

**User Experience**:
```yaml
# What users write (12 lines)
entity: Order
actions:
  - name: place_order
    steps:
      - insert: Order
        as: order
      - call_service:
          service: stripe
          operation: create_charge
          input:
            amount: $order.total
          on_success:
            - update: Order SET payment_status = 'paid'
```

**What framework generates** (500+ lines):
- Job queue schema & indexes
- PL/pgSQL action function with job queueing
- Callback functions for success/failure
- Service registry validation
- Worker integration points
- Observability views

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ SpecQL YAML (User writes)                                   │
│ - call_service steps                                         │
│ - success/failure callbacks                                  │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Team A: Parser (NEW call_service step)                      │
│ - Parse call_service syntax                                  │
│ - Validate service/operation exists                          │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Team B: Schema Generator (NEW jobs schema)                  │
│ - jobs.tb_job_run table                                      │
│ - Indexes for worker polling                                 │
│ - Observability views                                        │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ Team C: Action Compiler (NEW call_service step compiler)    │
│ - Generate INSERT INTO jobs.tb_job_run                       │
│ - Generate callback functions                                │
│ - Compile success/failure steps                              │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL Database                                          │
│ - actions insert jobs                                        │
│ - workers poll for pending jobs                              │
│ - callbacks execute on completion                            │
└──────────────────────────────────────────────────────────────┘
```

---

## PHASES

### Phase 1: Foundation - Service Registry & Schema

**Objective**: Establish service registry and core job queue schema

**Duration**: ~8 hours

#### Part 1A: Service Registry (Team A Extension)

**TDD Cycle 1.1: Service Registry Parser**

1. **RED**: Write failing test for service registry parsing
   - Test file: `tests/unit/registry/test_service_registry.py`
   - Expected failure: ServiceRegistry class doesn't exist
   ```python
   def test_parse_service_registry():
       """Parse service registry YAML"""
       registry = ServiceRegistry.from_yaml("registry/service_registry.yaml")
       assert len(registry.services) > 0
       assert registry.get_service("sendgrid") is not None

   def test_validate_operation_exists():
       """Validate service operation exists"""
       registry = ServiceRegistry.from_yaml("registry/service_registry.yaml")
       service = registry.get_service("sendgrid")
       assert service.has_operation("send_email")
   ```

2. **GREEN**: Implement minimal service registry
   - Files to create:
     - `src/registry/service_registry.py` - ServiceRegistry class
     - `registry/service_registry.yaml` - Initial registry (sendgrid, stripe)
   ```python
   @dataclass
   class ServiceOperation:
       name: str
       input_schema: Dict[str, str]
       output_schema: Dict[str, str]
       timeout: int = 30
       max_retries: int = 3

   @dataclass
   class Service:
       name: str
       type: str  # email, payment, webhook, notification
       category: str  # communication, financial, integration
       operations: List[ServiceOperation]

   @dataclass
   class ServiceRegistry:
       services: List[Service]

       @classmethod
       def from_yaml(cls, path: str) -> 'ServiceRegistry':
           # Load and parse YAML
           pass
   ```

3. **REFACTOR**: Clean up and optimize
   - Add caching for registry lookups
   - Add validation for input/output schemas
   - Follow project patterns from domain_registry.py

4. **QA**: Verify phase completion
   - [ ] All tests pass (`make test`)
   - [ ] Service registry loads correctly
   - [ ] Validation works for operations

**TDD Cycle 1.2: Parser Extension for call_service**

1. **RED**: Write failing test for call_service step parsing
   - Test file: `tests/unit/core/test_call_service_step.py`
   - Expected failure: call_service not recognized
   ```python
   def test_parse_call_service_basic():
       """Parse basic call_service step"""
       yaml_content = """
       entity: Order
       actions:
         - name: send_receipt
           steps:
             - call_service:
                 service: sendgrid
                 operation: send_email
                 input:
                   to: $order.customer_email
                   subject: "Receipt"
       """
       parsed = parse_specql(yaml_content)
       action = parsed.entities[0].actions[0]
       assert len(action.steps) == 1
       assert isinstance(action.steps[0], CallServiceStep)

   def test_call_service_with_callbacks():
       """Parse call_service with success/failure callbacks"""
       yaml_content = """
       entity: Order
       actions:
         - name: charge_order
           steps:
             - call_service:
                 service: stripe
                 operation: create_charge
                 on_success:
                   - update: Order SET status = 'paid'
                 on_failure:
                   - update: Order SET status = 'failed'
       """
       parsed = parse_specql(yaml_content)
       step = parsed.entities[0].actions[0].steps[0]
       assert len(step.on_success) == 1
       assert len(step.on_failure) == 1
   ```

2. **GREEN**: Implement call_service step parsing
   - Files to modify:
     - `src/core/models.py` - Add CallServiceStep class
     - `src/core/step_parser.py` - Add call_service parsing
   ```python
   @dataclass
   class CallServiceStep(Step):
       step_type: str = "call_service"
       service: str
       operation: str
       input: Dict[str, Any]
       async_mode: bool = True
       timeout: Optional[int] = None
       max_retries: Optional[int] = None
       on_success: List[Step] = field(default_factory=list)
       on_failure: List[Step] = field(default_factory=list)
       correlation_field: Optional[str] = None  # e.g., "$order.id"
   ```

3. **REFACTOR**: Clean up parser code
   - Extract common callback parsing logic
   - Add validation for service/operation existence
   - Ensure proper error messages

4. **QA**: Verify phase completion
   - [ ] All parser tests pass
   - [ ] call_service steps parse correctly
   - [ ] Callbacks parse correctly
   - [ ] Validation rejects invalid services

#### Part 1B: Job Queue Schema (Team B Extension)

**TDD Cycle 1.3: Job Queue Schema Generation**

1. **RED**: Write failing test for jobs schema generation
   - Test file: `tests/unit/schema/test_jobs_schema_generator.py`
   - Expected failure: JobsSchemaGenerator doesn't exist
   ```python
   def test_generate_jobs_schema():
       """Generate jobs schema with tb_job_run table"""
       generator = JobsSchemaGenerator()
       sql = generator.generate()
       assert "CREATE SCHEMA IF NOT EXISTS jobs" in sql
       assert "CREATE TABLE jobs.tb_job_run" in sql
       assert "pk_job_run INTEGER PRIMARY KEY" in sql
       assert "service_name TEXT NOT NULL" in sql

   def test_jobs_schema_indexes():
       """Generate indexes for job polling"""
       generator = JobsSchemaGenerator()
       sql = generator.generate()
       assert "idx_tb_job_run_pending" in sql
       assert "idx_tb_job_run_retry" in sql
       assert "idx_tb_job_run_correlation" in sql
   ```

2. **GREEN**: Implement jobs schema generator
   - Files to create:
     - `src/generators/schema/jobs_schema_generator.py`
   ```python
   class JobsSchemaGenerator:
       def generate(self) -> str:
           """Generate complete jobs schema"""
           return "\n\n".join([
               self._generate_schema(),
               self._generate_job_run_table(),
               self._generate_indexes(),
               self._generate_helper_functions(),
               self._generate_observability_views()
           ])
   ```

3. **REFACTOR**: Clean up schema generation
   - Extract common SQL patterns
   - Add proper comments
   - Follow naming conventions

4. **QA**: Verify phase completion
   - [ ] Schema generation tests pass
   - [ ] Generated SQL is valid PostgreSQL
   - [ ] Indexes are properly named

**TDD Cycle 1.4: Integration with Schema Orchestrator**

1. **RED**: Write test for jobs schema in orchestrator
   - Test file: `tests/unit/schema/test_schema_orchestrator_jobs.py`
   - Expected failure: Jobs schema not included
   ```python
   def test_orchestrator_includes_jobs_schema():
       """Schema orchestrator includes jobs schema"""
       orchestrator = SchemaOrchestrator(entities=[], actions=[])
       sql = orchestrator.generate_full_schema()
       assert "CREATE SCHEMA IF NOT EXISTS jobs" in sql
       assert "CREATE TABLE jobs.tb_job_run" in sql
   ```

2. **GREEN**: Integrate jobs schema into orchestrator
   - Files to modify:
     - `src/generators/schema/schema_orchestrator.py`
   ```python
   def generate_full_schema(self) -> str:
       sections = [
           # ... existing sections ...
           self._generate_jobs_schema(),  # NEW
           # ... rest ...
       ]
   ```

3. **REFACTOR**: Ensure proper ordering
   - Jobs schema after app schema (depends on app.mutation_result)
   - Before domain schemas (domain actions need jobs tables)

4. **QA**: Verify phase completion
   - [ ] Full schema includes jobs
   - [ ] Schema order is correct
   - [ ] Integration tests pass

---

### Phase 2: Action Compilation - call_service Step

**Objective**: Compile call_service steps to PL/pgSQL job queueing

**Duration**: ~12 hours

#### Part 2A: CallServiceStepCompiler (Team C Extension)

**TDD Cycle 2.1: Basic Job Insertion**

1. **RED**: Write failing test for call_service compilation
   - Test file: `tests/unit/actions/step_compilers/test_call_service_step_compiler.py`
   - Expected failure: Compiler doesn't exist
   ```python
   def test_compile_call_service_basic():
       """Compile call_service to INSERT INTO jobs.tb_job_run"""
       step = CallServiceStep(
           service="sendgrid",
           operation="send_email",
           input={"to": "$order.customer_email", "subject": "Receipt"}
       )
       compiler = CallServiceStepCompiler(step, context)
       sql = compiler.compile()
       assert "INSERT INTO jobs.tb_job_run" in sql
       assert "'sendgrid'" in sql
       assert "'send_email'" in sql
       assert "jsonb_build_object" in sql

   def test_compile_service_input_expressions():
       """Compile input expressions to JSON"""
       step = CallServiceStep(
           service="stripe",
           operation="create_charge",
           input={
               "amount": "$order.total",
               "customer": "$order.customer_id"
           }
       )
       compiler = CallServiceStepCompiler(step, context)
       sql = compiler.compile()
       assert "_order.total" in sql  # Trinity resolution
       assert "_order.customer_id" in sql
   ```

2. **GREEN**: Implement basic call_service compilation
   - Files to create:
     - `src/generators/actions/step_compilers/call_service_step.py`
   ```python
   class CallServiceStepCompiler:
       def __init__(self, step: CallServiceStep, context: CompilationContext):
           self.step = step
           self.context = context

       def compile(self) -> str:
           """Compile to INSERT INTO jobs.tb_job_run"""
           return f"""
           INSERT INTO jobs.tb_job_run (
               identifier,
               service_name,
               operation,
               input_data,
               tenant_id,
               triggered_by,
               correlation_id,
               entity_type,
               entity_pk
           ) VALUES (
               {self._generate_identifier()},
               '{self.step.service}',
               '{self.step.operation}',
               {self._compile_input_data()},
               _tenant_id,
               _user_id,
               {self._compile_correlation()},
               '{self.context.entity_name}',
               {self._compile_entity_pk()}
           ) RETURNING id INTO _job_id_{self._job_var_suffix()};
           """
   ```

3. **REFACTOR**: Clean up compilation logic
   - Extract input data compilation
   - Reuse expression compiler for $variables
   - Add proper error handling

4. **QA**: Verify phase completion
   - [ ] Call service compilation tests pass
   - [ ] Generated SQL is valid
   - [ ] Expressions compile correctly

**TDD Cycle 2.2: Callback Function Generation**

1. **RED**: Write failing test for callback generation
   - Test file: `tests/unit/actions/test_callback_generator.py`
   - Expected failure: Callbacks not generated
   ```python
   def test_generate_success_callback():
       """Generate on_success callback function"""
       step = CallServiceStep(
           service="stripe",
           operation="create_charge",
           on_success=[
               UpdateStep(
                   entity="Order",
                   set_fields={"payment_status": "paid"},
                   where="pk_order = $job.entity_pk"
               )
           ]
       )
       generator = CallbackGenerator(step, context)
       sql = generator.generate_success_callback()
       assert "CREATE FUNCTION" in sql
       assert "_job_run_id UUID" in sql
       assert "_output_data JSONB" in sql
       assert "UPDATE" in sql
   ```

2. **GREEN**: Implement callback function generation
   - Files to create:
     - `src/generators/actions/callback_generator.py`
   ```python
   class CallbackGenerator:
       def generate_success_callback(self) -> str:
           """Generate on_success callback function"""
           callback_name = self._callback_function_name("success")
           steps_sql = self._compile_callback_steps(self.step.on_success)

           return f"""
           CREATE FUNCTION {callback_name}(
               _job_run_id UUID,
               _output_data JSONB
           ) RETURNS void AS $$
           DECLARE
               _job RECORD;
           BEGIN
               SELECT * INTO _job
               FROM jobs.tb_job_run
               WHERE id = _job_run_id;

               {steps_sql}
           END;
           $$ LANGUAGE plpgsql;
           """
   ```

3. **REFACTOR**: Optimize callback generation
   - Reuse existing step compilers
   - Add proper variable scoping
   - Handle nested callbacks

4. **QA**: Verify phase completion
   - [ ] Callback generation tests pass
   - [ ] Success/failure callbacks both work
   - [ ] Callbacks can access job context

**TDD Cycle 2.3: Integration with Action Orchestrator**

1. **RED**: Write integration test for full action with call_service
   - Test file: `tests/integration/actions/test_call_service_action.py`
   - Expected failure: Action doesn't include job queueing
   ```python
   def test_action_with_call_service_compiles():
       """Full action with call_service compiles"""
       yaml_content = """
       entity: Order
       actions:
         - name: place_order
           steps:
             - insert: Order
               as: order
             - call_service:
                 service: stripe
                 operation: create_charge
                 input:
                   amount: $order.total
       """
       orchestrator = ActionOrchestrator.from_yaml(yaml_content)
       sql = orchestrator.generate()

       # Should include job insertion
       assert "INSERT INTO jobs.tb_job_run" in sql

       # Should return job_id in response
       assert "payment_job_id" in sql or "job_id" in sql
   ```

2. **GREEN**: Integrate into action orchestrator
   - Files to modify:
     - `src/generators/actions/action_orchestrator.py`
     - `src/generators/actions/core_logic_generator.py`
   ```python
   def _compile_step(self, step: Step) -> str:
       if isinstance(step, CallServiceStep):
           return CallServiceStepCompiler(step, self.context).compile()
       # ... existing compilers ...
   ```

3. **REFACTOR**: Clean up integration
   - Ensure callback functions generated before main action
   - Add job_id to mutation response metadata
   - Update success response generator

4. **QA**: Verify phase completion
   - [ ] Full action compilation works
   - [ ] Callbacks generated in correct order
   - [ ] Integration tests pass
   - [ ] Generated SQL is valid PostgreSQL

---

### Phase 3: Enhanced Features - Retries & Observability

**Objective**: Add retry logic, idempotency, and observability views

**Duration**: ~8 hours

#### Part 3A: Idempotency & Retry Logic

**TDD Cycle 3.1: Idempotent Job Identifiers**

1. **RED**: Write test for idempotent identifiers
   - Test file: `tests/unit/actions/test_job_idempotency.py`
   - Expected failure: Identifiers not unique per action invocation
   ```python
   def test_job_identifier_includes_entity_id():
       """Job identifier includes entity ID for idempotency"""
       step = CallServiceStep(
           service="sendgrid",
           operation="send_email"
       )
       compiler = CallServiceStepCompiler(step, context)
       sql = compiler.compile()

       # Should use entity ID in identifier
       assert "|| _order.id::text" in sql or similar pattern

   def test_duplicate_job_rejected():
       """Duplicate job identifier rejected by DB"""
       # This will be tested at integration level
       # UNIQUE constraint on identifier should prevent duplicates
   ```

2. **GREEN**: Implement idempotent identifiers
   - Files to modify:
     - `src/generators/actions/step_compilers/call_service_step.py`
   ```python
   def _generate_identifier(self) -> str:
       """Generate idempotent identifier"""
       entity_var = self.context.entity_variable
       return f"""
       '{self.context.entity_name}_' ||
       {entity_var}.id::text ||
       '_{self.step.service}_{self.step.operation}'
       """
   ```

3. **REFACTOR**: Improve identifier generation
   - Handle multiple call_service steps in one action
   - Add sequence number if needed
   - Document identifier format

4. **QA**: Verify phase completion
   - [ ] Identifiers are unique per entity + service + operation
   - [ ] Duplicate attempts don't create new jobs
   - [ ] Tests pass

**TDD Cycle 3.2: Retry Configuration**

1. **RED**: Write test for retry configuration
   - Test file: `tests/unit/actions/test_job_retry_config.py`
   - Expected failure: max_retries not respected
   ```python
   def test_custom_max_retries():
       """Custom max_retries respected"""
       step = CallServiceStep(
           service="stripe",
           operation="create_charge",
           max_retries=5
       )
       compiler = CallServiceStepCompiler(step, context)
       sql = compiler.compile()
       assert "max_attempts, 5" in sql or "max_attempts = 5" in sql

   def test_default_max_retries():
       """Default max_retries is 3"""
       step = CallServiceStep(
           service="sendgrid",
           operation="send_email"
       )
       compiler = CallServiceStepCompiler(step, context)
       sql = compiler.compile()
       # Should use service registry default or 3
   ```

2. **GREEN**: Implement retry configuration
   - Files to modify:
     - `src/generators/actions/step_compilers/call_service_step.py`
   ```python
   def _get_max_retries(self) -> int:
       """Get max retries from step or service registry"""
       if self.step.max_retries is not None:
           return self.step.max_retries

       # Lookup in service registry
       service = self.context.service_registry.get_service(self.step.service)
       operation = service.get_operation(self.step.operation)
       return operation.max_retries
   ```

3. **REFACTOR**: Consolidate retry logic
   - Extract retry configuration logic
   - Add timeout configuration similarly
   - Document configuration precedence

4. **QA**: Verify phase completion
   - [ ] Custom retries work
   - [ ] Defaults work
   - [ ] Service registry consulted

#### Part 3B: Observability Views (Team B Extension)

**TDD Cycle 3.3: Job Statistics Views**

1. **RED**: Write test for observability views
   - Test file: `tests/unit/schema/test_jobs_observability.py`
   - Expected failure: Views don't exist
   ```python
   def test_generate_job_stats_view():
       """Generate v_job_stats view"""
       generator = JobsSchemaGenerator()
       sql = generator.generate()
       assert "CREATE VIEW jobs.v_job_stats" in sql
       assert "service_name" in sql
       assert "avg_duration_sec" in sql

   def test_generate_failing_services_view():
       """Generate v_failing_services alert view"""
       generator = JobsSchemaGenerator()
       sql = generator.generate()
       assert "CREATE VIEW jobs.v_failing_services" in sql
       assert "failure_count" in sql
   ```

2. **GREEN**: Implement observability views
   - Files to modify:
     - `src/generators/schema/jobs_schema_generator.py`
   ```python
   def _generate_observability_views(self) -> str:
       """Generate observability views"""
       return """
       -- Job statistics by service/operation
       CREATE VIEW jobs.v_job_stats AS
       SELECT
           service_name,
           operation,
           status,
           COUNT(*) as total_jobs,
           AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::numeric(10,2) as avg_duration_sec,
           PERCENTILE_CONT(0.95) WITHIN GROUP (
               ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))
           )::numeric(10,2) as p95_duration_sec
       FROM jobs.tb_job_run
       WHERE started_at IS NOT NULL
       GROUP BY service_name, operation, status;

       -- Alert view for failing services
       CREATE VIEW jobs.v_failing_services AS
       SELECT
           service_name,
           operation,
           COUNT(*) as failure_count,
           MAX(updated_at) as last_failure,
           ARRAY_AGG(error_message) FILTER (WHERE error_message IS NOT NULL) as recent_errors
       FROM jobs.tb_job_run
       WHERE status = 'failed'
           AND attempts >= max_attempts
           AND updated_at > now() - interval '1 hour'
       GROUP BY service_name, operation
       HAVING COUNT(*) > 10;
       """
   ```

3. **REFACTOR**: Enhance observability
   - Add more useful metrics
   - Add correlation views
   - Add tenant-specific views

4. **QA**: Verify phase completion
   - [ ] Views generate correctly
   - [ ] Views provide useful metrics
   - [ ] Tests pass

---

### Phase 4: Frontend Integration - Metadata & Types

**Objective**: Generate TypeScript types and metadata for service calls

**Duration**: ~6 hours

#### Part 4A: Service Call Metadata (Team D Extension)

**TDD Cycle 4.1: Service Call Annotations**

1. **RED**: Write test for service call metadata
   - Test file: `tests/unit/fraiseql/test_service_call_metadata.py`
   - Expected failure: Metadata not generated
   ```python
   def test_mutation_includes_service_call_metadata():
       """Mutation metadata includes service calls"""
       yaml_content = """
       entity: Order
       actions:
         - name: place_order
           steps:
             - call_service:
                 service: stripe
                 operation: create_charge
       """
       generator = MutationMetadataGenerator.from_yaml(yaml_content)
       metadata = generator.generate()

       assert "service_calls" in metadata
       assert metadata["service_calls"][0]["service"] == "stripe"
       assert metadata["service_calls"][0]["operation"] == "create_charge"
   ```

2. **GREEN**: Implement service call metadata
   - Files to modify:
     - `src/generators/fraiseql/mutation_annotator.py`
   ```python
   def _extract_service_calls(self, action: Action) -> List[Dict]:
       """Extract service calls from action"""
       calls = []
       for step in action.steps:
           if isinstance(step, CallServiceStep):
               calls.append({
                   "service": step.service,
                   "operation": step.operation,
                   "async": step.async_mode
               })
       return calls
   ```

3. **REFACTOR**: Enhance metadata
   - Add service call timing estimates
   - Add retry configuration
   - Document metadata format

4. **QA**: Verify phase completion
   - [ ] Metadata includes service calls
   - [ ] Frontend can use metadata
   - [ ] Tests pass

**TDD Cycle 4.2: TypeScript Types for Jobs**

1. **RED**: Write test for job TypeScript types
   - Test file: `tests/unit/frontend/test_job_types_generator.py`
   - Expected failure: Job types not generated
   ```python
   def test_generate_job_status_types():
       """Generate TypeScript types for job status"""
       generator = TypeScriptTypesGenerator()
       ts = generator.generate_job_types()

       assert "type JobStatus = 'pending' | 'running' | 'completed' | 'failed'" in ts
       assert "interface JobRun {" in ts
   ```

2. **GREEN**: Implement job type generation
   - Files to create:
     - `src/generators/frontend/job_types_generator.py`
   ```python
   class JobTypesGenerator:
       def generate(self) -> str:
           """Generate TypeScript types for jobs"""
           return """
           export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

           export interface JobRun {
               id: string;
               service_name: string;
               operation: string;
               status: JobStatus;
               input_data: Record<string, any>;
               output_data?: Record<string, any>;
               error_message?: string;
               attempts: number;
               max_attempts: number;
               created_at: string;
               completed_at?: string;
           }

           export interface MutationWithJob<T> {
               data: T;
               job_id?: string;
           }
           """
   ```

3. **REFACTOR**: Improve type generation
   - Add service-specific types
   - Generate types from service registry
   - Add proper imports

4. **QA**: Verify phase completion
   - [ ] TypeScript types generated
   - [ ] Types are valid TS
   - [ ] Tests pass

---

### Phase 5: CLI Integration - Service Management

**Objective**: Add CLI commands for service management and testing

**Duration**: ~4 hours

#### Part 5A: Service CLI Commands (Team E Extension)

**TDD Cycle 5.1: Service List Command**

1. **RED**: Write test for service list command
   - Test file: `tests/unit/cli/test_service_commands.py`
   - Expected failure: Command doesn't exist
   ```python
   def test_list_services_command():
       """List available services"""
       result = run_cli(["services", "list"])
       assert result.exit_code == 0
       assert "sendgrid" in result.output
       assert "stripe" in result.output

   def test_show_service_details():
       """Show service details"""
       result = run_cli(["services", "show", "stripe"])
       assert "create_charge" in result.output
       assert "input_schema" in result.output
   ```

2. **GREEN**: Implement service list command
   - Files to create:
     - `src/cli/services.py`
   ```python
   @click.group()
   def services():
       """Manage external services"""
       pass

   @services.command()
   def list():
       """List available services"""
       registry = ServiceRegistry.from_yaml("registry/service_registry.yaml")
       for service in registry.services:
           click.echo(f"• {service.name} ({service.type})")
           for op in service.operations:
               click.echo(f"  - {op.name}")

   @services.command()
   @click.argument("service_name")
   def show(service_name: str):
       """Show service details"""
       registry = ServiceRegistry.from_yaml("registry/service_registry.yaml")
       service = registry.get_service(service_name)
       # Display full service details
   ```

3. **REFACTOR**: Improve CLI output
   - Add colors and formatting
   - Add JSON output option
   - Add filtering

4. **QA**: Verify phase completion
   - [ ] List command works
   - [ ] Show command works
   - [ ] Output is readable

**TDD Cycle 5.2: Job Monitoring Commands**

1. **RED**: Write test for job monitoring
   - Test file: `tests/unit/cli/test_job_commands.py`
   - Expected failure: Commands don't exist
   ```python
   def test_jobs_status_command():
       """Show job status"""
       result = run_cli(["jobs", "status"])
       assert result.exit_code == 0

   def test_jobs_stats_command():
       """Show job statistics"""
       result = run_cli(["jobs", "stats"])
       assert result.exit_code == 0
       assert "total_jobs" in result.output
   ```

2. **GREEN**: Implement job monitoring commands
   - Files to create:
     - `src/cli/jobs.py`
   ```python
   @click.group()
   def jobs():
       """Monitor and manage jobs"""
       pass

   @jobs.command()
   def status():
       """Show current job status"""
       # Query jobs.v_job_stats
       pass

   @jobs.command()
   @click.option("--service", help="Filter by service")
   def stats(service: Optional[str]):
       """Show job statistics"""
       # Query jobs.v_job_stats with filters
       pass
   ```

3. **REFACTOR**: Enhance monitoring
   - Add real-time updates
   - Add failure analysis
   - Add retry commands

4. **QA**: Verify phase completion
   - [ ] Monitoring commands work
   - [ ] Stats are accurate
   - [ ] CLI tests pass

---

## Phase 6: Documentation & Examples

**Objective**: Comprehensive documentation and example implementations

**Duration**: ~4 hours

**Tasks**:
1. Write user guide for call_service
2. Document service registry format
3. Create example: Email notifications
4. Create example: Payment processing
5. Create example: Webhook handling
6. Write worker implementation guide
7. Document observability dashboard

**Files to Create**:
- `docs/features/EXTERNAL_SERVICES.md` - User guide
- `docs/architecture/EXTERNAL_SERVICES_ARCHITECTURE.md` - Technical design
- `examples/call_service/` - Example implementations
- `docs/guides/WORKER_IMPLEMENTATION.md` - Worker setup

---

## Success Criteria

### Phase 1 Complete When:
- [ ] Service registry loads and validates
- [ ] call_service steps parse correctly
- [ ] Jobs schema generates
- [ ] All unit tests pass

### Phase 2 Complete When:
- [ ] call_service compiles to SQL
- [ ] Callback functions generate
- [ ] Full action with service calls works
- [ ] Integration tests pass

### Phase 3 Complete When:
- [ ] Idempotency works (no duplicate jobs)
- [ ] Retry configuration respected
- [ ] Observability views functional
- [ ] All tests pass

### Phase 4 Complete When:
- [ ] Service call metadata in mutations
- [ ] TypeScript types generated
- [ ] Frontend can track jobs
- [ ] Type generation tests pass

### Phase 5 Complete When:
- [ ] CLI commands work
- [ ] Job monitoring functional
- [ ] Service management easy
- [ ] CLI tests pass

### Phase 6 Complete When:
- [ ] Documentation complete
- [ ] Examples work
- [ ] Worker guide clear
- [ ] Ready for production use

---

## Testing Strategy

### Unit Tests
- Service registry parsing
- call_service step parsing
- Job schema generation
- Step compilation
- Callback generation

### Integration Tests
- Full action with call_service
- Job insertion
- Callback execution
- Idempotency enforcement
- Retry logic

### E2E Tests (Future)
- Real service calls
- Worker processing
- Full lifecycle test

---

## Technical Decisions

### 1. Async by Default
**Decision**: call_service is async unless explicitly set to sync
**Reasoning**:
- External calls shouldn't block mutations
- Better user experience (instant response)
- Easier to add sync later than remove it

### 2. Callbacks in Database
**Decision**: Store callbacks as PL/pgSQL functions, not in application
**Reasoning**:
- Consistency with SpecQL architecture
- Database guarantees execution
- No application state to manage

### 3. Job Queue in PostgreSQL
**Decision**: Use PostgreSQL table for job queue, not external system
**Reasoning**:
- Simplicity (no additional infrastructure)
- Transactional consistency
- Easy to query and monitor
- Can move to Temporal/Inngest later if needed

### 4. Service Registry YAML
**Decision**: Services defined in YAML, not database
**Reasoning**:
- Version controlled
- Easy to review changes
- Consistent with domain registry pattern

### 5. Idempotency via identifier
**Decision**: Use unique identifier field, not application logic
**Reasoning**:
- Database enforces uniqueness
- No race conditions
- Simple to implement

---

## Migration Path

### For Existing SpecQL Users:
1. No breaking changes
2. call_service is additive feature
3. Jobs schema optional (only if services used)
4. Can adopt incrementally

### For New Users:
1. Service registry comes with framework
2. Common services pre-configured (sendgrid, stripe, etc.)
3. Add API keys to environment
4. Start using call_service immediately

---

## Dependencies

### New Dependencies (if any):
- None for core functionality
- Worker implementation may need: `requests`, `httpx` for HTTP calls

### Internal Dependencies:
- Team A: Parser (for call_service parsing)
- Team B: Schema generator (for jobs schema)
- Team C: Action compiler (for step compilation)
- Team D: FraiseQL (for metadata)
- Team E: CLI (for service management)

---

## Risks & Mitigations

### Risk 1: Worker Implementation Complexity
**Mitigation**: Provide simple reference worker, document clearly

### Risk 2: Job Queue Performance
**Mitigation**: Proper indexes, partitioning strategy documented

### Risk 3: Service Registry Maintenance
**Mitigation**: Community contributions, clear extension guide

### Risk 4: Callback Execution Failures
**Mitigation**: Proper error handling, dead letter queue pattern

---

## Future Enhancements (Post-MVP)

1. **Saga Pattern Support**: Multi-service transactions with compensation
2. **Worker SDK**: Official Python/Node worker libraries
3. **Temporal Integration**: Optional Temporal.io backend
4. **Service Mocking**: Built-in mock services for testing
5. **Rate Limiting**: Per-service rate limit configuration
6. **Webhook Receiver**: Built-in webhook endpoint generation
7. **Service Discovery**: Auto-discover services from OpenAPI specs

---

## Timeline Estimate

| Phase | Duration | Team | Dependencies |
|-------|----------|------|--------------|
| Phase 1 | 8 hours | A, B | None |
| Phase 2 | 12 hours | C | Phase 1 |
| Phase 3 | 8 hours | B, C | Phase 2 |
| Phase 4 | 6 hours | D | Phase 2 |
| Phase 5 | 4 hours | E | Phase 1 |
| Phase 6 | 4 hours | All | Phase 5 |
| **Total** | **42 hours** (~1 week) | | |

---

## Getting Started (After Implementation)

```yaml
# 1. Define service in registry (or use built-in)
# registry/service_registry.yaml already has sendgrid, stripe

# 2. Add call_service to your action
entity: Order
actions:
  - name: place_order
    steps:
      - insert: Order
        as: order
      - call_service:
          service: stripe
          operation: create_charge
          input:
            amount: $order.total
          on_success:
            - update: Order SET status = 'paid'

# 3. Generate schema
specql generate entities/order.yaml

# 4. Deploy to PostgreSQL
psql -f db/schema/generated.sql

# 5. Run worker (simple Python script)
python workers/job_processor.py

# 6. Test!
```

---

**Status**: Ready for Phase 1 implementation
**Next Step**: Begin Phase 1 - TDD Cycle 1.1 (Service Registry Parser)
