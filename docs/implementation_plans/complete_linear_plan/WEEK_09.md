# Week 09: Java AST Parser & JPA Extraction

**Date**: TBD (After Week 8 + 2 week stabilization)
**Duration**: 5 days
**Status**: 📅 Planned
**Objective**: Build Java AST parser to extract JPA entities and map to SpecQL universal format

**Prerequisites**:
- Week 8 complete (PrintOptim migration validated)
- 2-week stabilization period complete
- Python reverse engineering working (from foundation)

**Output**:
- Java AST parser using Eclipse JDT
- JPA annotation extraction
- Hibernate/JPA type mapping to SpecQL
- 50+ passing tests

---

## 🎯 Executive Summary

This week begins Phase 2 (Multi-Language Backend Expansion) by adding Java/Spring Boot support to SpecQL. We'll leverage Eclipse JDT (Java Development Tools) to parse Java source code, extract JPA (Java Persistence API) annotations, and map them to SpecQL's universal entity model.

The goal is to enable:
```java
// Java JPA Entity
@Entity
@Table(name = "contacts")
public class Contact {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String email;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;

    @Enumerated(EnumType.STRING)
    private ContactStatus status;
}
```

↓↓↓ **SpecQL Reverse Engineering** ↓↓↓

```yaml
# SpecQL YAML (generated)
entity: Contact
schema: crm
fields:
  email: text
  company: ref(Company)
  status: enum(lead, qualified, customer)
```

This establishes the foundation for Java → SpecQL reverse engineering that will enable migration of Java/Spring Boot applications to SpecQL-generated schemas.

---

## 📅 Daily Breakdown

### Day 1: Java Parser Foundation

**Morning Block (4 hours): Eclipse JDT Setup & Exploration**

#### 1. Research & Setup (2 hours)

**Research Document**: `docs/research/JAVA_AST_PARSING_OPTIONS.md`

```markdown
# Java AST Parsing Options

## Option 1: Eclipse JDT (Java Development Tools) ✅ CHOSEN
**Pros**:
- Official Eclipse Java parser
- Complete AST representation
- Widely used, well-tested
- Excellent annotation support
- Can parse Java 8-21

**Cons**:
- Java library (requires Py4J or subprocess)
- More complex setup

## Option 2: JavaParser
**Pros**:
- Pure Java, simpler API
- Good documentation

**Cons**:
- Less comprehensive than JDT
- Requires Java bridge

## Option 3: Tree-sitter (tree-sitter-java)
**Pros**:
- Fast, incremental parsing
- Python bindings available

**Cons**:
- Less semantic information
- Harder to extract annotations

## Decision: Eclipse JDT via Py4J
- Most comprehensive AST
- Best annotation support
- Industry standard for Java parsing
```

**Setup Task**: Install dependencies

```bash
# Install Py4J for Python-Java bridge
uv add py4j

# Download Eclipse JDT Core
mkdir -p lib/jdt
cd lib/jdt
wget https://download.eclipse.org/eclipse/downloads/drops4/R-4.29-202309031000/org.eclipse.jdt.core_3.35.0.v20230913-1200.jar

# Create Java wrapper for JDT
cat > lib/jdt/JDTWrapper.java << 'EOF'
import org.eclipse.jdt.core.dom.*;
import py4j.GatewayServer;

public class JDTWrapper {
    public CompilationUnit parse(String source) {
        ASTParser parser = ASTParser.newParser(AST.JLS_Latest);
        parser.setSource(source.toCharArray());
        parser.setKind(ASTParser.K_COMPILATION_UNIT);
        return (CompilationUnit) parser.createAST(null);
    }

    public static void main(String[] args) {
        JDTWrapper app = new JDTWrapper();
        GatewayServer server = new GatewayServer(app);
        server.start();
    }
}
EOF

# Compile Java wrapper
javac -cp "org.eclipse.jdt.core_3.35.0.v20230913-1200.jar:py4j0.10.9.7.jar" JDTWrapper.java
```

---

#### 2. Basic Parser Implementation (2 hours)

