"""
Integration tests for complete schema.rs generation
"""

import pytest
from pathlib import Path
from src.generators.rust.diesel_table_generator import DieselTableGenerator
from src.core.specql_parser import SpecQLParser


class TestSchemaGeneration:
    """Integration tests for schema.rs generation"""

    @pytest.fixture
    def generator(self):
        return DieselTableGenerator()

    @pytest.fixture
    def sample_entities(self):
        """Load sample SpecQL entities"""
        parser = SpecQLParser()
        # Load and parse fixture files
        contact_yaml = Path("tests/fixtures/entities/contact.yaml").read_text()
        company_yaml = Path("tests/fixtures/entities/company.yaml").read_text()

        contact = parser.parse(contact_yaml)
        company = parser.parse(company_yaml)

        # Debug: print field info
        print("Contact fields:")
        for name, field in contact.fields.items():
            print(
                f"  {name}: type_name={field.type_name}, reference_entity={field.reference_entity}"
            )
        print("Company fields:")
        for name, field in company.fields.items():
            print(
                f"  {name}: type_name={field.type_name}, reference_entity={field.reference_entity}"
            )

        return [contact, company]

    def test_generate_complete_schema_file(self, generator, sample_entities):
        """Test generating complete schema.rs"""
        result = generator.generate_schema_file(sample_entities)

        # Verify structure
        assert "diesel::table!" in result
        assert "tb_contact" in result
        assert "tb_company" in result
        assert "diesel::joinable!" in result
        assert "allow_tables_to_appear_in_same_query!" in result

    def test_generated_schema_is_valid_rust(self, generator, sample_entities):
        """Test generated code is valid Rust syntax"""
        result = generator.generate_schema_file(sample_entities)

        # Basic syntax checks - ensure no malformed macros
        assert "diesel::table! {" in result
        assert "diesel::joinable!" in result
        assert "diesel::allow_tables_to_appear_in_same_query!" in result

        # Ensure all braces are balanced
        assert result.count("{") == result.count("}")
        assert result.count("(") == result.count(")")
        assert result.count("[") == result.count("]")

        # Ensure all statements end with semicolons where expected
        lines = result.split("\n")
        for line in lines:
            line = line.strip()
            if (
                line.startswith("diesel::")
                and not line.endswith("{")
                and not line.endswith("(")
            ):
                assert line.endswith(";"), f"Line should end with semicolon: {line}"

    def test_foreign_key_relationships(self, generator, sample_entities):
        """Test foreign key relationships are correctly defined"""
        result = generator.generate_schema_file(sample_entities)

        # Contact references Company
        assert "tb_contact -> tb_company (fk_company)" in result

    def test_all_tables_in_allow_macro(self, generator, sample_entities):
        """Test all tables appear in allow macro"""
        result = generator.generate_schema_file(sample_entities)

        # Extract allow_tables_to_appear_in_same_query! section
        allow_section = result[result.index("allow_tables_to_appear_in_same_query!") :]

        for entity in sample_entities:
            table_name = f"tb_{entity.name.lower()}"
            assert table_name in allow_section
