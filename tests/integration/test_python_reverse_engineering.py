import pytest
from pathlib import Path
import yaml
from click.testing import CliRunner

from src.cli.confiture_extensions import specql

class TestPythonReverseEngineering:

    def test_reverse_python_dataclass(self, tmp_path):
        """Test reversing Python dataclass"""
        # Create test Python file
        python_file = tmp_path / "contact.py"
        python_file.write_text('''
from dataclasses import dataclass

@dataclass
class Contact:
    """CRM contact"""
    email: str
    first_name: str
    last_name: str
    company: str
    status: str = "lead"

    def qualify_lead(self):
        if self.status != "lead":
            return False
        self.status = "qualified"
        return True
''')

        output_dir = tmp_path / "entities"

        # Run CLI command
        runner = CliRunner()
        result = runner.invoke(specql, [
            'reverse-python',
            str(python_file),
            '--output-dir', str(output_dir)
        ])

        assert result.exit_code == 0
        assert "✅ Written" in result.output

        # Check output file
        yaml_file = output_dir / "contact.yaml"
        assert yaml_file.exists()

        # Validate YAML content
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        assert data['entity'] == 'Contact'
        assert data['description'] == 'CRM contact'
        assert len(data['fields']) == 5
        assert len(data['actions']) == 1

        # Check fields
        email_field = next(f for f in data['fields'] if f['name'] == 'email')
        assert email_field['type'] == 'text'
        assert email_field['required'] is True

        # Check action
        action = data['actions'][0]
        assert action['name'] == 'qualify_lead'
        assert len(action['steps']) > 0

    def test_reverse_django_model(self, tmp_path):
        """Test reversing Django model"""
        python_file = tmp_path / "article.py"
        python_file.write_text('''
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_at = models.DateTimeField(null=True)
    author = models.ForeignKey('User', on_delete=models.CASCADE)
''')

        output_dir = tmp_path / "entities"

        runner = CliRunner()
        result = runner.invoke(specql, [
            'reverse-python',
            str(python_file),
            '--output-dir', str(output_dir),
            '--discover-patterns'
        ])

        assert result.exit_code == 0

        # Check Django model was detected
        yaml_file = output_dir / "article.yaml"
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        assert 'django_model' in data['_metadata']['patterns']

        # Check foreign key was detected
        author_field = next(f for f in data['fields'] if f['name'] == 'author')
        assert author_field['type'] == 'ref'
        assert author_field['ref'] == 'User'

    def test_dry_run_mode(self, tmp_path):
        """Test dry run doesn't write files"""
        python_file = tmp_path / "test.py"
        python_file.write_text('''
class Test:
    name: str
''')

        output_dir = tmp_path / "entities"

        runner = CliRunner()
        result = runner.invoke(specql, [
            'reverse-python',
            str(python_file),
            '--output-dir', str(output_dir),
            '--dry-run'
        ])

        assert result.exit_code == 0
        assert "Would write" in result.output
        assert not (output_dir / "test.yaml").exists()

    def test_universal_mapper_integration(self, tmp_path):
        """Test that universal mapper works with both Python and SQL"""
        from src.reverse_engineering.python_ast_parser import PythonASTParser
        from src.reverse_engineering.universal_ast_mapper import UniversalASTMapper

        # Test Python parsing
        python_code = '''
from dataclasses import dataclass

@dataclass
class Contact:
    email: str
    status: str = "lead"
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(python_code)

        mapper = UniversalASTMapper()
        specql_dict = mapper.map_entity_to_specql(entity)

        assert specql_dict['entity'] == 'Contact'
        assert specql_dict['_metadata']['source_language'] == 'python'
        assert len(specql_dict['fields']) == 2
        assert len(specql_dict['actions']) == 0  # No methods in this example