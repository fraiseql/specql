"""
Unit tests for interactive preview generator
"""

from src.cli.interactive.preview_generator import PreviewGenerator


class TestPreviewGenerator:

    def test_generate_schema_preview(self):
        """Test schema preview generation"""
        yaml_text = """entity: Contact
schema: crm
fields:
  email: text
  status: text
"""

        generator = PreviewGenerator()
        result = generator.generate_preview(yaml_text, mode="schema")

        assert result.success is True
        assert "CREATE TABLE" in result.output
        assert "crm.tb_contact" in result.output
        assert "email TEXT" in result.output

    def test_pattern_detection(self):
        """Test pattern detection in preview"""
        yaml_text = """entity: Task
schema: app
fields:
  title: text
  status: text
  organization_id: text
"""

        generator = PreviewGenerator()
        result = generator.generate_preview(yaml_text)

        assert result.success is True
        assert len(result.detected_patterns) >= 1

        pattern_names = {p['name'] for p in result.detected_patterns}
        assert 'state_machine' in pattern_names

    def test_error_recovery(self):
        """Test parsing partial/invalid YAML"""
        yaml_text = """
entity: Contact
schema: crm
fields:
  email: text
  # Incomplete field
  status:
"""

        generator = PreviewGenerator()
        result = generator.generate_preview(yaml_text)

        # Should handle gracefully
        assert result is not None

    def test_actions_preview(self):
        """Test actions preview mode"""
        yaml_text = """entity: Contact
schema: crm
fields:
  status: text
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
"""

        generator = PreviewGenerator()
        result = generator.generate_preview(yaml_text, mode="actions")

        assert result.success is True
        assert "CREATE FUNCTION" in result.output or "qualify_lead" in result.output

    def test_invalid_yaml_error(self):
        """Test error handling for completely invalid YAML"""
        yaml_text = "invalid: yaml: content: [unclosed"

        generator = PreviewGenerator()
        result = generator.generate_preview(yaml_text)

        assert result.success is False
        assert result.error is not None
        assert "Invalid YAML" in result.error