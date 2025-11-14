# Week 11: Java Code Generation (SpecQL → Spring Boot)

**Date**: 2025-11-14 (Updated)
**Duration**: 5 days (40 hours)
**Status**: 📅 Ready to Execute
**Objective**: Generate Spring Boot Java code from SpecQL entities

**Prerequisites**:
- Week 10 complete (Spring Boot reverse engineering - ALL TESTS PASSING ✅)
- Understanding of SpecQL UniversalEntity/UniversalField structure
- Familiarity with JPA annotations and Spring Data

**Output**: Complete Java code generator with tests

---

## 🎯 Executive Summary

Week 11 completes the **bidirectional Java integration** by implementing code generation (SpecQL → Java). This is the reverse direction of Week 10 (Java → SpecQL).

**Input**: SpecQL YAML entity definitions
**Output**: Production-ready Spring Boot Java code

### Key Deliverables

1. **JPA Entity Generator** - `@Entity` classes with JPA annotations
2. **Repository Generator** - Spring Data `JpaRepository` interfaces
3. **Service Generator** - `@Service` classes with business logic
4. **Controller Generator** - `@RestController` with REST endpoints
5. **Complete Test Suite** - 50+ tests ensuring correctness

### Architecture

```
SpecQL YAML
    ↓
UniversalEntity (src/core/universal_ast.py)
    ↓
JavaEntityGenerator → Product.java (@Entity)
JavaRepositoryGenerator → ProductRepository.java (interface)
JavaServiceGenerator → ProductService.java (@Service)
JavaControllerGenerator → ProductController.java (@RestController)
```

---

## 📅 Daily Breakdown

### Day 1: JPA Entity Generator (8 hours)

**Objective**: Generate JPA `@Entity` classes from SpecQL entities

#### Morning (4 hours): Core Entity Generation

**Step 1.1: Create module structure** (30 min)

```bash
# Create directory structure
mkdir -p src/generators/java
touch src/generators/java/__init__.py
touch src/generators/java/entity_generator.py
touch tests/unit/generators/java/test_entity_generator.py
```

**Step 1.2: Write failing test** (30 min)

Create `tests/unit/generators/java/test_entity_generator.py`:

```python
"""Test JPA entity generation from SpecQL"""
import pytest
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.java.entity_generator import JavaEntityGenerator


def test_generate_simple_entity():
    """Test basic entity generation"""
    # Create SpecQL entity
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
            UniversalField(name="price", type=FieldType.INTEGER, required=True),
            UniversalField(name="active", type=FieldType.BOOLEAN, default=True),
        ],
        actions=[],
    )

    # Generate Java entity
    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    # Assertions
    assert "package ecommerce;" in java_code
    assert "@Entity" in java_code
    assert "@Table(name = \"tb_product\")" in java_code
    assert "public class Product" in java_code
    assert "@Id" in java_code
    assert "@GeneratedValue" in java_code
    assert "private Long id;" in java_code
    assert "@Column(nullable = false)" in java_code
    assert "private String name;" in java_code
    assert "private Integer price;" in java_code
    assert "private Boolean active = true;" in java_code


def test_generate_entity_with_reference():
    """Test entity with foreign key reference"""
    entity = UniversalEntity(
        name="Order",
        schema="ecommerce",
        fields=[
            UniversalField(name="quantity", type=FieldType.INTEGER),
            UniversalField(
                name="product",
                type=FieldType.REFERENCE,
                references="Product",
                required=True
            ),
        ],
        actions=[],
    )

    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    assert "@ManyToOne(fetch = FetchType.LAZY)" in java_code
    assert "@JoinColumn(name = \"fk_product\", nullable = false)" in java_code
    assert "private Product product;" in java_code


def test_generate_entity_with_enum():
    """Test entity with enum field"""
    entity = UniversalEntity(
        name="Contact",
        schema="crm",
        fields=[
            UniversalField(
                name="status",
                type=FieldType.ENUM,
                enum_values=["lead", "qualified", "customer"],
            ),
        ],
        actions=[],
    )

    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    assert "@Enumerated(EnumType.STRING)" in java_code
    assert "private ContactStatus status;" in java_code


def test_generate_entity_with_timestamps():
    """Test that audit fields are auto-generated"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT),
        ],
        actions=[],
    )

    generator = JavaEntityGenerator()
    java_code = generator.generate(entity)

    # Trinity pattern audit fields
    assert "@CreatedDate" in java_code
    assert "private LocalDateTime createdAt;" in java_code
    assert "@LastModifiedDate" in java_code
    assert "private LocalDateTime updatedAt;" in java_code
```

