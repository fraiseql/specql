# v0.5.0-beta Release Checklist

## Pre-Release

- [x] All tests passing (2,937+ existing + 150+ new)
- [x] Test coverage >90% for new code
- [ ] No linting errors (`ruff check`)
- [ ] No type errors (`mypy`)
- [x] Documentation complete and reviewed
- [x] Examples tested and working
- [x] Demo GIFs created and embedded
- [x] Version numbers updated (0.5.0-beta)
- [x] CHANGELOG updated
- [x] Release notes drafted

## Testing

- [ ] `specql generate-tests` works
- [ ] `specql reverse-tests` works
- [ ] Both commands in `specql --help`
- [ ] Generated pgTAP tests are valid SQL
- [ ] Generated pytest tests are valid Python
- [ ] Preview mode works
- [ ] All CLI options work
- [ ] Examples in docs work

## Documentation

- [x] README updated
- [x] Test Generation Guide complete
- [x] Test Reverse Engineering Guide complete
- [x] Examples directory complete
- [x] Quick reference created
- [x] All links work
- [x] No typos

## Marketing

- [x] Blog post updated
- [x] Social media posts drafted
- [x] Comparison docs updated
- [x] Feature highlighted as differentiator

## Release

- [ ] Create Git tag: `git tag v0.5.0-beta`
- [ ] Push tag: `git push origin v0.5.0-beta`
- [ ] Create GitHub release
- [ ] Publish to PyPI: `uv publish`
- [ ] Announce on social media

## Post-Release

- [ ] Monitor GitHub issues
- [ ] Respond to user feedback
- [ ] Track adoption metrics
- [ ] Plan v0.6.0 features