# SpecQL Multi-Framework Evolution Plan

**Vision**: Transform SpecQL from a PostgreSQL+GraphQL code generator into a **Universal Business Logic Compiler** that generates production code for any backend/frontend framework.

**Tagline**: *Write business logic once. Deploy anywhere.*

**Current State**: Production-ready PostgreSQL + GraphQL + TypeScript generator
**Target State**: Framework-agnostic business logic → Django, Rails, Prisma, Laravel, etc.

---

## 🎯 Executive Summary

SpecQL already has the **perfect architecture** for multi-framework generation:
- **Team A (Parser)** produces a business-focused AST
- **Teams B-E (Generators)** transform AST → framework-specific code
- **Trinity Pattern** and conventions are already framework-agnostic concepts

**Key Insight**: We need to:
1. Abstract the AST to be truly framework-agnostic
2. Create a **Generator Adapter Pattern**
3. Implement adapters for Django, Rails, Prisma, etc.
4. Build framework selection into CLI

**Estimated Timeline**: 6-9 months to production-ready multi-framework support

---

## 📊 Strategic Value

### Market Differentiation
| Tool | Scope | Limitation |
|------|-------|------------|
| **Hasura** | GraphQL only | No business logic, PostgreSQL-only |
| **Supabase** | PostgreSQL only | Limited to PostgreSQL ecosystem |
| **Prisma** | TypeScript only | Node.js ecosystem lock-in |
| **Django** | Python only | Python ecosystem lock-in |
| **SpecQL** | **Any framework** | **Universal business logic** ✨ |

### Use Cases Unlocked
1. **Polyglot Teams**: Same business logic → Python, Ruby, TypeScript, PHP
2. **Migration Paths**: Gradually migrate from Rails → Django without rewriting logic
3. **Best-of-Breed**: Mix PostgreSQL data layer + Django admin + Prisma API
4. **Multi-Platform**: Generate for web (Apollo), mobile (React Query), desktop (SWR)

---

## 🏗️ Technical Architecture

### Current Architecture
```
SpecQL YAML → Team A (Parser) → PostgreSQL-focused AST
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
Team B      Team C      Team D
PostgreSQL  PL/pgSQL    FraiseQL
Schema      Actions     Metadata
```

### Target Architecture
```
SpecQL YAML → Team A (Parser) → Universal AST
                ↓
    ┌───────────┼─────────────────────────────────┐
    ↓           ↓           ↓           ↓         ↓
PostgreSQL  Django      Rails       Prisma    Laravel
Adapter     Adapter     Adapter     Adapter   Adapter
    ↓           ↓           ↓           ↓         ↓
   SQL      Python      Ruby      TypeScript   PHP
```

### Adapter Pattern
```python
class FrameworkAdapter(ABC):
    """Base class for all framework adapters"""

    @abstractmethod
    def generate_entity(self, entity: UniversalEntity) -> GeneratedCode:
        """Convert universal entity → framework-specific model"""

    @abstractmethod
    def generate_action(self, action: UniversalAction) -> GeneratedCode:
        """Convert universal action → framework-specific function"""

    @abstractmethod
    def generate_relationship(self, rel: UniversalRelationship) -> GeneratedCode:
        """Convert universal relationship → framework-specific FK/join"""

    @abstractmethod
    def get_conventions(self) -> FrameworkConventions:
        """Return framework-specific naming conventions"""
```

---

## 📋 PHASE 1: Foundation (4-6 weeks)

**Objective**: Abstract the AST and create the adapter pattern without breaking existing PostgreSQL generator.

### TDD Cycle 1.1: Universal AST Abstraction

#### RED: Write failing tests for framework-agnostic AST
```python
# tests/unit/core/test_universal_ast.py
def test_universal_entity_has_no_sql_specifics():
    """Universal entity should not reference SQL concepts"""
    entity = parse_specql_entity("""
    entity: Contact
    fields:
      email: text
      company: ref(Company)
    """)

    # Should NOT have SQL-specific attributes
    assert not hasattr(entity, 'table_name')
    assert not hasattr(entity, 'sql_type')

    # SHOULD have universal attributes
    assert entity.name == 'Contact'
    assert len(entity.fields) == 2
    assert entity.fields[0].type == FieldType.TEXT
    assert entity.fields[1].type == FieldType.REFERENCE

def test_universal_action_has_no_plpgsql_specifics():
    """Universal action should not reference PL/pgSQL concepts"""
    action = parse_specql_action("""
    name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
    """)

    # Should have framework-agnostic representation
    assert action.steps[0].type == StepType.VALIDATE
    assert action.steps[1].type == StepType.UPDATE
    assert action.steps[1].entity == 'Contact'
```

#### GREEN: Implement Universal AST
```python
# src/core/universal_ast.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

class FieldType(Enum):
    """Universal field types - not tied to any framework"""
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    REFERENCE = "reference"
    ENUM = "enum"
    LIST = "list"
    RICH = "rich"  # Composite types (money, dimensions, etc.)

class StepType(Enum):
    """Universal action step types"""
    VALIDATE = "validate"
    IF = "if"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CALL = "call"
    NOTIFY = "notify"
    FOREACH = "foreach"

@dataclass
class UniversalField:
    """Framework-agnostic field definition"""
    name: str
    type: FieldType
    required: bool = False
    unique: bool = False
    default: Optional[Any] = None

    # For REFERENCE type
    references: Optional[str] = None

    # For ENUM type
    enum_values: Optional[List[str]] = None

    # For RICH type
    composite_type: Optional[str] = None

@dataclass
class UniversalEntity:
    """Framework-agnostic entity definition"""
    name: str
    schema: str
    fields: List[UniversalField]
    actions: List['UniversalAction']

    # Multi-tenancy
    is_multi_tenant: bool = True

    # Metadata
    description: Optional[str] = None

@dataclass
class UniversalStep:
    """Framework-agnostic action step"""
    type: StepType
    expression: Optional[str] = None  # For validate, if conditions
    entity: Optional[str] = None      # For insert, update, delete
    fields: Optional[Dict[str, Any]] = None  # For insert, update
    function: Optional[str] = None    # For call
    collection: Optional[str] = None  # For foreach
    steps: Optional[List['UniversalStep']] = None  # For if, foreach

@dataclass
class UniversalAction:
    """Framework-agnostic business logic"""
    name: str
    entity: str
    steps: List[UniversalStep]
    impacts: List[str]
    description: Optional[str] = None
    parameters: Optional[List[UniversalField]] = None

@dataclass
class UniversalSchema:
    """Complete framework-agnostic schema"""
    entities: List[UniversalEntity]
    composite_types: Dict[str, List[UniversalField]]
    tenant_mode: str  # 'multi_tenant', 'single_tenant', 'shared'
```

