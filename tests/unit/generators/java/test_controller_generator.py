"""Test Spring @RestController generation"""

import pytest
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.java.controller_generator import JavaControllerGenerator


def test_generate_basic_controller():
    """Test basic @RestController generation"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
            UniversalField(name="price", type=FieldType.INTEGER),
        ],
        actions=[],
    )

    generator = JavaControllerGenerator()
    java_code = generator.generate(entity)

    assert "package ecommerce.controller;" in java_code
    assert "@RestController" in java_code
    assert '@RequestMapping("/api/products")' in java_code
    assert "public class ProductController" in java_code
    assert "private final ProductService productService;" in java_code


def test_generate_controller_with_rest_endpoints():
    """Test REST endpoint generation"""
    entity = UniversalEntity(
        name="User",
        schema="auth",
        fields=[UniversalField(name="email", type=FieldType.TEXT, unique=True)],
        actions=[],
    )

    generator = JavaControllerGenerator()
    java_code = generator.generate(entity)

    # REST endpoints
    assert "@PostMapping" in java_code
    assert (
        "public ResponseEntity<User> create(@Valid @RequestBody User user)" in java_code
    )
    assert '@GetMapping("/{id}")' in java_code
    assert "public ResponseEntity<User> getById(@PathVariable Long id)" in java_code
    assert "@GetMapping" in java_code
    assert "public List<User> getAll()" in java_code
    assert '@PutMapping("/{id}")' in java_code
    assert (
        "public ResponseEntity<User> update(@PathVariable Long id, @Valid @RequestBody User user)"
        in java_code
    )
    assert '@DeleteMapping("/{id}")' in java_code


def test_generate_controller_with_validation():
    """Test request validation"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
        ],
        actions=[],
    )

    generator = JavaControllerGenerator()
    java_code = generator.generate(entity)

    # Validation annotations
    assert "@Valid" in java_code
    assert "import javax.validation.Valid;" in java_code
