"""
Dependency Resolver
Provides topological sorting for dependency resolution
"""


class DependencyResolver:
    """Resolves dependencies using topological sorting"""

    def __init__(self):
        self.dependencies: dict[str, set[str]] = {}

    def add_dependency(self, item: str, depends_on: str) -> None:
        """
        Add a dependency relationship

        Args:
            item: Item that has the dependency
            depends_on: Item that 'item' depends on
        """
        if item not in self.dependencies:
            self.dependencies[item] = set()
        self.dependencies[item].add(depends_on)

    def resolve(self, items: list[str]) -> list[str]:
        """
        Resolve dependencies and return items in execution order

        Args:
            items: List of items to resolve dependencies for

        Returns:
            List of items in dependency order (dependencies first)

        Raises:
            ValueError: If circular dependencies are detected
        """
        # Build dependency graph for the given items
        graph = {item: self.dependencies.get(item, set()) for item in items}

        # Track visited items
        visited = set()
        visiting = set()
        result = []

        def visit(item: str):
            if item in visiting:
                raise ValueError(f"Circular dependency detected involving: {item}")
            if item in visited:
                return

            visiting.add(item)

            # Visit all dependencies first
            for dep in graph.get(item, set()):
                if dep in items:  # Only consider dependencies that are in our item list
                    visit(dep)

            visiting.remove(item)
            visited.add(item)
            result.append(item)

        # Visit all items
        for item in items:
            if item not in visited:
                visit(item)

        return result
