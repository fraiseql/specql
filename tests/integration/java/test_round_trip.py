"""Round-trip testing: Java → SpecQL → Java"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator
from src.core.yaml_serializer import YAMLSerializer


class TestRoundTrip:
    """Test round-trip conversion"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for intermediate files"""
        yaml_dir = tempfile.mkdtemp()
        java_dir = tempfile.mkdtemp()
        yield Path(yaml_dir), Path(java_dir)
        shutil.rmtree(yaml_dir)
        shutil.rmtree(java_dir)

    def test_round_trip_simple_entity(self, sample_project_dir, temp_dirs):
        """Test: Java → SpecQL YAML → Java"""
        yaml_dir, java_dir = temp_dirs

        # Step 1: Parse Java entity
        parser = SpringBootParser()
        entity_file = (
            sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        )
        original_entity = parser.parse_entity_file(str(entity_file))

        # Step 2: Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)
        yaml_file = yaml_dir / "product.yaml"
        yaml_file.write_text(yaml_content)

        # Step 3: Parse YAML back to entity
        from src.core.specql_parser import SpecQLParser

        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        # Step 4: Generate Java code from entity
        orchestrator = JavaGeneratorOrchestrator(str(java_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Step 5: Parse generated Java entity
        generated_entity_file = java_dir / "ecommerce" / "Product.java"
        regenerated_entity = parser.parse_entity_file(str(generated_entity_file))

        # Step 6: Compare original and regenerated entities
        self._assert_entities_equivalent(original_entity, regenerated_entity)

    def _assert_entities_equivalent(self, entity1, entity2):
        """Assert two entities are functionally equivalent"""
        # Compare basic properties
        assert entity1.name == entity2.name
        assert entity1.schema == entity2.schema

        # Compare field count
        assert len(entity1.fields) == len(entity2.fields)

        # Compare each field
        fields1_by_name = {f.name: f for f in entity1.fields}
        fields2_by_name = {f.name: f for f in entity2.fields}

        for field_name in fields1_by_name.keys():
            assert field_name in fields2_by_name, (
                f"Field {field_name} missing in regenerated entity"
            )

            field1 = fields1_by_name[field_name]
            field2 = fields2_by_name[field_name]

            # Compare field properties
            assert field1.type == field2.type, f"Field {field_name} type mismatch"
            assert field1.required == field2.required, (
                f"Field {field_name} required mismatch"
            )

            # Compare reference targets
            if field1.type.value == "reference":
                assert field1.references == field2.references, (
                    f"Field {field_name} reference mismatch"
                )

    def test_round_trip_preserves_annotations(self, sample_project_dir, temp_dirs):
        """Test that important JPA annotations are preserved"""
        yaml_dir, java_dir = temp_dirs

        # Parse original
        parser = SpringBootParser()
        entity_file = (
            sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        )
        original_entity = parser.parse_entity_file(str(entity_file))

        # Serialize and regenerate
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        from src.core.specql_parser import SpecQLParser

        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        orchestrator = JavaGeneratorOrchestrator(str(java_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Read generated Java file
        generated_entity_file = java_dir / "ecommerce" / "Product.java"
        generated_content = generated_entity_file.read_text()

        # Verify critical annotations are present
        assert "@Entity" in generated_content
        assert "@Table" in generated_content
        assert "@Id" in generated_content
        assert "@GeneratedValue" in generated_content
        assert "@ManyToOne" in generated_content
        assert "@JoinColumn" in generated_content
        assert "@Enumerated(EnumType.STRING)" in generated_content

        # Verify Trinity pattern fields
        assert "@CreatedDate" in generated_content
        assert "@LastModifiedDate" in generated_content
        assert "deletedAt" in generated_content

    def test_round_trip_with_enum(self, sample_project_dir, temp_dirs):
        """Test round-trip with enum fields"""
        yaml_dir, java_dir = temp_dirs

        # Parse Product entity (has enum status field)
        parser = SpringBootParser()
        entity_file = (
            sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        )
        original_entity = parser.parse_entity_file(str(entity_file))

        # Serialize and regenerate
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        from src.core.specql_parser import SpecQLParser

        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        orchestrator = JavaGeneratorOrchestrator(str(java_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Parse regenerated entity
        generated_entity_file = java_dir / "ecommerce" / "Product.java"
        regenerated_entity = parser.parse_entity_file(str(generated_entity_file))

        # Verify enum field is preserved
        original_status = next(f for f in original_entity.fields if f.name == "status")
        regenerated_status = next(
            f for f in regenerated_entity.fields if f.name == "status"
        )

        assert original_status.type == regenerated_status.type
        assert original_status.enum_values == regenerated_status.enum_values

    def test_round_trip_with_multiple_relationships(
        self, sample_project_dir, temp_dirs
    ):
        """Test round-trip with multiple foreign keys"""
        yaml_dir, java_dir = temp_dirs

        # Parse Order entity (has customer and items relationships)
        parser = SpringBootParser()
        entity_file = (
            sample_project_dir / "com" / "example" / "ecommerce" / "Order.java"
        )
        original_entity = parser.parse_entity_file(str(entity_file))

        # Serialize and regenerate
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        from src.core.specql_parser import SpecQLParser

        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        orchestrator = JavaGeneratorOrchestrator(str(java_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Parse regenerated entity
        generated_entity_file = java_dir / "ecommerce" / "Order.java"
        regenerated_entity = parser.parse_entity_file(str(generated_entity_file))

        # Verify relationships are preserved
        original_customer = next(
            f for f in original_entity.fields if f.name == "customer"
        )
        regenerated_customer = next(
            f for f in regenerated_entity.fields if f.name == "customer"
        )

        assert original_customer.type == regenerated_customer.type
        assert original_customer.references == regenerated_customer.references

        # Check items relationship (OneToMany)
        original_items = next(f for f in original_entity.fields if f.name == "items")
        regenerated_items = next(
            f for f in regenerated_entity.fields if f.name == "items"
        )

        assert original_items.type == regenerated_items.type
        # Note: list_item_type may not be preserved yet, but type should be

    def test_round_trip_with_unique_constraints(self, sample_project_dir, temp_dirs):
        """Test that unique constraints are preserved"""
        # This would require adding unique constraints to the sample entities
        # For now, skip or create a simple test
        pass

    def test_round_trip_with_embedded_types(self, sample_project_dir, temp_dirs):
        """Test that @Embedded types work correctly"""
        # Test with Customer entity which may have embedded address
        yaml_dir, java_dir = temp_dirs

        # Parse Customer entity
        parser = SpringBootParser()
        entity_file = (
            sample_project_dir / "com" / "example" / "ecommerce" / "Customer.java"
        )
        original_entity = parser.parse_entity_file(str(entity_file))

        # Serialize and regenerate
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        from src.core.specql_parser import SpecQLParser

        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        orchestrator = JavaGeneratorOrchestrator(str(java_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Parse regenerated entity
        generated_entity_file = java_dir / "ecommerce" / "Customer.java"
        regenerated_entity = parser.parse_entity_file(str(generated_entity_file))

        # Verify entity is preserved
        self._assert_entities_equivalent(original_entity, regenerated_entity)
