"""Tests for language-specific reverse engineering commands."""

from src.cli.confiture_extensions import specql


class TestLanguageReverseCommands:
    """Test language-specific reverse engineering commands."""

    def test_reverse_unified_command_exists(self, cli_runner):
        """Test unified reverse engineering command exists"""
        result = cli_runner.invoke(specql, ["reverse", "--help"])
        assert result.exit_code == 0
        # Should show unified command with language support
        assert "Rust:" in result.output
        assert "TypeScript:" in result.output
        assert "Python:" in result.output
        assert "Java:" in result.output

    def test_reverse_rust_supported(self, cli_runner):
        """Test Rust is supported in unified reverse command"""
        result = cli_runner.invoke(specql, ["reverse", "--help"])
        assert result.exit_code == 0
        assert "Rust: Diesel, SeaORM" in result.output

    def test_reverse_typescript_supported(self, cli_runner):
        """Test TypeScript is supported in unified reverse command"""
        result = cli_runner.invoke(specql, ["reverse", "--help"])
        assert result.exit_code == 0
        assert "TypeScript: Prisma, TypeORM" in result.output

    def test_reverse_java_supported(self, cli_runner):
        """Test Java is supported in unified reverse command"""
        result = cli_runner.invoke(specql, ["reverse", "--help"])
        assert result.exit_code == 0
        assert "Java: JPA, Hibernate" in result.output
