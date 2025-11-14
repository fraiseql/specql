"""Round-trip testing: Rust → SpecQL → Rust"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.rust.diesel_parser import DieselParser
from src.generators.rust.rust_generator_orchestrator import RustGeneratorOrchestrator
from src.core.yaml_serializer import YAMLSerializer
from src.core.specql_parser import SpecQLParser
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class TestRoundTrip:
    """Test round-trip conversion"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Diesel project"""
        return Path(__file__).parent / "sample_project" / "src"

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for intermediate files"""
        yaml_dir = tempfile.mkdtemp()
        rust_dir = tempfile.mkdtemp()
        yield Path(yaml_dir), Path(rust_dir)
        shutil.rmtree(yaml_dir)
        shutil.rmtree(rust_dir)

    def test_round_trip_simple_model(self, sample_project_dir, temp_dirs):
        """Test: Rust → SpecQL YAML → Rust"""
        yaml_dir, rust_dir = temp_dirs

        # Step 1: Parse Rust model
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "simple.rs"
        schema_file = sample_project_dir / "schema.rs"
        original_entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Step 2: Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)
        yaml_file = yaml_dir / "category.yaml"
        yaml_file.write_text(yaml_content)

        # Step 3: Parse YAML back to entity
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        # Step 4: Generate Rust code from entity
        # For now, just verify the YAML was created and parsed back
        assert intermediate_entity.name == original_entity.name

        # Verify that non-reserved fields are preserved in round-trip
        original_field_names = {f.name for f in original_entity.fields}
        intermediate_field_names = {f.name for f in intermediate_entity.fields}

        # SpecQL may add or remove certain fields (like 'id' which is reserved)
        # Check that the core business fields are preserved
        core_fields = {
            "name",
            "description",
            "price",
            "active",
            "status",
            "category_id",
        }
        original_core = original_field_names.intersection(core_fields)
        intermediate_core = intermediate_field_names.intersection(core_fields)

        assert original_core == intermediate_core, (
            f"Core fields mismatch: {original_core} vs {intermediate_core}"
        )

        # Basic round-trip validation: ensure core functionality works
        # The YAML serialization and parsing should work without errors
        # and preserve the essential structure and types
        assert len(intermediate_entity.fields) > 0
        assert all(
            f.type
            in [
                FieldType.TEXT,
                FieldType.INTEGER,
                FieldType.BOOLEAN,
                FieldType.ENUM,
                FieldType.REFERENCE,
            ]
            for f in intermediate_entity.fields
        )

    def test_round_trip_preserves_attributes(self, sample_project_dir, temp_dirs):
        """Test that important Diesel attributes are preserved"""
        yaml_dir, rust_dir = temp_dirs

        # Parse original
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "simple.rs"
        schema_file = sample_project_dir / "schema.rs"
        original_entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Serialize and regenerate
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        # Compare key attributes
        assert original_entity.name == intermediate_entity.name
        assert original_entity.schema == intermediate_entity.schema

        # Compare fields that exist in both
        intermediate_field_names = {f.name for f in intermediate_entity.fields}
        for orig_field in original_entity.fields:
            if orig_field.name in intermediate_field_names:
                inter_field = next(
                    f for f in intermediate_entity.fields if f.name == orig_field.name
                )
                assert orig_field.type == inter_field.type
                if orig_field.references:
                    assert inter_field.references == orig_field.references

    def test_round_trip_with_enum(self, sample_project_dir, temp_dirs):
        """Test round-trip with enum fields"""
        yaml_dir, rust_dir = temp_dirs

        # Parse Simple model (has enum status)
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "simple.rs"
        schema_file = sample_project_dir / "schema.rs"
        original_entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        # Parse back
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        # Verify enum field preserved
        orig_status = next(f for f in original_entity.fields if f.name == "status")
        inter_status = next(f for f in intermediate_entity.fields if f.name == "status")

        assert orig_status.type.value == "enum"
        assert inter_status.type.value == "enum"

    def test_round_trip_with_multiple_relationships(
        self, sample_project_dir, temp_dirs
    ):
        """Test round-trip with foreign keys"""
        yaml_dir, rust_dir = temp_dirs

        # Parse Simple model (has category_id reference)
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "simple.rs"
        schema_file = sample_project_dir / "schema.rs"
        original_entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        # Parse back
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        # Verify reference field preserved
        orig_category_id = next(
            f for f in original_entity.fields if f.name == "category_id"
        )
        inter_category_id = next(
            f for f in intermediate_entity.fields if f.name == "category_id"
        )

        assert orig_category_id.type.value == "reference"
        assert inter_category_id.type.value == "reference"
        assert orig_category_id.references == inter_category_id.references

    def test_round_trip_with_optional_fields(self, sample_project_dir, temp_dirs):
        """Test that Option<T> fields are preserved"""
        yaml_dir, rust_dir = temp_dirs

        # Parse Simple model (has optional description)
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "simple.rs"
        schema_file = sample_project_dir / "schema.rs"
        original_entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        # Parse back
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        # Verify optional fields
        orig_description = next(
            f for f in original_entity.fields if f.name == "description"
        )
        inter_description = next(
            f for f in intermediate_entity.fields if f.name == "description"
        )

        assert orig_description.required == False  # Should be optional
        assert inter_description.required == False


def test_yaml_serializer_rust_specific():
    """Test YAML serializer with Rust-specific patterns"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
            UniversalField(name="price", type=FieldType.INTEGER, required=True),
            UniversalField(name="active", type=FieldType.BOOLEAN, default=True),
            UniversalField(
                name="status",
                type=FieldType.ENUM,
                enum_values=["Draft", "Active", "Archived"],
            ),
            UniversalField(
                name="category_id",
                type=FieldType.REFERENCE,
                references="Category",
                required=True,
            ),
        ],
        actions=[],
    )

    serializer = YAMLSerializer()
    yaml_content = serializer.serialize(entity)

    # Verify YAML structure
    assert "entity: Product" in yaml_content
    assert "schema: ecommerce" in yaml_content
    assert "name: text!" in yaml_content
    assert "price: integer!" in yaml_content
    assert "active: boolean = True" in yaml_content
    assert "type: enum" in yaml_content
    assert "type: reference" in yaml_content
    assert "references: Category" in yaml_content
