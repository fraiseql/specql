"""Orchestrate all Java generators"""

from dataclasses import dataclass
from pathlib import Path
from typing import List
from src.core.universal_ast import UniversalEntity, FieldType
from src.generators.java.entity_generator import JavaEntityGenerator
from src.generators.java.repository_generator import JavaRepositoryGenerator
from src.generators.java.service_generator import JavaServiceGenerator
from src.generators.java.controller_generator import JavaControllerGenerator
from src.generators.java.enum_generator import JavaEnumGenerator


@dataclass
class GeneratedFile:
    """Represents a generated Java file"""

    path: str
    content: str


class JavaGeneratorOrchestrator:
    """Orchestrates all Java code generation"""

    def __init__(self, output_dir: str = "generated/java"):
        self.output_dir = Path(output_dir)
        self.entity_gen = JavaEntityGenerator()
        self.repo_gen = JavaRepositoryGenerator()
        self.service_gen = JavaServiceGenerator()
        self.controller_gen = JavaControllerGenerator()
        self.enum_gen = JavaEnumGenerator()

    def generate_all(self, entity: UniversalEntity) -> List[GeneratedFile]:
        """Generate all Java files for an entity"""
        files = []

        # Entity class
        files.append(
            GeneratedFile(
                path=f"{entity.schema}/{entity.name}.java",
                content=self.entity_gen.generate(entity),
            )
        )

        # Enums
        for field in entity.fields:
            if field.type == FieldType.ENUM:
                enum_code = self.enum_gen.generate(field, entity.schema, entity.name)
                enum_name = entity.name + field.name[0].upper() + field.name[1:]
                files.append(
                    GeneratedFile(
                        path=f"{entity.schema}/{enum_name}.java", content=enum_code
                    )
                )

        # Repository
        files.append(
            GeneratedFile(
                path=f"{entity.schema}/repository/{entity.name}Repository.java",
                content=self.repo_gen.generate(entity),
            )
        )

        # Service
        files.append(
            GeneratedFile(
                path=f"{entity.schema}/service/{entity.name}Service.java",
                content=self.service_gen.generate(entity),
            )
        )

        # Controller
        files.append(
            GeneratedFile(
                path=f"{entity.schema}/controller/{entity.name}Controller.java",
                content=self.controller_gen.generate(entity),
            )
        )

        return files

    def write_files(self, files: List[GeneratedFile]) -> None:
        """Write generated files to disk"""
        for file in files:
            full_path = self.output_dir / file.path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(file.content)
