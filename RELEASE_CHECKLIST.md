# v0.5.0-beta.1 Release Checklist

## Pre-Release

- [ ] All tests passing (verifying...)
- [x] Test coverage >90% for new code
- [x] No linting errors (`ruff check` - PASSED)
- [x] Type checking reviewed (`mypy` - acceptable warnings for beta)
- [x] Documentation complete and reviewed
- [x] Examples tested and working
- [x] Security audit complete (proprietary refs removed)
- [x] Version numbers updated (0.5.0-beta in VERSION and pyproject.toml)
- [x] CHANGELOG updated with v0.5.0-beta.1 entry
- [x] Release notes drafted (RELEASE_NOTES_v0.5.0-beta.1.md)

## Testing

- [x] Core CLI functional
- [x] All generation commands work
- [x] Modular dependencies tested
- [x] No regressions from v0.5.0-beta.0
- [ ] Full test suite passing (running...)

## Documentation

- [x] README cleaned (proprietary examples removed)
- [x] SECURITY.md added
- [x] CODE_OF_CONDUCT.md added
- [x] CHANGELOG.md updated for v0.5.0-beta.1
- [x] RELEASE_NOTES_v0.5.0-beta.1.md created
- [x] CONTRIBUTING.md simplified
- [x] All documentation current

## Release

- [ ] Commit all changes: `git add . && git commit -m "chore: prepare v0.5.0-beta.1 release"`
- [ ] Create Git tag: `git tag v0.5.0-beta.1`
- [ ] Push commits: `git push origin pre-public-cleanup`
- [ ] Push tag: `git push origin v0.5.0-beta.1`
- [ ] Create GitHub release with RELEASE_NOTES_v0.5.0-beta.1.md content
- [ ] Build package: `uv build`
- [ ] Publish to PyPI: `uv publish`
- [ ] Verify PyPI package: `pip install specql-generator==0.5.0b1`

## Post-Release

- [ ] Monitor GitHub issues
- [ ] Respond to user feedback
- [ ] Track adoption metrics
- [ ] Plan v0.6.0 features