#### REFACTOR: Update Parser to produce Universal AST
```python
# src/core/specql_parser.py - Refactor existing parser

class SpecQLParser:
    """Parse SpecQL YAML → Universal AST (framework-agnostic)"""

    def parse_entity(self, yaml_content: str) -> UniversalEntity:
        """Parse entity YAML → UniversalEntity"""
        data = yaml.safe_load(yaml_content)

        return UniversalEntity(
            name=data['entity'],
            schema=data.get('schema', 'app'),
            fields=self._parse_fields(data.get('fields', {})),
            actions=self._parse_actions(data.get('actions', [])),
            is_multi_tenant=data.get('multi_tenant', True),
            description=data.get('description')
        )

    def _parse_field_type(self, type_str: str) -> FieldType:
        """Convert SpecQL type → Universal FieldType"""
        if type_str == 'text':
            return FieldType.TEXT
        elif type_str == 'integer':
            return FieldType.INTEGER
        elif type_str.startswith('ref('):
            return FieldType.REFERENCE
        elif type_str.startswith('enum('):
            return FieldType.ENUM
        # ... etc
```

#### QA: Verify Universal AST
- [ ] All existing tests pass with new Universal AST
- [ ] No SQL-specific concepts in core AST classes
- [ ] Parser produces clean Universal AST
- [ ] Documentation updated

---

### TDD Cycle 1.2: Framework Adapter Pattern

#### RED: Write failing tests for adapter interface
```python
# tests/unit/adapters/test_adapter_interface.py
def test_framework_adapter_has_required_methods():
    """All adapters must implement standard interface"""

    class TestAdapter(FrameworkAdapter):
        pass

    # Should fail - missing required methods
    with pytest.raises(TypeError):
        adapter = TestAdapter()

def test_adapter_can_generate_entity():
    """Adapter can convert UniversalEntity → framework code"""
    entity = UniversalEntity(
        name='Contact',
        schema='crm',
        fields=[
            UniversalField(name='email', type=FieldType.TEXT)
        ],
        actions=[]
    )

    adapter = MockAdapter()
    result = adapter.generate_entity(entity)

    assert result.file_path is not None
    assert result.content is not None
    assert 'Contact' in result.content
```

#### GREEN: Implement Adapter Base Class
```python
# src/adapters/base_adapter.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class GeneratedCode:
    """Container for generated code"""
    file_path: str
    content: str
    language: str  # 'sql', 'python', 'ruby', 'typescript', etc.

@dataclass
class FrameworkConventions:
    """Framework-specific conventions"""
    naming_case: str  # 'snake_case', 'camelCase', 'PascalCase'
    primary_key_name: str
    foreign_key_pattern: str
    timestamp_fields: List[str]
    supports_multi_tenancy: bool

class FrameworkAdapter(ABC):
    """Base class for all framework adapters"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    @abstractmethod
    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate framework-specific entity/model code"""
        pass

    @abstractmethod
    def generate_action(self, action: UniversalAction, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate framework-specific business logic"""
        pass

    @abstractmethod
    def generate_relationship(self, field: UniversalField, entity: UniversalEntity) -> str:
        """Generate framework-specific relationship code"""
        pass

    @abstractmethod
    def get_conventions(self) -> FrameworkConventions:
        """Return framework conventions"""
        pass

    @abstractmethod
    def get_framework_name(self) -> str:
        """Return framework identifier (e.g., 'django', 'rails')"""
        pass

    def generate_full_schema(self, schema: UniversalSchema) -> List[GeneratedCode]:
        """Generate complete schema for all entities"""
        generated = []

        for entity in schema.entities:
            generated.extend(self.generate_entity(entity))

            for action in entity.actions:
                generated.extend(self.generate_action(action, entity))

        return generated
```

#### REFACTOR: Migrate PostgreSQL Generator to Adapter Pattern
```python
# src/adapters/postgresql_adapter.py
class PostgreSQLAdapter(FrameworkAdapter):
    """Adapter for PostgreSQL + PL/pgSQL"""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        # Wrap existing generators
        self.table_generator = TableGenerator()
        self.action_generator = ActionOrchestrator()

    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate PostgreSQL table DDL"""
        ddl = self.table_generator.generate_table(entity)

        return [GeneratedCode(
            file_path=f"db/schema/10_tables/{entity.name.lower()}.sql",
            content=ddl,
            language='sql'
        )]

    def generate_action(self, action: UniversalAction, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate PL/pgSQL function"""
        plpgsql = self.action_generator.generate_action(action, entity)

        return [GeneratedCode(
            file_path=f"db/schema/06_functions/{entity.schema}/{action.name}.sql",
            content=plpgsql,
            language='sql'
        )]

    def get_conventions(self) -> FrameworkConventions:
        return FrameworkConventions(
            naming_case='snake_case',
            primary_key_name='pk_{entity}',
            foreign_key_pattern='fk_{entity}',
            timestamp_fields=['created_at', 'updated_at', 'deleted_at'],
            supports_multi_tenancy=True
        )

    def get_framework_name(self) -> str:
        return 'postgresql'
```

#### QA: Verify Adapter Pattern
- [ ] PostgreSQL generator works through adapter
- [ ] All existing PostgreSQL tests pass
- [ ] Adapter interface is clean and extensible
- [ ] No regression in generated code quality

---

### TDD Cycle 1.3: Adapter Registry

#### RED: Write failing tests for adapter discovery
```python
# tests/unit/adapters/test_adapter_registry.py
def test_adapter_registry_can_register_adapter():
    """Registry can register new adapters"""
    registry = AdapterRegistry()

    class CustomAdapter(FrameworkAdapter):
        def get_framework_name(self) -> str:
            return 'custom'

    registry.register(CustomAdapter)

    assert registry.has_adapter('custom')
    assert isinstance(registry.get_adapter('custom'), CustomAdapter)

def test_adapter_registry_lists_available_adapters():
    """Registry can list all available adapters"""
    registry = AdapterRegistry()
    registry.register(PostgreSQLAdapter)
    registry.register(DjangoAdapter)

    adapters = registry.list_adapters()

    assert 'postgresql' in adapters
    assert 'django' in adapters
```