**Module**: `src/reverse_engineering/java/jdt_bridge.py`

```python
"""
Eclipse JDT Bridge

Python bridge to Eclipse JDT for parsing Java code.
Uses Py4J to communicate with Java process running JDT.
"""

import subprocess
from typing import Optional
from py4j.java_gateway import JavaGateway, GatewayParameters
import atexit


class JDTBridge:
    """Bridge to Eclipse JDT Java parser"""

    def __init__(self):
        self.gateway: Optional[JavaGateway] = None
        self.jdt_process: Optional[subprocess.Popen] = None
        self._start_jdt_server()

    def _start_jdt_server(self):
        """Start JDT Java process"""
        # Start Java process with JDT wrapper
        self.jdt_process = subprocess.Popen([
            'java',
            '-cp', 'lib/jdt/org.eclipse.jdt.core_3.35.0.v20230913-1200.jar:lib/jdt/py4j0.10.9.7.jar:lib/jdt/',
            'JDTWrapper'
        ])

        # Connect to gateway
        self.gateway = JavaGateway(gateway_parameters=GatewayParameters(auto_convert=True))

        # Register cleanup
        atexit.register(self.shutdown)

    def parse_java(self, source_code: str):
        """
        Parse Java source code to AST

        Args:
            source_code: Java source code as string

        Returns:
            CompilationUnit AST
        """
        if not self.gateway:
            raise RuntimeError("JDT gateway not initialized")

        wrapper = self.gateway.entry_point
        return wrapper.parse(source_code)

    def shutdown(self):
        """Shutdown JDT server"""
        if self.gateway:
            self.gateway.shutdown()
        if self.jdt_process:
            self.jdt_process.terminate()
            self.jdt_process.wait()


# Singleton instance
_jdt_bridge: Optional[JDTBridge] = None

def get_jdt_bridge() -> JDTBridge:
    """Get singleton JDT bridge instance"""
    global _jdt_bridge
    if _jdt_bridge is None:
        _jdt_bridge = JDTBridge()
    return _jdt_bridge
```

---

**Afternoon Block (4 hours): JPA Annotation Extraction**

#### 3. JPA Annotation Visitor (2 hours)

**Module**: `src/reverse_engineering/java/jpa_visitor.py`

