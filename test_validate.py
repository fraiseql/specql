#!/usr/bin/env python3
"""Test script for the validate command"""

import sys
import os

sys.path.insert(0, "src")

from cli.validate import main

if __name__ == "__main__":
    # Simulate command line args
    sys.argv = ["validate", "examples/crm/entities/contact.yaml", "--verbose"]
    try:
        main()
        print("Validation completed successfully")
    except SystemExit as e:
        print(f"Validation exited with code: {e.code}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
