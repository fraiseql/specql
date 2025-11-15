# Week 3: PyPI Publication & Production Testing

**Goal**: Publish v0.4.0-alpha to production PyPI and validate with real-world usage.

**Estimated Time**: 35-40 hours (1 week full-time)

**Prerequisites**:
- Week 2 completed (TestPyPI successful)
- All tests passing
- TestPyPI installation verified
- Documentation complete

---

## Overview

This week publishes SpecQL to production PyPI and validates it works for real users. By the end:
- ✅ Package live on PyPI
- ✅ `pip install specql-generator` works globally
- ✅ Real user testing completed
- ✅ Initial feedback gathered
- ✅ Quick-fix patches deployed (if needed)

---

## Day 1: Pre-Publication Final Checks (8 hours)

### Morning: Comprehensive Testing (4 hours)

#### Task 1.1: Run Full Test Suite (90 min)

```bash
cd ~/code/specql

# Clean environment
rm -rf dist/ build/ *.egg-info/ src/*.egg-info/

# Run ALL tests
uv run pytest --tb=short -v

# Expected: All tests pass
# If any fail, STOP and fix before publishing

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Open coverage report
open htmlcov/index.html

# Ensure coverage >90% for new code
```

**Record results**:
```markdown
# Final Test Run - Pre-Publication

**Date**: YYYY-MM-DD

## Test Results
- Total tests: ____
- Passed: ____
- Failed: ____
- Skipped: ____
- Coverage: ____%

## Status
- [ ] All tests pass
- [ ] Coverage >90%
- [ ] No critical issues

## Issues Found
[List any issues and their resolution]
```

#### Task 1.2: Cross-Platform Testing (90 min)

Test on different platforms if possible:

**Linux**:
```bash
# On Linux machine or Docker
docker run -it --rm -v $(pwd):/app python:3.11 bash
cd /app
pip install -e .
pytest
specql --version
```

**macOS**: (if available)
```bash
specql --version
pytest
```

**Windows**: (if available, via WSL or native)
```powershell
specql --version
pytest
```

**Document results**:
```markdown
# Cross-Platform Test Results

## Linux (Ubuntu 22.04)
- [ ] Installation successful
- [ ] Tests pass
- [ ] CLI works

## macOS (14.0)
- [ ] Installation successful
- [ ] Tests pass
- [ ] CLI works

## Windows (WSL/Native)
- [ ] Installation successful
- [ ] Tests pass
- [ ] CLI works
```

#### Task 1.3: Performance Benchmarks (60 min)

Run performance tests to establish baselines:

```bash
# Run benchmark tests
uv run pytest -m benchmark --benchmark-only

# Record results
uv run pytest -m benchmark --benchmark-json=benchmark-results.json

# Review results
cat benchmark-results.json | python -m json.tool
```

**Document key metrics**:
```markdown
# Performance Baselines - v0.4.0-alpha

## Entity Parsing
- Simple entity: ___ ms
- Complex entity: ___ ms
- 100 entities: ___ ms

## Code Generation
- PostgreSQL: ___ ms per entity
- Java: ___ ms per entity
- Rust: ___ ms per entity
- TypeScript: ___ ms per entity

## System
- Python version: ____
- Platform: ____
- CPU: ____
- RAM: ____
```

### Afternoon: Final Documentation Review (4 hours)

#### Task 1.4: User Journey Testing (2 hours)

**Simulate new user experience**:

```bash
# Fresh directory
cd /tmp
mkdir new-user-test
cd new-user-test

# Follow README exactly as written
# [Go through installation steps]
# [Follow quickstart guide]
# [Try 2-3 examples]

# Document any confusing steps
# Note: Where did you get stuck?
# Note: What wasn't clear?
# Fix those issues in docs
```

**Checklist**:
```markdown
# New User Journey Test

## Installation (Goal: <5 minutes)
- [ ] Prerequisites clear
- [ ] Installation commands work
- [ ] Verification works
- [ ] Time taken: ___ minutes

## Quickstart (Goal: <10 minutes)
- [ ] Tutorial easy to follow
- [ ] Code examples work
- [ ] Output as expected
- [ ] Time taken: ___ minutes

## Confusing Points
1. [What was unclear]
2. [What was unclear]

## Suggested Improvements
1. [Improvement]
2. [Improvement]
```

