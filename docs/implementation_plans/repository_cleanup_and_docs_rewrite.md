# Agent Task: Repository Cleanup & Documentation Rewrite

**Priority**: MEDIUM
**Estimated Effort**: 3-4 hours
**Goal**: Clean repository root and rewrite docs to be developer-friendly

---

## 🎯 Objectives

### 1. Repository Root Cleanup
Clean up the root directory to follow professional open-source project standards:
- Remove unnecessary files
- Organize configuration files
- Ensure clean, minimal root structure
- Keep only essential project files

### 2. Documentation Rewrite
Transform marketing-heavy documentation into practical, developer-focused content:
- Remove hyperbole and marketing language
- Add concrete examples and code snippets
- Focus on "how-to" rather than "why amazing"
- Use clear, direct technical language
- Emphasize practical use cases over ambitious visions

---

## 📋 Task 1: Repository Root Cleanup

### Current State Analysis Required

**Step 1**: List all files in repository root
```bash
ls -la /home/lionel/code/specql/
```

**Step 2**: Identify files to keep, move, or remove

### Files to KEEP (Standard project files)
- `README.md` (will be rewritten)
- `LICENSE` or `LICENSE.md`
- `pyproject.toml`
- `Makefile`
- `.gitignore`
- `.python-version`
- `CHANGELOG.md`
- `CONTRIBUTING.md` (if exists)

### Files to MOVE (Organize into subdirectories)
- Marketing docs → `docs/archive/` or delete
- Design docs → `docs/architecture/`
- Planning docs → `docs/planning/`
- Meeting notes → `docs/notes/` or delete
- Old implementation plans → `docs/archive/`

### Files to DELETE (Remove clutter)
- Duplicate files
- Temporary files
- Draft versions (keep only final)
- Personal notes not relevant to contributors
- Old TODO lists
- Scratch files

### Expected Clean Root Structure
```
specql/
├── README.md                 # Clean, developer-focused
├── LICENSE                   # Project license
├── pyproject.toml           # Python project config
├── Makefile                 # Build/test commands
├── .gitignore              # Git ignore rules
├── .python-version         # Python version
├── CHANGELOG.md            # Version history
├── GETTING_STARTED.md      # Quick start guide
├── src/                    # Source code
├── tests/                  # Test suite
├── docs/                   # Documentation
├── registry/               # Domain registry
├── entities/               # Example entities
└── database/               # Analytics DB (if relevant)
```

---

## 📋 Task 2: Documentation Rewrite

### Files to Rewrite

#### **Priority 1: README.md** (Root)

**Current Issues to Fix**:
- Remove marketing language ("game-changing", "revolutionary", etc.)
- Remove excessive emojis
- Remove vision/ambition sections
- Focus on what it does NOW, not future potential
- Add quick install/usage
- Show real code examples

**New Structure**:
```markdown
# SpecQL

Business logic to production PostgreSQL + GraphQL generator.

## What It Does

SpecQL generates production-ready PostgreSQL schema and PL/pgSQL functions from YAML business logic definitions. Write business rules in 20 lines of YAML, get 2000+ lines of tested SQL.

## Quick Start

[Installation, basic example, key commands]

## Features

[Concrete list of what works now]

## Documentation

[Links to docs/]

## Status

[Current version, test coverage, what's stable]

## Contributing

[How to contribute]

## License

[License info]
```

---

#### **Priority 2: GETTING_STARTED.md**

**Current Issues**:
- May have too much context/motivation
- Focus on doing, not understanding philosophy

**New Structure**:
```markdown
# Getting Started with SpecQL

## Prerequisites
- Python 3.12+
- PostgreSQL 14+
- 15 minutes

## Installation

[Exact commands]

## Your First Entity

[5-minute tutorial with real code]

## Next Steps

[Links to specific guides]
```

---

#### **Priority 3: docs/architecture/*.md**

**Files to Review**:
- `SPECQL_BUSINESS_LOGIC_REFINED.md`
- `INTEGRATION_PROPOSAL.md`
- `ONE_FILE_PER_MUTATION_PATTERN.md`
- Any other architecture docs

**Changes Needed**:
- Remove sales pitch language
- Keep technical specifications
- Add concrete examples
- Remove future vision sections
- Focus on current implementation
- Use standard technical documentation tone

**Checklist for Each File**:
- [ ] Remove words like: "revolutionary", "game-changing", "breakthrough", "amazing"
- [ ] Remove excessive exclamation marks
- [ ] Replace "will" with "does" (focus on present capabilities)
- [ ] Add code examples for concepts
- [ ] Remove speculative features
- [ ] Use standard technical terms
- [ ] Keep tone neutral and informative