#### GREEN: Implement Adapter Registry
```python
# src/adapters/registry.py
from typing import Dict, Type, List
import importlib
import pkgutil

class AdapterRegistry:
    """Central registry for framework adapters"""

    def __init__(self):
        self._adapters: Dict[str, Type[FrameworkAdapter]] = {}

    def register(self, adapter_class: Type[FrameworkAdapter]):
        """Register a framework adapter"""
        # Get framework name from adapter
        temp_instance = adapter_class()
        framework_name = temp_instance.get_framework_name()

        self._adapters[framework_name] = adapter_class

    def get_adapter(self, framework_name: str, config: Optional[Dict] = None) -> FrameworkAdapter:
        """Get adapter instance by framework name"""
        if framework_name not in self._adapters:
            raise ValueError(f"Unknown framework: {framework_name}")

        adapter_class = self._adapters[framework_name]
        return adapter_class(config)

    def has_adapter(self, framework_name: str) -> bool:
        """Check if adapter is registered"""
        return framework_name in self._adapters

    def list_adapters(self) -> List[str]:
        """List all registered adapter names"""
        return list(self._adapters.keys())

    def auto_discover(self):
        """Auto-discover and register all adapters in src/adapters/"""
        import src.adapters

        for _, module_name, _ in pkgutil.iter_modules(src.adapters.__path__):
            if module_name.endswith('_adapter'):
                module = importlib.import_module(f'src.adapters.{module_name}')

                # Find FrameworkAdapter subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, FrameworkAdapter) and
                        attr != FrameworkAdapter):
                        self.register(attr)

# Global registry instance
_registry = AdapterRegistry()

def get_registry() -> AdapterRegistry:
    """Get global adapter registry"""
    return _registry
```

#### REFACTOR: Update CLI to use registry
```python
# src/cli/generate.py
from src.adapters.registry import get_registry

def generate_command(
    specql_files: List[str],
    backends: List[str] = ['postgresql'],
    output_dir: str = 'generated/'
):
    """Generate code for multiple backends"""
    registry = get_registry()
    registry.auto_discover()

    # Parse SpecQL files
    parser = SpecQLParser()
    entities = [parser.parse_entity(f) for f in specql_files]
    schema = UniversalSchema(entities=entities, ...)

    # Generate for each backend
    for backend_name in backends:
        adapter = registry.get_adapter(backend_name)
        generated_files = adapter.generate_full_schema(schema)

        # Write files
        for gen_file in generated_files:
            write_file(gen_file.file_path, gen_file.content)
```

#### QA: Verify Registry System
- [ ] Registry can auto-discover adapters
- [ ] CLI can generate for multiple backends
- [ ] Tests verify adapter isolation
- [ ] Documentation updated

---

### Phase 1 Deliverables

**Completed**:
- ✅ Universal AST abstraction (framework-agnostic)
- ✅ FrameworkAdapter base class
- ✅ PostgreSQL adapter (refactored from existing generators)
- ✅ Adapter registry with auto-discovery
- ✅ CLI support for `--backends` flag

**Tests**:
- ✅ `tests/unit/core/test_universal_ast.py` - AST tests
- ✅ `tests/unit/adapters/test_adapter_interface.py` - Adapter interface
- ✅ `tests/unit/adapters/test_postgresql_adapter.py` - PostgreSQL adapter
- ✅ `tests/unit/adapters/test_adapter_registry.py` - Registry tests

**CLI Usage**:
```bash
# Still works exactly as before
specql generate entities/contact.yaml

# Now also supports explicit backend selection
specql generate entities/contact.yaml --backends=postgresql

# List available backends
specql list-backends
# Output: postgresql
```

**No Breaking Changes**: All existing functionality preserved.

---

## 📋 PHASE 2: Django Adapter (6-8 weeks)

**Objective**: Implement full Django adapter as proof-of-concept for multi-framework support.

### TDD Cycle 2.1: Django Entity Generation

#### RED: Write failing tests for Django model generation
```python
# tests/unit/adapters/test_django_adapter.py
def test_django_adapter_generates_model():
    """Django adapter generates valid Django model"""
    entity = UniversalEntity(
        name='Contact',
        schema='crm',
        fields=[
            UniversalField(name='email', type=FieldType.TEXT, required=True),
            UniversalField(name='status', type=FieldType.ENUM,
                         enum_values=['lead', 'qualified'])
        ],
        actions=[]
    )

    adapter = DjangoAdapter()
    result = adapter.generate_entity(entity)

    assert len(result) == 1
    assert result[0].file_path == 'crm/models/contact.py'
    assert 'class Contact(models.Model):' in result[0].content
    assert 'email = models.TextField()' in result[0].content
    assert 'status = models.CharField(choices=' in result[0].content

def test_django_adapter_applies_trinity_pattern():
    """Django adapter applies Trinity pattern"""
    entity = UniversalEntity(name='Contact', schema='crm', fields=[], actions=[])

    adapter = DjangoAdapter()
    result = adapter.generate_entity(entity)

    content = result[0].content
    assert 'pk_contact = models.AutoField(primary_key=True)' in content
    assert 'id = models.UUIDField(default=uuid.uuid4, unique=True)' in content
    assert 'identifier = models.CharField(max_length=255, unique=True)' in content
```

