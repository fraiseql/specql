"""Test multi-entity reverse engineering and generation"""

import pytest
from pathlib import Path
from src.parsers.rust.diesel_parser import DieselParser


class TestMultiEntityIntegration:
    """Test parsing multiple related entities"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Diesel project"""
        return Path(__file__).parent / "sample_project" / "src"

    def test_parse_all_entities(self, sample_project_dir):
        """Test parsing all entities in the project"""
        parser = DieselParser()
        models_path = sample_project_dir / "models"
        schema_path = sample_project_dir / "schema.rs"

        entities = parser.parse_project(str(models_path), str(schema_path))

        # Verify all entities were parsed
        entity_names = [e.name for e in entities]
        assert "Product" in entity_names
        assert "Category" in entity_names
        assert "Customer" in entity_names
        assert "Order" in entity_names
        assert "OrderItem" in entity_names

        assert len(entities) >= 5

    def test_relationships_between_entities(self, sample_project_dir):
        """Test that relationships are correctly parsed"""
        parser = DieselParser()
        models_path = sample_project_dir / "models"
        schema_path = sample_project_dir / "schema.rs"

        entities = parser.parse_project(str(models_path), str(schema_path))
        entities_by_name = {e.name: e for e in entities}

        # Check Product → Category relationship
        product = entities_by_name["Product"]
        category_field = next(f for f in product.fields if f.name == "category_id")
        assert category_field.type.value == "reference"
        assert category_field.references == "category"

        # Check Order → Customer relationship
        order = entities_by_name["Order"]
        customer_field = next(f for f in order.fields if f.name == "customer_id")
        assert customer_field.type.value == "reference"
        assert customer_field.references == "customer"

        # Check OrderItem → Order relationship
        order_item = entities_by_name["OrderItem"]
        order_field = next(f for f in order_item.fields if f.name == "order_id")
        assert order_field.type.value == "reference"
        assert order_field.references == "order"

        # Check OrderItem → Product relationship
        product_field = next(f for f in order_item.fields if f.name == "product_id")
        assert product_field.type.value == "reference"
        assert product_field.references == "product"

    def test_enum_fields_detected(self, sample_project_dir):
        """Test that enum fields are properly detected"""
        parser = DieselParser()
        models_path = sample_project_dir / "models"
        schema_path = sample_project_dir / "schema.rs"

        entities = parser.parse_project(str(models_path), str(schema_path))
        entities_by_name = {e.name: e for e in entities}

        # Check Product status enum
        product = entities_by_name["Product"]
        status_field = next(f for f in product.fields if f.name == "status")
        assert status_field.type.value == "enum"

        # Check Order status enum
        order = entities_by_name["Order"]
        order_status_field = next(f for f in order.fields if f.name == "status")
        assert order_status_field.type.value == "enum"

    def test_json_fields_detected(self, sample_project_dir):
        """Test that JSON fields are properly detected"""
        parser = DieselParser()
        models_path = sample_project_dir / "models"
        schema_path = sample_project_dir / "schema.rs"

        entities = parser.parse_project(str(models_path), str(schema_path))
        entities_by_name = {e.name: e for e in entities}

        # Check Customer address JSON field
        customer = entities_by_name["Customer"]
        address_field = next(f for f in customer.fields if f.name == "address")
        # JSON fields should be detected as text for now
        assert address_field.type.value in ["text", "jsonb"]
