from src.generators.diagrams.mermaid_generator import MermaidGenerator
from src.generators.diagrams.relationship_extractor import RelationshipExtractor
from src.core.ast_models import Entity, FieldDefinition

class TestMermaidGenerator:

    def test_generate_simple_diagram(self):
        """Test generating simple Mermaid ERD"""
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

        generator = MermaidGenerator(extractor)
        mermaid_source = generator.generate()

        # Check Mermaid structure
        assert '```mermaid' in mermaid_source
        assert 'erDiagram' in mermaid_source
        assert 'Company' in mermaid_source
        assert 'Contact' in mermaid_source
        assert 'company_id' in mermaid_source
        assert '||--||' in mermaid_source  # Required relationship

    def test_relationship_notation(self):
        """Test different relationship notations"""
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
                    'company_id': FieldDefinition(name='company_id', type_name='ref(Company)', nullable=True)  # Optional
                }
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = MermaidGenerator(extractor)
        mermaid_source = generator.generate()

        # Should use optional notation for nullable FK
        assert '||--o{' in mermaid_source

    def test_entity_fields_display(self):
        """Test entity fields are displayed correctly"""
        entity = Entity(
            name='User',
            schema='auth',
            fields={
                'id': FieldDefinition(name='id', type_name='uuid', nullable=False),
                'email': FieldDefinition(name='email', type_name='text', nullable=False),
                'name': FieldDefinition(name='name', type_name='text', nullable=True)
            }
        )

        extractor = RelationshipExtractor()
        extractor.extract_from_entities([entity])

        generator = MermaidGenerator(extractor)
        mermaid_source = generator.generate(show_fields=True, show_trinity=True)

        # Check entity definition block
        assert 'User {' in mermaid_source
        assert 'uuid id' in mermaid_source
        assert 'text email' in mermaid_source
        assert 'text name' in mermaid_source

    def test_hide_trinity_fields(self):
        """Test hiding Trinity pattern fields"""
        entity = Entity(
            name='Contact',
            schema='crm',
            fields={
                'pk_contact': FieldDefinition(name='pk_contact', type_name='uuid', nullable=False),
                'id': FieldDefinition(name='id', type_name='uuid', nullable=False),
                'identifier': FieldDefinition(name='identifier', type_name='text', nullable=False),
                'email': FieldDefinition(name='email', type_name='text', nullable=False)
            }
        )

        extractor = RelationshipExtractor()
        extractor.extract_from_entities([entity])

        generator = MermaidGenerator(extractor)
        mermaid_source = generator.generate(show_fields=True, show_trinity=False)

        # Trinity fields should be hidden (check for field declarations, not just field names)
        assert 'uuid pk_contact' not in mermaid_source
        assert 'uuid id' not in mermaid_source
        assert 'text identifier' not in mermaid_source
        # But other fields should be shown
        assert 'text email' in mermaid_source

    def test_title_inclusion(self):
        """Test title is included in output"""
        entities = [
            Entity(name='Test', schema='test', fields={})
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = MermaidGenerator(extractor)
        mermaid_source = generator.generate(title="Test Diagram")

        assert '# Test Diagram' in mermaid_source

    def test_output_to_file(self, tmp_path):
        """Test saving to file"""
        entities = [
            Entity(name='Test', schema='test', fields={})
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = MermaidGenerator(extractor)
        output_file = tmp_path / "test.md"

        generator.generate(output_path=str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert '```mermaid' in content
        assert 'erDiagram' in content

    def test_self_referential_relationship(self):
        """Test self-referential relationship"""
        entity = Entity(
            name='Employee',
            schema='hr',
            fields={
                'name': FieldDefinition(name='name', type_name='text', nullable=False),
                'manager_id': FieldDefinition(name='manager_id', type_name='ref(Employee)', nullable=True)
            }
        )

        extractor = RelationshipExtractor()
        extractor.extract_from_entities([entity])

        generator = MermaidGenerator(extractor)
        mermaid_source = generator.generate()

        # Should have self-relationship
        assert 'Employee ||--o{ Employee' in mermaid_source

    def test_multiple_relationships(self):
        """Test multiple relationships between entities"""
        entities = [
            Entity(
                name='User',
                schema='auth',
                fields={
                    'id': FieldDefinition(name='id', type_name='uuid', nullable=False)
                }
            ),
            Entity(
                name='Post',
                schema='blog',
                fields={
                    'author_id': FieldDefinition(name='author_id', type_name='ref(User)', nullable=False),
                    'editor_id': FieldDefinition(name='editor_id', type_name='ref(User)', nullable=True)
                }
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        generator = MermaidGenerator(extractor)
        mermaid_source = generator.generate()

        # Should have both relationships
        assert 'Post ||--|| User : "author_id"' in mermaid_source
        assert 'Post ||--o{ User : "editor_id"' in mermaid_source