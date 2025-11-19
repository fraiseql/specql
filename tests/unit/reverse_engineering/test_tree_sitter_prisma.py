import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "reverse_engineering")
)


# Lazy import to avoid module-level import errors
def _get_parser():
    try:
        from src.reverse_engineering.tree_sitter_prisma_parser import TreeSitterPrismaParser

        return TreeSitterPrismaParser
    except ImportError:
        pytest.skip("tree_sitter_prisma_parser not available")
        return None


@pytest.mark.requires_tree_sitter
def test_extract_basic_model():
    """Extract basic Prisma model via AST."""
    schema = """
    model User {
      id        Int      @id @default(autoincrement())
      email     String   @unique
      name      String?
      posts     Post[]
      createdAt DateTime @default(now())
    }
    """

    ParserClass = _get_parser()
    parser = ParserClass()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert models[0].name == "User"
    assert len(models[0].fields) == 5

    # Check field details
    id_field = models[0].fields[0]
    assert id_field.name == "id"
    assert id_field.type == "Int"
    assert id_field.is_id
    assert id_field.has_default

    email_field = models[0].fields[1]
    assert email_field.name == "email"
    assert email_field.type == "String"
    assert email_field.is_unique


@pytest.mark.requires_tree_sitter
def test_extract_model_with_inline_comments():
    """Handle models with inline comments."""
    schema = """
    model User {
      id        Int      @id @default(autoincrement()) // primary key
      email     String   @unique // must be unique
      name      String?  // optional field
      posts     Post[]   // one-to-many relation
    }
    """

    ParserClass = _get_parser()
    parser = ParserClass()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert len(models[0].fields) == 4
    # Comments should be ignored by tree-sitter


@pytest.mark.requires_tree_sitter
def test_extract_simple_relations():
    """Handle simple relation attributes."""
    schema = """
    model Post {
      id       Int    @id @default(autoincrement())
      authorId Int
      tags     Tag[]  @relation("PostTags")
    }
    """

    ParserClass = _get_parser()
    parser = ParserClass()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    # Check that tags field has relation name
    tags_field = next(f for f in models[0].fields if f.name == "tags")
    assert tags_field.relation_name == "PostTags"


@pytest.mark.requires_tree_sitter
def test_extract_nested_types():
    """Handle complex field types."""
    schema = """
    model Data {
      id       Int     @id
      metadata Json    // JSON type
      tags     String[] // Array type
      config   Bytes   // Binary type
    }
    """

    ParserClass = _get_parser()
    parser = ParserClass()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert len(models[0].fields) == 4

    # Check complex types
    metadata_field = next(f for f in models[0].fields if f.name == "metadata")
    assert metadata_field.type == "Json"

    tags_field = next(f for f in models[0].fields if f.name == "tags")
    assert tags_field.type == "String[]"

    config_field = next(f for f in models[0].fields if f.name == "config")
    assert config_field.type == "Bytes"


@pytest.mark.requires_tree_sitter
def test_extract_enums():
    """Extract Prisma enums."""
    schema = """
    enum Role {
      USER
      ADMIN
      MODERATOR
    }

    enum Status {
      ACTIVE
      INACTIVE
    }
    """

    ParserClass = _get_parser()
    parser = ParserClass()
    ast = parser.parse(schema)
    enums = parser.extract_enums(ast)

    assert len(enums) == 2
    assert enums[0].name == "Role"
    assert enums[0].values == ["USER", "ADMIN", "MODERATOR"]
    assert enums[1].name == "Status"
    assert enums[1].values == ["ACTIVE", "INACTIVE"]


@pytest.mark.requires_tree_sitter
def test_extract_indexes():
    """Extract model indexes."""
    schema = """
    model User {
      id        Int    @id
      email     String
      firstName String
      lastName  String

      @@index([email])
      @@index([firstName, lastName])
      @@unique([email])
    }
    """

    ParserClass = _get_parser()
    parser = ParserClass()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert len(models[0].indexes) == 2
    assert len(models[0].unique_constraints) == 1
