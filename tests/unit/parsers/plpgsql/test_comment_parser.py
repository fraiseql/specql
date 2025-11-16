"""Unit tests for CommentParser"""

import pytest
from src.parsers.plpgsql.comment_parser import CommentParser, CommentMetadata


class TestCommentParser:
    """Test CommentParser"""

    @pytest.fixture
    def parser(self):
        return CommentParser()

    def test_extract_comment_metadata_full(self, parser):
        """Test extracting metadata from COMMENT statement with full metadata"""

        sql = """
        COMMENT ON TABLE catalog.tb_language IS '[Table: 010111 | Write-Side.Common.Locale.Language] Defines supported languages...';
        """

        meta = parser.extract_comment_metadata(sql)

        assert meta is not None
        assert meta.table_code == "010111"
        assert meta.category == "Write-Side"
        assert meta.domain_hierarchy == ["Common", "Locale", "Language"]
        assert "Defines supported languages" in meta.description

    def test_extract_comment_metadata_minimal(self, parser):
        """Test extracting metadata with just description"""

        sql = """
        COMMENT ON TABLE catalog.tb_language IS 'This table stores language information.';
        """

        meta = parser.extract_comment_metadata(sql)

        assert meta is not None
        assert meta.table_code == ""
        assert meta.category == ""
        assert meta.domain_hierarchy == []
        assert meta.description == "This table stores language information."

    def test_extract_comment_metadata_multiline(self, parser):
        """Test extracting metadata from multiline COMMENT"""

        sql = """
        COMMENT ON TABLE catalog.tb_language IS
        '[Table: 010111 | Write-Side.Common.Locale.Language]
        Defines supported languages, following ISO 639-1/639-2 standards.
        Used for translation, formatting, and localization features.';
        """

        meta = parser.extract_comment_metadata(sql)

        assert meta is not None
        assert meta.table_code == "010111"
        assert meta.category == "Write-Side"
        assert meta.domain_hierarchy == ["Common", "Locale", "Language"]
        assert "ISO 639" in meta.description

    def test_extract_comment_metadata_no_comment(self, parser):
        """Test returns None when no COMMENT statement"""

        sql = """
        CREATE TABLE catalog.tb_language (
            id INTEGER PRIMARY KEY
        );
        """

        meta = parser.extract_comment_metadata(sql)
        assert meta is None

    def test_extract_comment_metadata_malformed(self, parser):
        """Test handling malformed COMMENT statements"""

        # This comment doesn't have proper quotes, so it won't be extracted
        sql = """
        COMMENT ON TABLE catalog.tb_language IS [Table: 010111 | Write-Side.Common.Locale.Language] Defines...;
        """

        meta = parser.extract_comment_metadata(sql)

        # Should return None for malformed comments
        assert meta is None

    def test_comment_pattern_matching(self, parser):
        """Test COMMENT pattern regex"""

        import re

        # Valid patterns
        valid_comments = [
            "COMMENT ON TABLE schema.table IS 'description';",
            'COMMENT ON TABLE "schema"."table" IS \'desc\';',
            "comment on table test.table is 'desc';",  # case insensitive
        ]

        pattern = re.compile(
            r"COMMENT\s+ON\s+TABLE\s+\S+\s+IS\s+'(.+?)'", re.IGNORECASE | re.DOTALL
        )

        for comment in valid_comments:
            match = pattern.search(comment)
            assert match is not None, f"Failed to match: {comment}"

    def test_metadata_pattern_matching(self, parser):
        """Test metadata pattern regex"""

        import re

        # Valid metadata strings
        valid_metadata = [
            "[Table: 010111 | Write-Side.Common.Locale.Language] Description",
            "[Table: 02005 | Query-Side.Base.Common] View description",
            "[Table: 03542 | Functions.SCD.Allocation] Function description",
        ]

        pattern = re.compile(r"\[Table:\s*(\d+)\s*\|\s*([^\]]+)\]\s*(.+)", re.DOTALL)

        for metadata in valid_metadata:
            match = pattern.match(metadata)
            assert match is not None, f"Failed to match: {metadata}"
            assert match.group(1)  # table_code
            assert match.group(2)  # hierarchy
            assert match.group(3)  # description
