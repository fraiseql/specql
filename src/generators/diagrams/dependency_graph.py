from typing import List, Dict, Set
import networkx as nx

class DependencyGraph:
    """
    Build dependency graph for entities

    Features:
    - Topological sorting (for migration order)
    - Cycle detection
    - Strongly connected components
    - Domain clustering
    """

    def __init__(self, extractor):
        self.extractor = extractor
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self) -> None:
        """Build NetworkX graph from relationships"""
        # Add entity nodes
        for entity_name, entity_node in self.extractor.entities.items():
            self.graph.add_node(
                entity_name,
                schema=entity_node.schema,
                description=entity_node.description,
                field_count=len(entity_node.fields),
            )

        # Add relationship edges (dependency -> dependent)
        for rel in self.extractor.relationships:
            self.graph.add_edge(
                rel.to_entity,  # dependency
                rel.from_entity,  # dependent
                field=rel.from_field,
                type=rel.relationship_type.value,
                nullable=rel.nullable,
            )

    def get_topological_order(self) -> List[str]:
        """
        Get entities in topological order (for migrations)

        Returns entities in dependency order:
        - Entities with no dependencies first
        - Entities that depend on others later

        Example: [Company, Contact, Order]
        (Company has no deps, Contact refs Company, Order refs Contact)
        """
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            # Has cycles - return best-effort order
            return list(self.graph.nodes())

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect circular dependencies

        Returns list of cycles (e.g., [['A', 'B', 'C', 'A']])
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            return []

    def get_strongly_connected_components(self) -> List[Set[str]]:
        """
        Get strongly connected components

        Useful for identifying tightly coupled entity groups
        """
        return list(nx.strongly_connected_components(self.graph))

    def get_entity_dependencies(self, entity_name: str) -> Dict[str, List[str]]:
        """
        Get dependencies for specific entity

        Returns:
            {
                'depends_on': ['Entity1', 'Entity2'],  # Entities this depends on
                'depended_by': ['Entity3', 'Entity4']  # Entities that depend on this
            }
        """
        return {
            'depends_on': list(self.graph.successors(entity_name)),
            'depended_by': list(self.graph.predecessors(entity_name)),
        }

    def get_entities_by_schema(self) -> Dict[str, List[str]]:
        """Group entities by schema (for clustering in diagram)"""
        schemas = {}

        for node, data in self.graph.nodes(data=True):
            schema = data.get('schema', 'public')
            if schema not in schemas:
                schemas[schema] = []
            schemas[schema].append(node)

        return schemas

    def calculate_entity_metrics(self) -> Dict[str, Dict[str, int]]:
        """
        Calculate metrics for each entity

        Metrics:
        - in_degree: How many entities reference this
        - out_degree: How many entities this references
        - centrality: Importance in the graph
        """
        metrics = {}

        # Degree centrality
        in_degree = dict(self.graph.in_degree())
        out_degree = dict(self.graph.out_degree())

        # Betweenness centrality (importance)
        betweenness = nx.betweenness_centrality(self.graph)

        for entity in self.graph.nodes():
            metrics[entity] = {
                'references_count': out_degree[entity],
                'referenced_by_count': in_degree[entity],
                'importance': round(betweenness[entity], 3),
            }

        return metrics