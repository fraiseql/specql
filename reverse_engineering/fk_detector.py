"""
Foreign Key Detector

Detects foreign key relationships from ALTER TABLE statements and converts
fk_* columns to ref() relationships.
"""

from dataclasses import dataclass
from typing import List
import re

from .table_parser import ParsedTable


@dataclass
class ForeignKeyInfo:
    """Information about a foreign key relationship."""

    column: str  # fk_company
    references_schema: str  # management
    references_table: str  # tb_organization
    references_column: str  # pk_organization
    entity_name: str  # Organization (inferred)


class ForeignKeyDetector:
    """Detects foreign key relationships in SQL."""

    def detect(
        self, parsed_table: ParsedTable, alter_statements: List[str]
    ) -> List[ForeignKeyInfo]:
        """Detect foreign keys from ALTER TABLE statements."""
        foreign_keys = []

        for alter_sql in alter_statements:
            fks = self._parse_alter_table_fk(alter_sql)
            foreign_keys.extend(fks)

        return foreign_keys

    def _parse_alter_table_fk(self, alter_sql: str) -> List[ForeignKeyInfo]:
        """Parse ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY."""
        foreign_keys = []

        # Look for FOREIGN KEY pattern
        fk_pattern = r"""
            ALTER\s+TABLE\s+\w+\.\w+\s+
            ADD\s+CONSTRAINT\s+\w+\s+
            FOREIGN\s+KEY\s*\(\s*(\w+)\s*\)\s*
            REFERENCES\s+(\w+)\.(\w+)\s*\(\s*(\w+)\s*\)
        """

        matches = re.findall(fk_pattern, alter_sql, re.IGNORECASE | re.VERBOSE)

        for match in matches:
            fk_column, ref_schema, ref_table, ref_column = match

            entity_name = self._infer_entity_name(ref_table)

            fk_info = ForeignKeyInfo(
                column=fk_column,
                references_schema=ref_schema,
                references_table=ref_table,
                references_column=ref_column,
                entity_name=entity_name,
            )

            foreign_keys.append(fk_info)

        return foreign_keys

    def _infer_entity_name(self, table_name: str) -> str:
        """Infer entity name from table name (tb_organization → Organization)."""
        # Remove tb_ or tv_ prefix
        name = table_name.removeprefix("tb_").removeprefix("tv_")

        # Convert snake_case to PascalCase
        return "".join(word.capitalize() for word in name.split("_"))
