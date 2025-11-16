"""
File path parser for PrintOptim hierarchical SQL schema structure.

Extracts organizational metadata from file paths like:
01_write_side/010_i18n/0101_locale/01011_language/010111_tb_language.sql
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


@dataclass
class FilePathMetadata:
    """Metadata extracted from file path"""

    category: str  # "write_side", "query_side", "functions"
    domain_path: List[str]  # ["010_i18n", "0101_locale", "01011_language"]
    domain_labels: List[str]  # ["i18n", "locale", "language"]
    table_code: str  # "010111"
    table_type: str  # "tb", "tl", "fn"
    entity_name: str  # "language"
    full_path: str  # Original file path
    relative_path: str  # Relative to root


class FilePathParser:
    """Parse PrintOptim hierarchical file paths"""

    def parse_path(self, file_path: Path, root_dir: Path) -> FilePathMetadata:
        """
        Parse file path to extract organizational metadata

        Example:
            Input: ../db/0_schema/01_write_side/010_i18n/0101_locale/01011_language/010111_tb_language.sql

            Returns:
                FilePathMetadata(
                    category="write_side",
                    domain_path=["010_i18n", "0101_locale", "01011_language"],
                    domain_labels=["i18n", "locale", "language"],
                    table_code="010111",
                    table_type="tb",
                    entity_name="language",
                    ...
                )
        """

        # 1. Get relative path from root
        rel_path = file_path.relative_to(root_dir)

        # 2. Extract category (01_write_side → "write_side")
        category = self._extract_category(rel_path.parts[0])

        # 3. Extract domain path (all intermediate directories)
        domain_path = list(rel_path.parts[1:-1])

        # 4. Extract domain labels (strip numbering)
        domain_labels = [self._strip_numbering(d) for d in domain_path]

        # 5. Parse filename
        filename = file_path.stem  # "010111_tb_language"
        table_code, table_type, entity_name = self._parse_filename(filename)

        return FilePathMetadata(
            category=category,
            domain_path=domain_path,
            domain_labels=domain_labels,
            table_code=table_code,
            table_type=table_type,
            entity_name=entity_name,
            full_path=str(file_path),
            relative_path=str(rel_path),
        )

    def _extract_category(self, dir_name: str) -> str:
        """01_write_side → write_side"""
        return re.sub(r"^\d+_", "", dir_name)

    def _strip_numbering(self, dir_name: str) -> str:
        """010_i18n → i18n, 01011_language → language"""
        return re.sub(r"^\d+_", "", dir_name)

    def _parse_filename(self, filename: str) -> Tuple[str, str, str]:
        """
        010111_tb_language → ("010111", "tb", "language")
        01042_fn_format_address → ("01042", "fn", "format_address")
        035017_allocate_to_stock → ("035017", "allocate_to_stock", "allocate_to_stock")  # functions without fn_ prefix
        """
        # Try pattern with type prefix first
        pattern_with_type = r"^(\d+)_(tb|tl|fn|vw)_(.+)$"
        match = re.match(pattern_with_type, filename)

        if match:
            return match.group(1), match.group(2), match.group(3)

        # Try pattern without type prefix (for functions)
        pattern_without_type = r"^(\d+)_(.+)$"
        match = re.match(pattern_without_type, filename)

        if match:
            code = match.group(1)
            name = match.group(2)
            # For functions without explicit type, use the name as type too
            return code, name, name

        raise ValueError(f"Invalid filename format: {filename}")
