from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


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
    fields: list["ParsedField"] = field(default_factory=list)
    methods: list["ParsedMethod"] = field(default_factory=list)
    inheritance: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    source_language: SourceLanguage = SourceLanguage.PYTHON
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedField:
    """Language-agnostic field representation"""

    field_name: str
    field_type: str  # Normalized to SpecQL types
    original_type: str  # Original language type
    required: bool = True
    default: Any | None = None
    constraints: list[str] = field(default_factory=list)
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedMethod:
    """Language-agnostic method/function representation"""

    method_name: str
    parameters: list[dict[str, str]] = field(default_factory=list)
    return_type: str | None = None
    body_lines: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    is_async: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class LanguageParser(Protocol):
    """Protocol for language-specific parsers"""

    def parse_entity(self, source_code: str, file_path: str = "") -> ParsedEntity:
        """Parse source code to entity representation"""
        ...

    def parse_method(self, source_code: str) -> ParsedMethod:
        """Parse method/function to action representation"""
        ...

    def detect_patterns(self, entity: ParsedEntity) -> list[str]:
        """Detect language-specific patterns"""
        ...

    @property
    def supported_language(self) -> SourceLanguage:
        """Language supported by this parser"""
        ...