---

#### **Priority 4: docs/guides/*.md** (If they exist)

Transform any guides to be practical:
- Step-by-step instructions
- Copy-paste examples
- Common gotchas
- Troubleshooting sections

---

### Writing Style Guidelines

#### ❌ AVOID (Marketing tone):
```markdown
# 🚀 Revolutionary Business Logic Framework!

SpecQL is a **game-changing** approach to database development that will
**transform** how you build applications! With our **breakthrough** technology,
you can achieve **100x productivity gains**!!!

## The Vision

Imagine a world where...
```

#### ✅ USE (Developer tone):
```markdown
# SpecQL

Business logic to PostgreSQL generator.

SpecQL generates PostgreSQL schema and functions from YAML specifications.
Define entities, fields, and actions in YAML; get tested SQL output.

## Example

Input (YAML):
```yaml
entity: Contact
schema: crm
fields:
  email: text
  status: enum(lead, qualified)
```

Output: PostgreSQL table with Trinity pattern, indexes, audit fields, helper functions.
```

---

### Language Transformation Guide

| ❌ Marketing | ✅ Developer |
|-------------|-------------|
| "Revolutionary framework" | "Code generator" |
| "Game-changing technology" | "Tool for generating SQL" |
| "Transform your workflow!" | "Generates SQL from YAML" |
| "Imagine a world where..." | "Usage: specql generate ..." |
| "100x productivity gains!!!" | "Reduces boilerplate code" |
| "Breakthrough approach" | "Convention-based generator" |
| "Amazing features" | "Features:" (then list them) |
| "Will change everything" | "Currently supports:" |
| "The future of development" | "Status: Beta" |
| "Unlock potential" | "See examples/" |

---

## 📝 Detailed Task List

### Phase 1: Analysis (Read-Only)

```bash
# Analyze repository structure
ls -la
tree -L 2 -a

# List all markdown files
find . -name "*.md" -type f

# Review root directory contents
ls -lh *.md *.txt *.yml *.yaml 2>/dev/null

# Check for duplicate or unnecessary files
find . -maxdepth 1 -type f | sort
```

**Deliverable**: List of files to keep/move/delete

---

### Phase 2: Root Cleanup (Write Operations)

**Task 2.1**: Create archive directory
```bash
mkdir -p docs/archive
```

**Task 2.2**: Move non-essential docs
```bash
# Example (adjust based on what exists):
mv docs/VISION.md docs/archive/ 2>/dev/null
mv docs/ROADMAP.md docs/archive/ 2>/dev/null
mv docs/MARKETING_*.md docs/archive/ 2>/dev/null
```

**Task 2.3**: Remove temporary/duplicate files
```bash
# Examples (verify before deleting):
rm TODO.md 2>/dev/null
rm NOTES.md 2>/dev/null
rm *_OLD.md 2>/dev/null
rm *_BACKUP.md 2>/dev/null
```

**Task 2.4**: Organize remaining docs
- Ensure docs/ has clear structure
- Move architecture docs to docs/architecture/
- Move guides to docs/guides/
- Move plans to docs/implementation_plans/

---

### Phase 3: README Rewrite

**Task 3.1**: Read current README.md
```bash
cat README.md
```

**Task 3.2**: Identify marketing language
- Highlight claims without evidence
- Note excessive emojis
- Find future-tense promises
- Locate hyperbolic language

**Task 3.3**: Rewrite README.md

**Structure**:
```markdown
# SpecQL

[One-line description - what it does]

## Overview

[2-3 paragraphs: what it is, what problem it solves, how it works]

## Installation

```bash
# Exact commands
git clone https://github.com/fraiseql/specql.git
cd specql
uv sync
```

## Quick Example

```yaml
# Input: entities/contact.yaml
entity: Contact
schema: crm
fields:
  email: text
  company: ref(Company)
```

```bash
# Generate
specql generate entities/contact.yaml
```

```sql
-- Output: PostgreSQL table + functions (generated)
CREATE TABLE crm.tb_contact (
  pk_contact INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,
  email TEXT,
  fk_company INTEGER REFERENCES crm.tb_company(pk_company),
  created_at TIMESTAMP DEFAULT NOW(),
  ...
);
```

## Key Features

- **Convention-based**: Trinity pattern, audit fields, indexes generated automatically
- **Business logic**: Define actions in YAML, get PL/pgSQL functions
- **FraiseQL integration**: GraphQL metadata generation
- **Type-safe**: PostgreSQL composite types, TypeScript generation
- **Tested**: [X]% test coverage, [Y] passing tests

## Documentation

- [Getting Started](GETTING_STARTED.md)
- [Architecture](docs/architecture/)
- [API Reference](docs/api/)

## Project Status

- **Version**: 0.x.x (pre-release)
- **Tests**: [X] passing
- **Stability**: Beta - API may change

## Development

```bash
# Run tests
make test

