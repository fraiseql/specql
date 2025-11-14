# Week 16: Rust Integration Testing & Validation

**Date**: TBD
**Duration**: 5 days (40 hours)
**Status**: 📅 Planned
**Objective**: Validate Rust/Diesel support with real projects and achieve production readiness

**Prerequisites**:
- Week 15 complete (Rust code generation working)
- Week 14 complete (Diesel pattern recognition working)
- Understanding of integration testing principles
- Access to sample Diesel projects for testing

**Output**:
- Complete integration test suite
- Performance benchmarks
- Round-trip validation (Rust → SpecQL → Rust)
- Migration guide and documentation

---

## 🎯 Executive Summary

Week 16 validates the complete **bidirectional Rust integration** built in weeks 13-15:
- **Week 13-14**: Rust → SpecQL (reverse engineering)
- **Week 15**: SpecQL → Rust (code generation)
- **Week 16**: Validate both directions work correctly

### Key Objectives

1. **Integration Testing**: Test with real Diesel/Actix Web projects
2. **Round-Trip Validation**: Rust → SpecQL → Rust produces equivalent code
3. **Performance Benchmarking**: Parse/generate 100+ entities efficiently
4. **Documentation**: Complete migration guide for production use

### Testing Philosophy

```
Real Diesel Project
    ↓ (Reverse Engineer)
 SpecQL YAML
    ↓ (Validate Schema)
 SpecQL YAML is correct
    ↓ (Generate Code)
Rust Diesel Code
    ↓ (Compare)
Original ≈ Generated (functionally equivalent)
```

---

## 📅 Daily Breakdown

### Day 1: Sample Project Setup & Basic Integration Tests (8 hours)

**Objective**: Set up test infrastructure and validate basic integration

#### Morning (4 hours): Test Infrastructure Setup

**Step 1.1: Create sample Diesel project** (1.5 hours)

Create a realistic Diesel project for testing:

```bash
# Create test project directory
mkdir -p tests/integration/rust/sample_project/src/models
mkdir -p tests/integration/rust/sample_project/src/schema
mkdir -p tests/integration/rust/sample_project/src/handlers
```

Create `tests/integration/rust/sample_project/src/models/product.rs`:

```rust
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use chrono::NaiveDateTime;

use crate::schema::products;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = products)]
pub struct Product {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub price: i32,
    pub active: bool,
    pub status: ProductStatus,
    pub category_id: i64,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
    pub deleted_at: Option<NaiveDateTime>,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = products)]
pub struct NewProduct {
    pub name: String,
    pub description: Option<String>,
    pub price: i32,
    pub active: bool,
    pub status: ProductStatus,
    pub category_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, diesel::sql_types::SqlType)]
#[diesel(postgres_type(name = "product_status"))]
pub enum ProductStatus {
    Draft,
    Active,
    Archived,
}
```

Create `tests/integration/rust/sample_project/src/schema.rs`:

```rust
diesel::table! {
    products (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        price -> Int4,
        active -> Bool,
        status -> Text,  // Stored as TEXT in DB
        category_id -> Int8,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        deleted_at -> Nullable<Timestamp>,
    }
}

diesel::table! {
    categories (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        deleted_at -> Nullable<Timestamp>,
    }
}

diesel::joinable!(products -> categories (category_id));

diesel::allow_tables_to_appear_in_same_query!(
    products,
    categories,
);
```

**Step 1.2: Create integration test framework** (1.5 hours)

Create `tests/integration/rust/test_integration_basic.py`:

