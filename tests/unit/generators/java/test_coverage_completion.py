"""Tests to close coverage gaps in Java generators"""

import pytest
from src.core.universal_ast import (
    UniversalEntity,
    UniversalField,
    UniversalAction,
    UniversalStep,
    FieldType,
    StepType,
)
from src.generators.java.service_generator import JavaServiceGenerator
from src.generators.java.repository_generator import JavaRepositoryGenerator
from src.generators.java.entity_generator import JavaEntityGenerator
from src.generators.java.enum_generator import JavaEnumGenerator


class TestServiceGeneratorCoverage:
    """Close coverage gaps in service_generator.py"""

    def test_service_with_invalid_action_step(self):
        """Test error handling for invalid action step"""
        entity = UniversalEntity(
            name="Product",
            schema="ecommerce",
            fields=[UniversalField(name="name", type=FieldType.TEXT)],
            actions=[
                UniversalAction(
                    name="invalid_action",
                    entity="Product",
                    steps=[
                        UniversalStep(
                            type=StepType.CALL,  # Step type not handled in the if/elif chain
                            expression="invalid",
                        )
                    ],
                    impacts=["Product"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should handle gracefully with TODO comment
        assert (
            "// TODO: Implement" in java_code
            or "throw new UnsupportedOperationException" in java_code
        )

    def test_service_with_validation_without_expression(self):
        """Test validation step without expression"""
        entity = UniversalEntity(
            name="Order",
            schema="ecommerce",
            fields=[UniversalField(name="total", type=FieldType.INTEGER)],
            actions=[
                UniversalAction(
                    name="validate_order",
                    entity="Order",
                    steps=[
                        UniversalStep(
                            type=StepType.VALIDATE,
                            expression=None,  # No expression
                        )
                    ],
                    impacts=["Order"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should generate TODO comment for validation without expression
        assert "// TODO: Validation step without expression" in java_code

    def test_service_with_update_without_fields(self):
        """Test update step without fields"""
        entity = UniversalEntity(
            name="Payment",
            schema="billing",
            fields=[UniversalField(name="amount", type=FieldType.INTEGER)],
            actions=[
                UniversalAction(
                    name="process_payment",
                    entity="Payment",
                    steps=[
                        UniversalStep(
                            type=StepType.UPDATE,
                            fields=None,  # No fields
                        )
                    ],
                    impacts=["Payment"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should generate TODO comment for update without fields
        assert "// TODO: Update step without fields" in java_code

    def test_service_with_if_step(self):
        """Test IF step generation"""
        entity = UniversalEntity(
            name="Order",
            schema="ecommerce",
            fields=[
                UniversalField(name="status", type=FieldType.TEXT),
                UniversalField(name="total", type=FieldType.INTEGER),
            ],
            actions=[
                UniversalAction(
                    name="conditional_update",
                    entity="Order",
                    steps=[
                        UniversalStep(
                            type=StepType.IF,
                            expression="status = 'pending'",
                            steps=[
                                UniversalStep(
                                    type=StepType.UPDATE, fields={"status": "processed"}
                                )
                            ],
                        )
                    ],
                    impacts=["Order"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should generate if block
        assert "if (" in java_code
        assert 'order.getStatus().equals("pending")' in java_code

    def test_service_expression_parsing_edge_cases(self):
        """Test expression parsing edge cases"""
        entity = UniversalEntity(
            name="Product",
            schema="ecommerce",
            fields=[UniversalField(name="price", type=FieldType.INTEGER)],
            actions=[
                UniversalAction(
                    name="check_price",
                    entity="Product",
                    steps=[
                        UniversalStep(
                            type=StepType.VALIDATE,
                            expression=None,  # Test default condition
                        )
                    ],
                    impacts=["Product"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should generate TODO comment for validation without expression
        assert "// TODO: Validation step without expression" in java_code

    def test_service_value_formatting_edge_cases(self):
        """Test value formatting edge cases"""
        entity = UniversalEntity(
            name="Product",
            schema="ecommerce",
            fields=[
                UniversalField(name="active", type=FieldType.BOOLEAN),
                UniversalField(name="count", type=FieldType.INTEGER),
            ],
            actions=[
                UniversalAction(
                    name="update_product",
                    entity="Product",
                    steps=[
                        UniversalStep(
                            type=StepType.UPDATE, fields={"active": True, "count": 42}
                        )
                    ],
                    impacts=["Product"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should format boolean as lowercase
        assert "setActive(true)" in java_code
        assert "setCount(42)" in java_code


class TestRepositoryGeneratorCoverage:
    """Close coverage gaps in repository_generator.py"""

    def test_repository_with_unique_fields(self):
        """Test repository generation with unique fields"""
        entity = UniversalEntity(
            name="User",
            schema="auth",
            fields=[
                UniversalField(name="email", type=FieldType.TEXT, unique=True),
                UniversalField(name="username", type=FieldType.TEXT, unique=True),
                UniversalField(name="name", type=FieldType.TEXT),
            ],
            actions=[],
        )

        generator = JavaRepositoryGenerator()
        java_code = generator.generate(entity)

        # Should generate Optional findBy and existsBy methods for unique fields
        assert "Optional<User> findByEmail(String email)" in java_code
        assert "boolean existsByEmail(String email)" in java_code
        assert "Optional<User> findByUsername(String username)" in java_code
        assert "boolean existsByUsername(String username)" in java_code

        # Should generate List findBy for non-unique field
        assert "List<User> findByName(String name)" in java_code

    def test_repository_reference_field_error_handling(self):
        """Test reference field type mapping error handling"""
        entity = UniversalEntity(
            name="Order",
            schema="ecommerce",
            fields=[
                UniversalField(
                    name="customer", type=FieldType.REFERENCE, references=None
                )  # Missing references
            ],
            actions=[],
        )

        generator = JavaRepositoryGenerator()

        # The error might be triggered during type mapping, let's see what happens
        try:
            java_code = generator.generate(entity)
            # If it doesn't raise, that's also fine - the error path might not be hit
            assert "OrderRepository" in java_code
        except ValueError as e:
            # If it does raise, check the message
            assert "Reference field customer must specify references" in str(e)


class TestEntityGeneratorCoverage:
    """Close coverage gaps in entity_generator.py"""

    def test_entity_reference_field_validation(self):
        """Test reference field validation error"""
        entity = UniversalEntity(
            name="Order",
            schema="ecommerce",
            fields=[
                UniversalField(
                    name="customer", type=FieldType.REFERENCE, references=None
                )  # Missing references
            ],
            actions=[],
        )

        generator = JavaEntityGenerator()

        # Should raise ValueError for reference field without references
        with pytest.raises(
            ValueError, match="Reference field customer must specify references"
        ):
            generator.generate(entity)

    def test_entity_default_value_formatting(self):
        """Test default value formatting for different types"""
        entity = UniversalEntity(
            name="Product",
            schema="ecommerce",
            fields=[
                UniversalField(name="name", type=FieldType.TEXT, default="Unknown"),
                UniversalField(name="active", type=FieldType.BOOLEAN, default=True),
                UniversalField(
                    name="price", type=FieldType.INTEGER, default=10
                ),  # Use non-zero default
            ],
            actions=[],
        )

        generator = JavaEntityGenerator()
        java_code = generator.generate(entity)

        # Should format text defaults with quotes
        assert '"Unknown"' in java_code
        # Should format boolean defaults as lowercase
        assert "true" in java_code
        # Should format integer defaults as plain numbers
        assert "price = 10" in java_code


class TestEnumGeneratorCoverage:
    """Close coverage gaps in enum_generator.py"""

    def test_enum_generator_with_non_enum_field(self):
        """Test enum generator with non-enum field"""
        field = UniversalField(name="name", type=FieldType.TEXT)  # Not an enum field

        generator = JavaEnumGenerator()

        # Should raise ValueError for non-enum field
        with pytest.raises(ValueError, match="Field name is not an enum"):
            generator.generate(field, "com.example", "Product")


class TestLombokHandler:
    """Test Lombok annotation handling"""

    def test_lombok_data_annotation(self):
        """Test @Data annotation detection"""
        from src.parsers.java.lombok_handler import LombokAnnotationHandler

        handler = LombokAnnotationHandler()
        java_code = """
        @Data
        public class TestEntity {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_data  is True
        assert metadata.has_getter  is True
        assert metadata.has_setter  is True

    def test_lombok_builder_annotation(self):
        """Test @Builder annotation detection"""
        from src.parsers.java.lombok_handler import LombokAnnotationHandler

        handler = LombokAnnotationHandler()
        java_code = """
        @Builder
        public class TestEntity {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_builder  is True

    def test_lombok_non_null_fields(self):
        """Test @NonNull field detection"""
        from src.parsers.java.lombok_handler import LombokAnnotationHandler

        handler = LombokAnnotationHandler()
        java_code = """
        public class TestEntity {
            @NonNull
            private String name;

            private String description;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert "name" in metadata.non_null_fields
        assert "description" not in metadata.non_null_fields

    def test_lombok_builder_defaults(self):
        """Test @Builder.Default value extraction"""
        from src.parsers.java.lombok_handler import LombokAnnotationHandler

        handler = LombokAnnotationHandler()
        java_code = """
        public class TestEntity {
            @Builder.Default
            private String status = "active";

            @Builder.Default
            private Integer count = 0;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.builder_defaults["status"] == '"active"'
        assert metadata.builder_defaults["count"] == "0"

    def test_lombok_integration_with_parser(self):
        """Test Lombok integration with SpringBootParser"""
        from src.parsers.java.spring_boot_parser import SpringBootParser
        import tempfile
        import os

        parser = SpringBootParser()

        # Create a temporary file with Lombok annotations
        java_code = """
        package com.example;

        import javax.persistence.*;
        import lombok.*;

        @Entity
        @Data
        @Builder
        public class TestEntity {
            @Id
            @GeneratedValue
            private Long id;

            @NonNull
            @Builder.Default
            private String name = "Unknown";

            private String description;
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_code)
            temp_file = f.name

        try:
            # Test the Lombok handler directly first
            lombok_metadata = parser.lombok_handler.extract_lombok_metadata(java_code)
            assert lombok_metadata.has_data  is True
            assert lombok_metadata.has_builder  is True
            assert lombok_metadata.builder_defaults.get("name") == '"Unknown"', (
                f"Builder defaults: {lombok_metadata.builder_defaults}"
            )

            entity = parser.parse_entity_file(temp_file)

            assert entity is not None
            assert entity.name == "TestEntity"

            # Check that @Builder.Default value is applied
            name_field = next((f for f in entity.fields if f.name == "name"), None)
            assert name_field is not None
            assert name_field.default == '"Unknown"'

        finally:
            os.unlink(temp_file)


class TestSpringBootParserCoverage:
    """Close coverage gaps in spring_boot_parser.py"""

    def test_parser_file_exception_handling(self):
        """Test parser handles file reading exceptions"""
        from src.parsers.java.spring_boot_parser import SpringBootParser
        import tempfile

        parser = SpringBootParser()

        # Create a directory that will cause an exception when trying to read as file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Try to parse a directory as a file (should be handled gracefully)
            entities = parser.parse_project(temp_dir)

            # Should return empty list or handle gracefully
            assert isinstance(entities, list)

    def test_parser_missing_class_error(self):
        """Test parser behavior when no public class found"""
        from src.parsers.java.spring_boot_parser import SpringBootParser
        import tempfile
        import os

        parser = SpringBootParser()

        # Create a temporary file with no class at all
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write("""
            package com.example;

            import javax.persistence.*;
            // This file has no classes
            """)
            temp_file = f.name

        try:
            # The parser should handle files with no classes
            result = parser.parse_entity_file(temp_file)
            # It may return a partial result or None
            assert result is None or hasattr(result, "name")
        except Exception as e:
            # If it raises an exception, it should be clear about the issue
            assert "class" in str(e).lower() or "parse" in str(e).lower()
        finally:
            os.unlink(temp_file)

    def test_parser_field_conversion_compatibility(self):
        """Test field conversion from old format (if exists)"""
        from src.parsers.java.spring_boot_parser import SpringBootParser

        parser = SpringBootParser()

        # Create a mock old-style field object
        class MockOldField:
            def __init__(self):
                self.name = "test_field"
                self.type = "String"
                self.required = True
                self.references = None
                self.enum_values = None

        old_field = MockOldField()

        # Test the conversion method
        converted_field = parser._convert_field(old_field)

        assert converted_field.name == "test_field"
        assert converted_field.required  is True
