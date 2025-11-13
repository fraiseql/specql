import pytest
import tempfile
from pathlib import Path
from src.core.specql_parser import SpecQLParser
from src.generators.diagrams.relationship_extractor import RelationshipExtractor
from src.generators.diagrams.graphviz_generator import GraphvizGenerator
from src.generators.diagrams.mermaid_generator import MermaidGenerator
from src.generators.diagrams.html_viewer_generator import HTMLViewerGenerator

class TestDiagramGenerationE2E:

    def test_full_diagram_workflow_crm_schema(self):
        """Test complete diagram generation workflow with CRM schema"""
        # Parse test entities
        parser = SpecQLParser()
        test_yaml_dir = Path("test_diagram")

        entities = []
        for yaml_file in test_yaml_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                yaml_content = f.read()
                entity = parser.parse(yaml_content)
                entities.append(entity)

        assert len(entities) >= 3  # Should have Company, Contact, Order at minimum

        # Extract relationships
        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        # Verify relationships were found
        assert len(extractor.relationships) > 0
        assert len(extractor.entities) == len(entities)

        # Test Graphviz generation
        graphviz_gen = GraphvizGenerator(extractor)
        dot_source = graphviz_gen.generate(
            title="CRM Schema",
            cluster_by_schema=True,
            show_fields=True
        )

        assert 'digraph schema' in dot_source
        assert 'Company' in dot_source
        assert 'Contact' in dot_source
        assert 'subgraph cluster_crm' in dot_source

        # Test Mermaid generation
        mermaid_gen = MermaidGenerator(extractor)
        mermaid_source = mermaid_gen.generate(
            title="CRM Schema",
            show_fields=True
        )

        assert '```mermaid' in mermaid_source
        assert 'erDiagram' in mermaid_source
        assert 'Company' in mermaid_source
        assert 'Contact' in mermaid_source

        # Test HTML generation
        # First generate SVG for embedding
        svg_content = graphviz_gen.generate(format='svg')

        html_gen = HTMLViewerGenerator(extractor)
        html_content = html_gen.generate(
            svg_content=svg_content,
            title="CRM Schema"
        )

        assert '<!DOCTYPE html>' in html_content
        assert 'CRM Schema' in html_content
        assert 'Company' in html_content
        assert 'Contact' in html_content
        assert 'const entities =' in html_content

    def test_diagram_file_output(self):
        """Test that diagrams can be written to files"""
        # Parse a simple entity
        parser = SpecQLParser()
        entity = parser.parse("""
entity: TestEntity
schema: test
fields:
  code: uuid
  name: text
""")

        extractor = RelationshipExtractor()
        extractor.extract_from_entities([entity])

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Test DOT output
            graphviz_gen = GraphvizGenerator(extractor)
            dot_file = tmp_path / "test.dot"
            graphviz_gen.generate(output_path=str(dot_file))

            assert dot_file.exists()
            content = dot_file.read_text()
            assert 'digraph schema' in content

            # Test Mermaid output
            mermaid_gen = MermaidGenerator(extractor)
            mermaid_file = tmp_path / "test.md"
            mermaid_gen.generate(output_path=str(mermaid_file))

            assert mermaid_file.exists()
            content = mermaid_file.read_text()
            assert '```mermaid' in content

            # Test HTML output
            svg_content = graphviz_gen.generate(format='svg')
            html_gen = HTMLViewerGenerator(extractor)
            html_file = tmp_path / "test.html"
            html_gen.generate(
                svg_content=svg_content,
                output_path=str(html_file)
            )

            assert html_file.exists()
            content = html_file.read_text()
            assert '<!DOCTYPE html>' in content

    def test_relationship_statistics_accuracy(self):
        """Test that relationship statistics are accurate"""
        parser = SpecQLParser()
        entities = [
            parser.parse("""
entity: Parent
schema: test
fields:
  pk_parent: uuid
"""),
            parser.parse("""
entity: Child
schema: test
fields:
  pk_child: uuid
  parent_id: ref(Parent)
"""),
            parser.parse("""
entity: GrandChild
schema: test
fields:
  pk_grandchild: uuid
  child_id: ref(Child)
""")
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        summary = extractor.get_relationship_summary()

        assert summary['total_entities'] == 3
        assert summary['total_relationships'] == 2
        assert 'test' in summary['schemas']

    def test_complex_relationship_patterns(self):
        """Test handling of complex relationship patterns"""
        parser = SpecQLParser()
        entities = [
            parser.parse("""
entity: User
schema: auth
fields:
  pk_user: uuid
"""),
            parser.parse("""
entity: Post
schema: blog
fields:
  pk_post: uuid
  author_id: ref(User)
  editor_id: ref(User)
"""),
            parser.parse("""
entity: Comment
schema: blog
fields:
  pk_comment: uuid
  post_id: ref(Post)
  author_id: ref(User)
""")
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        # Should find 4 relationships (Post->User x2, Comment->Post, Comment->User)
        assert len(extractor.relationships) == 4

        # Test Mermaid generation with multiple relationships
        mermaid_gen = MermaidGenerator(extractor)
        mermaid_source = mermaid_gen.generate()

        assert 'Post ||--|| User' in mermaid_source
        assert 'Comment ||--|| Post' in mermaid_source
        assert 'Comment ||--|| User' in mermaid_source

    def test_schema_clustering_visualization(self):
        """Test that schema clustering works in Graphviz output"""
        parser = SpecQLParser()
        entities = [
            parser.parse("""
entity: User
schema: auth
fields:
  pk_user: uuid
"""),
            parser.parse("""
entity: Company
schema: crm
fields:
  pk_company: uuid
"""),
            parser.parse("""
entity: Contact
schema: crm
fields:
  pk_contact: uuid
  company_id: ref(Company)
  user_id: ref(User)
""")
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        graphviz_gen = GraphvizGenerator(extractor)
        dot_source = graphviz_gen.generate(cluster_by_schema=True)

        # Should have separate clusters
        assert 'subgraph cluster_auth' in dot_source
        assert 'subgraph cluster_crm' in dot_source

        # Cross-schema relationship should exist
        assert 'Contact -> User' in dot_source or 'User -> Contact' in dot_source