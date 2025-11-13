# Java AST Parsing Architecture

## Overview

SpecQL's Java reverse engineering capability enables automatic conversion of Java JPA entities to SpecQL YAML specifications. This document describes the technical architecture and implementation details.

## Architecture Components

### 1. JDT Bridge (`jdt_bridge.py`)

**Purpose**: Python-Java interoperability layer using Py4J

**Key Components**:
- `JDTBridge` class: Manages Java process lifecycle and Py4J gateway
- Singleton pattern ensures single JDT instance
- Automatic cleanup on shutdown

**Technical Details**:
```python
class JDTBridge:
    def __init__(self):
        self.gateway: Optional[JavaGateway] = None
        self.jdt_process: Optional[subprocess.Popen] = None
        self._start_jdt_server()

    def parse_java(self, source_code: str) -> CompilationUnit:
        """Parse Java source to Eclipse JDT AST"""
```

**Dependencies**:
- Py4J 0.10.9+
- Eclipse JDT Core 3.35.0+
- Java 11+ runtime

### 2. JPA Annotation Visitor (`jpa_visitor.py`)

**Purpose**: AST traversal to extract JPA annotations and metadata

**Supported Annotations**:
- `@Entity`, `@Table`, `@Column`
- `@Id`, `@GeneratedValue`
- `@ManyToOne`, `@OneToMany`, `@JoinColumn`
- `@Enumerated`, `@ElementCollection`
- `@Embedded`, `@Embeddable`

**Key Classes**:
- `JPAAnnotationVisitor`: Main visitor implementing annotation extraction
- `JPAEntity`: Data structure for parsed entity information
- `JPAField`: Data structure for field-level metadata

**Annotation Processing Logic**:
```python
def _extract_entity(self, type_decl) -> JPAEntity:
    # Extract @Table information
    # Process all fields with annotations
    # Build JPAEntity structure
```

### 3. Hibernate Type Mapper (`hibernate_type_mapper.py`)

**Purpose**: Convert Java/Hibernate types to SpecQL field types

**Type Mappings**:
```python
TYPE_MAPPING = {
    'int': 'integer', 'Integer': 'integer',
    'String': 'text', 'LocalDate': 'date',
    'LocalDateTime': 'timestamp', 'BigDecimal': 'decimal',
    'boolean': 'boolean', 'UUID': 'uuid',
    # ... additional mappings
}
```

**Relationship Handling**:
- `@ManyToOne` → `ref(entity)`
- `@OneToMany` → `list(entity)`
- `@ManyToMany` → `list(entity)` (simplified)

**Enum Processing**:
- `@Enumerated(EnumType.STRING)` → `enum` type
- Extracts enum values from Java enum classes

### 4. JPA to SpecQL Converter (`jpa_to_specql.py`)

**Purpose**: Transform JPA entities to SpecQL EntitySpec objects

**Conversion Process**:
1. Map entity class name to SpecQL entity name
2. Extract table name from `@Table` or generate from class name
3. Convert each JPAField to FieldSpec
4. Apply type mapping and validation

**Key Features**:
- Automatic ID field exclusion (handled by Trinity pattern)
- Schema extraction from `@Table.schema`
- Nullable/unique constraint mapping

### 5. Java Parser Orchestrator (`java_parser.py`)

**Purpose**: High-level coordination of Java parsing pipeline

**Key Methods**:
- `parse_file()`: Single file processing
- `parse_directory()`: Batch directory processing
- `parse_package()`: Package-level entity extraction
- `validate_parse_result()`: Confidence scoring

**Configuration Options**:
```python
@dataclass
class JavaParseConfig:
    include_patterns: List[str] = ["*.java"]
    exclude_patterns: List[str] = ["**/test/**", "**/*Test.java"]
    min_confidence: float = 0.8
    recursive: bool = True
```

## CLI Integration

### Command Usage

```bash
# Single file processing
specql reverse java Contact.java --output-dir entities/

# Directory processing
specql reverse java src/main/java/com/example/ --output-dir entities/

# Preview mode
specql reverse java Contact.java --preview

# Custom confidence threshold
specql reverse java Contact.java --min-confidence 0.9
```

### Output Format

Generated SpecQL YAML:
```yaml
entity: Contact
schema: public
table: contacts
fields:
  email:
    type: text
    nullable: false
  company:
    type: ref(Company)
  status:
    type: enum(active, inactive)
```

## Error Handling & Validation

### Error Categories
1. **Parse Errors**: JDT parsing failures, syntax errors
2. **Annotation Errors**: Missing or malformed JPA annotations
3. **Type Mapping Errors**: Unsupported Java types
4. **Validation Errors**: Schema inconsistencies

