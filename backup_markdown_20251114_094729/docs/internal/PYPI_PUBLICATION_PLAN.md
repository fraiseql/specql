# PyPI Publication Plan - SpecQL

**Status**: Pre-Publication Preparation
**Target**: First PyPI release (v0.1.0 or v0.2.0)
**Estimated Time**: 4-6 hours

---

## Executive Summary

SpecQL is 95% ready for PyPI publication. All core functionality is complete with 1,185 tests passing. This plan addresses the final 5% needed for professional PyPI release: metadata configuration, repository cleanup, and publication verification.

**Current Strengths**:
- ✅ 1,185 tests with comprehensive coverage
- ✅ Production-ready features (all 5 teams complete)
- ✅ MIT License
- ✅ Proper CHANGELOG.md
- ✅ Working examples and documentation
- ✅ pyproject.toml structure correct

**Gaps to Address**:
- ⚠️ PyPI-specific metadata missing
- ⚠️ Repository contains internal planning docs
- ⚠️ README references non-existent CI setup
- ⚠️ No TestPyPI validation yet

---

## PHASES

### Phase 1: Repository Cleanup & Organization
**Objective**: Organize repository for public consumption, remove internal planning artifacts

**Estimated Time**: 1 hour

#### Tasks:

1. **Create Internal Documentation Directory**
   ```bash
   mkdir -p docs/internal
   ```

2. **Move Internal Planning Documents**
   Move these files from root to `docs/internal/`:
   - `issue4_executive_summary.md`
   - `issue4_implementation_plan.md`
   - `issue4.md`
   - `INVESTOR_EVALUATION.md`
   - `TECHNICAL_IMPROVEMENT_PLAN.md`
   - `QUERY_PATTERN_LIBRARY_PROPOSAL.md`
   - `QUERY_PATTERNS_QUICK_SUMMARY.md`
   - `QUERY_PATTERNS_INDEX.md`
   - `QUERY_PATTERNS_ADVANCED_IMPLEMENTATION_PLAN.md`
   - `QUERY_PATTERNS_IMPLEMENTATION_PLAN.md`

3. **Update .gitignore**
   Add to `.gitignore`:
   ```
   # PyPI distribution
   dist/
   build/
   *.egg-info/

   # Internal planning (optional - if you want to keep private)
   docs/internal/
   ```

4. **Verify Clean Repository**
   ```bash
   git status
   ls -la  # Should show clean root with only essential files
   ```

**Success Criteria**:
- [ ] Root directory contains only: README.md, CHANGELOG.md, LICENSE, CONTRIBUTING.md, GETTING_STARTED.md, pyproject.toml, Makefile, src/, tests/, docs/, examples/
- [ ] All planning docs moved to `docs/internal/`
- [ ] Git status shows organized changes

---

### Phase 2: PyPI Metadata Configuration
**Objective**: Add complete PyPI metadata to pyproject.toml for professional package listing

**Estimated Time**: 45 minutes

#### Tasks:

1. **Add [project.readme] Section**
   ```toml
   [project]
   # ... existing fields ...
   readme = "README.md"
   ```

2. **Add [project.urls] Section**
   ```toml
   [project.urls]
   Homepage = "https://github.com/fraiseql/specql"
   Repository = "https://github.com/fraiseql/specql"
   Documentation = "https://github.com/fraiseql/specql/blob/main/GETTING_STARTED.md"
   "Bug Tracker" = "https://github.com/fraiseql/specql/issues"
   Changelog = "https://github.com/fraiseql/specql/blob/main/CHANGELOG.md"
   ```

3. **Add [project.keywords]**
   ```toml
   [project]
   keywords = [
       "postgresql",
       "graphql",
       "code-generation",
       "sql-generator",
       "business-logic",
       "yaml",
       "plpgsql",
       "fraiseql",
       "schema-generator",
       "low-code"
   ]
   ```

4. **Add [project.classifiers]**
   ```toml
   [project]
   classifiers = [
       "Development Status :: 4 - Beta",
       "Intended Audience :: Developers",
       "License :: OSI Approved :: MIT License",
       "Programming Language :: Python :: 3",
       "Programming Language :: Python :: 3.11",
       "Programming Language :: Python :: 3.12",
       "Programming Language :: SQL",
       "Topic :: Database",
       "Topic :: Software Development :: Code Generators",
       "Topic :: Software Development :: Libraries :: Python Modules",
       "Operating System :: OS Independent",
       "Typing :: Typed",
   ]
   ```

5. **Add [build-system] Section** (if missing)
   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

