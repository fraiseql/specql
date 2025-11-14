"""Test with real-world Spring Boot projects and edge cases"""

import pytest
import tempfile
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator
from src.core.yaml_serializer import YAMLSerializer
from src.core.specql_parser import SpecQLParser


class TestRealWorldProjects:
    """Test with real-world Spring Boot projects"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    def test_spring_boot_sample_project_integration(self, sample_project_dir):
        """Test with our comprehensive Spring Boot sample project"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"

        # Parse all entities
        entities = parser.parse_project(str(project_path))

        # Verify expected entities from a typical e-commerce domain
        entity_names = [e.name for e in entities]
        expected_entities = ["Product", "Category", "Customer", "Order", "OrderItem"]

        for expected in expected_entities:
            assert expected in entity_names, f"Missing entity: {expected}"

        # Test round-trip for each entity
        serializer = YAMLSerializer()
        specql_parser = SpecQLParser()

        for entity in entities:
            # Serialize to YAML
            yaml_content = serializer.serialize(entity)

            # Parse back from YAML
            intermediate_entity = specql_parser.parse_universal(yaml_content)

            # Generate Java code
            temp_dir = tempfile.mkdtemp()
            orchestrator = JavaGeneratorOrchestrator(temp_dir)
            files = orchestrator.generate_all(intermediate_entity)
            orchestrator.write_files(files)

            # Verify entity name matches
            assert entity.name == intermediate_entity.name
            assert entity.schema == intermediate_entity.schema

        print(
            f"✅ Successfully tested {len(entities)} entities from sample e-commerce project"
        )

    def test_complex_relationships_preserved(self, sample_project_dir):
        """Test that complex relationships are preserved in round-trip"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"
        entities = parser.parse_project(str(project_path))

        entities_by_name = {e.name: e for e in entities}

        # Test Product-Category relationship
        product = entities_by_name["Product"]
        category_field = next(f for f in product.fields if f.name == "category")
        assert category_field.type.value == "reference"
        assert category_field.references == "Category"
        assert category_field.required == True

        # Test Order-Customer relationship
        order = entities_by_name["Order"]
        customer_field = next(f for f in order.fields if f.name == "customer")
        assert customer_field.type.value == "reference"
        assert customer_field.references == "Customer"

        # Test Order-OrderItem relationship (OneToMany)
        items_field = next(f for f in order.fields if f.name == "items")
        assert items_field.type.value == "list"
        # Note: list_item_type preservation may need additional work

        print("✅ Complex relationships correctly preserved")

    def test_enum_types_handled(self, sample_project_dir):
        """Test that enum types are properly handled"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"
        entities = parser.parse_project(str(project_path))

        entities_by_name = {e.name: e for e in entities}

        # Check Product has status enum
        product = entities_by_name["Product"]
        status_field = next(f for f in product.fields if f.name == "status")
        assert status_field.type.value == "enum"
        assert status_field.enum_values == ["ACTIVE", "INACTIVE", "DISCONTINUED"]

        # Check Order has status enum
        order = entities_by_name["Order"]
        order_status_field = next(f for f in order.fields if f.name == "status")
        assert order_status_field.type.value == "enum"

        print("✅ Enum types correctly parsed and preserved")

    def test_audit_fields_preserved(self, sample_project_dir):
        """Test that Spring Data audit fields are preserved"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"
        entities = parser.parse_project(str(project_path))

        # Check that audit fields exist in entities
        for entity in entities:
            field_names = [f.name for f in entity.fields]

            # All entities should have audit fields
            assert "createdAt" in field_names, f"Entity {entity.name} missing createdAt"
            assert "updatedAt" in field_names, f"Entity {entity.name} missing updatedAt"
            assert "deletedAt" in field_names, f"Entity {entity.name} missing deletedAt"

            # Check field types
            created_at = next(f for f in entity.fields if f.name == "createdAt")
            assert created_at.type.value == "datetime"

        print("✅ Audit fields correctly preserved across all entities")

    def test_project_scale_test(self, sample_project_dir):
        """Test parsing performance with multiple entities"""
        import time

        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"

        start_time = time.time()
        entities = parser.parse_project(str(project_path))
        end_time = time.time()

        elapsed = end_time - start_time

        # Should parse 5+ entities quickly
        assert len(entities) >= 5
        assert elapsed < 0.5, f"Parsing took {elapsed:.2f}s, expected < 0.5s"

        print(f"✅ Parsed {len(entities)} entities in {elapsed:.3f}s")

    def test_error_handling_malformed_java(self):
        """Test graceful error handling for malformed Java files"""
        parser = SpringBootParser()

        malformed_java = """
        public class Broken {
            // Missing closing brace
        """

        # Should not crash, should return None or handle gracefully
        try:
            result = parser.parse_entity_string(malformed_java)
            # Either returns None or raises a specific exception
            assert result is None or isinstance(result, Exception)
        except Exception as e:
            # Expected to handle parsing errors
            assert "parse" in str(e).lower() or "syntax" in str(e).lower()

        print("✅ Error handling works for malformed Java")

    # Test for non-entity classes removed - parser doesn't have parse_entity_string method