#### Task 1.5: Link Verification (90 min)

**Check ALL links**:

```bash
# Install link checker
pip install linkchecker

# Check README links
linkchecker README.md

# Check documentation links
find docs -name "*.md" -exec linkchecker {} \;

# Manual verification for important links
cat > check_links.py << 'EOF'
import re
import requests
from pathlib import Path

def check_md_links(file_path):
    content = Path(file_path).read_text()
    links = re.findall(r'\[.*?\]\((http.*?)\)', content)

    print(f"\nChecking {file_path}...")
    for link in links:
        try:
            r = requests.head(link, timeout=5, allow_redirects=True)
            status = "✅" if r.status_code == 200 else f"❌ {r.status_code}"
            print(f"{status} {link}")
        except Exception as e:
            print(f"❌ ERROR: {link} - {e}")

# Check main files
check_md_links("README.md")
check_md_links("CONTRIBUTING.md")
EOF

python check_links.py
```

Fix any broken links.

#### Task 1.6: Final Proofreading (30 min)

**Proofread key documents**:
- README.md
- CHANGELOG.md
- CONTRIBUTING.md
- docs/00_getting_started/QUICKSTART.md

Use spell checker:
```bash
# Install aspell
# brew install aspell (macOS)
# sudo apt install aspell (Linux)

# Check spelling
aspell check README.md
aspell check CONTRIBUTING.md
```

---

## Day 2: Production PyPI Setup & Upload (8 hours)

### Morning: PyPI Account Setup (2 hours)

#### Task 2.1: Create Production PyPI Account (30 min)

1. Go to https://pypi.org/account/register/
2. Use production email address
3. Verify email
4. Enable 2FA (REQUIRED for publishing)

#### Task 2.2: Create Production API Token (30 min)

1. Go to https://pypi.org/manage/account/token/
2. Create token: "specql-upload"
3. Scope: "Entire account" (for first upload)
4. Copy token securely
5. After first upload, can create project-scoped token

#### Task 2.3: Update .pypirc (30 min)

```bash
# Update ~/.pypirc with production token
nano ~/.pypirc

# Update [pypi] section:
[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-ACTUAL-PRODUCTION-TOKEN-HERE

# Verify permissions
chmod 600 ~/.pypirc
```

#### Task 2.4: Pre-Upload Checklist (30 min)

**Final verification**:

```markdown
# Production PyPI Upload Checklist

## Code
- [ ] All tests pass (100%)
- [ ] No linting errors
- [ ] No type errors
- [ ] Benchmarks run successfully

## Documentation
- [ ] README perfect
- [ ] CHANGELOG updated
- [ ] All links work
- [ ] No typos

## Package
- [ ] Version correct: 0.4.0-alpha
- [ ] TestPyPI upload successful
- [ ] TestPyPI installation tested
- [ ] No test files in package
- [ ] No internal docs in package

## Git
- [ ] All changes committed
- [ ] Working directory clean
- [ ] On main branch
- [ ] Pushed to remote

## PyPI Account
- [ ] Production account created
- [ ] Email verified
- [ ] 2FA enabled
- [ ] API token created
- [ ] .pypirc configured

## Backup
- [ ] Recent backup exists
- [ ] Can rollback if needed
```

**Only proceed if ALL checkboxes checked!**

### Afternoon: Production Upload (6 hours)

#### Task 2.5: Clean Build for Production (90 min)

```bash
cd ~/code/specql

# Ensure on correct branch and clean
git checkout main
git pull origin main
git status  # Must be clean

# Clean everything
rm -rf dist/ build/ *.egg-info/ src/*.egg-info/

# Final test run
uv run pytest --tb=short

# If ALL tests pass, proceed
# If any test fails, STOP

# Build
python -m build

# Verify build
twine check dist/*
# Must show: PASSED

# Inspect package one more time
unzip -l dist/specql_generator-0.4.0a0-py3-none-any.whl | less
# Verify contents look correct
```

