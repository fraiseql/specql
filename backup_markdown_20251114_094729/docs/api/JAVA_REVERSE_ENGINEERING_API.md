# Java Reverse Engineering API Reference

## Overview

The Java Reverse Engineering API provides programmatic access to SpecQL's Java AST parsing and JPA entity extraction capabilities. This API enables integration with build tools, IDEs, and custom migration workflows.

## Core Classes

### JavaParser

Main orchestrator for Java reverse engineering operations.

#### Constructor
```python
JavaParser()
```

#### Methods

##### parse_file(file_path: str) -> JavaParseResult
Parse a single Java file and extract JPA entities.

**Parameters:**
- `file_path` (str): Absolute path to Java file

**Returns:**
- `JavaParseResult`: Parsing results with entities and errors

**Example:**
```python
parser = JavaParser()
result = parser.parse_file("src/main/java/User.java")

for entity in result.entities:
    print(f"Found entity: {entity.name}")
```

##### parse_directory(directory_path: str, config: JavaParseConfig = None) -> List[JavaParseResult]
Parse all Java files in a directory recursively.

**Parameters:**
- `directory_path` (str): Path to directory containing Java files
- `config` (JavaParseConfig, optional): Parsing configuration

**Returns:**
- `List[JavaParseResult]`: Results for each processed file

**Example:**
```python
config = JavaParseConfig(
    include_patterns=["*.java"],
    exclude_patterns=["**/test/**"],
    recursive=True
)

results = parser.parse_directory("src/main/java/", config)
total_entities = sum(len(r.entities) for r in results)
```

##### parse_package(package_path: str, config: JavaParseConfig = None) -> Dict[str, List[Entity]]
Parse a Java package and return entities grouped by file.

**Parameters:**
- `package_path` (str): Path to Java package directory
- `config` (JavaParseConfig, optional): Parsing configuration

**Returns:**
- `Dict[str, List[Entity]]`: Mapping of file paths to entity lists

**Example:**
```python
entities_by_file = parser.parse_package("src/main/java/com/example/")

for file_path, entities in entities_by_file.items():
    print(f"{file_path}: {len(entities)} entities")
```

##### validate_parse_result(result: JavaParseResult) -> Dict[str, Any]
Validate parsing results and return confidence metrics.

**Parameters:**
- `result` (JavaParseResult): Result to validate

**Returns:**
- `Dict[str, Any]`: Validation metrics including confidence score

**Example:**
```python
metrics = parser.validate_parse_result(result)
confidence = metrics["confidence"]
error_count = metrics["error_count"]

if confidence > 0.8:
    print("High confidence parsing result")
```

### JavaParseConfig

Configuration class for Java parsing operations.

#### Attributes
- `include_patterns` (List[str]): File patterns to include (default: `["*.java"]`)
- `exclude_patterns` (List[str]): File patterns to exclude (default: `["**/test/**", "**/*Test.java"]`)
- `min_confidence` (float): Minimum confidence threshold (default: 0.8)
- `recursive` (bool): Whether to parse subdirectories (default: True)

**Example:**
```python
config = JavaParseConfig(
    include_patterns=["*.java", "*.kt"],  # Include Kotlin files
    exclude_patterns=["**/generated/**", "**/*Test.java"],
    min_confidence=0.9,
    recursive=False  # Only parse top-level directory
)
```

### JavaParseResult

Result container for Java file parsing operations.

#### Attributes
- `file_path` (str): Path to the parsed file
- `entities` (List[Entity]): Extracted SpecQL entities
- `errors` (List[str]): Parsing errors encountered

**Example:**
```python
result = parser.parse_file("User.java")

if result.errors:
    print(f"Errors: {result.errors}")

for entity in result.entities:
    print(f"Entity: {entity.name}, Table: {entity.table}")
```

## Data Structures

### Entity

SpecQL entity specification (from `src.core.ast_models`).

#### Attributes
- `name` (str): Entity name
- `schema` (str): Database schema
- `table` (str): Table name
- `fields` (Dict[str, FieldSpec]): Field specifications

### FieldSpec

Field specification within an entity.

#### Attributes
- `type_name` (str): Field type (e.g., "text", "integer", "ref(User)")
- `nullable` (bool): Whether field can be null
- `unique` (bool): Whether field has unique constraint