```python
"""Basic integration tests for Rust reverse engineering and generation"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.rust.diesel_parser import DieselParser
from src.generators.rust.rust_generator_orchestrator import RustGeneratorOrchestrator
from src.core.universal_ast import UniversalEntity


class TestBasicIntegration:
    """Test basic reverse engineering and generation"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Diesel project"""
        return Path(__file__).parent / "sample_project" / "src"

    @pytest.fixture
    def temp_output_dir(self):
        """Temporary directory for generated code"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_reverse_engineer_simple_model(self, sample_project_dir):
        """Test reverse engineering a simple Diesel model"""
        # Parse Product model
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "product.rs"
        schema_file = sample_project_dir / "schema.rs"

        entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Verify parsed entity
        assert entity.name == "Product"
        assert entity.schema == "ecommerce"

        # Verify fields
        field_names = [f.name for f in entity.fields]
        assert "name" in field_names
        assert "price" in field_names
        assert "active" in field_names
        assert "status" in field_names
        assert "category_id" in field_names

        # Verify field types
        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.required == True

        price_field = next(f for f in entity.fields if f.name == "price")
        assert price_field.type.value == "integer"

        active_field = next(f for f in entity.fields if f.name == "active")
        assert active_field.type.value == "boolean"
        assert active_field.default == True

        status_field = next(f for f in entity.fields if f.name == "status")
        assert status_field.type.value == "enum"

        category_field = next(f for f in entity.fields if f.name == "category_id")
        assert category_field.type.value == "reference"
        assert category_field.references == "Category"
        assert category_field.required == True

    def test_generate_from_reversed_model(self, sample_project_dir, temp_output_dir):
        """Test generating Rust code from a reversed model"""
        # Parse original model
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "product.rs"
        schema_file = sample_project_dir / "schema.rs"
        entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Generate Rust code
        orchestrator = RustGeneratorOrchestrator(str(temp_output_dir))
        generated_files = orchestrator.generate_all(entity)

        # Verify files were created
        assert len(generated_files) >= 3  # Model, Schema, Handler

        # Check model file exists
        model_file_path = temp_output_dir / "models" / "product.rs"
        assert model_file_path.exists()

        # Read generated model
        generated_content = model_file_path.read_text()

        # Verify key attributes
        assert "#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]" in generated_content
        assert "#[diesel(table_name = products)]" in generated_content
        assert "pub struct Product" in generated_content

        # Verify fields
        assert "pub name: String," in generated_content
        assert "pub price: i32," in generated_content
        assert "pub active: bool," in generated_content
        assert "pub status: ProductStatus," in generated_content
        assert "pub category_id: i64," in generated_content

        # Verify Trinity pattern fields
        assert "pub created_at: NaiveDateTime," in generated_content
        assert "pub updated_at: NaiveDateTime," in generated_content
        assert "pub deleted_at: Option<NaiveDateTime>," in generated_content

        # Verify NewProduct struct
        assert "pub struct NewProduct" in generated_content
```

**Step 1.3: Run basic integration tests** (1 hour)

```bash
# Run integration tests
uv run pytest tests/integration/rust/test_integration_basic.py -v

# Expected: Tests should pass if Week 14 and 15 are complete
# If tests fail, identify issues and fix
```

#### Afternoon (4 hours): Multi-Entity Integration

**Step 1.4: Create multi-entity test project** (2 hours)

Add more models to the sample project:

- `category.rs` - Simple model
- `customer.rs` - Model with embedded types
- `order.rs` - Model with multiple relationships
- `order_item.rs` - Junction model

Create `tests/integration/rust/sample_project/src/models/order.rs`:

```rust
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use chrono::NaiveDateTime;

use crate::schema::orders;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = orders)]
pub struct Order {
    pub id: i64,
    pub customer_id: i64,
    pub status: OrderStatus,
    pub total_amount: i32,
    pub shipped_at: Option<NaiveDateTime>,
    pub created_at: NaiveDateTime,
    pub updated_at: NaiveDateTime,
    pub deleted_at: Option<NaiveDateTime>,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = orders)]
pub struct NewOrder {
    pub customer_id: i64,
    pub status: OrderStatus,
    pub total_amount: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OrderStatus {
    Pending,
    Processing,
    Shipped,
    Delivered,
    Cancelled,
}
```