#### Task 2.6: Upload to Production PyPI (30 min)

**The big moment**:

```bash
# Deep breath... this is it!

# Upload to production PyPI
twine upload dist/*

# You'll see:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading specql_generator-0.4.0a0-py3-none-any.whl
# Uploading specql_generator-0.4.0a0.tar.gz
#
# View at:
# https://pypi.org/project/specql-generator/
```

**If successful**:
- 🎉 Congratulations! SpecQL is now public!
- Note the URL
- Take a screenshot

**If error**:
- Read error message carefully
- Do NOT panic
- Common fixes:
  - Check token in ~/.pypirc
  - Ensure version unique
  - Verify metadata

#### Task 2.7: Verify PyPI Page (90 min)

**Open production PyPI page**:

```bash
open https://pypi.org/project/specql-generator/
```

**Comprehensive verification**:

```markdown
# Production PyPI Verification

## Project Page
- [ ] Correct project name
- [ ] Correct version (0.4.0a0)
- [ ] README renders perfectly
- [ ] No formatting issues
- [ ] Images load (if any)

## Metadata
- [ ] Description accurate
- [ ] Keywords relevant
- [ ] Classifiers correct
- [ ] License shows: MIT
- [ ] Author correct
- [ ] Python requirement: >=3.11

## Links (click each one)
- [ ] Homepage works
- [ ] Repository works
- [ ] Documentation works
- [ ] Bug Tracker works
- [ ] Changelog works

## Dependencies
- [ ] Core dependencies listed
- [ ] Optional dependencies shown correctly
- [ ] No unexpected dependencies

## Download Section
- [ ] Wheel file available
- [ ] Source distribution available
- [ ] File sizes reasonable

## Install Instructions
- [ ] `pip install specql-generator` shown
- [ ] Copy button works
```

**Screenshot** everything for documentation.

#### Task 2.8: First Production Installation Test (2 hours)

**Critical test - clean machine**:

```bash
# Completely fresh environment
cd /tmp
rm -rf pypi-production-test
mkdir pypi-production-test
cd pypi-production-test

# Fresh venv
python -m venv venv
source venv/bin/activate

# THE BIG TEST: Install from production PyPI
pip install specql-generator

# Verify
specql --version
# Must show: 0.4.0-alpha

# Full functional test
mkdir test-project
cd test-project

# Create entity
cat > blog.yaml << 'EOF'
entity: Post
schema: blog
fields:
  title: text
  content: text
  published_at: timestamp
  status: enum(draft, published)
actions:
  - name: publish
    steps:
      - validate: status = 'draft'
      - update: Post SET status = 'published', published_at = NOW()
EOF

# Generate
specql generate blog.yaml

# Verify output
ls -la output/blog/
cat output/blog/01_tables.sql
# Should have generated SQL

# Test imports
python << 'EOF'
from src.core.specql_parser import SpecQLParser
from src.generators.postgresql import PostgreSQLGenerator
from src.generators.java import JavaGenerator
from src.generators.rust import RustGenerator
from src.generators.typescript import TypeScriptGenerator
print("✅ All imports successful")
EOF

# Success!
```

**Document results**:
```markdown
# First Production PyPI Installation

**Date**: YYYY-MM-DD
**Platform**: [OS/version]

## Installation
- Time taken: ___ seconds
- Package size downloaded: ___ MB
- Dependencies installed: ___

## Verification
- [ ] CLI available
- [ ] Version correct
- [ ] Generation works
- [ ] Imports successful

## Issues
[None / List issues]

## Status
✅ SUCCESS - Package works perfectly!
```

---

## Day 3: Git Tagging & Release (8 hours)

### Task 3.1: Create Git Tag (2 hours)

