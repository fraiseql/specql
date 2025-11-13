from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class SourceLanguage(Enum):
    """Supported source languages"""
    SQL = "sql"
    PYTHON = "python"
    TYPESCRIPT = "typescript"  # Future
    JAVA = "java"  # Future

@dataclass
class ParsedEntity:
    """Language-agnostic entity representation"""
    entity_name: str
    namespace: str  # schema (SQL) or module (Python)
    fields: List['ParsedField'] = field(default_factory=list)
    methods: List['ParsedMethod'] = field(default_factory=list)
    inheritance: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    source_language: SourceLanguage = SourceLanguage.PYTHON
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedField:
    """Language-agnostic field representation"""
    field_name: str
    field_type: str  # Normalized to SpecQL types
    original_type: str  # Original language type
    required: bool = True
    default: Optional[Any] = None
    constraints: List[str] = field(default_factory=list)
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_target: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedMethod:
    """Language-agnostic method/function representation"""
    method_name: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    body_lines: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class LanguageParser(Protocol):
    """Protocol for language-specific parsers"""

    def parse_entity(self, source_code: str, file_path: str = "") -> ParsedEntity:
        """Parse source code to entity representation"""
        ...

    def parse_method(self, source_code: str) -> ParsedMethod:
        """Parse method/function to action representation"""
        ...

    def detect_patterns(self, entity: ParsedEntity) -> List[str]:
        """Detect language-specific patterns"""
        ...

    @property
    def supported_language(self) -> SourceLanguage:
        """Language supported by this parser"""
        ...