#### GREEN: Implement Django Entity Generator
```python
# src/adapters/django_adapter.py
from typing import List, Dict, Optional
from src.core.universal_ast import *
from src.adapters.base_adapter import *

class DjangoAdapter(FrameworkAdapter):
    """Adapter for Django ORM + Python"""

    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate Django model"""
        model_code = self._generate_model_class(entity)

        return [GeneratedCode(
            file_path=f"{entity.schema}/models/{entity.name.lower()}.py",
            content=model_code,
            language='python'
        )]

    def _generate_model_class(self, entity: UniversalEntity) -> str:
        """Generate Django model class"""
        lines = [
            "from django.db import models",
            "import uuid",
            "",
            "",
            f"class {entity.name}(models.Model):",
        ]

        # Trinity pattern
        lines.extend([
            f"    pk_{entity.name.lower()} = models.AutoField(primary_key=True)",
            "    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)",
            "    identifier = models.CharField(max_length=255, unique=True)",
            "",
        ])

        # Multi-tenant support
        if entity.is_multi_tenant:
            lines.append("    tenant_id = models.UUIDField()")
            lines.append("")

        # User fields
        for field in entity.fields:
            field_def = self._generate_field(field)
            lines.append(f"    {field_def}")

        # Audit fields
        lines.extend([
            "",
            "    created_at = models.DateTimeField(auto_now_add=True)",
            "    updated_at = models.DateTimeField(auto_now=True)",
            "    deleted_at = models.DateTimeField(null=True, blank=True)",
        ])

        # Meta class
        lines.extend([
            "",
            "    class Meta:",
            f"        db_table = 'tb_{entity.name.lower()}'",
            "        indexes = [",
        ])

        # Auto-generate indexes
        if entity.is_multi_tenant:
            lines.append("            models.Index(fields=['tenant_id']),")

        for field in entity.fields:
            if field.type == FieldType.REFERENCE or field.type == FieldType.ENUM:
                lines.append(f"            models.Index(fields=['{field.name}']),")

        lines.extend([
            "        ]",
            "",
            f"    def __str__(self):",
            f"        return self.identifier",
        ])

        return "\n".join(lines)

    def _generate_field(self, field: UniversalField) -> str:
        """Generate Django field definition"""
        field_kwargs = []

        if not field.required:
            field_kwargs.append("null=True")
            field_kwargs.append("blank=True")

        if field.unique:
            field_kwargs.append("unique=True")

        if field.default is not None:
            field_kwargs.append(f"default={repr(field.default)}")

        kwargs_str = ", ".join(field_kwargs) if field_kwargs else ""

        # Map universal type to Django field
        if field.type == FieldType.TEXT:
            return f"{field.name} = models.TextField({kwargs_str})"

        elif field.type == FieldType.INTEGER:
            return f"{field.name} = models.IntegerField({kwargs_str})"

        elif field.type == FieldType.BOOLEAN:
            return f"{field.name} = models.BooleanField({kwargs_str})"

        elif field.type == FieldType.DATETIME:
            return f"{field.name} = models.DateTimeField({kwargs_str})"

        elif field.type == FieldType.REFERENCE:
            ref_entity = field.references
            fk_kwargs = [
                f"'{ref_entity}'",
                "on_delete=models.CASCADE",
                f"db_column='fk_{ref_entity.lower()}'",
            ]
            if kwargs_str:
                fk_kwargs.append(kwargs_str)
            return f"{field.name} = models.ForeignKey({', '.join(fk_kwargs)})"

        elif field.type == FieldType.ENUM:
            choices = [(v, v.replace('_', ' ').title()) for v in field.enum_values]
            enum_kwargs = [f"choices={choices}", "max_length=50"]
            if kwargs_str:
                enum_kwargs.append(kwargs_str)
            return f"{field.name} = models.CharField({', '.join(enum_kwargs)})"

        else:
            raise ValueError(f"Unsupported field type: {field.type}")

    def get_conventions(self) -> FrameworkConventions:
        return FrameworkConventions(
            naming_case='snake_case',
            primary_key_name='pk_{entity}',
            foreign_key_pattern='fk_{entity}',
            timestamp_fields=['created_at', 'updated_at', 'deleted_at'],
            supports_multi_tenancy=True
        )

    def get_framework_name(self) -> str:
        return 'django'
```

#### REFACTOR: Add field type mapping helpers
```python
# src/adapters/django_adapter.py (continued)

class DjangoFieldMapper:
    """Helper class for mapping universal fields to Django fields"""

    TYPE_MAP = {
        FieldType.TEXT: 'TextField',
        FieldType.INTEGER: 'IntegerField',
        FieldType.BOOLEAN: 'BooleanField',
        FieldType.DATETIME: 'DateTimeField',
    }

    @classmethod
    def map_field(cls, field: UniversalField) -> str:
        """Map universal field to Django field"""
        # ... refactored field mapping logic
```

#### QA: Verify Django Model Generation
- [ ] Generated models are valid Django code
- [ ] Trinity pattern applied correctly
- [ ] Foreign keys generated correctly
- [ ] Enum fields use Django choices
- [ ] Multi-tenant fields added when needed
- [ ] Audit fields present

---

### TDD Cycle 2.2: Django Action Generation

#### RED: Write failing tests for Django method generation
```python
# tests/unit/adapters/test_django_actions.py
def test_django_adapter_generates_model_method():
    """Django adapter generates model method for action"""
    action = UniversalAction(
        name='qualify_lead',
        entity='Contact',
        steps=[
            UniversalStep(
                type=StepType.VALIDATE,
                expression="status = 'lead'"
            ),
            UniversalStep(
                type=StepType.UPDATE,
                entity='Contact',
                fields={'status': 'qualified'}
            )
        ],
        impacts=['Contact']
    )

    entity = UniversalEntity(name='Contact', schema='crm', fields=[], actions=[action])

    adapter = DjangoAdapter()
    result = adapter.generate_action(action, entity)

    assert len(result) == 1
    content = result[0].content
    assert 'def qualify_lead(self):' in content
    assert 'if self.status != \'lead\':' in content
    assert 'self.status = \'qualified\'' in content
    assert 'self.save()' in content
    assert 'return MutationResult' in content
```

#### GREEN: Implement Django Action Generator
```python
# src/adapters/django_action_generator.py
class DjangoActionGenerator:
    """Generate Django model methods from universal actions"""

    def generate_method(self, action: UniversalAction, entity: UniversalEntity) -> str:
        """Generate Django model method"""
        lines = [
            f"    def {action.name}(self):",
            f'        """',
            f'        {action.description or action.name}',
            f'        ',
            f'        Impacts: {", ".join(action.impacts)}',
            f'        """',
        ]

        # Generate method body
        for step in action.steps:
            step_code = self._generate_step(step, entity)
            lines.extend([f"        {line}" for line in step_code.split('\n')])

        # Return mutation result
        lines.extend([
            "",
            "        return MutationResult(",
            "            success=True,",
            "            message=f'{self.identifier} updated successfully',",
            "            object_data=self.to_dict()",
            "        )"
        ])

        return "\n".join(lines)

    def _generate_step(self, step: UniversalStep, entity: UniversalEntity) -> str:
        """Generate code for a single step"""
        if step.type == StepType.VALIDATE:
            return self._generate_validate(step)

        elif step.type == StepType.UPDATE:
            return self._generate_update(step, entity)

        elif step.type == StepType.IF:
            return self._generate_if(step, entity)

        # ... other step types

    def _generate_validate(self, step: UniversalStep) -> str:
        """Generate validation code"""
        # Convert "status = 'lead'" → "self.status != 'lead'"
        condition = self._convert_condition(step.expression, negate=True)

        return f"""
if {condition}:
    raise ValidationError("{step.expression} validation failed")
""".strip()

    def _generate_update(self, step: UniversalStep, entity: UniversalEntity) -> str:
        """Generate update code"""
        lines = []

        for field_name, value in step.fields.items():
            lines.append(f"self.{field_name} = {repr(value)}")

        lines.append("self.save()")

        return "\n".join(lines)

    def _convert_condition(self, expression: str, negate: bool = False) -> str:
        """Convert SpecQL condition to Python"""
        # Simple implementation - would need full expression compiler
        # For now, handle basic equality
        expression = expression.replace(' = ', ' == ')

        if negate:
            expression = f"not ({expression})"

        # Add self. prefix to field references
        # This is simplified - real implementation would parse expression properly
        return expression.replace('status', 'self.status')
```

