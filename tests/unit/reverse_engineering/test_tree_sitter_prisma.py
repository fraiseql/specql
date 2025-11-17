import pytest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "reverse_engineering")
)

from tree_sitter_prisma_parser import TreeSitterPrismaParser


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

    parser = TreeSitterPrismaParser()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert models[0].name == "User"
    assert len(models[0].fields) == 5

    # Check field details
    id_field = models[0].fields[0]
    assert id_field.name == "id"
    assert id_field.type == "Int"
    assert id_field.is_id == True
    assert id_field.has_default == True

    email_field = models[0].fields[1]
    assert email_field.name == "email"
    assert email_field.type == "String"
    assert email_field.is_unique == True


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

    parser = TreeSitterPrismaParser()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert len(models[0].fields) == 4
    # Comments should be ignored by tree-sitter


def test_extract_simple_relations():
    """Handle simple relation attributes."""
    schema = """
    model Post {
      id       Int    @id @default(autoincrement())
      authorId Int
      tags     Tag[]  @relation("PostTags")
    }
    """

    parser = TreeSitterPrismaParser()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    # Check that tags field has relation name
    tags_field = next(f for f in models[0].fields if f.name == "tags")
    assert tags_field.relation_name == "PostTags"


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

    parser = TreeSitterPrismaParser()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert models[0].fields[1].type == "Json"
    assert models[0].fields[2].type == "String"
    assert models[0].fields[2].is_list == True


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

    parser = TreeSitterPrismaParser()
    ast = parser.parse(schema)
    enums = parser.extract_enums(ast)

    assert len(enums) == 2
    assert enums[0].name == "Role"
    assert len(enums[0].values) == 3
    assert "USER" in enums[0].values
    assert "ADMIN" in enums[0].values


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

    parser = TreeSitterPrismaParser()
    ast = parser.parse(schema)
    models = parser.extract_models(ast)

    assert len(models) == 1
    assert len(models[0].indexes) == 2
    assert len(models[0].unique_constraints) == 1
