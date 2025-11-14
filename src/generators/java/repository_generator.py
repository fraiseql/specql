"""Generate Spring Data JpaRepository interfaces"""

from typing import List
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class JavaRepositoryGenerator:
    """Generates Spring Data repository interfaces"""

    def generate(self, entity: UniversalEntity) -> str:
        """Generate JpaRepository interface"""
        lines = []

        # Package declaration
        lines.append(f"package {entity.schema}.repository;")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Interface declaration
        lines.append("@Repository")
        lines.append(
            f"public interface {entity.name}Repository extends JpaRepository<{entity.name}, Long>, JpaSpecificationExecutor<{entity.name}> {{"
        )
        lines.append("")

        # Query methods
        lines.extend(self._generate_query_methods(entity))
        lines.append("")

        # Pagination methods
        lines.extend(self._generate_pagination_methods(entity))
        lines.append("")

        # Soft delete queries
        lines.extend(self._generate_soft_delete_queries(entity))
        lines.append("")

        # Custom queries
        lines.extend(self._generate_custom_queries(entity))

        lines.append("}")

        return "\n".join(lines)

    def _generate_imports(self, entity: UniversalEntity) -> List[str]:
        """Generate import statements"""
        imports = [
            "import org.springframework.data.jpa.repository.JpaRepository;",
            "import org.springframework.data.jpa.repository.JpaSpecificationExecutor;",
            "import org.springframework.data.jpa.repository.Query;",
            "import org.springframework.data.repository.query.Param;",
            "import org.springframework.stereotype.Repository;",
            f"import {entity.schema}.{entity.name};",
            "import java.util.List;",
            "import java.util.Optional;",
        ]

        # Add pagination imports
        imports.extend(
            [
                "import org.springframework.data.domain.Page;",
                "import org.springframework.data.domain.Pageable;",
            ]
        )

        return imports

    def _generate_query_methods(self, entity: UniversalEntity) -> List[str]:
        """Generate Spring Data query methods"""
        lines = []

        for field in entity.fields:
            if field.type == FieldType.REFERENCE:
                continue  # Skip foreign keys for now

            java_type = self._get_java_type(field, entity.name)
            capitalized = field.name[0].upper() + field.name[1:]

            # findBy method
            if field.unique:
                lines.append(
                    f"    Optional<{entity.name}> findBy{capitalized}({java_type} {field.name});"
                )
                lines.append("")
                lines.append(
                    f"    boolean existsBy{capitalized}({java_type} {field.name});"
                )
            else:
                lines.append(
                    f"    List<{entity.name}> findBy{capitalized}({java_type} {field.name});"
                )

            lines.append("")

        return lines

    def _generate_pagination_methods(self, entity: UniversalEntity) -> List[str]:
        """Generate paginated query methods"""
        lines = []

        # Paginated findAll variants
        for field in entity.fields:
            if field.type in [FieldType.TEXT, FieldType.BOOLEAN]:
                capitalized = field.name[0].upper() + field.name[1:]
                java_type = self._get_java_type(field, entity.name)

                lines.append(
                    f"    Page<{entity.name}> findBy{capitalized}({java_type} {field.name}, Pageable pageable);"
                )
                lines.append("")

        return lines

    def _generate_soft_delete_queries(self, entity: UniversalEntity) -> List[str]:
        """Generate queries that respect deletedAt"""
        return [
            f'    @Query("SELECT e FROM {entity.name} e WHERE e.deletedAt IS NULL")',
            f"    List<{entity.name}> findAllActive();",
            "",
            f'    @Query("SELECT e FROM {entity.name} e WHERE e.deletedAt IS NULL AND e.id = :id")',
            f'    Optional<{entity.name}> findActiveById(@Param("id") Long id);',
            "",
        ]

    def _generate_custom_queries(self, entity: UniversalEntity) -> List[str]:
        """Generate @Query methods for complex queries"""
        lines = []

        # Example: Range query for integer fields
        for field in entity.fields:
            if field.type == FieldType.INTEGER:
                capitalized = field.name[0].upper() + field.name[1:]
                lines.append(
                    f'    @Query("SELECT o FROM {entity.name} o WHERE o.{field.name} > :min{capitalized}")'
                )
                lines.append(
                    f'    List<{entity.name}> findBy{capitalized}GreaterThan(@Param("min{capitalized}") Integer min{capitalized});'
                )
                lines.append("")

        return lines

    def _get_java_type(self, field: UniversalField, entity_name: str = "") -> str:
        """Map SpecQL types to Java types"""
        type_map = {
            FieldType.TEXT: "String",
            FieldType.INTEGER: "Integer",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "LocalDateTime",
        }

        if field.type == FieldType.REFERENCE:
            if field.references is None:
                raise ValueError(
                    f"Reference field {field.name} must specify references"
                )
            return field.references
        elif field.type == FieldType.ENUM:
            return entity_name + self._to_pascal_case(field.name)
        else:
            return type_map.get(field.type, "Object")

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
