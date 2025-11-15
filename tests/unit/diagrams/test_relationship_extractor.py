from src.generators.diagrams.relationship_extractor import (
    RelationshipExtractor,
    RelationshipType,
    RelationshipCardinality
)
from src.core.ast_models import Entity, FieldDefinition

class TestRelationshipExtractor:

    def test_extract_simple_relationship(self):
        """Test extracting simple FK relationship"""
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

        assert len(extractor.relationships) == 1

        rel = extractor.relationships[0]
        assert rel.from_entity == 'Contact'
        assert rel.to_entity == 'Company'
        assert rel.from_field == 'company_id'
        assert rel.relationship_type == RelationshipType.MANY_TO_ONE

    def test_detect_self_referential(self):
        """Test detecting self-referential relationship"""
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

        assert len(extractor.relationships) == 1

        rel = extractor.relationships[0]
        assert rel.from_entity == 'Employee'
        assert rel.to_entity == 'Employee'
        assert rel.relationship_type == RelationshipType.SELF_REFERENTIAL

    def test_nullable_relationship(self):
        """Test nullable FK has correct cardinality"""
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
                    'company_id': FieldDefinition(name='company_id', type_name='ref(Company)', nullable=True)
                }
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        rel = extractor.relationships[0]
        assert rel.nullable is True
        assert rel.from_cardinality == RelationshipCardinality.ZERO_OR_ONE

class TestDependencyGraph:

    def test_topological_order(self):
        """Test topological sorting"""
        from src.generators.diagrams.dependency_graph import DependencyGraph

        entities = [
            Entity(name='Company', schema='crm', fields={}),
            Entity(
                name='Contact',
                schema='crm',
                fields={
                    'company_id': FieldDefinition(name='company_id', type_name='ref(Company)', nullable=False)
                }
            ),
            Entity(
                name='Order',
                schema='crm',
                fields={
                    'contact_id': FieldDefinition(name='contact_id', type_name='ref(Contact)', nullable=False)
                }
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        graph = DependencyGraph(extractor)
        order = graph.get_topological_order()

        # Company should come before Contact, Contact before Order
        assert order.index('Company') < order.index('Contact')
        assert order.index('Contact') < order.index('Order')

    def test_cycle_detection(self):
        """Test detecting circular dependencies"""
        from src.generators.diagrams.dependency_graph import DependencyGraph

        # Create circular dependency: A → B → C → A
        entities = [
            Entity(
                name='A',
                schema='test',
                fields={
                    'b_id': FieldDefinition(name='b_id', type_name='ref(B)', nullable=False)
                }
            ),
            Entity(
                name='B',
                schema='test',
                fields={
                    'c_id': FieldDefinition(name='c_id', type_name='ref(C)', nullable=False)
                }
            ),
            Entity(
                name='C',
                schema='test',
                fields={
                    'a_id': FieldDefinition(name='a_id', type_name='ref(A)', nullable=False)
                }
            ),
        ]

        extractor = RelationshipExtractor()
        extractor.extract_from_entities(entities)

        graph = DependencyGraph(extractor)
        cycles = graph.detect_cycles()

        assert len(cycles) > 0
        # Should detect the A-B-C cycle