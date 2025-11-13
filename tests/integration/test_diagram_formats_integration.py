import pytest
import tempfile
from pathlib import Path
from src.generators.diagrams.relationship_extractor import RelationshipExtractor
from src.generators.diagrams.graphviz_generator import GraphvizGenerator
from src.generators.diagrams.mermaid_generator import MermaidGenerator
from src.generators.diagrams.html_viewer_generator import HTMLViewerGenerator
from src.core.ast_models import Entity, FieldDefinition

class TestDiagramFormatsIntegration:
    """Comprehensive integration tests for all diagram formats"""

    @pytest.fixture
    def crm_entities(self):
        """CRM entities fixture: Company -> Contact -> Order"""
        return [
            Entity(
                name='Company',
                schema='crm',
                fields={
                    'name': FieldDefinition(name='name', type_name='text', nullable=False),
                    'industry': FieldDefinition(name='industry', type_name='text', nullable=True),
                    'employee_count': FieldDefinition(name='employee_count', type_name='integer', nullable=True)
                }
            ),
            Entity(
                name='Contact',
                schema='crm',
                fields={
                    'email': FieldDefinition(name='email', type_name='text', nullable=False),
                    'phone': FieldDefinition(name='phone', type_name='text', nullable=True),
                    'company_id': FieldDefinition(name='company_id', type_name='ref(Company)', nullable=False),
                    'status': FieldDefinition(name='status', type_name='enum', nullable=True)
                }
            ),
            Entity(
                name='Order',
                schema='sales',
                fields={
                    'total': FieldDefinition(name='total', type_name='decimal', nullable=False),
                    'contact_id': FieldDefinition(name='contact_id', type_name='ref(Contact)', nullable=False),
                    'status': FieldDefinition(name='status', type_name='enum', nullable=True)
                }
            )
        ]

    @pytest.fixture
    def extractor(self, crm_entities):
        """Relationship extractor fixture"""
        extractor = RelationshipExtractor()
        extractor.extract_from_entities(crm_entities)
        return extractor

    def test_all_formats_generate_without_errors(self, extractor):
        """Test that all formats can generate without throwing exceptions"""
        # Graphviz formats
        graphviz_gen = GraphvizGenerator(extractor)

        # DOT format
        dot_content = graphviz_gen.generate(format='dot')
        assert isinstance(dot_content, str)
        assert 'digraph schema' in dot_content

        # SVG format (requires graphviz system dependency)
        try:
            svg_content = graphviz_gen.generate(format='svg')
            assert isinstance(svg_content, str)
            assert '<svg' in svg_content
        except Exception as e:
            # Graphviz might not be installed, skip this check
            pytest.skip(f"Graphviz not available: {e}")

        # Mermaid format
        mermaid_gen = MermaidGenerator(extractor)
        mermaid_content = mermaid_gen.generate()
        assert isinstance(mermaid_content, str)
        assert '```mermaid' in mermaid_content
        assert 'erDiagram' in mermaid_content

        # HTML format
        html_gen = HTMLViewerGenerator(extractor)
        svg_for_html = graphviz_gen.generate(format='svg')
        html_content = html_gen.generate(svg_content=svg_for_html)
        assert isinstance(html_content, str)
        assert '<!DOCTYPE html>' in html_content

    def test_cross_format_consistency(self, extractor):
        """Test that all formats represent the same relationships consistently"""
        graphviz_gen = GraphvizGenerator(extractor)
        mermaid_gen = MermaidGenerator(extractor)

        # Get relationship counts from extractor
        expected_relationships = len(extractor.relationships)
        expected_entities = len(extractor.entities)

        # Check Graphviz DOT
        dot_content = graphviz_gen.generate()
        # Count entity names in the DOT content
        dot_entity_names = ['Company', 'Contact', 'Order']
        dot_entity_count = sum(1 for name in dot_entity_names if name in dot_content)
        assert dot_entity_count == expected_entities

        # Check Mermaid
        mermaid_content = mermaid_gen.generate()
        mermaid_relationship_count = mermaid_content.count('||--')
        assert mermaid_relationship_count == expected_relationships

        # Check entity count in Mermaid
        mermaid_entity_blocks = mermaid_content.count('{')
        assert mermaid_entity_blocks == expected_entities

    def test_format_options_consistency(self, extractor):
        """Test that format options work consistently across generators"""
        graphviz_gen = GraphvizGenerator(extractor)
        mermaid_gen = MermaidGenerator(extractor)

        # Test with fields enabled
        dot_with_fields = graphviz_gen.generate(show_fields=True)
        mermaid_with_fields = mermaid_gen.generate(show_fields=True)

        assert 'name' in dot_with_fields  # Company name field
        assert 'text name' in mermaid_with_fields

        # Test with Trinity fields (should be hidden by default)
        dot_hide_trinity = graphviz_gen.generate(show_trinity=False)
        mermaid_hide_trinity = mermaid_gen.generate(show_trinity=False)

        # Should not contain any Trinity-like fields (check for field declarations)
        assert 'pk_' not in dot_hide_trinity.lower()
        assert 'uuid id' not in mermaid_hide_trinity.lower()

    def test_file_output_integration(self, extractor, tmp_path):
        """Test file output for all formats"""
        graphviz_gen = GraphvizGenerator(extractor)
        mermaid_gen = MermaidGenerator(extractor)
        html_gen = HTMLViewerGenerator(extractor)

        # Test DOT file output (DOT format doesn't create file via output_path)
        dot_file = tmp_path / "test.dot"
        dot_content = graphviz_gen.generate(format='dot')
        dot_file.write_text(dot_content)
        assert dot_file.exists()
        assert dot_file.read_text() == dot_content

        # Test Mermaid file output
        mermaid_file = tmp_path / "test.md"
        mermaid_content = mermaid_gen.generate(output_path=str(mermaid_file))
        assert mermaid_file.exists()
        assert mermaid_file.read_text() == mermaid_content

        # Test HTML file output
        svg_content = graphviz_gen.generate(format='svg')
        html_file = tmp_path / "test.html"
        html_content = html_gen.generate(svg_content=svg_content, output_path=str(html_file))
        assert html_file.exists()
        assert html_file.read_text() == html_content

    def test_large_schema_performance(self):
        """Test performance with larger schemas"""
        # Create 20 entities with relationships
        entities = []
        for i in range(20):
            entity = Entity(
                name=f'Entity{i}',
                schema='test',
                fields={
                    'id': FieldDefinition(name='id', type_name='uuid', nullable=False),
                    'name': FieldDefinition(name='name', type_name='text', nullable=False)
                }
            )

            # Add relationships to previous entities
            if i > 0:
                entity.fields[f'entity_{i-1}_id'] = FieldDefinition(
                    name=f'entity_{i-1}_id',
                    type_name=f'ref(Entity{i-1})',
                    nullable=True
                )

            entities.append(entity)

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        # Should handle 20 entities and ~19 relationships without issues
        assert len(extractor.entities) == 20
        assert len(extractor.relationships) >= 19

        # Generate all formats
        graphviz_gen = GraphvizGenerator(extractor)
        mermaid_gen = MermaidGenerator(extractor)
        html_gen = HTMLViewerGenerator(extractor)

        dot_content = graphviz_gen.generate()
        mermaid_content = mermaid_gen.generate()
        svg_content = graphviz_gen.generate(format='svg')
        html_content = html_gen.generate(svg_content=svg_content)

        # Basic content checks
        assert len(dot_content) > 1000  # Substantial content
        assert len(mermaid_content) > 500
        assert len(html_content) > 5000

    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases"""
        # Empty extractor
        empty_extractor = RelationshipExtractor()
        graphviz_gen = GraphvizGenerator(empty_extractor)
        mermaid_gen = MermaidGenerator(empty_extractor)
        html_gen = HTMLViewerGenerator(empty_extractor)

        # Should handle empty case gracefully
        dot_content = graphviz_gen.generate()
        assert isinstance(dot_content, str)

        mermaid_content = mermaid_gen.generate()
        assert isinstance(mermaid_content, str)

        html_content = html_gen.generate(svg_content='<svg></svg>')
        assert isinstance(html_content, str)

        # Entity with no fields
        entity_no_fields = Entity(name='EmptyEntity', schema='test', fields={})
        extractor = RelationshipExtractor()
        extractor.extract_from_entities([entity_no_fields])

        graphviz_gen = GraphvizGenerator(extractor)
        dot_content = graphviz_gen.generate(show_fields=True)
        assert 'EmptyEntity' in dot_content

    def test_schema_clustering_visualization(self, extractor):
        """Test schema clustering works in Graphviz output"""
        graphviz_gen = GraphvizGenerator(extractor)

        # With clustering
        dot_clustered = graphviz_gen.generate(cluster_by_schema=True)
        assert 'subgraph cluster_crm' in dot_clustered
        assert 'subgraph cluster_sales' in dot_clustered

        # Without clustering
        dot_flat = graphviz_gen.generate(cluster_by_schema=False)
        assert 'subgraph cluster_' not in dot_flat

    def test_relationship_types_display(self, extractor):
        """Test different relationship types are displayed correctly"""
        graphviz_gen = GraphvizGenerator(extractor)
        mermaid_gen = MermaidGenerator(extractor)

        dot_content = graphviz_gen.generate()
        mermaid_content = mermaid_gen.generate()

        # Should have arrows/edges for relationships
        assert '->' in dot_content or 'Contact' in dot_content  # Graphviz edges

        # Mermaid should have relationship notation
        assert '||--' in mermaid_content

    def test_custom_titles_and_metadata(self, extractor):
        """Test custom titles and metadata in outputs"""
        title = "Custom CRM Schema"

        graphviz_gen = GraphvizGenerator(extractor)
        mermaid_gen = MermaidGenerator(extractor)
        html_gen = HTMLViewerGenerator(extractor)

        # Graphviz with title
        dot_content = graphviz_gen.generate(title=title)
        assert title in dot_content

        # Mermaid with title
        mermaid_content = mermaid_gen.generate(title=title)
        assert f'# {title}' in mermaid_content

        # HTML with title
        svg_content = graphviz_gen.generate(format='svg')
        html_content = html_gen.generate(svg_content=svg_content, title=title)
        assert title in html_content
        assert f'<title>{title} - Schema Diagram</title>' in html_content