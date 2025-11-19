# Tree-Sitter Package Migration Guide

## Summary

SpecQL now uses **`tree-sitter-language-pack`** - the actively maintained successor to `tree-sitter-languages`, with **Python 3.13 support** and 165+ language grammars!

## What Changed

### Before (Legacy)
- `tree-sitter-languages` (unmaintained, no Python 3.13 wheels)
- Required workarounds or building from source for Python 3.13

### After (Current)
- **`tree-sitter-language-pack`** (actively maintained, Python 3.10-3.13)
- 165+ languages vs 40+ in the old package
- MIT licensed
- Drop-in replacement with identical API

## For New Users

Simply install:
```bash
pip install 'specql[reverse]'
```

This will install `tree-sitter-language-pack` and you're ready to go!

## For Existing Users

### If You Have tree-sitter-languages Installed

Nothing to do! The compatibility layer supports both packages with automatic fallback:
1. Individual packages (if installed) - highest priority
2. tree-sitter-language-pack (recommended)
3. tree-sitter-languages (legacy)

### Recommended Upgrade Path

```bash
# Remove the old package
pip uninstall tree-sitter-languages

# Install the new one
pip install tree-sitter-language-pack

# Or just reinstall specql[reverse]
pip install --force-reinstall 'specql[reverse]'
```

## Compatibility Layer Architecture

The updated `src/reverse_engineering/tree_sitter_compat.py` now supports **three** fallback levels:

### Priority 1: Individual Packages (Best for Latest Grammars)
```python
import tree_sitter_rust
import tree_sitter_prisma
import tree_sitter_typescript
```

**Advantages:**
- Most up-to-date grammars (e.g., Prisma v15 vs v13 in language-pack)
- Direct control over versions
- No monolithic package

**Use when:**
- You need the absolute latest grammar versions
- Working with cutting-edge language features

### Priority 2: tree-sitter-language-pack (Recommended)
```python
from tree_sitter_language_pack import get_language, get_parser
```

**Advantages:**
- ✅ Actively maintained
- ✅ Python 3.10-3.13 support (has Python 3.13 wheels!)
- ✅ 165+ languages in one package
- ✅ Regular updates
- ✅ MIT licensed

**Use when:**
- Fresh installation
- Python 3.13 environment
- Want comprehensive language support

### Priority 3: tree-sitter-languages (Legacy)
```python
from tree_sitter_languages import get_language, get_parser
```

**Status:**
- ⚠️ Unmaintained (archived)
- ⚠️ No Python 3.13 wheels
- ⚠️ Only 40+ languages

**Use when:**
- Already installed and working
- Python 3.11/3.12 environment
- Not worth changing

## Python 3.13 Notes

### The Good News
✅ `tree-sitter-language-pack` has pre-built wheels for Python 3.13!

### No More Workarounds Needed
The previous Python 3.13 workarounds are now **optional**:
- ❌ No need to build `tree-sitter-languages` from source
- ❌ No need to use individual packages (unless you want latest grammars)
- ✅ Just `pip install tree-sitter-language-pack` and it works!

### Legacy Python 3.13 Setup Script
The `scripts/install_tree_sitter_py313.sh` script is still available for users who want to build `tree-sitter-languages` from source, but it's no longer necessary.

## Testing Your Setup

```bash
# Check which backend is active
python3 -c "
from src.reverse_engineering.tree_sitter_compat import HAS_TREE_SITTER
import src.reverse_engineering.tree_sitter_compat as compat

print('Tree-sitter available:', HAS_TREE_SITTER)

if hasattr(compat, '_USE_INDIVIDUAL_PACKAGES') and compat._USE_INDIVIDUAL_PACKAGES:
    print('Using: Individual packages (Priority 1)')
elif hasattr(compat, '_USE_TREE_SITTER_LANGUAGE_PACK') and compat._USE_TREE_SITTER_LANGUAGE_PACK:
    print('Using: tree-sitter-language-pack (Priority 2)')
elif hasattr(compat, '_USE_TREE_SITTER_LANGUAGES') and compat._USE_TREE_SITTER_LANGUAGES:
    print('Using: tree-sitter-languages (Priority 3 - legacy)')
"

# Run tests
pytest tests/unit/reverse_engineering/ -v
```

## Grammar Version Differences

### Prisma Grammar Versions
- **Individual package (`tree-sitter-prisma`)**: v15 (latest)
- **tree-sitter-language-pack**: v13 (slightly older)
- **tree-sitter-languages**: v13

**Impact:** The compatibility layer prioritizes individual packages for Prisma to ensure the latest grammar is used. If you only have language-pack installed, you'll get v13 which works fine for most cases.

**Node type differences (v15 vs v13):**
- v15: Uses `model_declaration` nodes
- v13: Uses `model_block` nodes

The Prisma parser code handles both versions automatically.

## Migration Checklist

- [ ] Uninstall `tree-sitter-languages` (optional but recommended)
- [ ] Install `tree-sitter-language-pack`
- [ ] Run tests to verify: `pytest tests/unit/reverse_engineering/ -v`
- [ ] Check which backend is active (see "Testing Your Setup" above)
- [ ] Remove Python 3.13 workaround scripts if you used them

## Troubleshooting

### Import Errors
```python
ModuleNotFoundError: No module named 'tree_sitter_language_pack'
```

**Solution:**
```bash
pip install tree-sitter-language-pack
```

### Tests Failing After Migration
```bash
# Clear any cached imports
find . -type d -name __pycache__ -exec rm -rf {} +

# Reinstall
pip install --force-reinstall tree-sitter-language-pack

# Re-run tests
pytest tests/unit/reverse_engineering/ -v
```

### Want to Switch Between Backends?
The compatibility layer makes this seamless:

```bash
# Use language-pack (165+ languages)
pip uninstall tree-sitter-rust tree-sitter-prisma tree-sitter-typescript
pip install tree-sitter-language-pack

# Use individual packages (latest grammars)
pip uninstall tree-sitter-language-pack tree-sitter-languages
pip install tree-sitter-rust tree-sitter-prisma tree-sitter-typescript

# Use legacy (if on Python 3.11/3.12)
pip uninstall tree-sitter-language-pack
# Build from source as per docs/PYTHON_3.13_SETUP.md
```

No code changes needed - the compatibility layer adapts automatically!

## Benefits of tree-sitter-language-pack

1. **Active Maintenance**: Regular updates and community support
2. **Python 3.13 Ready**: Pre-built wheels available
3. **Comprehensive**: 165+ languages vs 40+ in legacy package
4. **Proven**: Fork of tree-sitter-languages with improvements
5. **Same API**: Drop-in replacement, no code changes
6. **MIT Licensed**: Permissive licensing

## References

- [tree-sitter-language-pack on GitHub](https://github.com/Goldziher/tree-sitter-language-pack)
- [tree-sitter-language-pack on PyPI](https://pypi.org/project/tree-sitter-language-pack/)
- [Original tree-sitter-languages (archived)](https://github.com/grantjenks/py-tree-sitter-languages)

## Conclusion

The migration to `tree-sitter-language-pack` provides:
- ✅ Python 3.13 support out of the box
- ✅ More languages (165+ vs 40+)
- ✅ Active maintenance and updates
- ✅ Seamless compatibility with existing code

Simply `pip install tree-sitter-language-pack` and you're ready to go!
