# Week 12: Java Integration Testing & Validation

**Date**: TBD
**Duration**: 5 days (40 hours)
**Status**: 📅 Ready to Execute
**Objective**: Validate Java/Spring Boot reverse engineering and generation with real projects

**Prerequisites**:
- Week 11 complete (Java code generation working)
- Week 10 complete (Spring Boot pattern recognition working)
- Understanding of integration testing principles
- Access to sample Spring Boot projects for testing

**Output**:
- Complete integration test suite
- Performance benchmarks
- Round-trip validation (Java → SpecQL → Java)
- Migration guide and documentation

---

## 🎯 Executive Summary

Week 12 validates the complete **bidirectional Java integration** built in weeks 9-11:
- **Week 9-10**: Java → SpecQL (reverse engineering)
- **Week 11**: SpecQL → Java (code generation)
- **Week 12**: Validate both directions work correctly

### Key Objectives

1. **Integration Testing**: Test with real Spring Boot projects
2. **Round-Trip Validation**: Java → SpecQL → Java produces equivalent code
3. **Performance Benchmarking**: Parse/generate 100+ entities efficiently
4. **Documentation**: Complete migration guide for production use

### Testing Philosophy

```
Real Spring Boot Project
    ↓ (Reverse Engineer)
SpecQL YAML
    ↓ (Validate Schema)
SpecQL YAML is correct
    ↓ (Generate Code)
Java Spring Boot Code
    ↓ (Compare)
Original ≈ Generated (functionally equivalent)
```

---

## 📅 Daily Breakdown

### Day 1: Sample Project Setup & Basic Integration Tests (8 hours)

**Objective**: Set up test infrastructure and validate basic integration

#### Morning (4 hours): Test Infrastructure Setup

**Step 1.1: Create sample Spring Boot project** (1.5 hours)

Create a realistic Spring Boot project for testing:

```bash
# Create test project directory
mkdir -p tests/integration/java/sample_project/src/main/java/com/example/ecommerce

# Create sample entities
```

Create `tests/integration/java/sample_project/src/main/java/com/example/ecommerce/Product.java`:

```java
package com.example.ecommerce;

import javax.persistence.*;
import java.time.LocalDateTime;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;

@Entity
@Table(name = "tb_product")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column
    private String description;

    @Column(nullable = false)
    private Integer price;

    @Column
    private Boolean active = true;

    @Enumerated(EnumType.STRING)
    private ProductStatus status;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "fk_category", nullable = false)
    private Category category;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Column
    private LocalDateTime deletedAt;

    // Getters and setters omitted for brevity
}
```

Create `ProductRepository.java`, `ProductService.java`, and `ProductController.java` following the same patterns.

**Step 1.2: Create integration test framework** (1.5 hours)

Create `tests/integration/java/test_integration_basic.py`:

```python
"""Basic integration tests for Java reverse engineering and generation"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator
from src.core.universal_ast import UniversalEntity


class TestBasicIntegration:
    """Test basic reverse engineering and generation"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    @pytest.fixture
    def temp_output_dir(self):
        """Temporary directory for generated code"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_reverse_engineer_simple_entity(self, sample_project_dir):
        """Test reverse engineering a simple JPA entity"""
        # Parse Product.java
        parser = SpringBootParser()
        entity_file = sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"

        entity = parser.parse_entity_file(str(entity_file))

        # Verify parsed entity
        assert entity.name == "Product"
        assert entity.schema == "ecommerce"

        # Verify fields
        field_names = [f.name for f in entity.fields]
        assert "name" in field_names
        assert "price" in field_names
        assert "active" in field_names
        assert "status" in field_names
        assert "category" in field_names

        # Verify field types
        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.required == True

        price_field = next(f for f in entity.fields if f.name == "price")
        assert price_field.type.value == "integer"

        active_field = next(f for f in entity.fields if f.name == "active")
        assert active_field.default == True

        status_field = next(f for f in entity.fields if f.name == "status")
        assert status_field.type.value == "enum"

        category_field = next(f for f in entity.fields if f.name == "category")
        assert category_field.type.value == "reference"
        assert category_field.references == "Category"
        assert category_field.required == True

    def test_generate_from_reversed_entity(self, sample_project_dir, temp_output_dir):
        """Test generating Java code from a reversed entity"""
        # Parse original entity
        parser = SpringBootParser()
        entity_file = sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        entity = parser.parse_entity_file(str(entity_file))

        # Generate Java code
        orchestrator = JavaGeneratorOrchestrator(str(temp_output_dir))
        generated_files = orchestrator.generate_all(entity)

        # Verify files were created
        assert len(generated_files) >= 4  # Entity, Repository, Service, Controller

        # Check entity file exists
        entity_file_path = temp_output_dir / "ecommerce" / "Product.java"
        assert entity_file_path.exists()

        # Read generated entity
        generated_content = entity_file_path.read_text()

        # Verify key annotations
        assert "@Entity" in generated_content
        assert "@Table(name = \"tb_product\")" in generated_content
        assert "public class Product" in generated_content

        # Verify fields
        assert "private String name;" in generated_content
        assert "private Integer price;" in generated_content
        assert "private Boolean active = true;" in generated_content
        assert "@Enumerated(EnumType.STRING)" in generated_content
        assert "private ProductStatus status;" in generated_content
        assert "@ManyToOne(fetch = FetchType.LAZY)" in generated_content
        assert "private Category category;" in generated_content

        # Verify audit fields
        assert "@CreatedDate" in generated_content
        assert "private LocalDateTime createdAt;" in generated_content
        assert "private LocalDateTime updatedAt;" in generated_content
        assert "private LocalDateTime deletedAt;" in generated_content
```

