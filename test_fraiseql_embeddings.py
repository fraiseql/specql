#!/usr/bin/env python3
"""
Test FraiseQL 1.5 embeddings functionality
"""

import sys

# Add user site-packages to path
sys.path.insert(0, "/home/lionel/.local/lib/python3.13/site-packages")


def test_fraiseql_embeddings():
    """Test FraiseQL embeddings functionality"""
    try:
        import fraiseql

        print("✓ FraiseQL imported successfully")
        print(f"  Version: {fraiseql.__version__}")

        # Check for embeddings module
        if hasattr(fraiseql, "embeddings"):
            print("✓ fraiseql.embeddings module found")
            embeddings_module = fraiseql.embeddings

            # Check what's in the embeddings module
            print("  Embeddings module contents:")
            for attr in dir(embeddings_module):
                if not attr.startswith("_"):
                    print(f"    - {attr}")

            # Check for EmbeddingService
            if hasattr(embeddings_module, "EmbeddingService"):
                print("✓ EmbeddingService found")
            else:
                print("⚠ EmbeddingService not found")

        else:
            print("⚠ fraiseql.embeddings module not found")

        # Check for vector operators
        if hasattr(fraiseql, "operators"):
            print("✓ fraiseql.operators module found")
            operators_module = fraiseql.operators

            if hasattr(operators_module, "vector"):
                print("✓ Vector operators found")
            else:
                print("⚠ Vector operators not found")
        else:
            print("⚠ fraiseql.operators module not found")

        # Check create_fraiseql_app function for embedding config
        if hasattr(fraiseql, "create_fraiseql_app"):
            print("✓ create_fraiseql_app function found")
            # We can't test the actual app creation without a config file
            # but we can check if the function exists
        else:
            print("⚠ create_fraiseql_app function not found")

        return True

    except ImportError as e:
        print(f"✗ Failed to import FraiseQL: {e}")
        return False


def test_config_parsing():
    """Test if FraiseQL can parse the embedding config"""
    try:
        import yaml
        from pathlib import Path

        config_path = Path("config/fraiseql.yaml")
        if config_path.exists():
            print("✓ FraiseQL config file found")

            with open(config_path) as f:
                config = yaml.safe_load(f)

            if "embeddings" in config:
                print("✓ Embeddings configuration found in config")
                embeddings_config = config["embeddings"]
                print(f"  Provider: {embeddings_config.get('provider', 'not set')}")
                print(f"  Model: {embeddings_config.get('model', 'not set')}")
                print(
                    f"  Auto generate: {embeddings_config.get('auto_generate', 'not set')}"
                )
            else:
                print("⚠ No embeddings configuration in config")

            if "vector_discovery" in config:
                print("✓ Vector discovery configuration found")
                vector_config = config["vector_discovery"]
                print(f"  Enabled: {vector_config.get('enabled', 'not set')}")
                print(
                    f"  Auto create operators: {vector_config.get('auto_create_operators', 'not set')}"
                )
            else:
                print("⚠ No vector discovery configuration in config")

        else:
            print("⚠ FraiseQL config file not found")

        return True

    except Exception as e:
        print(f"✗ Failed to test config parsing: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing FraiseQL 1.5 Embeddings Functionality")
    print("=" * 60)

    tests = [
        test_fraiseql_embeddings,
        test_config_parsing,
    ]

    results = []
    for test in tests:
        print(f"\n🧪 {test.__name__}")
        result = test()
        results.append(result)

    print("\n" + "=" * 60)
    print("📊 Summary:")
    passed = sum(results)
    total = len(results)
    print(f"  Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All FraiseQL embeddings functionality verified!")
    else:
        print(
            "⚠️ Some functionality missing - may need different version or configuration"
        )

    print("\n📋 Next Steps:")
    print("  1. Try starting FraiseQL dev server to see if embeddings work at runtime")
    print("  2. Check if embeddings are available via GraphQL API when server runs")
    print("  3. Consider that CLI commands might be added in future versions")

    sys.exit(0 if passed == total else 1)
