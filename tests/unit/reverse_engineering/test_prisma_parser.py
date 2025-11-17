# tests/unit/reverse_engineering/test_prisma_parser.py

import pytest
from src.reverse_engineering.prisma_parser import PrismaSchemaParser


class TestPrismaSchemaParser:
    """Test Prisma schema parsing"""

    def test_parse_prisma_model(self):
        """Test parsing Prisma model to SpecQL entity"""
        schema = """
        model Contact {
          id        Int      @id @default(autoincrement())
          email     String   @unique
          status    String   @default("lead")
          companyId Int?     @map("company_id")
          company   Company? @relation(fields: [companyId], references: [id])

          deletedAt DateTime? @map("deleted_at")
          createdAt DateTime  @default(now()) @map("created_at")
          updatedAt DateTime  @updatedAt @map("updated_at")

          @@map("contacts")
        }
        """

        parser = PrismaSchemaParser()
        entities = parser.parse_schema(schema)

        assert len(entities) == 1
        contact = entities[0]
        assert contact.name == "Contact"
        assert contact.table_name == "contacts"
        assert len(contact.fields) == 8

        # Check field types
        email_field = next(f for f in contact.fields if f.name == "email")
        assert email_field.type == "text"
        assert email_field.unique == True

        status_field = next(f for f in contact.fields if f.name == "status")
        assert status_field.default_value == "lead"

        # Check relation
        company_field = next(f for f in contact.fields if f.name == "company")
        assert company_field.is_relation == True
        assert company_field.related_entity == "Company"

    def test_parse_prisma_enums(self):
        """Test parsing Prisma enums"""
        schema = """
        enum ContactStatus {
          LEAD
          QUALIFIED
          CUSTOMER
        }

        model Contact {
          id     Int           @id
          status ContactStatus @default(LEAD)
        }
        """

        parser = PrismaSchemaParser()
        entities = parser.parse_schema(schema)

        assert len(entities) == 1
        contact = entities[0]

        status_field = next(f for f in contact.fields if f.name == "status")
        assert status_field.type == "enum"
        assert status_field.enum_values == ["LEAD", "QUALIFIED", "CUSTOMER"]

    def test_parse_prisma_indexes(self):
        """Test parsing Prisma indexes"""
        schema = """
        model Contact {
          id        Int    @id
          email     String
          companyId Int

          @@index([email])
          @@index([companyId, email])
          @@unique([email])
        }
        """

        parser = PrismaSchemaParser()
        entities = parser.parse_schema(schema)

        contact = entities[0]
        assert len(contact.indexes) == 2
        assert len(contact.unique_constraints) == 1