### Confidence Scoring
- **Entity Detection**: +0.5 for valid @Entity
- **Field Mapping**: +0.2 per successfully mapped field
- **Relationship Resolution**: +0.2 for valid relationships
- **Annotation Completeness**: +0.1 for complete metadata

### Fallback Mechanisms
- JDT server failure → Mock implementation
- Type mapping failure → `text` fallback
- Annotation parsing failure → Skip field

## Performance Characteristics

### Benchmarks
- **Single File**: < 500ms (JDT parsing + conversion)
- **Batch Processing**: < 5 seconds for 100 entities
- **Memory Usage**: ~50MB per JDT instance
- **Accuracy**: >95% for standard JPA patterns

### Optimization Strategies
1. **Singleton JDT Bridge**: Single Java process for all parsing
2. **Lazy Loading**: Initialize JDT only when needed
3. **Batch Processing**: Process multiple files per JDT session
4. **Caching**: AST caching for repeated parsing

## Supported Java Features

### JPA Versions
- **JPA 2.1+**: Full support for standard annotations
- **Hibernate**: Extended dialect support
- **Spring Data JPA**: Repository pattern compatibility

### Java Language Features
- **Generics**: `List<Entity>`, `Set<Entity>`
- **Enums**: `@Enumerated` with STRING/ORDINAL
- **Inheritance**: `@MappedSuperclass`, `@Inheritance`
- **Embedded Objects**: `@Embedded`, `@Embeddable`

### Limitations
- **Complex Inheritance**: TABLE_PER_CLASS strategy limited support
- **Custom Types**: User-defined types require manual mapping
- **Dynamic Queries**: JPQL/HQL parsing not supported
- **XML Configuration**: Annotation-based only

## Testing Strategy

### Unit Tests
- `test_jdt_bridge.py`: Java bridge connectivity
- `test_jpa_visitor.py`: Annotation extraction accuracy
- `test_hibernate_type_mapper.py`: Type mapping correctness
- `test_jpa_to_specql.py`: Conversion logic validation

### Integration Tests
- `test_java_parser.py`: End-to-end parsing pipeline
- `test_java_edge_cases.py`: Inheritance, embedded entities
- `test_spring_boot_entities.py`: Real-world Spring Boot projects

### Test Coverage Goals
- **Annotation Support**: 100% of common JPA annotations
- **Type Mapping**: 95% of Hibernate basic types
- **Error Handling**: All major error paths covered
- **Performance**: Sub-second parsing for typical entities

## Future Enhancements

### Planned Features
1. **Multi-Module Support**: Maven/Gradle project analysis
2. **Relationship Graph**: Automatic foreign key inference
3. **Validation Rules**: JPA constraint extraction
4. **Migration Scripts**: Automatic schema migration generation

### Research Areas
1. **Tree-sitter Integration**: Alternative parsing backend
2. **Java 21+ Support**: Modern Java language features
3. **Microservice Detection**: Service boundary analysis
4. **Legacy Code Support**: EJB 2.x to JPA migration

## Troubleshooting

### Common Issues

**JDT Server Connection Failed**
```
Error: An error occurred while trying to connect to the Java server
```
**Solution**: Ensure Java 11+ is installed and JDT JARs are available

**Annotation Not Recognized**
```
Warning: Unknown annotation @CustomAnnotation
```
**Solution**: Verify annotation is in supported list or add custom mapping

**Type Mapping Failed**
```
Warning: Could not map type 'CustomType' to SpecQL type
```
**Solution**: Add custom type mapping in `HibernateTypeMapper`

### Debug Mode
Enable detailed logging:
```bash
export JAVA_PARSER_DEBUG=1
specql reverse java --verbose
```

## API Reference

### JavaParser Class
```python
class JavaParser:
    def parse_file(self, file_path: str) -> JavaParseResult
    def parse_directory(self, dir_path: str, config: JavaParseConfig) -> List[JavaParseResult]
    def validate_parse_result(self, result: JavaParseResult) -> Dict[str, Any]
```

### Data Structures
```python
@dataclass
class JavaParseResult:
    file_path: str
    entities: List[Entity]
    errors: List[str]

@dataclass
class JPAEntity:
    class_name: str
    table_name: Optional[str]
    fields: List[JPAField]
```

## Related Documentation

- [Week 09 Implementation Plan](../implementation_plans/WEEK_09.md)
- [Spring Boot Migration Guide](SPRING_BOOT_MIGRATION.md)
- [Java Reverse Engineering API](JAVA_REVERSE_ENGINEERING_API.md)
- [Multi-Language AST Design](../architecture/MULTI_LANGUAGE_AST_DESIGN.md)