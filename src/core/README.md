# Core Parser Module (Team A)

**Responsibility**: Parse SpecQL YAML into AST (Abstract Syntax Tree)

## 🎯 Objectives

Transform business-focused YAML into structured Python objects:

```yaml
# Input: SpecQL YAML (40-60 lines)
entity: Contact
  fields:
    email: text
    status: enum(lead, qualified)
  actions:
    - name: create_contact
      steps:
        - validate: email MATCHES email_pattern
        - insert: Contact
```

↓

```python
# Output: Entity AST
Entity(
    name='Contact',
    fields={
        'email': FieldDefinition(name='email', type='text'),
        'status': FieldDefinition(name='status', type='enum', values=['lead', 'qualified'])
    },
    actions=[
        Action(
            name='create_contact',
            steps=[
                ActionStep(type='validate', expression='email MATCHES email_pattern'),
                ActionStep(type='insert', entity='Contact')
            ]
        )
    ]
)
```

## 📋 Components

### `ast_models.py` ✅ DONE
Data classes representing parsed entities:
- `Entity` - Root AST node
- `FieldDefinition` - Field metadata
- `Action` - Business action
- `ActionStep` - Individual step in workflow
- `Agent` - AI agent configuration

### `specql_parser.py` ✅ DONE
Main parser class:
- `SpecQLParser.parse(yaml_content)` → `Entity`
- Field parsing (text, enum, ref, list)
- Action step parsing (validate, if/then, insert, update, etc.)
- Agent parsing
- Expression validation
- Error handling with clear messages

### `validators.py` 🚧 TODO
Business rule validation:
- Field type validation
- Expression validation
- Dependency validation
- Circular reference detection

### `expression_parser.py` 🚧 TODO
Parse SpecQL expressions:
- `email MATCHES pattern` → SQL regex
- `status IN [...]` → SQL IN clause
- `input.field` → JSON accessor

## 🧪 Testing Strategy

### Unit Tests
```bash
uv run pytest tests/unit/core/ -v
```

Test files:
- `test_ast_models.py` - Data class behavior
- `test_specql_parser.py` - YAML parsing
- `test_validators.py` - Validation rules
- `test_expression_parser.py` - Expression conversion

### Test Coverage Target
- **Overall**: > 90%
- **Critical paths**: 100%

## 🔗 Interface Contract

### Input
YAML string (SpecQL format)

### Output
```python
from src.core.ast_models import Entity

def parse(yaml_content: str) -> Entity:
    """Parse SpecQL YAML into Entity AST"""
```

### Consumers
- Team B (SQL Generators) - Uses `Entity` AST
- Team C (Numbering System) - Uses `Entity.organization`
- Team D (Integration) - Uses `Entity` metadata
- Team E (CLI) - Orchestrates parsing

## 🚀 Getting Started

### 1. Setup
```bash
cd /home/lionel/code/printoptim_backend_poc
source .venv/bin/activate
```

### 2. Run Team A Tests
```bash
make teamA-test
```

### 3. Start TDD Cycle

#### RED Phase
```bash
# Edit test
vim tests/unit/core/test_specql_parser.py

# Run test (should fail)
uv run pytest tests/unit/core/test_specql_parser.py::test_parse_simple_entity -v
```

#### GREEN Phase
```bash
# Implement feature
vim src/core/specql_parser.py

# Run test (should pass)
uv run pytest tests/unit/core/test_specql_parser.py::test_parse_simple_entity -v
```

#### REFACTOR Phase
```bash
# Clean up code
vim src/core/specql_parser.py

# All tests still pass
make teamA-test
```

#### QA Phase
```bash
make lint
make typecheck
make coverage
```

## 📊 Progress Tracking

### Week 1 Goals ✅ COMPLETE
- [x] `ast_models.py` - Data classes (DONE ✅)
- [x] `specql_parser.py` - Full parsing (all entity types)
- [x] `validators.py` - Field validation (integrated into parser)
- [x] Parse simple entities (contact.yaml)
- [x] Parse complex entities (manufacturer.yaml)
- [x] Support all action step types (including notify)
- [x] Expression validation handles quoted strings
- [x] Lightweight SpecQL examples work

### Week 2 Goals (Future)
- [ ] `expression_parser.py` - Advanced expression conversion
- [ ] Enhanced error messages with line numbers
- [ ] Performance optimizations
- [ ] Integration testing with Team B output

## 🤝 Team Communication

### Daily Standup
Post in `#team-parser`:
```
**Yesterday**: Implemented basic YAML parsing
**Today**: Adding field type validation
**Blockers**: None
```

### Integration Points
- **Team B**: Finalize `Entity` AST structure (Week 1)
- **Team E**: CLI integration (Week 2)

## 📚 Resources

- [SpecQL DSL Reference](../../docs/guides/specql-dsl-reference.md) (TODO)
- [IMPLEMENTATION_PLAN_SPECQL.md](../../docs/architecture/IMPLEMENTATION_PLAN_SPECQL.md)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## 🎯 Current Status

**Phase**: Week 1 - Complete ✅
**Progress**: 100% (All SpecQL features implemented)
**Status**: ✅ READY for Team B (SQL Generators)

**Completed**:
- Full SpecQL YAML parser with comprehensive test coverage
- Support for all field types (text, enum, ref, list)
- Support for all action step types (validate, if/then, insert, update, find, call, reject, notify)
- AI agent parsing
- Expression validation with business rule checking (handles quoted strings)
- 20 comprehensive unit tests (100% pass rate)
- Proper error handling and clear error messages
- Lightweight SpecQL examples parse successfully
