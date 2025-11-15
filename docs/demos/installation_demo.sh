#!/bin/bash

# SpecQL Installation Demo Script
# This script simulates the installation process for asciinema recording

# Clear and show title
clear
echo "Installing SpecQL - Multi-Language Backend Generator"
echo "===================================================="
echo ""
sleep 2

# Check Python version
echo "Step 1: Verify Python 3.11+"
python --version
sleep 2
echo ""

# Install uv (if not installed)
echo "Step 2: Install uv package manager"
echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
echo "✓ uv installed"
sleep 2
echo ""

# Clone repository
echo "Step 3: Clone SpecQL repository"
echo "git clone https://github.com/fraiseql/specql.git"
echo "✓ Repository cloned"
sleep 2
echo ""

# Install dependencies
echo "Step 4: Install dependencies"
echo "cd specql && uv sync"
echo "✓ Dependencies installed"
sleep 3
echo ""

# Install SpecQL
echo "Step 5: Install SpecQL CLI"
echo "uv pip install -e ."
echo "✓ SpecQL CLI installed"
sleep 2
echo ""

# Verify installation
echo "Step 6: Verify installation"
echo "specql --version"
echo "specql 0.4.0-alpha"
sleep 1
echo ""

# Test generation
echo "Step 7: Test generation (dry run)"
echo "specql generate entities/examples/contact_lightweight.yaml --dry-run"
echo "✓ Generated code preview shown"
sleep 3
echo ""

# Success message
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  - Read quickstart: docs/00_getting_started/QUICKSTART.md"
echo "  - Try examples: specql generate entities/examples/**/*.yaml"
echo ""

# Pause before ending
sleep 3