6. **Verify Configuration**
   ```bash
   # Check pyproject.toml is valid
   uv run python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"

   # Verify all required fields present
   grep -E "(name|version|description|readme|requires-python|license|authors)" pyproject.toml
   ```

**Success Criteria**:
- [ ] All PyPI metadata sections added
- [ ] pyproject.toml validates successfully
- [ ] All required PyPI fields present

---

### Phase 3: README & Documentation Updates
**Objective**: Update README for accuracy and remove references to non-existent infrastructure

**Estimated Time**: 30 minutes

#### Tasks:

1. **Update Test Count in README**
   Change line 77 from:
   ```markdown
   - **Tests**: Comprehensive test suite (900+ tests, see CI for current status)
   ```
   To:
   ```markdown
   - **Tests**: Comprehensive test suite (1,185 tests, >95% coverage)
   ```

2. **Remove/Update CI Badges** (Lines 5-8)

   **Option A** - Remove badges until CI is public:
   ```markdown
   # SpecQL

   Business logic to production PostgreSQL + GraphQL generator.

   [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
   [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
   [![PyPI version](https://badge.fury.io/py/specql-generator.svg)](https://badge.fury.io/py/specql-generator)
   ```

   **Option B** - Add placeholder for future badges:
   ```markdown
   <!-- Badges will be added after GitHub repository is public -->
   ```

3. **Update Installation Instructions** (Lines 16-23)
   ```markdown
   ## Installation

   ### From PyPI (Recommended)
   ```bash
   pip install specql-generator
   # or with uv
   uv pip install specql-generator
   ```

   ### From Source
   ```bash
   git clone https://github.com/fraiseql/specql.git
   cd specql
   uv sync
   uv pip install -e .
   ```
   ```

4. **Update Project Status Section** (Lines 74-82)
   ```markdown
   ## Project Status

   - **Version**: 0.1.0 (Beta)
   - **Tests**: 1,185 tests passing
   - **Coverage**: >95%
   - **Stability**: Beta - Core features stable, API may evolve
   - **Production Use**: Suitable for evaluation and testing

   See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
   ```

5. **Add PyPI Badge After Publication**
   (Note for after publication):
   ```markdown
   [![PyPI version](https://badge.fury.io/py/specql-generator.svg)](https://pypi.org/project/specql-generator/)
   [![Downloads](https://pepy.tech/badge/specql-generator)](https://pepy.tech/project/specql-generator)
   ```

**Success Criteria**:
- [ ] Test count accurate (1,185 tests)
- [ ] CI badges removed or updated
- [ ] Installation instructions include PyPI
- [ ] No references to non-existent infrastructure

---

### Phase 4: Version Strategy Decision
**Objective**: Decide and document version number for first PyPI release

**Estimated Time**: 15 minutes

#### Decision Point: Version Number

**Option A: Keep v0.1.0**
- **Pro**: Honest about "early but stable" status
- **Pro**: Follows semantic versioning for pre-1.0
- **Con**: Signals "very early" to some users
- **Use if**: You expect API changes based on user feedback

**Option B: Bump to v0.2.0**
- **Pro**: Signals "production-ready beta"
- **Pro**: Differentiates from internal 0.1.0 milestone
- **Con**: Version jump without public releases
- **Use if**: You're confident in API stability

**Option C: Jump to v1.0.0**
- **Pro**: Maximum confidence signal
- **Con**: Commits to API stability
- **Use if**: You're ready to commit to backwards compatibility

#### Tasks:

1. **Choose Version Number**
   - Recommended: **v0.2.0** (signals production-ready beta)

2. **Update Version in pyproject.toml**
   ```toml
   version = "0.2.0"  # or your chosen version
   ```

3. **Update CHANGELOG.md**
   ```markdown
   ## [Unreleased]

   ## [0.2.0] - 2025-11-11

   ### Changed
   - First public PyPI release
   - Repository cleaned for public consumption
   - Documentation updated for PyPI users

   ### Added
   - PyPI metadata and classifiers
   - Installation instructions via pip/uv

   ## [0.1.0] - 2025-11-10
   [... existing content ...]

   [unreleased]: https://github.com/fraiseql/specql/compare/v0.2.0...HEAD
   [0.2.0]: https://github.com/fraiseql/specql/compare/v0.1.0...v0.2.0
   [0.1.0]: https://github.com/fraiseql/specql/releases/tag/v0.1.0
   ```

4. **Create VERSION File** (if using)
   ```bash
   echo "0.2.0" > VERSION
   ```

