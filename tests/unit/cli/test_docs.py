"""Tests for CLI docs command."""


class TestDocsCommand:
    """Test the docs CLI command."""

    def test_docs_command_help(self, cli_runner):
        """Test docs command help text."""
        from src.cli.docs import docs

        result = cli_runner.invoke(docs, ["--help"])
        assert result.exit_code == 0
        assert "Generate documentation from SpecQL entity files" in result.output
        assert "--format" in result.output
        assert "--output" in result.output

    def test_docs_markdown_format(self, cli_runner, sample_entity_file, temp_dir):
        """Test docs command with markdown format."""
        from src.cli.docs import docs

        output_file = temp_dir / "docs.md"

        result = cli_runner.invoke(
            docs, [str(sample_entity_file), "--format", "markdown", "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert "Generated markdown documentation" in result.output
        assert output_file.exists()

        # Check content
        content = output_file.read_text()
        assert "# SpecQL Entity Documentation" in content
        assert "## Contact" in content
        assert "**Schema:** crm" in content

    def test_docs_html_format(self, cli_runner, sample_entity_file, temp_dir):
        """Test docs command with HTML format."""
        from src.cli.docs import docs

        output_dir = temp_dir / "html_docs"

        result = cli_runner.invoke(
            docs, [str(sample_entity_file), "--format", "html", "--output", str(output_dir)]
        )

        assert result.exit_code == 0
        assert "Generated HTML documentation" in result.output
        assert (output_dir / "index.html").exists()

        # Check content
        content = (output_dir / "index.html").read_text()
        assert "<!DOCTYPE html>" in content
        assert "<title>SpecQL Entity Documentation</title>" in content
        assert "<h2>Contact</h2>" in content

    def test_docs_multiple_entities(self, cli_runner, multiple_entity_files, temp_dir):
        """Test docs command with multiple entity files."""
        from src.cli.docs import docs

        output_file = temp_dir / "multi_docs.md"

        result = cli_runner.invoke(
            docs,
            [
                *[str(f) for f in multiple_entity_files],
                "--format",
                "markdown",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert "Documented 2 entities" in result.output

        content = output_file.read_text()
        assert "## Contact" in content
        assert "## Task" in content

    def test_docs_no_files_specified(self, cli_runner):
        """Test docs command with no files specified."""
        from src.cli.docs import docs

        result = cli_runner.invoke(docs, ["--format", "markdown", "--output", "test.md"])

        assert result.exit_code == 0
        assert "No entity files specified" in result.output

    def test_docs_missing_output_option(self, cli_runner, sample_entity_file):
        """Test docs command with missing output option."""
        from src.cli.docs import docs

        result = cli_runner.invoke(docs, [str(sample_entity_file), "--format", "markdown"])

        assert result.exit_code == 2  # Click error for missing required option

    def test_docs_invalid_entity_file(self, cli_runner, temp_dir):
        """Test docs command with invalid entity file."""
        from src.cli.docs import docs

        invalid_file = temp_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")

        output_file = temp_dir / "invalid.md"

        result = cli_runner.invoke(
            docs, [str(invalid_file), "--format", "markdown", "--output", str(output_file)]
        )

        assert result.exit_code == 1
        assert "Error generating documentation" in result.output

    def test_docs_nonexistent_file(self, cli_runner, temp_dir):
        """Test docs command with nonexistent file."""
        from src.cli.docs import docs

        output_file = temp_dir / "nonexistent.md"

        result = cli_runner.invoke(
            docs, ["nonexistent.yaml", "--format", "markdown", "--output", str(output_file)]
        )

        assert result.exit_code == 2  # Click error for missing file

    def test_docs_output_directory_creation(self, cli_runner, sample_entity_file, temp_dir):
        """Test docs command creates output directory for HTML."""
        from src.cli.docs import docs

        output_dir = temp_dir / "deep" / "nested" / "docs"

        result = cli_runner.invoke(
            docs, [str(sample_entity_file), "--format", "html", "--output", str(output_dir)]
        )

        assert result.exit_code == 0
        assert output_dir.exists()
        assert (output_dir / "index.html").exists()

    def test_docs_markdown_content_structure(self, cli_runner, sample_entity_file, temp_dir):
        """Test markdown documentation content structure."""
        from src.cli.docs import docs

        output_file = temp_dir / "structured.md"

        result = cli_runner.invoke(
            docs, [str(sample_entity_file), "--format", "markdown", "--output", str(output_file)]
        )

        assert result.exit_code == 0

        content = output_file.read_text()
        # Check basic structure
        assert "# SpecQL Entity Documentation" in content
        assert "## Contact" in content
        assert "### Fields" in content
        assert "| Field | Type | Required | Description |" in content
        assert "email" in content
        assert "first_name" in content

    def test_docs_html_content_structure(self, cli_runner, sample_entity_file, temp_dir):
        """Test HTML documentation content structure."""
        from src.cli.docs import docs

        output_dir = temp_dir / "html_structured"

        result = cli_runner.invoke(
            docs, [str(sample_entity_file), "--format", "html", "--output", str(output_dir)]
        )

        assert result.exit_code == 0

        content = (output_dir / "index.html").read_text()
        # Check basic structure
        assert "<!DOCTYPE html>" in content
        assert "<h1>SpecQL Entity Documentation</h1>" in content
        assert "<h2>Contact</h2>" in content
        assert "<table>" in content
        assert "<th>Field</th>" in content
