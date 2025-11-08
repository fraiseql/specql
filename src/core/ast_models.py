"""
SpecQL AST Models
Data classes representing parsed SpecQL entities
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


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
    then_steps: List['ActionStep'] = field(default_factory=list)
    else_steps: List['ActionStep'] = field(default_factory=list)

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
class Entity:
    """Parsed SpecQL entity (root AST node)"""
    name: str
    schema: str = "public"
    table: Optional[str] = None  # If different from entity name
    description: str = ""

    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    agents: List[Agent] = field(default_factory=list)

    # Numbering system integration
    organization: Optional[Organization] = None

    def get_table_name(self) -> str:
        """Get table name (custom or derived from entity name)"""
        return self.table or f"tb_{self.name.lower()}"

    def get_field_names(self) -> List[str]:
        """Get list of all field names"""
        return list(self.fields.keys())

    def has_action(self, action_name: str) -> bool:
        """Check if entity has specific action"""
        return any(a.name == action_name for a in self.actions)
