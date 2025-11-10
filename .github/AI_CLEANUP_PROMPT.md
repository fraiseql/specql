# AI Assistant Cleanup Prompt

**Copy this entire prompt and send to Claude Code when ready to prepare for public release.**

---

## Task: Prepare SpecQL Repository for Public Release

You are helping prepare the private SpecQL repository at `fraiseql/specql` for public release. Perform a comprehensive security audit, code cleanup, and quality check.

### Phase 1: Security Audit (CRITICAL)

1. **Search for sensitive data**:
   - Scan for: passwords, secrets, API keys, tokens, credentials
   - Check for: internal email addresses, company references, hostnames
   - Review: environment files, config files, test fixtures
   - Command: `rg -i "password|secret|api_key|token" --type yaml --type py`

2. **Check git history**:
   - Review recent commits for sensitive data
   - Check for accidentally committed large files
   - Verify all commit messages are professional

3. **Verify .gitignore**:
   - Ensure `.env` files excluded
   - Check no sensitive configs tracked
   - Remove any tracked files that should be ignored

**Output**: Report any findings that must be addressed before public release.

### Phase 2: Code Quality

4. **Remove dead code**:
   - Find and remove/resolve all TODO/FIXME comments: `rg "TODO|FIXME|XXX|HACK" --type py`
   - Remove commented-out code blocks
   - Delete unused imports and variables
   - Clean up experimental/incomplete features

5. **Test coverage**:
   - Run full test suite: `make test`
   - Generate coverage report: `make coverage`
   - Fix any failing tests
   - Document why coverage is <80% if applicable

6. **Code style**:
   - Format code: `make format`
   - Fix linting: `make lint`
   - Fix type errors: `make typecheck`

**Output**: Summary of code quality improvements made.

### Phase 3: Documentation

7. **Review README.md**:
   - Verify installation instructions work
   - Test quick start example
   - Check all links work
   - Ensure no internal references
   - Add missing badges if needed

8. **Check all .md files**:
   - Review for accuracy and professionalism
   - Fix broken links
   - Update outdated information
   - Remove internal-only context

9. **Review code comments**:
   - Ensure public APIs have docstrings
   - Remove unprofessional comments
   - Verify no internal-only context required

**Output**: List of documentation improvements made.

### Phase 4: Repository Structure

10. **File organization**:
    - Check for build artifacts: `find . -name "*.pyc" -o -name "__pycache__"`
    - Remove unnecessary root files
    - Verify .gitignore is comprehensive
    - Clean up empty directories

11. **Dependencies**:
    - Review pyproject.toml dependencies
    - Remove unnecessary dependencies
    - Verify all are public packages
    - Check licenses are compatible

12. **GitHub configuration**:
    - Review .github/workflows/*.yml
    - Check ISSUE_TEMPLATE if present
    - Verify PR template is appropriate

**Output**: Repository structure improvements.

### Phase 5: Legal & Licensing

13. **License compliance**:
    - Verify LICENSE file exists (MIT preferred)
    - Check copyright notices
    - Acknowledge third-party licenses
    - Ensure proper attribution

**Output**: License compliance status.

### Phase 6: Final Verification

14. **Run automated checks**:
    ```bash
    bash scripts/pre_public_check.sh
    ```

15. **Version consistency**:
    - Verify VERSION and pyproject.toml match
    - Check if v1.0.0 is appropriate for public launch
    - Update CHANGELOG.md if needed

16. **Fresh install test**:
    - Test installation in clean environment
    - Follow README exactly
    - Verify quick start works

**Output**: Pass/fail status of automated checks.

---

## Deliverables

Provide a comprehensive report with:

1. **Security Findings** (if any - MUST be addressed)
2. **Code Quality Issues Fixed** (summary)
3. **Documentation Updates Made** (list)
4. **Repository Cleanup Actions** (list)
5. **Automated Check Results** (pass/fail)
6. **Recommended Next Steps** before going public

## Success Criteria

- [ ] No sensitive data anywhere in repository or history
- [ ] All tests passing
- [ ] Code quality checks passing (lint, typecheck)
- [ ] Documentation is accurate and complete
- [ ] Fresh installation works
- [ ] `scripts/pre_public_check.sh` passes with no errors
- [ ] LICENSE file present and correct
- [ ] Version ready (consider v1.0.0 for public launch)

---

## Important Notes

- Be thorough but don't be destructive
- Create a branch for cleanup work: `git checkout -b pre-public-cleanup`
- Run all commands from repository root: `/home/lionel/code/specql`
- Use existing Makefile targets when available
- Document any assumptions or decisions made
- Flag anything uncertain for human review

---

## Reference

See `.github/PRE_PUBLIC_CLEANUP.md` for the complete manual checklist.

Run: `bash scripts/pre_public_check.sh` for automated verification.

---

**Ready to begin? Start with Phase 1: Security Audit**
