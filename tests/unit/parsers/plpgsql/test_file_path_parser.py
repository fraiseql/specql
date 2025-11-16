"""Unit tests for FilePathParser"""

import pytest
from pathlib import Path
from src.parsers.plpgsql.file_path_parser import FilePathParser, FilePathMetadata


class TestFilePathParser:
    """Test FilePathParser"""

    @pytest.fixture
    def parser(self):
        return FilePathParser()

    def test_parse_write_side_table(self, parser):
        """Test parsing write-side table path"""

        file_path = Path(
            "../printoptim/db/0_schema/01_write_side/010_i18n/0101_locale/01011_language/010111_tb_language.sql"
        )
        root_dir = Path("../printoptim/db/0_schema")

        meta = parser.parse_path(file_path, root_dir)

        assert meta.category == "write_side"
        assert meta.domain_path == ["010_i18n", "0101_locale", "01011_language"]
        assert meta.domain_labels == ["i18n", "locale", "language"]
        assert meta.table_code == "010111"
        assert meta.table_type == "tb"
        assert meta.entity_name == "language"

    def test_parse_query_side_view(self, parser):
        """Test parsing query-side view path"""

        file_path = Path(
            "db/0_schema/02_query_side/020_base_views/0201_common/02011_vw_active_contacts.sql"
        )
        root_dir = Path("db/0_schema")

        meta = parser.parse_path(file_path, root_dir)

        assert meta.category == "query_side"
        assert meta.domain_path == ["020_base_views", "0201_common"]
        assert meta.domain_labels == ["base_views", "common"]
        assert meta.table_code == "02011"
        assert meta.table_type == "vw"
        assert meta.entity_name == "active_contacts"

    def test_parse_function_file(self, parser):
        """Test parsing function file path"""

        file_path = Path(
            "db/0_schema/03_functions/035_scd/03501_allocation/035017_allocate_to_stock.sql"
        )
        root_dir = Path("db/0_schema")

        meta = parser.parse_path(file_path, root_dir)

        assert meta.category == "functions"
        assert meta.domain_path == ["035_scd", "03501_allocation"]
        assert meta.domain_labels == ["scd", "allocation"]
        assert meta.table_code == "035017"
        assert (
            meta.table_type == "allocate_to_stock"
        )  # This is actually the function name
        assert meta.entity_name == "allocate_to_stock"

    def test_extract_category(self, parser):
        """Test category extraction"""
        assert parser._extract_category("01_write_side") == "write_side"
        assert parser._extract_category("02_query_side") == "query_side"
        assert parser._extract_category("03_functions") == "functions"

    def test_strip_numbering(self, parser):
        """Test numbering stripping"""
        assert parser._strip_numbering("010_i18n") == "i18n"
        assert parser._strip_numbering("01011_language") == "language"
        assert parser._strip_numbering("0201_common") == "common"

    def test_parse_filename_table(self, parser):
        """Test filename parsing for table"""
        code, type_, name = parser._parse_filename("010111_tb_language")
        assert code == "010111"
        assert type_ == "tb"
        assert name == "language"

    def test_parse_filename_translation(self, parser):
        """Test filename parsing for translation table"""
        code, type_, name = parser._parse_filename("010212_tl_continent")
        assert code == "010212"
        assert type_ == "tl"
        assert name == "continent"

    def test_parse_filename_function(self, parser):
        """Test filename parsing for function without fn_ prefix"""
        code, type_, name = parser._parse_filename("035017_allocate_to_stock")
        assert code == "035017"
        assert type_ == "allocate_to_stock"
        assert name == "allocate_to_stock"

    def test_parse_filename_function_with_fn_prefix(self, parser):
        """Test filename parsing for function with fn_ prefix"""
        code, type_, name = parser._parse_filename("01042_fn_format_address")
        assert code == "01042"
        assert type_ == "fn"
        assert name == "format_address"

    def test_parse_filename_invalid(self, parser):
        """Test invalid filename raises error"""
        with pytest.raises(ValueError, match="Invalid filename format"):
            parser._parse_filename("invalid_filename")
