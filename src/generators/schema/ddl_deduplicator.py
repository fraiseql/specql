"""
DDL deduplication utilities

Prevents duplicate CREATE INDEX and COMMENT statements
"""



class DDLDeduplicator:
    """Remove duplicate DDL statements"""

    @staticmethod
    def deduplicate_indexes(indexes: list[str]) -> list[str]:
        """
        Remove duplicate index statements

        Args:
            indexes: List of CREATE INDEX statements

        Returns:
            Deduplicated list (preserves order of first occurrence)
        """
        seen = set()
        result = []

        for idx in indexes:
            # Normalize whitespace for comparison
            normalized = " ".join(idx.split())

            if normalized not in seen:
                seen.add(normalized)
                result.append(idx)

        return result

    @staticmethod
    def deduplicate_comments(comments: list[str]) -> list[str]:
        """
        Remove duplicate comment statements

        Args:
            comments: List of COMMENT ON COLUMN statements

        Returns:
            Deduplicated list (preserves order of first occurrence)
        """
        seen = set()
        result = []

        for comment in comments:
            # Normalize whitespace for comparison
            normalized = " ".join(comment.split())

            if normalized not in seen:
                seen.add(normalized)
                result.append(comment)

        return result

    @staticmethod
    def deduplicate_ddl(ddl_statements: list[str]) -> list[str]:
        """
        Remove duplicate DDL statements of any type

        Args:
            ddl_statements: List of SQL DDL statements

        Returns:
            Deduplicated list
        """
        seen = set()
        result = []

        for stmt in ddl_statements:
            # Normalize whitespace
            normalized = " ".join(stmt.split())

            if normalized not in seen:
                seen.add(normalized)
                result.append(stmt)

        return result
