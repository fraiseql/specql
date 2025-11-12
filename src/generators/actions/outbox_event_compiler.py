"""
Outbox Event Compiler

Generates code to write events to app.outbox table from action functions.
"""

from dataclasses import dataclass
from src.core.ast_models import Action, CDCConfig, Entity


@dataclass
class OutboxEventCompiler:
    """Compiles outbox event writes from action metadata"""

    def compile(self, action: Action, entity: Entity) -> str:
        """Generate outbox event write if CDC enabled"""
        if not action.cdc or not action.cdc.enabled:
            return ""

        cdc = action.cdc
        event_type = cdc.event_type or self._infer_event_type(action, entity)

        # Determine aggregate info
        aggregate_type = entity.name
        aggregate_id_var = f"v_{entity.name.lower()}_id"

        # Build event payload
        payload = self._build_event_payload(action, entity, cdc)

        # Build event metadata (includes cascade)
        metadata = self._build_event_metadata(action, cdc)

        return f"""
    -- Write CDC event to outbox
    v_event_id := app.write_outbox_event(
        '{aggregate_type}',
        {aggregate_id_var},
        '{event_type}',
        {payload},
        {metadata},
        p_tenant_id,  -- Tenant routing
        p_trace_id,   -- Distributed tracing
        gen_random_uuid()  -- Correlation ID
    );
"""

    def _infer_event_type(self, action: Action, entity: Entity) -> str:
        """Infer event type from action name"""
        # create_post → PostCreated
        # update_user → UserUpdated
        # delete_comment → CommentDeleted

        if action.impact and action.impact.primary:
            operation = action.impact.primary.operation
            if operation == "CREATE":
                return f"{entity.name}Created"
            elif operation == "UPDATE":
                return f"{entity.name}Updated"
            elif operation == "DELETE":
                return f"{entity.name}Deleted"

        # Fallback: PascalCase action name
        return ''.join(word.capitalize() for word in action.name.split('_'))

    def _build_event_payload(
        self, action: Action, entity: Entity, cdc: CDCConfig
    ) -> str:
        """Build event payload JSONB expression"""
        if not cdc.include_payload:
            return "'{}'"

        # Build from table (Entity doesn't have table view info)
        return f"""(
            SELECT row_to_json(t.*)::jsonb
            FROM {entity.schema}.tb_{entity.name.lower()} t
            WHERE id = v_{entity.name.lower()}_id
        )"""

    def _build_event_metadata(self, action: Action, cdc: CDCConfig) -> str:
        """Build event metadata including cascade"""
        parts = ["'{}'::jsonb"]

        if cdc.include_cascade and action.impact:
            parts = [f"""jsonb_build_object(
                'cascade', v_cascade_data,
                'mutation', '{action.name}',
                'affectedEntities', ARRAY(
                    SELECT jsonb_array_elements_text(
                        v_cascade_data->'updated'
                    )->>'__typename'
                )
            )"""]

        return parts[0]

    def declare_variables(self, action: Action) -> str:
        """Declare variables needed for outbox"""
        if not action.cdc or not action.cdc.enabled:
            return ""

        return "v_event_id UUID;"