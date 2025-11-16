"""Performance tests for test generation."""

import time
from pathlib import Path
import tempfile
import subprocess


class TestTestGenerationPerformance:
    """Test performance of test generation."""

    def test_generate_tests_performance_single_entity(self):
        """Test generation should complete in reasonable time."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            entity_file = tmp_path / "entity.yaml"
            entity_file.write_text("""
entity: PerfTest
schema: test
fields:
  field1: text
  field2: text
  field3: text
  field4: text
  field5: text
actions:
  - name: action1
    steps: []
  - name: action2
    steps: []
            """)

            start = time.time()

            subprocess.run(
                [
                    "python",
                    "-m",
                    "src.cli.confiture_extensions",
                    "generate-tests",
                    str(entity_file),
                    "-o",
                    str(tmp_path / "tests"),
                ],
                input="y\n",
                capture_output=True,
                text=True,
            )

            duration = time.time() - start

            # Should complete in < 5 seconds
            assert duration < 5.0, f"Generation took {duration:.2f}s, expected < 5s"

    def test_generate_tests_performance_10_entities(self):
        """Test batch generation performance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            entity_dir = tmp_path / "entities"
            entity_dir.mkdir()

            # Create 10 entities
            for i in range(10):
                entity_file = entity_dir / f"entity{i}.yaml"
                entity_file.write_text(f"""
entity: Entity{i}
schema: test
fields:
  field1: text
  field2: text
                """)

            start = time.time()

            subprocess.run(
                ["python", "-m", "src.cli.confiture_extensions", "generate-tests"]
                + list(entity_dir.glob("*.yaml"))
                + ["-o", str(tmp_path / "tests")],
                input="y\n",
                capture_output=True,
                text=True,
            )

            duration = time.time() - start

            # Should complete in < 15 seconds for 10 entities
            assert duration < 15.0, (
                f"Batch generation took {duration:.2f}s, expected < 15s"
            )
