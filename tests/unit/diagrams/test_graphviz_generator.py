from src.generators.diagrams.graphviz_generator import GraphvizGenerator
from src.generators.diagrams.relationship_extractor import RelationshipExtractor
from src.core.ast_models import Entity, FieldDefinition


class TestGraphvizGenerator:
    def test_generate_simple_diagram(self):
        """Test generating simple ERD"""
        entities = [
            Entity(
                name="Company",
                schema="crm",
                fields={
                    "name": FieldDefinition(
                        name="name", type_name="text", nullable=False
                    )
                },
            ),
            Entity(
                name="Contact",
                schema="crm",
                fields={
                    "email": FieldDefinition(
                        name="email", type_name="text", nullable=False
                    ),
                    "company_id": FieldDefinition(
                        name="company_id", type_name="ref(Company)", nullable=False
                    ),
                },
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = GraphvizGenerator(extractor)
        dot_source = generator.generate()

        # Check DOT structure
        assert "digraph schema" in dot_source
        assert "Company" in dot_source
        assert "Contact" in dot_source
        assert "company_id" in dot_source

    def test_clustering_by_schema(self):
        """Test schema clustering"""
        entities = [
            Entity(name="User", schema="auth", fields={}),
            Entity(name="Contact", schema="crm", fields={}),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = GraphvizGenerator(extractor)
        dot_source = generator.generate(cluster_by_schema=True)

        # Should have subgraph clusters
        assert "subgraph cluster_auth" in dot_source
        assert "subgraph cluster_crm" in dot_source

    def test_self_referential_relationship(self):
        """Test self-referential relationship rendering"""
        entity = Entity(
            name="Employee",
            schema="hr",
            fields={
                "name": FieldDefinition(name="name", type_name="text", nullable=False),
                "manager_id": FieldDefinition(
                    name="manager_id", type_name="ref(Employee)", nullable=True
                ),
            },
        )

        extractor = RelationshipExtractor()
        extractor.extract_from_entities([entity])

        generator = GraphvizGenerator(extractor)
        dot_source = generator.generate()

        # Should have self-edge
        assert "Employee -> Employee" in dot_source
        assert "constraint=false" in dot_source  # Don't constrain layout
