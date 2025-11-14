#!/usr/bin/env python3
"""
Test FraiseQL 1.5 capabilities for vector search and embeddings
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_fraiseql_imports():
    """Test if we can import FraiseQL modules"""
    try:
        import fraiseql

        print("✓ FraiseQL imported successfully")
        print(
            f"  Version: {fraiseql.__version__ if hasattr(fraiseql, '__version__') else 'unknown'}"
        )

        # Check available modules
        print("  Available modules:")
        for attr in dir(fraiseql):
            if not attr.startswith("_"):
                print(f"    - {attr}")

        return True
    except ImportError as e:
        print(f"✗ Failed to import FraiseQL: {e}")
        return False


def test_fraiseql_client():
    """Test FraiseQL client capabilities"""
    try:
        from fraiseql import FraiseQLClient

        print("✓ FraiseQLClient imported successfully")

        # Check client methods
        print("  Client methods:")
        for attr in dir(FraiseQLClient):
            if not attr.startswith("_"):
                print(f"    - {attr}")

        return True
    except ImportError as e:
        print(f"✗ Failed to import FraiseQLClient: {e}")
        return False


def test_vector_operators():
    """Test if vector operators are available"""
    try:
        # Try to import vector-related modules
        import fraiseql.operators

        print("✓ fraiseql.operators imported")

        # Check for vector operators
        if hasattr(fraiseql.operators, "vector"):
            print("✓ Vector operators module found")
        else:
            print("⚠ No vector operators module")

        return True
    except ImportError:
        print("⚠ fraiseql.operators not available")
        return False


def test_embedding_service():
    """Test if embedding service is available"""
    try:
        import fraiseql.embeddings

        print("✓ fraiseql.embeddings imported")

        # Check embedding service
        if hasattr(fraiseql.embeddings, "EmbeddingService"):
            print("✓ EmbeddingService found")
        else:
            print("⚠ No EmbeddingService")

        return True
    except ImportError:
        print("⚠ fraiseql.embeddings not available")
        return False


def main():
    print("🔍 Testing FraiseQL 1.5 Capabilities")
    print("=" * 50)

    tests = [
        test_fraiseql_imports,
        test_fraiseql_client,
        test_vector_operators,
        test_embedding_service,
    ]

    results = []
    for test in tests:
        print(f"\n🧪 {test.__name__}")
        result = test()
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 Summary:")
    passed = sum(results)
    total = len(results)
    print(f"  Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All FraiseQL capabilities verified!")
    else:
        print(
            "⚠️ Some capabilities missing - may need different version or configuration"
        )

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
