"""
Tests for HierarchicalFileWriter
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.generators.schema.hierarchical_file_writer import (
    FileSpec,
    HierarchicalFileWriter,
    PathGenerator,
)


class MockPathGenerator:
    """Mock implementation of PathGenerator for testing"""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def generate_path(self, file_spec: FileSpec) -> Path:
        """Generate mock path based on file spec"""
        return self.base_path / f"{file_spec.code}_{file_spec.name}.sql"


class TestFileSpec:
    """Test FileSpec dataclass"""

    def test_file_spec_creation(self):
        """Test basic FileSpec creation"""
        spec = FileSpec(
            code="012361",
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side"
        )

        assert spec.code == "012361"
        assert spec.name == "tb_contact"
        assert spec.content == "CREATE TABLE tb_contact (...);"
        assert spec.layer == "write_side"

    def test_file_spec_read_side(self):
        """Test FileSpec for read-side"""
        spec = FileSpec(
            code="0220310",
            name="tv_contact",
            content="CREATE VIEW tv_contact AS SELECT ...;",
            layer="read_side"
        )

        assert spec.code == "0220310"
        assert spec.name == "tv_contact"
        assert spec.layer == "read_side"


class TestHierarchicalFileWriter:
    """Test HierarchicalFileWriter functionality"""

    def test_init(self):
        """Test initialization"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        assert writer.path_generator == mock_generator
        assert not writer.dry_run

    def test_init_dry_run(self):
        """Test initialization with dry run"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator, dry_run=True)

        assert writer.dry_run

    def test_write_files_empty_list(self):
        """Test writing empty file list"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        result = writer.write_files([])

        assert result == []

    def test_write_single_file_write_side(self):
        """Test writing single write-side file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            path_generator = MockPathGenerator(base_path)

            writer = HierarchicalFileWriter(path_generator)

            spec = FileSpec(
                code="012361",
                name="tb_contact",
                content="CREATE TABLE tb_contact (id UUID PRIMARY KEY);",
                layer="write_side"
            )

            result_path = writer.write_single_file(spec)

            expected_path = base_path / "012361_tb_contact.sql"
            assert result_path == expected_path
            assert expected_path.exists()

            with open(expected_path) as f:
                content = f.read()
                assert content == "CREATE TABLE tb_contact (id UUID PRIMARY KEY);"

    def test_write_single_file_read_side(self):
        """Test writing single read-side file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            path_generator = MockPathGenerator(base_path)

            writer = HierarchicalFileWriter(path_generator)

            spec = FileSpec(
                code="0220310",
                name="tv_contact",
                content="CREATE VIEW tv_contact AS SELECT * FROM tb_contact;",
                layer="read_side"
            )

            result_path = writer.write_single_file(spec)

            expected_path = base_path / "0220310_tv_contact.sql"
            assert result_path == expected_path
            assert expected_path.exists()

    def test_write_files_multiple(self):
        """Test writing multiple files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            path_generator = MockPathGenerator(base_path)

            writer = HierarchicalFileWriter(path_generator)

            specs = [
                FileSpec(
                    code="012361",
                    name="tb_contact",
                    content="CREATE TABLE tb_contact (id UUID PRIMARY KEY);",
                    layer="write_side"
                ),
                FileSpec(
                    code="0220310",
                    name="tv_contact",
                    content="CREATE VIEW tv_contact AS SELECT * FROM tb_contact;",
                    layer="read_side"
                )
            ]

            result_paths = writer.write_files(specs)

            assert len(result_paths) == 2
            assert all(path.exists() for path in result_paths)

    def test_write_single_file_dry_run(self):
        """Test dry run mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            path_generator = MockPathGenerator(base_path)

            writer = HierarchicalFileWriter(path_generator, dry_run=True)

            spec = FileSpec(
                code="012361",
                name="tb_contact",
                content="CREATE TABLE tb_contact (id UUID PRIMARY KEY);",
                layer="write_side"
            )

            result_path = writer.write_single_file(spec)

            expected_path = base_path / "012361_tb_contact.sql"
            assert result_path == expected_path
            # File should not exist in dry run
            assert not expected_path.exists()

    def test_write_files_with_directory_creation(self):
        """Test that directories are created automatically"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            deep_path = base_path / "deep" / "nested" / "structure"

            class DeepPathGenerator:
                def generate_path(self, file_spec: FileSpec) -> Path:
                    return deep_path / f"{file_spec.code}_{file_spec.name}.sql"

            writer = HierarchicalFileWriter(DeepPathGenerator())

            spec = FileSpec(
                code="012361",
                name="tb_contact",
                content="CREATE TABLE tb_contact (id UUID PRIMARY KEY);",
                layer="write_side"
            )

            result_path = writer.write_single_file(spec)

            assert result_path == deep_path / "012361_tb_contact.sql"
            assert result_path.exists()
            assert result_path.parent.exists()

    def test_write_single_file_7_digit_write_side(self):
        """Test writing single 7-digit write-side file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            path_generator = MockPathGenerator(base_path)

            writer = HierarchicalFileWriter(path_generator)

            spec = FileSpec(
                code="0123611",  # 7-digit code
                name="tb_contact",
                content="CREATE TABLE tb_contact (id UUID PRIMARY KEY);",
                layer="write_side"
            )

            result_path = writer.write_single_file(spec)

            expected_path = base_path / "0123611_tb_contact.sql"
            assert result_path == expected_path
            assert expected_path.exists()

            with open(expected_path) as f:
                content = f.read()
                assert content == "CREATE TABLE tb_contact (id UUID PRIMARY KEY);"

    def test_write_single_file_function(self):
        """Test writing single function file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            path_generator = MockPathGenerator(base_path)

            writer = HierarchicalFileWriter(path_generator)

            spec = FileSpec(
                code="0320311",
                name="fn_contact_create",
                content="CREATE OR REPLACE FUNCTION fn_contact_create(...) ...;",
                layer="functions"
            )

            result_path = writer.write_single_file(spec)

            expected_path = base_path / "0320311_fn_contact_create.sql"
            assert result_path == expected_path
            assert expected_path.exists()

            with open(expected_path) as f:
                content = f.read()
                assert content == "CREATE OR REPLACE FUNCTION fn_contact_create(...) ...;"


class TestValidation:
    """Test validation logic"""

    def test_validate_file_spec_valid_write_side(self):
        """Test validation of valid write-side file spec"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="012361",
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side"
        )

        # Should not raise
        writer._validate_file_spec(spec)

    def test_validate_file_spec_valid_read_side(self):
        """Test validation of valid read-side file spec"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="0220310",
            name="tv_contact",
            content="CREATE VIEW tv_contact AS ...;",
            layer="read_side"
        )

        # Should not raise
        writer._validate_file_spec(spec)

    def test_validate_file_spec_missing_code(self):
        """Test validation fails with missing code"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="",
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side"
        )

        with pytest.raises(ValueError, match="File spec must have a code"):
            writer._validate_file_spec(spec)

    def test_validate_file_spec_missing_name(self):
        """Test validation fails with missing name"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="012361",
            name="",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side"
        )

        with pytest.raises(ValueError, match="File spec must have a name"):
            writer._validate_file_spec(spec)

    def test_validate_file_spec_none_content(self):
        """Test validation fails with None content"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="012361",
            name="tb_contact",
            content=None,  # type: ignore
            layer="write_side"
        )

        with pytest.raises(ValueError, match="File spec must have content"):
            writer._validate_file_spec(spec)

    def test_validate_file_spec_invalid_layer(self):
        """Test validation fails with invalid layer"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="012361",
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="invalid_layer"
        )

        with pytest.raises(ValueError, match="Invalid layer 'invalid_layer'"):
            writer._validate_file_spec(spec)

    def test_validate_file_spec_wrong_code_length_write_side(self):
        """Test validation fails with wrong code length for write-side"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="01236123",  # 8 digits instead of 6
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side"
        )

        with pytest.raises(ValueError, match="Write-side code must be 6 or 7 digits"):
            writer._validate_file_spec(spec)

    def test_validate_file_spec_wrong_code_length_read_side(self):
        """Test validation fails with wrong code length for read-side"""
        mock_generator = Mock(spec=PathGenerator)
        writer = HierarchicalFileWriter(mock_generator)

        spec = FileSpec(
            code="022031",  # 6 digits instead of 7
            name="tv_contact",
            content="CREATE VIEW tv_contact AS ...;",
            layer="read_side"
        )

        with pytest.raises(ValueError, match="Read-side code must be 7 digits"):
            writer._validate_file_spec(spec)