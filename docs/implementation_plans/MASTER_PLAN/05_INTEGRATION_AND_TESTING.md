# Phase E: Integration and Testing - Implementation Plan

**Duration**: 4 weeks
**Objective**: Integrate all tracks (A+B+C+D) and comprehensive testing
**Team**: All teams + QA
**Output**: Fully integrated, tested system ready for beta release

---

## 🎯 Vision

Bring together four parallel tracks into a cohesive, production-ready system:

**Track A** (DSL Expansion) → 35 primitive actions
**Track B** (Pattern Library) → PostgreSQL + Python multi-language
**Track C** (Three-Tier) → Domain patterns + entity templates
**Track D** (Reverse Engineering) → SQL → SpecQL conversion

**Result**: End-to-end workflow from legacy SQL → SpecQL → Multi-language generation

---

## 📊 Current State (After Tracks A-D)

**What Works**:
- ✅ 35 primitive actions (Track A)
- ✅ Pattern library database (Track B)
- ✅ PostgreSQL + Django + SQLAlchemy generation (Track B)
- ✅ 15 domain patterns (Track C)
- ✅ 15+ entity templates (Track C)
- ✅ Reverse engineering pipeline (Track D)

**What's Missing**:
- ❌ Full integration tests
- ❌ Performance benchmarks
- ❌ Documentation
- ❌ Migration guides
- ❌ E2E workflows
- ❌ Load testing

---

## 🚀 Target State

**Full E2E Workflows**:
1. **Legacy Migration**: SQL → SpecQL → PostgreSQL (validate equivalence)
2. **New Development**: Template → Customize → Generate (PostgreSQL + Python)
3. **Pattern Composition**: Primitives → Domain Pattern → Entity Template
4. **Multi-Language**: 1 YAML → PostgreSQL + Django + SQLAlchemy

**Quality Gates**:
- All 200+ tests passing
- Performance benchmarks met
- Documentation complete
- Migration guides validated
- Load testing passed

---

## 📅 4-Week Timeline

### Week 1: Integration Testing
**Goal**: Integrate all tracks and fix integration issues

### Week 2: Performance & Load Testing
**Goal**: Benchmark and optimize performance

### Week 3: Documentation & Examples
**Goal**: Complete user documentation and examples

### Week 4: Beta Preparation
**Goal**: Final polish, migration guides, beta release

---

## WEEK 1: Integration Testing

### Objective
Connect all tracks and validate end-to-end workflows.

---

### Day 1-2: E2E Workflow 1 - Legacy Migration

**Test**: SQL → SpecQL → PostgreSQL (validate equivalence)

**File**: `tests/integration/test_e2e_legacy_migration.py`