## Advanced Usage

### Custom Type Mapping

Extend the default type mapper for custom Java types.

```python
from src.reverse_engineering.java.hibernate_type_mapper import HibernateTypeMapper

class CustomTypeMapper(HibernateTypeMapper):
    def map_type(self, java_type: str, jpa_field) -> FieldType:
        # Custom mapping for your types
        if java_type == "CustomMoneyType":
            return FieldType(type="decimal", precision=10, scale=2)

        # Fall back to default mapping
        return super().map_type(java_type, jpa_field)

# Use custom mapper
from src.reverse_engineering.java.jpa_to_specql import JPAToSpecQLConverter

converter = JPAToSpecQLConverter()
converter.type_mapper = CustomTypeMapper()
```

### Batch Processing with Progress

Process large codebases with progress tracking.

```python
import os
from tqdm import tqdm

def process_large_codebase(root_path: str):
    parser = JavaParser()
    all_results = []

    # Find all Java files
    java_files = []
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))

    # Process with progress bar
    for java_file in tqdm(java_files, desc="Processing Java files"):
        try:
            result = parser.parse_file(java_file)
            all_results.append(result)
        except Exception as e:
            print(f"Failed to process {java_file}: {e}")

    return all_results
```

### Integration with Build Tools

#### Gradle Plugin Integration
```kotlin
// build.gradle.kts
plugins {
    id("com.specql.reverse-engineering") version "1.0.0"
}

tasks.register("reverseEngineer") {
    doLast {
        exec {
            workingDir = projectDir
            commandLine("python", "-m", "specql.reverse", "java", "src/main/java", "--output-dir", "schemas")
        }
    }
}
```

#### Maven Plugin Integration
```xml
<!-- pom.xml -->
<plugin>
    <groupId>com.specql</groupId>
    <artifactId>specql-maven-plugin</artifactId>
    <version>1.0.0</version>
    <executions>
        <execution>
            <phase>generate-sources</phase>
            <goals>
                <goal>reverse-engineer</goal>
            </goals>
        </execution>
    </executions>
    <configuration>
        <sourceDirectory>src/main/java</sourceDirectory>
        <outputDirectory>target/schemas</outputDirectory>
    </configuration>
</plugin>
```

### Error Handling

Comprehensive error handling for production use.

```python
def safe_parse_file(parser: JavaParser, file_path: str) -> Optional[JavaParseResult]:
    """Safely parse a file with comprehensive error handling."""
    try:
        result = parser.parse_file(file_path)

        # Check for critical errors
        if result.errors:
            logger.warning(f"Parsing errors in {file_path}: {result.errors}")

        # Validate result quality
        metrics = parser.validate_parse_result(result)
        if metrics["confidence"] < 0.5:
            logger.error(f"Low confidence parsing result for {file_path}")
            return None

        return result

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing {file_path}: {e}")
        return None
```

## CLI Integration

### Command Line Usage

The API is accessible through the `specql reverse java` command.

```bash
# Single file
specql reverse java User.java --output-dir schemas/

# Directory (recursive)
specql reverse java src/main/java/ --output-dir schemas/

# Custom configuration
specql reverse java . --min-confidence 0.9 --output-dir schemas/

# Preview mode
specql reverse java User.java --preview
```

### Programmatic CLI Usage

Use the API programmatically in scripts.

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from src.reverse_engineering.java.java_parser import JavaParser, JavaParseConfig
import yaml

def main():
    if len(sys.argv) < 2:
        print("Usage: python reverse_java.py <java_file_or_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = Path("schemas")
    output_dir.mkdir(exist_ok=True)

    parser = JavaParser()
    path = Path(input_path)

    if path.is_file():
        # Single file
        result = parser.parse_file(str(path))
        if result.entities:
            output_file(result.entities[0], output_dir)
    elif path.is_dir():
        # Directory
        config = JavaParseConfig(recursive=True)
        results = parser.parse_directory(str(path), config)

        for result in results:
            for entity in result.entities:
                output_file(entity, output_dir)

def output_file(entity, output_dir: Path):
    """Write entity to YAML file."""
    entity_dict = {
        "entity": entity.name,
        "schema": entity.schema,
        "table": entity.table,
        "fields": {}
    }

    for field_name, field in entity.fields.items():
        entity_dict["fields"][field_name] = {
            "type": field.type_name,
            "nullable": field.nullable,
            "unique": getattr(field, 'unique', False)
        }

    output_path = output_dir / f"{entity.name}.yaml"
    with open(output_path, "w") as f:
        yaml.dump(entity_dict, f, default_flow_style=False)

    print(f"Generated {output_path}")

if __name__ == "__main__":
    main()
```

## Performance Optimization

### Memory Management

For large codebases, manage memory usage effectively.

```python
# Process in batches to control memory usage
def batch_process_java_files(file_paths: List[str], batch_size: int = 50):
    parser = JavaParser()
    all_entities = []

    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]

        for file_path in batch:
            result = parser.parse_file(file_path)
            all_entities.extend(result.entities)

        # Force garbage collection between batches
        import gc
        gc.collect()

    return all_entities