**Expected**: All tests FAIL (entity_generator.py doesn't exist yet)

**Step 1.3: Implement entity generator skeleton** (1 hour)

Create `src/generators/java/entity_generator.py`:

```python
"""Generate JPA entity classes from SpecQL entities"""
from dataclasses import dataclass
from typing import List
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


@dataclass
class JavaEntityGenerator:
    """Generates JPA @Entity classes from SpecQL entities"""

    def __init__(self, package_prefix: str = ""):
        self.package_prefix = package_prefix

    def generate(self, entity: UniversalEntity) -> str:
        """Generate complete Java entity class"""
        lines = []

        # Package declaration
        lines.append(f"package {entity.schema};")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Class declaration
        lines.append("@Entity")
        lines.append(f"@Table(name = \"tb_{entity.name.lower()}\")")
        lines.append(f"public class {entity.name} {{")
        lines.append("")

        # Primary key (Trinity pattern)
        lines.extend(self._generate_primary_key())
        lines.append("")

        # Fields
        for field in entity.fields:
            lines.extend(self._generate_field(field))
            lines.append("")

        # Audit fields (Trinity pattern)
        lines.extend(self._generate_audit_fields())
        lines.append("")

        # Getters/Setters
        lines.extend(self._generate_accessors(entity))

        lines.append("}")

        return "\n".join(lines)

    def _generate_imports(self, entity: UniversalEntity) -> List[str]:
        """Generate import statements"""
        imports = [
            "import javax.persistence.*;",
            "import java.time.LocalDateTime;",
            "import org.springframework.data.annotation.CreatedDate;",
            "import org.springframework.data.annotation.LastModifiedDate;",
            "import org.springframework.data.jpa.domain.support.AuditingEntityListener;",
        ]

        # Add enum imports if needed
        for field in entity.fields:
            if field.type == FieldType.ENUM:
                # Enum classes will be in same package
                pass

        return imports

    def _generate_primary_key(self) -> List[str]:
        """Generate Trinity pattern primary key"""
        return [
            "    @Id",
            "    @GeneratedValue(strategy = GenerationType.IDENTITY)",
            "    private Long id;",
        ]

    def _generate_field(self, field: UniversalField) -> List[str]:
        """Generate single field with annotations"""
        lines = []

        if field.type == FieldType.REFERENCE:
            # Foreign key relationship
            lines.append("    @ManyToOne(fetch = FetchType.LAZY)")
            nullable = "false" if field.required else "true"
            lines.append(f"    @JoinColumn(name = \"fk_{field.references.lower()}\", nullable = {nullable})")
            lines.append(f"    private {field.references} {field.name};")

        elif field.type == FieldType.ENUM:
            # Enum field
            lines.append("    @Enumerated(EnumType.STRING)")
            enum_class = self._to_pascal_case(field.name) + "Status"  # Convention
            lines.append(f"    private {enum_class} {field.name};")

        elif field.type == FieldType.LIST:
            # OneToMany relationship
            lines.append("    @OneToMany(mappedBy = \"parent\", cascade = CascadeType.ALL)")
            lines.append(f"    private List<{self._get_java_type(field)}> {field.name} = new ArrayList<>();")

        else:
            # Regular field
            if field.required:
                lines.append("    @Column(nullable = false)")

            java_type = self._get_java_type(field)
            default_value = f" = {self._format_default(field)}" if field.default else ""
            lines.append(f"    private {java_type} {field.name}{default_value};")

        return lines

    def _generate_audit_fields(self) -> List[str]:
        """Generate Trinity pattern audit fields"""
        return [
            "    @CreatedDate",
            "    @Column(nullable = false, updatable = false)",
            "    private LocalDateTime createdAt;",
            "",
            "    @LastModifiedDate",
            "    @Column(nullable = false)",
            "    private LocalDateTime updatedAt;",
            "",
            "    @Column",
            "    private LocalDateTime deletedAt;",
        ]

    def _generate_accessors(self, entity: UniversalEntity) -> List[str]:
        """Generate getters and setters"""
        lines = []

        # ID accessors
        lines.append("    public Long getId() {")
        lines.append("        return id;")
        lines.append("    }")
        lines.append("")
        lines.append("    public void setId(Long id) {")
        lines.append("        this.id = id;")
        lines.append("    }")
        lines.append("")

        # Field accessors
        for field in entity.fields:
            java_type = self._get_java_type(field)
            capitalized = field.name[0].upper() + field.name[1:]

            # Getter
            lines.append(f"    public {java_type} get{capitalized}() {{")
            lines.append(f"        return {field.name};")
            lines.append("    }")
            lines.append("")

            # Setter
            lines.append(f"    public void set{capitalized}({java_type} {field.name}) {{")
            lines.append(f"        this.{field.name} = {field.name};")
            lines.append("    }")
            lines.append("")

        return lines

    def _get_java_type(self, field: UniversalField) -> str:
        """Map SpecQL types to Java types"""
        type_map = {
            FieldType.TEXT: "String",
            FieldType.INTEGER: "Integer",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "LocalDateTime",
        }

        if field.type == FieldType.REFERENCE:
            return field.references
        elif field.type == FieldType.ENUM:
            return self._to_pascal_case(field.name) + "Status"
        elif field.type == FieldType.LIST:
            # Extract item type from list
            return "List<Object>"  # Simplified for now
        else:
            return type_map.get(field.type, "Object")

    def _format_default(self, field: UniversalField) -> str:
        """Format default value for Java"""
        if field.type == FieldType.TEXT:
            return f'"{field.default}"'
        elif field.type == FieldType.BOOLEAN:
            return str(field.default).lower()
        else:
            return str(field.default)

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
```

**Step 1.4: Run tests and iterate** (2 hours)

```bash
# Run tests
uv run pytest tests/unit/generators/java/test_entity_generator.py -v

# Expected: Some tests pass, some fail
# Fix issues until all tests pass
```

**Common issues to fix**:
- Missing imports
- Incorrect annotation format
- Wrong field type mappings
- Getter/setter capitalization

#### Afternoon (4 hours): Advanced Features

**Step 1.5: Add enum generation** (1.5 hours)

Create `src/generators/java/enum_generator.py`:

```python
"""Generate Java enum classes from SpecQL enum fields"""
from typing import List
from src.core.universal_ast import UniversalField, FieldType


class JavaEnumGenerator:
    """Generates Java enum classes"""

    def generate(self, field: UniversalField, package: str) -> str:
        """Generate enum class for an enum field"""
        if field.type != FieldType.ENUM:
            raise ValueError(f"Field {field.name} is not an enum")

        enum_name = self._to_pascal_case(field.name) + "Status"

        lines = []
        lines.append(f"package {package};")
        lines.append("")
        lines.append(f"public enum {enum_name} {{")

        # Enum values
        values = [f"    {val.upper()}" for val in field.enum_values]
        lines.append(",\n".join(values))

        lines.append("}")

        return "\n".join(lines)

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
```

Add test:

```python
def test_generate_enum_class():
    """Test enum class generation"""
    field = UniversalField(
        name="status",
        type=FieldType.ENUM,
        enum_values=["draft", "published", "archived"],
    )

    generator = JavaEnumGenerator()
    java_code = generator.generate(field, "com.example.blog")

    assert "package com.example.blog;" in java_code
    assert "public enum StatusStatus {" in java_code
    assert "DRAFT," in java_code
    assert "PUBLISHED," in java_code
    assert "ARCHIVED" in java_code
```

**Step 1.6: Add rich type support** (1.5 hours)

Handle composite types (money, dimensions, etc.):

```python
def _generate_rich_field(self, field: UniversalField) -> List[str]:
    """Generate rich/composite type field"""
    lines = []

    if field.composite_type == "money":
        lines.append("    @Embedded")
        lines.append(f"    private Money {field.name};")
    elif field.composite_type == "dimensions":
        lines.append("    @Embedded")
        lines.append(f"    @AttributeOverrides({{")
        lines.append(f"        @AttributeOverride(name = \"length\", column = @Column(name = \"{field.name}_length\")),")
        lines.append(f"        @AttributeOverride(name = \"width\", column = @Column(name = \"{field.name}_width\")),")
        lines.append(f"        @AttributeOverride(name = \"height\", column = @Column(name = \"{field.name}_height\"))")
        lines.append(f"    }})")
        lines.append(f"    private Dimensions {field.name};")

    return lines
```

**Step 1.7: Add multi-tenant support** (1 hour)

```python
def _generate_tenant_field(self, entity: UniversalEntity) -> List[str]:
    """Generate tenant_id field for multi-tenant entities"""
    if not entity.is_multi_tenant:
        return []

    return [
        "    @Column(nullable = false)",
        "    private UUID tenantId;",
        "",
    ]
```

**Day 1 Deliverables**:
- ✅ `JavaEntityGenerator` class complete
- ✅ `JavaEnumGenerator` class complete
- ✅ 15+ unit tests passing
- ✅ Generates valid JPA entities with:
  - Trinity pattern (id, createdAt, updatedAt)
  - Foreign keys (@ManyToOne, @JoinColumn)
  - Enums (@Enumerated)
  - Rich types (@Embedded)
  - Multi-tenancy (tenantId)

---

### Day 2: Repository Generator (8 hours)

**Objective**: Generate Spring Data `JpaRepository` interfaces

#### Morning (4 hours): Basic Repository Generation

**Step 2.1: Write failing tests** (1 hour)

Create `tests/unit/generators/java/test_repository_generator.py`:

```python
"""Test Spring Data repository generation"""
import pytest
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.generators.java.repository_generator import JavaRepositoryGenerator


def test_generate_basic_repository():
    """Test basic JpaRepository interface generation"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT),
            UniversalField(name="sku", type=FieldType.TEXT, unique=True),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    assert "package ecommerce.repository;" in java_code
    assert "import org.springframework.data.jpa.repository.JpaRepository;" in java_code
    assert "import ecommerce.Product;" in java_code
    assert "@Repository" in java_code
    assert "public interface ProductRepository extends JpaRepository<Product, Long>" in java_code


def test_generate_repository_with_query_methods():
    """Test auto-generated query methods"""
    entity = UniversalEntity(
        name="User",
        schema="auth",
        fields=[
            UniversalField(name="email", type=FieldType.TEXT, unique=True),
            UniversalField(name="username", type=FieldType.TEXT, unique=True),
            UniversalField(name="active", type=FieldType.BOOLEAN),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    # Spring Data query methods for unique fields
    assert "Optional<User> findByEmail(String email);" in java_code
    assert "Optional<User> findByUsername(String username);" in java_code
    assert "boolean existsByEmail(String email);" in java_code
    assert "List<User> findByActive(Boolean active);" in java_code


def test_generate_repository_with_custom_queries():
    """Test @Query annotations for complex queries"""
    entity = UniversalEntity(
        name="Order",
        schema="ecommerce",
        fields=[
            UniversalField(name="status", type=FieldType.ENUM, enum_values=["pending", "shipped"]),
            UniversalField(name="total", type=FieldType.INTEGER),
        ],
        actions=[],
    )

    generator = JavaRepositoryGenerator()
    java_code = generator.generate(entity)

    # Custom query for range search
    assert "@Query" in java_code
    assert "SELECT o FROM Order o WHERE o.total > :minTotal" in java_code
```

**Step 2.2: Implement repository generator** (2 hours)

Create `src/generators/java/repository_generator.py`:

```python
"""Generate Spring Data JpaRepository interfaces"""
from typing import List
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType


class JavaRepositoryGenerator:
    """Generates Spring Data repository interfaces"""

    def generate(self, entity: UniversalEntity) -> str:
        """Generate JpaRepository interface"""
        lines = []

        # Package declaration
        lines.append(f"package {entity.schema}.repository;")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Interface declaration
        lines.append("@Repository")
        lines.append(f"public interface {entity.name}Repository extends JpaRepository<{entity.name}, Long> {{")
        lines.append("")

        # Query methods
        lines.extend(self._generate_query_methods(entity))

        # Custom queries
        lines.extend(self._generate_custom_queries(entity))

        lines.append("}")

        return "\n".join(lines)

    def _generate_imports(self, entity: UniversalEntity) -> List[str]:
        """Generate import statements"""
        return [
            "import org.springframework.data.jpa.repository.JpaRepository;",
            "import org.springframework.data.jpa.repository.Query;",
            "import org.springframework.data.repository.query.Param;",
            "import org.springframework.stereotype.Repository;",
            f"import {entity.schema}.{entity.name};",
            "import java.util.List;",
            "import java.util.Optional;",
        ]

    def _generate_query_methods(self, entity: UniversalEntity) -> List[str]:
        """Generate Spring Data query methods"""
        lines = []

        for field in entity.fields:
            if field.type == FieldType.REFERENCE:
                continue  # Skip foreign keys for now

            java_type = self._get_java_type(field)
            capitalized = field.name[0].upper() + field.name[1:]

            # findBy method
            if field.unique:
                lines.append(f"    Optional<{entity.name}> findBy{capitalized}({java_type} {field.name});")
                lines.append("")
                lines.append(f"    boolean existsBy{capitalized}({java_type} {field.name});")
            else:
                lines.append(f"    List<{entity.name}> findBy{capitalized}({java_type} {field.name});")

            lines.append("")

        return lines

    def _generate_custom_queries(self, entity: UniversalEntity) -> List[str]:
        """Generate @Query methods for complex queries"""
        lines = []

        # Example: Range query for integer fields
        for field in entity.fields:
            if field.type == FieldType.INTEGER:
                capitalized = field.name[0].upper() + field.name[1:]
                lines.append(f"    @Query(\"SELECT e FROM {entity.name} e WHERE e.{field.name} > :min{capitalized}\")")
                lines.append(f"    List<{entity.name}> findBy{capitalized}GreaterThan(@Param(\"min{capitalized}\") Integer min{capitalized});")
                lines.append("")

        return lines

    def _get_java_type(self, field: UniversalField) -> str:
        """Map SpecQL types to Java types"""
        type_map = {
            FieldType.TEXT: "String",
            FieldType.INTEGER: "Integer",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "LocalDateTime",
        }

        if field.type == FieldType.REFERENCE:
            return field.references
        elif field.type == FieldType.ENUM:
            return self._to_pascal_case(field.name) + "Status"
        else:
            return type_map.get(field.type, "Object")

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
```

**Step 2.3: Run tests and fix** (1 hour)

```bash
uv run pytest tests/unit/generators/java/test_repository_generator.py -v
```

#### Afternoon (4 hours): Advanced Repository Features

**Step 2.4: Add pagination support** (1.5 hours)

```python
def _generate_pagination_methods(self, entity: UniversalEntity) -> List[str]:
    """Generate paginated query methods"""
    lines = []

    # Paginated findAll variants
    for field in entity.fields:
        if field.type in [FieldType.TEXT, FieldType.BOOLEAN]:
            capitalized = field.name[0].upper() + field.name[1:]
            java_type = self._get_java_type(field)

            lines.append(f"    Page<{entity.name}> findBy{capitalized}({java_type} {field.name}, Pageable pageable);")
            lines.append("")

    return lines
```

**Step 2.5: Add specification support** (1.5 hours)

```python
def _generate_specification_interface(self, entity: UniversalEntity) -> List[str]:
    """Add JpaSpecificationExecutor for dynamic queries"""
    # Modify extends clause
    return [
        f"public interface {entity.name}Repository extends JpaRepository<{entity.name}, Long>, JpaSpecificationExecutor<{entity.name}> {{"
    ]
```

**Step 2.6: Add soft delete support** (1 hour)

```python
def _generate_soft_delete_queries(self, entity: UniversalEntity) -> List[str]:
    """Generate queries that respect deletedAt"""
    return [
        f"    @Query(\"SELECT e FROM {entity.name} e WHERE e.deletedAt IS NULL\")",
        f"    List<{entity.name}> findAllActive();",
        "",
        f"    @Query(\"SELECT e FROM {entity.name} e WHERE e.deletedAt IS NULL AND e.id = :id\")",
        f"    Optional<{entity.name}> findActiveById(@Param(\"id\") Long id);",
        "",
    ]
```

**Day 2 Deliverables**:
- ✅ `JavaRepositoryGenerator` complete
- ✅ 12+ unit tests passing
- ✅ Generates Spring Data repositories with:
  - `JpaRepository` interface extension
  - Query methods (findBy, existsBy)
  - Custom @Query methods
  - Pagination support
  - Soft delete queries

---

### Day 3: Service Generator (8 hours)

**Objective**: Generate `@Service` classes with business logic

#### Morning (4 hours): Basic Service Generation

**Step 3.1: Write failing tests** (1 hour)

Create `tests/unit/generators/java/test_service_generator.py`:

```python
"""Test Spring @Service class generation"""
import pytest
from src.core.universal_ast import (
    UniversalEntity, UniversalField, UniversalAction,
    UniversalStep, FieldType, StepType
)
from src.generators.java.service_generator import JavaServiceGenerator


def test_generate_basic_service():
    """Test basic @Service class generation"""
    entity = UniversalEntity(
        name="Product",
        schema="ecommerce",
        fields=[
            UniversalField(name="name", type=FieldType.TEXT, required=True),
            UniversalField(name="price", type=FieldType.INTEGER),
        ],
        actions=[],
    )

    generator = JavaServiceGenerator()
    java_code = generator.generate(entity)

    assert "package ecommerce.service;" in java_code
    assert "import org.springframework.stereotype.Service;" in java_code
    assert "@Service" in java_code
    assert "public class ProductService" in java_code
    assert "private final ProductRepository productRepository;" in java_code
    assert "public ProductService(ProductRepository productRepository)" in java_code


def test_generate_service_with_crud_methods():
    """Test CRUD methods generation"""
    entity = UniversalEntity(
        name="User",
        schema="auth",
        fields=[UniversalField(name="email", type=FieldType.TEXT, unique=True)],
        actions=[],
    )

    generator = JavaServiceGenerator()
    java_code = generator.generate(entity)

    # CRUD methods
    assert "public User create(User user)" in java_code
    assert "public Optional<User> findById(Long id)" in java_code
    assert "public List<User> findAll()" in java_code
    assert "public User update(Long id, User user)" in java_code
    assert "public void delete(Long id)" in java_code


def test_generate_service_with_custom_action():
    """Test custom business logic method from SpecQL action"""
    entity = UniversalEntity(
        name="Order",
        schema="ecommerce",
        fields=[
            UniversalField(name="status", type=FieldType.ENUM, enum_values=["pending", "shipped"]),
        ],
        actions=[
            UniversalAction(
                name="ship_order",
                entity="Order",
                steps=[
                    UniversalStep(
                        type=StepType.VALIDATE,
                        expression="status = 'pending'"
                    ),
                    UniversalStep(
                        type=StepType.UPDATE,
                        entity="Order",
                        fields={"status": "shipped"}
                    ),
                ],
                impacts=["Order"],
            )
        ],
    )

    generator = JavaServiceGenerator()
    java_code = generator.generate(entity)

    assert "@Transactional" in java_code
    assert "public Order shipOrder(Long orderId)" in java_code
    assert "if (!order.getStatus().equals(OrderStatus.PENDING))" in java_code
    assert "order.setStatus(OrderStatus.SHIPPED);" in java_code
```

**Step 3.2: Implement service generator** (2 hours)

Create `src/generators/java/service_generator.py`:

```python
"""Generate Spring @Service classes with business logic"""
from typing import List
from src.core.universal_ast import UniversalEntity, UniversalAction, UniversalStep, StepType


class JavaServiceGenerator:
    """Generates Spring @Service classes"""

    def generate(self, entity: UniversalEntity) -> str:
        """Generate complete service class"""
        lines = []

        # Package declaration
        lines.append(f"package {entity.schema}.service;")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Class declaration
        lines.append("@Service")
        lines.append(f"public class {entity.name}Service {{")
        lines.append("")

        # Repository dependency injection
        lines.extend(self._generate_dependencies(entity))
        lines.append("")

        # Constructor
        lines.extend(self._generate_constructor(entity))
        lines.append("")

        # CRUD methods
        lines.extend(self._generate_crud_methods(entity))
        lines.append("")

        # Custom action methods
        for action in entity.actions:
            lines.extend(self._generate_action_method(entity, action))
            lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def _generate_imports(self, entity: UniversalEntity) -> List[str]:
        """Generate import statements"""
        return [
            "import org.springframework.stereotype.Service;",
            "import org.springframework.transaction.annotation.Transactional;",
            f"import {entity.schema}.{entity.name};",
            f"import {entity.schema}.repository.{entity.name}Repository;",
            "import java.util.List;",
            "import java.util.Optional;",
        ]

    def _generate_dependencies(self, entity: UniversalEntity) -> List[str]:
        """Generate repository field"""
        repo_field = f"{entity.name.lower()}Repository"
        return [
            f"    private final {entity.name}Repository {repo_field};",
        ]

    def _generate_constructor(self, entity: UniversalEntity) -> List[str]:
        """Generate constructor with dependency injection"""
        repo_field = f"{entity.name.lower()}Repository"
        return [
            f"    public {entity.name}Service({entity.name}Repository {repo_field}) {{",
            f"        this.{repo_field} = {repo_field};",
            "    }",
        ]

    def _generate_crud_methods(self, entity: UniversalEntity) -> List[str]:
        """Generate standard CRUD operations"""
        lines = []
        repo = f"{entity.name.lower()}Repository"

        # CREATE
        lines.append("    @Transactional")
        lines.append(f"    public {entity.name} create({entity.name} {entity.name.lower()}) {{")
        lines.append(f"        return {repo}.save({entity.name.lower()});")
        lines.append("    }")
        lines.append("")

        # READ
        lines.append(f"    public Optional<{entity.name}> findById(Long id) {{")
        lines.append(f"        return {repo}.findById(id);")
        lines.append("    }")
        lines.append("")

        lines.append(f"    public List<{entity.name}> findAll() {{")
        lines.append(f"        return {repo}.findAll();")
        lines.append("    }")
        lines.append("")

        # UPDATE
        lines.append("    @Transactional")
        lines.append(f"    public {entity.name} update(Long id, {entity.name} updated) {{")
        lines.append(f"        {entity.name} existing = {repo}.findById(id)")
        lines.append(f"            .orElseThrow(() -> new RuntimeException(\"{entity.name} not found\"));")
        lines.append("")
        lines.append("        // Update fields")
        lines.append("        // TODO: Add field setters")
        lines.append("")
        lines.append(f"        return {repo}.save(existing);")
        lines.append("    }")
        lines.append("")

        # DELETE (soft delete)
        lines.append("    @Transactional")
        lines.append(f"    public void delete(Long id) {{")
        lines.append(f"        {entity.name} entity = {repo}.findById(id)")
        lines.append(f"            .orElseThrow(() -> new RuntimeException(\"{entity.name} not found\"));")
        lines.append("")
        lines.append("        entity.setDeletedAt(LocalDateTime.now());")
        lines.append(f"        {repo}.save(entity);")
        lines.append("    }")

        return lines

    def _generate_action_method(self, entity: UniversalEntity, action: UniversalAction) -> List[str]:
        """Generate custom business logic method from SpecQL action"""
        lines = []

        method_name = self._to_camel_case(action.name)

        lines.append("    @Transactional")
        lines.append(f"    public {entity.name} {method_name}(Long {entity.name.lower()}Id) {{")

        # Load entity
        repo = f"{entity.name.lower()}Repository"
        lines.append(f"        {entity.name} {entity.name.lower()} = {repo}.findById({entity.name.lower()}Id)")
        lines.append(f"            .orElseThrow(() -> new RuntimeException(\"{entity.name} not found\"));")
        lines.append("")

        # Generate steps
        for step in action.steps:
            lines.extend(self._generate_step(entity, step))

        # Save and return
        lines.append("")
        lines.append(f"        return {repo}.save({entity.name.lower()});")
        lines.append("    }")

        return lines

    def _generate_step(self, entity: UniversalEntity, step: UniversalStep) -> List[str]:
        """Generate Java code for a single action step"""
        if step.type == StepType.VALIDATE:
            return self._generate_validate_step(entity, step)
        elif step.type == StepType.UPDATE:
            return self._generate_update_step(entity, step)
        elif step.type == StepType.IF:
            return self._generate_if_step(entity, step)
        else:
            return [f"        // TODO: Implement {step.type.value} step"]

    def _generate_validate_step(self, entity: UniversalEntity, step: UniversalStep) -> List[str]:
        """Generate validation check"""
        # Parse expression (simplified)
        # Example: "status = 'pending'" → if (!order.getStatus().equals(OrderStatus.PENDING))
        condition = self._parse_expression_to_java(entity, step.expression)

        return [
            f"        if (!({condition})) {{",
            f"            throw new IllegalStateException(\"Validation failed: {step.expression}\");",
            "        }",
        ]

    def _generate_update_step(self, entity: UniversalEntity, step: UniversalStep) -> List[str]:
        """Generate field update"""
        lines = []

        for field_name, value in step.fields.items():
            setter = f"set{field_name[0].upper()}{field_name[1:]}"
            # Format value based on type
            formatted_value = self._format_value(value)
            lines.append(f"        {entity.name.lower()}.{setter}({formatted_value});")

        return lines

    def _generate_if_step(self, entity: UniversalEntity, step: UniversalStep) -> List[str]:
        """Generate if/else block"""
        condition = self._parse_expression_to_java(entity, step.expression)

        lines = [f"        if ({condition}) {{"]

        # Then steps
        for sub_step in step.steps:
            sub_lines = self._generate_step(entity, sub_step)
            lines.extend([f"    {line}" for line in sub_lines])

        lines.append("        }")

        return lines

    def _parse_expression_to_java(self, entity: UniversalEntity, expression: str) -> str:
        """Convert SpecQL expression to Java condition"""
        # Simplified parser
        # Example: "status = 'pending'" → "order.getStatus().equals(OrderStatus.PENDING)"

        if "=" in expression:
            field, value = expression.split("=")
            field = field.strip()
            value = value.strip().strip("'\"")

            getter = f"get{field[0].upper()}{field[1:]}"
            formatted_value = self._format_value(value)

            return f"{entity.name.lower()}.{getter}().equals({formatted_value})"

        return expression

    def _format_value(self, value: any) -> str:
        """Format value for Java"""
        if isinstance(value, str):
            # Check if it's an enum value
            if value.isupper() or "_" in value:
                return value  # Assume enum constant
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        else:
            return str(value)

    def _to_camel_case(self, name: str) -> str:
        """Convert snake_case to camelCase"""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
```

**Step 3.3: Run tests** (1 hour)

```bash
uv run pytest tests/unit/generators/java/test_service_generator.py -v
```

#### Afternoon (4 hours): Advanced Service Features

**Step 3.4: Add validation logic** (1.5 hours)
**Step 3.5: Add transaction management** (1 hour)
**Step 3.6: Add error handling** (1.5 hours)

**Day 3 Deliverables**:
- ✅ `JavaServiceGenerator` complete
- ✅ 10+ unit tests passing
- ✅ Generates @Service classes with:
  - CRUD operations
  - Custom business logic from SpecQL actions
  - @Transactional annotations
  - Error handling

---

### Day 4: Controller Generator & Integration Tests (8 hours)

**Objective**: Generate REST controllers and test end-to-end

#### Morning (4 hours): Controller Generation

**Step 4.1: Write tests and implement** (3 hours)

Create `src/generators/java/controller_generator.py`:

```python
"""Generate Spring @RestController classes"""
from typing import List
from src.core.universal_ast import UniversalEntity


class JavaControllerGenerator:
    """Generates Spring @RestController classes"""

    def generate(self, entity: UniversalEntity) -> str:
        """Generate complete REST controller"""
        lines = []

        # Package
        lines.append(f"package {entity.schema}.controller;")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Class declaration
        lines.append("@RestController")
        lines.append(f"@RequestMapping(\"/api/{entity.name.lower()}s\")")
        lines.append(f"public class {entity.name}Controller {{")
        lines.append("")

        # Service injection
        lines.extend(self._generate_dependencies(entity))
        lines.append("")

        # Constructor
        lines.extend(self._generate_constructor(entity))
        lines.append("")

        # REST endpoints
        lines.extend(self._generate_rest_endpoints(entity))

        lines.append("}")

        return "\n".join(lines)

    def _generate_rest_endpoints(self, entity: UniversalEntity) -> List[str]:
        """Generate CRUD REST endpoints"""
        lines = []
        service = f"{entity.name.lower()}Service"

        # POST - Create
        lines.append("    @PostMapping")
        lines.append(f"    public ResponseEntity<{entity.name}> create(@RequestBody {entity.name} {entity.name.lower()}) {{")
        lines.append(f"        {entity.name} created = {service}.create({entity.name.lower()});")
        lines.append("        return ResponseEntity.status(HttpStatus.CREATED).body(created);")
        lines.append("    }")
        lines.append("")

        # GET - Read by ID
        lines.append("    @GetMapping(\"/{id}\")")
        lines.append(f"    public ResponseEntity<{entity.name}> getById(@PathVariable Long id) {{")
        lines.append(f"        return {service}.findById(id)")
        lines.append("            .map(ResponseEntity::ok)")
        lines.append("            .orElse(ResponseEntity.notFound().build());")
        lines.append("    }")
        lines.append("")

        # GET - List all
        lines.append("    @GetMapping")
        lines.append(f"    public List<{entity.name}> getAll() {{")
        lines.append(f"        return {service}.findAll();")
        lines.append("    }")
        lines.append("")

        # PUT - Update
        lines.append("    @PutMapping(\"/{id}\")")
        lines.append(f"    public ResponseEntity<{entity.name}> update(@PathVariable Long id, @RequestBody {entity.name} {entity.name.lower()}) {{")
        lines.append(f"        {entity.name} updated = {service}.update(id, {entity.name.lower()});")
        lines.append("        return ResponseEntity.ok(updated);")
        lines.append("    }")
        lines.append("")

        # DELETE
        lines.append("    @DeleteMapping(\"/{id}\")")
        lines.append("    public ResponseEntity<Void> delete(@PathVariable Long id) {")
        lines.append(f"        {service}.delete(id);")
        lines.append("        return ResponseEntity.noContent().build();")
        lines.append("    }")

        return lines
```

**Step 4.2: Add validation** (1 hour)

Add `@Valid` annotations and error handling.

#### Afternoon (4 hours): Integration Testing

**Step 4.3: Create integration test** (2 hours)

Create `tests/integration/java/test_java_generation_e2e.py`:

```python
"""End-to-end test: SpecQL YAML → Java Spring Boot code"""
import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.java.entity_generator import JavaEntityGenerator
from src.generators.java.repository_generator import JavaRepositoryGenerator
from src.generators.java.service_generator import JavaServiceGenerator
from src.generators.java.controller_generator import JavaControllerGenerator


def test_complete_spring_boot_generation():
    """Test full code generation pipeline"""
    # Parse SpecQL YAML
    yaml_content = """
entity: Product
schema: ecommerce
fields:
  name: text!
  price: integer
  active: boolean = true
actions:
  - name: activate_product
    steps:
      - validate: active = false
      - update: Product SET active = true
"""

    parser = SpecQLParser()
    entity = parser.parse(yaml_content)

    # Generate all Java classes
    entity_gen = JavaEntityGenerator()
    repo_gen = JavaRepositoryGenerator()
    service_gen = JavaServiceGenerator()
    controller_gen = JavaControllerGenerator()

    entity_code = entity_gen.generate(entity)
    repo_code = repo_gen.generate(entity)
    service_code = service_gen.generate(entity)
    controller_code = controller_gen.generate(entity)

    # Verify entity
    assert "@Entity" in entity_code
    assert "public class Product" in entity_code

    # Verify repository
    assert "public interface ProductRepository extends JpaRepository" in repo_code

    # Verify service
    assert "@Service" in service_code
    assert "public class ProductService" in service_code
    assert "public Product activateProduct" in service_code

    # Verify controller
    assert "@RestController" in controller_code
    assert "@RequestMapping(\"/api/products\")" in controller_code


def test_generated_code_compiles():
    """Test that generated Java code is syntactically valid"""
    # This would require Java compiler integration
    # For now, we'll do string validation
    pass
```

**Step 4.4: Add orchestrator** (2 hours)

Create `src/generators/java/java_generator_orchestrator.py`:

```python
"""Orchestrate all Java generators"""
from dataclasses import dataclass
from pathlib import Path
from typing import List
from src.core.universal_ast import UniversalEntity
from src.generators.java.entity_generator import JavaEntityGenerator
from src.generators.java.repository_generator import JavaRepositoryGenerator
from src.generators.java.service_generator import JavaServiceGenerator
from src.generators.java.controller_generator import JavaControllerGenerator
from src.generators.java.enum_generator import JavaEnumGenerator


@dataclass
class GeneratedFile:
    """Represents a generated Java file"""
    path: str
    content: str


class JavaGeneratorOrchestrator:
    """Orchestrates all Java code generation"""

    def __init__(self, output_dir: str = "generated/java"):
        self.output_dir = Path(output_dir)
        self.entity_gen = JavaEntityGenerator()
        self.repo_gen = JavaRepositoryGenerator()
        self.service_gen = JavaServiceGenerator()
        self.controller_gen = JavaControllerGenerator()
        self.enum_gen = JavaEnumGenerator()

    def generate_all(self, entity: UniversalEntity) -> List[GeneratedFile]:
        """Generate all Java files for an entity"""
        files = []

        # Entity class
        files.append(GeneratedFile(
            path=f"{entity.schema}/{entity.name}.java",
            content=self.entity_gen.generate(entity)
        ))

        # Enums
        for field in entity.fields:
            if field.type == FieldType.ENUM:
                enum_code = self.enum_gen.generate(field, entity.schema)
                enum_name = self._to_pascal_case(field.name) + "Status"
                files.append(GeneratedFile(
                    path=f"{entity.schema}/{enum_name}.java",
                    content=enum_code
                ))

        # Repository
        files.append(GeneratedFile(
            path=f"{entity.schema}/repository/{entity.name}Repository.java",
            content=self.repo_gen.generate(entity)
        ))

        # Service
        files.append(GeneratedFile(
            path=f"{entity.schema}/service/{entity.name}Service.java",
            content=self.service_gen.generate(entity)
        ))

        # Controller
        files.append(GeneratedFile(
            path=f"{entity.schema}/controller/{entity.name}Controller.java",
            content=self.controller_gen.generate(entity)
        ))

        return files

    def write_files(self, files: List[GeneratedFile]) -> None:
        """Write generated files to disk"""
        for file in files:
            full_path = self.output_dir / file.path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(file.content)

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
```

**Day 4 Deliverables**:
- ✅ `JavaControllerGenerator` complete
- ✅ `JavaGeneratorOrchestrator` complete
- ✅ 8+ integration tests passing
- ✅ Full pipeline: YAML → Entity/Repository/Service/Controller

---

### Day 5: Documentation, CLI, & Polish (8 hours)

**Objective**: Complete documentation, add CLI commands, final polish

#### Morning (4 hours): CLI Integration

**Step 5.1: Add CLI command** (2 hours)

Add to `src/cli/generate.py`:

```python
@cli.command("java")
@click.argument("entity_file", type=click.Path(exists=True))
@click.option("--output-dir", default="generated/java", help="Output directory")
def generate_java(entity_file: str, output_dir: str):
    """Generate Spring Boot Java code from SpecQL entity"""
    # Parse SpecQL
    parser = SpecQLParser()
    with open(entity_file) as f:
        entity = parser.parse(f.read())

    # Generate Java code
    orchestrator = JavaGeneratorOrchestrator(output_dir)
    files = orchestrator.generate_all(entity)
    orchestrator.write_files(files)

    click.echo(f"✅ Generated {len(files)} Java files in {output_dir}")
    for file in files:
        click.echo(f"  - {file.path}")
```

**Step 5.2: Test CLI** (1 hour)

```bash
# Test command
uv run specql generate java entities/product.yaml --output-dir=./test_output

# Verify files created
ls -R test_output/
```

**Step 5.3: Add validation** (1 hour)

Add pre-generation validation to catch errors early.

#### Afternoon (4 hours): Documentation & Examples

**Step 5.4: Write user guide** (2 hours)

Create `docs/guides/JAVA_CODE_GENERATION.md`:

```markdown
# Java Code Generation Guide

## Overview

SpecQL can generate production-ready Spring Boot Java code from your entity definitions.

## Quick Start

1. Define entity in SpecQL YAML
2. Run generator: `specql generate java entities/product.yaml`
3. Import generated code into your Spring Boot project

## Example

**Input** (`product.yaml`):
```yaml
entity: Product
schema: ecommerce
fields:
  name: text!
  price: integer
  active: boolean = true
```

**Output**:
- `ecommerce/Product.java` - JPA entity with @Entity
- `ecommerce/repository/ProductRepository.java` - Spring Data repository
- `ecommerce/service/ProductService.java` - Business logic service
- `ecommerce/controller/ProductController.java` - REST controller

## Generated Code Features

- Trinity Pattern (id, createdAt, updatedAt, deletedAt)
- JPA annotations (@Entity, @Column, @ManyToOne)
- Spring Data repositories with query methods
- RESTful endpoints (GET, POST, PUT, DELETE)
- Transaction management (@Transactional)
- Soft delete support

## Configuration

### Package Names

Use `--package-prefix` to set base package:

```bash
specql generate java entities/product.yaml --package-prefix=com.example
```

### Custom Templates

Override default templates with `--template-dir`:

```bash
specql generate java entities/ --template-dir=./custom-templates
```

## Integration with Existing Projects

1. Generate code in separate directory
2. Review generated files
3. Copy to `src/main/java/` in your Spring Boot project
4. Add dependencies to `pom.xml`:

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

## Best Practices

- Review generated code before committing
- Extend generated classes via inheritance when adding custom logic
- Use SpecQL actions for business logic (auto-generates service methods)
- Regenerate when entity schema changes

## Troubleshooting

### Issue: Import errors

**Solution**: Ensure all referenced entities are generated

### Issue: Compilation errors

**Solution**: Check Java version compatibility (requires Java 11+)
```

**Step 5.5: Create examples** (1 hour)

Create example entities in `examples/java/`:
- `examples/java/simple-entity.yaml`
- `examples/java/entity-with-relationships.yaml`
- `examples/java/custom-actions.yaml`

**Step 5.6: Run full test suite** (1 hour)

```bash
# Run all Java generator tests
uv run pytest tests/unit/generators/java/ -v
uv run pytest tests/integration/java/ -v

# Check coverage
uv run pytest tests/unit/generators/java/ --cov=src/generators/java --cov-report=html
```

**Day 5 Deliverables**:
- ✅ CLI command `specql generate java` working
- ✅ User guide documentation complete
- ✅ Examples created and tested
- ✅ All tests passing (50+ tests)

---

## ✅ Success Criteria (Week 11 Complete)

### Must Have
- [x] Generate JPA @Entity classes from SpecQL entities
- [x] Generate Spring Data JpaRepository interfaces
- [x] Generate @Service classes with CRUD + custom actions
- [x] Generate @RestController with REST endpoints
- [x] 50+ unit tests passing (>95% coverage)
- [x] 10+ integration tests passing
- [x] CLI command working
- [x] Documentation complete

### Nice to Have
- [ ] Maven/Gradle project file generation
- [ ] Spring Boot application.yml generation
- [ ] Docker compose for local development
- [ ] OpenAPI/Swagger documentation generation

### Metrics
- **Test Coverage**: >95% for Java generators
- **Code Quality**: Pass linting (ruff, mypy)
- **Performance**: Generate 100 entities in <5 seconds
- **Completeness**: All Spring Boot patterns supported

---

## 🧪 Testing Strategy

### Unit Tests (50+ tests)

**entity_generator.py** (15 tests):
- Simple entity generation
- Entity with foreign keys
- Entity with enums
- Entity with rich types
- Multi-tenant entities
- Audit field generation
- Getter/setter generation

**repository_generator.py** (12 tests):
- Basic JpaRepository interface
- Query methods (findBy, existsBy)
- Custom @Query methods
- Pagination support
- Specification executor
- Soft delete queries

**service_generator.py** (10 tests):
- Basic @Service class
- CRUD operations
- Custom action methods
- Validation logic
- Transaction management
- Error handling

**controller_generator.py** (8 tests):
- Basic @RestController
- REST endpoints (GET, POST, PUT, DELETE)
- Request validation
- Response formatting
- Error handling

**orchestrator** (5 tests):
- Full pipeline orchestration
- File path generation
- Multi-entity generation

### Integration Tests (10+ tests)

**test_java_generation_e2e.py**:
- Complete YAML → Java pipeline
- Multi-entity with relationships
- Custom actions compilation
- CLI command execution
- File output verification

---

## 📁 File Structure

```
src/generators/java/
├── __init__.py
├── entity_generator.py         # JPA @Entity generation
├── enum_generator.py            # Java enum generation
├── repository_generator.py     # Spring Data repository
├── service_generator.py        # @Service with business logic
├── controller_generator.py     # @RestController REST API
└── java_generator_orchestrator.py  # Orchestrates all generators

tests/unit/generators/java/
├── test_entity_generator.py
├── test_enum_generator.py
├── test_repository_generator.py
├── test_service_generator.py
├── test_controller_generator.py
└── test_orchestrator.py

tests/integration/java/
├── test_java_generation_e2e.py
└── test_cli_java_command.py

examples/java/
├── simple-entity.yaml
├── entity-with-relationships.yaml
└── custom-actions.yaml

docs/guides/
└── JAVA_CODE_GENERATION.md
```

---

## 🔗 Related Files

- **Previous**: [Week 10](./WEEK_10.md) - Spring Boot Pattern Recognition (Reverse Engineering)
- **Next**: [Week 12](./WEEK_12.md) - Python Code Generation
- **Roadmap**: [REPRIORITIZED_ROADMAP_2025-11-13.md](./REPRIORITIZED_ROADMAP_2025-11-13.md)
- **Related**:
  - Week 9 - Java AST Parser & JPA Extraction
  - Week 31-38 - Multi-Language Output Unification

---

## 📝 Implementation Notes

### Key Design Decisions

1. **Trinity Pattern Automatic**: All entities get `id`, `createdAt`, `updatedAt`, `deletedAt`
2. **Soft Delete by Default**: DELETE operations set `deletedAt` instead of hard delete
3. **Convention Over Configuration**: Package structure follows Spring Boot best practices
4. **Service Layer Required**: Business logic always goes in @Service, never in @Controller

### Common Pitfalls for Junior Developers

1. **Don't modify generated code directly** - Extend via inheritance instead
2. **Regenerate after schema changes** - Keep SpecQL YAML as source of truth
3. **Test generated code** - Don't assume generation is perfect
4. **Review before committing** - Generated code may need manual adjustments

### Code Quality Standards

- Follow Spring Boot naming conventions
- Use constructor injection (not field injection)
- Add @Transactional on write operations
- Include javadoc comments on public methods
- Handle exceptions properly (don't swallow errors)

---

**Status**: 📅 Ready to Execute
**Risk Level**: Medium
**Estimated Effort**: 40 hours (5 days)
**Prerequisites**: Week 10 complete ✅
**Confidence**: High (Well-defined scope, clear architecture)

---

*Last Updated*: 2025-11-14
*Author*: SpecQL Team
*Junior Developer Friendly*: Yes - Step-by-step instructions with code examples