**Step 1.5: Test multi-entity parsing** (2 hours)

Create `tests/integration/rust/test_multi_entity_integration.py`:

```python
"""Test multi-entity reverse engineering and generation"""
import pytest
from pathlib import Path
from src.parsers.rust.diesel_parser import DieselParser


class TestMultiEntityIntegration:
    """Test parsing multiple related entities"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Diesel project"""
        return Path(__file__).parent / "sample_project" / "src"

    def test_parse_all_entities(self, sample_project_dir):
        """Test parsing all entities in the project"""
        parser = DieselParser()
        models_path = sample_project_dir / "models"
        schema_path = sample_project_dir / "schema.rs"

        entities = parser.parse_project(str(models_path), str(schema_path))

        # Verify all entities were parsed
        entity_names = [e.name for e in entities]
        assert "Product" in entity_names
        assert "Category" in entity_names
        assert "Customer" in entity_names
        assert "Order" in entity_names
        assert "OrderItem" in entity_names

    def test_relationships_between_entities(self, sample_project_dir):
        """Test that relationships are correctly parsed"""
        parser = DieselParser()
        models_path = sample_project_dir / "models"
        schema_path = sample_project_dir / "schema.rs"

        entities = parser.parse_project(str(models_path), str(schema_path))
        entities_by_name = {e.name: e for e in entities}

        # Check Product → Category relationship
        product = entities_by_name["Product"]
        category_field = next(f for f in product.fields if f.name == "category_id")
        assert category_field.type.value == "reference"
        assert category_field.references == "Category"

        # Check Order → Customer relationship
        order = entities_by_name["Order"]
        customer_field = next(f for f in order.fields if f.name == "customer_id")
        assert customer_field.type.value == "reference"
        assert customer_field.references == "Customer"
```

**Day 1 Deliverables**:
- ✅ Sample Diesel project created with 5+ models
- ✅ Basic integration test framework set up
- ✅ 5+ integration tests passing
- ✅ Multi-entity parsing validated

---

### Day 2: Round-Trip Testing (8 hours)

**Objective**: Validate Rust → SpecQL → Rust produces functionally equivalent code

#### Morning (4 hours): Round-Trip Test Framework

**Step 2.1: Create round-trip test utilities** (2 hours)

Create `tests/integration/rust/test_round_trip.py`:

```python
"""Round-trip testing: Rust → SpecQL → Rust"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.parsers.rust.diesel_parser import DieselParser
from src.generators.rust.rust_generator_orchestrator import RustGeneratorOrchestrator
from src.core.yaml_serializer import YAMLSerializer


class TestRoundTrip:
    """Test round-trip conversion"""

    @pytest.fixture
    def sample_project_dir(self):
        """Path to sample Diesel project"""
        return Path(__file__).parent / "sample_project" / "src"

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for intermediate files"""
        yaml_dir = tempfile.mkdtemp()
        rust_dir = tempfile.mkdtemp()
        yield Path(yaml_dir), Path(rust_dir)
        shutil.rmtree(yaml_dir)
        shutil.rmtree(rust_dir)

    def test_round_trip_simple_model(self, sample_project_dir, temp_dirs):
        """Test: Rust → SpecQL YAML → Rust"""
        yaml_dir, rust_dir = temp_dirs

        # Step 1: Parse Rust model
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "product.rs"
        schema_file = sample_project_dir / "schema.rs"
        original_entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Step 2: Serialize to YAML
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)
        yaml_file = yaml_dir / "product.yaml"
        yaml_file.write_text(yaml_content)

        # Step 3: Parse YAML back to entity
        from src.core.specql_parser import SpecQLParser
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse(yaml_content)

        # Step 4: Generate Rust code from entity
        orchestrator = RustGeneratorOrchestrator(str(rust_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Step 5: Parse generated Rust model
        generated_model_file = rust_dir / "models" / "product.rs"
        generated_schema_file = rust_dir / "schema.rs"
        regenerated_entity = parser.parse_model_file(
            str(generated_model_file),
            str(generated_schema_file)
        )

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

    def test_round_trip_preserves_attributes(self, sample_project_dir, temp_dirs):
        """Test that important Diesel attributes are preserved"""
        yaml_dir, rust_dir = temp_dirs

        # Parse original
        parser = DieselParser()
        model_file = sample_project_dir / "models" / "product.rs"
        schema_file = sample_project_dir / "schema.rs"
        original_entity = parser.parse_model_file(str(model_file), str(schema_file))

        # Serialize and regenerate
        serializer = YAMLSerializer()
        yaml_content = serializer.serialize(original_entity)

        from src.core.specql_parser import SpecQLParser
        specql_parser = SpecQLParser()
        intermediate_entity = specql_parser.parse(yaml_content)

        orchestrator = RustGeneratorOrchestrator(str(rust_dir))
        generated_files = orchestrator.generate_all(intermediate_entity)
        orchestrator.write_files(generated_files)

        # Read generated Rust file
        generated_model_file = rust_dir / "models" / "product.rs"
        generated_content = generated_model_file.read_text()

        # Verify critical attributes are present
        assert "#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]" in generated_content
        assert "#[diesel(table_name = products)]" in generated_content
        assert "pub struct Product" in generated_content
        assert "pub struct NewProduct" in generated_content

        # Verify Trinity pattern fields
        assert "pub created_at: NaiveDateTime," in generated_content
        assert "pub updated_at: NaiveDateTime," in generated_content
        assert "pub deleted_at: Option<NaiveDateTime>," in generated_content
```

**Step 2.2: Verify YAML serializer works for Rust** (2 hours)

The YAML serializer from Week 12 should work universally. Verify it handles Rust-specific patterns:

```python
def test_yaml_serializer_rust_specific():
    """Test YAML serializer with Rust-specific patterns"""
    from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
    from src.core.yaml_serializer import YAMLSerializer

    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
            UniversalField(name="price", type=FieldType.INTEGER, required=True),
            UniversalField(name="active", type=FieldType.BOOLEAN, default=True),
            UniversalField(
                name="status",
                type=FieldType.ENUM,
                enum_values=["Draft", "Active", "Archived"]
            ),
            UniversalField(
                name="category_id",
                type=FieldType.REFERENCE,
                references="Category",
                required=True
            ),
        ]
    )

    serializer = YAMLSerializer()
    yaml_content = serializer.serialize(entity)

    # Verify YAML structure
    assert "entity: Product" in yaml_content
    assert "schema: ecommerce" in yaml_content
    assert "name: text!" in yaml_content
    assert "price: integer!" in yaml_content
    assert "active: boolean = true" in yaml_content
```

#### Afternoon (4 hours): Comprehensive Round-Trip Tests

**Step 2.3: Test all model types** (2 hours)

Add comprehensive round-trip tests for:
- Models with all field types
- Models with complex relationships
- Models with custom actions
- Models with embedded types

**Step 2.4: Test edge cases** (2 hours)

```python
def test_round_trip_with_enum(self, sample_project_dir, temp_dirs):
    """Test round-trip with enum fields"""
    # Test that enum values are preserved
    pass

def test_round_trip_with_multiple_relationships(self, sample_project_dir, temp_dirs):
    """Test round-trip with multiple foreign keys"""
    # Test Order model with customer_id, items, etc.
    pass

def test_round_trip_with_optional_fields(self, sample_project_dir, temp_dirs):
    """Test that Option<T> fields are preserved"""
    # Test that optional fields use Option<T>
    pass

def test_round_trip_with_custom_derives(self, sample_project_dir, temp_dirs):
    """Test that derive macros work correctly"""
    # Test Serialize, Deserialize, etc.
    pass
```

**Day 2 Deliverables**:
- ✅ Round-trip test framework complete
- ✅ 10+ round-trip tests passing
- ✅ Edge cases covered
- ✅ YAML serialization verified for Rust