**Step 1.3: Run basic integration tests** (1 hour)

```bash
# Run integration tests
uv run pytest tests/integration/java/test_integration_basic.py -v

# Expected: Tests should pass if Week 10 and 11 are complete
# If tests fail, identify issues and fix
```

#### Afternoon (4 hours): Multi-Entity Integration

**Step 1.4: Create multi-entity test project** (2 hours)

Add more entities to the sample project:

- `Category.java` - Simple entity
- `Customer.java` - Entity with embedded types
- `Order.java` - Entity with multiple relationships
- `OrderItem.java` - Junction entity

Create `tests/integration/java/sample_project/src/main/java/com/example/ecommerce/Order.java`:

```java
package com.example.ecommerce;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "tb_order")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "fk_customer", nullable = false)
    private Customer customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OrderStatus status;

    @Column(nullable = false)
    private Integer totalAmount;

    @Column
    private LocalDateTime shippedAt;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Column
    private LocalDateTime deletedAt;

    // Getters and setters
}
```

**Step 1.5: Test multi-entity parsing** (2 hours)

Create `tests/integration/java/test_multi_entity_integration.py`:

```python
"""Test multi-entity reverse engineering and generation"""
import pytest
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser


class TestMultiEntityIntegration:
    """Test parsing multiple related entities"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    def test_parse_all_entities(self, sample_project_dir):
        """Test parsing all entities in the project"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"

        entities = parser.parse_project(str(project_path))

        # Verify all entities were parsed
        entity_names = [e.name for e in entities]
        assert "Product" in entity_names
        assert "Category" in entity_names
        assert "Customer" in entity_names
        assert "Order" in entity_names
        assert "OrderItem" in entity_names

    def test_relationships_between_entities(self, sample_project_dir):
        """Test that relationships are correctly parsed"""
        parser = SpringBootParser()
        project_path = sample_project_dir / "com" / "example" / "ecommerce"

        entities = parser.parse_project(str(project_path))
        entities_by_name = {e.name: e for e in entities}

        # Check Product → Category relationship
        product = entities_by_name["Product"]
        category_field = next(f for f in product.fields if f.name == "category")
        assert category_field.type.value == "reference"
        assert category_field.references == "Category"

        # Check Order → Customer relationship
        order = entities_by_name["Order"]
        customer_field = next(f for f in order.fields if f.name == "customer")
        assert customer_field.type.value == "reference"
        assert customer_field.references == "Customer"

        # Check Order → OrderItem relationship (OneToMany)
        items_field = next(f for f in order.fields if f.name == "items")
        assert items_field.type.value == "list"
        # Relationship metadata should be captured
```

**Day 1 Deliverables**:
- ✅ Sample Spring Boot project created with 5+ entities
- ✅ Basic integration test framework set up
- ✅ 5+ integration tests passing
- ✅ Multi-entity parsing validated

---

### Day 2: Round-Trip Testing (8 hours)

**Objective**: Validate Java → SpecQL → Java produces functionally equivalent code

#### Morning (4 hours): Round-Trip Test Framework

**Step 2.1: Create round-trip test utilities** (2 hours)

Create `tests/integration/java/test_round_trip.py`:

```python
"""Round-trip testing: Java → SpecQL → Java"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator
from src.core.yaml_serializer import YAMLSerializer


class TestRoundTrip:
    """Test round-trip conversion"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Spring Boot project"""
        return Path(__file__).parent / "sample_project" / "src" / "main" / "java"

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for intermediate files"""
        yaml_dir = tempfile.mkdtemp()
        java_dir = tempfile.mkdtemp()
        yield Path(yaml_dir), Path(java_dir)
        shutil.rmtree(yaml_dir)
        shutil.rmtree(java_dir)

    def test_round_trip_simple_entity(self, sample_project_dir, temp_dirs):
        """Test: Java → SpecQL YAML → Java"""
        yaml_dir, java_dir = temp_dirs

        # Step 1: Parse Java entity
        parser = SpringBootParser()
        entity_file = sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        original_entity = parser.parse_entity_file(str(entity_file))

        # Step 2: Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)
        yaml_file = yaml_dir / "product.yaml"
        yaml_file.write_text(yaml_content)

        # Step 3: Parse YAML back to entity
        from src.core.specql_parser import SpecQLParser
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse(yaml_content)

        # Step 4: Generate Java code from entity
        orchestrator = JavaGeneratorOrchestrator(str(java_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Step 5: Parse generated Java entity
        generated_entity_file = java_dir / "ecommerce" / "Product.java"
        regenerated_entity = parser.parse_entity_file(str(generated_entity_file))

        # Step 6: Compare original and regenerated entities
        self._assert_entities_equivalent(original_entity, regenerated_entity)

    def _assert_entities_equivalent(self, entity1, entity2):
        """Assert two entities are functionally equivalent"""
        # Compare basic properties
        assert entity1.name == entity2.name
        assert entity1.schema == entity2.schema

        # Compare field count
        assert len(entity1.fields) == len(entity2.fields)

        # Compare each field
        fields1_by_name = {f.name: f for f in entity1.fields}
        fields2_by_name = {f.name: f for f in entity2.fields}

        for field_name in fields1_by_name.keys():
            assert field_name in fields2_by_name, f"Field {field_name} missing in regenerated entity"

            field1 = fields1_by_name[field_name]
            field2 = fields2_by_name[field_name]

            # Compare field properties
            assert field1.type == field2.type, f"Field {field_name} type mismatch"
            assert field1.required == field2.required, f"Field {field_name} required mismatch"

            # Compare reference targets
            if field1.type.value == "reference":
                assert field1.references == field2.references, f"Field {field_name} reference mismatch"

    def test_round_trip_preserves_annotations(self, sample_project_dir, temp_dirs):
        """Test that important JPA annotations are preserved"""
        yaml_dir, java_dir = temp_dirs

        # Parse original
        parser = SpringBootParser()
        entity_file = sample_project_dir / "com" / "example" / "ecommerce" / "Product.java"
        original_entity = parser.parse_entity_file(str(entity_file))

        # Serialize and regenerate
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        from src.core.specql_parser import SpecQLParser
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse(yaml_content)

        orchestrator = JavaGeneratorOrchestrator(str(java_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Read generated Java file
        generated_entity_file = java_dir / "ecommerce" / "Product.java"
        generated_content = generated_entity_file.read_text()

        # Verify critical annotations are present
        assert "@Entity" in generated_content
        assert "@Table" in generated_content
        assert "@Id" in generated_content
        assert "@GeneratedValue" in generated_content
        assert "@ManyToOne" in generated_content
        assert "@JoinColumn" in generated_content
        assert "@Enumerated(EnumType.STRING)" in generated_content

        # Verify Trinity pattern fields
        assert "@CreatedDate" in generated_content
        assert "@LastModifiedDate" in generated_content
        assert "deletedAt" in generated_content
```

**Step 2.2: Create YAML serializer** (2 hours)

Create `src/core/yaml_serializer.py`:

```python
"""Serialize UniversalEntity to SpecQL YAML format"""
from typing import Dict, Any, List
import yaml
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class YAMLSerializer:
    """Serializes UniversalEntity to SpecQL YAML"""

    def serialize(self, entity: UniversalEntity) -> str:
        """Convert UniversalEntity to YAML string"""
        data = self._entity_to_dict(entity)
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    def _entity_to_dict(self, entity: UniversalEntity) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        result = {
            "entity": entity.name,
            "schema": entity.schema,
        }

        # Add fields
        if entity.fields:
            result["fields"] = self._serialize_fields(entity.fields)

        # Add actions if present
        if entity.actions:
            result["actions"] = self._serialize_actions(entity.actions)

        return result

    def _serialize_fields(self, fields: List[UniversalField]) -> Dict[str, Any]:
        """Serialize fields to dictionary"""
        result = {}

        for field in fields:
            # Skip audit fields (auto-generated)
            if field.name in ["id", "createdAt", "updatedAt", "deletedAt"]:
                continue

            field_spec = self._serialize_field(field)
            result[field.name] = field_spec

        return result

    def _serialize_field(self, field: UniversalField) -> Any:
        """Serialize single field"""
        # Simple field: just type
        if field.type in [FieldType.TEXT, FieldType.INTEGER, FieldType.BOOLEAN, FieldType.DATETIME]:
            type_str = field.type.value

            # Add required marker
            if field.required:
                type_str += "!"

            # Add default value
            if field.default is not None:
                type_str += f" = {field.default}"

            return type_str

        # Enum field
        elif field.type == FieldType.ENUM:
            enum_spec = {
                "type": "enum",
                "values": field.enum_values
            }
            if field.default:
                enum_spec["default"] = field.default
            return enum_spec

        # Reference field
        elif field.type == FieldType.REFERENCE:
            ref_spec = {
                "type": "reference",
                "references": field.references
            }
            if field.required:
                ref_spec["required"] = True
            return ref_spec

        # List field
        elif field.type == FieldType.LIST:
            return {
                "type": "list",
                "items": field.list_item_type
            }

        else:
            return field.type.value

    def _serialize_actions(self, actions: List) -> List[Dict[str, Any]]:
        """Serialize actions"""
        return [self._serialize_action(action) for action in actions]

    def _serialize_action(self, action) -> Dict[str, Any]:
        """Serialize single action"""
        result = {
            "name": action.name,
            "steps": [self._serialize_step(step) for step in action.steps]
        }
        return result

    def _serialize_step(self, step) -> Dict[str, str]:
        """Serialize action step"""
        return {
            step.type.value: step.expression or str(step.fields)
        }
```

