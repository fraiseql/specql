# Version Management Guide

## Quick Start

```bash
# Bump patch version (0.6.0 → 0.6.1)
python scripts/version_manager.py patch

# Bump minor version (0.6.0 → 0.7.0)  
python scripts/version_manager.py minor

# Bump major version (0.6.0 → 1.0.0)
python scripts/version_manager.py major

# Preview changes (dry run)
python scripts/version_manager.py --dry-run patch
```

## Version Files

Three files are automatically synchronized:
- `version.json` - Primary source with metadata
- `VERSION` - Legacy compatibility
- `pyproject.toml` - Python package version

## Release Workflow

1. Make changes, create PR
2. Merge to main (quality gate runs)
3. Bump version: `python scripts/version_manager.py [patch|minor|major]`
4. Commit: `git add . && git commit -m "chore: bump version to X.Y.Z"`
5. Push tag: `git push origin vX.Y.Z`
6. CI/CD automatically publishes to PyPI + creates GitHub release

## Semantic Versioning

- **Patch** (0.6.1): Bug fixes
- **Minor** (0.7.0): New features (backwards compatible)
- **Major** (1.0.0): Breaking changes

## Features

✅ Atomic operations (all or nothing)
✅ Automatic rollback on failure
✅ Git tag creation
✅ Version consistency validation
✅ Complete audit trail

Adapted from PrintOptim's production system (100+ releases, zero inconsistencies).
