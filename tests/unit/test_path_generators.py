"""
Tests for PathGenerator implementations
"""

import pytest
from pathlib import Path

from src.generators.schema.hierarchical_file_writer import FileSpec
from src.generators.schema.write_side_path_generator import WriteSidePathGenerator
from src.generators.schema.read_side_path_generator import ReadSidePathGenerator


class TestWriteSidePathGenerator:
    """Test WriteSidePathGenerator functionality"""

    def test_init(self):
        """Test initialization"""
        generator = WriteSidePathGenerator()
        assert generator.base_dir == Path("generated")

    def test_init_custom_base_dir(self):
        """Test initialization with custom base directory"""
        generator = WriteSidePathGenerator("custom")
        assert generator.base_dir == Path("custom")

    def test_generate_path_write_side(self):
        """Test generating path for write-side file"""
        generator = WriteSidePathGenerator("generated")

        spec = FileSpec(
            code="012361",
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        path = generator.generate_path(spec)

        expected = (
            Path("generated")
            / "0_schema"
            / "01_write_side"
            / "012_crm"
            / "0123_customer"
            / "01236_contact"
            / "012361_tb_contact.sql"
        )
        assert path == expected

    def test_generate_path_invalid_layer(self):
        """Test error when file spec has wrong layer"""
        generator = WriteSidePathGenerator()

        spec = FileSpec(
            code="0220310",
            name="tv_contact",
            content="CREATE VIEW tv_contact AS ...;",
            layer="read_side",
        )

        with pytest.raises(
            ValueError, match="WriteSidePathGenerator can only handle write_side files"
        ):
            generator.generate_path(spec)

    def test_generate_path_invalid_code_length(self):
        """Test error when code has wrong length"""
        generator = WriteSidePathGenerator()

        spec = FileSpec(
            code="012361234",  # 9 digits instead of 6 or 7
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        with pytest.raises(ValueError, match="Write-side code must be 6 or 7 digits"):
            generator.generate_path(spec)

    def test_generate_path_invalid_schema_layer(self):
        """Test error when schema layer is not 01"""
        generator = WriteSidePathGenerator()

        spec = FileSpec(
            code="022361",  # Schema layer 02 instead of 01
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        with pytest.raises(
            ValueError, match="Invalid schema layer '02' for write-side code"
        ):
            generator.generate_path(spec)

    def test_generate_path_unknown_domain(self):
        """Test error when domain code is unknown"""
        generator = WriteSidePathGenerator()

        spec = FileSpec(
            code="019361",  # Domain 9 doesn't exist
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        with pytest.raises(ValueError, match="Unknown domain code: 9"):
            generator.generate_path(spec)

    def test_generate_path_unknown_subdomain(self):
        """Test error when subdomain code is unknown"""
        generator = WriteSidePathGenerator()

        spec = FileSpec(
            code="012961",  # Subdomain 9 doesn't exist in crm
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        with pytest.raises(ValueError, match="Unknown subdomain code: 9 in domain 2"):
            generator.generate_path(spec)

    def test_generate_path_invalid_filename_format(self):
        """Test error when filename doesn't start with tb_"""
        generator = WriteSidePathGenerator()

        spec = FileSpec(
            code="012361",
            name="contact",  # Missing tb_ prefix
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        with pytest.raises(
            ValueError, match="Write-side file name should start with 'tb_'"
        ):
            generator.generate_path(spec)

    def test_generate_path_write_side_7_digit(self):
        """Test generating path for write-side file with 7-digit code"""
        generator = WriteSidePathGenerator("generated")

        spec = FileSpec(
            code="0123611",  # 7-digit code
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        path = generator.generate_path(spec)

        # Should use the base 6 digits for path generation
        expected = (
            Path("generated")
            / "0_schema"
            / "01_write_side"
            / "012_crm"
            / "0123_customer"
            / "01236_contact"
            / "0123611_tb_contact.sql"
        )
        assert path == expected

    def test_generate_path_write_side_7_digit_audit(self):
        """Test generating path for audit table with 7-digit code"""
        generator = WriteSidePathGenerator("generated")

        spec = FileSpec(
            code="0123612",  # 7-digit code for audit table
            name="tb_contact_audit",
            content="CREATE TABLE tb_contact_audit (...);",
            layer="write_side",
        )

        path = generator.generate_path(spec)

        # Should use the base 6 digits for path generation
        expected = (
            Path("generated")
            / "0_schema"
            / "01_write_side"
            / "012_crm"
            / "0123_customer"
            / "01236_contact"
            / "0123612_tb_contact_audit.sql"
        )
        assert path == expected


class TestFunctionPathGenerator:
    """Test FunctionPathGenerator functionality"""

    def test_init(self):
        """Test initialization"""
        from src.generators.actions.function_path_generator import FunctionPathGenerator

        generator = FunctionPathGenerator()
        assert generator.base_dir == Path("generated")

    def test_init_custom_base_dir(self):
        """Test initialization with custom base directory"""
        from src.generators.actions.function_path_generator import FunctionPathGenerator

        generator = FunctionPathGenerator("custom")
        assert generator.base_dir == Path("custom")

    def test_generate_path_function(self):
        """Test generating path for function file"""
        from src.generators.actions.function_path_generator import FunctionPathGenerator

        generator = FunctionPathGenerator("generated")

        spec = FileSpec(
            code="0320311",
            name="fn_contact_create",
            content="CREATE OR REPLACE FUNCTION fn_contact_create(...) ...;",
            layer="functions",
        )

        path = generator.generate_path(spec)

        expected = (
            Path("generated")
            / "0_schema"
            / "03_functions"
            / "032_crm"
            / "0323_customer"
            / "03231_contact"
            / "0320311_fn_contact_create.sql"
        )
        assert path == expected

    def test_generate_path_function_invalid_code_length(self):
        """Test error when function code is not 7 digits"""
        from src.generators.actions.function_path_generator import FunctionPathGenerator

        generator = FunctionPathGenerator()

        spec = FileSpec(
            code="032361",  # 6 digits instead of 7
            name="fn_contact_create",
            content="CREATE OR REPLACE FUNCTION fn_contact_create(...) ...;",
            layer="functions",
        )

        with pytest.raises(ValueError, match="Function code must be 7 digits"):
            generator.generate_path(spec)

    def test_generate_path_function_invalid_schema_layer(self):
        """Test error when schema layer is not 03"""
        from src.generators.actions.function_path_generator import FunctionPathGenerator

        generator = FunctionPathGenerator()

        spec = FileSpec(
            code="0123611",  # Schema layer 01 instead of 03
            name="fn_contact_create",
            content="CREATE OR REPLACE FUNCTION fn_contact_create(...) ...;",
            layer="functions",
        )

        with pytest.raises(
            ValueError, match="Invalid schema layer '01' for function code"
        ):
            generator.generate_path(spec)

    def test_generate_path_function_unknown_domain(self):
        """Test error when domain code is unknown"""
        from src.generators.actions.function_path_generator import FunctionPathGenerator

        generator = FunctionPathGenerator()

        spec = FileSpec(
            code="0393611",  # Domain 9 doesn't exist
            name="fn_contact_create",
            content="CREATE OR REPLACE FUNCTION fn_contact_create(...) ...;",
            layer="functions",
        )

        with pytest.raises(ValueError, match="Unknown domain code: 9"):
            generator.generate_path(spec)

    def test_generate_path_function_invalid_filename_format(self):
        """Test error when filename doesn't start with fn_"""
        from src.generators.actions.function_path_generator import FunctionPathGenerator

        generator = FunctionPathGenerator()

        spec = FileSpec(
            code="0320311",  # Valid code
            name="contact_create",  # Missing fn_ prefix
            content="CREATE OR REPLACE FUNCTION fn_contact_create(...) ...;",
            layer="functions",
        )

        with pytest.raises(
            ValueError, match="Function file name should start with 'fn_'"
        ):
            generator.generate_path(spec)


class TestReadSidePathGenerator:
    """Test ReadSidePathGenerator functionality"""

    def test_init(self):
        """Test initialization"""
        generator = ReadSidePathGenerator()
        assert generator.base_dir == Path("generated")

    def test_init_custom_base_dir(self):
        """Test initialization with custom base directory"""
        generator = ReadSidePathGenerator("custom")
        assert generator.base_dir == Path("custom")

    def test_generate_path_read_side(self):
        """Test generating path for read-side file"""
        generator = ReadSidePathGenerator("generated")

        spec = FileSpec(
            code="0220310",
            name="tv_contact",
            content="CREATE VIEW tv_contact AS SELECT * FROM tb_contact;",
            layer="read_side",
        )

        path = generator.generate_path(spec)

        expected = (
            Path("generated")
            / "0_schema"
            / "02_query_side"
            / "022_crm"
            / "0223_customer"
            / "0220310_tv_contact.sql"
        )
        assert path == expected

    def test_generate_path_invalid_layer(self):
        """Test error when file spec has wrong layer"""
        generator = ReadSidePathGenerator()

        spec = FileSpec(
            code="012361",
            name="tb_contact",
            content="CREATE TABLE tb_contact (...);",
            layer="write_side",
        )

        with pytest.raises(
            ValueError, match="ReadSidePathGenerator can only handle read_side files"
        ):
            generator.generate_path(spec)

    def test_generate_path_empty_name(self):
        """Test error when file name is empty"""
        generator = ReadSidePathGenerator()

        spec = FileSpec(
            code="0220310",
            name="",  # Empty name
            content="CREATE VIEW tv_contact AS ...;",
            layer="read_side",
        )

        with pytest.raises(ValueError, match="view_name cannot be empty"):
            generator.generate_path(spec)

    def test_generate_path_invalid_code_format(self):
        """Test error when code has wrong format"""
        generator = ReadSidePathGenerator()

        spec = FileSpec(
            code="022031",  # 6 digits instead of 7
            name="tv_contact",
            content="CREATE VIEW tv_contact AS ...;",
            layer="read_side",
        )

        with pytest.raises(ValueError, match="Invalid code length: 6"):
            generator.generate_path(spec)
