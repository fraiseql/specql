import pytest
from pathlib import Path
import json
from src.generators.diagrams.html_viewer_generator import HTMLViewerGenerator
from src.generators.diagrams.relationship_extractor import RelationshipExtractor
from src.core.ast_models import Entity, FieldDefinition

class TestHTMLViewerGenerator:

    def test_generate_basic_html(self):
        """Test generating basic HTML viewer"""
        entities = [
            Entity(
                name='Company',
                schema='crm',
                fields={
                    'name': FieldDefinition(name='name', type_name='text', nullable=False)
                }
            ),
            Entity(
                name='Contact',
                schema='crm',
                fields={
                    'email': FieldDefinition(name='email', type_name='text', nullable=False),
                    'company_id': FieldDefinition(name='company_id', type_name='ref(Company)', nullable=False)
                }
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg><text>Test SVG</text></svg>'

        html = generator.generate(svg_content=svg_content, output_path=None, title="Test Diagram")

        # Check HTML structure
        assert '<!DOCTYPE html>' in html
        assert 'Test Diagram' in html
        assert 'Test SVG' in html
        assert 'Company' in html
        assert 'Contact' in html

    def test_entity_list_generation(self):
        """Test entity list HTML generation"""
        entities = [
            Entity(name='User', schema='auth', fields={'id': FieldDefinition(name='id', type_name='uuid', nullable=False)}),
            Entity(name='Post', schema='blog', fields={'title': FieldDefinition(name='title', type_name='text', nullable=False)})
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg></svg>'

        html = generator.generate(svg_content=svg_content, output_path=None)

        # Check entity list
        assert 'data-entity="User"' in html
        assert 'data-entity="Post"' in html
        assert 'auth • 1 fields' in html
        assert 'blog • 1 fields' in html

    def test_statistics_display(self):
        """Test statistics panel in HTML"""
        entities = [
            Entity(name='A', schema='s1', fields={}),
            Entity(name='B', schema='s1', fields={}),
            Entity(name='C', schema='s2', fields={}),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg></svg>'

        html = generator.generate(svg_content=svg_content, output_path=None)

        # Check statistics
        assert '3 entities' in html
        assert '2' in html  # Schema count

    def test_entities_json_data(self):
        """Test entities JSON data embedded in HTML"""
        entity = Entity(
            name='Test',
            schema='test',
            fields={
                'id': FieldDefinition(name='id', type_name='uuid', nullable=False),
                'name': FieldDefinition(name='name', type_name='text', nullable=True)
            }
        )

        extractor = RelationshipExtractor()
        extractor.extract_from_entities([entity])

        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg></svg>'

        html = generator.generate(svg_content=svg_content, output_path=None)

        # Extract JSON data from HTML
        start = html.find('const entities = ') + len('const entities = ')
        end = html.find(';', start)
        json_str = html[start:end].strip()

        entities_data = json.loads(json_str)

        assert 'Test' in entities_data
        assert entities_data['Test']['schema'] == 'test'
        assert len(entities_data['Test']['fields']) == 2
        assert entities_data['Test']['fields'][0]['name'] == 'id'
        assert entities_data['Test']['fields'][1]['name'] == 'name'

    def test_svg_content_embedding(self):
        """Test SVG content is properly embedded and escaped"""
        extractor = RelationshipExtractor()
        generator = HTMLViewerGenerator(extractor)

        # SVG with backticks that need escaping
        svg_content = '<svg><text>`backtick`</text></svg>'
        html = generator.generate(svg_content=svg_content, output_path=None)

        # Should be escaped in the JavaScript string
        assert '\\`backtick\\`' in html
        # Original SVG should not be present (it's embedded in JS)
        assert svg_content not in html

    def test_output_to_file(self, tmp_path):
        """Test saving HTML to file"""
        entities = [Entity(name='Test', schema='test', fields={})]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg></svg>'

        output_file = tmp_path / "test.html"
        generator.generate(svg_content=svg_content, output_path=str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert '<!DOCTYPE html>' in content
        assert 'Test' in content

    def test_custom_title(self):
        """Test custom title in HTML"""
        extractor = RelationshipExtractor()
        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg></svg>'

        html = generator.generate(svg_content=svg_content, output_path=None, title="Custom Title")

        assert 'Custom Title' in html
        assert '<title>Custom Title - Schema Diagram</title>' in html

    def test_relationship_statistics(self):
        """Test relationship count in HTML"""
        entities = [
            Entity(
                name='Parent',
                schema='test',
                fields={'id': FieldDefinition(name='id', type_name='uuid', nullable=False)}
            ),
            Entity(
                name='Child',
                schema='test',
                fields={
                    'parent_id': FieldDefinition(name='parent_id', type_name='ref(Parent)', nullable=False)
                }
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg></svg>'

        html = generator.generate(svg_content=svg_content, output_path=None)

        assert '1 relationships' in html

    def test_empty_extractor(self):
        """Test HTML generation with empty extractor"""
        extractor = RelationshipExtractor()
        generator = HTMLViewerGenerator(extractor)
        svg_content = '<svg></svg>'

        html = generator.generate(svg_content=svg_content, output_path=None)

        assert '<!DOCTYPE html>' in html
        assert '0 entities' in html
        assert '0 relationships' in html