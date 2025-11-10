"""
AST Models for SpecQL Entities

Extended to support:
- Tier 1: Scalar rich types
- Tier 2: Composite types (JSONB)
- Tier 3: Entity references (FK)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# Import from scalar_types
from src.core.scalar_types import (
    CompositeTypeDef,
    ScalarTypeDef,
    get_scalar_type,
    is_composite_type,
    is_scalar_type,
)

# Import separators
from src.core.separators import Separators


class FieldTier(Enum):
    """Which tier this field belongs to"""

    BASIC = "basic"  # text, integer, etc.
    SCALAR = "scalar"  # email, money, etc. (Tier 1)
    COMPOSITE = "composite"  # SimpleAddress, MoneyAmount (Tier 2)
    REFERENCE = "reference"  # ref(Entity) (Tier 3)


class TableViewMode(Enum):
    """Mode for table view generation."""

    AUTO = "auto"  # Generate if has foreign keys
    FORCE = "force"  # Always generate
    DISABLE = "disable"  # Never generate


class RefreshScope(Enum):
    """Scope for table view refresh."""

    SELF = "self"  # Only this entity
    RELATED = "related"  # This entity + all that reference it
    PROPAGATE = "propagate"  # This entity + explicit list
    BATCH = "batch"  # Deferred refresh (bulk operations)


@dataclass
class IncludeRelation:
    """Specification for including a related entity in table view."""

    entity_name: str
    fields: list[str]  # Which fields to include from related entity
    include_relations: list["IncludeRelation"] = field(default_factory=list)  # Nested

    def __post_init__(self):
        """Validate field list."""
        if not self.fields:
            raise ValueError(f"include_relations.{self.entity_name} must specify fields")

        # Special case: '*' means all fields
        if self.fields == ["*"]:
            pass  # All fields, resolved during generation
        elif not all(isinstance(f, str) for f in self.fields):
            raise ValueError(f"Fields must be strings in {self.entity_name}")


@dataclass
class RefreshTableViewStep:
    """Action step for refreshing table views."""

    scope: RefreshScope = RefreshScope.SELF
    propagate: list[str] = field(default_factory=list)  # Entity names to refresh
    strategy: str = "immediate"  # immediate | deferred


@dataclass
class ExtraFilterColumn:
    """Extra filter column specification."""

    name: str
    source: str | None = None  # e.g., "author.name" for nested extraction
    type: str | None = None  # Explicit type override
    index_type: str = "btree"  # btree | gin | gin_trgm | gist

    @classmethod
    def from_string(cls, name: str) -> "ExtraFilterColumn":
        """Create from simple string (e.g., 'rating')."""
        return cls(name=name)

    @classmethod
    def from_dict(cls, name: str, config: dict) -> "ExtraFilterColumn":
        """Create from dict config (e.g., {source: 'author.name', type: 'text'})."""
        return cls(
            name=name,
            source=config.get("source"),
            type=config.get("type"),
            index_type=config.get("index", "btree"),
        )


@dataclass
class TableViewConfig:
    """Configuration for table view (tv_) generation."""

    # Generation mode
    mode: TableViewMode = TableViewMode.AUTO

    # Explicit relation inclusion
    include_relations: list[IncludeRelation] = field(default_factory=list)

    # Performance-optimized filter columns
    extra_filter_columns: list[ExtraFilterColumn] = field(default_factory=list)

    # Refresh strategy (always explicit for now)
    refresh: str = "explicit"

    @property
    def should_generate(self) -> bool:
        """Check if table view should be generated (resolved during generation)."""
        # This will be resolved by Team B based on mode and entity characteristics
        return self.mode != TableViewMode.DISABLE

    @property
    def has_explicit_relations(self) -> bool:
        """Check if explicit relations are specified."""
        return len(self.include_relations) > 0


@dataclass
class FieldDefinition:
    """Represents a field in an entity"""

    # Core attributes
    name: str
    type_name: str
    nullable: bool = True
    default: Any | None = None
    description: str = ""

    # Tier classification
    tier: FieldTier = FieldTier.BASIC

    # For enum fields
    values: list[str] | None = None

    # For list fields
    item_type: str | None = None

    # Tier 1: Scalar rich type metadata
    scalar_def: ScalarTypeDef | None = None

    # Tier 2: Composite type metadata (set in Phase 2)
    composite_def: Optional["CompositeTypeDef"] = None

    # Tier 3: Reference metadata (set in Phase 3)
    reference_entity: str | None = None
    reference_schema: str | None = None

    # PostgreSQL generation metadata (for Team B)
    postgres_type: str | None = None
    postgres_precision: tuple | None = None
    validation_pattern: str | None = None
    min_value: float | None = None
    max_value: float | None = None

    # FraiseQL metadata (for Team D)
    fraiseql_type: str | None = None
    fraiseql_relation: str | None = None  # "many-to-one", "one-to-many"
    fraiseql_schema: dict[str, str] | None = None  # For composites

    # UI hints (future)
    input_type: str = "text"
    placeholder: str | None = None
    example: str | None = None

    def __post_init__(self):
        """Initialize field based on type_name"""
        # Set tier and scalar_def based on type_name
        if is_scalar_type(self.type_name):
            self.tier = FieldTier.SCALAR
            self.scalar_def = get_scalar_type(self.type_name)
            if self.scalar_def:
                self.postgres_type = self.scalar_def.get_postgres_type_with_precision()
                self.validation_pattern = self.scalar_def.validation_pattern
                self.min_value = self.scalar_def.min_value
                self.max_value = self.scalar_def.max_value
                self.postgres_precision = self.scalar_def.postgres_precision
                self.input_type = self.scalar_def.input_type
                self.placeholder = self.scalar_def.placeholder
        elif is_composite_type(self.type_name):
            self.tier = FieldTier.COMPOSITE
            # composite_def will be set in Phase 2
        elif self.type_name.startswith("ref(") and self.type_name.endswith(")"):
            self.tier = FieldTier.REFERENCE
        elif self.values:
            # Enum field
            pass  # Keep as BASIC
        else:
            # Basic type
            pass

    def is_rich_scalar(self) -> bool:
        """Check if this is a rich scalar type"""
        return self.tier == FieldTier.SCALAR

    def is_composite(self) -> bool:
        """Check if this is a composite type"""
        return self.tier == FieldTier.COMPOSITE

    def is_reference(self) -> bool:
        """Check if this is a reference to another entity"""
        return self.tier == FieldTier.REFERENCE

    def get_postgres_type(self) -> str:
        """Get the PostgreSQL type for this field"""

        # If we have a cached postgres_type, use it
        if self.postgres_type:
            return self.postgres_type

        # For scalar types, get from registry
        if self.scalar_def:
            return self.scalar_def.get_postgres_type_with_precision()

        # For basic types, map directly
        basic_mappings = {
            "text": "TEXT",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "timestamp": "TIMESTAMPTZ",
            "uuid": "UUID",
            "json": "JSONB",
            "decimal": "DECIMAL",
        }

        if self.type_name in basic_mappings:
            return basic_mappings[self.type_name]

        # For enum types
        if self.values:
            return "TEXT"

        # For ref types (foreign keys)
        if self.type_name == "ref":
            return "INTEGER"  # FK to pk_* column

        # Fallback
        return "TEXT"

    def get_validation_pattern(self) -> str | None:
        """Get validation regex pattern for this field"""
        if self.scalar_def and self.scalar_def.validation_pattern:
            return self.scalar_def.validation_pattern
        return None

    def is_rich_type(self) -> bool:
        """Check if this field uses a rich type"""
        from src.core.scalar_types import is_rich_type

        return is_rich_type(self.type_name) or bool(self.scalar_def)


@dataclass
class IdentifierComponent:
    """Component of identifier calculation."""

    field: str
    transform: str = "slugify"
    format: str | None = None
    separator: str = ""
    replace: dict[str, str] | None = None
    strip_tenant_prefix: bool = False  # NEW: Strip tenant prefix from referenced identifiers


@dataclass
class IdentifierConfig:
    """Identifier calculation strategy."""

    strategy: str

    # Components
    prefix: list[IdentifierComponent] = field(default_factory=list)
    components: list[IdentifierComponent] = field(default_factory=list)

    # Separators (NEW)
    separator: str = Separators.HIERARCHY  # Default changed from "_" to "."
    composition_separator: str = Separators.COMPOSITION  # For composite_hierarchical
    internal_separator: str = Separators.INTERNAL  # For intra-entity flat components


@dataclass
class TranslationConfig:
    """Configuration for i18n translation tables"""

    enabled: bool = False
    table_name: str | None = None  # e.g., "tl_manufacturer"
    fields: list[str] = field(default_factory=list)  # Fields to translate


@dataclass
class EntityDefinition:
    """Represents an entity in SpecQL"""

    name: str
    schema: str
    description: str = ""

    # Fields
    fields: dict[str, FieldDefinition] = field(default_factory=dict)

    # Actions (for Team C)
    actions: list["ActionDefinition"] = field(default_factory=list)

    # AI agents
    agents: list["Agent"] = field(default_factory=list)

    # Organization (numbering system)
    organization: Optional["Organization"] = None

    # Trinity pattern fields (auto-generated by Team B)
    has_trinity_pattern: bool = True

    # Metadata
    is_catalog_table: bool = False  # True for Country, Industry, etc.

    # i18n translations
    translations: TranslationConfig | None = None

    # NEW: Table views configuration
    table_views: TableViewConfig | None = None

    # Identifier configuration (NEW)
    identifier: IdentifierConfig | None = None

    @property
    def has_foreign_keys(self) -> bool:
        """Check if entity has any foreign key fields."""
        return any(field.is_reference() for field in self.fields.values())

    @property
    def should_generate_table_view(self) -> bool:
        """Determine if table view should be generated."""
        if self.table_views is None:
            # Default: auto mode
            return self.has_foreign_keys

        if self.table_views.mode == TableViewMode.DISABLE:
            return False
        elif self.table_views.mode == TableViewMode.FORCE:
            return True
        else:  # AUTO
            return self.has_foreign_keys


@dataclass
class ActionDefinition:
    """Represents an action in SpecQL"""

    name: str
    description: str = ""
    steps: list["ActionStep"] = field(default_factory=list)

    # Impact metadata (for Team C)
    impact: dict[str, Any] | None = None

    # Hierarchy impact (for explicit path recalculation)
    hierarchy_impact: str | None = (
        None  # 'recalculate_subtree', 'recalculate_tenant', 'recalculate_global'
    )


@dataclass
class ActionStep:
    """Parsed action step from SpecQL DSL"""

    type: str  # validate, if, insert, update, delete, call, find, etc.

    # For validate steps
    expression: str | None = None
    error: str | None = None

    # For conditional steps
    condition: str | None = None
    then_steps: list["ActionStep"] = field(default_factory=list)
    else_steps: list["ActionStep"] = field(default_factory=list)

    # For switch steps
    cases: dict[str, list["ActionStep"]] | None = None

    # For database operations
    entity: str | None = None
    fields: dict[str, Any] | None = None
    where_clause: str | None = None

    # For function calls
    function_name: str | None = None
    arguments: dict[str, Any] | None = None
    store_result: str | None = None

    # For foreach steps
    foreach_expr: str | None = None
    iterator_var: str | None = None
    collection: str | None = None

    # For notify steps
    recipient: str | None = None
    channel: str | None = None

    # For refresh_table_view steps
    refresh_scope: RefreshScope | None = None
    propagate_entities: list[str] = field(default_factory=list)
    refresh_strategy: str = "immediate"


@dataclass
class EntityImpact:
    """Impact of an action on a specific entity"""

    entity: str
    operation: str  # CREATE, UPDATE, DELETE
    fields: list[str] = field(default_factory=list)
    collection: str | None = None  # For side effects (e.g., "createdNotifications")


@dataclass
class CacheInvalidation:
    """Cache invalidation specification"""

    query: str  # GraphQL query name to invalidate
    filter: dict[str, Any] | None = None  # Filter conditions
    strategy: str = "REFETCH"  # REFETCH, REMOVE, UPDATE
    reason: str = ""  # Human-readable reason


@dataclass
class ActionImpact:
    """Complete impact metadata for an action"""

    primary: EntityImpact
    side_effects: list[EntityImpact] = field(default_factory=list)
    cache_invalidations: list[CacheInvalidation] = field(default_factory=list)


@dataclass
class Action:
    """Parsed action definition"""

    name: str
    requires: str | None = None  # Permission expression
    steps: list[ActionStep] = field(default_factory=list)
    impact: ActionImpact | None = None  # Impact metadata
    hierarchy_impact: str | None = None  # Explicit path recalculation scope


@dataclass
class Entity:
    """Parsed entity definition"""

    name: str
    schema: str = "public"
    table: str | None = None
    table_code: str | None = None
    description: str = ""

    # Core components
    fields: dict[str, FieldDefinition] = field(default_factory=dict)
    actions: list[Action] = field(default_factory=list)
    agents: list["Agent"] = field(default_factory=list)

    # Database schema
    foreign_keys: list["ForeignKey"] = field(default_factory=list)
    indexes: list["Index"] = field(default_factory=list)

    # Hierarchical entity support
    hierarchical: bool = False  # True if entity has parent/path structure

    # Identifier configuration (NEW)
    identifier: IdentifierConfig | None = None

    # Business logic
    validation: list["ValidationRule"] = field(default_factory=list)
    deduplication: Optional["DeduplicationStrategy"] = None
    operations: Optional["OperationConfig"] = None

    # Helpers and extensions
    trinity_helpers: Optional["TrinityHelpers"] = None
    graphql: Optional["GraphQLSchema"] = None
    translations: Optional["TranslationConfig"] = None

    # Organization (numbering system)
    organization: Optional["Organization"] = None

    # Metadata
    notes: str | None = None


@dataclass
class Agent:
    """AI agent definition"""

    name: str
    type: str = "rule_based"
    observes: list[str] = field(default_factory=list)
    can_execute: list[str] = field(default_factory=list)
    strategy: str = ""
    audit: str = "required"


@dataclass
class DeduplicationRule:
    """Deduplication rule"""

    fields: list[str]
    when: str | None = None
    priority: int = 1
    message: str = ""


@dataclass
class DeduplicationStrategy:
    """Deduplication strategy"""

    strategy: str
    rules: list[DeduplicationRule] = field(default_factory=list)


@dataclass
class ForeignKey:
    """Foreign key definition"""

    name: str
    references: str
    on: list[str]
    nullable: bool = True
    description: str = ""


@dataclass
class GraphQLSchema:
    """GraphQL schema configuration"""

    type_name: str
    queries: list[str] = field(default_factory=list)
    mutations: list[str] = field(default_factory=list)


@dataclass
class Index:
    """Database index definition"""

    columns: list[str]
    type: str = "btree"
    name: str | None = None


@dataclass
class OperationConfig:
    """Operations configuration"""

    create: bool = True
    update: bool = True
    delete: str = "soft"  # "soft", "hard", or False
    recalcid: bool = True


@dataclass
class Organization:
    """Organization configuration for numbering system"""

    table_code: str
    domain_name: str | None = None


@dataclass
class TrinityHelper:
    """Trinity helper function"""

    name: str
    params: dict[str, str]
    returns: str
    description: str = ""


@dataclass
class TrinityHelpers:
    """Trinity helpers configuration"""

    generate: bool = True
    lookup_by: str | None = None
    helpers: list[TrinityHelper] = field(default_factory=list)


@dataclass
class ValidationRule:
    """Validation rule"""

    name: str
    condition: str
    error: str
