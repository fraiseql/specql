"""
Notify Step Compiler

Compiles 'notify' steps to PL/pgSQL event emission.

Example SpecQL:
    - notify: owner(email, "Contact qualified")

Generated PL/pgSQL:
    -- Notify: owner via email
    PERFORM app.emit_event(
        p_tenant_id := auth_tenant_id,
        p_event_type := 'notification.email',
        p_payload := jsonb_build_object(
            'recipient', owner_email,
            'channel', 'email',
            'message', 'Contact qualified',
            'entity', 'contact',
            'entity_id', v_contact_id
        )
    );
"""

from src.core.ast_models import ActionStep, EntityDefinition


class NotifyStepCompiler:
    """Compiles notify steps to PL/pgSQL event emission"""

    def compile(self, step: ActionStep, entity: EntityDefinition, context: dict) -> str:
        """
        Compile notify step to PL/pgSQL

        Args:
            step: ActionStep with type='notify'
            entity: EntityDefinition for table/schema context
            context: Compilation context (variables, etc.)

        Returns:
            PL/pgSQL code for event emission
        """
        if step.type != "notify":
            raise ValueError(f"Expected notify step, got {step.type}")

        # Parse notification spec
        recipient, channel, message = self._parse_notification(step, entity)

        # Build payload
        payload = self._build_payload(recipient, channel, message, entity, context)

        return f"""
    -- Notify: {recipient} via {channel}
    PERFORM app.emit_event(
        p_tenant_id := auth_tenant_id,
        p_event_type := 'notification.{channel}',
        p_payload := {payload}
    );
"""

    def _parse_notification(
        self, step: ActionStep, entity: EntityDefinition
    ) -> tuple[str, str, str]:
        """
        Parse notification specification

        Uses arguments dict for notify parameters:
        arguments: {"recipient": "user", "channel": "email", "message": "Contact updated"}

        Returns:
            (recipient, channel, message)
        """
        args = step.arguments or {}

        recipient = args.get("recipient", "user")
        channel = args.get("channel", "email")
        message = args.get("message", f"{entity.name} updated")

        return recipient, channel, message

    def _build_payload(
        self, recipient: str, channel: str, message: str, entity: EntityDefinition, context: dict
    ) -> str:
        """
        Build JSON payload for the event

        Example:
            jsonb_build_object(
                'recipient', owner_email,
                'channel', 'email',
                'message', 'Contact qualified',
                'entity', 'contact',
                'entity_id', v_contact_id
            )
        """
        entity_lower = entity.name.lower()
        entity_id_var = f"v_{entity_lower}_id"

        # Build payload object
        payload_parts = [
            "'recipient'",
            recipient,
            "'channel'",
            f"'{channel}'",
            "'message'",
            f"'{message}'",
            "'entity'",
            f"'{entity_lower}'",
            "'entity_id'",
            entity_id_var,
        ]

        # Add any additional context
        if context.get("operation"):
            payload_parts.extend(["'operation'", f"'{context['operation']}'"])

        # Convert to jsonb_build_object call
        args_str = ", ".join(f"{k}, {v}" for k, v in zip(payload_parts[::2], payload_parts[1::2]))

        return f"jsonb_build_object({args_str})"