# Run specific team tests
make teamA-test  # Parser
make teamB-test  # Schema
make teamC-test  # Actions

# Format code
make format
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

[License type]
```

---

### Phase 4: GETTING_STARTED Rewrite

**Task 4.1**: Read current GETTING_STARTED.md
**Task 4.2**: Remove philosophy/motivation sections
**Task 4.3**: Rewrite as step-by-step tutorial

**New Structure**:
```markdown
# Getting Started

## Prerequisites

- Python 3.12 or later
- PostgreSQL 14 or later (optional for testing)
- 15 minutes

## Installation

[Step by step]

## Create Your First Entity

### Step 1: Define Entity

Create `entities/task.yaml`:
```yaml
entity: Task
schema: projects
fields:
  title: text
  status: enum(todo, in_progress, done)
```

### Step 2: Generate Schema

```bash
specql generate entities/task.yaml
```

### Step 3: Review Output

Output is written to `db/schema/`:
- `10_tables/task.sql` - Table definition
- `20_helpers/task_helpers.sql` - Helper functions

### Step 4: Apply to Database

```bash
psql -d your_db -f db/schema/10_tables/task.sql
psql -d your_db -f db/schema/20_helpers/task_helpers.sql
```

## Add an Action

[Next tutorial step]

## Next Steps

- [Define complex fields](docs/guides/field_types.md)
- [Write business actions](docs/guides/actions.md)
- [Understand Trinity pattern](docs/architecture/trinity_pattern.md)
```

---

### Phase 5: Architecture Docs Review

**For each file in `docs/architecture/`**:

**Task 5.1**: Read file
**Task 5.2**: Create rewrite checklist:
- [ ] Replace marketing language with technical terms
- [ ] Remove future-tense claims
- [ ] Add concrete examples
- [ ] Remove excessive formatting (too many emojis/headers)
- [ ] Focus on current implementation
- [ ] Add code snippets
- [ ] Use standard documentation structure

**Task 5.3**: Rewrite file following checklist

**Standard Architecture Doc Structure**:
```markdown
# [Feature Name]

## Overview

[What this is - 2 sentences]

## Implementation

[How it works technically]

## Example

```yaml
# Input
[Example YAML]
```

```sql
-- Output
[Generated SQL]
```

## Configuration

[Options, if any]

## See Also

[Related docs]
```

---

### Phase 6: Cleanup Passes

**Task 6.1**: Global search and replace
```bash
# Find marketing terms
grep -r "revolutionary\|game-changing\|amazing\|breakthrough" docs/

# Find excessive exclamation marks
grep -r "!!!" docs/

# Find "imagine" statements
grep -r "Imagine" docs/
```

**Task 6.2**: Emoji audit
- Keep emojis only in lists/checklists (✅, ❌, 📝, etc.)
- Remove decorative emojis from headers
- Remove emoji overuse (more than 2-3 per section)

**Task 6.3**: Consistency check
- Consistent terminology
- Consistent code formatting
- Consistent header levels
- Consistent example style

---

## ✅ Success Criteria

### Repository Root
- [ ] Root directory has < 15 files
- [ ] All essential config files present
- [ ] No temporary/draft files
- [ ] Clean `ls` output
- [ ] Well-organized docs/ subdirectory

### README.md
- [ ] No marketing language
- [ ] Shows real code example in first screen
- [ ] Installation instructions work
- [ ] Links to all major docs
- [ ] Includes project status
- [ ] Professional, neutral tone

### GETTING_STARTED.md
- [ ] Step-by-step tutorial format
- [ ] Working code examples
- [ ] Takes < 15 minutes to complete
- [ ] No philosophy/vision sections
- [ ] Clear next steps

### Architecture Docs
- [ ] Technical, not promotional
- [ ] Concrete examples in each doc
- [ ] Present tense ("does" not "will")
- [ ] Standard documentation structure
- [ ] Code snippets included
- [ ] Neutral tone throughout

### Overall Quality
- [ ] Consistent terminology
- [ ] Professional appearance
- [ ] Easy to scan/read
- [ ] Practical focus
- [ ] Developer-friendly
- [ ] No hyperbole

---

## 🚨 Important Guidelines

### DO:
- ✅ Keep technical accuracy
- ✅ Add working code examples
- ✅ Use clear, direct language
- ✅ Focus on current capabilities
- ✅ Be honest about project status
- ✅ Make docs scannable
- ✅ Use standard open-source patterns

### DON'T:
- ❌ Remove important technical content
- ❌ Delete attribution/credits
- ❌ Change code/examples that work
- ❌ Remove necessary architecture explanations
- ❌ Over-simplify complex concepts
- ❌ Delete version history/changelog

---

## 📊 Deliverables

### 1. Analysis Report
```markdown
# Repository Cleanup Analysis