```python
"""
JPA Annotation Visitor

Extracts JPA annotations from Java AST to identify:
- Entities (@Entity)
- Fields and their types
- Relationships (@ManyToOne, @OneToMany, etc.)
- Column mappings (@Column, @JoinColumn)
- Enums (@Enumerated)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from py4j.java_collections import JavaList


@dataclass
class JPAField:
    """Represents a field in a JPA entity"""
    name: str
    java_type: str
    column_name: Optional[str] = None
    nullable: bool = True
    unique: bool = False
    length: Optional[int] = None

    # Relationship info
    is_relationship: bool = False
    relationship_type: Optional[str] = None  # ManyToOne, OneToMany, etc.
    target_entity: Optional[str] = None
    join_column: Optional[str] = None

    # Enum info
    is_enum: bool = False
    enum_type: Optional[str] = None  # STRING or ORDINAL


@dataclass
class JPAEntity:
    """Represents a JPA entity class"""
    class_name: str
    table_name: Optional[str] = None
    schema: Optional[str] = None
    fields: List[JPAField] = field(default_factory=list)
    id_field: Optional[str] = None


class JPAAnnotationVisitor:
    """Visit Java AST and extract JPA annotations"""

    def __init__(self, compilation_unit):
        """
        Initialize visitor

        Args:
            compilation_unit: Eclipse JDT CompilationUnit
        """
        self.cu = compilation_unit
        self.entities: List[JPAEntity] = []

    def visit(self) -> List[JPAEntity]:
        """Visit AST and extract JPA entities"""
        # Get all types in compilation unit
        types = self.cu.types()

        for type_decl in types:
            if self._is_entity(type_decl):
                entity = self._extract_entity(type_decl)
                self.entities.append(entity)

        return self.entities

    def _is_entity(self, type_decl) -> bool:
        """Check if type is a JPA entity"""
        modifiers = type_decl.modifiers()

        for modifier in modifiers:
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()
                if annotation_name in ('Entity', 'jakarta.persistence.Entity', 'javax.persistence.Entity'):
                    return True

        return False

    def _extract_entity(self, type_decl) -> JPAEntity:
        """Extract entity information from type declaration"""
        class_name = type_decl.getName().getIdentifier()

        # Extract @Table annotation
        table_name = None
        schema = None

        for modifier in type_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()

                if annotation_name in ('Table', 'jakarta.persistence.Table', 'javax.persistence.Table'):
                    table_info = self._extract_table_annotation(modifier)
                    table_name = table_info.get('name')
                    schema = table_info.get('schema')

        # Create entity
        entity = JPAEntity(
            class_name=class_name,
            table_name=table_name or self._to_snake_case(class_name),
            schema=schema
        )

        # Extract fields
        for field_decl in type_decl.bodyDeclarations():
            if field_decl.getNodeType() == field_decl.FIELD_DECLARATION:
                jpa_field = self._extract_field(field_decl)
                entity.fields.append(jpa_field)

                # Check if ID field
                if self._is_id_field(field_decl):
                    entity.id_field = jpa_field.name

        return entity

    def _extract_field(self, field_decl) -> JPAField:
        """Extract field information"""
        # Get field name
        fragments = field_decl.fragments()
        field_name = fragments[0].getName().getIdentifier()

        # Get field type
        field_type = field_decl.getType().toString()

        # Initialize field
        jpa_field = JPAField(
            name=field_name,
            java_type=field_type
        )

        # Extract annotations
        for modifier in field_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()

                if annotation_name in ('Column', 'jakarta.persistence.Column', 'javax.persistence.Column'):
                    column_info = self._extract_column_annotation(modifier)
                    jpa_field.column_name = column_info.get('name')
                    jpa_field.nullable = column_info.get('nullable', True)
                    jpa_field.unique = column_info.get('unique', False)
                    jpa_field.length = column_info.get('length')

                elif annotation_name in ('ManyToOne', 'jakarta.persistence.ManyToOne', 'javax.persistence.ManyToOne'):
                    jpa_field.is_relationship = True
                    jpa_field.relationship_type = 'ManyToOne'
                    jpa_field.target_entity = field_type

                elif annotation_name in ('OneToMany', 'jakarta.persistence.OneToMany', 'javax.persistence.OneToMany'):
                    jpa_field.is_relationship = True
                    jpa_field.relationship_type = 'OneToMany'
                    # Extract target from generic type
                    jpa_field.target_entity = self._extract_generic_type(field_type)

                elif annotation_name in ('JoinColumn', 'jakarta.persistence.JoinColumn', 'javax.persistence.JoinColumn'):
                    join_info = self._extract_join_column_annotation(modifier)
                    jpa_field.join_column = join_info.get('name')

                elif annotation_name in ('Enumerated', 'jakarta.persistence.Enumerated', 'javax.persistence.Enumerated'):
                    jpa_field.is_enum = True
                    enum_info = self._extract_enumerated_annotation(modifier)
                    jpa_field.enum_type = enum_info.get('value', 'ORDINAL')

        return jpa_field

    def _is_id_field(self, field_decl) -> bool:
        """Check if field is annotated with @Id"""
        for modifier in field_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()
                if annotation_name in ('Id', 'jakarta.persistence.Id', 'javax.persistence.Id'):
                    return True
        return False

    def _extract_table_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @Table annotation values"""
        values = {}

        if annotation.isSingleMemberAnnotation():
            values['name'] = self._get_annotation_value(annotation.getValue())
        elif annotation.isNormalAnnotation():
            for pair in annotation.values():
                key = pair.getName().getIdentifier()
                value = self._get_annotation_value(pair.getValue())
                values[key] = value

        return values

    def _extract_column_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @Column annotation values"""
        return self._extract_table_annotation(annotation)  # Same logic

    def _extract_join_column_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @JoinColumn annotation values"""
        return self._extract_table_annotation(annotation)  # Same logic

    def _extract_enumerated_annotation(self, annotation) -> Dict[str, Any]:
        """Extract @Enumerated annotation values"""
        return self._extract_table_annotation(annotation)  # Same logic

    def _get_annotation_value(self, value_node):
        """Extract value from annotation"""
        # Handle string literals
        if value_node.getNodeType() == value_node.STRING_LITERAL:
            return value_node.getLiteralValue()

        # Handle boolean literals
        if value_node.getNodeType() == value_node.BOOLEAN_LITERAL:
            return value_node.booleanValue()

        # Handle number literals
        if value_node.getNodeType() == value_node.NUMBER_LITERAL:
            return int(value_node.getToken())

        # Handle qualified names (e.g., EnumType.STRING)
        if value_node.getNodeType() == value_node.QUALIFIED_NAME:
            return value_node.getFullyQualifiedName().split('.')[-1]

        return None

    def _extract_generic_type(self, type_str: str) -> Optional[str]:
        """Extract generic type from List<Entity>"""
        if '<' in type_str and '>' in type_str:
            start = type_str.index('<') + 1
            end = type_str.index('>')
            return type_str[start:end].strip()
        return None

    def _to_snake_case(self, camel_case: str) -> str:
        """Convert CamelCase to snake_case"""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()
```

