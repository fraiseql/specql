# Agent Prompt: Detail Weekly Implementation Plans

**Task**: Expand weekly implementation plans with comprehensive daily breakdowns, code examples, and success criteria.

**Context**: SpecQL has 50 weeks of implementation plans (Weeks 1-50). Weeks 1-24 (PrintOptim + Multi-Language Backend) and Weeks 25-30 (Frontend Core) have detailed plans. Weeks 31-36 have basic structure but need detailed daily breakdowns. Weeks 37-50 are placeholders.

**Your Mission**: Take a week number as input and create a comprehensive, production-ready implementation plan following the established pattern.

---

## 📋 Input Format

You will be given:
1. **Week Number**: (e.g., "Week 31", "Week 42")
2. **Week File**: Path to the existing week file (e.g., `WEEK_31.md`)
3. **Context**: Brief description of what this week should accomplish

---

## 📝 Output Requirements

Create a **comprehensive weekly plan** with the following structure:

### 1. Header Section
```markdown
# Week [N]: [Descriptive Title]

**Date**: TBD (After Week [N-1] complete)
**Duration**: 5-6 days
**Status**: 📅 Planned
**Objective**: [Clear, concise objective in 1-2 sentences]

**Prerequisites**: Week [N-1] complete ([what was accomplished])

**Output**:
- [Deliverable 1]
- [Deliverable 2]
- [Deliverable 3]
- [Deliverable 4]
- [Deliverable 5]
```

### 2. Executive Summary
```markdown
## 🎯 Executive Summary

[2-3 paragraphs explaining:]
- What this week accomplishes and why it matters
- How it builds on previous weeks
- Key technical decisions or approaches
- Expected impact/value

**Key Deliverables**:
1. [Major deliverable with brief explanation]
2. [Major deliverable with brief explanation]
3. [Major deliverable with brief explanation]

**Code Leverage**: [Input] → [Output] ([ratio])
```

### 3. Daily Breakdown

**CRITICAL**: Each day must have:
- **Morning Block (4 hours)**: Specific implementation task
- **Afternoon Block (4 hours)**: Specific implementation task
- **Actual code examples** (not TODOs or placeholders)
- **File paths** where code will be added

**Pattern**:
```markdown
## 📅 Daily Breakdown

### Day 1: [Focus Area]

**Morning Block (4 hours): [Specific Task]**

[Brief explanation of what and why]

**File**: `src/[path]/[filename].py`

```python
"""
[Docstring explaining purpose]
"""

[Complete, working code example - NOT pseudocode]
[Minimum 30-50 lines of actual implementation]
```

**Afternoon Block (4 hours): [Specific Task]**

[Same pattern - different file/feature]

---

### Day 2: [Focus Area]

[Same pattern for Days 2-6]
```

### 4. Success Criteria
```markdown
## ✅ Success Criteria

- [ ] [Specific, measurable criterion]
- [ ] [Specific, measurable criterion]
- [ ] [Must include test counts: "100+ unit tests passing"]
- [ ] [Must include coverage: ">95% coverage"]
- [ ] [Must include integration tests]
- [ ] [Must include performance benchmarks if applicable]
- [ ] [CLI commands functional]
- [ ] [Documentation complete]
```

### 5. Testing Strategy
```markdown
## 🧪 Testing Strategy

**Unit Tests**:
- [What to test - be specific]
- [Example test case with actual code]

**Integration Tests**:
- [What to test - be specific]
- [Example test case with actual code]

**Performance Tests** (if applicable):
- [Benchmarks with target metrics]

**Example Test**:
```python
def test_[specific_feature]():
    """[Test description]"""
    # Arrange
    [setup code]

    # Act
    [action code]

    # Assert
    [assertions with specific expected values]
```
```

### 6. Related Files
```markdown
## 🔗 Related Files

- **Previous**: [Week N-1](./WEEK_[N-1].md)
- **Next**: [Week N+1](./WEEK_[N+1].md)
- **Reference**: [Related documentation or previous weeks]

---

**Status**: 📅 Planned
**Complexity**: [Low/Medium/High] ([brief reason])
**Risk**: [Low/Medium/High] ([brief reason])
**Impact**: [What this enables]
```

---

## 🎯 Quality Standards

### Code Examples Must Be:
1. **Complete**: Not pseudocode or TODOs
2. **Realistic**: Actually implementable
3. **Consistent**: Follow SpecQL patterns from existing weeks
4. **Documented**: Docstrings, comments where needed
5. **Tested**: Include test examples

### Daily Tasks Must Be:
1. **Specific**: Not "implement feature X" but "implement X's Y using Z pattern"
2. **Sized Right**: 4 hours of focused work
3. **Sequential**: Day 2 builds on Day 1, etc.
4. **Practical**: Real developer workflow

### Writing Style:
1. **Technical**: Use precise terminology
2. **Clear**: Explain WHY, not just WHAT
3. **Actionable**: Developer can start coding immediately
4. **Consistent**: Match tone/style of Weeks 1-30

---

## 📚 Reference Examples

