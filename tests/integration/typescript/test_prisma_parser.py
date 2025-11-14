"""
Integration tests for Prisma parser.
"""

import pytest
from pathlib import Path
from src.parsers.typescript.prisma_parser import PrismaParser


class TestPrismaParser:
    """Test Prisma parser functionality."""

    def test_parse_basic_model(self):
        """Test parsing a basic Prisma model."""
        prisma_content = """
        model User {
          id        Int      @id @default(autoincrement())
          email     String   @unique
          name      String?
          createdAt DateTime @default(now())
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        assert len(entities) == 1
        entity = entities[0]
        assert entity.name == "User"
        assert len(entity.fields) == 4

        # Check fields
        id_field = next(f for f in entity.fields if f.name == "id")
        assert id_field.type.value == "integer"
        assert id_field.required == True
        assert id_field.unique == False  # @id doesn't set unique on the field

        email_field = next(f for f in entity.fields if f.name == "email")
        assert email_field.type.value == "text"
        assert email_field.required == True
        assert email_field.unique == True  # @unique sets this

        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.type.value == "text"
        assert name_field.required == False

        created_at_field = next(f for f in entity.fields if f.name == "createdAt")
        assert created_at_field.type.value == "datetime"
        assert created_at_field.required == True

    def test_parse_model_with_relations(self):
        """Test parsing models with relationships."""
        prisma_content = """
        model User {
          id     Int      @id @default(autoincrement())
          email  String   @unique
          posts  Post[]
          profile Profile?
        }

        model Post {
          id       Int     @id @default(autoincrement())
          title    String
          content  String?
          authorId Int

          author   User    @relation(fields: [authorId], references: [id])
          comments Comment[]
        }

        model Comment {
          id     Int    @id @default(autoincrement())
          content String
          postId Int
          userId Int

          post   Post   @relation(fields: [postId], references: [id])
          user   User   @relation(fields: [userId], references: [id])
        }

        model Profile {
          id     Int    @id @default(autoincrement())
          bio    String?
          userId Int    @unique

          user   User   @relation(fields: [userId], references: [id])
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        assert len(entities) == 4

        # Check User model
        user_entity = next(e for e in entities if e.name == "User")
        assert len(user_entity.fields) == 4

        # Check Post model
        post_entity = next(e for e in entities if e.name == "Post")
        assert len(post_entity.fields) == 6

        author_id_field = next(f for f in post_entity.fields if f.name == "authorId")
        assert author_id_field.type.value == "reference"  # Foreign key with @relation

        # Check Comment model
        comment_entity = next(e for e in entities if e.name == "Comment")
        assert len(comment_entity.fields) == 6

        # Check Profile model
        profile_entity = next(e for e in entities if e.name == "Profile")
        assert len(profile_entity.fields) == 4

    def test_parse_different_field_types(self):
        """Test parsing various Prisma field types."""
        prisma_content = """
        model TestModel {
          id          Int       @id @default(autoincrement())
          name        String
          age         Int
          height      Float
          weight      Decimal
          isActive    Boolean
          createdAt   DateTime
          metadata    Json
          binaryData  Bytes
          tags        String[]
          scores      Int[]
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 11

        # Test various types
        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.type.value == "text"

        age_field = next(f for f in entity.fields if f.name == "age")
        assert age_field.type.value == "integer"

        height_field = next(f for f in entity.fields if f.name == "height")
        assert height_field.type.value == "rich"  # Float maps to rich

        weight_field = next(f for f in entity.fields if f.name == "weight")
        assert weight_field.type.value == "rich"  # Decimal maps to rich

        is_active_field = next(f for f in entity.fields if f.name == "isActive")
        assert is_active_field.type.value == "boolean"

        created_at_field = next(f for f in entity.fields if f.name == "createdAt")
        assert created_at_field.type.value == "datetime"

        metadata_field = next(f for f in entity.fields if f.name == "metadata")
        assert metadata_field.type.value == "rich"  # Json maps to rich

        binary_field = next(f for f in entity.fields if f.name == "binaryData")
        assert binary_field.type.value == "rich"  # Bytes maps to rich

        tags_field = next(f for f in entity.fields if f.name == "tags")
        assert tags_field.type.value == "list"  # Array type

        scores_field = next(f for f in entity.fields if f.name == "scores")
        assert scores_field.type.value == "list"  # Array type

    def test_parse_optional_fields(self):
        """Test parsing optional fields."""
        prisma_content = """
        model Product {
          id          Int      @id @default(autoincrement())
          name        String
          description String?
          price       Float?
          categoryId  Int?
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 5

        # Required fields
        id_field = next(f for f in entity.fields if f.name == "id")
        assert id_field.required == True

        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.required == True

        # Optional fields
        desc_field = next(f for f in entity.fields if f.name == "description")
        assert desc_field.required == False

        price_field = next(f for f in entity.fields if f.name == "price")
        assert price_field.required == False

        category_field = next(f for f in entity.fields if f.name == "categoryId")
        assert category_field.required == False

    def test_parse_unique_constraints(self):
        """Test parsing unique constraints."""
        prisma_content = """
        model User {
          id       Int    @id @default(autoincrement())
          email    String @unique
          username String
          ssn      String

          @@unique([username, ssn])
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 4

        # Check unique field
        email_field = next(f for f in entity.fields if f.name == "email")
        assert email_field.unique == True

        # Other fields should not be marked unique (@@unique is not parsed yet)
        username_field = next(f for f in entity.fields if f.name == "username")
        assert username_field.unique == False

    def test_ignore_comments_and_config(self):
        """Test that comments and config blocks are ignored."""
        prisma_content = """
        // This is a comment
        generator client {
          provider = "prisma-client-js"
        }

        datasource db {
          provider = "postgresql"
          url      = env("DATABASE_URL")
        }

        // Another comment
        model User {
          id    Int    @id @default(autoincrement())
          email String @unique

          // Field comment
          name  String?
        }

        /* Multi-line
           comment */
        model Post {
          id    Int    @id @default(autoincrement())
          title String
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        assert len(entities) == 2

        user_entity = next(e for e in entities if e.name == "User")
        assert len(user_entity.fields) == 3

        post_entity = next(e for e in entities if e.name == "Post")
        assert len(post_entity.fields) == 2

    def test_parse_complex_relations(self):
        """Test parsing complex relationship scenarios."""
        prisma_content = """
        model Author {
          id      Int     @id @default(autoincrement())
          name    String
          books   Book[]
        }

        model Book {
          id          Int      @id @default(autoincrement())
          title       String
          authorId    Int
          publisherId Int?

          author      Author   @relation(fields: [authorId], references: [id])
          publisher   Publisher? @relation(fields: [publisherId], references: [id])
          categories  BookCategory[]
        }

        model Publisher {
          id     Int    @id @default(autoincrement())
          name   String
          books  Book[]
        }

        model Category {
          id     Int            @id @default(autoincrement())
          name   String          @unique
          books  BookCategory[]
        }

        model BookCategory {
          bookId     Int
          categoryId Int

          book     Book     @relation(fields: [bookId], references: [id])
          category Category @relation(fields: [categoryId], references: [id])

          @@id([bookId, categoryId])
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        assert len(entities) == 5

        # Check Book model has correct fields
        book_entity = next(e for e in entities if e.name == "Book")
        assert (
            len(book_entity.fields) == 7
        )  # id, title, authorId, publisherId, author, publisher, categories

        # Check that foreign key fields are marked as references
        author_id_field = next(f for f in book_entity.fields if f.name == "authorId")
        assert author_id_field.type.value == "reference"

        publisher_id_field = next(
            f for f in book_entity.fields if f.name == "publisherId"
        )
        assert publisher_id_field.type.value == "reference"

    def test_parse_file_integration(self, tmp_path):
        """Test parsing from actual file."""
        prisma_content = """
        model TestEntity {
          id    Int     @id @default(autoincrement())
          title String
          active Boolean @default(false)
        }
        """

        prisma_file = tmp_path / "test.prisma"
        prisma_file.write_text(prisma_content)

        parser = PrismaParser()
        entities = parser.parse_schema_file(str(prisma_file))

        assert len(entities) == 1
        assert entities[0].name == "TestEntity"
        assert len(entities[0].fields) == 3

    def test_parse_empty_model(self):
        """Test handling of empty models."""
        prisma_content = """
        model EmptyModel {
        }

        model ValidModel {
          id Int @id
        }
        """

        parser = PrismaParser()
        entities = parser.parse_schema_content(prisma_content)

        # Should only parse models with fields
        assert len(entities) == 1
        assert entities[0].name == "ValidModel"
