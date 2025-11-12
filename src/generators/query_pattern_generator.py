"""
Query Pattern Generator - generates SQL views from declarative query patterns.

This module implements the core generator for the Query Pattern Library,
converting YAML-defined patterns into executable SQL views.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from collections import defaultdict, deque

from src.patterns.pattern_registry import PatternRegistry


@dataclass
class SQLFile:
    """Represents a generated SQL file."""

    name: str
    content: str


class QueryPatternGenerator:
    """
    Generates SQL views from query patterns defined in entity YAML files.

    This generator takes entity definitions with query_patterns and produces
    the corresponding SQL view files using the pattern library.
    """

    def __init__(self, registry: "PatternRegistry"):
        """
        Initialize the query pattern generator.

        Args:
            registry: Pattern registry containing available patterns
        """
        self.registry = registry

    def generate(self, entity: Dict[str, Any]) -> List[SQLFile]:
        """
        Generate SQL files for all query patterns in the entity.

        Args:
            entity: Entity definition dictionary containing query_patterns

        Returns:
            List of SQLFile objects, one for each generated view
        """
        sql_files = []

        # Get patterns in dependency order
        ordered_patterns = self._resolve_dependencies(entity.get("query_patterns", []))

        for pattern_config in ordered_patterns:
            single_files = self.generate_single(entity, pattern_config)
            sql_files.extend(single_files)

        return sql_files

    def generate_single(
        self, entity: Dict[str, Any], pattern_config: Dict[str, Any]
    ) -> List[SQLFile]:
        """
        Generate SQL file for a single query pattern.

        Args:
            entity: Entity definition dictionary
            pattern_config: Single pattern configuration

        Returns:
            List of SQLFile objects (usually one file)
        """
        # Get the pattern from registry
        pattern_name = pattern_config["pattern"]
        pattern = self.registry.get_pattern(pattern_name)

        # Generate SQL using the pattern
        sql = pattern.generate(entity, pattern_config)

        # Create SQL file
        view_name = f"v_{pattern_config['name']}.sql"
        sql_file = SQLFile(name=view_name, content=sql)

        return [sql_file]

    def _resolve_dependencies(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Resolve pattern dependencies and return patterns in topological order.

        Args:
            patterns: List of pattern configurations

        Returns:
            Patterns sorted by dependency order
        """
        if not patterns:
            return patterns

        # Build dependency graph
        graph = defaultdict(list)  # view_name -> list of dependencies
        in_degree = defaultdict(int)  # view_name -> number of incoming edges
        pattern_map = {}  # view_name -> pattern

        # Initialize all patterns
        for pattern in patterns:
            view_name = f"v_{pattern['name']}"
            pattern_map[view_name] = pattern
            in_degree[view_name] = 0

        # Build graph and in-degrees
        for pattern in patterns:
            view_name = f"v_{pattern['name']}"
            depends_on = pattern.get("depends_on", [])

            for dependency in depends_on:
                if not dependency.startswith("v_"):
                    dependency = f"v_{dependency}"
                graph[dependency].append(view_name)
                in_degree[view_name] += 1

        # Perform topological sort using Kahn's algorithm
        queue = deque([view for view, degree in in_degree.items() if degree == 0])
        sorted_views = []

        while queue:
            current = queue.popleft()
            sorted_views.append(current)

            # Reduce in-degree of neighbors
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(sorted_views) != len(patterns):
            remaining = set(pattern_map.keys()) - set(sorted_views)
            raise ValueError(
                f"Circular dependency detected in query patterns. Remaining views: {remaining}"
            )

        # Return patterns in sorted order
        sorted_patterns = [pattern_map[view_name] for view_name in sorted_views]
        return sorted_patterns