```

### Caching

Cache parsing results for repeated operations.

```python
import pickle
from pathlib import Path

class CachedJavaParser:
    def __init__(self, cache_dir: str = ".java_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.parser = JavaParser()

    def parse_file_cached(self, file_path: str) -> JavaParseResult:
        cache_key = str(hash(file_path + str(Path(file_path).stat().st_mtime)))
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)

        result = self.parser.parse_file(file_path)

        with open(cache_file, "wb") as f:
            pickle.dump(result, f)

        return result
```

## Testing

### Unit Testing

Test your integrations with the Java parsing API.

```python
import pytest
from src.reverse_engineering.java.java_parser import JavaParser

class TestJavaParserIntegration:
    def test_parse_simple_entity(self):
        parser = JavaParser()

        java_code = """
        package com.example;
        import jakarta.persistence.*;

        @Entity
        public class User {
            @Id
            private Long id;

            @Column(nullable = false)
            private String name;
        }
        """

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write(java_code)
            temp_path = f.name

        try:
            result = parser.parse_file(temp_path)

            assert len(result.entities) == 1
            entity = result.entities[0]
            assert entity.name == "User"
            assert "name" in entity.fields

        finally:
            os.unlink(temp_path)
```

### Integration Testing

Test end-to-end migration workflows.

```python
def test_spring_boot_migration_workflow():
    """Test complete migration from Spring Boot entities to SpecQL."""
    parser = JavaParser()

    # Parse Spring Boot entities
    results = parser.parse_directory("src/main/java/com/example/")

    # Validate all entities parsed successfully
    assert all(len(r.errors) == 0 for r in results)

    # Check entity relationships
    entities = [e for r in results for e in r.entities]
    entity_names = {e.name for e in entities}

    # Validate relationships point to existing entities
    for entity in entities:
        for field_name, field in entity.fields.items():
            if field.type_name.startswith("ref("):
                ref_entity = field.type_name[4:-1]  # Extract entity name
                assert ref_entity in entity_names, f"Missing entity: {ref_entity}"
```

## Error Codes

### Parsing Errors
- `JDT_CONNECTION_FAILED`: Cannot connect to Eclipse JDT server
- `FILE_NOT_FOUND`: Input file does not exist
- `ENCODING_ERROR`: File encoding issues
- `SYNTAX_ERROR`: Java syntax errors preventing parsing

### Validation Errors
- `LOW_CONFIDENCE`: Parsing result below confidence threshold
- `MISSING_ENTITY`: Expected entity not found
- `INVALID_RELATIONSHIP`: Relationship references non-existent entity

### Type Mapping Errors
- `UNKNOWN_TYPE`: Java type not recognized
- `INVALID_RELATIONSHIP_TYPE`: Unsupported relationship annotation

## Migration Examples

See the [Spring Boot Migration Guide](../guides/SPRING_BOOT_MIGRATION.md) for comprehensive examples of migrating real-world applications.

## Support

### Getting Help
- **API Documentation**: This reference document
- **Examples**: [Java Examples Directory](../../../examples/java/)
- **Issues**: [GitHub Issues](https://github.com/specql/specql/issues)
- **Forum**: SpecQL Community Discussions

### Version Compatibility
- **SpecQL**: 0.4.0+
- **Java**: 11+ (for JDT), 8+ (for source compatibility)
- **Python**: 3.11+

### Deprecation Notices
- Methods marked as deprecated will be removed in future versions
- Migration guides provided for breaking changes