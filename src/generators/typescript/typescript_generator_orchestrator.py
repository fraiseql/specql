"""
TypeScript/Prisma generator orchestrator.

Coordinates generation of all TypeScript/Prisma artifacts.
"""

from pathlib import Path
from typing import List, Dict
from src.core.universal_ast import UniversalEntity
from src.generators.typescript.prisma_schema_generator import PrismaSchemaGenerator
from src.generators.typescript.typescript_entity_generator import (
    TypeScriptEntityGenerator,
)


class TypeScriptGeneratorOrchestrator:
    """Orchestrates TypeScript/Prisma code generation."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.prisma_generator = PrismaSchemaGenerator()
        self.entity_generator = TypeScriptEntityGenerator()

    def generate_all(self, entities: List[UniversalEntity]) -> Dict[str, str]:
        """
        Generate all TypeScript/Prisma files for entities.

        Args:
            entities: List of UniversalEntity objects

        Returns:
            Dictionary mapping file paths to generated content
        """
        files = {}

        # Generate Prisma schema
        prisma_schema = self.prisma_generator.generate(entities)
        files["prisma/schema.prisma"] = prisma_schema

        # Generate TypeScript interfaces
        for entity in entities:
            interface_content = self.entity_generator.generate(entity)
            files[f"src/entities/{entity.name}.ts"] = interface_content

        return files

    def write_files(self, files: Dict[str, str]):
        """
        Write generated files to disk.

        Args:
            files: Dictionary mapping file paths to content
        """
        for file_path, content in files.items():
            full_path = self.output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
