"""Tests for CLI diff command."""


from src.cli.diff import diff, generate_entity_sql, load_migration_sql


class TestDiffUtilities:
    """Test diff utility functions."""

    def test_generate_entity_sql(self, sample_entity_file):
        """Test generating SQL from entity file."""
        sql = generate_entity_sql(str(sample_entity_file))

        assert isinstance(sql, str)
        assert len(sql) > 0
        assert "CREATE TABLE" in sql.upper()

    def test_load_migration_sql(self, temp_dir):
        """Test loading SQL from migration file."""
        migration_content = "CREATE TABLE test (id INTEGER);"
        migration_file = temp_dir / "test.sql"
        migration_file.write_text(migration_content)

        sql = load_migration_sql(str(migration_file))

        assert sql == migration_content


class TestDiffCommand:
    """Test the diff CLI command."""

    def test_diff_command_help(self, cli_runner):
        """Test diff command help text."""

        result = cli_runner.invoke(diff, ["--help"])
        assert result.exit_code == 0
        assert "Show differences between entity definition and existing migration" in result.output
        assert "--compare" in result.output
        assert "--color" in result.output

    def test_diff_without_compare(self, cli_runner, sample_entity_file):
        """Test diff command without --compare option."""

        result = cli_runner.invoke(diff, [str(sample_entity_file)])

        assert result.exit_code == 0
        assert "Generated SQL for" in result.output
        assert "CREATE TABLE" in result.output.upper()
        assert "Size:" in result.output

    def test_diff_with_compare_no_differences(self, cli_runner, sample_entity_file, temp_dir):
        """Test diff with compare when files are identical."""

        # Generate SQL and save as "migration"
        entity_sql = generate_entity_sql(str(sample_entity_file))
        migration_file = temp_dir / "migration.sql"
        migration_file.write_text(entity_sql)

        result = cli_runner.invoke(
            diff, [str(sample_entity_file), "--compare", str(migration_file)]
        )

        assert result.exit_code == 0
        assert "No differences" in result.output

    def test_diff_with_compare_has_differences(self, cli_runner, sample_entity_file, temp_dir):
        """Test diff with compare when files differ."""

        # Create different migration SQL
        migration_sql = "CREATE TABLE contact (id INTEGER PRIMARY KEY, name TEXT);"
        migration_file = temp_dir / "migration.sql"
        migration_file.write_text(migration_sql)

        result = cli_runner.invoke(
            diff, [str(sample_entity_file), "--compare", str(migration_file)]
        )

        assert result.exit_code == 0
        assert "Differences between" in result.output
        # Should show diff markers
        assert any(marker in result.output for marker in ["+", "-", "@@"])

    def test_diff_with_color_option(self, cli_runner, sample_entity_file, temp_dir):
        """Test diff with color option."""

        # Create different migration SQL
        migration_sql = "CREATE TABLE contact (id INTEGER);"
        migration_file = temp_dir / "migration.sql"
        migration_file.write_text(migration_sql)

        result = cli_runner.invoke(
            diff, [str(sample_entity_file), "--compare", str(migration_file), "--color"]
        )

        assert result.exit_code == 0
        # Should show differences
        assert "Differences between" in result.output

    def test_diff_with_no_color_option(self, cli_runner, sample_entity_file, temp_dir):
        """Test diff with no-color option."""

        # Create different migration SQL
        migration_sql = "CREATE TABLE contact (id INTEGER);"
        migration_file = temp_dir / "migration.sql"
        migration_file.write_text(migration_sql)

        result = cli_runner.invoke(
            diff, [str(sample_entity_file), "--compare", str(migration_file), "--no-color"]
        )

        assert result.exit_code == 0
        # No ANSI color codes
        assert "\033[" not in result.output

    def test_diff_with_context_option(self, cli_runner, sample_entity_file, temp_dir):
        """Test diff with custom context lines."""

        # Create different migration SQL
        migration_sql = "CREATE TABLE contact (id INTEGER);"
        migration_file = temp_dir / "migration.sql"
        migration_file.write_text(migration_sql)

        result = cli_runner.invoke(
            diff, [str(sample_entity_file), "--compare", str(migration_file), "--context", "1"]
        )

        assert result.exit_code == 0
        # Should work with custom context
        assert "Differences between" in result.output

    def test_diff_invalid_entity_file(self, cli_runner, temp_dir):
        """Test diff with invalid entity file."""

        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")

        result = cli_runner.invoke(diff, [str(invalid_file)])

        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_diff_nonexistent_compare_file(self, cli_runner, sample_entity_file):
        """Test diff with nonexistent compare file."""

        result = cli_runner.invoke(diff, [str(sample_entity_file), "--compare", "nonexistent.sql"])

        assert result.exit_code == 2  # Click error for missing file

    def test_diff_nonexistent_entity_file(self, cli_runner):
        """Test diff with nonexistent entity file."""

        result = cli_runner.invoke(diff, ["nonexistent.yaml"])

        assert result.exit_code == 2  # Click error for missing file
