"""
Action Orchestrator

Coordinates complex actions involving multiple entities within transactions.
Handles multi-entity operations, side effects, and transaction management.
"""

from typing import Any

from src.core.ast_models import ActionDefinition, EntityDefinition
from src.core.specql_parser import SpecQLParser
from src.generators.actions.action_context import ActionContext
from src.generators.actions.callback_generator import CallbackGenerator
from src.generators.actions.step_compilers import (
    AggregateStepCompiler,
    CallFunctionStepCompiler,
    CallStepCompiler,
    CTEStepCompiler,
    DeclareStepCompiler,
    DeleteStepCompiler,
    DuplicateCheckCompiler,
    ForEachStepCompiler,
    IfStepCompiler,
    InsertStepCompiler,
    NotifyStepCompiler,
    PartialUpdateCompiler,
    RefreshTableViewStepCompiler,
    ReturnEarlyStepCompiler,
    SubqueryStepCompiler,
    SwitchStepCompiler,
    UpdateStepCompiler,
    ValidateStepCompiler,
)
from src.generators.actions.step_compilers.call_service_step_compiler import (
    CallServiceStepCompiler,
)
from src.utils.safe_slug import safe_slug, safe_table_name


class ActionOrchestrator:
    """Orchestrate complex actions involving multiple entities"""

    def __init__(
        self,
        step_compiler_registry=None,
        entity=None,
        yaml_content=None,
        service_registry=None,
    ) -> None:
        """
        Initialize with step compiler registry

        Args:
            step_compiler_registry: Dict mapping step types to compilers
            entity: Parsed entity (for from_yaml)
            yaml_content: Original YAML content
            service_registry: Service registry for call_service steps
        """
        self.step_compiler_registry = step_compiler_registry or {}
        self.entity = entity
        self.yaml_content = yaml_content
        self.service_registry = service_registry

    @classmethod
    def from_yaml(
        cls, yaml_content: str, service_registry=None
    ) -> "ActionOrchestrator":
        """
        Create ActionOrchestrator from SpecQL YAML content

        Args:
            yaml_content: SpecQL YAML string
            service_registry: Service registry for call_service steps

        Returns:
            ActionOrchestrator instance
        """
        # Parse the YAML to get entities and actions
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        # Create default step compiler registry
        default_registry = {
            "validate": ValidateStepCompiler(),
            "update": UpdateStepCompiler(),
            "insert": InsertStepCompiler(),
            "delete": DeleteStepCompiler(),
            "duplicate_check": DuplicateCheckCompiler(),
            "if": IfStepCompiler(),
            "foreach": ForEachStepCompiler(),
            "call": CallStepCompiler(),
            "notify": NotifyStepCompiler(),
            "partial_update": PartialUpdateCompiler(),
            "refresh_table_view": RefreshTableViewStepCompiler(),
            "declare": DeclareStepCompiler(),
            "cte": CTEStepCompiler(),
            "aggregate": AggregateStepCompiler(),
            "subquery": SubqueryStepCompiler(),
            "call_function": CallFunctionStepCompiler(),
            "switch": SwitchStepCompiler(),
            "return_early": ReturnEarlyStepCompiler(),
        }

        # Create orchestrator with call_service step compiler and default registry
        orchestrator = cls(
            service_registry=service_registry, step_compiler_registry=default_registry
        )
        orchestrator.entity = entity
        orchestrator.yaml_content = yaml_content

        return orchestrator

    def generate(self) -> str:
        """
        Generate complete action SQL including call_service compilation

        Returns:
            Complete PL/pgSQL for all actions in the entity
        """
        if not hasattr(self, "entity"):
            raise ValueError("ActionOrchestrator not initialized with from_yaml")

        # Compile all actions for the entity
        if not self.entity or not self.entity.actions:
            raise ValueError("No actions found in entity")

        compiled_actions = []
        for action in self.entity.actions:
            try:
                compiled_action = self._compile_single_action(action)
                compiled_actions.append(compiled_action)
            except Exception as e:
                # Log error but continue with other actions
                print(f"Failed to compile action {action.name}: {e}")
                raise

        # Combine all compiled actions
        return "\n\n".join(compiled_actions)

    def _compile_single_action(self, action: ActionDefinition) -> str:
        """
        Compile a single action to PL/pgSQL

        Args:
            action: Action definition to compile

        Returns:
            Complete PL/pgSQL function for the action
        """
        if not self.entity:
            raise ValueError("Entity not set in orchestrator")

        # Create action context
        context = ActionContext.from_ast(action, self.entity)

        # Compile all steps
        compiled_parts = []
        callback_functions = []

        for step in action.steps:
            if step.type == "insert":
                # Handle insert step
                compiled_parts.append(self._compile_simple_insert(step, self.entity))
            elif step.type == "call_service":
                # Handle call_service step
                compiled_parts.append(self._compile_call_service_step(step, context))
                # Generate callback functions
                callback_functions.extend(
                    self._generate_callback_functions(step, context)
                )
            else:
                # Use step compiler registry for other step types
                compiler = self.step_compiler_registry.get(step.type)
                if compiler:
                    compiled_parts.append(compiler.compile(step, self.entity, {}))
                else:
                    compiled_parts.append(
                        f"-- TODO: Compile {step.type} step (no compiler found)"
                    )

        # Build complete function
        function_sql = self._build_action_function(
            action, context, compiled_parts, callback_functions
        )

        return function_sql

    def compile_multi_entity_action(
        self,
        action: ActionDefinition,
        primary_entity: EntityDefinition,
        related_entities: list[EntityDefinition],
    ) -> str:
        """
        Compile actions that affect multiple entities within a transaction

        Args:
            action: The action definition
            primary_entity: The main entity being acted upon
            related_entities: Related entities involved in the action

        Returns:
            Complete PL/pgSQL function with transaction management

        Example:
          Action: create_reservation
            - Creates Reservation (primary)
            - Creates multiple Allocations (related)
            - Updates MachineItem statuses (side effects)
            - Sends notifications (side effects)
        """
        # Build function signature
        function_name = f"{primary_entity.schema}.{action.name}"
        params = self._build_function_parameters(action, primary_entity)

        # Compile action steps
        compiled_steps = self._compile_action_steps(
            action, primary_entity, related_entities
        )

        # Build complete function
        function_sql = f"""
CREATE OR REPLACE FUNCTION {function_name}({params})
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_result app.mutation_result;
    v_primary_id UUID;
BEGIN
    -- Start transaction
    BEGIN;

    {compiled_steps}

    -- Commit transaction
    COMMIT;

    -- Return success result
    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        -- Rollback on error
        ROLLBACK;

        -- Return error result
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            '{primary_entity.name.lower()}',
            COALESCE(v_primary_id, '00000000-0000-0000-0000-000000000000'::UUID),
            'ERROR',
            'failed:transaction_rollback',
            ARRAY[]::TEXT[],
            SQLERRM,
            NULL,
            jsonb_build_object('error_code', SQLSTATE, 'error_message', SQLERRM)
        );
END;
$$;
"""

        return function_sql

    def _compile_simple_insert(self, step: Any, entity: EntityDefinition) -> str:
        """Compile simple insert step"""
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        entity_var = f"_{entity.name.lower()}"
        return f"""
        -- Insert into {entity.name}
        {entity_var}.id := gen_random_uuid();

        INSERT INTO {table_name} (
            id,
            tenant_id,
            created_at,
            created_by
        ) VALUES (
            {entity_var}.id,
            auth_tenant_id,
            now(),
            auth_user_id
        ) RETURNING * INTO {entity_var};
        """

    def _compile_call_service_step(self, step: Any, context: ActionContext) -> str:
        """Compile call_service step using CallServiceStepCompiler"""
        if not self.service_registry:
            raise ValueError("Service registry required for call_service steps")
        compiler = CallServiceStepCompiler(step, context, self.service_registry)
        return compiler.compile()

    def _generate_callback_functions(
        self, step: Any, context: ActionContext
    ) -> list[str]:
        """Generate callback functions for call_service step"""
        generator = CallbackGenerator(step, context)
        callbacks = []

        success_callback = generator.generate_success_callback()
        if success_callback:
            callbacks.append(success_callback)

        failure_callback = generator.generate_failure_callback()
        if failure_callback:
            callbacks.append(failure_callback)

        return callbacks

    def _build_action_function(
        self,
        action: ActionDefinition,
        context: ActionContext,
        compiled_steps: list[str],
        callback_functions: list[str],
    ) -> str:
        """Build complete PL/pgSQL function"""
        function_name = context.function_name
        steps_sql = "\n\n".join(compiled_steps)
        callbacks_sql = "\n\n".join(callback_functions)

        # Find job variables from compiled steps
        job_vars = self._extract_job_variables(compiled_steps)

        # Build response with job_id
        if job_vars:
            response_sql = f"""
        -- Return success with job_id
        RETURN jsonb_build_object(
            'success', true,
            'job_id', {job_vars[0]}
        );
        """
        else:
            response_sql = """
        -- Return success
        RETURN jsonb_build_object('success', true);
        """

        # Build function parameters dynamically
        params = self._build_action_parameters(action, context)

        # Declare entity variable
        entity_var_decl = f"    _{context.entity_name.lower()} RECORD;"

        function_sql = f"""
-- Callback functions
{callbacks_sql}

-- Main action function
CREATE OR REPLACE FUNCTION {function_name}({params})
RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_result app.mutation_result;
{entity_var_decl}
    {self._declare_job_variables(job_vars)}
BEGIN
    -- Set up variables for step compilers
    _tenant_id := auth_tenant_id;
    _user_id := auth_user_id;

    -- Start transaction
    BEGIN;

    {steps_sql}

    -- Commit transaction
    COMMIT;

    {response_sql}

EXCEPTION
    WHEN OTHERS THEN
        -- Rollback on error
        ROLLBACK;

        -- Return error result
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            '{context.entity_name}',
            COALESCE(_{context.entity_name.lower()}.id, '00000000-0000-0000-0000-000000000000'::UUID),
            'ERROR',
            'failed:transaction_rollback',
            ARRAY[]::TEXT[],
            SQLERRM,
            NULL,
            jsonb_build_object('error_code', SQLSTATE, 'error_message', SQLERRM)
        );
END;
$$;
"""

        return function_sql

    def _extract_job_variables(self, compiled_steps: list[str]) -> list[str]:
        """Extract job variable names from compiled steps"""
        job_vars = []
        for step in compiled_steps:
            # Look for RETURNING id INTO _job_id_... pattern
            if "RETURNING id INTO" in step:
                lines = step.split("\n")
                for line in lines:
                    if "RETURNING id INTO" in line:
                        # Extract variable name
                        var_part = line.split("RETURNING id INTO")[1].strip()
                        var_name = var_part.split(";")[0].strip()
                        job_vars.append(var_name)
                        break
        return job_vars

    def _declare_job_variables(self, job_vars: list[str]) -> str:
        """Declare job variables in function"""
        if not job_vars:
            return ""
        declarations = [f"    {var} UUID;" for var in job_vars]
        return "\n".join(declarations)

    def _build_action_parameters(
        self, action: ActionDefinition, context: ActionContext
    ) -> str:
        """Build function parameters dynamically"""
        # Use parameter names expected by step compilers
        return """auth_tenant_id UUID,
    input_data app.type_create_order_input,
    input_payload JSONB,
    auth_user_id UUID"""

    def _build_function_parameters(
        self, action: ActionDefinition, primary_entity: EntityDefinition
    ) -> str:
        """
        Build function parameter list

        Args:
            action: Action definition
            primary_entity: Primary entity

        Returns:
            Parameter string for function signature
        """
        params = [
            "auth_tenant_id UUID",
            "input_data app.type_create_reservation_input",  # TODO: Make dynamic based on action
            "input_payload JSONB",
            "auth_user_id UUID",
        ]

        return ", ".join(params)

    def _compile_action_steps(
        self,
        action: ActionDefinition,
        primary_entity: EntityDefinition,
        related_entities: list[EntityDefinition],
    ) -> str:
        """
        Compile all steps in the action

        Args:
            action: Action definition
            primary_entity: Primary entity
            related_entities: Related entities

        Returns:
            Compiled PL/pgSQL for all steps
        """
        compiled_parts = []

        for step in action.steps:
            if step.type == "insert" and step.entity == primary_entity.name:
                # Primary entity insert
                compiled_parts.append(
                    self._compile_primary_insert(step, primary_entity)
                )
            elif step.type == "insert" and step.entity:
                # Related entity insert
                related_entity = self._find_entity_by_name(
                    step.entity, related_entities
                )
                if related_entity:
                    compiled_parts.append(
                        self._compile_related_insert(step, related_entity)
                    )
            elif step.type == "update":
                # Update operation
                compiled_parts.append(self._compile_update_step(step, primary_entity))
            elif step.type == "foreach":
                # Iteration over collections
                compiled_parts.append(self._compile_foreach_step(step, primary_entity))
            elif step.type == "call":
                # Function call
                compiled_parts.append(self._compile_call_step(step))
            elif step.type == "notify":
                # Notification
                compiled_parts.append(self._compile_notify_step(step))
            else:
                # Use step compiler registry for other step types
                compiler = self.step_compiler_registry.get(step.type)
                if compiler:
                    compiled_parts.append(compiler.compile(step, primary_entity, {}))
                else:
                    raise ValueError(f"No compiler for step type: {step.type}")

        return "\n\n".join(compiled_parts)

    def _compile_primary_insert(self, step: Any, entity: EntityDefinition) -> str:
        """
        Compile insert for primary entity

        Args:
            step: Insert step
            entity: Primary entity

        Returns:
            PL/pgSQL for primary insert
        """
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        return f"""
    -- Primary insert: {entity.name}
    v_primary_id := gen_random_uuid();

    INSERT INTO {table_name} (
        id,
        tenant_id,
        -- TODO: Add other fields
        created_at,
        created_by
    ) VALUES (
        v_primary_id,
        auth_tenant_id,
        -- TODO: Map input fields
        now(),
        auth_user_id
    );"""

    def _compile_related_insert(self, step: Any, entity: EntityDefinition) -> str:
        """
        Compile insert for related entity

        Args:
            step: Insert step
            entity: Related entity

        Returns:
            PL/pgSQL for related insert
        """
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        return f"""
    -- Related insert: {entity.name}
    INSERT INTO {table_name} (
        id,
        tenant_id,
        fk_{safe_slug(entity.name)}_id,  -- Reference to primary entity
        -- TODO: Add other fields
        created_at,
        created_by
    ) VALUES (
        gen_random_uuid(),
        auth_tenant_id,
        v_primary_id,
        -- TODO: Map input fields
        now(),
        auth_user_id
    );"""

    def _compile_update_step(self, step: Any, entity: EntityDefinition) -> str:
        """
        Compile update step

        Args:
            step: Update step
            entity: Entity being updated

        Returns:
            PL/pgSQL for update
        """
        # Check if partial updates are requested (default: True)
        partial_updates = (
            step.fields.get("partial_updates", True) if step.fields else True
        )

        if partial_updates:
            # Use PartialUpdateCompiler for partial updates
            partial_compiler = self.step_compiler_registry.get("partial_update")
            if partial_compiler:
                return partial_compiler.compile(step, entity, {})  # type: ignore
            else:
                raise ValueError(
                    "PartialUpdateCompiler not registered but partial_updates requested"
                )

        # Fall back to regular update compiler or basic implementation
        update_compiler = self.step_compiler_registry.get("update")
        if update_compiler:
            return update_compiler.compile(step, entity, {})  # type: ignore

        # Basic fallback implementation
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        return f"""
    -- Update: {entity.name}
    UPDATE {table_name}
    SET
        -- TODO: Map update fields
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_primary_id
      AND tenant_id = auth_tenant_id;"""

    def _compile_foreach_step(self, step: Any, entity: EntityDefinition) -> str:
        """
        Compile foreach iteration step

        Args:
            step: Foreach step
            entity: Current entity context

        Returns:
            PL/pgSQL for iteration
        """
        # Use ForEachStepCompiler if available
        foreach_compiler = self.step_compiler_registry.get("foreach")
        if foreach_compiler:
            return foreach_compiler.compile(step, entity, {})  # type: ignore
        else:
            return f"-- TODO: Implement foreach compilation for {step.foreach_expr}"

    def _compile_call_step(self, step: Any) -> str:
        """
        Compile function call step

        Args:
            step: Call step

        Returns:
            PL/pgSQL for function call
        """
        return f"""
    -- Call: {step.function_name}
    -- TODO: Implement function call compilation"""

    def _compile_notify_step(self, step: Any) -> str:
        """
        Compile notification step

        Args:
            step: Notify step

        Returns:
            PL/pgSQL for notification
        """
        return f"""
    -- Notify: {step.recipient} via {step.channel}
    -- TODO: Implement notification compilation"""

    def _find_entity_by_name(
        self, name: str, entities: list[EntityDefinition]
    ) -> EntityDefinition | None:
        """
        Find entity by name

        Args:
            name: Entity name
            entities: List of entities to search

        Returns:
            Matching entity or None
        """
        for entity in entities:
            if entity.name == name:
                return entity
        return None
