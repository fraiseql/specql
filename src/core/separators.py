"""Separator constants for identifier generation."""


class Separators:
    """Identifier separator constants.

    Four-level hierarchy:
    1. TENANT (|): Separates tenant from entity identifier
    2. HIERARCHY (.): Separates parent from child within one tree
    3. COMPOSITION (∘): Combines identifiers from different hierarchies
    4. INTERNAL (—): Separates flat components within one entity

    Examples:
        Simple:       acme-corp|coffee-maker
        Hierarchical: acme-corp|warehouse.floor1.room101
        Composite:    acme-corp|2025-Q1∘machine.child∘location.child
        Internal:     acme-corp|router—gateway—ip
    """

    # Level 1: Tenant scoping
    TENANT = "|"

    # Level 2: Hierarchy depth (within single tree)
    HIERARCHY = "."
    HIERARCHY_LEGACY = "_"  # Legacy support (old default was underscore)

    # Level 3: Cross-hierarchy composition
    COMPOSITION = "∘"  # U+2218 Ring Operator
    COMPOSITION_FALLBACK = "~"  # If ∘ causes encoding issues

    # Level 4: Intra-entity flat components
    INTERNAL = "—"  # U+2014 Em Dash

    # Other separators
    DEDUPLICATION = "#"
    ORDERING = "-"


# Default separator configuration
DEFAULT_SEPARATORS = {
    "tenant": Separators.TENANT,
    "hierarchy": Separators.HIERARCHY,
    "composition": Separators.COMPOSITION,
    "internal": Separators.INTERNAL,
    "deduplication": Separators.DEDUPLICATION,
    "ordering": Separators.ORDERING,
}


def strip_tenant_prefix(identifier: str, tenant_identifier: str) -> str:
    """Strip tenant prefix from identifier.

    Args:
        identifier: Full identifier (e.g., "acme-corp|warehouse.floor1")
        tenant_identifier: Tenant identifier (e.g., "acme-corp")

    Returns:
        Identifier without tenant prefix (e.g., "warehouse.floor1")

    Examples:
        >>> strip_tenant_prefix("acme-corp|warehouse.floor1", "acme-corp")
        'warehouse.floor1'
        >>> strip_tenant_prefix("no-prefix", "acme-corp")
        'no-prefix'
    """
    prefix = f"{tenant_identifier}{Separators.TENANT}"
    if identifier.startswith(prefix):
        return identifier[len(prefix) :]
    return identifier


def join_with_composition(components: list[str]) -> str:
    """Join components with composition separator.

    Args:
        components: List of identifier components

    Returns:
        Joined identifier

    Examples:
        >>> join_with_composition(["2025-Q1", "machine.child", "location.parent"])
        '2025-Q1∘machine.child∘location.parent'
    """
    return Separators.COMPOSITION.join(components)


def split_composition(identifier: str) -> list[str]:
    """Split identifier by composition separator.

    Args:
        identifier: Composite identifier

    Returns:
        List of components

    Examples:
        >>> split_composition("2025-Q1∘machine∘location")
        ['2025-Q1', 'machine', 'location']
    """
    return identifier.split(Separators.COMPOSITION)
