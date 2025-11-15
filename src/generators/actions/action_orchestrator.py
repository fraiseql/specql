"""
Action Orchestrator

Coordinates complex actions involving multiple entities within transactions.
Handles multi-entity operations, side effects, and transaction management.
"""

from typing import Any

from src.core.ast_models import ActionDefinition, EntityDefinition
from src.utils.logger import LogContext, get_team_logger
from src.utils.safe_slug import safe_slug, safe_table_name


class ActionOrchestrator:
    """Orchestrate complex actions involving multiple entities"""

    def __init__(self, step_compiler_registry=None):
        """
        Initialize with step compiler registry

        Args:
            step_compiler_registry: Dict mapping step types to compilers
        """
        self.logger = get_team_logger("Team C", __name__)
        self.step_compiler_registry = step_compiler_registry or {}
        self.logger.debug("ActionOrchestrator initialized")

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
        context = LogContext(
            entity_name=primary_entity.name,
            schema=primary_entity.schema,
            action_name=action.name,
            operation="compile_action"
        )
        logger = get_team_logger("Team C", __name__, context)
        logger.info(f"Compiling multi-entity action '{action.name}' for entity '{primary_entity.name}'")

        # Build function signature
        function_name = f"{primary_entity.schema}.{action.name}"
        params = self._build_function_parameters(action, primary_entity)

        # Compile action steps
        logger.debug(f"Compiling {len(action.steps)} action steps")
        compiled_steps = self._compile_action_steps(action, primary_entity, related_entities)

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

        logger.info(f"Successfully compiled action '{action.name}' ({len(action.steps)} steps)")
        return function_sql

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
                compiled_parts.append(self._compile_primary_insert(step, primary_entity))
            elif step.type == "insert" and step.entity:
                # Related entity insert
                related_entity = self._find_entity_by_name(step.entity, related_entities)
                if related_entity:
                    compiled_parts.append(self._compile_related_insert(step, related_entity))
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
            return foreach_compiler.compile(step, entity, {})
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