```python
"""
E2E Test: Legacy SQL Migration

Workflow:
1. Start with reference SQL function
2. Reverse engineer to SpecQL YAML
3. Generate PostgreSQL from YAML
4. Validate functional equivalence
"""

import pytest
from pathlib import Path
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser
from src.cli.generate import generate_schema
from src.testing.equivalence_tester import EquivalenceTester


def test_legacy_migration_calculate_total():
    """Test migrating calculate_total function"""

    # Original SQL
    reference_sql = """
    CREATE OR REPLACE FUNCTION crm.calculate_total(p_order_id UUID)
    RETURNS NUMERIC AS $$
    DECLARE
        v_total NUMERIC := 0;
    BEGIN
        SELECT SUM(amount) INTO v_total
        FROM tb_order_line
        WHERE order_id = p_order_id;

        RETURN v_total;
    END;
    $$ LANGUAGE plpgsql;
    """

    # Step 1: Reverse engineer
    parser = AlgorithmicParser()
    result = parser.parse(reference_sql)

    assert result.confidence >= 0.85
    assert result.function_name == "calculate_total"

    # Step 2: Generate SpecQL YAML
    yaml_content = parser.parse_to_yaml(reference_sql)

    # Step 3: Generate PostgreSQL from YAML
    generated_sql = generate_schema(yaml_content, target="postgresql")

    # Step 4: Test equivalence
    tester = EquivalenceTester()

    # Create test data
    test_data = {
        "tb_order": [
            {"pk_order": 1, "id": "uuid1", "identifier": "ORD-001"}
        ],
        "tb_order_line": [
            {"order_id": "uuid1", "amount": 100.00},
            {"order_id": "uuid1", "amount": 50.00},
            {"order_id": "uuid1", "amount": 25.00}
        ]
    }

    # Test both functions return same result
    result_original = tester.execute_function(
        reference_sql,
        "crm.calculate_total",
        {"order_id": "uuid1"},
        test_data
    )

    result_generated = tester.execute_function(
        generated_sql,
        "crm.calculate_total",
        {"order_id": "uuid1"},
        test_data
    )

    assert result_original == result_generated == 175.00


def test_legacy_migration_state_machine():
    """Test migrating state machine function"""

    reference_sql = Path("reference_sql/0_schema/fn_transition_contact_state.sql").read_text()

    # Reverse engineer
    parser = AlgorithmicParser()
    result = parser.parse(reference_sql)

    assert result.confidence >= 0.85

    # Generate YAML
    yaml_content = parser.parse_to_yaml(reference_sql)

    # Verify state machine pattern detected
    assert "state_machine" in yaml_content or "state" in yaml_content

    # Generate PostgreSQL
    generated_sql = generate_schema(yaml_content, target="postgresql")

    # Test equivalence
    tester = EquivalenceTester()
    assert tester.test_equivalence(reference_sql, generated_sql, test_cases=10)


def test_batch_migration_reference_sql():
    """Test batch migration of 50 reference SQL functions"""

    reference_dir = Path("../printoptim_specql/reference_sql/0_schema/")
    output_dir = Path("tests/integration/migrated_entities/")

    parser = AlgorithmicParser()
    results = []

    # Process first 50 functions
    sql_files = list(reference_dir.glob("*.sql"))[:50]

    for sql_file in sql_files:
        print(f"Processing {sql_file.name}...")

        sql = sql_file.read_text()

        # Reverse engineer
        result = parser.parse(sql)
        results.append((sql_file.name, result.confidence))

        # Generate YAML
        yaml_content = parser.parse_to_yaml(sql)

        # Write to output
        yaml_file = output_dir / f"{sql_file.stem}.yaml"
        yaml_file.write_text(yaml_content)

        # Generate PostgreSQL
        generated_sql = generate_schema(yaml_content, target="postgresql")

        # Validate SQL is parseable
        assert "CREATE OR REPLACE FUNCTION" in generated_sql

    # Summary
    avg_confidence = sum(conf for _, conf in results) / len(results)
    print(f"\n📊 Batch migration summary:")
    print(f"  Files processed: {len(results)}")
    print(f"  Average confidence: {avg_confidence:.0%}")
    print(f"  High confidence (>90%): {sum(1 for _, c in results if c > 0.90)}")

    assert avg_confidence >= 0.85
```

---

### Day 3-4: E2E Workflow 2 - New Development

**Test**: Template → Customize → Generate (PostgreSQL + Python)

**File**: `tests/integration/test_e2e_new_development.py`

