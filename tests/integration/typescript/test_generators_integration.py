"""Integration tests for TypeScript/Prisma generators."""

import pytest
import tempfile
from pathlib import Path
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.typescript.typescript_generator_orchestrator import (
    TypeScriptGeneratorOrchestrator,
)


class TestGeneratorsIntegration:
    """Integration tests for TypeScript/Prisma code generation."""

    @pytest.fixture
    def sample_entities(self):
        """Sample entities for testing."""
        user = UniversalEntity(
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
                UniversalField(
                    name="updatedAt", type=FieldType.DATETIME, required=True
                ),
            ],
            actions=[],
        )

        category = UniversalEntity(
            name="Category",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(name="name", type=FieldType.TEXT, required=True),
                UniversalField(name="description", type=FieldType.TEXT, required=False),
            ],
            actions=[],
        )

        product = UniversalEntity(
            name="Product",
            schema="public",
            fields=[
                UniversalField(name="id", type=FieldType.INTEGER, required=True),
                UniversalField(name="name", type=FieldType.TEXT, required=True),
                UniversalField(name="price", type=FieldType.INTEGER, required=True),
                UniversalField(
                    name="category",
                    type=FieldType.REFERENCE,
                    required=True,
                    references="Category",
                ),
                UniversalField(name="tags", type=FieldType.LIST, required=False),
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

        return [user, category, product]

    def test_generate_all_files(self, tmp_path, sample_entities):
        """Test generating all TypeScript/Prisma files."""
        orchestrator = TypeScriptGeneratorOrchestrator(str(tmp_path))
        files = orchestrator.generate_all(sample_entities)

        # Verify files were generated
        assert "prisma/schema.prisma" in files
        assert "src/entities/User.ts" in files
        assert "src/entities/Category.ts" in files
        assert "src/entities/Product.ts" in files

        # Verify Prisma schema content
        schema_content = files["prisma/schema.prisma"]
        assert "generator client" in schema_content
        assert "datasource db" in schema_content
        assert "model User {" in schema_content
        assert "model Category {" in schema_content
        assert "model Product {" in schema_content

        # Verify relationships
        assert "categoryId" in schema_content
        assert "@relation(fields: [categoryId], references: [id])" in schema_content

        # Verify TypeScript interfaces
        user_interface = files["src/entities/User.ts"]
        assert "export interface User {" in user_interface
        assert "email: string;" in user_interface  # Required field
        assert "name?: string;" in user_interface  # Optional field

        product_interface = files["src/entities/Product.ts"]
        assert "export interface Product {" in product_interface
        assert "category: Category;" in product_interface  # Required reference type
        assert "tags?: any[];" in product_interface  # Optional list type

    def test_write_files_to_disk(self, tmp_path, sample_entities):
        """Test writing generated files to disk."""
        orchestrator = TypeScriptGeneratorOrchestrator(str(tmp_path))
        files = orchestrator.generate_all(sample_entities)
        orchestrator.write_files(files)

        # Verify files exist on disk
        assert (tmp_path / "prisma/schema.prisma").exists()
        assert (tmp_path / "src/entities/User.ts").exists()
        assert (tmp_path / "src/entities/Category.ts").exists()
        assert (tmp_path / "src/entities/Product.ts").exists()

        # Verify content matches
        schema_content = (tmp_path / "prisma/schema.prisma").read_text()
        assert "model User {" in schema_content
        assert "model Product {" in schema_content

        user_interface = (tmp_path / "src/entities/User.ts").read_text()
        assert "export interface User {" in user_interface

    def test_generate_enum_in_schema(self, tmp_path):
        """Test generating enums in Prisma schema."""
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

        orchestrator = TypeScriptGeneratorOrchestrator(str(tmp_path))
        files = orchestrator.generate_all([entity])

        schema_content = files["prisma/schema.prisma"]

        # Verify enum declaration
        assert "enum StatusStatus {" in schema_content
        assert "pending" in schema_content
        assert "shipped" in schema_content
        assert "delivered" in schema_content

        # Verify enum usage in model
        assert "status          StatusStatus" in schema_content

        # Verify TypeScript interface
        interface_content = files["src/entities/Order.ts"]
        assert 'status: "pending" | "shipped" | "delivered";' in interface_content