---

#### 4. Initial Tests (2 hours)

**Test File**: `tests/unit/reverse_engineering/java/test_jpa_visitor.py`

```python
"""Tests for JPA annotation visitor"""

import pytest
from src.reverse_engineering.java.jdt_bridge import get_jdt_bridge
from src.reverse_engineering.java.jpa_visitor import JPAAnnotationVisitor


class TestJPAAnnotationVisitor:
    """Test JPA annotation extraction"""

    @pytest.fixture
    def jdt_bridge(self):
        return get_jdt_bridge()

    def test_simple_entity_extraction(self, jdt_bridge):
        """Test extracting a simple JPA entity"""
        java_code = """
import jakarta.persistence.*;

@Entity
@Table(name = "contacts")
public class Contact {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String email;

    private String name;
}
"""

        # Parse Java code
        cu = jdt_bridge.parse_java(java_code)

        # Extract entities
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        # Assertions
        assert len(entities) == 1
        entity = entities[0]

        assert entity.class_name == "Contact"
        assert entity.table_name == "contacts"
        assert entity.id_field == "id"
        assert len(entity.fields) == 3

        # Check email field
        email_field = next(f for f in entity.fields if f.name == "email")
        assert email_field.nullable == False
        assert email_field.java_type == "String"

    def test_relationship_extraction(self, jdt_bridge):
        """Test extracting JPA relationships"""
        java_code = """
import jakarta.persistence.*;

@Entity
public class Contact {
    @Id
    private Long id;

    @ManyToOne
    @JoinColumn(name = "company_id")
    private Company company;
}
"""

        cu = jdt_bridge.parse_java(java_code)
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        assert len(entities) == 1
        entity = entities[0]

        company_field = next(f for f in entity.fields if f.name == "company")
        assert company_field.is_relationship == True
        assert company_field.relationship_type == "ManyToOne"
        assert company_field.target_entity == "Company"
        assert company_field.join_column == "company_id"

    def test_enum_field_extraction(self, jdt_bridge):
        """Test extracting enum fields"""
        java_code = """
import jakarta.persistence.*;

@Entity
public class Contact {
    @Id
    private Long id;

    @Enumerated(EnumType.STRING)
    private ContactStatus status;
}
"""

        cu = jdt_bridge.parse_java(java_code)
        visitor = JPAAnnotationVisitor(cu)
        entities = visitor.visit()

        assert len(entities) == 1
        entity = entities[0]

        status_field = next(f for f in entity.fields if f.name == "status")
        assert status_field.is_enum == True
        assert status_field.enum_type == "STRING"
```

---

**Day 1 Deliverables**:
- ✅ JDT bridge implemented
- ✅ JPA annotation visitor working
- ✅ Basic entity extraction tests passing
- ✅ Relationship and enum extraction working

---

### Day 2: Hibernate Type Mapping

