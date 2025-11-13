"""
Java AST Parser Orchestrator

High-level coordinator for Java reverse engineering.
Parses Java files, extracts JPA entities, and converts to SpecQL format.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from src.reverse_engineering.java.jdt_bridge import get_jdt_bridge
from src.reverse_engineering.java.jpa_visitor import JPAAnnotationVisitor
from src.reverse_engineering.java.jpa_to_specql import JPAToSpecQLConverter
from src.core.ast_models import Entity


@dataclass
class JavaParseResult:
    """Result of parsing a Java file"""

    file_path: str
    entities: List[Entity]
    errors: List[str] = field(default_factory=list)


@dataclass
class JavaParseConfig:
    """Configuration for Java parsing"""

    include_patterns: List[str] = field(default_factory=lambda: ["*.java"])
    exclude_patterns: List[str] = field(
        default_factory=lambda: ["**/test/**", "**/*Test.java"]
    )
    min_confidence: float = 0.8
    recursive: bool = True


class JavaParser:
    """Orchestrator for Java AST parsing and SpecQL conversion"""

    def __init__(self):
        self.jdt_bridge = get_jdt_bridge()
        self.converter = JPAToSpecQLConverter()

    def parse_file(self, file_path: str) -> JavaParseResult:
        """
        Parse a single Java file

        Args:
            file_path: Path to Java file

        Returns:
            JavaParseResult with extracted entities
        """
        errors = []

        try:
            # Read Java source
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Parse with JDT
            cu = self.jdt_bridge.parse_java(source_code)

            # Extract JPA entities
            visitor = JPAAnnotationVisitor(cu)
            jpa_entities = visitor.visit()

            # Convert to SpecQL entities
            entities = []
            for jpa_entity in jpa_entities:
                try:
                    entity = self.converter.convert(jpa_entity)
                    entities.append(entity)
                except Exception as e:
                    errors.append(
                        f"Failed to convert entity {jpa_entity.class_name}: {e}"
                    )

        except FileNotFoundError:
            errors.append(f"File not found: {file_path}")
            entities = []
        except UnicodeDecodeError as e:
            errors.append(f"Encoding error reading {file_path}: {e}")
            entities = []
        except Exception as e:
            errors.append(f"Unexpected error parsing {file_path}: {e}")
            entities = []

        return JavaParseResult(file_path=file_path, entities=entities, errors=errors)

    def parse_directory(
        self, directory_path: str, config: Optional[JavaParseConfig] = None
    ) -> List[JavaParseResult]:
        """
        Parse all Java files in a directory

        Args:
            directory_path: Path to directory
            config: Parsing configuration

        Returns:
            List of JavaParseResult for each file
        """
        if config is None:
            config = JavaParseConfig()

        results = []

        # Find all Java files
        java_files = self._find_java_files(directory_path, config)

        # Parse each file
        for java_file in java_files:
            result = self.parse_file(java_file)
            results.append(result)

        return results

    def parse_package(
        self, package_path: str, config: Optional[JavaParseConfig] = None
    ) -> Dict[str, List[Entity]]:
        """
        Parse a Java package and return entities grouped by file

        Args:
            package_path: Path to package directory
            config: Parsing configuration

        Returns:
            Dict mapping file paths to lists of entities
        """
        results = self.parse_directory(package_path, config)

        # Group by file and filter out errors
        entities_by_file = {}
        for result in results:
            if result.entities:  # Only include files with entities
                entities_by_file[result.file_path] = result.entities

        return entities_by_file

    def _find_java_files(
        self, directory_path: str, config: JavaParseConfig
    ) -> List[str]:
        """
        Find all Java files in directory matching patterns

        Args:
            directory_path: Directory to search
            config: Configuration with include/exclude patterns

        Returns:
            List of Java file paths
        """
        java_files = []

        path = Path(directory_path)

        if not path.exists():
            return java_files

        # Walk directory
        if config.recursive:
            for root, dirs, files in os.walk(path):
                # Skip excluded directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not self._matches_exclude(d, config.exclude_patterns)
                ]

                for file in files:
                    if self._matches_include(file, config.include_patterns):
                        java_files.append(os.path.join(root, file))
        else:
            # Non-recursive
            for file in path.iterdir():
                if file.is_file() and self._matches_include(
                    file.name, config.include_patterns
                ):
                    java_files.append(str(file))

        return sorted(java_files)

    def _matches_include(self, filename: str, patterns: List[str]) -> bool:
        """Check if filename matches any include pattern"""
        for pattern in patterns:
            if pattern.startswith("*"):
                # Simple wildcard matching
                if filename.endswith(pattern[1:]):
                    return True
            elif filename == pattern:
                return True
        return False

    def _matches_exclude(self, dirname: str, patterns: List[str]) -> bool:
        """Check if directory matches any exclude pattern"""
        for pattern in patterns:
            if "**/" in pattern:
                # Directory pattern like **/test/**
                if "test" in dirname.lower():
                    return True
        return False

    def validate_parse_result(self, result: JavaParseResult) -> Dict[str, Any]:
        """
        Validate a parse result and return confidence metrics

        Args:
            result: Parse result to validate

        Returns:
            Validation metrics
        """
        metrics = {
            "file_path": result.file_path,
            "entity_count": len(result.entities),
            "error_count": len(result.errors),
            "confidence": 0.0,
            "issues": [],
        }

        if result.errors:
            metrics["issues"].extend(result.errors)
            metrics["confidence"] = 0.0
            return metrics

        # Basic validation
        total_fields = sum(len(entity.fields) for entity in result.entities)
        entities_with_ids = sum(
            1
            for entity in result.entities
            if any(field.name == "id" for field in entity.fields.values())
        )

        # Calculate confidence based on heuristics
        confidence = 0.5  # Base confidence

        if total_fields > 0:
            confidence += 0.2

        if entities_with_ids > 0:
            confidence += 0.2

        if len(result.entities) > 0:
            confidence += 0.1

        # Cap at 1.0
        confidence = min(confidence, 1.0)

        metrics["confidence"] = confidence

        # Check for potential issues
        for entity in result.entities:
            if not entity.fields:
                metrics["issues"].append(f"Entity {entity.name} has no fields")

            if not entity.table:
                metrics["issues"].append(f"Entity {entity.name} has no table name")

        return metrics