```python
"""
E2E Test: New Development Workflow

Workflow:
1. Instantiate entity template (CRM Contact)
2. Customize with additional fields
3. Generate PostgreSQL schema
4. Generate Django models
5. Validate multi-language consistency
"""

import pytest
from src.pattern_library.api import PatternLibrary
from src.cli.generate import generate_schema


def test_new_development_crm_contact():
    """Test creating new CRM Contact from template"""

    # Step 1: Instantiate template
    library = PatternLibrary("pattern_library.db")

    entity_yaml = library.instantiate_entity_template(
        template_name="contact",
        template_namespace="crm",
        customizations={
            "additional_fields": {
                "linkedin_url": {"type": "text"},
                "twitter_handle": {"type": "text"}
            },
            "enable_lead_scoring": True
        }
    )

    # Verify template applied
    assert "first_name" in entity_yaml  # From template
    assert "linkedin_url" in entity_yaml  # Custom field
    assert "state" in entity_yaml  # From state_machine pattern
    assert "created_at" in entity_yaml  # From audit_trail pattern

    # Step 2: Generate PostgreSQL
    pg_sql = generate_schema(entity_yaml, target="postgresql")

    assert "CREATE TABLE crm.tb_contact" in pg_sql
    assert "first_name TEXT" in pg_sql
    assert "linkedin_url TEXT" in pg_sql
    assert "state TEXT" in pg_sql  # State machine field
    assert "created_at TIMESTAMPTZ" in pg_sql  # Audit field

    # Step 3: Generate Django models
    django_models = generate_schema(entity_yaml, target="python_django")

    assert "class Contact(models.Model):" in django_models
    assert "first_name = models.TextField()" in django_models
    assert "linkedin_url = models.TextField()" in django_models
    assert "state = models.TextField()" in django_models

    # Step 4: Validate consistency
    # Both should have same fields
    pg_fields = extract_fields_from_sql(pg_sql)
    django_fields = extract_fields_from_django(django_models)

    assert set(pg_fields) == set(django_fields)


def test_new_development_ecommerce_product():
    """Test creating E-Commerce Product from template"""

    library = PatternLibrary("pattern_library.db")

    entity_yaml = library.instantiate_entity_template(
        template_name="product",
        template_namespace="ecommerce",
        customizations={
            "enable_variants": True,
            "enable_inventory_tracking": True,
            "additional_patterns": ["soft_delete", "search_optimization"]
        }
    )

    # Generate multiple targets
    pg_sql = generate_schema(entity_yaml, target="postgresql")
    django_models = generate_schema(entity_yaml, target="python_django")
    sqlalchemy_models = generate_schema(entity_yaml, target="python_sqlalchemy")

    # All should compile without errors
    assert "CREATE TABLE ecommerce.tb_product" in pg_sql
    assert "class Product(models.Model):" in django_models
    assert "class Product(Base):" in sqlalchemy_models


def test_pattern_composition():
    """Test composing multiple domain patterns"""

    library = PatternLibrary("pattern_library.db")

    # Compose custom entity from patterns
    composed = library.compose_patterns(
        entity_name="CustomEntity",
        patterns=[
            {"pattern": "state_machine", "params": {"states": ["draft", "published", "archived"]}},
            {"pattern": "audit_trail", "params": {"track_versions": True}},
            {"pattern": "soft_delete", "params": {}},
            {"pattern": "commenting", "params": {}}
        ]
    )

    # Should have fields from all patterns
    assert "state" in composed["fields"]  # state_machine
    assert "created_at" in composed["fields"]  # audit_trail
    assert "deleted_at" in composed["fields"]  # soft_delete
    assert "comments" in composed["actions"]  # commenting

    # Generate code
    pg_sql = generate_schema(composed, target="postgresql")
    assert "CREATE TABLE" in pg_sql
```

---

### Day 5-7: Cross-Track Integration

**Tests**:
1. Track A + Track B - Primitives → Pattern Library
2. Track B + Track C - Pattern Library → Domain Patterns
3. Track C + Track D - Entity Templates → Reverse Engineering
4. All tracks combined

**File**: `tests/integration/test_cross_track_integration.py`

```python
def test_track_a_b_integration():
    """Test Track A primitives stored in Track B pattern library"""

    library = PatternLibrary(":memory:")

    # Add Track A primitive to Track B library
    library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={"type": "declare", "fields": ["variable_name", "variable_type"]}
    )

    library.add_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="{{ variable_name }} {{ variable_type }};"
    )

    library.add_implementation(
        pattern_name="declare",
        language_name="python_django",
        template="{{ variable_name }}: {{ variable_type }}"
    )

    # Compile to both languages
    pg_code = library.compile_pattern("declare", "postgresql", {"variable_name": "total", "variable_type": "NUMERIC"})
    py_code = library.compile_pattern("declare", "python_django", {"variable_name": "total", "variable_type": "Decimal"})

    assert pg_code == "total NUMERIC;"
    assert py_code == "total: Decimal"


def test_track_b_c_integration():
    """Test Track B library → Track C domain patterns"""

    library = PatternLibrary(":memory:")

    # Add domain pattern using Track B primitives
    library.add_domain_pattern(
        name="audit_trail",
        category="audit",
        description="Audit trail pattern",
        parameters={},
        implementation={
            "fields": [
                {"name": "created_at", "type": "timestamp"},
                {"name": "created_by", "type": "uuid"}
            ]
        }
    )

    # Instantiate pattern
    result = library.instantiate_domain_pattern("audit_trail", "Contact", {})

    assert "created_at" in [f["name"] for f in result["fields"]]
    assert "created_by" in [f["name"] for f in result["fields"]]


def test_all_tracks_integration():
    """Test full workflow using all tracks"""

    # Track D: Start with SQL
    sql = """
    CREATE OR REPLACE FUNCTION crm.qualify_lead(p_lead_id UUID)
    RETURNS app.mutation_result AS $$
    BEGIN
        UPDATE tb_contact SET state = 'qualified' WHERE id = p_lead_id;
        RETURN ROW(TRUE, 'Lead qualified', '{}', '{}')::app.mutation_result;
    END;
    $$ LANGUAGE plpgsql;
    """

    # Track D: Reverse engineer
    from src.reverse_engineering.algorithmic_parser import AlgorithmicParser
    parser = AlgorithmicParser()
    result = parser.parse(sql)

    # Track A: Uses expanded primitives
    assert any(step.type == "update" for step in result.steps)

    # Track B: Store in pattern library
    library = PatternLibrary(":memory:")
    # ... (add to library)

    # Track C: Detect pattern (state machine transition)
    # Should detect this is a state transition action

    # Generate multi-language
    yaml = parser.parse_to_yaml(sql)
    pg_sql = generate_schema(yaml, target="postgresql")
    django_code = generate_schema(yaml, target="python_django")

    assert "CREATE OR REPLACE FUNCTION" in pg_sql
    assert "def qualify_lead" in django_code
```