---

### Day 3: Performance Benchmarking (8 hours)

**Objective**: Validate performance with large codebases (100+ models)

#### Morning (4 hours): Performance Test Framework

**Step 3.1: Create performance test utilities** (2 hours)

Create `tests/integration/rust/test_performance.py`:

```python
"""Performance benchmarking for Rust parsing and generation"""
import pytest
import time
from pathlib import Path
from src.parsers.rust.diesel_parser import DieselParser
from src.generators.rust.rust_generator_orchestrator import RustGeneratorOrchestrator


class TestPerformance:
    """Performance benchmarks"""

    def test_parse_100_models_under_10_seconds(self, large_project_dir):
        """Benchmark: Parse 100 models in < 10 seconds"""
        parser = DieselParser()

        start_time = time.time()
        entities = parser.parse_project(
            str(large_project_dir / "models"),
            str(large_project_dir / "schema.rs")
        )
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(entities) >= 100, "Test requires 100+ models"
        assert elapsed < 10.0, f"Parsing took {elapsed:.2f}s, expected < 10s"

        print(f"✅ Parsed {len(entities)} models in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(entities):.4f}s per model")

    def test_generate_100_models_under_30_seconds(self, sample_entities):
        """Benchmark: Generate 100 models in < 30 seconds"""
        import tempfile
        temp_dir = tempfile.mkdtemp()

        orchestrator = RustGeneratorOrchestrator(temp_dir)

        start_time = time.time()
        for entity in sample_entities:
            files = orchestrator.generate_all(entity)
            orchestrator.write_files(files)
        end_time = time.time()

        elapsed = end_time - start_time

        assert len(sample_entities) >= 100
        assert elapsed < 30.0, f"Generation took {elapsed:.2f}s, expected < 30s"

        print(f"✅ Generated {len(sample_entities)} models in {elapsed:.2f}s")
        print(f"   Average: {elapsed / len(sample_entities):.4f}s per model")

    def test_round_trip_100_models_under_60_seconds(self, large_project_dir):
        """Benchmark: Full round-trip for 100 models in < 60 seconds"""
        import tempfile

        parser = DieselParser()
        orchestrator = RustGeneratorOrchestrator(tempfile.mkdtemp())

        start_time = time.time()

        # Parse
        entities = parser.parse_project(
            str(large_project_dir / "models"),
            str(large_project_dir / "schema.rs")
        )

        # Generate
        for entity in entities:
            files = orchestrator.generate_all(entity)
            orchestrator.write_files(files)

        end_time = time.time()
        elapsed = end_time - start_time

        assert len(entities) >= 100
        assert elapsed < 60.0, f"Round-trip took {elapsed:.2f}s, expected < 60s"

        print(f"✅ Round-trip for {len(entities)} models in {elapsed:.2f}s")
```

**Step 3.2: Generate large test dataset** (2 hours)

Create script to generate 100+ test models:

```python
"""Generate large test dataset for performance testing"""
def generate_test_models(count: int = 100):
    """Generate N test models with realistic complexity"""
    for i in range(count):
        model_name = f"Entity{i:03d}"
        # Generate model with fields, relationships, etc.
```

#### Afternoon (4 hours): Performance Optimization

**Step 3.3: Profile and optimize** (2 hours)

```bash
# Profile parsing performance
uv run python -m cProfile -o parse.prof tests/integration/rust/profile_parsing.py

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
    parser = DieselParser()
    entities = parser.parse_project("large_project/models", "large_project/schema.rs")

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    assert memory_increase < 1024, f"Memory increase: {memory_increase:.0f}MB"
    print(f"Memory usage: {memory_increase:.0f}MB for {len(entities)} models")
```

**Day 3 Deliverables**:
- ✅ Performance test framework complete
- ✅ Benchmarks for parsing, generation, round-trip
- ✅ Performance targets met (< 10s parse, < 30s generate)
- ✅ Memory usage optimized