**Morning Block (4 hours): Type System Mapping**

Build comprehensive mapping from Hibernate/JPA types to SpecQL types.

**Module**: `src/reverse_engineering/java/hibernate_type_mapper.py`

```python
"""
Hibernate Type Mapper

Maps Hibernate/JPA Java types to SpecQL types.
"""

from typing import Optional, Dict, Any
from src.core.ast_models import FieldType


class HibernateTypeMapper:
    """Map Hibernate/JPA types to SpecQL types"""

    # Java primitive and wrapper types → SpecQL
    TYPE_MAPPING = {
        # Primitives
        'int': 'integer',
        'long': 'integer',
        'short': 'integer',
        'byte': 'integer',
        'float': 'decimal',
        'double': 'decimal',
        'boolean': 'boolean',

        # Wrappers
        'Integer': 'integer',
        'Long': 'integer',
        'Short': 'integer',
        'Byte': 'integer',
        'Float': 'decimal',
        'Double': 'decimal',
        'Boolean': 'boolean',

        # String
        'String': 'text',
        'char': 'text',
        'Character': 'text',

        # Date/Time (java.time)
        'LocalDate': 'date',
        'LocalDateTime': 'timestamp',
        'LocalTime': 'time',
        'Instant': 'timestamp',
        'ZonedDateTime': 'timestamp',

        # Date/Time (legacy java.util)
        'Date': 'timestamp',
        'Timestamp': 'timestamp',

        # Binary
        'byte[]': 'blob',
        'Byte[]': 'blob',

        # UUID
        'UUID': 'uuid',

        # JSON
        'JsonNode': 'json',
        'Map': 'json',
    }

    def map_type(
        self,
        java_type: str,
        jpa_field
    ) -> FieldType:
        """
        Map Java/JPA type to SpecQL FieldType

        Args:
            java_type: Java type string (e.g., "String", "Long")
            jpa_field: JPAField with annotation metadata

        Returns:
            SpecQL FieldType
        """
        # Handle relationships
        if jpa_field.is_relationship:
            if jpa_field.relationship_type == 'ManyToOne':
                return FieldType(
                    type='ref',
                    ref_entity=jpa_field.target_entity
                )
            elif jpa_field.relationship_type == 'OneToMany':
                return FieldType(
                    type='list',
                    ref_entity=jpa_field.target_entity
                )

        # Handle enums
        if jpa_field.is_enum:
            return FieldType(
                type='enum',
                # Note: actual enum values need to be extracted from Java enum class
            )

        # Handle collections
        if java_type.startswith('List<') or java_type.startswith('Set<'):
            inner_type = self._extract_generic_type(java_type)
            return FieldType(
                type='list',
                ref_entity=inner_type if inner_type else None
            )

        # Map simple types
        specql_type = self.TYPE_MAPPING.get(java_type, 'text')

        return FieldType(type=specql_type)

    def _extract_generic_type(self, type_str: str) -> Optional[str]:
        """Extract generic type from List<Entity>"""
        if '<' in type_str and '>' in type_str:
            start = type_str.index('<') + 1
            end = type_str.index('>')
            return type_str[start:end].strip()
        return None
```

---

**Afternoon Block (4 hours): Entity to SpecQL Converter**

Convert JPAEntity → SpecQL EntitySpec

**Module**: `src/reverse_engineering/java/jpa_to_specql.py`

