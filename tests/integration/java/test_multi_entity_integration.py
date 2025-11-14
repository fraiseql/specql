"""Test multi-entity reverse engineering and generation"""

import pytest
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser


class TestMultiEntityIntegration:
    """Test parsing multiple related entities"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    def test_parse_all_entities(self, sample_project_dir):
        """Test parsing all entities in the project"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"

        entities = parser.parse_project(str(project_path))

        # Verify all entities were parsed
        entity_names = [e.name for e in entities]
        assert "Product" in entity_names
        assert "Category" in entity_names
        assert "Customer" in entity_names
        assert "Order" in entity_names
        assert "OrderItem" in entity_names
        assert "Category" in entity_names
        assert "Customer" in entity_names
        assert "Order" in entity_names
        assert "OrderItem" in entity_names

    def test_relationships_between_entities(self, sample_project_dir):
        """Test that relationships are correctly parsed"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"

        entities = parser.parse_project(str(project_path))
        entities_by_name = {e.name: e for e in entities}

        # Check Product → Category relationship
        product = entities_by_name["Product"]
        category_field = next(f for f in product.fields if f.name == "category")
        assert category_field.type.value == "reference"
        assert category_field.references == "Category"

        # Check Order → Customer relationship
        order = entities_by_name["Order"]
        customer_field = next(f for f in order.fields if f.name == "customer")
        assert customer_field.type.value == "reference"
        assert customer_field.references == "Customer"

        # Check Order → OrderItem relationship (OneToMany)
        items_field = next(f for f in order.fields if f.name == "items")
        assert items_field.type.value == "list"
        # Relationship metadata should be captured
