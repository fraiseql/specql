"""Test Java enum generation from SpecQL enum fields"""

import pytest
from src.core.universal_ast import UniversalField, FieldType
from src.generators.java.enum_generator import JavaEnumGenerator


def test_generate_enum_class():
    """Test enum class generation"""
    field = UniversalField(
        name="status",
        type=FieldType.ENUM,
        enum_values=["draft", "published", "archived"],
    )

    generator = JavaEnumGenerator()
    java_code = generator.generate(field, "com.example.blog", "Post")

    assert "package com.example.blog;" in java_code
    assert "public enum PostStatus {" in java_code
    assert "DRAFT," in java_code
    assert "PUBLISHED," in java_code
    assert "ARCHIVED" in java_code


def test_generate_enum_class_empty_values():
    """Test enum class generation with no values"""
    field = UniversalField(
        name="priority",
        type=FieldType.ENUM,
        enum_values=[],
    )

    generator = JavaEnumGenerator()
    java_code = generator.generate(field, "com.example.task", "Task")

    assert "package com.example.task;" in java_code
    assert "public enum TaskPriority {" in java_code
    # Should still have the closing brace even with no values
    assert java_code.endswith("}")


def test_generate_enum_class_wrong_type():
    """Test that non-enum fields raise error"""
    field = UniversalField(
        name="name",
        type=FieldType.TEXT,
    )

    generator = JavaEnumGenerator()
    with pytest.raises(ValueError, match="Field name is not an enum"):
        generator.generate(field, "com.example", "Entity")
