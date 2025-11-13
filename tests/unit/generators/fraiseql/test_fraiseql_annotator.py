"""Tests for FraiseQL annotation generation"""

import pytest
from src.generators.fraiseql.fraiseql_annotator import FraiseQLAnnotator
from src.core.ast_models import Entity, FieldDefinition


class TestFraiseQLAnnotations:
    """Test FraiseQL metadata annotation generation"""

    @pytest.fixture
    def annotator(self):
        return FraiseQLAnnotator()

    @pytest.fixture
    def sample_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            description="Customer contact information",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False, description="Email address"),
                "company": FieldDefinition(name="company", type_name="ref", reference_entity="Company", description="Company reference"),
            }
        )

    def test_table_annotation(self, annotator, sample_entity):
        """Test base table gets FraiseQL annotation"""
        # Act
        result = annotator.annotate_table(sample_entity)

        # Assert
        assert "@fraiseql:entity" in result
        assert "name: Contact" in result
        assert "trinity: base_table" in result

    def test_table_view_annotation(self, annotator, sample_entity):
        """Test table view gets FraiseQL annotation"""
        # Act
        result = annotator.annotate_table_view(sample_entity)

        # Assert
        assert "@fraiseql:type" in result
        assert "name: Contact" in result
        assert "trinity: table_view" in result
        assert "query: true" in result

    def test_field_annotations(self, annotator, sample_entity):
        """Test field comments include FraiseQL metadata"""
        # Act
        result = annotator.annotate_fields(sample_entity)

        # Assert
        assert "@fraiseql:field" in result
        assert "name: email" in result
        assert "type: String!" in result

    def test_ref_field_annotations(self, annotator, sample_entity):
        """Test reference fields get proper FraiseQL annotations"""
        # Act
        result = annotator.annotate_fields(sample_entity)

        # Assert
        assert "name: company" in result
        assert "type: Company!" in result
        assert "relation: many_to_one" in result

    def test_helper_function_annotations(self, annotator, sample_entity):
        """Test Trinity helper functions get FraiseQL annotations"""
        # Act
        result = annotator.annotate_helper_functions(sample_entity)

        # Assert
        assert "@fraiseql:helper" in result
        assert "entity: Contact" in result
        assert "converts: UUID|INTEGER -> INTEGER" in result
        assert "converts: INTEGER -> UUID" in result