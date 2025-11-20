"""
SQL Utilities for Team B Generators
SQL formatting, quoting, and utility functions
"""

import re


class SQLUtils:
    """Utility functions for SQL generation and formatting"""

    @staticmethod
    def quote_identifier(identifier: str) -> str:
        """
        Quote SQL identifier if needed

        Args:
            identifier: SQL identifier (table name, column name, etc.)

        Returns:
            Quoted identifier if necessary
        """
        # Check if identifier needs quoting (contains special chars, reserved words, etc.)
        if re.match(r"^[a-z_][a-z0-9_]*$", identifier.lower()):
            # Simple identifier, no quoting needed
            return identifier
        else:
            # Complex identifier, quote it
            return f'"{identifier}"'

    @staticmethod
    def format_create_table_statement(
        schema: str, table_name: str, columns: list[str], constraints: list[str] | None = None
    ) -> str:
        """
        Format a CREATE TABLE statement

        Args:
            schema: Schema name
            table_name: Table name
            columns: List of column definitions
            constraints: Optional list of table constraints

        Returns:
            Formatted CREATE TABLE statement
        """
        qualified_table = f"{schema}.{table_name}"

        # Format column definitions
        column_defs = ",\n    ".join(columns)

        # Build basic statement
        sql = f"CREATE TABLE {qualified_table} (\n    {column_defs}"

        # Add constraints if provided
        if constraints:
            constraint_defs = ",\n    ".join(constraints)
            sql += f",\n    {constraint_defs}"

        sql += "\n);"

        return sql

    @staticmethod
    def format_comment_on_table(schema: str, table_name: str, comment: str) -> str:
        """
        Format COMMENT ON TABLE statement

        Args:
            schema: Schema name
            table_name: Table name
            comment: Comment text

        Returns:
            Formatted COMMENT statement
        """
        qualified_table = f"{schema}.{table_name}"
        # Escape single quotes in comment
        escaped_comment = comment.replace("'", "''")
        return f"COMMENT ON TABLE {qualified_table} IS '{escaped_comment}';"

    @staticmethod
    def format_comment_on_column(
        schema: str, table_name: str, column_name: str, comment: str
    ) -> str:
        """
        Format COMMENT ON COLUMN statement

        Args:
            schema: Schema name
            table_name: Table name
            column_name: Column name
            comment: Comment text

        Returns:
            Formatted COMMENT statement
        """
        qualified_table = f"{schema}.{table_name}"
        # Escape single quotes in comment
        escaped_comment = comment.replace("'", "''")
        return f"COMMENT ON COLUMN {qualified_table}.{column_name} IS '{escaped_comment}';"

    @staticmethod
    def format_alter_table_add_constraint(
        schema: str, table_name: str, constraint_name: str, constraint_definition: str
    ) -> str:
        """
        Format ALTER TABLE ADD CONSTRAINT statement

        Args:
            schema: Schema name
            table_name: Table name
            constraint_name: Constraint name
            constraint_definition: Constraint SQL

        Returns:
            Formatted ALTER TABLE statement
        """
        qualified_table = f"{schema}.{table_name}"
        return f"ALTER TABLE ONLY {qualified_table}\n    ADD CONSTRAINT {constraint_name} {constraint_definition};"

    @staticmethod
    def format_create_index(
        index_name: str,
        schema: str,
        table_name: str,
        columns: list[str],
        type: str = "btree",
        unique: bool = False,
    ) -> str:
        """
        Format CREATE INDEX statement

        Args:
            index_name: Index name
            schema: Schema name
            table_name: Table name
            columns: List of column names
            type: Index type (btree, hash, etc.)
            unique: Whether it's a unique index

        Returns:
            Formatted CREATE INDEX statement
        """
        qualified_table = f"{schema}.{table_name}"
        unique_clause = "UNIQUE " if unique else ""
        column_list = ", ".join(columns)

        return f"CREATE {unique_clause}INDEX {index_name}\n    ON {qualified_table} USING {type} ({column_list});"

    @staticmethod
    def format_create_function(
        schema: str,
        function_name: str,
        parameters: list[str],
        return_type: str,
        body: str,
        language: str = "sql",
    ) -> str:
        """
        Format CREATE FUNCTION statement

        Args:
            schema: Schema name
            function_name: Function name
            parameters: List of parameter definitions
            return_type: Return type
            body: Function body
            language: Language (sql, plpgsql, etc.)

        Returns:
            Formatted CREATE FUNCTION statement
        """
        qualified_function = f"{schema}.{function_name}"
        param_list = ", ".join(parameters) if parameters else ""

        return f"""CREATE OR REPLACE FUNCTION {qualified_function}({param_list})
RETURNS {return_type}
LANGUAGE {language}
AS $$
{body}
$$;"""

    @staticmethod
    def indent_sql(sql: str, indent: str = "    ") -> str:
        """
        Indent SQL statements for better readability

        Args:
            sql: SQL string
            indent: Indentation string

        Returns:
            Indented SQL
        """
        lines = sql.split("\n")
        indented_lines = []

        for line in lines:
            if line.strip():  # Non-empty line
                indented_lines.append(indent + line)
            else:  # Empty line
                indented_lines.append("")

        return "\n".join(indented_lines)

    @staticmethod
    def format_multiline_comment(title: str, content: str = "", width: int = 80) -> str:
        """
        Format a multi-line SQL comment block

        Args:
            title: Comment title
            content: Comment content
            width: Comment width

        Returns:
            Formatted comment block
        """
        border = "=" * width
        title_line = f"-- {title}"

        if content:
            content_lines = [f"-- {line}" for line in content.split("\n") if line.strip()]
            return f"-- {border}\n{title_line}\n{content_lines}\n-- {border}"
        else:
            return f"-- {border}\n{title_line}\n-- {border}"

    @staticmethod
    def escape_string_literal(value: str) -> str:
        """
        Escape string for SQL literal

        Args:
            value: String value

        Returns:
            Escaped string
        """
        # Escape single quotes by doubling them
        return value.replace("'", "''")

    @staticmethod
    def format_string_list(items: list[str], prefix: str = "", suffix: str = "") -> str:
        """
        Format a list of strings with optional prefix/suffix

        Args:
            items: List of strings
            prefix: Prefix for each item
            suffix: Suffix for each item

        Returns:
            Comma-separated formatted list
        """
        formatted_items = [f"{prefix}{item}{suffix}" for item in items]
        return ", ".join(formatted_items)
