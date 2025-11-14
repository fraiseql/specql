"""Test Spring @Service class generation"""

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


def test_generate_basic_service():
    """Test basic @Service class generation"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
            UniversalField(name="price", type=FieldType.INTEGER),
        ],
        actions=[],
    )

    generator = JavaServiceGenerator()
    java_code = generator.generate(entity)

    assert "package ecommerce.service;" in java_code
    assert "import org.springframework.stereotype.Service;" in java_code
    assert "@Service" in java_code
    assert "public class ProductService" in java_code
    assert "private final ProductRepository productRepository;" in java_code
    assert "public ProductService(ProductRepository productRepository)" in java_code


def test_generate_service_with_crud_methods():
    """Test CRUD methods generation"""
    entity = UniversalEntity(
        name="User",
        schema="auth",
        fields=[UniversalField(name="email", type=FieldType.TEXT, unique=True)],
        actions=[],
    )

    generator = JavaServiceGenerator()
    java_code = generator.generate(entity)

    # CRUD methods
    assert "public User create(User user)" in java_code
    assert "public Optional<User> findById(Long id)" in java_code
    assert "public List<User> findAll()" in java_code
    assert "public User update(Long id, User user)" in java_code
    assert "public void delete(Long id)" in java_code


def test_generate_service_with_custom_action():
    """Test custom business logic method from SpecQL action"""
    entity = UniversalEntity(
        name="Order",
        schema="ecommerce",
        fields=[
            UniversalField(
                name="status", type=FieldType.ENUM, enum_values=["pending", "shipped"]
            ),
        ],
        actions=[
            UniversalAction(
                name="ship_order",
                entity="Order",
                steps=[
                    UniversalStep(
                        type=StepType.VALIDATE, expression="status = 'pending'"
                    ),
                    UniversalStep(
                        type=StepType.UPDATE,
                        entity="Order",
                        fields={"status": "shipped"},
                    ),
                ],
                impacts=["Order"],
            )
        ],
    )

    generator = JavaServiceGenerator()
    java_code = generator.generate(entity)

    assert "@Transactional" in java_code
    assert "public Order shipOrder(Long orderId)" in java_code
    assert "if (!(order.getStatus().equals(OrderStatus.PENDING)))" in java_code
    assert "order.setStatus(OrderStatus.SHIPPED);" in java_code
