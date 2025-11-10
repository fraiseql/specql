"""
View Dependency Resolver for Query Patterns.

This module provides functionality to resolve dependencies between generated views
and determine the correct generation order using topological sorting.
"""

from typing import List, Dict, Set
from collections import defaultdict, deque


class ViewDependencyResolver:
    """
    Resolves dependencies between views to determine generation order.

    Uses topological sorting to ensure views are generated in the correct order
    based on their dependencies.
    """

    def sort(self, patterns: List[Dict]) -> List[str]:
        """
        Topologically sort patterns by their dependencies.

        Args:
            patterns: List of pattern configurations with optional 'depends_on' field

        Returns:
            List of pattern names in dependency order

        Raises:
            ValueError: If there are circular dependencies
        """
        # Build dependency graph
        graph, in_degree = self._build_graph(patterns)

        # Perform topological sort using Kahn's algorithm
        return self._topological_sort(graph, in_degree, patterns)

    def _build_graph(self, patterns: List[Dict]) -> tuple[Dict[str, Set[str]], Dict[str, int]]:
        """
        Build a dependency graph and in-degree count.

        Args:
            patterns: List of pattern configurations

        Returns:
            Tuple of (graph, in_degree) where:
            - graph: dict mapping pattern name to set of patterns that depend on it
            - in_degree: dict mapping pattern name to number of dependencies
        """
        graph = defaultdict(set)  # pattern -> set of patterns that depend on it
        in_degree = defaultdict(int)  # pattern -> number of dependencies

        # Initialize all patterns
        pattern_names = {p["name"] for p in patterns}
        for name in pattern_names:
            in_degree[name] = 0

        # Build the graph
        for pattern in patterns:
            pattern_name = pattern["name"]
            dependencies = pattern.get("depends_on", [])

            for dep in dependencies:
                if dep not in pattern_names:
                    raise ValueError(f"Pattern '{pattern_name}' depends on unknown pattern '{dep}'")
                graph[dep].add(pattern_name)  # dep -> pattern_name
                in_degree[pattern_name] += 1

        return graph, in_degree

    def _topological_sort(
        self, graph: Dict[str, Set[str]], in_degree: Dict[str, int], patterns: List[Dict]
    ) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.

        Args:
            graph: Dependency graph (pattern -> dependents)
            in_degree: In-degree count for each pattern
            patterns: Original pattern list

        Returns:
            List of pattern names in dependency order

        Raises:
            ValueError: If there are circular dependencies
        """
        # Start with patterns that have no dependencies
        queue = deque([name for name in in_degree if in_degree[name] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # For each pattern that depends on current
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(result) != len(in_degree):
            raise ValueError("Circular dependency detected in patterns")

        return result

    def validate_dependencies(self, patterns: List[Dict]) -> List[str]:
        """
        Validate that all dependencies exist and there are no cycles.

        Args:
            patterns: List of pattern configurations

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        try:
            self.sort(patterns)
        except ValueError as e:
            errors.append(str(e))

        return errors
