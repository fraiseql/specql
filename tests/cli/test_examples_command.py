"""Test specql examples command."""

from src.cli.commands.examples import EXAMPLES


def test_examples_data_structure():
    """EXAMPLES should have correct structure."""
    assert isinstance(EXAMPLES, dict)
    assert len(EXAMPLES) > 0

    for name, data in EXAMPLES.items():
        assert "description" in data
        assert "yaml" in data
        assert isinstance(data["description"], str)
        assert isinstance(data["yaml"], str)


def test_examples_contain_required_examples():
    """Should contain the main examples mentioned in help."""
    required_examples = ["simple-entity", "with-relationships", "with-actions"]
    for example in required_examples:
        assert example in EXAMPLES


def test_all_examples_are_valid_yaml():
    """All built-in examples should be valid YAML."""
    import yaml

    for name, data in EXAMPLES.items():
        # Should parse as valid YAML
        parsed = yaml.safe_load(data["yaml"])
        assert parsed is not None
        assert "entity" in parsed
        assert "schema" in parsed
        assert "fields" in parsed


def test_example_yaml_has_proper_structure():
    """Example YAML should have proper SpecQL structure."""
    import yaml

    for name, data in EXAMPLES.items():
        parsed = yaml.safe_load(data["yaml"])

        # Should have entity name
        assert "entity" in parsed
        assert isinstance(parsed["entity"], str)

        # Should have schema
        assert "schema" in parsed
        assert isinstance(parsed["schema"], str)

        # Should have fields
        assert "fields" in parsed
        assert isinstance(parsed["fields"], dict)
        assert len(parsed["fields"]) > 0
