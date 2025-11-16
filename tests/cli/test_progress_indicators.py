"""Test progress indicators during generation."""

from click.testing import CliRunner
from src.cli.confiture_extensions import specql
import tempfile
from pathlib import Path


def test_progress_shown_for_multiple_entities():
    """Progress should be shown when generating multiple entities."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple entities
        for i, name in enumerate(["User", "Post", "Comment"], 1):
            entity_file = Path(tmpdir) / f"{name.lower()}.yaml"
            entity_file.write_text(f"""entity: {name}
schema: blog
fields:
  name: text
  created_at: timestamp
""")

        result = runner.invoke(
            specql,
            ["generate", f"{tmpdir}/*.yaml", "--output-dir", f"{tmpdir}/output"],
            input="y\n",
        )

        # Progress indicators (text-based is fine for CLI)
        # Look for entity names in output
        assert "User" in result.output or "user" in result.output.lower()
        assert "Post" in result.output or "post" in result.output.lower()
