"""
SpecQL AST Models
Data classes representing parsed SpecQL entities
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.core.type_registry import get_type_registry


@dataclass
class FieldDefinition:
    """Parsed field definition with rich type support"""

    name: str
    type: str  # NOW SUPPORTS: text, integer, email, url, phone, coordinates, etc.
    nullable: bool = True
    default: Optional[Any] = None

    # Type metadata (for complex types like money(currency='USD'))
    type_metadata: Optional[Dict[str, Any]] = None

    # For enum fields
    values: Optional[List[str]] = None

    # For ref fields
    target_entity: Optional[str] = None

    # For list fields
    item_type: Optional[str] = None

    def is_rich_type(self) -> bool:
        """Check if this field uses a FraiseQL rich type"""
        registry = get_type_registry()
        return registry.is_rich_type(self.type)

    def get_postgres_type(self) -> str:
        """Get underlying PostgreSQL storage type"""
        registry = get_type_registry()

        # Rich types
        if self.is_rich_type():
            base_type = registry.get_postgres_type(self.type)

            # Handle money type with custom precision
            if self.type == "money" and self.type_metadata and "precision" in self.type_metadata:
                precision = self.type_metadata["precision"]
                return f"NUMERIC(19,{precision})"

            return base_type

        # Basic types
        basic_type_map = {
            "text": "TEXT",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "jsonb": "JSONB",
            "timestamp": "TIMESTAMPTZ",
        }

        return basic_type_map.get(self.type, "TEXT")

    def get_graphql_scalar(self) -> str:
        """Get GraphQL scalar type name"""
        registry = get_type_registry()

        # Rich types
        if self.is_rich_type():
            scalar = registry.get_graphql_scalar(self.type)
            return f"{scalar}!" if not self.nullable else scalar

        # Basic types
        basic_scalar_map = {
            "text": "String",
            "integer": "Int",
            "boolean": "Boolean",
            "jsonb": "JSON",
        }

        scalar = basic_scalar_map.get(self.type, "String")
        return f"{scalar}!" if not self.nullable else scalar

    def get_validation_pattern(self) -> Optional[str]:
        """Get regex validation pattern (if applicable)"""
        if not self.is_rich_type():
            return None

        registry = get_type_registry()
        return registry.get_validation_pattern(self.type)


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
