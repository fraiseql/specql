"""Tests for call_service step compiler."""

from src.generators.actions.step_compilers.call_service_step_compiler import CallServiceStepCompiler
from src.core.ast_models import ActionStep
from src.generators.actions.action_context import ActionContext
from src.registry.service_registry import ServiceRegistry, Service, ServiceOperation
from src.runners.execution_types import ExecutionType


def test_compile_call_service_basic():
    """Compile call_service to INSERT INTO jobs.tb_job_run"""
    step = ActionStep(
        type="call_service",
        service="sendgrid",
        operation="send_email",
        input={"to": "$order.customer_email", "subject": "Receipt"},
    )

    # Mock context
    context = ActionContext(
        function_name="crm.send_receipt",
        entity_schema="crm",
        entity_name="Order",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    # Mock service registry
    service = Service(
        name="sendgrid",
        type="email",
        category="communication",
        operations=[ServiceOperation(name="send_email", input_schema={}, output_schema={})],
        execution_type=ExecutionType.HTTP,
        runner_config={},
        security_policy={},
    )
    service_registry = ServiceRegistry(services=[service])

    compiler = CallServiceStepCompiler(step, context, service_registry)
    sql = compiler.compile()

    assert "INSERT INTO jobs.tb_job_run" in sql
    assert "'sendgrid'" in sql
    assert "'send_email'" in sql
    assert "jsonb_build_object" in sql
    assert "_job_id_sendgridsendemail" in sql


def test_compile_service_input_expressions():
    """Compile input expressions to JSON"""
    step = ActionStep(
        type="call_service",
        service="stripe",
        operation="create_charge",
        input={"amount": "$order.total", "customer": "$order.customer_id"},
    )

    # Mock context
    context = ActionContext(
        function_name="crm.place_order",
        entity_schema="crm",
        entity_name="Order",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    # Mock service registry
    service = Service(
        name="stripe",
        type="payment",
        category="financial",
        operations=[ServiceOperation(name="create_charge", input_schema={}, output_schema={})],
        execution_type=ExecutionType.HTTP,
        runner_config={},
        security_policy={},
    )
    service_registry = ServiceRegistry(services=[service])

    compiler = CallServiceStepCompiler(step, context, service_registry)
    sql = compiler.compile()

    assert "_order.total" in sql  # Trinity resolution
    assert "_order.customer_id" in sql
    assert "_job_id_stripecreatecharge" in sql


def test_get_execution_type_http():
    """Test execution type detection for HTTP service"""
    step = ActionStep(
        type="call_service",
        service="stripe",
        operation="create_charge",
    )

    context = ActionContext(
        function_name="crm.place_order",
        entity_schema="crm",
        entity_name="Order",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    # Mock HTTP service
    service = Service(
        name="stripe",
        type="payment",
        category="financial",
        operations=[ServiceOperation(name="create_charge", input_schema={}, output_schema={})],
        execution_type=ExecutionType.HTTP,
        runner_config={},
        security_policy={},
    )
    service_registry = ServiceRegistry(services=[service])

    compiler = CallServiceStepCompiler(step, context, service_registry)
    execution_type = compiler.get_execution_type()

    assert execution_type == "HTTP"


def test_get_execution_type_shell():
    """Test execution type detection for shell script service"""
    step = ActionStep(
        type="call_service",
        service="backup_script",
        operation="run_backup",
    )

    context = ActionContext(
        function_name="admin.backup_data",
        entity_schema="admin",
        entity_name="BackupJob",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    # Mock shell service
    service = Service(
        name="backup_script",
        type="utility",
        category="infrastructure",
        operations=[ServiceOperation(name="run_backup", input_schema={}, output_schema={})],
        execution_type=ExecutionType.SHELL,
        runner_config={},
        security_policy={},
    )
    service_registry = ServiceRegistry(services=[service])

    compiler = CallServiceStepCompiler(step, context, service_registry)
    execution_type = compiler.get_execution_type()

    assert execution_type == "SHELL"


def test_get_execution_type_docker():
    """Test execution type detection for Docker service"""
    step = ActionStep(
        type="call_service",
        service="ml_model",
        operation="predict",
    )

    context = ActionContext(
        function_name="analytics.predict_outcome",
        entity_schema="analytics",
        entity_name="Prediction",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    # Mock Docker service
    service = Service(
        name="ml_model",
        type="ml",
        category="analytics",
        operations=[ServiceOperation(name="predict", input_schema={}, output_schema={})],
        execution_type=ExecutionType.DOCKER,
        runner_config={},
        security_policy={},
    )
    service_registry = ServiceRegistry(services=[service])

    compiler = CallServiceStepCompiler(step, context, service_registry)
    execution_type = compiler.get_execution_type()

    assert execution_type == "DOCKER"


def test_compile_includes_execution_type_columns():
    """Test that compiled SQL includes new execution type columns"""
    step = ActionStep(
        type="call_service",
        service="stripe",
        operation="create_charge",
        input={"amount": "$order.total"},
    )

    context = ActionContext(
        function_name="crm.place_order",
        entity_schema="crm",
        entity_name="Order",
        entity=None,
        steps=[],
        impact=None,
        has_impact_metadata=False,
    )

    # Mock service with runner config and security policy
    service = Service(
        name="stripe",
        type="payment",
        category="financial",
        operations=[ServiceOperation(name="create_charge", input_schema={}, output_schema={})],
        execution_type=ExecutionType.HTTP,
        runner_config={"api_key": "secret", "timeout": 30},
        security_policy={"allow_network": True, "max_retries": 3},
    )
    service_registry = ServiceRegistry(services=[service])

    compiler = CallServiceStepCompiler(step, context, service_registry)
    sql = compiler.compile()

    # Check that new columns are included in INSERT
    assert "execution_type" in sql
    assert "runner_config" in sql
    assert "security_context" in sql

    # Check that execution type value is correct
    assert "'HTTP'" in sql

    # Check that runner config is compiled to JSONB
    assert "jsonb_build_object" in sql
    assert "'api_key', 'secret'" in sql
    assert "'timeout', 30" in sql

    # Check that security context is compiled to JSONB
    assert "'allow_network', true" in sql
    assert "'max_retries', 3" in sql