```bash
cd ~/code/specql

# Ensure clean and up-to-date
git status  # Must be clean
git pull origin main

# Create annotated tag
git tag -a v0.4.0-alpha -m "Release v0.4.0-alpha - First Public Release

First public alpha release of SpecQL on PyPI.

Features:
- Multi-language code generation (PostgreSQL, Java, Rust, TypeScript)
- Reverse engineering for 5 languages
- FraiseQL integration
- Pattern library with 100+ patterns
- Interactive CLI with live preview
- Comprehensive documentation

Technical:
- 6,173 lines of code
- 96%+ test coverage
- 100x code leverage
- Published to PyPI: https://pypi.org/project/specql-generator/

Installation:
pip install specql-generator

Documentation:
https://github.com/fraiseql/specql/blob/main/docs/00_getting_started/README.md"

# Verify tag
git tag -l
git show v0.4.0-alpha

# Push tag
git push origin v0.4.0-alpha
```

### Task 3.2: Create GitHub Release (3 hours)

**Using GitHub CLI** (or web interface):

```bash
# Install gh if needed
# brew install gh (macOS)
# See: https://cli.github.com/

# Authenticate
gh auth login

# Create release
gh release create v0.4.0-alpha \
  --title "SpecQL v0.4.0-alpha - First Public Release 🎉" \
  --notes "# SpecQL v0.4.0-alpha - First Public Release

## 🎉 Now Available on PyPI!

\`\`\`bash
pip install specql-generator
\`\`\`

## What is SpecQL?

SpecQL generates production-ready backends from YAML specifications. Write your data model once, deploy across 4 languages.

**One YAML spec → PostgreSQL + Java + Rust + TypeScript** (100x code leverage)

## ✨ Features

### Multi-Language Code Generation
- **PostgreSQL**: Tables, indexes, PL/pgSQL functions (96% test coverage)
- **Java/Spring Boot**: JPA entities, repositories, services, controllers (97% coverage)
- **Rust/Diesel**: Models, schemas, queries, Actix-web handlers (100% pass rate)
- **TypeScript/Prisma**: Schema, interfaces, type-safe client (96% coverage)

### Reverse Engineering
- PostgreSQL → SpecQL
- Python → SpecQL
- Java → SpecQL
- Rust → SpecQL
- TypeScript → SpecQL

### Developer Tools
- Interactive CLI with live preview
- Pattern library (100+ reusable patterns)
- Visual schema diagrams
- CI/CD generation (GitHub Actions, GitLab CI, CircleCI, Jenkins, Azure)
- Infrastructure as Code (Terraform, Kubernetes, Docker Compose)
- Test generation (pgTAP, pytest)

### FraiseQL Integration
- Automatic GraphQL metadata
- Vector search support
- Auto-discovery for instant APIs

## 📚 Documentation

- **[Getting Started](https://github.com/fraiseql/specql/blob/main/docs/00_getting_started/README.md)**
- **[Quickstart Guide](https://github.com/fraiseql/specql/blob/main/docs/00_getting_started/QUICKSTART.md)** (10 minutes)
- **[Complete Tutorials](https://github.com/fraiseql/specql/blob/main/docs/01_tutorials/)**
- **[Examples](https://github.com/fraiseql/specql/blob/main/docs/06_examples/)**

## 📊 Stats

- **Lines of Code**: 6,173
- **Test Coverage**: 96%+
- **Code Leverage**: 100x (20 YAML → 2000+ code)
- **Performance**: Up to 37,233 entities/sec

## 🚀 Quick Example

\`\`\`yaml
# contact.yaml
entity: Contact
schema: crm

fields:
  email: text
  name: text
  company: ref(Company)
  status: enum(lead, qualified, customer)

actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
\`\`\`

\`\`\`bash
specql generate contact.yaml
\`\`\`

Generates 2000+ lines across 4 languages!

## 🐛 Known Issues

This is an alpha release. Please report issues:
https://github.com/fraiseql/specql/issues

## 🙏 Acknowledgments

Thank you to all contributors and early testers!

## 📝 Changelog

See [CHANGELOG.md](https://github.com/fraiseql/specql/blob/main/CHANGELOG.md) for full details.

---

**Installation**: \`pip install specql-generator\`
**PyPI**: https://pypi.org/project/specql-generator/
**Documentation**: https://github.com/fraiseql/specql/tree/main/docs
**Issues**: https://github.com/fraiseql/specql/issues
" \
  dist/specql_generator-0.4.0a0-py3-none-any.whl \
  dist/specql_generator-0.4.0a0.tar.gz
```

