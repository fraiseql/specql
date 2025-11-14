"""Generate 100-entity Prisma schema for performance testing."""

from pathlib import Path


def generate_prisma_schema_100_entities() -> str:
    """Generate Prisma schema with 100 models."""
    lines = []

    # Header
    lines.append("""generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
""")

    # Generate 100 entities
    for i in range(100):
        entity_name = f"Entity{i:03d}"
        prev_entity = f"Entity{max(0, i - 1):03d}" if i > 0 else "Entity000"

        model = f"""
model {entity_name} {{
  id          Int       @id @default(autoincrement())
  name        String
  description String?
  value{i}    Int
  active      Boolean   @default(true)
  relatedId   Int?

  related     {prev_entity}? @relation(fields: [relatedId], references: [id])

  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
  deletedAt   DateTime?
}}
"""
        lines.append(model)

    return "\n".join(lines)


if __name__ == "__main__":
    schema = generate_prisma_schema_100_entities()
    output_file = Path("tests/integration/typescript/benchmark_dataset/schema.prisma")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(schema)
    print(f"✅ Generated 100-entity Prisma schema: {output_file}")
