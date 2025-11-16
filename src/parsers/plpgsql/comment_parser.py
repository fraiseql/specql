"""
Comment parser for extracting metadata from PostgreSQL COMMENT statements.

Parses COMMENT ON TABLE statements like:
COMMENT ON TABLE catalog.tb_language IS '[Table: 010111 | Write-Side.Common.Locale.Language] Defines...';
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class CommentMetadata:
    """Metadata extracted from COMMENT ON TABLE"""

    table_code: str  # "010111"
    category: str  # "Write-Side"
    domain_hierarchy: list[str]  # ["Common", "Locale", "Language"]
    description: str  # Main description text


class CommentParser:
    """Parse PostgreSQL COMMENT metadata"""

    COMMENT_PATTERN = r"COMMENT\s+ON\s+TABLE\s+\S+\s+IS\s+'(.+?)'"
    METADATA_PATTERN = r"\[Table:\s*(\d+)\s*\|\s*([^\]]+)\]\s*(.+)"

    def extract_comment_metadata(self, sql: str) -> Optional[CommentMetadata]:
        """
        Extract metadata from COMMENT ON TABLE statement

        Example:
            Input: COMMENT ON TABLE catalog.tb_language IS
                   '[Table: 010111 | Write-Side.Common.Locale.Language] Defines...';

            Returns:
                CommentMetadata(
                    table_code="010111",
                    category="Write-Side",
                    domain_hierarchy=["Common", "Locale", "Language"],
                    description="Defines supported languages..."
                )
        """

        # 1. Extract full COMMENT text
        comment_match = re.search(self.COMMENT_PATTERN, sql, re.IGNORECASE | re.DOTALL)
        if not comment_match:
            return None

        comment_text = comment_match.group(1)

        # 2. Parse metadata section
        metadata_match = re.match(self.METADATA_PATTERN, comment_text)
        if not metadata_match:
            # No metadata, just description
            return CommentMetadata(
                table_code="",
                category="",
                domain_hierarchy=[],
                description=comment_text.strip(),
            )

        table_code = metadata_match.group(1)
        hierarchy_str = metadata_match.group(2)
        description = metadata_match.group(3).strip()

        # 3. Parse domain hierarchy (Write-Side.Common.Locale.Language)
        parts = hierarchy_str.split(".")
        category = parts[0] if parts else ""
        domain_hierarchy = parts[1:] if len(parts) > 1 else []

        return CommentMetadata(
            table_code=table_code,
            category=category,
            domain_hierarchy=domain_hierarchy,
            description=description,
        )