#### REFACTOR: Create Django-specific expression compiler
```python
# src/adapters/django_expression_compiler.py
class DjangoExpressionCompiler:
    """Compile universal expressions to Python"""

    def compile(self, expression: str, context: str = 'self') -> str:
        """Compile expression to Python code"""
        # Convert SQL-like syntax to Python
        # status = 'lead' → self.status == 'lead'
        # count > 0 → self.count > 0
        # ... etc
```

#### QA: Verify Django Action Generation
- [ ] Model methods generated correctly
- [ ] Validation steps work
- [ ] Update steps work
- [ ] Returns proper MutationResult
- [ ] Error handling present

---

### TDD Cycle 2.3: Django Migrations

#### RED: Write tests for Django migration generation
```python
# tests/unit/adapters/test_django_migrations.py
def test_django_adapter_generates_initial_migration():
    """Django adapter generates initial migration"""
    entity = UniversalEntity(
        name='Contact',
        schema='crm',
        fields=[
            UniversalField(name='email', type=FieldType.TEXT)
        ],
        actions=[]
    )

    adapter = DjangoAdapter()
    migrations = adapter.generate_migrations(entity, is_initial=True)

    assert len(migrations) == 1
    assert 'migrations.CreateModel' in migrations[0].content
    assert 'name=\'Contact\'' in migrations[0].content
```

#### GREEN: Implement Django migration generator
```python
# src/adapters/django_migration_generator.py
class DjangoMigrationGenerator:
    """Generate Django migrations from universal entities"""

    def generate_initial_migration(self, entity: UniversalEntity) -> GeneratedCode:
        """Generate initial migration for entity"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')

        migration_code = f"""
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='{entity.name}',
            fields=[
                ('pk_{entity.name.lower()}', models.AutoField(primary_key=True)),
                ('id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('identifier', models.CharField(max_length=255, unique=True)),
                # ... other fields
            ],
            options={{
                'db_table': 'tb_{entity.name.lower()}',
            }},
        ),
    ]
"""

        return GeneratedCode(
            file_path=f"{entity.schema}/migrations/{timestamp}_initial.py",
            content=migration_code,
            language='python'
        )
```

#### REFACTOR: Integrate migration generation into adapter
```python
# src/adapters/django_adapter.py
class DjangoAdapter(FrameworkAdapter):
    # ... existing methods

    def generate_full_schema(self, schema: UniversalSchema) -> List[GeneratedCode]:
        """Generate models + migrations"""
        generated = []

        # Generate models
        for entity in schema.entities:
            generated.extend(self.generate_entity(entity))

            # Generate actions
            for action in entity.actions:
                generated.extend(self.generate_action(action, entity))

        # Generate migrations
        migration_gen = DjangoMigrationGenerator()
        for entity in schema.entities:
            migration = migration_gen.generate_initial_migration(entity)
            generated.append(migration)

        return generated
```

#### QA: Verify Migration Generation
- [ ] Migrations are valid Django code
- [ ] Can run `python manage.py migrate`
- [ ] Tables created correctly
- [ ] Indexes created

---

### TDD Cycle 2.4: Django Integration Tests

#### RED: Write end-to-end Django tests
```python
# tests/integration/test_django_full_generation.py
def test_django_full_contact_generation(tmp_path):
    """Full Django code generation for Contact entity"""
    specql_yaml = """
    entity: Contact
    schema: crm
    fields:
      email: text
      company: ref(Company)
      status: enum(lead, qualified, customer)
    actions:
      - name: qualify_lead
        steps:
          - validate: status = 'lead'
          - update: Contact SET status = 'qualified'
    """

    # Parse
    parser = SpecQLParser()
    entity = parser.parse_entity(specql_yaml)

    # Generate
    adapter = DjangoAdapter()
    generated = adapter.generate_entity(entity)

    # Write to temp directory
    for gen_file in generated:
        file_path = tmp_path / gen_file.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(gen_file.content)

    # Verify generated files
    model_file = tmp_path / 'crm/models/contact.py'
    assert model_file.exists()

    # Verify can import (syntax check)
    import sys
    sys.path.insert(0, str(tmp_path))

    # This would fail if syntax is invalid
    import importlib.util
    spec = importlib.util.spec_from_file_location("contact", model_file)
    module = importlib.util.module_from_spec(spec)
    # Note: Won't execute because Django not configured, but validates syntax
```

#### GREEN: Ensure all components work together
- Fix any integration issues
- Ensure generated code is syntactically valid
- Add helper scripts for Django project setup

#### REFACTOR: Polish Django adapter
- Code cleanup
- Add docstrings
- Optimize generation

#### QA: Full Django Validation
- [ ] Can create Django project
- [ ] Can import generated models
- [ ] Can run migrations
- [ ] Can execute model methods
- [ ] Business logic works correctly

---

### Phase 2 Deliverables

**Completed**:
- ✅ Django model generation with Trinity pattern
- ✅ Django action methods from universal actions
- ✅ Django migration generation
- ✅ Full integration tests with real Django project