```python
"""
JPA to SpecQL Converter

Converts JPA entities to SpecQL entity specifications.
"""

from src.reverse_engineering.java.jpa_visitor import JPAEntity
from src.reverse_engineering.java.hibernate_type_mapper import HibernateTypeMapper
from src.core.ast_models import EntitySpec, FieldSpec


class JPAToSpecQLConverter:
    """Convert JPA entities to SpecQL"""

    def __init__(self):
        self.type_mapper = HibernateTypeMapper()

    def convert(self, jpa_entity: JPAEntity) -> EntitySpec:
        """
        Convert JPA entity to SpecQL EntitySpec

        Args:
            jpa_entity: Parsed JPA entity

        Returns:
            SpecQL EntitySpec
        """
        # Convert fields
        fields = []
        for jpa_field in jpa_entity.fields:
            # Skip ID field (Trinity pattern handles this)
            if jpa_field.name == jpa_entity.id_field:
                continue

            # Map type
            field_type = self.type_mapper.map_type(
                jpa_field.java_type,
                jpa_field
            )

            # Create FieldSpec
            field_spec = FieldSpec(
                name=jpa_field.name,
                type=field_type,
                nullable=jpa_field.nullable,
                unique=jpa_field.unique
            )

            fields.append(field_spec)

        # Create EntitySpec
        entity_spec = EntitySpec(
            name=jpa_entity.class_name,
            schema=jpa_entity.schema or 'public',
            table_name=jpa_entity.table_name,
            fields=fields
        )

        return entity_spec
```

---

**Day 2 Deliverables**:
- ✅ Hibernate type mapper complete
- ✅ JPAEntity → EntitySpec converter working
- ✅ Type mapping tests passing

---

### Days 3-4: Integration & Testing

**Day 3**:
- Complete Java AST parser orchestrator
- Integration tests with real Spring Boot entities
- Handle edge cases (inheritance, embedded entities)

**Day 4**:
- Performance optimization
- Error handling and validation
- Batch processing for multiple files

---

### Day 5: CLI Integration & Documentation

**Morning Block (4 hours)**: CLI commands

```bash
# Reverse engineer Java file
specql reverse java Contact.java --output entities/contact.yaml

# Reverse engineer entire package
specql reverse java src/main/java/com/example/models/ --output entities/

# With confidence threshold
specql reverse java Contact.java --min-confidence 0.80
```

**Afternoon Block (4 hours)**: Documentation

- Architecture docs
- API reference
- Migration guide (Spring Boot → SpecQL)
- Examples

---

## ✅ Success Criteria

- [ ] Eclipse JDT bridge working (Java ↔ Python)
- [ ] JPA annotation extraction complete (Entity, Table, Column, relationships, enums)
- [ ] Hibernate type mapping covers 95% of common types
- [ ] JPAEntity → SpecQL EntitySpec conversion working
- [ ] 50+ unit tests passing (>95% coverage)
- [ ] 5+ integration tests with real Spring Boot entities
- [ ] CLI integration complete (`specql reverse java`)
- [ ] Documentation complete

---

## 🧪 Testing Strategy

**Unit Tests** (`tests/unit/reverse_engineering/java/`):
- `test_jdt_bridge.py` - Java parsing
- `test_jpa_visitor.py` - Annotation extraction
- `test_hibernate_type_mapper.py` - Type mapping
- `test_jpa_to_specql.py` - Conversion logic

**Integration Tests** (`tests/integration/java/`):
- `test_spring_boot_entities.py` - Real Spring Boot entities
- `test_batch_processing.py` - Multiple files

**Performance Benchmarks**:
- Parse 100 Java entities in <5 seconds
- Type mapping accuracy >95%

---

## 📚 Documentation

- `docs/reverse_engineering/JAVA_AST_PARSING.md` - Technical architecture
- `docs/guides/SPRING_BOOT_MIGRATION.md` - Migration guide
- `docs/api/JAVA_REVERSE_ENGINEERING_API.md` - API reference

---

## 🔗 Related Files

- **Previous**: [Week 08: Production Migration](./WEEK_08.md)
- **Next**: [Week 10: Spring Boot Pattern Recognition](./WEEK_10_SPRING_BOOT_PATTERNS.md)
- **Architecture**: [Multi-Language AST Design](../architecture/MULTI_LANGUAGE_AST_DESIGN.md)
- **Foundation**: [Python Reverse Engineering](./done/WEEK_7_8_PYTHON_REVERSE_ENGINEERING.md)

---

**Week 9 Status**: 📅 Planned (starts after Week 8 + stabilization)
**Estimated Effort**: 40 hours (5 days × 8 hours)
**Risk Level**: Medium (new Java bridge, type system complexity)
**Dependencies**: Week 8 complete, foundation working
