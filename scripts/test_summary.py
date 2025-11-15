"""
Generate test summary for documentation.
Usage: python scripts/test_summary.py
"""

import subprocess
from datetime import datetime


def run_pytest_collect():
    """Collect test information"""
    result = subprocess.run(["pytest", "--collect-only", "--quiet"], capture_output=True, text=True)
    return result.stdout


def parse_test_counts(output: str) -> dict:
    """Parse pytest output for counts"""
    lines = output.strip().split("\n")
    last_line = lines[-1]

    # Parse: "1164 tests collected, 3 errors"
    import re

    match = re.search(r"(\d+) tests? collected", last_line)
    total = int(match.group(1)) if match else 0

    match = re.search(r"(\d+) errors?", last_line)
    errors = int(match.group(1)) if match else 0

    return {
        "total_tests": total,
        "collection_errors": errors,
        "status": "healthy" if errors == 0 else "needs_attention",
    }


def generate_summary():
    """Generate human-readable summary"""
    output = run_pytest_collect()
    counts = parse_test_counts(output)

    summary = f"""
# Test Suite Summary

**Generated**: {datetime.now().isoformat()}

## Overview
- **Total Tests**: {counts["total_tests"]}
- **Collection Errors**: {counts["collection_errors"]}
- **Status**: {counts["status"]}

## Run Tests
```bash
# All tests
make test

# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v
```

## Coverage
Run `make coverage` to generate detailed coverage report.
    """

    return summary


if __name__ == "__main__":
    print(generate_summary())
