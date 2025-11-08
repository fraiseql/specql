"""
SpecQL AST Models
Data classes representing parsed SpecQL entities
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FieldDefinition:
    """Parsed field definition"""

    name: str
    type: str  # text, integer, enum, ref, list
    nullable: bool = True
    default: Optional[Any] = None

    # For enum fields
    values: Optional[List[str]] = None

    # For ref fields
    target_entity: Optional[str] = None

    # For list fields
    item_type: Optional[str] = None


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

    # For database operations
    entity: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None
    where_clause: Optional[str] = None

    # For function calls
    function_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    store_result: Optional[str] = None


@dataclass
class Action:
    """Parsed action definition"""

    name: str
    requires: Optional[str] = None  # Permission expression
    steps: List[ActionStep] = field(default_factory=list)


@dataclass
class Agent:
    """Parsed AI agent definition"""

    name: str
    type: str  # ai_llm, rule_based
    observes: List[str] = field(default_factory=list)
    can_execute: List[str] = field(default_factory=list)
    strategy: str = ""
    audit: str = "required"


@dataclass
class Organization:
    """Entity organization metadata (numbering system)"""

    table_code: str
    domain_name: Optional[str] = None


@dataclass
class ForeignKey:
    """Foreign key definition"""

    name: str
    references: str  # table.column format
    on: str  # referenced column
    nullable: bool = True
    description: str = ""


@dataclass
class Index:
    """Index definition"""

    columns: List[str]
    type: str = "btree"  # btree, hash, gist, gin, etc.
    name: Optional[str] = None
    unique: bool = False


@dataclass
class ValidationRule:
    """Validation rule definition"""

    name: str
    condition: str
    error: str


@dataclass
class DeduplicationRule:
    """Deduplication rule for preventing duplicates"""

    fields: List[str]
    when: Optional[str] = None  # condition when this rule applies
    priority: int = 1
    message: str = ""


@dataclass
class DeduplicationStrategy:
    """Deduplication strategy configuration"""

    strategy: str  # identifier_based, field_based, etc.
    rules: List[DeduplicationRule] = field(default_factory=list)


@dataclass
class OperationConfig:
    """CRUD operation configuration"""

    create: bool = True
    update: bool = True
    delete: str = "soft"  # soft, hard, or false
    recalcid: bool = True


@dataclass
class TrinityHelper:
    """Trinity pattern helper function"""

    name: str
    params: List[str]
    returns: str
    description: str = ""


@dataclass
class TrinityHelpers:
    """Trinity pattern helpers configuration"""

    generate: bool = True
    lookup_by: Optional[str] = None
    helpers: List[TrinityHelper] = field(default_factory=list)


@dataclass
class GraphQLQuery:
    """GraphQL query definition"""

    name: str


@dataclass
class GraphQLMutation:
    """GraphQL mutation definition"""

    name: str


@dataclass
class GraphQLSchema:
    """GraphQL schema configuration"""

    type_name: str
    queries: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)


@dataclass
class TranslationConfig:
    """Internationalization configuration"""

    enabled: bool = False
    table_name: Optional[str] = None
    fields: List[str] = field(default_factory=list)


@dataclass
class Entity:
    """Parsed SpecQL entity (root AST node)"""

    name: str
    schema: str = "public"
    table: Optional[str] = None  # If different from entity name
    table_code: Optional[str] = None  # Trinity pattern table code
    description: str = ""

    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    agents: List[Agent] = field(default_factory=list)

    # Numbering system integration
    organization: Optional[Organization] = None

    # Database schema extensions
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)

    # Business logic
    validation: List[ValidationRule] = field(default_factory=list)
    deduplication: Optional[DeduplicationStrategy] = None
    operations: Optional[OperationConfig] = None

    # Trinity pattern helpers
    trinity_helpers: Optional[TrinityHelpers] = None

    # API layers
    graphql: Optional[GraphQLSchema] = None

    # Internationalization
    translations: Optional[TranslationConfig] = None

    # Documentation
    notes: str = ""

    def get_table_name(self) -> str:
        """Get table name (custom or derived from entity name)"""
        return self.table or f"tb_{self.name.lower()}"

    def get_field_names(self) -> List[str]:
        """Get list of all field names"""
        return list(self.fields.keys())

    def has_action(self, action_name: str) -> bool:
        """Check if entity has specific action"""
        return any(a.name == action_name for a in self.actions)
