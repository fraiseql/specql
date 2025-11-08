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

### `specql_parser.py` 🚧 TODO
Main parser class:
- `SpecQLParser.parse(yaml_content)` → `Entity`
- Field parsing (text, enum, ref, list)
- Action step parsing (validate, if/then, insert, update, etc.)
- Agent parsing

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

### Week 1 Goals
- [ ] `ast_models.py` - Data classes (DONE ✅)
- [ ] `specql_parser.py` - Basic parsing (simple entities)
- [ ] `validators.py` - Field validation
- [ ] Parse simple entities (contact.yaml)

### Week 2 Goals
- [ ] `expression_parser.py` - Expression conversion
- [ ] Complex action step parsing (if/then, switch)
- [ ] Agent parsing
- [ ] Parse complex entities (reservation.yaml)

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

**Phase**: Week 1 - Basic Parsing
**Progress**: 10% (AST models complete)
**Next**: Implement `SpecQLParser.parse()` method