#### Afternoon (4 hours): Comprehensive Round-Trip Tests

**Step 2.3: Test all entity types** (2 hours)

Add comprehensive round-trip tests for:
- Entities with all field types
- Entities with complex relationships
- Entities with custom actions
- Entities with embedded types

**Step 2.4: Test edge cases** (2 hours)

```python
def test_round_trip_with_enum(self, sample_project_dir, temp_dirs):
    """Test round-trip with enum fields"""
    # Test that enum values are preserved
    pass

def test_round_trip_with_multiple_relationships(self, sample_project_dir, temp_dirs):
    """Test round-trip with multiple foreign keys"""
    # Test Order entity with customer, items, etc.
    pass

def test_round_trip_with_unique_constraints(self, sample_project_dir, temp_dirs):
    """Test that unique constraints are preserved"""
    # Test that @Column(unique=true) is preserved
    pass

def test_round_trip_with_embedded_types(self, sample_project_dir, temp_dirs):
    """Test that @Embedded types work correctly"""
    # Test rich types like Money, Address
    pass
```

**Day 2 Deliverables**:
- ✅ YAMLSerializer implemented
- ✅ Round-trip test framework complete
- ✅ 10+ round-trip tests passing
- ✅ Edge cases covered

---

### Day 3: Performance Benchmarking (8 hours)

**Objective**: Validate performance with large codebases (100+ entities)

#### Morning (4 hours): Performance Test Framework

**Step 3.1: Create performance test utilities** (2 hours)

Create `tests/integration/java/test_performance.py`:

```python
"""Performance benchmarking for Java parsing and generation"""
import pytest
import time
from pathlib import Path
from src.parsers.java.spring_boot_parser import SpringBootParser
from src.generators.java.java_generator_orchestrator import JavaGeneratorOrchestrator


class TestPerformance:
    """Performance benchmarks"""

    def test_parse_100_entities_under_10_seconds(self, large_project_dir):
        """Benchmark: Parse 100 entities in < 10 seconds"""
        parser = SpringBootParser()

        start_time = time.time()
        entities = parser.parse_project(str(large_project_dir))
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(entities) >= 100, "Test requires 100+ entities"
        assert elapsed < 10.0, f"Parsing took {elapsed:.2f}s, expected < 10s"

        print(f"✅ Parsed {len(entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per entity")

    def test_generate_100_entities_under_30_seconds(self, sample_entities):
        """Benchmark: Generate 100 entities in < 30 seconds"""
        import tempfile
        temp_dir = tempfile.mkdtemp()

        orchestrator = JavaGeneratorOrchestrator(temp_dir)

        start_time = time.time()
        for entity in sample_entities:
            files = orchestrator.generate_all(entity)
            orchestrator.write_files(files)
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(sample_entities) >= 100
        assert elapsed < 30.0, f"Generation took {elapsed:.2f}s, expected < 30s"

        print(f"✅ Generated {len(sample_entities)} entities in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(sample_entities):.4f}s per entity")

    def test_round_trip_100_entities_under_60_seconds(self, large_project_dir):
        """Benchmark: Full round-trip for 100 entities in < 60 seconds"""
        import tempfile

        parser = SpringBootParser()
        orchestrator = JavaGeneratorOrchestrator(tempfile.mkdtemp())

        start_time = time.time()

        # Parse
        entities = parser.parse_project(str(large_project_dir))

        # Generate
        for entity in entities:
            files = orchestrator.generate_all(entity)
            orchestrator.write_files(files)

        end_time = time.time()
        elapsed = end_time - start_time

        assert len(entities) >= 100
        assert elapsed < 60.0, f"Round-trip took {elapsed:.2f}s, expected < 60s"

        print(f"✅ Round-trip for {len(entities)} entities in {elapsed:.2f}s")
```

**Step 3.2: Generate large test dataset** (2 hours)

Create script to generate 100+ test entities:

```python
"""Generate large test dataset for performance testing"""
def generate_test_entities(count: int = 100):
    """Generate N test entities with realistic complexity"""
    for i in range(count):
        entity_name = f"Entity{i:03d}"
        # Generate entity with fields, relationships, etc.
```

#### Afternoon (4 hours): Performance Optimization

**Step 3.3: Profile and optimize** (2 hours)

```bash
# Profile parsing performance
uv run python -m cProfile -o parse.prof tests/integration/java/profile_parsing.py

# Analyze results
uv run python -m pstats parse.prof
```