### Task 3.3: Update README Badges (1 hour)

**Update README.md** with real PyPI badge:

```markdown
# SpecQL - Multi-Language Backend Code Generator

[![PyPI version](https://badge.fury.io/py/specql-generator.svg)](https://pypi.org/project/specql-generator/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/specql-generator.svg)](https://pypi.org/project/specql-generator/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/specql-generator.svg)](https://pypistats.org/packages/specql-generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Rest of README...]
```

Commit and push:
```bash
git add README.md
git commit -m "docs: update badges for PyPI production release"
git push origin main
```

### Task 3.4: Post-Release Validation (2 hours)

**Final checks**:

```markdown
# Post-Release Validation

## PyPI
- [ ] Package visible: https://pypi.org/project/specql-generator/
- [ ] Version correct: 0.4.0a0
- [ ] Can install: `pip install specql-generator`
- [ ] All features work

## GitHub
- [ ] Release published: https://github.com/fraiseql/specql/releases/tag/v0.4.0-alpha
- [ ] Release notes complete
- [ ] Download links work
- [ ] Badge updated in README

## Git
- [ ] Tag pushed
- [ ] Latest commit tagged
- [ ] Clean git status

## Documentation
- [ ] Installation instructions mention PyPI
- [ ] Links all work
- [ ] Version numbers consistent
```

---

## Day 4-5: User Testing & Feedback (16 hours)

### Task 4.1: Internal Testing (4 hours)

**Have 2-3 colleagues test**:

```markdown
# Internal Tester Instructions

## Your Mission
Install and use SpecQL as if you've never seen it before.

## Tasks
1. Install from PyPI
2. Follow the Quickstart guide
3. Try to build something (Blog, CRM, or your idea)
4. Report ALL issues, confusions, bugs

## Feedback Form
- What was confusing?
- What didn't work?
- What was surprisingly good?
- What's missing?
- Would you use this? Why/why not?

## Time Tracking
- Installation: ___ minutes
- Quickstart: ___ minutes
- First project: ___ minutes
- Total: ___ minutes

## Report
[Detailed feedback here]
```

### Task 4.2: Create Feedback Tracking (2 hours)

Create: `docs/feedback/ALPHA_FEEDBACK.md`

```markdown
# v0.4.0-alpha Feedback Tracking

**Period**: YYYY-MM-DD onwards (First 30 days)

## Metrics

### PyPI Downloads
- Week 1: ___
- Week 2: ___
- Week 3: ___
- Week 4: ___

### GitHub
- Stars: ___
- Watchers: ___
- Forks: ___
- Issues opened: ___
- Pull requests: ___

## Feedback Summary

### Installation Issues
1. [Issue] - Reported by: ___ - Status: ___
2. [Issue] - Reported by: ___ - Status: ___

### Documentation Confusion
1. [What was unclear] - Fixed in: ___
2. [What was unclear] - Fixed in: ___

### Feature Requests
1. [Request] - Priority: ___ - Planned for: ___
2. [Request] - Priority: ___ - Planned for: ___

### Bugs
1. [Bug] - Severity: ___ - Fixed in: ___
2. [Bug] - Severity: ___ - Status: ___

## Quick Wins (Fix This Week)
- [ ] [Easy fix that helps users]
- [ ] [Documentation clarification]
- [ ] [Error message improvement]

## Planned for v0.4.1-alpha (Patch)
- [ ] [Critical bug fix]
- [ ] [Important improvement]

## Planned for v0.5.0-beta
- [ ] [Bigger feature]
- [ ] [Significant improvement]
```

### Task 4.3: Monitor PyPI Stats (2 hours)

**Set up monitoring**:

