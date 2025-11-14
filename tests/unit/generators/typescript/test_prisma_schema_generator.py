"""Tests for Prisma schema generator."""

import pytest
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.typescript.prisma_schema_generator import PrismaSchemaGenerator


class TestPrismaSchemaGenerator:
    """Test Prisma schema generation."""

    def test_generate_simple_model(self):
        """Test generating a simple Prisma model."""
        entity = UniversalEntity(
            name="User",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(
                    name="email", type=FieldType.TEXT, required=True, unique=True
                ),
                UniversalField(name="name", type=FieldType.TEXT, required=False),
                UniversalField(
                    name="createdAt", type=FieldType.DATETIME, required=True
                ),
            ],
            actions=[],
        )

        generator = PrismaSchemaGenerator()
        schema = generator.generate([entity])

        # Verify header
        assert "generator client" in schema
        assert "datasource db" in schema

        # Verify model
        assert "model User {" in schema
        assert "id" in schema
        assert "@id @default(autoincrement())" in schema
        assert "email" in schema
        assert "@unique" in schema
        assert "name" in schema and "String?" in schema
        assert "createdAt" in schema
        assert "DateTime" in schema

    def test_generate_model_with_relationships(self):
        """Test generating models with foreign key relationships."""
        category = UniversalEntity(
            name="Category",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(name="name", type=FieldType.TEXT, required=True),
            ],
            actions=[],
        )

        product = UniversalEntity(
            name="Product",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(name="name", type=FieldType.TEXT, required=True),
                UniversalField(
                    name="category",
                    type=FieldType.REFERENCE,
                    required=True,
                    references="Category",
                ),
            ],
            actions=[],
        )

        generator = PrismaSchemaGenerator()
        schema = generator.generate([category, product])

        # Verify relationship
        assert "categoryId" in schema
        assert "@relation(fields: [categoryId], references: [id])" in schema

    def test_generate_model_with_enum(self):
        """Test generating models with enum fields."""
        entity = UniversalEntity(
            name="Order",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(
                    name="status",
                    type=FieldType.ENUM,
                    required=True,
                    enum_values=["pending", "shipped", "delivered"],
                ),
            ],
            actions=[],
        )

        generator = PrismaSchemaGenerator()
        schema = generator.generate([entity])

        # Verify enum declaration
        assert "enum StatusStatus {" in schema
        assert "pending" in schema
        assert "shipped" in schema
        assert "delivered" in schema

        # Verify enum usage in model
        assert "status" in schema

    def test_generate_model_with_list_field(self):
        """Test generating models with array/list fields."""
        entity = UniversalEntity(
            name="Product",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(name="name", type=FieldType.TEXT, required=True),
                UniversalField(name="tags", type=FieldType.LIST, required=False),
            ],
            actions=[],
        )

        generator = PrismaSchemaGenerator()
        schema = generator.generate([entity])

        # Verify array field
        assert "tags" in schema
        assert "String[]?" in schema

    def test_generate_model_with_defaults(self):
        """Test generating models with default values."""
        entity = UniversalEntity(
            name="Product",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(name="name", type=FieldType.TEXT, required=True),
                UniversalField(
                    name="active", type=FieldType.BOOLEAN, required=True, default=True
                ),
                UniversalField(
                    name="createdAt", type=FieldType.DATETIME, required=True
                ),
                UniversalField(
                    name="updatedAt", type=FieldType.DATETIME, required=True
                ),
            ],
            actions=[],
        )

        generator = PrismaSchemaGenerator()
        schema = generator.generate([entity])

        # Verify defaults
        assert "@default(true)" in schema
        assert "@default(now())" in schema
        assert "@updatedAt" in schema
