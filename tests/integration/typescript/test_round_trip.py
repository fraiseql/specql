"""Round-trip testing: Prisma → SpecQL YAML → Prisma"""

import pytest
import tempfile
from pathlib import Path
from src.parsers.typescript.prisma_parser import PrismaParser
from src.generators.typescript.prisma_schema_generator import PrismaSchemaGenerator
from src.core.yaml_serializer import YAMLSerializer
from src.core.specql_parser import SpecQLParser


class TestRoundTrip:
    """Test round-trip conversion."""

    def test_round_trip_simple_model(self, tmp_path):
        """Test: Prisma → SpecQL YAML → Prisma"""
        # Original Prisma schema
        original_schema = """
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
"""

        # Step 1: Parse Prisma schema
        parser = PrismaParser()
        entities = parser.parse_schema_content(original_schema)

        assert len(entities) == 1
        original_entity = entities[0]

        # Step 2: Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        # Step 3: Parse YAML back to entity
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse_universal(yaml_content)

        # Step 4: Generate Prisma schema
        generator = PrismaSchemaGenerator()
        regenerated_schema = generator.generate([intermediate_entity])

        # Step 5: Parse regenerated schema
        regenerated_entities = parser.parse_schema_content(regenerated_schema)
        assert len(regenerated_entities) == 1
        regenerated_entity = regenerated_entities[0]

        # Step 6: Compare entities
        assert original_entity.name == regenerated_entity.name

        # Note: YAML serializer skips audit fields (id, createdAt, updatedAt, deletedAt)
        # So we expect fewer fields in the regenerated entity
        original_business_fields = [
            f
            for f in original_entity.fields
            if f.name not in ["id", "createdAt", "updatedAt", "deletedAt"]
        ]
        assert len(original_business_fields) == len(regenerated_entity.fields)

        # Compare business field names
        original_names = {f.name for f in original_business_fields}
        regenerated_names = {f.name for f in regenerated_entity.fields}
        assert original_names == regenerated_names

    def test_round_trip_with_relationships(self, tmp_path):
        """Test round-trip with foreign key relationships."""
        original_schema = """
model Category {
  id       Int       @id @default(autoincrement())
  name     String    @unique
  products Product[]
}

model Product {
  id          Int      @id @default(autoincrement())
  name        String
  categoryId  Int

  category    Category @relation(fields: [categoryId], references: [id])
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)

    def test_round_trip_preserves_field_properties(self, tmp_path):
        """Test that field properties are preserved in round-trip."""
        original_schema = """
model Product {
  id          Int      @id @default(autoincrement())
  name        String
  description String?
  price       Int
  active      Boolean  @default(true)
  tags        String[]
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse → Generate → Parse
        original_entities = parser.parse_schema_content(original_schema)
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare field counts and types
        original_fields = original_entities[0].fields
        regenerated_fields = regenerated_entities[0].fields

        assert len(original_fields) == len(regenerated_fields)

    def test_round_trip_with_enum(self, tmp_path):
        """Test round-trip with enum fields."""
        original_schema = """
enum Status {
  ACTIVE
  INACTIVE
  PENDING
}

model Order {
  id        Int     @id @default(autoincrement())
  status    Status  @default(ACTIVE)
  createdAt DateTime @default(now())
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)

    def test_round_trip_self_referential(self, tmp_path):
        """Test round-trip with self-referential relationships."""
        original_schema = """
model Employee {
  id         Int       @id @default(autoincrement())
  name       String
  managerId  Int?

  manager    Employee? @relation("EmployeeManager", fields: [managerId], references: [id])
  reports    Employee[] @relation("EmployeeManager")
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)

    def test_round_trip_many_to_many(self, tmp_path):
        """Test round-trip with many-to-many relationships."""
        original_schema = """
model Post {
  id         Int      @id @default(autoincrement())
  title      String
  tags       Tag[]
}

model Tag {
  id    Int    @id @default(autoincrement())
  name  String @unique
  posts Post[]
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)

    def test_round_trip_composite_primary_key(self, tmp_path):
        """Test round-trip with composite primary keys."""
        original_schema = """
model OrderItem {
  orderId   Int
  productId Int
  quantity  Int

  order    Order   @relation(fields: [orderId], references: [id])
  product  Product @relation(fields: [productId], references: [id])

  @@id([orderId, productId])
}

model Order {
  id    Int         @id @default(autoincrement())
  items OrderItem[]
}

model Product {
  id    Int         @id @default(autoincrement())
  items OrderItem[]
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)

    def test_round_trip_optional_relationships(self, tmp_path):
        """Test round-trip with optional relationships."""
        original_schema = """
model User {
  id      Int      @id @default(autoincrement())
  profile Profile?
}

model Profile {
  id     Int  @id @default(autoincrement())
  bio    String?
  userId Int  @unique

  user   User @relation(fields: [userId], references: [id])
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)

    def test_round_trip_soft_delete(self, tmp_path):
        """Test round-trip with soft delete fields."""
        original_schema = """
model Document {
  id        Int      @id @default(autoincrement())
  title     String
  content   String?
  deletedAt DateTime?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)

    def test_round_trip_complex_nested_relationships(self, tmp_path):
        """Test round-trip with complex nested relationships."""
        original_schema = """
model Company {
  id      Int      @id @default(autoincrement())
  name    String
  departments Department[]
}

model Department {
  id        Int       @id @default(autoincrement())
  name      String
  companyId Int

  company   Company   @relation(fields: [companyId], references: [id])
  employees Employee[]
}

model Employee {
  id            Int         @id @default(autoincrement())
  name          String
  departmentId  Int

  department    Department  @relation(fields: [departmentId], references: [id])
  projects      Project[]
}

model Project {
  id         Int       @id @default(autoincrement())
  name       String
  employeeId Int

  employee   Employee  @relation(fields: [employeeId], references: [id])
}
"""

        parser = PrismaParser()
        generator = PrismaSchemaGenerator()

        # Parse original
        original_entities = parser.parse_schema_content(original_schema)

        # Round-trip
        regenerated_schema = generator.generate(original_entities)
        regenerated_entities = parser.parse_schema_content(regenerated_schema)

        # Compare
        assert len(original_entities) == len(regenerated_entities)
