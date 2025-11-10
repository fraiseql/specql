"""
Manifest Generator
Creates execution manifests with dependency resolution and topological ordering
"""

from dataclasses import dataclass, field

from src.numbering.numbering_parser import NumberingParser


@dataclass
class ManifestEntry:
    """Entry in the execution manifest"""

    entity_name: str
    table_code: str
    dependencies: list[str] = field(default_factory=list)
    directory_path: str = ""
    file_paths: list[str] = field(default_factory=list)


class ManifestGenerator:
    """Generates execution manifests with dependency resolution"""

    def __init__(self):
        self.entries: dict[str, ManifestEntry] = {}
        self.dependencies: dict[str, set[str]] = {}
        self.parser = NumberingParser()

    def add_entity(
        self, entity_name: str, table_code: str, dependencies: list[str] | None = None
    ) -> None:
        """
        Add an entity to the manifest

        Args:
            entity_name: Name of the entity
            table_code: 6-digit table code
            dependencies: List of entity names this entity depends on
        """
        if entity_name in self.entries:
            raise ValueError(f"Entity '{entity_name}' already exists in manifest")

        # Parse table code to validate and get directory path
        self.parser.parse_table_code_detailed(table_code)  # Validates table code
        directory_path = self.parser.generate_directory_path(table_code, entity_name)

        # Generate file paths (table SQL file)
        file_paths = [self.parser.generate_file_path(table_code, entity_name, "table")]

        entry = ManifestEntry(
            entity_name=entity_name,
            table_code=table_code,
            dependencies=dependencies or [],
            directory_path=directory_path,
            file_paths=file_paths,
        )

        self.entries[entity_name] = entry
        self.dependencies[entity_name] = set(dependencies or [])

    def add_dependency(self, entity_name: str, depends_on: str) -> None:
        """
        Add a dependency relationship

        Args:
            entity_name: Entity that has the dependency
            depends_on: Entity that entity_name depends on
        """
        if entity_name not in self.entries:
            raise ValueError(f"Entity '{entity_name}' not found in manifest")

        if depends_on not in self.entries:
            raise ValueError(f"Dependency entity '{depends_on}' not found in manifest")

        self.dependencies[entity_name].add(depends_on)
        self.entries[entity_name].dependencies.append(depends_on)

    def generate_manifest(self) -> list[ManifestEntry]:
        """
        Generate execution manifest with dependency-aware ordering

        Strategy:
        1. Sort entities by table code (natural hierarchy)
        2. Apply dependency constraints to ensure dependents come after dependencies

        Returns:
            List of ManifestEntry in execution order

        Raises:
            ValueError: If circular dependencies are detected
        """
        # First, sort by table code for natural hierarchy
        sorted_by_code = sorted(self.entries.keys(), key=lambda e: self.entries[e].table_code)

        # Then apply dependency ordering
        execution_order = self._dependency_aware_sort(sorted_by_code)

        # Return entries in execution order
        return [self.entries[entity] for entity in execution_order]

    def _dependency_aware_sort(self, entities: list[str]) -> list[str]:
        """
        Sort entities ensuring dependencies come before dependents

        Args:
            entities: List of entity names (pre-sorted by table code)

        Returns:
            List of entity names in dependency order

        Raises:
            ValueError: If circular dependencies exist
        """
        result = []
        visited = set()
        visiting = set()

        def visit(entity: str):
            if entity in visiting:
                raise ValueError(f"Circular dependency detected involving: {entity}")
            if entity in visited:
                return

            visiting.add(entity)

            # Visit all dependencies first
            for dep in self.dependencies.get(entity, set()):
                if dep in self.entries:  # Only if dependency is in our manifest
                    visit(dep)

            visiting.remove(entity)
            visited.add(entity)
            result.append(entity)

        # Visit all entities
        for entity in entities:
            if entity not in visited:
                visit(entity)

        return result
