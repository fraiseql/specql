# Versioning Quick Reference

## Current Version
```bash
make version
# Output: Current version: 0.1.0
```

## Bump Version

| Command | From | To | Use For |
|---------|------|-----|---------|
| `make version-patch` | 0.1.0 | 0.1.1 | Bug fixes |
| `make version-minor` | 0.1.0 | 0.2.0 | New features |
| `make version-major` | 0.1.0 | 1.0.0 | Breaking changes |

## Release Process (TL;DR)

```bash
# 1. Bump version
make version-minor  # or patch/major

# 2. Update CHANGELOG.md
# Move [Unreleased] items to new version section

# 3. Commit and tag
VERSION=$(cat VERSION)
git add VERSION pyproject.toml CHANGELOG.md
git commit -m "chore: Bump version to $VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"

# 4. Push (triggers automated release)
git push origin main
git push origin "v$VERSION"
```

## What Happens Automatically

When you push a tag like `v0.2.0`, GitHub Actions will:
1. ✅ Run all tests
2. ✅ Verify version consistency
3. ✅ Create GitHub Release
4. ✅ Extract changelog notes
5. ✅ Build distribution packages

## Files Managed by Versioning

- **VERSION** - Single source of truth
- **pyproject.toml** - Auto-synced by `scripts/version.py`
- **CHANGELOG.md** - Manually updated per release
- **README.md** - Version badge (manual update)

## Troubleshooting

**Q: Version mismatch error in CI?**
```bash
# Always use the script to update versions
python scripts/version.py bump patch
# Never edit VERSION or pyproject.toml directly!
```

**Q: Need to rollback a release?**
```bash
VERSION=0.2.0
git tag -d v$VERSION              # Delete local tag
git push origin :refs/tags/v$VERSION  # Delete remote tag
```

**Q: Forgot to update CHANGELOG.md?**
```bash
# Edit CHANGELOG.md
git add CHANGELOG.md
git commit --amend --no-edit
git tag -d v$VERSION
git tag -a "v$VERSION" -m "Release v$VERSION"
git push -f origin main
git push -f origin "v$VERSION"
```

## See Also

- 📖 [Full Documentation](../docs/VERSIONING.md)
- ✅ [Release Checklist](RELEASE_CHECKLIST.md)
- 📝 [CHANGELOG.md](../CHANGELOG.md)
