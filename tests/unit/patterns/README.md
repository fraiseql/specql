# Pattern Testing Strategy

## Overview
This directory contains comprehensive tests for SpecQL patterns. Each pattern gets a dedicated test module with multiple test categories to ensure robust functionality.

## Test Structure

Each pattern gets a dedicated test module with:
1. **Schema Tests** (5-8 tests): Verify DDL generation
2. **Validation Tests** (5-8 tests): Verify runtime behavior
3. **Integration Tests** (5-8 tests): Verify with actions/entities
4. **Edge Case Tests** (3-5 tests): Verify error handling

## Test Template

```python
import pytest
from src.core.parser import SpecQLParser
from src.generators.schema.schema_orchestrator import SchemaOrchestrator

class TestPatternName:
    """Test suite for pattern_name pattern."""

    @pytest.fixture
    def entity_yaml(self):
        """Base entity with pattern."""
        return '''
entity: TestEntity
schema: test
fields:
  field1: text
patterns:
  - type: pattern_name
    params:
      param1: value1
'''

    # Schema Generation Tests
    def test_schema_extension_applied(self, entity_yaml):
        """Verify pattern adds schema extensions."""
        pass

    def test_indexes_generated(self, entity_yaml):
        """Verify pattern adds required indexes."""
        pass

    # ... more tests
```

## Pattern Test Matrix

| Pattern | Schema Tests | Validation Tests | Integration Tests | Total |
|---------|--------------|------------------|-------------------|-------|
| non_overlapping_daterange | 8 | 5 | 7 | 20 |
| recursive_dependency_validator | 6 | 10 | 8 | 24 |
| aggregate_view | 8 | 5 | 7 | 20 |
| scd_type2_helper | 6 | 6 | 6 | 18 |
| template_inheritance | 5 | 5 | 6 | 16 |
| computed_column | 6 | 4 | 4 | 14 |
| **Total** | **39** | **35** | **38** | **112** |

## Test Categories

### Schema Generation Tests
- Verify DDL extensions (computed columns, indexes, constraints)
- Test parameter validation
- Check generated function signatures
- Validate schema comments and metadata

### Validation Tests
- Test runtime validation logic
- Verify error messages and codes
- Check constraint enforcement
- Test edge cases and boundary conditions

### Integration Tests
- Test with complete entity definitions
- Verify action compilation
- Check GraphQL generation
- Test with multiple patterns combined

### Edge Case Tests
- Invalid parameters
- Missing required fields
- Circular dependencies
- Performance with large datasets

## Test Fixtures

### Shared Fixtures (`conftest.py`)
- `schema_registry`: Pre-configured SchemaRegistry
- `table_generator`: Pre-configured TableGenerator
- `function_generator`: Pre-configured FunctionGenerator
- `test_db`: Database connection for integration tests

### Pattern-Specific Fixtures
- Base entity YAML with pattern applied
- Valid/invalid parameter combinations
- Test data sets for validation

## Running Tests

```bash
# All pattern tests
uv run pytest tests/unit/patterns/

# Specific pattern
uv run pytest tests/unit/patterns/temporal/test_non_overlapping_daterange.py

# With coverage
uv run pytest tests/unit/patterns/ --cov=src --cov-report=html

# Skip optional dependencies
uv run pytest tests/unit/patterns/ -m "not requires_pglast"
```

## Test Organization

```
tests/unit/patterns/
├── README.md                           # This file
├── conftest.py                         # Shared fixtures
├── temporal/
│   ├── test_non_overlapping_daterange.py
│   └── test_scd_type2_helper.py
├── validation/
│   ├── test_recursive_dependency_validator.py
│   └── test_template_inheritance_validator.py
├── schema/
│   ├── test_aggregate_view.py
│   └── test_computed_column.py
└── integration/
    └── test_pattern_combinations.py
```

## Success Criteria

- [ ] All 112 pattern tests implemented
- [ ] 95%+ test coverage for pattern code
- [ ] All tests pass with and without optional dependencies
- [ ] Clear error messages for invalid configurations
- [ ] Performance benchmarks for large datasets
- [ ] Integration tests with full entity lifecycles

## Implementation Notes

### TDD Approach
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor and optimize
4. Add edge case tests

### Dependency Handling
- Tests automatically skip if optional dependencies unavailable
- Clear markers indicate which dependencies required
- Graceful degradation for missing features

### Performance Testing
- Benchmark tests for large datasets
- Memory usage validation
- Query performance validation

### Documentation
- Each test documents expected behavior
- Examples in docstrings
- Links to pattern specifications</content>
</xai:function_call">Now let me create the test file structure as specified in the guide. I need to create the directories and stub files.

Based on the guide, I need to create:
- tests/unit/patterns/temporal/
- tests/unit/patterns/validation/
- tests/unit/patterns/schema/
- And the corresponding test files

Let me create these directories and files.

<xai:function_call name="todowrite">
<parameter name="todos">[{"content":"Day 3 Morning: Design pattern test strategy and create README.md","status":"completed","priority":"high","id":"day3_morning_design_test_strategy"},{"content":"Day 3 Morning: Create test file structure for patterns","status":"in_progress","priority":"high","id":"day3_morning_create_test_structure"}]
