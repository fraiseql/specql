"""
Spring Boot Parser

High-level coordinator for Spring Boot reverse engineering.
Parses Spring Boot applications and converts to SpecQL actions.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from src.reverse_engineering.java.spring_visitor import (
    SpringComponent,
    SpringAnnotationVisitor,
)
from src.reverse_engineering.java.spring_to_specql import SpringToSpecQLConverter
from src.reverse_engineering.java.jdt_bridge import get_jdt_bridge
from src.core.ast_models import Action


@dataclass
class SpringParseResult:
    """Result of parsing a Spring Boot file"""

    file_path: str
    components: List[SpringComponent]
    actions: List[Action]
    errors: List[str] = field(default_factory=list)


@dataclass
class SpringParseConfig:
    """Configuration for Spring parsing"""

    include_patterns: List[str] = field(default_factory=lambda: ["*.java"])
    exclude_patterns: List[str] = field(
        default_factory=lambda: ["**/test/**", "**/*Test.java", "**/*Tests.java"]
    )
    min_confidence: float = 0.8
    recursive: bool = True


class SpringParser:
    """Orchestrator for Spring Boot AST parsing and SpecQL conversion"""

    def __init__(self):
        self.jdt_bridge = get_jdt_bridge()
        self.converter = SpringToSpecQLConverter()

    def parse_file(self, file_path: str) -> SpringParseResult:
        """
        Parse a single Java file for Spring components

        Args:
            file_path: Path to Java file

        Returns:
            SpringParseResult with extracted components and actions
        """
        errors = []

        try:
            # Read Java source
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Parse with JDT
            cu = self.jdt_bridge.parse_java(source_code)

            # Extract Spring components
            visitor = SpringAnnotationVisitor(cu)
            components = visitor.visit()

            # Convert to SpecQL actions
            actions = []
            for component in components:
                try:
                    component_actions = self.converter.convert_component(component)
                    actions.extend(component_actions)
                except Exception as e:
                    errors.append(
                        f"Failed to convert component {component.class_name}: {e}"
                    )

        except FileNotFoundError:
            errors.append(f"File not found: {file_path}")
            components = []
            actions = []
        except UnicodeDecodeError as e:
            errors.append(f"Encoding error reading {file_path}: {e}")
            components = []
            actions = []
        except Exception as e:
            errors.append(f"Unexpected error parsing {file_path}: {e}")
            components = []
            actions = []

        return SpringParseResult(
            file_path=file_path, components=components, actions=actions, errors=errors
        )

    def parse_directory(
        self, directory_path: str, config: Optional[SpringParseConfig] = None
    ) -> List[SpringParseResult]:
        """
        Parse all Java files in a directory for Spring components

        Args:
            directory_path: Path to directory
            config: Parsing configuration

        Returns:
            List of SpringParseResult for each file
        """
        if config is None:
            config = SpringParseConfig()

        results = []

        # Find all Java files
        java_files = self._find_java_files(directory_path, config)

        # Parse each file
        for java_file in java_files:
            result = self.parse_file(java_file)
            results.append(result)

        return results

    def parse_spring_boot_project(
        self, project_path: str, config: Optional[SpringParseConfig] = None
    ) -> Dict[str, List[Action]]:
        """
        Parse a complete Spring Boot project

        Args:
            project_path: Path to Spring Boot project root
            config: Parsing configuration

        Returns:
            Dict mapping file paths to lists of actions
        """
        results = self.parse_directory(project_path, config)

        # Group by file and filter out errors
        actions_by_file = {}
        for result in results:
            if result.actions:  # Only include files with actions
                actions_by_file[result.file_path] = result.actions

        return actions_by_file

    def _find_java_files(
        self, directory_path: str, config: SpringParseConfig
    ) -> List[str]:
        """
        Find all Java files in directory matching patterns

        Args:
            directory_path: Directory to search
            config: Configuration with include/exclude patterns

        Returns:
            List of Java file paths
        """
        java_files: list[str] = []

        path = Path(directory_path)

        if not path.exists():
            return java_files

        # Walk directory
        if config.recursive:
            for item in path.rglob("*"):
                if item.is_file() and self._matches_include(
                    str(item), config.include_patterns
                ):
                    java_files.append(str(item))
        else:
            # Non-recursive
            for file in path.iterdir():
                if file.is_file() and self._matches_include(
                    str(file), config.include_patterns
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

    def validate_parse_result(self, result: SpringParseResult) -> Dict[str, Any]:
        """
        Validate a parse result and return confidence metrics

        Args:
            result: Parse result to validate

        Returns:
            Validation metrics
        """
        metrics: Dict[str, Any] = {
            "file_path": result.file_path,
            "component_count": len(result.components),
            "action_count": len(result.actions),
            "error_count": len(result.errors),
            "confidence": 0.0,
            "issues": [],
        }

        if result.errors:
            metrics["issues"].extend(list(result.errors))
            metrics["confidence"] = 0.0
            return metrics

        # Basic validation
        total_methods = sum(len(component.methods) for component in result.components)
        controllers_with_endpoints = sum(
            1
            for component in result.components
            if component.component_type in ("controller", "rest_controller")
            and component.methods
        )

        # Calculate confidence based on heuristics
        confidence = 0.5  # Base confidence

        if total_methods > 0:
            confidence += 0.2

        if controllers_with_endpoints > 0:
            confidence += 0.2

        if len(result.components) > 0:
            confidence += 0.1

        # Cap at 1.0
        confidence = min(confidence, 1.0)

        metrics["confidence"] = confidence

        # Check for potential issues
        for component in result.components:
            if not component.methods and component.component_type in (
                "controller",
                "rest_controller",
            ):
                metrics["issues"].append(
                    f"Controller {component.class_name} has no endpoints"
                )

            if component.component_type == "service" and not component.methods:
                metrics["issues"].append(
                    f"Service {component.class_name} has no methods"
                )

        return metrics