---

## WEEK 2: Performance & Load Testing

### Objective
Benchmark performance and optimize bottlenecks.

---

### Day 1-3: Performance Benchmarks

**File**: `tests/performance/test_benchmarks.py`

```python
"""
Performance benchmarks for all tracks
"""

import pytest
import time
from src.cli.generate import generate_schema
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


def test_benchmark_simple_entity_generation():
    """Benchmark: Generate simple entity (PostgreSQL)"""

    yaml_content = """
    entity: Contact
    fields:
      email: text
      name: text
    """

    start = time.time()
    sql = generate_schema(yaml_content, target="postgresql")
    elapsed = time.time() - start

    print(f"Simple entity generation: {elapsed:.3f}s")

    # Should be fast (< 100ms)
    assert elapsed < 0.1


def test_benchmark_complex_entity_generation():
    """Benchmark: Generate entity with 3 domain patterns"""

    yaml_content = """
    entity: Contact
    patterns:
      - state_machine
      - audit_trail
      - soft_delete
    fields:
      email: text
      name: text
    """

    start = time.time()
    sql = generate_schema(yaml_content, target="postgresql")
    elapsed = time.time() - start

    print(f"Complex entity generation: {elapsed:.3f}s")

    # Should still be fast (< 500ms)
    assert elapsed < 0.5


def test_benchmark_reverse_engineering():
    """Benchmark: Reverse engineer SQL function"""

    sql = """
    CREATE OR REPLACE FUNCTION crm.calculate_total(p_order_id UUID)
    RETURNS NUMERIC AS $$
    DECLARE v_total NUMERIC := 0;
    BEGIN
        SELECT SUM(amount) INTO v_total FROM tb_order_line WHERE order_id = p_order_id;
        RETURN v_total;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()

    start = time.time()
    result = parser.parse(sql)
    elapsed = time.time() - start

    print(f"Reverse engineering (algorithmic): {elapsed:.3f}s")

    # Should be fast (< 1s)
    assert elapsed < 1.0


def test_benchmark_batch_generation():
    """Benchmark: Batch generate 100 entities"""

    entities = [
        f"""
        entity: Entity{i}
        fields:
          name: text
          value: integer
        """
        for i in range(100)
    ]

    start = time.time()
    for yaml in entities:
        sql = generate_schema(yaml, target="postgresql")
    elapsed = time.time() - start

    print(f"Batch 100 entities: {elapsed:.3f}s")
    print(f"Average per entity: {elapsed/100:.3f}s")

    # Should be reasonable (< 10s total, < 100ms per entity)
    assert elapsed < 10.0


def test_benchmark_pattern_library_query():
    """Benchmark: Query pattern library"""

    library = PatternLibrary("pattern_library.db")

    start = time.time()
    for _ in range(1000):
        library.get_pattern("state_machine")
    elapsed = time.time() - start

    print(f"1000 pattern queries: {elapsed:.3f}s")
    print(f"Average per query: {elapsed/1000*1000:.3f}ms")

    # Should be very fast (< 10ms per query)
    assert elapsed < 10.0


@pytest.mark.slow
def test_benchmark_full_pipeline():
    """Benchmark: Full pipeline (reverse → generate → multi-language)"""

    sql = Path("reference_sql/0_schema/fn_complex_function.sql").read_text()

    parser = AlgorithmicParser()

    start = time.time()

    # Reverse engineer
    result = parser.parse(sql)
    yaml = parser.parse_to_yaml(sql)

    # Generate PostgreSQL
    pg_sql = generate_schema(yaml, target="postgresql")

    # Generate Django
    django_code = generate_schema(yaml, target="python_django")

    # Generate SQLAlchemy
    sa_code = generate_schema(yaml, target="python_sqlalchemy")

    elapsed = time.time() - start

    print(f"Full pipeline: {elapsed:.3f}s")

    # Should complete in reasonable time (< 5s)
    assert elapsed < 5.0
```

