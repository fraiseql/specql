"""Test JPA entity generation from SpecQL"""

import pytest
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.java.entity_generator import JavaEntityGenerator


def test_generate_simple_entity():
    """Test basic entity generation"""
    # Create SpecQL entity
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
            UniversalField(name="price", type=FieldType.INTEGER, required=True),
            UniversalField(name="active", type=FieldType.BOOLEAN, default=True),
        ],
        actions=[],
    )

    # Generate Java entity
    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    # Assertions
    assert "package ecommerce;" in java_code
    assert "@Entity" in java_code
    assert '@Table(name = "tb_product")' in java_code
    assert "public class Product" in java_code
    assert "@Id" in java_code
    assert "@GeneratedValue" in java_code
    assert "private Long id;" in java_code
    assert "@Column(nullable = false)" in java_code
    assert "private String name;" in java_code
    assert "private Integer price;" in java_code
    assert "private Boolean active = true;" in java_code


def test_generate_entity_with_reference():
    """Test entity with foreign key reference"""
    entity = UniversalEntity(
        name="Order",
        schema="ecommerce",
        fields=[
            UniversalField(name="quantity", type=FieldType.INTEGER),
            UniversalField(
                name="product",
                type=FieldType.REFERENCE,
                references="Product",
                required=True,
            ),
        ],
        actions=[],
    )

    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    assert "@ManyToOne(fetch = FetchType.LAZY)" in java_code
    assert '@JoinColumn(name = "fk_product", nullable = false)' in java_code
    assert "private Product product;" in java_code


def test_generate_entity_with_enum():
    """Test entity with enum field"""
    entity = UniversalEntity(
        name="Contact",
        schema="crm",
        fields=[
            UniversalField(
                name="status",
                type=FieldType.ENUM,
                enum_values=["lead", "qualified", "customer"],
            ),
        ],
        actions=[],
    )

    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    assert "@Enumerated(EnumType.STRING)" in java_code
    assert "private ContactStatus status;" in java_code


def test_generate_entity_with_timestamps():
    """Test that audit fields are auto-generated"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT),
        ],
        actions=[],
    )

    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    # Trinity pattern audit fields
    assert "@CreatedDate" in java_code
    assert "private LocalDateTime createdAt;" in java_code
    assert "@LastModifiedDate" in java_code
    assert "private LocalDateTime updatedAt;" in java_code


def test_generate_entity_with_list():
    """Test entity with list field"""
    entity = UniversalEntity(
        name="Category",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT),
            UniversalField(name="tags", type=FieldType.LIST),
        ],
        actions=[],
    )

    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    assert "import java.util.List;" in java_code
    assert "import java.util.ArrayList;" in java_code
    assert '@OneToMany(mappedBy = "parent", cascade = CascadeType.ALL)' in java_code
    assert "private List<Object> tags = new ArrayList<>();" in java_code