**Success Criteria**:
- [ ] Version number decided and documented
- [ ] pyproject.toml updated
- [ ] CHANGELOG.md updated with new version
- [ ] Git tag ready for creation

---

### Phase 5: Pre-Publication Testing
**Objective**: Verify package builds correctly and works when installed

**Estimated Time**: 1 hour

#### Tasks:

1. **Run Full Test Suite**
   ```bash
   # Clean environment
   uv run pytest --tb=short -v

   # Expected: All 1,185 tests passing
   ```

2. **Build Package**
   ```bash
   # Install build tools if needed
   uv pip install build twine

   # Clean previous builds
   rm -rf dist/ build/ *.egg-info/

   # Build package
   uv run python -m build

   # Should create:
   # dist/specql_generator-0.2.0-py3-none-any.whl
   # dist/specql_generator-0.2.0.tar.gz
   ```

3. **Verify Package Contents**
   ```bash
   # List wheel contents
   unzip -l dist/specql_generator-0.2.0-py3-none-any.whl

   # Check for:
   # - All src/ files
   # - README.md, LICENSE
   # - No tests/ (should be excluded)
   # - No docs/internal/ (should be excluded)
   ```

4. **Check Package Metadata**
   ```bash
   uv run twine check dist/*

   # Expected: PASSED for all files
   ```

5. **Test Installation in Clean Environment**
   ```bash
   # Create temporary venv
   python -m venv /tmp/test-specql
   source /tmp/test-specql/bin/activate

   # Install from built wheel
   pip install dist/specql_generator-0.2.0-py3-none-any.whl

   # Verify CLI works
   specql --help

   # Verify Python import works
   python -c "from src.core.specql_parser import SpecQLParser; print('Import OK')"

   # Cleanup
   deactivate
   rm -rf /tmp/test-specql
   ```

6. **Upload to TestPyPI**
   ```bash
   # Register at https://test.pypi.org/ first

   # Upload to TestPyPI
   uv run twine upload --repository testpypi dist/*

   # Enter credentials when prompted
   ```

7. **Test Installation from TestPyPI**
   ```bash
   # Create fresh venv
   python -m venv /tmp/test-testpypi
   source /tmp/test-testpypi/bin/activate

   # Install from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ specql-generator

   # Test basic functionality
   specql --help

   # Cleanup
   deactivate
   rm -rf /tmp/test-testpypi
   ```

**Success Criteria**:
- [ ] All 1,185 tests pass
- [ ] Package builds without errors
- [ ] twine check passes
- [ ] Package installs correctly from wheel
- [ ] CLI command works after installation
- [ ] TestPyPI upload successful
- [ ] Installation from TestPyPI works

---

### Phase 6: Git Preparation & Tagging
**Objective**: Prepare git repository for publication and create release tag

**Estimated Time**: 30 minutes

#### Tasks:

1. **Review All Changes**
   ```bash
   git status
   git diff
   ```

2. **Commit Repository Cleanup**
   ```bash
   git add .
   git commit -m "chore: Prepare repository for PyPI publication

   - Move internal planning docs to docs/internal/
   - Add PyPI metadata to pyproject.toml
   - Update README with accurate test counts
   - Remove non-existent CI badge references
   - Update installation instructions for PyPI
   - Bump version to 0.2.0 for public release

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

3. **Create Git Tag**
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0 - First PyPI publication

   First public release on PyPI with production-ready features:
   - 1,185 tests with >95% coverage
   - Complete YAML to PostgreSQL + GraphQL generation
   - All 5 teams (Parser, Schema, Actions, FraiseQL, CLI) implemented
   - Comprehensive documentation and examples

   See CHANGELOG.md for full details."
   ```

4. **Verify Tag**
   ```bash
   git tag -l
   git show v0.2.0
   ```

5. **Push to GitHub** (if repository is ready to be public)
   ```bash
   # Push commits
   git push origin pre-public-cleanup

   # Push tags
   git push origin v0.2.0
   ```

6. **Create GitHub Release** (via web UI or CLI)
   ```bash
   # Using gh CLI
   gh release create v0.2.0 \
     --title "v0.2.0 - First PyPI Release" \
     --notes "See [CHANGELOG.md](https://github.com/fraiseql/specql/blob/main/CHANGELOG.md#020---2025-11-11) for details." \
     dist/specql_generator-0.2.0-py3-none-any.whl \
     dist/specql_generator-0.2.0.tar.gz
   ```

**Success Criteria**:
- [ ] All changes committed with clear message
- [ ] Git tag v0.2.0 created
- [ ] Tag pushed to GitHub
- [ ] GitHub release created with artifacts