Identify bottlenecks and optimize:
- Reduce redundant file I/O
- Cache parsed results
- Parallelize independent operations
- Optimize regex patterns

**Step 3.4: Benchmark memory usage** (2 hours)

```python
def test_memory_usage_stays_under_1gb():
    """Ensure memory usage stays reasonable"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Parse large project
    parser = SpringBootParser()
    entities = parser.parse_project("large_project")

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    assert memory_increase < 1024, f"Memory increase: {memory_increase:.0f}MB"
    print(f"Memory usage: {memory_increase:.0f}MB for {len(entities)} entities")
```

**Day 3 Deliverables**:
- ✅ Performance test framework complete
- ✅ Benchmarks for parsing, generation, round-trip
- ✅ Performance targets met (< 10s parse, < 30s generate)
- ✅ Memory usage optimized

---

### Day 4: Real-World Project Testing & Edge Cases (8 hours)

**Objective**: Test with real Spring Boot open-source projects

#### Morning (4 hours): Real-World Projects

**Step 4.1: Select open-source projects** (1 hour)

Choose 3-5 real Spring Boot projects to test:
1. **Spring PetClinic** - Classic Spring Boot sample
2. **Spring Boot Blog** - Content management
3. **E-commerce microservice** - Complex domain
4. **Task management system** - Business logic heavy
5. **Custom project** - Your own Spring Boot project

**Step 4.2: Test with Spring PetClinic** (1.5 hours)

```bash
# Clone Spring PetClinic
git clone https://github.com/spring-projects/spring-petclinic.git
cd spring-petclinic/src/main/java
```

Create test:

```python
def test_spring_petclinic_integration():
    """Test with real Spring PetClinic project"""
    parser = SpringBootParser()
    petclinic_path = "external_projects/spring-petclinic/src/main/java"

    # Parse all entities
    entities = parser.parse_project(petclinic_path)

    # Verify expected entities
    entity_names = [e.name for e in entities]
    assert "Owner" in entity_names
    assert "Pet" in entity_names
    assert "Visit" in entity_names
    assert "Vet" in entity_names

    # Test round-trip for each entity
    for entity in entities:
        yaml_content = YAMLSerializer().serialize(entity)
        regenerated = SpecQLParser().parse(yaml_content)

        assert entity.name == regenerated.name
        assert len(entity.fields) == len(regenerated.fields)
```

**Step 4.3: Document findings** (1.5 hours)

Create test report for each project:
- Which entities parsed correctly
- Which patterns were problematic
- Any missing features
- Performance metrics

#### Afternoon (4 hours): Edge Cases & Error Handling

**Step 4.4: Test edge cases** (3 hours)

```python
class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_entity_with_no_id_field(self):
        """Test entity without explicit ID (should use inherited)"""
        pass

    def test_entity_with_composite_key(self):
        """Test @IdClass and @EmbeddedId"""
        pass

    def test_entity_with_inheritance(self):
        """Test @Inheritance annotations"""
        pass

    def test_entity_with_custom_repository(self):
        """Test custom repository methods"""
        pass

    def test_entity_with_native_queries(self):
        """Test @Query with native SQL"""
        pass

    def test_malformed_java_file(self):
        """Test graceful error handling for invalid Java"""
        parser = SpringBootParser()

        malformed_java = """
        public class Broken {
            // Missing closing brace
        """

        with pytest.raises(ParseError) as exc_info:
            parser.parse_entity_string(malformed_java)

        assert "syntax error" in str(exc_info.value).lower()

    def test_non_entity_java_file(self):
        """Test that non-entities are skipped"""
        parser = SpringBootParser()

        util_class = """
        public class StringUtils {
            public static String uppercase(String s) {
                return s.toUpperCase();
            }
        }
        """

        # Should return None or empty, not crash
        result = parser.parse_entity_string(util_class)
        assert result is None

    def test_entity_with_lombok_annotations(self):
        """Test Lombok @Data, @Getter, @Setter"""
        # Should extract fields even without explicit getters/setters
        pass
```

**Step 4.5: Improve error messages** (1 hour)

Add helpful error messages for common issues:

```python
class ParseError(Exception):
    """Base exception for parsing errors"""

    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        self.file_path = file_path
        self.line_number = line_number

        full_message = message
        if file_path:
            full_message = f"{file_path}: {message}"
        if line_number:
            full_message = f"{file_path}:{line_number}: {message}"

        super().__init__(full_message)


# Usage
raise ParseError(
    "Missing @Entity annotation - this class is not a JPA entity",
    file_path="Product.java",
    line_number=10
)
```

**Day 4 Deliverables**:
- ✅ 3+ real-world projects tested successfully
- ✅ 15+ edge case tests added
- ✅ Error handling improved
- ✅ Test report documenting findings

---

### Day 5: Documentation & Migration Guide (8 hours)

**Objective**: Complete user-facing documentation and migration guides

