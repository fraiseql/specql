"""Call Service Step Compiler

Compiles 'call_service' steps to PL/pgSQL INSERT statements that queue jobs for external service calls.

Example SpecQL:
    - call_service:
        service: stripe
        operation: create_charge
        input:
          amount: $order.total

Generated PL/pgSQL:
    -- Queue job for stripe.create_charge
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
        'order_' || _order.id::text || '_stripe_create_charge',
        'stripe',
        'create_charge',
        jsonb_build_object('amount', _order.total),
        _tenant_id,
        _user_id,
        _order.id::text,
        'Order',
        _order.id
    ) RETURNING id INTO _job_id_stripe_create_charge;
"""

from typing import Any

from src.core.ast_models import ActionStep
from src.generators.actions.action_context import ActionContext
from src.registry.service_registry import ServiceRegistry


class CallServiceStepCompiler:
    """Compiles call_service steps to PL/pgSQL job queueing"""

    def __init__(self, step: ActionStep, context: ActionContext, service_registry: ServiceRegistry):
        self.step = step
        self.context = context
        self.service_registry = service_registry

    def get_execution_type(self) -> str:
        """Get execution type for the service from registry"""
        service = self.service_registry.get_service(self.step.service)
        return service.execution_type.name

    def compile(self) -> str:
        """Compile call_service step to INSERT INTO jobs.tb_job_run"""
        self._validate_step()

        return f"""
        -- Queue job for {self.step.service}.{self.step.operation}
        INSERT INTO jobs.tb_job_run (
            identifier,
            idempotency_key,
            service_name,
            operation,
            input_data,
            tenant_id,
            triggered_by,
            correlation_id,
            entity_type,
            entity_pk,
            max_attempts,
            timeout_seconds,
            execution_type,
            runner_config,
            security_context
        ) VALUES (
            {self._generate_identifier()},
            {self._generate_idempotency_key()},
            '{self.step.service}',
            '{self.step.operation}',
            {self._compile_input_data()},
            _tenant_id,
            _user_id,
            {self._compile_correlation()},
            '{self.context.entity_name}',
            {self._compile_entity_pk()},
            {self._compile_max_attempts()},
            {self._compile_timeout()},
            '{self.get_execution_type()}',
            {self._compile_runner_config()},
            {self._compile_security_context()}
        ) RETURNING id INTO _job_id_{self._job_var_suffix()};
        """

    def _validate_step(self) -> None:
        """Validate call_service step has required fields"""
        if self.step.type != "call_service":
            raise ValueError(f"Expected call_service step, got {self.step.type}")

        if not self.step.service:
            raise ValueError("call_service step missing service name")

        if not self.step.operation:
            raise ValueError("call_service step missing operation name")

    def _generate_identifier(self) -> str:
        """Generate idempotent identifier for job deduplication"""
        entity_var = f"_{self.context.entity_name.lower()}"
        # Format: EntityName_PK_Service_Operation
        return f"""
        '{self.context.entity_name}_' ||
        {entity_var}.id::text ||
        '_{self.step.service}_{self.step.operation}'
        """.strip()

    def _generate_idempotency_key(self) -> str:
        """Generate idempotency key for duplicate prevention"""
        entity_var = f"_{self.context.entity_name.lower()}"
        # Use same format as identifier for now
        return f"""
        '{self.context.entity_name}_' ||
        {entity_var}.id::text ||
        '_{self.step.service}_{self.step.operation}'
        """.strip()

    def _compile_input_data(self) -> str:
        """Compile input data to JSONB"""
        if not self.step.input:
            return "'{}'::jsonb"

        # Compile key-value pairs for jsonb_build_object
        pairs = []
        for key, value in self.step.input.items():
            compiled_value = self._compile_input_value(value)
            pairs.append(f"'{key}', {compiled_value}")

        return f"jsonb_build_object({', '.join(pairs)})"

    def _compile_input_value(self, value: Any) -> str:
        """Compile a single input value"""
        if isinstance(value, str):
            if value.startswith("$"):
                # Handle variable references like $order.total
                return self._compile_variable_reference(value)
            else:
                # String literal
                return f"'{value}'"
        elif isinstance(value, (int, float)):
            # Numeric literal
            return str(value)
        elif isinstance(value, bool):
            # Boolean literal
            return "true" if value else "false"
        else:
            # For complex types, convert to string representation
            return f"'{str(value)}'"

    def _compile_variable_reference(self, var_ref: str) -> str:
        """Compile variable reference like $order.total"""
        if not var_ref.startswith("$"):
            raise ValueError(f"Expected variable reference starting with $, got {var_ref}")

        var_path = var_ref[1:]  # Remove $
        parts = var_path.split(".")

        if len(parts) != 2:
            raise ValueError(f"Expected entity.field format, got {var_path}")

        entity_name, field_name = parts
        entity_var = f"_{entity_name.lower()}"

        return f"{entity_var}.{field_name}"

    def _compile_correlation(self) -> str:
        """Compile correlation ID"""
        entity_var = f"_{self.context.entity_name.lower()}"
        return f"{entity_var}.id::text"

    def _compile_entity_pk(self) -> str:
        """Compile entity primary key"""
        entity_var = f"_{self.context.entity_name.lower()}"
        return f"{entity_var}.id"

    def _compile_max_attempts(self) -> str:
        """Compile max_attempts value"""
        if self.step.max_retries is not None:
            # max_attempts = max_retries + 1 (for initial attempt)
            return str(self.step.max_retries + 1)
        else:
            # Default to 3 attempts
            return "3"

    def _compile_timeout(self) -> str:
        """Compile timeout_seconds value"""
        if self.step.timeout is not None:
            return str(self.step.timeout)
        else:
            # Default to 300 seconds (5 minutes)
            return "300"

    def _compile_runner_config(self) -> str:
        """Compile runner configuration to JSONB"""
        service = self.service_registry.get_service(self.step.service)
        if service.runner_config:
            # Convert dict to JSONB literal
            pairs = []
            for key, value in service.runner_config.items():
                if isinstance(value, bool):
                    pairs.append(f"'{key}', {'true' if value else 'false'}")
                elif isinstance(value, str):
                    pairs.append(f"'{key}', '{value}'")
                elif isinstance(value, (int, float)):
                    pairs.append(f"'{key}', {value}")
                else:
                    # For complex types, convert to string
                    pairs.append(f"'{key}', '{str(value)}'")
            return f"jsonb_build_object({', '.join(pairs)})"
        else:
            return "'{}'::jsonb"

    def _compile_security_context(self) -> str:
        """Compile security context to JSONB"""
        service = self.service_registry.get_service(self.step.service)
        if service.security_policy:
            # Convert dict to JSONB literal
            pairs = []
            for key, value in service.security_policy.items():
                if isinstance(value, bool):
                    pairs.append(f"'{key}', {'true' if value else 'false'}")
                elif isinstance(value, str):
                    pairs.append(f"'{key}', '{value}'")
                elif isinstance(value, (int, float)):
                    pairs.append(f"'{key}', {value}")
                else:
                    # For complex types, convert to string
                    pairs.append(f"'{key}', '{str(value)}'")
            return f"jsonb_build_object({', '.join(pairs)})"
        else:
            return "'{}'::jsonb"

    def _job_var_suffix(self) -> str:
        """Generate unique suffix for job variables"""
        return f"{self.step.service}_{self.step.operation}".replace("_", "")