**Generated Django Code Example**:
```python
# crm/models/contact.py (auto-generated)
from django.db import models
import uuid

class Contact(models.Model):
    # Trinity pattern
    pk_contact = models.AutoField(primary_key=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True)
    identifier = models.CharField(max_length=255, unique=True)

    # Multi-tenant
    tenant_id = models.UUIDField()

    # Business fields
    email = models.TextField()
    company = models.ForeignKey('Company', on_delete=models.CASCADE, db_column='fk_company')
    status = models.CharField(choices=[('lead', 'Lead'), ('qualified', 'Qualified')], max_length=50)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tb_contact'
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['company']),
            models.Index(fields=['status']),
        ]

    def qualify_lead(self):
        """Qualify a lead contact"""
        if self.status != 'lead':
            raise ValidationError("Contact must be a lead")

        self.status = 'qualified'
        self.save()

        return MutationResult(
            success=True,
            message=f'{self.identifier} qualified successfully',
            object_data=self.to_dict()
        )
```

**CLI Usage**:
```bash
# Generate for both PostgreSQL and Django
specql generate entities/contact.yaml --backends=postgresql,django

# Output:
# ✓ Generated: db/schema/10_tables/contact.sql (PostgreSQL)
# ✓ Generated: crm/models/contact.py (Django)
# ✓ Generated: crm/migrations/20250111_1430_initial.py (Django)
```

---

## 📋 PHASE 3: Additional Framework Adapters (8-12 weeks)

**Objective**: Implement adapters for Rails, Prisma, and Laravel to prove ecosystem scalability.

### Framework Priority

1. **Prisma** (TypeScript) - Most requested by modern web developers
2. **Rails** (Ruby) - Mature ecosystem, ActiveRecord proven pattern
3. **Laravel** (PHP) - Large PHP community

### TDD Cycle 3.1: Prisma Adapter

#### Implementation Plan
```python
# src/adapters/prisma_adapter.py
class PrismaAdapter(FrameworkAdapter):
    """Adapter for Prisma ORM + TypeScript"""

    def generate_entity(self, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate Prisma schema model"""
        # Generate: prisma/schema.prisma

    def generate_action(self, action: UniversalAction, entity: UniversalEntity) -> List[GeneratedCode]:
        """Generate TypeScript service methods"""
        # Generate: src/services/{entity}.service.ts
```

**Generated Prisma Code**:
```prisma
// prisma/schema.prisma (auto-generated)
model Contact {
  pk_contact Int      @id @default(autoincrement()) @map("pk_contact")
  id         String   @unique @default(uuid()) @db.Uuid
  identifier String   @unique

  tenantId   String   @map("tenant_id") @db.Uuid

  email      String
  company    Company  @relation(fields: [fk_company], references: [pk_company])
  fk_company Int
  status     ContactStatus

  createdAt  DateTime @default(now()) @map("created_at")
  updatedAt  DateTime @updatedAt @map("updated_at")
  deletedAt  DateTime? @map("deleted_at")

  @@map("tb_contact")
  @@index([tenantId])
  @@index([fk_company])
  @@index([status])
}

enum ContactStatus {
  LEAD
  QUALIFIED
  CUSTOMER
}
```

```typescript
// src/services/contact.service.ts (auto-generated)
import { PrismaClient, Contact, ContactStatus } from '@prisma/client';

export class ContactService {
  constructor(private prisma: PrismaClient) {}

  async qualifyLead(contactId: string): Promise<MutationResult<Contact>> {
    const contact = await this.prisma.contact.findUnique({
      where: { id: contactId }
    });

    if (!contact) {
      throw new Error('Contact not found');
    }

    if (contact.status !== ContactStatus.LEAD) {
      throw new ValidationError('Contact must be a lead');
    }

    const updated = await this.prisma.contact.update({
      where: { id: contactId },
      data: { status: ContactStatus.QUALIFIED }
    });

    return {
      success: true,
      message: `${updated.identifier} qualified successfully`,
      objectData: updated
    };
  }
}
```

---

### TDD Cycle 3.2: Rails Adapter

#### Implementation Plan
```ruby
# app/models/contact.rb (auto-generated)
class Contact < ApplicationRecord
  self.primary_key = 'pk_contact'

  belongs_to :company, foreign_key: 'fk_company', primary_key: 'pk_company'

  enum status: { lead: 'lead', qualified: 'qualified', customer: 'customer' }

  validates :identifier, presence: true, uniqueness: true
  validates :email, presence: true

  def qualify_lead
    raise ValidationError, 'Contact must be a lead' unless lead?

    update!(status: :qualified)

    MutationResult.new(
      success: true,
      message: "#{identifier} qualified successfully",
      object_data: as_json
    )
  end
end
```

---

### TDD Cycle 3.3: Laravel Adapter

#### Implementation Plan
```php
// app/Models/Contact.php (auto-generated)
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Contact extends Model
{
    protected $table = 'tb_contact';
    protected $primaryKey = 'pk_contact';

    protected $fillable = [
        'identifier',
        'tenant_id',
        'email',
        'fk_company',
        'status'
    ];

    protected $casts = [
        'id' => 'string',
        'tenant_id' => 'string',
    ];

    public function company()
    {
        return $this->belongsTo(Company::class, 'fk_company', 'pk_company');
    }

    public function qualifyLead()
    {
        if ($this->status !== 'lead') {
            throw new ValidationException('Contact must be a lead');
        }

        $this->status = 'qualified';
        $this->save();

        return new MutationResult([
            'success' => true,
            'message' => "{$this->identifier} qualified successfully",
            'object_data' => $this->toArray()
        ]);
    }
}
```

---

### Phase 3 Deliverables

**Completed**:
- ✅ Prisma adapter (TypeScript ecosystem)
- ✅ Rails adapter (Ruby ecosystem)
- ✅ Laravel adapter (PHP ecosystem)

**CLI Usage**:
```bash
# Generate for all frameworks
specql generate entities/contact.yaml \
  --backends=postgresql,django,prisma,rails,laravel

# Output:
# ✓ Generated: db/schema/10_tables/contact.sql (PostgreSQL)
# ✓ Generated: crm/models/contact.py (Django)
# ✓ Generated: prisma/schema.prisma (Prisma)
# ✓ Generated: app/models/contact.rb (Rails)
# ✓ Generated: app/Models/Contact.php (Laravel)
```

**Ecosystem Coverage**:
- ✅ SQL: PostgreSQL
- ✅ Python: Django
- ✅ TypeScript: Prisma
- ✅ Ruby: Rails
- ✅ PHP: Laravel

---

## 📋 PHASE 4: Frontend Framework Support (6-8 weeks)

**Objective**: Generate frontend code (React Query, SWR, Vue) from same business logic.

### TDD Cycle 4.1: React Query Adapter

