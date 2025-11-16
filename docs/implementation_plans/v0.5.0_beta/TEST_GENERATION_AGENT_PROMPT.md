# Agent Prompt: Test Generation Features Implementation Plan

## Task Overview

You are tasked with creating a **comprehensive, phased implementation plan** to complete SpecQL's test generation and reverse-engineering features. The implementation code already exists (~1,437 lines) but needs CLI integration, documentation, testing, and marketing.

---

## Context

### What You Have Available

1. **Assessment Document**: Read `TEST_GENERATION_FEATURES_ASSESSMENT.md` in this directory for complete analysis
2. **Existing Code**: Review these files to understand what's already implemented:
   - `src/testing/pgtap/pgtap_generator.py` (305 lines)
   - `src/testing/pytest/pytest_generator.py` (257 lines)
   - `src/reverse_engineering/tests/pgtap_test_parser.py` (352 lines)
   - `src/reverse_engineering/tests/pytest_test_parser.py` (513 lines)
   - `src/testing/spec/spec_models.py` (370 lines)
   - `src/cli/reverse_tests.py` (400 lines - currently broken)

3. **Development Methodology**: Read `/home/lionel/.claude/CLAUDE.md` for:
   - Phased TDD approach (RED → GREEN → REFACTOR → QA)
   - Task complexity assessment
   - Quality gates

4. **Project Context**:
   - Current version: v0.4.0-alpha
   - Test suite: 2,937 tests passing
   - Coverage requirement: >90%
   - Language: Python 3.11+

---

## Your Deliverable

Create a detailed implementation plan document named: **`TEST_GENERATION_IMPLEMENTATION_PLAN.md`**

The plan should be structured as follows:

---

## Required Document Structure

### 1. Executive Summary

**Include**:
- Goal: Complete test generation features (from 40% → 100%)
- Estimated total time: 12-17 hours
- Success criteria
- Business value/ROI
- Risk assessment

### 2. Phases Overview

Create **4 phases** based on priorities from the assessment:

```
Phase 1: Make Features Discoverable (4-6 hours) - CRITICAL
Phase 2: Comprehensive Documentation (3-4 hours) - HIGH
Phase 3: Test Coverage (4-5 hours) - HIGH
Phase 4: Marketing Integration (1-2 hours) - MEDIUM
```

Each phase should be a complete mini-project that delivers value.

### 3. Phase 1: Make Features Discoverable

**Goal**: Users can find and use test generation features

#### Required Tasks

**Task 1.1: Fix `reverse-tests` Command** (1 hour)
- **Objective**: Make `specql reverse-tests` work without errors
- **Current Issue**: Command registered but exits with code 1
- **TDD Cycle**:
  - RED: Write test that runs `specql reverse-tests test.sql --preview`
  - GREEN: Debug and fix the error (likely import/path issue)
  - REFACTOR: Clean up error handling
  - QA: Test with pgTAP and pytest files

**Provide**:
- Step-by-step debugging approach
- Code changes needed (with file paths and line numbers)
- Test code to verify fix
- Success criteria

**Task 1.2: Create `generate-tests` CLI Command** (2-3 hours)
- **Objective**: Add new command to generate tests from entities
- **Current State**: Generators exist but no CLI command
- **TDD Cycle**:
  - RED: Write failing test for command
  - GREEN: Implement minimal command
  - REFACTOR: Add options and help text
  - QA: Verify with multiple entity types

**Provide**:
- Complete code for new command in `src/cli/generate_tests.py`
- Integration into `src/cli/confiture_extensions.py`
- Test suite for the command
- Examples of usage

**Task 1.3: Update CLI Help Text** (30 min)
- **Objective**: Make commands visible in `specql --help`
- **Changes**:
  - Update main CLI docstring
  - Register commands properly
  - Add command descriptions

**Provide**:
- Exact text for help strings
- Code changes needed

**Task 1.4: Update README.md** (1 hour)
- **Objective**: Document test features in main README
- **Sections to add**:
  - "Automated Testing" section
  - Quick examples
  - Links to detailed guides