**Excellent Examples** (use these as templates):
- `WEEK_25.md` - Universal Component Grammar (comprehensive, detailed)
- `WEEK_26.md` - React Parser Foundation (good code examples)
- `WEEK_27.md` - React Code Generation (detailed generators)
- `WEEK_09.md` - Java AST Parser (good daily breakdown)

**Pattern to Follow**:
1. Day 1: Setup infrastructure
2. Day 2-3: Core implementation
3. Day 4: Integration/advanced features
4. Day 5: Testing, CLI, documentation

---

## 🔍 Context You Should Reference

### SpecQL Architecture
**Location**: `.claude/CLAUDE.md`
- Team-based architecture (Teams A-E)
- Trinity pattern (pk_*, id, identifier)
- FileSpec protocol
- Testing with `make test`

### Completed Work
**Location**: `docs/implementation_plans/complete_linear_plan/done/`
- Week 7-8: Python Reverse Engineering (reference for parser patterns)
- Week 12-14: Trinity Pattern (reference for schema patterns)
- Week 15-17: CI/CD (reference for code generation)
- Week 18-20: Infrastructure (reference for multi-provider support)

### Frontend Design
**Location**: `../specql_front/PRD.md`
- Complete YAML grammar specification
- Entity/Field/Page/Action types
- Reference for Weeks 25-36

### Project Constraints
- Python 3.11+
- Dataclasses for models
- Protocol classes for interfaces
- pytest for testing
- Type hints required
- Confiture CLI framework

---

## 🚫 What NOT to Do

❌ **Don't write placeholders**:
```python
# TODO: Implement this
def my_function():
    pass
```

✅ **DO write complete code**:
```python
def my_function(entity: str, fields: List[str]) -> str:
    """Generate SQL table from entity and fields."""
    field_defs = []
    for field in fields:
        field_defs.append(f"  {field} TEXT NOT NULL")

    return f"""
CREATE TABLE {entity} (
{chr(10).join(field_defs)}
);
"""
```

❌ **Don't be vague**:
"Implement parser for format X"

✅ **DO be specific**:
"Implement parser for Docker Compose YAML using PyYAML, extracting service definitions into ComposeService dataclass with fields for image, ports, volumes, and environment variables"

❌ **Don't skip testing**:
No test examples

✅ **DO include tests**:
Complete unit test with arrange/act/assert pattern

---

## 🎬 Execution Instructions

When given a week to detail:

1. **Read the existing week file** (if it exists)
2. **Read related context**:
   - Previous week (Week N-1)
   - Next week (Week N+1)
   - Reference implementations from done/
3. **Understand the objective** from the current basic outline
4. **Create comprehensive plan** following the template above
5. **Write actual code examples** (minimum 200 lines total across the week)
6. **Include tests** (minimum 2-3 complete test examples)
7. **Verify consistency** with existing weeks

---

## 📊 Example Input/Output

### Input
```
Week Number: 33
Week File: WEEK_33.md
Context: State Management & Data Fetching - TanStack Query, Apollo Client,
         framework-specific state solutions, optimistic updates, cache management
```

### Output Structure
```markdown
# Week 33: State Management & Data Fetching

[Complete 5-6 day plan with:]
- Executive summary explaining TanStack Query integration
- Day 1: TanStack Query setup + basic queries
  - Morning: Query hook generator (WITH ACTUAL CODE)
  - Afternoon: Pagination patterns (WITH ACTUAL CODE)
- Day 2: Mutations & optimistic updates
  - Morning: Mutation hook generator (WITH CODE)
  - Afternoon: Optimistic update patterns (WITH CODE)
- Day 3: Cache management
  - Morning: Cache invalidation strategies (WITH CODE)
  - Afternoon: Prefetching patterns (WITH CODE)
- Day 4: Real-time subscriptions
  - Morning: GraphQL subscriptions (WITH CODE)
  - Afternoon: WebSocket integration (WITH CODE)
- Day 5: Testing & documentation
  - Morning: Integration tests (WITH CODE)
  - Afternoon: CLI + docs

[Include 5+ complete code examples of 30-50 lines each]
[Include 3+ complete test examples]
[Include success criteria with metrics]
```

---

## ✅ Success Criteria for Your Output

Your detailed week plan is complete when:

- [ ] All 5-6 days have morning + afternoon blocks
- [ ] Every block has a specific file path and task
- [ ] Minimum 5 complete code examples (30+ lines each)
- [ ] Minimum 3 complete test examples
- [ ] Success criteria has 8+ measurable items
- [ ] Testing strategy has unit + integration examples
- [ ] Links to previous/next weeks are correct
- [ ] Code follows SpecQL patterns (dataclasses, protocols, type hints)
- [ ] A developer could start implementing immediately
- [ ] Total document is 400-600 lines

---

## 🎯 Your Task

**When invoked, you will**:

1. Receive a week number (e.g., "Week 33")
2. Read the existing week file
3. Read context from related weeks
4. Generate a comprehensive implementation plan
5. Output the complete markdown content
6. Verify it meets all quality standards above

**Start with**: "I'll create a comprehensive implementation plan for Week [N]..."

---

**Template Version**: 1.0
**Last Updated**: 2025-11-13
**Applies To**: Weeks 31-50 (detailed expansion needed)
**Pattern Source**: Weeks 25-30 (reference implementations)