---

### Day 4: Real-World Project Testing & Edge Cases (8 hours)

**Objective**: Test with real Diesel open-source projects

#### Morning (4 hours): Real-World Projects

**Step 4.1: Select open-source projects** (1 hour)

Choose 3-5 real Diesel projects to test:
1. **Conduit** - Real-world Medium clone
2. **Rocket.rs examples** - Rocket + Diesel examples
3. **Actix-web examples** - Actix + Diesel examples
4. **Custom project** - Your own Diesel project

**Step 4.2: Test with Conduit** (1.5 hours)

```bash
# Clone Conduit
git clone https://github.com/gothinkster/rust-realworld-example-app.git
cd rust-realworld-example-app/src
```

Create test:

```python
def test_conduit_integration():
    """Test with real Conduit (RealWorld) project"""
    parser = DieselParser()
    conduit_path = "external_projects/conduit/src"

    # Parse all models
    entities = parser.parse_project(
        conduit_path + "/models",
        conduit_path + "/schema.rs"
    )

    # Verify expected entities
    entity_names = [e.name for e in entities]
    assert "User" in entity_names
    assert "Article" in entity_names
    assert "Comment" in entity_names
    assert "Follow" in entity_names

    # Test round-trip for each entity
    for entity in entities:
        yaml_content = YAMLSerializer().serialize(entity)
        regenerated = SpecQLParser().parse(yaml_content)

        assert entity.name == regenerated.name
        assert len(entity.fields) == len(regenerated.fields)
```

**Step 4.3: Document findings** (1.5 hours)

Create test report for each project:
- Which models parsed correctly
- Which patterns were problematic
- Any missing features
- Performance metrics

#### Afternoon (4 hours): Edge Cases & Error Handling

**Step 4.4: Test edge cases** (3 hours)

```python
class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_model_with_custom_derives(self):
        """Test custom derive macros"""
        pass

    def test_model_with_generic_types(self):
        """Test models with generic parameters"""
        pass

    def test_model_with_lifetime_parameters(self):
        """Test models with lifetime annotations"""
        pass

    def test_model_with_embedded_structs(self):
        """Test models with embedded/nested structs"""
        pass

    def test_model_with_json_fields(self):
        """Test Jsonb fields"""
        pass

    def test_malformed_rust_file(self):
        """Test graceful error handling for invalid Rust"""
        parser = DieselParser()

        malformed_rust = """
        pub struct Broken {
            // Missing closing brace
        """

        with pytest.raises(ParseError) as exc_info:
            parser.parse_model_string(malformed_rust)

        assert "syntax error" in str(exc_info.value).lower()

    def test_non_model_rust_file(self):
        """Test that non-models are skipped"""
        parser = DieselParser()

        util_code = """
        pub fn uppercase(s: &str) -> String {
            s.to_uppercase()
        }
        """

        # Should return None or empty, not crash
        result = parser.parse_model_string(util_code)
        assert result is None
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
    "Missing #[diesel(table_name = ...)] attribute - this struct is not a Diesel model",
    file_path="product.rs",
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

Create `docs/guides/RUST_MIGRATION_GUIDE.md`:

```markdown
# Migrating Diesel Projects to SpecQL

## Overview

This guide helps you migrate existing Diesel/Actix Web projects to SpecQL, enabling:
- Declarative model definitions in YAML
- Cross-language code generation
- Automatic API generation
- Simplified maintenance

## Migration Process

### Step 1: Analyze Your Project

```bash
# Run analysis tool
uv run specql analyze-project ./src

# Output:
# Found 47 models
# Found 12 custom queries
# Found 8 handlers with custom logic
# Migration complexity: Medium
```

### Step 2: Reverse Engineer Models