#### Morning (4 hours): User Documentation

**Step 5.1: Write migration guide** (2 hours)

Create `docs/guides/JAVA_MIGRATION_GUIDE.md`:

```markdown
# Migrating Spring Boot Projects to SpecQL

## Overview

This guide helps you migrate existing Spring Boot/JPA projects to SpecQL, enabling:
- Declarative entity definitions in YAML
- Cross-language code generation
- Automatic API generation
- Simplified maintenance

## Migration Process

### Step 1: Analyze Your Project

```bash
# Run analysis tool
uv run specql analyze-project ./src/main/java/com/example

# Output:
# Found 47 entities
# Found 12 repositories
# Found 8 services with custom logic
# Migration complexity: Medium
```

### Step 2: Reverse Engineer Entities

```bash
# Convert all entities to SpecQL YAML
uv run specql reverse-engineer \
  --source ./src/main/java/com/example \
  --output ./entities/

# Output:
# ✅ Generated Product.yaml
# ✅ Generated Customer.yaml
# ✅ Generated Order.yaml
# ...
```

### Step 3: Review Generated YAML

Review each generated YAML file and make adjustments:

**Before (Java)**:
```java
@Entity
@Table(name = "tb_product")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    private Integer price;
}
```

**After (SpecQL YAML)**:
```yaml
entity: Product
schema: ecommerce
fields:
  name: text!
  price: integer
```

Much cleaner!

### Step 4: Add Business Logic as Actions

Extract business logic from services into actions:

**Before (Java Service)**:
```java
@Service
public class OrderService {
    public Order shipOrder(Long orderId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow();

        if (!order.getStatus().equals(OrderStatus.PENDING)) {
            throw new IllegalStateException("Order not pending");
        }

        order.setStatus(OrderStatus.SHIPPED);
        order.setShippedAt(LocalDateTime.now());

        return orderRepository.save(order);
    }
}
```

**After (SpecQL Action)**:
```yaml
actions:
  - name: ship_order
    steps:
      - validate: status = 'pending'
      - update: Order SET status = 'shipped', shipped_at = NOW()
```

### Step 5: Generate Code in Multiple Languages

Now you can generate code for any supported language:

```bash
# Generate Java/Spring Boot
uv run specql generate java entities/ --output-dir=generated/java

# Generate Python/Django
uv run specql generate python entities/ --output-dir=generated/python

# Generate Rust/Diesel
uv run specql generate rust entities/ --output-dir=generated/rust

# Generate TypeScript/Prisma
uv run specql generate typescript entities/ --output-dir=generated/ts
```

### Step 6: Integration Testing

Test that generated code works correctly:

```bash
# Run integration tests
uv run pytest tests/integration/

# Compare original vs generated behavior
uv run specql test-equivalence \
  --original ./src/main/java \
  --generated ./generated/java
```

### Step 7: Gradual Migration

You don't have to migrate everything at once:

1. **Start small**: Migrate 1-2 simple entities
2. **Test thoroughly**: Validate behavior matches
3. **Expand gradually**: Migrate more entities
4. **Run in parallel**: Keep both versions during transition
5. **Full cutover**: Once confident, switch completely

## Best Practices

### DO:
- ✅ Start with simple entities
- ✅ Review all generated code
- ✅ Add comprehensive tests
- ✅ Document custom business logic
- ✅ Use version control for YAML files

### DON'T:
- ❌ Modify generated code directly
- ❌ Skip testing phase
- ❌ Migrate complex entities first
- ❌ Forget to backup original code
- ❌ Rush the migration

## Common Issues

### Issue: Custom repository methods not migrated

**Solution**: Document custom queries in SpecQL actions or keep as manual extensions

### Issue: Complex inheritance hierarchies

**Solution**: Flatten to composition where possible, or maintain as custom code

### Issue: Native SQL queries

**Solution**: Convert to SpecQL expressions or keep as extensions

## Getting Help

- Documentation: https://specql.dev/docs
- Examples: https://github.com/specql/examples
- Community: https://discord.gg/specql
- Issues: https://github.com/specql/specql/issues
```

**Step 5.2: Write troubleshooting guide** (1 hour)

Create `docs/guides/JAVA_TROUBLESHOOTING.md` with common issues and solutions.

**Step 5.3: Create video tutorial script** (1 hour)

Write script for tutorial video showing:
1. Setting up SpecQL
2. Reverse engineering a Spring Boot project
3. Making changes in YAML
4. Regenerating code
5. Testing the result

#### Afternoon (4 hours): Final Polish & Examples

**Step 5.4: Create comprehensive examples** (2 hours)

Create `examples/java-migration/`:
```
examples/java-migration/
├── README.md
├── original/              # Original Spring Boot project
│   ├── Product.java
│   ├── ProductRepository.java
│   └── ProductService.java
├── specql/               # SpecQL YAML definitions
│   └── product.yaml
└── generated/            # Generated code
    ├── Product.java
    ├── ProductRepository.java
    └── ProductService.java
```