#### Implementation Plan
```typescript
// src/hooks/useQualifyLead.ts (auto-generated)
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';

export interface QualifyLeadInput {
  contactId: string;
}

export interface QualifyLeadResult {
  success: boolean;
  message: string;
  objectData: Contact;
}

/**
 * Qualify a lead contact
 *
 * Impacts: Contact, dashboard_stats
 */
export const useQualifyLead = () => {
  const queryClient = useQueryClient();

  return useMutation<QualifyLeadResult, Error, QualifyLeadInput>({
    mutationFn: async (input) => {
      const response = await api.post('/contacts/qualify_lead', input);
      return response.data;
    },

    onSuccess: (data) => {
      // Auto-invalidate based on impact metadata
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard_stats'] });
    },

    meta: {
      impacts: ['Contact', 'dashboard_stats'],
      description: 'Qualify a lead contact'
    }
  });
};
```

---

### TDD Cycle 4.2: SWR Adapter

```typescript
// src/api/useQualifyLead.ts (auto-generated)
import useSWRMutation from 'swr/mutation';
import { api } from './client';

export const useQualifyLead = () => {
  const { trigger, isMutating, error } = useSWRMutation(
    '/api/contacts/qualify_lead',
    async (url: string, { arg }: { arg: { contactId: string } }) => {
      const response = await api.post(url, arg);
      return response.data;
    },
    {
      onSuccess: () => {
        // Auto-revalidate impacted resources
        mutate('/api/contacts');
        mutate('/api/dashboard_stats');
      }
    }
  );

  return {
    qualifyLead: trigger,
    isLoading: isMutating,
    error
  };
};
```

---

### TDD Cycle 4.3: Vue Composition API Adapter

```typescript
// src/composables/useQualifyLead.ts (auto-generated)
import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { api } from '../api';

export const useQualifyLead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: { contactId: string }) => {
      const { data } = await api.post('/contacts/qualify_lead', input);
      return data;
    },

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard_stats'] });
    }
  });
};
```

---

### Phase 4 Deliverables

**Completed**:
- ✅ React Query hooks generator
- ✅ SWR hooks generator
- ✅ Vue Composition API generator
- ✅ Auto-invalidation based on impact metadata

**CLI Usage**:
```bash
# Generate frontend hooks
specql generate entities/contact.yaml \
  --frontend=react-query,swr,vue \
  --output-frontend=src/generated

# Output:
# ✓ Generated: src/generated/hooks/useQualifyLead.ts (React Query)
# ✓ Generated: src/generated/api/useQualifyLead.ts (SWR)
# ✓ Generated: src/generated/composables/useQualifyLead.ts (Vue)
```

---

## 📋 PHASE 5: Configuration & Developer Experience (4-6 weeks)

**Objective**: Make multi-framework generation configurable and delightful to use.

### TDD Cycle 5.1: Configuration System

#### Implementation
```yaml
# specql.config.yaml
version: 1.0

# Backend frameworks to generate
backends:
  - type: postgresql
    enabled: true
    output: db/schema/
    conventions:
      trinity_pattern: true
      audit_fields: true

  - type: django
    enabled: true
    output: backend/
    version: 4.2
    conventions:
      trinity_pattern: true
      migration_format: timestamp

  - type: prisma
    enabled: true
    output: prisma/
    conventions:
      client_output: node_modules/.prisma/client

# Frontend frameworks to generate
frontends:
  - type: react-query
    enabled: true
    output: src/hooks/
    version: 5.0

  - type: swr
    enabled: false
    output: src/api/

# Global conventions
conventions:
  naming_case: snake_case
  multi_tenant: true
  audit_fields: true

# Schema organization
schemas:
  multi_tenant:
    - crm
    - projects
  shared:
    - catalog
    - analytics
```

---

### TDD Cycle 5.2: Enhanced CLI

```bash
# Initialize new SpecQL project
specql init --backends=postgresql,django --frontend=react-query

# List available adapters
specql list-adapters
# Output:
# Backend Adapters:
#   - postgresql (built-in)
#   - django (built-in)
#   - prisma (built-in)
#   - rails (built-in)
#   - laravel (built-in)
# Frontend Adapters:
#   - react-query (built-in)
#   - swr (built-in)
#   - vue (built-in)

# Generate with config file
specql generate entities/*.yaml --config=specql.config.yaml

# Generate specific backends only
specql generate entities/contact.yaml --backends=django,prisma

# Watch mode for development
specql watch entities/ --backends=postgresql,django

# Diff between SpecQL and generated code
specql diff entities/contact.yaml --backend=django

# Validate SpecQL syntax
specql validate entities/*.yaml

# Generate documentation
specql docs entities/*.yaml --output=docs/
```

---

### TDD Cycle 5.3: VS Code Extension

```json
// .vscode/settings.json (auto-generated)
{
  "specql.backends": ["postgresql", "django"],
  "specql.frontends": ["react-query"],
  "specql.autoGenerate": true,
  "specql.configFile": "specql.config.yaml"
}
```

**Features**:
- Syntax highlighting for SpecQL YAML
- Auto-completion for field types, actions
- Inline validation errors
- Jump to generated code
- Auto-format on save

---

### Phase 5 Deliverables

**Completed**:
- ✅ Configuration file system (`specql.config.yaml`)
- ✅ Enhanced CLI with watch mode
- ✅ VS Code extension (basic)
- ✅ Comprehensive documentation

**Developer Experience**:
```bash
# One command to rule them all
specql generate entities/*.yaml

# Auto-generates:
# - PostgreSQL schema
# - Django models + migrations
# - Prisma schema
# - React Query hooks
# - TypeScript types
# - Documentation
```

---

## 📋 PHASE 6: Community & Ecosystem (Ongoing)

**Objective**: Enable community-contributed adapters and build ecosystem.

### TDD Cycle 6.1: Adapter Plugin System

#### Implementation
```python
# src/adapters/plugin_system.py
class AdapterPlugin(ABC):
    """Base class for community-contributed adapters"""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    def create_adapter(self) -> FrameworkAdapter:
        """Create adapter instance"""
        pass

# Allow community to publish adapters
class CommunityAdapterRegistry:
    """Registry for community adapters"""

    def install_adapter(self, package_name: str):
        """Install adapter from PyPI"""
        subprocess.run(['pip', 'install', package_name])
        self._load_adapter(package_name)
```

**Usage**:
```bash
# Install community adapter
specql install-adapter specql-supabase

# Use community adapter
specql generate entities/*.yaml --backends=supabase
```