```bash
# Convert all models to SpecQL YAML
uv run specql reverse-engineer \
  --source ./src/models \
  --schema ./src/schema.rs \
  --output ./entities/

# Output:
# ✅ Generated Product.yaml
# ✅ Generated Customer.yaml
# ✅ Generated Order.yaml
# ...
```

### Step 3: Review Generated YAML

Review each generated YAML file and make adjustments:

**Before (Rust)**:
```rust
#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = products)]
pub struct Product {
    pub id: i64,
    pub name: String,
    pub price: i32,
    pub active: bool,
}
```

**After (SpecQL YAML)**:
```yaml
entity: Product
schema: ecommerce
fields:
  name: text!
  price: integer!
  active: boolean = true
```

Much cleaner!

### Step 4: Generate Code in Multiple Languages

Now you can generate code for any supported language:

```bash
# Generate Rust/Diesel
uv run specql generate rust entities/ --output-dir=generated/rust

# Generate Java/Spring Boot
uv run specql generate java entities/ --output-dir=generated/java

# Generate Python/Django
uv run specql generate python entities/ --output-dir=generated/python
```

## Best Practices

### DO:
- ✅ Start with simple models
- ✅ Review all generated code
- ✅ Add comprehensive tests
- ✅ Document custom business logic
- ✅ Use version control for YAML files

### DON'T:
- ❌ Modify generated code directly
- ❌ Skip testing phase
- ❌ Migrate complex models first
- ❌ Forget to backup original code
- ❌ Rush the migration
```

**Step 5.2: Write troubleshooting guide** (1 hour)

Create `docs/guides/RUST_TROUBLESHOOTING.md` with common issues and solutions.

**Step 5.3: Create video tutorial script** (1 hour)

Write script for tutorial video showing:
1. Setting up SpecQL
2. Reverse engineering a Diesel project
3. Making changes in YAML
4. Regenerating code
5. Testing the result

#### Afternoon (4 hours): Final Polish & Examples

**Step 5.4: Create comprehensive examples** (2 hours)

Create `examples/rust-migration/`:
```
examples/rust-migration/
├── README.md
├── original/              # Original Diesel project
│   ├── product.rs
│   └── schema.rs
├── specql/               # SpecQL YAML definitions
│   └── product.yaml
└── generated/            # Generated code
    ├── product.rs
    └── schema.rs
```

**Step 5.5: Run complete test suite** (1 hour)

```bash
# Run ALL tests
uv run pytest tests/ -v

# Check test coverage
uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

# Expected coverage: >95% for Rust integration

# Generate coverage report
open htmlcov/index.html
```

**Step 5.6: Create week summary report** (1 hour)

Create `WEEK_16_COMPLETION_REPORT.md`:

```markdown
# Week 16 Completion Report

## Executive Summary

Week 16 successfully validated the complete bidirectional Rust integration:
- ✅ Integration tests with sample Diesel projects
- ✅ Round-trip validation (Rust → SpecQL → Rust)
- ✅ Performance benchmarks (100+ models in < 60s)
- ✅ Real-world project testing (Conduit, etc.)
- ✅ Comprehensive documentation and migration guide

## Metrics

### Test Coverage
- **Unit tests**: 120+ tests (from weeks 13-15)
- **Integration tests**: 35+ tests (new this week)
- **Total coverage**: 96.3%

### Performance
- **Parse 100 models**: 7.2 seconds (target: < 10s) ✅
- **Generate 100 models**: 24.1 seconds (target: < 30s) ✅
- **Round-trip 100 models**: 48.7 seconds (target: < 60s) ✅
- **Memory usage**: 412 MB (target: < 1GB) ✅

### Real-World Testing
- **Projects tested**: 3
- **Total models parsed**: 147
- **Success rate**: 98.4%
- **Edge cases handled**: 18

## Deliverables

1. **Integration test suite** (tests/integration/rust/)
2. **Performance benchmarks**
3. **Documentation**
   - Migration guide for Diesel projects
   - Troubleshooting guide
   - Video tutorial script
   - Comprehensive examples

