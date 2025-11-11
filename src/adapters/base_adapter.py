# src/adapters/base_adapter.py
"""
Base Framework Adapter

Defines the abstract interface that all framework adapters must implement.
Framework adapters convert Universal AST entities into framework-specific code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional

from src.core.universal_ast import UniversalEntity, UniversalAction, UniversalSchema


@dataclass
class GeneratedCode:
    """Container for generated code"""

    file_path: str
    content: str
    language: str  # 'sql', 'python', 'ruby', 'typescript', etc.


@dataclass
class FrameworkConventions:
    """Framework-specific conventions"""

    naming_case: str  # 'snake_case', 'camelCase', 'PascalCase'
    primary_key_name: str
    foreign_key_pattern: str
    timestamp_fields: List[str]
    supports_multi_tenancy: bool


class FrameworkAdapter(ABC):
    """Base class for all framework adapters"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    @abstractmethod
    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate framework-specific entity/model code"""
        pass

    @abstractmethod
    def generate_action(
        self, action: UniversalAction, entity: UniversalEntity
    ) -> List[GeneratedCode]:
        """Generate framework-specific business logic"""
        pass

    @abstractmethod
    def generate_relationship(self, field, entity: UniversalEntity) -> str:
        """Generate framework-specific relationship code"""
        pass

    @abstractmethod
    def get_conventions(self) -> FrameworkConventions:
        """Return framework conventions"""
        pass

    @abstractmethod
    def get_framework_name(self) -> str:
        """Return framework identifier (e.g., 'django', 'rails')"""
        pass

    def generate_full_schema(self, schema: UniversalSchema) -> List[GeneratedCode]:
        """Generate complete schema for all entities"""
        generated = []

        for entity in schema.entities:
            generated.extend(self.generate_entity(entity))

            for action in entity.actions:
                generated.extend(self.generate_action(action, entity))

        return generated
