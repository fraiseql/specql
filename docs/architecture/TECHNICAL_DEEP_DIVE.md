# SpecQL Technical Deep Dive

An in-depth look at SpecQL's architecture, design decisions, and implementation details.

## Overview

SpecQL is a multi-language code generator that transforms YAML entity definitions into production-ready code across PostgreSQL, Java, Rust, TypeScript, and Python. This document explores the technical foundations that make this possible.

## Core Architecture

### 1. Universal AST (Abstract Syntax Tree)

At SpecQL's heart is a language-agnostic representation of data models:

```python
@dataclass
class UniversalEntity:
    """Language-independent entity representation"""
    name: str
    schema: str
    fields: List[UniversalField]
    actions: List[UniversalAction]
    relationships: List[UniversalRelationship]
    metadata: Dict[str, Any]
```

**Key Design Decisions**:
- **Single source of truth**: All language-specific representations derive from this AST
- **Extensible metadata**: Framework-specific annotations stored here
- **Validation at AST level**: Business rules enforced before code generation

### 2. Adapter Pattern for Language Generation

Each target language has a dedicated adapter:

```
src/adapters/
├── base_adapter.py      # Abstract base class
├── postgresql_adapter.py # DDL + PL/pgSQL generation
├── java_adapter.py      # Spring Boot entities
├── rust_adapter.py      # Diesel models
└── typescript_adapter.py # Type interfaces
```

**Adapter Interface**:
```python
class BaseAdapter(ABC):
    @abstractmethod
    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate language-specific code for an entity"""

    @abstractmethod
    def generate_action(self, action: UniversalAction) -> str:
        """Generate business logic implementation"""
```

### 3. Trinity Pattern for Primary Keys

SpecQL implements a three-part primary key system:

```sql
CREATE TABLE tb_user (
    pk_user UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- Internal ID
    id BIGSERIAL UNIQUE NOT NULL,                        -- User-friendly ID
    username TEXT UNIQUE                                 -- Natural key (optional)
);
```

**Benefits**:
- **Migration safety**: `pk_*` never changes
- **User experience**: `id` is sequential and readable
- **Flexibility**: Natural keys for domain-specific lookups
- **Performance**: Optimized for different access patterns

## Code Generation Pipeline

### Phase 1: Parsing & Validation

```python
# YAML → Universal AST
parser = SpecQLParser()
entity_def = parser.parse(yaml_content)
entity = convert_entity_definition_to_entity(entity_def)
```

**Validation Rules**:
- Field type compatibility
- Relationship validity
- Action syntax correctness
- Schema naming conventions

### Phase 2: Framework-Aware Generation

```python
# Apply framework defaults
registry = get_framework_registry()
effective_defaults = registry.get_effective_defaults(framework, dev_mode)

# Generate with framework context
orchestrator = CLIOrchestrator(
    framework=resolved_framework,
    output_format=effective_defaults["output_format"]
)
```

**Framework Registry**:
```python
FRAMEWORK_DEFAULTS = {
    "fraiseql": {
        "include_tv": True,      # Table views for GraphQL
        "trinity_pattern": True, # pk_*, id, identifier
        "audit_fields": True,    # created_at, updated_at, etc.
    },
    "django": {
        "include_tv": False,
        "trinity_pattern": False,
        "single_pk": True,       # Just 'id' field
    }
}
```

### Phase 3: Multi-Language Orchestration

```python
# Generate all targets
results = []
for target in ["postgresql", "java", "typescript"]:
    adapter = get_adapter_for_target(target)
    code = adapter.generate_entity(entity)
    results.append(code)
```

## Advanced Features

### 1. Business Logic Compilation

SpecQL compiles YAML actions into executable code:

**YAML Action**:
```yaml
actions:
  - name: transfer_funds
    steps:
      - validate: from_account.balance >= amount
      - update: Account SET balance = balance - :amount WHERE id = :from_account_id
      - update: Account SET balance = balance + :amount WHERE id = :to_account_id
      - insert: Transaction VALUES (:from_account_id, :to_account_id, :amount)
```

**Generated PL/pgSQL**:
```sql
CREATE FUNCTION fn_transfer_funds(
    p_from_account_id BIGINT,
    p_to_account_id BIGINT,
    p_amount DECIMAL
) RETURNS VOID AS $$
DECLARE
    v_from_balance DECIMAL;
BEGIN
    -- Validation
    SELECT balance INTO v_from_balance
    FROM tb_account WHERE id = p_from_account_id;

    IF v_from_balance < p_amount THEN
        RAISE EXCEPTION 'Insufficient funds';
    END IF;

    -- Transfer
    UPDATE tb_account SET balance = balance - p_amount WHERE id = p_from_account_id;
    UPDATE tb_account SET balance = balance + p_amount WHERE id = p_to_account_id;

    -- Record transaction
    INSERT INTO tb_transaction (from_account_id, to_account_id, amount)
    VALUES (p_from_account_id, p_to_account_id, p_amount);
END;
$$ LANGUAGE plpgsql;
```

### 2. Reverse Engineering

Import existing codebases into SpecQL:

```bash
# From PostgreSQL
specql reverse postgresql --connection="postgresql://..." --schema=public

# From Java classes
specql reverse java --source-path=src/main/java --package=com.example

# From TypeScript interfaces
specql reverse typescript --file=types.ts
```

**Reverse Engineering Pipeline**:
1. **Parse source code** using language-specific parsers
2. **Extract entities** and relationships
3. **Infer types** and constraints
4. **Generate YAML** representation

### 3. Registry System for Table Codes

Production deployments use hierarchical table codes:

```
01_write_side/
├── 011_catalog/
│   ├── 0111_product/
│   │   └── 01111_tb_product.sql
│   └── 0112_category/
│       └── 01121_tb_category.sql
└── 012_order/
    └── 0121_tb_order.sql
```

**Benefits**:
- **Predictable organization**: Domain → Subdomain → Entity
- **Migration ordering**: Numerical sorting ensures correct application
- **Team coordination**: Avoid table code conflicts

### 4. Framework Integration

**FraiseQL GraphQL**:
```sql
-- Auto-generated GraphQL metadata
COMMENT ON TABLE crm.tb_contact IS '@fraiseql:entity';
COMMENT ON COLUMN crm.tb_contact.email IS '@fraiseql:field(type=email)';
COMMENT ON FUNCTION crm.fn_create_contact IS '@fraiseql:mutation';
```

**Spring Boot**:
```java
// Generated with JPA annotations
@Entity
@Table(name = "tb_user", schema = "auth")
public class User {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotNull @Email
    private String email;

    @Enumerated(EnumType.STRING)
    private UserRole role;
}
```

## Performance Optimizations

### 1. Incremental Generation

Only regenerate changed entities:

```python
# Track file modification times
last_generated = get_last_generation_time(entity_file)
if entity_file.stat().st_mtime > last_generated:
    regenerate_entity(entity_file)
```

### 2. Parallel Processing

Generate multiple entities concurrently:

```python
from concurrent.futures import ThreadPoolExecutor

def generate_entities_parallel(entities, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(generate_entity, entity) for entity in entities]
        return [f.result() for f in futures]
```

### 3. Template Caching

Cache Jinja2 templates to avoid recompilation:

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader('templates/'),
    cache_size=1000,  # Cache compiled templates
    auto_reload=False  # Disable in production
)
```

## Testing Strategy

### 1. Golden File Testing

Compare generated output against known-good files:

```python
def test_user_entity_generation():
    entity = load_test_entity('user')
    generated = generate_postgresql(entity)

    expected = load_golden_file('user_postgresql.sql')
    assert generated == expected
```

### 2. Integration Testing

End-to-end tests with real databases:

```python
def test_generated_code_works():
    # Generate schema
    generate_postgresql(test_entity)

    # Apply to test database
    run_migrations()

    # Test CRUD operations
    test_create_read_update_delete()
```

### 3. Cross-Language Consistency

Ensure generated code is semantically equivalent:

```python
def test_cross_language_consistency():
    entity = load_entity()

    pg_code = generate_postgresql(entity)
    java_code = generate_java(entity)
    ts_code = generate_typescript(entity)

    # Verify all represent same data model
    assert_semantic_equivalence(pg_code, java_code, ts_code)
```

## Error Handling & Validation

### 1. Multi-Level Validation

**YAML Syntax**: Basic structure validation
**Semantic**: Business rule validation
**Cross-Reference**: Relationship validation
**Framework-Specific**: Target language constraints

### 2. Helpful Error Messages

```python
class SpecQLError(Exception):
    def __init__(self, message, context=None, suggestion=None):
        self.message = message
        self.context = context  # file, line, entity
        self.suggestion = suggestion

# Usage
raise SpecQLError(
    "Invalid field type 'string'",
    context=ErrorContext(file="user.yaml", field="email"),
    suggestion="Use 'text' instead of 'string'"
)
```

### 3. Recovery & Suggestions

```python
def suggest_field_type(invalid_type: str) -> List[str]:
    """Suggest valid field types for typos"""
    valid_types = ['text', 'integer', 'decimal', 'boolean', 'timestamp']
    return difflib.get_close_matches(invalid_type, valid_types, n=3)
```

## Extensibility

### 1. Custom Adapters

Add support for new languages:

```python
class GoAdapter(BaseAdapter):
    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        # Generate Go structs with GORM tags
        return [GeneratedCode(
            filename=f"{entity.name}.go",
            content=self.render_go_struct(entity)
        )]
```

### 2. Plugin System

Allow third-party extensions:

```python
@specql_plugin
class CustomValidationPlugin:
    def validate_entity(self, entity: UniversalEntity) -> List[str]:
        # Custom validation logic
        return errors
```

### 3. Template Customization

Override default templates:

```python
# Custom Java template
templates/java/entity.java.j2
templates/java/repository.java.j2
```

## Deployment & Distribution

### 1. PyPI Package

```toml
[project]
name = "specql-generator"
version = "0.5.0-beta"
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1.2",
    "click>=8.1.0",
    "rich>=13.0.0",
]
```

### 2. Docker Images

```dockerfile
FROM python:3.11-slim
COPY . /app
RUN pip install -e .
ENTRYPOINT ["specql"]
```

### 3. GitHub Actions

```yaml
- uses: specql/setup@v1
  with:
    version: '0.5.0-beta'
- run: specql generate entities/*.yaml
```

## Future Architecture

### 1. Language Server Protocol

IDE integration for real-time validation and autocompletion.

### 2. Visual Schema Designer

Web-based UI for designing entities visually.

### 3. Advanced Relationships

Support for complex relationship patterns (polymorphism, inheritance).

### 4. Migration Management

Automatic migration generation and conflict resolution.

## Performance Characteristics

- **Generation Speed**: ~37,000 entities/second (TypeScript)
- **Memory Usage**: O(n) where n = number of entities
- **Disk I/O**: Minimal, template-based generation
- **Scalability**: Linear scaling with entity count

## Conclusion

SpecQL's architecture enables the "write once, generate everywhere" promise through:

1. **Universal AST** as the single source of truth
2. **Adapter pattern** for language-specific generation
3. **Comprehensive validation** at multiple levels
4. **Extensible plugin system** for customization
5. **Performance optimizations** for large codebases

This foundation supports SpecQL's mission of eliminating duplication in multi-language backend development.