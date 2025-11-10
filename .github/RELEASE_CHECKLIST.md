# Release Checklist

Use this checklist when preparing a new release.

## Pre-Release

- [ ] All tests passing: `make test`
- [ ] Code quality checks pass:
  - [ ] `make lint`
  - [ ] `make typecheck`
  - [ ] `make format`
- [ ] CHANGELOG.md updated with all changes in `[Unreleased]` section
- [ ] Documentation updated (if needed)

## Version Bump

Choose the appropriate version bump based on changes:

- **PATCH** (0.1.0 → 0.1.1): Bug fixes only
  ```bash
  make version-patch
  ```

- **MINOR** (0.1.0 → 0.2.0): New features, backward-compatible
  ```bash
  make version-minor
  ```

- **MAJOR** (0.1.0 → 1.0.0): Breaking changes
  ```bash
  make version-major
  ```

## Update CHANGELOG.md

1. Move items from `[Unreleased]` to new version section
2. Add release date
3. Update comparison links at bottom

Example:
```markdown
## [Unreleased]

## [0.2.0] - 2025-11-15

### Added
- New feature X

### Fixed
- Bug Y

[unreleased]: https://github.com/fraiseql/specql/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/fraiseql/specql/compare/v0.1.0...v0.2.0
```

## Commit and Tag

```bash
# Get version
VERSION=$(cat VERSION)

# Commit changes
git add VERSION pyproject.toml CHANGELOG.md
git commit -m "chore: Bump version to $VERSION

- Update VERSION and pyproject.toml
- Update CHANGELOG.md with release notes"

# Create tag
git tag -a "v$VERSION" -m "Release v$VERSION"

# Push
git push origin main
git push origin "v$VERSION"
```

## Post-Release

- [ ] Verify GitHub Actions release workflow completed successfully
- [ ] Check GitHub Release page: `https://github.com/fraiseql/specql/releases`
- [ ] Verify release notes are correct
- [ ] Test installation from release artifacts (if applicable)

## Rollback (if needed)

If something goes wrong:

```bash
# Delete local tag
git tag -d v$VERSION

# Delete remote tag
git push origin :refs/tags/v$VERSION

# Revert commit
git revert HEAD

# Push revert
git push origin main
```

---

**See also**: [docs/VERSIONING.md](../docs/VERSIONING.md) for detailed versioning guidelines.
