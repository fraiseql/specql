# SpecQL Version Management

## Overview

SpecQL uses an industrial-grade version management system adapted from production systems (PrintOptim backend). This ensures **atomic operations**, **automatic rollback**, and **complete consistency** across all version files.

## Version Files

The system maintains **three synchronized version files**:

1. **`version.json`** - Primary source of truth with metadata
2. **`VERSION`** - Legacy file for backwards compatibility
3. **`pyproject.toml`** - Python package version

All three files are **automatically synchronized** by the version manager.

## Version Manager

### Usage

```bash
# Dry run (preview changes)
python scripts/version_manager.py --dry-run patch

# Bump patch version (0.6.0 → 0.6.1)
python scripts/version_manager.py patch

# Bump minor version (0.6.0 → 0.7.0)
python scripts/version_manager.py minor

# Bump major version (0.6.0 → 1.0.0)
python scripts/version_manager.py major
```

See full documentation in the file.