---

### TDD Cycle 6.2: Adapter Template

Create adapter template repository for community:
```
specql-adapter-template/
├── src/
│   └── specql_adapter_myframework/
│       ├── __init__.py
│       ├── adapter.py          # Main adapter class
│       ├── entity_generator.py
│       ├── action_generator.py
│       └── tests/
├── pyproject.toml
├── README.md
└── ADAPTER_SPEC.md
```

**Documentation**:
- "Creating Your First Adapter" tutorial
- Adapter development guide
- Testing best practices
- Publishing to PyPI guide

---

### TDD Cycle 6.3: Adapter Marketplace

**Website**: `adapters.specql.dev`

Features:
- Browse available adapters
- Search by framework, language, popularity
- Installation instructions
- Ratings and reviews
- Compatibility matrix

---

### Phase 6 Deliverables

**Completed**:
- ✅ Plugin system for community adapters
- ✅ Adapter template repository
- ✅ Adapter marketplace website
- ✅ Comprehensive adapter development docs

**Community Adapters** (Examples):
- `specql-supabase` - Supabase adapter
- `specql-hasura` - Hasura metadata generator
- `specql-graphql-yoga` - GraphQL Yoga resolvers
- `specql-trpc` - tRPC router generator
- `specql-fastapi` - FastAPI endpoints
- `specql-nestjs` - NestJS modules

---

## 🎯 Success Metrics

### Technical Metrics
- **Adapter Count**: 5+ built-in, 10+ community adapters
- **Test Coverage**: 90%+ for all adapters
- **Generation Speed**: < 1 second for 100 entities
- **Code Quality**: All generated code passes linting

### Adoption Metrics
- **GitHub Stars**: 1,000+ stars
- **NPM Downloads**: 10,000+ monthly (if published to NPM)
- **Community Adapters**: 10+ published adapters
- **Documentation**: 100% API coverage

### Business Metrics
- **Time Savings**: 95% reduction in boilerplate code
- **Multi-framework Projects**: 50+ projects using 2+ backends
- **Developer NPS**: 50+ (promoter score)

---

## 🚧 Risks & Mitigations

### Risk 1: Framework API Changes
**Impact**: High - Framework updates could break adapters

**Mitigation**:
- Version-specific adapters (Django 4.2, Django 5.0)
- Automated CI tests against multiple framework versions
- Community contributions for updates

---

### Risk 2: Feature Parity
**Impact**: Medium - Not all frameworks support all features

**Mitigation**:
- Define "core feature set" all adapters must support
- Optional "extended features" per framework
- Clear documentation of limitations

---

### Risk 3: Complexity Creep
**Impact**: High - Too many frameworks = maintenance nightmare

**Mitigation**:
- Strict adapter interface contract
- Comprehensive test requirements for new adapters
- Community ownership of less-popular adapters

---

### Risk 4: Ecosystem Fragmentation
**Impact**: Medium - Too many community adapters of varying quality

**Mitigation**:
- Adapter certification program
- Quality badges (tested, maintained, popular)
- Official "blessed" adapters

---

## 📚 Documentation Plan

### User Documentation
1. **Getting Started** - Quick start for each framework
2. **Configuration Guide** - specql.config.yaml reference
3. **CLI Reference** - All commands and options
4. **Adapter Comparison** - Feature matrix
5. **Migration Guides** - Moving between frameworks

### Developer Documentation
1. **Architecture Overview** - Universal AST design
2. **Creating Adapters** - Step-by-step tutorial
3. **Testing Adapters** - Test requirements
4. **Publishing Adapters** - PyPI/NPM guide
5. **Contributing** - Contribution guidelines

---

## 🎯 Go-to-Market Strategy

### Messaging
**Tagline**: *Write business logic once. Deploy anywhere.*

**Value Propositions**:
1. **For Polyglot Teams**: One source of truth, multiple languages
2. **For Migrating Projects**: Gradual framework migration without rewrite
3. **For Startups**: Start fast, migrate later without tech debt
4. **For Enterprises**: Standardize business logic across departments

### Launch Plan

#### Phase 1: Internal Beta (Month 1-2)
- Use SpecQL multi-framework in own projects
- Gather feedback from early adopters
- Refine adapter interfaces

#### Phase 2: Public Alpha (Month 3-4)
- Open source PostgreSQL + Django adapters
- Blog post: "Introducing Multi-Framework SpecQL"
- Submit to Hacker News, Reddit

#### Phase 3: Public Beta (Month 5-6)
- Release Prisma, Rails, Laravel adapters
- Launch adapter marketplace
- Conference talks (PyCon, RailsConf, etc.)

#### Phase 4: 1.0 Release (Month 7-9)
- Production-ready all adapters
- Case studies from real projects
- Official partnerships (Django Foundation, etc.)

---

## 🏁 Conclusion

SpecQL's multi-framework evolution is **highly achievable** because:

1. **Architecture is Ready**: Universal AST already exists conceptually
2. **Proof of Concept Works**: PostgreSQL generator validates approach
3. **Market Need Exists**: Developers want framework flexibility
4. **Community Multiplier**: Plugin system enables ecosystem growth

**Timeline**: 6-9 months to production-ready multi-framework support

**Investment**: 1-2 full-time developers (or equivalent)

**ROI**: Massive - becomes the **universal standard** for business logic generation

---

## 📞 Next Steps

### Immediate (This Week)
1. Refactor Team A parser → Universal AST
2. Create FrameworkAdapter base class
3. Migrate PostgreSQL generator → PostgreSQL adapter
4. Validate no regressions in existing tests

### Short-term (This Month)
1. Implement Django adapter (proof-of-concept)
2. Generate side-by-side PostgreSQL + Django
3. Write comprehensive adapter development guide
4. Create adapter template repository

### Medium-term (Next Quarter)
1. Complete Prisma, Rails, Laravel adapters
2. Implement frontend framework support
3. Build configuration system
4. Launch adapter marketplace beta

### Long-term (Next Year)
1. Grow to 10+ community adapters
2. Achieve 1,000+ GitHub stars
3. Become the standard for multi-framework code generation
4. Explore commercial opportunities (enterprise support, hosted service)

---

**Status**: Ready to Execute
**Confidence**: High (Architecture proven, market validated)
**Next Milestone**: Universal AST + Django Adapter (6-8 weeks)

---

*Last Updated*: 2025-01-11
*Author*: SpecQL Core Team
*Document Version*: 1.0
