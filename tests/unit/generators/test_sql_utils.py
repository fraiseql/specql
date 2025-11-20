"""
Tests for SQL Utils
"""

from generators.sql_utils import SQLUtils


class TestSQLUtils:
    """Test SQL utility functions"""

    def test_quote_identifier_simple(self):
        """Test quoting simple identifiers"""
        assert SQLUtils.quote_identifier("user_name") == "user_name"
        assert SQLUtils.quote_identifier("id") == "id"
        assert SQLUtils.quote_identifier("created_at") == "created_at"

    def test_quote_identifier_complex(self):
        """Test quoting complex identifiers"""
        assert SQLUtils.quote_identifier("User Name") == '"User Name"'
        assert SQLUtils.quote_identifier("user-name") == '"user-name"'
        assert SQLUtils.quote_identifier("123start") == '"123start"'

    def test_format_create_table_statement(self):
        """Test CREATE TABLE formatting"""
        columns = ["id INTEGER PRIMARY KEY", "name TEXT NOT NULL", "email TEXT"]

        sql = SQLUtils.format_create_table_statement("public", "users", columns)

        expected = """CREATE TABLE public.users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT
);"""

        assert sql == expected

    def test_format_create_table_with_constraints(self):
        """Test CREATE TABLE with constraints"""
        columns = ["id INTEGER", "email TEXT"]
        constraints = ["PRIMARY KEY (id)", "UNIQUE (email)"]

        sql = SQLUtils.format_create_table_statement("crm", "contacts", columns, constraints)

        expected = """CREATE TABLE crm.contacts (
    id INTEGER,
    email TEXT,
    PRIMARY KEY (id),
    UNIQUE (email)
);"""

        assert sql == expected

    def test_format_comment_on_table(self):
        """Test table comment formatting"""
        sql = SQLUtils.format_comment_on_table("crm", "contacts", "Customer contact information")

        expected = "COMMENT ON TABLE crm.contacts IS 'Customer contact information';"
        assert sql == expected

    def test_format_comment_on_table_with_quotes(self):
        """Test table comment with quotes"""
        sql = SQLUtils.format_comment_on_table("crm", "contacts", "Table for 'customer' data")

        expected = "COMMENT ON TABLE crm.contacts IS 'Table for ''customer'' data';"
        assert sql == expected

    def test_format_comment_on_column(self):
        """Test column comment formatting"""
        sql = SQLUtils.format_comment_on_column("crm", "contacts", "email", "Contact email address")

        expected = "COMMENT ON COLUMN crm.contacts.email IS 'Contact email address';"
        assert sql == expected

    def test_format_alter_table_add_constraint(self):
        """Test ALTER TABLE ADD CONSTRAINT formatting"""
        sql = SQLUtils.format_alter_table_add_constraint(
            "crm", "contacts", "contacts_email_key", "UNIQUE (email)"
        )

        expected = """ALTER TABLE ONLY crm.contacts
    ADD CONSTRAINT contacts_email_key UNIQUE (email);"""

        assert sql == expected

    def test_format_create_index(self):
        """Test CREATE INDEX formatting"""
        sql = SQLUtils.format_create_index("idx_contacts_email", "crm", "contacts", ["email"])

        expected = """CREATE INDEX idx_contacts_email
    ON crm.contacts USING btree (email);"""

        assert sql == expected

    def test_format_create_unique_index(self):
        """Test CREATE UNIQUE INDEX formatting"""
        sql = SQLUtils.format_create_index(
            "idx_contacts_email_unique", "crm", "contacts", ["email"], unique=True
        )

        expected = """CREATE UNIQUE INDEX idx_contacts_email_unique
    ON crm.contacts USING btree (email);"""

        assert sql == expected

    def test_format_create_function(self):
        """Test CREATE FUNCTION formatting"""
        parameters = ["p_id INTEGER", "p_name TEXT"]
        body = "SELECT * FROM users WHERE id = p_id AND name = p_name;"

        sql = SQLUtils.format_create_function(
            "core", "find_user", parameters, "TABLE(id INTEGER, name TEXT)", body
        )

        expected = """CREATE OR REPLACE FUNCTION core.find_user(p_id INTEGER, p_name TEXT)
RETURNS TABLE(id INTEGER, name TEXT)
LANGUAGE sql
AS $$
SELECT * FROM users WHERE id = p_id AND name = p_name;
$$;"""

        assert sql == expected

    def test_escape_string_literal(self):
        """Test string literal escaping"""
        assert SQLUtils.escape_string_literal("hello") == "hello"
        assert SQLUtils.escape_string_literal("it's") == "it''s"
        assert SQLUtils.escape_string_literal("O'Connor") == "O''Connor"
        assert SQLUtils.escape_string_literal("test's 'quoted'") == "test''s ''quoted''"

    def test_format_string_list(self):
        """Test string list formatting"""
        items = ["apple", "banana", "cherry"]

        assert SQLUtils.format_string_list(items) == "apple, banana, cherry"
        assert SQLUtils.format_string_list(items, "'", "'") == "'apple', 'banana', 'cherry'"
        assert (
            SQLUtils.format_string_list(items, "prefix_", "_suffix")
            == "prefix_apple_suffix, prefix_banana_suffix, prefix_cherry_suffix"
        )
