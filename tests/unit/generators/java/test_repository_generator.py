"""Test Spring Data repository generation"""

import pytest
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.java.repository_generator import JavaRepositoryGenerator


def test_generate_basic_repository():
    """Test basic JpaRepository interface generation"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT),
            UniversalField(name="sku", type=FieldType.TEXT, unique=True),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    assert "package ecommerce.repository;" in java_code
    assert "import org.springframework.data.jpa.repository.JpaRepository;" in java_code
    assert "import ecommerce.Product;" in java_code
    assert "@Repository" in java_code
    assert (
        "public interface ProductRepository extends JpaRepository<Product, Long>"
        in java_code
    )


def test_generate_repository_with_query_methods():
    """Test auto-generated query methods"""
    entity = UniversalEntity(
        name="User",
        schema="auth",
        fields=[
            UniversalField(name="email", type=FieldType.TEXT, unique=True),
            UniversalField(name="username", type=FieldType.TEXT, unique=True),
            UniversalField(name="active", type=FieldType.BOOLEAN),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    # Spring Data query methods for unique fields
    assert "Optional<User> findByEmail(String email);" in java_code
    assert "Optional<User> findByUsername(String username);" in java_code
    assert "boolean existsByEmail(String email);" in java_code
    assert "List<User> findByActive(Boolean active);" in java_code


def test_generate_repository_with_custom_queries():
    """Test @Query annotations for complex queries"""
    entity = UniversalEntity(
        name="Order",
        schema="ecommerce",
        fields=[
            UniversalField(
                name="status", type=FieldType.ENUM, enum_values=["pending", "shipped"]
            ),
            UniversalField(name="total", type=FieldType.INTEGER),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    # Custom query for range search
    assert "@Query" in java_code
    assert "SELECT o FROM Order o WHERE o.total > :minTotal" in java_code


def test_generate_repository_with_pagination():
    """Test pagination support"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="category", type=FieldType.TEXT),
            UniversalField(name="active", type=FieldType.BOOLEAN),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    # Should include Pageable imports and methods
    assert "import org.springframework.data.domain.Pageable;" in java_code
    assert "Page<Product> findByCategory" in java_code
    assert "Pageable pageable" in java_code


def test_generate_repository_with_soft_delete():
    """Test soft delete queries"""
    entity = UniversalEntity(
        name="User",
        schema="auth",
        fields=[
            UniversalField(name="email", type=FieldType.TEXT, unique=True),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    # Soft delete queries
    assert '@Query("SELECT e FROM User e WHERE e.deletedAt IS NULL")' in java_code
    assert "List<User> findAllActive();" in java_code
    assert "Optional<User> findActiveById" in java_code
