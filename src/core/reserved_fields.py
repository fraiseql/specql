"""Reserved field names that cannot be used by end users."""

# Primary Keys & Foreign Keys
RESERVED_PK_FK = {
    "id",  # UUID external reference
    "tenant_id",  # Multi-tenant reference
}

# Deduplication Fields
RESERVED_DEDUPLICATION = {
    "identifier",  # Base identifier
    "sequence_number",  # Deduplication sequence
    "display_identifier",  # Computed identifier with #n suffix
}

# Hierarchy Fields (for hierarchical entities)
RESERVED_HIERARCHY = {
    "path",  # LTREE path (INTEGER-based)
}

# Audit Fields
RESERVED_AUDIT = {
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "deleted_at",
    "deleted_by",
}

# Recalculation Audit
RESERVED_RECALCULATION_AUDIT = {
    "identifier_recalculated_at",
    "identifier_recalculated_by",
    "path_updated_at",
    "path_updated_by",
}

# Combine all reserved names
RESERVED_FIELD_NAMES: set[str] = (
    RESERVED_PK_FK
    | RESERVED_DEDUPLICATION
    | RESERVED_HIERARCHY
    | RESERVED_AUDIT
    | RESERVED_RECALCULATION_AUDIT
)

# Reserved prefixes (dynamic naming)
RESERVED_PREFIXES = {
    "pk_",  # Primary keys: pk_location, pk_contact, etc.
    "fk_",  # Foreign keys: fk_parent_location, fk_company, etc.
}


def is_reserved_field_name(field_name: str) -> bool:
    """Check if a field name is reserved by the framework."""
    # Check exact matches
    if field_name in RESERVED_FIELD_NAMES:
        return True

    # Check prefixes
    for prefix in RESERVED_PREFIXES:
        if field_name.startswith(prefix):
            return True

    return False


def get_reserved_field_error_message(field_name: str) -> str:
    """Generate helpful error message for reserved field names."""
    return f"""
Field name '{field_name}' is reserved by the framework.

Reserved fields:
  - Primary/Foreign Keys: id, pk_*, fk_*, tenant_id
  - Deduplication: identifier, sequence_number, display_identifier
  - Hierarchy: path, fk_parent_*
  - Audit: created_at, updated_at, deleted_at, created_by, updated_by, deleted_by
  - Recalculation: identifier_recalculated_at, path_updated_at, etc.

Please choose a different field name.
""".strip()