```bash
# Check downloads
# Via pypistats.org or:
pip install pypistats

# Get download stats
pypistats recent specql-generator

# Get detailed stats
pypistats python_minor specql-generator --last-month
```

**Create monitoring script**:

```python
# scripts/monitor_pypi.py
import pypistats
from datetime import datetime

def get_stats():
    package = "specql-generator"

    print(f"SpecQL PyPI Stats - {datetime.now()}")
    print("=" * 50)

    # Recent downloads
    recent = pypistats.recent(package, period="week")
    print(f"Downloads (last week): {recent}")

    # By Python version
    python_versions = pypistats.python_minor(package, total=True)
    print(f"\nBy Python version: {python_versions}")

if __name__ == "__main__":
    get_stats()
```

Run weekly to track adoption.

### Task 4.4: Community Outreach (4 hours)

**Soft launch** to friendly communities:

1. **Personal network**:
   - Email to colleagues
   - Share on LinkedIn
   - Share on Twitter/X

2. **Relevant communities** (gentle, not spammy):
   - Python community groups
   - PostgreSQL forums
   - Backend development communities

**Template message**:
```
Hi [community],

I just released the alpha of SpecQL, a tool I've been working on that generates multi-language backends from YAML.

The idea: Write your data model once, generate PostgreSQL + Java + Rust + TypeScript automatically.

Example: 20 lines of YAML → 2000+ lines of production code.

Now available on PyPI:
pip install specql-generator

Would love feedback from this community!

Docs: https://github.com/fraiseql/specql
PyPI: https://pypi.org/project/specql-generator/

Let me know what you think!
```

### Task 4.5: Address Quick Fixes (4 hours)

**Based on first feedback**:

```bash
# If critical issues found:

# 1. Fix the issue
# 2. Add test to prevent regression
# 3. Update version to 0.4.1-alpha
# 4. Rebuild and upload

# Example patch workflow:
git checkout -b fix/critical-issue-123

# Make fix
# Add test

uv run pytest  # Ensure all pass

# Update version in pyproject.toml
# version = "0.4.1-alpha"

# Update CHANGELOG.md
cat >> CHANGELOG.md << 'EOF'

## [0.4.1-alpha] - YYYY-MM-DD

### Fixed
- Critical issue #123: [description]
EOF

# Commit
git commit -am "fix: critical issue #123"

# Merge to main
git checkout main
git merge fix/critical-issue-123

# Tag and release
git tag -a v0.4.1-alpha -m "Hotfix release"
git push origin main --tags

# Build and upload
python -m build
twine upload dist/*
```

---

## Week 3 Deliverables

### Published
- [ ] Package live on PyPI
- [ ] GitHub release created
- [ ] Git tagged (v0.4.0-alpha)
- [ ] README badges updated

### Validated
- [ ] Production installation tested
- [ ] All features work from PyPI
- [ ] Cross-platform tested
- [ ] Performance benchmarked

### Feedback
- [ ] Internal testers completed
- [ ] Feedback tracking system in place
- [ ] Initial PyPI stats recorded
- [ ] Community outreach begun

### Quick Fixes
- [ ] Critical issues addressed
- [ ] Patch release (if needed)
- [ ] Documentation updated

---

## Success Criteria

**End of Week 3**:
- ✅ SpecQL is public and installable worldwide
- ✅ At least 10 PyPI downloads
- ✅ No critical bugs reported
- ✅ Feedback system working
- ✅ Ready for broader marketing (Week 5)

---

## Emergency Procedures

**If critical bug found**:
1. Create hotfix branch immediately
2. Fix + test
3. Release patch version (0.4.1-alpha)
4. Upload to PyPI
5. Update GitHub release

**If package needs to be yanked**:
```bash
# Last resort - removes version from PyPI
# (files remain for already installed users)
# DO NOT DO THIS unless absolutely necessary

pip install twine
twine upload --skip-existing dist/*
# Then go to PyPI web interface to yank
```

**Better**: Release fixed version quickly instead of yanking.

---

**Next Week**: [Week 4 - User Experience Polish](WEEK_04_USER_EXPERIENCE_POLISH.md)
