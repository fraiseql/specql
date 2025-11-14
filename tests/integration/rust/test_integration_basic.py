"""Basic integration tests for Rust reverse engineering and generation"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.rust.diesel_parser import DieselParser


class TestBasicIntegration:
    """Test basic reverse engineering and generation"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Diesel project"""
        return Path(__file__).parent / "sample_project" / "src"

    @pytest.fixture
    def temp_output_dir(self):
        """Temporary directory for generated code"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_reverse_engineer_simple_model(self, sample_project_dir):
        """Test reverse engineering a simple Diesel model"""
        # Parse Product model
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "product.rs"
        schema_file = sample_project_dir / "schema.rs"

        entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Verify parsed entity
        assert entity.name == "Product"
        assert entity.schema == "public"  # Default schema

        # Verify fields
        field_names = [f.name for f in entity.fields]
        assert "name" in field_names
        assert "price" in field_names
        assert "active" in field_names
        assert "status" in field_names
        assert "category_id" in field_names

        # Verify field types
        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.required == True

        price_field = next(f for f in entity.fields if f.name == "price")
        assert price_field.type.value == "integer"

        active_field = next(f for f in entity.fields if f.name == "active")
        assert active_field.type.value == "boolean"
        # TODO: Check default value parsing

        status_field = next(f for f in entity.fields if f.name == "status")
        assert status_field.type.value == "enum"

        category_field = next(f for f in entity.fields if f.name == "category_id")
        assert category_field.type.value == "reference"
        assert category_field.references == "category"
        assert category_field.required == True

    def test_generate_from_reversed_model(self, sample_project_dir, temp_output_dir):
        """Test generating Rust code from a reversed model"""
        # Parse original model
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "product.rs"
        schema_file = sample_project_dir / "schema.rs"
        entity = parser.parse_model_file(str(model_file), str(schema_file))

        # For now, just verify the entity was parsed correctly
        # TODO: Test code generation once generators are working
        assert entity.name == "Product"
        assert len(entity.fields) > 0