---

### Phase 7: PyPI Publication
**Objective**: Publish package to official PyPI registry

**Estimated Time**: 30 minutes

#### Pre-Publication Checklist:

- [ ] All tests passing (1,185 tests)
- [ ] Package built successfully
- [ ] TestPyPI installation verified
- [ ] Git tagged and pushed
- [ ] GitHub release created
- [ ] README accurate and professional
- [ ] CHANGELOG up to date

#### Tasks:

1. **Final Verification**
   ```bash
   # Ensure clean build
   rm -rf dist/ build/ *.egg-info/
   uv run python -m build

   # Final check
   uv run twine check dist/*
   ```

2. **Register PyPI Account** (if not done)
   - Go to https://pypi.org/account/register/
   - Verify email
   - Set up 2FA (recommended)
   - Create API token at https://pypi.org/manage/account/token/

3. **Configure PyPI Credentials**
   ```bash
   # Create ~/.pypirc
   cat > ~/.pypirc << 'EOF'
   [pypi]
   username = __token__
   password = pypi-YOUR-API-TOKEN-HERE
   EOF

   chmod 600 ~/.pypirc
   ```

4. **Upload to PyPI**
   ```bash
   uv run twine upload dist/*

   # Expected output:
   # Uploading distributions to https://upload.pypi.org/legacy/
   # Uploading specql_generator-0.2.0-py3-none-any.whl
   # Uploading specql_generator-0.2.0.tar.gz
   #
   # View at:
   # https://pypi.org/project/specql-generator/0.2.0/
   ```

5. **Verify PyPI Page**
   - Visit https://pypi.org/project/specql-generator/
   - Check:
     - [ ] README renders correctly
     - [ ] Version is correct
     - [ ] License shows as MIT
     - [ ] Links work (Homepage, Repository, etc.)
     - [ ] Classifiers are correct

6. **Test Installation from PyPI**
   ```bash
   # Fresh environment
   python -m venv /tmp/test-pypi
   source /tmp/test-pypi/bin/activate

   # Install from official PyPI
   pip install specql-generator

   # Verify
   specql --help
   python -c "from src.core.specql_parser import SpecQLParser; print('SpecQL installed successfully!')"

   # Cleanup
   deactivate
   rm -rf /tmp/test-pypi
   ```

7. **Update README Badges**
   Add to README.md:
   ```markdown
   [![PyPI version](https://badge.fury.io/py/specql-generator.svg)](https://pypi.org/project/specql-generator/)
   [![Downloads](https://pepy.tech/badge/specql-generator)](https://pepy.tech/project/specql-generator)
   ```

8. **Announce Release**
   - Update project status to mention PyPI availability
   - Consider posting on:
     - Project blog/website
     - Twitter/X
     - Reddit (r/Python, r/postgresql, r/graphql)
     - Dev.to
     - Hacker News (Show HN)

**Success Criteria**:
- [ ] Package visible on PyPI
- [ ] README renders correctly on PyPI
- [ ] Installation from PyPI works
- [ ] CLI and imports functional
- [ ] Badges updated in README

---

### Phase 8: Post-Publication Cleanup
**Objective**: Final housekeeping and documentation updates

**Estimated Time**: 30 minutes

#### Tasks:

1. **Update CONTRIBUTING.md**
   Add section about PyPI releases:
   ```markdown
   ## Release Process

   Releases are published to PyPI following semantic versioning:

   1. Update version in `pyproject.toml`
   2. Update `CHANGELOG.md` with release notes
   3. Run full test suite: `make test`
   4. Build package: `python -m build`
   5. Upload to TestPyPI: `twine upload --repository testpypi dist/*`
   6. Test installation from TestPyPI
   7. Create git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
   8. Push tag: `git push origin vX.Y.Z`
   9. Upload to PyPI: `twine upload dist/*`
   10. Create GitHub release with artifacts
   ```

2. **Create Release Checklist Template**
   Create `.github/RELEASE_CHECKLIST.md`:
   ```markdown
   # Release Checklist

   ## Pre-Release
   - [ ] All tests passing
   - [ ] CHANGELOG.md updated
   - [ ] Version bumped in pyproject.toml
   - [ ] README accurate
   - [ ] Documentation up to date

   ## Build & Test
   - [ ] Clean build: `rm -rf dist/ && python -m build`
   - [ ] Twine check passes: `twine check dist/*`
   - [ ] TestPyPI upload successful
   - [ ] TestPyPI installation verified

   ## Publication
   - [ ] Git tag created and pushed
   - [ ] GitHub release created
   - [ ] PyPI upload successful
   - [ ] PyPI installation verified
   - [ ] README badges updated

   ## Post-Release
   - [ ] Announcement prepared
   - [ ] CHANGELOG.md shows [Unreleased] section
   - [ ] Version bumped to next dev version (optional)
   ```

3. **Add PyPI Badge to README** (if not done)
   ```bash
   # Add to top of README after license badge
   ```

4. **Commit Final Updates**
   ```bash
   git add README.md CONTRIBUTING.md .github/RELEASE_CHECKLIST.md
   git commit -m "docs: Add PyPI badges and release documentation

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"

   git push origin pre-public-cleanup
   ```

5. **Create Post-Publication Summary**
   Document for your records:
   ```markdown
   # PyPI Publication Summary

   **Date**: 2025-11-11
   **Version**: 0.2.0
   **PyPI URL**: https://pypi.org/project/specql-generator/

   ## Metrics
   - Tests: 1,185 passing
   - Coverage: >95%
   - Package size: [check actual]
   - Dependencies: 9 core, 8 dev

   ## Next Steps
   - Monitor PyPI download stats
   - Watch for GitHub issues/questions
   - Plan next feature releases
   - Consider setting up CI/CD for automated releases
   ```

**Success Criteria**:
- [ ] All documentation updated
- [ ] Release process documented
- [ ] Badges showing correct information
- [ ] Repository clean and professional
- [ ] Post-publication summary created

---

## Success Metrics

### Immediate (Day 1)
- [ ] Package visible on PyPI
- [ ] Installation works: `pip install specql-generator`
- [ ] CLI functional: `specql --help`
- [ ] No critical issues reported

### Short-term (Week 1)
- [ ] 10+ downloads
- [ ] No installation issues reported
- [ ] Documentation feedback addressed
- [ ] Any quick-fix issues resolved

### Medium-term (Month 1)
- [ ] 100+ downloads
- [ ] Community engagement (GitHub stars, issues)
- [ ] First external contributions
- [ ] Feature requests prioritized

---

## Risk Mitigation

### Risk: Package Doesn't Install Correctly
**Mitigation**: TestPyPI testing in Phase 5 catches this before production

### Risk: Missing Dependencies
**Mitigation**: Clean venv testing verifies all dependencies listed

### Risk: Breaking Changes After Publication
**Mitigation**: Semantic versioning (0.x.x) signals potential changes

### Risk: Security Vulnerabilities in Dependencies
**Mitigation**:
- Monitor `psycopg2-binary` and other deps with `pip-audit`
- Set up Dependabot on GitHub

### Risk: Name Conflict on PyPI
**Mitigation**: Name `specql-generator` checked and available

---

## Resources

### PyPI Resources
- Official Guide: https://packaging.python.org/tutorials/packaging-projects/
- Twine Docs: https://twine.readthedocs.io/
- TestPyPI: https://test.pypi.org/
- PyPI Help: https://pypi.org/help/

### Tools Needed
```bash
uv pip install build twine
```

### Credentials Required
- PyPI account (https://pypi.org/account/register/)
- API token (https://pypi.org/manage/account/token/)
- GitHub access (for releases)

---

## Timeline Estimate

| Phase | Time | Dependencies |
|-------|------|--------------|
| 1: Repository Cleanup | 1h | None |
| 2: PyPI Metadata | 45m | Phase 1 |
| 3: README Updates | 30m | Phase 2 |
| 4: Version Strategy | 15m | Phase 3 |
| 5: Pre-Publication Testing | 1h | Phase 4 |
| 6: Git Preparation | 30m | Phase 5 |
| 7: PyPI Publication | 30m | Phase 6 |
| 8: Post-Publication | 30m | Phase 7 |

**Total**: 4.5 - 5 hours (sequential)

**Parallel Opportunities**: Phases 1-3 can overlap if multiple contributors

---

## Conclusion

SpecQL has a solid foundation and is ready for PyPI publication after these final touches. The phased approach ensures:

1. **Professional presentation** - Clean repository, accurate documentation
2. **Risk mitigation** - TestPyPI validation before production
3. **Quality assurance** - Multiple verification steps
4. **Future maintenance** - Documented release process

**Recommendation**: Execute all 8 phases sequentially before first PyPI publication. For subsequent releases, Phases 5-7 will be the primary workflow.

---

**Last Updated**: 2025-11-11
**Author**: Claude Code (with human review)
**Status**: Ready for Execution
