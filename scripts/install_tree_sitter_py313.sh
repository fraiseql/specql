#!/bin/bash
# Install tree-sitter-languages for Python 3.13
#
# The tree-sitter-languages library doesn't have pre-built wheels for Python 3.13 yet.
# This script builds it from source as a workaround.
#
# Source: https://github.com/aider-chat/aider/discussions/2526

set -e

echo "🔧 Installing tree-sitter-languages for Python 3.13"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" != "3.13" ]]; then
    echo "⚠️  Warning: This script is designed for Python 3.13"
    echo "   Your version is $PYTHON_VERSION"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install build dependencies
echo ""
echo "📦 Installing build dependencies..."
pip install Cython setuptools tree-sitter==0.21.3 wheel

# Download tree-sitter-languages source
echo ""
echo "⬇️  Downloading tree-sitter-languages v1.10.2..."
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
curl -L -o tree-sitter-languages-1.10.2.tar.gz https://github.com/grantjenks/py-tree-sitter-languages/archive/refs/tags/v1.10.2.tar.gz

# Extract and build
echo ""
echo "🏗️  Building tree-sitter-languages from source..."
tar -x -f tree-sitter-languages-1.10.2.tar.gz
cd py-tree-sitter-languages-1.10.2
python build.py

# Install
echo ""
echo "📥 Installing tree-sitter-languages..."
pip install .

# Test installation
echo ""
echo "✅ Testing installation..."
python -c 'from tree_sitter_languages import get_language; get_language("python"); print("Success! tree-sitter-languages is working")'

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 tree-sitter-languages installation complete!"
echo ""
echo "Note: The compatibility layer in src/reverse_engineering/tree_sitter_compat.py"
echo "will automatically use tree-sitter-languages now that it's available."