## Current State
- [X] files in root
- [Y] markdown docs
- [Z] MB total size

## Files to Move
- file1.md → docs/archive/
- file2.md → docs/architecture/

## Files to Delete
- temp.md (duplicate)
- old_notes.txt (outdated)

## Files to Rewrite
- README.md (heavy marketing)
- GETTING_STARTED.md (too much context)
- docs/architecture/X.md (hyperbolic)
```

### 2. Updated Files
- Clean root directory
- Rewritten README.md
- Rewritten GETTING_STARTED.md
- Rewritten architecture docs

### 3. Summary Report
```markdown
# Cleanup & Rewrite Summary

## Changes Made

### Root Directory
- Moved X files to docs/archive/
- Deleted Y temporary files
- Organized Z configuration files

### Documentation
- Rewrote README.md (removed 80% marketing language)
- Rewrote GETTING_STARTED.md (tutorial format)
- Updated N architecture docs (neutral tone)

### Before/After Metrics
- Root files: 47 → 12
- Marketing terms: 156 → 0
- Code examples: 3 → 15
- Docs readability: ↑

## Recommendations
[Any follow-up suggestions]
```

---

## 🎯 Example Transformations

### README - Before/After

**Before**:
```markdown
# 🚀 SpecQL - The Revolutionary Business Logic Framework!!!

## Transform Your Development Forever!

SpecQL is a **game-changing breakthrough** that will revolutionize how you
build applications! Imagine a world where you write business logic in simple
YAML and get production-ready code automatically!

### 🌟 Amazing Features
- 100x productivity gains!!!
- Revolutionary approach
- The future of development
```

**After**:
```markdown
# SpecQL

Business logic to PostgreSQL generator.

## Overview

SpecQL generates PostgreSQL schema and PL/pgSQL functions from YAML
business logic definitions. Define entities, fields, and actions in YAML;
get tested SQL output.

## Features

- Convention-based schema generation (Trinity pattern)
- Business action compilation (YAML to PL/pgSQL)
- FraiseQL metadata generation
- Type-safe PostgreSQL composite types
```

---

## 🧪 Testing Your Changes

### Before Committing:

1. **Test all links**:
```bash
# Check for broken internal links
find docs -name "*.md" -exec grep -H "\[.*\](.*.md)" {} \;
```

2. **Verify examples work**:
```bash
# Try the quick start yourself
[Run the commands from README]
```

3. **Check formatting**:
```bash
# Ensure markdown is valid
make lint-docs  # If available
```

4. **Review diff**:
```bash
git diff
git status
```

---

## 📝 Commit Strategy

Make focused commits for reviewability:

```bash
# Commit 1: Root cleanup
git add .
git commit -m "chore: Clean up repository root directory

- Move marketing docs to docs/archive/
- Remove temporary files
- Organize configuration files
- Clean root has 12 files (was 47)"

# Commit 2: README rewrite
git add README.md
git commit -m "docs: Rewrite README with developer-focused tone

- Remove marketing language
- Add practical code examples
- Include installation instructions
- Update project status section"

# Commit 3: Getting Started rewrite
git add GETTING_STARTED.md
git commit -m "docs: Rewrite Getting Started as step-by-step tutorial

- Remove philosophy sections
- Add working code examples
- Focus on practical usage
- 15-minute quick start"

# Commit 4: Architecture docs
git add docs/architecture/
git commit -m "docs: Update architecture docs with technical focus

- Remove promotional language
- Add concrete code examples
- Use present tense
- Neutral, professional tone"
```

---

## 🎓 Agent Execution Notes

This task requires:
- **Reading many files** - Use Read tool extensively
- **Writing new content** - Use Write/Edit tools
- **Moving files** - Use Bash for file operations
- **Careful judgment** - Don't delete important content

**Approach**:
1. Start with analysis (Phase 1)
2. Get approval on what to delete/move
3. Execute cleanup (Phase 2)
4. Rewrite docs one at a time (Phases 3-5)
5. Final consistency pass (Phase 6)

**Estimated Time**: 3-4 hours

---

**Last Updated**: 2025-11-10
**Agent Type**: General-purpose (requires file operations, reading, writing)
**Complexity**: Medium (requires judgment calls on content)
