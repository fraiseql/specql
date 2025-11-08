"""
AST Models for SpecQL Entities

Extended to support:
- Tier 1: Scalar rich types
- Tier 2: Composite types (JSONB)
- Tier 3: Entity references (FK)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

# Import from scalar_types
from src.core.scalar_types import (
    ScalarTypeDef,
    CompositeTypeDef,
    get_scalar_type,
    is_scalar_type,
    is_composite_type,
)


class FieldTier(Enum):
    """Which tier this field belongs to"""

    BASIC = "basic"  # text, integer, etc.
    SCALAR = "scalar"  # email, money, etc. (Tier 1)
    COMPOSITE = "composite"  # SimpleAddress, MoneyAmount (Tier 2)
    REFERENCE = "reference"  # ref(Entity) (Tier 3)


@dataclass
class CompositeTypeDef:
    """Placeholder for composite type definition (Phase 2)"""

    name: str
    fields: Dict[str, "FieldDefinition"] = field(default_factory=dict)


@dataclass
class FieldDefinition:
    """Represents a field in an entity"""

    # Core attributes
    name: str
    type_name: str
    nullable: bool = True
    default: Optional[Any] = None
    description: str = ""

    # Tier classification
    tier: FieldTier = FieldTier.BASIC

    # For enum fields
    values: Optional[List[str]] = None

    # For list fields
    item_type: Optional[str] = None

    # Tier 1: Scalar rich type metadata
    scalar_def: Optional[ScalarTypeDef] = None

    # Tier 2: Composite type metadata (set in Phase 2)
    composite_def: Optional["CompositeTypeDef"] = None

    # Tier 3: Reference metadata (set in Phase 3)
    reference_entity: Optional[str] = None
    reference_schema: Optional[str] = None

    # PostgreSQL generation metadata (for Team B)
    postgres_type: Optional[str] = None
    postgres_precision: Optional[tuple] = None
    validation_pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    # FraiseQL metadata (for Team D)
    fraiseql_type: Optional[str] = None
    fraiseql_relation: Optional[str] = None  # "many-to-one", "one-to-many"
    fraiseql_schema: Optional[Dict[str, str]] = None  # For composites

    # UI hints (future)
    input_type: str = "text"
    placeholder: Optional[str] = None
    example: Optional[str] = None

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
        elif self.type_name == "ref":
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
        from src.core.scalar_types import get_scalar_type

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

    def get_validation_pattern(self) -> Optional[str]:
        """Get validation regex pattern for this field"""
        if self.scalar_def and self.scalar_def.validation_pattern:
            return self.scalar_def.validation_pattern
        return None

    def is_rich_type(self) -> bool:
        """Check if this field uses a rich type"""
        from src.core.scalar_types import is_rich_type

        return is_rich_type(self.type_name) or bool(self.scalar_def)


@dataclass
class TranslationConfig:
    """Configuration for i18n translation tables"""

    enabled: bool = False
    table_name: Optional[str] = None  # e.g., "tl_manufacturer"
    fields: List[str] = field(default_factory=list)  # Fields to translate


@dataclass
class EntityDefinition:
    """Represents an entity in SpecQL"""

    name: str
    schema: str
    description: str = ""

    # Fields
    fields: Dict[str, FieldDefinition] = field(default_factory=dict)

    # Actions (for Team C)
    actions: List["ActionDefinition"] = field(default_factory=list)

    # AI agents
    agents: List["Agent"] = field(default_factory=list)

    # Organization (numbering system)
    organization: Optional["Organization"] = None

    # Trinity pattern fields (auto-generated by Team B)
    has_trinity_pattern: bool = True

    # Metadata
    is_catalog_table: bool = False  # True for Country, Industry, etc.

    # i18n translations
    translations: Optional[TranslationConfig] = None


@dataclass
class ActionDefinition:
    """Represents an action in SpecQL"""

    name: str
    description: str = ""
    steps: List["ActionStep"] = field(default_factory=list)

    # Impact metadata (for Team C)
    impact: Optional[Dict[str, Any]] = None


@dataclass
class ActionStep:
    """Parsed action step from SpecQL DSL"""

    type: str  # validate, if, insert, update, delete, call, find, etc.

    # For validate steps
    expression: Optional[str] = None
    error: Optional[str] = None

    # For conditional steps
    condition: Optional[str] = None
    then_steps: List["ActionStep"] = field(default_factory=list)
    else_steps: List["ActionStep"] = field(default_factory=list)

    # For switch steps
    cases: Optional[Dict[str, List["ActionStep"]]] = None

    # For database operations
    entity: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None
    where_clause: Optional[str] = None

    # For function calls
    function_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    store_result: Optional[str] = None

    # For foreach steps
    foreach_expr: Optional[str] = None
    iterator_var: Optional[str] = None
    collection: Optional[str] = None

    # For notify steps
    recipient: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class EntityImpact:
    """Impact of an action on a specific entity"""

    entity: str
    operation: str  # CREATE, UPDATE, DELETE
    fields: List[str] = field(default_factory=list)
    collection: Optional[str] = None  # For side effects (e.g., "createdNotifications")


@dataclass
class CacheInvalidation:
    """Cache invalidation specification"""

    query: str  # GraphQL query name to invalidate
    filter: Optional[Dict[str, Any]] = None  # Filter conditions
    strategy: str = "REFETCH"  # REFETCH, REMOVE, UPDATE
    reason: str = ""  # Human-readable reason


@dataclass
class ActionImpact:
    """Complete impact metadata for an action"""

    primary: EntityImpact
    side_effects: List[EntityImpact] = field(default_factory=list)
    cache_invalidations: List[CacheInvalidation] = field(default_factory=list)


@dataclass
class Action:
    """Parsed action definition"""

    name: str
    requires: Optional[str] = None  # Permission expression
    steps: List[ActionStep] = field(default_factory=list)
    impact: Optional[ActionImpact] = None  # Impact metadata


@dataclass
class Entity:
    """Parsed entity definition"""

    name: str
    schema: str = "public"
    table: Optional[str] = None
    table_code: Optional[str] = None
    description: str = ""

    # Core components
    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    agents: List["Agent"] = field(default_factory=list)

    # Database schema
    foreign_keys: List["ForeignKey"] = field(default_factory=list)
    indexes: List["Index"] = field(default_factory=list)

    # Business logic
    validation: List["ValidationRule"] = field(default_factory=list)
    deduplication: Optional["DeduplicationStrategy"] = None
    operations: Optional["OperationConfig"] = None

    # Helpers and extensions
    trinity_helpers: Optional["TrinityHelpers"] = None
    graphql: Optional["GraphQLSchema"] = None
    translations: Optional["TranslationConfig"] = None

    # Organization (numbering system)
    organization: Optional["Organization"] = None

    # Metadata
    notes: Optional[str] = None


@dataclass
class Agent:
    """AI agent definition"""

    name: str
    type: str = "rule_based"
    observes: List[str] = field(default_factory=list)
    can_execute: List[str] = field(default_factory=list)
    strategy: str = ""
    audit: str = "required"


@dataclass
class DeduplicationRule:
    """Deduplication rule"""

    fields: List[str]
    when: Optional[str] = None
    priority: int = 1
    message: str = ""


@dataclass
class DeduplicationStrategy:
    """Deduplication strategy"""

    strategy: str
    rules: List[DeduplicationRule] = field(default_factory=list)


@dataclass
class ForeignKey:
    """Foreign key definition"""

    name: str
    references: str
    on: List[str]
    nullable: bool = True
    description: str = ""


@dataclass
class GraphQLSchema:
    """GraphQL schema configuration"""

    type_name: str
    queries: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)


@dataclass
class Index:
    """Database index definition"""

    columns: List[str]
    type: str = "btree"
    name: Optional[str] = None


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
    domain_name: Optional[str] = None


@dataclass
class TranslationConfig:
    """Translation configuration"""

    enabled: bool = False
    table_name: Optional[str] = None
    fields: List[str] = field(default_factory=list)


@dataclass
class TrinityHelper:
    """Trinity helper function"""

    name: str
    params: Dict[str, str]
    returns: str
    description: str = ""


@dataclass
class TrinityHelpers:
    """Trinity helpers configuration"""

    generate: bool = True
    lookup_by: Optional[str] = None
    helpers: List[TrinityHelper] = field(default_factory=list)


@dataclass
class ValidationRule:
    """Validation rule"""

    name: str
    condition: str
    error: str