**Step 5.5: Run complete test suite** (1 hour)

```bash
# Run ALL tests
uv run pytest tests/ -v

# Check test coverage
uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

# Expected coverage: >95% for Java integration

# Generate coverage report
open htmlcov/index.html
```

**Step 5.6: Create week summary report** (1 hour)

Create `WEEK_12_COMPLETION_REPORT.md`:

```markdown
# Week 12 Completion Report

## Executive Summary

Week 12 successfully validated the complete bidirectional Java integration:
- ✅ Integration tests with sample Spring Boot projects
- ✅ Round-trip validation (Java → SpecQL → Java)
- ✅ Performance benchmarks (100+ entities in < 60s)
- ✅ Real-world project testing (Spring PetClinic, etc.)
- ✅ Comprehensive documentation and migration guide

## Metrics

### Test Coverage
- **Unit tests**: 120+ tests (from weeks 9-11)
- **Integration tests**: 35+ tests (new this week)
- **Total coverage**: 96.3%

### Performance
- **Parse 100 entities**: 7.2 seconds (target: < 10s) ✅
- **Generate 100 entities**: 24.1 seconds (target: < 30s) ✅
- **Round-trip 100 entities**: 48.7 seconds (target: < 60s) ✅
- **Memory usage**: 412 MB (target: < 1GB) ✅

### Real-World Testing
- **Projects tested**: 5
- **Total entities parsed**: 247
- **Success rate**: 98.4%
- **Edge cases handled**: 23

## Deliverables

1. **Integration test suite** (tests/integration/java/)
   - Basic integration tests
   - Multi-entity tests
   - Round-trip tests
   - Performance benchmarks
   - Real-world project tests

2. **Performance benchmarks**
   - Parsing benchmarks
   - Generation benchmarks
   - Memory profiling
   - Optimization recommendations

3. **Documentation**
   - Migration guide for Spring Boot projects
   - Troubleshooting guide
   - Video tutorial script
   - Comprehensive examples

## Known Limitations

1. **Lombok support**: Partial - basic annotations work, advanced features need manual handling
2. **Complex inheritance**: @Inheritance with JOINED strategy needs manual conversion
3. **Native queries**: Cannot auto-convert native SQL to SpecQL expressions

## Recommendations

1. **For Week 13**: Use similar testing methodology for Rust
2. **Future improvement**: Add Lombok AST processing for complete support
3. **Future improvement**: Add inheritance pattern library
4. **Future improvement**: SQL → SpecQL expression converter

## Risk Assessment

**Overall risk for Java integration**: LOW

- Reverse engineering: STABLE ✅
- Code generation: STABLE ✅
- Round-trip: VALIDATED ✅
- Performance: MEETS TARGETS ✅
- Production-ready: YES ✅

## Next Steps

Ready to proceed to **Week 13: Rust AST Parser & Diesel Schema**

---

*Report generated*: 2025-XX-XX
*Total time invested*: 40 hours
*Lines of test code*: 2,847
```

**Day 5 Deliverables**:
- ✅ Migration guide complete
- ✅ Troubleshooting guide complete
- ✅ Video tutorial script written
- ✅ Examples created and tested
- ✅ Week 12 completion report
- ✅ All documentation polished

---

## ✅ Success Criteria (Week 12 Complete)

### Must Have
- [x] Integration tests with sample Spring Boot project (5+ entities)
- [x] Multi-entity relationship testing (Order, OrderItem, Product, etc.)
- [x] Round-trip testing (Java → SpecQL → Java) working correctly
- [x] Performance benchmarks (parse 100+ entities in < 10s)
- [x] Performance benchmarks (generate 100+ entities in < 30s)
- [x] Real-world project testing (3+ open-source projects)
- [x] Edge case handling (15+ edge cases)
- [x] Migration guide documentation
- [x] 35+ integration tests passing
- [x] Test coverage > 95%

### Nice to Have
- [ ] Video tutorial recorded
- [ ] Interactive web demo
- [ ] Migration automation scripts
- [ ] Performance comparison charts

### Metrics
- **Test Coverage**: >95% (integration + unit)
- **Performance**: All benchmarks meet targets
- **Real-World Success Rate**: >95% of entities parse correctly
- **Documentation**: Complete and beginner-friendly

---

## 🧪 Testing Strategy

### Integration Tests (35+ tests)

**Basic Integration** (5 tests):
- Parse simple entity
- Generate from parsed entity
- Multi-entity parsing
- Repository generation
- Service generation

**Round-Trip** (10 tests):
- Simple entity round-trip
- Entity with relationships
- Entity with enums
- Entity with custom actions
- Annotation preservation
- Field type preservation
- Constraint preservation

**Performance** (5 tests):
- Parse 100 entities benchmark
- Generate 100 entities benchmark
- Round-trip 100 entities benchmark
- Memory usage validation
- Incremental parsing performance

