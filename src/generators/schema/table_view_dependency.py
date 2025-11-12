"""
Table View Dependency Resolver

Resolves dependency order for tv_ generation and refresh operations.
Uses topological sort to ensure proper ordering of table view creation and updates.
"""

from src.core.ast_models import EntityDefinition


class TableViewDependencyResolver:
    """Resolve dependency order for tv_ generation and refresh."""

    def __init__(self, entities: list[EntityDefinition]):
        self.entities = {e.name: e for e in entities}
        self.dependency_graph = self._build_dependency_graph()

    def _build_dependency_graph(self) -> dict[str, set[str]]:
        """Build dependency graph (entity -> entities that depend on this entity)."""
        graph = {name: set() for name in self.entities.keys()}

        for entity in self.entities.values():
            # Find ref() fields - these create dependencies
            for field_name, field in entity.fields.items():
                if field.is_reference():
                    # Try reference_entity first (new format), then parse type_name (legacy format)
                    ref_entity = field.reference_entity
                    if not ref_entity and field.type_name.startswith("ref(") and field.type_name.endswith(")"):
                        # Legacy format: extract from type_name
                        ref_entity = field.type_name[4:-1]

                    if ref_entity and ref_entity != entity.name and ref_entity in graph:  # Not self-reference
                        # entity depends on ref_entity, so ref_entity has entity as dependent
                        graph[ref_entity].add(entity.name)

        return graph

    def get_generation_order(self) -> list[str]:
        """Get entity names in dependency order (topological sort)."""
        # Build reverse dependency graph (entity -> depends on entities)
        reverse_graph = {name: set() for name in self.entities.keys()}
        in_degree = {name: 0 for name in self.entities.keys()}

        for entity, dependents in self.dependency_graph.items():
            for dependent in dependents:
                reverse_graph[dependent].add(entity)
                in_degree[dependent] += 1

        # Kahn's algorithm for topological sort
        # Queue entities with no dependencies (in_degree = 0)
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Process entity with no dependencies
            entity_name = queue.pop(0)
            result.append(entity_name)

            # For each entity that depends on this one, reduce their in_degree
            for dependent in self.dependency_graph[entity_name]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self.entities):
            # Cycle detected
            raise ValueError("Circular dependency detected in entity references")

        return result

    def get_refresh_order_for_entity(self, entity_name: str) -> list[str]:
        """Get entities that must be refreshed when given entity changes."""
        # Return all entities that depend on this one
        return list(self.dependency_graph.get(entity_name, set()))
