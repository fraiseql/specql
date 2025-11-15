"""
AST Models for SpecQL Entities

Extended to support:
- Tier 1: Scalar rich types
- Tier 2: Composite types (JSONB)
- Tier 3: Entity references (FK)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Forward references will be resolved
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
            raise ValueError(
                f"include_relations.{self.entity_name} must specify fields"
            )

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
class CallServiceStep:
    """Action step for calling external services."""

    service: str
    operation: str
    input: dict[str, Any]
    async_mode: bool = True
    timeout: int | None = None
    max_retries: int | None = None
    on_success: list["ActionStep"] = field(default_factory=list)
    on_failure: list["ActionStep"] = field(default_factory=list)
    correlation_field: str | None = None  # e.g., "$order.id"


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

    composite_def: Optional["CompositeTypeDef"] = None

    reference_entity: str | None = None
    reference_schema: str | None = None

    postgres_type: str | None = None
    postgres_precision: tuple | None = None
    validation_pattern: str | None = None
    min_value: float | None = None
    max_value: float | None = None

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
    strip_tenant_prefix: bool = (
        False  # NEW: Strip tenant prefix from referenced identifiers
    )


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
    subdomain: str | None = None  # Optional subdomain override
    description: str = ""

    # Features (for advanced functionality like vectors, search, etc.)
    features: list[str] = field(default_factory=list)

    # Vector search configuration
    search_functions: bool = True  # Generate custom search functions (default True for backward compatibility)

    # Fields
    fields: dict[str, FieldDefinition] = field(default_factory=dict)

    actions: list["ActionDefinition"] = field(default_factory=list)

    # AI agents
    agents: list["Agent"] = field(default_factory=list)

    # Organization (numbering system)
    organization: Optional["Organization"] = None

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
class CDCConfig:
    """CDC/Outbox configuration for actions"""

    enabled: bool = False
    event_type: str | None = None  # e.g., 'PostCreated'
    include_cascade: bool = True  # Include cascade in event_metadata
    include_payload: bool = True  # Include full entity data
    partition_key: str | None = None  # Custom partition key expression


@dataclass
class ActionDefinition:
    """Represents an action in SpecQL"""

    name: str
    description: str = ""
    steps: list["ActionStep"] = field(default_factory=list)

    impact: dict[str, Any] | None = None

    # Hierarchy impact (for explicit path recalculation)
    hierarchy_impact: str | None = (
        None  # 'recalculate_subtree', 'recalculate_tenant', 'recalculate_global'
    )

    pattern: str | None = None  # Pattern name if this action uses a pattern
    pattern_config: dict[str, Any] | None = None  # Pattern configuration

    cdc: CDCConfig | None = None  # CDC configuration


@dataclass
class VariableDeclaration:
    """Variable declaration"""

    name: str
    type: str  # numeric, text, boolean, uuid, etc.
    default_value: Any | None = None


@dataclass
class SwitchCase:
    """Case in a switch statement"""

    when_condition: str | None = None  # For complex conditions
    when_value: str | None = None  # For simple value matching
    then_steps: list["ActionStep"] = field(default_factory=list)


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
    switch_expression: str | None = None
    cases: list[SwitchCase] = field(default_factory=list)
    default_steps: list["ActionStep"] = field(default_factory=list)

    # For database operations
    entity: str | None = None
    fields: dict[str, Any] | None = None
    where_clause: str | None = None

    # For function calls
    function_name: str | None = None
    arguments: dict[str, Any] | None = None
    store_result: str | None = None

    # For raw SQL steps (used by patterns)
    sql: str | None = None

    # For table view refresh steps
    view_name: str | None = None

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

    # For call_service steps
    service: str | None = None
    operation: str | None = None
    input: dict[str, Any] | None = None
    async_mode: bool = True
    timeout: int | None = None
    max_retries: int | None = None
    correlation_field: str | None = None
    on_success: list["ActionStep"] = field(default_factory=list)
    on_failure: list["ActionStep"] = field(default_factory=list)

    # NEW: declare step
    variable_name: str | None = None
    variable_type: str | None = None
    default_value: Any | None = None
    declarations: list[VariableDeclaration] = field(default_factory=list)

    # NEW: cte step
    cte_name: str | None = None
    cte_query: str | None = None
    cte_materialized: bool = False

    # NEW: aggregate step
    aggregate_operation: str | None = None
    aggregate_field: str | None = None
    aggregate_from: str | None = None
    aggregate_where: str | None = None
    aggregate_group_by: str | None = None
    aggregate_as: str | None = None

    # NEW: subquery step
    subquery_query: str | None = None
    subquery_result_variable: str | None = None

    # NEW: call_function step
    call_function_name: str | None = None
    call_function_arguments: dict[str, Any] | None = None
    call_function_return_variable: str | None = None

    # NEW: switch step
    # (switch_expression, cases, default_steps already defined above)

    # NEW: return_early step
    return_value: Any | None = None

    # NEW: while loop
    while_condition: str | None = None
    loop_body: list["ActionStep"] = field(default_factory=list)

    # NEW: for_query loop
    for_query_sql: str | None = None
    for_query_alias: str | None = None
    for_query_body: list["ActionStep"] = field(default_factory=list)

    # NEW: exception handling
    try_steps: list["ActionStep"] = field(default_factory=list)
    catch_handlers: list["ExceptionHandler"] = field(default_factory=list)  # type: ignore
    finally_steps: list["ActionStep"] = field(default_factory=list)

    # NEW: Week 6 - Advanced Queries
    # json_build step
    json_variable_name: str | None = None
    json_object: dict[str, Any] | None = None

    # array_build step
    array_variable_name: str | None = None
    array_elements: list[Any] | None = None

    # upsert step
    upsert_entity: str | None = None
    upsert_fields: dict[str, Any] | None = None
    upsert_conflict_target: str | None = None
    upsert_conflict_action: str | None = None

    # batch_operation step
    batch_operation_type: str | None = None  # insert, update, delete
    batch_data: list[dict[str, Any]] | None = None
    batch_entity: str | None = None

    # window_function step
    window_function_name: str | None = None
    window_partition_by: list[str] | None = None
    window_order_by: list[str] | None = None
    window_frame: str | None = None
    window_as: str | None = None

    # return_table step
    return_table_query: str | None = None

    # cursor step
    cursor_name: str | None = None
    cursor_query: str | None = None
    cursor_operations: list["ActionStep"] | None = None

    # recursive_cte step
    recursive_cte_name: str | None = None
    recursive_cte_base_query: str | None = None
    recursive_cte_recursive_query: str | None = None

    # dynamic_sql step
    dynamic_sql_template: str | None = None
    dynamic_sql_parameters: dict[str, Any] | None = None
    dynamic_sql_result_variable: str | None = None

    # transaction_control step
    transaction_command: str | None = None  # BEGIN, COMMIT, ROLLBACK, SAVEPOINT


@dataclass
class ExceptionHandler:
    """Exception handler in catch block"""

    when_condition: str  # Exception type (payment_failed, OTHERS, etc.)
    then_steps: list["ActionStep"] = field(default_factory=list)


@dataclass
class EntityImpact:
    """Impact of an action on a specific entity"""

    entity: str
    operation: str  # CREATE, UPDATE, DELETE
    fields: list[str] = field(default_factory=list)
    collection: str | None = None  # For side effects (e.g., "createdNotifications")
    schema: str | None = None  # Schema for cross-schema references


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

    @classmethod
    def from_dict(
        cls, impact_dict: dict, entity_name: str = "Unknown"
    ) -> "ActionImpact":
        """Create ActionImpact from dict format (for backwards compatibility)"""
        primary_data = impact_dict.get("primary", {})
        entity_name = primary_data.get("entity", entity_name)
        operation = primary_data.get("operation", "UPDATE")
        fields = primary_data.get("fields", [])

        side_effects_data = impact_dict.get("side_effects", [])
        side_effects = (
            [EntityImpact(**effect) for effect in side_effects_data]
            if side_effects_data
            else []
        )

        cache_data = impact_dict.get("cache_invalidations", [])
        cache_invalidations = (
            [CacheInvalidation(**inv) for inv in cache_data] if cache_data else []
        )

        return cls(
            primary=EntityImpact(
                entity=entity_name, operation=operation, fields=fields
            ),
            side_effects=side_effects,
            cache_invalidations=cache_invalidations,
        )


@dataclass
class Action:
    """Parsed action definition"""

    name: str
    requires: str | None = None  # Permission expression
    steps: list[ActionStep] = field(default_factory=list)
    impact: ActionImpact | None = None  # Impact metadata
    hierarchy_impact: str | None = None  # Explicit path recalculation scope
    cdc: CDCConfig | None = None  # CDC configuration


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