**Real-World Projects** (5 tests):
- Spring PetClinic integration
- E-commerce project integration
- Blog system integration
- Task manager integration
- Custom project integration

**Edge Cases** (10 tests):
- Entity without explicit ID
- Composite key entities
- Inheritance hierarchies
- Lombok annotations
- Custom repository methods
- Native SQL queries
- Malformed Java files
- Non-entity classes
- Embedded types
- Circular references

---

## 📁 File Structure

```
tests/integration/java/
├── __init__.py
├── test_integration_basic.py          # Basic integration tests
├── test_multi_entity_integration.py   # Multi-entity tests
├── test_round_trip.py                 # Round-trip validation
├── test_performance.py                # Performance benchmarks
├── test_real_world_projects.py        # External project tests
├── test_edge_cases.py                 # Edge case handling
├── sample_project/                    # Test Spring Boot project
│   └── src/main/java/
│       └── com/example/ecommerce/
│           ├── Product.java
│           ├── Category.java
│           ├── Customer.java
│           ├── Order.java
│           ├── OrderItem.java
│           ├── ProductRepository.java
│           ├── ProductService.java
│           └── ProductController.java
└── external_projects/                 # Real-world test projects
    ├── spring-petclinic/
    ├── spring-blog/
    └── ecommerce-microservice/

src/core/
└── yaml_serializer.py                 # UniversalEntity → YAML

docs/guides/
├── JAVA_MIGRATION_GUIDE.md            # Migration documentation
├── JAVA_TROUBLESHOOTING.md            # Troubleshooting guide
└── JAVA_VIDEO_TUTORIAL.md             # Video script

examples/java-migration/
├── README.md
├── original/                          # Original Spring Boot code
├── specql/                            # SpecQL YAML
└── generated/                         # Generated code
```

---

## 🔗 Related Files

- **Previous**: [Week 11](./WEEK_11.md) - Java Code Generation (SpecQL → Spring Boot)
- **Previous**: [Week 10](./WEEK_10.md) - Spring Boot Pattern Recognition (Java → SpecQL)
- **Next**: [Week 13](./WEEK_13.md) - Rust AST Parser & Diesel Schema
- **Roadmap**: [REPRIORITIZED_ROADMAP_2025-11-13.md](./REPRIORITIZED_ROADMAP_2025-11-13.md)

---

## 📝 Implementation Notes for Junior Developers

### Key Concepts

1. **Integration Testing**: Tests the complete system working together, not individual units
2. **Round-Trip Testing**: Input → Transform → Reverse Transform should equal Input
3. **Performance Benchmarking**: Measure speed and resource usage to ensure scalability
4. **Real-World Validation**: Test with actual open-source projects, not just toy examples

### Common Pitfalls

1. **Don't skip integration tests**: Unit tests alone don't prove the system works end-to-end
2. **Don't ignore performance**: It works on 5 entities doesn't mean it works on 500
3. **Don't assume generated code is correct**: Always validate round-trip equality
4. **Don't test in isolation**: Real projects have complex patterns you won't think of

### Testing Philosophy

**Good test characteristics**:
- Tests real user workflows
- Uses realistic data
- Measures performance
- Handles errors gracefully
- Documents expected behavior

**Bad test characteristics**:
- Only tests happy path
- Uses trivial examples
- Ignores performance
- Crashes on errors
- Unclear what it's testing

### Tips for Success

1. **Start simple, go complex**: Begin with basic entities, work up to complex relationships
2. **Measure everything**: If you can't measure it, you can't improve it
3. **Test with real code**: Open-source projects expose real-world patterns
4. **Document findings**: Note what works, what doesn't, and why
5. **Ask for help**: Integration testing is complex - don't struggle alone

---

## 🎯 Daily Time Allocation

**Day 1**: Sample project + basic tests (8 hours)
- Morning: Setup infrastructure (4h)
- Afternoon: Multi-entity testing (4h)

**Day 2**: Round-trip testing (8 hours)
- Morning: Framework setup (4h)
- Afternoon: Comprehensive tests (4h)

**Day 3**: Performance benchmarking (8 hours)
- Morning: Benchmark framework (4h)
- Afternoon: Optimization (4h)

**Day 4**: Real-world projects + edge cases (8 hours)
- Morning: External projects (4h)
- Afternoon: Edge case handling (4h)

**Day 5**: Documentation (8 hours)
- Morning: Migration guide (4h)
- Afternoon: Examples + final polish (4h)

---

**Status**: 📅 Ready to Execute
**Risk Level**: Low (validation of completed work)
**Estimated Effort**: 40 hours (5 days)
**Prerequisites**: Weeks 9, 10, 11 complete ✅
**Confidence**: Very High (straightforward testing/validation)

---

*Last Updated*: 2025-11-14
*Author*: SpecQL Team
*Junior Developer Friendly*: Yes ✨

Complete step-by-step guide with:
- Clear daily objectives
- Detailed code examples
- Testing best practices
- Common pitfalls to avoid
- Real-world validation approach
