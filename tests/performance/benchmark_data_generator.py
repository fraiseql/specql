"""
Benchmark dataset generator for performance testing.

Generates realistic PostgreSQL schemas with:
- Multiple entities (10-1000+)
- Foreign key relationships
- Trinity pattern
- Audit fields
- Actions
- Complex constraints
"""

import random
from dataclasses import dataclass
from typing import List, Set, Tuple, Optional
from pathlib import Path


@dataclass
class BenchmarkEntity:
    """Represents a benchmark entity configuration"""

    name: str
    table_name: str
    num_fields: int
    has_trinity: bool
    has_audit_fields: bool
    has_deduplication: bool
    foreign_keys: List[Tuple[str, str]]  # (field_name, referenced_entity)
    num_actions: int
    num_indexes: int


class BenchmarkDataGenerator:
    """Generate realistic benchmark datasets"""

    def __init__(self, seed: int = 42):
        """Initialize with reproducible random seed"""
        random.seed(seed)
        self.entities: List[BenchmarkEntity] = []
        self.entity_name_map: dict[str, str] = {}  # name -> table_name

    def generate_dataset(
        self,
        num_entities: int = 100,
        avg_fields_per_entity: int = 12,
        relationship_density: float = 0.3,
        trinity_percentage: float = 0.80,
        audit_fields_percentage: float = 0.90,
        dedup_percentage: float = 0.20,
        actions_per_entity: int = 3,
    ) -> List[BenchmarkEntity]:
        """
        Generate complete benchmark dataset.

        Args:
            num_entities: Number of entities to generate
            avg_fields_per_entity: Average number of fields per entity
            relationship_density: Probability of foreign key between entities (0.0-1.0)
            trinity_percentage: Percentage of entities with Trinity pattern
            audit_fields_percentage: Percentage with audit fields
            dedup_percentage: Percentage with deduplication fields
            actions_per_entity: Average number of actions per entity

        Returns:
            List of BenchmarkEntity configurations
        """
        self.entities = []
        self.entity_name_map = {}

        # Step 1: Generate entities without relationships
        for i in range(num_entities):
            entity = self._generate_entity(
                index=i,
                avg_fields=avg_fields_per_entity,
                trinity_prob=trinity_percentage,
                audit_prob=audit_fields_percentage,
                dedup_prob=dedup_percentage,
                num_actions=actions_per_entity,
            )
            self.entities.append(entity)
            self.entity_name_map[entity.name] = entity.table_name

        # Step 2: Add foreign key relationships
        self._add_relationships(relationship_density)

        return self.entities

    def _generate_entity(
        self,
        index: int,
        avg_fields: int,
        trinity_prob: float,
        audit_prob: float,
        dedup_prob: float,
        num_actions: int,
    ) -> BenchmarkEntity:
        """Generate single entity configuration"""

        # Entity name from realistic domains
        domains = [
            "Customer",
            "Order",
            "Product",
            "Invoice",
            "Payment",
            "Shipment",
            "Employee",
            "Department",
            "Project",
            "Task",
            "Contact",
            "Company",
            "Account",
            "Transaction",
            "Report",
            "Document",
            "Message",
            "Notification",
            "User",
            "Role",
            "Permission",
            "Audit",
            "Log",
            "Setting",
            "Configuration",
        ]

        if index < len(domains):
            name = domains[index]
        else:
            name = f"Entity{index:03d}"

        table_name = f"tb_{name.lower()}"

        # Vary number of fields (gaussian distribution)
        num_fields = max(3, int(random.gauss(avg_fields, avg_fields * 0.3)))

        # Patterns
        has_trinity = random.random() < trinity_prob
        has_audit = random.random() < audit_prob
        has_dedup = random.random() < dedup_prob

        # Actions (1-5 per entity)
        num_entity_actions = random.randint(1, min(num_actions + 2, 5))

        # Indexes (2-6 per entity)
        num_indexes = random.randint(2, 6)

        return BenchmarkEntity(
            name=name,
            table_name=table_name,
            num_fields=num_fields,
            has_trinity=has_trinity,
            has_audit_fields=has_audit,
            has_deduplication=has_dedup,
            foreign_keys=[],  # Added in next step
            num_actions=num_entity_actions,
            num_indexes=num_indexes,
        )

    def _add_relationships(self, density: float):
        """Add foreign key relationships between entities"""

        # Create DAG of relationships (no cycles for simplicity)
        for i, entity in enumerate(self.entities):
            # Can only reference earlier entities (prevents cycles)
            potential_targets = self.entities[:i]

            if not potential_targets:
                continue

            # Decide how many FKs this entity has (0-3)
            num_fks = 0
            for _ in range(3):
                if random.random() < density:
                    num_fks += 1

            # Add foreign keys
            if num_fks > 0:
                # Sample without replacement
                targets = random.sample(
                    potential_targets, min(num_fks, len(potential_targets))
                )

                for target in targets:
                    fk_field_name = f"pk_{target.name.lower()}"
                    entity.foreign_keys.append((fk_field_name, target.name))

    def generate_ddl(self, entities: Optional[List[BenchmarkEntity]] = None) -> str:
        """
        Generate PostgreSQL DDL for benchmark entities.

        Args:
            entities: List of entities (uses self.entities if None)

        Returns:
            Complete DDL as string
        """
        if entities is None:
            entities = self.entities

        ddl_parts = [
            "-- Benchmark Dataset DDL",
            "-- Generated by BenchmarkDataGenerator",
            "",
            "CREATE SCHEMA IF NOT EXISTS benchmark;",
            "",
        ]

        for entity in entities:
            ddl_parts.append(self._generate_entity_ddl(entity))
            ddl_parts.append("")

        return "\n".join(ddl_parts)

    def _generate_entity_ddl(self, entity: BenchmarkEntity) -> str:
        """Generate DDL for single entity"""

        lines = [f"CREATE TABLE benchmark.{entity.table_name} ("]
        columns = []

        # Primary key (always present)
        pk_name = f"pk_{entity.name.lower()}"
        columns.append(f"    {pk_name} SERIAL PRIMARY KEY")

        # Trinity pattern
        if entity.has_trinity:
            columns.append("    id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid()")
            columns.append("    identifier TEXT NOT NULL UNIQUE")

        # Foreign keys
        for fk_field, referenced_entity in entity.foreign_keys:
            ref_table = f"tb_{referenced_entity.lower()}"
            ref_pk = f"pk_{referenced_entity.lower()}"
            columns.append(
                f"    {fk_field} INTEGER NOT NULL REFERENCES benchmark.{ref_table}({ref_pk})"
            )

        # Regular fields
        field_types = [
            "TEXT",
            "INTEGER",
            "NUMERIC(10,2)",
            "BOOLEAN",
            "TIMESTAMP",
            "JSONB",
        ]
        num_regular_fields = entity.num_fields

        for i in range(num_regular_fields):
            field_type = random.choice(field_types)
            field_name = f"field_{i:02d}"
            nullable = "NULL" if random.random() < 0.3 else "NOT NULL"
            columns.append(f"    {field_name} {field_type} {nullable}")

        # Deduplication fields
        if entity.has_deduplication:
            columns.append("    dedup_key TEXT")
            columns.append("    dedup_hash TEXT")
            columns.append("    is_unique BOOLEAN DEFAULT TRUE")

        # Audit fields
        if entity.has_audit_fields:
            columns.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns.append("    deleted_at TIMESTAMP")

        lines.append(",\n".join(columns))
        lines.append(");")

        # Indexes
        ddl = "\n".join(lines)

        if entity.has_trinity:
            ddl += f"\nCREATE INDEX idx_{entity.name.lower()}_id ON benchmark.{entity.table_name}(id);"
            ddl += f"\nCREATE INDEX idx_{entity.name.lower()}_identifier ON benchmark.{entity.table_name}(identifier);"

        if entity.has_deduplication:
            ddl += f"\nCREATE INDEX idx_{entity.name.lower()}_dedup_hash ON benchmark.{entity.table_name}(dedup_hash);"

        # Actions (PL/pgSQL functions)
        if entity.num_actions > 0:
            ddl += "\n" + self._generate_actions_ddl(entity)

        return ddl

    def _generate_actions_ddl(self, entity: BenchmarkEntity) -> str:
        """Generate PL/pgSQL action functions for entity"""

        actions_ddl = []

        # Create action
        pk_name = f"pk_{entity.name.lower()}"
        actions_ddl.append(f"""
CREATE OR REPLACE FUNCTION benchmark.create_{entity.name.lower()}(
    p_field_00 TEXT
) RETURNS INTEGER AS $$
DECLARE
    v_{pk_name} INTEGER;
BEGIN
    INSERT INTO benchmark.{entity.table_name} (field_00)
    VALUES (p_field_00)
    RETURNING {pk_name} INTO v_{pk_name};

    RETURN v_{pk_name};
END;
$$ LANGUAGE plpgsql;
""")

        # Update action (if multiple actions requested)
        if entity.num_actions >= 2:
            actions_ddl.append(f"""
CREATE OR REPLACE FUNCTION benchmark.update_{entity.name.lower()}(
    p_{pk_name} INTEGER,
    p_field_00 TEXT
) RETURNS VOID AS $$
BEGIN
    UPDATE benchmark.{entity.table_name}
    SET field_00 = p_field_00,
        updated_at = CURRENT_TIMESTAMP
    WHERE {pk_name} = p_{pk_name};
END;
$$ LANGUAGE plpgsql;
""")

        # Soft delete action (if 3+ actions)
        if entity.num_actions >= 3:
            actions_ddl.append(f"""
CREATE OR REPLACE FUNCTION benchmark.delete_{entity.name.lower()}(
    p_{pk_name} INTEGER
) RETURNS VOID AS $$
BEGIN
    UPDATE benchmark.{entity.table_name}
    SET deleted_at = CURRENT_TIMESTAMP
    WHERE {pk_name} = p_{pk_name};
END;
$$ LANGUAGE plpgsql;
""")

        return "\n".join(actions_ddl)

    def save_ddl(
        self, filepath: Path, entities: Optional[List[BenchmarkEntity]] = None
    ):
        """Save generated DDL to file"""
        ddl = self.generate_ddl(entities)
        filepath.write_text(ddl)

    def generate_statistics_report(
        self, entities: Optional[List[BenchmarkEntity]] = None
    ) -> str:
        """Generate statistics about the benchmark dataset"""

        if entities is None:
            entities = self.entities

        total_entities = len(entities)
        total_fields = sum(e.num_fields for e in entities)
        total_fks = sum(len(e.foreign_keys) for e in entities)
        total_actions = sum(e.num_actions for e in entities)
        total_indexes = sum(e.num_indexes for e in entities)

        trinity_count = sum(1 for e in entities if e.has_trinity)
        audit_count = sum(1 for e in entities if e.has_audit_fields)
        dedup_count = sum(1 for e in entities if e.has_deduplication)

        return f"""
# Benchmark Dataset Statistics

## Overview
- Total Entities: {total_entities}
- Total Fields: {total_fields}
- Average Fields per Entity: {total_fields / total_entities:.1f}
- Total Foreign Keys: {total_fks}
- Total Actions: {total_actions}
- Total Indexes: {total_indexes}

## Pattern Distribution
- Trinity Pattern: {trinity_count} ({trinity_count / total_entities * 100:.1f}%)
- Audit Fields: {audit_count} ({audit_count / total_entities * 100:.1f}%)
- Deduplication: {dedup_count} ({dedup_count / total_entities * 100:.1f}%)

## Complexity Metrics
- Relationship Density: {total_fks / total_entities:.2f} FKs per entity
- Actions per Entity: {total_actions / total_entities:.1f}
- Indexes per Entity: {total_indexes / total_entities:.1f}

## Estimated Size
- DDL Lines: ~{total_entities * 50} lines
- Estimated Parse Time: ~{total_entities * 0.05:.1f} seconds
- Estimated Generate Time: ~{total_entities * 0.15:.1f} seconds
"""


# CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate benchmark datasets")
    parser.add_argument("--entities", type=int, default=100, help="Number of entities")
    parser.add_argument(
        "--output", type=str, default="benchmark_dataset.sql", help="Output file"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    generator = BenchmarkDataGenerator(seed=args.seed)
    entities = generator.generate_dataset(num_entities=args.entities)

    output_path = Path(args.output)
    generator.save_ddl(output_path, entities)

    print(f"✅ Generated {args.entities} entities")
    print(f"📝 Saved to {output_path}")
    print(generator.generate_statistics_report(entities))