**Provide**:
- Markdown text to add
- Location in README (after which section)
- Example commands

**Phase 1 Deliverables**:
- [ ] `specql reverse-tests` works without errors
- [ ] `specql generate-tests` command exists and works
- [ ] Both commands in `specql --help`
- [ ] README documents test features
- [ ] All changes committed with proper commit message

### 4. Phase 2: Comprehensive Documentation

**Goal**: Complete user-facing documentation for test features

#### Required Tasks

**Task 2.1: Create Test Generation Guide** (2 hours)
- **File**: `docs/02_guides/TEST_GENERATION.md`
- **Required Sections**:
  1. Overview - What is automatic test generation?
  2. Why Generate Tests - Benefits and use cases
  3. Quick Start - Basic usage examples
  4. Generated Test Types - pgTAP vs pytest
  5. Customizing Tests - How to modify generated tests
  6. CI/CD Integration - GitHub Actions examples
  7. Advanced Usage - Options and flags
  8. Troubleshooting - Common issues
  9. Examples - Real-world scenarios

**Provide**:
- Complete markdown document
- Code examples for each section
- Screenshots/diagrams if applicable

**Task 2.2: Create Test Reverse Engineering Guide** (1 hour)
- **File**: `docs/02_guides/TEST_REVERSE_ENGINEERING.md`
- **Required Sections**:
  1. Overview - What is test reverse engineering?
  2. Why Reverse Engineer Tests - Use cases
  3. Supported Frameworks - pgTAP, pytest
  4. TestSpec Format - Universal test specification
  5. Coverage Analysis - Finding gaps
  6. Examples - Converting tests
  7. Advanced Features - Customization

**Provide**:
- Complete markdown document
- Example TestSpec YAML
- Coverage analysis output example

