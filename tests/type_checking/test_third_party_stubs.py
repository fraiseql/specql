# tests/type_checking/test_third_party_stubs.py
import subprocess


def test_pglast_has_type_stubs():
    """Verify pglast type stubs are available"""
    result = subprocess.run(
        ["uv", "run", "mypy", "-c", 'import pglast; pglast.parse_sql("SELECT 1")'],
        capture_output=True,
        text=True,
    )
    # Should not have "Skipping analyzing" error - this test should FAIL initially
    full_output = result.stdout + result.stderr
    print(f"Full mypy output: {full_output}")
    assert "Skipping analyzing" not in full_output, f"MyPy output: {full_output}"
    assert "import-untyped" not in full_output, f"MyPy output: {full_output}"
