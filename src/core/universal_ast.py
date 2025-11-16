# src/core/universal_ast.py
"""
Universal AST for framework-agnostic business logic representation.

This module defines the core data structures that represent SpecQL entities,
fields, and actions in a way that is completely independent of any specific
framework (PostgreSQL, Django, Rails, etc.).

The Universal AST serves as the intermediate representation that adapters
use to generate framework-specific code.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any


class FieldType(Enum):
    """Universal field types - not tied to any framework"""

    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    REFERENCE = "reference"
    ENUM = "enum"
    LIST = "list"
    RICH = "rich"  # Composite types (money, dimensions, etc.)


class StepType(Enum):
    """Universal action step types"""

    VALIDATE = "validate"
    IF = "if"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    SELECT = "select"
    CALL = "call"
    NOTIFY = "notify"
    FOREACH = "foreach"


@dataclass
class UniversalField:
    """Framework-agnostic field definition"""

    name: str
    type: FieldType
    required: bool = False
    unique: bool = False
    default: Optional[Any] = None

    # For REFERENCE type
    references: Optional[str] = None

    # For ENUM type
    enum_values: Optional[List[str]] = None

    # For RICH type
    composite_type: Optional[str] = None

    # For LIST type
    list_item_type: Optional[str] = None

    # For round-trip testing: preserve original PostgreSQL type
    postgres_type: Optional[str] = None
    character_maximum_length: Optional[int] = None


@dataclass
class UniversalEntity:
    """Framework-agnostic entity definition"""

    name: str
    schema: str
    fields: List[UniversalField]
    actions: List["UniversalAction"]

    # Multi-tenancy
    is_multi_tenant: bool = True

    # Metadata
    description: Optional[str] = None


@dataclass
class UniversalStep:
    """Framework-agnostic action step"""

    type: StepType
    expression: Optional[str] = None  # For validate, if conditions
    entity: Optional[str] = None  # For insert, update, delete
    fields: Optional[Dict[str, Any]] = None  # For insert, update
    function: Optional[str] = None  # For call
    collection: Optional[str] = None  # For foreach
    steps: Optional[List["UniversalStep"]] = None  # For if, foreach


@dataclass
class UniversalAction:
    """Framework-agnostic business logic"""

    name: str
    entity: str
    steps: List[UniversalStep]
    impacts: List[str]
    description: Optional[str] = None
    parameters: Optional[List[UniversalField]] = None


@dataclass
class UniversalSchema:
    """Complete framework-agnostic schema"""

    entities: List[UniversalEntity]
    composite_types: Dict[str, List[UniversalField]]
    tenant_mode: str  # 'multi_tenant', 'single_tenant', 'shared'
