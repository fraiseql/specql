# Python 3.13 Setup Guide

> **🎉 GREAT NEWS:** Python 3.13 is now fully supported!
>
> See [TREE_SITTER_MIGRATION.md](TREE_SITTER_MIGRATION.md) for the modern approach using `tree-sitter-language-pack`.
>
> This document is kept for historical reference and details the old workarounds (no longer needed).

## Tree-Sitter Dependencies for Reverse Engineering

SpecQL's reverse engineering features require tree-sitter parsers for Rust, TypeScript, and Prisma.

### Modern Approach (Python 3.10+)

```bash
pip install 'specql[reverse]'
```

This installs `tree-sitter-language-pack>=0.11.0` which includes 165+ pre-compiled language grammars with **Python 3.13 wheel support**!

✅ **This is all you need!** The rest of this document describes legacy workarounds that are no longer necessary.

## Legacy Options (Historical Reference)

### Python 3.11 & 3.12: Legacy Package

Previously used `tree-sitter-languages>=1.10.2` (40+ languages, now unmaintained).

### Python 3.13: Old Workarounds (No Longer Needed!)

The `tree-sitter-languages` package doesn't have pre-built wheels for Python 3.13. These workarounds are now **obsolete** thanks to `tree-sitter-language-pack`:

#### Option 1: Build from Source (Recommended)

Use the provided script to build `tree-sitter-languages` from source:

```bash
./scripts/install_tree_sitter_py313.sh
```

This script:
- Installs build dependencies (Cython, setuptools, wheel)
- Downloads tree-sitter-languages v1.10.2 source
- Builds and installs it locally
- Tests the installation

**Advantages:**
- ✅ Single package with 40+ language grammars
- ✅ Simpler dependency management
- ✅ Matches Python 3.11/3.12 setup

**Requirements:**
- Build tools (gcc/clang)
- Internet connection for source download

#### Option 2: Use Individual Packages (Current Fallback)

The project currently uses individual tree-sitter packages as a fallback:

```bash
pip install tree-sitter-rust tree-sitter-typescript tree-sitter-prisma
```

These are already installed if you're seeing tests pass.

**Advantages:**
- ✅ No build step required
- ✅ Works immediately

**Disadvantages:**
- ⚠️ Limited to 3 languages (vs 40+ in tree-sitter-languages)
- ⚠️ Different import patterns

## How It Works

The compatibility layer in `src/reverse_engineering/tree_sitter_compat.py` automatically detects which approach is available:

1. **First Choice**: Try to import `tree_sitter_languages` (unified package)
2. **Fallback**: Use individual packages (`tree_sitter_rust`, etc.)
3. **Error**: If neither is available, raise helpful error

This means:
- Python 3.11/3.12: Uses tree-sitter-languages (pre-built wheels)
- Python 3.13 with Option 1: Uses tree-sitter-languages (built from source)
- Python 3.13 with Option 2: Uses individual packages (current setup)

## Testing Your Setup

Verify tree-sitter is working:

```bash
python3 -c "
from src.reverse_engineering.tree_sitter_compat import (
    HAS_TREE_SITTER,
    get_rust_language,
    get_prisma_language,
    get_typescript_language,
)

print('HAS_TREE_SITTER:', HAS_TREE_SITTER)
print('Rust:', get_rust_language())
print('Prisma:', get_prisma_language())
print('TypeScript:', get_typescript_language())
print('✅ All working!')
"
```

Run reverse engineering tests:

```bash
# Rust tests
pytest tests/unit/reverse_engineering/test_tree_sitter_rust.py -v

# Prisma tests
pytest tests/unit/reverse_engineering/test_tree_sitter_prisma.py -v

# All reverse engineering tests
pytest tests/unit/reverse_engineering/ -v
```

## Troubleshooting

### Build Failures (Option 1)

If `./scripts/install_tree_sitter_py313.sh` fails:

**Missing compiler:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install
```

**Cython errors:**
```bash
pip install --upgrade Cython setuptools wheel
```

### Import Errors (Option 2)

If individual packages fail to import:

```bash
# Reinstall packages
pip install --force-reinstall tree-sitter-rust tree-sitter-typescript tree-sitter-prisma

# Verify installations
pip list | grep tree-sitter
```

### Tests Still Failing

```bash
# Check which approach is being used
python3 -c "
from src.reverse_engineering.tree_sitter_compat import HAS_TREE_SITTER
print('Tree-sitter available:', HAS_TREE_SITTER)

try:
    from tree_sitter_languages import get_language
    print('Using: tree-sitter-languages (unified)')
except ImportError:
    print('Using: individual packages (fallback)')
"

# Run tests with verbose output
pytest tests/unit/reverse_engineering/ -vv --tb=short
```

## Future Plans

The `tree-sitter-languages` maintainer has archived the project, but:
- Pre-built wheels for Python 3.13 may still be released
- Alternative packages (TSL Pack) are in development
- Our compatibility layer is ready for either approach

## References

- [tree-sitter-languages GitHub](https://github.com/grantjenks/py-tree-sitter-languages)
- [Python 3.13 workaround discussion](https://github.com/aider-chat/aider/discussions/2526)
- [tree-sitter documentation](https://tree-sitter.github.io/tree-sitter/)
