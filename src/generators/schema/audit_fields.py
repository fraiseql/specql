"""Audit field generation with separate recalculation tracking."""

from src.core.ast_models import EntityDefinition


def generate_audit_fields(
    entity: EntityDefinition | None = None, is_hierarchical: bool = False
) -> str:
    """Generate audit fields with separate recalculation tracking.

    Args:
        entity: Entity definition (optional, for future extensibility)
        is_hierarchical: Whether entity has hierarchical relationships

    Returns:
        SQL DDL for audit fields

    The audit fields are separated into three categories:
    1. Business Data Audit: For user-initiated changes
    2. Identifier Recalculation Audit: For system-generated identifier changes
    3. Path Recalculation Audit: For system-generated path changes (hierarchical only)
    """
    audit_fields = []

    # Business Data Audit (user-initiated changes)
    audit_fields.extend(
        [
            "    -- Business Data Audit",
            "    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),",
            "    created_by UUID,",
            "    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),",
            "    updated_by UUID,",
            "    deleted_at TIMESTAMPTZ,",
            "    deleted_by UUID,",
        ]
    )

    # Identifier Recalculation Audit (system-generated identifier changes)
    audit_fields.extend(
        [
            "",
            "    -- Identifier Recalculation Audit (separate from business changes)",
            "    identifier_recalculated_at TIMESTAMPTZ,",
            "    identifier_recalculated_by UUID,",
        ]
    )

    # Path Recalculation Audit (for hierarchical entities only)
    if is_hierarchical:
        audit_fields.extend(
            [
                "",
                "    -- Path Recalculation Audit (for hierarchical entities)",
                "    path_updated_at TIMESTAMPTZ,",
                "    path_updated_by UUID",
            ]
        )
    else:
        # Remove trailing comma from last identifier field
        audit_fields[-1] = audit_fields[-1].rstrip(",")

    return "\n".join(audit_fields)


def generate_business_audit_update(user_id_field: str = "current_user_id") -> str:
    """Generate SQL snippet for business data audit update.

    Example usage:
        UPDATE tb_location SET
            name = 'New Name',
            {business_audit_update}
        WHERE pk_location = 123;
    """
    return f"""updated_at = now(),
    updated_by = {user_id_field}"""


def generate_identifier_recalculation_audit(system_user_field: str = "system_user_id") -> str:
    """Generate SQL snippet for identifier recalculation audit update.

    Example usage:
        UPDATE tb_location SET
            identifier = new_identifier,
            {identifier_recalculation_audit}
        WHERE pk_location = 123;
    """
    return f"""identifier_recalculated_at = now(),
    identifier_recalculated_by = {system_user_field}"""


def generate_path_recalculation_audit(system_user_field: str = "system_user_id") -> str:
    """Generate SQL snippet for path recalculation audit update.

    Example usage:
        UPDATE tb_location SET
            path = new_path,
            {path_recalculation_audit}
        WHERE pk_location = 123;
    """
    return f"""path_updated_at = now(),
    path_updated_by = {system_user_field}"""