## Risk Assessment

**Overall risk for Rust integration**: LOW

- Reverse engineering: STABLE ✅
- Code generation: STABLE ✅
- Round-trip: VALIDATED ✅
- Performance: MEETS TARGETS ✅
- Production-ready: YES ✅

## Next Steps

Ready to proceed to **Week 17: Cross-Language Validation**

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
- ✅ Week 16 completion report
- ✅ All documentation polished

---

## ✅ Success Criteria (Week 16 Complete)

### Must Have
- [x] Integration tests with sample Diesel project (5+ models)
- [x] Multi-entity relationship testing (Order, OrderItem, Product, etc.)
- [x] Round-trip testing (Rust → SpecQL → Rust) working correctly
- [x] Performance benchmarks (parse 100+ models in < 10s)
- [x] Performance benchmarks (generate 100+ models in < 30s)
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
- **Real-World Success Rate**: >95% of models parse correctly
- **Documentation**: Complete and beginner-friendly

---

## 🧪 Testing Strategy

### Integration Tests (35+ tests)

**Basic Integration** (5 tests):
- Parse simple model
- Generate from parsed model
- Multi-entity parsing
- Handler generation
- Schema generation

**Round-Trip** (10 tests):
- Simple model round-trip
- Model with relationships
- Model with enums
- Model with custom actions
- Attribute preservation
- Field type preservation
- Constraint preservation

**Performance** (5 tests):
- Parse 100 models benchmark
- Generate 100 models benchmark
- Round-trip 100 models benchmark
- Memory usage validation
- Incremental parsing performance

**Real-World Projects** (5 tests):
- Conduit integration
- Rocket.rs example integration
- Actix-web example integration
- Custom project integration

**Edge Cases** (10 tests):
- Custom derive macros
- Generic types
- Lifetime parameters
- Embedded structs
- Jsonb fields
- Malformed Rust files
- Non-model files
- Complex relationships
- Optional fields
- Circular references

---

## 📁 File Structure

```
tests/integration/rust/
├── __init__.py
├── test_integration_basic.py          # Basic integration tests
├── test_multi_entity_integration.py   # Multi-entity tests
├── test_round_trip.py                 # Round-trip validation
├── test_performance.py                # Performance benchmarks
├── test_real_world_projects.py        # External project tests
├── test_edge_cases.py                 # Edge case handling
├── sample_project/                    # Test Diesel project
│   └── src/
│       ├── models/
│       │   ├── product.rs
│       │   ├── category.rs
│       │   ├── customer.rs
│       │   ├── order.rs
│       │   └── order_item.rs
│       ├── schema.rs
│       └── handlers/
│           └── product.rs
└── external_projects/                 # Real-world test projects
    ├── conduit/
    ├── rocket-examples/
    └── actix-examples/

docs/guides/
├── RUST_MIGRATION_GUIDE.md            # Migration documentation
├── RUST_TROUBLESHOOTING.md            # Troubleshooting guide
└── RUST_VIDEO_TUTORIAL.md             # Video script

examples/rust-migration/
├── README.md
├── original/                          # Original Diesel code
├── specql/                            # SpecQL YAML
└── generated/                         # Generated code
```

---

## 🔗 Related Files

- **Previous**: [Week 15](./WEEK_15.md) - Rust Code Generation (SpecQL → Diesel)
- **Previous**: [Week 14](./WEEK_14.md) - Diesel Pattern Recognition (Rust → SpecQL)
- **Next**: [Week 17](./WEEK_17.md) - Cross-Language Validation
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
2. **Don't ignore performance**: It works on 5 models doesn't mean it works on 500
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

1. **Start simple, go complex**: Begin with basic models, work up to complex relationships
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

**Status**: 📅 Planned
**Risk Level**: Low (validation of completed work)
**Estimated Effort**: 40 hours (5 days)
**Prerequisites**: Weeks 13, 14, 15 complete ✅
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
