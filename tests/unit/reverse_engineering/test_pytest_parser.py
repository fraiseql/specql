import pytest
from src.reverse_engineering.tests.pytest_test_parser import (
    PytestParser,
    PytestTestSpecMapper
)


class TestPytestParser:

    def test_parse_simple_pytest_test(self):
        """Test parsing simple pytest test"""
        pytest_code = """
import pytest

class TestContact:
    def test_create_contact(self):
        '''Test: Create contact successfully'''
        result = create_contact("test@example.com")
        assert result.status == "success"

    def test_create_duplicate_error(self):
        '''Test: Raise error for duplicate email'''
        with pytest.raises(ValidationError):
            create_contact("existing@example.com")
        """

        parser = PytestParser()
        parsed = parser.parse_test_file(pytest_code)

        assert parsed.source_language.value == "pytest"
        assert len(parsed.test_functions) == 2
        assert parsed.test_functions[0].function_name == "test_create_contact"

    def test_extract_assertions(self):
        """Test extracting assertions from pytest"""
        pytest_code = """
def test_qualify_lead():
    result = qualify_lead(contact_id)
    assert result.status == "success"
    assert contact.status == "qualified"
        """

        parser = PytestParser()
        parsed = parser.parse_test_file(pytest_code)

        assert len(parsed.test_functions) == 1
        test_func = parsed.test_functions[0]
        assert len(test_func.assertions) == 2
        assert test_func.assertions[0]["type"] == "equals"

    def test_extract_fixtures(self):
        """Test extracting pytest fixtures"""
        pytest_code = """
import pytest

@pytest.fixture
def test_contact(test_db):
    return create_contact(email="test@example.com", status="lead")

@pytest.fixture(scope="module")
def test_db():
    # Setup database
    return setup_test_database()

class TestContact:
    def test_something(self, test_contact):
        assert test_contact.email == "test@example.com"
        """

        parser = PytestParser()
        parsed = parser.parse_test_file(pytest_code)

        assert len(parsed.fixtures) == 2

        # Check function fixture
        func_fixture = next(f for f in parsed.fixtures if f["name"] == "test_contact")
        assert func_fixture["scope"] == "function"
        assert func_fixture["parameters"] == ["test_db"]

        # Check module fixture
        module_fixture = next(f for f in parsed.fixtures if f["name"] == "test_db")
        assert module_fixture["scope"] == "module"

    def test_parse_pytest_raises(self):
        """Test parsing pytest.raises() context manager"""
        pytest_code = """
def test_duplicate_email_error():
    with pytest.raises(ValidationError, match="duplicate email"):
        create_contact("existing@example.com")
        """

        parser = PytestParser()
        parsed = parser.parse_test_file(pytest_code)

        assert len(parsed.test_functions) == 1
        test_func = parsed.test_functions[0]
        assert len(test_func.assertions) == 1

        assertion = test_func.assertions[0]
        assert assertion["type"] == "throws"
        assert assertion["expected"] == "ValidationError"
        assert "duplicate email" in assertion["message"]

    def test_detect_test_type_from_names(self):
        """Test detecting test type from function names"""
        # CRUD test
        crud_code = """
def test_create_contact():
    pass

def test_read_contact():
    pass
        """
        parser = PytestParser()
        parsed = parser.parse_test_file(crud_code)
        test_type = parser.detect_test_type(parsed)
        assert test_type == "crud_create"  # First match wins

        # Validation test
        validation_code = """
def test_validate_email():
    pass
        """
        parsed = parser.parse_test_file(validation_code)
        test_type = parser.detect_test_type(parsed)
        assert test_type == "validation"

    def test_map_pytest_to_test_spec(self):
        """Test mapping pytest to TestSpec"""
        pytest_code = """
def test_qualify_lead():
    result = qualify_lead(contact_id)
    assert result.status == "success"
        """

        parser = PytestParser()
        parsed = parser.parse_test_file(pytest_code)

        mapper = PytestTestSpecMapper()
        test_spec = mapper.map_to_test_spec(parsed, "Contact")

        assert test_spec.entity_name == "Contact"
        assert len(test_spec.scenarios) == 1
        assert test_spec.scenarios[0].scenario_name == "test_qualify_lead"