"""Basic integration tests for Java reverse engineering and generation"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator


class TestBasicIntegration:
    """Test basic reverse engineering and generation"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    @pytest.fixture
    def temp_output_dir(self):
        """Temporary directory for generated code"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_reverse_engineer_simple_entity(self, sample_project_dir):
        """Test reverse engineering a simple JPA entity"""
        # Parse Product.java
        parser = SpringBootParser()
        entity_file = (
            sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        )

        entity = parser.parse_entity_file(str(entity_file))

        # Verify parsed entity
        assert entity.name == "Product"
        assert entity.schema == "ecommerce"

        # Verify fields
        field_names = [f.name for f in entity.fields]
        assert "name" in field_names
        assert "price" in field_names
        assert "active" in field_names
        assert "status" in field_names
        assert "category" in field_names

        # Verify field types
        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.required  is True

        price_field = next(f for f in entity.fields if f.name == "price")
        assert price_field.type.value == "integer"

        active_field = next(f for f in entity.fields if f.name == "active")
        assert active_field.default  is True

        status_field = next(f for f in entity.fields if f.name == "status")
        assert status_field.type.value == "enum"

        category_field = next(f for f in entity.fields if f.name == "category")
        assert category_field.type.value == "reference"
        assert category_field.references == "Category"
        assert category_field.required  is True

    def test_generate_from_reversed_entity(self, sample_project_dir, temp_output_dir):
        """Test generating Java code from a reversed entity"""
        # Parse original entity
        parser = SpringBootParser()
        entity_file = (
            sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        )
        entity = parser.parse_entity_file(str(entity_file))

        # Generate Java code
        orchestrator = JavaGeneratorOrchestrator(str(temp_output_dir))
        generated_files = orchestrator.generate_all(entity)
        orchestrator.write_files(generated_files)

        # Verify files were created
        assert len(generated_files) >= 4  # Entity, Repository, Service, Controller

        # Check entity file exists
        entity_file_path = temp_output_dir / "ecommerce" / "Product.java"
        assert entity_file_path.exists()

        # Read generated entity
        generated_content = entity_file_path.read_text()

        # Verify key annotations
        assert "@Entity" in generated_content
        assert '@Table(name = "tb_product")' in generated_content
        assert "public class Product" in generated_content

        # Verify fields
        assert "private String name;" in generated_content
        assert "private Integer price;" in generated_content
        assert "private Boolean active = true;" in generated_content
        assert "@Enumerated(EnumType.STRING)" in generated_content
        assert "private ProductStatus status;" in generated_content
        assert "@ManyToOne(fetch = FetchType.LAZY)" in generated_content
        assert "private Category category;" in generated_content

        # Verify audit fields
        assert "@CreatedDate" in generated_content
        assert "private LocalDateTime createdAt;" in generated_content
        assert "private LocalDateTime updatedAt;" in generated_content
        assert "private LocalDateTime deletedAt;" in generated_content