**Performance Targets**:
- Simple entity generation: < 100ms
- Complex entity generation: < 500ms
- Reverse engineering: < 1s
- Batch 100 entities: < 10s
- Pattern query: < 10ms
- Full pipeline: < 5s

---

### Day 4-5: Load Testing

**File**: `tests/performance/test_load.py`

```python
"""
Load testing for concurrent operations
"""

import pytest
import concurrent.futures
from src.cli.generate import generate_schema


def test_load_concurrent_generation():
    """Load test: 50 concurrent entity generations"""

    yaml_content = """
    entity: Contact
    fields:
      email: text
    """

    def generate():
        return generate_schema(yaml_content, target="postgresql")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(generate) for _ in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 50
    assert all("CREATE TABLE" in r for r in results)


def test_load_pattern_library_concurrent_access():
    """Load test: 100 concurrent pattern library queries"""

    library = PatternLibrary("pattern_library.db")

    def query_pattern():
        return library.get_pattern("state_machine")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(query_pattern) for _ in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 100
    assert all(r is not None for r in results)
```

---

## WEEK 3: Documentation & Examples

### Objective
Complete user-facing documentation and examples.

---

### Documentation Structure

```
docs/
├── getting_started.md
├── tutorials/
│   ├── 01_first_entity.md
│   ├── 02_using_patterns.md
│   ├── 03_custom_actions.md
│   ├── 04_reverse_engineering.md
│   └── 05_multi_language.md
├── reference/
│   ├── primitives.md (35 primitives)
│   ├── domain_patterns.md (15 patterns)
│   ├── entity_templates.md (15+ templates)
│   └── cli_commands.md
├── guides/
│   ├── migration_guide.md
│   ├── pattern_authoring.md
│   ├── contributing.md
│   └── best_practices.md
└── examples/
    ├── crm/
    ├── ecommerce/
    ├── healthcare/
    └── custom/
```

---

## WEEK 4: Beta Preparation

### Objective
Final polish and prepare for beta release.

---

### Checklist

**Code Quality**:
- [ ] All 200+ tests passing
- [ ] Code coverage > 85%
- [ ] Ruff + mypy clean
- [ ] Performance benchmarks met

**Documentation**:
- [ ] Getting started guide
- [ ] 5 tutorials complete
- [ ] Reference docs for all features
- [ ] Migration guide validated

**Examples**:
- [ ] 10+ example entities
- [ ] 3 full applications (CRM, E-Commerce, Healthcare)
- [ ] Video walkthrough recorded

**Infrastructure**:
- [ ] CI/CD pipeline configured
- [ ] Release scripts ready
- [ ] PyPI package configured
- [ ] Docker image available

**Beta Release**:
- [ ] Version tagged (v0.5.0-beta)
- [ ] Release notes written
- [ ] Beta testers identified
- [ ] Feedback channels established

---

## 📊 Phase E Summary (4 Weeks)

### Deliverables

**Tests**:
- ✅ 50+ integration tests
- ✅ 20+ E2E workflow tests
- ✅ 10+ performance benchmarks
- ✅ 10+ load tests

**Documentation**:
- ✅ Getting started guide
- ✅ 5 tutorials
- ✅ Complete reference docs
- ✅ Migration guide

**Examples**:
- ✅ 10+ example entities
- ✅ 3 full applications
- ✅ Video walkthrough

### Success Criteria

- [x] All integration tests passing
- [x] Performance targets met
- [x] Documentation complete
- [x] Examples validated
- [x] Beta ready

---

**Last Updated**: 2025-11-12
**Status**: Ready for Implementation
**Next**: Week 1 - Integration Testing (E2E workflows)
