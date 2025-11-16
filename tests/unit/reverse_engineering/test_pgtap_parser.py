from src.reverse_engineering.tests.pgtap_test_parser import (
    PgTAPTestParser,
    PgTAPTestSpecMapper,
)


class TestPgTAPTestParser:
    def test_parse_simple_pgtap_test(self):
        """Test parsing simple pgTAP test"""
        pgtap_code = """
        BEGIN;
        SELECT plan(2);

        -- Test: Create contact successfully
        SELECT ok(
            (SELECT app.create_contact('test@example.com')).status = 'success',
            'Should create contact'
        );

        -- Test: Throw error for duplicate
        SELECT throws_ok(
            $$SELECT app.create_contact('test@example.com')$$ ,
            'Duplicate email'
        );

        SELECT * FROM finish();
        ROLLBACK;
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        assert parsed.source_language.value == "pgtap"
        assert parsed.metadata["test_count"] == 2
        assert len(parsed.test_functions) >= 2

    def test_map_pgtap_to_test_spec(self):
        """Test mapping pgTAP to TestSpec"""
        pgtap_code = """
        SELECT ok((SELECT app.qualify_lead('uuid')).status = 'success');
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        mapper = PgTAPTestSpecMapper()
        test_spec = mapper.map_to_test_spec(parsed, "Contact")

        assert test_spec.entity_name == "Contact"
        assert len(test_spec.scenarios) > 0

    def test_extract_assertions_from_pgtap(self):
        """Test extracting different types of pgTAP assertions"""
        pgtap_code = """
        -- Test basic assertion
        SELECT ok((SELECT 1) = 1, 'Basic equality');

        -- Test exception assertion
        SELECT throws_ok(
            $$SELECT app.invalid_function()$$,
            'Function should throw error'
        );

        -- Test schema assertion
        SELECT has_table('crm.tb_contact', 'Contact table should exist');
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        # Should extract 3 test functions
        assert len(parsed.test_functions) == 3

        # Check assertion types
        assertion_types = [func.assertions[0]["type"] for func in parsed.test_functions]
        assert "ok" in assertion_types
        assert "throws_ok" in assertion_types
        assert "has_table" in assertion_types

    def test_detect_test_type_from_assertions(self):
        """Test detecting test type from pgTAP assertions"""
        # CRUD test
        crud_code = """
        SELECT ok((SELECT app.create_contact('test@example.com')).status = 'success');
        """
        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(crud_code)
        test_type = parser.detect_test_type(parsed)
        assert test_type == "integration"  # Default for basic assertions

        # Schema test
        schema_code = """
        SELECT has_table('crm.tb_contact');
        SELECT has_column('crm.tb_contact', 'email');
        """
        parsed = parser.parse_test_file(schema_code)
        test_type = parser.detect_test_type(parsed)
        assert test_type == "integration"  # Schema checks are integration tests

        # Exception test
        exception_code = """
        SELECT throws_ok($$SELECT app.qualify_lead('invalid')$$, 'Should throw');
        """
        parsed = parser.parse_test_file(exception_code)
        test_type = parser.detect_test_type(parsed)
        assert test_type == "validation"  # Exception tests are validation

    def test_extract_fixtures_from_transaction_wrapper(self):
        """Test extracting transaction fixtures"""
        pgtap_code = """
        BEGIN;
        SELECT plan(1);
        SELECT ok(true);
        SELECT * FROM finish();
        ROLLBACK;
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        assert len(parsed.fixtures) == 1
        fixture = parsed.fixtures[0]
        assert fixture["name"] == "transaction_rollback"
        assert fixture["type"] == "database"
        assert fixture["setup_sql"] == "BEGIN;"
        assert fixture["teardown_sql"] == "ROLLBACK;"

    def test_parse_complex_pgtap_with_comments(self):
        """Test parsing pgTAP with detailed comments and complex assertions"""
        pgtap_code = """
        BEGIN;
        SELECT plan(3);

        -- Test: Contact creation should succeed with valid data
        -- This tests the happy path for contact creation
        SELECT ok(
            (SELECT app.create_contact(
                'john.doe@example.com'::text,
                'John Doe'::text,
                'lead'::text
            )).status = 'success',
            'Contact creation should succeed'
        );

        -- Test: Duplicate email should throw validation error
        SELECT throws_ok(
            $$SELECT app.create_contact('john.doe@example.com', 'Jane Doe', 'lead')$$,
            'Duplicate email should cause error'
        );

        -- Test: Contact table should exist
        SELECT has_table('crm.tb_contact', 'Contact table must exist');

        SELECT * FROM finish();
        ROLLBACK;
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        assert len(parsed.test_functions) == 3

        # Check docstrings were extracted from comments
        docstrings = [func.docstring for func in parsed.test_functions]
        assert any("Contact creation should succeed" in str(ds) for ds in docstrings)
        assert any("Duplicate email should throw" in str(ds) for ds in docstrings)
        assert any("Contact table should exist" in str(ds) for ds in docstrings)

    def test_parse_pgtap_action_tests(self):
        """Test parsing pgTAP action tests."""
        pgtap_code = """
        BEGIN;
        SELECT plan(2);

        -- Action success test
        SELECT ok(
            (SELECT crm.qualify_lead('contact-id', 'user-id')).status = 'success',
            'Qualify lead should succeed'
        );

        -- Action with state change
        DO $$
        DECLARE
            v_result app.mutation_result;
        BEGIN
            v_result := crm.qualify_lead('contact-id', 'user-id');
            PERFORM ok(v_result.status = 'success', 'Action should succeed');
            PERFORM ok(
                (SELECT status FROM crm.tb_contact WHERE id = 'contact-id') = 'qualified',
                'Contact status should change to qualified'
            );
        END $$;

        SELECT * FROM finish();
        ROLLBACK;
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        assert len(parsed.test_functions) >= 1

    def test_parse_pgtap_with_setup_teardown(self):
        """Test parsing pgTAP with setup and teardown SQL."""
        pgtap_code = """
        -- Setup: Create test data
        INSERT INTO crm.tb_contact (id, email) VALUES ('test-id', 'test@example.com');

        BEGIN;
        SELECT plan(1);

        SELECT ok(
            (SELECT email FROM crm.tb_contact WHERE id = 'test-id') = 'test@example.com',
            'Setup data should exist'
        );

        SELECT * FROM finish();
        ROLLBACK;

        -- Teardown: Clean up
        DELETE FROM crm.tb_contact WHERE id = 'test-id';
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        assert len(parsed.test_functions) == 1
        # Should detect setup/teardown SQL
        assert len(parsed.fixtures) >= 1

    def test_parse_empty_pgtap_file(self):
        """Test parsing empty pgTAP file."""
        parser = PgTAPTestParser()
        parsed = parser.parse_test_file("")

        assert len(parsed.test_functions) == 0
        assert len(parsed.fixtures) == 0

    def test_parse_pgtap_with_malformed_sql(self):
        """Test parsing pgTAP with malformed SQL."""
        malformed_code = """
        BEGIN;
        SELECT plan(1);

        -- Missing closing parenthesis
        SELECT ok((SELECT 1 = 1, 'Test');

        SELECT * FROM finish();
        ROLLBACK;
        """

        parser = PgTAPTestParser()
        # Should not crash, but may not parse perfectly
        parsed = parser.parse_test_file(malformed_code)

        # At minimum should not crash
        assert parsed is not None

    def test_pgtap_test_spec_mapping_comprehensive(self):
        """Test comprehensive mapping from pgTAP to TestSpec."""
        pgtap_code = """
        BEGIN;
        SELECT plan(2);

        -- Happy path
        SELECT ok(
            (SELECT app.create_contact('test@example.com')).status = 'success',
            'Create contact happy path'
        );

        -- Error case
        SELECT throws_ok(
            $$SELECT app.create_contact('test@example.com')$$,
            'Duplicate contact error'
        );

        SELECT * FROM finish();
        ROLLBACK;
        """

        parser = PgTAPTestParser()
        parsed = parser.parse_test_file(pgtap_code)

        mapper = PgTAPTestSpecMapper()
        test_spec = mapper.map_to_test_spec(parsed, "Contact")

        assert test_spec.entity_name == "Contact"
        assert len(test_spec.scenarios) >= 1