**Task 2.3: Add Examples to docs/06_examples/** (1 hour)
- **Directory**: `docs/06_examples/simple_contact/generated_tests/`
- **Required Files**:
  - `test_contact_structure.sql` - pgTAP structure tests
  - `test_contact_crud.sql` - pgTAP CRUD tests
  - `test_contact_actions.sql` - pgTAP action tests
  - `test_contact_integration.py` - pytest integration tests
  - `test_spec.yaml` - Example TestSpec
  - `README.md` - Explains the examples

**Provide**:
- Complete example files
- README explaining each file
- How to run the tests

**Phase 2 Deliverables**:
- [ ] Complete TEST_GENERATION.md guide
- [ ] Complete TEST_REVERSE_ENGINEERING.md guide
- [ ] Example generated tests in docs/
- [ ] Links added to main documentation index
- [ ] All changes committed

### 5. Phase 3: Test Coverage

**Goal**: Achieve >90% test coverage for test generation features

#### Required Tasks

**Task 3.1: Test pgTAP Generator** (1.5 hours)
- **File**: `tests/testing/test_pgtap_generator.py`
- **Test Coverage Required**:
  - `generate_structure_tests()` - 5+ test cases
  - `generate_crud_tests()` - 6+ test cases
  - `generate_constraint_tests()` - 4+ test cases
  - `generate_action_tests()` - 4+ test cases

**Provide**:
- Complete test file with TDD approach
- Each method follows RED → GREEN → REFACTOR → QA
- Mock strategies for complex dependencies
- Assertions validating generated SQL quality

**Task 3.2: Test pytest Generator** (1.5 hours)
- **File**: `tests/testing/test_pytest_generator.py`
- **Test Coverage Required**:
  - `generate_pytest_integration_tests()` - 5+ test cases
  - Helper methods - 3+ test cases
  - Error handling - 3+ test cases

**Provide**:
- Complete test file
- Validation of generated Python code syntax
- Testing different entity configurations

**Task 3.3: Test Parsers** (1.5 hours)
- **Files**:
  - `tests/reverse_engineering/test_pgtap_parser.py`
  - `tests/reverse_engineering/test_pytest_parser.py`
- **Test Coverage Required**:
  - Parse valid test files - 4+ cases per parser
  - Extract assertions correctly - 3+ cases
  - Extract fixtures - 2+ cases
  - Handle malformed input - 2+ error cases

**Provide**:
- Complete test files
- Sample test input files
- Assertion validation

**Task 3.4: CLI Integration Tests** (30 min)
- **File**: `tests/cli/test_generate_tests_command.py`
- **Test Coverage Required**:
  - Command runs successfully - 2+ cases
  - Options work correctly - 3+ cases
  - Error handling - 2+ cases

**Provide**:
- End-to-end CLI tests
- Temporary file handling
- Output validation

**Phase 3 Deliverables**:
- [ ] All test files created
- [ ] Coverage >90% for test generation code
- [ ] All tests passing in CI
- [ ] Coverage report included
- [ ] All changes committed

### 6. Phase 4: Marketing Integration

**Goal**: Promote test generation as a key differentiator

#### Required Tasks

**Task 4.1: Update Blog Post** (30 min)
- **File**: `docs/blog/INTRODUCING_SPECQL.md`
- **Add Section**: "Automatic Test Generation"
- **Content**:
  - Highlight as unique feature
  - Show example: 1 entity → 70+ tests
  - Compare with competitors (they don't have this)

**Provide**:
- Markdown text to insert
- Location in blog post
- Example showing test generation

**Task 4.2: Update Social Media Content** (30 min)
- **File**: `docs/marketing/SOCIAL_MEDIA_CONTENT.md`
- **Add**:
  - Tweet about test generation
  - LinkedIn post highlighting testing
  - Reddit post for r/PostgreSQL (pgTAP tests)

**Provide**:
- Complete social media posts
- Hashtags
- Timing recommendations

**Task 4.3: Update Comparison Docs** (30 min)
- **File**: `docs/comparisons/SPECQL_VS_ALTERNATIVES.md`
- **Add Row**: Test Generation comparison
- **Update**:
  - SpecQL: ✅ pgTAP + pytest
  - Prisma: ❌ None
  - Hasura: ❌ None
  - PostgREST: ❌ None

**Provide**:
- Updated comparison table
- Text explaining the advantage

**Phase 4 Deliverables**:
- [ ] Blog post updated
- [ ] Social media content prepared
- [ ] Comparison docs updated
- [ ] Feature highlighted as differentiator
- [ ] All changes committed

---

## 7. Implementation Guidelines

### Code Quality Requirements

1. **Follow TDD Methodology**:
   - Every feature must have RED → GREEN → REFACTOR → QA cycle documented
   - Write tests BEFORE implementation
   - No code without tests

2. **Code Standards**:
   - Python 3.11+ type hints
   - Docstrings for all public functions
   - Follow project conventions (check existing files)
   - Pass `ruff check` and `mypy` validation

3. **Testing Standards**:
   - Coverage >90% for new code
   - Use pytest fixtures for setup
   - Clear test names: `test_<what>_<scenario>_<expected>`
   - Include both happy path and error cases

4. **Documentation Standards**:
   - Clear headings and structure
   - Code examples that work (copy-paste ready)
   - Links to related documentation
   - Troubleshooting sections

### Git Commit Guidelines

**Phase Commits**: One commit per phase

```bash
# Phase 1 commit
git commit -m "feat: make test generation features discoverable

- Fix reverse-tests command (exit code 1 → success)
- Add generate-tests CLI command with full options
- Update specql --help to show test commands
- Document test features in README

Commands now working:
  specql generate-tests entities/contact.yaml
  specql reverse-tests test.sql --analyze-coverage

Related: TEST_GENERATION_IMPLEMENTATION_PLAN.md Phase 1"

# Phase 2 commit
git commit -m "docs: comprehensive test generation documentation

- Add docs/02_guides/TEST_GENERATION.md (2000+ words)
- Add docs/02_guides/TEST_REVERSE_ENGINEERING.md (1500+ words)
- Add example generated tests to docs/06_examples/
- Link from main documentation index

Users can now:
  - Understand test generation features
  - Follow step-by-step guides
  - See real examples

Related: TEST_GENERATION_IMPLEMENTATION_PLAN.md Phase 2"

# Phase 3 commit
git commit -m "test: comprehensive test coverage for test generation

- Add tests/testing/test_pgtap_generator.py (150+ lines)
- Add tests/testing/test_pytest_generator.py (130+ lines)
- Add tests/reverse_engineering/test_pgtap_parser.py (120+ lines)
- Add tests/reverse_engineering/test_pytest_parser.py (140+ lines)
- Add tests/cli/test_generate_tests_command.py (80+ lines)

Coverage: 95% for test generation code
All 2,937 + 50 new tests passing

Related: TEST_GENERATION_IMPLEMENTATION_PLAN.md Phase 3"

# Phase 4 commit
git commit -m "docs: market test generation as key differentiator

- Update blog post with test generation section
- Add social media content highlighting testing
- Update comparison docs (SpecQL ✅, competitors ❌)
- Position as unique feature

Test generation is now:
  - Documented
  - Tested
  - Marketed
  - Ready for launch

Related: TEST_GENERATION_IMPLEMENTATION_PLAN.md Phase 4
Closes: TEST_GENERATION_FEATURES_ASSESSMENT.md"
```

---

## 8. Success Criteria

At completion, verify:

### Functionality
- [ ] `specql generate-tests entities/*.yaml` generates pgTAP tests
- [ ] `specql generate-tests entities/*.yaml --type pytest` generates pytest tests
- [ ] `specql reverse-tests test.sql` parses pgTAP tests without errors
- [ ] `specql reverse-tests test.py` parses pytest tests without errors
- [ ] Both commands appear in `specql --help`

### Quality
- [ ] All existing tests still pass (2,937 tests)
- [ ] New tests added and passing (50+ tests)
- [ ] Coverage >90% for test generation code
- [ ] `ruff check` passes (no linting errors)
- [ ] `mypy` validation passes (no type errors)

### Documentation
- [ ] README mentions test generation
- [ ] Complete guides in docs/02_guides/
- [ ] Examples in docs/06_examples/
- [ ] All links work
- [ ] No typos or formatting issues

### Marketing
- [ ] Blog post highlights test generation
- [ ] Social media content prepared
- [ ] Comparison docs updated
- [ ] Feature positioned as differentiator

### Git
- [ ] 4 commits (one per phase)
- [ ] Commit messages follow template
- [ ] All changes pushed to remote
- [ ] No uncommitted changes

---

## 9. Specific Requirements for the Agent

### Research Phase (Before Writing Plan)

1. **Read the Assessment**: Thoroughly read `TEST_GENERATION_FEATURES_ASSESSMENT.md`
2. **Examine Code**: Review all files listed in "Context" section
3. **Check Methodology**: Read `/home/lionel/.claude/CLAUDE.md` for TDD approach
4. **Understand Project**: Review `README.md` and `pyproject.toml`

### Plan Structure Requirements

1. **Be Extremely Detailed**:
   - Don't say "add tests" - specify exact test names and what they test
   - Don't say "update docs" - provide the exact markdown text
   - Don't say "fix bug" - provide debugging steps and code changes

2. **Provide Complete Code Examples**:
   - Full function implementations (not pseudocode)
   - Complete test files (not just outlines)
   - Exact markdown text (copy-paste ready)
   - Specific file paths and line numbers

3. **Follow TDD Strictly**:
   - Every task must show RED → GREEN → REFACTOR → QA cycle
   - Tests written BEFORE implementation
   - Clear success criteria for each cycle

4. **Include Time Estimates**:
   - Break tasks into 30-min to 3-hour chunks
   - Provide cumulative time for each phase
   - Total should be 12-17 hours

5. **Show Dependencies**:
   - Which tasks must be done in order
   - Which can be parallelized
   - Prerequisites for each task

### Document Formatting

- Use clear markdown headings (## Phase, ### Task)
- Include code blocks with language tags (```python, ```bash, ```markdown)
- Use checklists for deliverables (- [ ] item)
- Include tables for comparisons
- Add diagrams/flowcharts if helpful (mermaid or ASCII)

### Tone and Style

- **Actionable**: Every sentence should be a step someone can execute
- **Specific**: No vague instructions ("improve", "enhance", "update")
- **Complete**: Don't reference external docs - include everything needed
- **Professional**: This is a production implementation plan

---

## 10. Output Format

Your output should be a single markdown file with this structure:

```markdown
# Test Generation Features - Implementation Plan

**Goal**: Complete test generation features (40% → 100%)
**Estimated Time**: 12-17 hours
**Target Completion**: [Date]

## Executive Summary
[2-3 paragraphs with goal, value, risks]

## Phases Overview
[Table showing 4 phases with time estimates]

## Phase 1: Make Features Discoverable (4-6 hours)
### Overview
### Task 1.1: Fix reverse-tests Command (1 hour)
#### Objective
#### Current Issue
#### TDD Cycle
##### RED: Write Failing Test
[Complete code]
##### GREEN: Fix Implementation
[Complete code with explanations]
##### REFACTOR: Improve Code
[Complete code]
##### QA: Verify Quality
[Verification steps]
#### Success Criteria
#### Deliverables

[Continue for all tasks in Phase 1]

### Phase 1 Commit
[Complete commit message with code changes summary]

## Phase 2: Comprehensive Documentation (3-4 hours)
[Same detailed structure]

## Phase 3: Test Coverage (4-5 hours)
[Same detailed structure]

## Phase 4: Marketing Integration (1-2 hours)
[Same detailed structure]

## Implementation Timeline
[Gantt chart or timeline showing task dependencies]

## Risk Assessment
[Potential issues and mitigation strategies]

## Success Validation
[Complete checklist to verify completion]

## Appendix
### A: File Changes Summary
[Table of all files to be created/modified]

### B: Testing Strategy
[How to validate the implementation]

### C: Rollback Plan
[What to do if something goes wrong]
```

---

## 11. Key Points to Remember

1. **This is NOT research** - The code exists, we're completing the feature
2. **This is NOT design** - Architecture is done, we're implementing the interface
3. **This IS integration** - Connect existing code to CLI, docs, tests, marketing
4. **Quality over speed** - Better to have detailed, correct plan than fast, vague one
5. **Think like a user** - How will someone discover and use these features?

---

## 12. Questions to Answer in Your Plan

For each phase, address:

1. **What** exactly needs to be built/written/fixed?
2. **Why** is this important for the feature?
3. **How** will it be implemented (specific code)?
4. **When** should this be done (dependencies)?
5. **Who** will use this (user perspective)?
6. **Where** does it fit in the codebase/docs?
7. **How long** will it take (realistic estimate)?
8. **What could go wrong** and how to handle it?

---

## 13. Final Checklist for Your Plan

Before submitting, verify your plan includes:

- [ ] Executive summary with clear goal and value
- [ ] 4 phases with detailed tasks
- [ ] Complete code examples (not pseudocode)
- [ ] TDD cycles for all implementation tasks
- [ ] Test specifications for all new code
- [ ] Documentation content (actual markdown text)
- [ ] Commit messages for each phase
- [ ] Success criteria and validation steps
- [ ] Time estimates (12-17 hours total)
- [ ] Risk assessment and mitigation
- [ ] File changes summary
- [ ] Timeline/dependencies diagram
- [ ] Rollback plan

---

## Start Your Work

Begin by:

1. Reading `TEST_GENERATION_FEATURES_ASSESSMENT.md` completely
2. Reviewing the existing code files listed
3. Understanding the TDD methodology in `CLAUDE.md`
4. Creating a detailed, actionable implementation plan

**Remember**: The goal is to create a plan so detailed that someone could follow it step-by-step without making any decisions. Every question should be answered, every code snippet provided, every test specified.

Good luck! 🚀
